"""Printemps scraper - French luxury department store."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct
from .premium_brands import is_attractive_brand, normalize_brand_name

logger = logging.getLogger(__name__)


class PrintempsScraper(BaseScraper):
    """Scraper for Printemps sale section."""

    SOURCE_NAME = "printemps"
    BASE_URL = "https://www.printemps.com"
    CATEGORY = "textile"

    # Different sale categories
    SALE_URLS = [
        # Mode Homme
        "/fr/fr/mode-homme/soldes",
        "/fr/fr/mode-homme/soldes/pulls-gilets-sweats",
        "/fr/fr/mode-homme/soldes/chemises",
        "/fr/fr/mode-homme/soldes/t-shirts-polos",
        "/fr/fr/mode-homme/soldes/vestes-blousons-manteaux",
        "/fr/fr/mode-homme/soldes/pantalons-jeans",
        # Mode Femme
        "/fr/fr/mode-femme/soldes",
        "/fr/fr/mode-femme/soldes/pulls-gilets-sweats",
        "/fr/fr/mode-femme/soldes/chemises-tops",
        "/fr/fr/mode-femme/soldes/robes",
        "/fr/fr/mode-femme/soldes/vestes-blousons-manteaux",
        # Chaussures
        "/fr/fr/chaussures/soldes",
        "/fr/fr/chaussures/soldes/sneakers",
    ]

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/fr/fr/soldes"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Printemps sale products."""
        products = []
        seen_ids = set()

        # Try API first
        try:
            api_products = await self._scrape_via_api()
            if api_products:
                for p in api_products:
                    if p.external_id not in seen_ids:
                        seen_ids.add(p.external_id)
                        products.append(p)
                logger.info(f"[Printemps] Got {len(products)} products via API")
        except Exception as e:
            logger.debug(f"Printemps API scraping failed: {e}")

        # Fallback to browser for each category
        if not products:
            for url_path in self.SALE_URLS:
                try:
                    url = f"{self.BASE_URL}{url_path}"
                    page_products = await self._scrape_page(url)
                    for p in page_products:
                        if p.external_id not in seen_ids:
                            seen_ids.add(p.external_id)
                            products.append(p)
                except Exception as e:
                    logger.warning(f"Error scraping Printemps URL {url_path}: {e}")

        return products

    async def _scrape_via_api(self) -> List[ScrapedProduct]:
        """Try to scrape via Printemps API/GraphQL."""
        products = []

        # Printemps may use Algolia or similar
        # Common search API patterns
        search_endpoints = [
            f"{self.BASE_URL}/api/search",
            f"{self.BASE_URL}/api/products",
            f"{self.BASE_URL}/_next/data",
        ]

        headers = {
            "Accept": "application/json",
            "x-requested-with": "XMLHttpRequest",
            "Content-Type": "application/json",
        }

        for endpoint in search_endpoints:
            try:
                response = await self._http_client.get(
                    endpoint,
                    params={"sale": "true", "page": 1, "limit": 100},
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    if "products" in data or "hits" in data or "items" in data:
                        items = data.get("products") or data.get("hits") or data.get("items", [])
                        for item in items:
                            product = self._parse_api_product(item)
                            if product:
                                products.append(product)
                        if products:
                            return products
            except Exception as e:
                logger.debug(f"Printemps API endpoint {endpoint} failed: {e}")

        return products

    def _parse_api_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse product from API response."""
        try:
            product_id = str(item.get("id", "") or item.get("productId", "") or item.get("sku", ""))
            name = item.get("name", "") or item.get("title", "") or item.get("label", "")
            brand = item.get("brand", "") or item.get("vendor", "") or item.get("brandName", "")

            if not brand:
                brand_obj = item.get("brand", {})
                if isinstance(brand_obj, dict):
                    brand = brand_obj.get("name", "") or brand_obj.get("label", "")

            # Filter by attractive brands
            if not is_attractive_brand(brand):
                return None

            # Prices
            price_data = item.get("price", {})
            if isinstance(price_data, dict):
                sale_price = float(price_data.get("current", 0) or price_data.get("sale", 0) or price_data.get("value", 0))
                original_price = float(price_data.get("original", sale_price) or price_data.get("regular", sale_price))
            else:
                sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
                original_price = float(item.get("originalPrice", sale_price) or item.get("compareAtPrice", sale_price))

            if not sale_price or sale_price <= 0 or original_price <= sale_price:
                return None

            # URL
            url_path = item.get("url", "") or item.get("slug", "") or item.get("handle", "")
            product_url = f"{self.BASE_URL}{url_path}" if url_path and not url_path.startswith("http") else url_path

            # Image
            images = item.get("images", []) or item.get("media", [])
            image_url = ""
            if images:
                if isinstance(images[0], dict):
                    image_url = images[0].get("url", "") or images[0].get("src", "")
                elif isinstance(images[0], str):
                    image_url = images[0]

            # Category
            category_raw = item.get("category", "") or item.get("productType", "")
            category, subcategory = self._detect_printemps_category(name, category_raw)

            return ScrapedProduct(
                external_id=product_id,
                product_name=name,
                brand=normalize_brand_name(brand),
                model=self.extract_model_from_name(name, brand),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                category=category,
                subcategory=subcategory,
                gender=self.detect_gender(name, product_url),
                raw_data=item,
            )
        except Exception as e:
            logger.debug(f"Error parsing Printemps API product: {e}")
            return None

    async def _scrape_page(self, url: str) -> List[ScrapedProduct]:
        """Scrape a single Printemps category page."""
        products = []
        page = await self.get_page()

        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector(
                    '#onetrust-accept-btn-handler, '
                    '[data-testid="cookie-accept"], '
                    '.cookie-accept, '
                    'button:has-text("Accepter")'
                )
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Scroll to load more products (lazy loading)
            for _ in range(8):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            # Get product cards - Printemps uses various selectors
            cards = await page.query_selector_all(
                '.product-tile, '
                '.product-card, '
                '[data-testid="product-tile"], '
                '[class*="ProductCard"], '
                '[class*="product-item"], '
                'article[class*="product"]'
            )

            logger.info(f"[Printemps] Found {len(cards)} product cards on {url}")

            for card in cards[:80]:
                try:
                    product = await self._parse_product_card(card, url)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Error parsing Printemps product card: {e}")

        except Exception as e:
            logger.error(f"Printemps scraping error for {url}: {e}")
        finally:
            await page.close()

        return products

    async def _parse_product_card(self, card, page_url: str) -> Optional[ScrapedProduct]:
        """Parse a product card element from Printemps website."""
        try:
            # Get link
            link = await card.query_selector("a[href*='/p/'], a[href*='product']")
            if not link:
                link = await card.query_selector("a")

            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

            # Extract product ID from URL
            match = re.search(r'/p/([^/?\s]+)', href)
            if match:
                external_id = match.group(1)
            else:
                match = re.search(r'[-/](\d{6,})', href)
                external_id = match.group(1) if match else href.split("/")[-1].split("?")[0]

            # Get brand
            brand_el = await card.query_selector(
                '.product-brand, '
                '[class*="brand"], '
                '[data-testid="product-brand"], '
                '[class*="Brand"]'
            )
            brand = ""
            if brand_el:
                brand = await brand_el.inner_text()
                brand = brand.strip()

            # Filter by attractive brands
            if not is_attractive_brand(brand):
                return None

            # Get product name
            name_el = await card.query_selector(
                '.product-name, '
                '.product-title, '
                '[class*="name"], '
                '[class*="title"], '
                '[data-testid="product-name"], '
                'h2, h3'
            )
            product_name = ""
            if name_el:
                product_name = await name_el.inner_text()
                product_name = product_name.strip()

            if not product_name:
                return None

            full_name = f"{brand} {product_name}" if brand else product_name

            # Get prices
            sale_price_el = await card.query_selector(
                '.price-sale, '
                '.sale-price, '
                '[class*="sale"], '
                '[class*="current-price"], '
                '[data-testid="sale-price"]'
            )
            original_price_el = await card.query_selector(
                '.price-original, '
                '.original-price, '
                '.price-crossed, '
                '[class*="was-price"], '
                '[class*="crossed"], '
                '[data-testid="original-price"], '
                'del, s'
            )

            if not sale_price_el:
                sale_price_el = await card.query_selector('.price, [class*="price"]')

            if not sale_price_el:
                return None

            sale_price_text = await sale_price_el.inner_text()
            sale_price = self.parse_price(sale_price_text)

            if original_price_el:
                original_price_text = await original_price_el.inner_text()
                original_price = self.parse_price(original_price_text)
            else:
                original_price = sale_price

            if not sale_price or sale_price <= 0:
                return None

            if not original_price or original_price <= sale_price:
                return None

            # Get image
            img_el = await card.query_selector("img")
            image_url = ""
            if img_el:
                image_url = await img_el.get_attribute("src") or await img_el.get_attribute("data-src") or ""

            # Detect attributes
            gender = self.detect_gender(full_name, product_url)
            if not gender or gender == "unisex":
                if "homme" in page_url.lower():
                    gender = "men"
                elif "femme" in page_url.lower():
                    gender = "women"

            category, subcategory = self._detect_printemps_category(full_name, page_url)

            return ScrapedProduct(
                external_id=external_id,
                product_name=full_name,
                brand=normalize_brand_name(brand),
                model=self.extract_model_from_name(product_name, brand),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                gender=gender,
                category=category,
                subcategory=subcategory,
                sizes_available=[],
                stock_available=True,
            )

        except Exception as e:
            logger.debug(f"Error parsing Printemps card: {e}")
            return None

    def _detect_printemps_category(self, product_name: str, context: str = "") -> tuple[str, str]:
        """Detect category for Printemps products."""
        text = f"{product_name} {context}".lower()

        # Chaussures/Sneakers
        if any(kw in text for kw in ["sneaker", "basket", "chaussure", "trainer", "shoe"]):
            return "sneakers", "lifestyle"

        # Pulls/Knitwear
        if any(kw in text for kw in ["pull", "sweater", "cardigan", "gilet", "tricot", "maille"]):
            return "textile", "knitwear"

        # Chemises
        if any(kw in text for kw in ["chemise", "shirt", "oxford"]) and "t-shirt" not in text:
            return "textile", "shirts"

        # T-shirts
        if any(kw in text for kw in ["t-shirt", "tee", "tshirt"]):
            return "textile", "tshirts"

        # Polos
        if "polo" in text:
            return "textile", "polos"

        # Sweatshirts/Hoodies
        if any(kw in text for kw in ["sweat", "hoodie", "hoody"]):
            return "textile", "hoodies"

        # Vestes/Manteaux
        if any(kw in text for kw in ["veste", "blouson", "manteau", "jacket", "coat", "blazer", "parka"]):
            return "textile", "jackets"

        # Pantalons
        if any(kw in text for kw in ["pantalon", "pant", "jean", "denim", "chino"]):
            return "textile", "pants"

        # Robes (femme)
        if "robe" in text or "dress" in text:
            return "textile", "dresses"

        # Accessoires
        if any(kw in text for kw in ["sac", "bag", "ceinture", "belt", "écharpe", "scarf", "chapeau", "hat", "casquette", "cap"]):
            if any(kw in text for kw in ["casquette", "cap", "chapeau", "hat", "bonnet", "beanie"]):
                return "accessoires", "caps"
            return "accessoires", "other"

        # Default
        return "textile", "premium"
