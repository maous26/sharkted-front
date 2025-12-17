"""Deals router - endpoints for deal management."""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from database import get_db, Deal, VintedStats, DealScore, User
from dependencies import get_current_user, get_current_user_optional

router = APIRouter()


# Pydantic schemas
class VintedStatsResponse(BaseModel):
    """Vinted stats response schema."""
    nb_listings: Optional[int] = 0
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_median: Optional[float] = None
    margin_euro: Optional[float] = None
    margin_pct: Optional[float] = None
    liquidity_score: Optional[float] = None

    class Config:
        from_attributes = True


class DealScoreResponse(BaseModel):
    """Deal score response schema."""
    flip_score: float
    margin_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    popularity_score: Optional[float] = None
    recommended_action: Optional[str] = None
    recommended_price: Optional[float] = None
    confidence: Optional[float] = None
    explanation_short: Optional[str] = None
    risks: Optional[List[str]] = None
    estimated_sell_days: Optional[int] = None

    class Config:
        from_attributes = True


class DealResponse(BaseModel):
    """Deal response schema."""
    id: int
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    original_price: Optional[float] = None
    price: float
    discount_pct: Optional[float] = None
    url: str
    image_url: Optional[str] = None
    sizes_available: Optional[List[str]] = None
    in_stock: bool = True
    source: str
    first_seen_at: datetime
    vinted_stats: Optional[VintedStatsResponse] = None
    score: Optional[DealScoreResponse] = None

    class Config:
        from_attributes = True


class DealsListResponse(BaseModel):
    """Paginated deals list response."""
    items: List[DealResponse]
    total: int
    page: int
    per_page: int
    pages: int


def deal_to_response(deal: Deal) -> DealResponse:
    """Convert Deal model to response schema."""
    # Handle sizes_available - can be dict/list from JSONB
    sizes = None
    if deal.sizes_available:
        if isinstance(deal.sizes_available, dict):
            sizes = list(deal.sizes_available.keys()) if deal.sizes_available else None
        elif isinstance(deal.sizes_available, list):
            sizes = deal.sizes_available

    # Handle risks - can be dict/list from JSONB
    risks = None
    if deal.deal_score and deal.deal_score.risks:
        if isinstance(deal.deal_score.risks, dict):
            risks = list(deal.deal_score.risks.values()) if deal.deal_score.risks else None
        elif isinstance(deal.deal_score.risks, list):
            risks = deal.deal_score.risks

    return DealResponse(
        id=deal.id,
        title=deal.title,
        brand=deal.brand,
        model=deal.model,
        category=deal.category,
        color=deal.color,
        gender=deal.gender,
        original_price=float(deal.original_price) if deal.original_price else None,
        price=float(deal.price),
        discount_pct=float(deal.discount_percent) if deal.discount_percent else None,
        url=deal.url,
        image_url=deal.image_url,
        sizes_available=sizes,
        in_stock=deal.in_stock,
        source=deal.source,
        first_seen_at=deal.first_seen_at,
        vinted_stats=VintedStatsResponse(
            nb_listings=deal.vinted_stats.nb_listings or 0,
            price_min=float(deal.vinted_stats.price_min) if deal.vinted_stats.price_min else None,
            price_max=float(deal.vinted_stats.price_max) if deal.vinted_stats.price_max else None,
            price_median=float(deal.vinted_stats.price_median) if deal.vinted_stats.price_median else None,
            margin_euro=float(deal.vinted_stats.margin_euro) if deal.vinted_stats.margin_euro else None,
            margin_pct=float(deal.vinted_stats.margin_pct) if deal.vinted_stats.margin_pct else None,
            liquidity_score=float(deal.vinted_stats.liquidity_score) if deal.vinted_stats.liquidity_score else None,
        ) if deal.vinted_stats else None,
        score=DealScoreResponse(
            flip_score=float(deal.deal_score.flip_score),
            margin_score=float(deal.deal_score.margin_score) if deal.deal_score.margin_score else None,
            liquidity_score=float(deal.deal_score.liquidity_score) if deal.deal_score.liquidity_score else None,
            popularity_score=float(deal.deal_score.popularity_score) if deal.deal_score.popularity_score else None,
            recommended_action=deal.deal_score.recommended_action,
            recommended_price=float(deal.deal_score.recommended_price) if deal.deal_score.recommended_price else None,
            confidence=float(deal.deal_score.confidence) if deal.deal_score.confidence else None,
            explanation_short=deal.deal_score.explanation_short,
            risks=risks,
            estimated_sell_days=deal.deal_score.estimated_sell_days,
        ) if deal.deal_score else None,
    )


