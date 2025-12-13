"""Alerts router - endpoints for alert management."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from database import get_db
from models import Alert, User
from dependencies import get_current_user

router = APIRouter()


# Pydantic schemas
class AlertResponse(BaseModel):
    """Alert response schema."""
    id: UUID
    deal_id: UUID
    channel: str
    status: str
    alert_data: Optional[dict]
    was_clicked: bool
    led_to_purchase: bool
    sent_at: datetime

    class Config:
        from_attributes = True


class AlertsListResponse(BaseModel):
    """Paginated alerts list response."""
    items: List[AlertResponse]
    total: int
    page: int
    per_page: int


class AlertStatsResponse(BaseModel):
    """Alert statistics response."""
    total_sent: int
    total_clicked: int
    total_purchased: int
    click_rate: float
    conversion_rate: float


@router.get("", response_model=AlertsListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's alerts with pagination."""

    query = select(Alert).where(Alert.user_id == user.id)

    if channel:
        query = query.where(Alert.channel == channel)

    if status_filter:
        query = query.where(Alert.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Order and paginate
    query = query.order_by(Alert.sent_at.desc())
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertsListResponse(
        items=[
            AlertResponse(
                id=alert.id,
                deal_id=alert.deal_id,
                channel=alert.channel,
                status=alert.status,
                alert_data=alert.alert_data,
                was_clicked=alert.was_clicked,
                led_to_purchase=alert.led_to_purchase,
                sent_at=alert.sent_at,
            )
            for alert in alerts
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics for the user."""

    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)

    # Get counts
    base_query = select(Alert).where(
        Alert.user_id == user.id,
        Alert.sent_at >= since,
    )

    # Total sent
    total_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total_sent = total_result.scalar() or 0

    # Clicked
    clicked_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Alert.was_clicked == True).subquery()
        )
    )
    total_clicked = clicked_result.scalar() or 0

    # Purchased
    purchased_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Alert.led_to_purchase == True).subquery()
        )
    )
    total_purchased = purchased_result.scalar() or 0

    # Calculate rates
    click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
    conversion_rate = (total_purchased / total_clicked * 100) if total_clicked > 0 else 0

    return AlertStatsResponse(
        total_sent=total_sent,
        total_clicked=total_clicked,
        total_purchased=total_purchased,
        click_rate=round(click_rate, 2),
        conversion_rate=round(conversion_rate, 2),
    )


@router.post("/{alert_id}/click")
async def mark_alert_clicked(
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as clicked."""

    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    alert.was_clicked = True
    alert.clicked_at = datetime.utcnow()
    await db.commit()

    return {"message": "Alert marked as clicked"}


@router.post("/{alert_id}/purchase")
async def mark_alert_purchased(
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as leading to a purchase."""

    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    alert.led_to_purchase = True
    await db.commit()

    return {"message": "Alert marked as purchased"}
