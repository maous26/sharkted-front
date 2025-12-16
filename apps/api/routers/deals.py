"""Deals router - endpoints for deal management."""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from database import get_db, DealStatus
from models import Deal, VintedStats, DealScore, Source, User
from dependencies import get_current_user, get_current_user_optional
from services.ai_service import ai_service
from services.vinted_service import get_vinted_stats_for_deal

router = APIRouter()


# Pydantic schemas
class VintedStatsResponse(BaseModel):
    """Vinted stats response schema."""
    nb_listings: int
    price_min: Optional[float]
    price_max: Optional[float]
    price_median: Optional[float]
    margin_euro: Optional[float]
    margin_pct: Optional[float]
    liquidity_score: Optional[float]

    class Config:
        from_attributes = True


class ScoreBreakdownResponse(BaseModel):
    """Score breakdown details."""
    margin_contribution: Optional[float] = None
    liquidity_contribution: Optional[float] = None
    popularity_contribution: Optional[float] = None
    size_bonus: Optional[float] = None
    brand_bonus: Optional[float] = None
    discount_bonus: Optional[float] = None


class DealScoreResponse(BaseModel):
    """Deal score response schema."""
    flip_score: float
    margin_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    popularity_score: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdownResponse] = None
    recommended_action: Optional[str]
    recommended_price: Optional[float]
    confidence: Optional[float]
    explanation_short: Optional[str]
    risks: Optional[List[str]]
    estimated_sell_days: Optional[int]

    class Config:
        from_attributes = True


class DealResponse(BaseModel):
    """Deal response schema."""
    id: UUID
    product_name: str
    brand: Optional[str]
    model: Optional[str]
    category: Optional[str]
    color: Optional[str]
    gender: Optional[str]
    original_price: Optional[float]
    sale_price: float
    discount_pct: Optional[float]
    product_url: str
    image_url: Optional[str]
    sizes_available: Optional[List[str]]
    stock_available: bool
    source_name: Optional[str]
    detected_at: datetime
    vinted_stats: Optional[VintedStatsResponse]
    score: Optional[DealScoreResponse]

    class Config:
        from_attributes = True


class DealsListResponse(BaseModel):
    """Paginated deals list response."""
    items: List[DealResponse]
    total: int
    page: int
    per_page: int
    pages: int


