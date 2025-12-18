"""
Service ML Scoring - Machine Learning pour le FlipScore
Version 2: Modèle entraînable avec données réelles

Utilise:
- XGBoost/LightGBM pour la prédiction du score
- Données historiques des Outcomes pour l'apprentissage
- Features engineerées à partir des deals
"""

import os
import json
import pickle
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import numpy as np
from pathlib import Path
from loguru import logger

try:
    from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, accuracy_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("sklearn non installé - ML scoring désactivé")

from config import BRAND_TIERS, CATEGORY_WEIGHTS


class MLScoringEngine:
    """
    Moteur de scoring basé sur le Machine Learning

    Features utilisées:
    - Prix d'achat
    - Prix original / Remise %
    - Marque (encodée)
    - Catégorie
    - Saison (mois)
    - Stats Vinted si disponibles
    """

    MODEL_DIR = Path(__file__).parent.parent / "ml_models"
    MODEL_FILE = "flip_score_model.pkl"
    SCALER_FILE = "flip_score_scaler.pkl"
    ENCODERS_FILE = "flip_score_encoders.pkl"

    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.is_trained = False
        self.model_version = "ml_v1"

        # Créer le répertoire des modèles
        self.MODEL_DIR.mkdir(exist_ok=True)

        # Charger le modèle existant si disponible
        self._load_model()

    def _load_model(self) -> bool:
        """Charge le modèle pré-entraîné si disponible"""
        if not ML_AVAILABLE:
            return False

        model_path = self.MODEL_DIR / self.MODEL_FILE
        scaler_path = self.MODEL_DIR / self.SCALER_FILE
        encoders_path = self.MODEL_DIR / self.ENCODERS_FILE

        if model_path.exists() and scaler_path.exists():
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                if encoders_path.exists():
                    with open(encoders_path, "rb") as f:
                        self.label_encoders = pickle.load(f)
                self.is_trained = True
                logger.info("Modèle ML chargé avec succès")
                return True
            except Exception as e:
                logger.error(f"Erreur chargement modèle ML: {e}")
        return False

    def _save_model(self):
        """Sauvegarde le modèle entraîné"""
        if not self.model or not self.scaler:
            return

        try:
            with open(self.MODEL_DIR / self.MODEL_FILE, "wb") as f:
                pickle.dump(self.model, f)
            with open(self.MODEL_DIR / self.SCALER_FILE, "wb") as f:
                pickle.dump(self.scaler, f)
            with open(self.MODEL_DIR / self.ENCODERS_FILE, "wb") as f:
                pickle.dump(self.label_encoders, f)
            logger.info("Modèle ML sauvegardé")
        except Exception as e:
            logger.error(f"Erreur sauvegarde modèle: {e}")

    def _get_brand_tier_score(self, brand: Optional[str]) -> float:
        """Score de la marque basé sur le tier (0-100)"""
        if not brand:
            return 50.0

        brand_lower = brand.lower().strip()
        brand_info = BRAND_TIERS.get(brand_lower, {})
        tier = brand_info.get("tier", "C")

        tier_scores = {"S": 95, "A": 80, "B": 65, "C": 50, "D": 35}
        return tier_scores.get(tier, 50)

    def _get_category_weight(self, category: str) -> float:
        """Poids de la catégorie pour le scoring"""
        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS.get("sneakers_lifestyle", {}))
        return cat_config.get("liquidity_weight", 1.0) * 100

    def _extract_features(self, deal_data: Dict[str, Any], vinted_stats: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Extrait les features pour le modèle ML

        Returns:
            Array numpy des features normalisées
        """
        features = []

        # 1. Prix d'achat (normalisé sur échelle 0-500€)
        sale_price = deal_data.get("sale_price", deal_data.get("price", 0))
        features.append(min(sale_price / 500, 2.0))

        # 2. Prix original (si disponible)
        original_price = deal_data.get("original_price", sale_price)
        features.append(min(original_price / 500, 2.0))

        # 3. Remise %
        discount_pct = deal_data.get("discount_percent", deal_data.get("discount_pct", 0)) or 0
        if discount_pct == 0 and original_price > sale_price:
            discount_pct = ((original_price - sale_price) / original_price) * 100
        features.append(min(discount_pct / 100, 1.0))

        # 4. Score de la marque
        brand = deal_data.get("brand", "")
        brand_score = self._get_brand_tier_score(brand) / 100
        features.append(brand_score)

        # 5. Poids catégorie
        category = deal_data.get("category", "sneakers_lifestyle")
        cat_weight = self._get_category_weight(category) / 100
        features.append(cat_weight)

        # 6. Mois (saisonnalité) - encodé circulaire
        month = datetime.now().month
        features.append(np.sin(2 * np.pi * month / 12))
        features.append(np.cos(2 * np.pi * month / 12))

        # 7. Stats Vinted (si disponibles)
        if vinted_stats:
            # Nombre d'annonces (normalisé sur 0-100)
            nb_listings = vinted_stats.get("nb_listings", 0)
            features.append(min(nb_listings / 100, 1.0))

            # Marge estimée
            margin_pct = vinted_stats.get("margin_pct", vinted_stats.get("margin_percent", 0)) or 0
            features.append(min(max(margin_pct, -50), 100) / 100)

            # Liquidité
            liquidity = vinted_stats.get("liquidity_score", 50) or 50
            features.append(liquidity / 100)

            # Coefficient de variation des prix
            cv = vinted_stats.get("coefficient_variation", 20) or 20
            features.append(min(cv / 50, 1.0))
        else:
            # Valeurs par défaut si pas de stats Vinted
            features.extend([0.3, 0.2, 0.5, 0.4])

        # 8. Tailles disponibles (booléen pour tailles standard)
        sizes = deal_data.get("sizes_available", [])
        if isinstance(sizes, dict):
            sizes = list(sizes.keys()) if sizes else []
        standard_sizes = {"40", "41", "42", "43", "44", "M", "L", "S", "XL"}
        has_standard = 1.0 if sizes and any(str(s) in standard_sizes for s in sizes) else 0.5
        features.append(has_standard)

        # 9. Coloris safe
        color = deal_data.get("color", "") or ""
        safe_colors = {"noir", "black", "blanc", "white", "gris", "grey", "gray", "bleu", "blue"}
        is_safe_color = 1.0 if any(c in color.lower() for c in safe_colors) else 0.6
        features.append(is_safe_color)

        return np.array(features).reshape(1, -1)

    def predict_flip_score(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Prédit le FlipScore avec le modèle ML

        Returns:
            Tuple (flip_score, metadata)
        """
        features = self._extract_features(deal_data, vinted_stats)

        if self.is_trained and self.model and self.scaler:
            try:
                # Normaliser les features
                features_scaled = self.scaler.transform(features)

                # Prédiction
                score = self.model.predict(features_scaled)[0]
                score = max(0, min(100, score))

                return round(score, 1), {
                    "model_version": self.model_version,
                    "source": "ml_prediction",
                    "features_count": features.shape[1]
                }
            except Exception as e:
                logger.warning(f"Erreur prédiction ML: {e}, fallback sur heuristique")

        # Fallback: scoring heuristique
        return self._heuristic_score(deal_data, vinted_stats, features)

    def _heuristic_score(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]],
        features: np.ndarray
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Scoring heuristique en fallback du ML
        Utilise les features déjà extraites
        """
        f = features.flatten()

        # Pondération des features
        # [price, orig_price, discount, brand, cat, sin_month, cos_month,
        #  nb_listings, margin, liquidity, cv, sizes, color]

        score = 50.0  # Base

        # Boost remise (index 2)
        discount_pct = f[2] * 100
        if discount_pct >= 50:
            score += 20
        elif discount_pct >= 30:
            score += 10
        elif discount_pct >= 20:
            score += 5

        # Boost marque (index 3)
        brand_score = f[3] * 100
        score += (brand_score - 50) * 0.3

        # Boost marge si dispo (index 8)
        if len(f) > 8:
            margin_norm = f[8]
            if margin_norm > 0.3:
                score += 15
            elif margin_norm > 0.2:
                score += 10
            elif margin_norm > 0.1:
                score += 5
            elif margin_norm < 0:
                score -= 10

        # Boost liquidité (index 9)
        if len(f) > 9:
            liquidity_norm = f[9]
            score += (liquidity_norm - 0.5) * 20

        # Boost tailles (index 11)
        if len(f) > 11:
            score += (f[11] - 0.5) * 10

        # Boost couleur (index 12)
        if len(f) > 12:
            score += (f[12] - 0.5) * 10

        score = max(0, min(100, score))

        return round(score, 1), {
            "model_version": "heuristic_v1",
            "source": "heuristic_fallback",
            "features_count": len(f)
        }

    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Entraîne le modèle avec les données d'outcomes

        Args:
            training_data: Liste de dicts avec:
                - deal_data: données du deal
                - vinted_stats: stats vinted (optionnel)
                - actual_score: score réel basé sur outcome

        Returns:
            Métriques d'entraînement
        """
        if not ML_AVAILABLE:
            return {"error": "sklearn non disponible"}

        if len(training_data) < 50:
            return {"error": f"Pas assez de données ({len(training_data)} < 50 minimum)"}

        logger.info(f"Entraînement ML avec {len(training_data)} exemples")

        # Préparer les features et labels
        X = []
        y = []

        for item in training_data:
            features = self._extract_features(
                item.get("deal_data", {}),
                item.get("vinted_stats")
            )
            X.append(features.flatten())
            y.append(item.get("actual_score", 50))

        X = np.array(X)
        y = np.array(y)

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Normalisation
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Entraînement
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)

        # Évaluation
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)

        # Sauvegarder
        self.is_trained = True
        self._save_model()

        metrics = {
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "rmse": round(rmse, 2),
            "mse": round(mse, 2),
            "feature_importance": dict(zip(
                ["price", "orig_price", "discount", "brand", "cat", "sin_m", "cos_m",
                 "listings", "margin", "liquidity", "cv", "sizes", "color"],
                [round(x, 3) for x in self.model.feature_importances_]
            ))
        }

        logger.info(f"Modèle entraîné - RMSE: {rmse:.2f}")
        return metrics

    def get_recommendation(
        self,
        flip_score: float,
        margin_pct: float = 0,
        margin_euro: float = 0
    ) -> Tuple[str, float]:
        """
        Détermine la recommandation basée sur le score ML
        """
        # Règles de décision
        if flip_score >= 80:
            if margin_pct >= 25 and margin_euro >= 15:
                return "buy", min(0.95, flip_score / 100)
            return "buy", min(0.85, flip_score / 100)
        elif flip_score >= 65:
            if margin_pct >= 20:
                return "buy", 0.7 + (flip_score - 65) / 100
            return "watch", 0.65
        elif flip_score >= 50:
            return "watch", 0.5 + (flip_score - 50) / 100
        else:
            return "ignore", 0.3 + flip_score / 200

    def estimate_margin(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Estime la marge basée sur les données disponibles
        """
        sale_price = deal_data.get("sale_price", deal_data.get("price", 0))

        if vinted_stats and vinted_stats.get("margin_pct"):
            margin_pct = vinted_stats["margin_pct"]
            margin_euro = vinted_stats.get("margin_euro", 0)
        else:
            # Estimation basée sur la remise et la marque
            discount_pct = deal_data.get("discount_percent", 0) or 0
            brand = deal_data.get("brand", "")
            brand_tier = self._get_brand_tier_score(brand)

            # Formule simplifiée: marge estimée = f(remise, popularité marque)
            # Plus la remise est haute et la marque populaire, plus la marge est bonne
            base_margin = discount_pct * 0.4  # 40% de la remise devient marge potentielle
            brand_bonus = (brand_tier - 50) * 0.2  # Bonus/malus marque

            margin_pct = base_margin + brand_bonus
            margin_euro = sale_price * (margin_pct / 100)

        # Prix de revente recommandé
        recommended_price = sale_price * (1 + margin_pct / 100) if margin_pct > 0 else sale_price * 1.1

        return {
            "estimated_margin_pct": round(margin_pct, 1),
            "estimated_margin_euro": round(margin_euro, 2),
            "recommended_price": round(recommended_price, 2)
        }


# Instance singleton
ml_scoring_engine = MLScoringEngine()


async def ml_score_deal(
    deal_data: Dict[str, Any],
    vinted_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Fonction helper pour scorer un deal avec ML
    """
    # Prédire le FlipScore
    flip_score, meta = ml_scoring_engine.predict_flip_score(deal_data, vinted_stats)

    # Estimer la marge
    margin_data = ml_scoring_engine.estimate_margin(deal_data, vinted_stats)

    # Recommandation
    recommendation, confidence = ml_scoring_engine.get_recommendation(
        flip_score,
        margin_data["estimated_margin_pct"],
        margin_data["estimated_margin_euro"]
    )

    # Risques
    risks = []
    if margin_data["estimated_margin_pct"] < 15:
        risks.append("Marge estimée faible")
    if not vinted_stats or vinted_stats.get("nb_listings", 0) < 10:
        risks.append("Données marché limitées")

    brand = deal_data.get("brand", "")
    if brand and ml_scoring_engine._get_brand_tier_score(brand) < 50:
        risks.append("Marque moins liquide")

    # Estimation délai de vente
    if flip_score >= 80:
        estimated_days = 5
    elif flip_score >= 65:
        estimated_days = 10
    elif flip_score >= 50:
        estimated_days = 15
    else:
        estimated_days = 25

    return {
        "flip_score": flip_score,
        "margin_score": min(100, margin_data["estimated_margin_pct"] * 2),
        "liquidity_score": min(100, (vinted_stats or {}).get("liquidity_score", 50)),
        "popularity_score": ml_scoring_engine._get_brand_tier_score(deal_data.get("brand")),
        "recommended_action": recommendation,
        "recommended_price": margin_data["recommended_price"],
        "confidence": confidence,
        "risks": risks,
        "estimated_sell_days": estimated_days,
        "model_version": meta.get("model_version", "ml_v1"),
        "score_breakdown": {
            "discount_score": min(100, (deal_data.get("discount_percent", 0) or 0) * 1.5),
            "margin_score": min(100, margin_data["estimated_margin_pct"] * 2),
            "brand_score": ml_scoring_engine._get_brand_tier_score(deal_data.get("brand")),
            "estimated_margin_pct": margin_data["estimated_margin_pct"],
            "estimated_margin_euro": margin_data["estimated_margin_euro"]
        }
    }
