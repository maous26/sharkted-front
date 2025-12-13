"""
Configuration Sellshark - Variables d'environnement et settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    """Configuration de l'application Sellshark"""
    
    # Application
    APP_NAME: str = "Sellshark"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(default="your-super-secret-key-change-in-production", env="SECRET_KEY")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sellshark",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    
    # Scraping
    SCRAPE_INTERVAL_MINUTES: int = Field(default=10, env="SCRAPE_INTERVAL_MINUTES")
    PROXY_URL: str = Field(default="", env="PROXY_URL")
    WEBSHARE_PROXY_URL: str = Field(
        default="https://proxy.webshare.io/api/v2/proxy/list/download/vvdkytztqbtnmleqcuqblttmsdvnahqoayfgfypy/-/any/username/direct/-/",
        env="WEBSHARE_PROXY_URL"
    )
    MAX_CONCURRENT_SCRAPERS: int = Field(default=3, env="MAX_CONCURRENT_SCRAPERS")
    USE_ROTATING_PROXY: bool = Field(default=True, env="USE_ROTATING_PROXY")
    
    # Discord
    DISCORD_WEBHOOK_URL: str = Field(default="", env="DISCORD_WEBHOOK_URL")
    DISCORD_ALERT_THRESHOLD: int = Field(default=70, env="DISCORD_ALERT_THRESHOLD")
    
    # JWT Auth
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-change-in-production", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Vinted
    VINTED_API_BASE: str = "https://www.vinted.fr"
    VINTED_SEARCH_LIMIT: int = Field(default=50, env="VINTED_SEARCH_LIMIT")
    
    # Scoring thresholds
    MIN_MARGIN_PERCENT: float = Field(default=25.0, env="MIN_MARGIN_PERCENT")
    MIN_FLIP_SCORE: int = Field(default=60, env="MIN_FLIP_SCORE")
    HIGH_FLIP_SCORE: int = Field(default=80, env="HIGH_FLIP_SCORE")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Récupère les settings (cached)"""
    return Settings()

settings = get_settings()

# Sources de scraping configurées
SCRAPING_SOURCES = {
    "nike": {
        "name": "Nike",
        "base_url": "https://www.nike.com/fr/w/promotions",
        "enabled": True,
        "priority": 1,
        "categories": ["sneakers", "textile"]
    },
    "adidas": {
        "name": "Adidas",
        "base_url": "https://www.adidas.fr/outlet",
        "enabled": True,
        "priority": 1,
        "categories": ["sneakers", "textile"]
    },
    "zalando": {
        "name": "Zalando",
        "base_url": "https://www.zalando.fr/promo/",
        "enabled": True,
        "priority": 2,
        "categories": ["sneakers", "textile", "accessoires"]
    },
    "courir": {
        "name": "Courir",
        "base_url": "https://www.courir.com/fr/promotions/",
        "enabled": True,
        "priority": 2,
        "categories": ["sneakers"]
    },
    "footlocker": {
        "name": "Foot Locker",
        "base_url": "https://www.footlocker.fr/fr/sale/",
        "enabled": True,
        "priority": 2,
        "categories": ["sneakers"]
    },
    "ralph_lauren": {
        "name": "Ralph Lauren",
        "base_url": "https://www.ralphlauren.fr/fr/sale/",
        "enabled": True,
        "priority": 1,
        "categories": ["textile", "accessoires"]
    },
    # === PRO SOURCES ===
    "end": {
        "name": "END.",
        "base_url": "https://www.endclothing.com/fr/sale",
        "enabled": True,
        "priority": 1,
        "categories": ["sneakers", "textile", "accessoires"],
        "plan_required": "pro"
    },
    "size": {
        "name": "Size?",
        "base_url": "https://www.size.co.uk/sale/",
        "enabled": True,
        "priority": 1,
        "categories": ["sneakers", "textile"],
        "plan_required": "pro"
    },
    "bstn": {
        "name": "BSTN",
        "base_url": "https://www.bstn.com/fr/sale",
        "enabled": True,
        "priority": 1,
        "categories": ["sneakers", "textile"],
        "plan_required": "pro"
    },
    "snipes": {
        "name": "Snipes",
        "base_url": "https://www.snipes.fr/c/sale",
        "enabled": True,
        "priority": 2,
        "categories": ["sneakers", "textile"],
        "plan_required": "pro"
    },
    "yoox": {
        "name": "YOOX",
        "base_url": "https://www.yoox.com/fr/homme/soldes",
        "enabled": True,
        "priority": 2,
        "categories": ["textile", "accessoires"],
        "plan_required": "pro"
    },
    "laredoute": {
        "name": "La Redoute",
        "base_url": "https://www.laredoute.fr/prlst/vt_soldes.aspx",
        "enabled": True,
        "priority": 2,
        "categories": ["textile", "sneakers"],
        "plan_required": "pro"
    }
}

# Catégories et leurs poids pour le scoring
CATEGORY_WEIGHTS = {
    "sneakers_lifestyle": {
        "liquidity_weight": 0.9,
        "popularity_weight": 0.95,
        "margin_threshold": 25,
        "expected_sell_days": 7
    },
    "sneakers_running": {
        "liquidity_weight": 0.7,
        "popularity_weight": 0.6,
        "margin_threshold": 35,
        "expected_sell_days": 14
    },
    "textile_premium": {
        "liquidity_weight": 0.85,
        "popularity_weight": 0.8,
        "margin_threshold": 30,
        "expected_sell_days": 10
    },
    "textile_streetwear": {
        "liquidity_weight": 0.8,
        "popularity_weight": 0.85,
        "margin_threshold": 25,
        "expected_sell_days": 7
    },
    "accessoires": {
        "liquidity_weight": 0.75,
        "popularity_weight": 0.7,
        "margin_threshold": 20,
        "expected_sell_days": 14
    }
}

# Marques et leur tier de popularité
BRAND_TIERS = {
    # Tier S - Très haute demande
    "nike": {"tier": "S", "popularity_bonus": 1.2},
    "jordan": {"tier": "S", "popularity_bonus": 1.25},
    "adidas": {"tier": "S", "popularity_bonus": 1.15},
    
    # Tier A - Haute demande
    "ralph lauren": {"tier": "A", "popularity_bonus": 1.1},
    "new balance": {"tier": "A", "popularity_bonus": 1.1},
    "asics": {"tier": "A", "popularity_bonus": 1.05},
    "lacoste": {"tier": "A", "popularity_bonus": 1.05},
    
    # Tier B - Demande moyenne
    "puma": {"tier": "B", "popularity_bonus": 1.0},
    "reebok": {"tier": "B", "popularity_bonus": 1.0},
    "tommy hilfiger": {"tier": "B", "popularity_bonus": 1.0},
    "converse": {"tier": "B", "popularity_bonus": 1.0},
    
    # Tier C - Demande plus faible
    "fila": {"tier": "C", "popularity_bonus": 0.9},
    "le coq sportif": {"tier": "C", "popularity_bonus": 0.9},
}