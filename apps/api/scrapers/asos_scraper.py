"""ASOS scraper - Fashion outlet deals."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct
from .premium_brands import is_attractive_brand, normalize_brand_name

logger = logging.getLogger(__name__)


class AsosScraper(BaseScraper):
    """Scraper for ASOS sale section."""

    SOURCE_NAME = "asos"
    BASE_URL = "https://www.asos.com"
    CATEGORY = "textile"

    # ASOS outlet/sale endpoints
    SALE_ENDPOINTS = [
        "/fr/hommes/outlet/cat/?cid=27391",
        "/fr/hommes/soldes/cat/?cid=8409",
        "/fr/femmes/outlet/cat/?cid=27394",
        "/fr/femmes/soldes/cat/?cid=7046",
    ]

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/fr/hommes/outlet/cat/?cid=27391"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape ASOS sale products."""
        products = []
        seen_ids = set()

        # Try API first
        for endpoint in self.SALE_ENDPOINTS:
            try:
                endpoint_products = await self._scrape_api(endpoint)
                for p in endpoint_products:
                    if p.external_id not in seen_ids:
                        seen_ids.add(p.external_id)
                        products.append(p)
            except Exception as e:
                logger.warning(f"Error scraping ASOS endpoint {endpoint}: {e}")

        # Fallback to browser if API fails
        if not products:
            logger.info("[ASOS] API failed, trying browser fallback")
            products = await self._scrape_with_browser()

        return products

    async def _scrape_api(self, endpoint: str) -> List[ScrapedProduct]:
        """Scrape ASOS using their API."""
        products = []

        # Extract category ID from endpoint
        cid_match = re.search(r'cid=(\d+)', endpoint)
        if not cid_match:
            return products

        cid = cid_match.group(1)

        # ASOS API endpoint
        api_url = f"https://www.asos.com/api/product/search/v2/categories/{cid}"
        params = {
            "offset": 0,
            "limit": 72,
            "store": "FR",
            "lang": "fr-FR",
            "currency": "EUR",
            "rowlength": 4,
            "channel": "desktop-web",
            "country": "FR",
            "keyStoreDataversion": "3pn0hpe-39",
            "advertisementsEnabled": "false",
            "advertisementsPlacementEnabled": "false",
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "asos-c-plat": "Web",
            "asos-c-name": "Asos.Commerce.Pdp.Web",
        }

        try:
            response = await self._http_client.get(
                api_url,
                params=params,
                headers=headers
            )

            if response.status_code != 200:
                logger.debug(f"ASOS API returned {response.status_code}")
                return products

            data = response.json()
            items = data.get("products", [])

            for item in items:
                try:
                    product = self._parse_api_product(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Error parsing ASOS product: {e}")

        except Exception as e:
            logger.warning(f"Error fetching ASOS API: {e}")

        return products

    def _parse_api_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse an ASOS API product."""
        try:
            product_id = str(item.get("id", ""))
            name = item.get("name", "")

            if not product_id or not name:
                return None

            # Get brand
            brand = item.get("brandName", "")
            if not brand:
                return None

            # Filter by attractive brands
            if not is_attractive_brand(brand):
                return None

            # Get prices
            price_info = item.get("price", {})
            current_price = price_info.get("current", {}).get("value", 0)
            previous_price = price_info.get("previous", {}).get("value", 0)
            rrp_price = price_info.get("rrp", {}).get("value", 0)

            sale_price = float(current_price) if current_price else None
            original_price = float(previous_price) if previous_price else float(rrp_price) if rrp_price else None

            if not sale_price:
                return None

            # Must have a discount
            if not original_price or original_price <= sale_price:
                return None

            # Get image
            image_url = item.get("imageUrl", "")
            if image_url and not image_url.startswith("http"):
                image_url = f"https://{image_url}"

            # Build product URL
            product_url = item.get("url", "")
            if product_url and not product_url.startswith("http"):
                product_url = f"{self.BASE_URL}{product_url}"

            # Detect category
            product_type = item.get("productType", "")
            category, subcategory = self._detect_asos_category(name, product_type)

            # Detect gender from URL or name
            gender = self.detect_gender(name, product_url)
            if not gender or gender == "unisex":
                if "/hommes/" in product_url or "/men/" in product_url.lower():
                    gender = "men"
                elif "/femmes/" in product_url or "/women/" in product_url.lower():
                    gender = "women"

            # Get color
            color = item.get("colour", "")

            return ScrapedProduct(
                external_id=product_id,
                product_name=name,
                brand=normalize_brand_name(brand),
                model=self._extract_model(name, brand),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                category=category,
                subcategory=subcategory,
                gender=gender,
                color=color,
                stock_available=True,
            )

        except Exception as e:
            logger.debug(f"Error parsing ASOS product: {e}")
            return None

    def _detect_asos_category(self, title: str, product_type: str) -> tuple[str, str]:
        """Detect category for ASOS products."""
        text = f"{title} {product_type}".lower()

        # Footwear
        if any(kw in text for kw in ["sneaker", "shoe", "trainer", "basket", "chaussure", "boot", "sandal"]):
            return "sneakers", "lifestyle"

        # Outerwear
        if any(kw in text for kw in ["jacket", "coat", "parka", "bomber", "veste", "manteau", "blouson"]):
            return "textile", "jackets"

        # Hoodies
        if any(kw in text for kw in ["hoodie", "hoody", "sweat", "capuche"]):
            return "textile", "hoodies"

        # T-shirts
        if any(kw in text for kw in ["t-shirt", "tee", "tshirt"]):
            return "textile", "tshirts"

        # Shirts
        if any(kw in text for kw in ["shirt", "chemise"]) and "t-shirt" not in text:
            return "textile", "shirts"

        # Pants
        if any(kw in text for kw in ["pant", "trouser", "jean", "pantalon", "chino", "jogger"]):
            return "textile", "pants"

        # Shorts
        if "short" in text:
            return "textile", "shorts"

        # Polos
        if "polo" in text:
            return "textile", "polos"

        # Knitwear
        if any(kw in text for kw in ["sweater", "pull", "cardigan", "knit"]):
            return "textile", "knitwear"

        # Accessories
        if any(kw in text for kw in ["cap", "casquette", "hat", "bag", "sac", "belt", "ceinture"]):
            return "accessoires", "other"

        return "textile", "other"

    def _extract_model(self, title: str, brand: str) -> Optional[str]:
        """Extract model name from title."""
        title_clean = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE).strip()

        # Common sneaker models
        sneaker_patterns = [
            r"(Air Max \d+)", r"(Air Force \d+)", r"(Air Jordan \d+)", r"(Dunk \w+)",
            r"(Ultraboost)", r"(Stan Smith)", r"(Superstar)", r"(NMD)",
            r"(574)", r"(990)", r"(550)", r"(2002)",
            r"(Old Skool)", r"(Sk8-Hi)", r"(Era)",
        ]

        for pattern in sneaker_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)

        words = title_clean.split()
        if len(words) >= 2:
            return " ".join(words[:3])

        return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Browser fallback for ASOS."""
        products = []

        try:
            page = await self.get_page()

            for endpoint in self.SALE_ENDPOINTS[:2]:
                try:
                    url = f"{self.BASE_URL}{endpoint}"
                    await page.goto(url, wait_until="networkidle")
                    await page.wait_for_timeout(3000)

                    # Scroll to load more
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await page.wait_for_timeout(1500)

                    # Get product cards
                    cards = await page.query_selector_all(
                        '[data-auto-id="productTile"], .product-card, article[data-id]'
                    )

                    for card in cards[:50]:
                        try:
                            product = await self._parse_browser_card(card)
                            if product:
                                products.append(product)
                        except Exception as e:
                            logger.debug(f"Error parsing ASOS card: {e}")

                except Exception as e:
                    logger.warning(f"Error browsing ASOS endpoint: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"ASOS browser scraping error: {e}")

        return products

    async def _parse_browser_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card from browser."""
        try:
            # Get link
            link = await card.query_selector("a[href*='/prd/']")
            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            # Extract product ID
            prd_match = re.search(r'/prd/(\d+)', href)
            product_id = prd_match.group(1) if prd_match else href[:30]

            # Get title
            title_el = await card.query_selector('[data-auto-id="productTitle"], .product-title, h2, h3')
            title = await title_el.inner_text() if title_el else ""
            title = title.strip()

            if not title:
                return None

            # Try to extract brand from title (ASOS format: "Brand - Product Name")
            brand = ""
            if " - " in title:
                brand = title.split(" - ")[0].strip()
            elif " | " in title:
                brand = title.split(" | ")[0].strip()

            if not brand or not is_attractive_brand(brand):
                return None

            # Get prices
            price_container = await card.query_selector('[data-auto-id="productPrice"], .product-price')
            if not price_container:
                return None

            sale_el = await price_container.query_selector('.sale-price, [data-auto-id="salePrice"]')
            orig_el = await price_container.query_selector('.original-price, [data-auto-id="originalPrice"], s')

            if not sale_el:
                sale_el = await price_container.query_selector('span')

            if not sale_el:
                return None

            sale_text = await sale_el.inner_text()
            sale_price = self.parse_price(sale_text)

            if orig_el:
                orig_text = await orig_el.inner_text()
                original_price = self.parse_price(orig_text)
            else:
                original_price = sale_price

            if not sale_price or not original_price or original_price <= sale_price:
                return None

            # Get image
            img = await card.query_selector("img")
            image_url = ""
            if img:
                image_url = await img.get_attribute("src") or await img.get_attribute("data-src") or ""

            category, subcategory = self._detect_asos_category(title, "")

            return ScrapedProduct(
                external_id=product_id,
                product_name=title,
                brand=normalize_brand_name(brand),
                model=self._extract_model(title, brand),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                category=category,
                subcategory=subcategory,
                gender=self.detect_gender(title, product_url),
            )

        except Exception as e:
            logger.debug(f"Error parsing ASOS card: {e}")
            return None
