"""
Router Scraping - Gestion des jobs de scraping
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
from loguru import logger

from database import get_db, Deal, ScrapingLog, ScrapingLogStatus
from routers.users import get_current_user, User
from services.scraping_orchestrator import ScrapingOrchestrator
from config import SCRAPING_SOURCES, settings

router = APIRouter()

# ============= SCHEMAS =============

class SourceResponse(BaseModel):
    name: str
    slug: str
    base_url: str
    is_active: bool
    priority: int
    total_deals: int = 0
    plan_required: str = "free"

    class Config:
        from_attributes = True

class ScrapingJobResponse(BaseModel):
    job_id: str
    status: str
    source: str
    started_at: datetime
    deals_found: int = 0

class ManualScrapeRequest(BaseModel):
    source_slug: Optional[str] = None
    sources: Optional[List[str]] = None
    send_alerts: Optional[bool] = True


class SystemSettingsResponse(BaseModel):
    use_rotating_proxy: bool
    proxy_count: int
    scrape_interval_minutes: int
    max_concurrent_scrapers: int
    min_margin_percent: float
    min_flip_score: int


class SystemSettingsUpdate(BaseModel):
    use_rotating_proxy: Optional[bool] = None
    scrape_interval_minutes: Optional[int] = None
    max_concurrent_scrapers: Optional[int] = None
    min_margin_percent: Optional[float] = None
    min_flip_score: Optional[int] = None


class ScrapingLogResponse(BaseModel):
    id: uuid.UUID
    source_slug: str
    source_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    deals_found: int
    deals_new: int
    deals_updated: int
    error_message: Optional[str]
    triggered_by: str
    proxy_used: bool

    class Config:
        from_attributes = True


class ScrapingLogsListResponse(BaseModel):
    logs: List[ScrapingLogResponse]
    total: int
    page: int
    page_size: int

# ============= ENDPOINTS =============

@router.get("/sources", response_model=List[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db)
):
    """
    Liste toutes les sources de scraping configurées (from config + deal counts)
    """
    # Get deal counts per source from database
    counts_query = (
        select(Deal.source, func.count(Deal.id))
        .where(Deal.in_stock == True)
        .group_by(Deal.source)
    )
    counts_result = await db.execute(counts_query)
    source_counts = {row[0]: row[1] for row in counts_result.fetchall()}

    response_sources = []
    for slug, config in SCRAPING_SOURCES.items():
        source_dict = {
            "name": config["name"],
            "slug": slug,
            "base_url": config["base_url"],
            "is_active": config["enabled"],
            "priority": config["priority"],
            "total_deals": source_counts.get(slug, 0),
            "plan_required": config.get("plan_required", "free")
        }
        response_sources.append(SourceResponse(**source_dict))

    return response_sources


@router.get("/sources/{source_slug}", response_model=SourceResponse)
async def get_source(
    source_slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère une source spécifique
    """
    config = SCRAPING_SOURCES.get(source_slug)
    if not config:
        raise HTTPException(status_code=404, detail="Source non trouvée")

    # Get deal count
    count_query = select(func.count(Deal.id)).where(Deal.source == source_slug, Deal.in_stock == True)
    count_result = await db.execute(count_query)
    total_deals = count_result.scalar() or 0

    return SourceResponse(
        name=config["name"],
        slug=source_slug,
        base_url=config["base_url"],
        is_active=config["enabled"],
        priority=config["priority"],
        total_deals=total_deals,
        plan_required=config.get("plan_required", "free")
    )


