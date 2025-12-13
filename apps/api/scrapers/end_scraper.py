"""END. Clothing scraper - Premium streetwear and sneakers."""
import logging
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class EndScraper(BaseScraper):
    """Scraper for END. Clothing sale section."""

    SOURCE_NAME = "end"
    BASE_URL = "https://www.endclothing.com"
    CATEGORY = "sneakers"

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/fr/sale"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape END. sale products via API."""
        products = []

        try:
            # END. uses a GraphQL/REST API for product listing
            api_url = f"{self.BASE_URL}/fr/api/products"
            params = {
                "category": "sale",
                "limit": 100,
                "offset": 0,
            }

            headers = {
                "Accept": "application/json",
                "x-requested-with": "XMLHttpRequest",
            }

            # Try API first
            try:
                response = await self._http_client.get(
                    f"{self.BASE_URL}/fr/_next/data/sale.json",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    products = self._parse_api_response(data)
                    if products:
                        return products
            except Exception as e:
                logger.debug(f"API method failed, trying browser: {e}")

            # Fallback to browser scraping
            products = await self._scrape_with_browser()

        except Exception as e:
            logger.error(f"END. scraping error: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[ScrapedProduct]:
        """Parse API response into products."""
        products = []

        items = data.get("pageProps", {}).get("products", [])
        if not items:
            items = data.get("products", [])

        for item in items:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing END. product: {e}")

        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse single product from API response."""
        try:
            product_id = item.get("id") or item.get("sku", "")
            name = item.get("name", "")
            brand = item.get("brand", {}).get("name", "") if isinstance(item.get("brand"), dict) else item.get("brand", "")

            # Prices
            price_info = item.get("price", {})
            if isinstance(price_info, dict):
                sale_price = price_info.get("current", 0)
                original_price = price_info.get("original", sale_price)
            else:
                sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
                original_price = float(item.get("originalPrice", sale_price) or sale_price)

            if not sale_price or sale_price <= 0:
                return None

            # URL
            slug = item.get("slug", "") or item.get("url", "")
            product_url = f"{self.BASE_URL}/fr/product/{slug}" if slug and not slug.startswith("http") else slug

            # Image
            images = item.get("images", [])
            image_url = images[0].get("url", "") if images else item.get("image", "")

            # Sizes
            sizes = []
            variants = item.get("variants", []) or item.get("sizes", [])
            for v in variants:
                if isinstance(v, dict):
                    size = v.get("size", "") or v.get("name", "")
                    if v.get("available", True) and size:
                        sizes.append(str(size))
                elif isinstance(v, str):
                    sizes.append(v)

            # Category detection
            category, subcategory = self.detect_category(name)
            gender = self.detect_gender(name, product_url)

            return ScrapedProduct(
                external_id=str(product_id),
                product_name=name,
                brand=self.normalize_brand(brand),
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                model=self.extract_model_from_name(name, brand),
                category=category,
                subcategory=subcategory,
                gender=gender,
                sku=item.get("sku", ""),
                sizes_available=sizes,
                stock_available=len(sizes) > 0,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing END. product: {e}")
            return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Fallback browser scraping for END."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(self.get_sale_url(), wait_until="networkidle")

            # Wait for products to load
            await page.wait_for_selector("[data-testid='product-card'], .product-card", timeout=10000)

            # Extract product cards
            cards = await page.query_selector_all("[data-testid='product-card'], .product-card, .plp-product")

            for card in cards[:50]:  # Limit to 50 products
                try:
                    # Extract data from card
                    name_el = await card.query_selector("[data-testid='product-name'], .product-name, h3")
                    brand_el = await card.query_selector("[data-testid='product-brand'], .product-brand")
                    price_el = await card.query_selector("[data-testid='current-price'], .sale-price, .current-price")
                    original_el = await card.query_selector("[data-testid='original-price'], .original-price, .was-price")
                    link_el = await card.query_selector("a[href]")
                    img_el = await card.query_selector("img")

                    if not name_el or not price_el:
                        continue

                    name = await name_el.inner_text()
                    brand = await brand_el.inner_text() if brand_el else ""
                    price_text = await price_el.inner_text()
                    original_text = await original_el.inner_text() if original_el else ""
                    href = await link_el.get_attribute("href") if link_el else ""
                    img_src = await img_el.get_attribute("src") if img_el else ""

                    sale_price = self.parse_price(price_text)
                    original_price = self.parse_price(original_text) or sale_price

                    if not sale_price:
                        continue

                    product_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    category, subcategory = self.detect_category(name)

                    products.append(ScrapedProduct(
                        external_id=href.split("/")[-1] if href else name[:20],
                        product_name=name.strip(),
                        brand=self.normalize_brand(brand) if brand else "END.",
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
                    logger.debug(f"Error parsing END. card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"END. browser scraping error: {e}")

        return products
