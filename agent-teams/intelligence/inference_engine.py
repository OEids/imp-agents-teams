"""
Inference Engine - Central Reasoning with Confidence Scoring

The main intelligence component that combines rules, context, learning,
and reasoning to make confident decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import uuid

from .confidence import (
    ConfidenceLevel, ConfidenceThresholds, ConfidenceAction,
    get_action_for_confidence, combine_confidence_factors
)
from .reasoning_trail import ReasoningTrail, ReasoningTrailManager, ReasoningStepType
from .decision_context import DecisionContext, ContextBuilder
from .rule_registry import RuleRegistry, Rule
from .schema_registry import SchemaRegistry, StrandSchema
from .learning import LearningEngine


@dataclass
class InferenceResult:
    """Result of an inference operation."""
    decision: Any  # The actual decision
    confidence: float  # 0.0 - 1.0
    confidence_level: ConfidenceLevel
    reasoning: List[str]  # Step-by-step explanation (human readable)
    alternatives: List[Dict]  # Other options considered
    requires_review: bool  # Should human review?
    action: ConfidenceAction  # What action to take
    reasoning_trail: Optional[ReasoningTrail] = None  # Full audit trail

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "decision": str(self.decision),
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives,
            "requires_review": self.requires_review,
            "action_message": self.action.message
        }


class InferenceEngine:
    """
    Central reasoning engine for intelligent decision-making.

    Combines:
    - YAML-configurable rules (RuleRegistry)
    - Dynamic schemas (SchemaRegistry)
    - Learning from corrections (LearningEngine)
    - Full reasoning trails for audit
    - Confidence-based action decisions
    """

    def __init__(
        self,
        rules_dir: Optional[Path] = None,
        schemas_dir: Optional[Path] = None,
        learning_dir: Optional[Path] = None,
        thresholds: Optional[ConfidenceThresholds] = None,
        hot_reload: bool = False
    ):
        # Initialize components
        base_dir = Path(__file__).parent.parent / "config"

        self.rule_registry = RuleRegistry(
            rules_dir=rules_dir or base_dir / "rules",
            hot_reload=hot_reload
        )
        self.schema_registry = SchemaRegistry(
            schemas_dir=schemas_dir or base_dir / "schemas"
        )
        self.learning_engine = LearningEngine(
            storage_path=learning_dir or Path(__file__).parent.parent / "memory"
        )
        self.thresholds = thresholds or ConfidenceThresholds()
        self.trail_manager = ReasoningTrailManager()

        # Fallback handlers for when rules don't match
        self.fallback_handlers: Dict[str, Callable] = {}

    def infer_strand(
        self,
        columns: List[str],
        sample_data: Optional[Any] = None,
        context: Optional[DecisionContext] = None
    ) -> InferenceResult:
        """
        Infer which strand (S1, S2, S3) data belongs to.

        Replaces hardcoded detect_strand() logic.

        Args:
            columns: List of column names
            sample_data: Optional sample data for deeper analysis
            context: Optional decision context

        Returns:
            InferenceResult with strand decision and confidence
        """
        trail = self.trail_manager.create_trail("strand_detection")

        # Prepare data for rule evaluation
        columns_lower = [c.lower() for c in columns]
        columns_str = " ".join(columns_lower)

        # Track scores for each strand
        strand_scores: Dict[str, float] = {}
        strand_matches: Dict[str, List[str]] = {}

        # 1. Evaluate strand detection rules
        trail.add_step(
            ReasoningStepType.SCORE_CALCULATION,
            "Evaluating strand detection rules",
            rule_count=len(self.rule_registry.get_rules_by_category("strand_detection"))
        )

        rule_results = self.rule_registry.evaluate_rules(
            "strand_detection",
            columns_str,
            {"columns": columns, "columns_lower": columns_lower}
        )

        for rule, matched in rule_results:
            strand = rule.metadata.get("subcategory", rule.result)
            if strand:
                if matched:
                    strand_scores[strand] = strand_scores.get(strand, 0) + rule.weight
                    strand_matches.setdefault(strand, []).append(rule.name)
                    trail.add_rule_match(
                        rule.id, rule.name,
                        strand, rule.weight / 10  # Normalize contribution
                    )
                else:
                    trail.add_rule_no_match(rule.id, rule.name, "Condition not met")

        # 2. Use schema registry indicators as fallback
        if not strand_scores:
            trail.add_step(
                ReasoningStepType.FALLBACK,
                "No rule matches, using schema indicators"
            )
            schema_matches = self.schema_registry.detect_strand_by_indicators(columns)
            for strand_id, score, indicators in schema_matches:
                strand_scores[strand_id] = score
                strand_matches[strand_id] = indicators
                trail.add_step(
                    ReasoningStepType.SCORE_CALCULATION,
                    f"Schema indicator match for {strand_id}",
                    confidence_delta=score / 10,
                    indicators=indicators
                )

        # 3. Check learning engine for suggestions
        if context:
            learned = self.learning_engine.get_learned_suggestion(
                "strand_detection",
                {"columns": columns_lower}
            )
            if learned:
                learned_strand, learned_confidence = learned
                trail.add_step(
                    ReasoningStepType.LEARNING,
                    f"Learned suggestion: {learned_strand} ({learned_confidence:.0%})",
                    confidence_delta=learned_confidence * 0.2
                )
                # Boost learned strand's score
                strand_scores[learned_strand] = strand_scores.get(learned_strand, 0) + (learned_confidence * 2)

        # 4. Calculate final confidence
        if not strand_scores:
            # No matches at all
            trail.add_warning("No strand indicators found", severity="high")
            trail.add_decision(None, 0.0, [])

            return InferenceResult(
                decision=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                reasoning=["No strand indicators found in column names"],
                alternatives=[],
                requires_review=True,
                action=get_action_for_confidence(0.0, self.thresholds),
                reasoning_trail=trail
            )

        # Find best strand
        best_strand = max(strand_scores, key=strand_scores.get)
        best_score = strand_scores[best_strand]

        # Calculate confidence based on score dominance
        total_score = sum(strand_scores.values())
        confidence = best_score / total_score if total_score > 0 else 0

        # Adjust confidence based on match count
        match_count = len(strand_matches.get(best_strand, []))
        if match_count >= 3:
            confidence = min(1.0, confidence * 1.2)
        elif match_count == 1:
            confidence *= 0.8

        # Build alternatives
        alternatives = [
            {
                "strand": strand,
                "score": score,
                "confidence": score / total_score if total_score > 0 else 0,
                "matches": strand_matches.get(strand, [])
            }
            for strand, score in strand_scores.items()
            if strand != best_strand
        ]
        alternatives.sort(key=lambda x: -x["score"])

        # Build reasoning
        reasoning = [
            f"Detected strand: {best_strand}",
            f"Matched {match_count} indicators: {', '.join(strand_matches.get(best_strand, [])[:5])}",
            f"Score: {best_score:.1f} out of {total_score:.1f} total"
        ]

        if alternatives:
            alt = alternatives[0]
            reasoning.append(f"Next best: {alt['strand']} ({alt['confidence']:.0%})")

        # Finalize
        confidence_level = self.thresholds.classify(confidence)
        action = get_action_for_confidence(confidence, self.thresholds)

        trail.add_decision(best_strand, confidence, alternatives)

        return InferenceResult(
            decision=best_strand,
            confidence=confidence,
            confidence_level=confidence_level,
            reasoning=reasoning,
            alternatives=alternatives,
            requires_review=action.add_warning,
            action=action,
            reasoning_trail=trail
        )

    def infer_column_mapping(
        self,
        source_column: str,
        strand: str,
        context: Optional[DecisionContext] = None,
        candidate_columns: Optional[List[str]] = None
    ) -> InferenceResult:
        """
        Infer the standard column name for a source column.

        Replaces hardcoded column alias dictionaries.
        Uses tiered matching: exact -> variation -> fuzzy -> unmapped.

        Args:
            source_column: Original column name
            strand: Target strand (S1, S2, S3)
            context: Optional decision context
            candidate_columns: Optional list of candidate standard columns for fuzzy matching

        Returns:
            InferenceResult with mapped column name
        """
        trail = self.trail_manager.create_trail("column_mapping")
        col_lower = source_column.lower().strip()

        # =====================================================================
        # Step 1: Check schema registry first (exact match - confidence 1.0)
        # =====================================================================
        schema_match = self.schema_registry.find_column_in_strand(source_column, strand)
        if schema_match:
            trail.add_step(
                ReasoningStepType.RULE_MATCH,
                f"Schema exact match: {schema_match.standard_name}",
                confidence_delta=1.0
            )
            trail.add_decision(schema_match.standard_name, 1.0, [])

            return InferenceResult(
                decision=schema_match.standard_name,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                reasoning=[f"Exact match in schema: {source_column} -> {schema_match.standard_name}"],
                alternatives=[],
                requires_review=False,
                action=get_action_for_confidence(1.0, self.thresholds),
                reasoning_trail=trail
            )

        # =====================================================================
        # Step 2: Evaluate column mapping rules (variation match - confidence 0.95)
        # =====================================================================
        rule_results = self.rule_registry.evaluate_rules(
            "column_mapping",
            col_lower,
            {"column": source_column, "strand": strand}
        )

        matched_rules = [(r, m) for r, m in rule_results if m]

        if matched_rules:
            # Use highest weight match
            best_rule = max(matched_rules, key=lambda x: x[0].weight)[0]
            confidence = min(0.95, 0.7 + (best_rule.weight * 0.1))

            trail.add_rule_match(
                best_rule.id, best_rule.name,
                best_rule.result, confidence
            )
            trail.add_decision(best_rule.result, confidence, [])

            return InferenceResult(
                decision=best_rule.result,
                confidence=confidence,
                confidence_level=self.thresholds.classify(confidence),
                reasoning=[f"Variation match via rule: {best_rule.name}", f"Maps '{source_column}' to '{best_rule.result}'"],
                alternatives=[
                    {"column": r.result, "rule": r.name}
                    for r, _ in matched_rules[1:4]
                ],
                requires_review=confidence < self.thresholds.medium_threshold,
                action=get_action_for_confidence(confidence, self.thresholds),
                reasoning_trail=trail
            )

        # =====================================================================
        # Step 3: Try fuzzy matching (confidence 0.7-0.9)
        # =====================================================================
        fuzzy_result = self._try_fuzzy_column_match(
            source_column, strand, candidate_columns, trail
        )
        if fuzzy_result:
            return fuzzy_result

        # =====================================================================
        # Step 4: Check learning engine
        # =====================================================================
        learned = self.learning_engine.get_learned_suggestion(
            "column_mapping",
            {"source": col_lower, "strand": strand}
        )

        if learned:
            learned_mapping, learned_confidence = learned
            trail.add_step(
                ReasoningStepType.LEARNING,
                f"Learned mapping: {learned_mapping} ({learned_confidence:.0%})"
            )
            trail.add_decision(learned_mapping, learned_confidence, [])

            return InferenceResult(
                decision=learned_mapping,
                confidence=learned_confidence,
                confidence_level=self.thresholds.classify(learned_confidence),
                reasoning=[f"Learned from previous corrections: {source_column} -> {learned_mapping}"],
                alternatives=[],
                requires_review=learned_confidence < self.thresholds.medium_threshold,
                action=get_action_for_confidence(learned_confidence, self.thresholds),
                reasoning_trail=trail
            )

        # =====================================================================
        # Step 5: Smart pattern inference based on domain knowledge
        # =====================================================================
        smart_result = self._smart_column_inference(source_column, strand, trail)
        if smart_result:
            return smart_result

        # =====================================================================
        # Step 6: No match - return original with low confidence and suggestions
        # =====================================================================
        trail.add_warning(f"No mapping found for '{source_column}'", severity="medium")
        trail.add_fallback("No rules matched", source_column)

        # Get fuzzy suggestions even if below threshold
        suggestions = self._get_fuzzy_suggestions(source_column, strand, candidate_columns)

        trail.add_decision(source_column, 0.3, suggestions)

        return InferenceResult(
            decision=source_column,  # Keep original
            confidence=0.3,
            confidence_level=ConfidenceLevel.LOW,
            reasoning=[
                f"No mapping found for '{source_column}'",
                "Keeping original column name",
                f"Possible matches: {', '.join([s['column'] for s in suggestions[:3]])}" if suggestions else "No suggestions"
            ],
            alternatives=suggestions[:5],
            requires_review=True,
            action=get_action_for_confidence(0.3, self.thresholds),
            reasoning_trail=trail
        )

    def _try_fuzzy_column_match(
        self,
        source_column: str,
        strand: str,
        candidate_columns: Optional[List[str]],
        trail
    ) -> Optional[InferenceResult]:
        """
        Try fuzzy matching for column names.

        Returns InferenceResult if fuzzy match found with confidence >= 0.7.
        """
        try:
            from .fuzzy_matcher import get_default_fuzzy_matcher
            from .config_loader import get_config_loader

            matcher = get_default_fuzzy_matcher()

            # Load abbreviations from config
            try:
                config = get_config_loader()
                abbreviations = config.get_abbreviations()
                if abbreviations:
                    matcher.set_abbreviations(abbreviations)
            except Exception:
                pass  # Use default abbreviations

            # Get candidate columns from schema if not provided
            if not candidate_columns:
                candidate_columns = self._get_schema_columns(strand)

            if not candidate_columns:
                return None

            # Find best fuzzy match
            matches = matcher.find_all_matches(
                source_column,
                candidate_columns,
                threshold=0.7,
                max_results=5
            )

            if matches and matches[0].score >= 0.7:
                best_match = matches[0]
                confidence = min(0.9, best_match.score)  # Cap at 0.9 for fuzzy

                trail.add_step(
                    ReasoningStepType.SCORE_CALCULATION,
                    f"Fuzzy match: {best_match.target} (score: {best_match.score:.2f})",
                    confidence_delta=confidence
                )

                alternatives = [
                    {"column": m.target, "score": m.score, "type": m.match_type}
                    for m in matches[1:5]
                ]

                trail.add_decision(best_match.target, confidence, alternatives)

                return InferenceResult(
                    decision=best_match.target,
                    confidence=confidence,
                    confidence_level=self.thresholds.classify(confidence),
                    reasoning=[
                        f"Fuzzy match: '{source_column}' -> '{best_match.target}'",
                        f"Match score: {best_match.score:.0%}",
                        f"Match type: {best_match.match_type}"
                    ],
                    alternatives=alternatives,
                    requires_review=confidence < self.thresholds.high_threshold,
                    action=get_action_for_confidence(confidence, self.thresholds),
                    reasoning_trail=trail
                )

        except ImportError:
            # Fuzzy matcher not available
            trail.add_step(
                ReasoningStepType.FALLBACK,
                "Fuzzy matcher not available"
            )

        return None

    def _get_fuzzy_suggestions(
        self,
        source_column: str,
        strand: str,
        candidate_columns: Optional[List[str]]
    ) -> List[Dict]:
        """Get fuzzy match suggestions even below threshold."""
        try:
            from .fuzzy_matcher import get_default_fuzzy_matcher

            matcher = get_default_fuzzy_matcher()

            if not candidate_columns:
                candidate_columns = self._get_schema_columns(strand)

            if not candidate_columns:
                return []

            matches = matcher.find_all_matches(
                source_column,
                candidate_columns,
                threshold=0.4,  # Lower threshold for suggestions
                max_results=5
            )

            return [
                {"column": m.target, "score": m.score, "type": m.match_type}
                for m in matches
            ]

        except ImportError:
            return []

    def _get_schema_columns(self, strand: str) -> List[str]:
        """Get all standard column names from schema for a strand."""
        columns = []
        try:
            schema = self.schema_registry.get_strand_schema(strand)
            if schema and hasattr(schema, 'data_types'):
                for data_type in schema.data_types:
                    if hasattr(data_type, 'columns'):
                        for col in data_type.columns:
                            if hasattr(col, 'standard_name'):
                                columns.append(col.standard_name)
                            if hasattr(col, 'variations'):
                                columns.extend(col.variations)
        except Exception:
            pass
        return list(set(columns))

    # =========================================================================
    # SMART INFERENCE PATTERNS - Domain knowledge for automatic decisions
    # =========================================================================

    # Column name patterns -> standard column mappings
    SMART_COLUMN_PATTERNS = {
        # Name fields
        'surname': ['surname', 'last_name', 'lastname', 'family', 'familyname', 'lname'],
        'forename': ['forename', 'first_name', 'firstname', 'given', 'givenname', 'fname'],
        'name': ['name', 'full_name', 'fullname', 'staff_name', 'employee_name'],

        # Identifier fields
        'payroll_number': ['payroll', 'emp_no', 'employee_number', 'employee_id', 'staff_id',
                          'personnel', 'pr_no', 'empno', 'empid', 'staff_no', 'unique_id'],

        # Job/Role fields
        'job_title': ['job_title', 'jobtitle', 'position', 'role', 'post', 'job', 'title',
                     'designation', 'occupation', 'staff_role'],

        # Pay fields
        'pay_scale': ['pay_scale', 'payscale', 'scale', 'pay_grade', 'grade', 'salary_scale',
                     'scale_type', 'pay_type', 'pay_scale_type'],
        'scale_point': ['scale_point', 'scp', 'spine_point', 'point', 'pay_point',
                       'spinal_point', 'current_point', 'grade_point'],
        'salary': ['salary', 'annual_salary', 'gross_salary', 'basic_salary', 'pay',
                  'annual_pay', 'wage', 'earnings'],
        'spot_salary': ['spot_salary', 'spot', 'spot_scale', 'spot_amount', 'spot_pay',
                       'fixed_salary', 'fixed_amount'],

        # Hours/FTE fields
        'weekly_hours': ['hours', 'weekly_hours', 'hours_per_week', 'hpw', 'contracted_hours',
                        'work_hours', 'hrs', 'ft_hours'],
        'fte': ['fte', 'full_time_equivalent', 'weekly_fte', 'ft_equivalent'],

        # Date fields
        'start_date': ['start_date', 'service_start', 'join_date', 'hire_date', 'commence',
                      'commencement', 'date_joined', 'employed_from'],
        'dob': ['dob', 'date_of_birth', 'birth_date', 'birthdate', 'birthday'],

        # School/Location fields
        'school_code': ['school', 'school_code', 'site', 'establishment', 'location',
                       'academy', 'cost_centre', 'cost_center', 'cc'],
        'department': ['department', 'dept', 'department_code', 'section', 'team'],

        # Other common fields
        'pension': ['pension', 'pension_code', 'pension_scheme', 'pens', 'superannuation'],
        'gender': ['gender', 'sex', 'gender_code'],
        'ni_number': ['ni', 'ni_number', 'national_insurance', 'nino', 'ni_no'],
        'contract_type': ['contract_type', 'employment_type', 'contract_status', 'type'],
        'reference': ['reference', 'ref', 'contract_ref', 'contract_no', 'contract_id'],
    }

    def _smart_column_inference(
        self,
        source_column: str,
        strand: str,
        trail
    ) -> Optional[InferenceResult]:
        """
        Smart column inference using domain knowledge patterns.

        Makes automatic decisions based on:
        1. Pattern matching against known column name variations
        2. Keyword extraction from column names
        3. Abbreviation expansion

        This avoids asking the user when a confident match can be made.
        """
        col_lower = source_column.lower().strip()
        # Split into words for word-based matching
        col_words = col_lower.replace('_', ' ').replace('-', ' ').split()
        # Normalize: remove special chars for pattern matching
        col_normalized = ''.join(c if c.isalnum() else '' for c in col_lower)

        best_match = None
        best_confidence = 0.0
        match_reason = ""

        # PASS 1: Exact word match - highest confidence
        # Look for exact matches of key words in the column name
        for standard_col, patterns in self.SMART_COLUMN_PATTERNS.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                # Check if pattern is an exact word in column name
                if pattern_lower in col_words:
                    # Longer pattern = more specific = higher confidence
                    score = min(0.95, 0.85 + len(pattern_lower) * 0.01)
                    if score > best_confidence:
                        best_match = standard_col
                        best_confidence = score
                        match_reason = f"Exact word match '{pattern}': '{source_column}' -> '{standard_col}'"

        # PASS 2: Normalized exact match
        if best_confidence < 0.95:
            for standard_col, patterns in self.SMART_COLUMN_PATTERNS.items():
                for pattern in patterns:
                    pattern_normalized = ''.join(c if c.isalnum() else '' for c in pattern.lower())
                    if col_normalized == pattern_normalized:
                        if 0.95 > best_confidence:
                            best_match = standard_col
                            best_confidence = 0.95
                            match_reason = f"Normalized exact match: '{source_column}' -> '{standard_col}'"

        # PASS 3: Full pattern contained in column (minimum 4 chars to avoid false matches)
        if best_confidence < 0.85:
            for standard_col, patterns in self.SMART_COLUMN_PATTERNS.items():
                for pattern in patterns:
                    if len(pattern) >= 4:  # Only match patterns with 4+ chars
                        pattern_normalized = ''.join(c if c.isalnum() else '' for c in pattern.lower())
                        if pattern_normalized in col_normalized:
                            # Longer pattern = better match
                            score = min(0.85, 0.7 + len(pattern_normalized) * 0.02)
                            if score > best_confidence:
                                best_match = standard_col
                                best_confidence = score
                                match_reason = f"Contains pattern '{pattern}': '{source_column}' -> '{standard_col}'"

        # PASS 4: Word-based partial match for compound names
        if best_confidence < 0.75:
            for standard_col, patterns in self.SMART_COLUMN_PATTERNS.items():
                for word in col_words:
                    if len(word) >= 4:  # Only match words with 4+ chars
                        for pattern in patterns:
                            pattern_lower = pattern.lower()
                            # Word matches pattern or is substring of pattern
                            if word == pattern_lower or (len(pattern_lower) >= 4 and word in pattern_lower):
                                score = 0.75
                                if score > best_confidence:
                                    best_match = standard_col
                                    best_confidence = score
                                    match_reason = f"Word match '{word}' -> '{standard_col}'"
                                break

        if best_match and best_confidence >= 0.65:
            trail.add_step(
                ReasoningStepType.SCORE_CALCULATION,
                f"Smart pattern match: {match_reason}",
                confidence_delta=best_confidence
            )
            trail.add_decision(best_match, best_confidence, [])

            return InferenceResult(
                decision=best_match,
                confidence=best_confidence,
                confidence_level=self.thresholds.classify(best_confidence),
                reasoning=[
                    "Smart inference using domain knowledge",
                    match_reason
                ],
                alternatives=[],
                requires_review=best_confidence < 0.8,  # Only review if below 0.8
                action=get_action_for_confidence(best_confidence, self.thresholds),
                reasoning_trail=trail
            )

        return None

    def infer_column_from_data(
        self,
        column_name: str,
        sample_values: list,
        strand: str = "S2"
    ) -> Optional[InferenceResult]:
        """
        Infer column type by analyzing sample data values.

        Uses pattern recognition on actual data to make smart decisions:
        - Date patterns -> date fields
        - Currency/large numbers -> salary fields
        - Pension codes (TPS, LGPS) -> pension
        - Gender codes (M, F) -> gender
        - Scale points (1-50) -> scale_point
        - Pay scale codes -> pay_scale

        Args:
            column_name: Original column name
            sample_values: List of sample values from the column
            strand: Target strand

        Returns:
            InferenceResult if confident match found
        """
        if not sample_values:
            return None

        trail = self.trail_manager.create_trail("content_inference")

        # Clean sample values
        clean_values = []
        for v in sample_values[:20]:  # Sample first 20
            if v is not None and str(v).strip().lower() not in ['', 'nan', 'none']:
                clean_values.append(str(v).strip())

        if not clean_values:
            return None

        # Analyze patterns in data
        inferred_type = None
        confidence = 0.0
        reason = ""

        # Check for pension codes
        pension_patterns = {'tps', 'lgps', 'teachers', 'local government', 'nhs', 'civil service'}
        pension_matches = sum(1 for v in clean_values if v.lower() in pension_patterns or
                             any(p in v.lower() for p in pension_patterns))
        if pension_matches / len(clean_values) > 0.5:
            inferred_type = 'pension'
            confidence = 0.9
            reason = f"Data contains pension codes (TPS, LGPS, etc.)"

        # Check for gender codes
        gender_patterns = {'m', 'f', 'male', 'female', 'man', 'woman'}
        gender_matches = sum(1 for v in clean_values if v.lower() in gender_patterns)
        if gender_matches / len(clean_values) > 0.5:
            inferred_type = 'gender'
            confidence = 0.9
            reason = f"Data contains gender codes (M, F)"

        # Check for pay scale codes
        payscale_patterns = {'mps', 'ups', 'tms', 'leadership', 'njc', 'support', 'teaching'}
        payscale_matches = sum(1 for v in clean_values if
                               any(p in v.lower() for p in payscale_patterns))
        if payscale_matches / len(clean_values) > 0.3:
            inferred_type = 'pay_scale'
            confidence = 0.85
            reason = f"Data contains pay scale codes"

        # Check for scale points (small integers 1-50)
        try:
            numeric_vals = [int(float(v)) for v in clean_values if v.replace('.', '').isdigit()]
            if numeric_vals and all(1 <= n <= 50 for n in numeric_vals):
                if len(numeric_vals) / len(clean_values) > 0.7:
                    inferred_type = 'scale_point'
                    confidence = 0.8
                    reason = f"Data contains scale point numbers (1-50)"
        except (ValueError, TypeError):
            pass

        # Check for salary amounts (large numbers)
        try:
            numeric_vals = [float(v.replace(',', '').replace('£', '')) for v in clean_values
                          if v.replace(',', '').replace('£', '').replace('.', '').isdigit()]
            if numeric_vals and all(10000 <= n <= 200000 for n in numeric_vals):
                if len(numeric_vals) / len(clean_values) > 0.5:
                    inferred_type = 'salary'
                    confidence = 0.85
                    reason = f"Data contains salary amounts (£10k-£200k)"
        except (ValueError, TypeError):
            pass

        # Check for date patterns
        import re
        date_pattern = re.compile(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}')
        date_matches = sum(1 for v in clean_values if date_pattern.match(v))
        if date_matches / len(clean_values) > 0.5:
            # Try to determine which date field
            col_lower = column_name.lower()
            if 'birth' in col_lower or 'dob' in col_lower:
                inferred_type = 'dob'
            elif 'start' in col_lower or 'join' in col_lower or 'commence' in col_lower:
                inferred_type = 'start_date'
            else:
                inferred_type = 'start_date'  # Default to start_date for dates
            confidence = 0.85
            reason = f"Data contains date values"

        # Check for school/location codes (short alphanumeric)
        if not inferred_type:
            short_codes = [v for v in clean_values if len(v) <= 10 and v.isalnum()]
            if len(short_codes) / len(clean_values) > 0.7:
                col_lower = column_name.lower()
                if 'school' in col_lower or 'site' in col_lower or 'location' in col_lower:
                    inferred_type = 'school_code'
                    confidence = 0.8
                    reason = f"Data contains location/school codes"

        if inferred_type and confidence >= 0.7:
            trail.add_step(
                ReasoningStepType.SCORE_CALCULATION,
                f"Content analysis: {reason}",
                confidence_delta=confidence
            )
            trail.add_decision(inferred_type, confidence, [])

            return InferenceResult(
                decision=inferred_type,
                confidence=confidence,
                confidence_level=self.thresholds.classify(confidence),
                reasoning=[
                    "Inferred from data content analysis",
                    reason,
                    f"Based on {len(clean_values)} sample values"
                ],
                alternatives=[],
                requires_review=confidence < 0.85,
                action=get_action_for_confidence(confidence, self.thresholds),
                reasoning_trail=trail
            )

        return None

    def infer_classification(
        self,
        value: Any,
        classification_type: str,
        context: Optional[DecisionContext] = None
    ) -> InferenceResult:
        """
        Infer a classification (e.g., teaching/support role).

        Replaces hardcoded is_teaching_role(), is_support_role(), etc.

        Args:
            value: Value to classify
            classification_type: Type of classification (role_type, pension_scheme, etc.)
            context: Optional decision context

        Returns:
            InferenceResult with classification
        """
        trail = self.trail_manager.create_trail(f"classification_{classification_type}")
        value_str = str(value).lower() if value else ""

        # Evaluate classification rules
        category = f"classification_{classification_type}"
        rule_results = self.rule_registry.evaluate_rules(
            category,
            value_str,
            {"value": value, "type": classification_type}
        )

        matched_rules = [(r, m) for r, m in rule_results if m]

        if matched_rules:
            # Sort by weight and use best match
            matched_rules.sort(key=lambda x: -x[0].weight)
            best_rule = matched_rules[0][0]

            # Calculate confidence based on match quality
            confidence = min(0.95, 0.7 + (best_rule.weight * 0.1) + (best_rule.confidence_boost))

            trail.add_rule_match(
                best_rule.id, best_rule.name,
                best_rule.result, confidence
            )

            # Build alternatives from other matches
            alternatives = [
                {"classification": r.result, "rule": r.name, "weight": r.weight}
                for r, _ in matched_rules[1:4]
            ]

            trail.add_decision(best_rule.result, confidence, alternatives)

            return InferenceResult(
                decision=best_rule.result,
                confidence=confidence,
                confidence_level=self.thresholds.classify(confidence),
                reasoning=[
                    f"Classified as: {best_rule.result}",
                    f"Matched rule: {best_rule.name}",
                    f"Based on value: '{value}'"
                ],
                alternatives=alternatives,
                requires_review=confidence < self.thresholds.medium_threshold,
                action=get_action_for_confidence(confidence, self.thresholds),
                reasoning_trail=trail
            )

        # No rule match - try learning
        learned = self.learning_engine.get_learned_suggestion(
            f"classification_{classification_type}",
            {"value": value_str}
        )

        if learned:
            learned_class, learned_conf = learned
            trail.add_step(
                ReasoningStepType.LEARNING,
                f"Learned classification: {learned_class}"
            )
            trail.add_decision(learned_class, learned_conf, [])

            return InferenceResult(
                decision=learned_class,
                confidence=learned_conf,
                confidence_level=self.thresholds.classify(learned_conf),
                reasoning=[f"Learned from previous: '{value}' -> {learned_class}"],
                alternatives=[],
                requires_review=learned_conf < self.thresholds.medium_threshold,
                action=get_action_for_confidence(learned_conf, self.thresholds),
                reasoning_trail=trail
            )

        # Default to unknown
        trail.add_warning(f"Could not classify '{value}'", severity="medium")
        trail.add_decision("unknown", 0.2, [])

        return InferenceResult(
            decision="unknown",
            confidence=0.2,
            confidence_level=ConfidenceLevel.LOW,
            reasoning=[f"No classification rule matched for '{value}'"],
            alternatives=[],
            requires_review=True,
            action=get_action_for_confidence(0.2, self.thresholds),
            reasoning_trail=trail
        )

    def validate_threshold(
        self,
        value: float,
        threshold_name: str,
        context: Optional[Dict] = None
    ) -> InferenceResult:
        """
        Validate a value against configurable thresholds.

        Replaces hardcoded magic numbers (20%, 5%, etc.).

        Args:
            value: Value to validate
            threshold_name: Name of threshold to check
            context: Optional context

        Returns:
            InferenceResult with validation result
        """
        trail = self.trail_manager.create_trail(f"threshold_{threshold_name}")

        # Get threshold rules
        category = "validation_thresholds"
        rules = self.rule_registry.get_rules_by_category(category)

        # Find matching threshold rule
        for rule in rules:
            if rule.metadata.get("threshold_name") == threshold_name:
                min_val = rule.metadata.get("min", float('-inf'))
                max_val = rule.metadata.get("max", float('inf'))
                warning_min = rule.metadata.get("warning_min", min_val)
                warning_max = rule.metadata.get("warning_max", max_val)

                # Check thresholds
                in_range = min_val <= value <= max_val
                in_warning = warning_min <= value <= warning_max

                if in_range and in_warning:
                    confidence = 0.95
                    result = "valid"
                    trail.add_threshold_check(threshold_name, value, max_val, True)
                elif in_range:
                    confidence = 0.7
                    result = "warning"
                    trail.add_threshold_check(threshold_name, value, max_val, True)
                    trail.add_warning(f"Value {value} in warning range for {threshold_name}")
                else:
                    confidence = 0.3
                    result = "invalid"
                    trail.add_threshold_check(threshold_name, value, max_val, False)

                trail.add_decision(result, confidence, [])

                return InferenceResult(
                    decision=result,
                    confidence=confidence,
                    confidence_level=self.thresholds.classify(confidence),
                    reasoning=[
                        f"Validated {threshold_name}: {value}",
                        f"Range: {min_val} - {max_val}",
                        f"Result: {result}"
                    ],
                    alternatives=[],
                    requires_review=result != "valid",
                    action=get_action_for_confidence(confidence, self.thresholds),
                    reasoning_trail=trail
                )

        # No threshold defined
        trail.add_warning(f"No threshold defined for '{threshold_name}'", severity="low")
        trail.add_decision("unknown", 0.5, [])

        return InferenceResult(
            decision="unknown",
            confidence=0.5,
            confidence_level=ConfidenceLevel.MEDIUM,
            reasoning=[f"No threshold rule defined for '{threshold_name}'"],
            alternatives=[],
            requires_review=True,
            action=get_action_for_confidence(0.5, self.thresholds),
            reasoning_trail=trail
        )

    def record_correction(
        self,
        inference_type: str,
        original_result: InferenceResult,
        corrected_value: Any,
        context: Dict
    ):
        """
        Record a user correction for learning.

        Args:
            inference_type: Type of inference (strand_detection, column_mapping, etc.)
            original_result: The original inference result
            corrected_value: What the user corrected it to
            context: Context for the decision
        """
        self.learning_engine.record_correction(
            correction_type=inference_type,
            original_decision=original_result.decision,
            corrected_value=corrected_value,
            context=context
        )

    def get_all_reasoning_trails(self) -> Dict:
        """Get all reasoning trails for audit."""
        return self.trail_manager.export_all()

    def get_warnings(self) -> List[Dict]:
        """Get all warnings from reasoning trails."""
        return self.trail_manager.get_all_warnings()

    def get_assumptions(self) -> List[Dict]:
        """Get all assumptions from reasoning trails."""
        return self.trail_manager.get_all_assumptions()

    def get_stats(self) -> Dict:
        """Get statistics about the inference engine."""
        return {
            "rules": self.rule_registry.get_stats(),
            "schemas": self.schema_registry.get_stats(),
            "learning": self.learning_engine.get_learning_stats(),
            "decisions_made": len(self.trail_manager.trails),
            "thresholds": {
                "high": self.thresholds.high_threshold,
                "medium": self.thresholds.medium_threshold
            }
        }
