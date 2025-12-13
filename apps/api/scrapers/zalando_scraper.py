"""Zalando FR scraper for sale products."""
import logging
import json
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class ZalandoScraper(BaseScraper):
    """Scraper for Zalando FR sale section."""

    SOURCE_NAME = "zalando"
    BASE_URL = "https://www.zalando.fr"
    CATEGORY = "sneakers"

    def get_sale_url(self) -> str:
        """Get Zalando sale page URL."""
        return f"{self.BASE_URL}/promo-chaussures-homme/"

    async def scrape_sales(self) -> List[ScrapedProduct]:
        """Scrape Zalando sale products."""
        products = []

        # Scrape different sale categories
        sale_urls = [
            f"{self.BASE_URL}/promo-chaussures-homme/",
            f"{self.BASE_URL}/promo-chaussures-femme/",
            f"{self.BASE_URL}/promo-baskets-homme/",
            f"{self.BASE_URL}/promo-baskets-femme/",
        ]

        for url in sale_urls:
            try:
                page_products = await self._scrape_page(url)
                products.extend(page_products)
            except Exception as e:
                logger.warning(f"Error scraping Zalando URL {url}: {e}")

        # Remove duplicates
        seen = set()
        unique_products = []
        for p in products:
            if p.external_id not in seen:
                seen.add(p.external_id)
                unique_products.append(p)

        return unique_products

    async def _scrape_page(self, url: str) -> List[ScrapedProduct]:
        """Scrape a single Zalando category page."""
        products = []
        page = await self.get_page()

        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector('[data-testid="uc-accept-all-button"]')
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Scroll to load more products
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            # Try to extract data from page JSON
            try:
                # Zalando embeds product data in script tags
                script_content = await page.evaluate('''
                    () => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const script of scripts) {
                            const data = JSON.parse(script.textContent);
                            if (data['@type'] === 'ItemList') {
                                return JSON.stringify(data);
                            }
                        }
                        return null;
                    }
                ''')

                if script_content:
                    data = json.loads(script_content)
                    items = data.get("itemListElement", [])
                    for item in items:
                        product = self._parse_json_ld_product(item)
                        if product:
                            products.append(product)
                    return products
            except Exception as e:
                logger.debug(f"Could not parse Zalando JSON-LD: {e}")

            # Fallback to DOM scraping
            product_cards = await page.query_selector_all('[data-zalon-partner-target="true"]')
            if not product_cards:
                product_cards = await page.query_selector_all('article[class*="product"]')

            for card in product_cards[:100]:
                try:
                    product = await self._parse_product_card(card, page)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing Zalando product card: {e}")

        except Exception as e:
            logger.error(f"Zalando scraping error for {url}: {e}")
        finally:
            await page.close()

        return products

    def _parse_json_ld_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Parse product from JSON-LD data."""
        try:
            product_data = item.get("item", {})
            if not product_data:
                return None

            offers = product_data.get("offers", {})
            price = offers.get("price")
            if not price:
                return None

            # Check for sale (look for crossed out price in name or description)
            name = product_data.get("name", "Unknown")
            url = product_data.get("url", "")
            image = product_data.get("image", "")

            # Extract product ID from URL
            external_id = url.split("/")[-1].replace(".html", "") if url else ""

            # Detect brand
            brand = product_data.get("brand", {}).get("name", "")
            if not brand:
                brand = self._detect_brand_from_name(name)

            # Detect attributes
            gender = self.detect_gender(name, url)
            category, subcategory = self.detect_category(name)
            model = self.extract_model_from_name(name, brand) if brand else None

            return ScrapedProduct(
                external_id=external_id,
                product_name=name,
                brand=self.normalize_brand(brand) if brand else "Unknown",
                model=model,
                original_price=float(price),  # Will need to find original price
                sale_price=float(price),
                discount_pct=None,
                product_url=url,
                image_url=image,
                gender=gender,
                category=category,
                subcategory=subcategory,
                sizes_available=[],
                stock_available=True,
            )
        except Exception as e:
            logger.warning(f"Error parsing Zalando JSON-LD product: {e}")
            return None

    async def _parse_product_card(self, card, page) -> Optional[ScrapedProduct]:
        """Parse a product card element from Zalando website."""
        try:
            # Get link
            link = await card.query_selector("a")
            if not link:
                return None

            href = await link.get_attribute("href")
            if not href:
                return None

            product_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

            # Extract product ID
            match = re.search(r"/([A-Z0-9-]+)\.html", href)
            external_id = match.group(1) if match else href.split("/")[-1]

            # Get product name
            name_el = await card.query_selector('[class*="product-name"], [class*="ProductName"]')
            if not name_el:
                name_el = await card.query_selector('h3, [class*="name"]')
            product_name = await name_el.inner_text() if name_el else "Unknown"

            # Get brand
            brand_el = await card.query_selector('[class*="brand"], [class*="Brand"]')
            brand = await brand_el.inner_text() if brand_el else self._detect_brand_from_name(product_name)

            # Get prices
            price_container = await card.query_selector('[class*="price"], [class*="Price"]')
            if not price_container:
                return None

            price_text = await price_container.inner_text()

            # Parse prices from text (format can be "59,99 € 89,99 €" or similar)
            prices = re.findall(r'(\d+[,.]?\d*)\s*€', price_text)
            if len(prices) >= 2:
                # First price is usually the sale price, second is original
                sale_price = self.parse_price(prices[0] + "€")
                original_price = self.parse_price(prices[1] + "€")
            elif len(prices) == 1:
                sale_price = self.parse_price(prices[0] + "€")
                original_price = sale_price
            else:
                return None

            if not sale_price or sale_price >= original_price:
                return None

            # Get image
            img_el = await card.query_selector("img")
            image_url = await img_el.get_attribute("src") if img_el else None

            # Detect attributes
            gender = self.detect_gender(product_name, product_url)
            category, subcategory = self.detect_category(product_name)
            model = self.extract_model_from_name(product_name, brand)

            return ScrapedProduct(
                external_id=external_id,
                product_name=product_name,
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
            logger.warning(f"Error parsing Zalando card: {e}")
            return None

    def _detect_brand_from_name(self, name: str) -> str:
        """Try to detect brand from product name."""
        brands = [
            "Nike", "Adidas", "New Balance", "Puma", "Reebok", "Asics",
            "Converse", "Vans", "Timberland", "Dr. Martens", "Clarks",
            "Tommy Hilfiger", "Calvin Klein", "Lacoste", "Geox", "Ecco",
        ]
        name_lower = name.lower()
        for brand in brands:
            if brand.lower() in name_lower:
                return brand
        return "Unknown"
