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

        # Tracking
        self.schools_found = set()
        self.finance_codes_found = set()
        self.current_year = "2025/26"
        self.previous_year = "2024/25"

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

    # =========================================================================
    # PHASE 1: DEEP ANALYSIS
    # =========================================================================

    def analyze_customer_data(self, data_dir: Path):
        """Analyze all S3 customer data files."""
        self.log("="*60)
        self.log("PHASE 1: DEEP ANALYSIS OF S3 CUSTOMER DATA")
        self.log("="*60)

        all_files = list(data_dir.rglob("*.xls*")) + list(data_dir.rglob("*.csv"))
        all_files = [f for f in all_files if not f.name.startswith("~$")]

        self.log(f"Found {len(all_files)} files to analyze")

        for file_path in all_files:
            self.log(f"\nAnalyzing: {file_path.name}")
            self._analyze_file(file_path)

        self._print_analysis_summary()

    def _analyze_file(self, file_path: Path):
        """Analyze a single file."""
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
                self._classify_and_extract(df, file_path.name, "CSV")
            else:
                xl = pd.ExcelFile(file_path)
                self.log(f"  Sheets: {xl.sheet_names}")

                for sheet in xl.sheet_names:
                    if self._is_skip_sheet(sheet):
                        continue

                    df = self._read_sheet_smart(xl, sheet)
                    if df is not None and len(df) > 0:
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

            dept = str(row.get('department_code', 'DEFAULT')).strip()
            if dept == 'nan':
                dept = 'DEFAULT'

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
    # MAIN ENTRY POINT
    # =========================================================================

    def process(self, customer_data_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Main processing entry point."""
        self.log("="*60)
        self.log("S3 SPECIALIST AGENT - STARTING PROCESSING")
        self.log("="*60)

        # Phase 1: Analysis
        self.analyze_customer_data(customer_data_dir)

        # Phase 2: Build templates
        template_sheets = self.build_all_templates()

        # Save output
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"S3_complete_template_{timestamp}.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in template_sheets.items():
                if len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Summary
            summary_data = {
                "Metric": [
                    "Pupil Records",
                    "Income Lines",
                    "Expenditure Lines",
                    "Grants",
                    "Schools",
                    "Finance Codes",
                    "Issues",
                ],
                "Value": [
                    len(self.extracted_pupils),
                    len([b for b in self.extracted_budgets if b.line_type == 'income']),
                    len([b for b in self.extracted_budgets if b.line_type == 'expenditure']),
                    len(self.extracted_grants),
                    len(self.schools_found),
                    len(self.finance_codes_found),
                    len(self.issues),
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="_Summary", index=False)

        self.log(f"\nOutput saved to: {output_file}")

        return {
            "success": len(self.issues) == 0,
            "output_file": output_file,
            "template_sheets": template_sheets,
            "issues": self.issues,
            "summary": {
                "pupils": len(self.extracted_pupils),
                "income_lines": len([b for b in self.extracted_budgets if b.line_type == 'income']),
                "expenditure_lines": len([b for b in self.extracted_budgets if b.line_type == 'expenditure']),
                "grants": len(self.extracted_grants),
                "schools": list(self.schools_found),
            }
        }


def run_s3_specialist(customer_data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Run the S3 specialist agent."""
    agent = S3SpecialistAgent()
    return agent.process(customer_data_dir, output_dir)
