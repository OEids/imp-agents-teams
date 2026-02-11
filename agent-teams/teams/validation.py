"""
Validation Module

Provides multiple validation checks, original data comparison,
and assumption tracking for full transparency.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"           # Informational only
    WARNING = "warning"     # Potential issue, may need review
    ERROR = "error"         # Definite issue, needs attention
    CRITICAL = "critical"   # Blocking issue, cannot proceed


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_rows: List[int] = field(default_factory=list)
    affected_columns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "affected_rows_count": len(self.affected_rows),
            "affected_columns": self.affected_columns
        }


@dataclass
class Assumption:
    """Tracks an assumption made during processing."""
    category: str           # e.g., "data_type", "missing_value", "format"
    description: str        # What was assumed
    reason: str            # Why this assumption was made
    impact: str            # What this affects
    confidence: str        # "high", "medium", "low"
    affected_records: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "description": self.description,
            "reason": self.reason,
            "impact": self.impact,
            "confidence": self.confidence,
            "affected_records": self.affected_records,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DataChange:
    """Tracks a change made to the data."""
    row_index: int
    column: str
    original_value: Any
    new_value: Any
    change_type: str  # "modified", "removed", "added", "type_converted"
    reason: str

    def to_dict(self) -> Dict:
        return {
            "row": self.row_index,
            "column": self.column,
            "original": str(self.original_value),
            "new": str(self.new_value),
            "type": self.change_type,
            "reason": self.reason
        }


class DataValidator:
    """
    Comprehensive data validation with multiple check types.
    """

    def __init__(self, team_id: str):
        self.team_id = team_id
        self.results: List[ValidationResult] = []

    def validate_all(self, df: pd.DataFrame, context: Dict = None) -> List[ValidationResult]:
        """Run all validation checks on a dataframe."""
        self.results = []
        context = context or {}

        # Structure checks
        self._check_empty_dataframe(df)
        self._check_column_names(df)
        self._check_duplicate_columns(df)

        # Data quality checks
        self._check_null_values(df)
        self._check_duplicate_rows(df)
        self._check_data_types(df)

        # Format checks
        self._check_date_formats(df)
        self._check_numeric_formats(df)
        self._check_text_formats(df)

        # Business logic checks (team-specific)
        self._check_business_rules(df, context)

        # Consistency checks
        self._check_referential_integrity(df, context)
        self._check_value_ranges(df)

        return self.results

    def _add_result(self, check_name: str, passed: bool, severity: ValidationSeverity,
                    message: str, details: Dict = None, affected_rows: List = None,
                    affected_columns: List = None):
        """Add a validation result."""
        self.results.append(ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=message,
            details=details or {},
            affected_rows=affected_rows or [],
            affected_columns=affected_columns or []
        ))

    def _check_empty_dataframe(self, df: pd.DataFrame):
        """Check if dataframe is empty."""
        if df.empty:
            self._add_result(
                "empty_data",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message="Dataset is empty - no records to process"
            )
        else:
            self._add_result(
                "empty_data",
                passed=True,
                severity=ValidationSeverity.INFO,
                message=f"Dataset has {len(df)} records",
                details={"row_count": len(df), "column_count": len(df.columns)}
            )

    def _check_column_names(self, df: pd.DataFrame):
        """Check for problematic column names."""
        issues = []
        for col in df.columns:
            col_str = str(col)
            if col_str.startswith('Unnamed'):
                issues.append(col_str)
            elif col_str.strip() != col_str:
                issues.append(f"'{col_str}' (has whitespace)")

        if issues:
            self._add_result(
                "column_names",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found {len(issues)} problematic column names",
                details={"issues": issues[:10]},
                affected_columns=issues
            )
        else:
            self._add_result(
                "column_names",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="All column names are valid"
            )

    def _check_duplicate_columns(self, df: pd.DataFrame):
        """Check for duplicate column names."""
        cols = [str(c) for c in df.columns]
        duplicates = [c for c in cols if cols.count(c) > 1]

        if duplicates:
            self._add_result(
                "duplicate_columns",
                passed=False,
                severity=ValidationSeverity.ERROR,
                message=f"Found duplicate column names: {set(duplicates)}",
                affected_columns=list(set(duplicates))
            )
        else:
            self._add_result(
                "duplicate_columns",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="No duplicate column names"
            )

    def _check_null_values(self, df: pd.DataFrame):
        """Check for null/missing values."""
        null_counts = df.isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]

        if len(cols_with_nulls) > 0:
            total_nulls = cols_with_nulls.sum()
            null_pct = (total_nulls / (len(df) * len(df.columns))) * 100

            severity = ValidationSeverity.INFO if null_pct < 5 else \
                       ValidationSeverity.WARNING if null_pct < 20 else \
                       ValidationSeverity.ERROR

            self._add_result(
                "null_values",
                passed=null_pct < 5,
                severity=severity,
                message=f"Found {total_nulls} null values ({null_pct:.1f}%) across {len(cols_with_nulls)} columns",
                details={
                    "total_nulls": int(total_nulls),
                    "percentage": round(null_pct, 2),
                    "by_column": cols_with_nulls.to_dict()
                },
                affected_columns=cols_with_nulls.index.tolist()
            )
        else:
            self._add_result(
                "null_values",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="No null values found"
            )

    def _check_duplicate_rows(self, df: pd.DataFrame):
        """Check for duplicate rows."""
        duplicates = df.duplicated()
        dup_count = duplicates.sum()

        if dup_count > 0:
            dup_indices = df[duplicates].index.tolist()
            self._add_result(
                "duplicate_rows",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found {dup_count} duplicate rows",
                details={"count": int(dup_count)},
                affected_rows=dup_indices[:100]  # First 100
            )
        else:
            self._add_result(
                "duplicate_rows",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="No duplicate rows found"
            )

    def _check_data_types(self, df: pd.DataFrame):
        """Check for mixed data types in columns."""
        mixed_type_cols = []

        for col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                types = non_null.apply(type).unique()
                if len(types) > 1:
                    mixed_type_cols.append({
                        "column": str(col),
                        "types": [t.__name__ for t in types]
                    })

        if mixed_type_cols:
            self._add_result(
                "mixed_data_types",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found {len(mixed_type_cols)} columns with mixed data types",
                details={"columns": mixed_type_cols},
                affected_columns=[c["column"] for c in mixed_type_cols]
            )
        else:
            self._add_result(
                "mixed_data_types",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="All columns have consistent data types"
            )

    def _check_date_formats(self, df: pd.DataFrame):
        """Check date columns for format consistency."""
        date_issues = []
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # Also check object columns that might be dates
        for col in df.select_dtypes(include=['object']).columns:
            sample = df[col].dropna().head(100)
            date_patterns = sample.astype(str).str.match(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}')
            if date_patterns.any():
                date_cols.append(col)

        for col in date_cols:
            try:
                parsed = pd.to_datetime(df[col], errors='coerce')
                failed = parsed.isna() & df[col].notna()
                if failed.any():
                    date_issues.append({
                        "column": str(col),
                        "invalid_count": int(failed.sum())
                    })
            except Exception:
                pass

        if date_issues:
            self._add_result(
                "date_formats",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found date format issues in {len(date_issues)} columns",
                details={"issues": date_issues},
                affected_columns=[d["column"] for d in date_issues]
            )
        else:
            self._add_result(
                "date_formats",
                passed=True,
                severity=ValidationSeverity.INFO,
                message=f"Date formats are consistent ({len(date_cols)} date columns found)"
            )

    def _check_numeric_formats(self, df: pd.DataFrame):
        """Check numeric columns for issues."""
        numeric_issues = []

        for col in df.select_dtypes(include=['object']).columns:
            # Check if column should be numeric
            sample = df[col].dropna().head(100).astype(str)
            numeric_pattern = sample.str.match(r'^-?\d+\.?\d*$')

            if numeric_pattern.mean() > 0.5:  # More than 50% look numeric
                non_numeric = df[col].dropna()[~df[col].astype(str).str.match(r'^-?\d+\.?\d*$', na=False)]
                if len(non_numeric) > 0:
                    numeric_issues.append({
                        "column": str(col),
                        "non_numeric_count": len(non_numeric),
                        "examples": non_numeric.head(5).tolist()
                    })

        if numeric_issues:
            self._add_result(
                "numeric_formats",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found {len(numeric_issues)} columns with numeric format issues",
                details={"issues": numeric_issues},
                affected_columns=[n["column"] for n in numeric_issues]
            )
        else:
            self._add_result(
                "numeric_formats",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="Numeric formats are consistent"
            )

    def _check_text_formats(self, df: pd.DataFrame):
        """Check text columns for common issues."""
        text_issues = []

        for col in df.select_dtypes(include=['object']).columns:
            issues = []
            sample = df[col].dropna()

            if len(sample) == 0:
                continue

            # Check for leading/trailing whitespace
            whitespace = sample.astype(str).str.match(r'^\s+|\s+$')
            if whitespace.any():
                issues.append(f"whitespace ({whitespace.sum()} rows)")

            # Check for excessive length
            lengths = sample.astype(str).str.len()
            if lengths.max() > 500:
                issues.append(f"long text (max {lengths.max()} chars)")

            # Check for special characters
            special = sample.astype(str).str.contains(r'[\x00-\x1f]', regex=True)
            if special.any():
                issues.append(f"special chars ({special.sum()} rows)")

            if issues:
                text_issues.append({"column": str(col), "issues": issues})

        if text_issues:
            self._add_result(
                "text_formats",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found text format issues in {len(text_issues)} columns",
                details={"issues": text_issues[:10]},
                affected_columns=[t["column"] for t in text_issues]
            )
        else:
            self._add_result(
                "text_formats",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="Text formats are clean"
            )

    def _check_business_rules(self, df: pd.DataFrame, context: Dict):
        """Check team-specific business rules."""
        rules_checked = []

        if self.team_id == "S1":
            # Structure team rules
            rules_checked.extend(self._check_s1_rules(df))
        elif self.team_id == "S2":
            # Staff team rules
            rules_checked.extend(self._check_s2_rules(df))
        elif self.team_id == "S3":
            # Financial team rules
            rules_checked.extend(self._check_s3_rules(df))

        if not rules_checked:
            self._add_result(
                "business_rules",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="No business rule violations detected"
            )

    def _check_s1_rules(self, df: pd.DataFrame) -> List[str]:
        """Structure team specific rules."""
        issues = []
        cols_lower = [str(c).lower() for c in df.columns]

        # Check for required code columns
        if not any('code' in c for c in cols_lower):
            issues.append("No 'code' column found - required for structure data")
            self._add_result(
                "s1_code_column",
                passed=False,
                severity=ValidationSeverity.ERROR,
                message="Missing required 'code' column for structure data"
            )

        return issues

    def _check_s2_rules(self, df: pd.DataFrame) -> List[str]:
        """Staff team specific rules."""
        issues = []
        cols_lower = {str(c).lower(): c for c in df.columns}

        # Check for payroll number
        payroll_cols = [c for c in cols_lower if 'payroll' in c]
        if payroll_cols:
            col = cols_lower[payroll_cols[0]]
            # Check for duplicates in payroll
            if df[col].duplicated().any():
                dup_count = df[col].duplicated().sum()
                issues.append(f"Duplicate payroll numbers found: {dup_count}")
                self._add_result(
                    "s2_duplicate_payroll",
                    passed=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Found {dup_count} duplicate payroll numbers - may indicate multiple contracts per person",
                    details={"duplicate_count": int(dup_count)}
                )

        # Check salary ranges
        salary_cols = [c for c in cols_lower if 'salary' in c]
        for sal_col in salary_cols:
            col = cols_lower[sal_col]
            try:
                salaries = pd.to_numeric(df[col], errors='coerce')
                if salaries.min() < 0:
                    issues.append(f"Negative salaries found in {col}")
                    self._add_result(
                        "s2_negative_salary",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Negative salary values found in {col}",
                        affected_columns=[col]
                    )
                if salaries.max() > 500000:
                    self._add_result(
                        "s2_high_salary",
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Unusually high salary values (>{salaries.max():,.0f}) in {col} - verify correctness",
                        affected_columns=[col]
                    )
            except Exception:
                pass

        return issues

    def _check_s3_rules(self, df: pd.DataFrame) -> List[str]:
        """Financial team specific rules."""
        issues = []
        cols_lower = {str(c).lower(): c for c in df.columns}

        # Check for budget columns
        budget_cols = [c for c in cols_lower if 'budget' in c or 'amount' in c or 'value' in c]
        for budget_col in budget_cols:
            col = cols_lower[budget_col]
            try:
                values = pd.to_numeric(df[col], errors='coerce')
                if values.isna().all():
                    continue

                # Check for negative budgets (may be valid for some cases)
                neg_count = (values < 0).sum()
                if neg_count > 0:
                    self._add_result(
                        "s3_negative_budgets",
                        passed=True,  # Not necessarily wrong
                        severity=ValidationSeverity.INFO,
                        message=f"Found {neg_count} negative values in {col} - verify if these represent credits/adjustments",
                        details={"negative_count": int(neg_count)},
                        affected_columns=[col]
                    )
            except Exception:
                pass

        return issues

    def _check_referential_integrity(self, df: pd.DataFrame, context: Dict):
        """Check referential integrity if reference data is provided."""
        ref_data = context.get("reference_data", {})

        if not ref_data:
            self._add_result(
                "referential_integrity",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="No reference data provided for integrity check"
            )
            return

        # Check each reference
        for ref_name, ref_values in ref_data.items():
            matching_cols = [c for c in df.columns if ref_name.lower() in str(c).lower()]
            for col in matching_cols:
                invalid = ~df[col].isin(ref_values) & df[col].notna()
                if invalid.any():
                    self._add_result(
                        f"ref_integrity_{ref_name}",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {invalid.sum()} values in {col} not in reference list",
                        details={"invalid_values": df.loc[invalid, col].unique()[:10].tolist()},
                        affected_columns=[str(col)]
                    )

    def _check_value_ranges(self, df: pd.DataFrame):
        """Check for outliers and unusual value ranges."""
        outlier_cols = []

        for col in df.select_dtypes(include=[np.number]).columns:
            values = df[col].dropna()
            if len(values) < 10:
                continue

            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 3 * iqr
            upper = q3 + 3 * iqr

            outliers = values[(values < lower) | (values > upper)]
            if len(outliers) > 0:
                outlier_cols.append({
                    "column": str(col),
                    "outlier_count": len(outliers),
                    "range": f"{lower:.2f} to {upper:.2f}",
                    "examples": outliers.head(5).tolist()
                })

        if outlier_cols:
            self._add_result(
                "value_ranges",
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found potential outliers in {len(outlier_cols)} columns",
                details={"outliers": outlier_cols},
                affected_columns=[o["column"] for o in outlier_cols]
            )
        else:
            self._add_result(
                "value_ranges",
                passed=True,
                severity=ValidationSeverity.INFO,
                message="No significant outliers detected"
            )

    def get_summary(self) -> Dict:
        """Get validation summary."""
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        by_severity = {}
        for r in self.results:
            sev = r.severity.value
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(r.check_name)

        return {
            "total_checks": len(self.results),
            "passed": len(passed),
            "failed": len(failed),
            "by_severity": by_severity,
            "critical_issues": [r.message for r in self.results if r.severity == ValidationSeverity.CRITICAL],
            "errors": [r.message for r in self.results if r.severity == ValidationSeverity.ERROR]
        }


class DataComparator:
    """
    Compares processed data against original to track all changes.
    """

    def __init__(self):
        self.changes: List[DataChange] = []
        self.original_hash: str = ""
        self.original_stats: Dict = {}
        self.original_data: Optional[pd.DataFrame] = None

    def capture_original(self, df: pd.DataFrame):
        """Capture original data state for comparison."""
        self.original_data = df.copy()
        self.original_hash = self._hash_dataframe(df)
        self.original_stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "null_count": int(df.isnull().sum().sum()),
            "dtypes": {str(k): str(v) for k, v in df.dtypes.items()}
        }
        self._original_df = df.copy()

    def compare(self, new_df: pd.DataFrame) -> Dict:
        """Compare new data against original."""
        self.changes = []

        comparison = {
            "original": self.original_stats,
            "new": {
                "rows": len(new_df),
                "columns": len(new_df.columns),
                "null_count": int(new_df.isnull().sum().sum())
            },
            "changes": {
                "rows_added": 0,
                "rows_removed": 0,
                "rows_modified": 0,
                "columns_added": [],
                "columns_removed": [],
                "values_changed": 0
            }
        }

        # Column changes
        orig_cols = set(self.original_stats["column_names"])
        new_cols = set(new_df.columns.tolist())
        comparison["changes"]["columns_added"] = list(new_cols - orig_cols)
        comparison["changes"]["columns_removed"] = list(orig_cols - new_cols)

        # Row changes
        comparison["changes"]["rows_added"] = max(0, len(new_df) - self.original_stats["rows"])
        comparison["changes"]["rows_removed"] = max(0, self.original_stats["rows"] - len(new_df))

        # Value-level comparison (if same structure)
        if hasattr(self, '_original_df') and len(new_df) == len(self._original_df):
            common_cols = list(orig_cols & new_cols)
            for col in common_cols:
                if col in self._original_df.columns and col in new_df.columns:
                    try:
                        orig_vals = self._original_df[col].astype(str).fillna('')
                        new_vals = new_df[col].astype(str).fillna('')
                        changed = orig_vals != new_vals

                        for idx in changed[changed].index:
                            self.changes.append(DataChange(
                                row_index=int(idx),
                                column=str(col),
                                original_value=self._original_df.loc[idx, col],
                                new_value=new_df.loc[idx, col],
                                change_type="modified",
                                reason="Value changed during processing"
                            ))
                    except Exception:
                        pass

        comparison["changes"]["values_changed"] = len(self.changes)

        return comparison

    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        """Create hash of dataframe for change detection."""
        return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()

    def get_change_report(self) -> List[Dict]:
        """Get detailed change report."""
        return [c.to_dict() for c in self.changes[:1000]]  # First 1000 changes


class AssumptionTracker:
    """
    Tracks all assumptions made during data processing.
    """

    def __init__(self, team_id: str):
        self.team_id = team_id
        self.assumptions: List[Assumption] = []

    def add(self, category: str, description: str, reason: str,
            impact: str, confidence: str = "medium", affected_records: int = 0):
        """Add an assumption."""
        self.assumptions.append(Assumption(
            category=category,
            description=description,
            reason=reason,
            impact=impact,
            confidence=confidence,
            affected_records=affected_records
        ))

    def add_missing_value_assumption(self, column: str, fill_value: Any, count: int):
        """Track assumption about handling missing values."""
        self.add(
            category="missing_value",
            description=f"Filled {count} missing values in '{column}' with '{fill_value}'",
            reason="Missing values would cause processing errors",
            impact=f"Records may have incorrect {column} values",
            confidence="low",
            affected_records=count
        )

    def add_type_conversion_assumption(self, column: str, from_type: str, to_type: str, count: int):
        """Track assumption about type conversion."""
        self.add(
            category="type_conversion",
            description=f"Converted '{column}' from {from_type} to {to_type}",
            reason="Target template requires specific data type",
            impact="Some values may have lost precision or format",
            confidence="medium",
            affected_records=count
        )

    def add_format_assumption(self, column: str, format_applied: str, count: int):
        """Track assumption about format standardization."""
        self.add(
            category="format",
            description=f"Standardized format in '{column}' to {format_applied}",
            reason="Consistent formatting required for import",
            impact="Original formatting lost",
            confidence="high",
            affected_records=count
        )

    def add_duplicate_handling_assumption(self, strategy: str, count: int):
        """Track assumption about duplicate handling."""
        self.add(
            category="duplicates",
            description=f"Handled {count} duplicates using strategy: {strategy}",
            reason="Duplicates would cause import errors",
            impact="Some records may have been removed or merged",
            confidence="medium",
            affected_records=count
        )

    def add_mapping_assumption(self, source_col: str, target_col: str, mapping_type: str):
        """Track assumption about column mapping."""
        self.add(
            category="mapping",
            description=f"Mapped '{source_col}' to '{target_col}' ({mapping_type})",
            reason="Column names differ between source and template",
            impact="Data may be in wrong field if mapping is incorrect",
            confidence="medium" if mapping_type == "exact" else "low"
        )

    def add_business_rule_assumption(self, rule: str, action: str, count: int):
        """Track assumption about business rule application."""
        self.add(
            category="business_rule",
            description=f"Applied rule '{rule}': {action}",
            reason="Business logic requirement",
            impact="Data modified to meet business requirements",
            confidence="high",
            affected_records=count
        )

    def get_all(self) -> List[Dict]:
        """Get all assumptions as dictionaries."""
        return [a.to_dict() for a in self.assumptions]

    def get_by_category(self, category: str) -> List[Assumption]:
        """Get assumptions by category."""
        return [a for a in self.assumptions if a.category == category]

    def get_low_confidence(self) -> List[Assumption]:
        """Get all low-confidence assumptions that need review."""
        return [a for a in self.assumptions if a.confidence == "low"]

    def get_summary(self) -> Dict:
        """Get summary of all assumptions."""
        by_category = {}
        by_confidence = {"high": 0, "medium": 0, "low": 0}

        for a in self.assumptions:
            if a.category not in by_category:
                by_category[a.category] = 0
            by_category[a.category] += 1
            by_confidence[a.confidence] += 1

        return {
            "total": len(self.assumptions),
            "by_category": by_category,
            "by_confidence": by_confidence,
            "needs_review": len(self.get_low_confidence()),
            "total_affected_records": sum(a.affected_records for a in self.assumptions)
        }

    def display(self):
        """Display all assumptions."""
        print(f"\n{'='*70}")
        print(f"ASSUMPTIONS MADE BY {self.team_id}")
        print(f"{'='*70}")

        summary = self.get_summary()
        print(f"Total assumptions: {summary['total']}")
        print(f"Needs review (low confidence): {summary['needs_review']}")
        print(f"Total affected records: {summary['total_affected_records']}")

        if self.assumptions:
            print(f"\nDetailed Assumptions:")
            for i, a in enumerate(self.assumptions, 1):
                conf_icon = {"high": "[H]", "medium": "[M]", "low": "[L]"}[a.confidence]
                print(f"\n  {i}. {conf_icon} [{a.category.upper()}]")
                print(f"     {a.description}")
                print(f"     Reason: {a.reason}")
                print(f"     Impact: {a.impact}")
                if a.affected_records > 0:
                    print(f"     Affected: {a.affected_records} records")

        print(f"{'='*70}\n")
