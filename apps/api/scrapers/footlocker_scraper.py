"""Foot Locker FR scraper for sale products."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class FootLockerScraper(BaseScraper):
    """Scraper for Foot Locker FR sale section."""

    SOURCE_NAME = "footlocker"
    BASE_URL = "https://www.footlocker.fr"
    CATEGORY = "sneakers"

    # Foot Locker API endpoint
    API_BASE = "https://www.footlocker.fr/api/products/search"

    def get_sale_url(self) -> str:
        """Get Foot Locker sale page URL."""
        return f"{self.BASE_URL}/fr/category/soldes.html"

    def _build_api_url(self, page: int = 0) -> str:
        """Build Foot Locker API URL for fetching products."""
        params = {
            "query": "",
            "currentPage": page,
            "pageSize": 60,
            "sort": "sale",
            "categories": "soldes",
        }
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.API_BASE}?{query}"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Foot Locker sale products."""
        products = []

        try:
            # Try API first
            current_page = 0
            while True:
                url = self._build_api_url(page=current_page)

                try:
                    data = await self.fetch_json(url)
                except Exception as e:
                    logger.warning(f"Foot Locker API failed, using browser: {e}")
                    return await self._scrape_via_browser()

                if not data:
                    break

                items = data.get("products", [])
                if not items:
                    break

                for item in items:
                    product = self._parse_api_product(item)
                    if product:
                        products.append(product)

                # Check pagination
                pagination = data.get("pagination", {})
                total_pages = pagination.get("totalPages", 1)

                current_page += 1
                if current_page >= total_pages or current_page > 10:
                    break

        except Exception as e:
            logger.error(f"Foot Locker scraping error: {e}")
            return await self._scrape_via_browser()

        return products

    def _parse_api_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse a product from Foot Locker API response."""
        try:
            # Get pricing
            price_info = item.get("price", {})
            original_price = price_info.get("originalPrice", {}).get("value", 0)
            sale_price = price_info.get("value", original_price)

            if not sale_price or sale_price >= original_price:
                return None

            product_id = item.get("sku", "")
            name = item.get("name", "Unknown")

            # Get brand
            brand = item.get("brand", "")

            # Build URL
            url = item.get("url", "")
            product_url = f"{self.BASE_URL}{url}" if url.startswith("/") else url

            # Get image
            images = item.get("images", [])
            image_url = images[0].get("url", "") if images else ""

            # Get color
            color = item.get("colorDescription", "")

            # Detect attributes
            gender = self.detect_gender(name, product_url)
            category, subcategory = self.detect_category(name)
            model = self.extract_model_from_name(name, brand) if brand else None

            return ScrapedProduct(
                external_id=product_id,
                product_name=name,
                brand=self.normalize_brand(brand) if brand else "Unknown",
                model=model,
                original_price=float(original_price),
                sale_price=float(sale_price),
                discount_pct=None,
                product_url=product_url,
                image_url=image_url,
                color=color,
                gender=gender,
                category=category,
                subcategory=subcategory,
                sku=product_id,
                sizes_available=[],
                stock_available=True,
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"Error parsing Foot Locker product: {e}")
            return None

    async def _scrape_via_browser(self) -> List[ScrapedProduct]:
        """Fallback: scrape Foot Locker via browser."""
        products = []
        page = await self.get_page()

        try:
            await page.goto(self.get_sale_url(), wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector('#consent-tracking')
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
            product_cards = await page.query_selector_all('.ProductCard, .product-card')

            for card in product_cards[:100]:
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing Foot Locker product card: {e}")

        except Exception as e:
            logger.error(f"Foot Locker browser scraping error: {e}")
        finally:
            await page.close()

        return products

    async def _parse_product_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card element from Foot Locker website."""
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
            match = re.search(r'/product/[^/]+/([A-Z0-9]+)', href, re.IGNORECASE)
            if match:
                external_id = match.group(1)
            else:
                external_id = href.split("/")[-1].replace(".html", "")

            # Get product name
            name_el = await card.query_selector('.ProductName, .product-name')
            product_name = await name_el.inner_text() if name_el else "Unknown"

            # Get brand
            brand_el = await card.query_selector('.ProductBrand, .product-brand')
            brand = await brand_el.inner_text() if brand_el else "Unknown"

            full_name = f"{brand} {product_name}".strip()

            # Get prices
            sale_price_el = await card.query_selector('.ProductPrice--sale, .price--sale')
            original_price_el = await card.query_selector('.ProductPrice--original, .price--original')

            if not sale_price_el:
                sale_price_el = await card.query_selector('.ProductPrice, .price')

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
            gender = self.detect_gender(full_name, product_url)
            category, subcategory = self.detect_category(full_name)
            model = self.extract_model_from_name(full_name, brand)

            return ScrapedProduct(
                external_id=external_id,
                product_name=full_name,
                brand=self.normalize_brand(brand),
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
            logger.warning(f"Error parsing Foot Locker card: {e}")
            return None
