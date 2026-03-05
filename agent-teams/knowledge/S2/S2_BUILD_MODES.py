"""
S2 Build Modes and Input Configuration
=======================================
Defines the two upload modes and input file types for S2 staff/payroll processing.

Mirrors the S3 pattern for consistency across the application.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# BUILD MODES
# =============================================================================

class BuildMode(Enum):
    """
    Two upload modes available in the app.
    Same pattern as S3 (budget) processing.
    """
    RAW_DATA = "raw_data"
    """
    Raw Data Mode:
    - Customer uploads raw HR/staff export files
    - Agent must map columns, infer roles, classify staff
    - Pay scales, role groups must be extracted/inferred
    - More complex processing required
    """

    PREPOPULATED_TEMPLATE = "prepopulated_template"
    """
    Pre-populated Template Mode:
    - Customer uploads a workbook template that already has:
      - Pay Scales and Points defined
      - Staff Role Groups (SRGs) configured
      - Pension schemes set up
      - EQW Patterns defined
      - Allowance Types configured
    - Agent extracts reference data from template
    - Then applies customer's raw staff data to template structure
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


# Customer-provided input files for S2
CUSTOMER_INPUT_FILES = {
    "staff_list": InputFileType(
        name="Staff List/HR Export",
        description="Staff members, contracts, and salary data",
        required=True,
        typical_content=[
            "Employee names and IDs",
            "Job titles/roles",
            "Contract type (Teaching/Support)",
            "FTE or Hours",
            "Salary/Pay point",
            "Start/End dates",
            "School/Location",
        ],
        file_patterns=["*staff*", "*employee*", "*hr*", "*payroll*", "*personnel*"]
    ),

    "pay_scales": InputFileType(
        name="Pay Scales",
        description="Teacher and Support pay scale definitions",
        required=True,
        typical_content=[
            "Scale names (MPS, UPS, Leadership, NJC)",
            "Point numbers",
            "Annual salary values",
            "Effective dates",
        ],
        file_patterns=["*pay*scale*", "*salary*", "*njc*", "*teacher*pay*"]
    ),

    "allowances": InputFileType(
        name="Allowances",
        description="TLR, SEN, and other allowance definitions",
        required=False,
        typical_content=[
            "TLR1, TLR2, TLR3 amounts",
            "SEN allowance values",
            "Recruitment/Retention amounts",
        ],
        file_patterns=["*allowance*", "*tlr*", "*sen*"]
    ),

    "pension_rates": InputFileType(
        name="Pension Rates",
        description="LGPS and Teachers' Pension contribution rates",
        required=False,
        typical_content=[
            "Employee contribution rates",
            "Employer contribution rates",
            "Salary bands for LGPS",
        ],
        file_patterns=["*pension*", "*lgps*", "*tps*"]
    ),

    "eqw_patterns": InputFileType(
        name="EQW Patterns",
        description="Equated Week patterns for support staff",
        required=False,
        typical_content=[
            "Pattern names (TTO 38, TTO 44, 52 weeks)",
            "Weeks worked",
            "Equated week factors",
        ],
        file_patterns=["*eqw*", "*equated*", "*term*time*"]
    ),
}


# =============================================================================
# TEMPLATE REFERENCE SHEETS
# =============================================================================
"""
When in PREPOPULATED_TEMPLATE mode, these sheets provide reference data
that should be extracted and used (not rebuilt from scratch):
"""

TEMPLATE_REFERENCE_SHEETS = [
    "PayScales",              # Pay scale definitions
    "PayScalePoints",         # Salary points per scale
    "PayScaleGrades",         # Grade definitions
    "PayScaleIncreasePercen", # Annual increase percentages
    "AllowanceTypes",         # TLR, SEN, etc.
    "AllowanceTypePoint",     # Allowance point values
    "AllowanceIncreasePercen",# Allowance increases
    "Pensions",               # Pension scheme definitions
    "EQWPatterns",            # Equated week patterns
    "StfRoleGroup",           # Staff Role Group definitions
    "StfRole",                # Individual role definitions
    "Finance Codes S2",       # Finance code mappings
]


# =============================================================================
# STAFF ROLE GROUP DEFINITIONS
# =============================================================================
"""
Standard Staff Role Groups (SRGs) used across trusts.
"""

