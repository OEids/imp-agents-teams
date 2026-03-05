"""
S3 Column Mappings
==================
Comprehensive column mapping rules for transforming customer budget data
into the standard S3 import format.

This module provides intelligent mapping functions that can handle:
- Direct column name matches
- Fuzzy/partial matches
- Content-based inference
- Multi-column extraction
"""

from typing import Dict, List, Tuple, Optional, Any
import re
from dataclasses import dataclass


# =============================================================================
# COLUMN MAPPING DEFINITIONS
# =============================================================================

@dataclass
class ColumnMapping:
    """Defines a mapping from source to target column."""
    target: str                     # Target column name in API format
    sources: List[str]              # Possible source column names (priority order)
    patterns: List[str]             # Regex patterns for fuzzy matching
    default: Optional[Any] = None   # Default value if no match
    transform: Optional[str] = None # Name of transform function


# Finance Code Mappings
FINANCE_CODE_MAPPING = ColumnMapping(
    target="FinanceCode",
    sources=[
        "FinanceCode", "Finance Code", "Finance_Code",
        "Nominal Code", "Nominal", "NOMINAL", "Nomina;",
        "NL Code", "NL", "GL Code", "GL",
        "Code", "Account Code", "Account",
    ],
    patterns=[
        r"(?i)nominal\s*code?",
        r"(?i)finance\s*code?",
        r"(?i)^code$",
        r"(?i)^nl\s*code?$",
        r"(?i)^gl\s*code?$",
        r"(?i)^account\s*code?$",
        r"(?i)^account$",
    ],
    default=None
)

# School Code Mappings
SCHOOL_CODE_MAPPING = ColumnMapping(
    target="SchoolCode",
    sources=[
        "SchoolCode", "School Code", "School_Code",
        "Location", "Site", "Entity", "Academy",
        "Company", "Cost Centre", "CostCentre",
    ],
    patterns=[
        r"(?i)school\s*code?",
        r"(?i)^location$",
        r"(?i)^site$",
        r"(?i)^entity$",
        r"(?i)^academy$",
        r"(?i)^company$",
    ],
    default=""
)

# Department Code Mappings
DEPARTMENT_CODE_MAPPING = ColumnMapping(
    target="DepartmentCode",
    sources=[
        "DepartmentCode", "Department Code", "Department_Code",
        "Dept", "Department", "Dept Code",
        "Cost Centre", "CostCentre", "Cost Center",
        "CC", "Analysis Code", "Fund Code",
    ],
    patterns=[
        r"(?i)department\s*code?",
        r"(?i)^dept(\s*code)?$",
        r"(?i)cost\s*cent(re|er)",
        r"(?i)^cc$",
        r"(?i)analysis\s*code",
    ],
    default="DEFAULT"
)

# Ledger Code Mappings
LEDGER_CODE_MAPPING = ColumnMapping(
    target="LedgerCode",
    sources=[
        "LedgerCode", "Ledger Code", "Ledger_Code",
        "Ledger", "Account Type", "Account",
    ],
    patterns=[
        r"(?i)ledger\s*code?",
        r"(?i)^ledger$",
        r"(?i)account\s*type",
    ],
    default="COSTCTR"
)

# Fund Code Mappings
FUND_CODE_MAPPING = ColumnMapping(
    target="FundCode",
    sources=[
        "FundCode", "Fund Code", "Fund_Code",
        "Funds", "Fund", "Fund Type", "Funding Source",
    ],
    patterns=[
        r"(?i)fund\s*code?",
        r"(?i)^funds?$",
        r"(?i)fund\s*type",
        r"(?i)funding\s*source",
    ],
    default=""
)

# Description Mappings
DESCRIPTION_MAPPING = ColumnMapping(
    target="Description",
    sources=[
        "Description", "Desc", "Title", "Name",
        "Account Title", "Account Name", "Account Description",
        "Nominal Description", "Section Name", "Line Description",
    ],
    patterns=[
        r"(?i)^description$",
        r"(?i)^desc$",
        r"(?i)^title$",
        r"(?i)^name$",
        r"(?i)account\s*(title|name|desc)",
        r"(?i)nominal\s*desc",
        r"(?i)section\s*name",
    ],
    default=""
)

