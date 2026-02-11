"""
S2 Specialist Agent - Deep Analysis & Complete Template Builder

An upskilled agent that thoroughly analyzes customer data and builds
ALL template sheets with no data left behind.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import warnings
warnings.filterwarnings('ignore')

from .finished_workbook_patterns import (
    S2_STAFF_ROLE_GROUP_PATTERNS,
    S2_PAY_SCALE_PATTERNS,
    S2_CONTRACT_PATTERNS,
    S2_EQWP_PATTERNS,
    S2_PENSION_PATTERNS,
    get_srg_for_role,
    get_finance_codes_for_srg,
)


@dataclass
class AnalysisReport:
    """Detailed analysis report of customer data."""
    file_name: str
    sheet_name: str
    row_count: int
    column_count: int
    columns_found: List[str]
    columns_mapped: Dict[str, str]  # original -> standard
    data_quality: Dict[str, Any]
    sample_data: Dict[str, List]
    issues: List[str]
    recommendations: List[str]


@dataclass
class ExtractedPayScale:
    """Extracted pay scale data."""
    code: str
    title: str
    scale_type: str  # teaching, support, leadership
    london_weighting: str
    increment_date: str
    increase_date: str
    increase_percentage: float
    points: List[Dict]  # [{code, title, number, rate, date_from}]
    grades: List[Dict]  # [{code, title, from_point, to_point}]


@dataclass
class ExtractedAllowance:
    """Extracted allowance data."""
    type_code: str
    type_title: str
    points: List[Dict]  # [{code, title, amount}]
    increase_date: str
    increase_percentage: float


class S2SpecialistAgent:
    """
    Upskilled S2 agent with deep analysis capabilities.

    Responsibilities:
    1. Deep analysis of ALL customer data files
    2. Extract pay scales and ALL points/rates
    3. Extract allowances (TLR, SEN, etc.)
    4. Build ALL template sheets - nothing ignored
    5. Provide detailed analysis reports
    """

    def __init__(self):
        self.analysis_reports: List[AnalysisReport] = []
        self.extracted_pay_scales: List[ExtractedPayScale] = []
        self.extracted_allowances: List[ExtractedAllowance] = []
        self.staff_data: List[pd.DataFrame] = []
        self.issues: List[str] = []
        self.assumptions: List[str] = []

        # Template sheet builders
        self.template_data = {
            "PayScales": [],
            "PayScalePoints": [],
            "PayScaleGrades": [],
            "PayScaleIncreasePercen": [],
            "AllowanceTypes": [],
            "AllowanceTypePoint": [],
            "AllowanceIncreasePercen": [],
            "Pensions": [],
            "EQWPatterns": [],
            "StfRoleGroup": [],
            "StfRole": [],
            "StaffMembers": [],
            "ContractsTeachFTE": [],
            "ContractsSupportHours": [],
            "ContractAllowances": [],
            "ContractAdjustments": [],
            "Finance Codes S2": [],
        }

        # Tracking
        self.schools_found = set()
        self.finance_codes_found = set()
        self.pay_scales_found = set()
        self.allowance_types_found = set()

    def log(self, message: str, level: str = "INFO"):
        """Log a message with proper encoding and error handling for Streamlit."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Ensure message is a string and handle encoding
            msg_str = str(message)
            # Replace problematic characters
            msg_str = msg_str.replace('\x00', '').replace('\n\n', '\n')
            # Truncate very long messages
            if len(msg_str) > 10000:
                msg_str = msg_str[:10000] + "... [truncated]"
            output = f"[{timestamp}] [{level}] S2-Specialist: {msg_str}"
            # Try to print with error handling
            try:
                print(output, flush=True)
            except (OSError, IOError, ValueError):
                # If print fails, try unicode encoding
                try:
                    print(output.encode('ascii', errors='replace').decode('ascii'), flush=True)
                except Exception:
                    # Last resort - silent fail
                    pass
        except Exception:
            # Completely silent - don't let logging break execution
            pass

    def _safe_get(self, row, key, default=''):
        """Safely get a value from a row, handling Series/duplicate column cases."""
        try:
            val = row.get(key, default)
            # If it's a Series (duplicate columns), take the first non-null value
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            return val
        except Exception:
            return default

    def _safe_notna(self, val) -> bool:
        """Safely check if a value is not NA, handling Series case."""
        try:
            if isinstance(val, pd.Series):
                return pd.notna(val.iloc[0]) if len(val) > 0 else False
            return pd.notna(val)
        except Exception:
            return False

    # =========================================================================
    # PHASE 1: DEEP ANALYSIS
    # =========================================================================

    def analyze_customer_data(self, data_dir: Path) -> List[AnalysisReport]:
        """
        Perform deep analysis of ALL customer data files.
        Returns detailed reports on what was found.
        """
        self.log("="*60)
        self.log("PHASE 1: DEEP ANALYSIS OF CUSTOMER DATA")
        self.log("="*60)

        all_files = list(data_dir.rglob("*.xls*")) + list(data_dir.rglob("*.csv"))
        all_files = [f for f in all_files if not f.name.startswith("~$")]

        self.log(f"Found {len(all_files)} files to analyze")

        for file_path in all_files:
            self.log(f"\nAnalyzing: {file_path.name}")
            self._analyze_file(file_path)

        self._print_analysis_summary()
        return self.analysis_reports

    def _analyze_file(self, file_path: Path):
        """Deeply analyze a single file."""
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
                self._analyze_dataframe(df, file_path.name, "CSV")
            else:
                # Try multiple engines for reading Excel files
                xl = None
                error_msg = ""
                
                # Try with openpyxl first (default)
                try:
                    xl = pd.ExcelFile(file_path, engine='openpyxl')
                except Exception as e1:
                    error_msg = str(e1)[:100]
                    try:
                        self.log(f"  Warning: openpyxl failed, trying xlrd engine...")
                    except Exception:
                        pass
                    # Try with xlrd engine
                    try:
                        xl = pd.ExcelFile(file_path, engine='xlrd')
                    except Exception as e2:
                        try:
                            self.log(f"  Warning: xlrd also failed, trying read_excel with sheet discovery...")
                        except Exception:
                            pass
                        # Try reading sheets with sheet discovery
                        try:
                            # Use None to get all sheets automatically
                            xls = pd.read_excel(file_path, sheet_name=None)
                            if xls:
                                try:
                                    self.log(f"  Sheets: {len(xls)} found")
                                except Exception:
                                    pass
                                for sheet_name, df in xls.items():
                                    if sheet_name.lower() not in ['guidance', 'notes', 'instructions', 'help']:
                                        if df is not None and len(df) > 0:
                                            self._analyze_dataframe(df, file_path.name, sheet_name)
                                return
                        except Exception as e3:
                            error_msg = "Multiple engine failures"
                            self.issues.append(f"Error analyzing {file_path.name}: Could not read with any engine")
                            return
                
                # If we have a valid ExcelFile object, proceed normally
                if xl is not None:
                    try:
                        self.log(f"  Sheets: {len(xl.sheet_names)} found")
                    except Exception:
                        pass
                    for sheet in xl.sheet_names:
                        if sheet.lower() in ['guidance', 'notes', 'instructions', 'help']:
                            continue

                        df = self._read_sheet_smart(xl, sheet)
                        if df is not None and len(df) > 0:
                            self._analyze_dataframe(df, file_path.name, sheet)

        except Exception as e:
            self.issues.append(f"Error analyzing {file_path.name}: {str(e)[:100]}")

    def _read_sheet_smart(self, xl: pd.ExcelFile, sheet: str) -> Optional[pd.DataFrame]:
        """Smart read that finds the header row automatically."""
        try:
            # First read to find header
            df_raw = pd.read_excel(xl, sheet, header=None, nrows=20)

            # Key column indicators for staff data
            staff_indicators = ['payroll', 'last name', 'first name', 'surname', 'forename',
                               'unique', 'employee', 'staff', 'contract', 'role', 'job title',
                               'hours', 'fte', 'salary', 'scale point', 'pension']

            # Find the best header row - prefer rows with staff-related column names
            best_row = 0
            best_score = 0

            for idx in range(min(15, len(df_raw))):
                row = df_raw.iloc[idx]
                row_str = ' '.join([str(v).lower() for v in row if pd.notna(v)])

                # Score based on staff indicators found
                indicator_score = sum(3 for ind in staff_indicators if ind in row_str)
                # Also score non-empty strings
                string_score = sum(1 for v in row if isinstance(v, str) and len(str(v).strip()) > 2)

                total_score = indicator_score + string_score

                if total_score > best_score:
                    best_score = total_score
                    best_row = idx

            # Re-read with correct header
            df = pd.read_excel(xl, sheet, header=best_row)
            df = df.dropna(how='all')

            # Remove rows that are just category headers (like "Core", "Essential")
            if len(df) > 0:
                try:
                    first_col = df.iloc[:, 0].astype(str).str.lower()
                    df = df[~first_col.isin(['core', 'essential', 'desirable', 'optional', 'core/mappable'])]
                except Exception:
                    pass  # Continue if this operation fails

            # Clean column names
            df.columns = [self._clean_column_name(c) for c in df.columns]

            return df

        except Exception as e:
            self.log(f"Error reading sheet {sheet}: {e}")
            # Try one more time with minimal options
            try:
                df = pd.read_excel(xl, sheet, dtype=str)
                if len(df) > 0:
                    df.columns = [self._clean_column_name(c) for c in df.columns]
                    return df
            except Exception:
                pass
            return None

    def _clean_column_name(self, col: Any) -> str:
        """Standardize column name."""
        if pd.isna(col):
            return "unnamed"

        col_str = str(col).strip().lower()

        # Exact/priority mappings (checked first, order matters)
        priority_mappings = [
            ('unique payroll', 'payroll_number'),
            ('payroll number', 'payroll_number'),
            ('person id', 'payroll_number'),
            ('employee id', 'payroll_number'),
            ('staff id', 'payroll_number'),
            ('last name', 'surname'),
            ('family name', 'surname'),
            ('first name', 'forename'),
            ('given name', 'forename'),
            ('continuous service', 'service_start_date'),
            ('service start', 'service_start_date'),
            ('start date', 'service_start_date'),
            ('date of birth', 'dob'),
            ('birth date', 'dob'),
            ('work location', 'school_code'),
            ('school name', 'school_code'),
            ('cost centre', 'cost_centre'),
            ('contract reference', 'contract_ref'),
            ('contract ref', 'contract_ref'),
            ('staff role', 'job_title'),
            ('job title', 'job_title'),
            ('role title', 'job_title'),
            ('gross salary finance', 'finance_code'),
            ('finance code', 'finance_code'),
            ('nominal code', 'finance_code'),
            ('full time hours', 'ft_hours'),
            ('ft hours', 'ft_hours'),
            ('fte hours', 'ft_hours'),
            ('contracted hours', 'weekly_hours'),
            ('weekly hours', 'weekly_hours'),
            ('hours per week', 'weekly_hours'),
            ('weekly fte', 'fte'),
            ('annual fte', 'fte'),
            ('weeks worked', 'weeks_worked'),
            ('tto weeks', 'weeks_worked'),
            ('weeks paid', 'weeks_paid'),
            ('pay scale', 'pay_scale'),
            ('pay range', 'pay_scale'),
            ('scale point', 'scale_point'),
            ('spine point', 'scale_point'),
            ('current point', 'scale_point'),
        ]

        # Check priority mappings first
        for pattern, standard in priority_mappings:
            if pattern in col_str:
                return standard

        # Standard single-word mappings (fallback)
        mappings = {
            'payroll': 'payroll_number',
            'surname': 'surname',
            'forename': 'forename',
            'dob': 'dob',
            'gender': 'gender',
            'sex': 'gender',
            'school': 'school_code',
            'location': 'school_code',
            'department': 'cost_centre',
            'role': 'job_title',
            'position': 'job_title',
            'nominal': 'finance_code',
            'fte': 'fte',
            'scale': 'pay_scale',
            'point': 'scale_point',
            'scp': 'scale_point',
            'grade': 'grade',
            'annual salary': 'annual_salary',
            'fte salary': 'annual_salary',
            'salary': 'annual_salary',
            'actual salary': 'actual_salary',
            'pro rata': 'actual_salary',
            'pension': 'pension',
            'pension scheme': 'pension',
            'contract type': 'contract_type',
            'contract ref': 'contract_ref',
            'reference': 'contract_ref',
            'allowance': 'allowance',
            'tlr': 'tlr_allowance',
            'sen': 'sen_allowance',
            'recruitment': 'recruitment_allowance',
            'retention': 'retention_allowance',
        }

        for pattern, standard in mappings.items():
            if pattern in col_str:
                return standard

        return col_str.replace(' ', '_').replace('/', '_')

    def _analyze_dataframe(self, df: pd.DataFrame, file_name: str, sheet_name: str):
        """Analyze a dataframe and create detailed report."""
        columns_mapped = {}
        data_quality = {}
        sample_data = {}
        issues = []
        recommendations = []

        # Analyze each column - use unique columns to avoid DataFrame issues
        seen_cols = set()
        for col in df.columns:
            if col.startswith('unnamed') or col in seen_cols:
                continue
            seen_cols.add(col)

            try:
                col_data = df[col]
                # Handle case where duplicate column names return a DataFrame
                if isinstance(col_data, pd.DataFrame):
                    col_data = col_data.iloc[:, 0]  # Take first column
                non_null = col_data.dropna()
            except Exception:
                continue

            if len(non_null) == 0:
                continue

            # Sample data - use values.tolist() for safety
            try:
                sample_data[col] = non_null.head(5).values.tolist()
            except Exception:
                sample_data[col] = list(non_null.head(5))

            # Data quality
            data_quality[col] = {
                'non_null_count': len(non_null),
                'null_count': len(df) - len(non_null),
                'unique_values': non_null.nunique(),
                'dtype': str(non_null.dtype),
            }

            # Detect data type from content
            content_type = self._detect_content_type(non_null)
            data_quality[col]['content_type'] = content_type

        # Determine what type of data this is
        data_type = self._classify_data_type(df, sheet_name)

        report = AnalysisReport(
            file_name=file_name,
            sheet_name=sheet_name,
            row_count=len(df),
            column_count=len(df.columns),
            columns_found=list(df.columns),
            columns_mapped=columns_mapped,
            data_quality=data_quality,
            sample_data=sample_data,
            issues=issues,
            recommendations=recommendations
        )

        self.analysis_reports.append(report)

        # Store data for processing
        if data_type == 'staff_contracts':
            self.staff_data.append(df)
            self.log(f"    -> Staff contract data: {len(df)} rows")
            # ALSO extract pay scales and allowances from staff data
            self._extract_pay_scales_from_staff_data(df)
            self._extract_allowances_from_staff_data(df)
        elif data_type == 'pay_scales':
            self._extract_pay_scales_from_df(df, sheet_name)
            self.log(f"    -> Pay scale data extracted")
        elif data_type == 'allowances':
            self._extract_allowances_from_df(df)
            self.log(f"    -> Allowance data extracted")

    def _detect_content_type(self, series: pd.Series) -> str:
        """Detect the type of content in a series."""
        try:
            # Handle DataFrame case (duplicate columns)
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]

            sample = series.head(10).astype(str).values.tolist()
            sample_str = ' '.join(sample).lower()

            # Check for dates
            head_vals = series.head(10).values
            if any(isinstance(v, (datetime, pd.Timestamp)) for v in head_vals):
                return 'date'

            # Check for currency/salary
            if any(c in sample_str for c in ['£', '$', 'salary', 'pay']):
                return 'currency'

            # Check for percentages
            if '%' in sample_str or all(0 <= v <= 1 for v in head_vals if isinstance(v, (int, float))):
                return 'percentage'

            # Check for names
            if series.dtype == 'object':
                try:
                    if series.str.match(r'^[A-Z][a-z]+$').any():
                        return 'name'
                except Exception:
                    pass

            # Check for codes
            if series.dtype == 'object':
                try:
                    if series.str.match(r'^[A-Z0-9_]+$').any():
                        return 'code'
                except Exception:
                    pass

            return 'text' if series.dtype == 'object' else 'numeric'
        except Exception:
            return 'unknown'

    def _classify_data_type(self, df: pd.DataFrame, sheet_name: str) -> str:
        """Classify what type of data this sheet contains."""
        cols_lower = [str(c).lower() for c in df.columns]
        sheet_lower = sheet_name.lower()

        # Staff contracts - look for multiple staff identifiers
        if any(c in cols_lower for c in ['surname', 'forename', 'payroll_number', 'job_title']):
            if any(c in cols_lower for c in ['weekly_hours', 'fte', 'scale_point', 'annual_salary']):
                return 'staff_contracts'

        # Pay scales - EXPANDED DETECTION
        pay_scale_indicators = ['pay scale', 'pay range', 'pay grid', 'salary scale', 'spine', 
                               'payscale', 'pay spines', 'standard practice', 'salary rates',
                               'mps', 'ups', 'aps', 'upper pay scale', 'main pay']
        if any(x in sheet_lower for x in pay_scale_indicators):
            return 'pay_scales'
        
        # Check columns for pay scale indicators
        if any(c in cols_lower for c in ['scale_point', 'spine_point', 'pay_scale_rate', 'scp', 
                                         'point', 'salary', 'rate', 'annual salary']):
            # Make sure it's not staff contracts
            if not any(c in cols_lower for c in ['surname', 'forename', 'payroll_number']):
                # If we see numeric or currency columns with point/scale references
                if any(c in cols_lower for c in ['point', 'scp', 'spine', 'scale', 'grade']):
                    return 'pay_scales'

        # Allowances - EXPANDED DETECTION
        allowance_indicators = ['allowance', 'tlr', 'sen', 'recruitment', 'retention', 'london',
                               'weighting', 'supplement', 'enhancement', 'discretionary', 
                               'annual addition', 'teaching and learning']
        if any(x in sheet_lower for x in allowance_indicators):
            return 'allowances'
        
        # Check columns for allowance structure
        if any(c in cols_lower for c in ['tlr', 'sen', 'allowance', 'supplement', 'london', 'weighting']):
            # If we see amount/rate columns
            if any(c in cols_lower for c in ['amount', 'rate', 'salary', 'value', '£']):
                return 'allowances'

        # EQWP/TTO
        if 'tto' in sheet_lower or 'equated' in sheet_lower or 'weeks' in sheet_lower:
            return 'eqwp'

        return 'unknown'

    def _print_analysis_summary(self):
        """Print summary of analysis."""
        try:
            self.log("\n" + "="*60)
            self.log("ANALYSIS SUMMARY")
            self.log("="*60)

            total_staff = sum(len(df) if isinstance(df, list) else 0 for df in self.staff_data)
            self.log(f"Total staff records found: {total_staff}")
            self.log(f"Pay scales extracted: {len(self.extracted_pay_scales)}")
            self.log(f"Allowance types found: {len(self.extracted_allowances)}")
            
            # Safely handle the schools_found set
            schools_count = len(self.schools_found) if self.schools_found else 0
            self.log(f"Schools found: {schools_count}")
            
            self.log(f"Finance codes found: {len(self.finance_codes_found)}")

            if self.issues:
                self.log(f"\nIssues found: {len(self.issues)}")
                for idx, issue in enumerate(self.issues[:5], 1):
                    try:
                        # Make issue string safe
                        safe_issue = str(issue)[:200]  # Limit length
                        self.log(f"  {idx}. {safe_issue}")
                    except Exception:
                        self.log(f"  {idx}. [Issue display failed]")
        except Exception as e:
            # Silently continue if summary fails
            pass

    # =========================================================================
    # PHASE 2: PAY SCALE EXTRACTION
    # =========================================================================

    def _extract_pay_scales_from_df(self, df: pd.DataFrame, sheet_name: str):
        """Extract pay scales and points from a dedicated pay scale dataframe."""
        self.log(f"  Extracting pay scales from dedicated sheet: {sheet_name}")

        # Detect scale type hint from sheet name
        sheet_lower = sheet_name.lower()
        if 'leadership' in sheet_lower or 'lead' in sheet_lower:
            scale_type_hint = 'leadership'
        elif 'support' in sheet_lower or 'njc' in sheet_lower or 'nj' in sheet_lower:
            scale_type_hint = 'support'
        elif 'teaching' in sheet_lower or 'teacher' in sheet_lower or 'main' in sheet_lower or 'mps' in sheet_lower or 'ups' in sheet_lower:
            scale_type_hint = 'teaching'
        else:
            scale_type_hint = 'auto'  # Will detect from point codes

        # Extended column detection for rates/salaries
        rate_keywords = ['rate', 'salary', 'annual', 'pay', '£', '202', '2024', '2025', '2026', 'amount', 'value']
        rate_cols = [c for c in df.columns if any(x in str(c).lower() for x in rate_keywords)]

        # Extended column detection for point codes
        point_keywords = ['point', 'scp', 'spine', 'scale', 'grade', 'code', 'level', 'step', 'band']
        point_cols = [c for c in df.columns if any(x in str(c).lower() for x in point_keywords)]

        # Also check first column - often contains point codes
        if len(df.columns) > 0:
            first_col = df.columns[0]
            if first_col not in point_cols:
                # Check if first column contains point-like values
                sample = df[first_col].dropna().head(5).astype(str).tolist()
                if any(re.match(r'^[MLU]?\d+$', str(v).strip(), re.IGNORECASE) for v in sample):
                    point_cols = [first_col] + point_cols

        self.log(f"    Rate columns found: {rate_cols[:5]}")
        self.log(f"    Point columns found: {point_cols[:5]}")

        # Collect points categorized by scale type
        main_points = []      # M1-M6
        upper_points = []     # U1-U3
        leadership_points = []  # L01-L43
        support_points = []   # Numeric points (1-43 etc)

        # Extract points and rates
        for idx, row in df.iterrows():
            point_code = None
            rate = None

            # Try to get point code from point columns
            for col in point_cols:
                val = row.get(col)
                if pd.notna(val) and str(val).strip():
                    point_code = str(val).strip()
                    # Skip header-like values
                    if point_code.lower() in ['point', 'scp', 'scale', 'grade', 'code']:
                        point_code = None
                        continue
                    break

            # If no point code from columns, check if row index is the point
            if not point_code and isinstance(idx, (int, str)):
                idx_str = str(idx).strip()
                if re.match(r'^[MLU]?\d+$', idx_str, re.IGNORECASE):
                    point_code = idx_str

            if not point_code:
                continue

            # Try to get rate from rate columns (prefer most recent year)
            year_cols = sorted([c for c in rate_cols if re.search(r'202[4-9]', str(c))], reverse=True)
            other_rate_cols = [c for c in rate_cols if c not in year_cols]

            for col in year_cols + other_rate_cols:
                val = row.get(col)
                if pd.notna(val):
                    try:
                        # Handle various currency formats
                        val_str = str(val).replace('£', '').replace(',', '').replace(' ', '').strip()
                        rate = float(val_str)
                        if rate > 1000:  # Likely an annual salary
                            break
                        elif rate > 5 and rate < 100:  # Might be hourly rate
                            rate = rate * 37 * 52.143  # Convert to annual
                            break
                    except (ValueError, TypeError):
                        pass

            if not rate or rate <= 0:
                continue

            # Categorize by point code pattern
            point_code_clean = str(point_code).strip().upper()
            point_lower = point_code_clean.lower()

            # Leadership scale (L1-L43)
            if point_lower.startswith('l') and any(c.isdigit() for c in point_code_clean):
                num = self._extract_point_number(point_code_clean)
                normalized = f"L{num:02d}"
                leadership_points.append({
                    'code': normalized,
                    'title': normalized,
                    'number': num,
                    'rate': rate,
                    'date_from': '2025-09-01',
                })
            # Upper pay scale (U1-U3 or UPS1-UPS3)
            elif point_lower.startswith('u') or 'ups' in point_lower:
                num = self._extract_point_number(point_code_clean)
                normalized = f"U{min(num, 3)}"
                upper_points.append({
                    'code': normalized,
                    'title': normalized,
                    'number': num,
                    'rate': rate,
                    'date_from': '2025-09-01',
                })
            # Main pay scale (M1-M6 or MPS1-MPS6)
            elif point_lower.startswith('m') or 'mps' in point_lower:
                num = self._extract_point_number(point_code_clean)
                normalized = f"M{min(num, 6)}"
                main_points.append({
                    'code': normalized,
                    'title': normalized,
                    'number': num,
                    'rate': rate,
                    'date_from': '2025-09-01',
                })
            # Pure numeric - could be support or need context
            elif point_code_clean.isdigit():
                num = int(point_code_clean)
                if scale_type_hint == 'support' or num > 6:
                    # Support scale point
                    support_points.append({
                        'code': str(num),
                        'title': f"Point {num}",
                        'number': num,
                        'rate': rate,
                        'date_from': '2025-04-01',
                    })
                elif scale_type_hint == 'teaching' and num <= 6:
                    # Assume Main scale
                    normalized = f"M{num}"
                    main_points.append({
                        'code': normalized,
                        'title': normalized,
                        'number': num,
                        'rate': rate,
                        'date_from': '2025-09-01',
                    })
                else:
                    # Default to support for ambiguous numeric points
                    support_points.append({
                        'code': str(num),
                        'title': f"Point {num}",
                        'number': num,
                        'rate': rate,
                        'date_from': '2025-04-01',
                    })
            else:
                # Other format - try to extract number and categorize
                num = self._extract_point_number(point_code_clean)
                if num > 0:
                    if scale_type_hint == 'leadership':
                        normalized = f"L{num:02d}"
                        leadership_points.append({
                            'code': normalized,
                            'title': point_code,
                            'number': num,
                            'rate': rate,
                            'date_from': '2025-09-01',
                        })
                    elif scale_type_hint == 'support':
                        support_points.append({
                            'code': str(num),
                            'title': point_code,
                            'number': num,
                            'rate': rate,
                            'date_from': '2025-04-01',
                        })
                    else:
                        # Default teaching
                        main_points.append({
                            'code': point_code_clean,
                            'title': point_code,
                            'number': num,
                            'rate': rate,
                            'date_from': '2025-09-01',
                        })

        # Create pay scales from extracted points (combine main + upper for MAIN scale)
        teaching_points = main_points + upper_points
        if teaching_points and 'MAIN' not in self.pay_scales_found:
            # Deduplicate by code
            seen = set()
            unique_points = []
            for p in sorted(teaching_points, key=lambda x: x['number']):
                if p['code'] not in seen:
                    seen.add(p['code'])
                    unique_points.append(p)

            if unique_points:
                pay_scale = ExtractedPayScale(
                    code='MAIN',
                    title='Teachers Main',
                    scale_type='teaching',
                    london_weighting='England & Wales',
                    increment_date='2025-09-01',
                    increase_date='2025-09-01',
                    increase_percentage=0,
                    points=unique_points,
                    grades=[]
                )
                self.extracted_pay_scales.append(pay_scale)
                self.pay_scales_found.add('MAIN')
                self.log(f"    Extracted {len(unique_points)} teaching scale points (MAIN)")

        if leadership_points and 'LS' not in self.pay_scales_found:
            # Deduplicate
            seen = set()
            unique_points = []
            for p in sorted(leadership_points, key=lambda x: x['number']):
                if p['code'] not in seen:
                    seen.add(p['code'])
                    unique_points.append(p)

            if unique_points:
                pay_scale = ExtractedPayScale(
                    code='LS',
                    title='Leadership Group',
                    scale_type='leadership',
                    london_weighting='England & Wales',
                    increment_date='2025-09-01',
                    increase_date='2025-09-01',
                    increase_percentage=0,
                    points=unique_points,
                    grades=[]
                )
                self.extracted_pay_scales.append(pay_scale)
                self.pay_scales_found.add('LS')
                self.log(f"    Extracted {len(unique_points)} leadership scale points (LS)")

        if support_points and 'MAT_SUP' not in self.pay_scales_found:
            # Deduplicate
            seen = set()
            unique_points = []
            for p in sorted(support_points, key=lambda x: x['number']):
                if p['code'] not in seen:
                    seen.add(p['code'])
                    unique_points.append(p)

            if unique_points:
                pay_scale = ExtractedPayScale(
                    code='MAT_SUP',
                    title='MAT Support Scale',
                    scale_type='support',
                    london_weighting='England & Wales',
                    increment_date='2025-04-01',
                    increase_date='2025-04-01',
                    increase_percentage=0,
                    points=unique_points,
                    grades=[]
                )
                self.extracted_pay_scales.append(pay_scale)
                self.pay_scales_found.add('MAT_SUP')
                self.log(f"    Extracted {len(unique_points)} support scale points (MAT_SUP)")

    def _extract_point_number(self, code: str) -> int:
        """Extract numeric point number from code."""
        numbers = re.findall(r'\d+', str(code))
        if numbers:
            return int(numbers[0])
        return 0

    def _extract_allowances_from_df(self, df: pd.DataFrame):
        """Extract allowance types and points from a dedicated allowance dataframe."""
        self.log(f"  Extracting allowances from dedicated sheet...")

        # Look for allowance type column and amount column
        type_col = None
        amount_col = None
        code_col = None

        for col in df.columns:
            col_lower = str(col).lower()
            if any(x in col_lower for x in ['type', 'allowance', 'name', 'description']):
                if type_col is None:
                    type_col = col
            if any(x in col_lower for x in ['amount', 'value', 'rate', '£', 'annual']):
                if amount_col is None:
                    amount_col = col
            if any(x in col_lower for x in ['code', 'point', 'level']):
                if code_col is None:
                    code_col = col

        # If we found structured columns, extract from rows
        if type_col and amount_col:
            self.log(f"    Found structured allowance data: type={type_col}, amount={amount_col}")
            allowances_by_type = {}

            for _, row in df.iterrows():
                type_val = row.get(type_col)
                amount_val = row.get(amount_col)

                if not pd.notna(type_val) or not pd.notna(amount_val):
                    continue

                type_str = str(type_val).strip().upper()
                try:
                    amount = float(str(amount_val).replace('£', '').replace(',', '').strip())
                    if amount <= 0:
                        continue
                except (ValueError, TypeError):
                    continue

                # Categorize by type
                if 'TLR' in type_str:
                    type_code = 'TLR'
                    type_title = 'Teaching and Learning Responsibilities'
                elif 'SEN' in type_str and 'PENSION' not in type_str:
                    type_code = 'SEN'
                    type_title = 'Special Educational Needs'
                elif 'RECRUIT' in type_str:
                    type_code = 'REC'
                    type_title = 'Recruitment Allowance'
                elif 'RETAIN' in type_str or 'RETENTION' in type_str:
                    type_code = 'RET'
                    type_title = 'Retention Allowance'
                elif 'LONDON' in type_str:
                    type_code = 'LON'
                    type_title = 'London Weighting'
                else:
                    continue

                if type_code not in allowances_by_type:
                    allowances_by_type[type_code] = {'title': type_title, 'amounts': set()}
                allowances_by_type[type_code]['amounts'].add(amount)

            # Create allowance types
            for type_code, data in allowances_by_type.items():
                if type_code in self.allowance_types_found:
                    continue

                points = []
                for idx, amount in enumerate(sorted(data['amounts'], reverse=True), 1):
                    points.append({
                        'code': f'{type_code}{idx}',
                        'title': f'{data["title"]} {idx}',
                        'amount': amount,
                    })

                if points:
                    allowance = ExtractedAllowance(
                        type_code=type_code,
                        type_title=data['title'],
                        points=points,
                        increase_date='2025-09-01',
                        increase_percentage=0,
                    )
                    self.extracted_allowances.append(allowance)
                    self.allowance_types_found.add(type_code)
                    self.log(f"    Extracted {len(points)} {type_code} allowance points")

        else:
            # Fallback: Look for columns named after allowance types
            for col in df.columns:
                col_lower = str(col).lower()

                # TLR allowances
                if 'tlr' in col_lower:
                    self._extract_allowance_type(df, col, 'TLR', 'Teaching and Learning Responsibilities')
                # SEN allowances (avoid matching 'pension')
                elif 'sen' in col_lower and 'pension' not in col_lower:
                    self._extract_allowance_type(df, col, 'SEN', 'Special Educational Needs')
                # Recruitment allowances
                elif 'recruitment' in col_lower or 'recruit' in col_lower:
                    self._extract_allowance_type(df, col, 'REC', 'Recruitment Allowance')
                # Retention allowances
                elif 'retention' in col_lower or 'retain' in col_lower:
                    self._extract_allowance_type(df, col, 'RET', 'Retention Allowance')
                # London weighting
                elif 'london' in col_lower and 'weight' in col_lower:
                    self._extract_allowance_type(df, col, 'LON', 'London Weighting')

    def _extract_allowance_type(self, df: pd.DataFrame, col: str, code: str, title: str):
        """Extract a specific allowance type from a column."""
        # Skip if already extracted
        if code in self.allowance_types_found:
            return

        # Collect unique amounts
        unique_amounts = set()

        for idx, row in df.iterrows():
            val = row.get(col)
            if pd.notna(val):
                try:
                    amount = float(str(val).replace('£', '').replace(',', '').strip())
                    if amount > 0:
                        unique_amounts.add(amount)
                except (ValueError, TypeError):
                    pass

        if not unique_amounts:
            return

        # Create points from unique amounts (sorted descending - highest value = level 1)
        points = []
        for idx, amount in enumerate(sorted(unique_amounts, reverse=True), 1):
            points.append({
                'code': f"{code}{idx}",
                'title': f"{title} {idx}",
                'amount': amount,
            })

        if points:
            allowance = ExtractedAllowance(
                type_code=code,
                type_title=title,
                points=points,
                increase_date='2025-09-01',
                increase_percentage=0,
            )
            self.extracted_allowances.append(allowance)
            self.allowance_types_found.add(code)
            self.log(f"    Extracted {len(points)} {code} allowance points from column '{col}'")

    def _extract_pay_scales_from_staff_data(self, df: pd.DataFrame):
        """
        Extract pay scale points from staff contract data.
        This handles cases where pay scale info is embedded in staff rows.
        """
        self.log("    Extracting pay scales from staff data...")

        # Track unique scale points by scale type
        teaching_points = {}  # {point_code: rate}
        leadership_points = {}
        support_points = {}

        for _, row in df.iterrows():
            # Get scale point
            scale_point = self._safe_get(row, 'scale_point', '')
            if not self._safe_notna(scale_point):
                scale_point = self._safe_get(row, 'scp', '')
            if not self._safe_notna(scale_point):
                scale_point = self._safe_get(row, 'spine_point', '')

            scale_point_str = str(scale_point).strip() if self._safe_notna(scale_point) else ''
            if not scale_point_str or scale_point_str == 'nan':
                continue

            # Get salary/rate if available
            rate = None
            for col in ['annual_salary', 'fte_salary', 'salary', 'rate']:
                val = self._safe_get(row, col, None)
                if self._safe_notna(val):
                    try:
                        rate = float(str(val).replace('£', '').replace(',', '').strip())
                        if rate > 1000:  # Looks like a salary
                            break
                    except (ValueError, TypeError):
                        pass

            # Determine scale type from job title or scale point
            job_title = str(self._safe_get(row, 'job_title', '')).lower()
            point_lower = scale_point_str.lower()

            # Leadership points (L1-L43)
            if 'l' in point_lower and any(c.isdigit() for c in scale_point_str):
                normalized = self._normalize_scale_point(scale_point_str, 'teaching')
                if normalized.startswith('L'):
                    if normalized not in leadership_points or (rate and rate > 0):
                        leadership_points[normalized] = rate
                    continue

            # Teaching points (M1-M6, U1-U3)
            if any(x in point_lower for x in ['m', 'u']) and any(c.isdigit() for c in scale_point_str):
                normalized = self._normalize_scale_point(scale_point_str, 'teaching')
                if normalized not in teaching_points or (rate and rate > 0):
                    teaching_points[normalized] = rate
                continue

            # Check job title for teaching vs support
            is_teaching = any(x in job_title for x in ['teacher', 'head', 'principal', 'lecturer'])

            if is_teaching:
                normalized = self._normalize_scale_point(scale_point_str, 'teaching')
                if normalized not in teaching_points or (rate and rate > 0):
                    teaching_points[normalized] = rate
            else:
                # Support scale - just numbers
                normalized = self._normalize_scale_point(scale_point_str, 'support')
                if normalized not in support_points or (rate and rate > 0):
                    support_points[normalized] = rate

        # Create pay scales from extracted points
        if teaching_points and 'MAIN' not in self.pay_scales_found:
            points = []
            for code, rate in sorted(teaching_points.items(), key=lambda x: self._extract_point_number(x[0])):
                if not code.startswith('L'):  # Exclude leadership from MAIN
                    points.append({
                        'code': code,
                        'title': code,
                        'number': self._extract_point_number(code),
                        'rate': rate if rate else 0,
                        'date_from': '2025-09-01',
                    })

            if points:
                pay_scale = ExtractedPayScale(
                    code='MAIN',
                    title='Teachers Main',
                    scale_type='teaching',
                    london_weighting='England & Wales',
                    increment_date='2025-09-01',
                    increase_date='2025-09-01',
                    increase_percentage=0,
                    points=points,
                    grades=[]
                )
                self.extracted_pay_scales.append(pay_scale)
                self.pay_scales_found.add('MAIN')
                self.log(f"      Extracted {len(points)} teaching scale points (MAIN)")

        if leadership_points and 'LS' not in self.pay_scales_found:
            points = []
            for code, rate in sorted(leadership_points.items(), key=lambda x: self._extract_point_number(x[0])):
                points.append({
                    'code': code,
                    'title': code,
                    'number': self._extract_point_number(code),
                    'rate': rate if rate else 0,
                    'date_from': '2025-09-01',
                })

            if points:
                pay_scale = ExtractedPayScale(
                    code='LS',
                    title='Leadership Group',
                    scale_type='leadership',
                    london_weighting='England & Wales',
                    increment_date='2025-09-01',
                    increase_date='2025-09-01',
                    increase_percentage=0,
                    points=points,
                    grades=[]
                )
                self.extracted_pay_scales.append(pay_scale)
                self.pay_scales_found.add('LS')
                self.log(f"      Extracted {len(points)} leadership scale points (LS)")

        if support_points and 'MAT_SUP' not in self.pay_scales_found:
            points = []
            for code, rate in sorted(support_points.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                points.append({
                    'code': code,
                    'title': f"Point {code}",
                    'number': int(code) if code.isdigit() else self._extract_point_number(code),
                    'rate': rate if rate else 0,
                    'date_from': '2025-04-01',
                })

            if points:
                pay_scale = ExtractedPayScale(
                    code='MAT_SUP',
                    title='MAT Support Scale',
                    scale_type='support',
                    london_weighting='England & Wales',
                    increment_date='2025-04-01',
                    increase_date='2025-04-01',
                    increase_percentage=0,
                    points=points,
                    grades=[]
                )
                self.extracted_pay_scales.append(pay_scale)
                self.pay_scales_found.add('MAT_SUP')
                self.log(f"      Extracted {len(points)} support scale points (MAT_SUP)")

    def _extract_allowances_from_staff_data(self, df: pd.DataFrame):
        """
        Extract allowance types and points from staff contract data.
        This handles cases where allowance info is embedded in staff rows.
        """
        self.log("    Extracting allowances from staff data...")

        # Track unique allowance amounts by type
        tlr_amounts = set()
        sen_amounts = set()
        recruitment_amounts = set()
        retention_amounts = set()

        # Look for allowance columns
        for col in df.columns:
            col_lower = str(col).lower()

            # TLR allowances
            if 'tlr' in col_lower:
                for _, row in df.iterrows():
                    val = row.get(col)
                    if pd.notna(val):
                        try:
                            amount = float(str(val).replace('£', '').replace(',', '').strip())
                            if amount > 0:
                                tlr_amounts.add(amount)
                        except (ValueError, TypeError):
                            pass

            # SEN allowances
            elif 'sen' in col_lower and 'pension' not in col_lower:
                for _, row in df.iterrows():
                    val = row.get(col)
                    if pd.notna(val):
                        try:
                            amount = float(str(val).replace('£', '').replace(',', '').strip())
                            if amount > 0:
                                sen_amounts.add(amount)
                        except (ValueError, TypeError):
                            pass

            # Recruitment allowances
            elif 'recruitment' in col_lower or 'recruit' in col_lower:
                for _, row in df.iterrows():
                    val = row.get(col)
                    if pd.notna(val):
                        try:
                            amount = float(str(val).replace('£', '').replace(',', '').strip())
                            if amount > 0:
                                recruitment_amounts.add(amount)
                        except (ValueError, TypeError):
                            pass

            # Retention allowances
            elif 'retention' in col_lower or 'retain' in col_lower:
                for _, row in df.iterrows():
                    val = row.get(col)
                    if pd.notna(val):
                        try:
                            amount = float(str(val).replace('£', '').replace(',', '').strip())
                            if amount > 0:
                                retention_amounts.add(amount)
                        except (ValueError, TypeError):
                            pass

        # Create allowance types from extracted amounts
        if tlr_amounts and 'TLR' not in self.allowance_types_found:
            points = []
            for idx, amount in enumerate(sorted(tlr_amounts, reverse=True), 1):
                points.append({
                    'code': f'TLR{idx}',
                    'title': f'TLR {idx}',
                    'amount': amount,
                })

            allowance = ExtractedAllowance(
                type_code='TLR',
                type_title='Teaching and Learning Responsibilities',
                points=points,
                increase_date='2025-09-01',
                increase_percentage=0,
            )
            self.extracted_allowances.append(allowance)
            self.allowance_types_found.add('TLR')
            self.log(f"      Extracted {len(points)} TLR allowance points")

        if sen_amounts and 'SEN' not in self.allowance_types_found:
            points = []
            for idx, amount in enumerate(sorted(sen_amounts, reverse=True), 1):
                points.append({
                    'code': f'SEN{idx}',
                    'title': f'SEN {idx}',
                    'amount': amount,
                })

            allowance = ExtractedAllowance(
                type_code='SEN',
                type_title='Special Educational Needs',
                points=points,
                increase_date='2025-09-01',
                increase_percentage=0,
            )
            self.extracted_allowances.append(allowance)
            self.allowance_types_found.add('SEN')
            self.log(f"      Extracted {len(points)} SEN allowance points")

        if recruitment_amounts and 'REC' not in self.allowance_types_found:
            points = []
            for idx, amount in enumerate(sorted(recruitment_amounts, reverse=True), 1):
                points.append({
                    'code': f'REC{idx}',
                    'title': f'Recruitment Allowance {idx}',
                    'amount': amount,
                })

            allowance = ExtractedAllowance(
                type_code='REC',
                type_title='Recruitment Allowance',
                points=points,
                increase_date='2025-09-01',
                increase_percentage=0,
            )
            self.extracted_allowances.append(allowance)
            self.allowance_types_found.add('REC')
            self.log(f"      Extracted {len(points)} Recruitment allowance points")

        if retention_amounts and 'RET' not in self.allowance_types_found:
            points = []
            for idx, amount in enumerate(sorted(retention_amounts, reverse=True), 1):
                points.append({
                    'code': f'RET{idx}',
                    'title': f'Retention Allowance {idx}',
                    'amount': amount,
                })

            allowance = ExtractedAllowance(
                type_code='RET',
                type_title='Retention Allowance',
                points=points,
                increase_date='2025-09-01',
                increase_percentage=0,
            )
            self.extracted_allowances.append(allowance)
            self.allowance_types_found.add('RET')
            self.log(f"      Extracted {len(points)} Retention allowance points")

    # =========================================================================
    # PHASE 3: BUILD ALL TEMPLATE SHEETS
    # =========================================================================

    def build_all_templates(self) -> Dict[str, pd.DataFrame]:
        """Build ALL template sheets from extracted data."""
        self.log("\n" + "="*60)
        self.log("PHASE 3: BUILDING ALL TEMPLATE SHEETS")
        self.log("="*60)

        # Build in correct order
        self._build_pay_scales()
        self._build_pay_scale_points()
        self._build_pay_scale_grades()
        self._build_allowance_types()
        self._build_allowance_points()
        self._build_pensions()
        self._build_eqw_patterns()
        self._build_staff_role_groups()
        self._build_staff_roles()
        self._build_staff_members()
        self._build_contracts_teaching()
        self._build_contracts_support()
        self._build_contract_allowances()
        self._build_finance_codes_s2()

        # Convert to DataFrames
        result = {}
        for sheet_name, data in self.template_data.items():
            if data:
                result[sheet_name] = pd.DataFrame(data)
                self.log(f"  {sheet_name}: {len(data)} rows")
            else:
                self.log(f"  {sheet_name}: 0 rows (no data)")

        return result

    def _build_pay_scales(self):
        """Build PayScales sheet."""
        self.log("Building PayScales...")

        for ps in self.extracted_pay_scales:
            self.template_data["PayScales"].append({
                "PayScaleCode": ps.code,
                "PayScaleTitle": ps.title,
                "ServiceIncrementDateEnabled": ps.scale_type == 'support',
                "IncrementDate": ps.increment_date,
                "IncreaseDate": ps.increase_date,
                "IncreasePercentage": ps.increase_percentage,
                "AvailableToAllSchools": True,
                "SchoolCodes": "",
                "PayScaleEnabled": True,
                "ExcludeNationalInsurance": False,
                "ExcludePension": False,
            })

        # Add defaults if none extracted
        if not self.template_data["PayScales"]:
            defaults = [
                ("MAIN", "Teachers Main", False, "2025-09-01"),
                ("LS", "Leadership Group", False, "2025-09-01"),
                ("MAT_SUP", "MAT Support Scale", True, "2025-04-01"),
            ]
            for code, title, increment, date in defaults:
                self.template_data["PayScales"].append({
                    "PayScaleCode": code,
                    "PayScaleTitle": title,
                    "ServiceIncrementDateEnabled": increment,
                    "IncrementDate": date,
                    "IncreaseDate": date,
                    "IncreasePercentage": 0,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "PayScaleEnabled": True,
                    "ExcludeNationalInsurance": False,
                    "ExcludePension": False,
                })

    def _build_pay_scale_points(self):
        """Build PayScalePoints sheet."""
        self.log("Building PayScalePoints...")

        for ps in self.extracted_pay_scales:
            for point in ps.points:
                self.template_data["PayScalePoints"].append({
                    "PayScaleCode": ps.code,
                    "PayScalePointCode": point['code'],
                    "PayScalePointTitle": point['title'],
                    "ScalePointNumber": point['number'],
                    "Hourly": False,
                    "PayScalePointEnabled": True,
                    "RateDateFrom": point['date_from'],
                    "RateDateTo": "",
                    "PayScaleRate": point['rate'],
                })

    def _build_pay_scale_grades(self):
        """Build PayScaleGrades sheet."""
        self.log("Building PayScaleGrades...")

        for ps in self.extracted_pay_scales:
            if ps.points:
                # Create a grade spanning all points
                min_point = min(p['number'] for p in ps.points if p['number'] > 0) or 1
                max_point = max(p['number'] for p in ps.points if p['number'] > 0) or len(ps.points)

                self.template_data["PayScaleGrades"].append({
                    "PayScaleGradeCode": f"{ps.code}_FULL",
                    "Title": f"{ps.title} Full Range",
                    "PayScaleCode": ps.code,
                    "ScalePointNumberFrom": min_point,
                    "ScalePointNumberTo": max_point,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "PayScaleGradeEnabled": True,
                })

    def _build_allowance_types(self):
        """Build AllowanceTypes sheet."""
        self.log("Building AllowanceTypes...")

        for allowance in self.extracted_allowances:
            self.template_data["AllowanceTypes"].append({
                "AllowanceTypeCode": allowance.type_code,
                "AllowanceTypeTitle": allowance.type_title,
                "IncreaseDate": allowance.increase_date,
                "IncreasePercentage": allowance.increase_percentage,
                "AvailableToAllSchools": True,
                "SchoolCodes": "",
                "ExcludePension": False,
                "ExcludeNI": False,
                "AllowanceTypeEnabled": True,
            })

        # Add defaults if none extracted
        if not self.template_data["AllowanceTypes"]:
            for code, title in [("TLR", "Teaching and Learning Responsibilities"), ("SEN", "Special Educational Needs")]:
                self.template_data["AllowanceTypes"].append({
                    "AllowanceTypeCode": code,
                    "AllowanceTypeTitle": title,
                    "IncreaseDate": "2025-09-01",
                    "IncreasePercentage": 0,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "ExcludePension": False,
                    "ExcludeNI": False,
                    "AllowanceTypeEnabled": True,
                })

    def _build_allowance_points(self):
        """Build AllowanceTypePoint sheet."""
        self.log("Building AllowanceTypePoint...")

        for allowance in self.extracted_allowances:
            for point in allowance.points:
                self.template_data["AllowanceTypePoint"].append({
                    "AllowanceTypeCode": allowance.type_code,
                    "AllowancePointCode": point['code'],
                    "AllowancePointTitle": point['title'],
                    "AllowancePointEnabled": True,
                    "RateDateFrom": "2025-09-01",
                    "RateDateTo": "",
                    "Amount": point['amount'],
                })

    def _build_pensions(self):
        """Build Pensions sheet."""
        self.log("Building Pensions...")

        pensions = [
            ("TPS", "Teachers Pension Scheme", 28.68, "2024-04-01"),
            ("LGPS", "Local Government Pension Scheme", 21.90, "2025-04-01"),
            ("OPTOUT", "Opted Out 0%", 0, "2024-04-01"),
        ]

        for code, title, rate, date in pensions:
            self.template_data["Pensions"].append({
                "PensionCode": code,
                "Title": title,
                "AvailableToAllSchools": True,
                "SchoolCodes": "",
                "PensionEnabled": True,
                "RateDateFrom": date,
                "RateDateTo": "",
                "PensionPercentage": rate,
            })

    def _build_eqw_patterns(self):
        """Build EQWPatterns sheet."""
        self.log("Building EQWPatterns...")

        patterns = [
            ("AYR", "All Year Round", 52.143, 52.143, 0, 99),
            ("TTO_38", "38 Weeks Term Time Only", 43.5, 52.143, 0, 99),
            ("TTO_39", "39 Weeks Term Time Only", 44.7, 52.143, 0, 99),
            ("TTO_40", "40 Weeks Term Time Only", 45.9, 52.143, 0, 99),
        ]

        for code, title, equated, full_time, years_from, years_to in patterns:
            self.template_data["EQWPatterns"].append({
                "EquatedWeekPatternCode": code,
                "EquatedWeekPatternTitle": title,
                "AvailableToAllSchools": True,
                "SchoolCodes": "",
                "ServiceYearsFrom": years_from,
                "ServiceYearsTo": years_to,
                "EquatedWeeks": equated,
                "FullTimeWeeks": full_time,
                "EquatedWeekPatternEnabled": True,
            })

    def _build_staff_role_groups(self):
        """Build StfRoleGroup sheet from finished workbook patterns."""
        self.log("Building StfRoleGroup...")

        for code, data in S2_STAFF_ROLE_GROUP_PATTERNS.items():
            fc = get_finance_codes_for_srg(code)

            self.template_data["StfRoleGroup"].append({
                "StaffRoleGroupCode": code,
                "Title": data["title"],
                "GrossSalaryFinanceCode": data["gross_salary_fc"],
                "LeaveRebateFinanceCode": data["gross_salary_fc"],
                "AllowanceTypesFinanceCode": data["gross_salary_fc"],
                "AdjustmentsFinanceCode": data["gross_salary_fc"],
                "EmployersNiFinanceCode": data["ni_fc"],
                "PensionFinanceCode": data["pension_fc"],
                "WeeklyFteFinanceCode": fc["weekly_fte"],
                "AnnualFteFinanceCode": fc["annual_fte"],
                "WeeklyFteLeaveAdjustmentFinanceCode": fc["weekly_leave_adj"],
                "AnnualFteLeaveAdjustmentFinanceCode": fc["annual_leave_adj"],
                "TeachingRoleGroup": data["teaching"],
                "StaffRoleGroupEnabled": True,
            })

    def _build_staff_roles(self):
        """Build StfRole sheet from staff data."""
        self.log("Building StfRole...")

        roles_seen = set()

        for df in self.staff_data:
            if 'job_title' not in df.columns:
                continue

            for _, row in df.iterrows():
                title = str(self._safe_get(row, 'job_title', '')).strip()
                if not title or title == 'nan' or title in roles_seen:
                    continue

                # Skip 0-hour contracts
                hours = self._safe_get(row, 'weekly_hours', 0)
                if not hours:
                    hours = self._safe_get(row, 'ft_hours', 0)
                try:
                    if self._safe_notna(hours) and float(hours) == 0:
                        continue
                except (ValueError, TypeError):
                    pass

                roles_seen.add(title)

                # Determine role group and pay scale
                srg = get_srg_for_role(title)
                is_teaching = S2_STAFF_ROLE_GROUP_PATTERNS.get(srg, {}).get('teaching', False)

                ft_hours = self._safe_get(row, 'ft_hours', 32.436 if is_teaching else 37.0)
                if not self._safe_notna(ft_hours) or ft_hours == 0:
                    ft_hours = 32.436 if is_teaching else 37.0

                pay_scale = 'MAIN' if is_teaching else 'MAT_SUP'
                if 'leadership' in title.lower() or 'head' in title.lower():
                    pay_scale = 'LS'

                # Create role code
                code = self._create_role_code(title, srg)

                self.template_data["StfRole"].append({
                    "StaffRoleGroupCode": srg,
                    "StaffRoleCode": code,
                    "Title": title,
                    "PayScaleCode": pay_scale,
                    "FullTimeHoursPerWeek": float(ft_hours),
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "MonthsServiceBeforeIncrement": 0 if is_teaching else 6,
                    "DaysServiceBeforeIncrement": 0,
                    "StaffRoleEnabled": True,
                    "IsFinanceRole": 'finance' in title.lower(),
                })

    def _create_role_code(self, title: str, srg: str) -> str:
        """Create a role code from title."""
        # Clean and abbreviate
        title_clean = title.upper().strip()
        title_clean = re.sub(r'[^A-Z0-9\s]', '', title_clean)
        words = title_clean.split()

        if len(words) == 1:
            code = words[0][:6]
        elif len(words) == 2:
            code = words[0][:3] + "_" + words[1][:3]
        else:
            code = ''.join(w[0] for w in words[:4])

        return code

    def _build_staff_members(self):
        """Build StaffMembers sheet from staff data."""
        self.log("Building StaffMembers...")

        members_seen = set()

        for df in self.staff_data:
            for _, row in df.iterrows():
                payroll = self._safe_get(row, 'payroll_number', '')
                payroll_str = str(payroll).strip() if self._safe_notna(payroll) else ''

                # Skip if already seen or no payroll
                if not payroll_str or payroll_str == 'nan' or payroll_str in members_seen:
                    continue

                members_seen.add(payroll_str)

                # Extract data
                surname = str(self._safe_get(row, 'surname', '')).strip()
                forename = str(self._safe_get(row, 'forename', '')).strip()

                if surname == 'nan': surname = ''
                if forename == 'nan': forename = ''

                service_start = self._safe_get(row, 'service_start_date', '')
                dob = self._safe_get(row, 'dob', '')

                gender = str(self._safe_get(row, 'gender', 'ZZZ')).strip().upper()
                if gender in ['M', 'MALE']: gender = 'M'
                elif gender in ['F', 'FEMALE']: gender = 'F'
                else: gender = 'ZZZ'

                school = str(self._safe_get(row, 'school_code', '')).strip()
                if school != 'nan':
                    self.schools_found.add(school)

                # Check for casual/0-hour
                hours = self._safe_get(row, 'weekly_hours', 0)
                casual = self._safe_notna(hours) and float(hours) == 0

                self.template_data["StaffMembers"].append({
                    "StaffMemberCode": payroll_str,
                    "FirstName": forename,
                    "LastName": surname,
                    "Title": f"{forename} {surname}".strip(),
                    "ServiceStartDate": service_start if self._safe_notna(service_start) else '',
                    "ServiceEndDate": '',
                    "DateOfBirth": dob if self._safe_notna(dob) else '',
                    "Apprenticeship": False,
                    "PensionOptOut": False,
                    "AvailableToAllSchools": False,
                    "SchoolCodes": school if school != 'nan' else '',
                    "StaffMemberEnabled": True,
                    "GenderCode": gender,
                    "Casual": casual,
                })

    def _build_contracts_teaching(self):
        """Build ContractsTeachFTE sheet."""
        self.log("Building ContractsTeachFTE...")

        for df in self.staff_data:
            for _, row in df.iterrows():
                title = str(self._safe_get(row, 'job_title', '')).strip()
                srg = get_srg_for_role(title)

                # Only teaching contracts
                if not S2_STAFF_ROLE_GROUP_PATTERNS.get(srg, {}).get('teaching', False):
                    continue

                payroll = self._safe_get(row, 'payroll_number', '')
                payroll_str = str(payroll).strip() if self._safe_notna(payroll) else ''
                if not payroll_str or payroll_str == 'nan':
                    continue

                school = str(self._safe_get(row, 'school_code', '')).strip()
                if school == 'nan': school = ''

                fte = self._safe_get(row, 'fte', 1.0)
                if not self._safe_notna(fte): fte = 1.0

                scale_point = str(self._safe_get(row, 'scale_point', '')).strip()
                if scale_point == 'nan': scale_point = 'M1'

                # Clean scale point
                scale_point = self._normalize_scale_point(scale_point, 'teaching')

                role_code = self._create_role_code(title, srg)

                contract_ref = self._safe_get(row, 'contract_ref', '')
                if not self._safe_notna(contract_ref) or str(contract_ref) == 'nan':
                    contract_ref = f"{payroll_str}A"

                forename = str(self._safe_get(row, 'forename', '')).strip()
                surname = str(self._safe_get(row, 'surname', '')).strip()
                if forename == 'nan': forename = ''
                if surname == 'nan': surname = ''

                self.template_data["ContractsTeachFTE"].append({
                    "SchoolCode": school,
                    "StaffMemberCode": payroll_str,
                    "Reference": contract_ref,
                    "Title": f"{forename} {surname}".strip(),
                    "StaffRoleCode": role_code,
                    "PayScaleCode": "LS" if 'head' in title.lower() else "MAIN",
                    "PayScaleGradeCode": "",
                    "PayScalePointCode": scale_point,
                    "DepartmentCode": "STCH",
                    "FundCode": "",
                    "PensionCode": "TPS",
                    "EquatedWeekPatternCode": "AYR",
                    "DateFrom": "2025-09-01",
                    "DateTo": "",
                    "WeeklyFteOrHpw": float(fte),
                    "MatEditOnly": False,
                    "NoIncrement": False,
                    "ContractTypeCode": "PERM",
                    "Notes": "",
                })

                # Check for allowances
                self._extract_contract_allowances(row, payroll_str, contract_ref)

    def _build_contracts_support(self):
        """Build ContractsSupportHours sheet."""
        self.log("Building ContractsSupportHours...")

        for df in self.staff_data:
            for _, row in df.iterrows():
                title = str(self._safe_get(row, 'job_title', '')).strip()
                srg = get_srg_for_role(title)

                # Only support contracts
                if S2_STAFF_ROLE_GROUP_PATTERNS.get(srg, {}).get('teaching', False):
                    continue

                payroll = self._safe_get(row, 'payroll_number', '')
                payroll_str = str(payroll).strip() if self._safe_notna(payroll) else ''
                if not payroll_str or payroll_str == 'nan':
                    continue

                # Skip 0-hour contracts
                hours = self._safe_get(row, 'weekly_hours', 0)
                if not self._safe_notna(hours):
                    continue
                try:
                    if float(hours) == 0:
                        continue
                except (ValueError, TypeError):
                    continue

                school = str(self._safe_get(row, 'school_code', '')).strip()
                if school == 'nan': school = ''

                scale_point = str(self._safe_get(row, 'scale_point', '')).strip()
                if scale_point == 'nan': scale_point = '1'

                scale_point = self._normalize_scale_point(scale_point, 'support')

                role_code = self._create_role_code(title, srg)

                contract_ref = self._safe_get(row, 'contract_ref', '')
                if not self._safe_notna(contract_ref) or str(contract_ref) == 'nan':
                    contract_ref = f"{payroll_str}A"

                # Determine EQWP
                weeks_paid = self._safe_get(row, 'weeks_paid', 52.143)
                if not self._safe_notna(weeks_paid): weeks_paid = 52.143

                try:
                    weeks_paid_float = float(weeks_paid)
                except (ValueError, TypeError):
                    weeks_paid_float = 52.143

                if weeks_paid_float >= 52:
                    eqwp = "AYR"
                elif weeks_paid_float >= 40:
                    eqwp = "TTO_40"
                elif weeks_paid_float >= 39:
                    eqwp = "TTO_39"
                else:
                    eqwp = "TTO_38"

                forename = str(self._safe_get(row, 'forename', '')).strip()
                surname = str(self._safe_get(row, 'surname', '')).strip()
                if forename == 'nan': forename = ''
                if surname == 'nan': surname = ''

                self.template_data["ContractsSupportHours"].append({
                    "SchoolCode": school,
                    "StaffMemberCode": payroll_str,
                    "Reference": contract_ref,
                    "Title": f"{forename} {surname}".strip(),
                    "StaffRoleCode": role_code,
                    "PayScaleCode": "MAT_SUP",
                    "PayScaleGradeCode": "",
                    "PayScalePointCode": scale_point,
                    "DepartmentCode": "SFIN",
                    "FundCode": "",
                    "PensionCode": "LGPS",
                    "EquatedWeekPatternCode": eqwp,
                    "DateFrom": "2025-09-01",
                    "DateTo": "",
                    "WeeklyFteOrHpw": float(hours),
                    "MatEditOnly": False,
                    "NoIncrement": False,
                    "ContractTypeCode": "PERM",
                    "Notes": "",
                })

                # Check for allowances on support contracts too
                self._extract_contract_allowances(row, payroll_str, contract_ref)

    def _normalize_scale_point(self, point: str, scale_type: str) -> str:
        """Normalize scale point code."""
        point = str(point).strip()

        # Extract number
        numbers = re.findall(r'\d+', point)
        if not numbers:
            return "M1" if scale_type == 'teaching' else "1"

        num = int(numbers[0])

        if scale_type == 'teaching':
            if 'l' in point.lower():
                return f"L{num:02d}"
            elif 'u' in point.lower() or num > 6:
                return f"U{min(num, 3)}"
            else:
                return f"M{min(num, 6)}"
        else:
            return str(num)

    def _find_allowance_point_code(self, type_code: str, amount: float) -> str:
        """Find the matching allowance point code for a given amount."""
        for allowance in self.extracted_allowances:
            if allowance.type_code == type_code:
                # Find the point with matching or closest amount
                best_match = None
                best_diff = float('inf')
                for point in allowance.points:
                    diff = abs(point['amount'] - amount)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = point['code']
                    # Exact match
                    if diff < 0.01:
                        return point['code']
                if best_match:
                    return best_match
        # Default fallback
        return f"{type_code}1"

    def _extract_contract_allowances(self, row: pd.Series, staff_code: str, contract_ref: str):
        """Extract allowances from a contract row."""
        # Check for TLR
        tlr = self._safe_get(row, 'tlr_allowance', None)
        if not self._safe_notna(tlr):
            tlr = self._safe_get(row, 'tlr', None)
        if self._safe_notna(tlr):
            try:
                amount = float(str(tlr).replace('£', '').replace(',', '').strip())
                if amount > 0:
                    point_code = self._find_allowance_point_code('TLR', amount)
                    self.template_data["ContractAllowances"].append({
                        "StaffMemberCode": staff_code,
                        "ContractReference": contract_ref,
                        "AllowanceTypeCode": "TLR",
                        "AllowancePointCode": point_code,
                        "Amount": amount,
                        "DateFrom": "2025-09-01",
                        "DateTo": "",
                    })
            except:
                pass

        # Check for SEN
        sen = self._safe_get(row, 'sen_allowance', None)
        if not self._safe_notna(sen):
            sen = self._safe_get(row, 'sen', None)
        if self._safe_notna(sen):
            try:
                amount = float(str(sen).replace('£', '').replace(',', '').strip())
                if amount > 0:
                    point_code = self._find_allowance_point_code('SEN', amount)
                    self.template_data["ContractAllowances"].append({
                        "StaffMemberCode": staff_code,
                        "ContractReference": contract_ref,
                        "AllowanceTypeCode": "SEN",
                        "AllowancePointCode": point_code,
                        "Amount": amount,
                        "DateFrom": "2025-09-01",
                        "DateTo": "",
                    })
            except:
                pass

        # Check for Recruitment allowance
        rec = self._safe_get(row, 'recruitment_allowance', None)
        if not self._safe_notna(rec):
            rec = self._safe_get(row, 'recruitment', None)
        if self._safe_notna(rec):
            try:
                amount = float(str(rec).replace('£', '').replace(',', '').strip())
                if amount > 0:
                    point_code = self._find_allowance_point_code('REC', amount)
                    self.template_data["ContractAllowances"].append({
                        "StaffMemberCode": staff_code,
                        "ContractReference": contract_ref,
                        "AllowanceTypeCode": "REC",
                        "AllowancePointCode": point_code,
                        "Amount": amount,
                        "DateFrom": "2025-09-01",
                        "DateTo": "",
                    })
            except:
                pass

        # Check for Retention allowance
        ret = self._safe_get(row, 'retention_allowance', None)
        if not self._safe_notna(ret):
            ret = self._safe_get(row, 'retention', None)
        if self._safe_notna(ret):
            try:
                amount = float(str(ret).replace('£', '').replace(',', '').strip())
                if amount > 0:
                    point_code = self._find_allowance_point_code('RET', amount)
                    self.template_data["ContractAllowances"].append({
                        "StaffMemberCode": staff_code,
                        "ContractReference": contract_ref,
                        "AllowanceTypeCode": "RET",
                        "AllowancePointCode": point_code,
                        "Amount": amount,
                        "DateFrom": "2025-09-01",
                        "DateTo": "",
                    })
            except:
                pass

    def _build_contract_allowances(self):
        """Finalize ContractAllowances sheet - already built during contracts."""
        self.log("Building ContractAllowances...")
        # Already populated during _build_contracts_teaching

    def _build_finance_codes_s2(self):
        """Build Finance Codes S2 sheet."""
        self.log("Building Finance Codes S2...")

        # Add FTE codes for each staff role group
        for srg_code in S2_STAFF_ROLE_GROUP_PATTERNS.keys():
            fc = get_finance_codes_for_srg(srg_code)

            for code_type in ['weekly_fte', 'annual_fte', 'weekly_leave_adj', 'annual_leave_adj']:
                code = fc[code_type]
                title_map = {
                    'weekly_fte': f'{srg_code} Weekly FTE',
                    'annual_fte': f'{srg_code} Annual FTE',
                    'weekly_leave_adj': f'{srg_code} Weekly FTE Leave Adjustment',
                    'annual_leave_adj': f'{srg_code} Annual FTE Leave Adjustment',
                }

                self.template_data["Finance Codes S2"].append({
                    "FinanceCode": code,
                    "Title": title_map[code_type],
                    "FinanceCodeTypeCode": "STATISTICS",
                    "GroupingCode": "Z05",
                    "CustomGrouping": "ZZZ",
                    "LedgerCode": "COSTCTR",
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "FinanceCodeEnabled": True,
                })

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def process(self, customer_data_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Main processing entry point.

        1. Deeply analyze all customer data
        2. Extract pay scales, allowances, and staff data
        3. Build ALL template sheets
        4. Save output
        """
        self.log("="*60)
        self.log("S2 SPECIALIST AGENT - STARTING PROCESSING")
        self.log("="*60)

        # Phase 1: Analysis
        self.analyze_customer_data(customer_data_dir)

        # Phase 2: Build templates
        template_sheets = self.build_all_templates()

        # Phase 3: Save output
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"S2_complete_template_{timestamp}.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in template_sheets.items():
                if len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Add analysis summary
            summary_data = {
                "Metric": [
                    "Total Staff Members",
                    "Staff Roles",
                    "Teaching Contracts",
                    "Support Contracts",
                    "Pay Scales",
                    "Pay Scale Points",
                    "Allowance Types",
                    "Contract Allowances",
                    "Schools",
                    "Issues",
                    "Assumptions",
                ],
                "Value": [
                    len(template_sheets.get("StaffMembers", [])),
                    len(template_sheets.get("StfRole", [])),
                    len(template_sheets.get("ContractsTeachFTE", [])),
                    len(template_sheets.get("ContractsSupportHours", [])),
                    len(template_sheets.get("PayScales", [])),
                    len(template_sheets.get("PayScalePoints", [])),
                    len(template_sheets.get("AllowanceTypes", [])),
                    len(template_sheets.get("ContractAllowances", [])),
                    len(self.schools_found),
                    len(self.issues),
                    len(self.assumptions),
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="_Summary", index=False)

            if self.issues:
                pd.DataFrame({"Issues": self.issues}).to_excel(writer, sheet_name="_Issues", index=False)

        self.log(f"\nOutput saved to: {output_file}")

        return {
            "success": len(self.issues) == 0,
            "output_file": output_file,
            "template_sheets": template_sheets,
            "analysis_reports": self.analysis_reports,
            "issues": self.issues,
            "assumptions": self.assumptions,
            "summary": {
                "staff_members": len(template_sheets.get("StaffMembers", [])),
                "staff_roles": len(template_sheets.get("StfRole", [])),
                "teaching_contracts": len(template_sheets.get("ContractsTeachFTE", [])),
                "support_contracts": len(template_sheets.get("ContractsSupportHours", [])),
                "pay_scales": len(template_sheets.get("PayScales", [])),
                "pay_scale_points": len(template_sheets.get("PayScalePoints", [])),
                "allowances": len(template_sheets.get("ContractAllowances", [])),
                "schools": list(self.schools_found),
            }
        }


def run_s2_specialist(customer_data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Run the S2 specialist agent."""
    agent = S2SpecialistAgent()
    return agent.process(customer_data_dir, output_dir)
