"""
PreFlightValidator - Pre-Flight Column Validation and Mapping

Provides pre-flight analysis of uploaded data files to identify
column mappings, suggest fuzzy matches, and allow user corrections
before processing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


@dataclass
class ColumnMappingResult:
    """Result of column mapping analysis."""
    source_column: str
    mapped_to: Optional[str]
    confidence: float
    match_type: str  # 'exact', 'variation', 'fuzzy', 'unmapped'
    alternatives: List[Tuple[str, float]]  # (column_name, score)
    sample_values: List[Any]
    user_override: Optional[str] = None
    ignored: bool = False

    @property
    def status(self) -> str:
        """Get status for UI display."""
        if self.ignored:
            return 'ignored'
        if self.user_override:
            return 'corrected'
        if self.match_type == 'exact':
            return 'matched'
        if self.match_type in ('variation', 'fuzzy') and self.confidence >= 0.7:
            return 'review'
        return 'unmapped'

    @property
    def final_mapping(self) -> Optional[str]:
        """Get final mapping (user override or auto-mapped)."""
        if self.ignored:
            return None
        if self.user_override:
            return self.user_override
        if self.confidence >= 0.7:
            return self.mapped_to
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'source_column': self.source_column,
            'mapped_to': self.mapped_to,
            'confidence': self.confidence,
            'match_type': self.match_type,
            'alternatives': self.alternatives,
            'sample_values': [str(v) for v in self.sample_values[:5]],
            'user_override': self.user_override,
            'ignored': self.ignored,
            'status': self.status,
            'final_mapping': self.final_mapping
        }


@dataclass
class FileValidationResult:
    """Result of validating a single file."""
    file_path: Path
    file_name: str
    sheet_name: Optional[str]
    row_count: int
    column_count: int
    column_mappings: List[ColumnMappingResult]
    detected_strand: Optional[str]
    strand_confidence: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)

    @property
    def matched_columns(self) -> List[ColumnMappingResult]:
        """Get columns that were successfully matched."""
        return [c for c in self.column_mappings if c.status == 'matched']

    @property
    def review_columns(self) -> List[ColumnMappingResult]:
        """Get columns that need review (fuzzy matches)."""
        return [c for c in self.column_mappings if c.status == 'review']

    @property
    def unmapped_columns(self) -> List[ColumnMappingResult]:
        """Get columns that couldn't be mapped."""
        return [c for c in self.column_mappings if c.status == 'unmapped']

    @property
    def mapping_summary(self) -> Dict[str, int]:
        """Get summary counts by status."""
        statuses = [c.status for c in self.column_mappings]
        return {
            'matched': statuses.count('matched'),
            'review': statuses.count('review'),
            'unmapped': statuses.count('unmapped'),
            'ignored': statuses.count('ignored'),
            'corrected': statuses.count('corrected'),
            'total': len(self.column_mappings)
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'file_name': self.file_name,
            'sheet_name': self.sheet_name,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'detected_strand': self.detected_strand,
            'strand_confidence': self.strand_confidence,
            'mapping_summary': self.mapping_summary,
            'column_mappings': [c.to_dict() for c in self.column_mappings],
            'warnings': self.warnings,
            'errors': self.errors,
            'validated_at': self.validated_at.isoformat()
        }


