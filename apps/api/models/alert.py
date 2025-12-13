"""
Router Alerts - Gestion des alertes et notifications
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

from database import get_db, Alert, User, Deal, DealScore
from routers.users import get_current_user
from services.discord_service import send_discord_alert
from config import settings

router = APIRouter()

# ============= SCHEMAS =============

class AlertCreate(BaseModel):
    deal_id: uuid.UUID
    channel: str = "discord"

class AlertResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    channel: str
    sent_at: datetime
    delivered: bool
    clicked: bool
    
    class Config:
        from_attributes = True

class AlertSettings(BaseModel):
    discord_webhook: Optional[str] = None
    email_alerts: bool = True
    alert_threshold: int = 70
    categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    min_margin: Optional[float] = 20

class WebhookTest(BaseModel):
    webhook_url: str

# ============= ENDPOINTS =============

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste les alertes envoyées à l'utilisateur
    """
    query = (
        select(Alert)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.sent_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/settings")
async def get_alert_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les paramètres d'alerte de l'utilisateur
    """
    prefs = current_user.preferences or {}
    
    return AlertSettings(
        discord_webhook=current_user.discord_webhook,
        email_alerts=current_user.email_alerts,
        alert_threshold=prefs.get("alert_threshold", 70),
        categories=prefs.get("categories", []),
        brands=prefs.get("brands", []),
        min_margin=prefs.get("min_margin", 20)
    )


@router.put("/settings")
async def update_alert_settings(
    settings_data: AlertSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Met à jour les paramètres d'alerte
    """
    current_user.discord_webhook = settings_data.discord_webhook
    current_user.email_alerts = settings_data.email_alerts
    
    # Update preferences
    prefs = current_user.preferences or {}
    prefs["alert_threshold"] = settings_data.alert_threshold
    if settings_data.categories:
        prefs["categories"] = settings_data.categories
    if settings_data.brands:
        prefs["brands"] = settings_data.brands
    if settings_data.min_margin:
        prefs["min_margin"] = settings_data.min_margin
    current_user.preferences = prefs
    
    await db.commit()
    
    return {"message": "Paramètres d'alerte mis à jour", "settings": settings_data}


@router.post("/test-webhook")
async def test_discord_webhook(
    webhook_data: WebhookTest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Teste un webhook Discord
    """
    test_message = {
        "product_name": "🧪 Test Sellshark Alert",
        "brand": "Test",
        "sale_price": 49.99,
        "original_price": 99.99,
        "discount_percent": 50,
        "margin_euro": 25,
        "margin_percent": 50,
        "flip_score": 85,
        "product_url": "https://sellshark.app",
        "image_url": None
    }
    
    try:
        success = await send_discord_alert(
            webhook_url=webhook_data.webhook_url,
            deal_data=test_message,
            is_test=True
        )
        
        if success:
            return {"success": True, "message": "Webhook testé avec succès! Vérifiez votre Discord."}
        else:
            raise HTTPException(status_code=400, detail="Échec de l'envoi du webhook")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur webhook: {str(e)}")


@router.post("/mark-clicked/{alert_id}")
async def mark_alert_clicked(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marque une alerte comme cliquée (pour tracking)
    """
    query = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    alert.clicked = True
    alert.clicked_at = datetime.utcnow()
    await db.commit()
    
    return {"success": True, "message": "Alerte marquée comme cliquée"}


@router.get("/stats")
async def get_alert_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Statistiques des alertes de l'utilisateur
    """
    from sqlalchemy import func
    
    # Total sent
    total_query = select(func.count(Alert.id)).where(Alert.user_id == current_user.id)
    total_result = await db.execute(total_query)
    total_sent = total_result.scalar() or 0
    
    # Delivered
    delivered_query = select(func.count(Alert.id)).where(
        and_(Alert.user_id == current_user.id, Alert.delivered == True)
    )
    delivered_result = await db.execute(delivered_query)
    total_delivered = delivered_result.scalar() or 0
    
    # Clicked
    clicked_query = select(func.count(Alert.id)).where(
        and_(Alert.user_id == current_user.id, Alert.clicked == True)
    )
    clicked_result = await db.execute(clicked_query)
    total_clicked = clicked_result.scalar() or 0
    
    return {
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_clicked": total_clicked,
        "delivery_rate": round(total_delivered / total_sent * 100, 1) if total_sent > 0 else 0,
        "click_rate": round(total_clicked / total_delivered * 100, 1) if total_delivered > 0 else 0
    }