"""La Redoute scraper - French fashion retailer."""
import logging
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct
from .premium_brands import is_attractive_brand, normalize_brand_name

logger = logging.getLogger(__name__)


class LaRedouteScraper(BaseScraper):
    """Scraper for La Redoute sale section - only premium brands."""

    SOURCE_NAME = "laredoute"
    BASE_URL = "https://www.laredoute.fr"
    CATEGORY = "textile"

    # Categories to scrape - focus on branded fashion
    SALE_CATEGORIES = [
        "/prlst/vt_soldes.aspx",
        "/prlst/cat-homme-soldes.aspx",
        "/prlst/cat-femme-soldes.aspx",
        "/prlst/cat-homme-soldes-pulls-gilets.aspx",
        "/prlst/cat-homme-soldes-chemises.aspx",
        "/prlst/cat-homme-soldes-polos.aspx",
        "/prlst/cat-homme-soldes-vestes-blousons.aspx",
        "/prlst/cat-femme-soldes-pulls-gilets.aspx",
        "/prlst/cat-femme-soldes-chemises-blouses.aspx",
    ]

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/prlst/vt_soldes.aspx"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape La Redoute sale products - only attractive brands."""
        products = []
        seen_ids = set()

        # Try API first
        try:
            api_products = await self._scrape_via_api()
            for p in api_products:
                if p.external_id not in seen_ids:
                    seen_ids.add(p.external_id)
                    products.append(p)
        except Exception as e:
            logger.debug(f"La Redoute API failed: {e}")

        # Fallback to browser for multiple categories
        if not products:
            for cat_path in self.SALE_CATEGORIES[:5]:
                try:
                    url = f"{self.BASE_URL}{cat_path}"
                    page_products = await self._scrape_page_browser(url)
                    for p in page_products:
                        if p.external_id not in seen_ids:
                            seen_ids.add(p.external_id)
                            products.append(p)
                except Exception as e:
                    logger.warning(f"Error scraping La Redoute {cat_path}: {e}")

        logger.info(f"[La Redoute] Total products after brand filter: {len(products)}")
        return products

    async def _scrape_via_api(self) -> List[ScrapedProduct]:
        """Try to scrape via La Redoute API."""
        products = []

        api_url = f"{self.BASE_URL}/ajax/products/search"
        params = {
            "category": "soldes",
            "page": 1,
            "pageSize": 100,
        }

        headers = {
            "Accept": "application/json",
            "x-requested-with": "XMLHttpRequest",
        }

        try:
            response = await self._http_client.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                products = self._parse_api_response(data)
        except Exception as e:
            logger.debug(f"La Redoute API failed: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[ScrapedProduct]:
        """Parse La Redoute API response."""
        products = []

        items = data.get("products", []) or data.get("items", [])

        for item in items:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing La Redoute product: {e}")

        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse single La Redoute product - only if attractive brand."""
        try:
            product_id = item.get("ref") or item.get("id", "")
            name = item.get("label", "") or item.get("name", "")
            brand = item.get("brand", {}).get("label", "") if isinstance(item.get("brand"), dict) else item.get("brand", "")

            # IMPORTANT: Filter by attractive brands only
            if not brand or not is_attractive_brand(brand):
                return None

            # Prices
            price_data = item.get("price", {})
            if isinstance(price_data, dict):
                sale_price = float(price_data.get("current", 0) or price_data.get("sale", 0))
                original_price = float(price_data.get("crossed", sale_price) or price_data.get("original", sale_price))
            else:
                sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
                original_price = float(item.get("originalPrice", sale_price))

            if not sale_price or sale_price <= 0:
                return None

            # Must be on sale
            if original_price <= sale_price:
                return None

            # URL
            url_path = item.get("url", "") or item.get("link", "")
            product_url = f"{self.BASE_URL}{url_path}" if url_path and not url_path.startswith("http") else url_path

            # Image
            images = item.get("images", []) or item.get("visuals", [])
            image_url = ""
            if images:
                if isinstance(images[0], dict):
                    image_url = images[0].get("url", "") or images[0].get("src", "")
                elif isinstance(images[0], str):
                    image_url = images[0]

            # Sizes
            sizes = []
            size_data = item.get("sizes", []) or item.get("variants", [])
            for size in size_data:
                if isinstance(size, dict):
                    if size.get("available", True):
                        sizes.append(size.get("label", "") or size.get("value", ""))
                elif isinstance(size, str):
                    sizes.append(size)

            category, subcategory = self._detect_laredoute_category(name)

            return ScrapedProduct(
                external_id=str(product_id),
                product_name=name,
                brand=normalize_brand_name(brand),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                model=self.extract_model_from_name(name, brand),
                category=category,
                subcategory=subcategory,
                gender=self.detect_gender(name, product_url),
                sizes_available=sizes,
                stock_available=len(sizes) > 0 if sizes else True,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing La Redoute product: {e}")
            return None

    def _detect_laredoute_category(self, product_name: str) -> tuple[str, str]:
        """Detect category for La Redoute products."""
        name_lower = product_name.lower()

        # Pulls/Knitwear
        if any(kw in name_lower for kw in ["pull", "sweater", "cardigan", "gilet", "maille"]):
            return "textile", "knitwear"

        # Chemises
        if any(kw in name_lower for kw in ["chemise", "shirt"]) and "t-shirt" not in name_lower:
            return "textile", "shirts"

        # T-shirts
        if any(kw in name_lower for kw in ["t-shirt", "tee"]):
            return "textile", "tshirts"

        # Polos
        if "polo" in name_lower:
            return "textile", "polos"

        # Sweatshirts/Hoodies
        if any(kw in name_lower for kw in ["sweat", "hoodie"]):
            return "textile", "hoodies"

        # Vestes/Manteaux
        if any(kw in name_lower for kw in ["veste", "blouson", "manteau", "jacket", "blazer", "parka"]):
            return "textile", "jackets"

        # Pantalons
        if any(kw in name_lower for kw in ["pantalon", "jean", "chino"]):
            return "textile", "pants"

        # Sneakers
        if any(kw in name_lower for kw in ["basket", "sneaker", "chaussure"]):
            return "sneakers", "lifestyle"

        return "textile", "streetwear"

    async def _scrape_page_browser(self, url: str) -> List[ScrapedProduct]:
        """Scrape a single La Redoute page via browser."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(url, wait_until="networkidle")

            # Handle cookie popup
            try:
                cookie_btn = await page.query_selector("#popin_tc_privacy_button_2, .didomi-continue-without-agreeing")
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Scroll to load more
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            await page.wait_for_selector(".product-tile, .prd, [data-product-id]", timeout=15000)

            cards = await page.query_selector_all(".product-tile, .prd, [data-product-id]")

            for card in cards[:80]:
                try:
                    name_el = await card.query_selector(".prd-info-title, .product-name, h2, h3")
                    brand_el = await card.query_selector(".prd-info-brand, .product-brand")
                    price_el = await card.query_selector(".prd-price-new, .sale-price, .price-current")
                    original_el = await card.query_selector(".prd-price-old, .original-price, .price-crossed")
                    link_el = await card.query_selector("a[href]")
                    img_el = await card.query_selector("img")

                    if not name_el or not price_el:
                        continue

                    name = await name_el.inner_text()
                    brand = await brand_el.inner_text() if brand_el else ""
                    brand = brand.strip()

                    # IMPORTANT: Filter by attractive brands only
                    if not brand or not is_attractive_brand(brand):
                        continue

                    price_text = await price_el.inner_text()
                    original_text = await original_el.inner_text() if original_el else ""
                    href = await link_el.get_attribute("href") if link_el else ""
                    img_src = ""
                    if img_el:
                        img_src = await img_el.get_attribute("src") or await img_el.get_attribute("data-src") or ""

                    sale_price = self.parse_price(price_text)
                    original_price = self.parse_price(original_text) or sale_price

                    if not sale_price or original_price <= sale_price:
                        continue

                    product_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    category, subcategory = self._detect_laredoute_category(name)

                    products.append(ScrapedProduct(
                        external_id=href.split("/")[-1].split(".")[0] if href else name[:20],
                        product_name=name.strip(),
                        brand=normalize_brand_name(brand),
                        original_price=original_price,
                        sale_price=sale_price,
                        discount_pct=None,
                        product_url=product_url,
                        image_url=img_src,
                        category=category,
                        subcategory=subcategory,
                        gender=self.detect_gender(name, product_url),
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing La Redoute card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"La Redoute browser error for {url}: {e}")

        return products
