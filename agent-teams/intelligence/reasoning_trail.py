"""
Reasoning Trail - Full Audit Trail for Decisions

Tracks every step of the reasoning process with timestamps,
confidence scores, and justifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Dict
from enum import Enum
import json


class ReasoningStepType(Enum):
    """Types of reasoning steps."""
    RULE_MATCH = "rule_match"
    RULE_NO_MATCH = "rule_no_match"
    SCORE_CALCULATION = "score_calculation"
    THRESHOLD_CHECK = "threshold_check"
    DECISION = "decision"
    ASSUMPTION = "assumption"
    WARNING = "warning"
    FALLBACK = "fallback"
    LEARNING = "learning"


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    step_type: ReasoningStepType
    description: str
    confidence_delta: float = 0.0  # How much this step affected confidence
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "type": self.step_type.value,
            "description": self.description,
            "confidence_delta": self.confidence_delta,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

    def __str__(self) -> str:
        delta_str = ""
        if self.confidence_delta > 0:
            delta_str = f" (+{self.confidence_delta:.0%})"
        elif self.confidence_delta < 0:
            delta_str = f" ({self.confidence_delta:.0%})"
        return f"[{self.step_type.value}] {self.description}{delta_str}"


@dataclass
class ReasoningTrail:
    """
    Complete reasoning trail for a decision.

    Provides full audit capability by recording every step
    taken to reach a conclusion.
    """
    decision_id: str
    category: str  # e.g., "strand_detection", "column_mapping"
    steps: List[ReasoningStep] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    final_decision: Optional[Any] = None
    final_confidence: float = 0.0

    def add_step(
        self,
        step_type: ReasoningStepType,
        description: str,
        confidence_delta: float = 0.0,
        **details
    ) -> ReasoningStep:
        """Add a reasoning step to the trail."""
        step = ReasoningStep(
            step_type=step_type,
            description=description,
            confidence_delta=confidence_delta,
            details=details
        )
        self.steps.append(step)
        return step

    def add_rule_match(
        self,
        rule_id: str,
        rule_name: str,
        matched_value: Any,
        confidence_contribution: float
    ):
        """Record a rule match."""
        self.add_step(
            ReasoningStepType.RULE_MATCH,
            f"Matched rule '{rule_name}'",
            confidence_delta=confidence_contribution,
            rule_id=rule_id,
            matched_value=str(matched_value)
        )

    def add_rule_no_match(self, rule_id: str, rule_name: str, reason: str):
        """Record a rule that didn't match."""
        self.add_step(
            ReasoningStepType.RULE_NO_MATCH,
            f"Rule '{rule_name}' did not match: {reason}",
            rule_id=rule_id
        )

    def add_score_calculation(
        self,
        score_name: str,
        raw_score: float,
        normalized_score: float,
        method: str
    ):
        """Record a score calculation."""
        self.add_step(
            ReasoningStepType.SCORE_CALCULATION,
            f"Calculated {score_name}: {normalized_score:.2%}",
            score_name=score_name,
            raw_score=raw_score,
            normalized_score=normalized_score,
            method=method
        )

    def add_threshold_check(
        self,
        threshold_name: str,
        value: float,
        threshold: float,
        passed: bool
    ):
        """Record a threshold check."""
        result = "passed" if passed else "failed"
        self.add_step(
            ReasoningStepType.THRESHOLD_CHECK,
            f"Threshold check '{threshold_name}': {value:.2f} vs {threshold:.2f} ({result})",
            threshold_name=threshold_name,
            value=value,
            threshold=threshold,
            passed=passed
        )

    def add_decision(
        self,
        decision: Any,
        confidence: float,
        alternatives: Optional[List[Dict]] = None
    ):
        """Record the final decision."""
        self.final_decision = decision
        self.final_confidence = confidence
        self.end_time = datetime.now()

        self.add_step(
            ReasoningStepType.DECISION,
            f"Decision: {decision} (confidence: {confidence:.0%})",
            decision=str(decision),
            confidence=confidence,
            alternatives=alternatives or []
        )

    def add_assumption(
        self,
        assumption: str,
        reason: str,
        confidence: float
    ):
        """Record an assumption made during reasoning."""
        self.add_step(
            ReasoningStepType.ASSUMPTION,
            f"Assumption: {assumption}",
            confidence_delta=0,
            reason=reason,
            assumption_confidence=confidence
        )

    def add_warning(self, warning: str, severity: str = "medium"):
        """Record a warning."""
        self.add_step(
            ReasoningStepType.WARNING,
            f"WARNING: {warning}",
            severity=severity
        )

    def add_fallback(self, reason: str, fallback_value: Any):
        """Record when fallback logic was used."""
        self.add_step(
            ReasoningStepType.FALLBACK,
            f"Fallback used: {reason}",
            fallback_value=str(fallback_value)
        )

    def get_summary(self) -> str:
        """Get a human-readable summary of the reasoning."""
        lines = [
            f"=== Reasoning Trail: {self.category} ===",
            f"Decision ID: {self.decision_id}",
            f"Duration: {self._get_duration()}",
            f"Steps: {len(self.steps)}",
            "",
            "Reasoning steps:"
        ]

        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. {step}")

        if self.final_decision is not None:
            lines.extend([
                "",
                f"Final Decision: {self.final_decision}",
                f"Final Confidence: {self.final_confidence:.0%}"
            ])

        return "\n".join(lines)

    def _get_duration(self) -> str:
        """Get duration as string."""
        if self.end_time is None:
            return "in progress"
        delta = self.end_time - self.start_time
        ms = delta.total_seconds() * 1000
        return f"{ms:.0f}ms"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "decision_id": self.decision_id,
            "category": self.category,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [s.to_dict() for s in self.steps],
            "final_decision": str(self.final_decision) if self.final_decision else None,
            "final_confidence": self.final_confidence
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_warnings(self) -> List[ReasoningStep]:
        """Get all warning steps."""
        return [s for s in self.steps if s.step_type == ReasoningStepType.WARNING]

    def get_assumptions(self) -> List[ReasoningStep]:
        """Get all assumption steps."""
        return [s for s in self.steps if s.step_type == ReasoningStepType.ASSUMPTION]

    def get_rule_matches(self) -> List[ReasoningStep]:
        """Get all rule match steps."""
        return [s for s in self.steps if s.step_type == ReasoningStepType.RULE_MATCH]


