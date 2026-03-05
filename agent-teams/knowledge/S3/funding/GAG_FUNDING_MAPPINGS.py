"""
GAG Funding Mappings for S3 Budget Processing
==============================================
Defines how DfE GAG funding statement values map to IMP Planner format.

CRITICAL: Mapping uses SchoolCode + Description (NOT FinanceCode) because
finance codes vary between trusts, but DfE descriptions are consistent.

Reference: gag_funding_mapper.py
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


# =============================================================================
# FUNDING LINE MAPPINGS BY SCHOOL TYPE
# =============================================================================
"""
DfE funding statements have different line items depending on school type.
Each mapping defines:
- dfe_description: Text that appears in DfE statement
- imp_finance_code: Standard IMP Planner finance code
- imp_description: IMP Planner description
- category: Pre-16 or Post-16
"""

@dataclass
class FundingLineMapping:
    """Maps a DfE funding line to IMP format."""
    dfe_description: str
    imp_finance_code: str
    imp_description: str
    category: str  # "pre16" or "post16"


# -----------------------------------------------------------------------------
# PRIMARY SCHOOL MAPPINGS
# -----------------------------------------------------------------------------
PRIMARY_FUNDING_MAPPINGS = [
    FundingLineMapping(
        dfe_description="Basic entitlement",
        imp_finance_code="I1201",
        imp_description="GAG - Basic Entitlement (Primary AWPU)",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Deprivation",
        imp_finance_code="I1202",
        imp_description="GAG - Deprivation",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Looked-after children (LAC) and previously looked-after children",
        imp_finance_code="I1203",
        imp_description="GAG - LAC/PLAC",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="English as an additional language (EAL)",
        imp_finance_code="I1204",
        imp_description="GAG - EAL",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Mobility",
        imp_finance_code="I1205",
        imp_description="GAG - Mobility",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Prior attainment (low prior attainment)",
        imp_finance_code="I1206",
        imp_description="GAG - Prior Attainment",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Lump sum",
        imp_finance_code="I1207",
        imp_description="GAG - Lump Sum",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Sparsity",
        imp_finance_code="I1208",
        imp_description="GAG - Sparsity",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Split site",
        imp_finance_code="I1209",
        imp_description="GAG - Split Site",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Rates",
        imp_finance_code="I1210",
        imp_description="GAG - Rates",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="PFI funding",
        imp_finance_code="I1211",
        imp_description="GAG - PFI Funding",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Exceptional circumstances",
        imp_finance_code="I1212",
        imp_description="GAG - Exceptional Circumstances",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Minimum per pupil funding level",
        imp_finance_code="I1213",
        imp_description="GAG - Minimum Per Pupil",
        category="pre16"
    ),
]


# -----------------------------------------------------------------------------
# SECONDARY SCHOOL MAPPINGS
# -----------------------------------------------------------------------------
SECONDARY_FUNDING_MAPPINGS = [
    FundingLineMapping(
        dfe_description="Basic entitlement: Key Stage 3",
        imp_finance_code="I1221",
        imp_description="GAG - Basic Entitlement KS3",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Basic entitlement: Key Stage 4",
        imp_finance_code="I1222",
        imp_description="GAG - Basic Entitlement KS4",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Deprivation",
        imp_finance_code="I1202",
        imp_description="GAG - Deprivation",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Looked-after children (LAC) and previously looked-after children",
        imp_finance_code="I1203",
        imp_description="GAG - LAC/PLAC",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="English as an additional language (EAL)",
        imp_finance_code="I1204",
        imp_description="GAG - EAL",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Mobility",
        imp_finance_code="I1205",
        imp_description="GAG - Mobility",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Prior attainment (low prior attainment)",
        imp_finance_code="I1206",
        imp_description="GAG - Prior Attainment",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Lump sum",
        imp_finance_code="I1207",
        imp_description="GAG - Lump Sum",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Sparsity",
        imp_finance_code="I1208",
        imp_description="GAG - Sparsity",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Split site",
        imp_finance_code="I1209",
        imp_description="GAG - Split Site",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Rates",
        imp_finance_code="I1210",
        imp_description="GAG - Rates",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="PFI funding",
        imp_finance_code="I1211",
        imp_description="GAG - PFI Funding",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Exceptional circumstances",
        imp_finance_code="I1212",
        imp_description="GAG - Exceptional Circumstances",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Minimum per pupil funding level",
        imp_finance_code="I1213",
        imp_description="GAG - Minimum Per Pupil",
        category="pre16"
    ),
]


# -----------------------------------------------------------------------------
# ALL-THROUGH SCHOOL MAPPINGS
# -----------------------------------------------------------------------------
ALLTHROUGH_FUNDING_MAPPINGS = [
    FundingLineMapping(
        dfe_description="Basic entitlement: Primary",
        imp_finance_code="I1201",
        imp_description="GAG - Basic Entitlement Primary",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Basic entitlement: Key Stage 3",
        imp_finance_code="I1221",
        imp_description="GAG - Basic Entitlement KS3",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Basic entitlement: Key Stage 4",
        imp_finance_code="I1222",
        imp_description="GAG - Basic Entitlement KS4",
        category="pre16"
    ),
    # Plus all the shared lines (Deprivation, EAL, etc.)
    FundingLineMapping(
        dfe_description="Deprivation",
        imp_finance_code="I1202",
        imp_description="GAG - Deprivation",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Looked-after children (LAC) and previously looked-after children",
        imp_finance_code="I1203",
        imp_description="GAG - LAC/PLAC",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="English as an additional language (EAL)",
        imp_finance_code="I1204",
        imp_description="GAG - EAL",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Mobility",
        imp_finance_code="I1205",
        imp_description="GAG - Mobility",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Prior attainment (low prior attainment)",
        imp_finance_code="I1206",
        imp_description="GAG - Prior Attainment",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Lump sum",
        imp_finance_code="I1207",
        imp_description="GAG - Lump Sum",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Sparsity",
        imp_finance_code="I1208",
        imp_description="GAG - Sparsity",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Split site",
        imp_finance_code="I1209",
        imp_description="GAG - Split Site",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Rates",
        imp_finance_code="I1210",
        imp_description="GAG - Rates",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="PFI funding",
        imp_finance_code="I1211",
        imp_description="GAG - PFI Funding",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Exceptional circumstances",
        imp_finance_code="I1212",
        imp_description="GAG - Exceptional Circumstances",
        category="pre16"
    ),
    FundingLineMapping(
        dfe_description="Minimum per pupil funding level",
        imp_finance_code="I1213",
        imp_description="GAG - Minimum Per Pupil",
        category="pre16"
    ),
]


# -----------------------------------------------------------------------------
# POST-16 FUNDING MAPPINGS
# -----------------------------------------------------------------------------
POST16_FUNDING_MAPPINGS = [
    FundingLineMapping(
        dfe_description="Post-16 programme funding",
        imp_finance_code="I1301",
        imp_description="Post-16 Programme Funding",
        category="post16"
    ),
    FundingLineMapping(
        dfe_description="Post-16 student support",
        imp_finance_code="I1302",
        imp_description="Post-16 Student Support",
        category="post16"
    ),
    FundingLineMapping(
        dfe_description="Post-16 bursary funding",
        imp_finance_code="I1303",
        imp_description="Post-16 Bursary Funding",
        category="post16"
    ),
    FundingLineMapping(
        dfe_description="16-19 tuition fund",
        imp_finance_code="I1304",
        imp_description="16-19 Tuition Fund",
        category="post16"
    ),
    FundingLineMapping(
        dfe_description="Post-16 high needs place funding",
        imp_finance_code="I1305",
        imp_description="Post-16 High Needs Places",
        category="post16"
    ),
]


# =============================================================================
# SCHOOL TYPE DETECTION
# =============================================================================
"""
Detect school type from school name or URN patterns.
"""

def detect_school_type(school_name: str) -> str:
    """
    Detect school type from name.

    Returns: "primary", "secondary", "allthrough", or "unknown"
    """
    name_lower = school_name.lower()

    # All-through indicators
    allthrough_indicators = [
        "all-through", "all through", "allthrough",
        "3-18", "4-18", "3-16", "4-16",
        "free school",  # Many free schools are all-through
    ]
    for indicator in allthrough_indicators:
        if indicator in name_lower:
            return "allthrough"

    # Primary indicators
    primary_indicators = [
        "primary", "infant", "junior", "first school",
        "prep", "preparatory",
    ]
    for indicator in primary_indicators:
        if indicator in name_lower:
            return "primary"

    # Secondary indicators
    secondary_indicators = [
        "secondary", "high school", "academy", "college",
        "grammar", "comprehensive",
    ]
    for indicator in secondary_indicators:
        if indicator in name_lower:
            return "secondary"

    return "unknown"


def get_funding_mappings_for_school_type(school_type: str) -> List[FundingLineMapping]:
    """
    Get appropriate funding mappings for school type.

    Args:
        school_type: "primary", "secondary", "allthrough"

    Returns:
        List of FundingLineMapping objects
    """
    mappings = {
        "primary": PRIMARY_FUNDING_MAPPINGS,
        "secondary": SECONDARY_FUNDING_MAPPINGS,
        "allthrough": ALLTHROUGH_FUNDING_MAPPINGS,
    }
    return mappings.get(school_type, SECONDARY_FUNDING_MAPPINGS)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_mapping_by_description(
    description: str,
    school_type: str = "secondary"
) -> Optional[FundingLineMapping]:
    """
    Find the IMP mapping for a DfE description.

    Args:
        description: DfE funding line description
        school_type: Type of school

    Returns:
        FundingLineMapping or None if not found
    """
    mappings = get_funding_mappings_for_school_type(school_type)
    description_lower = description.lower().strip()

    for mapping in mappings:
        if mapping.dfe_description.lower() in description_lower:
            return mapping
        if description_lower in mapping.dfe_description.lower():
            return mapping

    # Also check Post-16 mappings
    for mapping in POST16_FUNDING_MAPPINGS:
        if mapping.dfe_description.lower() in description_lower:
            return mapping
        if description_lower in mapping.dfe_description.lower():
            return mapping

    return None


def get_all_finance_codes() -> Dict[str, str]:
    """
    Get all IMP finance codes and their descriptions.

    Returns:
        Dict mapping finance code to description
    """
    codes = {}

    all_mappings = (
        PRIMARY_FUNDING_MAPPINGS +
        SECONDARY_FUNDING_MAPPINGS +
        POST16_FUNDING_MAPPINGS
    )

    for mapping in all_mappings:
        codes[mapping.imp_finance_code] = mapping.imp_description

    return codes


# =============================================================================
# OUTPUT FORMAT
# =============================================================================
"""
GAG funding mapper outputs in two formats:

