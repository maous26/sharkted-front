"""
Router Analytics - Statistiques et analyses
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import (
    get_db, Deal, VintedStats, DealScore, Source, 
    Outcome, User, DealStatus, ActionType
)
from routers.users import get_current_user

router = APIRouter()

# ============= SCHEMAS =============

class BrandStats(BaseModel):
    brand: str
    total_deals: int
    avg_discount: float
    avg_margin: float
    avg_flip_score: float
    best_deal_score: float

class CategoryStats(BaseModel):
    category: str
    total_deals: int
    avg_margin: float
    avg_flip_score: float

class SourceStats(BaseModel):
    source: str
    total_deals: int
    avg_discount: float
    last_scraped: Optional[datetime]

class TrendData(BaseModel):
    date: str
    deals_count: int
    avg_flip_score: float
    avg_margin: float

# ============= ENDPOINTS =============

@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques principales pour le dashboard
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total active deals
    total_query = select(func.count(Deal.id)).where(Deal.status == DealStatus.ACTIVE)
    total_result = await db.execute(total_query)
    total_deals = total_result.scalar() or 0

    # Deals today
    today_query = select(func.count(Deal.id)).where(Deal.detected_at >= today)
    today_result = await db.execute(today_query)
    deals_today = today_result.scalar() or 0

    # Average flip score
    avg_score_query = (
        select(func.avg(DealScore.flip_score))
        .select_from(DealScore)
        .join(Deal)
        .where(Deal.status == DealStatus.ACTIVE)
    )
    avg_score_result = await db.execute(avg_score_query)
    avg_flip_score = avg_score_result.scalar() or 0

    # Active deals (Score >= 60)
    active_query = (
        select(func.count(Deal.id))
        .join(DealScore)
        .where(and_(
            Deal.status == DealStatus.ACTIVE,
            DealScore.flip_score >= 60
        ))
    )
    active_result = await db.execute(active_query)
    active_deals = active_result.scalar() or 0

    # Top deals count (score >= 80 for top deals section)
    top_query = (
        select(func.count(Deal.id))
        .join(DealScore)
        .where(and_(
            Deal.status == DealStatus.ACTIVE,
            DealScore.flip_score >= 80
        ))
    )
    top_result = await db.execute(top_query)
    top_deals_count = top_result.scalar() or 0

    # Total sources
    sources_query = select(func.count(Source.id)).where(Source.is_active == True)
    sources_result = await db.execute(sources_query)
    total_sources = sources_result.scalar() or 0

    # Last scan time
    last_scan_query = select(func.max(Source.last_scraped_at))
    last_scan_result = await db.execute(last_scan_query)
    last_scan = last_scan_result.scalar()

    return {
        "active_deals": active_deals,
        "total_deals": total_deals,
        "deals_today": deals_today,
        "avg_flip_score": round(avg_flip_score, 1) if avg_flip_score else 0,
        "top_deals_count": top_deals_count,
        "total_sources": total_sources,
        "last_scan": last_scan.isoformat() if last_scan else None
    }


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Vue d'ensemble des analytics
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    # Total deals
    total_query = select(func.count(Deal.id)).where(Deal.detected_at >= since)
    total_result = await db.execute(total_query)
    total_deals = total_result.scalar() or 0
    
    # Active deals
    active_query = select(func.count(Deal.id)).where(Deal.status == DealStatus.ACTIVE)
    active_result = await db.execute(active_query)
    active_deals = active_result.scalar() or 0
    
    # Deals avec bon score (>= 70)
    good_query = (
        select(func.count(Deal.id))
        .join(DealScore)
        .where(and_(
            Deal.detected_at >= since,
            DealScore.flip_score >= 70
        ))
    )
    good_result = await db.execute(good_query)
    good_deals = good_result.scalar() or 0
    
    # Excellent deals (>= 85)
    excellent_query = (
        select(func.count(Deal.id))
        .join(DealScore)
        .where(and_(
            Deal.detected_at >= since,
            DealScore.flip_score >= 85
        ))
    )
    excellent_result = await db.execute(excellent_query)
    excellent_deals = excellent_result.scalar() or 0
    
    # Average flip score
    avg_score_query = (
        select(func.avg(DealScore.flip_score))
        .join(Deal)
        .where(Deal.detected_at >= since)
    )
    avg_score_result = await db.execute(avg_score_query)
    avg_flip_score = avg_score_result.scalar() or 0
    
    # Average margin
    avg_margin_query = (
        select(func.avg(VintedStats.margin_percent))
        .join(Deal)
        .where(Deal.detected_at >= since)
    )
    avg_margin_result = await db.execute(avg_margin_query)
    avg_margin = avg_margin_result.scalar() or 0
    
    # Best margin
    best_margin_query = (
        select(func.max(VintedStats.margin_percent))
        .join(Deal)
        .where(Deal.detected_at >= since)
    )
    best_margin_result = await db.execute(best_margin_query)
    best_margin = best_margin_result.scalar() or 0
    
    return {
        "period_days": days,
        "total_deals_detected": total_deals,
        "active_deals": active_deals,
        "good_deals": good_deals,
        "excellent_deals": excellent_deals,
        "average_flip_score": round(avg_flip_score, 1) if avg_flip_score else 0,
        "average_margin_percent": round(avg_margin, 1) if avg_margin else 0,
        "best_margin_percent": round(best_margin, 1) if best_margin else 0,
        "good_deals_rate": round(good_deals / total_deals * 100, 1) if total_deals > 0 else 0
    }


@router.get("/by-brand", response_model=List[BrandStats])
async def get_stats_by_brand(
    limit: int = Query(20, ge=1, le=50),
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques par marque
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(
            Deal.brand,
            func.count(Deal.id).label("total_deals"),
            func.avg(Deal.discount_percent).label("avg_discount"),
            func.avg(VintedStats.margin_percent).label("avg_margin"),
            func.avg(DealScore.flip_score).label("avg_flip_score"),
            func.max(DealScore.flip_score).label("best_deal_score")
        )
        .outerjoin(VintedStats, Deal.id == VintedStats.deal_id)
        .outerjoin(DealScore, Deal.id == DealScore.deal_id)
        .where(and_(
            Deal.detected_at >= since,
            Deal.brand.isnot(None)
        ))
        .group_by(Deal.brand)
        .order_by(desc("total_deals"))
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        BrandStats(
            brand=row.brand or "Unknown",
            total_deals=row.total_deals,
            avg_discount=round(row.avg_discount or 0, 1),
            avg_margin=round(row.avg_margin or 0, 1),
            avg_flip_score=round(row.avg_flip_score or 0, 1),
            best_deal_score=round(row.best_deal_score or 0, 1)
        )
        for row in rows
    ]


@router.get("/by-category", response_model=List[CategoryStats])
async def get_stats_by_category(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques par catégorie
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(
            Deal.category,
            func.count(Deal.id).label("total_deals"),
            func.avg(VintedStats.margin_percent).label("avg_margin"),
            func.avg(DealScore.flip_score).label("avg_flip_score")
        )
        .outerjoin(VintedStats, Deal.id == VintedStats.deal_id)
        .outerjoin(DealScore, Deal.id == DealScore.deal_id)
        .where(Deal.detected_at >= since)
        .group_by(Deal.category)
        .order_by(desc("total_deals"))
    )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        CategoryStats(
            category=row.category or "autre",
            total_deals=row.total_deals,
            avg_margin=round(row.avg_margin or 0, 1),
            avg_flip_score=round(row.avg_flip_score or 0, 1)
        )
        for row in rows
    ]


@router.get("/by-source", response_model=List[SourceStats])
async def get_stats_by_source(
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques par source de scraping
    """
    query = (
        select(
            Source.name,
            func.count(Deal.id).label("total_deals"),
            func.avg(Deal.discount_percent).label("avg_discount"),
            Source.last_scraped_at
        )
        .outerjoin(Deal, Source.id == Deal.source_id)
        .group_by(Source.id)
        .order_by(desc("total_deals"))
    )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        SourceStats(
            source=row.name,
            total_deals=row.total_deals or 0,
            avg_discount=round(row.avg_discount or 0, 1),
            last_scraped=row.last_scraped_at
        )
        for row in rows
    ]


