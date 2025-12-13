"""Outcome model - Track actual results of deals for ML training."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Outcome(Base):
    """Track actual outcome of a deal for ML training."""

    __tablename__ = "outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Action taken
    action = Column(String(20), nullable=False)  # 'bought', 'ignored', 'watched'

    # Purchase details (if bought)
    buy_price = Column(Numeric(10, 2))
    buy_date = Column(DateTime(timezone=True))
    buy_size = Column(String(20))
    buy_quantity = Column(Integer, default=1)

    # Sale details (if sold)
    sold = Column(Boolean, default=False)
    sell_price = Column(Numeric(10, 2))
    sell_date = Column(DateTime(timezone=True))
    sell_platform = Column(String(50))  # 'vinted', 'leboncoin', 'ebay', etc.
    sell_fees = Column(Numeric(10, 2), default=0)  # Platform fees

    # Actual metrics
    actual_margin_euro = Column(Numeric(10, 2))  # sell_price - buy_price - fees
    actual_margin_pct = Column(Numeric(5, 2))
    days_to_sell = Column(Integer)

    # Feedback
    was_good_deal = Column(Boolean)  # User subjective feedback
    difficulty_rating = Column(Integer)  # 1-5, how hard was it to sell
    notes = Column(Text)  # User notes

    # For ML training
    flip_score_at_purchase = Column(Numeric(5, 2))  # Score when user bought
    predicted_margin = Column(Numeric(5, 2))  # What we predicted
    prediction_error = Column(Numeric(5, 2))  # Actual - Predicted

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal = relationship("Deal", back_populates="outcomes")
    user = relationship("User", back_populates="outcomes")

    # Indexes
    __table_args__ = (
        Index("idx_outcome_user", "user_id"),
        Index("idx_outcome_deal", "deal_id"),
        Index("idx_outcome_action", "action"),
        Index("idx_outcome_sold", "sold"),
    )

    def __repr__(self):
        return f"<Outcome {self.action} - margin={self.actual_margin_pct}%>"

    @property
    def is_successful(self) -> bool:
        """Check if outcome was successful (sold with positive margin)."""
        if self.sold and self.actual_margin_euro:
            return float(self.actual_margin_euro) > 0
        return False

    @property
    def roi(self) -> float:
        """Calculate return on investment."""
        if self.buy_price and self.actual_margin_euro:
            return float(self.actual_margin_euro / self.buy_price * 100)
        return 0.0