# Calculator Code Mappings
CALCULATOR_CODE_MAPPING = ColumnMapping(
    target="CalculatorCode",
    sources=[
        "CalculatorCode", "Calculator Code", "Calculator_Code",
        "Calculator", "Calc Code", "Calculation Code",
    ],
    patterns=[
        r"(?i)calculator\s*code?",
        r"(?i)^calc(\s*code)?$",
        r"(?i)calculation\s*code",
    ],
    default=""
)

# Month Profile Mappings
MONTH_PROFILE_MAPPING = ColumnMapping(
    target="MonthProfileCode",
    sources=[
        "MonthProfileCode", "Month Profile Code", "MonthProfile_Code",
        "Profile", "Month Profile", "Phasing", "Spread",
    ],
    patterns=[
        r"(?i)month\s*profile\s*code?",
        r"(?i)^profile$",
        r"(?i)^phasing$",
        r"(?i)^spread$",
    ],
    default="MONTHLY"
)

# Year Value Mappings (budget amounts)
YEAR_VALUE_MAPPING = ColumnMapping(
    target="YearValue",
    sources=[
        "YearValue", "Year Value", "Amount", "Value",
        "Budget", "Budget Year", "Annual", "Total",
        "Approved", "Master", "Consolidated",
    ],
    patterns=[
        r"(?i)year\s*value",
        r"(?i)^amount$",
        r"(?i)^value$",
        r"(?i)^budget(\s*year)?$",
        r"(?i)^annual$",
        r"(?i)^total$",
        r"(?i)^approved$",
        r"(?i)202\d[-/]2\d",  # Year format like 2025-26 or 2025/26
        r"(?i)202\d\s*-\s*2\d",  # 2025 - 26
    ],
    default=0.0
)

# Financial Year Code Mappings
FINANCIAL_YEAR_MAPPING = ColumnMapping(
    target="FinancialYearCode",
    sources=[
        "FinancialYearCode", "Financial Year Code", "Year Code",
        "Year", "FY", "Financial Year",
    ],
    patterns=[
        r"(?i)financial\s*year\s*code?",
        r"(?i)^year\s*code$",
        r"(?i)^fy$",
        r"(?i)^year$",
    ],
    default="2025/26"
)


# All mappings in priority order
ALL_COLUMN_MAPPINGS = [
    FINANCE_CODE_MAPPING,
    SCHOOL_CODE_MAPPING,
    DEPARTMENT_CODE_MAPPING,
    LEDGER_CODE_MAPPING,
    FUND_CODE_MAPPING,
    DESCRIPTION_MAPPING,
    CALCULATOR_CODE_MAPPING,
    MONTH_PROFILE_MAPPING,
    YEAR_VALUE_MAPPING,
    FINANCIAL_YEAR_MAPPING,
]


# =============================================================================
# VALUE COLUMN PATTERNS
# =============================================================================
# Patterns for recognizing columns that contain budget values

YEAR_COLUMN_PATTERNS = [
    # Standard year formats
    r"^\d{4}[-/]\d{2}$",           # 2025/26, 2025-26
    r"^\d{4}\s*-\s*\d{2}$",        # 2025 - 26
    r"^\d{4}[-/]\d{4}$",           # 2025/2026, 2025-2026
    r"^FY\s*\d{4}[-/]?\d{2,4}$",   # FY2025/26, FY 2025-26

    # Date-based columns (monthly)
    r"^\d{4}-\d{2}-\d{2}",         # 2025-09-01

    # Named periods
    r"(?i)^PERIOD\s*\d{1,2}$",     # PERIOD 1, PERIOD 12
    r"(?i)^P\d{1,2}$",             # P1, P12
]

