"""Kith EU scraper - Premium streetwear retailer (Shopify-based)."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct
from .premium_brands import is_attractive_brand, normalize_brand_name

logger = logging.getLogger(__name__)


class KithScraper(BaseScraper):
    """Scraper for Kith EU sale section (Shopify store)."""

    SOURCE_NAME = "kith"
    BASE_URL = "https://eu.kith.com"
    CATEGORY = "textile"

    # Kith uses Shopify - we can use the JSON API
    SALE_COLLECTIONS = [
        "sale",
        "mens-sale",
        "womens-sale",
        "sale-footwear",
        "sale-apparel",
    ]

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/collections/sale"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Kith sale products via Shopify JSON API."""
        products = []
        seen_ids = set()

        for collection in self.SALE_COLLECTIONS:
            try:
                collection_products = await self._scrape_collection(collection)
                for p in collection_products:
                    if p.external_id not in seen_ids:
                        seen_ids.add(p.external_id)
                        products.append(p)
            except Exception as e:
                logger.warning(f"Error scraping Kith collection {collection}: {e}")

        # If API fails, fallback to browser
        if not products:
            logger.info("[Kith] API failed, trying browser fallback")
            products = await self._scrape_with_browser()

        return products

    async def _scrape_collection(self, collection: str) -> List[ScrapedProduct]:
        """Scrape a single Kith collection via Shopify JSON API."""
        products = []
        page = 1
        max_pages = 5

        while page <= max_pages:
            try:
                # Shopify standard JSON endpoint
                url = f"{self.BASE_URL}/collections/{collection}/products.json?page={page}&limit=250"
                response = await self._http_client.get(url)

                if response.status_code != 200:
                    logger.debug(f"Kith API returned {response.status_code} for {collection}")
                    break

                data = response.json()
                items = data.get("products", [])

                if not items:
                    break

                for item in items:
                    try:
                        product = self._parse_shopify_product(item)
                        if product:
                            products.append(product)
                    except Exception as e:
                        logger.debug(f"Error parsing Kith product: {e}")

                page += 1

            except Exception as e:
                logger.warning(f"Error fetching Kith collection {collection} page {page}: {e}")
                break

        return products

    def _parse_shopify_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse a Shopify product JSON object."""
        try:
            product_id = str(item.get("id", ""))
            title = item.get("title", "")
            vendor = item.get("vendor", "Kith")
            handle = item.get("handle", "")
            product_type = item.get("product_type", "")

            # Filter by attractive brands only
            if not is_attractive_brand(vendor):
                return None

            # Get variants for pricing and sizes
            variants = item.get("variants", [])
            if not variants:
                return None

            # Find prices - look for compare_at_price (original) vs price (sale)
            sale_price = None
            original_price = None
            available_sizes = []

            for variant in variants:
                variant_price = float(variant.get("price", 0))
                compare_price = variant.get("compare_at_price")

                if compare_price:
                    compare_price = float(compare_price)

                # Track available sizes
                if variant.get("available", False):
                    size = variant.get("title", "") or variant.get("option1", "")
                    if size and size != "Default Title":
                        available_sizes.append(size)

                # Get the lowest sale price and highest original price
                if variant_price > 0:
                    if sale_price is None or variant_price < sale_price:
                        sale_price = variant_price

                if compare_price and compare_price > 0:
                    if original_price is None or compare_price > original_price:
                        original_price = compare_price

            # Must have a sale (compare_at_price > price)
            if not sale_price:
                return None

            if not original_price or original_price <= sale_price:
                return None

            # Get image
            images = item.get("images", [])
            image_url = ""
            if images:
                if isinstance(images[0], dict):
                    image_url = images[0].get("src", "")
                elif isinstance(images[0], str):
                    image_url = images[0]

            # Build product URL
            product_url = f"{self.BASE_URL}/products/{handle}"

            # Detect category
            category, subcategory = self._detect_kith_category(title, product_type)

            # Detect gender
            gender = self.detect_gender(title, product_url)
            if not gender or gender == "unisex":
                # Try from tags
                tags = item.get("tags", [])
                if isinstance(tags, list):
                    tags_str = " ".join(tags).lower()
                    if "mens" in tags_str or "men" in tags_str:
                        gender = "men"
                    elif "womens" in tags_str or "women" in tags_str:
                        gender = "women"

            return ScrapedProduct(
                external_id=product_id,
                product_name=title,
                brand=normalize_brand_name(vendor),
                model=self._extract_model(title, vendor),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                category=category,
                subcategory=subcategory,
                gender=gender,
                sizes_available=available_sizes[:10],
                stock_available=len(available_sizes) > 0,
                raw_data={"handle": handle, "product_type": product_type},
            )

        except Exception as e:
            logger.debug(f"Error parsing Kith product: {e}")
            return None

    def _detect_kith_category(self, title: str, product_type: str) -> tuple[str, str]:
        """Detect category for Kith products."""
        text = f"{title} {product_type}".lower()

        # Footwear
        if any(kw in text for kw in ["sneaker", "shoe", "runner", "slide", "sandal", "boot", "trainer"]):
            if any(kw in text for kw in ["running", "runner"]):
                return "sneakers", "running"
            return "sneakers", "lifestyle"

        # Outerwear
        if any(kw in text for kw in ["jacket", "coat", "parka", "bomber", "windbreaker", "puffer", "down"]):
            return "textile", "jackets"

        # Hoodies & Sweatshirts
        if any(kw in text for kw in ["hoodie", "hoody", "sweatshirt", "crewneck", "pullover"]):
            return "textile", "hoodies"

        # T-shirts
        if any(kw in text for kw in ["t-shirt", "tee", "tshirt"]):
            return "textile", "tshirts"

        # Shirts
        if any(kw in text for kw in ["shirt", "oxford", "button"]) and "t-shirt" not in text:
            return "textile", "shirts"

        # Pants
        if any(kw in text for kw in ["pant", "trouser", "jean", "denim", "chino", "jogger", "sweatpant"]):
            return "textile", "pants"

        # Shorts
        if "short" in text:
            return "textile", "shorts"

        # Polos
        if "polo" in text:
            return "textile", "polos"

        # Knitwear
        if any(kw in text for kw in ["sweater", "knit", "cardigan"]):
            return "textile", "knitwear"

        # Accessories
        if any(kw in text for kw in ["cap", "hat", "beanie", "bag", "backpack", "belt", "scarf", "glove"]):
            if any(kw in text for kw in ["cap", "hat", "beanie"]):
                return "accessoires", "caps"
            return "accessoires", "other"

        # Default to streetwear
        return "textile", "streetwear"

    def _extract_model(self, title: str, brand: str) -> Optional[str]:
        """Extract model name from Kith product title."""
        # Remove brand name from title
        title_clean = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE).strip()

        # Common model patterns for sneakers
        sneaker_models = [
            r"(Air Max \d+)", r"(Air Force \d+)", r"(Air Jordan \d+)", r"(Dunk \w+)",
            r"(Ultraboost \d*)", r"(NMD \w+)", r"(Stan Smith)", r"(Superstar)",
            r"(574)", r"(990v?\d?)", r"(550)", r"(2002r)",
            r"(Gel-\w+)", r"(Old Skool)", r"(Sk8-Hi)",
        ]

        for pattern in sneaker_models:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)

        # Return first meaningful words
        words = title_clean.split()
        if len(words) >= 2:
            return " ".join(words[:3])

        return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Browser fallback for Kith."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(self.get_sale_url(), wait_until="networkidle")

            # Wait for products to load
            await page.wait_for_timeout(3000)

            # Scroll to load more
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1500)

            # Get product cards - Kith uses various selectors
            cards = await page.query_selector_all(
                '.product-card, .product-item, [data-product-card], .collection-product'
            )

            for card in cards[:100]:
                try:
                    product = await self._parse_browser_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Error parsing Kith browser card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"Kith browser scraping error: {e}")

        return products

    async def _parse_browser_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card from browser."""
        try:
            # Get link
            link = await card.query_selector("a[href*='/products/']")
            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            handle = href.split("/products/")[-1].split("?")[0] if "/products/" in href else ""

            # Get title
            title_el = await card.query_selector(".product-title, .product-name, h2, h3, [class*='title']")
            title = await title_el.inner_text() if title_el else ""
            title = title.strip()

            if not title:
                return None

            # Get brand
            brand_el = await card.query_selector(".product-vendor, .product-brand, [class*='vendor']")
            brand = await brand_el.inner_text() if brand_el else "Kith"
            brand = brand.strip()

            # Filter by attractive brands
            if not is_attractive_brand(brand):
                return None

            # Get prices
            sale_el = await card.query_selector(".price-sale, .sale-price, [class*='sale'], .price--on-sale")
            orig_el = await card.query_selector(".price-compare, .compare-price, [class*='compare'], .price--regular")

            if not sale_el:
                sale_el = await card.query_selector(".price, [class*='price']")

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

            category, subcategory = self._detect_kith_category(title, "")

            return ScrapedProduct(
                external_id=handle or title[:30],
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
            logger.debug(f"Error parsing Kith card: {e}")
            return None
