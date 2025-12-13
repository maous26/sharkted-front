"""
AI Router - Endpoints for AI analysis and scoring
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from database import get_db
from models import Deal, VintedStats, DealScore, User
from dependencies import get_current_user, get_current_user_optional
from services.ai_service import ai_service, analyze_deal_full
from services.vinted_service import get_vinted_stats_for_deal

router = APIRouter()


# ============= SCHEMAS =============

class AnalyzeProductRequest(BaseModel):
    """Request to analyze a product by name."""
    product_name: str = Field(..., min_length=3, max_length=500)
    brand: Optional[str] = None
    sale_price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    category: Optional[str] = None
    color: Optional[str] = None
    sizes_available: Optional[List[str]] = None


class EntityExtractionRequest(BaseModel):
    """Request to extract entities from product text."""
    text: str = Field(..., min_length=3, max_length=1000)
    category_hint: Optional[str] = "sneakers"


class EntityExtractionResponse(BaseModel):
    """Response with extracted entities."""
    brand: Optional[str]
    model: Optional[str]
    color: Optional[str]
    gender: Optional[str]
    sizes_detected: List[str]
    extraction_confidence: float


class ScoreComponentsResponse(BaseModel):
    """Score breakdown - SharkScore V2."""
    margin_score: float
    liquidity_score: float
    popularity_score: float
    risk_score: float


class RecommendedPricesResponse(BaseModel):
    """Recommended selling prices."""
    aggressive: float
    optimal: float
    patient: float


class ExtractedEntitiesResponse(BaseModel):
    """Extracted entity information."""
    brand: Optional[str]
    model: Optional[str]
    color: Optional[str]
    gender: Optional[str]
    category: str
    category_confidence: float


class FullAnalysisResponse(BaseModel):
    """Complete AI analysis response - SharkScore V2."""
    shark_score: float
    score_components: ScoreComponentsResponse
    recommended_action: str
    confidence: float
    recommended_price: float
    recommended_price_range: RecommendedPricesResponse
    estimated_sell_days: int
    explanation: str
    explanation_short: str
    risks: List[str]
    opportunities: List[str]
    tips: List[str]
    extracted_entities: ExtractedEntitiesResponse
    model_version: str
    analyzed_at: str


class VintedStatsResponse(BaseModel):
    """Vinted market statistics."""
    nb_listings: int
    price_min: Optional[float]
    price_max: Optional[float]
    price_median: Optional[float]
    price_p25: Optional[float]
    price_p75: Optional[float]
    margin_euro: float
    margin_percent: float
    liquidity_score: float


class QuickScoreResponse(BaseModel):
    """Quick score response without full analysis - SharkScore V2."""
    shark_score: float
    recommended_action: str
    margin_percent: float
    margin_euro: float
    liquidity_score: float
    risk_score: float
    nb_listings: int


# ============= ENDPOINTS =============

@router.post("/analyze", response_model=FullAnalysisResponse)
async def analyze_product(
    request: AnalyzeProductRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a product and get full AI recommendation.

    This endpoint:
    1. Extracts entities (brand, model, color) from product name
    2. Searches Vinted for market data
    3. Calculates SharkScore V2
    4. Generates LLM-powered recommendation
    """

    # Calculate discount
    discount_percent = 0
    if request.original_price and request.original_price > request.sale_price:
        discount_percent = ((request.original_price - request.sale_price) / request.original_price) * 100

    # Get Vinted stats
    vinted_stats = await get_vinted_stats_for_deal(
        product_name=request.product_name,
        brand=request.brand,
        sale_price=request.sale_price,
        category=request.category
    )

    # Build deal data
    deal_data = {
        "product_name": request.product_name,
        "brand": request.brand,
        "sale_price": request.sale_price,
        "original_price": request.original_price,
        "discount_percent": discount_percent,
        "category": request.category,
        "color": request.color,
        "sizes_available": request.sizes_available,
    }

    # Get user preferences if authenticated
    user_preferences = None
    if current_user and current_user.preferences:
        user_preferences = {
            "min_margin": current_user.preferences.get("min_margin", 20),
            "categories": current_user.preferences.get("categories", []),
            "sizes": current_user.preferences.get("sizes", []),
            "risk_profile": current_user.preferences.get("risk_profile", "balanced"),
        }

    # Run full AI analysis
    analysis = await ai_service.analyze_deal(
        deal_data=deal_data,
        vinted_stats=vinted_stats,
        user_preferences=user_preferences,
        include_llm_analysis=True
    )

    return analysis


