"""YOOX scraper - Luxury fashion outlet."""
import logging
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class YooxScraper(BaseScraper):
    """Scraper for YOOX sale section."""

    SOURCE_NAME = "yoox"
    BASE_URL = "https://www.yoox.com"
    CATEGORY = "textile"

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/fr/homme/soldes"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape YOOX sale products."""
        products = []

        try:
            # YOOX API endpoint
            api_url = f"{self.BASE_URL}/api/search"
            params = {
                "area": "salehomme",
                "page": 1,
                "limit": 100,
                "country": "FR",
                "lang": "fr",
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
                    if products:
                        return products
            except Exception as e:
                logger.debug(f"YOOX API failed: {e}")

            # Fallback to browser
            products = await self._scrape_with_browser()

        except Exception as e:
            logger.error(f"YOOX scraping error: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[ScrapedProduct]:
        """Parse YOOX API response."""
        products = []

        items = data.get("items", []) or data.get("products", []) or data.get("SearchResults", [])

        for item in items:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing YOOX product: {e}")

        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse single YOOX product."""
        try:
            product_id = item.get("cod10") or item.get("id", "")
            name = item.get("microCategory", "") or item.get("name", "") or item.get("description", "")
            brand = item.get("brand", {}).get("name", "") if isinstance(item.get("brand"), dict) else item.get("brand", "")

            # Prices
            price_data = item.get("formattedPrice", {}) or item.get("price", {})
            if isinstance(price_data, dict):
                sale_price = float(price_data.get("discountedPrice", "0").replace(",", ".").replace("€", "").strip() or 0)
                original_price = float(price_data.get("fullPrice", "0").replace(",", ".").replace("€", "").strip() or sale_price)
            else:
                sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
                original_price = float(item.get("originalPrice", sale_price))

            if not sale_price or sale_price <= 0:
                return None

            # URL
            product_url = f"{self.BASE_URL}/fr/item/{product_id}"

            # Image
            images = item.get("images", []) or item.get("defaultColorsImages", [])
            image_url = ""
            if images:
                if isinstance(images[0], dict):
                    image_url = images[0].get("url", "") or images[0].get("src", "")
                elif isinstance(images[0], str):
                    image_url = images[0]

            # Category
            category_info = item.get("microCategoryPlural", "") or item.get("category", "")
            category, subcategory = self.detect_category(f"{name} {category_info}")

            return ScrapedProduct(
                external_id=str(product_id),
                product_name=f"{brand} {name}".strip() if brand else name,
                brand=self.normalize_brand(brand) if brand else "YOOX",
                original_price=original_price,
                sale_price=sale_price,
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                model=name,
                category=category,
                subcategory=subcategory,
                gender="men",  # We're scraping men's sale
                sizes_available=[],
                stock_available=True,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing YOOX product: {e}")
            return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Browser fallback for YOOX."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(self.get_sale_url(), wait_until="networkidle")

            # Accept cookies
            try:
                cookie_btn = await page.query_selector("#onetrust-accept-btn-handler, .privacy-policy-accept")
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            await page.wait_for_selector(".item-data, .product-item, article[data-itemcode]", timeout=15000)

            cards = await page.query_selector_all(".item-data, .product-item, article[data-itemcode]")

            for card in cards[:50]:
                try:
                    brand_el = await card.query_selector(".brand-name, .brand, .item-brand")
                    name_el = await card.query_selector(".micro-category, .product-name, .item-category")
                    price_el = await card.query_selector(".discounted-price, .sale-price")
                    original_el = await card.query_selector(".full-price, .original-price")
                    link_el = await card.query_selector("a[href]")
                    img_el = await card.query_selector("img")

                    if not price_el:
                        continue

                    brand = await brand_el.inner_text() if brand_el else "YOOX"
                    name = await name_el.inner_text() if name_el else ""
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
                        product_name=f"{brand} {name}".strip(),
                        brand=self.normalize_brand(brand),
                        original_price=original_price,
                        sale_price=sale_price,
                        discount_pct=None,
                        product_url=product_url,
                        image_url=img_src,
                        category=category,
                        subcategory=subcategory,
                        gender="men",
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing YOOX card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"YOOX browser error: {e}")

        return products