class ReasoningTrailManager:
    """
    Manages multiple reasoning trails for a session.

    Provides centralized storage and retrieval of all
    reasoning trails generated during processing.
    """

    def __init__(self):
        self.trails: Dict[str, ReasoningTrail] = {}
        self._id_counter = 0

    def create_trail(self, category: str) -> ReasoningTrail:
        """Create a new reasoning trail."""
        self._id_counter += 1
        decision_id = f"{category}_{self._id_counter}"
        trail = ReasoningTrail(decision_id=decision_id, category=category)
        self.trails[decision_id] = trail
        return trail

    def get_trail(self, decision_id: str) -> Optional[ReasoningTrail]:
        """Get a trail by ID."""
        return self.trails.get(decision_id)

    def get_trails_by_category(self, category: str) -> List[ReasoningTrail]:
        """Get all trails for a category."""
        return [t for t in self.trails.values() if t.category == category]

    def get_all_warnings(self) -> List[Dict]:
        """Get all warnings from all trails."""
        warnings = []
        for trail in self.trails.values():
            for warning in trail.get_warnings():
                warnings.append({
                    "decision_id": trail.decision_id,
                    "category": trail.category,
                    "warning": warning.description,
                    "severity": warning.details.get("severity", "medium")
                })
        return warnings

    def get_all_assumptions(self) -> List[Dict]:
        """Get all assumptions from all trails."""
        assumptions = []
        for trail in self.trails.values():
            for assumption in trail.get_assumptions():
                assumptions.append({
                    "decision_id": trail.decision_id,
                    "category": trail.category,
                    "assumption": assumption.description,
                    "reason": assumption.details.get("reason", ""),
                    "confidence": assumption.details.get("assumption_confidence", 0)
                })
        return assumptions

    def export_all(self) -> Dict:
        """Export all trails for audit."""
        return {
            "exported_at": datetime.now().isoformat(),
            "total_decisions": len(self.trails),
            "trails": {k: v.to_dict() for k, v in self.trails.items()}
        }
