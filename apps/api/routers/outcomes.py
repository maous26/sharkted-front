"""Outcomes router - endpoints for tracking deal outcomes."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from decimal import Decimal

from database import get_db
from models import Outcome, Deal, User
from dependencies import get_current_user

router = APIRouter()


# Pydantic schemas
class OutcomeCreate(BaseModel):
    """Outcome creation schema."""
    deal_id: UUID
    action: str = Field(..., pattern="^(bought|ignored|watched)$")
    buy_price: Optional[float] = None
    buy_date: Optional[datetime] = None
    buy_size: Optional[str] = None
    buy_quantity: int = 1


class OutcomeSoldUpdate(BaseModel):
    """Update outcome with sale info."""
    sell_price: float
    sell_date: Optional[datetime] = None
    sell_platform: str = "vinted"
    sell_fees: float = 0
    notes: Optional[str] = None


class OutcomeFeedback(BaseModel):
    """User feedback on outcome."""
    was_good_deal: bool
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class OutcomeResponse(BaseModel):
    """Outcome response schema."""
    id: UUID
    deal_id: UUID
    action: str
    buy_price: Optional[float]
    buy_date: Optional[datetime]
    buy_size: Optional[str]
    sold: bool
    sell_price: Optional[float]
    sell_date: Optional[datetime]
    sell_platform: Optional[str]
    actual_margin_euro: Optional[float]
    actual_margin_pct: Optional[float]
    days_to_sell: Optional[int]
    was_good_deal: Optional[bool]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OutcomesListResponse(BaseModel):
    """Paginated outcomes list response."""
    items: List[OutcomeResponse]
    total: int
    page: int
    per_page: int


class OutcomeStatsResponse(BaseModel):
    """Outcome statistics response."""
    total_bought: int
    total_sold: int
    total_revenue: float
    total_profit: float
    avg_margin_pct: float
    avg_days_to_sell: float
    success_rate: float


@router.post("", response_model=OutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_outcome(
    outcome_data: OutcomeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new outcome (track action on a deal)."""

    # Check if deal exists
    result = await db.execute(
        select(Deal)
        .options(selectinload(Deal.score))
        .where(Deal.id == outcome_data.deal_id)
    )
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    # Create outcome
    outcome = Outcome(
        deal_id=outcome_data.deal_id,
        user_id=user.id,
        action=outcome_data.action,
        buy_price=Decimal(str(outcome_data.buy_price)) if outcome_data.buy_price else None,
        buy_date=outcome_data.buy_date or datetime.utcnow(),
        buy_size=outcome_data.buy_size,
        buy_quantity=outcome_data.buy_quantity,
        flip_score_at_purchase=deal.score.flip_score if deal.score else None,
        predicted_margin=deal.vinted_stats.margin_pct if deal.vinted_stats else None,
    )
    db.add(outcome)
    await db.commit()
    await db.refresh(outcome)

    return OutcomeResponse(
        id=outcome.id,
        deal_id=outcome.deal_id,
        action=outcome.action,
        buy_price=float(outcome.buy_price) if outcome.buy_price else None,
        buy_date=outcome.buy_date,
        buy_size=outcome.buy_size,
        sold=outcome.sold,
        sell_price=float(outcome.sell_price) if outcome.sell_price else None,
        sell_date=outcome.sell_date,
        sell_platform=outcome.sell_platform,
        actual_margin_euro=float(outcome.actual_margin_euro) if outcome.actual_margin_euro else None,
        actual_margin_pct=float(outcome.actual_margin_pct) if outcome.actual_margin_pct else None,
        days_to_sell=outcome.days_to_sell,
        was_good_deal=outcome.was_good_deal,
        notes=outcome.notes,
        created_at=outcome.created_at,
    )


