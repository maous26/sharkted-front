"""
Service Discord - Envoi d'alertes via webhooks
"""

import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from config import settings


def get_score_emoji(score: float) -> str:
    """Retourne un emoji basé sur le score"""
    if score >= 85:
        return "🔥"
    elif score >= 70:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"


def get_score_color(score: float) -> int:
    """Retourne une couleur Discord basée sur le score"""
    if score >= 85:
        return 0xFF4500  # Orange-red (fire)
    elif score >= 70:
        return 0x00FF00  # Green
    elif score >= 50:
        return 0xFFFF00  # Yellow
    else:
        return 0xFF0000  # Red


async def send_discord_alert(
    webhook_url: str,
    deal_data: Dict[str, Any],
    is_test: bool = False
) -> bool:
    """
    Envoie une alerte Discord pour un deal
    
    Args:
        webhook_url: URL du webhook Discord
        deal_data: Données du deal à envoyer
        is_test: Si True, envoie un message de test
        
    Returns:
        True si envoi réussi, False sinon
    """
    
    flip_score = deal_data.get("flip_score", 0)
    score_emoji = get_score_emoji(flip_score)
    score_color = get_score_color(flip_score)
    
    # Construction de l'embed Discord
    embed = {
        "title": f"{score_emoji} {'🧪 TEST - ' if is_test else ''}{deal_data.get('product_name', 'Deal détecté')}",
        "description": f"**{deal_data.get('brand', 'Marque inconnue')}** - FlipScore: **{flip_score}/100**",
        "color": score_color,
        "fields": [
            {
                "name": "💰 Prix",
                "value": f"~~{deal_data.get('original_price', 0):.2f}€~~ → **{deal_data.get('sale_price', 0):.2f}€** (-{deal_data.get('discount_percent', 0):.0f}%)",
                "inline": True
            },
            {
                "name": "📈 Marge estimée",
                "value": f"**+{deal_data.get('margin_euro', 0):.2f}€** ({deal_data.get('margin_percent', 0):.0f}%)",
                "inline": True
            },
            {
                "name": "🎯 FlipScore",
                "value": f"**{flip_score}/100** {score_emoji}",
                "inline": True
            }
        ],
        "footer": {
            "text": f"🦈 Sellshark • {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC"
        }
    }
    
    # Ajouter l'image si disponible
    if deal_data.get("image_url"):
        embed["thumbnail"] = {"url": deal_data["image_url"]}
    
    # Ajouter le lien vers le produit
    if deal_data.get("product_url"):
        embed["url"] = deal_data["product_url"]
        embed["fields"].append({
            "name": "🔗 Lien",
            "value": f"[Voir le deal]({deal_data['product_url']})",
            "inline": False
        })
    
    # Payload Discord
    payload = {
        "username": "🦈 Sellshark",
        "avatar_url": "https://i.imgur.com/vXQWEyX.png",  # Placeholder - mettre le vrai logo
        "embeds": [embed]
    }
    
    # Si c'est un test, ajouter un message
    if is_test:
        payload["content"] = "✅ **Webhook configuré avec succès!** Voici un exemple d'alerte que vous recevrez:"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Alert Discord envoyée: {deal_data.get('product_name', 'unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Erreur Discord webhook: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"Exception lors de l'envoi Discord: {e}")
        return False


async def send_batch_alerts(
    webhook_url: str,
    deals: list,
    max_per_message: int = 5
) -> int:
    """
    Envoie plusieurs deals dans un seul message Discord
    
    Args:
        webhook_url: URL du webhook
        deals: Liste des deals à envoyer
        max_per_message: Nombre max de deals par message
        
    Returns:
        Nombre de deals envoyés avec succès
    """
    
    if not deals:
        return 0
    
    # Limiter le nombre de deals
    deals_to_send = deals[:max_per_message]
    
    embeds = []
    for deal in deals_to_send:
        flip_score = deal.get("flip_score", 0)
        score_emoji = get_score_emoji(flip_score)
        
        embed = {
            "title": f"{score_emoji} {deal.get('product_name', 'Deal')}",
            "description": f"**{deal.get('brand', '')}** | {deal.get('sale_price', 0):.2f}€ (-{deal.get('discount_percent', 0):.0f}%) | Marge: +{deal.get('margin_euro', 0):.2f}€",
            "color": get_score_color(flip_score),
            "url": deal.get("product_url", ""),
            "thumbnail": {"url": deal.get("image_url", "")} if deal.get("image_url") else None
        }
        embeds.append({k: v for k, v in embed.items() if v is not None})
    
    payload = {
        "username": "🦈 Sellshark",
        "content": f"🚨 **{len(deals_to_send)} nouveaux deals détectés!**",
        "embeds": embeds
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Batch alert Discord: {len(deals_to_send)} deals envoyés")
                    return len(deals_to_send)
                else:
                    logger.error(f"Erreur batch Discord: {response.status}")
                    return 0
                    
    except Exception as e:
        logger.error(f"Exception batch Discord: {e}")
        return 0