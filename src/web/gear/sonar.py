"""
Web Sonar Gear - Drift Detection Implementation

Detects when research is looping or encountering redundant information.
Based on Protocol Beta (Anti-Drift) architecture.

Uses compression ratio as a proxy for information novelty:
- High ratio (>1.05): New information detected
- Low ratio (<1.05): Redundant content, possible saturation
"""

import logging
import zlib
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("web.sonar")


@dataclass
class SonarResult:
    """Result of sonar analysis."""

    information_gain: float
    is_saturated: bool
    saturation_level: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "information_gain": round(self.information_gain, 4),
            "is_saturated": self.is_saturated,
            "saturation_level": self.saturation_level,
            "recommendation": self.recommendation,
        }


class DiveSonarGear:
    """
    Drift Detection gear for research monitoring.

    Analyzes text for information saturation using compression ratios.
    Detects when an agent is seeing redundant content (Zombie Researcher problem).
    """

    def __init__(self):
        self.saturation_counter = 0
        self.max_consecutive_saturations = 3

    def analyze(
        self,
        new_text: str,
        context: str,
        threshold: float = 1.05,
    ) -> dict[str, Any]:
        """
        Analyze new text for information novelty.

        Args:
            new_text: New text to analyze
            context: Existing knowledge/context to compare against
            threshold: Information gain threshold (default: 1.05 = 5% new info)

        Returns:
            SonarResult as dict
        """
        if not context:
            # No context = everything is new
            return SonarResult(
                information_gain=2.0,
                is_saturated=False,
                saturation_level="fresh",
                recommendation="Continue gathering information.",
            ).to_dict()

        # Calculate compression ratio
        context_compressed = len(zlib.compress(context.encode()))
        combined = context + new_text
        combined_compressed = len(zlib.compress(combined.encode()))

        # Avoid division by zero
        if context_compressed == 0:
            ratio = 2.0
        else:
            ratio = combined_compressed / context_compressed

        # Determine saturation
        is_saturated = ratio < threshold

        if is_saturated:
            self.saturation_counter += 1
        else:
            self.saturation_counter = 0

        # Determine saturation level
        if ratio >= 1.20:
            level = "highly_novel"
            recommendation = "Significant new information. Continue exploring this thread."
        elif ratio >= 1.10:
            level = "moderately_novel"
            recommendation = "Good information gain. Continue with current approach."
        elif ratio >= threshold:
            level = "marginally_novel"
            recommendation = "Some new information. Consider diversifying sources."
        elif self.saturation_counter >= self.max_consecutive_saturations:
            level = "critically_saturated"
            recommendation = (
                "SURFACE NOW: Critical saturation detected. "
                "You are likely reading redundant content or SEO spam. "
                "Pivot to a different source or reformulate your query."
            )
        else:
            level = "saturated"
            recommendation = (
                f"Low information gain ({self.saturation_counter}/"
                f"{self.max_consecutive_saturations} warnings). "
                "Consider pivoting to alternative sources."
            )

        logger.info(f"Sonar: gain={ratio:.4f}, level={level}")

        return SonarResult(
            information_gain=ratio,
            is_saturated=is_saturated,
            saturation_level=level,
            recommendation=recommendation,
        ).to_dict()

    def reset(self):
        """Reset saturation counter."""
        self.saturation_counter = 0
