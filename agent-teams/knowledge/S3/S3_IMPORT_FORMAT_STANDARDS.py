"""
S3 Import Format Standards
==========================
Knowledge extracted from: COR004 - Strand 3 Standard Workbook API.xlsx

This module defines the exact output format required for importing budget data
into the Strand 3 workbook. All S3 agent output must conform to these schemas.

The API workbook defines validation columns that check data integrity before import.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# CORE SHEET SCHEMAS
# =============================================================================

@dataclass
class ColumnSchema:
    """Defines a column in an import sheet."""
    name: str
    data_type: str  # 'string', 'number', 'boolean', 'date'
    required: bool
    max_length: Optional[int] = None
    allowed_values: Optional[List[str]] = None
    default_value: Optional[any] = None
    description: str = ""


# Income Sheet Schema (exact match to API)
INCOME_SHEET_SCHEMA = {
    "sheet_name": "Income",
    "description": "Income budget lines - all income entries for schools",
    "columns": [
        ColumnSchema("FinanceCode", "string", True, 20, description="Standard finance code e.g. 510100"),
        ColumnSchema("SchoolCode", "string", True, 10, description="School identifier e.g. ALS, BLS"),
        ColumnSchema("LedgerCode", "string", True, 20, default_value="COSTCTR", description="Usually COSTCTR"),
        ColumnSchema("DepartmentCode", "string", True, 20, description="Department e.g. IGAG, IPUPIL"),
        ColumnSchema("FundCode", "string", False, 10, description="Optional fund code"),
        ColumnSchema("CalculatorCode", "string", False, 30, description="Calculator for auto-calculation"),
        ColumnSchema("MonthProfileCode", "string", True, 20, default_value="MONTHLY", description="How value spreads across months"),
        ColumnSchema("Description", "string", True, 100, description="Line description"),
        ColumnSchema("Notes", "string", False, 500, description="Additional notes"),
        ColumnSchema("YearNotes", "string", False, 500, description="Year-specific notes"),
        ColumnSchema("MatEditOnly", "boolean", True, default_value=False, description="If True, only MAT can edit"),
        ColumnSchema("FinancialYearCode", "string", True, 7, description="Year code e.g. 2025/26"),
        ColumnSchema("Calculated", "boolean", True, default_value=False, description="If True, value is calculated"),
        ColumnSchema("YearValue", "number", False, description="Annual value (negative for income)"),
    ]
}

# Expenditure Sheet Schema (exact match to API)
EXPENDITURE_SHEET_SCHEMA = {
    "sheet_name": "Expenditure",
    "description": "Expenditure budget lines - all expense entries for schools",
    "columns": [
        ColumnSchema("FinanceCode", "string", True, 20, description="Standard finance code e.g. 611100"),
        ColumnSchema("SchoolCode", "string", True, 10, description="School identifier"),
        ColumnSchema("LedgerCode", "string", True, 20, default_value="COSTCTR", description="Usually COSTCTR"),
        ColumnSchema("DepartmentCode", "string", True, 20, description="Department code"),
        ColumnSchema("FundCode", "string", False, 10, description="Optional fund code"),
        ColumnSchema("CalculatorCode", "string", False, 30, description="Calculator for auto-calculation"),
        ColumnSchema("MonthProfileCode", "string", True, 20, default_value="MONTHLY", description="Month profile"),
        ColumnSchema("Description", "string", True, 100, description="Line description"),
        ColumnSchema("Notes", "string", False, 500, description="Additional notes"),
        ColumnSchema("YearNotes", "string", False, 500, description="Year-specific notes"),
        ColumnSchema("MatEditOnly", "boolean", True, default_value=False, description="MAT edit restriction"),
        ColumnSchema("FinancialYearCode", "string", True, 7, description="Year code"),
        ColumnSchema("Calculated", "boolean", True, default_value=False, description="Is calculated"),
        ColumnSchema("YearValue", "number", False, description="Annual value (positive for expenditure)"),
    ]
}

# Finance Codes Budget Sheet Schema
FINANCE_CODES_BUDGET_SCHEMA = {
    "sheet_name": "FinanceCodes Budget",
    "api_sheet_name": "11_Finance Codes S3",
    "description": "Finance code definitions for budget lines",
    "columns": [
        ColumnSchema("FinanceCode", "string", True, 20, description="Unique finance code"),
        ColumnSchema("Title", "string", True, 100, description="Finance code title"),
        ColumnSchema("GroupingCode", "string", True, 10, description="Grouping e.g. A0, A1, E1"),
        ColumnSchema("CustomGrouping", "string", False, 10, description="Custom grouping"),
        ColumnSchema("AvailableToAllSchools", "boolean", True, default_value=False),
        ColumnSchema("SchoolCodes", "string", False, 500, description="Comma-separated school codes"),
        ColumnSchema("FinanceCodeTypeCode", "string", True, 20, allowed_values=["BUDGET", "STATISTICS"]),
        ColumnSchema("LedgerCode", "string", True, 20, default_value="COSTCTR"),
        ColumnSchema("FinanceCodeEnabled", "boolean", True, default_value=True),
        ColumnSchema("BalanceToScenario", "boolean", False, default_value=False),
    ]
}

# Departments Sheet Schema
DEPARTMENTS_SCHEMA = {
    "sheet_name": "Depts",
    "description": "Department code definitions",
    "columns": [
        ColumnSchema("DepartmentCode", "string", True, 20, description="Unique department code"),
        ColumnSchema("Title", "string", True, 100, description="Department title"),
        ColumnSchema("AvailableToAllSchools", "boolean", True, default_value=False),
        ColumnSchema("SchoolCodes", "string", False, 500, description="Comma-separated school codes"),
        ColumnSchema("ActivityCode", "string", False, 20, description="Activity code"),
        ColumnSchema("FundCode", "string", False, 10, description="Default fund code"),
        ColumnSchema("LedgerCode", "string", True, 20, default_value="COSTCTR"),
        ColumnSchema("DefaultFinanceCode", "string", False, 20),
        ColumnSchema("DepartmentEnabled", "boolean", True, default_value=True),
    ]
}

# Calculators Sheet Schema
CALCULATORS_SCHEMA = {
    "sheet_name": "14_Calculators",
    "description": "Calculator definitions for auto-calculated values",
    "columns": [
        ColumnSchema("CalculatorCode", "string", True, 30, description="Unique calculator code"),
        ColumnSchema("Title", "string", True, 100, description="Calculator title"),
        ColumnSchema("CalculatorEnabled", "boolean", True, default_value=True),
        ColumnSchema("CalculatorTypeCode", "string", True, 20,
                     allowed_values=["DEFAULT", "FUNDING", "BUDGET"],
                     description="Calculator type"),
        ColumnSchema("SourceFinanceCodes", "string", False, 500, description="Source FCs comma-separated"),
        ColumnSchema("MultiplierFinanceCodes", "string", False, 500, description="Multiplier FCs"),
        ColumnSchema("SourceSelectAllSchools", "boolean", False, default_value=False),
        ColumnSchema("SourceSelectAllFunds", "boolean", False, default_value=False),
        ColumnSchema("SourceSelectAllDepartments", "boolean", False, default_value=False),
        ColumnSchema("SourceConstant", "number", False),
        ColumnSchema("CalculatorLockRows", "boolean", False, default_value=False),
    ]
}

# Month Profiles Sheet Schema
MONTH_PROFILES_SCHEMA = {
    "sheet_name": "15_MonthProfiles",
    "description": "Month profile definitions for spreading annual values",
    "columns": [
        ColumnSchema("Code", "string", True, 20, description="Profile code e.g. MONTHLY"),
        ColumnSchema("Title", "string", True, 50, description="Profile title"),
        ColumnSchema("Period01Percentage", "number", True, description="September %"),
        ColumnSchema("Period02Percentage", "number", True, description="October %"),
        ColumnSchema("Period03Percentage", "number", True, description="November %"),
        ColumnSchema("Period04Percentage", "number", True, description="December %"),
        ColumnSchema("Period05Percentage", "number", True, description="January %"),
        ColumnSchema("Period06Percentage", "number", True, description="February %"),
        ColumnSchema("Period07Percentage", "number", True, description="March %"),
        ColumnSchema("Period08Percentage", "number", True, description="April %"),
        ColumnSchema("Period09Percentage", "number", True, description="May %"),
        ColumnSchema("Period10Percentage", "number", True, description="June %"),
        ColumnSchema("Period11Percentage", "number", True, description="July %"),
        ColumnSchema("Period12Percentage", "number", True, description="August %"),
        ColumnSchema("Enabled", "boolean", True, default_value=True),
    ]
}


# =============================================================================
# SCENARIO SHEETS - Budget Lines and Values
# =============================================================================
# ScenarioRows = Budget LINE definitions (the structure/metadata)
# ScenarioYearValues = The actual customer VALUES (the numbers)

# ScenarioRows Sheet Schema (35_ScenarioRows)
SCENARIO_ROWS_SCHEMA = {
    "sheet_name": "35_ScenarioRows",
    "description": "Budget line definitions - the row structure for each budget entry",
    "columns": [
        ColumnSchema("Tab", "string", True, 20, description="Source tab: Income, Expenditure, Statistics, Pupils, Funding"),
        ColumnSchema("ScenarioCode", "string", False, 30, description="Scenario identifier (optional)"),
        ColumnSchema("FinanceCode", "string", True, 20, description="Finance code e.g. 510100"),
        ColumnSchema("SchoolCode", "string", True, 10, description="School identifier"),
        ColumnSchema("LedgerCode", "string", True, 20, default_value="DEFAULT", description="Ledger code"),
        ColumnSchema("DepartmentCode", "string", True, 20, default_value="DEFAULT", description="Department code"),
        ColumnSchema("FundCode", "string", False, 10, description="Fund code"),
        ColumnSchema("CalculatorCode", "string", False, 30, description="Calculator for auto-calculation"),
        ColumnSchema("MonthProfileCode", "string", True, 20, default_value="MONTHLY", description="Month profile"),
        ColumnSchema("StaffMemberCode", "string", False, 20, description="Staff member (for staff costs)"),
        ColumnSchema("StaffRoleCode", "string", False, 20, description="Staff role (for staff costs)"),
        ColumnSchema("ContractReference", "string", False, 50, description="Contract reference"),
        ColumnSchema("ContractDateFrom", "date", False, description="Contract start date"),
        ColumnSchema("ContractDateTo", "date", False, description="Contract end date"),
        ColumnSchema("Description", "string", True, 100, description="Line description"),
        ColumnSchema("Notes", "string", False, 500, description="Additional notes"),
        ColumnSchema("MatEditOnly", "boolean", True, default_value=False, description="MAT edit restriction"),
    ]
}

# ScenarioYearValues Sheet Schema (36_ScenarioYearValues)
SCENARIO_YEAR_VALUES_SCHEMA = {
    "sheet_name": "36_ScenarioYearValues",
    "description": "Budget year values - the actual customer values/amounts for each line",
    "columns": [
        ColumnSchema("Tab", "string", True, 20, description="Source tab: Income, Expenditure, Statistics, Pupils, Funding"),
        ColumnSchema("ScenarioCode", "string", False, 30, description="Scenario identifier (optional)"),
        ColumnSchema("FinanceCode", "string", True, 20, description="Finance code - must match ScenarioRows"),
        ColumnSchema("SchoolCode", "string", True, 10, description="School code - must match ScenarioRows"),
        ColumnSchema("LedgerCode", "string", True, 20, default_value="DEFAULT", description="Ledger code"),
        ColumnSchema("DepartmentCode", "string", True, 20, default_value="DEFAULT", description="Department code"),
        ColumnSchema("Description", "string", False, 100, description="Line description"),
        ColumnSchema("YearNotes", "string", False, 500, description="Year-specific notes"),
        ColumnSchema("FinancialYearCode", "string", True, 7, description="Year code e.g. 2025/26"),
        ColumnSchema("Calculated", "boolean", True, default_value=False, description="If True, value is calculated"),
        ColumnSchema("YearValue", "number", True, description="The actual customer value (always a number)"),
    ]
}

# Monthly Values Sheet Schema (37_Monthly Values)
MONTHLY_VALUES_SCHEMA = {
    "sheet_name": "37_Monthly Values",
    "description": "Monthly breakdown of budget values",
    "columns": [
        ColumnSchema("Tab", "string", True, 20, description="Source tab"),
        ColumnSchema("ScenarioCode", "string", False, 30, description="Scenario identifier"),
        ColumnSchema("FinanceCode", "string", True, 20, description="Finance code"),
        ColumnSchema("SchoolCode", "string", True, 10, description="School code"),
        ColumnSchema("LedgerCode", "string", True, 20, description="Ledger code"),
        ColumnSchema("DepartmentCode", "string", True, 20, description="Department code"),
        ColumnSchema("FinancialYearCode", "string", True, 7, description="Year code"),
        ColumnSchema("Period01Value", "number", False, description="September value"),
        ColumnSchema("Period02Value", "number", False, description="October value"),
        ColumnSchema("Period03Value", "number", False, description="November value"),
        ColumnSchema("Period04Value", "number", False, description="December value"),
        ColumnSchema("Period05Value", "number", False, description="January value"),
        ColumnSchema("Period06Value", "number", False, description="February value"),
        ColumnSchema("Period07Value", "number", False, description="March value"),
        ColumnSchema("Period08Value", "number", False, description="April value"),
        ColumnSchema("Period09Value", "number", False, description="May value"),
        ColumnSchema("Period10Value", "number", False, description="June value"),
        ColumnSchema("Period11Value", "number", False, description="July value"),
        ColumnSchema("Period12Value", "number", False, description="August value"),
    ]
}


# Valid Tab values for scenario sheets
SCENARIO_TAB_VALUES = ["Income", "Expenditure", "Statistics", "Pupils", "Funding", "BF Balances"]


# =============================================================================
# STANDARD CALCULATOR CODES
# =============================================================================

STANDARD_CALCULATORS = {
    # Default/No uplift
    "0%_CALC": {"title": "No Uplift", "type": "DEFAULT"},
    "1%_CALC": {"title": "1% Uplift", "type": "DEFAULT"},
    "2%_CALC": {"title": "2% Uplift", "type": "DEFAULT"},
    "3%_CALC": {"title": "3% Uplift", "type": "DEFAULT"},
    "4%_CALC": {"title": "4% Uplift", "type": "DEFAULT"},
    "5%_CALC": {"title": "5% Uplift", "type": "DEFAULT"},

    # Funding calculators
    "FUNDING_GAG": {"title": "GAG Funding", "type": "FUNDING"},
    "FUNDING_16_19": {"title": "Post 16 Funding", "type": "FUNDING"},
    "FUNDING_HNPOST16": {"title": "High Needs Post 16", "type": "FUNDING"},
    "FUNDING_HNPRE16": {"title": "High Needs Pre 16", "type": "FUNDING"},
    "FUNDING_SFS": {"title": "Student Financial Support", "type": "FUNDING"},

    # AWPU calculators
    "AWPU01_CHE_PRI": {"title": "Total AWPU PRI Cheshire East", "type": "FUNDING"},
    "AWPU02_CHE_KS3": {"title": "Total AWPU KS3 Cheshire East", "type": "FUNDING"},
    "AWPU03_CHE_KS4": {"title": "Total AWPU KS4 Cheshire East", "type": "FUNDING"},

    # Central charges
    "CENTRALCHG_MAT": {"title": "Central Charge MAT", "type": "BUDGET"},
    "CENTRALCHG_SCH": {"title": "Central Charge School", "type": "BUDGET"},
    "CENCHG": {"title": "Central Charge Rate", "type": "BUDGET"},

    # DFC calculators
    "DFC_CORE": {"title": "DFC Core funding", "type": "FUNDING"},
    "DFC_EXP": {"title": "DFC Expenditure", "type": "BUDGET"},
    "DFC_PUPIL_NUR": {"title": "DFC Nursery Per pupil", "type": "FUNDING"},
    "DFC_PUPIL_POST16": {"title": "DFC Post 16 Per pupil", "type": "FUNDING"},

    # Pupil Premium
    "PUPPREMIUM_FACTOR": {"title": "Pupil Premium Factor", "type": "FUNDING"},
    "PUPPREMIUM_CALC": {"title": "Pupil Premium Calculator", "type": "FUNDING"},

    # PE Grant
    "PE_GRANT_CORE": {"title": "PE Grant Core", "type": "FUNDING"},
    "PE_GRANT_PUPIL": {"title": "PE Grant Per Pupil", "type": "FUNDING"},

    # UIFSM
    "UIFSM_CALC": {"title": "UIFSM Calculator", "type": "FUNDING"},
    "UIFSM_RATE": {"title": "UIFSM Rate", "type": "FUNDING"},
}


# =============================================================================
# STANDARD MONTH PROFILES
# =============================================================================

STANDARD_MONTH_PROFILES = {
    "MONTHLY": {
        "title": "Monthly",
        "percentages": [8.3334, 8.3333, 8.3333, 8.3334, 8.3333, 8.3333,
                        8.3334, 8.3333, 8.3333, 8.3334, 8.3333, 8.3333],
    },
    "01.SEPT": {
        "title": "September",
        "percentages": [100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    "TERMLY": {
        "title": "Termly",
        "percentages": [0, 0, 0, 33.33, 0, 0, 0, 33.33, 0, 0, 33.34, 0],
    },
    "WINTER": {
        "title": "Winter Weighting",
        "percentages": [7, 9, 11, 13, 18, 17, 8, 5, 4, 4, 3, 1],
    },
    "M05_APR-AUG": {
        "title": "April to August",
        "percentages": [0, 0, 0, 0, 0, 0, 0, 20, 20, 20, 20, 20],
    },
    "M07_SEP-MAR": {
        "title": "September to March",
        "percentages": [14.2858, 14.2857, 14.2857, 14.2857, 14.2857, 14.2857, 14.2857, 0, 0, 0, 0, 0],
    },
    "M10_SEP-JUN": {
        "title": "Curriculum Spend",
        "percentages": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 0, 0],
    },
    "M11_SEP-JUL": {
        "title": "September to July",
        "percentages": [9.091, 9.0909, 9.0909, 9.0909, 9.0909, 9.0909, 9.0909, 9.0909, 9.0909, 9.0909, 9.0909, 0],
    },
    "QTRLY.01-SEPT": {
        "title": "Quarterly From September",
        "percentages": [25, 0, 0, 25, 0, 0, 25, 0, 0, 25, 0, 0],
    },
    "SEPT_DEC_MAR": {
        "title": "September/December/March",
        "percentages": [33.3334, 0, 0, 33.3333, 0, 0, 33.3333, 0, 0, 0, 0, 0],
    },
}


# =============================================================================
# STANDARD DEPARTMENT CODES
# =============================================================================

STANDARD_DEPARTMENTS = {
    # Income Departments
    "IGAG": {"title": "GAG Income", "activity": "SCHOOL", "fund": "GAG"},
    "IPUPIL": {"title": "Pupil Premium Income", "activity": "SCHOOL", "fund": "PP"},
    "IUIFSM": {"title": "UIFSM Income", "activity": "SCHOOL", "fund": "UIFSM"},
    "ISPORT": {"title": "Sports Grant Income", "activity": "SCHOOL", "fund": "SPORT"},
    "IDFE": {"title": "DfE Revenue Grants", "activity": "SCHOOL", "fund": "DEFAULT"},
    "INTRA": {"title": "Trading Income", "activity": "COMM", "fund": "TRADE"},

    # Expenditure Departments
    "STLEA": {"title": "Leadership Staff", "activity": "SCHOOL", "fund": "DEFAULT"},
    "STADM": {"title": "Admin Staff", "activity": "DEFAULT", "fund": "DEFAULT"},
    "ADMIN": {"title": "Administration", "activity": "DEFAULT", "fund": "DEFAULT"},
    "ADMINSER": {"title": "MAT contribution", "activity": "DEFAULT", "fund": "DEFAULT"},
    "EXDFC": {"title": "DFC Expenditure", "activity": "SCHOOL", "fund": "DFC"},
    "TCT_CS": {"title": "Central Services", "activity": "DEFAULT", "fund": "DEFAULT"},

    # Activity Departments
    "ACHIEVE": {"title": "Keep on Track / Achievement", "activity": "SCHOOL", "fund": "GAG"},
    "ALTPROV": {"title": "Alternative Provision", "activity": "DEFAULT", "fund": "DESF"},
    "BFL": {"title": "Behaviour for Learning", "activity": "DEFAULT", "fund": "DEFAULT"},
}


# =============================================================================
# VALIDATION RULES
# =============================================================================

class ValidationSeverity(Enum):
    ERROR = "error"      # Will fail import
    WARNING = "warning"  # Will import but flagged
    INFO = "info"        # Informational


@dataclass
class ValidationRule:
    """Defines a validation rule for data checking."""
    name: str
    description: str
    severity: ValidationSeverity
    check_function: str  # Name of function to call


VALIDATION_RULES = {
    "duplicate_line": ValidationRule(
        "DuplicateLine",
        "Check for duplicate entries (same FC + School + Dept)",
        ValidationSeverity.ERROR,
        "check_duplicate_line"
    ),
    "finance_code_issue": ValidationRule(
        "FinanceCodeIssue",
        "Finance code must exist in FinanceCodes Budget sheet",
        ValidationSeverity.ERROR,
        "check_finance_code"
    ),
    "location_issue": ValidationRule(
        "LocationIssue",
        "School code must exist in Schools sheet",
        ValidationSeverity.ERROR,
        "check_school_code"
    ),
    "ledger_issue": ValidationRule(
        "LedgerIssue",
        "Ledger code must be valid (COSTCTR, CAPITAL, etc.)",
        ValidationSeverity.WARNING,
        "check_ledger_code"
    ),
    "month_profile_issue": ValidationRule(
        "MonthProfileIssue",
        "Month profile code must exist in MonthProfiles sheet",
        ValidationSeverity.ERROR,
        "check_month_profile"
    ),
    "department_issue": ValidationRule(
        "DepartmentIssue",
        "Department code must exist in Depts sheet",
        ValidationSeverity.ERROR,
        "check_department"
    ),
    "calc_issue": ValidationRule(
        "CalcIssue",
        "If Calculated=True, CalculatorCode must be set",
        ValidationSeverity.WARNING,
        "check_calculator"
    ),
    "code_uppercase": ValidationRule(
        "CodesAreUppercase",
        "All codes must be uppercase",
        ValidationSeverity.WARNING,
        "check_uppercase"
    ),
    "description_length": ValidationRule(
        "DescriptionLengthCheck",
        "Description must not exceed 100 characters",
        ValidationSeverity.WARNING,
        "check_description_length"
    ),
    "true_false_check": ValidationRule(
        "TRUEFALSECheck",
        "Boolean fields must be True or False",
        ValidationSeverity.ERROR,
        "check_boolean"
    ),
    "year_code_check": ValidationRule(
        "FinancialYearCodeCheck",
        "Year code format must be YYYY/YY e.g. 2025/26",
        ValidationSeverity.ERROR,
        "check_year_code"
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_schema_for_sheet(sheet_name: str) -> Optional[Dict]:
    """Get the schema for a given sheet name."""
    schemas = {
        "Income": INCOME_SHEET_SCHEMA,
        "Expenditure": EXPENDITURE_SHEET_SCHEMA,
        "FinanceCodes Budget": FINANCE_CODES_BUDGET_SCHEMA,
        "11_Finance Codes S3": FINANCE_CODES_BUDGET_SCHEMA,
        "Depts": DEPARTMENTS_SCHEMA,
        "14_Calculators": CALCULATORS_SCHEMA,
        "15_MonthProfiles": MONTH_PROFILES_SCHEMA,
    }
    return schemas.get(sheet_name)


def get_required_columns(sheet_name: str) -> List[str]:
    """Get list of required columns for a sheet."""
    schema = get_schema_for_sheet(sheet_name)
    if not schema:
        return []
    return [col.name for col in schema["columns"] if col.required]


def get_column_default(sheet_name: str, column_name: str) -> Optional[any]:
    """Get default value for a column."""
    schema = get_schema_for_sheet(sheet_name)
    if not schema:
        return None
    for col in schema["columns"]:
        if col.name == column_name:
            return col.default_value
    return None


def validate_year_code(year_code: str) -> bool:
    """Validate financial year code format (YYYY/YY)."""
    import re
    pattern = r"^\d{4}/\d{2}$"
    if not re.match(pattern, year_code):
        return False
    # Check year consistency
    try:
        first_year = int(year_code[:4])
        second_year = int(year_code[5:7])
        return second_year == (first_year + 1) % 100
    except ValueError:
        return False


def get_income_sign_convention() -> str:
    """
    Return the income sign convention.
    In this system, income values should be NEGATIVE (credit).
    """
    return "negative"


def get_expenditure_sign_convention() -> str:
    """
    Return the expenditure sign convention.
    In this system, expenditure values should be POSITIVE (debit).
    """
    return "positive"
