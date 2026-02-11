"""
Base Agent and Team Classes

Each agent handles a specific phase of data processing:
- Analyze: Understand data structure and identify issues
- Clean: Fix data quality issues
- Transform: Convert to target format
- Build: Output to template

All agents track:
- Validation results (multiple checks)
- Data comparison (original vs processed)
- Assumptions made during processing
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .validation import (
    DataValidator, DataComparator, AssumptionTracker,
    ValidationResult, ValidationSeverity
)


@dataclass
class CheckInReport:
    """Report generated after each phase for user review."""
    team_id: str
    team_name: str
    phase: str
    status: str  # 'success', 'warning', 'error', 'needs_input'
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validation_results: List[Dict] = field(default_factory=list)
    assumptions: List[Dict] = field(default_factory=list)
    data_comparison: Dict = field(default_factory=dict)
    data_preview: Optional[pd.DataFrame] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "phase": self.phase,
            "status": self.status,
            "summary": self.summary,
            "details": self.details,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "validation_results": self.validation_results,
            "assumptions": self.assumptions,
            "data_comparison": self.data_comparison,
            "timestamp": self.timestamp.isoformat()
        }

    def display(self):
        """Display report in console."""
        print(f"\n{'='*70}")
        print(f"CHECK-IN: {self.team_name} - {self.phase.upper()} Phase")
        print(f"{'='*70}")
        print(f"Status: {self.status.upper()}")
        print(f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nSummary:\n{self.summary}")

        if self.details:
            print(f"\n--- Details ---")
            for key, value in self.details.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in list(value.items())[:5]:
                        print(f"    - {k}: {v}")
                elif isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                else:
                    print(f"  {key}: {value}")

        # Display validation results
        if self.validation_results:
            print(f"\n--- Validation Results ({len(self.validation_results)} checks) ---")
            failed = [v for v in self.validation_results if not v.get('passed')]
            passed = [v for v in self.validation_results if v.get('passed')]
            print(f"  Passed: {len(passed)} | Failed: {len(failed)}")

            if failed:
                print(f"\n  Failed Checks:")
                for v in failed[:10]:
                    sev = v.get('severity', 'unknown').upper()
                    print(f"    [{sev}] {v.get('check_name')}: {v.get('message')}")

        # Display assumptions
        if self.assumptions:
            print(f"\n--- Assumptions Made ({len(self.assumptions)}) ---")
            low_conf = [a for a in self.assumptions if a.get('confidence') == 'low']
            if low_conf:
                print(f"  !! {len(low_conf)} LOW CONFIDENCE - NEEDS REVIEW !!")

            for a in self.assumptions[:10]:
                conf = a.get('confidence', '?')[0].upper()
                print(f"  [{conf}] {a.get('category')}: {a.get('description')}")

        # Display data comparison
        if self.data_comparison:
            print(f"\n--- Data Comparison (Original vs Processed) ---")
            orig = self.data_comparison.get('original', {})
            new = self.data_comparison.get('new', {})
            changes = self.data_comparison.get('changes', {})

            print(f"  Rows: {orig.get('rows', '?')} -> {new.get('rows', '?')}")
            print(f"  Columns: {orig.get('columns', '?')} -> {new.get('columns', '?')}")
            print(f"  Nulls: {orig.get('null_count', '?')} -> {new.get('null_count', '?')}")

            if changes:
                if changes.get('columns_added'):
                    print(f"  Columns added: {changes['columns_added']}")
                if changes.get('columns_removed'):
                    print(f"  Columns removed: {changes['columns_removed']}")
                if changes.get('values_changed'):
                    print(f"  Values changed: {changes['values_changed']}")

        if self.issues:
            print(f"\n--- Issues Found ({len(self.issues)}) ---")
            for issue in self.issues[:10]:
                print(f"  ! {issue}")

        if self.recommendations:
            print(f"\n--- Recommendations ---")
            for rec in self.recommendations:
                print(f"  > {rec}")

        if self.data_preview is not None and not self.data_preview.empty:
            print(f"\n--- Data Preview (first 5 rows) ---")
            print(self.data_preview.head().to_string())

        print(f"{'='*70}\n")


class BaseAgent(ABC):
    """Base class for all agents with validation and tracking."""

    def __init__(self, team_id: str, team_config: Dict, phase: str):
        self.team_id = team_id
        self.team_config = team_config
        self.phase = phase
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.issues: List[str] = []

        # Validation and tracking
        self.validator = DataValidator(team_id)
        self.comparator = DataComparator()
        self.assumptions = AssumptionTracker(team_id)

    @property
    def name(self) -> str:
        return f"{self.team_config['name']} - {self.phase.title()} Agent"

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """Execute the agent's task. Must be implemented by subclasses."""
        pass

    def create_report(self, status: str, summary: str,
                      details: Dict = None, recommendations: List[str] = None) -> CheckInReport:
        """Create a check-in report with validation and assumptions."""
        return CheckInReport(
            team_id=self.team_id,
            team_name=self.team_config['name'],
            phase=self.phase,
            status=status,
            summary=summary,
            details=details or {},
            issues=self.issues.copy(),
            recommendations=recommendations or [],
            validation_results=[r.to_dict() for r in self.validator.results],
            assumptions=self.assumptions.get_all(),
            data_comparison=self.metadata.get('comparison', {}),
            data_preview=self.data
        )

    def log(self, message: str):
        """Log a message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{self.team_id}:{self.phase}] {message}")


class AnalyzeAgent(BaseAgent):
    """Analyzes source data structure and identifies issues."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config, "analyze")

    def execute(self, input_data: Path) -> CheckInReport:
        """Analyze data files in the input directory."""
        self.log(f"Starting analysis of {input_data}")

        details = {
            "source_path": str(input_data),
            "files_found": 0,
            "total_records": 0,
            "columns_detected": [],
            "data_quality_score": 0
        }

        # Find all data files
        files = []
        if input_data.exists():
            for ext in ['*.xlsx', '*.xlsm', '*.csv', '*.json']:
                files.extend(input_data.glob(ext))
            files = [f for f in files if not f.name.startswith('~$')]

        details["files_found"] = len(files)

        if not files:
            self.issues.append(f"No data files found in {input_data}")
            self.assumptions.add(
                category="data_source",
                description="No source data files found",
                reason="Directory exists but contains no processable files",
                impact="Cannot proceed without source data",
                confidence="high"
            )
            return self.create_report(
                status="error",
                summary=f"No data files found in source directory",
                details=details,
                recommendations=[f"Add source data files (.xlsx, .xlsm, .csv) to {input_data}"]
            )

        # Analyze each file and collect all data
        all_dataframes = []
        file_summaries = []

        for file in files:
            try:
                if file.suffix in ['.xlsx', '.xlsm']:
                    xl = None
                    # Try openpyxl first
                    try:
                        xl = pd.ExcelFile(file, engine='openpyxl')
                    except Exception as e1:
                        self.log(f"  Warning: openpyxl failed for {file.name}, trying xlrd...")
                        try:
                            xl = pd.ExcelFile(file, engine='xlrd')
                        except Exception as e2:
                            # Try direct read_excel with sheet discovery
                            try:
                                xls_dict = pd.read_excel(file, sheet_name=None)
                                if xls_dict:
                                    for sheet_name, df in xls_dict.items():
                                        if df is not None and not df.empty and len(df.columns) > 1:
                                            all_dataframes.append(df)
                                            file_summaries.append({
                                                "file": file.name,
                                                "sheet": sheet_name,
                                                "rows": len(df),
                                                "columns": len(df.columns)
                                            })
                                continue
                            except Exception as e3:
                                self.issues.append(f"Error reading {file.name}: Failed with all engines - {e1} | {e2} | {e3}")
                                continue
                    
                    if xl is not None:
                        for sheet in xl.sheet_names:
                            df = pd.read_excel(file, sheet_name=sheet)
                            if not df.empty and len(df.columns) > 1:
                                all_dataframes.append(df)
                                file_summaries.append({
                                    "file": file.name,
                                    "sheet": sheet,
                                    "rows": len(df),
                                    "columns": len(df.columns)
                                })
                elif file.suffix == '.csv':
                    df = pd.read_csv(file)
                    all_dataframes.append(df)
                    file_summaries.append({
                        "file": file.name,
                        "rows": len(df),
                        "columns": len(df.columns)
                    })

            except Exception as e:
                self.issues.append(f"Error reading {file.name}: {str(e)}")

        # Combine for validation
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            details["total_records"] = len(combined_df)
            details["columns_detected"] = combined_df.columns.tolist()[:30]

            # Capture original state
            self.comparator.capture_original(combined_df)

            # Run validation
            self.validator.validate_all(combined_df)

            # Calculate quality score
            passed = len([r for r in self.validator.results if r.passed])
            total = len(self.validator.results)
            details["data_quality_score"] = round((passed / total) * 100, 1) if total > 0 else 0

            self.data = combined_df
            self.metadata = {
                "file_summaries": file_summaries,
                "original_data": combined_df.copy(),
                "validation_summary": self.validator.get_summary()
            }

        # Add assumptions about data structure
        if len(files) > 1:
            self.assumptions.add(
                category="data_source",
                description=f"Combined data from {len(files)} files into single dataset",
                reason="Multiple source files detected",
                impact="Records from different files are now merged",
                confidence="medium",
                affected_records=details["total_records"]
            )

        details["file_summaries"] = file_summaries

        # Generate recommendations
        recommendations = []
        validation_summary = self.validator.get_summary()

        if validation_summary.get('critical_issues'):
            recommendations.append("CRITICAL: Address critical issues before proceeding")
        if validation_summary.get('errors'):
            recommendations.append(f"Review {len(validation_summary['errors'])} error(s) flagged")
        if details["data_quality_score"] < 70:
            recommendations.append("Data quality score is low - consider additional cleanup")

        status = "success"
        if validation_summary.get('critical_issues'):
            status = "error"
        elif validation_summary.get('errors') or details["data_quality_score"] < 70:
            status = "warning"

        return self.create_report(
            status=status,
            summary=f"Analyzed {len(files)} files with {details['total_records']} records. Quality score: {details['data_quality_score']}%",
            details=details,
            recommendations=recommendations
        )


