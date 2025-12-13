"""Nike FR scraper for sale products."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class NikeScraper(BaseScraper):
    """Scraper for Nike FR sale section."""

    SOURCE_NAME = "nike"
    BASE_URL = "https://www.nike.com/fr"
    CATEGORY = "sneakers"

    # Nike API endpoints
    API_BASE = "https://api.nike.com"
    SALE_ENDPOINT = "/cic/browse/v2"

    def get_sale_url(self) -> str:
        """Get Nike sale page URL."""
        return f"{self.BASE_URL}/w/promos-chaussures"

    def _build_api_url(self, anchor: int = 0, count: int = 60) -> str:
        """Build Nike API URL for fetching products."""
        # Nike uses a specific API for product listing
        params = {
            "queryid": "products",
            "anonymousId": "auto",
            "country": "fr",
            "endpoint": "/product_feed/rollup_threads/v2",
            "language": "fr",
            "localizedRangeStr": "{lowestPrice} — {highestPrice}",
            "anchor": anchor,
            "consumerChannelId": "d9a5bc42-4b9c-4976-858a-f159cf99c647",
            "count": count,
        }

        # Filter for sale items (shoes)
        filter_params = [
            "marketplace=FR",
            "language=fr",
            "attributeIds=16633190-45e5-4830-a068-232ac7aea82c",  # Chaussures
            "attributeIds=0f64ecc7-d624-4e91-b171-b83a03dd8550",  # Promo
        ]

        query = "&".join([f"{k}={v}" for k, v in params.items()])
        query += "&" + "&".join(filter_params)

        return f"{self.API_BASE}{self.SALE_ENDPOINT}?{query}"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Nike sale products via API."""
        products = []
        anchor = 0
        count = 60

        try:
            while True:
                url = self._build_api_url(anchor=anchor, count=count)

                headers = {
                    "Accept": "application/json",
                    "Nike-Api-Caller-Id": "com.nike.commerce.nikedotcom.web",
                }

                try:
                    data = await self.fetch_json(url, headers=headers)
                except Exception as e:
                    logger.warning(f"Nike API request failed, trying web scraping: {e}")
                    return await self._scrape_via_browser()

                if not data or "objects" not in data:
                    break

                objects = data.get("objects", [])
                if not objects:
                    break

                for obj in objects:
                    product = self._parse_api_product(obj)
                    if product and product.sale_price < product.original_price:
                        products.append(product)

                # Check if more products available
                pages = data.get("pages", {})
                total_pages = pages.get("totalPages", 1)
                current_page = pages.get("currentPage", 1)

                if current_page >= total_pages:
                    break

                anchor += count

                # Safety limit
                if anchor > 500:
                    break

        except Exception as e:
            logger.error(f"Nike scraping error: {e}")
            # Fallback to browser scraping
            return await self._scrape_via_browser()

        return products

    def _parse_api_product(self, obj: dict) -> Optional[ScrapedProduct]:
        """Parse a product object from Nike API response."""
        try:
            product_info = obj.get("productInfo", [{}])[0]
            if not product_info:
                return None

            # Get pricing
            price_obj = product_info.get("merchPrice", {})
            current_price = price_obj.get("currentPrice", 0)
            full_price = price_obj.get("fullPrice", current_price)

            # Skip if not on sale
            if current_price >= full_price:
                return None

            # Extract product details
            product_id = product_info.get("merchProduct", {}).get("id", "")
            style_color = product_info.get("merchProduct", {}).get("styleColor", "")

            # Get product name and subtitle
            title = obj.get("publishedContent", {}).get("properties", {}).get("title", "")
            subtitle = obj.get("publishedContent", {}).get("properties", {}).get("subtitle", "")

            if not title:
                title = product_info.get("productContent", {}).get("title", "Unknown")

            product_name = f"{title} {subtitle}".strip()

            # Get color
            color_desc = product_info.get("productContent", {}).get("colorDescription", "")

            # Get image
            images = obj.get("publishedContent", {}).get("properties", {}).get("portraitURL", "")
            if not images:
                images = obj.get("publishedContent", {}).get("properties", {}).get("squarishURL", "")

            # Get available sizes
            skus = product_info.get("availableGtins", [])
            sizes = []
            for sku_info in product_info.get("skus", []):
                if sku_info.get("available", False):
                    size = sku_info.get("countrySpecifications", [{}])
                    if size:
                        sizes.append(size[0].get("localizedSize", ""))

            # Build product URL
            url_slug = obj.get("publishedContent", {}).get("properties", {}).get("seo", {}).get("slug", "")
            product_url = f"{self.BASE_URL}/t/{url_slug}/{style_color}"

            # Detect gender and category
            gender = self.detect_gender(product_name, product_url)
            category, subcategory = self.detect_category(product_name)

            # Extract model
            model = self.extract_model_from_name(product_name, "Nike")

            return ScrapedProduct(
                external_id=product_id or style_color,
                product_name=product_name,
                brand="Nike",
                model=model,
                original_price=float(full_price),
                sale_price=float(current_price),
                discount_pct=None,  # Will be calculated
                product_url=product_url,
                image_url=images,
                color=color_desc,
                gender=gender,
                category=category,
                subcategory=subcategory,
                sku=style_color,
                sizes_available=sizes,
                stock_available=len(sizes) > 0,
                raw_data=obj,
            )
        except Exception as e:
            logger.warning(f"Error parsing Nike product: {e}")
            return None

    async def _scrape_via_browser(self) -> List[ScrapedProduct]:
        """Fallback: scrape Nike via browser when API fails."""
        products = []
        page = await self.get_page()

        try:
            await page.goto(self.get_sale_url(), wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Scroll to load more products
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            # Get product cards
            product_cards = await page.query_selector_all('[data-testid="product-card"]')

            for card in product_cards[:100]:  # Limit to 100 products
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing Nike product card: {e}")

        except Exception as e:
            logger.error(f"Nike browser scraping error: {e}")
        finally:
            await page.close()

        return products

    async def _parse_product_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card element from Nike website."""
        try:
            # Get link and extract product ID
            link = await card.query_selector("a")
            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = f"https://www.nike.com{href}" if href.startswith("/") else href

            # Extract product ID from URL
            external_id = href.split("/")[-1] if "/" in href else href

            # Get product name
            title_el = await card.query_selector('[data-testid="product-card__title"]')
            product_name = await title_el.inner_text() if title_el else "Unknown"

            # Get subtitle (model info)
            subtitle_el = await card.query_selector('[data-testid="product-card__subtitle"]')
            subtitle = await subtitle_el.inner_text() if subtitle_el else ""

            full_name = f"{product_name} {subtitle}".strip()

            # Get prices
            current_price_el = await card.query_selector('[data-testid="product-price-reduced"]')
            original_price_el = await card.query_selector('[data-testid="product-price"]')

            if not current_price_el:
                return None  # Not on sale

            current_price = self.parse_price(await current_price_el.inner_text())
            original_price = self.parse_price(await original_price_el.inner_text()) if original_price_el else current_price

            if not current_price or current_price >= original_price:
                return None

            # Get image
            img_el = await card.query_selector("img")
            image_url = await img_el.get_attribute("src") if img_el else None

            # Detect attributes
            gender = self.detect_gender(full_name, product_url)
            category, subcategory = self.detect_category(full_name)
            model = self.extract_model_from_name(full_name, "Nike")

            return ScrapedProduct(
                external_id=external_id,
                product_name=full_name,
                brand="Nike",
                model=model,
                original_price=original_price,
                sale_price=current_price,
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
            logger.warning(f"Error parsing Nike card: {e}")
            return None
