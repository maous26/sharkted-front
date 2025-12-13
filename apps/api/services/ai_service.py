"""
AI Service V2 - Unified AI Pipeline for Sellshark
SharkScore: The intelligent resale scoring algorithm
Combines: Entity Extraction, Product Classification, Risk Analysis, Scoring, LLM Analysis
"""

import json
import re
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from loguru import logger
from openai import AsyncOpenAI

from config import settings, CATEGORY_WEIGHTS, BRAND_TIERS


class EntityExtractor:
    """Extract product entities (brand, model, color, size, gender) from text."""

    # Common brand aliases
    BRAND_ALIASES = {
        "nke": "nike",
        "nb": "new balance",
        "rl": "ralph lauren",
        "polo ralph lauren": "ralph lauren",
        "polo": "ralph lauren",
        "adidas originals": "adidas",
        "air jordan": "jordan",
        "aj": "jordan",
        "asics tiger": "asics",
        "tnf": "the north face",
        "tommy": "tommy hilfiger",
        "th": "tommy hilfiger",
    }

    # Known model patterns for major brands
    MODEL_PATTERNS = {
        "nike": [
            r"air max (?:90|95|97|1|270|720|plus|tn)",
            r"air force (?:1|one|af1)",
            r"dunk (?:low|high|sb)",
            r"blazer (?:mid|low)",
            r"cortez",
            r"vapormax",
            r"zoom",
            r"tech fleece",
            r"acg",
        ],
        "adidas": [
            r"yeezy (?:350|500|700|boost|foam)",
            r"superstar",
            r"stan smith",
            r"gazelle",
            r"samba",
            r"campus",
            r"forum (?:low|high|84)",
            r"ultraboost",
            r"nmd",
            r"ozweego",
        ],
        "jordan": [
            r"(?:jordan|air jordan|aj)\s*(?:1|2|3|4|5|6|11|12|13)",
            r"retro",
            r"mid",
            r"low",
            r"high",
        ],
        "new balance": [
            r"(?:nb\s*)?(?:327|530|550|574|990|991|992|993|2002r|1906)",
            r"made in (?:usa|uk|england)",
        ],
        "ralph lauren": [
            r"polo",
            r"oxford",
            r"slim fit",
            r"custom fit",
            r"classic fit",
            r"big pony",
            r"bear",
        ],
        "asics": [
            r"gel[ -](?:kayano|nimbus|1130|lyte|quantum|contend)",
            r"gt-(?:1000|2000)",
        ],
    }

    # Color mappings (FR -> EN normalized)
    COLOR_MAP = {
        "noir": "black", "blanc": "white", "gris": "grey",
        "rouge": "red", "bleu": "blue", "vert": "green",
        "jaune": "yellow", "orange": "orange", "rose": "pink",
        "violet": "purple", "marron": "brown", "beige": "beige",
        "creme": "cream", "navy": "navy", "kaki": "khaki",
        "bordeaux": "burgundy", "turquoise": "turquoise",
    }

    # Size patterns
    SIZE_PATTERNS = {
        "shoes": r"(?:taille|size|sz|eu|us|uk)?\s*(\d{2}(?:[.,]\d)?)",
        "clothing": r"(?:taille|size)?\s*(XXS|XS|S|M|L|XL|XXL|XXXL|\d{2})",
    }

    def extract_brand(self, text: str) -> Optional[str]:
        """Extract brand from product text."""
        text_lower = text.lower()

        # Check known brands first
        for brand in BRAND_TIERS.keys():
            if brand in text_lower:
                return brand.title()

        # Check aliases
        for alias, brand in self.BRAND_ALIASES.items():
            if alias in text_lower:
                return brand.title()

        return None

    def extract_model(self, text: str, brand: Optional[str] = None) -> Optional[str]:
        """Extract model from product text."""
        text_lower = text.lower()

        if brand:
            brand_lower = brand.lower()
            patterns = self.MODEL_PATTERNS.get(brand_lower, [])

            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    return match.group(0).title()

        # Try all patterns
        for brand_patterns in self.MODEL_PATTERNS.values():
            for pattern in brand_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    return match.group(0).title()

        return None

    def extract_color(self, text: str) -> Optional[str]:
        """Extract color from product text."""
        text_lower = text.lower()

        # Check French colors
        for fr_color, en_color in self.COLOR_MAP.items():
            if fr_color in text_lower:
                return en_color

        # Check English colors
        english_colors = ["black", "white", "grey", "gray", "red", "blue", "green",
                        "yellow", "orange", "pink", "purple", "brown", "beige", "navy"]
        for color in english_colors:
            if color in text_lower:
                return color

        return None

    def extract_gender(self, text: str) -> Optional[str]:
        """Extract gender from product text."""
        text_lower = text.lower()

        male_terms = ["homme", "men", "mens", "man", "male", "masculin", "garçon", "boy"]
        female_terms = ["femme", "women", "womens", "woman", "female", "féminin", "fille", "girl"]
        kids_terms = ["enfant", "kids", "child", "junior", "jr", "gs"]
        unisex_terms = ["unisex", "unisexe", "mixte"]

        for term in kids_terms:
            if term in text_lower:
                return "kids"

        for term in unisex_terms:
            if term in text_lower:
                return "unisex"

        for term in male_terms:
            if term in text_lower:
                return "men"

        for term in female_terms:
            if term in text_lower:
                return "women"

        return None

    def extract_sizes(self, text: str, category: str = "shoes") -> List[str]:
        """Extract available sizes from text."""
        sizes = []

        pattern = self.SIZE_PATTERNS.get(category, self.SIZE_PATTERNS["shoes"])
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match in matches:
            size = match.strip().upper()
            if size and size not in sizes:
                sizes.append(size)

        return sizes

    def extract_all(self, text: str, category_hint: Optional[str] = "sneakers") -> Dict[str, Any]:
        """Extract all entities from product text."""
        brand = self.extract_brand(text)
        model = self.extract_model(text, brand)
        color = self.extract_color(text)
        gender = self.extract_gender(text)

        category_hint = category_hint or "sneakers"
        size_category = "shoes" if "sneakers" in category_hint.lower() else "clothing"
        sizes = self.extract_sizes(text, size_category)

        return {
            "brand": brand,
            "model": model,
            "color": color,
            "gender": gender,
            "sizes_detected": sizes,
            "extraction_confidence": self._calculate_confidence(brand, model, color)
        }

    def _calculate_confidence(
        self,
        brand: Optional[str],
        model: Optional[str],
        color: Optional[str]
    ) -> float:
        """Calculate confidence score for extraction."""
        score = 0.3  # Base confidence

        if brand:
            score += 0.3
        if model:
            score += 0.25
        if color:
            score += 0.15

        return min(score, 1.0)


