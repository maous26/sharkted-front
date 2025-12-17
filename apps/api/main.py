"""
Sellshark API - Le Bloomberg Terminal du resell mode
Point d'entrée principal de l'application FastAPI
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from loguru import logger

from config import settings
from database import engine, Base, get_db
from routers import deals, users, alerts, analytics, scraping, ai, favorites
from services.scheduler import start_scheduler, stop_scheduler

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    logger.info("🦈 Démarrage de Sellshark API...")
    
    # Note: Les tables sont gérées par Alembic
    # Le create_all est désactivé pour éviter les conflits de migration
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    pass
    
    # Démarrage du scheduler de scraping
    await start_scheduler()
    
    logger.info("✅ Sellshark API prêt!")
    yield
    
    # Cleanup
    logger.info("🛑 Arrêt de Sellshark API...")
    await stop_scheduler()
    await engine.dispose()

# Application FastAPI
app = FastAPI(
    title="Sellshark API",
    description="""
    🦈 **Sellshark** - Le Bloomberg Terminal du resell mode en Europe
    
    Transformez le chaos des promos retail en signaux d'arbitrage exploitables.
    
    ## Fonctionnalités
    
    * **Scraping automatique** - 6+ sources retail surveillées en temps réel
    * **Matching intelligent** - Correspondance automatique avec les prix Vinted
    * **Scoring IA** - FlipScore prédictif pour identifier les meilleures opportunités
    * **Alertes temps réel** - Notifications Discord instantanées
    
    ## Authentification
    
    Utilisez un token JWT dans le header `Authorization: Bearer <token>`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /v1 prefix (as expected by frontend)
app.include_router(deals.router, prefix="/v1/deals", tags=["Deals"])
app.include_router(users.router, prefix="/v1/users", tags=["Users"])
app.include_router(alerts.router, prefix="/v1/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
app.include_router(scraping.router, prefix="/v1/scraping", tags=["Scraping"])
app.include_router(scraping.router, prefix="/v1/sources", tags=["Sources"])  # Alias for frontend
app.include_router(ai.router, prefix="/v1/ai", tags=["AI Analysis"])
app.include_router(favorites.router, prefix="/v1/favorites", tags=["Favorites"])

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Vérification de l'état du système"""
    return {
        "status": "healthy",
        "service": "sellshark-api",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "🦈 Bienvenue sur Sellshark API",
        "description": "Le Bloomberg Terminal du resell mode",
        "docs": "/docs",
        "health": "/health"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Une erreur interne est survenue",
            "status_code": 500
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )