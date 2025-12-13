"""Embedding service for semantic matching."""
import logging
from typing import List, Optional
import hashlib

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and comparing text embeddings."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_embedding_model
        self._cache: dict = {}  # Simple in-memory cache

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for a text string."""
        if not self.client:
            logger.warning("OpenAI client not initialized")
            return None

        # Check cache
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            embedding = response.data[0].embedding

            # Cache result
            self._cache[cache_key] = embedding

            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for multiple texts in a batch."""
        if not self.client:
            return [None] * len(texts)

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
            )

            embeddings = [None] * len(texts)
            for item in response.data:
                embeddings[item.index] = item.embedding

            return embeddings
        except Exception as e:
            logger.error(f"Error getting batch embeddings: {e}")
            return [None] * len(texts)

    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not embedding1 or not embedding2:
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Calculate magnitudes
        mag1 = sum(a * a for a in embedding1) ** 0.5
        mag2 = sum(b * b for b in embedding2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    async def find_best_match(
        self,
        query_embedding: List[float],
        candidate_texts: List[str],
        threshold: float = 0.7,
    ) -> Optional[tuple[int, float]]:
        """Find the best matching text from candidates."""
        if not query_embedding or not candidate_texts:
            return None

        # Get embeddings for all candidates
        candidate_embeddings = await self.get_embeddings_batch(candidate_texts)

        best_idx = -1
        best_score = 0.0

        for i, emb in enumerate(candidate_embeddings):
            if emb:
                score = self.cosine_similarity(query_embedding, emb)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_idx = i

        if best_idx >= 0:
            return (best_idx, best_score)
        return None

    def build_product_text(
        self,
        brand: str,
        model: Optional[str] = None,
        category: Optional[str] = None,
        color: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> str:
        """Build a text representation of a product for embedding."""
        parts = [brand]

        if model:
            parts.append(model)

        if category:
            parts.append(category)

        if color:
            parts.append(color)

        if gender:
            gender_map = {
                "men": "homme",
                "women": "femme",
                "kids": "enfant",
                "unisex": "unisexe",
            }
            parts.append(gender_map.get(gender, gender))

        return " ".join(parts)

    async def calculate_match_score(
        self,
        product_text: str,
        listing_title: str,
    ) -> float:
        """Calculate semantic match score between product and listing."""
        if not self.client:
            # Fallback to simple text matching
            return self._simple_match_score(product_text, listing_title)

        try:
            # Get embeddings
            product_emb = await self.get_embedding(product_text)
            listing_emb = await self.get_embedding(listing_title)

            if product_emb and listing_emb:
                return self.cosine_similarity(product_emb, listing_emb)
        except Exception as e:
            logger.warning(f"Error calculating match score: {e}")

        return self._simple_match_score(product_text, listing_title)

    def _simple_match_score(self, text1: str, text2: str) -> float:
        """Simple text matching fallback."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0