@router.get("/trends", response_model=List[TrendData])
async def get_trends(
    days: int = Query(14, ge=7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Tendances journalières des deals
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(
            func.date(Deal.detected_at).label("date"),
            func.count(Deal.id).label("deals_count"),
            func.avg(DealScore.flip_score).label("avg_flip_score"),
            func.avg(VintedStats.margin_percent).label("avg_margin")
        )
        .outerjoin(DealScore, Deal.id == DealScore.deal_id)
        .outerjoin(VintedStats, Deal.id == VintedStats.deal_id)
        .where(Deal.detected_at >= since)
        .group_by(func.date(Deal.detected_at))
        .order_by("date")
    )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        TrendData(
            date=str(row.date),
            deals_count=row.deals_count,
            avg_flip_score=round(row.avg_flip_score or 0, 1),
            avg_margin=round(row.avg_margin or 0, 1)
        )
        for row in rows
    ]


@router.get("/my-performance")
async def get_user_performance(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Performance personnelle de l'utilisateur
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    # Outcomes bought
    bought_query = (
        select(
            func.count(Outcome.id).label("total"),
            func.sum(Outcome.buy_price).label("total_invested")
        )
        .where(and_(
            Outcome.user_id == current_user.id,
            Outcome.action == ActionType.BOUGHT,
            Outcome.created_at >= since
        ))
    )
    bought_result = await db.execute(bought_query)
    bought_row = bought_result.fetchone()

    # Outcomes sold
    sold_query = (
        select(
            func.count(Outcome.id).label("total"),
            func.sum(Outcome.sell_price).label("total_revenue"),
            func.sum(Outcome.actual_margin_euro).label("total_profit"),
            func.avg(Outcome.actual_margin_percent).label("avg_margin"),
            func.avg(Outcome.days_to_sell).label("avg_days")
        )
        .where(and_(
            Outcome.user_id == current_user.id,
            Outcome.sold == True,
            Outcome.sell_date >= since
        ))
    )
    sold_result = await db.execute(sold_query)
    sold_row = sold_result.fetchone()

    # Safely handle None for bought_row and sold_row
    total_bought = bought_row.total if bought_row and bought_row.total is not None else 0
    total_invested = bought_row.total_invested if bought_row and bought_row.total_invested is not None else 0

    total_sold = sold_row.total if sold_row and sold_row.total is not None else 0
    total_revenue = sold_row.total_revenue if sold_row and sold_row.total_revenue is not None else 0
    total_profit = sold_row.total_profit if sold_row and sold_row.total_profit is not None else 0
    avg_margin = sold_row.avg_margin if sold_row and sold_row.avg_margin is not None else 0
    avg_days = sold_row.avg_days if sold_row and sold_row.avg_days is not None else 0

    return {
        "period_days": days,
        "total_bought": total_bought,
        "total_sold": total_sold,
        "pending": total_bought - total_sold,
        "total_invested": round(total_invested, 2),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "roi_percent": round(total_profit / total_invested * 100, 1) if total_invested > 0 else 0,
        "average_margin_percent": round(avg_margin, 1),
        "average_days_to_sell": round(avg_days, 1),
        "success_rate": round(total_sold / total_bought * 100, 1) if total_bought > 0 else 0
    }