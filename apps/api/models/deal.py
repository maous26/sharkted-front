"""
Router Deals - Gestion des deals/opportunités
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid

from database import get_db, Deal, VintedStats, DealScore, DealStatus, RecommendedAction

router = APIRouter()

# ============= SCHEMAS =============

class DealBase(BaseModel):
    product_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    original_price: float
    sale_price: float
    product_url: str
    image_url: Optional[str] = None

class VintedStatsResponse(BaseModel):
    nb_listings: int
    price_min: Optional[float]
    price_max: Optional[float]
    price_avg: Optional[float]
    price_median: Optional[float]
    margin_euro: Optional[float]
    margin_percent: Optional[float]
    liquidity_score: Optional[float]
    
    class Config:
        from_attributes = True

class DealScoreResponse(BaseModel):
    flip_score: float
    popularity_score: float
    liquidity_score: float
    margin_score: float
    recommended_action: str
    recommended_price: Optional[float]
    confidence: float
    explanation: Optional[str]
    risks: Optional[List[str]]
    estimated_sell_days: Optional[int]
    
    class Config:
        from_attributes = True

class DealResponse(BaseModel):
    id: uuid.UUID
    source_name: Optional[str] = None
    external_id: str
    product_name: str
    brand: Optional[str]
    model: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    color: Optional[str]
    gender: Optional[str]
    original_price: float
    sale_price: float
    discount_percent: float
    sizes_available: Optional[List[str]]
    product_url: str
    image_url: Optional[str]
    status: str
    detected_at: datetime
    
    vinted_stats: Optional[VintedStatsResponse] = None
    score: Optional[DealScoreResponse] = None
    
    class Config:
        from_attributes = True

class DealListResponse(BaseModel):
    deals: List[DealResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class DealFilters(BaseModel):
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_discount: Optional[float] = None
    max_price: Optional[float] = None
    min_flip_score: Optional[float] = None
    min_margin: Optional[float] = None
    sizes: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    recommended_only: bool = False

# ============= ENDPOINTS =============

@router.get("/", response_model=DealListResponse)
async def list_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("flip_score", regex="^(flip_score|detected_at|margin_percent|discount_percent)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    # Filters
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_discount: Optional[float] = None,
    max_price: Optional[float] = None,
    min_flip_score: Optional[float] = None,
    min_margin: Optional[float] = None,
    search: Optional[str] = None,
    status: Optional[str] = Query("active"),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste des deals avec filtres et pagination
    
    - **page**: Numéro de page (défaut: 1)
    - **per_page**: Nombre de résultats par page (défaut: 20, max: 100)
    - **sort_by**: Champ de tri (flip_score, detected_at, margin_percent, discount_percent)
    - **sort_order**: Ordre de tri (asc, desc)
    """
    
    # Build query
    query = select(Deal).options(
        selectinload(Deal.source),
        selectinload(Deal.vinted_stats),
        selectinload(Deal.score)
    )
    
    # Apply filters
    conditions = []
    
    if status:
        conditions.append(Deal.status == status)
    
    if brand:
        conditions.append(func.lower(Deal.brand) == brand.lower())
    
    if category:
        conditions.append(func.lower(Deal.category) == category.lower())
    
    if min_discount:
        conditions.append(Deal.discount_percent >= min_discount)
    
    if max_price:
        conditions.append(Deal.sale_price <= max_price)
    
    if search:
        search_term = f"%{search}%"
        conditions.append(
            or_(
                Deal.product_name.ilike(search_term),
                Deal.brand.ilike(search_term),
                Deal.model.ilike(search_term)
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Join for score-based filters
    if min_flip_score or min_margin:
        query = query.join(DealScore, Deal.id == DealScore.deal_id, isouter=True)
        if min_flip_score:
            query = query.where(DealScore.flip_score >= min_flip_score)
    
    if min_margin:
        query = query.join(VintedStats, Deal.id == VintedStats.deal_id, isouter=True)
        query = query.where(VintedStats.margin_percent >= min_margin)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply sorting
    if sort_by == "flip_score":
        query = query.join(DealScore, Deal.id == DealScore.deal_id, isouter=True)
        sort_column = DealScore.flip_score
    elif sort_by == "margin_percent":
        query = query.join(VintedStats, Deal.id == VintedStats.deal_id, isouter=True)
        sort_column = VintedStats.margin_percent
    elif sort_by == "discount_percent":
        sort_column = Deal.discount_percent
    else:
        sort_column = Deal.detected_at
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Execute
    result = await db.execute(query)
    deals = result.scalars().unique().all()
    
    # Transform to response
    deals_response = []
    for deal in deals:
        deal_dict = {
            "id": deal.id,
            "source_name": deal.source.name if deal.source else None,
            "external_id": deal.external_id,
            "product_name": deal.product_name,
            "brand": deal.brand,
            "model": deal.model,
            "category": deal.category,
            "subcategory": deal.subcategory,
            "color": deal.color,
            "gender": deal.gender,
            "original_price": deal.original_price,
            "sale_price": deal.sale_price,
            "discount_percent": deal.discount_percent,
            "sizes_available": deal.sizes_available,
            "product_url": deal.product_url,
            "image_url": deal.image_url,
            "status": deal.status.value,
            "detected_at": deal.detected_at,
            "vinted_stats": deal.vinted_stats,
            "score": deal.score
        }
        deals_response.append(DealResponse(**deal_dict))
    
    return DealListResponse(
        deals=deals_response,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


@router.get("/top", response_model=List[DealResponse])
async def get_top_deals(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère les meilleurs deals des dernières X heures
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = (
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score)
        )
        .join(DealScore, Deal.id == DealScore.deal_id)
        .where(
            and_(
                Deal.status == DealStatus.ACTIVE,
                Deal.detected_at >= since,
                DealScore.flip_score >= 70
            )
        )
        .order_by(desc(DealScore.flip_score))
        .limit(limit)
    )
    
    result = await db.execute(query)
    deals = result.scalars().unique().all()
    
    return [
        DealResponse(
            id=deal.id,
            source_name=deal.source.name if deal.source else None,
            external_id=deal.external_id,
            product_name=deal.product_name,
            brand=deal.brand,
            model=deal.model,
            category=deal.category,
            subcategory=deal.subcategory,
            color=deal.color,
            gender=deal.gender,
            original_price=deal.original_price,
            sale_price=deal.sale_price,
            discount_percent=deal.discount_percent,
            sizes_available=deal.sizes_available,
            product_url=deal.product_url,
            image_url=deal.image_url,
            status=deal.status.value,
            detected_at=deal.detected_at,
            vinted_stats=deal.vinted_stats,
            score=deal.score
        )
        for deal in deals
    ]


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère les détails d'un deal spécifique
    """
    query = (
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score)
        )
        .where(Deal.id == deal_id)
    )
    
    result = await db.execute(query)
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal non trouvé")
    
    return DealResponse(
        id=deal.id,
        source_name=deal.source.name if deal.source else None,
        external_id=deal.external_id,
        product_name=deal.product_name,
        brand=deal.brand,
        model=deal.model,
        category=deal.category,
        subcategory=deal.subcategory,
        color=deal.color,
        gender=deal.gender,
        original_price=deal.original_price,
        sale_price=deal.sale_price,
        discount_percent=deal.discount_percent,
        sizes_available=deal.sizes_available,
        product_url=deal.product_url,
        image_url=deal.image_url,
        status=deal.status.value,
        detected_at=deal.detected_at,
        vinted_stats=deal.vinted_stats,
        score=deal.score
    )


@router.get("/stats/summary")
async def get_deals_summary(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques résumées des deals
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Total deals actifs
    total_query = select(func.count(Deal.id)).where(Deal.status == DealStatus.ACTIVE)
    total_result = await db.execute(total_query)
    total_active = total_result.scalar() or 0
    
    # Nouveaux deals
    new_query = select(func.count(Deal.id)).where(
        and_(Deal.status == DealStatus.ACTIVE, Deal.detected_at >= since)
    )
    new_result = await db.execute(new_query)
    new_deals = new_result.scalar() or 0
    
    # Deals avec bon score
    good_query = (
        select(func.count(Deal.id))
        .join(DealScore)
        .where(
            and_(
                Deal.status == DealStatus.ACTIVE,
                DealScore.flip_score >= 70
            )
        )
    )
    good_result = await db.execute(good_query)
    good_deals = good_result.scalar() or 0
    
    # Meilleure marge
    best_margin_query = (
        select(func.max(VintedStats.margin_percent))
        .join(Deal)
        .where(Deal.status == DealStatus.ACTIVE)
    )
    best_margin_result = await db.execute(best_margin_query)
    best_margin = best_margin_result.scalar() or 0
    
    # Répartition par catégorie
    category_query = (
        select(Deal.category, func.count(Deal.id))
        .where(Deal.status == DealStatus.ACTIVE)
        .group_by(Deal.category)
    )
    category_result = await db.execute(category_query)
    categories = {row[0] or "autre": row[1] for row in category_result.fetchall()}
    
    return {
        "total_active": total_active,
        "new_last_hours": new_deals,
        "hours": hours,
        "good_deals_count": good_deals,
        "best_margin_percent": round(best_margin, 1) if best_margin else 0,
        "by_category": categories
    }