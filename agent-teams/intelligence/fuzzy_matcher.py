"""
FuzzyMatcher - Fuzzy String Matching for Column Names

Provides fuzzy matching algorithms for flexible column name recognition.
Includes Jaro-Winkler, Levenshtein distance, and abbreviation expansion.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re


@dataclass
class MatchResult:
    """Result of a fuzzy match operation."""
    source: str
    target: str
    score: float
    match_type: str  # 'exact', 'variation', 'fuzzy', 'abbreviation'
    details: Optional[Dict[str, Any]] = None


class FuzzyMatcher:
    """
    Fuzzy string matching with multiple algorithms.

    Provides:
    - Jaro-Winkler similarity (good for typos/transpositions)
    - Levenshtein distance (edit distance)
    - Abbreviation expansion
    - Combined scoring with weights
    """

    def __init__(
        self,
        abbreviations: Optional[Dict[str, List[str]]] = None,
        jaro_weight: float = 0.5,
        levenshtein_weight: float = 0.3,
        abbrev_weight: float = 0.2
    ):
        """
        Initialize the FuzzyMatcher.

        Args:
            abbreviations: Dictionary of abbreviation -> expansions
            jaro_weight: Weight for Jaro-Winkler score (0-1)
            levenshtein_weight: Weight for Levenshtein score (0-1)
            abbrev_weight: Weight for abbreviation match score (0-1)
        """
        self.abbreviations = abbreviations or {}
        self.jaro_weight = jaro_weight
        self.levenshtein_weight = levenshtein_weight
        self.abbrev_weight = abbrev_weight

        # Pre-compile common transformations
        self._normalize_pattern = re.compile(r'[^a-z0-9]+')

    def match(self, source: str, target: str) -> float:
        """
        Calculate overall match score between two strings.

        Args:
            source: Source string to match
            target: Target string to match against

        Returns:
            Float score from 0.0 (no match) to 1.0 (exact match)
        """
        if not source or not target:
            return 0.0

        # Normalize strings
        source_norm = self._normalize(source)
        target_norm = self._normalize(target)

        # Exact match
        if source_norm == target_norm:
            return 1.0

        # Calculate component scores
        jaro = self.jaro_winkler(source_norm, target_norm)
        lev = self.levenshtein_similarity(source_norm, target_norm)

        # Check abbreviation matches
        abbrev_score = self._check_abbreviation_match(source_norm, target_norm)

        # Weighted combination
        total_weight = self.jaro_weight + self.levenshtein_weight + self.abbrev_weight
        score = (
            (jaro * self.jaro_weight) +
            (lev * self.levenshtein_weight) +
            (abbrev_score * self.abbrev_weight)
        ) / total_weight

        return round(score, 4)

    def jaro_winkler(self, s1: str, s2: str, winkler_boost: float = 0.1) -> float:
        """
        Calculate Jaro-Winkler similarity between two strings.

        Good for detecting typos and transposed characters.

        Args:
            s1: First string
            s2: Second string
            winkler_boost: Prefix bonus multiplier (default 0.1)

        Returns:
            Float from 0.0 to 1.0
        """
        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Calculate match window
        match_distance = max(len1, len2) // 2 - 1
        if match_distance < 0:
            match_distance = 0

        s1_matches = [False] * len1
        s2_matches = [False] * len2

        matches = 0
        transpositions = 0

        # Find matches
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)

            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

        if matches == 0:
            return 0.0

        # Count transpositions
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

        # Calculate Jaro similarity
        jaro = (
            (matches / len1) +
            (matches / len2) +
            ((matches - transpositions / 2) / matches)
        ) / 3

        # Apply Winkler boost for common prefix
        prefix_len = 0
        for i in range(min(len1, len2, 4)):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break

        return jaro + (prefix_len * winkler_boost * (1 - jaro))

    def levenshtein(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein edit distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Integer edit distance (0 = identical)
        """
        if s1 == s2:
            return 0

        len1, len2 = len(s1), len(s2)
        if len1 == 0:
            return len2
        if len2 == 0:
            return len1

        # Create distance matrix
        prev_row = list(range(len2 + 1))
        curr_row = [0] * (len2 + 1)

        for i in range(len1):
            curr_row[0] = i + 1

            for j in range(len2):
                cost = 0 if s1[i] == s2[j] else 1
                curr_row[j + 1] = min(
                    prev_row[j + 1] + 1,     # deletion
                    curr_row[j] + 1,          # insertion
                    prev_row[j] + cost        # substitution
                )

            prev_row, curr_row = curr_row, prev_row

        return prev_row[len2]

    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate Levenshtein similarity as a ratio.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Float from 0.0 to 1.0 (1.0 = identical)
        """
        if s1 == s2:
            return 1.0

        distance = self.levenshtein(s1, s2)
        max_len = max(len(s1), len(s2))

        if max_len == 0:
            return 1.0

        return 1.0 - (distance / max_len)

    def expand_abbreviations(self, text: str) -> List[str]:
        """
        Expand a string using known abbreviations.

        Args:
            text: Input string potentially containing abbreviations

        Returns:
            List of possible expansions (including original)
        """
        expansions = [text]
        text_lower = text.lower()

        for abbrev, full_forms in self.abbreviations.items():
            abbrev_lower = abbrev.lower()

            # Check if abbreviation appears in text
            if abbrev_lower in text_lower:
                for full_form in full_forms:
                    # Replace abbreviation with each possible expansion
                    expanded = re.sub(
                        re.escape(abbrev_lower),
                        full_form,
                        text_lower,
                        flags=re.IGNORECASE
                    )
                    if expanded not in expansions:
                        expansions.append(expanded)

            # Also check if text IS the abbreviation
            if text_lower == abbrev_lower:
                expansions.extend(full_forms)

        return list(set(expansions))

    def find_best_match(
        self,
        source: str,
        candidates: List[str],
        threshold: float = 0.5
    ) -> Tuple[Optional[str], float]:
        """
        Find the best matching candidate for a source string.

        Args:
            source: String to match
            candidates: List of candidate strings
            threshold: Minimum score to consider a match

        Returns:
            Tuple of (best_match, score) or (None, 0.0) if no match
        """
        if not source or not candidates:
            return None, 0.0

        best_match = None
        best_score = 0.0

        # Expand source with abbreviations
        source_variants = self.expand_abbreviations(source)

        for candidate in candidates:
            # Also expand candidate
            candidate_variants = self.expand_abbreviations(candidate)

            # Try all combinations
            for src in source_variants:
                for cand in candidate_variants:
                    score = self.match(src, cand)
                    if score > best_score:
                        best_score = score
                        best_match = candidate

        if best_score >= threshold:
            return best_match, best_score

        return None, 0.0

    def find_all_matches(
        self,
        source: str,
        candidates: List[str],
        threshold: float = 0.5,
        max_results: int = 5
    ) -> List[MatchResult]:
        """
        Find all matching candidates above threshold.

        Args:
            source: String to match
            candidates: List of candidate strings
            threshold: Minimum score to include
            max_results: Maximum number of results

        Returns:
            List of MatchResult objects, sorted by score descending
        """
        if not source or not candidates:
            return []

        results = []
        source_norm = self._normalize(source)
        source_variants = self.expand_abbreviations(source_norm)

        for candidate in candidates:
            cand_norm = self._normalize(candidate)
            cand_variants = self.expand_abbreviations(cand_norm)

            best_score = 0.0
            match_type = 'fuzzy'
            match_details = {}

            for src in source_variants:
                for cand in cand_variants:
                    # Check exact match first
                    if src == cand:
                        best_score = 1.0
                        match_type = 'exact' if src == source_norm else 'abbreviation'
                        break

                    score = self.match(src, cand)
                    if score > best_score:
                        best_score = score
                        match_details = {
                            'jaro_winkler': self.jaro_winkler(src, cand),
                            'levenshtein': self.levenshtein_similarity(src, cand),
                            'source_expanded': src if src != source_norm else None,
                            'target_expanded': cand if cand != cand_norm else None
                        }

                if best_score == 1.0:
                    break

            if best_score >= threshold:
                results.append(MatchResult(
                    source=source,
                    target=candidate,
                    score=best_score,
                    match_type=match_type,
                    details=match_details
                ))

        # Sort by score descending
        results.sort(key=lambda r: -r.score)

        return results[:max_results]

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Replace common separators with underscores
        normalized = normalized.replace('-', '_').replace(' ', '_')

        # Remove non-alphanumeric except underscores
        normalized = self._normalize_pattern.sub('_', normalized)

        # Remove leading/trailing underscores and collapse multiples
        normalized = re.sub(r'_+', '_', normalized).strip('_')

        return normalized

    def _check_abbreviation_match(self, source: str, target: str) -> float:
        """
        Check if source matches target through abbreviation expansion.

        Returns score from 0.0 to 1.0.
        """
        source_expansions = self.expand_abbreviations(source)
        target_expansions = self.expand_abbreviations(target)

        # Check if any expansion matches
        for src_exp in source_expansions:
            if src_exp in target_expansions:
                return 1.0

            # Partial match on expansions
            for tgt_exp in target_expansions:
                if src_exp in tgt_exp or tgt_exp in src_exp:
                    # Partial match - calculate overlap
                    longer = max(len(src_exp), len(tgt_exp))
                    shorter = min(len(src_exp), len(tgt_exp))
                    return shorter / longer

        return 0.0

    def set_abbreviations(self, abbreviations: Dict[str, List[str]]):
        """Update the abbreviations dictionary."""
        self.abbreviations = abbreviations

    def add_abbreviation(self, abbrev: str, expansions: List[str]):
        """Add or update a single abbreviation."""
        self.abbreviations[abbrev] = expansions


# Default abbreviations for common column name variations
DEFAULT_ABBREVIATIONS = {
    # Name fields
    "fn": ["first_name", "firstname", "forename"],
    "ln": ["last_name", "lastname", "surname"],
    "nm": ["name"],
    "fname": ["first_name", "firstname"],
    "lname": ["last_name", "lastname"],

    # Employee/Staff
    "emp": ["employee", "employment"],
    "emp_no": ["employee_number", "payroll_number"],
    "empno": ["employee_number", "payroll_number"],
    "staff_no": ["staff_number", "employee_number"],

    # Pay/Salary
    "sal": ["salary"],
    "fte": ["full_time_equivalent"],
    "hpw": ["hours_per_week"],
    "hrs": ["hours"],
    "wkly": ["weekly"],
    "ann": ["annual"],

    # Pension
    "pens": ["pension"],
    "tps": ["teachers_pension_scheme"],
    "lgps": ["local_government_pension_scheme"],

    # School/Organization
    "sch": ["school"],
    "dept": ["department"],
    "org": ["organization", "organisation"],

    # Dates
    "dt": ["date"],
    "dob": ["date_of_birth"],
    "start_dt": ["start_date"],
    "end_dt": ["end_date"],

    # Contract
    "cont": ["contract"],
    "ref": ["reference"],
    "typ": ["type"],

    # Pay Scales
    "ps": ["pay_scale", "payscale"],
    "sp": ["scale_point", "spine_point"],
    "njc": ["national_joint_council"],
    "mps": ["main_pay_scale"],
    "ups": ["upper_pay_scale"],

    # Role
    "pos": ["position"],
    "role": ["staff_role"],
    "grp": ["group"],
    "srg": ["staff_role_group"],
}


def get_default_fuzzy_matcher() -> FuzzyMatcher:
    """Get a FuzzyMatcher with default abbreviations."""
    return FuzzyMatcher(abbreviations=DEFAULT_ABBREVIATIONS)
