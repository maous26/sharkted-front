"""DealScore model - AI/ML scoring for deals."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from database import Base


class DealScore(Base):
    """AI/ML scoring and recommendations for a deal."""

    __tablename__ = "deal_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, unique=True)

    # Main scores (0-100)
    flip_score = Column(Numeric(5, 2), nullable=False)  # Overall score
    popularity_score = Column(Numeric(5, 2))  # Based on brand/model popularity
    liquidity_score = Column(Numeric(5, 2))  # From vinted_stats
    margin_score = Column(Numeric(5, 2))  # Based on margin percentage
    anomaly_score = Column(Numeric(5, 2))  # Isolation forest output (0 = normal, 100 = rare deal)

    # Score components breakdown
    score_breakdown = Column(JSONB, default=dict)
    # Format: {
    #   "margin_contribution": 35,
    #   "liquidity_contribution": 25,
    #   "popularity_contribution": 20,
    #   "size_bonus": 10,
    #   "brand_bonus": 10
    # }

    # Recommendations
    recommended_action = Column(String(20))  # 'buy', 'watch', 'ignore'
    recommended_price = Column(Numeric(10, 2))  # Optimal listing price on Vinted
    recommended_price_range = Column(JSONB)  # {"min": 75, "optimal": 85, "max": 95}
    confidence = Column(Numeric(5, 2))  # 0-100, model confidence

    # LLM explanation
    explanation = Column(Text)  # Human-readable explanation
    explanation_short = Column(String(255))  # One-liner summary
    risks = Column(ARRAY(String))  # List of identified risks
    opportunities = Column(ARRAY(String))  # List of opportunities

    # Predictions
    estimated_sell_days = Column(Integer)  # Estimated days to sell
    estimated_margin_range = Column(JSONB)  # {"min": 20, "expected": 35, "max": 50}

    # Model metadata
    model_version = Column(String(50), default="rules_v1")  # 'rules_v1', 'ml_v1', 'ml_v2'
    features_used = Column(JSONB, default=list)  # List of features used for scoring

    # Timestamps
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal = relationship("Deal", back_populates="score")

    # Indexes
    __table_args__ = (
        Index("idx_score_flip", "flip_score", postgresql_ops={"flip_score": "DESC"}),
        Index("idx_score_deal", "deal_id"),
        Index("idx_score_action", "recommended_action"),
    )

    def __repr__(self):
        return f"<DealScore {self.flip_score}/100 - {self.recommended_action}>"

    @property
    def score_emoji(self) -> str:
        """Get emoji based on flip score."""
        if self.flip_score >= 80:
            return "🟢"  # Excellent
        elif self.flip_score >= 60:
            return "🟡"  # Good
        elif self.flip_score >= 40:
            return "🟠"  # Average
        else:
            return "🔴"  # Poor

    @property
    def is_recommended(self) -> bool:
        """Check if deal is recommended for purchase."""
        return self.recommended_action == "buy" and self.flip_score >= 70
