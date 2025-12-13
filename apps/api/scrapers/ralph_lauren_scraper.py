"""Ralph Lauren FR scraper for sale products."""
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class RalphLaurenScraper(BaseScraper):
    """Scraper for Ralph Lauren FR sale section."""

    SOURCE_NAME = "ralph_lauren"
    BASE_URL = "https://www.ralphlauren.fr"
    CATEGORY = "textile"

    def get_sale_url(self) -> str:
        """Get Ralph Lauren sale page URL."""
        return f"{self.BASE_URL}/fr/soldes"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Ralph Lauren sale products."""
        products = []

        # Scrape different sale categories
        sale_urls = [
            f"{self.BASE_URL}/fr/hommes/soldes",
            f"{self.BASE_URL}/fr/femmes/soldes",
            f"{self.BASE_URL}/fr/hommes/soldes/polos",
            f"{self.BASE_URL}/fr/hommes/soldes/chemises",
            f"{self.BASE_URL}/fr/hommes/soldes/pulls-et-cardigans",
            f"{self.BASE_URL}/fr/femmes/soldes/polos",
            f"{self.BASE_URL}/fr/hommes/soldes/casquettes-et-chapeaux",
        ]

        for url in sale_urls:
            try:
                page_products = await self._scrape_page(url)
                products.extend(page_products)
            except Exception as e:
                logger.warning(f"Error scraping Ralph Lauren URL {url}: {e}")

        # Remove duplicates
        seen = set()
        unique_products = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique_products.append(p)

        return unique_products

    async def _scrape_page(self, url: str) -> List[ScrapedProduct]:
        """Scrape a single Ralph Lauren category page."""
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

            # Handle country selector if present
            try:
                country_modal = await page.query_selector('.country-selector-modal')
                if country_modal:
                    france_btn = await page.query_selector('[data-country="FR"]')
                    if france_btn:
                        await france_btn.click()
                        await page.wait_for_timeout(500)
            except Exception:
                pass

            # Scroll to load more products
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            # Get product cards - RL uses various selectors
            product_cards = await page.query_selector_all('.product-tile, .product-item, [data-component="product-tile"]')

            for card in product_cards[:100]:
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing Ralph Lauren product card: {e}")

        except Exception as e:
            logger.error(f"Ralph Lauren scraping error for {url}: {e}")
        finally:
            await page.close()

        return products

    async def _parse_product_card(self, card) -> Optional[ScrapedProduct]:
        """Parse a product card element from Ralph Lauren website."""
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
            match = re.search(r'/(\d+)\.html', href)
            if match:
                external_id = match.group(1)
            else:
                # Try to extract from data attribute
                external_id = await card.get_attribute("data-product-id")
                if not external_id:
                    external_id = href.split("/")[-1].replace(".html", "")

            # Get product name
            name_el = await card.query_selector('.product-name, .product-tile-name, [class*="product-name"]')
            product_name = await name_el.inner_text() if name_el else "Unknown"
            product_name = product_name.strip()

            # Full name with brand
            full_name = f"Ralph Lauren {product_name}"

            # Get prices
            sale_price_el = await card.query_selector('.sale-price, .price-sale, [class*="sale-price"]')
            original_price_el = await card.query_selector('.original-price, .price-original, .strike-through, [class*="original-price"]')

            if not sale_price_el:
                # Try to find any price element
                sale_price_el = await card.query_selector('.price, [class*="price"]')

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
            category, subcategory = self._detect_rl_category(full_name)

            return ScrapedProduct(
                external_id=external_id,
                product_name=full_name,
                brand="Ralph Lauren",
                model=None,  # RL doesn't really have models
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
            logger.warning(f"Error parsing Ralph Lauren card: {e}")
            return None

    def _detect_rl_category(self, product_name: str) -> tuple[str, str]:
        """Detect category for Ralph Lauren products."""
        name_lower = product_name.lower()

        # Polos - very popular for resale
        if "polo" in name_lower:
            return "textile", "polos"

        # Shirts
        if any(kw in name_lower for kw in ["chemise", "shirt", "oxford"]):
            return "textile", "shirts"

        # Knitwear
        if any(kw in name_lower for kw in ["pull", "sweater", "cardigan", "tricot"]):
            return "textile", "knitwear"

        # Caps - also popular
        if any(kw in name_lower for kw in ["casquette", "cap", "chapeau", "hat"]):
            return "accessoires", "caps"

        # T-shirts
        if any(kw in name_lower for kw in ["t-shirt", "tee"]):
            return "textile", "tshirts"

        # Jackets
        if any(kw in name_lower for kw in ["veste", "jacket", "blouson", "manteau"]):
            return "textile", "jackets"

        # Pants
        if any(kw in name_lower for kw in ["pantalon", "pants", "chino", "jean"]):
            return "textile", "pants"

        # Default to premium category
        return "textile", "premium"
