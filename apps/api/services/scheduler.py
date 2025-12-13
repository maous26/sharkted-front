"""
Scheduler service - Gestion des jobs de scraping planifiés
"""

import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

from config import settings

# Global scheduler state
_scheduler_task: Optional[asyncio.Task] = None
_scheduler_running: bool = False


async def scraping_job():
    """Job de scraping exécuté à intervalles réguliers"""
    from database import async_session
    from services.scraping_orchestrator import ScrapingOrchestrator

    logger.info("🔄 Démarrage du job de scraping planifié...")

    try:
        async with async_session() as db:
            orchestrator = ScrapingOrchestrator(db)
            results = await orchestrator.run_all_scrapers(send_alerts=True)

            logger.info(
                f"✅ Scraping terminé: {results['total_new_deals']} nouveaux deals, "
                f"{results['total_scored']} scorés, {results['alerts_sent']} alertes envoyées"
            )

            await db.commit()

    except Exception as e:
        logger.error(f"❌ Erreur lors du scraping planifié: {e}")


async def scheduler_loop():
    """Boucle principale du scheduler"""
    global _scheduler_running

    interval_minutes = settings.SCRAPE_INTERVAL_MINUTES
    interval_seconds = interval_minutes * 60

    logger.info(f"⏰ Scheduler démarré - Intervalle: {interval_minutes} minutes")

    while _scheduler_running:
        try:
            # Exécuter le job de scraping
            await scraping_job()

            # Attendre l'intervalle suivant
            logger.info(f"💤 Prochain scraping dans {interval_minutes} minutes...")
            await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info("🛑 Scheduler annulé")
            break
        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle du scheduler: {e}")
            # Attendre un peu avant de réessayer en cas d'erreur
            await asyncio.sleep(60)


async def start_scheduler():
    """Démarre le scheduler de scraping en arrière-plan"""
    global _scheduler_task, _scheduler_running

    if _scheduler_task is not None and not _scheduler_task.done():
        logger.warning("⚠️ Le scheduler est déjà en cours d'exécution")
        return

    _scheduler_running = True
    _scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("🚀 Scheduler de scraping démarré")


async def stop_scheduler():
    """Arrête le scheduler de scraping"""
    global _scheduler_task, _scheduler_running

    _scheduler_running = False

    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None

    logger.info("🛑 Scheduler de scraping arrêté")


def is_scheduler_running() -> bool:
    """Vérifie si le scheduler est en cours d'exécution"""
    return _scheduler_running and _scheduler_task is not None and not _scheduler_task.done()