MONTH_COLUMN_PATTERNS = [
    # Full month names
    r"(?i)^(January|February|March|April|May|June|July|August|September|October|November|December)$",
    # Abbreviated
    r"(?i)^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$",
    # With year
    r"(?i)^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{2,4}$",
]

SCHOOL_COLUMN_PATTERNS = [
    # School-specific columns in MAT consolidated reports
    r"(?i)SCHOOL\s*\d+",           # SCHOOL 1, SCHOOL 2
    r"^\d{3}\s+[A-Z]",             # 206 SCHOOL NAME pattern
    r"(?i)^(Primary|Secondary|Central|Special)\s*$",  # School type totals
]


# =============================================================================
# SECTION/LINE TYPE PATTERNS
# =============================================================================
# Patterns for determining income vs expenditure from section codes

INCOME_SECTION_PATTERNS = [
    r"(?i)^IL\s*\d",               # IL 101, IL 220
    r"(?i)^A\d",                   # A0, A1 (grouping codes)
    r"(?i)income",
    r"(?i)revenue",
    r"(?i)receipt",
    r"(?i)grant",
    r"(?i)funding",
]

EXPENDITURE_SECTION_PATTERNS = [
    r"(?i)^EL\s*\d",               # EL 300, EL 303b
    r"(?i)^E\d",                   # E1, E3 (grouping codes)
    r"(?i)expenditure",
    r"(?i)expense",
    r"(?i)cost",
    r"(?i)spend",
]


# =============================================================================
# FINANCE CODE EXTRACTION PATTERNS
# =============================================================================
# Patterns for extracting finance codes from complex strings

