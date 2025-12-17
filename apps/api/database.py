"""
Sellshark Database - Modèles SQLAlchemy et connexion async
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, JSON, 
    ForeignKey, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
from typing import Optional, List
import uuid
import enum

from config import settings

# Engine async
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    echo=settings.DEBUG
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Alias pour compatibilité
async_session = AsyncSessionLocal

# Base class
class Base(DeclarativeBase):
    pass

# Dependency pour FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ============= ENUMS =============

class DealStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SOLD_OUT = "sold_out"
    ARCHIVED = "archived"

class ActionType(str, enum.Enum):
    BOUGHT = "bought"
    IGNORED = "ignored"
    WATCHED = "watched"

class RecommendedAction(str, enum.Enum):
    BUY = "buy"
    WATCH = "watch"
    IGNORE = "ignore"

class PlanType(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    AGENCY = "agency"

# ============= MODELS =============

class Deal(Base):
    """Deals détectés (produits en promo)"""
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # Identité produit
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    color: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[Optional[str]] = mapped_column(String(20))

    # Prix
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    original_price: Mapped[Optional[float]] = mapped_column(Float)
    discount_percent: Mapped[Optional[float]] = mapped_column(Float)

    # Tailles (JSONB in DB)
    sizes_available: Mapped[Optional[dict]] = mapped_column(JSON)

    # URLs et images
    url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)

    # Seller info
    seller_name: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))

    # Status
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    score: Mapped[Optional[float]] = mapped_column(Float)

    # Raw data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Timestamps
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    price_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relations
    vinted_stats: Mapped[Optional["VintedStats"]] = relationship("VintedStats", back_populates="deal", uselist=False)
    deal_score: Mapped[Optional["DealScore"]] = relationship("DealScore", back_populates="deal", uselist=False)
    outcomes: Mapped[List["Outcome"]] = relationship("Outcome", back_populates="deal")

    # Index - using existing index names from DB
    __table_args__ = (
        UniqueConstraint('source', 'external_id', name='ix_deals_source_external_id'),
    )


class VintedStats(Base):
    """Statistiques Vinted pour chaque deal"""
    __tablename__ = "vinted_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), unique=True)

    # Stats de marché
    nb_listings: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Prix
    price_min: Mapped[Optional[float]] = mapped_column(Float)
    price_max: Mapped[Optional[float]] = mapped_column(Float)
    price_avg: Mapped[Optional[float]] = mapped_column(Float)
    price_median: Mapped[Optional[float]] = mapped_column(Float)
    price_p25: Mapped[Optional[float]] = mapped_column(Float)
    price_p75: Mapped[Optional[float]] = mapped_column(Float)
    coefficient_variation: Mapped[Optional[float]] = mapped_column(Float)

    # Calculs
    margin_euro: Mapped[Optional[float]] = mapped_column(Float)
    margin_pct: Mapped[Optional[float]] = mapped_column(Float)
    liquidity_score: Mapped[Optional[float]] = mapped_column(Float)

    # Sample listings
    sample_listings: Mapped[Optional[dict]] = mapped_column(JSON)
    search_query: Mapped[Optional[str]] = mapped_column(String(255))

    # Timestamps
    computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    deal: Mapped["Deal"] = relationship("Deal", back_populates="vinted_stats")


class DealScore(Base):
    """Scores IA pour chaque deal"""
    __tablename__ = "deal_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), unique=True)

    # Scores (0-100)
    flip_score: Mapped[float] = mapped_column(Float, nullable=False)
    popularity_score: Mapped[Optional[float]] = mapped_column(Float)
    liquidity_score: Mapped[Optional[float]] = mapped_column(Float)
    margin_score: Mapped[Optional[float]] = mapped_column(Float)
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON)

    # Recommandations
    recommended_action: Mapped[Optional[str]] = mapped_column(String(20))
    recommended_price: Mapped[Optional[float]] = mapped_column(Float)
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Explications
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    explanation_short: Mapped[Optional[str]] = mapped_column(String(255))
    risks: Mapped[Optional[dict]] = mapped_column(JSON)
    estimated_sell_days: Mapped[Optional[int]] = mapped_column(Integer)

    # Metadata
    model_version: Mapped[Optional[str]] = mapped_column(String(50), default="rules_v1")
    computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Vinted data
    vinted_median_price: Mapped[Optional[float]] = mapped_column(Float)
    vinted_avg_days_to_sell: Mapped[Optional[float]] = mapped_column(Float)
    vinted_total_sold: Mapped[Optional[int]] = mapped_column(Integer)
    vinted_total_listings: Mapped[Optional[int]] = mapped_column(Integer)
    vinted_searched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relations
    deal: Mapped["Deal"] = relationship("Deal", back_populates="deal_score")


class User(Base):
    """Utilisateurs de l'application"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Profile
    name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    
    # Subscription
    plan: Mapped[PlanType] = mapped_column(SQLEnum(PlanType), default=PlanType.FREE)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100))
    plan_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Préférences
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default={
        "min_margin": 20,
        "categories": [],
        "brands": [],
        "sizes": [],
        "risk_profile": "balanced",
        "alert_threshold": 70
    })
    
    # Alerting
    discord_webhook: Mapped[Optional[str]] = mapped_column(Text)
    email_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Stats
    total_deals_viewed: Mapped[int] = mapped_column(Integer, default=0)
    total_deals_bought: Mapped[int] = mapped_column(Integer, default=0)
    
    # Auth
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    outcomes: Mapped[List["Outcome"]] = relationship("Outcome", back_populates="user")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="user")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user")


