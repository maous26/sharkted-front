"""Snipes scraper - Urban streetwear and sneakers."""
import logging
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class SnipesScraper(BaseScraper):
    """Scraper for Snipes France sale section."""

    SOURCE_NAME = "snipes"
    BASE_URL = "https://www.snipes.fr"
    CATEGORY = "sneakers"

    def get_sale_url(self) -> str:
        return f"{self.BASE_URL}/c/sale"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Snipes sale products."""
        products = []

        try:
            # Snipes uses Salesforce Commerce Cloud API
            api_url = f"{self.BASE_URL}/on/demandware.store/Sites-snipes-FR-Site/fr_FR/Search-UpdateGrid"
            params = {
                "cgid": "sale",
                "start": 0,
                "sz": 100,
                "format": "ajax",
            }

            headers = {
                "Accept": "*/*",
                "x-requested-with": "XMLHttpRequest",
            }

            try:
                response = await self._http_client.get(api_url, params=params, headers=headers)
                if response.status_code == 200:
                    # Try to parse as JSON first
                    try:
                        data = response.json()
                        products = self._parse_api_response(data)
                        if products:
                            return products
                    except:
                        # If not JSON, parse HTML
                        products = self._parse_html_response(response.text)
                        if products:
                            return products
            except Exception as e:
                logger.debug(f"Snipes API failed: {e}")

            # Fallback to browser
            products = await self._scrape_with_browser()

        except Exception as e:
            logger.error(f"Snipes scraping error: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[ScrapedProduct]:
        """Parse Snipes API response."""
        products = []

        items = data.get("products", []) or data.get("hits", [])

        for item in items:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing Snipes product: {e}")

        return products

    def _parse_html_response(self, html: str) -> List[ScrapedProduct]:
        """Parse Snipes HTML response."""
        products = []
        # Basic HTML parsing - in production would use BeautifulSoup
        # For now, return empty and rely on browser fallback
        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse single Snipes product."""
        try:
            product_id = item.get("productId") or item.get("id", "")
            name = item.get("productName", "") or item.get("name", "")
            brand = item.get("brand", "")

            # Prices
            price_data = item.get("price", {})
            if isinstance(price_data, dict):
                sale_price = float(price_data.get("sales", {}).get("value", 0) or price_data.get("sale", 0))
                original_price = float(price_data.get("list", {}).get("value", sale_price) or price_data.get("original", sale_price))
            else:
                sale_price = float(item.get("salePrice", 0) or item.get("price", 0))
                original_price = float(item.get("listPrice", sale_price))

            if not sale_price or sale_price <= 0:
                return None

            # URL
            url_path = item.get("productUrl", "") or item.get("url", "")
            product_url = f"{self.BASE_URL}{url_path}" if url_path and not url_path.startswith("http") else url_path

            # Image
            images = item.get("images", {})
            if isinstance(images, dict):
                image_url = images.get("large", [{}])[0].get("url", "") if images.get("large") else ""
            elif isinstance(images, list) and images:
                image_url = images[0].get("url", "") if isinstance(images[0], dict) else images[0]
            else:
                image_url = item.get("imageUrl", "") or item.get("image", "")

            # Sizes
            sizes = []
            variants = item.get("variationAttributes", [])
            for attr in variants:
                if attr.get("attributeId") == "size":
                    for val in attr.get("values", []):
                        if val.get("selectable", True):
                            sizes.append(val.get("displayValue", ""))

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
            logger.warning(f"Error parsing Snipes product: {e}")
            return None

    async def _scrape_with_browser(self) -> List[ScrapedProduct]:
        """Browser fallback for Snipes."""
        products = []

        try:
            page = await self.get_page()
            await page.goto(self.get_sale_url(), wait_until="networkidle")

            # Accept cookies if present
            try:
                cookie_btn = await page.query_selector("#onetrust-accept-btn-handler, .accept-cookies")
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            await page.wait_for_selector(".b-product-tile, .product-tile", timeout=10000)

            cards = await page.query_selector_all(".b-product-tile, .product-tile")

            for card in cards[:50]:
                try:
                    name_el = await card.query_selector(".b-product-tile-name, .product-name")
                    brand_el = await card.query_selector(".b-product-tile-brand, .product-brand")
                    price_el = await card.query_selector(".b-price-item--sale, .sale-price")
                    original_el = await card.query_selector(".b-price-item--original, .original-price")
                    link_el = await card.query_selector("a.b-product-tile-link, a[href]")
                    img_el = await card.query_selector("img.b-product-tile-image, img")

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
                        external_id=href.split("/")[-1].split(".")[0] if href else name[:20],
                        product_name=name.strip(),
                        brand=self.normalize_brand(brand) if brand else "Snipes",
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
                    logger.debug(f"Error parsing Snipes card: {e}")

            await page.close()

        except Exception as e:
            logger.error(f"Snipes browser error: {e}")

        return products
