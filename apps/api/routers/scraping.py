"""
Router Scraping - Gestion des jobs de scraping
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
from loguru import logger

from database import get_db, Source, Deal, ScrapingLog, ScrapingLogStatus
from routers.users import get_current_user, User
from services.scraping_orchestrator import ScrapingOrchestrator
from config import SCRAPING_SOURCES, settings

router = APIRouter()

# ============= SCHEMAS =============

class SourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    base_url: str
    is_active: bool
    priority: int
    last_scraped_at: Optional[datetime]
    last_error: Optional[str]
    total_deals_found: int
    plan_required: str = "free"  # "free" or "pro"

    class Config:
        from_attributes = True

class SourceUpdate(BaseModel):
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class ScrapingJobResponse(BaseModel):
    job_id: str
    status: str
    source: str
    started_at: datetime
    deals_found: int = 0

class ManualScrapeRequest(BaseModel):
    source_slug: Optional[str] = None  # None = all sources
    sources: Optional[List[str]] = None  # Support array from frontend
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
    Liste toutes les sources de scraping configurées
    """
    query = select(Source).order_by(Source.priority, Source.name)
    result = await db.execute(query)
    sources = result.scalars().all()

    # Add plan_required from config
    response_sources = []
    for source in sources:
        source_dict = {
            "id": source.id,
            "name": source.name,
            "slug": source.slug,
            "base_url": source.base_url,
            "is_active": source.is_active,
            "priority": source.priority,
            "last_scraped_at": source.last_scraped_at,
            "last_error": source.last_error,
            "total_deals_found": source.total_deals_found,
            "plan_required": SCRAPING_SOURCES.get(source.slug, {}).get("plan_required", "free")
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
    query = select(Source).where(Source.slug == source_slug)
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    return SourceResponse.model_validate(source)


@router.patch("/sources/{source_slug}", response_model=SourceResponse)
async def update_source(
    source_slug: str,
    source_update: SourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Met à jour une source (admin uniquement)
    """
    # Check admin (simple check - en prod utiliser des rôles)
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    query = select(Source).where(Source.slug == source_slug)
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    
    await db.commit()
    await db.refresh(source)
    
    return SourceResponse.model_validate(source)


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

    # Support both source_slug (single) and sources (array from frontend)
    source_to_scrape = request.source_slug
    sources_to_scrape = request.sources
    send_alerts = request.send_alerts if request.send_alerts is not None else True

    if source_to_scrape:
        # Scrape une source spécifique (single slug)
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
        # Scrape multiple sources from frontend array
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
        # Scrape toutes les sources
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
    from sqlalchemy import func
    
    # Sources stats
    sources_query = (
        select(
            func.count(Source.id).label("total"),
            func.count(Source.id).filter(Source.is_active == True).label("active")
        )
    )
    sources_result = await db.execute(sources_query)
    sources_row = sources_result.fetchone()
    
    # Recent scrapes
    recent_query = (
        select(Source.name, Source.last_scraped_at, Source.last_error)
        .where(Source.last_scraped_at.isnot(None))
        .order_by(Source.last_scraped_at.desc())
        .limit(5)
    )
    recent_result = await db.execute(recent_query)
    recent_scrapes = [
        {
            "source": row.name,
            "last_scraped": row.last_scraped_at,
            "error": row.last_error
        }
        for row in recent_result.fetchall()
    ]
    
    # Deals today
    from datetime import timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    deals_query = select(func.count(Deal.id)).where(Deal.detected_at >= today)
    deals_result = await db.execute(deals_query)
    deals_today = deals_result.scalar() or 0
    
    return {
        "total_sources": sources_row.total,
        "active_sources": sources_row.active,
        "deals_today": deals_today,
        "recent_scrapes": recent_scrapes
    }


@router.post("/init-sources")
async def initialize_sources(
    db: AsyncSession = Depends(get_db)
):
    """
    Initialise les sources de scraping dans la base de données
    """
    created = []
    
    for slug, config in SCRAPING_SOURCES.items():
        # Check if exists
        query = select(Source).where(Source.slug == slug)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if not existing:
            source = Source(
                name=config["name"],
                slug=slug,
                base_url=config["base_url"],
                is_active=config["enabled"],
                priority=config["priority"],
                scraper_config={"categories": config["categories"]}
            )
            db.add(source)
            created.append(slug)
    
    await db.commit()

    return {
        "message": f"{len(created)} sources créées",
        "sources_created": created
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

    # Obtenir le nombre de proxies du service centralisé
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
    Note: Les changements sont appliqués en mémoire et persistent jusqu'au redémarrage.
    Les proxies sont utilisés par tous les scrapers (Vinted, Nike, Adidas, etc.)
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from config import settings
    from services.proxy_service import get_proxy_rotator

    update_data = settings_update.model_dump(exclude_unset=True)

    # Apply updates to runtime settings
    if "use_rotating_proxy" in update_data:
        settings.USE_ROTATING_PROXY = update_data["use_rotating_proxy"]
        # If enabling proxies, force reload via centralized service
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

    # Obtenir le nombre de proxies
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


@router.post("/settings/reload-proxies")
async def reload_proxies(
    current_user: User = Depends(get_current_user)
):
    """
    Force le rechargement de la liste des proxies.
    Les proxies sont partagés par tous les scrapers (Vinted, Nike, Adidas, etc.)
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from services.proxy_service import get_proxy_rotator, _proxy_rotator

    # Réinitialiser le rotateur pour forcer le rechargement
    global _proxy_rotator
    try:
        # Créer un nouveau rotateur qui rechargera les proxies
        from services.proxy_service import ProxyRotator
        webshare_url = getattr(settings, 'WEBSHARE_PROXY_URL', None) or settings.PROXY_URL

        new_rotator = ProxyRotator(
            webshare_api_url=webshare_url if webshare_url and "webshare" in webshare_url else None
        )
        await new_rotator.initialize()

        # Remplacer l'instance globale
        import services.proxy_service as proxy_module
        proxy_module._proxy_rotator = new_rotator

        proxy_count = len(new_rotator.proxies)
        success = proxy_count > 0

        return {
            "success": success,
            "proxy_count": proxy_count,
            "message": f"{proxy_count} proxies chargés pour tous les scrapers" if success else "Échec du chargement des proxies"
        }
    except Exception as e:
        logger.error(f"Erreur rechargement proxies: {e}")
        return {
            "success": False,
            "proxy_count": 0,
            "message": f"Erreur: {str(e)}"
        }


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

    from sqlalchemy import func, desc

    # Build query
    query = select(ScrapingLog)

    # Filters
    if source_slug:
        query = query.where(ScrapingLog.source_slug == source_slug)
    if status:
        query = query.where(ScrapingLog.status == status)

    # Count total
    count_query = select(func.count(ScrapingLog.id))
    if source_slug:
        count_query = count_query.where(ScrapingLog.source_slug == source_slug)
    if status:
        count_query = count_query.where(ScrapingLog.status == status)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Paginate and order
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


@router.delete("/logs/{log_id}")
async def delete_scraping_log(
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprime un log de scraping spécifique
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    query = select(ScrapingLog).where(ScrapingLog.id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")

    await db.delete(log)
    await db.commit()

    return {"success": True, "message": "Log supprimé"}


@router.delete("/logs")
async def delete_scraping_logs(
    older_than_days: Optional[int] = None,
    source_slug: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprime plusieurs logs de scraping.
    - older_than_days: Supprime les logs plus vieux que N jours
    - source_slug: Filtre par source
    - status: Filtre par statut
    Sans paramètres, supprime tous les logs.
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from sqlalchemy import delete as sql_delete
    from datetime import timedelta

    query = sql_delete(ScrapingLog)

    if older_than_days:
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        query = query.where(ScrapingLog.started_at < cutoff)
    if source_slug:
        query = query.where(ScrapingLog.source_slug == source_slug)
    if status:
        query = query.where(ScrapingLog.status == status)

    result = await db.execute(query)
    await db.commit()

    deleted_count = result.rowcount
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"{deleted_count} logs supprimés"
    }


@router.post("/rescrape-vinted-stats")
async def rescrape_vinted_stats(
    background_tasks: BackgroundTasks,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rescrape les stats Vinted pour tous les deals existants (admin uniquement).
    Utilise les nouveaux filtres améliorés pour obtenir des prix plus réalistes.
    """
    if current_user.plan.value not in ["pro", "agency"]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from services.vinted_service import get_vinted_stats_for_deal
    from services.scoring_service import score_deal
    from models.vinted_stats import VintedStats
    from models.deal_score import DealScore

    async def rescrape_all_deals():
        """Background task to rescrape all deals"""
        from database import async_session

        logger.info(f"🔄 Démarrage du rescraping Vinted pour {limit} deals...")

        async with async_session() as session:
            # Get all deals with their current stats
            query = (
                select(Deal)
                .order_by(Deal.first_seen_at.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            deals = result.scalars().all()

            updated_count = 0
            error_count = 0

            for deal in deals:
                try:
                    # Get new Vinted stats with improved filtering
                    new_stats = await get_vinted_stats_for_deal(
                        product_name=deal.title,
                        brand=deal.seller_name,
                        sale_price=float(deal.price),
                        category=deal.category
                    )

                    if new_stats.get("nb_listings", 0) > 0:
                        # Update or create VintedStats
                        existing_stats_query = select(VintedStats).where(VintedStats.deal_id == deal.id)
                        existing_result = await session.execute(existing_stats_query)
                        existing_stats = existing_result.scalar_one_or_none()

                        if existing_stats:
                            # Update existing stats
                            existing_stats.nb_listings = new_stats.get("nb_listings", 0)
                            existing_stats.price_min = new_stats.get("price_min")
                            existing_stats.price_max = new_stats.get("price_max")
                            existing_stats.price_avg = new_stats.get("price_avg")
                            existing_stats.price_median = new_stats.get("price_median")
                            existing_stats.price_p25 = new_stats.get("price_p25")
                            existing_stats.price_p75 = new_stats.get("price_p75")
                            existing_stats.margin_euro = new_stats.get("margin_euro")
                            existing_stats.margin_pct = new_stats.get("margin_percent")
                            existing_stats.liquidity_score = new_stats.get("liquidity_score")
                            existing_stats.sample_listings = new_stats.get("sample_listings", [])
                            existing_stats.search_query = new_stats.get("query_used", "")
                            existing_stats.updated_at = datetime.utcnow()
                        else:
                            # Create new stats
                            new_vinted_stats = VintedStats(
                                deal_id=deal.id,
                                nb_listings=new_stats.get("nb_listings", 0),
                                price_min=new_stats.get("price_min"),
                                price_max=new_stats.get("price_max"),
                                price_avg=new_stats.get("price_avg"),
                                price_median=new_stats.get("price_median"),
                                price_p25=new_stats.get("price_p25"),
                                price_p75=new_stats.get("price_p75"),
                                margin_euro=new_stats.get("margin_euro"),
                                margin_pct=new_stats.get("margin_percent"),
                                liquidity_score=new_stats.get("liquidity_score"),
                                sample_listings=new_stats.get("sample_listings", []),
                                search_query=new_stats.get("query_used", "")
                            )
                            session.add(new_vinted_stats)

                        # Re-score the deal with new stats
                        deal_data = {
                            "product_name": deal.title,
                            "brand": deal.seller_name,
                            "sale_price": float(deal.price),
                            "category": deal.category,
                            "discount_percent": float(deal.discount_percent) if deal.discount_percent else 0,
                            "sizes_available": deal.sizes_available or [],
                            "color": deal.color
                        }

                        new_score = await score_deal(deal_data, new_stats)

                        # Update or create DealScore
                        existing_score_query = select(DealScore).where(DealScore.deal_id == deal.id)
                        existing_score_result = await session.execute(existing_score_query)
                        existing_score = existing_score_result.scalar_one_or_none()

                        if existing_score:
                            existing_score.flip_score = new_score.get("flip_score", 0)
                            existing_score.margin_score = new_score.get("margin_score")
                            existing_score.liquidity_score = new_score.get("liquidity_score")
                            existing_score.popularity_score = new_score.get("popularity_score")
                            existing_score.recommended_action = new_score.get("recommended_action", "ignore")
                            existing_score.recommended_price = new_score.get("recommended_price")
                            existing_score.confidence = new_score.get("confidence")
                            existing_score.explanation = new_score.get("explanation")
                            existing_score.risks = new_score.get("risks", [])
                            existing_score.estimated_sell_days = new_score.get("estimated_sell_days")
                            existing_score.updated_at = datetime.utcnow()

                        updated_count += 1
                        logger.debug(f"✅ Deal {deal.id}: Médiane Vinted = {new_stats.get('price_median')}€")

                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Erreur rescraping deal {deal.id}: {e}")

                # Rate limiting between requests
                import asyncio
                await asyncio.sleep(1.5)

            await session.commit()
            logger.info(f"🎉 Rescraping terminé: {updated_count} deals mis à jour, {error_count} erreurs")

    background_tasks.add_task(rescrape_all_deals)

    return {
        "status": "started",
        "message": f"Rescraping Vinted démarré pour {limit} deals",
        "limit": limit
    }


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

    from sqlalchemy import func
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Total logs
    total_query = select(func.count(ScrapingLog.id)).where(ScrapingLog.started_at >= cutoff)
    total_result = await db.execute(total_query)
    total_logs = total_result.scalar() or 0

    # By status
    status_query = (
        select(ScrapingLog.status, func.count(ScrapingLog.id))
        .where(ScrapingLog.started_at >= cutoff)
        .group_by(ScrapingLog.status)
    )
    status_result = await db.execute(status_query)
    by_status = {row[0].value: row[1] for row in status_result.fetchall()}

    # Total deals
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

    # Average duration
    duration_query = (
        select(func.avg(ScrapingLog.duration_seconds))
        .where(ScrapingLog.started_at >= cutoff)
        .where(ScrapingLog.status == ScrapingLogStatus.COMPLETED)
    )
    duration_result = await db.execute(duration_query)
    avg_duration = duration_result.scalar() or 0

    # By source
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