class Outcome(Base):
    """Tracking des résultats (pour entraîner le ML)"""
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    deal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("deals.id"))

    # Action prise
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    buy_price: Mapped[Optional[float]] = mapped_column(Float)
    buy_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    buy_size: Mapped[Optional[str]] = mapped_column(String(20))
    buy_platform: Mapped[Optional[str]] = mapped_column(String(50))

    # Résultat
    sold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sell_price: Mapped[Optional[float]] = mapped_column(Float)
    sell_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sell_platform: Mapped[Optional[str]] = mapped_column(String(50))

    # Métriques réelles
    actual_margin_euro: Mapped[Optional[float]] = mapped_column(Float)
    actual_margin_pct: Mapped[Optional[float]] = mapped_column(Float)
    days_to_sell: Mapped[Optional[int]] = mapped_column(Integer)

    # Feedback
    was_good_deal: Mapped[Optional[bool]] = mapped_column(Boolean)
    difficulty_rating: Mapped[Optional[int]] = mapped_column(Integer)
    context_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="outcomes")
    user: Mapped["User"] = relationship("User", back_populates="outcomes")


class Alert(Base):
    """Alertes envoyées aux utilisateurs"""
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    deal_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="alerts")


class PopularityReference(Base):
    """Référentiel de popularité des modèles"""
    __tablename__ = "popularity_reference"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    popularity_score: Mapped[float] = mapped_column(Float, default=50)
    avg_days_to_sell: Mapped[float] = mapped_column(Float, default=14)
    avg_margin_percent: Mapped[Optional[float]] = mapped_column(Float)
    volume_tier: Mapped[str] = mapped_column(String(20), default="medium")

    # Stats
    total_tracked: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('brand', 'model', 'category', name='uq_popularity_ref'),
    )


class ScrapingLogStatus(str, enum.Enum):
    """Statuts possibles pour un job de scraping"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapingLog(Base):
    """Journal des activités de scraping"""
    __tablename__ = "scraping_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source info
    source_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Status
    status: Mapped[ScrapingLogStatus] = mapped_column(
        SQLEnum(ScrapingLogStatus),
        default=ScrapingLogStatus.STARTED
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)

    # Results
    deals_found: Mapped[int] = mapped_column(Integer, default=0)
    deals_new: Mapped[int] = mapped_column(Integer, default=0)
    deals_updated: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text)

    # Context
    triggered_by: Mapped[str] = mapped_column(String(50), default="scheduler")  # scheduler, manual, api
    proxy_used: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index('idx_scraping_logs_source', 'source_slug'),
        Index('idx_scraping_logs_status', 'status'),
        Index('idx_scraping_logs_started', 'started_at'),
    )


class Favorite(Base):
    """Deals favoris/trackés par les utilisateurs"""
    __tablename__ = "user_favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    deal: Mapped["Deal"] = relationship("Deal")