@router.get("", response_model=DealsListResponse)
async def list_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    brand: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = Query(60, ge=0, le=100),
    min_margin: Optional[float] = None,
    max_price: Optional[float] = None,
    recommended_only: bool = False,
    sort_by: str = Query("detected_at", regex="^(detected_at|flip_score|margin_pct|sale_price)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """List deals with filters and pagination."""

    # Base query with joins
    query = (
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score),
        )
        .where(Deal.status == DealStatus.ACTIVE)
    )

    # Apply user category filter from preferences
    # If user has categories selected, only show those categories
    # If no categories selected, show all deals
    if user and user.preferences:
        user_categories = user.preferences.get("categories", [])
        if user_categories and len(user_categories) > 0:
            # Filter deals to only include user's selected categories
            query = query.where(Deal.category.in_(user_categories))

    # Apply filters
    if brand:
        query = query.where(Deal.brand.ilike(f"%{brand}%"))

    if category:
        query = query.where(Deal.category == category)

    if source:
        query = query.join(Source).where(Source.name == source)

    if max_price:
        query = query.where(Deal.sale_price <= max_price)

    if min_score:
        query = query.join(DealScore).where(DealScore.flip_score >= min_score)

    if min_margin:
        query = query.join(VintedStats).where(VintedStats.margin_pct >= min_margin)

    if recommended_only:
        query = query.join(DealScore, isouter=True).where(DealScore.recommended_action == "buy")

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply sorting
    if sort_by == "flip_score":
        query = query.join(DealScore, isouter=True)
        order_col = DealScore.flip_score
    elif sort_by == "margin_pct":
        query = query.join(VintedStats, isouter=True)
        order_col = VintedStats.margin_pct
    elif sort_by == "sale_price":
        order_col = Deal.sale_price
    else:
        order_col = Deal.detected_at

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
    items = []
    for deal in deals:
        item = DealResponse(
            id=deal.id,
            product_name=deal.product_name,
            brand=deal.brand,
            model=deal.model,
            category=deal.category,
            color=deal.color,
            gender=deal.gender,
            original_price=float(deal.original_price) if deal.original_price else None,
            sale_price=float(deal.sale_price),
            discount_pct=float(deal.discount_percent) if deal.discount_percent else None,
            product_url=deal.product_url,
            image_url=deal.image_url,
            sizes_available=deal.sizes_available,
            stock_available=deal.stock_available,
            source_name=deal.source.name if deal.source else None,
            detected_at=deal.detected_at,
            vinted_stats=VintedStatsResponse(
                nb_listings=deal.vinted_stats.nb_listings,
                price_min=float(deal.vinted_stats.price_min) if deal.vinted_stats.price_min else None,
                price_max=float(deal.vinted_stats.price_max) if deal.vinted_stats.price_max else None,
                price_median=float(deal.vinted_stats.price_median) if deal.vinted_stats.price_median else None,
                margin_euro=float(deal.vinted_stats.margin_euro) if deal.vinted_stats.margin_euro else None,
                margin_pct=float(deal.vinted_stats.margin_percent) if deal.vinted_stats.margin_percent else None,
                liquidity_score=float(deal.vinted_stats.liquidity_score) if deal.vinted_stats.liquidity_score else None,
            ) if deal.vinted_stats else None,
            score=DealScoreResponse(
                flip_score=float(deal.score.flip_score),
                margin_score=float(deal.score.margin_score) if deal.score.margin_score else None,
                liquidity_score=float(deal.score.liquidity_score) if deal.score.liquidity_score else None,
                popularity_score=float(deal.score.popularity_score) if deal.score.popularity_score else None,
                score_breakdown=ScoreBreakdownResponse(**deal.score.score_breakdown) if deal.score.score_breakdown else None,
                recommended_action=deal.score.recommended_action,
                recommended_price=float(deal.score.recommended_price) if deal.score.recommended_price else None,
                confidence=float(deal.score.confidence) if deal.score.confidence else None,
                explanation_short=deal.score.explanation_short,
                risks=deal.score.risks,
                estimated_sell_days=deal.score.estimated_sell_days,
            ) if deal.score else None,
        )
        items.append(item)

    return DealsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single deal by ID."""

    result = await db.execute(
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score),
        )
        .where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    return DealResponse(
        id=deal.id,
        product_name=deal.product_name,
        brand=deal.brand,
        model=deal.model,
        category=deal.category,
        color=deal.color,
        gender=deal.gender,
        original_price=float(deal.original_price) if deal.original_price else None,
        sale_price=float(deal.sale_price),
        discount_pct=float(deal.discount_percent) if deal.discount_percent else None,
        product_url=deal.product_url,
        image_url=deal.image_url,
        sizes_available=deal.sizes_available,
        stock_available=deal.stock_available,
        source_name=deal.source.name if deal.source else None,
        detected_at=deal.detected_at,
        vinted_stats=VintedStatsResponse(
            nb_listings=deal.vinted_stats.nb_listings,
            price_min=float(deal.vinted_stats.price_min) if deal.vinted_stats.price_min else None,
            price_max=float(deal.vinted_stats.price_max) if deal.vinted_stats.price_max else None,
            price_median=float(deal.vinted_stats.price_median) if deal.vinted_stats.price_median else None,
            margin_euro=float(deal.vinted_stats.margin_euro) if deal.vinted_stats.margin_euro else None,
            margin_pct=float(deal.vinted_stats.margin_percent) if deal.vinted_stats.margin_percent else None,
            liquidity_score=float(deal.vinted_stats.liquidity_score) if deal.vinted_stats.liquidity_score else None,
        ) if deal.vinted_stats else None,
        score=DealScoreResponse(
            flip_score=float(deal.score.flip_score),
            margin_score=float(deal.score.margin_score) if deal.score.margin_score else None,
            liquidity_score=float(deal.score.liquidity_score) if deal.score.liquidity_score else None,
            popularity_score=float(deal.score.popularity_score) if deal.score.popularity_score else None,
            score_breakdown=ScoreBreakdownResponse(**deal.score.score_breakdown) if deal.score.score_breakdown else None,
            recommended_action=deal.score.recommended_action,
            recommended_price=float(deal.score.recommended_price) if deal.score.recommended_price else None,
            confidence=float(deal.score.confidence) if deal.score.confidence else None,
            explanation_short=deal.score.explanation_short,
            risks=deal.score.risks,
            estimated_sell_days=deal.score.estimated_sell_days,
        ) if deal.score else None,
    )


