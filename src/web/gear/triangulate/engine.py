"""
Fact Triangulator - "The Judge"

Cross-verifies claims by finding independent sources.
"""

import logging
from typing import Any

logger = logging.getLogger("web.triangulate")


# Mocking mechanism for reasonkit_mem
try:
    import reasonkit_mem  # type: ignore
except ImportError:
    logger.warning("reasonkit_mem not found. Using simulation mock for Triangulation Protocol V2.")

    class MockTriangulator:
        def verify_batch(self, claim: str, contexts: list[str]) -> list[float]:
            results = []
            claim_words = set(claim.lower().split())
            if not claim_words:
                return [0.0] * len(contexts)

            for ctx in contexts:
                ctx_lower = ctx.lower()
                matches = sum(1 for w in claim_words if w in ctx_lower)
                score = matches / len(claim_words)
                results.append(min(1.0, score))
            return results

    class _MockModule:
        Triangulator = MockTriangulator

    reasonkit_mem = _MockModule()


class SemanticVerifier:
    """
    Implementation of Triangulation Protocol V2.
    Delegates heavy compute (embeddings) to Rust/reasonkit-mem.
    """

    def __init__(self):
        try:
            self.engine = reasonkit_mem.Triangulator()
        except Exception as e:
            logger.error(f"Failed to init Triangulator: {e}")
            # Create a mock instance if the real one fails
            self.engine = MockTriangulator()

    def triangulate(self, claim: str, sources: list[str]) -> float:
        """
        Returns a confidence score 0.0 - 1.0 using Noisy-OR Aggregation.
        Formula: P(Truth) = 1 - product(1 - (Score * alpha))
        """
        if not sources:
            return 0.0

        try:
            scores = self.engine.verify_batch(claim, sources)
        except Exception as e:
            logger.error(f"Error in verify_batch: {e}")
            return 0.0

        p_false = 1.0
        strictness = 0.8

        for score in scores:
            if score > 0.7:  # Relevance threshold
                p_false *= 1.0 - (score * strictness)

        return 1.0 - p_false


class TriangulationEngine:
    """
    Engine for cross-referencing claims against multiple sources.
    Wrapper around SemanticVerifier for Protocol V2.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.min_sources = self.config.get("verify.min_sources", 3)
        self.verifier = SemanticVerifier()

    async def verify(self, claim: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Verify a claim against a list of source documents.

        Args:
            claim: The claim to verify.
            sources: List of dicts with 'url', 'content', 'date'.

        Returns:
            Verification result with confidence score.
        """
        source_texts = [s.get("content", "") for s in sources]

        confidence = self.verifier.triangulate(claim, source_texts)

        # Protocol V2: Threshold 0.85
        success = confidence > 0.85

        return {
            "verified": success,
            "claim": claim,
            "source_count": len(sources),
            "required_confidence": 0.85,
            "confidence": confidence,
            "method": "semantic_triangulation_v2",
        }