class CleanAgent(BaseAgent):
    """Cleans and normalizes data with full tracking."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config, "clean")

    def execute(self, input_data: Dict) -> CheckInReport:
        """Clean data based on analysis results."""
        self.log("Starting data cleanup")

        details = {
            "records_input": 0,
            "records_output": 0,
            "nulls_handled": 0,
            "duplicates_removed": 0,
            "formats_normalized": 0,
            "cleaning_actions": []
        }

        original_df = input_data.get("original_data")

        if original_df is None or (isinstance(original_df, pd.DataFrame) and original_df.empty):
            self.issues.append("No data to clean")
            return self.create_report(
                status="error",
                summary="Cannot clean data - no input data available",
                details=details
            )

        # Capture original state for comparison
        self.comparator.capture_original(original_df)
        details["records_input"] = len(original_df)

        # Work on a copy
        df = original_df.copy()

        # 1. Remove completely empty rows
        before = len(df)
        df = df.dropna(how='all')
        empty_rows_removed = before - len(df)
        if empty_rows_removed > 0:
            details["cleaning_actions"].append(f"Removed {empty_rows_removed} empty rows")
            self.assumptions.add(
                category="empty_rows",
                description=f"Removed {empty_rows_removed} completely empty rows",
                reason="Empty rows provide no data value",
                impact="Row count reduced",
                confidence="high",
                affected_records=empty_rows_removed
            )

        # 2. Handle column name issues
        unnamed_cols = [c for c in df.columns if str(c).startswith('Unnamed')]
        if unnamed_cols:
            # Try to detect if first row should be header
            df = df.rename(columns={c: f"Column_{i}" for i, c in enumerate(unnamed_cols)})
            self.assumptions.add(
                category="column_names",
                description=f"Renamed {len(unnamed_cols)} unnamed columns to Column_N",
                reason="Columns had no names (likely empty header cells)",
                impact="Column names are now generic",
                confidence="low",
                affected_records=len(df)
            )
            details["cleaning_actions"].append(f"Renamed {len(unnamed_cols)} unnamed columns")

        # 3. Handle duplicates
        before = len(df)
        duplicates = df.duplicated()
        dup_count = duplicates.sum()
        if dup_count > 0:
            df = df.drop_duplicates()
            details["duplicates_removed"] = dup_count
            details["cleaning_actions"].append(f"Removed {dup_count} duplicate rows")
            self.assumptions.add_duplicate_handling_assumption(
                strategy="keep_first",
                count=dup_count
            )

        # 4. Handle missing values
        null_counts = df.isnull().sum()
        for col in null_counts[null_counts > 0].index:
            null_count = null_counts[col]

            # Decide fill strategy based on column type
            if df[col].dtype in ['int64', 'float64']:
                # For numeric, note but don't fill automatically
                self.assumptions.add(
                    category="missing_value",
                    description=f"Column '{col}' has {null_count} missing numeric values",
                    reason="Missing values detected in numeric column",
                    impact="Missing values preserved - may need manual handling",
                    confidence="high",
                    affected_records=null_count
                )
            elif df[col].dtype == 'object':
                # For text, standardize empty strings
                empty_count = (df[col] == '').sum()
                if empty_count > 0:
                    df[col] = df[col].replace('', np.nan)
                    details["cleaning_actions"].append(f"Standardized {empty_count} empty strings in {col}")

            details["nulls_handled"] += null_count

        # 5. Normalize text columns
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            # Strip whitespace
            original = df[col].copy()
            df[col] = df[col].astype(str).str.strip()

            # Track changes
            changed = (df[col] != original.astype(str)).sum()
            if changed > 0:
                details["formats_normalized"] += 1
                self.assumptions.add_format_assumption(
                    column=col,
                    format_applied="stripped whitespace",
                    count=changed
                )

        # 6. Standardize date formats
        for col in df.columns:
            if 'date' in str(col).lower() or 'dob' in str(col).lower():
                try:
                    original = df[col].copy()
                    df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                    converted = df[col].notna().sum() - original.notna().sum()

                    if converted != 0:
                        self.assumptions.add_type_conversion_assumption(
                            column=col,
                            from_type="mixed",
                            to_type="datetime",
                            count=abs(converted)
                        )
                except Exception:
                    pass

        details["records_output"] = len(df)

        # Compare with original
        comparison = self.comparator.compare(df)
        self.metadata["comparison"] = comparison

        # Run validation on cleaned data
        self.validator.validate_all(df)

        self.data = df
        self.metadata.update({
            "cleaned_data": df,
            "original_data": original_df,
            "comparison": comparison
        })

        # Generate recommendations
        recommendations = []
        low_conf = self.assumptions.get_low_confidence()
        if low_conf:
            recommendations.append(f"Review {len(low_conf)} low-confidence assumptions")

        if details["nulls_handled"] > 100:
            recommendations.append("Many null values found - consider data quality review")

        status = "success" if not self.issues else "warning"
        if len(low_conf) > 5:
            status = "warning"

        return self.create_report(
            status=status,
            summary=f"Cleaned {details['records_input']} -> {details['records_output']} records. {len(self.assumptions.assumptions)} assumptions made.",
            details=details,
            recommendations=recommendations
        )


class TransformAgent(BaseAgent):
    """Transforms data to match template requirements with full tracking."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config, "transform")

    def execute(self, input_data: Dict) -> CheckInReport:
        """Transform cleaned data to template format."""
        self.log("Starting data transformation")

        details = {
            "records_input": 0,
            "records_output": 0,
            "columns_mapped": 0,
            "columns_created": 0,
            "columns_dropped": 0,
            "transform_actions": [],
            "mapping_report": []
        }

        cleaned_data = input_data.get("cleaned_data")
        original_data = input_data.get("original_data")

        if cleaned_data is None or (isinstance(cleaned_data, pd.DataFrame) and cleaned_data.empty):
            self.issues.append("No cleaned data to transform")
            return self.create_report(
                status="error",
                summary="No data available for transformation",
                details=details
            )

        # Capture state for comparison
        self.comparator.capture_original(cleaned_data)
        details["records_input"] = len(cleaned_data)

        # Work on a copy
        df = cleaned_data.copy()

        # Get expected template columns
        template_columns = self._get_template_columns()

        # 1. Normalize column names
        original_columns = df.columns.tolist()
        df.columns = [str(c).strip().lower().replace(' ', '_').replace('/', '_') for c in df.columns]
        normalized_columns = df.columns.tolist()

        # Track column name changes
        for orig, norm in zip(original_columns, normalized_columns):
            if str(orig) != norm:
                self.assumptions.add_mapping_assumption(
                    source_col=str(orig),
                    target_col=norm,
                    mapping_type="normalized"
                )
                details["mapping_report"].append({
                    "original": str(orig),
                    "normalized": norm,
                    "type": "name_normalization"
                })

        details["columns_mapped"] = len(df.columns)

        # 2. Map to template columns
        column_mapping = self._create_column_mapping(df.columns.tolist(), template_columns)

        for source, target in column_mapping.items():
            if source in df.columns and source != target:
                df = df.rename(columns={source: target})
                self.assumptions.add_mapping_assumption(
                    source_col=source,
                    target_col=target,
                    mapping_type="template_mapping"
                )
                details["mapping_report"].append({
                    "source": source,
                    "target": target,
                    "type": "template_mapping"
                })

        # 3. Add missing required columns
        required_cols = self._get_required_columns()
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
                details["columns_created"] += 1
                self.assumptions.add(
                    category="missing_column",
                    description=f"Created empty column '{col}'",
                    reason=f"Required by template but not in source data",
                    impact="Column will need manual population",
                    confidence="high",
                    affected_records=len(df)
                )
                details["transform_actions"].append(f"Created missing column: {col}")

        # 4. Validate data types for template
        type_requirements = self._get_type_requirements()
        for col, req_type in type_requirements.items():
            if col in df.columns:
                try:
                    original_dtype = str(df[col].dtype)
                    if req_type == 'numeric':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif req_type == 'date':
                        df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                    elif req_type == 'text':
                        df[col] = df[col].astype(str)

                    new_dtype = str(df[col].dtype)
                    if original_dtype != new_dtype:
                        self.assumptions.add_type_conversion_assumption(
                            column=col,
                            from_type=original_dtype,
                            to_type=new_dtype,
                            count=len(df)
                        )
                except Exception as e:
                    self.issues.append(f"Failed to convert {col} to {req_type}: {e}")

        # 5. Apply team-specific transformations
        df = self._apply_team_transformations(df)

        details["records_output"] = len(df)

        # Compare with input
        comparison = self.comparator.compare(df)
        self.metadata["comparison"] = comparison

        # Run validation
        self.validator.validate_all(df)

        self.data = df
        self.metadata.update({
            "transformed_data": df,
            "original_data": original_data,
            "column_mapping": column_mapping,
            "comparison": comparison
        })

        # Generate recommendations
        recommendations = []
        if details["columns_created"] > 0:
            recommendations.append(f"Review {details['columns_created']} newly created (empty) columns")

        low_conf = self.assumptions.get_low_confidence()
        if low_conf:
            recommendations.append(f"Review {len(low_conf)} low-confidence assumptions")

        validation_summary = self.validator.get_summary()
        if validation_summary.get('errors'):
            recommendations.append(f"Address {len(validation_summary['errors'])} validation errors")

        status = "success"
        if self.issues or validation_summary.get('errors'):
            status = "warning"

        return self.create_report(
            status=status,
            summary=f"Transformed {details['records_input']} records. Mapped {details['columns_mapped']} columns. {len(self.assumptions.assumptions)} assumptions.",
            details=details,
            recommendations=recommendations
        )

    def _get_template_columns(self) -> List[str]:
        """Get expected columns from template (team-specific)."""
        templates = {
            "S1": ["code", "title", "type", "parent_code", "active", "grouping_code"],
            "S2": ["payroll_number", "last_name", "first_name", "date_of_birth", "gender",
                   "service_start_date", "school_code", "job_title", "finance_code",
                   "weekly_hours", "weekly_fte", "annual_salary", "contract_type", "pension_scheme"],
            "S3": ["fund_code", "activity_code", "ledger_code", "amount", "period",
                   "scenario", "pupil_numbers", "funding_rate"]
        }
        return templates.get(self.team_id, [])

    def _get_required_columns(self) -> List[str]:
        """Get required columns (team-specific)."""
        required = {
            "S1": ["code", "title"],
            "S2": ["payroll_number", "last_name"],
            "S3": ["fund_code", "amount"]
        }
        return required.get(self.team_id, [])

    def _get_type_requirements(self) -> Dict[str, str]:
        """Get column type requirements."""
        types = {
            "S1": {},
            "S2": {
                "date_of_birth": "date",
                "service_start_date": "date",
                "weekly_hours": "numeric",
                "weekly_fte": "numeric",
                "annual_salary": "numeric"
            },
            "S3": {
                "amount": "numeric",
                "pupil_numbers": "numeric",
                "funding_rate": "numeric"
            }
        }
        return types.get(self.team_id, {})

    def _create_column_mapping(self, source_cols: List[str], target_cols: List[str]) -> Dict[str, str]:
        """Create intelligent column mapping."""
        mapping = {}

        # Common aliases
        aliases = {
            "payroll_number": ["payroll", "payroll_no", "employee_id", "staff_id", "unique_payroll"],
            "last_name": ["surname", "family_name", "lastname"],
            "first_name": ["forename", "given_name", "firstname"],
            "date_of_birth": ["dob", "birth_date", "birthdate"],
            "annual_salary": ["salary", "annual_pay", "fte_salary"],
            "weekly_hours": ["hours", "contracted_hours", "weekly_hrs"],
            "school_code": ["school", "location", "work_location"],
            "finance_code": ["nominal", "cost_code", "account_code"],
            "fund_code": ["fund", "funding_code"],
            "amount": ["value", "budget", "total"]
        }

        for target in target_cols:
            target_lower = target.lower()

            # Direct match
            if target_lower in source_cols:
                mapping[target_lower] = target
                continue

            # Alias match
            if target_lower in aliases:
                for alias in aliases[target_lower]:
                    if alias in source_cols:
                        mapping[alias] = target
                        break

        return mapping

    def _apply_team_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply team-specific transformations."""
        if self.team_id == "S2":
            # Staff team: ensure proper name formatting
            for col in ['last_name', 'first_name']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.title()
                    self.assumptions.add_format_assumption(
                        column=col,
                        format_applied="title_case",
                        count=len(df)
                    )

        return df


class BuildAgent(BaseAgent):
    """Builds data into template format with full tracking."""

    def __init__(self, team_id: str, team_config: Dict, template_path: Path):
        super().__init__(team_id, team_config, "build")
        self.template_path = template_path

    def execute(self, input_data: Dict) -> CheckInReport:
        """Build transformed data into template format."""
        self.log(f"Building data into template: {self.template_path.name}")

        details = {
            "template": self.template_path.name,
            "records_written": 0,
            "sheets_populated": 0,
            "output_path": "",
            "build_actions": []
        }

        transformed_data = input_data.get("transformed_data")
        original_data = input_data.get("original_data")

        if transformed_data is None or (isinstance(transformed_data, pd.DataFrame) and transformed_data.empty):
            self.issues.append("No transformed data to build")
            return self.create_report(
                status="error",
                summary="No data available for template building",
                details=details
            )

        # Capture state
        self.comparator.capture_original(transformed_data)

        # Generate output path
        from config.settings import REPORTS_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = REPORTS_DIR / f"{self.team_id}_output_{timestamp}.xlsx"
        output_path.parent.mkdir(exist_ok=True)

        try:
            # Write output with multiple sheets
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main data sheet
                transformed_data.to_excel(writer, sheet_name='Data', index=False)
                details["records_written"] = len(transformed_data)
                details["sheets_populated"] += 1
                details["build_actions"].append(f"Wrote {len(transformed_data)} records to Data sheet")

                # Validation summary sheet
                validation_df = self._create_validation_summary()
                validation_df.to_excel(writer, sheet_name='Validation', index=False)
                details["sheets_populated"] += 1

                # Assumptions sheet
                assumptions_df = self._create_assumptions_summary()
                assumptions_df.to_excel(writer, sheet_name='Assumptions', index=False)
                details["sheets_populated"] += 1

                # Comparison sheet
                comparison_df = self._create_comparison_summary(original_data, transformed_data)
                comparison_df.to_excel(writer, sheet_name='Data_Comparison', index=False)
                details["sheets_populated"] += 1

            details["output_path"] = str(output_path)
            self.data = transformed_data

        except Exception as e:
            self.issues.append(f"Error writing output: {str(e)}")
            return self.create_report(
                status="error",
                summary=f"Failed to write output: {str(e)}",
                details=details
            )

        # Final comparison
        comparison = self.comparator.compare(transformed_data)
        self.metadata["comparison"] = comparison
        self.metadata["output_path"] = str(output_path)

        recommendations = [
            "Review output file before importing to budgeting software",
            "Check 'Assumptions' sheet for all decisions made during processing",
            "Verify 'Data_Comparison' sheet for changes from original data"
        ]

        if self.assumptions.get_low_confidence():
            recommendations.insert(0, "IMPORTANT: Review low-confidence assumptions before proceeding")

        return self.create_report(
            status="success" if not self.issues else "warning",
            summary=f"Built {details['records_written']} records into {details['sheets_populated']} sheets. Output: {output_path.name}",
            details=details,
            recommendations=recommendations
        )

    def _create_validation_summary(self) -> pd.DataFrame:
        """Create validation summary dataframe."""
        rows = []
        for r in self.validator.results:
            rows.append({
                "Check": r.check_name,
                "Passed": "Yes" if r.passed else "No",
                "Severity": r.severity.value,
                "Message": r.message,
                "Affected Columns": ", ".join(r.affected_columns[:5]) if r.affected_columns else ""
            })
        return pd.DataFrame(rows) if rows else pd.DataFrame({"Message": ["No validation checks run"]})

    def _create_assumptions_summary(self) -> pd.DataFrame:
        """Create assumptions summary dataframe."""
        rows = []
        for a in self.assumptions.assumptions:
            rows.append({
                "Category": a.category,
                "Confidence": a.confidence.upper(),
                "Description": a.description,
                "Reason": a.reason,
                "Impact": a.impact,
                "Affected Records": a.affected_records
            })
        return pd.DataFrame(rows) if rows else pd.DataFrame({"Message": ["No assumptions made"]})

    def _create_comparison_summary(self, original: pd.DataFrame, processed: pd.DataFrame) -> pd.DataFrame:
        """Create data comparison summary."""
        rows = [
            {"Metric": "Original Rows", "Value": len(original) if original is not None else 0},
            {"Metric": "Processed Rows", "Value": len(processed)},
            {"Metric": "Original Columns", "Value": len(original.columns) if original is not None else 0},
            {"Metric": "Processed Columns", "Value": len(processed.columns)},
            {"Metric": "Original Nulls", "Value": int(original.isnull().sum().sum()) if original is not None else 0},
            {"Metric": "Processed Nulls", "Value": int(processed.isnull().sum().sum())}
        ]
        return pd.DataFrame(rows)


class QualityCheckAgent(BaseAgent):
    """Quality assurance agent that reviews all processing and validates output."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config, "quality_check")
        self.quality_score: float = 0.0
        self.quality_checks: List[Dict] = []

    def execute(self, input_data: Dict) -> CheckInReport:
        """Perform comprehensive quality check on all processed data."""
        self.log("Starting quality assurance review")

        details = {
            "quality_score": 0,
            "checks_passed": 0,
            "checks_failed": 0,
            "critical_issues": [],
            "warnings": [],
            "data_integrity": {},
            "assumption_review": {},
            "standards_compliance": {}
        }

        # Get all phase data for review
        original_data = input_data.get("original_data")
        transformed_data = input_data.get("transformed_data")
        output_path = input_data.get("output_path", "")

        if transformed_data is None or (isinstance(transformed_data, pd.DataFrame) and transformed_data.empty):
            self.issues.append("No data available for quality check")
            return self.create_report(
                status="error",
                summary="Quality check failed - no data to review",
                details=details
            )

        # Capture state
        self.comparator.capture_original(transformed_data)
        self.data = transformed_data

        # 1. DATA INTEGRITY CHECKS
        integrity_results = self._check_data_integrity(original_data, transformed_data)
        details["data_integrity"] = integrity_results
        self.quality_checks.extend(integrity_results.get("checks", []))

        # 2. ASSUMPTION REVIEW
        assumption_results = self._review_assumptions(input_data)
        details["assumption_review"] = assumption_results

        # 3. STANDARDS COMPLIANCE
        standards_results = self._check_standards_compliance(transformed_data)
        details["standards_compliance"] = standards_results
        self.quality_checks.extend(standards_results.get("checks", []))

        # 4. DATA QUALITY VALIDATION
        quality_results = self._validate_data_quality(transformed_data)
        self.quality_checks.extend(quality_results)

        # 5. SECURITY & SENSITIVITY CHECK
        security_results = self._check_security_concerns(transformed_data)
        self.quality_checks.extend(security_results)

        # 6. OUTPUT VALIDATION
        if output_path:
            output_results = self._validate_output(output_path)
            self.quality_checks.extend(output_results)

        # Calculate quality score
        passed = sum(1 for c in self.quality_checks if c.get("passed", False))
        total = len(self.quality_checks)
        self.quality_score = round((passed / total) * 100, 1) if total > 0 else 0

        details["quality_score"] = self.quality_score
        details["checks_passed"] = passed
        details["checks_failed"] = total - passed

        # Categorize issues
        for check in self.quality_checks:
            if not check.get("passed", False):
                if check.get("severity") == "critical":
                    details["critical_issues"].append(check.get("message", "Unknown issue"))
                else:
                    details["warnings"].append(check.get("message", "Unknown issue"))

        # Determine status
        if details["critical_issues"]:
            status = "error"
        elif self.quality_score < 70:
            status = "warning"
        elif details["warnings"]:
            status = "warning"
        else:
            status = "success"

        # Generate recommendations
        recommendations = self._generate_recommendations(details)

        return self.create_report(
            status=status,
            summary=f"Quality Score: {self.quality_score}%. Passed {passed}/{total} checks. {len(details['critical_issues'])} critical issues.",
            details=details,
            recommendations=recommendations
        )

    def _check_data_integrity(self, original: pd.DataFrame, processed: pd.DataFrame) -> Dict:
        """Check data integrity between original and processed data."""
        results = {
            "row_preservation": {},
            "key_field_integrity": {},
            "data_loss_analysis": {},
            "checks": []
        }

        if original is None:
            return results

        # Row count analysis
        original_rows = len(original)
        processed_rows = len(processed)
        row_diff = original_rows - processed_rows
        row_loss_pct = (row_diff / original_rows * 100) if original_rows > 0 else 0

        results["row_preservation"] = {
            "original": original_rows,
            "processed": processed_rows,
            "difference": row_diff,
            "loss_percentage": round(row_loss_pct, 2)
        }

        # Check: Excessive data loss
        if row_loss_pct > 20:
            results["checks"].append({
                "name": "Data Loss Check",
                "passed": False,
                "severity": "critical",
                "message": f"Excessive data loss: {row_loss_pct:.1f}% of records removed ({row_diff} rows)"
            })
            self.issues.append(f"Data loss exceeds 20%: {row_loss_pct:.1f}%")
        elif row_loss_pct > 5:
            results["checks"].append({
                "name": "Data Loss Check",
                "passed": True,
                "severity": "warning",
                "message": f"Moderate data reduction: {row_loss_pct:.1f}% ({row_diff} rows)"
            })
        else:
            results["checks"].append({
                "name": "Data Loss Check",
                "passed": True,
                "severity": "info",
                "message": f"Data preservation OK: {row_loss_pct:.1f}% change"
            })

        # Column integrity
        orig_cols = set(str(c).lower() for c in original.columns)
        proc_cols = set(str(c).lower() for c in processed.columns)
        missing_cols = orig_cols - proc_cols

        if missing_cols:
            results["checks"].append({
                "name": "Column Integrity",
                "passed": True,  # Columns can be intentionally removed
                "severity": "info",
                "message": f"{len(missing_cols)} original columns not in output: {list(missing_cols)[:5]}"
            })

        # Null value analysis
        orig_nulls = original.isnull().sum().sum() if original is not None else 0
        proc_nulls = processed.isnull().sum().sum()

        results["data_loss_analysis"]["null_values"] = {
            "original": int(orig_nulls),
            "processed": int(proc_nulls),
            "change": int(proc_nulls - orig_nulls)
        }

        return results

    def _review_assumptions(self, input_data: Dict) -> Dict:
        """Review all assumptions made during processing."""
        results = {
            "total_assumptions": 0,
            "by_confidence": {"high": 0, "medium": 0, "low": 0},
            "high_risk_assumptions": [],
            "checks": []
        }

        # Collect assumptions from all phases (they're tracked in metadata)
        all_assumptions = []

        # The assumptions are typically collected throughout the pipeline
        if hasattr(self, 'assumptions') and self.assumptions:
            all_assumptions = self.assumptions.get_all()

        results["total_assumptions"] = len(all_assumptions)

        for assumption in all_assumptions:
            conf = assumption.get("confidence", "medium")
            if conf in results["by_confidence"]:
                results["by_confidence"][conf] += 1

            if conf == "low":
                results["high_risk_assumptions"].append({
                    "category": assumption.get("category"),
                    "description": assumption.get("description"),
                    "impact": assumption.get("impact")
                })

        # Check: Too many low-confidence assumptions
        low_count = results["by_confidence"]["low"]
        if low_count > 10:
            results["checks"].append({
                "name": "Assumption Risk",
                "passed": False,
                "severity": "critical",
                "message": f"{low_count} low-confidence assumptions require manual review"
            })
        elif low_count > 3:
            results["checks"].append({
                "name": "Assumption Risk",
                "passed": True,
                "severity": "warning",
                "message": f"{low_count} low-confidence assumptions should be reviewed"
            })
        else:
            results["checks"].append({
                "name": "Assumption Risk",
                "passed": True,
                "severity": "info",
                "message": f"Assumption confidence levels acceptable"
            })

        return results

    def _check_standards_compliance(self, df: pd.DataFrame) -> Dict:
        """Check compliance with data standards."""
        results = {
            "naming_conventions": {},
            "data_types": {},
            "format_compliance": {},
            "checks": []
        }

        # Column naming conventions
        non_standard_cols = []
        for col in df.columns:
            col_str = str(col)
            # Check for proper naming (snake_case, no spaces, lowercase)
            if ' ' in col_str or col_str != col_str.lower() or col_str.startswith('Unnamed'):
                non_standard_cols.append(col_str)

        if non_standard_cols:
            results["checks"].append({
                "name": "Column Naming Standards",
                "passed": False,
                "severity": "warning",
                "message": f"{len(non_standard_cols)} columns don't follow naming conventions: {non_standard_cols[:5]}"
            })
        else:
            results["checks"].append({
                "name": "Column Naming Standards",
                "passed": True,
                "severity": "info",
                "message": "All columns follow naming conventions"
            })

        # Check for required type consistency
        type_issues = []
        for col in df.columns:
            col_lower = str(col).lower()
            # Date columns should be datetime
            if 'date' in col_lower or 'dob' in col_lower:
                if df[col].dtype == 'object':
                    type_issues.append(f"{col} should be datetime, is object")
            # Amount/salary columns should be numeric
            if any(x in col_lower for x in ['amount', 'salary', 'fte', 'hours']):
                if df[col].dtype == 'object':
                    type_issues.append(f"{col} should be numeric, is object")

        if type_issues:
            results["checks"].append({
                "name": "Data Type Standards",
                "passed": False,
                "severity": "warning",
                "message": f"{len(type_issues)} type issues: {type_issues[:3]}"
            })
        else:
            results["checks"].append({
                "name": "Data Type Standards",
                "passed": True,
                "severity": "info",
                "message": "Data types are appropriate"
            })

        return results

    def _validate_data_quality(self, df: pd.DataFrame) -> List[Dict]:
        """Validate overall data quality."""
        checks = []

        # Check for empty dataframe
        if df.empty:
            checks.append({
                "name": "Data Presence",
                "passed": False,
                "severity": "critical",
                "message": "Output dataframe is empty"
            })
            return checks

        checks.append({
            "name": "Data Presence",
            "passed": True,
            "severity": "info",
            "message": f"Output contains {len(df)} records"
        })

        # Check null ratio
        total_cells = df.size
        null_cells = df.isnull().sum().sum()
        null_ratio = (null_cells / total_cells * 100) if total_cells > 0 else 0

        if null_ratio > 30:
            checks.append({
                "name": "Null Value Ratio",
                "passed": False,
                "severity": "warning",
                "message": f"High null ratio: {null_ratio:.1f}% of cells are empty"
            })
        else:
            checks.append({
                "name": "Null Value Ratio",
                "passed": True,
                "severity": "info",
                "message": f"Null ratio acceptable: {null_ratio:.1f}%"
            })

        # Check for duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            checks.append({
                "name": "Duplicate Rows",
                "passed": False,
                "severity": "warning",
                "message": f"{dup_count} duplicate rows found in output"
            })
        else:
            checks.append({
                "name": "Duplicate Rows",
                "passed": True,
                "severity": "info",
                "message": "No duplicate rows"
            })

        return checks

    def _check_security_concerns(self, df: pd.DataFrame) -> List[Dict]:
        """Check for potential security or sensitivity issues."""
        checks = []

        # Check for potential PII columns that might need protection
        sensitive_patterns = ['ssn', 'social', 'password', 'secret', 'token', 'key', 'bank', 'account_number']
        sensitive_found = []

        for col in df.columns:
            col_lower = str(col).lower()
            for pattern in sensitive_patterns:
                if pattern in col_lower:
                    sensitive_found.append(col)

        if sensitive_found:
            checks.append({
                "name": "Sensitive Data Check",
                "passed": True,  # Not a failure, just awareness
                "severity": "warning",
                "message": f"Potentially sensitive columns detected: {sensitive_found}"
            })
        else:
            checks.append({
                "name": "Sensitive Data Check",
                "passed": True,
                "severity": "info",
                "message": "No obvious sensitive data patterns detected"
            })

        return checks

    def _validate_output(self, output_path: str) -> List[Dict]:
        """Validate the output file."""
        checks = []

        output_file = Path(output_path)
        if output_file.exists():
            file_size = output_file.stat().st_size
            checks.append({
                "name": "Output File Created",
                "passed": True,
                "severity": "info",
                "message": f"Output file created: {output_file.name} ({file_size:,} bytes)"
            })

            # Check file is not suspiciously small
            if file_size < 1000:
                checks.append({
                    "name": "Output File Size",
                    "passed": False,
                    "severity": "warning",
                    "message": f"Output file seems very small ({file_size} bytes) - verify contents"
                })
        else:
            checks.append({
                "name": "Output File Created",
                "passed": False,
                "severity": "critical",
                "message": f"Output file not found at {output_path}"
            })

        return checks

    def _generate_recommendations(self, details: Dict) -> List[str]:
        """Generate recommendations based on quality check results."""
        recommendations = []

        if details["critical_issues"]:
            recommendations.append("CRITICAL: Address critical issues before using this data")

        if details["quality_score"] < 70:
            recommendations.append("Quality score is below threshold - manual review strongly recommended")

        if details["assumption_review"].get("by_confidence", {}).get("low", 0) > 0:
            low_count = details["assumption_review"]["by_confidence"]["low"]
            recommendations.append(f"Review {low_count} low-confidence assumptions in the Assumptions sheet")

        row_loss = details["data_integrity"].get("row_preservation", {}).get("loss_percentage", 0)
        if row_loss > 10:
            recommendations.append(f"Verify {row_loss:.1f}% data reduction is expected")

        if not details["critical_issues"] and details["quality_score"] >= 80:
            recommendations.append("Data passed quality checks - ready for review and import")

        return recommendations