FINANCE_CODE_EXTRACTION_PATTERNS = [
    # Standard 6-digit code
    r"^(\d{6})\b",                 # 510100 at start
    r"\b(\d{6})\s*-",              # 510100 - Description
    r"\((\d{6})\)",                # (510100) in description

    # Code with description
    r"^([A-Z]{3}\d{6})",           # SCH510100 pattern
    r"^(\d{2}-\d{3}-\d{4}-\d{2})", # 50-200-1000-10 pattern

    # Named format
    r"(\d{6})\s*[-:]\s*",          # 510100: or 510100 -
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_matching_column(columns: List[str], mapping: ColumnMapping) -> Optional[str]:
    """
    Find a column that matches the given mapping.

    Args:
        columns: List of column names from source data
        mapping: ColumnMapping to match against

    Returns:
        Matching column name or None
    """
    # First try exact matches from sources list
    for source in mapping.sources:
        for col in columns:
            if col.lower().strip() == source.lower().strip():
                return col

    # Then try pattern matching
    for pattern in mapping.patterns:
        regex = re.compile(pattern)
        for col in columns:
            if regex.search(col.strip()):
                return col

    return None


def map_all_columns(source_columns: List[str]) -> Dict[str, str]:
    """
    Map all source columns to target columns.

    Args:
        source_columns: List of column names from source data

    Returns:
        Dict mapping source column -> target column
    """
    mappings = {}
    used_sources = set()

    for mapping in ALL_COLUMN_MAPPINGS:
        match = find_matching_column(
            [c for c in source_columns if c not in used_sources],
            mapping
        )
        if match:
            mappings[match] = mapping.target
            used_sources.add(match)

    return mappings


def extract_finance_code(text: str) -> Optional[str]:
    """
    Extract a finance code from a text string.

    Args:
        text: Text that may contain a finance code

    Returns:
        Extracted finance code or None
    """
    if not text:
        return None

    text = str(text).strip()

    for pattern in FINANCE_CODE_EXTRACTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            code = match.group(1)
            # Remove any prefix like SCH
            if code.startswith(('SCH', 'MAT', 'TRU')):
                code = code[3:]
            return code

    # If no pattern matched but looks like a code, return as-is
    if re.match(r'^\d{6}$', text):
        return text

    return None


def is_value_column(column_name: str) -> bool:
    """Check if a column name represents a value/amount column."""
    for pattern in YEAR_COLUMN_PATTERNS + MONTH_COLUMN_PATTERNS:
        if re.search(pattern, column_name):
            return True
    return False


def is_school_column(column_name: str) -> bool:
    """Check if a column name represents a school-specific column."""
    for pattern in SCHOOL_COLUMN_PATTERNS:
        if re.search(pattern, column_name):
            return True
    return False


def determine_line_type(section: str = None, code: str = None, amount: float = None) -> str:
    """
    Determine if a line is income or expenditure.

    Args:
        section: Section code like 'IL 101' or 'EL 300'
        code: Finance code like '510100' or '611100'
        amount: The value amount (negative often = income)

    Returns:
        'income', 'expenditure', or 'unknown'
    """
    # Check section code first
    if section:
        for pattern in INCOME_SECTION_PATTERNS:
            if re.search(pattern, str(section)):
                return "income"
        for pattern in EXPENDITURE_SECTION_PATTERNS:
            if re.search(pattern, str(section)):
                return "expenditure"

    # Check finance code prefix
    if code:
        code_str = str(code).strip()
        if code_str and code_str[0].isdigit():
            first_digit = int(code_str[0])
            if first_digit in [4, 5]:
                return "income"
            elif first_digit in [6, 7, 8, 9]:
                return "expenditure"

    # Fallback to amount sign
    if amount is not None:
        if amount < 0:
            return "income"
        elif amount > 0:
            return "expenditure"

    return "unknown"


def extract_year_from_column(column_name: str) -> Optional[str]:
    """
    Extract financial year code from a column name.

    Args:
        column_name: Column name like "2025/26" or "2025 - 26"

    Returns:
        Standardized year code like "2025/26" or None
    """
    # Standard format
    match = re.search(r'(\d{4})[-/](\d{2})', column_name)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    # Extended format 2025/2026
    match = re.search(r'(\d{4})[-/](\d{4})', column_name)
    if match:
        return f"{match.group(1)}/{match.group(2)[2:]}"

    # Spaced format
    match = re.search(r'(\d{4})\s*-\s*(\d{2})', column_name)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    return None


def normalize_amount(value: Any, line_type: str = None) -> Optional[float]:
    """
    Normalize an amount value, handling currency symbols and formatting.

    Args:
        value: Raw value from source data
        line_type: 'income' or 'expenditure' for sign convention

    Returns:
        Normalized float value or None
    """
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return None

    # Convert to string and clean
    val_str = str(value).strip()
    val_str = val_str.replace('£', '').replace('$', '').replace(',', '')
    val_str = val_str.replace('(', '-').replace(')', '')  # Accounting negative

    try:
        amount = float(val_str)

        # Apply sign convention if specified
        if line_type == "income" and amount > 0:
            amount = -amount
        elif line_type == "expenditure" and amount < 0:
            amount = abs(amount)

        return amount
    except (ValueError, TypeError):
        return None


def get_default_department_for_finance_code(finance_code: str) -> str:
    """
    Get the default department code for a finance code.

    Args:
        finance_code: Finance code like '510100'

    Returns:
        Default department code
    """
    from .S3_BUDGET_TERMINOLOGY import INCOME_FINANCE_CODES, EXPENDITURE_FINANCE_CODES

    if finance_code in INCOME_FINANCE_CODES:
        return INCOME_FINANCE_CODES[finance_code].get("dept", "DEFAULT")
    if finance_code in EXPENDITURE_FINANCE_CODES:
        return EXPENDITURE_FINANCE_CODES[finance_code].get("dept", "DEFAULT")

    # Prefix-based defaults
    if finance_code.startswith("510"):
        if finance_code in ["510100", "510110", "510120", "510700"]:
            return "IGAG"
        elif finance_code.startswith("5102"):
            return "IPUPIL"
        elif finance_code.startswith("5104"):
            return "ISPORT"
        return "IGAG"
    elif finance_code.startswith("6"):
        return "STAFF"

    return "DEFAULT"
