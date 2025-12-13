"""Adidas FR scraper for sale products."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class AdidasScraper(BaseScraper):
    """Scraper for Adidas FR sale section."""

    SOURCE_NAME = "adidas"
    BASE_URL = "https://www.adidas.fr"
    CATEGORY = "sneakers"

    # Adidas API endpoint
    API_BASE = "https://www.adidas.fr/api/plp/content-engine"

    def get_sale_url(self) -> str:
        """Get Adidas sale page URL."""
        return f"{self.BASE_URL}/chaussures-promo"

    def _build_api_url(self, start: int = 0) -> str:
        """Build Adidas API URL for fetching products."""
        query_params = {
            "query": "chaussures-promo",
            "start": start,
        }
        query = "&".join([f"{k}={v}" for k, v in query_params.items()])
        return f"{self.API_BASE}?{query}"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Adidas sale products."""
        products = []

        try:
            # Try API first
            start = 0
            while True:
                url = self._build_api_url(start=start)

                try:
                    data = await self.fetch_json(url)
                except Exception as e:
                    logger.warning(f"Adidas API failed, using browser: {e}")
                    return await self._scrape_via_browser()

                if not data:
                    break

                items = data.get("raw", {}).get("itemList", {}).get("items", [])
                if not items:
                    break

                for item in items:
                    product = self._parse_api_product(item)
                    if product:
                        products.append(product)

                # Check pagination
                view_size = data.get("raw", {}).get("itemList", {}).get("viewSize", 48)
                total = data.get("raw", {}).get("itemList", {}).get("count", 0)

                start += view_size
                if start >= total or start > 500:
                    break

        except Exception as e:
            logger.error(f"Adidas scraping error: {e}")
            return await self._scrape_via_browser()

        return products

    def _parse_api_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse a product from Adidas API response."""
        try:
            # Check if on sale
            price = item.get("price", 0)
            sale_price = item.get("salePrice", price)

            if not sale_price or sale_price >= price:
                return None

            product_id = item.get("productId", "")
            model_id = item.get("modelId", "")

            # Get product details
            display_name = item.get("displayName", "Unknown")
            subtitle = item.get("subTitle", "")
            product_name = f"{display_name} {subtitle}".strip()

            # Build URL
            link = item.get("link", "")
            product_url = f"{self.BASE_URL}{link}" if link.startswith("/") else link

            # Get image
            image = item.get("image", {})
            image_url = image.get("src", "")

            # Get color
            color = item.get("colorVariations", [{}])[0].get("color", "") if item.get("colorVariations") else ""

            # Detect attributes
            gender = self.detect_gender(product_name, product_url)
            category, subcategory = self.detect_category(product_name)
            model = self.extract_model_from_name(product_name, "Adidas")

            return ScrapedProduct(
                external_id=product_id or model_id,
                product_name=product_name,
                brand="Adidas",
                model=model,
                original_price=float(price),
                sale_price=float(sale_price),
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                color=color,
                gender=gender,
                category=category,
                subcategory=subcategory,
                sku=model_id,
                sizes_available=[],
                stock_available=True,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing Adidas product: {e}")
            return None

    async def _scrape_via_browser(self) -> List[ScrapedProduct]:
        """Fallback: scrape Adidas via browser."""
        products = []
        page = await self.get_page()

        try:
            await page.goto(self.get_sale_url(), wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector('[data-testid="consent-modal-accept-btn"]')
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Scroll to load more products
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            # Get product cards
            product_cards = await page.query_selector_all('[data-testid="product-card"]')

            for card in product_cards[:100]:
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing Adidas product card: {e}")

        except Exception as e:
            logger.error(f"Adidas browser scraping error: {e}")
        finally:
            await page.close()

        return products

    async def _parse_product_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card element from Adidas website."""
        try:
            # Get link
            link = await card.query_selector("a")
            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

            # Extract product ID from URL
            match = re.search(r"/([A-Z0-9]+)\.html", href)
            external_id = match.group(1) if match else href.split("/")[-1]

            # Get product name
            title_el = await card.query_selector('[data-testid="product-card-title"]')
            product_name = await title_el.inner_text() if title_el else "Unknown"

            # Get prices
            sale_price_el = await card.query_selector('[data-testid="product-card-sale-price"]')
            original_price_el = await card.query_selector('[data-testid="product-card-price"]')

            if not sale_price_el:
                return None

            sale_price = self.parse_price(await sale_price_el.inner_text())
            original_price = self.parse_price(await original_price_el.inner_text()) if original_price_el else sale_price

            if not sale_price or sale_price >= original_price:
                return None

            # Get image
            img_el = await card.query_selector("img")
            image_url = await img_el.get_attribute("src") if img_el else None

            # Detect attributes
            gender = self.detect_gender(product_name, product_url)
            category, subcategory = self.detect_category(product_name)
            model = self.extract_model_from_name(product_name, "Adidas")

            return ScrapedProduct(
                external_id=external_id,
                product_name=product_name,
                brand="Adidas",
                model=model,
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
            logger.warning(f"Error parsing Adidas card: {e}")
            return None
