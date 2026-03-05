"""
S3 Build Modes and Input Configuration
=======================================
Defines the two upload modes and input file types for S3 budget processing.

CRITICAL: The system supports two distinct upload modes that must be handled differently.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# BUILD MODES
# =============================================================================

class BuildMode(Enum):
    """
    Two upload modes available in the app.
    Same pattern applies to S2 (staff) processing.
    """
    RAW_DATA = "raw_data"
    """
    Raw Data Mode:
    - Customer uploads raw budget files that need analysis
    - Agent must map columns, infer structure, classify data
    - Departments, schools, codes must be extracted/inferred
    - More complex processing required
    """

    PREPOPULATED_TEMPLATE = "prepopulated_template"
    """
    Pre-populated Template Mode:
    - Customer uploads a workbook template that already has:
      - Schools list with SchoolCode, SchoolType, etc.
      - Department codes mapped
      - Fund codes defined
      - Local Authority rates set
      - Calculator definitions
    - Agent extracts reference data from template
    - Then applies customer's raw budget data to template structure
    """


# =============================================================================
# INPUT FILE TYPES
# =============================================================================

@dataclass
class InputFileType:
    """Defines an input file type the customer may provide."""
    name: str
    description: str
    required: bool
    typical_content: List[str]
    file_patterns: List[str]


# Customer-provided input files
CUSTOMER_INPUT_FILES = {
    "budget": InputFileType(
        name="Budget File",
        description="Income and Expenditure budget data",
        required=True,
        typical_content=[
            "Finance codes (nominal codes)",
            "School/location codes",
            "Department/cost centre codes",
            "Budget values by year",
            "Sometimes monthly breakdown",
        ],
        file_patterns=["*budget*", "*income*", "*expenditure*", "*forecast*"]
    ),

    "pupil_census": InputFileType(
        name="Pupil Census Data",
        description="Spring/Autumn census pupil numbers",
        required=True,
        typical_content=[
            "Pupil counts by key stage (FS, KS1, KS2, KS3, KS4, KS5)",
            "School identifiers",
            "Census date/period",
            "Sometimes FSM eligibility counts",
        ],
        file_patterns=["*census*", "*pupil*", "*student*"]
    ),

    "funding_statement": InputFileType(
        name="DfE Funding Statement",
        description="Official DfE funding allocation statement",
        required=True,
        typical_content=[
            "GAG allocation breakdown",
            "AWPU calculations",
            "Pupil Premium amounts",
            "High Needs funding",
            "Post-16 funding",
        ],
        file_patterns=["*funding*", "*statement*", "*allocation*", "*gag*"]
    ),

    "brought_forward": InputFileType(
        name="Brought Forward Balances",
        description="Opening balances from previous year",
        required=True,
        typical_content=[
            "Revenue BF balance per school",
            "Capital BF balance per school",
            "Sometimes restricted/unrestricted split",
        ],
        file_patterns=["*balance*", "*bf*", "*brought*forward*", "*opening*"]
    ),

    "statistics": InputFileType(
        name="Statistics/Rates",
        description="Uplift percentages and rates (optional)",
        required=False,
        typical_content=[
            "Inflation rates",
            "Pay uplift percentages",
            "Custom calculation rates",
        ],
        file_patterns=["*statistic*", "*rate*", "*uplift*"]
    ),
}


# =============================================================================
# SCENARIO CODES - CRITICAL DISTINCTION
# =============================================================================
"""
CRITICAL: Two budget types that MUST NOT be confused!

1. APPROVED BUDGET (APBUD)
   - Full year budget
   - Set at start of financial year
   - ScenarioCode: APBUD{YYYY} e.g., APBUD2526

2. MASTER BUDGET (MASTER)
   - Changed in-year
   - Reflects amendments/virements made during the year
   - ScenarioCode: MASTER{YYYY} e.g., MASTER2526