class AgentTeam:
    """A team of agents that process data through all phases."""

    def __init__(self, team_id: str, team_config: Dict, template_path: Path):
        self.team_id = team_id
        self.team_config = team_config
        self.template_path = template_path

        # Create agents for each phase
        self.agents = {
            "analyze": AnalyzeAgent(team_id, team_config),
            "clean": CleanAgent(team_id, team_config),
            "transform": TransformAgent(team_id, team_config),
            "build": BuildAgent(team_id, team_config, template_path),
            "quality_check": QualityCheckAgent(team_id, team_config)
        }

        self.reports: List[CheckInReport] = []
        self.current_phase: str = ""
        self.phase_data: Dict[str, Any] = {}
        self.all_assumptions: List[Dict] = []

    @property
    def name(self) -> str:
        return self.team_config['name']

    def run_phase(self, phase: str, input_data: Any = None) -> CheckInReport:
        """Run a single phase and return the report."""
        self.current_phase = phase
        agent = self.agents[phase]

        # Use previous phase output if no input provided
        if input_data is None:
            input_data = self.phase_data.get(phase, self.team_config['data_dir'])

        report = agent.execute(input_data)
        self.reports.append(report)

        # Store phase output for next phase
        self.phase_data[phase] = agent.metadata

        # Collect assumptions
        self.all_assumptions.extend(report.assumptions)

        return report

    def run_all(self, check_in_callback=None) -> List[CheckInReport]:
        """Run all phases with optional check-in callback."""
        phases = ["analyze", "clean", "transform", "build", "quality_check"]

        for phase in phases:
            # Determine input for this phase
            if phase == "analyze":
                input_data = self.team_config['data_dir']
            elif phase == "quality_check":
                # QA agent gets all accumulated data from previous phases
                input_data = self.phase_data.get("build", {})
            else:
                prev_phase = phases[phases.index(phase) - 1]
                input_data = self.phase_data.get(prev_phase, {})

            report = self.run_phase(phase, input_data)

            # Call check-in callback if provided
            if check_in_callback:
                check_in_callback(report)

        return self.reports

    def get_all_assumptions(self) -> List[Dict]:
        """Get all assumptions from all phases."""
        return self.all_assumptions
