"""
National Grant Allocation Mappings for S3 Budget Processing
============================================================
Maps DfE national grant allocation data columns to IMP Planner Funding tab.

Data Sources:
- School Funding Statistics: https://explore-education-statistics.service.gov.uk/find-statistics/school-funding-statistics
- Pupil Premium Allocations: https://www.gov.uk/government/publications/pupil-premium-allocations-and-conditions-of-grant
- PE & Sport Premium: https://www.gov.uk/government/publications/pe-and-sport-premium-allocations
- Universal Infant Free School Meals: https://www.gov.uk/government/publications/universal-infant-free-school-meals

CRITICAL: Match schools by URN, then insert values into Funding tab rows
using SchoolCode + Description matching.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GrantColumnMapping:
    """Maps a DfE data column to IMP Funding tab."""
    dfe_column: str           # Column header in DfE data file
    dfe_column_patterns: List[str]  # Alternative patterns for column matching
    imp_finance_code: str     # IMP finance code (for reference)
    imp_description: str      # Description to match in Funding tab
    grant_type: str           # Category: PP, DFC, GAG, PEG, UIFSM, etc.
    is_negative: bool = True  # Income values should be negative


# =============================================================================
# PUPIL PREMIUM MAPPINGS
# =============================================================================
PUPIL_PREMIUM_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="Pupil premium allocation",
        dfe_column_patterns=["pupil premium", "pp allocation", "pp_allocation", "total pp"],
        imp_finance_code="PP_TOTAL",
        imp_description="Pupil Premium Total Allocation",
        grant_type="PP"
    ),
    GrantColumnMapping(
        dfe_column="Pupil premium - disadvantaged pupils",
        dfe_column_patterns=["pp disadvantaged", "fsm", "ever 6", "disadvantaged"],
        imp_finance_code="PP_DISAD",
        imp_description="Pupil Premium - Disadvantaged",
        grant_type="PP"
    ),
    GrantColumnMapping(
        dfe_column="Pupil premium - looked-after children",
        dfe_column_patterns=["pp lac", "looked after", "lac allocation"],
        imp_finance_code="PP_LAC",
        imp_description="Pupil Premium - LAC",
        grant_type="PP"
    ),
    GrantColumnMapping(
        dfe_column="Pupil premium - post LAC",
        dfe_column_patterns=["post lac", "previously lac", "plac"],
        imp_finance_code="PP_PLAC",
        imp_description="Pupil Premium - Post LAC",
        grant_type="PP"
    ),
    GrantColumnMapping(
        dfe_column="Pupil premium - service children",
        dfe_column_patterns=["service children", "service premium", "armed forces"],
        imp_finance_code="PP_SERVICE",
        imp_description="Pupil Premium - Service Children",
        grant_type="PP"
    ),
]


# =============================================================================
# DEVOLVED FORMULA CAPITAL (DFC) MAPPINGS
# =============================================================================
DFC_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="DFC allocation",
        dfe_column_patterns=["dfc", "devolved formula capital", "capital allocation"],
        imp_finance_code="DFC",
        imp_description="DFC Total Allocation",
        grant_type="DFC"
    ),
    GrantColumnMapping(
        dfe_column="DFC lump sum",
        dfe_column_patterns=["dfc lump", "dfc core", "capital lump"],
        imp_finance_code="DFC",
        imp_description="DFC Core Amount",
        grant_type="DFC"
    ),
    GrantColumnMapping(
        dfe_column="DFC per pupil",
        dfe_column_patterns=["dfc pupil", "dfc per pupil"],
        imp_finance_code="DFC",
        imp_description="DFC Per Pupil",
        grant_type="DFC"
    ),
]


# =============================================================================
# PE AND SPORT PREMIUM MAPPINGS
# =============================================================================
PE_SPORT_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="PE and sport premium allocation",
        dfe_column_patterns=["pe sport", "pe premium", "sport premium", "peg"],
        imp_finance_code="PEG",
        imp_description="PE and Sport Premium",
        grant_type="PEG"
    ),
    GrantColumnMapping(
        dfe_column="PE and sport premium lump sum",
        dfe_column_patterns=["pe lump", "sport lump", "peg core"],
        imp_finance_code="PEG",
        imp_description="PE Grant Core",
        grant_type="PEG"
    ),
    GrantColumnMapping(
        dfe_column="PE and sport premium per pupil",
        dfe_column_patterns=["pe per pupil", "sport per pupil"],
        imp_finance_code="PEG",
        imp_description="PE Grant Per Pupil",
        grant_type="PEG"
    ),
]


# =============================================================================
# UIFSM (Universal Infant Free School Meals) MAPPINGS
# =============================================================================
UIFSM_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="UIFSM allocation",
        dfe_column_patterns=["uifsm", "universal infant", "free school meals allocation"],
        imp_finance_code="UIFSM",
        imp_description="UIFSM Allocation",
        grant_type="UIFSM"
    ),
]


# =============================================================================
# TEACHERS PAY/PENSION GRANT MAPPINGS
# =============================================================================
TPG_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="Teachers' pay grant",
        dfe_column_patterns=["tpg", "teachers pay", "pay grant"],
        imp_finance_code="TPG",
        imp_description="Teachers Pay Grant",
        grant_type="TPG"
    ),
    GrantColumnMapping(
        dfe_column="Teachers' pension grant",
        dfe_column_patterns=["tpeg", "teachers pension", "pension grant"],
        imp_finance_code="TPEG",
        imp_description="Teachers Pension Employer Contribution Grant",
        grant_type="TPEG"
    ),
]


# =============================================================================
# RECOVERY PREMIUM MAPPINGS
# =============================================================================
RECOVERY_PREMIUM_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="Recovery premium allocation",
        dfe_column_patterns=["recovery premium", "recovery allocation"],
        imp_finance_code="RECOVERY",
        imp_description="Recovery Premium",
        grant_type="RECOVERY"
    ),
]


# =============================================================================
# HIGH NEEDS MAPPINGS
# =============================================================================
HIGH_NEEDS_MAPPINGS = [
    GrantColumnMapping(
        dfe_column="High needs place funding",
        dfe_column_patterns=["high needs", "hn place", "hnpf", "element 3"],
        imp_finance_code="HNPF",
        imp_description="High Needs Place Funding",
        grant_type="HNPF"
    ),
]


# =============================================================================
# ALL GRANT MAPPINGS COMBINED
# =============================================================================
ALL_GRANT_MAPPINGS = (
    PUPIL_PREMIUM_MAPPINGS +
    DFC_MAPPINGS +
    PE_SPORT_MAPPINGS +
    UIFSM_MAPPINGS +
    TPG_MAPPINGS +
    RECOVERY_PREMIUM_MAPPINGS +
    HIGH_NEEDS_MAPPINGS
)


def find_grant_mapping(column_name: str) -> Optional[GrantColumnMapping]:
    """
    Find matching grant mapping for a column name.

    Args:
        column_name: Column header from DfE data file

    Returns:
        GrantColumnMapping or None
    """
    col_lower = column_name.lower().strip()

    for mapping in ALL_GRANT_MAPPINGS:
        # Exact match
        if mapping.dfe_column.lower() == col_lower:
            return mapping

        # Pattern match
        for pattern in mapping.dfe_column_patterns:
            if pattern.lower() in col_lower:
                return mapping

    return None


def get_mappings_by_type(grant_type: str) -> List[GrantColumnMapping]:
    """Get all mappings for a grant type (PP, DFC, etc.)."""
    return [m for m in ALL_GRANT_MAPPINGS if m.grant_type == grant_type]


def get_all_grant_types() -> List[str]:
    """Get list of all grant types."""
    return list(set(m.grant_type for m in ALL_GRANT_MAPPINGS))


# =============================================================================
# URN TO SCHOOL CODE MATCHING
# =============================================================================
def create_urn_to_school_mapping(schools_df) -> Dict[str, str]:
    """
    Create URN to SchoolCode mapping from Schools sheet.

    Args:
        schools_df: DataFrame from Schools sheet (header row 1)

    Returns:
        Dict mapping URN (str) to SchoolCode (str)
    """
    mapping = {}

    # Find URN column
    urn_col = None
    for col in schools_df.columns:
        if 'urn' in str(col).lower() or 'uniquereference' in str(col).lower():
            urn_col = col
            break

    # Find SchoolCode column
    code_col = None
    for col in schools_df.columns:
        if col == 'SchoolCode' or 'schoolcode' in str(col).lower():
            code_col = col
            break

    if urn_col and code_col:
        for _, row in schools_df.iterrows():
            urn = str(row[urn_col]).strip()
            code = str(row[code_col]).strip()
            if urn and code and urn not in ['nan', '', '0']:
                mapping[urn] = code

    return mapping


@dataclass
class GrantAllocationResult:
    """Result of matching grant allocations to schools."""
    school_code: str
    urn: str
    grant_type: str
    description: str
    finance_code: str
    value: float
    source_column: str


def process_grant_allocations(
    allocations_df,
    urn_to_school: Dict[str, str]
) -> List[GrantAllocationResult]:
    """
    Process grant allocation data and match to schools.

    Args:
        allocations_df: DataFrame with grant allocations (must have URN column)
        urn_to_school: Dict mapping URN to SchoolCode

    Returns:
        List of GrantAllocationResult for schools in the workbook
    """
    results = []

    # Find URN column in allocations
    urn_col = None
    for col in allocations_df.columns:
        if 'urn' in str(col).lower():
            urn_col = col
            break

    if not urn_col:
        return results

    # Find grant columns
    grant_columns = {}
    for col in allocations_df.columns:
        mapping = find_grant_mapping(str(col))
        if mapping:
            grant_columns[col] = mapping

    # Process each row
    for _, row in allocations_df.iterrows():
        urn = str(row[urn_col]).strip()

        # Skip if not in our schools
        if urn not in urn_to_school:
            continue

        school_code = urn_to_school[urn]

        # Extract grant values
        for col, mapping in grant_columns.items():
            try:
                value = float(row[col])
                if value != 0:
                    # Make negative for income
                    if mapping.is_negative:
                        value = -abs(value)

                    results.append(GrantAllocationResult(
                        school_code=school_code,
                        urn=urn,
                        grant_type=mapping.grant_type,
                        description=mapping.imp_description,
                        finance_code=mapping.imp_finance_code,
                        value=value,
                        source_column=col
                    ))
            except (ValueError, TypeError):
                continue

    return results