# ==================== STATIC ROUTES FIRST ====================
# These must be defined BEFORE /{deal_id} to avoid being captured

@router.get("/stats")
async def get_deals_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get deals statistics summary (main stats endpoint)."""

    # Total active deals
    total_query = select(func.count(Deal.id)).where(Deal.in_stock == True)
    total_result = await db.execute(total_query)
    total_active = total_result.scalar() or 0

    # Deals with good score (>= 70)
    good_score_query = (
        select(func.count(Deal.id))
        .join(DealScore, Deal.id == DealScore.deal_id)
        .where(and_(Deal.in_stock == True, DealScore.flip_score >= 70))
    )
    good_score_result = await db.execute(good_score_query)
    good_deals = good_score_result.scalar() or 0

    # New deals (last 24h)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    new_query = select(func.count(Deal.id)).where(
        and_(Deal.in_stock == True, Deal.first_seen_at >= yesterday)
    )
    new_result = await db.execute(new_query)
    new_deals = new_result.scalar() or 0

    # By source
    source_query = (
        select(Deal.source, func.count(Deal.id))
        .where(Deal.in_stock == True)
        .group_by(Deal.source)
    )
    source_result = await db.execute(source_query)
    by_source = {row[0]: row[1] for row in source_result.fetchall()}

    # By category
    category_query = (
        select(Deal.category, func.count(Deal.id))
        .where(Deal.in_stock == True)
        .group_by(Deal.category)
    )
    category_result = await db.execute(category_query)
    by_category = {row[0] or "other": row[1] for row in category_result.fetchall()}

    return {
        "total_active": total_active,
        "good_deals": good_deals,
        "new_last_24h": new_deals,
        "by_source": by_source,
        "by_category": by_category,
    }


@router.get("/stats/summary")
async def get_deals_stats_summary(
    db: AsyncSession = Depends(get_db),
):
    """Alias for /stats - Get deals statistics summary."""
    return await get_deals_stats(db)


@router.get("/stats/brands")
async def get_brands_stats(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get stats by brand."""
    query = (
        select(Deal.brand, func.count(Deal.id).label("count"))
        .where(and_(Deal.in_stock == True, Deal.brand.isnot(None)))
        .group_by(Deal.brand)
        .order_by(func.count(Deal.id).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return [{"brand": row[0], "count": row[1]} for row in result.fetchall()]


@router.get("/stats/categories")
async def get_categories_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get stats by category."""
    query = (
        select(Deal.category, func.count(Deal.id).label("count"))
        .where(Deal.in_stock == True)
        .group_by(Deal.category)
        .order_by(func.count(Deal.id).desc())
    )
    result = await db.execute(query)
    return [{"category": row[0] or "other", "count": row[1]} for row in result.fetchall()]


@router.get("/stats/sources")
async def get_sources_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get stats by source."""
    query = (
        select(Deal.source, func.count(Deal.id).label("count"))
        .where(Deal.in_stock == True)
        .group_by(Deal.source)
        .order_by(func.count(Deal.id).desc())
    )
    result = await db.execute(query)
    return [{"source": row[0], "count": row[1]} for row in result.fetchall()]


@router.get("/stats/trends")
async def get_deals_trends(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Get deals trends over time."""
    since = datetime.utcnow() - timedelta(days=days)

    query = (
        select(
            func.date(Deal.first_seen_at).label("date"),
            func.count(Deal.id).label("count")
        )
        .where(Deal.first_seen_at >= since)
        .group_by(func.date(Deal.first_seen_at))
        .order_by(func.date(Deal.first_seen_at))
    )
    result = await db.execute(query)
    return [{"date": str(row[0]), "count": row[1]} for row in result.fetchall()]


@router.get("/stats/score-distribution")
async def get_score_distribution(
    db: AsyncSession = Depends(get_db),
):
    """Get distribution of flip scores."""
    # Define score ranges
    ranges = [
        (0, 40, "0-40"),
        (40, 60, "40-60"),
        (60, 70, "60-70"),
        (70, 80, "70-80"),
        (80, 90, "80-90"),
        (90, 100, "90-100"),
    ]

    distribution = []
    for min_score, max_score, label in ranges:
        query = (
            select(func.count(DealScore.id))
            .join(Deal, Deal.id == DealScore.deal_id)
            .where(and_(
                Deal.in_stock == True,
                DealScore.flip_score >= min_score,
                DealScore.flip_score < max_score
            ))
        )
        result = await db.execute(query)
        count = result.scalar() or 0
        distribution.append({"range": label, "count": count})

    return distribution


@router.get("/top/recommended", response_model=List[DealResponse])
async def get_top_recommended_deals(
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get top recommended deals by FlipScore."""

    query = (
        select(Deal)
        .options(
            selectinload(Deal.vinted_stats),
            selectinload(Deal.deal_score),
        )
        .outerjoin(DealScore, Deal.id == DealScore.deal_id)
        .where(Deal.in_stock == True)
    )

    # Apply user category filter from preferences
    if user and user.preferences:
        user_categories = user.preferences.get("categories", [])
        if user_categories and len(user_categories) > 0:
            query = query.where(Deal.category.in_(user_categories))

    if category:
        query = query.where(Deal.category == category)

    # Order by flip_score (nulls last) and limit
    query = query.order_by(DealScore.flip_score.desc().nullslast()).limit(limit)

    result = await db.execute(query)
    deals = result.scalars().unique().all()

    return [deal_to_response(deal) for deal in deals]


# ==================== MAIN LIST ENDPOINT ====================

@router.get("", response_model=DealsListResponse)
async def list_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    brand: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    min_margin: Optional[float] = None,
    max_price: Optional[float] = None,
    recommended_only: bool = False,
    sort_by: str = Query("first_seen_at", regex="^(first_seen_at|flip_score|margin_pct|price)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """List deals with filters and pagination."""

    # Determine which joins are needed upfront to avoid duplicates
    needs_score_join = min_score is not None or recommended_only or sort_by == "flip_score"
    needs_vinted_join = min_margin is not None or sort_by == "margin_pct"

    # Base query with eager loading
    query = (
        select(Deal)
        .options(
            selectinload(Deal.vinted_stats),
            selectinload(Deal.deal_score),
        )
        .where(Deal.in_stock == True)
    )

    # Add joins once (outer joins to allow deals without scores/stats)
    if needs_score_join:
        query = query.outerjoin(DealScore, Deal.id == DealScore.deal_id)
    if needs_vinted_join:
        query = query.outerjoin(VintedStats, Deal.id == VintedStats.deal_id)

    # Apply user category filter from preferences
    if user and user.preferences:
        user_categories = user.preferences.get("categories", [])
        if user_categories and len(user_categories) > 0:
            query = query.where(Deal.category.in_(user_categories))

    # Apply filters
    if brand:
        query = query.where(Deal.brand.ilike(f"%{brand}%"))

    if category:
        query = query.where(Deal.category == category)

    if source:
        query = query.where(Deal.source == source)

    if max_price:
        query = query.where(Deal.price <= max_price)

    if min_score is not None:
        query = query.where(DealScore.flip_score >= min_score)

    if min_margin is not None:
        query = query.where(VintedStats.margin_pct >= min_margin)

    if recommended_only:
        query = query.where(DealScore.recommended_action == "buy")

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    if sort_by == "flip_score":
        if not needs_score_join:
            query = query.outerjoin(DealScore, Deal.id == DealScore.deal_id)
        order_col = DealScore.flip_score
    elif sort_by == "margin_pct":
        if not needs_vinted_join:
            query = query.outerjoin(VintedStats, Deal.id == VintedStats.deal_id)
        order_col = VintedStats.margin_pct
    elif sort_by == "price":
        order_col = Deal.price
    else:
        order_col = Deal.first_seen_at

    if sort_order == "desc":
        query = query.order_by(order_col.desc().nullslast())
    else:
        query = query.order_by(order_col.asc().nullsfirst())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute
    result = await db.execute(query)
    deals = result.scalars().unique().all()

    # Transform to response
    items = [deal_to_response(deal) for deal in deals]

    return DealsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 0,
    )


# ==================== DYNAMIC ROUTE LAST ====================
# This must be AFTER all /stats/* and /top/* routes

@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single deal by ID."""

    result = await db.execute(
        select(Deal)
        .options(
            selectinload(Deal.vinted_stats),
            selectinload(Deal.deal_score),
        )
        .where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    return deal_to_response(deal)
