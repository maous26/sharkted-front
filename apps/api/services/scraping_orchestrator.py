"""Scraping orchestrator for managing scraping jobs."""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database import Deal, VintedStats, DealScore, ScrapingLog, ScrapingLogStatus
from scrapers import SCRAPERS, ScrapedProduct
import traceback
from services.scoring_service import ScoringEngine as ScoringService
from services.discord_service import send_discord_alert
from services.proxy_service import get_proxy_rotator, get_rotating_proxy
from services.ai_service import ai_service
from services.vinted_service import get_vinted_stats_for_deal
from config import settings, SCRAPING_SOURCES

logger = logging.getLogger(__name__)


class ScrapingOrchestrator:
    """Orchestrates scraping jobs across multiple sources."""

    def __init__(
        self,
        db: AsyncSession,
        scoring_service: Optional[ScoringService] = None,
    ):
        self.db = db
        self.scoring_service = scoring_service or ScoringService()

    async def run_all_scrapers(
        self,
        sources: Optional[List[str]] = None,
        send_alerts: bool = True,
        triggered_by: str = "scheduler",
    ) -> Dict[str, Any]:
        """Run all active scrapers and process results."""

        results = {
            "total_scraped": 0,
            "total_new_deals": 0,
            "total_scored": 0,
            "alerts_sent": 0,
            "errors": [],
            "by_source": {},
        }

        # Get active sources from config
        if sources:
            active_sources = [s for s in sources if s in SCRAPING_SOURCES and SCRAPING_SOURCES[s].get("enabled", True)]
        else:
            active_sources = [slug for slug, cfg in SCRAPING_SOURCES.items() if cfg.get("enabled", True) and slug in SCRAPERS]

        if not active_sources:
            active_sources = list(SCRAPERS.keys())

        # Run scrapers with concurrency limit
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_SCRAPERS)

        async def run_with_semaphore(source_name: str):
            async with semaphore:
                return await self._run_single_scraper(source_name, triggered_by=triggered_by)

        # Run scrapers concurrently
        tasks = [run_with_semaphore(name) for name in active_sources]
        scraper_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        all_new_deals = []

        for source_name, result in zip(active_sources, scraper_results):
            if isinstance(result, Exception):
                results["errors"].append({
                    "source": source_name,
                    "error": str(result),
                })
                results["by_source"][source_name] = {
                    "status": "error",
                    "error": str(result),
                }
                continue

            results["by_source"][source_name] = result
            results["total_scraped"] += result.get("scraped", 0)
            results["total_new_deals"] += result.get("new_deals", 0)

            if result.get("deals"):
                all_new_deals.extend(result["deals"])

        # Score new deals
        if all_new_deals:
            scored_deals = await self._score_deals(all_new_deals)
            results["total_scored"] = len(scored_deals)

            # Send alerts for top deals
            if send_alerts:
                alerts_sent = await self._send_alerts(scored_deals)
                results["alerts_sent"] = alerts_sent

        return results

    async def _run_single_scraper(self, source_name: str, triggered_by: str = "scheduler") -> Dict[str, Any]:
        """Run a single scraper and save results."""

        result = {
            "status": "success",
            "scraped": 0,
            "new_deals": 0,
            "updated_deals": 0,
            "deals": [],
        }

        scraper_class = SCRAPERS.get(source_name)
        if not scraper_class:
            raise ValueError(f"Unknown scraper: {source_name}")

        # Get source config
        source_config = SCRAPING_SOURCES.get(source_name, {})
        source_display_name = source_config.get("name", source_name.replace("_", " ").title())

        # Get proxy info
        proxy_url = None
        proxy_used = False
        if settings.USE_ROTATING_PROXY:
            proxy_url = await get_rotating_proxy()
            proxy_used = proxy_url is not None
            logger.info(f"Using rotating proxy for {source_name}: {proxy_url[:30]}..." if proxy_url else f"No proxy available for {source_name}")
        elif settings.PROXY_URL:
            proxy_url = settings.PROXY_URL
            proxy_used = True

        # Create scraping log entry
        scraping_log = ScrapingLog(
            source_slug=source_name,
            source_name=source_display_name,
            status="started",
            triggered_by=triggered_by,
            proxy_used=proxy_used,
        )
        self.db.add(scraping_log)
        await self.db.flush()

        start_time = datetime.utcnow()

        try:
            # Update log status to in_progress
            scraping_log.status = "in_progress"
            await self.db.flush()

            # Run scraper with proxy
            scraper = scraper_class(proxy_url=proxy_url)
            products = await scraper.run()

            result["scraped"] = len(products)

            # Save products as deals
            new_deals, updated_count = await self._save_products_with_count(products, source_name)
            result["new_deals"] = len(new_deals)
            result["updated_deals"] = updated_count
            result["deals"] = new_deals

            # Update log with success
            end_time = datetime.utcnow()
            scraping_log.status = "completed"
            scraping_log.completed_at = end_time
            scraping_log.duration_seconds = (end_time - start_time).total_seconds()
            scraping_log.deals_found = len(products)
            scraping_log.deals_new = len(new_deals)
            scraping_log.deals_updated = updated_count

        except Exception as e:
            logger.error(f"Scraper {source_name} failed: {e}")

            # Update log with failure
            end_time = datetime.utcnow()
            scraping_log.status = ScrapingLogStatus.FAILED
            scraping_log.completed_at = end_time
            scraping_log.duration_seconds = (end_time - start_time).total_seconds()
            scraping_log.error_message = str(e)
            scraping_log.error_traceback = traceback.format_exc()

            raise

        finally:
            await self.db.flush()
            await self.db.commit()

        return result

    async def _save_products_with_count(
        self,
        products: List[ScrapedProduct],
        source_name: str,
    ) -> tuple[List[Deal], int]:
        """Save scraped products as deals and return count of updated deals."""

        new_deals = []
        updated_count = 0

        for product in products:
            # Check if deal already exists
            result = await self.db.execute(
                select(Deal)
                .where(Deal.source == source_name)
                .where(Deal.external_id == product.external_id)
            )
            existing_deal = result.scalar_one_or_none()

            if existing_deal:
                # Update existing deal
                existing_deal.price = float(product.sale_price)
                existing_deal.original_price = float(product.original_price) if product.original_price else None
                existing_deal.discount_percent = float(product.discount_pct) if product.discount_pct else None
                existing_deal.in_stock = product.stock_available
                existing_deal.sizes_available = product.sizes_available
                existing_deal.last_seen_at = datetime.utcnow()
                updated_count += 1
                continue

            # Create new deal
            deal = Deal(
                source=source_name,
                external_id=product.external_id,
                title=product.product_name,
                brand=product.brand,
                model=product.model,
                category=product.category,
                color=product.color,
                gender=product.gender,
                original_price=float(product.original_price) if product.original_price else None,
                price=float(product.sale_price),
                discount_percent=float(product.discount_pct) if product.discount_pct else None,
                url=product.product_url,
                image_url=product.image_url,
                in_stock=product.stock_available,
                sizes_available=product.sizes_available,
            )
            self.db.add(deal)
            new_deals.append(deal)

        await self.db.flush()
        return new_deals, updated_count

    async def _score_deals(self, deals: List[Deal]) -> List[Deal]:
        """Score deals using AI service with Vinted market data."""

        scored_deals = []

        for deal in deals:
            try:
                # 1. Get Vinted market stats
                vinted_stats = await get_vinted_stats_for_deal(
                    product_name=deal.title,
                    brand=deal.brand,
                    sale_price=float(deal.price),
                    category=deal.category
                )

                # 2. Save Vinted stats to database
                if vinted_stats.get("nb_listings", 0) > 0:
                    vinted_record = VintedStats(
                        deal_id=deal.id,
                        nb_listings=vinted_stats.get("nb_listings", 0),
                        price_min=float(vinted_stats.get("price_min", 0)) if vinted_stats.get("price_min") else None,
                        price_max=float(vinted_stats.get("price_max", 0)) if vinted_stats.get("price_max") else None,
                        price_median=float(vinted_stats.get("price_median", 0)) if vinted_stats.get("price_median") else None,
                        price_p25=float(vinted_stats.get("price_p25", 0)) if vinted_stats.get("price_p25") else None,
                        price_p75=float(vinted_stats.get("price_p75", 0)) if vinted_stats.get("price_p75") else None,
                        margin_euro=float(vinted_stats.get("margin_euro", 0)),
                        margin_pct=float(vinted_stats.get("margin_percent", 0)),
                        liquidity_score=float(vinted_stats.get("liquidity_score", 0)),
                    )
                    self.db.add(vinted_record)
                    deal.vinted_stats = vinted_record

                # 3. Run AI analysis
                deal_data = {
                    "product_name": deal.title,
                    "brand": deal.brand,
                    "model": deal.model,
                    "sale_price": float(deal.price),
                    "original_price": float(deal.original_price) if deal.original_price else None,
                    "discount_percent": float(deal.discount_percent) if deal.discount_percent else 0,
                    "category": deal.category,
                    "color": deal.color,
                    "gender": deal.gender,
                    "sizes_available": deal.sizes_available,
                }

                # Quick analysis without LLM for batch processing
                analysis = await ai_service.analyze_deal(
                    deal_data=deal_data,
                    vinted_stats=vinted_stats,
                    include_llm_analysis=False
                )

                # 4. Create DealScore from AI analysis
                score_record = DealScore(
                    deal_id=deal.id,
                    flip_score=float(analysis.get("flip_score", 0)),
                    popularity_score=float(analysis.get("score_components", {}).get("popularity_score", 0)),
                    recommended_action=analysis.get("recommended_action", "ignore"),
                    recommended_price=float(analysis.get("recommended_price", 0)) if analysis.get("recommended_price") else None,
                    confidence=float(analysis.get("confidence", 0)),
                    explanation_short=analysis.get("explanation_short", ""),
                    risks=analysis.get("risks", []),
                    estimated_sell_days=analysis.get("estimated_sell_days"),
                    model_version=analysis.get("model_version", "ai_mvp_v1"),
                )
                self.db.add(score_record)
                deal.deal_score = score_record

                scored_deals.append(deal)
                logger.info(f"Scored deal {deal.title}: FlipScore={analysis.get('flip_score', 0)}")

            except Exception as e:
                logger.warning(f"Error scoring deal {deal.id}: {e}")

        await self.db.flush()
        return scored_deals

    async def _send_alerts(self, deals: List[Deal]) -> int:
        """Send alerts for deals above threshold."""

        alerts_sent = 0

        for deal in deals:
            if not deal.deal_score:
                continue

            # Check if deal meets alert threshold
            if float(deal.deal_score.flip_score) < settings.MIN_FLIP_SCORE:
                continue

            # Build alert data
            deal_data = {
                "product_name": deal.title,
                "brand": deal.brand,
                "model": deal.model,
                "original_price": float(deal.original_price) if deal.original_price else 0,
                "sale_price": float(deal.price),
                "discount_percent": float(deal.discount_percent) if deal.discount_percent else 0,
                "product_url": deal.url,
                "image_url": deal.image_url,
                "source": deal.source,
            }

            score_data = {
                "flip_score": float(deal.deal_score.flip_score),
                "margin_euro": float(deal.vinted_stats.margin_euro) if deal.vinted_stats and deal.vinted_stats.margin_euro else 0,
                "margin_percent": float(deal.vinted_stats.margin_pct) if deal.vinted_stats and deal.vinted_stats.margin_pct else 0,
                "liquidity_score": float(deal.vinted_stats.liquidity_score) if deal.vinted_stats and deal.vinted_stats.liquidity_score else 0,
                "nb_listings": deal.vinted_stats.nb_listings if deal.vinted_stats else 0,
                "recommended_action": deal.deal_score.recommended_action,
                "recommended_price": float(deal.deal_score.recommended_price) if deal.deal_score.recommended_price else 0,
                "explanation_short": deal.deal_score.explanation_short,
                "risks": deal.deal_score.risks or [],
            }

            try:
                webhook_url = settings.DISCORD_WEBHOOK_URL if hasattr(settings, 'DISCORD_WEBHOOK_URL') else None
                if webhook_url:
                    alert_data = {**deal_data, **score_data}
                    sent = await send_discord_alert(webhook_url, alert_data)
                    if sent:
                        alerts_sent += 1
            except Exception as e:
                logger.warning(f"Error sending alert for deal {deal.id}: {e}")

        return alerts_sent

    async def run_scheduled(self):
        """Run as scheduled job (called by scheduler)."""
        try:
            results = await self.run_all_scrapers(send_alerts=True)
            logger.info(f"Scheduled scraping completed: {results['total_new_deals']} new deals")
            return results
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")
            raise