1. NEW CUSTOMER MODE - Excel output:
   - Funding_Tab_Values.xlsx
   - Columns: SchoolCode, Description, FinanceCode, Value
   - Used to populate template for first time

2. EXISTING CUSTOMER MODE - CSV output:
   - ScenarioYearValues_Updated.csv
   - Updates existing ScenarioYearValues with new funding values
   - Matches on SchoolCode + Description (NOT FinanceCode)

CRITICAL: Always use SchoolCode + Description for matching because
FinanceCode may vary between trusts. DfE descriptions are consistent.
"""

@dataclass
class FundingOutputRow:
    """Output row for funding values."""
    school_code: str
    description: str
    finance_code: str
    value: float
    category: str  # "pre16" or "post16"


def create_funding_output(
    school_code: str,
    dfe_description: str,
    value: float,
    school_type: str = "secondary"
) -> Optional[FundingOutputRow]:
    """
    Create a funding output row from DfE data.

    Args:
        school_code: IMP school code
        dfe_description: Description from DfE statement
        value: Funding value
        school_type: Type of school

    Returns:
        FundingOutputRow or None if mapping not found
    """
    mapping = find_mapping_by_description(dfe_description, school_type)

    if mapping:
        return FundingOutputRow(
            school_code=school_code,
            description=mapping.imp_description,
            finance_code=mapping.imp_finance_code,
            value=value,
            category=mapping.category
        )

    return None
