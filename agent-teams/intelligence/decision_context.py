"""
Decision Context - Contextual Awareness for Decisions

Provides context about the current record, history, and knowledge base
to inform intelligent decision-making.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import pandas as pd


class ContextType(Enum):
    """Types of context information."""
    CURRENT_RECORD = "current_record"
    COLUMN_CONTEXT = "column_context"
    HISTORICAL = "historical"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    USER_PREFERENCE = "user_preference"
    SESSION = "session"


@dataclass
class ColumnContext:
    """Context about a specific column."""
    name: str
    data_type: str
    sample_values: List[Any]
    unique_count: int
    null_count: int
    total_count: int
    patterns_detected: List[str] = field(default_factory=list)
    likely_semantic_type: Optional[str] = None

    @property
    def completeness(self) -> float:
        """Calculate completeness ratio."""
        return (self.total_count - self.null_count) / self.total_count if self.total_count > 0 else 0.0

    @property
    def uniqueness(self) -> float:
        """Calculate uniqueness ratio."""
        non_null = self.total_count - self.null_count
        return self.unique_count / non_null if non_null > 0 else 0.0


@dataclass
class DecisionContext:
    """
    Complete context for making an intelligent decision.

    Aggregates information from multiple sources to provide
    comprehensive context for the inference engine.
    """

    # Current record context
    current_record: Optional[Dict[str, Any]] = None
    record_index: int = 0

    # Column-level context
    column_contexts: Dict[str, ColumnContext] = field(default_factory=dict)

    # Data sample context
    sample_data: Optional[pd.DataFrame] = None
    all_columns: List[str] = field(default_factory=list)
    detected_patterns: Dict[str, List[str]] = field(default_factory=dict)

    # Historical context (what worked before)
    historical_decisions: List[Dict] = field(default_factory=list)
    historical_confidence: float = 0.5  # Default neutral

    # Domain knowledge context
    known_mappings: Dict[str, str] = field(default_factory=dict)
    known_values: Dict[str, Set[str]] = field(default_factory=dict)
    domain_rules: List[str] = field(default_factory=list)

    # User preference context
    user_corrections: List[Dict] = field(default_factory=list)
    preferred_defaults: Dict[str, Any] = field(default_factory=dict)

    # Session context
    session_id: str = ""
    processing_strand: Optional[str] = None
    processed_count: int = 0
    error_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, strand: Optional[str] = None) -> 'DecisionContext':
        """Create context from a DataFrame."""
        context = cls(
            sample_data=df.head(100) if len(df) > 100 else df.copy(),
            all_columns=list(df.columns),
            processing_strand=strand
        )

        # Build column contexts
        for col in df.columns:
            series = df[col]
            context.column_contexts[col] = ColumnContext(
                name=col,
                data_type=str(series.dtype),
                sample_values=series.dropna().head(10).tolist(),
                unique_count=series.nunique(),
                null_count=series.isna().sum(),
                total_count=len(series),
                patterns_detected=context._detect_patterns(series),
                likely_semantic_type=context._infer_semantic_type(col, series)
            )

        return context

    def _detect_patterns(self, series: pd.Series) -> List[str]:
        """Detect patterns in a series."""
        patterns = []
        sample = series.dropna().head(100).astype(str)

        if len(sample) == 0:
            return patterns

        # Check for numeric patterns
        numeric_count = sample.str.match(r'^-?\d+\.?\d*$').sum()
        if numeric_count > len(sample) * 0.9:
            patterns.append("numeric")

        # Check for date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO date
            r'\d{2}/\d{2}/\d{4}',  # UK date
            r'\d{2}-\d{2}-\d{4}',  # Date with dashes
        ]
        for pattern in date_patterns:
            if sample.str.match(pattern).sum() > len(sample) * 0.5:
                patterns.append("date")
                break

        # Check for code patterns
        if sample.str.match(r'^[A-Z]{2,4}\d{2,4}$').sum() > len(sample) * 0.5:
            patterns.append("code_format")

        # Check for combined format (CODE: Title)
        if sample.str.match(r'^[A-Z0-9]+:\s*.+').sum() > len(sample) * 0.3:
            patterns.append("combined_code_title")

        # Check for consistent length
        lengths = sample.str.len()
        if lengths.std() == 0 and len(sample) > 5:
            patterns.append(f"fixed_length_{int(lengths.iloc[0])}")

        return patterns

    def _infer_semantic_type(self, col_name: str, series: pd.Series) -> Optional[str]:
        """Infer semantic type from column name and data."""
        col_lower = col_name.lower()

        # Common semantic type indicators
        type_indicators = {
            'payroll': 'identifier',
            'employee': 'identifier',
            'staff': 'identifier',
            'id': 'identifier',
            'code': 'code',
            'finance': 'finance_code',
            'nominal': 'finance_code',
            'salary': 'currency',
            'amount': 'currency',
            'rate': 'currency',
            'fte': 'decimal',
            'percent': 'percentage',
            'date': 'date',
            'start': 'date',
            'end': 'date',
            'name': 'text',
            'title': 'text',
            'description': 'text',
            'school': 'reference',
            'department': 'reference',
            'scale': 'reference',
            'pension': 'reference',
            'email': 'email',
            'phone': 'phone',
        }

        for indicator, semantic_type in type_indicators.items():
            if indicator in col_lower:
                return semantic_type

        return None

    def add_historical_decision(
        self,
        decision_type: str,
        input_data: Dict,
        decision: Any,
        was_correct: bool,
        confidence: float
    ):
        """Add a historical decision for learning."""
        self.historical_decisions.append({
            "type": decision_type,
            "input": input_data,
            "decision": decision,
            "correct": was_correct,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })

        # Update historical confidence
        if self.historical_decisions:
            correct_count = sum(1 for d in self.historical_decisions if d["correct"])
            self.historical_confidence = correct_count / len(self.historical_decisions)

    def add_user_correction(
        self,
        original_decision: Any,
        corrected_value: Any,
        context_data: Dict
    ):
        """Record a user correction."""
        self.user_corrections.append({
            "original": original_decision,
            "corrected": corrected_value,
            "context": context_data,
            "timestamp": datetime.now().isoformat()
        })

    def get_column_context(self, column_name: str) -> Optional[ColumnContext]:
        """Get context for a specific column."""
        # Try exact match first
        if column_name in self.column_contexts:
            return self.column_contexts[column_name]

        # Try case-insensitive match
        col_lower = column_name.lower()
        for col, ctx in self.column_contexts.items():
            if col.lower() == col_lower:
                return ctx

        return None

    def has_pattern(self, column_name: str, pattern: str) -> bool:
        """Check if a column has a specific pattern."""
        ctx = self.get_column_context(column_name)
        return ctx is not None and pattern in ctx.patterns_detected

    def get_columns_with_pattern(self, pattern: str) -> List[str]:
        """Get all columns with a specific pattern."""
        return [
            col for col, ctx in self.column_contexts.items()
            if pattern in ctx.patterns_detected
        ]

    def get_columns_by_semantic_type(self, semantic_type: str) -> List[str]:
        """Get all columns with a specific semantic type."""
        return [
            col for col, ctx in self.column_contexts.items()
            if ctx.likely_semantic_type == semantic_type
        ]

    def to_dict(self) -> Dict:
        """Convert context to dictionary."""
        return {
            "columns": self.all_columns,
            "column_contexts": {
                k: {
                    "data_type": v.data_type,
                    "completeness": v.completeness,
                    "uniqueness": v.uniqueness,
                    "patterns": v.patterns_detected,
                    "semantic_type": v.likely_semantic_type
                }
                for k, v in self.column_contexts.items()
            },
            "strand": self.processing_strand,
            "historical_confidence": self.historical_confidence,
            "corrections_count": len(self.user_corrections),
            "processed_count": self.processed_count,
            "error_count": self.error_count
        }


class ContextBuilder:
    """
    Builder for creating DecisionContext incrementally.

    Useful when context needs to be built up over multiple steps.
    """

    def __init__(self):
        self.context = DecisionContext()

    def with_dataframe(self, df: pd.DataFrame) -> 'ContextBuilder':
        """Add DataFrame context."""
        base_context = DecisionContext.from_dataframe(df)
        self.context.sample_data = base_context.sample_data
        self.context.all_columns = base_context.all_columns
        self.context.column_contexts = base_context.column_contexts
        return self

    def with_strand(self, strand: str) -> 'ContextBuilder':
        """Set processing strand."""
        self.context.processing_strand = strand
        return self

    def with_known_mappings(self, mappings: Dict[str, str]) -> 'ContextBuilder':
        """Add known column mappings."""
        self.context.known_mappings.update(mappings)
        return self

    def with_known_values(self, field: str, values: Set[str]) -> 'ContextBuilder':
        """Add known valid values for a field."""
        self.context.known_values[field] = values
        return self

    def with_domain_rules(self, rules: List[str]) -> 'ContextBuilder':
        """Add domain rules."""
        self.context.domain_rules.extend(rules)
        return self

    def with_history(self, decisions: List[Dict]) -> 'ContextBuilder':
        """Add historical decisions."""
        self.context.historical_decisions = decisions
        if decisions:
            correct = sum(1 for d in decisions if d.get("correct", False))
            self.context.historical_confidence = correct / len(decisions)
        return self

    def with_user_preferences(self, defaults: Dict[str, Any]) -> 'ContextBuilder':
        """Add user preference defaults."""
        self.context.preferred_defaults.update(defaults)
        return self

    def with_session(self, session_id: str) -> 'ContextBuilder':
        """Set session ID."""
        self.context.session_id = session_id
        return self

    def build(self) -> DecisionContext:
        """Build and return the context."""
        return self.context