The customer files will be labeled indicating which budget type they represent.
Agent MUST correctly identify and tag the scenario code.
"""

class BudgetType(Enum):
    APPROVED = "approved"  # Full year, set at start
    MASTER = "master"      # Changed in-year


@dataclass
class ScenarioConfig:
    """Configuration for a budget scenario."""
    scenario_code: str
    budget_type: BudgetType
    description: str
    year_code: str


def generate_scenario_code(budget_type: BudgetType, year_code: str) -> str:
    """
    Generate the scenario code for a budget.

    Args:
        budget_type: APPROVED or MASTER
        year_code: Financial year e.g., "2025/26"

    Returns:
        Scenario code e.g., "APBUD2526" or "MASTER2526"
    """
    # Convert year code to compact format
    year_parts = year_code.replace("/", "").replace("-", "")
    if len(year_parts) == 6:  # 202526
        year_suffix = year_parts[2:6]  # 2526
    elif len(year_parts) == 4:  # 2526
        year_suffix = year_parts
    else:
        year_suffix = year_code.replace("/", "")

    if budget_type == BudgetType.APPROVED:
        return f"APBUD{year_suffix}"
    elif budget_type == BudgetType.MASTER:
        return f"MASTER{year_suffix}"
    else:
        return f"BUDGET{year_suffix}"


def detect_budget_type_from_filename(filename: str) -> Optional[BudgetType]:
    """
    Detect budget type from filename.

    Args:
        filename: Name of the budget file

    Returns:
        BudgetType or None if cannot determine
    """
    filename_lower = filename.lower()

    # Check for approved budget indicators
    approved_indicators = [
        "approved", "apbud", "app budget", "approved budget",
        "full year", "annual budget", "original budget"
    ]
    for indicator in approved_indicators:
        if indicator in filename_lower:
            return BudgetType.APPROVED

    # Check for master budget indicators
    master_indicators = [
        "master", "amended", "revised", "current", "in-year",
        "inyear", "in year", "updated", "latest"
    ]
    for indicator in master_indicators:
        if indicator in filename_lower:
            return BudgetType.MASTER

    return None


# =============================================================================
# TEMPLATE DATA SOURCES
# =============================================================================
"""
When in PREPOPULATED_TEMPLATE mode, these sheets provide reference data
that should be extracted and used (not rebuilt from scratch):
"""

TEMPLATE_REFERENCE_SHEETS = [
    "Schools",           # School codes, types, hubs, URNs
    "Depts",             # Department code definitions
    "Funds",             # Fund code definitions
    "LocalAuth",         # Local authority and rates
    "14_Calculators",    # Calculator definitions
    "15_MonthProfiles",  # Month profile definitions
    "FinanceCodes Budget",  # Standard finance codes
    "11_Finance Codes S3",  # S3-specific finance codes
    "Activity",          # Activity codes
    "Ledger",            # Ledger codes
    "SchHub",            # School hub definitions
    "SchType",           # School type definitions
]


# =============================================================================
# STANDARD STATISTICS ROWS
# =============================================================================
"""
These uplift statistics rows are created automatically for EVERY school.
Users can amend the values post-build.
"""

STANDARD_UPLIFT_STATISTICS = [
    {
        "finance_code": "UPLIFT_PUPILASCL%",
        "description": "Pupil ASCL Uplift %",
        "notes": "Percentage change of pupil numbers from previous year combined with ASCL Uplift %",
        "calculator_code": "PUPILASCL_FACTOR",
    },
    {
        "finance_code": "UPLIFT_PUPILEXP%",
        "description": "Pupil Expenditure Uplift %",
        "notes": "Percentage change of pupil numbers from previous year combined with Expenditure Uplift %",
        "calculator_code": "PUPILEXP_FACTOR",
    },
    {
        "finance_code": "UPLIFT_PUPILGAG%",
        "description": "Pupil GAG Uplift %",
        "notes": "Percentage change of pupil numbers from previous year combined with GAG Uplift %",
        "calculator_code": "PUPILGAG_FACTOR",
    },
    {
        "finance_code": "UPLIFT_PUPILINC%",
        "description": "Pupil Income Uplift %",
        "notes": "Percentage change of pupil numbers from previous year combined with Income Uplift %",
        "calculator_code": "PUPILINC_FACTOR",
    },
    {
        "finance_code": "UPLIFT_PUPILRPI%",
        "description": "Pupil RPI Uplift %",
        "notes": "Percentage change of pupil numbers from previous year combined with RPI Uplift %",
        "calculator_code": "PUPILRPI_FACTOR",
    },
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_required_input_files() -> List[str]:
    """Get list of required input file types."""
    return [name for name, config in CUSTOMER_INPUT_FILES.items() if config.required]


def get_all_input_files() -> List[str]:
    """Get list of all input file types."""
    return list(CUSTOMER_INPUT_FILES.keys())


def is_raw_data_mode(has_template: bool) -> BuildMode:
    """Determine build mode based on whether template is provided."""
    return BuildMode.PREPOPULATED_TEMPLATE if has_template else BuildMode.RAW_DATA
