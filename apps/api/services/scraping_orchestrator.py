"""Scraping orchestrator for managing scraping jobs."""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models import Source, Deal, VintedStats, DealScore, ScrapingLog, ScrapingLogStatus
from scrapers import SCRAPERS, ScrapedProduct
import traceback
from services.scoring_service import ScoringEngine as ScoringService
from services.discord_service import send_discord_alert
from services.proxy_service import get_proxy_rotator, get_rotating_proxy
from services.ai_service import ai_service
from services.vinted_service import get_vinted_stats_for_deal
from config import settings

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

        # Get active sources from database
        if sources:
            # If specific sources requested, still check if they are active
            db_sources_result = await self.db.execute(
                select(Source).where(Source.slug.in_(sources))
            )
            db_sources = {s.slug: s for s in db_sources_result.scalars().all()}
            active_sources = [s for s in sources if s in db_sources and db_sources[s].is_active]

            # Log disabled sources
            disabled = [s for s in sources if s not in active_sources]
            if disabled:
                logger.info(f"Skipping disabled sources: {disabled}")
        else:
            # Get only active sources from database
            db_sources_result = await self.db.execute(
                select(Source).where(Source.is_active == True)
            )
            db_sources = db_sources_result.scalars().all()
            active_sources = [s.slug for s in db_sources if s.slug in SCRAPERS]

            # If no active sources in DB, use all scrapers (first run)
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

        # Send summary to Discord (disabled - discord_service not implemented as class)
        # if send_alerts and results["total_new_deals"] > 0:
        #     top_deals = self._get_top_deals(all_new_deals, limit=5)
        #     logger.info(f"Would send Discord summary for {results['total_new_deals']} deals")

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

        # Get or create source record
        source = await self._get_or_create_source(source_name, scraper_class)

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
            source_name=source.name if source else source_name.replace("_", " ").title(),
            status=ScrapingLogStatus.STARTED,
            triggered_by=triggered_by,
            proxy_used=proxy_used,
        )
        self.db.add(scraping_log)
        await self.db.flush()

        start_time = datetime.utcnow()

        try:
            # Update log status to in_progress
            scraping_log.status = ScrapingLogStatus.IN_PROGRESS
            await self.db.flush()

            # Run scraper with proxy
            scraper = scraper_class(proxy_url=proxy_url)
            products = await scraper.run()

            result["scraped"] = len(products)

            # Save products as deals
            new_deals, updated_count = await self._save_products_with_count(products, source)
            result["new_deals"] = len(new_deals)
            result["updated_deals"] = updated_count
            result["deals"] = new_deals

            # Update source stats
            await self._update_source_stats(source, len(products), success=True)

            # Update log with success
            end_time = datetime.utcnow()
            scraping_log.status = ScrapingLogStatus.COMPLETED
            scraping_log.completed_at = end_time
            scraping_log.duration_seconds = (end_time - start_time).total_seconds()
            scraping_log.deals_found = len(products)
            scraping_log.deals_new = len(new_deals)
            scraping_log.deals_updated = updated_count

        except Exception as e:
            logger.error(f"Scraper {source_name} failed: {e}")
            await self._update_source_stats(source, 0, success=False, error=str(e))

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

    async def _get_or_create_source(
        self,
        source_name: str,
        scraper_class,
    ) -> Source:
        """Get or create a source record."""

        result = await self.db.execute(
            select(Source).where(Source.name == source_name)
        )
        source = result.scalar_one_or_none()

        if not source:
            source = Source(
                name=source_name,
                display_name=source_name.replace("_", " ").title(),
                base_url=scraper_class.BASE_URL,
                is_active=True,
            )
            self.db.add(source)
            await self.db.flush()

        return source

    async def _save_products(
        self,
        products: List[ScrapedProduct],
        source: Source,
    ) -> List[Deal]:
        """Save scraped products as deals."""
        new_deals, _ = await self._save_products_with_count(products, source)
        return new_deals

    async def _save_products_with_count(
        self,
        products: List[ScrapedProduct],
        source: Source,
    ) -> tuple[List[Deal], int]:
        """Save scraped products as deals and return count of updated deals."""

        new_deals = []
        updated_count = 0

        for product in products:
            # Check if deal already exists
            result = await self.db.execute(
                select(Deal)
                .where(Deal.source_id == source.id)
                .where(Deal.external_id == product.external_id)
            )
            existing_deal = result.scalar_one_or_none()

            if existing_deal:
                # Update existing deal
                existing_deal.sale_price = Decimal(str(product.sale_price))
                existing_deal.original_price = Decimal(str(product.original_price)) if product.original_price else None
                existing_deal.discount_percent = Decimal(str(product.discount_pct)) if product.discount_pct else None
                existing_deal.stock_available = product.stock_available
                existing_deal.sizes_available = product.sizes_available
                existing_deal.updated_at = datetime.utcnow()
                updated_count += 1
                continue

            # Create new deal
            deal = Deal(
                source_id=source.id,
                external_id=product.external_id,
                product_name=product.product_name,
                brand=product.brand,
                model=product.model,
                category=product.category,
                subcategory=product.subcategory,
                color=product.color,
                gender=product.gender,
                sku=product.sku,
                original_price=Decimal(str(product.original_price)) if product.original_price else None,
                sale_price=Decimal(str(product.sale_price)),
                discount_percent=Decimal(str(product.discount_pct)) if product.discount_pct else None,
                product_url=product.product_url,
                image_url=product.image_url,
                stock_available=product.stock_available,
                sizes_available=product.sizes_available,
                is_active=True,
            )
            self.db.add(deal)
            new_deals.append(deal)

        await self.db.flush()
        return new_deals, updated_count

    async def _update_source_stats(
        self,
        source: Source,
        deals_found: int,
        success: bool,
        error: Optional[str] = None,
    ):
        """Update source scraping statistics."""

        source.last_scraped_at = datetime.utcnow()

        if success:
            source.last_success_at = datetime.utcnow()
            source.total_deals_found = str(int(source.total_deals_found or "0") + deals_found)
            source.error_count = "0"
        else:
            source.error_count = str(int(source.error_count or "0") + 1)

    async def _score_deals(self, deals: List[Deal]) -> List[Deal]:
        """Score deals using AI service with Vinted market data."""

        scored_deals = []

        for deal in deals:
            try:
                # 1. Get Vinted market stats
                vinted_stats = await get_vinted_stats_for_deal(
                    product_name=deal.product_name,
                    brand=deal.brand,
                    sale_price=float(deal.sale_price),
                    category=deal.category
                )

                # 2. Save Vinted stats to database
                if vinted_stats.get("nb_listings", 0) > 0:
                    vinted_record = VintedStats(
                        deal_id=deal.id,
                        nb_listings=vinted_stats.get("nb_listings", 0),
                        price_min=Decimal(str(vinted_stats.get("price_min", 0))) if vinted_stats.get("price_min") else None,
                        price_max=Decimal(str(vinted_stats.get("price_max", 0))) if vinted_stats.get("price_max") else None,
                        price_median=Decimal(str(vinted_stats.get("price_median", 0))) if vinted_stats.get("price_median") else None,
                        price_p25=Decimal(str(vinted_stats.get("price_p25", 0))) if vinted_stats.get("price_p25") else None,
                        price_p75=Decimal(str(vinted_stats.get("price_p75", 0))) if vinted_stats.get("price_p75") else None,
                        margin_euro=Decimal(str(vinted_stats.get("margin_euro", 0))),
                        margin_percent=Decimal(str(vinted_stats.get("margin_percent", 0))),
                        liquidity_score=Decimal(str(vinted_stats.get("liquidity_score", 0))),
                    )
                    self.db.add(vinted_record)
                    deal.vinted_stats = vinted_record

                # 3. Run AI analysis
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
                }

                # Quick analysis without LLM for batch processing
                analysis = await ai_service.analyze_deal(
                    deal_data=deal_data,
                    vinted_stats=vinted_stats,
                    include_llm_analysis=False  # Disable LLM for batch to save costs/time
                )

                # 4. Create DealScore from AI analysis
                score_record = DealScore(
                    deal_id=deal.id,
                    flip_score=Decimal(str(analysis.get("flip_score", 0))),
                    popularity_score=Decimal(str(analysis.get("score_components", {}).get("popularity_score", 0))),
                    recommended_action=analysis.get("recommended_action", "ignore"),
                    recommended_price=Decimal(str(analysis.get("recommended_price", 0))) if analysis.get("recommended_price") else None,
                    confidence=Decimal(str(analysis.get("confidence", 0))),
                    explanation_short=analysis.get("explanation_short", ""),
                    risks=analysis.get("risks", []),
                    estimated_sell_days=analysis.get("estimated_sell_days"),
                    model_version=analysis.get("model_version", "ai_mvp_v1"),
                )
                self.db.add(score_record)
                deal.score = score_record

                scored_deals.append(deal)
                logger.info(f"Scored deal {deal.product_name}: FlipScore={analysis.get('flip_score', 0)}")

            except Exception as e:
                logger.warning(f"Error scoring deal {deal.id}: {e}")

        await self.db.flush()
        return scored_deals

    async def _send_alerts(self, deals: List[Deal]) -> int:
        """Send alerts for deals above threshold."""

        alerts_sent = 0

        for deal in deals:
            if not deal.score:
                continue

            # Check if deal meets alert threshold
            if float(deal.score.flip_score) < settings.min_flip_score:
                continue

            # Build alert data
            deal_data = {
                "product_name": deal.product_name,
                "brand": deal.brand,
                "model": deal.model,
                "original_price": float(deal.original_price) if deal.original_price else 0,
                "sale_price": float(deal.sale_price),
                "discount_percent": float(deal.discount_percent) if deal.discount_percent else 0,
                "product_url": deal.product_url,
                "image_url": deal.image_url,
                "source": deal.source.display_name if deal.source else "Unknown",
            }

            score_data = {
                "flip_score": float(deal.score.flip_score),
                "margin_euro": float(deal.vinted_stats.margin_euro) if deal.vinted_stats and deal.vinted_stats.margin_euro else 0,
                "margin_percent": float(deal.vinted_stats.margin_percent) if deal.vinted_stats and deal.vinted_stats.margin_percent else 0,
                "liquidity_score": float(deal.vinted_stats.liquidity_score) if deal.vinted_stats and deal.vinted_stats.liquidity_score else 0,
                "nb_listings": deal.vinted_stats.nb_listings if deal.vinted_stats else 0,
                "recommended_action": deal.score.recommended_action,
                "recommended_price": float(deal.score.recommended_price) if deal.score.recommended_price else 0,
                "explanation_short": deal.score.explanation_short,
                "risks": deal.score.risks or [],
            }

            try:
                # Use the function-based discord alert
                webhook_url = settings.DISCORD_WEBHOOK_URL if hasattr(settings, 'DISCORD_WEBHOOK_URL') else None
                if webhook_url:
                    alert_data = {**deal_data, **score_data}
                    sent = await send_discord_alert(webhook_url, alert_data)
                    if sent:
                        alerts_sent += 1
            except Exception as e:
                logger.warning(f"Error sending alert for deal {deal.id}: {e}")

        return alerts_sent

    def _get_top_deals(
        self,
        deals: List[Deal],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get top deals by FlipScore."""

        scored_deals = [d for d in deals if d.score]
        sorted_deals = sorted(
            scored_deals,
            key=lambda d: float(d.score.flip_score) if d.score else 0,
            reverse=True,
        )

        return [
            {
                "name": d.product_name,
                "flip_score": float(d.score.flip_score) if d.score else 0,
                "margin_pct": float(d.vinted_stats.margin_percent) if d.vinted_stats and d.vinted_stats.margin_percent else 0,
                "action": d.score.recommended_action if d.score else "ignore",
            }
            for d in sorted_deals[:limit]
        ]

    async def run_scheduled(self):
        """Run as scheduled job (called by scheduler)."""
        try:
            results = await self.run_all_scrapers(send_alerts=True)
            logger.info(f"Scheduled scraping completed: {results['total_new_deals']} new deals")
            return results
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")
            raise
