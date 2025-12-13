"""Size? scraper - UK sneaker retailer."""
import logging
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class SizeScraper(BaseScraper):
    """Scraper for Size? sale section."""

    SOURCE_NAME = "size"
    BASE_URL = "https://www.size.co.uk"
    CATEGORY = "sneakers"

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/sale/"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Size? sale products."""
        products = []

        try:
            # Size? uses JD Sports API
            api_url = f"{self.BASE_URL}/search/api/sli/category/sale"
            params = {
                "page": 1,
                "pageSize": 100,
                "sort": "relevance",
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
                logger.debug(f"Size? API failed: {e}")

            # Fallback to browser
            products = await self._scrape_with_browser()

        except Exception as e:
            logger.error(f"Size? scraping error: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[ScrapedProduct]:
        """Parse Size? API response."""
        products = []

        items = data.get("products", []) or data.get("items", [])

        for item in items:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing Size? product: {e}")

        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse single Size? product."""
        try:
            product_id = item.get("seoId") or item.get("id", "")
            name = item.get("name", "")
            brand = item.get("brand", "")

            # Prices (in GBP, convert to EUR approx)
            sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
            original_price = float(item.get("ticketPrice", sale_price) or sale_price)

            # Convert GBP to EUR (approximate)
            gbp_to_eur = 1.17
            sale_price = round(sale_price * gbp_to_eur, 2)
            original_price = round(original_price * gbp_to_eur, 2)

            if not sale_price or sale_price <= 0:
                return None

            # URL
            url_path = item.get("url", "") or item.get("seoUrl", "")
            product_url = f"{self.BASE_URL}{url_path}" if url_path else ""

            # Image
            image_url = item.get("image", "") or item.get("imageUrl", "")
            if image_url and not image_url.startswith("http"):
                image_url = f"https:{image_url}"

            # Sizes
            sizes = []
            for size_info in item.get("sizes", []):
                if isinstance(size_info, dict) and size_info.get("available"):
                    sizes.append(str(size_info.get("size", "")))
                elif isinstance(size_info, str):
                    sizes.append(size_info)

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
                sizes_available=sizes,
                stock_available=len(sizes) > 0,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing Size? product: {e}")
            return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Browser fallback for Size?."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(self.get_sale_url(), wait_until="networkidle")

            await page.wait_for_selector(".productListItem, .product-card", timeout=10000)

            cards = await page.query_selector_all(".productListItem, .product-card")

            for card in cards[:50]:
                try:
                    name_el = await card.query_selector(".itemTitle, .product-name")
                    price_el = await card.query_selector(".price .salePrice, .sale-price")
                    original_el = await card.query_selector(".price .ticketPrice, .original-price")
                    link_el = await card.query_selector("a[href]")
                    img_el = await card.query_selector("img")

                    if not name_el or not price_el:
                        continue

                    name = await name_el.inner_text()
                    price_text = await price_el.inner_text()
                    original_text = await original_el.inner_text() if original_el else ""
                    href = await link_el.get_attribute("href") if link_el else ""
                    img_src = await img_el.get_attribute("src") if img_el else ""

                    sale_price = self.parse_price(price_text.replace("£", ""))
                    original_price = self.parse_price(original_text.replace("£", "")) if original_text else sale_price

                    # Convert GBP to EUR
                    if sale_price:
                        sale_price = round(sale_price * 1.17, 2)
                    if original_price:
                        original_price = round(original_price * 1.17, 2)

                    if not sale_price:
                        continue

                    product_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    category, subcategory = self.detect_category(name)

                    products.append(ScrapedProduct(
                        external_id=href.split("/")[-1] if href else name[:20],
                        product_name=name.strip(),
                        brand="Size?",
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
                    logger.debug(f"Error parsing Size? card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"Size? browser error: {e}")

        return products
