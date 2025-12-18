"""
Service Scoring - Calcul du FlipScore et recommandations
Version 1: Règles pondérées (MVP)
Version 2: Machine Learning (Phase 2)
"""

from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import math
from loguru import logger
from openai import AsyncOpenAI

from config import settings, CATEGORY_WEIGHTS, BRAND_TIERS


class ScoringEngine:
    """
    Moteur de scoring pour évaluer la qualité des deals
    
    FlipScore = Pondération de:
    - Marge potentielle (40%)
    - Liquidité du marché (30%)
    - Popularité marque/modèle (20%)
    - Bonus/Malus contextuels (10%)
    """
    
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    def _get_margin_score(
        self,
        margin_percent: float,
        margin_euro: float,
        category: str = "sneakers_lifestyle"
    ) -> float:
        """
        Calcule le score de marge (0-100)
        
        - Marge % pondérée par rapport au seuil de la catégorie
        - Bonus si marge € absolue élevée
        """
        
        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["sneakers_lifestyle"])
        threshold = cat_config["margin_threshold"]
        
        # Score base sur le % de marge
        if margin_percent <= 0:
            base_score = 0
        elif margin_percent < threshold:
            # Score linéaire jusqu'au seuil
            base_score = (margin_percent / threshold) * 50
        elif margin_percent < threshold * 2:
            # Score accéléré au-dessus du seuil
            base_score = 50 + ((margin_percent - threshold) / threshold) * 30
        else:
            # Bonus pour marges exceptionnelles
            base_score = 80 + min((margin_percent - threshold * 2) / 20, 20)
        
        # Bonus marge € absolue (important pour tickets élevés)
        if margin_euro >= 50:
            euro_bonus = 10
        elif margin_euro >= 30:
            euro_bonus = 5
        elif margin_euro >= 20:
            euro_bonus = 2
        else:
            euro_bonus = 0
        
        return min(base_score + euro_bonus, 100)
    
    def _get_liquidity_score(
        self,
        nb_listings: int,
        liquidity_from_vinted: float,
        category: str = "sneakers_lifestyle"
    ) -> float:
        """
        Calcule le score de liquidité (0-100)
        
        - Nombre d'annonces Vinted
        - Score de liquidité calculé par le service Vinted
        - Pondéré par la catégorie
        """
        
        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["sneakers_lifestyle"])
        liquidity_weight = cat_config["liquidity_weight"]
        
        # Score basé sur le nombre d'annonces
        if nb_listings == 0:
            listings_score = 0
        elif nb_listings < 5:
            listings_score = 20
        elif nb_listings < 15:
            listings_score = 40
        elif nb_listings < 30:
            listings_score = 60
        elif nb_listings < 50:
            listings_score = 80
        else:
            listings_score = 100
        
        # Combiner avec le score Vinted
        combined_score = (listings_score * 0.4 + liquidity_from_vinted * 0.6)
        
        # Appliquer le poids de la catégorie
        return combined_score * liquidity_weight
    
    def _get_popularity_score(
        self,
        brand: Optional[str],
        model: Optional[str],
        category: str = "sneakers_lifestyle"
    ) -> float:
        """
        Calcule le score de popularité (0-100)
        
        - Tier de la marque
        - Popularité du modèle (si référencé)
        """
        
        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["sneakers_lifestyle"])
        popularity_weight = cat_config["popularity_weight"]
        
        base_score = 50  # Score par défaut
        
        # Bonus marque
        if brand:
            brand_lower = brand.lower()
            brand_info = BRAND_TIERS.get(brand_lower)
            
            if brand_info:
                tier = brand_info["tier"]
                bonus = brand_info["popularity_bonus"]
                
                if tier == "S":
                    base_score = 85
                elif tier == "A":
                    base_score = 70
                elif tier == "B":
                    base_score = 55
                else:
                    base_score = 40
                
                base_score *= bonus
        
        # TODO: Ajouter la popularité du modèle depuis la table de référence
        
        return min(base_score * popularity_weight, 100)
    
    def _get_contextual_bonus(
        self,
        discount_percent: float,
        sizes_available: Optional[List[str]],
        color: Optional[str],
        season_match: bool = True
    ) -> float:
        """
        Calcule les bonus/malus contextuels (-20 à +20)
        
        - Discount exceptionnel
        - Tailles disponibles
        - Coloris safe
        - Match saisonnier
        """
        
        bonus = 0
        
        # Bonus discount élevé
        if discount_percent >= 70:
            bonus += 10
        elif discount_percent >= 50:
            bonus += 5
        
        # Bonus tailles standard disponibles
        standard_sizes = {"40", "41", "42", "43", "44", "M", "L", "S"}
        if sizes_available:
            matching_sizes = set(sizes_available) & standard_sizes
            if len(matching_sizes) >= 3:
                bonus += 5
            elif len(matching_sizes) >= 1:
                bonus += 2
        
        # Bonus coloris safe (noir, blanc, gris)
        safe_colors = {"noir", "black", "blanc", "white", "gris", "grey", "gray"}
        if color and any(safe in color.lower() for safe in safe_colors):
            bonus += 3
        
        # Malus hors saison (à améliorer avec les vraies données saisonnières)
        if not season_match:
            bonus -= 5
        
        return bonus
    
    def calculate_flip_score(
        self,
        margin_percent: float,
        margin_euro: float,
        nb_listings: int,
        liquidity_score: float,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        category: str = "sneakers_lifestyle",
        discount_percent: float = 0,
        sizes_available: Optional[List[str]] = None,
        color: Optional[str] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calcule le FlipScore final (0-100)
        
        Returns:
            Tuple (score_final, détail_composantes)
        """
        
        # Calculer les composantes
        margin_score = self._get_margin_score(margin_percent, margin_euro, category)
        liq_score = self._get_liquidity_score(nb_listings, liquidity_score, category)
        pop_score = self._get_popularity_score(brand, model, category)
        ctx_bonus = self._get_contextual_bonus(discount_percent, sizes_available, color)
        
        # Pondération finale
        # Marge: 40%, Liquidité: 30%, Popularité: 20%, Contexte: 10%
        weighted_score = (
            margin_score * 0.40 +
            liq_score * 0.30 +
            pop_score * 0.20 +
            ctx_bonus  # Bonus direct (max ±20)
        )
        
        final_score = max(0, min(100, weighted_score))
        
        components = {
            "margin_score": round(margin_score, 1),
            "liquidity_score": round(liq_score, 1),
            "popularity_score": round(pop_score, 1),
            "contextual_bonus": round(ctx_bonus, 1)
        }
        
        return round(final_score, 1), components
    
    def get_recommendation(
        self,
        flip_score: float,
        margin_percent: float,
        margin_euro: float
    ) -> Tuple[str, float]:
        """
        Détermine la recommandation basée sur le score
        
        Returns:
            Tuple (action, confidence)
        """
        
        # Règles de décision
        if flip_score >= 80 and margin_percent >= 30 and margin_euro >= 20:
            return "buy", min(0.95, flip_score / 100)
        elif flip_score >= 70 and margin_percent >= 25:
            return "buy", min(0.85, flip_score / 100)
        elif flip_score >= 60 and margin_percent >= 20:
            return "watch", 0.6 + (flip_score - 60) / 100
        elif flip_score >= 50:
            return "watch", 0.5
        else:
            return "ignore", 0.3 + flip_score / 200
    
    def calculate_recommended_price(
        self,
        vinted_stats: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calcule les prix de vente recommandés
        
        Returns:
            Dict avec prix agressif, optimal et patient
        """
        
        price_median = vinted_stats.get("price_median", 0)
        price_p25 = vinted_stats.get("price_p25", 0)
        price_p75 = vinted_stats.get("price_p75", 0)
        
        if not price_median:
            return {"aggressive": 0, "optimal": 0, "patient": 0}
        
        return {
            "aggressive": round(price_p25 * 0.95, 2),  # Vente rapide
            "optimal": round(price_median * 0.98, 2),  # Équilibré
            "patient": round(price_p75 * 0.95, 2)      # Marge max
        }
    
    def estimate_sell_days(
        self,
        flip_score: float,
        liquidity_score: float,
        category: str = "sneakers_lifestyle"
    ) -> int:
        """
        Estime le nombre de jours pour vendre
        """
        
        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["sneakers_lifestyle"])
        base_days = cat_config["expected_sell_days"]
        
        # Ajuster selon le score
        if flip_score >= 80 and liquidity_score >= 70:
            return max(3, base_days - 4)
        elif flip_score >= 70:
            return base_days
        elif flip_score >= 60:
            return base_days + 3
        else:
            return base_days + 7
    
    async def generate_explanation(
        self,
        deal_data: Dict[str, Any],
        score_components: Dict[str, float],
        flip_score: float,
        recommendation: str
    ) -> str:
        """
        Génère une explication en langage naturel avec GPT-4o
        """
        
        if not self.openai_client:
            # Fallback sans OpenAI
            return self._generate_simple_explanation(
                deal_data, score_components, flip_score, recommendation
            )
        
        prompt = f"""Tu es un expert en resell Vinted. Explique brièvement pourquoi ce deal a un FlipScore de {flip_score}/100.

Deal:
- Produit: {deal_data.get('product_name', 'Inconnu')}
- Marque: {deal_data.get('brand', 'Inconnue')}
- Prix achat: {deal_data.get('sale_price', 0)}€
- Marge estimée: {deal_data.get('margin_euro', 0)}€ ({deal_data.get('margin_percent', 0)}%)
- Annonces Vinted: {deal_data.get('nb_listings', 0)}

Scores:
- Score marge: {score_components.get('margin_score', 0)}/100
- Score liquidité: {score_components.get('liquidity_score', 0)}/100
- Score popularité: {score_components.get('popularity_score', 0)}/100

Recommandation: {recommendation.upper()}

Donne une explication de 2-3 phrases maximum, factuelle et actionnable. Pas de phrases bateau."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erreur OpenAI: {e}")
            return self._generate_simple_explanation(
                deal_data, score_components, flip_score, recommendation
            )
    
    def _generate_simple_explanation(
        self,
        deal_data: Dict[str, Any],
        score_components: Dict[str, float],
        flip_score: float,
        recommendation: str
    ) -> str:
        """Génère une explication simple sans LLM"""
        
        parts = []
        
        # Analyse de la marge
        margin_score = score_components.get("margin_score", 0)
        if margin_score >= 70:
            parts.append(f"Excellente marge ({deal_data.get('margin_percent', 0):.0f}%)")
        elif margin_score >= 50:
            parts.append(f"Marge correcte ({deal_data.get('margin_percent', 0):.0f}%)")
        else:
            parts.append(f"Marge faible ({deal_data.get('margin_percent', 0):.0f}%)")
        
        # Analyse de la liquidité
        liq_score = score_components.get("liquidity_score", 0)
        nb_listings = deal_data.get("nb_listings", 0)
        if liq_score >= 60:
            parts.append(f"marché actif ({nb_listings} annonces)")
        elif liq_score >= 40:
            parts.append(f"liquidité moyenne ({nb_listings} annonces)")
        else:
            parts.append(f"peu d'annonces ({nb_listings})")
        
        # Recommandation
        if recommendation == "buy":
            conclusion = "Deal recommandé à l'achat."
        elif recommendation == "watch":
            conclusion = "À surveiller pour une meilleure opportunité."
        else:
            conclusion = "Pass recommandé."
        
        return f"{', '.join(parts)}. {conclusion}"
    
    def identify_risks(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Dict[str, Any]
    ) -> List[str]:
        """Identifie les risques potentiels du deal"""
        
        risks = []
        
        # Risque liquidité
        nb_listings = vinted_stats.get("nb_listings", 0)
        if nb_listings < 10:
            risks.append("Faible nombre d'annonces sur Vinted - revente potentiellement longue")
        
        # Risque dispersion prix
        cv = vinted_stats.get("coefficient_variation", 0)
        if cv > 30:
            risks.append("Prix très variables sur Vinted - estimation de marge incertaine")
        
        # Risque taille
        sizes = deal_data.get("sizes_available", [])
        if sizes and all(s not in ["40", "41", "42", "43", "44", "M", "L"] for s in sizes):
            risks.append("Tailles atypiques disponibles - liquidité réduite")
        
        # Risque coloris
        color = deal_data.get("color", "")
        risky_colors = ["rose", "pink", "jaune", "yellow", "orange", "violet", "purple"]
        if any(c in color.lower() for c in risky_colors):
            risks.append("Coloris moins demandé - potentielle difficulté de revente")
        
        # Risque marge faible en €
        margin_euro = vinted_stats.get("margin_euro", 0)
        if margin_euro < 15:
            risks.append(f"Marge absolue faible ({margin_euro:.0f}€) - peu de marge d'erreur")
        
        return risks


# Instance singleton
scoring_engine = ScoringEngine()

# Import ML scoring si disponible
try:
    from services.ml_scoring_service import ml_score_deal, ml_scoring_engine
    ML_SCORING_AVAILABLE = True
except ImportError:
    ML_SCORING_AVAILABLE = False
    logger.warning("ML scoring non disponible, utilisation des règles")


async def score_deal(
    deal_data: Dict[str, Any],
    vinted_stats: Dict[str, Any],
    use_ml: bool = True
) -> Dict[str, Any]:
    """
    Fonction helper pour scorer un deal complet

    Args:
        deal_data: Données du deal
        vinted_stats: Stats Vinted
        use_ml: Utiliser le ML si disponible (défaut: True)

    Returns:
        Score complet avec toutes les métriques
    """

    # Essayer le ML d'abord si disponible et demandé
    if use_ml and ML_SCORING_AVAILABLE:
        try:
            ml_result = await ml_score_deal(deal_data, vinted_stats)
            if ml_result and ml_result.get("flip_score", 0) > 0:
                logger.debug(f"Score ML utilisé: {ml_result['flip_score']}")
                return ml_result
        except Exception as e:
            logger.warning(f"Erreur ML scoring, fallback règles: {e}")

    # Fallback sur les règles
    margin_percent = vinted_stats.get("margin_percent", 0)
    margin_euro = vinted_stats.get("margin_euro", 0)
    nb_listings = vinted_stats.get("nb_listings", 0)
    liquidity_score = vinted_stats.get("liquidity_score", 0)

    # Déterminer la catégorie
    category = f"{deal_data.get('category', 'sneakers')}_{deal_data.get('subcategory', 'lifestyle')}"
    if category not in CATEGORY_WEIGHTS:
        category = "sneakers_lifestyle"

    # Calculer le FlipScore
    flip_score, components = scoring_engine.calculate_flip_score(
        margin_percent=margin_percent,
        margin_euro=margin_euro,
        nb_listings=nb_listings,
        liquidity_score=liquidity_score,
        brand=deal_data.get("brand"),
        model=deal_data.get("model"),
        category=category,
        discount_percent=deal_data.get("discount_percent", 0),
        sizes_available=deal_data.get("sizes_available"),
        color=deal_data.get("color")
    )

    # Recommandation
    recommendation, confidence = scoring_engine.get_recommendation(
        flip_score, margin_percent, margin_euro
    )

    # Prix recommandé
    recommended_prices = scoring_engine.calculate_recommended_price(vinted_stats)

    # Estimation temps de vente
    estimated_days = scoring_engine.estimate_sell_days(
        flip_score, liquidity_score, category
    )

    # Risques
    risks = scoring_engine.identify_risks(deal_data, vinted_stats)

    # Explication
    deal_for_explanation = {
        **deal_data,
        "margin_euro": margin_euro,
        "margin_percent": margin_percent,
        "nb_listings": nb_listings
    }
    explanation = await scoring_engine.generate_explanation(
        deal_for_explanation, components, flip_score, recommendation
    )

    return {
        "flip_score": flip_score,
        "popularity_score": components["popularity_score"],
        "liquidity_score": components["liquidity_score"],
        "margin_score": components["margin_score"],
        "recommended_action": recommendation,
        "recommended_price": recommended_prices["optimal"],
        "recommended_price_range": recommended_prices,
        "confidence": confidence,
        "explanation": explanation,
        "risks": risks,
        "estimated_sell_days": estimated_days,
        "model_version": "rules_v1",
        "score_breakdown": {
            "discount_score": min(100, (deal_data.get("discount_percent", 0) or 0) * 1.5),
            "margin_score": components["margin_score"],
            "brand_score": components["popularity_score"],
            "estimated_margin_pct": margin_percent,
            "estimated_margin_euro": margin_euro
        }
    }