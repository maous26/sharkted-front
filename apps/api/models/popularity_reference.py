"""PopularityReference model - Reference data for product popularity."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database import Base


class PopularityReference(Base):
    """Reference data for brand/model popularity on Vinted."""

    __tablename__ = "popularity_reference"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Product identification
    brand = Column(String(50), nullable=False, index=True)
    model = Column(String(100))  # Optional, can be null for brand-level stats
    category = Column(String(50), nullable=False)

    # Popularity metrics
    popularity_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    avg_days_to_sell = Column(Numeric(5, 1))  # Average days to sell
    volume_tier = Column(String(20))  # 'low', 'medium', 'high', 'very_high'

    # Market data
    avg_price = Column(Numeric(10, 2))
    price_trend = Column(String(20))  # 'rising', 'stable', 'falling'
    seasonality = Column(JSONB, default=dict)  # {"spring": 1.2, "summer": 0.8, ...}

    # Size demand (for sneakers)
    size_demand = Column(JSONB, default=dict)
    # Format: {"40": 0.7, "41": 0.9, "42": 1.0, "43": 1.0, "44": 0.95, "45": 0.8, "46": 0.6}

    # Color preferences
    color_preferences = Column(JSONB, default=dict)
    # Format: {"black": 1.0, "white": 0.95, "red": 0.7, ...}

    # Data quality
    sample_size = Column(String(20))  # Number of sales analyzed
    confidence = Column(Numeric(5, 2))  # Data confidence score

    # Timestamps
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    data_from = Column(DateTime(timezone=True))  # When data was collected
    data_to = Column(DateTime(timezone=True))

    # Indexes
    __table_args__ = (
        Index("idx_pop_brand_model", "brand", "model"),
        Index("idx_pop_category", "category"),
        Index("idx_pop_score", "popularity_score", postgresql_ops={"popularity_score": "DESC"}),
    )

    def __repr__(self):
        return f"<PopularityReference {self.brand} {self.model or ''} = {self.popularity_score}>"

    def get_size_multiplier(self, size: str) -> float:
        """Get demand multiplier for a specific size."""
        if self.size_demand and size in self.size_demand:
            return float(self.size_demand[size])
        return 1.0  # Default multiplier

    def get_color_multiplier(self, color: str) -> float:
        """Get demand multiplier for a specific color."""
        if self.color_preferences:
            # Try exact match first
            if color.lower() in self.color_preferences:
                return float(self.color_preferences[color.lower()])
            # Try to find partial match
            for ref_color, mult in self.color_preferences.items():
                if ref_color in color.lower() or color.lower() in ref_color:
                    return float(mult)
        return 0.9  # Default slightly lower for unknown colors
