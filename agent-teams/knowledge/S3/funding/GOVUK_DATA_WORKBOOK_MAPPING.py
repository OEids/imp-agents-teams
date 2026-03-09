"""
GOV.UK Grant Data → Workbook Mapping
=====================================
Defines where data from GOV.UK grant allocation files should be inserted
into the S3 workbook.

DATA FLOW:
1. GOV.UK files contain: Pupil counts, Rates, Allocations
2. Workbook needs:
   - Pupils tab: Eligible pupil counts (PP, UIFSM)
   - Statistics tab: Per-pupil rates
   - Funding tab: ONLY GAG entered values (NOT calculated ones)

CRITICAL - FUNDING TAB RULES:
- Most Funding values are CALCULATED automatically (DFC, AWPU, Totals)
- Only GAG "entered" values should be inserted:
  - Deprivation (IDACI bands, FSM, FSM6)
  - Prior Attainment, EAL, Mobility
  - London Fringe, PFI, Split Sites, Sparsity
  - Minimum per pupil, MFG, Funding statement adjustment
  - Post-16 GAG lines

DO NOT INSERT into Funding tab:
- DFC amounts (calculated from rates × pupils)
- AWPU amounts (calculated from rates × pupils)
- Total lines (DFE_TOTAL, DFE_POST16_TOTAL)
- Pupil Premium amounts (calculated)
- PE Grant amounts (calculated)
- UIFSM amounts (calculated)

These are all calculated from Pupils × Rates automatically.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


# =============================================================================
# WORKBOOK TABS AND THEIR PURPOSE
# =============================================================================
"""
Tab             | Purpose                           | Data Type
----------------|-----------------------------------|------------------
Pupils          | Eligible pupil counts             | Numbers (integers)
Statistics      | Per-pupil rates                   | Rates (decimals/currency)
Funding         | Allocation amounts for review     | Currency (£)
Income          | Calculated income (auto)          | Currency (calculated)
ScenarioYearValues | All values with year code     | All types
"""


# =============================================================================
# PUPIL PREMIUM DATA MAPPING
# =============================================================================
"""
GOV.UK Pupil Premium allocation files contain:
- URN (school identifier)
- School name
- Number of eligible pupils (by category)
- Per-pupil rate (national rate)
- Total allocation (pupils × rate)

We need to import:
1. Pupil counts → Pupils tab
2. Rates → Statistics tab (usually national rates, same for all schools)

