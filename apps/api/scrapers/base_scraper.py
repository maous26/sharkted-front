"""Base scraper class for all retail sources."""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

import httpx
from playwright.async_api import async_playwright, Browser, Page

from config import settings
from services.proxy_service import (
    get_proxy_rotator,
    get_rotating_proxy,
    get_playwright_proxy_config,
    get_random_user_agent,
    get_default_headers,
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Represents a scraped product from a retail source."""

    external_id: str
    product_name: str
    brand: str
    original_price: Optional[float]
    sale_price: float
    discount_pct: Optional[float]
    product_url: str
    image_url: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    sku: Optional[str] = None
    sizes_available: List[str] = field(default_factory=list)
    stock_available: bool = True
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate discount percentage if not provided."""
        if self.discount_pct is None and self.original_price and self.sale_price:
            self.discount_pct = round(
                (1 - self.sale_price / self.original_price) * 100, 1
            )


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    # Override in subclass
    SOURCE_NAME: str = "base"
    BASE_URL: str = ""
    CATEGORY: str = "sneakers"  # Default category

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: int = 30000,
        headless: bool = True,
        use_rotating_proxy: bool = True,  # Utiliser le service de proxy centralisé
    ):
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.headless = headless
        self.use_rotating_proxy = use_rotating_proxy and settings.USE_ROTATING_PROXY
        self._browser: Optional[Browser] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._current_proxy: Optional[str] = None
        self._user_agent: str = get_random_user_agent()

    async def __aenter__(self):
        """Setup resources on context manager entry."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources on context manager exit."""
        await self.cleanup()

    async def setup(self):
        """Initialize browser and HTTP client with proxy support."""
        # Initialiser le rotateur de proxy si activé
        if self.use_rotating_proxy:
            try:
                rotator = await get_proxy_rotator()
                self._current_proxy = rotator.get_proxy_url()
                if self._current_proxy:
                    logger.info(f"[{self.SOURCE_NAME}] Proxy activé pour ce scraper")
            except Exception as e:
                logger.warning(f"[{self.SOURCE_NAME}] Impossible d'initialiser les proxies: {e}")
                self._current_proxy = None

        # Utiliser le proxy spécifié manuellement ou celui du rotateur
        proxy_to_use = self.proxy_url or self._current_proxy

        # Setup HTTP client avec headers réalistes
        client_kwargs = {
            "timeout": self.timeout / 1000,
            "follow_redirects": True,
            "headers": get_default_headers(for_api=False, referer=self.BASE_URL),
        }

        if proxy_to_use:
            client_kwargs["proxy"] = proxy_to_use

        self._http_client = httpx.AsyncClient(**client_kwargs)

    async def cleanup(self):
        """Cleanup browser and HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
        if self._browser:
            await self._browser.close()

    async def get_browser(self) -> Browser:
        """Get or create browser instance with proxy support."""
        if not self._browser:
            playwright = await async_playwright().start()
            launch_options = {
                "headless": self.headless,
            }

            # Configurer le proxy pour Playwright
            proxy_to_use = self.proxy_url or self._current_proxy
            if proxy_to_use:
                # Parser l'URL du proxy pour Playwright
                if "@" in proxy_to_use:
                    # Format: http://username:password@ip:port
                    auth_part, server_part = proxy_to_use.replace("http://", "").replace("https://", "").split("@")
                    username, password = auth_part.split(":")
                    launch_options["proxy"] = {
                        "server": f"http://{server_part}",
                        "username": username,
                        "password": password,
                    }
                else:
                    launch_options["proxy"] = {"server": proxy_to_use}

            self._browser = await playwright.chromium.launch(**launch_options)
        return self._browser

    async def get_page(self) -> Page:
        """Create a new browser page with stealth settings and rotating user agent."""
        browser = await self.get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self._user_agent,
            locale="fr-FR",
        )
        page = await context.new_page()
        page.set_default_timeout(self.timeout)
        return page

    async def fetch_html(self, url: str) -> str:
        """Fetch HTML content via HTTP client."""
        try:
            response = await self._http_client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise

    async def fetch_json(self, url: str, headers: Optional[Dict] = None) -> Dict:
        """Fetch JSON content via HTTP client."""
        try:
            response = await self._http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching JSON {url}: {e}")
            raise

    @abstractmethod
    async def scrape_sales(self) -> List[ScrapedProduct]:
        """
        Scrape sale products from the source.
        Must be implemented by subclasses.

        Returns:
            List of ScrapedProduct objects
        """
        pass

    @abstractmethod
    def get_sale_url(self) -> str:
        """
        Get the URL for the sale/promo page.
        Must be implemented by subclasses.
        """
        pass

    def parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float."""
        if not price_str:
            return None
        try:
            # Remove currency symbols and spaces
            cleaned = price_str.replace("€", "").replace(",", ".").replace(" ", "").strip()
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not parse price: {price_str}")
            return None

    def normalize_brand(self, brand: str) -> str:
        """Normalize brand name."""
        brand_map = {
            "nike": "Nike",
            "adidas": "Adidas",
            "new balance": "New Balance",
            "puma": "Puma",
            "reebok": "Reebok",
            "asics": "Asics",
            "converse": "Converse",
            "vans": "Vans",
            "jordan": "Jordan",
            "ralph lauren": "Ralph Lauren",
            "polo ralph lauren": "Ralph Lauren",
            "lacoste": "Lacoste",
            "tommy hilfiger": "Tommy Hilfiger",
        }
        return brand_map.get(brand.lower().strip(), brand.title())

    def extract_model_from_name(self, product_name: str, brand: str) -> Optional[str]:
        """Try to extract model name from product name."""
        # Remove brand from name
        name_lower = product_name.lower()
        brand_lower = brand.lower()
        name_without_brand = name_lower.replace(brand_lower, "").strip()

        # Common model patterns
        model_patterns = [
            "air max", "air force", "air jordan", "dunk", "blazer",
            "ultraboost", "nmd", "stan smith", "superstar", "gazelle", "campus",
            "574", "990", "993", "550", "2002r",
            "gel-kayano", "gel-lyte", "gel-nimbus",
            "classic leather", "club c",
        ]

        for pattern in model_patterns:
            if pattern in name_lower:
                return pattern.title()

        # Return first few words as model
        words = name_without_brand.split()
        if len(words) >= 2:
            return " ".join(words[:3]).title()

        return None

    def detect_gender(self, product_name: str, url: str = "") -> str:
        """Detect gender from product name or URL."""
        text = f"{product_name} {url}".lower()

        if any(w in text for w in ["homme", "men", "masculin", "man"]):
            return "men"
        elif any(w in text for w in ["femme", "women", "féminin", "woman"]):
            return "women"
        elif any(w in text for w in ["enfant", "kids", "junior", "gs", "child"]):
            return "kids"
        elif any(w in text for w in ["unisex", "unisexe"]):
            return "unisex"

        return "unisex"

    def detect_category(self, product_name: str) -> tuple[str, str]:
        """Detect category and subcategory from product name."""
        name_lower = product_name.lower()

        # Sneakers
        sneaker_keywords = ["sneaker", "shoe", "chaussure", "basket", "trainer"]
        if any(kw in name_lower for kw in sneaker_keywords):
            # Detect subcategory
            if any(kw in name_lower for kw in ["running", "course", "run"]):
                return "sneakers", "running"
            elif any(kw in name_lower for kw in ["basket", "jordan", "dunk"]):
                return "sneakers", "basketball"
            elif any(kw in name_lower for kw in ["trail", "outdoor"]):
                return "sneakers", "trail"
            else:
                return "sneakers", "lifestyle"

        # Textile
        textile_keywords = ["t-shirt", "tee", "polo", "shirt", "hoodie", "sweat", "jacket", "veste", "pantalon", "pants", "short"]
        if any(kw in name_lower for kw in textile_keywords):
            return "textile", "streetwear"

        # Accessories
        accessory_keywords = ["cap", "casquette", "bag", "sac", "belt", "ceinture", "hat", "chapeau"]
        if any(kw in name_lower for kw in accessory_keywords):
            if "cap" in name_lower or "casquette" in name_lower:
                return "accessoires", "caps"
            elif "bag" in name_lower or "sac" in name_lower:
                return "accessoires", "bags"
            return "accessoires", "other"

        return self.CATEGORY, "other"

    async def run(self) -> List[ScrapedProduct]:
        """Run the scraper with proper setup and cleanup."""
        try:
            await self.setup()
            products = await self.scrape_sales()
            logger.info(f"[{self.SOURCE_NAME}] Scraped {len(products)} products")
            return products
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] Scraper error: {e}")
            raise
        finally:
            await self.cleanup()