@router.get("/{deal_id}/ai-analysis")
async def get_deal_ai_analysis(
    deal_id: UUID,
    refresh_vinted: bool = Query(False, description="Force refresh Vinted data"),
    include_llm: bool = Query(True, description="Include LLM-powered explanation"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get full AI analysis for a deal.

    Returns detailed FlipScore breakdown, LLM explanation, risks, opportunities, and tips.
    """

    # Get deal
    result = await db.execute(
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score),
        )
        .where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    # Get Vinted stats (refresh or use cached)
    if refresh_vinted or not deal.vinted_stats:
        vinted_stats = await get_vinted_stats_for_deal(
            product_name=deal.product_name,
            brand=deal.brand,
            sale_price=float(deal.sale_price),
            category=deal.category
        )
    else:
        vinted_stats = {
            "nb_listings": deal.vinted_stats.nb_listings,
            "price_min": float(deal.vinted_stats.price_min) if deal.vinted_stats.price_min else None,
            "price_max": float(deal.vinted_stats.price_max) if deal.vinted_stats.price_max else None,
            "price_median": float(deal.vinted_stats.price_median) if deal.vinted_stats.price_median else None,
            "price_p25": float(deal.vinted_stats.price_p25) if deal.vinted_stats.price_p25 else None,
            "price_p75": float(deal.vinted_stats.price_p75) if deal.vinted_stats.price_p75 else None,
            "margin_euro": float(deal.vinted_stats.margin_euro) if deal.vinted_stats.margin_euro else 0,
            "margin_percent": float(deal.vinted_stats.margin_percent) if deal.vinted_stats.margin_percent else 0,
            "liquidity_score": float(deal.vinted_stats.liquidity_score) if deal.vinted_stats.liquidity_score else 0,
        }

    # Build deal data
    deal_data = {
        "product_name": deal.product_name,
        "brand": deal.brand,
        "model": deal.model,
        "sale_price": float(deal.sale_price),
        "original_price": float(deal.original_price) if deal.original_price else None,
        "discount_percent": float(deal.discount_percent) if deal.discount_percent else 0,
        "category": deal.category,
        "color": deal.color,
        "gender": deal.gender,
        "sizes_available": deal.sizes_available,
        "product_url": deal.product_url,
        "image_url": deal.image_url,
        "source_name": deal.source.name if deal.source else None,
    }

    # User preferences
    user_preferences = None
    if current_user and current_user.preferences:
        user_preferences = {
            "min_margin": current_user.preferences.get("min_margin", 20),
            "categories": current_user.preferences.get("categories", []),
            "sizes": current_user.preferences.get("sizes", []),
            "risk_profile": current_user.preferences.get("risk_profile", "balanced"),
        }

    # Run AI analysis
    analysis = await ai_service.analyze_deal(
        deal_data=deal_data,
        vinted_stats=vinted_stats,
        user_preferences=user_preferences,
        include_llm_analysis=include_llm
    )

    return {
        "deal_id": str(deal_id),
        "deal": deal_data,
        "vinted_stats": vinted_stats,
        "analysis": analysis,
    }


@router.get("/top/recommended", response_model=List[DealResponse])
async def get_top_recommended_deals(
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get top recommended deals by FlipScore."""

    # Use outerjoin to handle cases where no DealScore exists yet
    query = (
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score),
        )
        .outerjoin(DealScore)
        .where(Deal.status == DealStatus.ACTIVE)
    )

    # Apply user category filter from preferences
    if user and user.preferences:
        user_categories = user.preferences.get("categories", [])
        if user_categories and len(user_categories) > 0:
            query = query.where(Deal.category.in_(user_categories))

    if category:
        query = query.where(Deal.category == category)

    # Filter for recommended deals if they have scores, otherwise just get active deals
    query = query.where(
        or_(
            DealScore.recommended_action == "buy",
            DealScore.id.is_(None)  # Include deals without scores
        )
    )

    # Order by flip_score (nulls last) and limit
    query = query.order_by(DealScore.flip_score.desc().nullslast()).limit(limit)

    result = await db.execute(query)
    deals = result.scalars().unique().all()

    return [
        DealResponse(
            id=deal.id,
            product_name=deal.product_name,
            brand=deal.brand,
            model=deal.model,
            category=deal.category,
            color=deal.color,
            gender=deal.gender,
            original_price=float(deal.original_price) if deal.original_price else None,
            sale_price=float(deal.sale_price),
            discount_pct=float(deal.discount_percent) if deal.discount_percent else None,
            product_url=deal.product_url,
            image_url=deal.image_url,
            sizes_available=deal.sizes_available,
            stock_available=deal.stock_available,
            source_name=deal.source.name if deal.source else None,
            detected_at=deal.detected_at,
            vinted_stats=VintedStatsResponse(
                nb_listings=deal.vinted_stats.nb_listings,
                price_min=float(deal.vinted_stats.price_min) if deal.vinted_stats.price_min else None,
                price_max=float(deal.vinted_stats.price_max) if deal.vinted_stats.price_max else None,
                price_median=float(deal.vinted_stats.price_median) if deal.vinted_stats.price_median else None,
                margin_euro=float(deal.vinted_stats.margin_euro) if deal.vinted_stats.margin_euro else None,
                margin_pct=float(deal.vinted_stats.margin_percent) if deal.vinted_stats.margin_percent else None,
                liquidity_score=float(deal.vinted_stats.liquidity_score) if deal.vinted_stats.liquidity_score else None,
            ) if deal.vinted_stats else None,
            score=DealScoreResponse(
                flip_score=float(deal.score.flip_score),
                margin_score=float(deal.score.margin_score) if deal.score.margin_score else None,
                liquidity_score=float(deal.score.liquidity_score) if deal.score.liquidity_score else None,
                popularity_score=float(deal.score.popularity_score) if deal.score.popularity_score else None,
                score_breakdown=ScoreBreakdownResponse(**deal.score.score_breakdown) if deal.score.score_breakdown else None,
                recommended_action=deal.score.recommended_action,
                recommended_price=float(deal.score.recommended_price) if deal.score.recommended_price else None,
                confidence=float(deal.score.confidence) if deal.score.confidence else None,
                explanation_short=deal.score.explanation_short,
                risks=deal.score.risks,
                estimated_sell_days=deal.score.estimated_sell_days,
            ) if deal.score else None,
        )
        for deal in deals
    ]