@router.post("/run")
async def trigger_scraping(
    request: ManualScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Déclenche un scraping manuel (admin/pro uniquement)
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(
            status_code=403,
            detail="Le scraping manuel est réservé aux plans Pro et Agency"
        )

    orchestrator = ScrapingOrchestrator(db)

    source_to_scrape = request.source_slug
    sources_to_scrape = request.sources
    send_alerts = request.send_alerts if request.send_alerts is not None else True

    if source_to_scrape:
        background_tasks.add_task(
            orchestrator.run_all_scrapers,
            sources=[source_to_scrape],
            send_alerts=send_alerts,
            triggered_by="manual"
        )
        return {
            "status": "started",
            "message": f"Scraping de {source_to_scrape} démarré",
            "source": source_to_scrape
        }
    elif sources_to_scrape and len(sources_to_scrape) > 0:
        background_tasks.add_task(
            orchestrator.run_all_scrapers,
            sources=[s.lower() for s in sources_to_scrape],
            send_alerts=send_alerts,
            triggered_by="manual"
        )
        return {
            "status": "started",
            "message": f"Scraping de {len(sources_to_scrape)} source(s) démarré",
            "sources": sources_to_scrape
        }
    else:
        background_tasks.add_task(
            orchestrator.run_all_scrapers,
            send_alerts=send_alerts,
            triggered_by="manual"
        )
        return {
            "status": "started",
            "message": "Scraping de toutes les sources démarré",
            "sources": list(SCRAPING_SOURCES.keys())
        }


@router.get("/status")
async def get_scraping_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Statut actuel du scraping
    """
    # Sources stats from config
    total_sources = len(SCRAPING_SOURCES)
    active_sources = sum(1 for cfg in SCRAPING_SOURCES.values() if cfg.get("enabled", True))

    # Get last scraping logs
    recent_query = (
        select(ScrapingLog)
        .order_by(desc(ScrapingLog.started_at))
        .limit(5)
    )
    recent_result = await db.execute(recent_query)
    recent_logs = recent_result.scalars().all()

    recent_scrapes = [
        {
            "source": log.source_name,
            "last_scraped": log.started_at,
            "error": log.error_message
        }
        for log in recent_logs
    ]

    # Deals today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    deals_query = select(func.count(Deal.id)).where(Deal.first_seen_at >= today)
    deals_result = await db.execute(deals_query)
    deals_today = deals_result.scalar() or 0

    return {
        "total_sources": total_sources,
        "active_sources": active_sources,
        "deals_today": deals_today,
        "recent_scrapes": recent_scrapes
    }


@router.get("/settings", response_model=SystemSettingsResponse)
async def get_system_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les paramètres système (admin uniquement)
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from config import settings
    from services.proxy_service import get_proxy_rotator

    proxy_count = 0
    try:
        rotator = await get_proxy_rotator()
        proxy_count = len(rotator.proxies)
    except Exception:
        pass

    return SystemSettingsResponse(
        use_rotating_proxy=settings.USE_ROTATING_PROXY,
        proxy_count=proxy_count,
        scrape_interval_minutes=settings.SCRAPE_INTERVAL_MINUTES,
        max_concurrent_scrapers=settings.MAX_CONCURRENT_SCRAPERS,
        min_margin_percent=settings.MIN_MARGIN_PERCENT,
        min_flip_score=settings.MIN_FLIP_SCORE
    )


@router.patch("/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour les paramètres système (admin uniquement).
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from config import settings
    from services.proxy_service import get_proxy_rotator

    update_data = settings_update.model_dump(exclude_unset=True)

    if "use_rotating_proxy" in update_data:
        settings.USE_ROTATING_PROXY = update_data["use_rotating_proxy"]
        if update_data["use_rotating_proxy"]:
            try:
                rotator = await get_proxy_rotator()
                await rotator.initialize()
            except Exception as e:
                logger.warning(f"Erreur lors du rechargement des proxies: {e}")

    if "scrape_interval_minutes" in update_data:
        settings.SCRAPE_INTERVAL_MINUTES = update_data["scrape_interval_minutes"]

    if "max_concurrent_scrapers" in update_data:
        settings.MAX_CONCURRENT_SCRAPERS = update_data["max_concurrent_scrapers"]

    if "min_margin_percent" in update_data:
        settings.MIN_MARGIN_PERCENT = update_data["min_margin_percent"]

    if "min_flip_score" in update_data:
        settings.MIN_FLIP_SCORE = update_data["min_flip_score"]

    proxy_count = 0
    try:
        rotator = await get_proxy_rotator()
        proxy_count = len(rotator.proxies)
    except Exception:
        pass

    return SystemSettingsResponse(
        use_rotating_proxy=settings.USE_ROTATING_PROXY,
        proxy_count=proxy_count,
        scrape_interval_minutes=settings.SCRAPE_INTERVAL_MINUTES,
        max_concurrent_scrapers=settings.MAX_CONCURRENT_SCRAPERS,
        min_margin_percent=settings.MIN_MARGIN_PERCENT,
        min_flip_score=settings.MIN_FLIP_SCORE
    )


# ============= SCRAPING LOGS ENDPOINTS =============

@router.get("/logs", response_model=ScrapingLogsListResponse)
async def list_scraping_logs(
    page: int = 1,
    page_size: int = 50,
    source_slug: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste les logs de scraping avec pagination
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    query = select(ScrapingLog)

    if source_slug:
        query = query.where(ScrapingLog.source_slug == source_slug)
    if status:
        query = query.where(ScrapingLog.status == status)

    count_query = select(func.count(ScrapingLog.id))
    if source_slug:
        count_query = count_query.where(ScrapingLog.source_slug == source_slug)
    if status:
        count_query = count_query.where(ScrapingLog.status == status)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(desc(ScrapingLog.started_at)).offset(offset).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return ScrapingLogsListResponse(
        logs=[ScrapingLogResponse(
            id=log.id,
            source_slug=log.source_slug,
            source_name=log.source_name,
            status=log.status.value,
            started_at=log.started_at,
            completed_at=log.completed_at,
            duration_seconds=log.duration_seconds,
            deals_found=log.deals_found,
            deals_new=log.deals_new,
            deals_updated=log.deals_updated,
            error_message=log.error_message,
            triggered_by=log.triggered_by,
            proxy_used=log.proxy_used
        ) for log in logs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/logs/stats")
async def get_scraping_logs_stats(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques des logs de scraping
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    cutoff = datetime.utcnow() - timedelta(days=days)

    total_query = select(func.count(ScrapingLog.id)).where(ScrapingLog.started_at >= cutoff)
    total_result = await db.execute(total_query)
    total_logs = total_result.scalar() or 0

    status_query = (
        select(ScrapingLog.status, func.count(ScrapingLog.id))
        .where(ScrapingLog.started_at >= cutoff)
        .group_by(ScrapingLog.status)
    )
    status_result = await db.execute(status_query)
    by_status = {row[0].value: row[1] for row in status_result.fetchall()}

    deals_query = (
        select(
            func.sum(ScrapingLog.deals_found),
            func.sum(ScrapingLog.deals_new)
        )
        .where(ScrapingLog.started_at >= cutoff)
        .where(ScrapingLog.status == ScrapingLogStatus.COMPLETED)
    )
    deals_result = await db.execute(deals_query)
    deals_row = deals_result.fetchone()
    total_deals_found = deals_row[0] or 0
    total_deals_new = deals_row[1] or 0

    duration_query = (
        select(func.avg(ScrapingLog.duration_seconds))
        .where(ScrapingLog.started_at >= cutoff)
        .where(ScrapingLog.status == ScrapingLogStatus.COMPLETED)
    )
    duration_result = await db.execute(duration_query)
    avg_duration = duration_result.scalar() or 0

    source_query = (
        select(
            ScrapingLog.source_name,
            func.count(ScrapingLog.id),
            func.sum(ScrapingLog.deals_found)
        )
        .where(ScrapingLog.started_at >= cutoff)
        .group_by(ScrapingLog.source_name)
    )
    source_result = await db.execute(source_query)
    by_source = [
        {"source": row[0], "runs": row[1], "deals_found": row[2] or 0}
        for row in source_result.fetchall()
    ]

    return {
        "period_days": days,
        "total_logs": total_logs,
        "by_status": by_status,
        "total_deals_found": total_deals_found,
        "total_deals_new": total_deals_new,
        "avg_duration_seconds": round(avg_duration, 2) if avg_duration else 0,
        "by_source": by_source
    }