@router.get("", response_model=OutcomesListResponse)
async def list_outcomes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    sold_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's outcomes with pagination."""

    query = select(Outcome).where(Outcome.user_id == user.id)

    if action:
        query = query.where(Outcome.action == action)

    if sold_only:
        query = query.where(Outcome.sold == True)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Order and paginate
    query = query.order_by(Outcome.created_at.desc())
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    outcomes = result.scalars().all()

    return OutcomesListResponse(
        items=[
            OutcomeResponse(
                id=o.id,
                deal_id=o.deal_id,
                action=o.action,
                buy_price=float(o.buy_price) if o.buy_price else None,
                buy_date=o.buy_date,
                buy_size=o.buy_size,
                sold=o.sold,
                sell_price=float(o.sell_price) if o.sell_price else None,
                sell_date=o.sell_date,
                sell_platform=o.sell_platform,
                actual_margin_euro=float(o.actual_margin_euro) if o.actual_margin_euro else None,
                actual_margin_pct=float(o.actual_margin_pct) if o.actual_margin_pct else None,
                days_to_sell=o.days_to_sell,
                was_good_deal=o.was_good_deal,
                notes=o.notes,
                created_at=o.created_at,
            )
            for o in outcomes
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.patch("/{outcome_id}/sold", response_model=OutcomeResponse)
async def mark_outcome_sold(
    outcome_id: UUID,
    sold_data: OutcomeSoldUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an outcome as sold and record sale details."""

    result = await db.execute(
        select(Outcome).where(
            Outcome.id == outcome_id,
            Outcome.user_id == user.id,
        )
    )
    outcome = result.scalar_one_or_none()

    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outcome not found",
        )

    if outcome.action != "bought":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only mark purchased items as sold",
        )

    # Update with sale data
    outcome.sold = True
    outcome.sell_price = Decimal(str(sold_data.sell_price))
    outcome.sell_date = sold_data.sell_date or datetime.utcnow()
    outcome.sell_platform = sold_data.sell_platform
    outcome.sell_fees = Decimal(str(sold_data.sell_fees))
    outcome.notes = sold_data.notes

    # Calculate actual margin
    if outcome.buy_price:
        margin_euro = float(outcome.sell_price) - float(outcome.buy_price) - float(outcome.sell_fees)
        outcome.actual_margin_euro = Decimal(str(margin_euro))
        outcome.actual_margin_pct = Decimal(str(margin_euro / float(outcome.buy_price) * 100))

    # Calculate days to sell
    if outcome.buy_date:
        outcome.days_to_sell = (outcome.sell_date - outcome.buy_date).days

    # Calculate prediction error
    if outcome.predicted_margin:
        outcome.prediction_error = outcome.actual_margin_pct - outcome.predicted_margin

    outcome.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(outcome)

    return OutcomeResponse(
        id=outcome.id,
        deal_id=outcome.deal_id,
        action=outcome.action,
        buy_price=float(outcome.buy_price) if outcome.buy_price else None,
        buy_date=outcome.buy_date,
        buy_size=outcome.buy_size,
        sold=outcome.sold,
        sell_price=float(outcome.sell_price) if outcome.sell_price else None,
        sell_date=outcome.sell_date,
        sell_platform=outcome.sell_platform,
        actual_margin_euro=float(outcome.actual_margin_euro) if outcome.actual_margin_euro else None,
        actual_margin_pct=float(outcome.actual_margin_pct) if outcome.actual_margin_pct else None,
        days_to_sell=outcome.days_to_sell,
        was_good_deal=outcome.was_good_deal,
        notes=outcome.notes,
        created_at=outcome.created_at,
    )


@router.patch("/{outcome_id}/feedback", response_model=OutcomeResponse)
async def add_outcome_feedback(
    outcome_id: UUID,
    feedback: OutcomeFeedback,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add user feedback to an outcome."""

    result = await db.execute(
        select(Outcome).where(
            Outcome.id == outcome_id,
            Outcome.user_id == user.id,
        )
    )
    outcome = result.scalar_one_or_none()

    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outcome not found",
        )

    outcome.was_good_deal = feedback.was_good_deal
    outcome.difficulty_rating = feedback.difficulty_rating
    if feedback.notes:
        outcome.notes = feedback.notes

    outcome.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(outcome)

    return OutcomeResponse(
        id=outcome.id,
        deal_id=outcome.deal_id,
        action=outcome.action,
        buy_price=float(outcome.buy_price) if outcome.buy_price else None,
        buy_date=outcome.buy_date,
        buy_size=outcome.buy_size,
        sold=outcome.sold,
        sell_price=float(outcome.sell_price) if outcome.sell_price else None,
        sell_date=outcome.sell_date,
        sell_platform=outcome.sell_platform,
        actual_margin_euro=float(outcome.actual_margin_euro) if outcome.actual_margin_euro else None,
        actual_margin_pct=float(outcome.actual_margin_pct) if outcome.actual_margin_pct else None,
        days_to_sell=outcome.days_to_sell,
        was_good_deal=outcome.was_good_deal,
        notes=outcome.notes,
        created_at=outcome.created_at,
    )


@router.get("/stats", response_model=OutcomeStatsResponse)
async def get_outcome_stats(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get outcome statistics for the user."""

    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)

    # Get all outcomes in period
    result = await db.execute(
        select(Outcome).where(
            Outcome.user_id == user.id,
            Outcome.created_at >= since,
        )
    )
    outcomes = result.scalars().all()

    bought = [o for o in outcomes if o.action == "bought"]
    sold = [o for o in bought if o.sold]

    total_revenue = sum(float(o.sell_price) for o in sold if o.sell_price)
    total_profit = sum(float(o.actual_margin_euro) for o in sold if o.actual_margin_euro)

    avg_margin = (
        sum(float(o.actual_margin_pct) for o in sold if o.actual_margin_pct) / len(sold)
        if sold else 0
    )

    avg_days = (
        sum(o.days_to_sell for o in sold if o.days_to_sell) / len(sold)
        if sold else 0
    )

    success_rate = (
        len([o for o in sold if o.actual_margin_euro and float(o.actual_margin_euro) > 0]) / len(sold) * 100
        if sold else 0
    )

    return OutcomeStatsResponse(
        total_bought=len(bought),
        total_sold=len(sold),
        total_revenue=round(total_revenue, 2),
        total_profit=round(total_profit, 2),
        avg_margin_pct=round(avg_margin, 2),
        avg_days_to_sell=round(avg_days, 1),
        success_rate=round(success_rate, 2),
    )
