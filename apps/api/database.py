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

class Source(Base):
    """Sources de scraping (Nike, Adidas, etc.)"""
    __tablename__ = "sources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    scraper_config: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    total_deals_found: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relations
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="source")


class Deal(Base):
    """Deals détectés (produits en promo)"""
    __tablename__ = "deals"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    
    # Identité produit
    external_id: Mapped[str] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(50))
    subcategory: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Prix
    original_price: Mapped[float] = mapped_column(Float, nullable=False)
    sale_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float)
    
    # Tailles
    sizes_available: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=[])
    
    # URLs et images
    product_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[DealStatus] = mapped_column(SQLEnum(DealStatus), default=DealStatus.ACTIVE)
    stock_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    source: Mapped["Source"] = relationship("Source", back_populates="deals")
    vinted_stats: Mapped[Optional["VintedStats"]] = relationship("VintedStats", back_populates="deal", uselist=False)
    score: Mapped[Optional["DealScore"]] = relationship("DealScore", back_populates="deal", uselist=False)
    outcomes: Mapped[List["Outcome"]] = relationship("Outcome", back_populates="deal")
    
    # Index et contraintes
    __table_args__ = (
        UniqueConstraint('source_id', 'external_id', name='uq_source_external'),
        Index('idx_deals_status', 'status'),
        Index('idx_deals_brand', 'brand'),
        Index('idx_deals_category', 'category'),
        Index('idx_deals_detected', 'detected_at'),
    )


class VintedStats(Base):
    """Statistiques Vinted pour chaque deal"""
    __tablename__ = "vinted_stats"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"), unique=True)
    
    # Stats de marché
    nb_listings: Mapped[int] = mapped_column(Integer, default=0)
    nb_listings_by_size: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    
    # Prix
    price_min: Mapped[Optional[float]] = mapped_column(Float)
    price_max: Mapped[Optional[float]] = mapped_column(Float)
    price_avg: Mapped[Optional[float]] = mapped_column(Float)
    price_median: Mapped[Optional[float]] = mapped_column(Float)
    price_p25: Mapped[Optional[float]] = mapped_column(Float)
    price_p75: Mapped[Optional[float]] = mapped_column(Float)
    
    # Calculs
    margin_euro: Mapped[Optional[float]] = mapped_column(Float)
    margin_percent: Mapped[Optional[float]] = mapped_column(Float)
    liquidity_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Sample listings
    sample_listings: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=[])
    
    # Timestamps
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relations
    deal: Mapped["Deal"] = relationship("Deal", back_populates="vinted_stats")
    
    __table_args__ = (
        Index('idx_vinted_deal', 'deal_id'),
        Index('idx_vinted_liquidity', 'liquidity_score'),
    )


class DealScore(Base):
    """Scores IA pour chaque deal"""
    __tablename__ = "deal_scores"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"), unique=True)
    
    # Scores (0-100)
    flip_score: Mapped[float] = mapped_column(Float, default=0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0)
    liquidity_score: Mapped[float] = mapped_column(Float, default=0)
    margin_score: Mapped[float] = mapped_column(Float, default=0)
    anomaly_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Recommandations
    recommended_action: Mapped[RecommendedAction] = mapped_column(
        SQLEnum(RecommendedAction), 
        default=RecommendedAction.IGNORE
    )
    recommended_price: Mapped[Optional[float]] = mapped_column(Float)
    recommended_price_range: Mapped[Optional[dict]] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    
    # Explications LLM
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    risks: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=[])
    estimated_sell_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    model_version: Mapped[str] = mapped_column(String(50), default="rules_v1")
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relations
    deal: Mapped["Deal"] = relationship("Deal", back_populates="score")
    
    __table_args__ = (
        Index('idx_scores_flip', 'flip_score'),
        Index('idx_scores_action', 'recommended_action'),
    )


class User(Base):
    """Utilisateurs de l'application"""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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


class Outcome(Base):
    """Tracking des résultats (pour entraîner le ML)"""
    __tablename__ = "outcomes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Action prise
    action: Mapped[ActionType] = mapped_column(SQLEnum(ActionType), nullable=False)
    buy_price: Mapped[Optional[float]] = mapped_column(Float)
    buy_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    buy_size: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Résultat
    sold: Mapped[bool] = mapped_column(Boolean, default=False)
    sell_price: Mapped[Optional[float]] = mapped_column(Float)
    sell_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sell_platform: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Métriques réelles
    actual_margin_euro: Mapped[Optional[float]] = mapped_column(Float)
    actual_margin_percent: Mapped[Optional[float]] = mapped_column(Float)
    days_to_sell: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Feedback
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    deal: Mapped["Deal"] = relationship("Deal", back_populates="outcomes")
    user: Mapped["User"] = relationship("User", back_populates="outcomes")
    
    __table_args__ = (
        Index('idx_outcomes_user', 'user_id'),
        Index('idx_outcomes_deal', 'deal_id'),
    )


class Alert(Base):
    """Alertes envoyées aux utilisateurs"""
    __tablename__ = "alerts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    deal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deals.id"))
    
    # Alert info
    channel: Mapped[str] = mapped_column(String(20))  # discord, email, push
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
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