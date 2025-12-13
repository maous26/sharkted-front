"""VintedStats model - Vinted market statistics for a deal."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database import Base


class VintedStats(Base):
    """Vinted market statistics for a specific deal."""

    __tablename__ = "vinted_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, unique=True)

    # Listing counts
    nb_listings = Column(Integer, default=0)
    nb_listings_by_size = Column(JSONB, default=dict)  # {"42": 15, "43": 12}
    nb_sold_last_30d = Column(Integer, default=0)  # Sold items in last 30 days

    # Price statistics (in euros)
    price_min = Column(Numeric(10, 2))
    price_max = Column(Numeric(10, 2))
    price_avg = Column(Numeric(10, 2))
    price_median = Column(Numeric(10, 2))
    price_p25 = Column(Numeric(10, 2))  # 25th percentile
    price_p75 = Column(Numeric(10, 2))  # 75th percentile

    # Calculated metrics
    margin_euro = Column(Numeric(10, 2))  # price_median - deal.sale_price
    margin_pct = Column(Numeric(5, 2))    # margin as percentage
    liquidity_score = Column(Numeric(5, 2))  # 0-100, based on nb_listings & velocity

    # Sample listings
    sample_listings = Column(JSONB, default=list)  # Top 5 listings for reference
    # Format: [{"id": "123", "price": 85, "title": "...", "url": "..."}]

    # Search query used
    search_query = Column(String(255))
    match_confidence = Column(Numeric(5, 2))  # 0-100, embedding similarity score

    # Timestamps
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal = relationship("Deal", back_populates="vinted_stats")

    # Indexes
    __table_args__ = (
        Index("idx_vinted_stats_deal", "deal_id"),
        Index("idx_vinted_stats_margin", "margin_pct"),
        Index("idx_vinted_stats_liquidity", "liquidity_score"),
    )

    def __repr__(self):
        return f"<VintedStats deal={self.deal_id} margin={self.margin_pct}%>"

    @property
    def price_spread(self) -> float:
        """Calculate price spread (p75 - p25)."""
        if self.price_p75 and self.price_p25:
            return float(self.price_p75 - self.price_p25)
        return 0.0

    @property
    def is_liquid(self) -> bool:
        """Check if market is liquid (enough listings)."""
        return self.nb_listings >= 10