class ProductClassifier:
    """Classify products into categories and subcategories."""

    CATEGORY_RULES = {
        "sneakers_lifestyle": {
            "keywords": ["air force", "dunk", "superstar", "stan smith", "gazelle",
                        "samba", "campus", "574", "550", "327", "jordan", "blazer"],
            "brands": ["nike", "adidas", "jordan", "new balance", "converse", "puma"],
        },
        "sneakers_running": {
            "keywords": ["running", "run", "boost", "ultraboost", "pegasus", "zoom",
                        "gel-kayano", "gel-nimbus", "fresh foam", "fuelcell", "vaporfly"],
            "brands": ["asics", "hoka", "saucony", "brooks", "mizuno"],
        },
        "textile_premium": {
            "keywords": ["polo", "oxford", "chemise", "shirt", "pull", "sweater",
                        "veste", "jacket", "blazer"],
            "brands": ["ralph lauren", "lacoste", "tommy hilfiger", "gant"],
        },
        "textile_streetwear": {
            "keywords": ["tech fleece", "hoodie", "sweat", "t-shirt", "tee", "jogger",
                        "tracksuit", "survêtement"],
            "brands": ["nike", "adidas", "supreme", "stussy"],
        },
        "accessoires": {
            "keywords": ["casquette", "cap", "bonnet", "beanie", "sac", "bag",
                        "ceinture", "belt", "écharpe", "scarf", "portefeuille", "wallet"],
            "brands": [],
        },
    }

    def classify(
        self,
        product_name: str,
        brand: Optional[str] = None,
        detected_category: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Classify product into category.

        Returns:
            Tuple (category_key, confidence)
        """
        text_lower = product_name.lower()
        brand_lower = brand.lower() if brand else ""

        scores = {}

        for category, rules in self.CATEGORY_RULES.items():
            score = 0

            # Check keywords
            for keyword in rules["keywords"]:
                if keyword in text_lower:
                    score += 0.4

            # Check brands
            for cat_brand in rules["brands"]:
                if cat_brand in brand_lower or cat_brand in text_lower:
                    score += 0.3

            # Use hint if provided
            if detected_category and detected_category.lower() in category:
                score += 0.2

            scores[category] = min(score, 1.0)

        # Get best match
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]

            if best_score >= 0.2:
                return best_category, best_score

        # Default fallback
        return "sneakers_lifestyle", 0.3


class RiskAnalyzer:
    """Analyze risks for resale deals - Component of SharkScore V2."""

    # Tailles liquides (faciles à revendre)
    LIQUID_SIZES = {
        "shoes": {"41", "42", "43", "44", "45"},
        "clothing": {"S", "M", "L"}
    }

    # Tailles atypiques (difficiles à revendre)
    ATYPICAL_SIZES = {
        "shoes": {"38", "39", "46", "47", "48", "49"},
        "clothing": {"XXS", "XS", "XXL", "XXXL"}
    }

    # Coloris difficiles à revendre
    RISKY_COLORS = {"rose", "pink", "jaune", "yellow", "orange", "violet", "purple", "turquoise"}

    # Coloris faciles à revendre
    SAFE_COLORS = {"noir", "black", "blanc", "white", "gris", "grey", "gray", "navy", "beige"}

    # Produits saisonniers
    SEASONAL_PRODUCTS = {
        "sandales": [11, 12, 1, 2],  # Mois défavorables
        "tongs": [11, 12, 1, 2],
        "flip-flop": [11, 12, 1, 2],
        "boots": [5, 6, 7, 8],
        "bottes": [5, 6, 7, 8],
        "doudoune": [5, 6, 7, 8],
        "puffer": [5, 6, 7, 8],
    }

    def calculate_risk_score(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]],
        category: str,
        brand: Optional[str]
    ) -> Tuple[float, List[str]]:
        """
        Calculate risk score (0-100, higher = less risky).

        Returns:
            Tuple (risk_score, list of risk factors)
        """
        risk_score = 100  # Start at max, subtract for each risk
        risk_factors = []

        # 1. Size risk (-15 to 0)
        sizes = deal_data.get("sizes_available", [])
        size_type = "shoes" if "sneakers" in category else "clothing"

        if sizes:
            sizes_str = {str(s).upper() for s in sizes}
            atypical = sizes_str & self.ATYPICAL_SIZES[size_type]
            liquid = sizes_str & self.LIQUID_SIZES[size_type]

            if atypical and not liquid:
                risk_score -= 15
                risk_factors.append(f"Tailles atypiques uniquement ({', '.join(atypical)})")
            elif not liquid:
                risk_score -= 8
                risk_factors.append("Aucune taille liquide disponible")

        # 2. Color risk (-20 to 0)
        color = deal_data.get("color", "")
        if color:
            color_lower = color.lower()
            if any(c in color_lower for c in self.RISKY_COLORS):
                risk_score -= 20
                risk_factors.append(f"Coloris difficile ({color})")
            elif not any(c in color_lower for c in self.SAFE_COLORS):
                risk_score -= 5
                risk_factors.append("Coloris non standard")

        # 3. Seasonality risk (-25 to 0)
        current_month = datetime.now().month
        product_name = deal_data.get("product_name", "").lower()

        for product_type, bad_months in self.SEASONAL_PRODUCTS.items():
            if product_type in product_name and current_month in bad_months:
                risk_score -= 25
                risk_factors.append(f"Produit saisonnier (hors saison)")
                break

        # 4. Brand tier risk (-15 to 0)
        if brand:
            brand_lower = brand.lower()
            brand_info = BRAND_TIERS.get(brand_lower)
            if brand_info:
                tier = brand_info["tier"]
                if tier == "C":
                    risk_score -= 15
                    risk_factors.append("Marque peu demandée (Tier C)")
                elif tier == "B":
                    risk_score -= 5
                    risk_factors.append("Marque demande moyenne (Tier B)")
            else:
                risk_score -= 10
                risk_factors.append("Marque non référencée")

        # 5. Market data risk (-20 to 0)
        if vinted_stats:
            nb_listings = vinted_stats.get("nb_listings", 0)
            cv = vinted_stats.get("coefficient_variation", 0)

            if nb_listings < 5:
                risk_score -= 20
                risk_factors.append(f"Très peu d'annonces Vinted ({nb_listings})")
            elif nb_listings < 15:
                risk_score -= 10
                risk_factors.append(f"Peu d'annonces Vinted ({nb_listings})")

            if cv and cv > 40:
                risk_score -= 10
                risk_factors.append(f"Prix très variables (CV: {cv:.0f}%)")
            elif cv and cv > 25:
                risk_score -= 5
                risk_factors.append(f"Prix variables (CV: {cv:.0f}%)")
        else:
            risk_score -= 20
            risk_factors.append("Pas de données de marché")

        # 6. Margin risk (-15 to 0)
        if vinted_stats:
            margin_euro = vinted_stats.get("margin_euro", 0)
            if margin_euro < 0:
                risk_score -= 15
                risk_factors.append(f"Marge négative ({margin_euro:.0f}€)")
            elif margin_euro < 10:
                risk_score -= 10
                risk_factors.append(f"Marge très faible ({margin_euro:.0f}€)")
            elif margin_euro < 20:
                risk_score -= 5
                risk_factors.append(f"Marge faible ({margin_euro:.0f}€)")

        return max(0, risk_score), risk_factors


class AIService:
    """
    Unified AI Service for Sellshark V2.
    Orchestrates all AI components: extraction, classification, risk analysis, scoring, LLM analysis.

    SharkScore V2 Formula:
    SharkScore = (Marge × 0.40) + (Liquidité × 0.30) + (Popularité × 0.20) + (Anti-Risque × 0.10)
    """

    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        self.entity_extractor = EntityExtractor()
        self.product_classifier = ProductClassifier()
        self.risk_analyzer = RiskAnalyzer()

    async def analyze_deal(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        include_llm_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Full AI analysis pipeline for a deal.

        Args:
            deal_data: Deal information (product_name, brand, sale_price, etc.)
            vinted_stats: Market statistics from Vinted
            user_preferences: User preferences for personalization
            include_llm_analysis: Whether to include LLM-powered explanation

        Returns:
            Complete analysis with SharkScore, recommendation, explanation
        """

        # Step 1: Entity extraction
        product_text = f"{deal_data.get('product_name', '')} {deal_data.get('brand', '')} {deal_data.get('model', '')}"
        entities = self.entity_extractor.extract_all(
            product_text,
            deal_data.get("category", "sneakers")
        )

        # Merge with existing data
        brand = deal_data.get("brand") or entities.get("brand")
        model = deal_data.get("model") or entities.get("model")
        color = deal_data.get("color") or entities.get("color")
        gender = deal_data.get("gender") or entities.get("gender")

        # Step 2: Classification
        category, category_confidence = self.product_classifier.classify(
            deal_data.get("product_name", ""),
            brand,
            deal_data.get("category")
        )

        # Step 3: Calculate Risk Score
        risk_score, risk_factors = self.risk_analyzer.calculate_risk_score(
            deal_data, vinted_stats, category, brand
        )

        # Step 4: Calculate SharkScore V2
        if vinted_stats:
            shark_score, score_components = self._calculate_shark_score(
                deal_data, vinted_stats, category, brand, risk_score
            )
        else:
            shark_score = 0
            score_components = {
                "margin_score": 0,
                "liquidity_score": 0,
                "popularity_score": 0,
                "risk_score": risk_score
            }

        # Step 5: Generate recommendation
        recommendation, confidence = self._get_recommendation(
            shark_score,
            vinted_stats.get("margin_percent", 0) if vinted_stats else 0,
            vinted_stats.get("margin_euro", 0) if vinted_stats else 0,
            risk_score
        )

        # Step 6: Calculate recommended prices
        recommended_prices = self._calculate_recommended_prices(vinted_stats) if vinted_stats else {}

        # Step 7: Estimate sell days
        estimated_sell_days = self._estimate_sell_days(
            shark_score,
            vinted_stats.get("liquidity_score", 0) if vinted_stats else 0,
            category
        )

        # Step 8: LLM Analysis (optional)
        if include_llm_analysis and self.openai_client:
            llm_analysis = await self._generate_llm_analysis(
                deal_data=deal_data,
                vinted_stats=vinted_stats,
                shark_score=shark_score,
                score_components=score_components,
                recommendation=recommendation,
                risk_factors=risk_factors,
                user_preferences=user_preferences
            )
        else:
            llm_analysis = self._generate_basic_explanation(
                deal_data, vinted_stats, shark_score, score_components, recommendation, risk_factors
            )

        return {
            # Core scores - SharkScore V2
            "shark_score": shark_score,
            "score_components": score_components,

            # Recommendation
            "recommended_action": recommendation,
            "confidence": confidence,
            "recommended_price": recommended_prices.get("optimal", 0),
            "recommended_price_range": recommended_prices,
            "estimated_sell_days": estimated_sell_days,

            # Analysis
            "explanation": llm_analysis.get("explanation", ""),
            "explanation_short": llm_analysis.get("explanation_short", ""),
            "risks": risk_factors,
            "opportunities": llm_analysis.get("opportunities", []),
            "tips": llm_analysis.get("tips", []),

            # Extracted entities
            "extracted_entities": {
                "brand": brand,
                "model": model,
                "color": color,
                "gender": gender,
                "category": category,
                "category_confidence": category_confidence,
            },

            # Metadata
            "model_version": "sharkscore_v2",
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_shark_score(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Dict[str, Any],
        category: str,
        brand: Optional[str],
        risk_score: float
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate SharkScore V2 with component breakdown.

        Formula: SharkScore = (Marge × 0.40) + (Liquidité × 0.30) + (Popularité × 0.20) + (Anti-Risque × 0.10)
        """

        margin_percent = vinted_stats.get("margin_percent", 0)
        margin_euro = vinted_stats.get("margin_euro", 0)
        nb_listings = vinted_stats.get("nb_listings", 0)
        liquidity_from_vinted = vinted_stats.get("liquidity_score", 0)

        # Get category config
        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["sneakers_lifestyle"])

        # ============================================
        # 1. MARGIN SCORE (40%) - Normalized to 50% cap
        # ============================================
        # min(margin_pct / 50, 1) × 100 (cap à 50% = score max)
        if margin_percent <= 0:
            margin_score = 0
        else:
            margin_score = min(margin_percent / 50, 1.0) * 100

        # Bonus for absolute margin (important for low-price items)
        if margin_euro >= 40:
            margin_score = min(margin_score + 10, 100)
        elif margin_euro >= 25:
            margin_score = min(margin_score + 5, 100)

        # ============================================
        # 2. LIQUIDITY SCORE (30%) - Based on listings count
        # ============================================
        # min(nb_listings / 50, 1) × 100
        if nb_listings == 0:
            listings_score = 0
        else:
            listings_score = min(nb_listings / 50, 1.0) * 100

        # Combine with Vinted's calculated liquidity score
        liquidity_score = (listings_score * 0.5 + liquidity_from_vinted * 0.5)

        # ============================================
        # 3. POPULARITY SCORE (20%) - Brand-based
        # ============================================
        base_popularity = 50  # Default for unknown brands

        if brand:
            brand_lower = brand.lower()
            brand_info = BRAND_TIERS.get(brand_lower)
            if brand_info:
                tier = brand_info["tier"]
                bonus = brand_info["popularity_bonus"]
                if tier == "S":
                    base_popularity = 90
                elif tier == "A":
                    base_popularity = 75
                elif tier == "B":
                    base_popularity = 60
                else:  # Tier C
                    base_popularity = 40
                base_popularity *= bonus

        popularity_score = min(base_popularity, 100)

        # ============================================
        # 4. RISK SCORE (10%) - Already calculated (0-100)
        # ============================================
        # risk_score is already 0-100, higher = less risky

        # ============================================
        # FINAL SHARKSCORE CALCULATION
        # ============================================
        shark_score = (
            margin_score * 0.40 +
            liquidity_score * 0.30 +
            popularity_score * 0.20 +
            risk_score * 0.10
        )

        final_score = max(0, min(100, shark_score))

        components = {
            "margin_score": round(margin_score, 1),
            "liquidity_score": round(liquidity_score, 1),
            "popularity_score": round(popularity_score, 1),
            "risk_score": round(risk_score, 1)
        }

        return round(final_score, 1), components

    def _get_recommendation(
        self,
        shark_score: float,
        margin_percent: float,
        margin_euro: float,
        risk_score: float
    ) -> Tuple[str, float]:
        """Determine recommendation based on SharkScore V2."""

        # BUY: High score + positive margin + acceptable risk
        if shark_score >= 75 and margin_percent >= 25 and margin_euro >= 15 and risk_score >= 50:
            return "buy", min(0.95, shark_score / 100)
        elif shark_score >= 65 and margin_percent >= 20 and margin_euro >= 10:
            return "buy", min(0.85, shark_score / 100)

        # WATCH: Decent score but some concerns
        elif shark_score >= 50 and margin_percent >= 15:
            return "watch", 0.5 + (shark_score - 50) / 100
        elif shark_score >= 40:
            return "watch", 0.45

        # IGNORE: Low score or negative margin
        else:
            return "ignore", 0.3 + shark_score / 200

    def _calculate_recommended_prices(self, vinted_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate recommended selling prices."""

        price_median = vinted_stats.get("price_median", 0)
        price_p25 = vinted_stats.get("price_p25", 0)
        price_p75 = vinted_stats.get("price_p75", 0)

        if not price_median:
            return {"aggressive": 0, "optimal": 0, "patient": 0}

        return {
            "aggressive": round(price_p25 * 0.95, 2),  # Vente rapide
            "optimal": round(price_median * 0.98, 2),  # Prix équilibré
            "patient": round(price_p75 * 0.95, 2)      # Maximiser le profit
        }

    def _estimate_sell_days(
        self,
        shark_score: float,
        liquidity_score: float,
        category: str
    ) -> int:
        """Estimate days to sell based on SharkScore and liquidity."""

        cat_config = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["sneakers_lifestyle"])
        base_days = cat_config["expected_sell_days"]

        if shark_score >= 80 and liquidity_score >= 70:
            return max(2, base_days - 5)
        elif shark_score >= 70 and liquidity_score >= 50:
            return max(3, base_days - 3)
        elif shark_score >= 60:
            return base_days
        elif shark_score >= 40:
            return base_days + 5
        else:
            return base_days + 10

    async def _generate_llm_analysis(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]],
        shark_score: float,
        score_components: Dict[str, float],
        recommendation: str,
        risk_factors: List[str],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate LLM-powered analysis."""

        if not self.openai_client:
            return self._generate_basic_explanation(
                deal_data, vinted_stats, shark_score, score_components, recommendation, risk_factors
            )

        prompt = self._build_analysis_prompt(
            deal_data, vinted_stats, shark_score, score_components,
            recommendation, risk_factors, user_preferences
        )

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=800
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return self._generate_basic_explanation(
                deal_data, vinted_stats, shark_score, score_components, recommendation, risk_factors
            )

    def _get_system_prompt(self) -> str:
        """System prompt for LLM analysis."""
        return """Tu es un expert en resell mode sur Vinted pour Sellshark. Ton rôle est d'analyser des opportunités d'achat-revente et de fournir des recommandations précises et actionnables.

Tu dois toujours répondre en JSON avec cette structure:
{
    "explanation": "Explication détaillée de 2-3 phrases",
    "explanation_short": "Résumé en une phrase avec emoji (🦈/🟢/🟡/🔴)",
    "opportunities": ["opportunité 1", "opportunité 2"],
    "tips": ["conseil 1", "conseil 2"]
}

Utilise 🦈 pour les excellents deals (SharkScore > 75), 🟢 pour les bons (60-75), 🟡 pour les moyens (40-60), 🔴 pour les mauvais (<40).

Sois factuel, concis et actionnable. Pas de phrases bateau."""

    def _build_analysis_prompt(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]],
        shark_score: float,
        score_components: Dict[str, float],
        recommendation: str,
        risk_factors: List[str],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the analysis prompt for LLM."""

        margin_pct = vinted_stats.get("margin_percent", 0) if vinted_stats else 0
        margin_euro = vinted_stats.get("margin_euro", 0) if vinted_stats else 0
        nb_listings = vinted_stats.get("nb_listings", 0) if vinted_stats else 0

        prompt = f"""Analyse ce deal de resell:

PRODUIT:
- Nom: {deal_data.get('product_name', 'N/A')}
- Marque: {deal_data.get('brand', 'N/A')}
- Prix achat: {deal_data.get('sale_price', 0)}€
- Réduction: {deal_data.get('discount_percent', 0) or deal_data.get('discount_pct', 0):.0f}%

MARCHÉ VINTED:
- Annonces: {nb_listings}
- Prix médian: {vinted_stats.get('price_median', 0) if vinted_stats else 0}€
- Marge: {margin_euro:.0f}€ ({margin_pct:.0f}%)

SHARKSCORE V2: {shark_score}/100
- Score marge: {score_components.get('margin_score', 0)}/100
- Score liquidité: {score_components.get('liquidity_score', 0)}/100
- Score popularité: {score_components.get('popularity_score', 0)}/100
- Score anti-risque: {score_components.get('risk_score', 0)}/100

RECOMMANDATION: {recommendation.upper()}
RISQUES IDENTIFIÉS: {', '.join(risk_factors) if risk_factors else 'Aucun'}"""

        if user_preferences:
            prompt += f"""

PRÉFÉRENCES USER:
- Marge minimum: {user_preferences.get('min_margin', 20)}%
- Profil: {user_preferences.get('risk_profile', 'balanced')}"""

        prompt += "\n\nFournis ton analyse en JSON."

        return prompt

    def _generate_basic_explanation(
        self,
        deal_data: Dict[str, Any],
        vinted_stats: Optional[Dict[str, Any]],
        shark_score: float,
        score_components: Dict[str, float],
        recommendation: str,
        risk_factors: List[str]
    ) -> Dict[str, Any]:
        """Generate basic explanation without LLM."""

        margin_pct = vinted_stats.get("margin_percent", 0) if vinted_stats else 0
        nb_listings = vinted_stats.get("nb_listings", 0) if vinted_stats else 0

        parts = []

        # Margin analysis
        margin_score = score_components.get("margin_score", 0)
        if margin_score >= 70:
            parts.append(f"Excellente marge ({margin_pct:.0f}%)")
        elif margin_score >= 40:
            parts.append(f"Marge correcte ({margin_pct:.0f}%)")
        elif margin_pct > 0:
            parts.append(f"Marge faible ({margin_pct:.0f}%)")
        else:
            parts.append(f"Marge négative ({margin_pct:.0f}%)")

        # Liquidity analysis
        liq_score = score_components.get("liquidity_score", 0)
        if liq_score >= 60:
            parts.append(f"marché actif ({nb_listings} annonces)")
        elif liq_score >= 30:
            parts.append(f"liquidité moyenne ({nb_listings} annonces)")
        else:
            parts.append(f"peu d'annonces ({nb_listings})")

        # Recommendation
        if recommendation == "buy":
            conclusion = "Deal recommandé à l'achat."
            emoji = "🦈" if shark_score >= 75 else "🟢"
        elif recommendation == "watch":
            conclusion = "À surveiller pour une meilleure opportunité."
            emoji = "🟡"
        else:
            conclusion = "Pass recommandé."
            emoji = "🔴"

        explanation = f"{', '.join(parts)}. {conclusion}"
        explanation_short = f"{emoji} {recommendation.capitalize()} - SharkScore {shark_score:.0f}/100"

        # Opportunities
        opportunities = []
        if margin_pct >= 30:
            opportunities.append("Marge excellente")
        if nb_listings >= 40:
            opportunities.append("Marché très liquide")
        discount = deal_data.get("discount_percent", 0) or deal_data.get("discount_pct", 0)
        if discount >= 50:
            opportunities.append("Forte réduction")
        if score_components.get("risk_score", 0) >= 80:
            opportunities.append("Profil de risque faible")

        # Tips
        tips = [
            "Prends des photos avec bon éclairage naturel",
        ]
        if vinted_stats and vinted_stats.get("price_median"):
            tips.append(f"Liste autour de {vinted_stats['price_median']:.0f}€ pour une vente rapide")
        if risk_factors:
            tips.append(f"Attention: {risk_factors[0]}")

        return {
            "explanation": explanation,
            "explanation_short": explanation_short,
            "opportunities": opportunities,
            "tips": tips
        }

    async def batch_analyze(
        self,
        deals: List[Dict[str, Any]],
        include_llm: bool = False
    ) -> List[Dict[str, Any]]:
        """Analyze multiple deals in batch."""

        tasks = [
            self.analyze_deal(deal, deal.get("vinted_stats"), include_llm_analysis=include_llm)
            for deal in deals
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        analyzed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing deal {i}: {result}")
                analyzed.append({"error": str(result), "shark_score": 0})
            else:
                analyzed.append(result)

        return analyzed


# Singleton instance
ai_service = AIService()


async def analyze_deal_full(
    deal_data: Dict[str, Any],
    vinted_stats: Optional[Dict[str, Any]] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for full deal analysis.
    """
    return await ai_service.analyze_deal(
        deal_data=deal_data,
        vinted_stats=vinted_stats,
        user_preferences=user_preferences,
        include_llm_analysis=True
    )