class PreFlightValidator:
    """
    Pre-flight validation for data files.

    Analyzes uploaded files before processing to:
    1. Detect strand (S1, S2, S3)
    2. Map column names with confidence scores
    3. Identify fuzzy matches for user review
    4. Allow user corrections before processing
    """

    # Standard field names for fuzzy matching (by strand)
    STANDARD_FIELDS = {
        "S2": {
            # Staff identification
            "payroll_number": ["payroll", "payroll_number", "payroll no", "emp no", "employee number", "employee id", "staff id", "personnel number", "pay no", "pay number"],
            "surname": ["surname", "last name", "last_name", "family name", "lastname"],
            "forename": ["forename", "first name", "first_name", "given name", "firstname", "christian name"],
            "name": ["name", "full name", "fullname", "staff name", "employee name"],
            "job_title": ["job title", "job_title", "post", "position", "role", "job", "title", "designation", "post title"],
            "school_code": ["school", "school code", "school_code", "cost centre", "cost center", "cc", "location", "site", "establishment"],
            "weekly_hours": ["hours", "weekly hours", "weekly_hours", "contracted hours", "hpw", "hours per week", "ft hours", "full time hours", "weekly", "contract hours"],
            "fte": ["fte", "full time equivalent", "wte", "whole time equivalent"],
            "pay_scale": ["pay scale", "pay_scale", "scale", "payscale", "pay type", "scale type"],
            "scale_point": ["point", "scale point", "scp", "spine point", "current point", "pay point", "scale_point"],
            "annual_salary": ["salary", "annual salary", "actual salary", "gross salary", "pay", "annual pay", "fte salary"],
            "pension": ["pension", "pension scheme", "pension code", "superannuation"],
            "start_date": ["start date", "start_date", "service start", "hire date", "commencement", "date started", "contract start"],
            "date_of_birth": ["dob", "date of birth", "birth date", "birthdate"],
            "gender": ["gender", "sex", "m/f"],
            "ni_number": ["ni", "ni number", "national insurance", "nino"],
            "department": ["department", "dept", "section", "team", "division"],
            "contract_type": ["contract type", "contract_type", "employment type", "type"],
            "grade": ["grade", "pay grade", "band", "level"],
            "allowance_type": ["allowance", "tlr", "sen", "allowance type"],
            "staff_role_code": ["role code", "staff role", "job code", "post code"],
            "staff_role_group": ["role group", "srg", "category", "staff group", "job family"],
        },
        "S1": {
            "finance_code": ["finance code", "nominal", "nominal code", "account code", "gl code"],
            "school_code": ["school", "school code", "establishment", "site"],
            "department_code": ["department", "dept", "department code"],
            "fund_code": ["fund", "fund code", "funding"],
        },
        "S3": {
            "school_code": ["school", "school code", "establishment"],
            "pupil_count": ["pupils", "pupil count", "nos", "number on roll", "nor"],
        }
    }

    def __init__(self, inference_engine=None):
        """
        Initialize PreFlightValidator.

        Args:
            inference_engine: Optional InferenceEngine instance
        """
        self.inference_engine = inference_engine
        self._results: Dict[str, FileValidationResult] = {}
        self._corrections: Dict[str, Dict[str, str]] = {}

        # Try to get inference engine if not provided
        if self.inference_engine is None:
            try:
                from intelligence import InferenceEngine
                self.inference_engine = InferenceEngine()
            except ImportError:
                pass

    def validate_file(
        self,
        file_path: Path,
        sheet_name: Optional[str] = None,
        strand: Optional[str] = None
    ) -> FileValidationResult:
        """
        Validate a single file and analyze columns.

        Args:
            file_path: Path to the file
            sheet_name: Specific sheet to validate (for Excel files)
            strand: Force specific strand (auto-detect if None)

        Returns:
            FileValidationResult with column analysis
        """
        file_path = Path(file_path)

        # Read the file
        try:
            if file_path.suffix.lower() in ['.xlsx', '.xlsm', '.xls']:
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    xl = pd.ExcelFile(file_path)
                    # Use first sheet with data (skip empty/summary sheets)
                    sheet_name = None
                    for sn in xl.sheet_names:
                        try:
                            test_df = pd.read_excel(xl, sheet_name=sn, nrows=5)
                            if len(test_df.columns) >= 3 and len(test_df) >= 1:
                                sheet_name = sn
                                break
                        except:
                            continue
                    if not sheet_name:
                        sheet_name = xl.sheet_names[0]
                    df = pd.read_excel(xl, sheet_name=sheet_name)

                    # Skip rows if first row looks like a header/title (single value spanning columns)
                    if len(df) > 0:
                        first_row_nulls = df.iloc[0].isna().sum()
                        if first_row_nulls > len(df.columns) * 0.7:
                            # First row is mostly empty, might be a title row - try reading with header in row 1
                            df = pd.read_excel(xl, sheet_name=sheet_name, header=1)

            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                return self._create_error_result(file_path, f"Unsupported file type: {file_path.suffix}")
        except Exception as e:
            return self._create_error_result(file_path, f"Error reading file: {e}")

        # Detect strand if not provided
        detected_strand = strand
        strand_confidence = 1.0 if strand else 0.0

        if not strand and self.inference_engine:
            try:
                strand_result = self.inference_engine.infer_strand(
                    columns=list(df.columns)
                )
                detected_strand = strand_result.decision
                strand_confidence = strand_result.confidence
            except Exception:
                detected_strand = None
                strand_confidence = 0.0

        # Analyze each column (skip blank column names)
        column_mappings = []
        for col in df.columns:
            # Skip blank/empty column names and pandas auto-generated "Unnamed:" columns
            # Handle NaN, None, empty strings, and numeric NaN values
            if col is None or (isinstance(col, float) and pd.isna(col)):
                continue
            col_str = str(col).strip()
            if not col_str or col_str.lower().startswith("unnamed:") or col_str.lower() == "nan":
                continue
            mapping = self._analyze_column(col, df[col], detected_strand)
            column_mappings.append(mapping)

        # Generate warnings
        warnings = self._generate_warnings(column_mappings, df)

        result = FileValidationResult(
            file_path=file_path,
            file_name=file_path.name,
            sheet_name=sheet_name,
            row_count=len(df),
            column_count=len(column_mappings),  # Use filtered count
            column_mappings=column_mappings,
            detected_strand=detected_strand,
            strand_confidence=strand_confidence,
            warnings=warnings
        )

        # Cache result
        cache_key = f"{file_path.name}:{sheet_name or 'default'}"
        self._results[cache_key] = result

        return result

    def _analyze_column(
        self,
        column_name: str,
        column_data: pd.Series,
        strand: Optional[str]
    ) -> ColumnMappingResult:
        """Analyze a single column and find mapping."""
        # Get sample values (non-null)
        sample_values = column_data.dropna().head(5).tolist()

        # Default result
        mapped_to = None
        confidence = 0.0
        match_type = 'unmapped'
        alternatives = []

        # First try inference engine if available
        if self.inference_engine and strand:
            try:
                result = self.inference_engine.infer_column_mapping(
                    source_column=column_name,
                    strand=strand
                )
                mapped_to = result.decision
                confidence = result.confidence

                # Determine match type
                if confidence >= 0.95:
                    match_type = 'exact'
                elif confidence >= 0.85:
                    match_type = 'variation'
                elif confidence >= 0.7:
                    match_type = 'fuzzy'
                else:
                    match_type = 'unmapped'

                # Get alternatives
                for alt in result.alternatives[:5]:
                    if isinstance(alt, dict):
                        alt_col = alt.get('column', alt.get('target', ''))
                        alt_score = alt.get('score', alt.get('confidence', 0.0))
                        if alt_col:
                            alternatives.append((alt_col, alt_score))

            except Exception:
                pass

        # Fallback: Use simple fuzzy matching if inference engine didn't provide good results
        if confidence < 0.7 and strand:
            fuzzy_result = self._fuzzy_match_column(column_name, strand)
            if fuzzy_result:
                best_match, best_score, all_matches = fuzzy_result
                if best_score > confidence:
                    mapped_to = best_match
                    confidence = best_score
                    match_type = 'exact' if best_score >= 0.95 else 'variation' if best_score >= 0.85 else 'fuzzy'
                    # Add alternatives
                    alternatives = [(m, s) for m, s in all_matches if m != best_match][:5]

        return ColumnMappingResult(
            source_column=column_name,
            mapped_to=mapped_to if confidence >= 0.5 else None,
            confidence=confidence,
            match_type=match_type,
            alternatives=alternatives,
            sample_values=sample_values
        )

    def _fuzzy_match_column(self, column_name: str, strand: str) -> Optional[Tuple[str, float, List[Tuple[str, float]]]]:
        """
        Simple fuzzy matching against standard field names.

        Returns: (best_match, score, all_matches) or None
        """
        if strand not in self.STANDARD_FIELDS:
            return None

        # Normalize source column name
        source_clean = column_name.lower().strip()
        source_clean = source_clean.replace('_', ' ').replace('-', ' ')

        matches = []

        for target_field, variations in self.STANDARD_FIELDS[strand].items():
            best_variation_score = 0.0

            for variation in variations:
                variation_clean = variation.lower().strip()

                # Exact match
                if source_clean == variation_clean:
                    matches.append((target_field, 1.0))
                    best_variation_score = max(best_variation_score, 1.0)
                    continue

                # Contains match
                if variation_clean in source_clean or source_clean in variation_clean:
                    # Score based on length similarity
                    len_ratio = min(len(source_clean), len(variation_clean)) / max(len(source_clean), len(variation_clean))
                    score = 0.7 + (0.25 * len_ratio)
                    best_variation_score = max(best_variation_score, score)
                    continue

                # Word overlap
                source_words = set(source_clean.split())
                variation_words = set(variation_clean.split())
                if source_words & variation_words:
                    overlap = len(source_words & variation_words) / max(len(source_words), len(variation_words))
                    score = 0.5 + (0.4 * overlap)
                    best_variation_score = max(best_variation_score, score)

            if best_variation_score > 0:
                matches.append((target_field, best_variation_score))

        if not matches:
            return None

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        # Remove duplicates (keep highest score for each target)
        seen = set()
        unique_matches = []
        for target, score in matches:
            if target not in seen:
                seen.add(target)
                unique_matches.append((target, score))

        if unique_matches:
            return (unique_matches[0][0], unique_matches[0][1], unique_matches)
        return None

    def _generate_warnings(
        self,
        column_mappings: List[ColumnMappingResult],
        df: pd.DataFrame
    ) -> List[str]:
        """Generate warnings based on column analysis."""
        warnings = []

        # Check unmapped column ratio
        unmapped_count = sum(1 for c in column_mappings if c.status == 'unmapped')
        total_count = len(column_mappings)

        if unmapped_count > total_count * 0.5:
            warnings.append(
                f"High proportion of unmapped columns ({unmapped_count}/{total_count}). "
                "Consider checking file format."
            )

        # Check for empty columns
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            warnings.append(f"Empty columns detected: {', '.join(empty_cols[:5])}")

        # Check for duplicate columns
        if len(df.columns) != len(set(df.columns)):
            warnings.append("Duplicate column names detected")

        return warnings

    def _create_error_result(self, file_path: Path, error: str) -> FileValidationResult:
        """Create an error result for failed validation."""
        return FileValidationResult(
            file_path=file_path,
            file_name=file_path.name,
            sheet_name=None,
            row_count=0,
            column_count=0,
            column_mappings=[],
            detected_strand=None,
            strand_confidence=0.0,
            errors=[error]
        )

    def get_unmapped_columns(self, file_key: Optional[str] = None) -> List[ColumnMappingResult]:
        """Get all unmapped columns across validated files."""
        unmapped = []
        results = [self._results[file_key]] if file_key else self._results.values()

        for result in results:
            unmapped.extend(result.unmapped_columns)

        return unmapped

    def get_fuzzy_matches(self, file_key: Optional[str] = None) -> List[ColumnMappingResult]:
        """Get all fuzzy-matched columns that need review."""
        fuzzy = []
        results = [self._results[file_key]] if file_key else self._results.values()

        for result in results:
            fuzzy.extend(result.review_columns)

        return fuzzy

    def apply_user_corrections(self, corrections: Dict[str, str], file_key: str = None):
        """
        Apply user corrections to column mappings.

        Args:
            corrections: Dict mapping source_column -> corrected_standard_column
            file_key: Optional file key to limit corrections to
        """
        if file_key:
            self._corrections.setdefault(file_key, {}).update(corrections)

            if file_key in self._results:
                for mapping in self._results[file_key].column_mappings:
                    if mapping.source_column in corrections:
                        mapping.user_override = corrections[mapping.source_column]
        else:
            # Apply to all files
            for key, result in self._results.items():
                for mapping in result.column_mappings:
                    if mapping.source_column in corrections:
                        mapping.user_override = corrections[mapping.source_column]

    def ignore_column(self, source_column: str, file_key: str = None):
        """Mark a column as ignored (won't be processed)."""
        results = [self._results[file_key]] if file_key else self._results.values()

        for result in results:
            for mapping in result.column_mappings:
                if mapping.source_column == source_column:
                    mapping.ignored = True

    def get_final_mappings(self, file_key: str) -> Dict[str, str]:
        """
        Get final column mappings for a file after corrections.

        Returns:
            Dict mapping source_column -> standard_column
        """
        if file_key not in self._results:
            return {}

        result = self._results[file_key]
        mappings = {}

        for mapping in result.column_mappings:
            final = mapping.final_mapping
            if final:
                mappings[mapping.source_column] = final

        return mappings

    def get_sample_data(
        self,
        file_path: Path,
        column: str,
        n: int = 5,
        sheet_name: Optional[str] = None
    ) -> List[Any]:
        """Get sample data from a column."""
        try:
            if file_path.suffix.lower() in ['.xlsx', '.xlsm', '.xls']:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_csv(file_path)

            if column in df.columns:
                return df[column].dropna().head(n).tolist()
        except Exception:
            pass

        return []

    def validate_mapping_completeness(self, file_key: str, required_columns: List[str]) -> Dict:
        """
        Check if all required columns are mapped.

        Returns dict with 'complete' bool and 'missing' list.
        """
        if file_key not in self._results:
            return {'complete': False, 'missing': required_columns}

        mappings = self.get_final_mappings(file_key)
        mapped_standards = set(mappings.values())

        missing = [col for col in required_columns if col not in mapped_standards]

        return {
            'complete': len(missing) == 0,
            'missing': missing,
            'mapped': list(mapped_standards),
            'coverage': len(mapped_standards) / len(required_columns) if required_columns else 1.0
        }

    def get_all_results(self) -> Dict[str, FileValidationResult]:
        """Get all validation results."""
        return self._results.copy()

    def clear_results(self):
        """Clear all cached results and corrections."""
        self._results.clear()
        self._corrections.clear()

    def export_mappings(self, file_key: str = None) -> Dict:
        """Export all mappings for saving/reuse."""
        if file_key:
            if file_key not in self._results:
                return {}
            return {
                file_key: {
                    'mappings': self.get_final_mappings(file_key),
                    'corrections': self._corrections.get(file_key, {}),
                    'ignored': [
                        m.source_column
                        for m in self._results[file_key].column_mappings
                        if m.ignored
                    ]
                }
            }

        return {
            key: {
                'mappings': self.get_final_mappings(key),
                'corrections': self._corrections.get(key, {}),
                'ignored': [
                    m.source_column
                    for m in result.column_mappings
                    if m.ignored
                ]
            }
            for key, result in self._results.items()
        }

    def import_mappings(self, mapping_data: Dict):
        """Import previously saved mappings."""
        for file_key, data in mapping_data.items():
            if file_key in self._results:
                # Apply corrections
                corrections = data.get('corrections', {})
                self.apply_user_corrections(corrections, file_key)

                # Apply ignored columns
                for col in data.get('ignored', []):
                    self.ignore_column(col, file_key)


# Convenience function for quick validation
def validate_files(
    file_paths: List[Path],
    strand: Optional[str] = None
) -> Dict[str, FileValidationResult]:
    """
    Validate multiple files.

    Args:
        file_paths: List of file paths to validate
        strand: Optional strand to force

    Returns:
        Dict of file_key -> FileValidationResult
    """
    validator = PreFlightValidator()
    results = {}

    for path in file_paths:
        result = validator.validate_file(Path(path), strand=strand)
        key = f"{result.file_name}:{result.sheet_name or 'default'}"
        results[key] = result

    return results