DO NOT import allocation amounts - they are CALCULATED in the workbook.
"""

@dataclass
class PupilPremiumMapping:
    """Maps PP data columns to workbook locations."""
    govuk_column: str           # Column name in GOV.UK file
    govuk_patterns: List[str]   # Alternative column name patterns
    target_tab: str             # Workbook tab: Pupils, Statistics, Funding
    finance_code: str           # FinanceCode in workbook
    description: str            # Description to match
    value_type: str             # 'count', 'rate', or 'amount'


PUPIL_PREMIUM_MAPPINGS = [
    # Pupil Counts → Pupils tab
    PupilPremiumMapping(
        govuk_column="Number of primary pupils",
        govuk_patterns=["primary pupils", "pri pupils", "number primary"],
        target_tab="Pupils",
        finance_code="PUPILPREMIUM_PRI",
        description="Pupil Premium Numbers Primary",
        value_type="count"
    ),
    PupilPremiumMapping(
        govuk_column="Number of secondary pupils",
        govuk_patterns=["secondary pupils", "sec pupils", "number secondary"],
        target_tab="Pupils",
        finance_code="PUPILPREMIUM_SEC",
        description="Pupil Premium Numbers Secondary",
        value_type="count"
    ),
    PupilPremiumMapping(
        govuk_column="Number of looked after children",
        govuk_patterns=["lac pupils", "looked after", "lac number"],
        target_tab="Pupils",
        finance_code="PUPILPREMIUMPLAC",
        description="Pupil Premium PLAC Numbers",
        value_type="count"
    ),
    PupilPremiumMapping(
        govuk_column="Number of service children",
        govuk_patterns=["service children", "service pupils"],
        target_tab="Pupils",
        finance_code="PUPILPREMIUMSER",
        description="Pupil Premium Service Numbers",
        value_type="count"
    ),

    # Rates → Statistics tab (national rates, same for all)
    PupilPremiumMapping(
        govuk_column="Primary per pupil rate",
        govuk_patterns=["primary rate", "pri rate"],
        target_tab="Statistics",
        finance_code="PUPPRI_RATE",
        description="Pupil Premium Rate Primary",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="Secondary per pupil rate",
        govuk_patterns=["secondary rate", "sec rate"],
        target_tab="Statistics",
        finance_code="PUPSEC_RATE",
        description="Pupil Premium Rate Secondary",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="LAC per pupil rate",
        govuk_patterns=["lac rate", "plac rate"],
        target_tab="Statistics",
        finance_code="PUPLAC_RATE",
        description="Pupil Premium PLAC Rate",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="Service children per pupil rate",
        govuk_patterns=["service rate"],
        target_tab="Statistics",
        finance_code="PUPSER_RATE",
        description="Pupil Premium SER Rate",
        value_type="rate"
    ),
    # NOTE: PP allocation amounts are NOT imported - they are CALCULATED
    # from pupil counts × rates in the workbook
]


# =============================================================================
# UIFSM DATA MAPPING
# =============================================================================
"""
UIFSM (Universal Infant Free School Meals) files contain:
- Number of eligible pupils (KS1 taking UIFSM)
- Per-meal rate
- Total allocation
"""

UIFSM_MAPPINGS = [
    # Pupil Counts → Pupils tab
    PupilPremiumMapping(
        govuk_column="Number of pupils taking UIFSM (October)",
        govuk_patterns=["uifsm pupils oct", "october uifsm", "uifsm oct"],
        target_tab="Pupils",
        finance_code="PUPIL_UIFSM_OCT",
        description="Pupils taking UIFSM in October Census",
        value_type="count"
    ),
    PupilPremiumMapping(
        govuk_column="Number of pupils taking UIFSM (January)",
        govuk_patterns=["uifsm pupils jan", "january uifsm", "uifsm jan"],
        target_tab="Pupils",
        finance_code="PUPIL_UIFSM_JAN",
        description="Pupils taking UIFSM in January Census",
        value_type="count"
    ),

    # Rate → Statistics tab
    PupilPremiumMapping(
        govuk_column="UIFSM per pupil rate (final)",
        govuk_patterns=["uifsm rate final", "final rate"],
        target_tab="Statistics",
        finance_code="UIFSM_RATE_FIN",
        description="UIFSM Per Pupil Per Annum (Final)",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="UIFSM per pupil rate (provisional)",
        govuk_patterns=["uifsm rate prov", "provisional rate"],
        target_tab="Statistics",
        finance_code="UIFSM_RATE_PRO",
        description="UIFSM Per Pupil Per Annum(Provisional)",
        value_type="rate"
    ),
    # NOTE: UIFSM allocation amounts are NOT imported - they are CALCULATED
]


# =============================================================================
# DFC (DEVOLVED FORMULA CAPITAL) MAPPING
# =============================================================================
"""
DFC files contain rates only - allocations are CALCULATED in workbook.
"""

DFC_MAPPINGS = [
    # Rates → Statistics tab
    PupilPremiumMapping(
        govuk_column="DFC core amount",
        govuk_patterns=["dfc core", "dfc lump"],
        target_tab="Statistics",
        finance_code="DFC_CORE",
        description="DFC Core",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="DFC per pupil primary",
        govuk_patterns=["dfc primary", "dfc pri pupil"],
        target_tab="Statistics",
        finance_code="DFC_PUPIL_PRI",
        description="DFC Primary Pupil",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="DFC per pupil secondary",
        govuk_patterns=["dfc secondary", "dfc sec pupil"],
        target_tab="Statistics",
        finance_code="DFC_PUPIL_SEC",
        description="DFC Secondary Pupil",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="DFC per pupil post-16",
        govuk_patterns=["dfc post 16", "dfc post16"],
        target_tab="Statistics",
        finance_code="DFC_PUPIL_POST16",
        description="DFC Post16 Pupil",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="DFC per pupil nursery",
        govuk_patterns=["dfc nursery", "dfc nur pupil"],
        target_tab="Statistics",
        finance_code="DFC_PUPIL_NUR",
        description="DFC Nursery Pupil",
        value_type="rate"
    ),
    # NOTE: DFC allocation amounts are NOT imported - they are CALCULATED
]


# =============================================================================
# PE AND SPORT PREMIUM MAPPING
# =============================================================================

PE_SPORT_MAPPINGS = [
    # Rates → Statistics tab
    PupilPremiumMapping(
        govuk_column="PE grant core",
        govuk_patterns=["pe core", "pe lump", "sport core"],
        target_tab="Statistics",
        finance_code="PEG_CORE",
        description="PE Grant Core Rate",
        value_type="rate"
    ),
    PupilPremiumMapping(
        govuk_column="PE grant per pupil",
        govuk_patterns=["pe per pupil", "pe pupil rate"],
        target_tab="Statistics",
        finance_code="PEG_PUPIL",
        description="PE Grant Per Pupil Rate",
        value_type="rate"
    ),
    # NOTE: PE allocation amounts are NOT imported - they are CALCULATED
]


# =============================================================================
# ALL MAPPINGS COMBINED
# =============================================================================

ALL_WORKBOOK_MAPPINGS = (
    PUPIL_PREMIUM_MAPPINGS +
    UIFSM_MAPPINGS +
    DFC_MAPPINGS +
    PE_SPORT_MAPPINGS
)


def find_workbook_mapping(column_name: str) -> Optional[PupilPremiumMapping]:
    """Find mapping for a GOV.UK column name."""
    col_lower = column_name.lower().strip()

    for mapping in ALL_WORKBOOK_MAPPINGS:
        if mapping.govuk_column.lower() == col_lower:
            return mapping
        for pattern in mapping.govuk_patterns:
            if pattern.lower() in col_lower:
                return mapping

    return None


def get_mappings_by_tab(tab_name: str) -> List[PupilPremiumMapping]:
    """Get all mappings for a specific workbook tab."""
    return [m for m in ALL_WORKBOOK_MAPPINGS if m.target_tab == tab_name]


def get_mappings_by_value_type(value_type: str) -> List[PupilPremiumMapping]:
    """Get mappings by value type (count, rate, amount)."""
    return [m for m in ALL_WORKBOOK_MAPPINGS if m.value_type == value_type]


# =============================================================================
# WORKBOOK INSERTION LOGIC
# =============================================================================
"""
When inserting data into the workbook:

