"""Scrapers for retail sources."""
from .base_scraper import BaseScraper, ScrapedProduct
from .nike_scraper import NikeScraper
from .adidas_scraper import AdidasScraper
from .zalando_scraper import ZalandoScraper
from .courir_scraper import CourirScraper
from .footlocker_scraper import FootLockerScraper
from .ralph_lauren_scraper import RalphLaurenScraper
# Pro scrapers
from .end_scraper import EndScraper
from .size_scraper import SizeScraper
from .bstn_scraper import BstnScraper
from .snipes_scraper import SnipesScraper
from .yoox_scraper import YooxScraper
from .laredoute_scraper import LaRedouteScraper
# New textile scrapers
from .kith_scraper import KithScraper
from .printemps_scraper import PrintempsScraper
# Brand utilities
from .premium_brands import is_attractive_brand, get_brand_tier, normalize_brand_name, ATTRACTIVE_BRANDS

# Registry of available scrapers - FREE tier
SCRAPERS_FREE = {
    "nike": NikeScraper,
    "adidas": AdidasScraper,
    "zalando": ZalandoScraper,
    "courir": CourirScraper,
    "footlocker": FootLockerScraper,
    "ralph_lauren": RalphLaurenScraper,
}

# PRO tier scrapers (additional sources)
SCRAPERS_PRO = {
    "end": EndScraper,
    "size": SizeScraper,
    "bstn": BstnScraper,
    "snipes": SnipesScraper,
    "yoox": YooxScraper,
    "laredoute": LaRedouteScraper,
    # New textile sources
    "kith": KithScraper,
    "printemps": PrintempsScraper,
}

# All scrapers combined
SCRAPERS = {**SCRAPERS_FREE, **SCRAPERS_PRO}

__all__ = [
    "BaseScraper",
    "ScrapedProduct",
    # Free scrapers
    "NikeScraper",
    "AdidasScraper",
    "ZalandoScraper",
    "CourirScraper",
    "FootLockerScraper",
    "RalphLaurenScraper",
    # Pro scrapers
    "EndScraper",
    "SizeScraper",
    "BstnScraper",
    "SnipesScraper",
    "YooxScraper",
    "LaRedouteScraper",
    # New textile scrapers
    "KithScraper",
    "PrintempsScraper",
    # Brand utilities
    "is_attractive_brand",
    "get_brand_tier",
    "normalize_brand_name",
    "ATTRACTIVE_BRANDS",
    # Registries
    "SCRAPERS",
    "SCRAPERS_FREE",
    "SCRAPERS_PRO",
]