STANDARD_STAFF_ROLE_GROUPS = {
    "LEA": {
        "title": "Leadership",
        "description": "Headteachers, Principals, Deputies, Assistant Heads",
        "contract_type": "teaching",
        "finance_prefix": "611",
    },
    "TEA": {
        "title": "Teaching Staff",
        "description": "Classroom teachers, subject leads, heads of department",
        "contract_type": "teaching",
        "finance_prefix": "611",
    },
    "SEN": {
        "title": "SEN Staff",
        "description": "SENCO, SEN teachers, specialist SEN roles",
        "contract_type": "teaching",
        "finance_prefix": "611",
    },
    "SAS": {
        "title": "Support - Academic",
        "description": "Teaching Assistants, HLTAs, Learning Support",
        "contract_type": "support",
        "finance_prefix": "621",
    },
    "SAD": {
        "title": "Support - Admin",
        "description": "Admin staff, office, secretaries, receptionists",
        "contract_type": "support",
        "finance_prefix": "625",
    },
    "SBM": {
        "title": "School Business Management",
        "description": "Business Manager, Finance Officer, HR Manager",
        "contract_type": "support",
        "finance_prefix": "625",
    },
    "SPR": {
        "title": "Support - Premises",
        "description": "Caretakers, cleaners, site managers",
        "contract_type": "support",
        "finance_prefix": "623",
    },
    "SCA": {
        "title": "Support - Catering",
        "description": "Kitchen staff, catering managers, cooks",
        "contract_type": "support",
        "finance_prefix": "627",
    },
    "SWE": {
        "title": "Support - Welfare",
        "description": "Midday supervisors, welfare assistants",
        "contract_type": "support",
        "finance_prefix": "622",
    },
    "STE": {
        "title": "Support - Technical",
        "description": "IT technicians, science technicians, DT technicians",
        "contract_type": "support",
        "finance_prefix": "624",
    },
    "OTH": {
        "title": "Other",
        "description": "Unclassified or specialist roles",
        "contract_type": "support",
        "finance_prefix": "629",
    },
}


# =============================================================================
# JOB TITLE PATTERNS FOR ROLE MAPPING
# =============================================================================
"""
Patterns used to infer Staff Role Group from job titles.
"""

ROLE_TITLE_PATTERNS = {
    "LEA": [
        r"head\s*teacher", r"principal", r"deputy\s*head", r"assistant\s*head",
        r"executive\s*head", r"ceo", r"chief\s*exec",
    ],
    "TEA": [
        r"teacher", r"head\s*of\s*(department|year|subject)", r"hod",
        r"subject\s*lead", r"curriculum\s*lead", r"class\s*teacher",
        r"nqt", r"ect", r"main\s*scale", r"upper\s*pay",
    ],
    "SEN": [
        r"senco", r"sen\s*coordinator", r"inclusion", r"send",
    ],
    "SAS": [
        r"teaching\s*assistant", r"\bta\b", r"hlta", r"learning\s*support",
        r"cover\s*supervisor", r"intervention",
    ],
    "SAD": [
        r"admin", r"office", r"secretary", r"receptionist", r"clerk",
        r"data\s*manager", r"attendance",
    ],
    "SBM": [
        r"business\s*manager", r"finance\s*(officer|manager)", r"bursar",
        r"hr\s*(officer|manager)", r"operations\s*manager",
    ],
    "SPR": [
        r"caretaker", r"site\s*manager", r"cleaner", r"premises",
        r"maintenance", r"groundskeeper",
    ],
    "SCA": [
        r"cook", r"chef", r"catering", r"kitchen",
    ],
    "SWE": [
        r"midday", r"lunchtime", r"welfare", r"msa",
    ],
    "STE": [
        r"technician", r"it\s*support", r"network", r"ict",
        r"science\s*tech", r"dt\s*tech",
    ],
}


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


def get_srg_for_title(job_title: str) -> str:
    """
    Infer Staff Role Group from job title.

    Args:
        job_title: Job title text

    Returns:
        SRG code (e.g., 'TEA', 'SAS') or 'OTH' if unknown
    """
    import re

    if not job_title:
        return "OTH"

    title_lower = job_title.lower()

    for srg, patterns in ROLE_TITLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return srg

    return "OTH"


def get_contract_type_for_srg(srg: str) -> str:
    """
    Get contract type (teaching/support) for a Staff Role Group.

    Args:
        srg: Staff Role Group code

    Returns:
        'teaching' or 'support'
    """
    if srg in STANDARD_STAFF_ROLE_GROUPS:
        return STANDARD_STAFF_ROLE_GROUPS[srg]["contract_type"]
    return "support"


def get_finance_prefix_for_srg(srg: str) -> str:
    """
    Get finance code prefix for a Staff Role Group.

    Args:
        srg: Staff Role Group code

    Returns:
        Finance code prefix (e.g., '611' for teaching)
    """
    if srg in STANDARD_STAFF_ROLE_GROUPS:
        return STANDARD_STAFF_ROLE_GROUPS[srg]["finance_prefix"]
    return "629"
