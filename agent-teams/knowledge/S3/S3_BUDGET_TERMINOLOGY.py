"""
S3 Budget Terminology and Variable Mappings
============================================
Knowledge extracted from: Strand 1 Terminology and Variables.xlsx

This module defines the standard terminology mappings between customer budget
file formats and the IMP (Import) standard format used by the S3 agent.

Customer budget files come in many formats (EXP1-EXP11 examples). This knowledge
helps the S3 agent recognize and normalize these different formats.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# =============================================================================
# TERMINOLOGY MAPPINGS
# =============================================================================
# Maps IMP (Import) standard terms to various customer terminology variations

FINANCE_CODE_TERMS = {
    # IMP Term: FinanceCode
    # Customer variations:
    "Nominal Code": "FinanceCode",      # EXP1, EXP6
    "Nominal": "FinanceCode",           # EXP1, EXP3, EXP4, EXP11
    "NOMINAL": "FinanceCode",           # EXP1 uppercase
    "Nomina;": "FinanceCode",           # EXP7 typo variant
    "Code": "FinanceCode",              # EXP8
    "Account": "FinanceCode",           # EXP10
    "Account Code": "FinanceCode",
    "NL Code": "FinanceCode",
    "GL Code": "FinanceCode",
    "Finance Code": "FinanceCode",
    "FinCode": "FinanceCode",
}

DEPARTMENT_CODE_TERMS = {
    # IMP Term: DepartmentCode
    # Customer variations:
    "Cost Centre": "DepartmentCode",    # EXP2, EXP6, EXP9
    "Cost Centre/Account": "DepartmentCode",  # EXP5
    "Cost Center": "DepartmentCode",    # US spelling
    "Dept": "DepartmentCode",
    "Department": "DepartmentCode",
    "Dept Code": "DepartmentCode",
    "CC": "DepartmentCode",
    "Fund Code": "DepartmentCode",      # Sometimes used as department
    "Analysis Code": "DepartmentCode",  # EXP2
}

SCHOOL_CODE_TERMS = {
    # IMP Term: SchoolCode
    # Customer variations:
    "Location": "SchoolCode",           # EXP7
    "Company": "SchoolCode",
    "School": "SchoolCode",
    "Academy": "SchoolCode",
    "Site": "SchoolCode",
    "Entity": "SchoolCode",
    "Cost Centre": "SchoolCode",        # Sometimes school is in cost centre
}

FUND_CODE_TERMS = {
    # IMP Term: FundCode
    # Customer variations:
    "Funds": "FundCode",                # EXP7
    "Fund": "FundCode",
    "Fund Type": "FundCode",
    "Funding Source": "FundCode",
}

LEDGER_CODE_TERMS = {
    # IMP Term: LedgerCode
    # Customer variations:
    "Ledger": "LedgerCode",             # EXP2, EXP7, EXP11
    "Ledger Code": "LedgerCode",
    "Account": "LedgerCode",            # EXP1, EXP11
    "Account Type": "LedgerCode",
}

DESCRIPTION_TERMS = {
    # IMP Term: Description
    # Customer variations:
    "Description": "Description",        # EXP2, EXP8, EXP9, EXP11
    "Account Title": "Description",      # EXP7
    "Nominal Description": "Description", # EXP11
    "Title": "Description",
    "Name": "Description",
    "Account Name": "Description",
    "Section Name": "Description",       # EXP2, EXP11
}


# =============================================================================
# BUDGET FILE FORMAT PATTERNS
# =============================================================================
# Patterns recognized from the 11 example budget file types

@dataclass
class BudgetFilePattern:
    """Defines a recognizable budget file pattern."""
    name: str
    description: str
    key_columns: List[str]
    header_row_hint: int  # Typical row where headers appear (0-indexed)
    has_monthly_breakdown: bool
    has_multi_year: bool
    has_school_breakdown: bool
    value_columns: List[str]  # Column names that contain values
    example_trust: str


BUDGET_FILE_PATTERNS = {
    # EXP1: Budget Matrix - Monthly with Nominal/Ledger
    "matrix_monthly": BudgetFilePattern(
        name="Budget Matrix",
        description="Monthly budget with NOMINAL, LEDGER, and PERIOD columns",
        key_columns=["NOMINAL", "LEDGER", "ACCOUNT"],
        header_row_hint=8,
        has_monthly_breakdown=True,
        has_multi_year=False,
        has_school_breakdown=False,
        value_columns=["PERIOD 1", "PERIOD 2", "PERIOD 3", "PERIOD 4", "PERIOD 5",
                       "PERIOD 6", "PERIOD 7", "PERIOD 8", "PERIOD 9", "PERIOD 10",
                       "PERIOD 11", "PERIOD 12", "TOTAL"],
        example_trust="AST002"
    ),

    # EXP2: Multi-Year Budget with Cost Centre
    "multi_year_section": BudgetFilePattern(
        name="Multi-Year Section Budget",
        description="Budget with Section/Description/Cost Centre and multiple year columns",
        key_columns=["Section", "Section Name", "Description", "Cost Centre", "Ledger Code"],
        header_row_hint=0,
        has_monthly_breakdown=False,
        has_multi_year=True,
        has_school_breakdown=False,
        value_columns=["2025 - 26", "2026 - 27", "2027 - 28"],
        example_trust="INS007"
    ),

    # EXP3: Budget Forecast by Cost Centres
    "forecast_costcentre": BudgetFilePattern(
        name="Budget Forecast by Cost Centres",
        description="Budget forecast with school name, DFE number, and ledger code totals",
        key_columns=["School Name:", "DFE No.:", "Version Name:"],
        header_row_hint=10,
        has_monthly_breakdown=False,
        has_multi_year=True,
        has_school_breakdown=False,
        value_columns=["2025/26", "2026/27", "2027/28"],
        example_trust="DIS003"
    ),

    # EXP4: Simple School Budget with Finance Codes
    "simple_school": BudgetFilePattern(
        name="Simple School Budget",
        description="Finance code with GAG/PP/SP codes and year columns",
        key_columns=["School Name:", "REVENUE INCOME"],
        header_row_hint=2,
        has_monthly_breakdown=False,
        has_multi_year=True,
        has_school_breakdown=False,
        value_columns=["2025/2026", "2026/2027", "2027/2028"],
        example_trust="ELV001"
    ),

    # EXP5: MAT Consolidated Multi-School
    "mat_consolidated": BudgetFilePattern(
        name="MAT Consolidated Budget",
        description="Multi-school budget with Central/Special/Primary/Secondary columns",
        key_columns=["Cost Centre/Account", "Central", "Primary", "Secondary"],
        header_row_hint=0,
        has_monthly_breakdown=False,
        has_multi_year=False,
        has_school_breakdown=True,
        value_columns=["Central", "Primary", "Secondary", "Total"],
        example_trust="BIS006"
    ),

    # EXP6: Income/Expenditure Profile with Monthly
    "profile_monthly": BudgetFilePattern(
        name="Income/Expenditure Profile",
        description="Profile report with Nominal Code, Cost Centre, and monthly columns",
        key_columns=["Nominal Code", "Cost Centre", "Description", "Budget"],
        header_row_hint=2,
        has_monthly_breakdown=True,
        has_multi_year=False,
        has_school_breakdown=False,
        value_columns=["September", "October", "November", "December", "January",
                       "February", "March", "April", "May", "June", "July", "August", "Total"],
        example_trust="AST002"
    ),

    # EXP7: Location/Nominal/Account with Funds
    "location_nominal": BudgetFilePattern(
        name="Location/Nominal Budget",
        description="Budget with Location, Nominal, Account, Ledger, and Funds columns",
        key_columns=["Location", "Nomina;", "Account", "Account Title", "Ledger", "Funds"],
        header_row_hint=0,
        has_monthly_breakdown=False,
        has_multi_year=False,
        has_school_breakdown=True,
        value_columns=["Approved", "Master"],
        example_trust="ADV002"
    ),

    # EXP8: Simple Code/Description/Budget
    "simple_code_budget": BudgetFilePattern(
        name="Simple Code Budget",
        description="Simple format with Code, Description, Budget Year columns",
        key_columns=["Code", "Description", "Budget Year"],
        header_row_hint=0,
        has_monthly_breakdown=False,
        has_multi_year=False,
        has_school_breakdown=False,
        value_columns=["Budget Year"],
        example_trust="AIM001"
    ),

    # EXP9: Trust Consolidated Multi-School
    "trust_consolidated": BudgetFilePattern(
        name="Trust Consolidated Budget",
        description="Trust budget with Description, Cost Centre, Fund Code and school columns",
        key_columns=["Description", "Cost Centre", "Fund Code"],
        header_row_hint=0,
        has_monthly_breakdown=False,
        has_multi_year=False,
        has_school_breakdown=True,
        value_columns=["SCHOOL 1", "SCHOOL 2", "SCHOOL 3", "Consolidated"],
        example_trust="MOS002"
    ),

    # EXP10: Monthly by Account
    "monthly_account": BudgetFilePattern(
        name="Monthly by Account",
        description="Monthly budget with Account and date columns (2025-09-01 format)",
        key_columns=["Account"],
        header_row_hint=3,
        has_monthly_breakdown=True,
        has_multi_year=False,
        has_school_breakdown=False,
        value_columns=["2025-09-01", "2025-10-01", "2025-11-01", "2025-12-01",
                       "2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01",
                       "2026-05-01", "2026-06-01", "2026-07-01", "2026-08-01", "Total"],
        example_trust="ACE004"
    ),

    # EXP11: Full Detail with Section/Nominal/Ledger/Account
    "full_detail": BudgetFilePattern(
        name="Full Detail Budget",
        description="Complete budget with Section, Nominal, Ledger, Account, Scale details",
        key_columns=["Section", "Section Name", "Description", "Budget Type", "Nominal",
                     "Nominal Description", "Ledger", "Ledger Description", "Account",
                     "Account Description", "Job Type", "Scale Group", "Scale Code"],
        header_row_hint=0,
        has_monthly_breakdown=False,
        has_multi_year=True,
        has_school_breakdown=False,
        value_columns=["2025 - 26", "2026 - 27", "2027 - 28", "2028 - 29", "2029 - 30"],
        example_trust="IMP002"
    ),
}


# =============================================================================
# FINANCE CODE PATTERNS
# =============================================================================
# Standard DfE/ESFA finance code patterns for income and expenditure

INCOME_FINANCE_CODES = {
    # GAG Income
    "510100": {"title": "DfE Rev Grnts-GAG-not stud supp & trst", "grouping": "A0", "dept": "IGAG"},
    "510110": {"title": "DfE Rev Grnts-GAG-student support", "grouping": "A0", "dept": "IGAG"},
    "510120": {"title": "DfE Rev Grnts-GAG-start up grants", "grouping": "A0", "dept": "IGAG"},
    "510130": {"title": "DfE Rev Grnts-Trust level grants", "grouping": "A1", "dept": "IGAG"},
    "510140": {"title": "DfE Rev Grnts-Pupil number adjustment", "grouping": "A1", "dept": "IGAG"},
    "510150": {"title": "DfE Rev Grnts-Rates reclaim", "grouping": "A1", "dept": "IGAG"},

    # Pupil Premium
    "510200": {"title": "DfE Rev Grnts-Pupil Premium", "grouping": "A0", "dept": "IPUPIL"},
    "510205": {"title": "DfE Rev Grnts-Pupil Premium - Nursery", "grouping": "A1", "dept": "IPUPIL"},

    # Other DfE Grants
    "510250": {"title": "DfE Rev Grnts-Univ'l Inf Free Schl Meals", "grouping": "A1", "dept": "IUIFSM"},
    "510300": {"title": "DfE Rev Grnts-Insurance top up", "grouping": "A1", "dept": "IGAG"},
    "510350": {"title": "DfE Rev Grnts-Sponsor capacity grant", "grouping": "A1", "dept": "IGAG"},
    "510400": {"title": "DfE Rev Grnts-PE & Sports grant", "grouping": "A1", "dept": "ISPORT"},
    "510450": {"title": "DfE Rev Grnts-Year 7 catch up", "grouping": "A1", "dept": "IGAG"},
    "510500": {"title": "DfE Rev Grnts-Teachers Pay Grant", "grouping": "A1", "dept": "IGAG"},
    "510510": {"title": "DfE Rev Grnts-Teacher Pens Emp Cont Grnt", "grouping": "A1", "dept": "IGAG"},

    # Post-16 Funding
    "510700": {"title": "DfE Rev Grnts - 16 to 19 Funding", "grouping": "A0", "dept": "IGAG"},
    "510101": {"title": "16 to 19 funding", "grouping": "A0", "dept": "IGAG"},
    "510102": {"title": "16 to 19 Bursary", "grouping": "A1", "dept": "IGAG"},

    # Other Income
    "525750": {"title": "Bank Interest Income", "grouping": "B0", "dept": "INTRA"},
    "530700": {"title": "Income from trading activities", "grouping": "B1", "dept": "INTRA"},
    "530990": {"title": "Central Contribution from Schools", "grouping": "B1", "dept": "TCT_CS"},
}

EXPENDITURE_FINANCE_CODES = {
    # Staff Costs
    "611100": {"title": "Teaching Staff - Basic Pay", "grouping": "E1", "dept": "STLEA"},
    "611200": {"title": "Teaching Staff - NI", "grouping": "E1", "dept": "STLEA"},
    "611300": {"title": "Teaching Staff - Pension", "grouping": "E1", "dept": "STLEA"},
    "625100": {"title": "Admin Staff - Basic Pay", "grouping": "E3", "dept": "STADM"},
    "625200": {"title": "Admin Staff - NI", "grouping": "E3", "dept": "STADM"},
    "625300": {"title": "Admin Staff - Pension", "grouping": "E3", "dept": "STADM"},

    # Central Charges
    "835170": {"title": "Central Charge School", "grouping": "E8", "dept": "ADMINSER"},

    # Capital
    "770102": {"title": "DFC Expenditure", "grouping": "C1", "dept": "EXDFC"},
    "550250": {"title": "DFC Capital Grant Income", "grouping": "C0", "dept": "EXDFC"},
}


# =============================================================================
# SECTION/IL/EL CODE MAPPINGS
# =============================================================================
# Maps section codes (IL/EL) to income/expenditure types

SECTION_CODE_MAPPINGS = {
    # Income Lines (IL)
    "IL 101": {"type": "income", "category": "Rates Relief", "fc_prefix": "510150"},
    "IL 102": {"type": "income", "category": "GAG", "fc_prefix": "510100"},
    "IL 103": {"type": "income", "category": "Student Services Grant", "fc_prefix": "510110"},
    "IL 108": {"type": "income", "category": "Pupil Premium", "fc_prefix": "510200"},
    "IL 211": {"type": "income", "category": "Trading Activities", "fc_prefix": "530700"},
    "IL 220": {"type": "income", "category": "Other Income", "fc_prefix": "525"},

    # Expenditure Lines (EL)
    "EL 300": {"type": "expenditure", "category": "Teaching Staff", "fc_prefix": "611"},
    "EL 303b": {"type": "expenditure", "category": "Administrative Staff", "fc_prefix": "625"},
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_column_name(col_name: str) -> str:
    """Normalize a column name to standard IMP format."""
    col_lower = col_name.lower().strip()

    # Check all terminology mappings
    all_mappings = {
        **FINANCE_CODE_TERMS,
        **DEPARTMENT_CODE_TERMS,
        **SCHOOL_CODE_TERMS,
        **FUND_CODE_TERMS,
        **LEDGER_CODE_TERMS,
        **DESCRIPTION_TERMS,
    }

    for source, target in all_mappings.items():
        if col_lower == source.lower():
            return target

    return col_name


def detect_budget_file_pattern(df_columns: List[str], df_sample: Optional[List] = None) -> Optional[str]:
    """
    Detect which budget file pattern matches the given columns.

    Args:
        df_columns: List of column names from the DataFrame
        df_sample: Optional sample rows for content-based detection

    Returns:
        Pattern name or None if no match
    """
    col_set = set(c.lower().strip() for c in df_columns)

    best_match = None
    best_score = 0

    for pattern_name, pattern in BUDGET_FILE_PATTERNS.items():
        # Calculate match score
        key_cols_lower = [c.lower() for c in pattern.key_columns]
        matches = sum(1 for kc in key_cols_lower if any(kc in c for c in col_set))
        score = matches / len(pattern.key_columns) if pattern.key_columns else 0

        if score > best_score:
            best_score = score
            best_match = pattern_name

    # Require at least 50% match
    return best_match if best_score >= 0.5 else None


def get_finance_code_info(code: str) -> Optional[Dict]:
    """Get information about a finance code."""
    if code in INCOME_FINANCE_CODES:
        return {**INCOME_FINANCE_CODES[code], "type": "income"}
    elif code in EXPENDITURE_FINANCE_CODES:
        return {**EXPENDITURE_FINANCE_CODES[code], "type": "expenditure"}
    return None


def classify_finance_code(code: str) -> str:
    """Classify a finance code as income or expenditure."""
    if not code:
        return "unknown"

    # Check explicit mappings
    if code in INCOME_FINANCE_CODES:
        return "income"
    if code in EXPENDITURE_FINANCE_CODES:
        return "expenditure"

    # Use prefix rules
    try:
        prefix = int(code[0])
        if prefix in [4, 5]:  # 4xx, 5xx are income
            return "income"
        elif prefix in [6, 7, 8, 9]:  # 6xx-9xx are expenditure
            return "expenditure"
    except (ValueError, IndexError):
        pass

    return "unknown"
