"""
Rule Registry - YAML Rule Loading with Hot-Reload

Manages rules loaded from YAML configuration files.
Supports hot-reloading when files change.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Lazy import for FuzzyMatcher to avoid circular imports
_fuzzy_matcher = None


def _get_fuzzy_matcher():
    """Get or create a FuzzyMatcher instance for fuzzy conditions."""
    global _fuzzy_matcher
    if _fuzzy_matcher is None:
        try:
            from .fuzzy_matcher import get_default_fuzzy_matcher
            _fuzzy_matcher = get_default_fuzzy_matcher()
        except ImportError:
            _fuzzy_matcher = None
    return _fuzzy_matcher


@dataclass
class RuleCondition:
    """A condition that can be evaluated."""
    condition_type: str  # contains, matches, equals, greater_than, fuzzy_contains, etc.
    value: Any
    field: Optional[str] = None  # Which field to check
    case_sensitive: bool = False
    threshold: float = 0.7  # Threshold for fuzzy matching conditions

    def evaluate(self, data: Any, field_value: Any = None) -> bool:
        """Evaluate the condition against data."""
        target = field_value if field_value is not None else data

        if target is None:
            return False

        # Convert to string for text operations
        target_str = str(target).lower() if not self.case_sensitive else str(target)

        if self.condition_type == "contains":
            values = self.value if isinstance(self.value, list) else [self.value]
            return any(
                (v.lower() if not self.case_sensitive else v) in target_str
                for v in values
            )

        elif self.condition_type == "matches":
            pattern = self.value
            if not self.case_sensitive:
                return bool(re.match(pattern, target_str, re.IGNORECASE))
            return bool(re.match(pattern, str(target)))

        elif self.condition_type == "equals":
            compare = str(self.value).lower() if not self.case_sensitive else str(self.value)
            return target_str == compare

        elif self.condition_type == "in":
            values = self.value if isinstance(self.value, list) else [self.value]
            values_lower = [str(v).lower() for v in values] if not self.case_sensitive else values
            return target_str in values_lower

        elif self.condition_type == "greater_than":
            try:
                return float(target) > float(self.value)
            except (ValueError, TypeError):
                return False

        elif self.condition_type == "less_than":
            try:
                return float(target) < float(self.value)
            except (ValueError, TypeError):
                return False

        elif self.condition_type == "between":
            try:
                val = float(target)
                return self.value[0] <= val <= self.value[1]
            except (ValueError, TypeError, IndexError):
                return False

        elif self.condition_type == "not_empty":
            return bool(target_str.strip())

        elif self.condition_type == "length":
            if isinstance(self.value, dict):
                min_len = self.value.get('min', 0)
                max_len = self.value.get('max', float('inf'))
                return min_len <= len(target_str) <= max_len
            return len(target_str) == int(self.value)

        # =====================================================================
        # Fuzzy Matching Conditions
        # =====================================================================
        elif self.condition_type == "fuzzy_contains":
            # Check if any value fuzzy-matches the target
            matcher = _get_fuzzy_matcher()
            if matcher is None:
                # Fall back to regular contains if fuzzy matcher unavailable
                values = self.value if isinstance(self.value, list) else [self.value]
                return any(
                    (v.lower() if not self.case_sensitive else v) in target_str
                    for v in values
                )

            values = self.value if isinstance(self.value, list) else [self.value]
            for v in values:
                score = matcher.match(target_str, v.lower() if not self.case_sensitive else v)
                if score >= self.threshold:
                    return True
            return False

        elif self.condition_type == "jaro_winkler":
            # Jaro-Winkler similarity check
            matcher = _get_fuzzy_matcher()
            if matcher is None:
                return target_str == str(self.value).lower()

            compare = str(self.value).lower() if not self.case_sensitive else str(self.value)
            score = matcher.jaro_winkler(target_str, compare)
            return score >= self.threshold

        elif self.condition_type == "levenshtein":
            # Levenshtein similarity check
            matcher = _get_fuzzy_matcher()
            if matcher is None:
                return target_str == str(self.value).lower()

            compare = str(self.value).lower() if not self.case_sensitive else str(self.value)
            score = matcher.levenshtein_similarity(target_str, compare)
            return score >= self.threshold

        elif self.condition_type == "fuzzy_match":
            # Combined fuzzy match using all algorithms
            matcher = _get_fuzzy_matcher()
            if matcher is None:
                return target_str == str(self.value).lower()

            compare = str(self.value).lower() if not self.case_sensitive else str(self.value)
            score = matcher.match(target_str, compare)
            return score >= self.threshold

        return False

    def get_fuzzy_score(self, data: Any, field_value: Any = None) -> float:
        """
        Get the fuzzy match score for this condition.

        Returns score from 0.0 to 1.0, or 1.0 for exact/boolean matches.
        """
        target = field_value if field_value is not None else data

        if target is None:
            return 0.0

        target_str = str(target).lower() if not self.case_sensitive else str(target)

        # For non-fuzzy conditions, return 1.0 if matched, 0.0 otherwise
        if self.condition_type not in ("fuzzy_contains", "jaro_winkler", "levenshtein", "fuzzy_match"):
            return 1.0 if self.evaluate(data, field_value) else 0.0

        matcher = _get_fuzzy_matcher()
        if matcher is None:
            return 1.0 if self.evaluate(data, field_value) else 0.0

        compare = str(self.value).lower() if not self.case_sensitive else str(self.value)

        if self.condition_type == "fuzzy_contains":
            values = self.value if isinstance(self.value, list) else [self.value]
            max_score = 0.0
            for v in values:
                score = matcher.match(target_str, v.lower() if not self.case_sensitive else v)
                max_score = max(max_score, score)
            return max_score

        elif self.condition_type == "jaro_winkler":
            return matcher.jaro_winkler(target_str, compare)

        elif self.condition_type == "levenshtein":
            return matcher.levenshtein_similarity(target_str, compare)

        elif self.condition_type == "fuzzy_match":
            return matcher.match(target_str, compare)

        return 0.0


@dataclass
class Rule:
    """A single rule definition."""
    id: str
    name: str
    category: str
    conditions: List[RuleCondition]
    weight: float = 1.0
    confidence_boost: float = 0.0  # How much to boost confidence when matched
    result: Optional[Any] = None  # Result value when rule matches
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0  # Higher priority rules checked first

    @classmethod
    def from_dict(cls, data: Dict) -> 'Rule':
        """Create a Rule from dictionary (YAML)."""
        conditions = []

        # Parse condition string or list
        condition_data = data.get('condition', data.get('conditions', []))
        if isinstance(condition_data, str):
            # Parse shorthand: "contains:staff,employee,payroll"
            conditions.append(cls._parse_condition_string(condition_data))
        elif isinstance(condition_data, list):
            for cond in condition_data:
                if isinstance(cond, str):
                    conditions.append(cls._parse_condition_string(cond))
                elif isinstance(cond, dict):
                    conditions.append(RuleCondition(
                        condition_type=cond.get('type', 'contains'),
                        value=cond.get('value'),
                        field=cond.get('field'),
                        case_sensitive=cond.get('case_sensitive', False),
                        threshold=float(cond.get('threshold', 0.7))
                    ))

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            category=data.get('category', ''),
            conditions=conditions,
            weight=float(data.get('weight', 1.0)),
            confidence_boost=float(data.get('confidence_boost', 0.0)),
            result=data.get('result'),
            metadata=data.get('metadata', {}),
            enabled=data.get('enabled', True),
            priority=int(data.get('priority', 0))
        )

    @staticmethod
    def _parse_condition_string(condition_str: str) -> RuleCondition:
        """Parse a condition string like 'contains:staff,employee'."""
        if ':' in condition_str:
            cond_type, values_str = condition_str.split(':', 1)
            values = [v.strip() for v in values_str.split(',')]
            return RuleCondition(
                condition_type=cond_type.strip(),
                value=values if len(values) > 1 else values[0]
            )
        else:
            return RuleCondition(
                condition_type='contains',
                value=condition_str
            )

    def evaluate(self, data: Any, context: Optional[Dict] = None) -> bool:
        """Evaluate all conditions against data."""
        if not self.enabled:
            return False

        for condition in self.conditions:
            field_value = None
            if condition.field and isinstance(data, dict):
                field_value = data.get(condition.field)
            elif condition.field and context:
                field_value = context.get(condition.field)

            if not condition.evaluate(data, field_value):
                return False

        return True


class RuleFileHandler(FileSystemEventHandler):
    """Handler for file change events to support hot-reload."""

    def __init__(self, registry: 'RuleRegistry'):
        self.registry = registry

    def on_modified(self, event):
        if event.src_path.endswith('.yaml') or event.src_path.endswith('.yml'):
            self.registry._reload_file(event.src_path)


class RuleRegistry:
    """
    Central registry for all rules loaded from YAML.

    Supports:
    - Loading rules from multiple YAML files
    - Hot-reload when files change
    - Querying rules by category
    - Evaluating rules against data
    """

    def __init__(self, rules_dir: Optional[Path] = None, hot_reload: bool = False):
        self.rules_dir = rules_dir or Path(__file__).parent.parent / "config" / "rules"
        self.rules: Dict[str, Rule] = {}  # id -> Rule
        self.rules_by_category: Dict[str, List[Rule]] = {}
        self.file_timestamps: Dict[str, float] = {}
        self.hot_reload = hot_reload
        self._observer: Optional[Observer] = None

        # Load all rules
        self._load_all_rules()

        # Start hot-reload if enabled
        if hot_reload:
            self._start_watching()

    def _load_all_rules(self):
        """Load all rules from YAML files."""
        if not self.rules_dir.exists():
            return

        for yaml_file in self.rules_dir.glob("*.yaml"):
            self._load_file(yaml_file)

        for yml_file in self.rules_dir.glob("*.yml"):
            self._load_file(yml_file)

    def _load_file(self, file_path: Path):
        """Load rules from a single YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            self.file_timestamps[str(file_path)] = os.path.getmtime(file_path)

            # Handle both 'rules' list and direct rule definitions
            rules_data = data.get('rules', [])
            if not rules_data and isinstance(data, list):
                rules_data = data

            for rule_data in rules_data:
                rule = Rule.from_dict(rule_data)
                if rule.id:
                    self.rules[rule.id] = rule

                    # Index by category
                    if rule.category not in self.rules_by_category:
                        self.rules_by_category[rule.category] = []
                    self.rules_by_category[rule.category].append(rule)

        except Exception as e:
            print(f"Error loading rules from {file_path}: {e}")

    def _reload_file(self, file_path: str):
        """Reload a single file after modification."""
        path = Path(file_path)

        # Remove old rules from this file
        # (In production, track which rules came from which file)

        # Reload
        self._load_file(path)
        print(f"[RuleRegistry] Hot-reloaded {path.name}")

    def _start_watching(self):
        """Start watching for file changes."""
        if self._observer is not None:
            return

        self._observer = Observer()
        handler = RuleFileHandler(self)
        self._observer.schedule(handler, str(self.rules_dir), recursive=False)
        self._observer.start()

    def stop_watching(self):
        """Stop watching for file changes."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)

    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Get all rules in a category, sorted by priority."""
        rules = self.rules_by_category.get(category, [])
        return sorted(rules, key=lambda r: -r.priority)

    def evaluate_rules(
        self,
        category: str,
        data: Any,
        context: Optional[Dict] = None,
        stop_on_first: bool = False
    ) -> List[tuple]:
        """
        Evaluate all rules in a category against data.

        Args:
            category: Rule category to evaluate
            data: Data to evaluate against
            context: Optional additional context
            stop_on_first: Stop after first matching rule

        Returns:
            List of (rule, matched) tuples
        """
        results = []
        rules = self.get_rules_by_category(category)

        for rule in rules:
            matched = rule.evaluate(data, context)
            results.append((rule, matched))

            if matched and stop_on_first:
                break

        return results

    def find_matching_rules(
        self,
        category: str,
        data: Any,
        context: Optional[Dict] = None
    ) -> List[Rule]:
        """Find all rules that match the given data."""
        results = self.evaluate_rules(category, data, context)
        return [rule for rule, matched in results if matched]

    def calculate_score(
        self,
        category: str,
        data: Any,
        context: Optional[Dict] = None
    ) -> tuple:
        """
        Calculate a weighted score based on matching rules.

        Returns:
            (score, confidence, matched_rules)
        """
        matched_rules = self.find_matching_rules(category, data, context)

        if not matched_rules:
            return 0.0, 0.0, []

        total_weight = sum(r.weight for r in matched_rules)
        confidence_boost = sum(r.confidence_boost for r in matched_rules)

        # Normalize score (0-1)
        all_rules = self.get_rules_by_category(category)
        max_possible = sum(r.weight for r in all_rules) if all_rules else 1

        score = total_weight / max_possible if max_possible > 0 else 0
        confidence = min(1.0, score + confidence_boost)

        return score, confidence, matched_rules

    def add_rule(self, rule: Rule):
        """Add a rule programmatically."""
        self.rules[rule.id] = rule
        if rule.category not in self.rules_by_category:
            self.rules_by_category[rule.category] = []
        self.rules_by_category[rule.category].append(rule)

    def remove_rule(self, rule_id: str):
        """Remove a rule by ID."""
        if rule_id in self.rules:
            rule = self.rules.pop(rule_id)
            if rule.category in self.rules_by_category:
                self.rules_by_category[rule.category] = [
                    r for r in self.rules_by_category[rule.category]
                    if r.id != rule_id
                ]

    def get_stats(self) -> Dict:
        """Get statistics about loaded rules."""
        return {
            "total_rules": len(self.rules),
            "categories": list(self.rules_by_category.keys()),
            "rules_per_category": {
                cat: len(rules)
                for cat, rules in self.rules_by_category.items()
            },
            "files_loaded": len(self.file_timestamps),
            "hot_reload_enabled": self.hot_reload
        }
