"""BSTN scraper - German premium sneaker retailer."""
import logging
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class BstnScraper(BaseScraper):
    """Scraper for BSTN sale section."""

    SOURCE_NAME = "bstn"
    BASE_URL = "https://www.bstn.com"
    CATEGORY = "sneakers"

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/fr/sale"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape BSTN sale products."""
        products = []

        try:
            # BSTN has a REST API
            api_url = f"{self.BASE_URL}/api/catalog/products"
            params = {
                "category": "sale",
                "locale": "fr",
                "limit": 100,
            }

            headers = {
                "Accept": "application/json",
            }

            try:
                response = await self._http_client.get(api_url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    products = self._parse_api_response(data)
                    if products:
                        return products
            except Exception as e:
                logger.debug(f"BSTN API failed: {e}")

            # Fallback to browser
            products = await self._scrape_with_browser()

        except Exception as e:
            logger.error(f"BSTN scraping error: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[ScrapedProduct]:
        """Parse BSTN API response."""
        products = []

        items = data.get("products", []) or data.get("items", []) or data.get("data", [])

        for item in items:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing BSTN product: {e}")

        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse single BSTN product."""
        try:
            product_id = item.get("sku") or item.get("id", "")
            name = item.get("name", "") or item.get("title", "")
            brand = item.get("brand", {}).get("name", "") if isinstance(item.get("brand"), dict) else item.get("brand", "")

            # Prices
            price_data = item.get("price", {})
            if isinstance(price_data, dict):
                sale_price = float(price_data.get("current", 0) or price_data.get("sale", 0))
                original_price = float(price_data.get("original", sale_price) or price_data.get("regular", sale_price))
            else:
                sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
                original_price = float(item.get("originalPrice", sale_price))

            if not sale_price or sale_price <= 0:
                return None

            # URL
            slug = item.get("slug", "") or item.get("url", "")
            product_url = f"{self.BASE_URL}/fr/p/{slug}" if slug and not slug.startswith("http") else slug or ""

            # Image
            images = item.get("images", []) or item.get("media", [])
            image_url = ""
            if images:
                if isinstance(images[0], dict):
                    image_url = images[0].get("url", "") or images[0].get("src", "")
                else:
                    image_url = images[0]

            # Sizes
            sizes = []
            variants = item.get("variants", []) or item.get("sizes", [])
            for v in variants:
                if isinstance(v, dict):
                    if v.get("available", True) or v.get("inStock", True):
                        size = v.get("size", "") or v.get("name", "")
                        if size:
                            sizes.append(str(size))

            category, subcategory = self.detect_category(name)

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
                gender=self.detect_gender(name, product_url),
                sku=str(product_id),
                sizes_available=sizes,
                stock_available=len(sizes) > 0,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing BSTN product: {e}")
            return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Browser fallback for BSTN."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(self.get_sale_url(), wait_until="networkidle")

            await page.wait_for_selector("[data-testid='product-tile'], .product-tile", timeout=10000)

            cards = await page.query_selector_all("[data-testid='product-tile'], .product-tile, .product-card")

            for card in cards[:50]:
                try:
                    name_el = await card.query_selector("[data-testid='product-name'], .product-name, h3")
                    brand_el = await card.query_selector("[data-testid='product-brand'], .product-brand")
                    price_el = await card.query_selector("[data-testid='sale-price'], .sale-price")
                    original_el = await card.query_selector("[data-testid='original-price'], .original-price")
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
                        brand=self.normalize_brand(brand) if brand else "BSTN",
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
                    logger.debug(f"Error parsing BSTN card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"BSTN browser error: {e}")

        return products
