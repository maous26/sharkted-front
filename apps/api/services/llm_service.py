"""LLM service for deal explanations and recommendations."""
import json
import logging
from typing import Optional, Dict, Any, List

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered analysis and explanations."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_chat_model

    async def analyze_deal(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Dict[str, Any],
        score_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate LLM analysis for a deal."""

        if not self.client:
            # Return basic analysis without LLM
            return self._basic_analysis(deal_data, vinted_stats, score_data)

        prompt = self._build_analysis_prompt(
            deal_data, vinted_stats, score_data, user_preferences
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return self._basic_analysis(deal_data, vinted_stats, score_data)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for deal analysis."""
        return """Tu es un expert en resell mode sur Vinted. Ton rôle est d'analyser des opportunités d'achat-revente et de fournir des recommandations précises et actionnables.

Tu dois toujours répondre en JSON avec la structure suivante:
{
    "recommendation": "buy" | "watch" | "ignore",
    "confidence": 0-100,
    "explanation": "Explication détaillée de 2-3 phrases",
    "explanation_short": "Résumé en une phrase",
    "risks": ["risque 1", "risque 2"],
    "opportunities": ["opportunité 1", "opportunité 2"],
    "suggested_price": {
        "listing": prix_recommandé,
        "min_accept": prix_minimum_acceptable
    },
    "estimated_sell_days": nombre_jours_estimé,
    "tips": ["conseil 1", "conseil 2"]
}

Critères d'évaluation:
- Marge > 30% = Excellent
- Marge 20-30% = Bon
- Marge 10-20% = Moyen
- Marge < 10% = À éviter (sauf très haute liquidité)

- Liquidité > 50 annonces = Très liquide
- Liquidité 20-50 = Liquide
- Liquidité 10-20 = Modérée
- Liquidité < 10 = Risquée

Prends en compte:
- La saisonnalité (été/hiver)
- La popularité de la marque/modèle
- Les tailles standards vs extrêmes
- Les couleurs (noir/blanc = plus liquide)"""

    def _build_analysis_prompt(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Dict[str, Any],
        score_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the analysis prompt."""

        prompt = f"""Analyse ce deal de resell:

## PRODUIT
- Nom: {deal_data.get('product_name', 'N/A')}
- Marque: {deal_data.get('brand', 'N/A')}
- Modèle: {deal_data.get('model', 'N/A')}
- Catégorie: {deal_data.get('category', 'N/A')}
- Couleur: {deal_data.get('color', 'N/A')}
- Genre: {deal_data.get('gender', 'N/A')}
- Tailles disponibles: {deal_data.get('sizes_available', [])}

## PRIX
- Prix original: {deal_data.get('original_price', 0)}€
- Prix soldé: {deal_data.get('sale_price', 0)}€
- Réduction: {deal_data.get('discount_pct', 0)}%

## MARCHÉ VINTED
- Nombre d'annonces: {vinted_stats.get('nb_listings', 0)}
- Prix médian: {vinted_stats.get('price_median', 0)}€
- Prix min: {vinted_stats.get('price_min', 0)}€
- Prix max: {vinted_stats.get('price_max', 0)}€
- Fourchette P25-P75: {vinted_stats.get('price_p25', 0)}€ - {vinted_stats.get('price_p75', 0)}€

## MÉTRIQUES CALCULÉES
- Marge estimée: {vinted_stats.get('margin_euro', 0)}€ ({vinted_stats.get('margin_pct', 0)}%)
- Score de liquidité: {vinted_stats.get('liquidity_score', 0)}/100
- FlipScore actuel: {score_data.get('flip_score', 0)}/100
- Confiance du matching: {vinted_stats.get('match_confidence', 0)}%"""

        if user_preferences:
            prompt += f"""

## PRÉFÉRENCES UTILISATEUR
- Marge minimum souhaitée: {user_preferences.get('min_margin', 20)}%
- Catégories favorites: {user_preferences.get('categories', [])}
- Tailles recherchées: {user_preferences.get('sizes', [])}
- Profil de risque: {user_preferences.get('risk_profile', 'balanced')}"""

        prompt += """

Fournis ton analyse complète en JSON."""

        return prompt

    def _basic_analysis(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Dict[str, Any],
        score_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate basic analysis without LLM."""

        margin_pct = float(vinted_stats.get('margin_pct', 0))
        liquidity = float(vinted_stats.get('liquidity_score', 0))
        flip_score = float(score_data.get('flip_score', 0))

        # Determine recommendation
        if flip_score >= 80 and margin_pct >= 25:
            recommendation = "buy"
            confidence = 85
        elif flip_score >= 60 and margin_pct >= 15:
            recommendation = "watch"
            confidence = 65
        else:
            recommendation = "ignore"
            confidence = 50

        # Build explanation
        if recommendation == "buy":
            explanation = f"Excellente opportunité avec une marge de {margin_pct:.1f}% et une bonne liquidité ({vinted_stats.get('nb_listings', 0)} annonces). Le FlipScore de {flip_score:.0f}/100 indique un deal rentable."
        elif recommendation == "watch":
            explanation = f"Deal intéressant mais avec une marge de {margin_pct:.1f}% et {vinted_stats.get('nb_listings', 0)} annonces. À surveiller si le prix baisse."
        else:
            explanation = f"Deal peu attractif avec une marge de seulement {margin_pct:.1f}% et un FlipScore de {flip_score:.0f}/100."

        # Identify risks
        risks = []
        if liquidity < 30:
            risks.append("Faible liquidité - revente potentiellement longue")
        if margin_pct < 20:
            risks.append("Marge faible - peu de marge d'erreur")
        if vinted_stats.get('match_confidence', 0) < 70:
            risks.append("Confiance du matching modérée - vérifier manuellement")

        # Identify opportunities
        opportunities = []
        if margin_pct >= 35:
            opportunities.append("Marge excellente")
        if liquidity >= 70:
            opportunities.append("Marché très liquide - revente rapide probable")
        if deal_data.get('discount_pct', 0) >= 50:
            opportunities.append("Forte réduction - prix d'entrée avantageux")

        # Suggested price
        price_median = float(vinted_stats.get('price_median', 0))
        suggested_listing = round(price_median * 0.95, 0)  # Slightly below median
        min_accept = round(price_median * 0.85, 0)

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "explanation": explanation,
            "explanation_short": f"{'🟢 Acheter' if recommendation == 'buy' else '🟡 Surveiller' if recommendation == 'watch' else '🔴 Ignorer'} - Marge {margin_pct:.0f}%",
            "risks": risks,
            "opportunities": opportunities,
            "suggested_price": {
                "listing": suggested_listing,
                "min_accept": min_accept,
            },
            "estimated_sell_days": self._estimate_sell_days(liquidity, margin_pct),
            "tips": self._generate_tips(deal_data, vinted_stats),
        }

    def _estimate_sell_days(self, liquidity: float, margin_pct: float) -> int:
        """Estimate days to sell based on liquidity and pricing."""
        base_days = 14

        # Adjust for liquidity
        if liquidity >= 80:
            base_days = 5
        elif liquidity >= 60:
            base_days = 10
        elif liquidity >= 40:
            base_days = 14
        else:
            base_days = 21

        # Adjust for pricing (higher margin = potentially longer to sell)
        if margin_pct >= 40:
            base_days += 3
        elif margin_pct >= 30:
            base_days += 1

        return base_days

    def _generate_tips(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable tips."""
        tips = []

        # Photo tips
        tips.append("Prends des photos avec bon éclairage naturel")

        # Pricing tips
        price_median = vinted_stats.get('price_median', 0)
        if price_median:
            tips.append(f"Liste autour de {price_median}€ pour une vente rapide")

        # Category-specific tips
        category = deal_data.get('category', '')
        if category == 'sneakers':
            tips.append("Nettoie bien les semelles avant les photos")
        elif category == 'textile':
            tips.append("Repasse/défroisse avant les photos")

        # Size tips
        sizes = deal_data.get('sizes_available', [])
        if sizes and len(sizes) > 1:
            tips.append("Privilégie les tailles 41-44 pour les sneakers homme")

        return tips[:3]  # Return max 3 tips

    async def generate_alert_message(
        self,
        deal_data: Dict[str, Any],
        score_data: Dict[str, Any],
    ) -> str:
        """Generate a formatted alert message for Discord/notifications."""

        emoji = "🟢" if score_data.get('flip_score', 0) >= 80 else "🟡" if score_data.get('flip_score', 0) >= 60 else "🔴"

        message = f"""{emoji} **Nouveau Deal Détecté!**

**{deal_data.get('product_name', 'Produit')}**
💰 Prix: ~~{deal_data.get('original_price', 0)}€~~ → **{deal_data.get('sale_price', 0)}€** (-{deal_data.get('discount_pct', 0):.0f}%)

📊 **FlipScore: {score_data.get('flip_score', 0):.0f}/100**
💵 Marge estimée: **{score_data.get('margin_euro', 0):.0f}€** ({score_data.get('margin_pct', 0):.0f}%)
📈 Liquidité: {score_data.get('liquidity_score', 0):.0f}/100

🛒 [{deal_data.get('source', 'Lien')}]({deal_data.get('product_url', '#')})

{score_data.get('explanation_short', '')}"""

        return message