1. PUPIL COUNTS (value_type='count'):
   - Target: Pupils tab
   - Match: SchoolCode + FinanceCode
   - Column: YearValue
   - Sign: Positive (counts are positive)

2. RATES (value_type='rate'):
   - Target: Statistics tab
   - Match: FinanceCode (rates are usually the same for all schools)
   - Column: YearValue
   - Sign: Positive (rates are positive)
   - Note: Some rates may be per-school (e.g., LA-specific)

3. AMOUNTS (value_type='amount'):
   - Target: Funding tab
   - Match: SchoolCode + Description
   - Column: YearValue
   - Sign: NEGATIVE (income values are credits)

IMPORTANT: Income tab values are CALCULATED automatically using calculators.
Do NOT directly insert allocation amounts into Income - let the calculator
compute them from Pupils × Rates.
"""


@dataclass
class WorkbookInsertInstruction:
    """Instructions for inserting a value into the workbook."""
    tab: str                    # Target sheet name
    school_code: str            # School code (or 'ALL' for rates)
    finance_code: str           # FinanceCode to match
    description: str            # Description to match (backup)
    value: float                # Value to insert
    value_type: str             # 'count', 'rate', 'amount'
    make_negative: bool         # True for income/allocation amounts
    source: str                 # Source file/column for audit


def create_insert_instructions(
    school_code: str,
    govuk_column: str,
    value: float,
    source_file: str
) -> Optional[WorkbookInsertInstruction]:
    """
    Create workbook insert instruction from GOV.UK data.

    Args:
        school_code: 3-letter school code (from URN lookup)
        govuk_column: Column name from GOV.UK file
        value: The value to insert
        source_file: Name of source file for audit

    Returns:
        WorkbookInsertInstruction or None if no mapping
    """
    mapping = find_workbook_mapping(govuk_column)

    if not mapping:
        return None

    # Amounts should be negative (income)
    make_negative = mapping.value_type == 'amount'

    # For rates, use 'DEFAULT' school code (applies to all)
    effective_school_code = school_code
    if mapping.value_type == 'rate':
        effective_school_code = 'DEFAULT'

    return WorkbookInsertInstruction(
        tab=mapping.target_tab,
        school_code=effective_school_code,
        finance_code=mapping.finance_code,
        description=mapping.description,
        value=value,
        value_type=mapping.value_type,
        make_negative=make_negative,
        source=f"{source_file}:{govuk_column}"
    )
