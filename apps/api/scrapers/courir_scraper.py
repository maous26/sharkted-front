"""Courir FR scraper for sale products."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class CourirScraper(BaseScraper):
    """Scraper for Courir FR sale section."""

    SOURCE_NAME = "courir"
    BASE_URL = "https://www.courir.com"
    CATEGORY = "sneakers"

    def get_sale_url(self) -> str:
        """Get Courir sale page URL."""
        return f"{self.BASE_URL}/c/soldes/"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Courir sale products."""
        products = []

        # Scrape multiple sale categories
        sale_urls = [
            f"{self.BASE_URL}/c/soldes/",
            f"{self.BASE_URL}/c/soldes-homme/",
            f"{self.BASE_URL}/c/soldes-femme/",
        ]

        for url in sale_urls:
            try:
                page_products = await self._scrape_page(url)
                products.extend(page_products)
            except Exception as e:
                logger.warning(f"Error scraping Courir URL {url}: {e}")

        # Remove duplicates
        seen = set()
        unique_products = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique_products.append(p)

        return unique_products

    async def _scrape_page(self, url: str) -> List[ScrapedProduct]:
        """Scrape a single Courir category page."""
        products = []
        page = await self.get_page()

        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector('#onetrust-accept-btn-handler')
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
            product_cards = await page.query_selector_all('.product-tile')

            for card in product_cards[:100]:
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing Courir product card: {e}")

        except Exception as e:
            logger.error(f"Courir scraping error for {url}: {e}")
        finally:
            await page.close()

        return products

    async def _parse_product_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card element from Courir website."""
        try:
            # Get link
            link = await card.query_selector("a.product-tile-link")
            if not link:
                link = await card.query_selector("a")
            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

            # Extract product ID from URL
            match = re.search(r'/([A-Z0-9-]+)\.html', href, re.IGNORECASE)
            if match:
                external_id = match.group(1)
            else:
                external_id = href.split("/")[-1].replace(".html", "")

            # Get brand
            brand_el = await card.query_selector('.product-tile-brand')
            brand = await brand_el.inner_text() if brand_el else "Unknown"
            brand = brand.strip()

            # Get product name
            name_el = await card.query_selector('.product-tile-name')
            product_name = await name_el.inner_text() if name_el else "Unknown"
            product_name = product_name.strip()

            # Full name with brand
            full_name = f"{brand} {product_name}".strip()

            # Get prices
            sale_price_el = await card.query_selector('.product-tile-price-sale, .price-sale')
            original_price_el = await card.query_selector('.product-tile-price-original, .price-original')

            if not sale_price_el:
                # Try alternative selectors
                sale_price_el = await card.query_selector('.product-tile-price')

            if not sale_price_el:
                return None

            sale_price_text = await sale_price_el.inner_text()
            sale_price = self.parse_price(sale_price_text)

            if original_price_el:
                original_price_text = await original_price_el.inner_text()
                original_price = self.parse_price(original_price_text)
            else:
                original_price = sale_price

            if not sale_price or sale_price >= original_price:
                return None

            # Get image
            img_el = await card.query_selector("img")
            image_url = None
            if img_el:
                image_url = await img_el.get_attribute("src")
                if not image_url:
                    image_url = await img_el.get_attribute("data-src")

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
            logger.warning(f"Error parsing Courir card: {e}")
            return None
