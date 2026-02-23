"""
Confidence Scoring and Thresholds

Manages confidence levels for automated decisions.
Based on confidence, determines whether to auto-proceed, warn, or pause.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConfidenceLevel(Enum):
    """Confidence level classifications."""
    HIGH = "high"       # >90% - Auto-process silently
    MEDIUM = "medium"   # 70-90% - Auto-process with logged assumption
    LOW = "low"         # <70% - Auto-process with WARNING for post-review


@dataclass
class ConfidenceThresholds:
    """Configurable confidence thresholds."""
    high_threshold: float = 0.90
    medium_threshold: float = 0.70

    def classify(self, confidence: float) -> ConfidenceLevel:
        """Classify a confidence score into a level."""
        if confidence >= self.high_threshold:
            return ConfidenceLevel.HIGH
        elif confidence >= self.medium_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def requires_review(self, confidence: float) -> bool:
        """Check if confidence level requires review."""
        return confidence < self.medium_threshold


@dataclass
class ConfidenceAction:
    """Action to take based on confidence level."""
    proceed: bool
    log_assumption: bool
    add_warning: bool
    message: str


def get_action_for_confidence(
    confidence: float,
    thresholds: Optional[ConfidenceThresholds] = None
) -> ConfidenceAction:
    """
    Determine action based on confidence score.

    User preference: Auto-proceed with warnings (no blocking prompts),
    learn from corrections over time.

    Args:
        confidence: Score from 0.0 to 1.0
        thresholds: Custom thresholds (uses defaults if None)

    Returns:
        ConfidenceAction with proceed/logging guidance
    """
    if thresholds is None:
        thresholds = ConfidenceThresholds()

    level = thresholds.classify(confidence)

    if level == ConfidenceLevel.HIGH:
        return ConfidenceAction(
            proceed=True,
            log_assumption=False,
            add_warning=False,
            message=f"High confidence ({confidence:.0%}) - proceeding"
        )
    elif level == ConfidenceLevel.MEDIUM:
        return ConfidenceAction(
            proceed=True,
            log_assumption=True,
            add_warning=False,
            message=f"Medium confidence ({confidence:.0%}) - proceeding with logged assumption"
        )
    else:  # LOW
        return ConfidenceAction(
            proceed=True,
            log_assumption=True,
            add_warning=True,
            message=f"Low confidence ({confidence:.0%}) - proceeding with WARNING for post-review"
        )


def calculate_weighted_confidence(
    scores: dict[str, float],
    weights: Optional[dict[str, float]] = None
) -> float:
    """
    Calculate weighted average confidence from multiple sources.

    Args:
        scores: Dict of score_name -> confidence value (0-1)
        weights: Optional dict of score_name -> weight (default: equal weights)

    Returns:
        Weighted average confidence
    """
    if not scores:
        return 0.0

    if weights is None:
        weights = {k: 1.0 for k in scores.keys()}

    total_weight = sum(weights.get(k, 1.0) for k in scores.keys())
    weighted_sum = sum(
        scores[k] * weights.get(k, 1.0)
        for k in scores.keys()
    )

    return weighted_sum / total_weight if total_weight > 0 else 0.0


def combine_confidence_factors(
    primary: float,
    secondary: float,
    primary_weight: float = 0.7
) -> float:
    """
    Combine two confidence factors with weighting.

    Common use case: combining rule-based confidence with
    historical/learning-based confidence.

    Args:
        primary: Primary confidence score (e.g., from rules)
        secondary: Secondary confidence score (e.g., from history)
        primary_weight: Weight for primary (secondary gets 1 - primary_weight)

    Returns:
        Combined confidence score
    """
    return (primary * primary_weight) + (secondary * (1 - primary_weight))
