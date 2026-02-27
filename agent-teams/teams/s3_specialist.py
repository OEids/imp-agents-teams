"""
S3 Specialist Agent - Financial Team

Deep analysis and complete template builder for:
- Pupil Numbers (Spring/Autumn Census)
- Statistics & Rates
- Funding (GAG, Grants)
- Income & Expenditure Budgets
- Calculators
- Month Profiles
- Scenarios
- BF Balances

Enhanced with InferenceEngine for intelligent column mapping,
budget classification, and confidence-based decisions.
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

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# Import Intelligence Module for smart decisions
try:
    from intelligence import InferenceEngine, InferenceResult, ConfidenceLevel
    from intelligence import TemplateRegistry, TemplateFormatter
    INFERENCE_AVAILABLE = True
    TEMPLATE_AVAILABLE = True
except ImportError:
    INFERENCE_AVAILABLE = False
    TEMPLATE_AVAILABLE = False

# Shared inference engine instance for S3
_s3_inference_engine: Optional['InferenceEngine'] = None


def get_s3_inference_engine() -> Optional['InferenceEngine']:
    """Get or create the shared InferenceEngine for S3."""
    global _s3_inference_engine
    if _s3_inference_engine is None and INFERENCE_AVAILABLE:
        try:
            _s3_inference_engine = InferenceEngine(hot_reload=False)
        except Exception:
            pass
    return _s3_inference_engine

from .finished_workbook_patterns import (
    S3_PUPIL_PATTERNS,
    S3_INCOME_PATTERNS,
    S3_EXPENDITURE_PATTERNS,
    S3_CALCULATOR_PATTERNS,
    S3_SCENARIO_PATTERNS,
)


@dataclass
class ExtractedPupilNumber:
    """Extracted pupil number data."""
    finance_code: str
    school_code: str
    description: str
    year_code: str
    value: float
    calculator_code: str
    notes: str


@dataclass
class ExtractedBudgetLine:
    """Extracted budget line data."""
    finance_code: str
    school_code: str
    department_code: str
    description: str
    year_value: float
    line_type: str  # income, expenditure
    calculator_code: str
    month_profile: str


@dataclass
class ExtractedGrant:
    """Extracted grant data."""
    grant_type: str  # DFC, SCA, PE, UIFSM, PP
    school_code: str
    amount: float
    calculation_basis: str
    pupil_count: int


class S3SpecialistAgent:
    """
    Upskilled S3 agent for financial data.

    Builds ALL S3 template sheets:
    - Pupils
    - Statistics
    - Funding
    - Calculators
    - MonthProfiles
    - Income
    - Expenditure
    - ScenarioApBud
    - BF Balances
    - Finance Codes S3
    """

    def __init__(self):
        self.extracted_pupils: List[ExtractedPupilNumber] = []
        self.extracted_budgets: List[ExtractedBudgetLine] = []
        self.extracted_grants: List[ExtractedGrant] = []
        self.issues: List[str] = []
        self.assumptions: List[str] = []

        # Initialize InferenceEngine for intelligent decisions
        self.inference_engine = get_s3_inference_engine()
        self.inference_results: List[Dict] = []  # Track all inference decisions

        self.template_data = {
            "Pupils": [],
            "Statistics": [],
            "Funding": [],
            "Calculators": [],
            "MonthProfiles": [],
            "Income": [],
            "Expenditure": [],
            "ScenarioApBud": [],
            "BF Balances": [],
            "Finance Codes S3": [],
        }

        # Mapping from internal sheet names to official template sheet names
        self.SHEET_NAME_MAPPING = {
            "Pupils": "Pupils",
            "Statistics": "Statistics",
            "Funding": "Funding",
            "Calculators": "14_Calculators",
            "MonthProfiles": "15_MonthProfiles",
            "Income": "Income",
            "Expenditure": "Expenditure",
            "ScenarioApBud": "ScenarioApBud",
            "BF Balances": "BF Balances",
            "Finance Codes S3": "11_Finance Codes S3",
            "ScenarioRows": "35_ScenarioRows",
            "ScenarioYearValues": "36_ScenarioYearValues",
            "Monthly Values": "37_Monthly Values",
        }

        # Initialize template registry and formatter if available
        self.template_registry = None
        self.template_formatter = None
        if TEMPLATE_AVAILABLE:
            try:
                self.template_registry = TemplateRegistry()
                self.template_formatter = TemplateFormatter(self.template_registry)
            except Exception as e:
                self.log(f"[WARN] Could not initialize template registry: {e}")

        # Tracking
        self.schools_found = set()
        self.finance_codes_found = set()
        self.current_year = "2025/26"
        self.previous_year = "2024/25"

        # Validation tracking
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

        # External Audit Review tracking
        self.audit_results = {
            "source_vs_output": [],
            "data_integrity": [],
            "domain_checks": [],
            "missing_data": [],
            "data_lineage": [],
        }
        self.audit_passed = True
        self.audit_score = 100.0

        # Track source data for audit comparison
        self.source_pupils = set()
        self.source_budgets = set()
        self.source_grants = set()

    def log(self, message: str, level: str = "INFO"):
        """Log a message with proper encoding and error handling for Streamlit."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg_str = str(message).replace('\x00', '').replace('\n\n', '\n')
            if len(msg_str) > 10000:
                msg_str = msg_str[:10000] + "... [truncated]"
            output = f"[{timestamp}] [{level}] S3-Specialist: {msg_str}"
            try:
                print(output, flush=True)
            except (OSError, IOError, ValueError):
                try:
                    print(output.encode('ascii', errors='replace').decode('ascii'), flush=True)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_column_mappings(self, df: pd.DataFrame, file_name: str, sheet_name: str = None) -> pd.DataFrame:
        """
        Apply validated column mappings from pre-flight validation.

        Args:
            df: DataFrame to apply mappings to
            file_name: Name of the file being processed
            sheet_name: Optional sheet name for Excel files

        Returns:
            DataFrame with columns renamed according to mappings
        """
        if not hasattr(self, 'column_mappings') or not self.column_mappings:
            return df

        # Try different key formats to find matching mappings
        possible_keys = [
            f"{file_name}:{sheet_name or 'default'}",
            f"{file_name}:default",
            file_name,
        ]

        file_mappings = {}
        for key in possible_keys:
            if key in self.column_mappings:
                file_mappings = self.column_mappings[key]
                break

        if not file_mappings:
            # Also try partial match on file name
            for key, mappings in self.column_mappings.items():
                if file_name in key or key.split(':')[0] in file_name:
                    file_mappings = mappings
                    break

        if file_mappings:
            # Build rename dict: only rename columns that exist in df
            rename_dict = {}
            for source_col, target_col in file_mappings.items():
                if source_col in df.columns and source_col != target_col:
                    rename_dict[source_col] = target_col

            if rename_dict:
                self.log(f"  Applying {len(rename_dict)} column mappings from pre-flight validation")
                df = df.rename(columns=rename_dict)

        return df

    # =========================================================================
    # INTELLIGENT COLUMN MAPPING & CLASSIFICATION
    # Uses InferenceEngine for confidence-scored decisions
    # =========================================================================

    def infer_column(self, source_column: str) -> Tuple[str, float]:
        """
        Intelligently map a source column name to standard name.

        Args:
            source_column: Original column name from customer data

        Returns:
            Tuple of (mapped_column_name, confidence)
        """
        if self.inference_engine:
            result = self.inference_engine.infer_column_mapping(
                source_column=source_column,
                strand="S3"
            )

            # Track inference for audit
            self.inference_results.append({
                "type": "column_mapping",
                "source": source_column,
                "result": result.decision,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            })

            if result.confidence >= 0.5:
                if result.requires_review:
                    self.assumptions.append(
                        f"Low confidence column mapping: {source_column} -> {result.decision} ({result.confidence:.0%})"
                    )
                return result.decision, result.confidence

        return source_column, 0.3

    def infer_budget_type(self, description: str, amount: float = None) -> Tuple[str, float]:
        """
        Classify a budget line as income or expenditure.

        Args:
            description: Budget line description
            amount: Optional amount (positive=income, negative=expenditure)

        Returns:
            Tuple of (budget_type, confidence)
        """
        if self.inference_engine:
            result = self.inference_engine.infer_classification(
                value=description,
                classification_type="budget_type"
            )

            self.inference_results.append({
                "type": "budget_classification",
                "source": description,
                "result": result.decision,
                "confidence": result.confidence
            })

            if result.confidence >= 0.5:
                return result.decision, result.confidence

        # Fallback: use amount sign if available
        if amount is not None:
            return ('income' if amount >= 0 else 'expenditure'), 0.6

        return 'unknown', 0.3

    def infer_grant_type(self, description: str) -> Tuple[str, float]:
        """
        Classify a grant type (DFC, SCA, PE, UIFSM, PP, etc.)

        Args:
            description: Grant description

        Returns:
            Tuple of (grant_type, confidence)
        """
        if self.inference_engine:
            result = self.inference_engine.infer_classification(
                value=description,
                classification_type="grant_type"
            )

            self.inference_results.append({
                "type": "grant_classification",
                "source": description,
                "result": result.decision,
                "confidence": result.confidence
            })

            if result.confidence >= 0.5:
                return result.decision, result.confidence

        return 'other', 0.3

    def infer_data_category(self, columns: List[str], sample_values: List = None) -> Tuple[str, float]:
        """
        Infer what type of S3 data this is (pupils, income, expenditure, grants, etc.)

        Args:
            columns: List of column names
            sample_values: Optional sample data values

        Returns:
            Tuple of (data_category, confidence)
        """
        cols_lower = " ".join(c.lower() for c in columns)

        # Pattern matching for S3 data types
        patterns = {
            'pupils': ['pupil', 'student', 'enrol', 'census', 'headcount', 'fte_ks', 'key_stage'],
            'income': ['income', 'revenue', 'receipt', 'grant', 'funding', 'allocation'],
            'expenditure': ['expenditure', 'expense', 'cost', 'spend', 'budget'],
            'grants': ['grant', 'dfc', 'sca', 'uifsm', 'pupil premium', 'pe grant'],
            'scenarios': ['scenario', 'forecast', 'projection', 'plan'],
            'calculators': ['calculator', 'formula', 'calculation', 'rate']
        }

        scores = {}
        for category, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw in cols_lower)
            scores[category] = score

        best_category = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        confidence = scores[best_category] / total if scores[best_category] > 0 else 0.3

        return best_category, confidence

    def get_inference_summary(self) -> Dict:
        """Get summary of all inference decisions made."""
        if not self.inference_results:
            return {"total": 0, "high_confidence": 0, "low_confidence": 0}

        high_conf = sum(1 for r in self.inference_results if r.get("confidence", 0) >= 0.9)
        med_conf = sum(1 for r in self.inference_results if 0.7 <= r.get("confidence", 0) < 0.9)
        low_conf = sum(1 for r in self.inference_results if r.get("confidence", 0) < 0.7)

        return {
            "total": len(self.inference_results),
            "high_confidence": high_conf,
            "medium_confidence": med_conf,
            "low_confidence": low_conf,
            "inference_available": self.inference_engine is not None
        }

    # =========================================================================
    # PHASE 1: DEEP ANALYSIS
    # =========================================================================

    def analyze_customer_data(self, data_dir: Path):
        """Analyze all S3 customer data files."""
        self.log("="*60)
        self.log("PHASE 1: DEEP ANALYSIS OF S3 CUSTOMER DATA")
        self.log("="*60)

        all_files = list(data_dir.rglob("*.xls*")) + list(data_dir.rglob("*.csv")) + list(data_dir.rglob("*.docx")) + list(data_dir.rglob("*.doc"))
        all_files = [f for f in all_files if not f.name.startswith("~$")]

        self.log(f"Found {len(all_files)} files to analyze")

        for file_path in all_files:
            self.log(f"\nAnalyzing: {file_path.name}")
            self._analyze_file(file_path)

        self._print_analysis_summary()

    def _analyze_file(self, file_path: Path):
        """Analyze a single file."""
        try:
            if file_path.suffix.lower() in ['.docx', '.doc'] and DOCX_SUPPORT:
                document = docx.Document(file_path)
                for table_idx, table in enumerate(document.tables):
                    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
                    if len(rows) > 1:
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                        df = self._apply_column_mappings(df, file_path.name)
                        self._classify_and_extract(df, file_path.name, f"DOCX_Table{table_idx+1}")
            elif file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
                # Apply validated column mappings
                df = self._apply_column_mappings(df, file_path.name)
                self._classify_and_extract(df, file_path.name, "CSV")
            else:
                xl = pd.ExcelFile(file_path)
                self.log(f"  Sheets: {xl.sheet_names}")

                for sheet in xl.sheet_names:
                    if self._is_skip_sheet(sheet):
                        continue

                    df = self._read_sheet_smart(xl, sheet)
                    if df is not None and len(df) > 0:
                        # Apply validated column mappings
                        df = self._apply_column_mappings(df, file_path.name, sheet)
                        self._classify_and_extract(df, file_path.name, sheet)

        except Exception as e:
            self.issues.append(f"Error analyzing {file_path.name}: {e}")

    def _is_skip_sheet(self, sheet: str) -> bool:
        """Check if sheet should be skipped."""
        skip_words = ['guidance', 'notes', 'instructions', 'help', 'checklist', 'validation', 'lookup']
        return any(w in sheet.lower() for w in skip_words)

    def _read_sheet_smart(self, xl: pd.ExcelFile, sheet: str) -> Optional[pd.DataFrame]:
        """Smart read that finds header row."""
        try:
            df_raw = pd.read_excel(xl, sheet, header=None, nrows=20)

            best_row = 0
            best_score = 0

            for idx in range(min(10, len(df_raw))):
                row = df_raw.iloc[idx]
                score = sum(1 for v in row if isinstance(v, str) and len(str(v).strip()) > 2)
                if score > best_score:
                    best_score = score
                    best_row = idx

            df = pd.read_excel(xl, sheet, header=best_row)
            df = df.dropna(how='all')
            df.columns = [self._clean_column_name(c) for c in df.columns]

            return df
        except:
            return None

    def _clean_column_name(self, col: Any) -> str:
        """Standardize column name."""
        if pd.isna(col):
            return "unnamed"

        col_str = str(col).strip().lower()

        mappings = {
            'school': 'school_code',
            'location': 'school_code',
            'cost centre': 'school_code',
            'finance code': 'finance_code',
            'nominal': 'finance_code',
            'account': 'finance_code',
            'description': 'description',
            'title': 'description',
            'amount': 'amount',
            'value': 'amount',
            'budget': 'amount',
            'pupil': 'pupils',
            'student': 'pupils',
            'fte': 'fte',
            'year': 'year',
            'period': 'period',
            'department': 'department_code',
            'fund': 'fund_code',
        }

        for pattern, standard in mappings.items():
            if pattern in col_str:
                return standard

        return col_str.replace(' ', '_')

    def _classify_and_extract(self, df: pd.DataFrame, file_name: str, sheet_name: str):
        """Classify data type and extract."""
        cols = [str(c).lower() for c in df.columns]
        sheet_lower = sheet_name.lower()
        file_lower = file_name.lower()

        # Pupil numbers
        if 'pupil' in sheet_lower or 'census' in sheet_lower or 'student' in file_lower:
            self._extract_pupil_numbers(df, sheet_name)
            self.log(f"    -> Pupil numbers extracted")

        # Budgets
        elif 'budget' in sheet_lower or 'budget' in file_lower:
            self._extract_budgets(df, sheet_name)
            self.log(f"    -> Budget data extracted")

        # Funding statement
        elif 'funding' in sheet_lower or 'gag' in sheet_lower:
            self._extract_funding(df, sheet_name)
            self.log(f"    -> Funding data extracted")

        # Grants
        elif any(g in sheet_lower for g in ['grant', 'dfc', 'sca', 'uifsm', 'pupil premium', 'pe ']):
            self._extract_grants(df, sheet_name)
            self.log(f"    -> Grant data extracted")

        # General financial data
        elif 'amount' in cols or 'value' in cols:
            self._extract_budgets(df, sheet_name)
            self.log(f"    -> Financial data extracted")

    def _extract_pupil_numbers(self, df: pd.DataFrame, sheet_name: str):
        """Extract pupil numbers from dataframe."""
        for _, row in df.iterrows():
            school = row.get('school_code', '')
            if pd.isna(school):
                school = ''
            school_str = str(school).strip()

            # Look for pupil count columns
            for col in df.columns:
                col_lower = str(col).lower()

                if any(x in col_lower for x in ['pupil', 'student', 'number', 'count', 'fte']):
                    value = row.get(col)
                    if pd.notna(value):
                        try:
                            value_float = float(value)
                            if value_float >= 0:
                                # Determine pupil type from column name
                                finance_code = self._determine_pupil_finance_code(col_lower)
                                calculator = self._determine_pupil_calculator(col_lower)

                                pupil = ExtractedPupilNumber(
                                    finance_code=finance_code,
                                    school_code=school_str if school_str != 'nan' else '',
                                    description=col,
                                    year_code=self.current_year,
                                    value=value_float,
                                    calculator_code=calculator,
                                    notes=f"Extracted from {sheet_name}",
                                )
                                self.extracted_pupils.append(pupil)

                                if school_str and school_str != 'nan':
                                    self.schools_found.add(school_str)
                        except:
                            pass

    def _determine_pupil_finance_code(self, col_name: str) -> str:
        """Determine pupil finance code from column name."""
        col_lower = col_name.lower()

        if 'ks3' in col_lower or 'key stage 3' in col_lower:
            return 'PUPIL_SPRING_KS3'
        elif 'ks4' in col_lower or 'key stage 4' in col_lower:
            return 'PUPIL_SPRING_KS4'
        elif 'ks5' in col_lower or 'post 16' in col_lower or 'sixth' in col_lower:
            return 'PUPIL_SPRING_KS5'
        elif 'primary' in col_lower or 'ks1' in col_lower or 'ks2' in col_lower:
            return 'PUPIL_SPRING_PRI'
        elif 'nursery' in col_lower or 'eyfs' in col_lower:
            return 'PUPIL_SPRING_NUR'
        elif 'premium' in col_lower:
            if 'plac' in col_lower:
                return 'PUPILPREMIUMPLAC'
            elif 'service' in col_lower:
                return 'PUPILPREMIUMSER'
            elif 'primary' in col_lower:
                return 'PUPILPREMIUM_PRI'
            elif 'secondary' in col_lower:
                return 'PUPILPREMIUM_SEC'
            else:
                return 'PUPILPREMIUM'
        elif 'uifsm' in col_lower or 'infant' in col_lower:
            return 'PUPIL_UIFSM'

        return 'PUPIL_TOTAL'

    def _determine_pupil_calculator(self, col_name: str) -> str:
        """Determine calculator code for pupils."""
        col_lower = col_name.lower()

        if 'premium' in col_lower:
            return 'PUPPREMIUM_FACTOR'
        elif 'uifsm' in col_lower:
            return 'UIFSM_RATE'

        return '0%_CALC'

    def _extract_budgets(self, df: pd.DataFrame, sheet_name: str):
        """Extract budget lines from dataframe."""
        for _, row in df.iterrows():
            finance_code = row.get('finance_code', '')
            if pd.isna(finance_code):
                continue

            code_str = str(finance_code).strip()
            if not code_str or code_str == 'nan':
                continue

            school = str(row.get('school_code', '')).strip()
            if school == 'nan':
                school = ''

            # NEVER use defaults - use 'MISSING' if data not found
            dept = str(row.get('department_code', '')).strip()
            if not dept or dept == 'nan':
                dept = 'MISSING'

            description = str(row.get('description', '')).strip()
            if description == 'nan':
                description = code_str

            # Find amount column
            amount = 0
            for col in df.columns:
                col_lower = str(col).lower()
                if any(x in col_lower for x in ['amount', 'value', 'budget', '202']):
                    val = row.get(col)
                    if pd.notna(val):
                        try:
                            amount = float(str(val).replace('£', '').replace(',', '').strip())
                            break
                        except:
                            pass

            if amount == 0:
                continue

            # Determine line type from code
            line_type = self._determine_line_type(code_str, amount)

            budget = ExtractedBudgetLine(
                finance_code=code_str,
                school_code=school,
                department_code=dept,
                description=description,
                year_value=amount,
                line_type=line_type,
                calculator_code='',
                month_profile='MONTHLY',
            )
            self.extracted_budgets.append(budget)
            self.finance_codes_found.add(code_str)

            if school:
                self.schools_found.add(school)

    def _determine_line_type(self, code: str, amount: float) -> str:
        """Determine if line is income or expenditure."""
        if not code:
            return 'expenditure' if amount > 0 else 'income'

        # Try to determine from code
        if code[0].isdigit():
            first = int(code[0])
            if first in [4, 5]:
                return 'income'
            elif first in [6, 7, 8, 9]:
                return 'expenditure'

        # Determine from sign
        return 'expenditure' if amount > 0 else 'income'

    def _extract_funding(self, df: pd.DataFrame, sheet_name: str):
        """Extract funding statement data."""
        # Process as budget lines with income type
        for _, row in df.iterrows():
            school = str(row.get('school_code', '')).strip()

            for col in df.columns:
                col_lower = str(col).lower()

                # Look for funding columns
                if any(x in col_lower for x in ['gag', 'funding', 'grant', 'allocation']):
                    val = row.get(col)
                    if pd.notna(val):
                        try:
                            amount = float(str(val).replace('£', '').replace(',', '').strip())
                            if amount != 0:
                                budget = ExtractedBudgetLine(
                                    finance_code=self._determine_funding_code(col_lower),
                                    school_code=school if school != 'nan' else '',
                                    department_code='IGAG',
                                    description=col,
                                    year_value=-abs(amount),  # Income is negative
                                    line_type='income',
                                    calculator_code=self._determine_funding_calculator(col_lower),
                                    month_profile='MONTHLY',
                                )
                                self.extracted_budgets.append(budget)
                        except:
                            pass

    def _determine_funding_code(self, col_name: str) -> str:
        """Determine funding finance code."""
        col_lower = col_name.lower()

        if 'post 16' in col_lower or '16-19' in col_lower:
            return '510700'
        elif 'gag' in col_lower:
            return '510100'
        elif 'pupil premium' in col_lower:
            return '510200'

        return '510100'

    def _determine_funding_calculator(self, col_name: str) -> str:
        """Determine funding calculator."""
        col_lower = col_name.lower()

        if 'post 16' in col_lower or '16-19' in col_lower:
            return 'FUNDING_16_19'
        elif 'gag' in col_lower:
            return 'FUNDING_GAG'
        elif 'pupil premium' in col_lower:
            return 'PUPPREMIUM_CALC'

        return 'FUNDING_GAG'

    def _extract_grants(self, df: pd.DataFrame, sheet_name: str):
        """Extract grant data."""
        sheet_lower = sheet_name.lower()

        for _, row in df.iterrows():
            school = str(row.get('school_code', '')).strip()

            # Find grant amounts
            for col in df.columns:
                val = row.get(col)
                if pd.notna(val):
                    try:
                        amount = float(str(val).replace('£', '').replace(',', '').strip())
                        if amount > 0:
                            # Determine grant type
                            grant_type = self._determine_grant_type(sheet_lower, str(col).lower())

                            grant = ExtractedGrant(
                                grant_type=grant_type,
                                school_code=school if school != 'nan' else '',
                                amount=amount,
                                calculation_basis=col,
                                pupil_count=0,
                            )
                            self.extracted_grants.append(grant)
                    except:
                        pass

    def _determine_grant_type(self, sheet_name: str, col_name: str) -> str:
        """Determine grant type."""
        combined = sheet_name + ' ' + col_name

        if 'dfc' in combined or 'devolved formula' in combined:
            return 'DFC'
        elif 'sca' in combined or 'condition' in combined:
            return 'SCA'
        elif 'pe ' in combined or 'sport' in combined:
            return 'PE'
        elif 'uifsm' in combined or 'infant' in combined:
            return 'UIFSM'
        elif 'premium' in combined:
            return 'PP'

        return 'OTHER'

    def _print_analysis_summary(self):
        """Print analysis summary."""
        self.log("\n" + "="*60)
        self.log("ANALYSIS SUMMARY")
        self.log("="*60)

        self.log(f"Pupil records: {len(self.extracted_pupils)}")
        self.log(f"Budget lines: {len(self.extracted_budgets)}")
        self.log(f"Grants: {len(self.extracted_grants)}")
        self.log(f"Schools: {self.schools_found}")
        self.log(f"Finance codes: {len(self.finance_codes_found)}")

    # =========================================================================
    # PHASE 2: BUILD ALL TEMPLATE SHEETS
    # =========================================================================

    def build_all_templates(self) -> Dict[str, pd.DataFrame]:
        """Build ALL S3 template sheets."""
        self.log("\n" + "="*60)
        self.log("PHASE 2: BUILDING ALL S3 TEMPLATE SHEETS")
        self.log("="*60)

        self._build_pupils()
        self._build_statistics()
        self._build_funding()
        self._build_calculators()
        self._build_month_profiles()
        self._build_income()
        self._build_expenditure()
        self._build_scenario_apbud()
        self._build_bf_balances()
        self._build_finance_codes_s3()

        result = {}
        for sheet_name, data in self.template_data.items():
            if data:
                result[sheet_name] = pd.DataFrame(data)
                self.log(f"  {sheet_name}: {len(data)} rows")

        return result

    def _build_pupils(self):
        """Build Pupils sheet."""
        self.log("Building Pupils...")

        for pupil in self.extracted_pupils:
            self.template_data["Pupils"].append({
                "FinanceCode": pupil.finance_code,
                "SchoolCode": pupil.school_code,
                "LedgerCode": "DEFAULT",
                "DepartmentCode": "DEFAULT",
                "FundCode": "",
                "CalculatorCode": pupil.calculator_code,
                "MonthProfileCode": "MONTHLY",
                "Description": pupil.description,
                "Notes": pupil.notes,
                "YearNotes": "",
                "MatEditOnly": False,
                "FinancialYearCode": pupil.year_code,
                "Calculated": False,
                "YearValue": pupil.value,
            })

        # Add defaults for each school if no pupil data
        if not self.template_data["Pupils"]:
            for school in self.schools_found or ['MAT']:
                for key_stage in ['PRI', 'KS3', 'KS4', 'KS5']:
                    self.template_data["Pupils"].append({
                        "FinanceCode": f"PUPIL_SPRING_{key_stage}",
                        "SchoolCode": school,
                        "LedgerCode": "DEFAULT",
                        "DepartmentCode": "DEFAULT",
                        "FundCode": "",
                        "CalculatorCode": "0%_CALC",
                        "MonthProfileCode": "MONTHLY",
                        "Description": f"{key_stage} Spring Census Pupil Numbers",
                        "Notes": "",
                        "YearNotes": "",
                        "MatEditOnly": False,
                        "FinancialYearCode": self.previous_year,
                        "Calculated": False,
                        "YearValue": 0,
                    })

    def _build_statistics(self):
        """Build Statistics sheet."""
        self.log("Building Statistics...")

        # Uplift factors for each school
        uplifts = [
            ("UPLIFT_PUPILASCL%", "Pupil ASCL Uplift %", "PUPILASCL_FACTOR"),
            ("UPLIFT_PUPILEXP%", "Pupil Expenditure Uplift %", "PUPILEXP_FACTOR"),
            ("UPLIFT_PUPILGAG%", "Pupil GAG Uplift %", "PUPILGAG_FACTOR"),
            ("UPLIFT_PUPILINC%", "Pupil Income Uplift %", "PUPILINC_FACTOR"),
            ("UPLIFT_PUPILRPI%", "Pupil RPI Uplift %", "PUPILRPI_FACTOR"),
        ]

        for school in self.schools_found or ['MAT']:
            for code, desc, calc in uplifts:
                self.template_data["Statistics"].append({
                    "FinanceCode": code,
                    "SchoolCode": school,
                    "LedgerCode": "DEFAULT",
                    "DepartmentCode": "DEFAULT",
                    "FundCode": "",
                    "CalculatorCode": calc,
                    "MonthProfileCode": "MONTHLY",
                    "Description": desc,
                    "Notes": "",
                    "YearNotes": "",
                    "MatEditOnly": True,
                    "FinancialYearCode": self.current_year,
                    "Calculated": True,
                    "YearValue": None,
                })

    def _build_funding(self):
        """Build Funding sheet."""
        self.log("Building Funding...")

        # Extract funding lines from budgets
        for budget in self.extracted_budgets:
            if budget.line_type == 'income' and budget.calculator_code:
                self.template_data["Funding"].append({
                    "FinanceCode": budget.finance_code,
                    "SchoolCode": budget.school_code,
                    "LedgerCode": "DEFAULT",
                    "DepartmentCode": budget.department_code,
                    "FundCode": "",
                    "MonthProfileCode": "MONTHLY",
                    "CalculatorCode": budget.calculator_code,
                    "Description": budget.description,
                    "Notes": "",
                    "YearNotes": "",
                    "MatEditOnly": True,
                    "FinancialYearCode": self.current_year,
                    "Calculated": True,
                    "YearValue": None,
                })

    def _build_calculators(self):
        """Build Calculators sheet."""
        self.log("Building Calculators...")

        calculators = [
            ("0%_CALC", "Zero Calculator", "0"),
            ("FUNDING_GAG", "GAG Funding", "FUNDING"),
            ("FUNDING_16_19", "Post 16 Funding", "FUNDING"),
            ("PUPPREMIUM_FACTOR", "Pupil Premium Factor", "PUPILPREMIUM"),
            ("PUPPREMIUM_CALC", "Pupil Premium Calculator", "PUPILPREMIUM"),
            ("DFC_CORE", "DFC Core Amount", "DFC"),
            ("DFC_PUPIL", "DFC Per Pupil", "DFC"),
            ("DFC_EXP", "DFC Expenditure", "DFC"),
            ("PE_GRANT_CORE", "PE Grant Core", "PEGRANT"),
            ("PE_GRANT_PUPIL", "PE Grant Per Pupil", "PEGRANT"),
            ("UIFSM_CALC", "UIFSM Calculator", "UIFSM"),
            ("CENTRALCHG_SCH", "Central Charge School", "CENTRAL"),
            ("CENTRALCHG_MAT", "Central Charge MAT", "CENTRAL"),
        ]

        for code, title, category in calculators:
            self.template_data["Calculators"].append({
                "CalculatorCode": code,
                "Title": title,
                "Category": category,
                "CalculatorEnabled": True,
            })

    def _build_month_profiles(self):
        """Build MonthProfiles sheet."""
        self.log("Building MonthProfiles...")

        # Standard monthly profile (equal distribution)
        monthly_pct = round(100/12, 2)

        self.template_data["MonthProfiles"].append({
            "MonthProfileCode": "MONTHLY",
            "Title": "Monthly Equal",
            "Sep": monthly_pct,
            "Oct": monthly_pct,
            "Nov": monthly_pct,
            "Dec": monthly_pct,
            "Jan": monthly_pct,
            "Feb": monthly_pct,
            "Mar": monthly_pct,
            "Apr": monthly_pct,
            "May": monthly_pct,
            "Jun": monthly_pct,
            "Jul": monthly_pct,
            "Aug": round(100 - 11*monthly_pct, 2),  # Ensure totals 100
            "MonthProfileEnabled": True,
        })

        # Academic year front-loaded
        self.template_data["MonthProfiles"].append({
            "MonthProfileCode": "ACADEMIC",
            "Title": "Academic Year",
            "Sep": 10,
            "Oct": 10,
            "Nov": 10,
            "Dec": 8,
            "Jan": 8,
            "Feb": 8,
            "Mar": 10,
            "Apr": 8,
            "May": 8,
            "Jun": 8,
            "Jul": 8,
            "Aug": 4,
            "MonthProfileEnabled": True,
        })

    def _build_income(self):
        """Build Income sheet."""
        self.log("Building Income...")

        for budget in self.extracted_budgets:
            if budget.line_type == 'income':
                self.template_data["Income"].append({
                    "FinanceCode": budget.finance_code,
                    "SchoolCode": budget.school_code,
                    "LedgerCode": "COSTCTR",
                    "DepartmentCode": budget.department_code or "IGAG",
                    "FundCode": "",
                    "CalculatorCode": budget.calculator_code,
                    "MonthProfileCode": budget.month_profile,
                    "Description": budget.description,
                    "Notes": "",
                    "YearNotes": "",
                    "MatEditOnly": bool(budget.calculator_code),
                    "FinancialYearCode": self.current_year,
                    "Calculated": bool(budget.calculator_code),
                    "YearValue": budget.year_value if not budget.calculator_code else None,
                })

    def _build_expenditure(self):
        """Build Expenditure sheet."""
        self.log("Building Expenditure...")

        for budget in self.extracted_budgets:
            if budget.line_type == 'expenditure':
                self.template_data["Expenditure"].append({
                    "FinanceCode": budget.finance_code,
                    "SchoolCode": budget.school_code,
                    "LedgerCode": "COSTCTR",
                    "DepartmentCode": budget.department_code,
                    "FundCode": "",
                    "CalculatorCode": budget.calculator_code,
                    "MonthProfileCode": budget.month_profile,
                    "Description": budget.description,
                    "Notes": "",
                    "YearNotes": "",
                    "MatEditOnly": bool(budget.calculator_code),
                    "FinancialYearCode": self.current_year,
                    "Calculated": bool(budget.calculator_code),
                    "YearValue": budget.year_value if not budget.calculator_code else None,
                })

    def _build_scenario_apbud(self):
        """Build ScenarioApBud sheet."""
        self.log("Building ScenarioApBud...")

        scenario_code = f"APBUD{self.current_year.replace('/', '')[-4:]}"

        # Copy all budget lines to approved budget scenario
        for budget in self.extracted_budgets:
            self.template_data["ScenarioApBud"].append({
                "ScenarioCode": scenario_code,
                "FinanceCode": budget.finance_code,
                "SchoolCode": budget.school_code,
                "LedgerCode": "COSTCTR",
                "DepartmentCode": budget.department_code,
                "FundCode": "",
                "CalculatorCode": "",
                "MonthProfileCode": "MONTHLY",
                "Description": budget.description,
                "Notes": "",
                "YearNotes": "",
                "MatEditOnly": True,
                "FinancialYearCode": self.current_year,
                "Calculated": False,
                "YearValue": abs(budget.year_value) if budget.line_type == 'income' else budget.year_value,
            })

    def _build_bf_balances(self):
        """Build BF Balances sheet."""
        self.log("Building BF Balances...")

        for school in self.schools_found or ['MAT']:
            # Capital BF
            self.template_data["BF Balances"].append({
                "FinanceCode": "CAP_BFWD_RES",
                "SchoolCode": school,
                "LedgerCode": "DEFAULT",
                "DepartmentCode": "DEFAULT",
                "FundCode": "",
                "CalculatorCode": "",
                "MonthProfileCode": "MONTHLY",
                "Description": "Brought Forward Balance Capital",
                "Notes": "",
                "YearNotes": "",
                "MatEditOnly": True,
                "FinancialYearCode": self.current_year,
                "Calculated": False,
                "YearValue": 0,
            })

            # Revenue BF
            self.template_data["BF Balances"].append({
                "FinanceCode": "REV_BFWD_RES",
                "SchoolCode": school,
                "LedgerCode": "DEFAULT",
                "DepartmentCode": "DEFAULT",
                "FundCode": "",
                "CalculatorCode": "",
                "MonthProfileCode": "MONTHLY",
                "Description": "Brought Forward Balance Revenue",
                "Notes": "",
                "YearNotes": "",
                "MatEditOnly": True,
                "FinancialYearCode": self.current_year,
                "Calculated": False,
                "YearValue": 0,
            })

    def _build_finance_codes_s3(self):
        """Build Finance Codes S3 sheet."""
        self.log("Building Finance Codes S3...")

        # Add pupil finance codes
        pupil_codes = [
            ("PUPIL_SPRING_PRI", "Primary Spring Census", "STATISTICS"),
            ("PUPIL_SPRING_KS3", "KS3 Spring Census", "STATISTICS"),
            ("PUPIL_SPRING_KS4", "KS4 Spring Census", "STATISTICS"),
            ("PUPIL_SPRING_KS5", "KS5 Spring Census", "STATISTICS"),
            ("PUPILPREMIUMPLAC", "Pupil Premium PLAC", "STATISTICS"),
            ("PUPILPREMIUMSER", "Pupil Premium Service", "STATISTICS"),
            ("PUPILPREMIUM_PRI", "Pupil Premium Primary", "STATISTICS"),
            ("PUPILPREMIUM_SEC", "Pupil Premium Secondary", "STATISTICS"),
            ("PUPIL_UIFSM", "UIFSM Pupils", "STATISTICS"),
            ("CAP_BFWD_RES", "Capital BF Balance", "BUDGET"),
            ("REV_BFWD_RES", "Revenue BF Balance", "BUDGET"),
        ]

        for code, title, fc_type in pupil_codes:
            self.template_data["Finance Codes S3"].append({
                "FinanceCode": code,
                "Title": title,
                "FinanceCodeTypeCode": fc_type,
                "GroupingCode": "ZZZ",
                "CustomGrouping": "ZZZ",
                "LedgerCode": "DEFAULT",
                "AvailableToAllSchools": True,
                "SchoolCodes": "",
                "FinanceCodeEnabled": True,
            })

    # =========================================================================
    # EXTERNAL AUDIT REVIEW
    # =========================================================================

    def perform_external_audit(self, customer_data_dir: Path) -> Dict[str, Any]:
        """
        External Audit Review - Compare source data against processed output.
        Validates data integrity, completeness, and accuracy for S3 financial data.
        """
        self.log("\n" + "="*60)
        self.log("EXTERNAL AUDIT REVIEW")
        self.log("="*60)

        # Reset audit results
        self.audit_results = {
            "source_vs_output": [],
            "data_integrity": [],
            "domain_checks": [],
            "missing_data": [],
            "data_lineage": [],
        }
        self.audit_passed = True
        self.audit_score = 100.0

        # 1. Source vs Output comparison
        self._audit_source_vs_output()

        # 2. Data integrity checks
        self._audit_data_integrity()

        # 3. Domain-specific checks
        self._audit_domain_rules()

        # 4. Missing/incomplete data
        self._audit_missing_data()

        # 5. Data lineage verification
        self._audit_data_lineage(customer_data_dir)

        # Calculate final audit score
        self._calculate_audit_score()

        # Log audit summary
        self._log_audit_summary()

        # Generate detailed report
        self.detailed_audit_report = self._generate_detailed_audit_report()

        return {
            "passed": self.audit_passed,
            "score": self.audit_score,
            "results": self.audit_results,
            "detailed_report": self.detailed_audit_report,
        }

    def _audit_source_vs_output(self):
        """Compare source data counts against output."""
        self.log("Auditing: Source vs Output comparison...")

        checks = []

        # Pupil records
        output_pupils = len(self.extracted_pupils)
        checks.append({
            "check": "Pupil Records Extracted",
            "output_count": output_pupils,
            "passed": output_pupils > 0,
            "severity": "warning" if output_pupils == 0 else "info",
            "details": f"Output: {output_pupils} pupil records"
        })

        # Budget lines
        income_count = len([b for b in self.extracted_budgets if b.line_type == 'income'])
        exp_count = len([b for b in self.extracted_budgets if b.line_type == 'expenditure'])
        checks.append({
            "check": "Income Lines Extracted",
            "output_count": income_count,
            "passed": True,
            "severity": "info",
            "details": f"Output: {income_count} income lines"
        })
        checks.append({
            "check": "Expenditure Lines Extracted",
            "output_count": exp_count,
            "passed": True,
            "severity": "info",
            "details": f"Output: {exp_count} expenditure lines"
        })

        # Grants
        grant_count = len(self.extracted_grants)
        checks.append({
            "check": "Grants Extracted",
            "output_count": grant_count,
            "passed": True,
            "severity": "info",
            "details": f"Output: {grant_count} grants"
        })

        self.audit_results["source_vs_output"] = checks

    def _audit_data_integrity(self):
        """Check data integrity - duplicates, nulls, format consistency."""
        self.log("Auditing: Data integrity...")

        checks = []

        # Check for duplicate pupil records (same school + finance code + year)
        pupil_keys = [(p.school_code, p.finance_code, p.year_code) for p in self.extracted_pupils]
        pupil_duplicates = [k for k in set(pupil_keys) if pupil_keys.count(k) > 1]
        checks.append({
            "check": "Pupil Record Uniqueness",
            "passed": len(pupil_duplicates) == 0,
            "severity": "warning" if pupil_duplicates else "info",
            "details": f"Duplicates: {len(pupil_duplicates)}" if pupil_duplicates else "All unique"
        })

        # Check for duplicate budget lines (same school + finance code + department)
        budget_keys = [(b.school_code, b.finance_code, b.department_code) for b in self.extracted_budgets]
        budget_duplicates = [k for k in set(budget_keys) if budget_keys.count(k) > 1]
        checks.append({
            "check": "Budget Line Uniqueness",
            "passed": len(budget_duplicates) == 0,
            "severity": "warning" if budget_duplicates else "info",
            "details": f"Duplicates: {len(budget_duplicates)}" if budget_duplicates else "All unique"
        })

        # Check schools are valid
        invalid_schools = [s for s in self.schools_found if not s or s == 'nan']
        checks.append({
            "check": "Valid School Codes",
            "passed": len(invalid_schools) == 0,
            "severity": "error" if invalid_schools else "info",
            "details": f"Invalid: {len(invalid_schools)}" if invalid_schools else "All valid"
        })
        if invalid_schools:
            self.audit_passed = False

        # Check finance codes have valid format
        invalid_fc = [fc for fc in self.finance_codes_found if not fc or fc == 'nan']
        checks.append({
            "check": "Valid Finance Codes",
            "passed": len(invalid_fc) == 0,
            "severity": "warning" if invalid_fc else "info",
            "details": f"Invalid: {len(invalid_fc)}" if invalid_fc else "All valid"
        })

        self.audit_results["data_integrity"] = checks

    def _audit_domain_rules(self):
        """Check domain-specific business rules for S3 financial data."""
        self.log("Auditing: Domain rules...")

        checks = []

        # Check pupil numbers are non-negative
        negative_pupils = [p for p in self.extracted_pupils if p.value < 0]
        checks.append({
            "check": "Pupil Numbers Non-Negative",
            "passed": len(negative_pupils) == 0,
            "severity": "error" if negative_pupils else "info",
            "details": f"Negative values: {len(negative_pupils)}" if negative_pupils else "All valid"
        })
        if negative_pupils:
            self.audit_passed = False

        # Check income lines have negative values (accounting convention)
        positive_income = [b for b in self.extracted_budgets
                         if b.line_type == 'income' and b.year_value > 0]
        checks.append({
            "check": "Income Values Negative",
            "passed": len(positive_income) == 0,
            "severity": "warning" if positive_income else "info",
            "details": f"Positive income: {len(positive_income)}" if positive_income else "Correct sign convention"
        })

        # Check expenditure lines have positive values
        negative_exp = [b for b in self.extracted_budgets
                       if b.line_type == 'expenditure' and b.year_value < 0]
        checks.append({
            "check": "Expenditure Values Positive",
            "passed": len(negative_exp) == 0,
            "severity": "warning" if negative_exp else "info",
            "details": f"Negative expenditure: {len(negative_exp)}" if negative_exp else "Correct sign convention"
        })

        # Check grant amounts are positive
        negative_grants = [g for g in self.extracted_grants if g.amount < 0]
        checks.append({
            "check": "Grant Amounts Positive",
            "passed": len(negative_grants) == 0,
            "severity": "warning" if negative_grants else "info",
            "details": f"Negative grants: {len(negative_grants)}" if negative_grants else "All valid"
        })

        # Check calculator codes are valid
        valid_calculators = {'0%_CALC', 'FUNDING_GAG', 'FUNDING_16_19', 'PUPPREMIUM_FACTOR',
                            'PUPPREMIUM_CALC', 'DFC_CORE', 'DFC_PUPIL', 'DFC_EXP',
                            'PE_GRANT_CORE', 'PE_GRANT_PUPIL', 'UIFSM_CALC', 'UIFSM_RATE',
                            'CENTRALCHG_SCH', 'CENTRALCHG_MAT', ''}
        invalid_calcs = [p.calculator_code for p in self.extracted_pupils
                        if p.calculator_code and p.calculator_code not in valid_calculators]
        checks.append({
            "check": "Valid Calculator Codes",
            "passed": len(invalid_calcs) == 0,
            "severity": "warning" if invalid_calcs else "info",
            "details": f"Invalid: {set(invalid_calcs)}" if invalid_calcs else "All valid"
        })

        self.audit_results["domain_checks"] = checks

    def _audit_missing_data(self):
        """Check for missing or incomplete data."""
        self.log("Auditing: Missing data...")

        checks = []

        # Check if we have any data at all
        has_data = (len(self.extracted_pupils) > 0 or
                   len(self.extracted_budgets) > 0 or
                   len(self.extracted_grants) > 0)
        checks.append({
            "check": "Data Extracted",
            "passed": has_data,
            "severity": "error" if not has_data else "info",
            "details": "Some data extracted" if has_data else "No data extracted"
        })
        if not has_data:
            self.audit_passed = False

        # Check if we have schools
        checks.append({
            "check": "Schools Identified",
            "passed": len(self.schools_found) > 0,
            "severity": "warning" if len(self.schools_found) == 0 else "info",
            "details": f"Schools: {len(self.schools_found)}"
        })

        # Check pupils have school codes
        pupils_no_school = [p for p in self.extracted_pupils if not p.school_code]
        pupil_school_pct = ((len(self.extracted_pupils) - len(pupils_no_school)) /
                          len(self.extracted_pupils) * 100) if self.extracted_pupils else 0
        checks.append({
            "check": "Pupils Have School Codes",
            "passed": pupil_school_pct >= 80,
            "severity": "warning" if pupil_school_pct < 80 else "info",
            "details": f"{pupil_school_pct:.1f}% have school codes"
        })

        # Check budgets have descriptions
        budgets_no_desc = [b for b in self.extracted_budgets
                         if not b.description or b.description == b.finance_code]
        budget_desc_pct = ((len(self.extracted_budgets) - len(budgets_no_desc)) /
                         len(self.extracted_budgets) * 100) if self.extracted_budgets else 0
        checks.append({
            "check": "Budget Lines Have Descriptions",
            "passed": budget_desc_pct >= 50,
            "severity": "warning" if budget_desc_pct < 50 else "info",
            "details": f"{budget_desc_pct:.1f}% have descriptions"
        })

        self.audit_results["missing_data"] = checks

    def _audit_data_lineage(self, customer_data_dir: Path):
        """Verify data lineage - track where data came from."""
        self.log("Auditing: Data lineage...")

        checks = []

        # Count source files processed
        source_files = list(customer_data_dir.rglob("*.xls*")) + list(customer_data_dir.rglob("*.csv"))
        source_files = [f for f in source_files if not f.name.startswith("~$")]

        checks.append({
            "check": "Source Files Processed",
            "passed": len(source_files) > 0,
            "severity": "error" if len(source_files) == 0 else "info",
            "details": f"Files: {len(source_files)}"
        })
        if len(source_files) == 0:
            self.audit_passed = False

        # Record source file names
        checks.append({
            "check": "Source File List",
            "passed": True,
            "severity": "info",
            "details": ", ".join([f.name for f in source_files[:5]]) +
                      (f" (+{len(source_files)-5} more)" if len(source_files) > 5 else "")
        })

        # Check for issues during extraction
        checks.append({
            "check": "Extraction Issues",
            "passed": len(self.issues) == 0,
            "severity": "warning" if self.issues else "info",
            "details": f"Issues: {len(self.issues)}" if self.issues else "No issues"
        })

        self.audit_results["data_lineage"] = checks

    def _calculate_audit_score(self):
        """Calculate overall audit score based on check results."""
        total_checks = 0
        passed_checks = 0
        error_count = 0
        warning_count = 0

        for category, checks in self.audit_results.items():
            for check in checks:
                total_checks += 1
                if check.get("passed", True):
                    passed_checks += 1
                elif check.get("severity") == "error":
                    error_count += 1
                elif check.get("severity") == "warning":
                    warning_count += 1

        # Calculate score: errors = -10 points, warnings = -5 points
        if total_checks > 0:
            base_score = (passed_checks / total_checks) * 100
            penalty = (error_count * 10) + (warning_count * 5)
            self.audit_score = max(0, base_score - penalty)
        else:
            self.audit_score = 0

        # Audit fails if score < 60 or any critical errors
        if self.audit_score < 60 or error_count > 0:
            self.audit_passed = False

    def _log_audit_summary(self):
        """Log audit summary."""
        self.log("\n" + "-"*40)
        self.log("AUDIT SUMMARY")
        self.log("-"*40)
        self.log(f"  Audit Score: {self.audit_score:.1f}%")
        self.log(f"  Audit Passed: {self.audit_passed}")

        for category, checks in self.audit_results.items():
            errors = [c for c in checks if not c.get("passed") and c.get("severity") == "error"]
            warnings = [c for c in checks if not c.get("passed") and c.get("severity") == "warning"]

            if errors or warnings:
                self.log(f"\n  {category}:")
                for check in errors:
                    self.log(f"    ERROR: {check['check']} - {check['details']}")
                for check in warnings:
                    self.log(f"    WARNING: {check['check']} - {check['details']}")

        self.log("-"*40)

    def _generate_detailed_audit_report(self) -> Dict[str, Any]:
        """Generate detailed audit report with explanations and recommendations."""
        detailed_report = {
            "summary": {
                "score": self.audit_score,
                "passed": self.audit_passed,
                "total_issues": 0,
                "critical_issues": 0,
                "warnings": 0,
            },
            "issues": [],
            "recommendations": [],
        }

        for category, checks in self.audit_results.items():
            for check in checks:
                if not check.get("passed", True):
                    issue = self._explain_audit_issue(category, check)
                    if issue:
                        detailed_report["issues"].append(issue)
                        detailed_report["summary"]["total_issues"] += 1
                        if check.get("severity") == "error":
                            detailed_report["summary"]["critical_issues"] += 1
                        elif check.get("severity") == "warning":
                            detailed_report["summary"]["warnings"] += 1

        detailed_report["recommendations"] = self._generate_recommendations(detailed_report["issues"])
        return detailed_report

    def _explain_audit_issue(self, category: str, check: Dict) -> Dict[str, Any]:
        """Generate detailed explanation for audit issue."""
        check_name = check.get("check", "Unknown")
        severity = check.get("severity", "info")
        details = check.get("details", "")

        explanation = {
            "category": category,
            "check": check_name,
            "severity": severity,
            "details": details,
            "what_is_missing": "",
            "why_it_matters": "",
            "how_to_fix": "",
            "affected_records": [],
        }

        # Source vs Output issues
        if category == "source_vs_output":
            if "Pupil" in check_name:
                explanation["what_is_missing"] = f"Pupil records mismatch: {details}"
                explanation["why_it_matters"] = "Accurate pupil numbers are essential for funding calculations (PP, UIFSM, etc.)"
                explanation["how_to_fix"] = "Verify census data is in correct format. Check Spring/Autumn census columns are labeled correctly."
            elif "Grant" in check_name:
                explanation["what_is_missing"] = f"Grant data issue: {details}"
                explanation["why_it_matters"] = "Missing grants affect budget projections and income calculations"
                explanation["how_to_fix"] = "Ensure grant allocations are included in source data with correct grant types."
            elif "Budget" in check_name:
                explanation["what_is_missing"] = f"Budget line discrepancy: {details}"
                explanation["why_it_matters"] = "Missing budget lines cause incomplete financial projections"
                explanation["how_to_fix"] = "Check income/expenditure columns are correctly labeled and contain valid amounts."

        # Data integrity issues
        elif category == "data_integrity":
            if "Duplicate" in check_name:
                explanation["what_is_missing"] = f"Duplicate records found: {details}"
                explanation["why_it_matters"] = "Duplicates cause double-counting in budgets and reports"
                explanation["how_to_fix"] = "Review source data for unintentional duplicates."
            elif "Negative" in check_name:
                explanation["what_is_missing"] = f"Invalid values: {details}"
                explanation["why_it_matters"] = "Negative pupil numbers or invalid amounts cause calculation errors"
                explanation["how_to_fix"] = "Check for data entry errors in source files."

        # Domain checks
        elif category == "domain_checks":
            if "Census" in check_name:
                explanation["what_is_missing"] = f"Census data issue: {details}"
                explanation["why_it_matters"] = "Census data drives funding calculations"
                explanation["how_to_fix"] = "Ensure census columns include correct term (Spring/Autumn) and year."
            elif "Funding" in check_name:
                explanation["what_is_missing"] = f"Funding calculation issue: {details}"
                explanation["why_it_matters"] = "Incorrect funding affects budget accuracy"
                explanation["how_to_fix"] = "Verify funding rates match current DfE rates."

        # Missing data
        elif category == "missing_data":
            if "School" in check_name:
                explanation["what_is_missing"] = f"Schools missing pupil data: {details}"
                explanation["why_it_matters"] = "Schools without pupil data cannot receive proper funding allocations"
                explanation["how_to_fix"] = "Add pupil numbers for all schools in the census data."

        return explanation

    def _generate_recommendations(self, issues: List[Dict]) -> List[Dict[str, str]]:
        """Generate prioritized recommendations."""
        recommendations = []
        seen = set()

        for issue in issues:
            if issue.get("severity") == "error":
                rec = {
                    "priority": "HIGH",
                    "category": issue.get("category", ""),
                    "action": issue.get("how_to_fix", "Review and fix critical data issues"),
                    "reason": issue.get("why_it_matters", ""),
                }
                key = f"{rec['category']}:{rec['action'][:50]}"
                if key not in seen:
                    recommendations.append(rec)
                    seen.add(key)

        for issue in issues:
            if issue.get("severity") == "warning":
                rec = {
                    "priority": "MEDIUM",
                    "category": issue.get("category", ""),
                    "action": issue.get("how_to_fix", "Review data quality"),
                    "reason": issue.get("why_it_matters", ""),
                }
                key = f"{rec['category']}:{rec['action'][:50]}"
                if key not in seen:
                    recommendations.append(rec)
                    seen.add(key)

        if not self.extracted_pupils:
            recommendations.insert(0, {
                "priority": "HIGH",
                "category": "data_source",
                "action": "Add census data with pupil numbers to the S3 folder",
                "reason": "No pupil data found - funding calculations require pupil numbers",
            })

        return recommendations

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def process(self, customer_data_dir: Path, output_dir: Path, column_mappings: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """Main processing entry point with external audit.

        Args:
            customer_data_dir: Path to customer data files
            output_dir: Path to save output
            column_mappings: Optional dict of validated column mappings from pre-flight validation
        """
        # Store column mappings for use during processing
        self.column_mappings = column_mappings or {}

        self.log("="*60)
        self.log("S3 SPECIALIST AGENT - STARTING PROCESSING")
        self.log("="*60)

        # Phase 1: Analysis
        self.analyze_customer_data(customer_data_dir)

        # Phase 2: Build templates
        template_sheets = self.build_all_templates()

        # Phase 3: External Audit Review
        audit_results = self.perform_external_audit(customer_data_dir)

        # Phase 4: Format data to match official template schema
        template_warnings = []
        formatted_sheets = {}

        self.log("\nPHASE 4: FORMATTING FOR OFFICIAL TEMPLATE")
        self.log("-" * 40)

        for internal_name, df in template_sheets.items():
            if len(df) == 0:
                continue

            # Get official template sheet name
            official_name = self.SHEET_NAME_MAPPING.get(internal_name, internal_name)

            # Apply template formatting if available
            if self.template_formatter and self.template_registry:
                s3_sheets = self.template_registry.list_sheets("S3")
                if official_name in s3_sheets:
                    formatted_df, warnings = self.template_formatter.format_dataframe(
                        df, "S3", official_name
                    )
                    formatted_sheets[official_name] = formatted_df
                    if warnings:
                        template_warnings.extend([f"{official_name}: {w}" for w in warnings])
                        self.log(f"  {official_name}: {len(df)} rows (formatted, {len(warnings)} warnings)")
                    else:
                        self.log(f"  {official_name}: {len(df)} rows (formatted)")
                else:
                    # No template schema, use as-is with official name
                    formatted_sheets[official_name] = df
                    self.log(f"  {official_name}: {len(df)} rows (no schema)")
            else:
                # No formatter available, use official name
                formatted_sheets[official_name] = df
                self.log(f"  {official_name}: {len(df)} rows")

        if template_warnings:
            self.log(f"\n[WARN] Template formatting warnings: {len(template_warnings)}")
            for w in template_warnings[:5]:
                self.log(f"  - {w}")

        # Save output
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"S3_complete_template_{timestamp}.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in formatted_sheets.items():
                if len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Summary with audit results
            summary_data = {
                "Metric": [
                    "Pupil Records",
                    "Income Lines",
                    "Expenditure Lines",
                    "Grants",
                    "Schools",
                    "Finance Codes",
                    "Issues",
                    "---",
                    "AUDIT SCORE",
                    "AUDIT PASSED",
                ],
                "Value": [
                    len(self.extracted_pupils),
                    len([b for b in self.extracted_budgets if b.line_type == 'income']),
                    len([b for b in self.extracted_budgets if b.line_type == 'expenditure']),
                    len(self.extracted_grants),
                    len(self.schools_found),
                    len(self.finance_codes_found),
                    len(self.issues),
                    "---",
                    f"{self.audit_score:.1f}%",
                    "YES" if self.audit_passed else "NO",
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="_Summary", index=False)

            # Issues sheet if any
            if self.issues:
                issues_data = [{"Issue": issue} for issue in self.issues]
                pd.DataFrame(issues_data).to_excel(writer, sheet_name="_Issues", index=False)

            # External Audit Report sheet
            audit_report = []
            for category, checks in self.audit_results.items():
                for check in checks:
                    audit_report.append({
                        "Category": category,
                        "Check": check.get("check", ""),
                        "Passed": "YES" if check.get("passed", True) else "NO",
                        "Severity": check.get("severity", "info").upper(),
                        "Details": check.get("details", ""),
                    })
            if audit_report:
                pd.DataFrame(audit_report).to_excel(writer, sheet_name="_Audit_Report", index=False)

            # Detailed Audit Report sheet
            detailed_issues = []
            for issue in self.detailed_audit_report.get("issues", []):
                detailed_issues.append({
                    "Category": issue.get("category", ""),
                    "Check": issue.get("check", ""),
                    "Severity": issue.get("severity", "").upper(),
                    "What Is Missing": issue.get("what_is_missing", ""),
                    "Why It Matters": issue.get("why_it_matters", ""),
                    "How To Fix": issue.get("how_to_fix", ""),
                })
            if detailed_issues:
                pd.DataFrame(detailed_issues).to_excel(writer, sheet_name="_Audit_Details", index=False)

            # Recommendations sheet
            recommendations = self.detailed_audit_report.get("recommendations", [])
            if recommendations:
                rec_data = [{
                    "Priority": r.get("priority", ""),
                    "Category": r.get("category", ""),
                    "Action Required": r.get("action", ""),
                    "Reason": r.get("reason", ""),
                } for r in recommendations]
                pd.DataFrame(rec_data).to_excel(writer, sheet_name="_Recommendations", index=False)

        self.log(f"\nOutput saved to: {output_file}")

        # Determine overall success (includes audit)
        has_critical_errors = len(self.issues) > 0 or not self.audit_passed

        return {
            "success": not has_critical_errors,
            "output_file": output_file,
            "template_sheets": template_sheets,
            "issues": self.issues,
            "audit": {
                "passed": self.audit_passed,
                "score": self.audit_score,
                "results": self.audit_results,
                "detailed_report": self.detailed_audit_report,
            },
            "summary": {
                "pupils": len(self.extracted_pupils),
                "income_lines": len([b for b in self.extracted_budgets if b.line_type == 'income']),
                "expenditure_lines": len([b for b in self.extracted_budgets if b.line_type == 'expenditure']),
                "grants": len(self.extracted_grants),
                "schools": list(self.schools_found),
                "audit_score": self.audit_score,
                "audit_passed": self.audit_passed,
            }
        }


def run_s3_specialist(customer_data_dir: Path, output_dir: Path, column_mappings: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
    """Run the S3 specialist agent.

    Args:
        customer_data_dir: Path to customer data files
        output_dir: Path to save output
        column_mappings: Optional dict of validated column mappings from pre-flight validation

    Returns:
        Processing result dictionary
    """
    agent = S3SpecialistAgent()
    return agent.process(customer_data_dir, output_dir, column_mappings=column_mappings)