@router.post("/quick-score", response_model=QuickScoreResponse)
async def quick_score_product(
    request: AnalyzeProductRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a quick SharkScore without full LLM analysis.
    Faster but less detailed than /analyze.
    """

    # Get Vinted stats
    vinted_stats = await get_vinted_stats_for_deal(
        product_name=request.product_name,
        brand=request.brand,
        sale_price=request.sale_price,
        category=request.category
    )

    discount_percent = 0
    if request.original_price and request.original_price > request.sale_price:
        discount_percent = ((request.original_price - request.sale_price) / request.original_price) * 100

    deal_data = {
        "product_name": request.product_name,
        "brand": request.brand,
        "sale_price": request.sale_price,
        "discount_percent": discount_percent,
        "category": request.category,
        "color": request.color,
        "sizes_available": request.sizes_available,
    }

    # Quick analysis without LLM
    analysis = await ai_service.analyze_deal(
        deal_data=deal_data,
        vinted_stats=vinted_stats,
        include_llm_analysis=False
    )

    return {
        "shark_score": analysis["shark_score"],
        "recommended_action": analysis["recommended_action"],
        "margin_percent": vinted_stats.get("margin_percent", 0),
        "margin_euro": vinted_stats.get("margin_euro", 0),
        "liquidity_score": vinted_stats.get("liquidity_score", 0),
        "risk_score": analysis.get("score_components", {}).get("risk_score", 100),
        "nb_listings": vinted_stats.get("nb_listings", 0),
    }


@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest
):
    """
    Extract product entities from text.

    Extracts brand, model, color, gender, and sizes from product text.
    Useful for cleaning/normalizing product data.
    """

    entities = ai_service.entity_extractor.extract_all(
        request.text,
        request.category_hint or "sneakers"
    )

    return entities


@router.get("/analyze-deal/{deal_id}", response_model=FullAnalysisResponse)
async def analyze_existing_deal(
    deal_id: UUID,
    refresh: bool = Query(False, description="Force refresh Vinted data"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze an existing deal from the database.
    """

    # Get deal with relations
    query = (
        select(Deal)
        .options(
            selectinload(Deal.source),
            selectinload(Deal.vinted_stats),
            selectinload(Deal.score),
        )
        .where(Deal.id == deal_id)
    )

    result = await db.execute(query)
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )

    # Get Vinted stats (refresh or use cached)
    if refresh or not deal.vinted_stats:
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

    # Run analysis
    analysis = await ai_service.analyze_deal(
        deal_data=deal_data,
        vinted_stats=vinted_stats,
        user_preferences=user_preferences,
        include_llm_analysis=True
    )

    return analysis


@router.get("/vinted-stats")
async def get_vinted_market_stats(
    product_name: str = Query(..., min_length=3),
    brand: Optional[str] = None,
    sale_price: Optional[float] = None,
    category: Optional[str] = None
):
    """
    Get Vinted market statistics for a product.

    Returns listing counts, price distribution, and calculated metrics.
    """

    stats = await get_vinted_stats_for_deal(
        product_name=product_name,
        brand=brand,
        sale_price=sale_price or 50,  # Default price for search
        category=category
    )

    return stats


@router.post("/batch-analyze")
async def batch_analyze_products(
    products: List[AnalyzeProductRequest],
    include_llm: bool = Query(False, description="Include LLM analysis (slower)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze multiple products in batch.

    Returns quick scores for all products.
    Set include_llm=true for full analysis (slower).
    """

    if len(products) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 products per batch"
        )

    results = []

    for product in products:
        try:
            vinted_stats = await get_vinted_stats_for_deal(
                product_name=product.product_name,
                brand=product.brand,
                sale_price=product.sale_price,
                category=product.category
            )

            discount_percent = 0
            if product.original_price and product.original_price > product.sale_price:
                discount_percent = ((product.original_price - product.sale_price) / product.original_price) * 100

            deal_data = {
                "product_name": product.product_name,
                "brand": product.brand,
                "sale_price": product.sale_price,
                "discount_percent": discount_percent,
                "category": product.category,
                "color": product.color,
                "sizes_available": product.sizes_available,
            }

            analysis = await ai_service.analyze_deal(
                deal_data=deal_data,
                vinted_stats=vinted_stats,
                include_llm_analysis=include_llm
            )

            results.append({
                "product_name": product.product_name,
                "success": True,
                "analysis": analysis
            })

        except Exception as e:
            results.append({
                "product_name": product.product_name,
                "success": False,
                "error": str(e)
            })

    return {
        "total": len(products),
        "successful": sum(1 for r in results if r["success"]),
        "results": results
    }


@router.get("/category-config")
async def get_category_config():
    """
    Get category configuration and weights.

    Returns the scoring weights for each product category.
    """
    from config import CATEGORY_WEIGHTS, BRAND_TIERS

    return {
        "categories": CATEGORY_WEIGHTS,
        "brand_tiers": BRAND_TIERS
    }
