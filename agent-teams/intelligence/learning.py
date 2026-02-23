"""
Learning Engine - Learn from User Corrections

Records user corrections and adjusts rule weights/confidence
based on feedback. Exports learned patterns for review.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib


@dataclass
class Correction:
    """A user correction to a system decision."""
    id: str
    correction_type: str  # strand_detection, column_mapping, classification, etc.
    original_decision: Any
    corrected_value: Any
    context: Dict[str, Any]  # What data led to the original decision
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False  # Whether this correction has been applied to rules

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.correction_type,
            "original": str(self.original_decision),
            "corrected": str(self.corrected_value),
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "applied": self.applied
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Correction':
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            correction_type=data.get('type', ''),
            original_decision=data.get('original'),
            corrected_value=data.get('corrected'),
            context=data.get('context', {}),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            applied=data.get('applied', False)
        )


@dataclass
class LearnedPattern:
    """A pattern learned from corrections."""
    pattern_id: str
    pattern_type: str
    condition: Dict[str, Any]  # When this pattern applies
    result: Any  # What result to produce
    confidence: float  # How confident we are (based on repetition)
    occurrence_count: int = 1
    last_seen: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.pattern_id,
            "type": self.pattern_type,
            "condition": self.condition,
            "result": str(self.result),
            "confidence": self.confidence,
            "occurrences": self.occurrence_count,
            "last_seen": self.last_seen.isoformat()
        }


class LearningEngine:
    """
    Learns from user corrections to improve future decisions.

    Features:
    - Records corrections with full context
    - Identifies patterns from repeated corrections
    - Adjusts confidence based on learning
    - Exports/imports learned patterns
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent / "memory"
        self.corrections: List[Correction] = []
        self.learned_patterns: Dict[str, LearnedPattern] = {}
        self.rule_weight_adjustments: Dict[str, float] = {}  # rule_id -> weight adjustment

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load_corrections()
        self._load_patterns()

    def _load_corrections(self):
        """Load corrections from storage."""
        corrections_file = self.storage_path / "corrections.json"
        if corrections_file.exists():
            try:
                with open(corrections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.corrections = [Correction.from_dict(c) for c in data.get('corrections', [])]
            except Exception as e:
                print(f"Error loading corrections: {e}")

    def _load_patterns(self):
        """Load learned patterns from storage."""
        patterns_file = self.storage_path / "learned_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for p in data.get('patterns', []):
                    pattern = LearnedPattern(
                        pattern_id=p.get('id', ''),
                        pattern_type=p.get('type', ''),
                        condition=p.get('condition', {}),
                        result=p.get('result'),
                        confidence=p.get('confidence', 0.5),
                        occurrence_count=p.get('occurrences', 1),
                        last_seen=datetime.fromisoformat(p.get('last_seen', datetime.now().isoformat()))
                    )
                    self.learned_patterns[pattern.pattern_id] = pattern
            except Exception as e:
                print(f"Error loading patterns: {e}")

    def _save_corrections(self):
        """Save corrections to storage."""
        corrections_file = self.storage_path / "corrections.json"
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "corrections": [c.to_dict() for c in self.corrections]
            }
            with open(corrections_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving corrections: {e}")

    def _save_patterns(self):
        """Save learned patterns to storage."""
        patterns_file = self.storage_path / "learned_patterns.json"
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "patterns": [p.to_dict() for p in self.learned_patterns.values()]
            }
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving patterns: {e}")

    def record_correction(
        self,
        correction_type: str,
        original_decision: Any,
        corrected_value: Any,
        context: Dict[str, Any]
    ) -> Correction:
        """
        Record a user correction.

        Args:
            correction_type: Type of correction (strand_detection, column_mapping, etc.)
            original_decision: What the system decided
            corrected_value: What the user corrected it to
            context: Context data that led to the decision

        Returns:
            The recorded correction
        """
        # Generate unique ID
        context_hash = hashlib.md5(
            json.dumps(context, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        correction_id = f"{correction_type}_{context_hash}_{len(self.corrections)}"

        correction = Correction(
            id=correction_id,
            correction_type=correction_type,
            original_decision=original_decision,
            corrected_value=corrected_value,
            context=context
        )

        self.corrections.append(correction)
        self._save_corrections()

        # Try to learn from this correction
        self._learn_from_correction(correction)

        return correction

    def _learn_from_correction(self, correction: Correction):
        """Attempt to learn a pattern from a correction."""
        # Create a pattern ID based on correction type and context
        context_keys = sorted(correction.context.keys())
        context_signature = "_".join(context_keys)
        pattern_id = f"{correction.correction_type}_{context_signature}"

        if pattern_id in self.learned_patterns:
            # Update existing pattern
            pattern = self.learned_patterns[pattern_id]

            # If same correction, increase confidence
            if str(pattern.result) == str(correction.corrected_value):
                pattern.occurrence_count += 1
                # Confidence increases with repetition, max 0.95
                pattern.confidence = min(0.95, 0.5 + (pattern.occurrence_count * 0.1))
            else:
                # Different correction - might need to reconsider
                pattern.confidence = max(0.3, pattern.confidence - 0.1)

            pattern.last_seen = datetime.now()
        else:
            # Create new pattern
            pattern = LearnedPattern(
                pattern_id=pattern_id,
                pattern_type=correction.correction_type,
                condition=correction.context,
                result=correction.corrected_value,
                confidence=0.6  # Initial confidence
            )
            self.learned_patterns[pattern_id] = pattern

        self._save_patterns()

    def get_learned_suggestion(
        self,
        decision_type: str,
        context: Dict[str, Any]
    ) -> Optional[tuple]:
        """
        Get a suggestion based on learned patterns.

        Args:
            decision_type: Type of decision being made
            context: Current context

        Returns:
            (suggested_value, confidence) or None if no pattern matches
        """
        best_match = None
        best_score = 0.0

        for pattern in self.learned_patterns.values():
            if pattern.pattern_type != decision_type:
                continue

            # Calculate match score based on context overlap
            match_score = self._calculate_context_match(pattern.condition, context)

            if match_score > best_score and match_score >= 0.5:
                best_score = match_score
                best_match = pattern

        if best_match:
            # Adjust confidence by match score
            adjusted_confidence = best_match.confidence * best_score
            return best_match.result, adjusted_confidence

        return None

    def _calculate_context_match(
        self,
        pattern_context: Dict[str, Any],
        current_context: Dict[str, Any]
    ) -> float:
        """Calculate how well a pattern context matches current context."""
        if not pattern_context:
            return 0.0

        matches = 0
        total = len(pattern_context)

        for key, value in pattern_context.items():
            if key in current_context:
                current_value = current_context[key]

                # Compare values
                if isinstance(value, list) and isinstance(current_value, list):
                    # List comparison - check overlap
                    overlap = len(set(value) & set(current_value))
                    if overlap > 0:
                        matches += overlap / max(len(value), len(current_value))
                elif str(value).lower() == str(current_value).lower():
                    matches += 1
                elif str(value).lower() in str(current_value).lower():
                    matches += 0.5

        return matches / total if total > 0 else 0.0

    def adjust_rule_weight(self, rule_id: str, adjustment: float):
        """
        Adjust a rule's weight based on feedback.

        Positive adjustment = rule performed well
        Negative adjustment = rule performed poorly
        """
        current = self.rule_weight_adjustments.get(rule_id, 0.0)
        # Keep adjustments bounded
        self.rule_weight_adjustments[rule_id] = max(-0.5, min(0.5, current + adjustment))

    def get_rule_weight_adjustment(self, rule_id: str) -> float:
        """Get the learned weight adjustment for a rule."""
        return self.rule_weight_adjustments.get(rule_id, 0.0)

    def get_corrections_by_type(self, correction_type: str) -> List[Correction]:
        """Get all corrections of a specific type."""
        return [c for c in self.corrections if c.correction_type == correction_type]

    def get_recent_corrections(self, limit: int = 10) -> List[Correction]:
        """Get most recent corrections."""
        sorted_corrections = sorted(
            self.corrections,
            key=lambda c: c.timestamp,
            reverse=True
        )
        return sorted_corrections[:limit]

    def export_learned_patterns(self) -> Dict:
        """Export all learned patterns for review."""
        return {
            "exported_at": datetime.now().isoformat(),
            "total_corrections": len(self.corrections),
            "patterns": [p.to_dict() for p in self.learned_patterns.values()],
            "rule_adjustments": self.rule_weight_adjustments,
            "corrections_summary": {
                ctype: len([c for c in self.corrections if c.correction_type == ctype])
                for ctype in set(c.correction_type for c in self.corrections)
            }
        }

    def clear_learning_data(self, keep_patterns: bool = False):
        """
        Clear learning data.

        Args:
            keep_patterns: If True, keep learned patterns but clear corrections
        """
        self.corrections = []
        self.rule_weight_adjustments = {}

        if not keep_patterns:
            self.learned_patterns = {}
            self._save_patterns()

        self._save_corrections()

    def get_learning_stats(self) -> Dict:
        """Get statistics about learning."""
        return {
            "total_corrections": len(self.corrections),
            "unique_patterns": len(self.learned_patterns),
            "corrections_by_type": {
                ctype: len([c for c in self.corrections if c.correction_type == ctype])
                for ctype in set(c.correction_type for c in self.corrections)
            },
            "high_confidence_patterns": len([
                p for p in self.learned_patterns.values()
                if p.confidence >= 0.8
            ]),
            "rule_adjustments": len(self.rule_weight_adjustments)
        }
