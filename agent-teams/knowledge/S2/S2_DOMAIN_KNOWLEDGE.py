"""
S2 Domain Knowledge - Staff & Payroll
======================================
This file contains all the domain knowledge required for the S2 (Staff Team) agent
to correctly process and transform staff data into IMP Planner format.

CRITICAL: The import files use "Combined" format fields that must be parsed.
Example: "0000003: Hamilton Lee" -> Code: "0000003", Title: "Hamilton Lee"

This knowledge base includes:
1. Combined field parsing rules
2. Pay scale definitions and hierarchy
3. Staff role group to finance code mappings
4. Equated week patterns and assignment rules
5. Pension schemes
6. Contract types
7. Fund codes
8. Validation rules
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re


# =============================================================================
# SECTION 1: COMBINED FIELD PARSING
# =============================================================================

def parse_combined_field(value: str) -> Tuple[str, str]:
    """
    Parse a combined field in format "CODE: Title" or "CODE: Title (EXTRA)"

    Examples:
        "0000003: Hamilton Lee" -> ("0000003", "Hamilton Lee")
        "CAT_AST: General Kitchen Staff" -> ("CAT_AST", "General Kitchen Staff")
        "2700: Catering - Salaries (COSTCTR: Cost Centres)" -> ("2700", "Catering - Salaries")
        "NJC: NJC Scale" -> ("NJC", "NJC Scale")

    Returns:
        Tuple of (code, title)
    """
    if not value or str(value) == 'nan':
        return ('', '')

    value = str(value).strip()

    if ':' not in value:
        return (value, value)

    # Split on first colon only
    parts = value.split(':', 1)
    code = parts[0].strip()
    title = parts[1].strip() if len(parts) > 1 else ''

    # Remove parenthetical suffix if present (e.g., "(COSTCTR: Cost Centres)")
    if '(' in title:
        title = title.split('(')[0].strip()

    return (code, title)


def extract_finance_code(combined_value: str) -> str:
    """
    Extract just the finance code from a combined finance code field.

    Example:
        "2700: Catering - Salaries (COSTCTR: Cost Centres)" -> "2700"
    """
    code, _ = parse_combined_field(combined_value)
    return code


# =============================================================================
# SECTION 2: PAY SCALES
# =============================================================================

# Complete pay scale definitions from DEM003 - Pay Scales_ Master Scenario.xlsx
PAY_SCALES = {
    "APPRENTICE": {
        "title": "Apprentice",
        "type": "apprentice",
        "increment_date": "2019-04-01",
        "increase_date": "2019-04-01",
        "teaching": False,
    },
    "NJC": {
        "title": "NJC Scale",
        "type": "njc",
        "increment_date": "2021-04-01",
        "increase_date": "2021-04-01",
        "teaching": False,
        "description": "National Joint Council pay scale for support staff",
    },
    "NJC_SM1": {"title": "NJC Scale SMTest 1", "type": "njc", "teaching": False},
    "NJC_SM2": {"title": "NJC Scale SMTest 2", "type": "njc", "teaching": False},
    "NJC_SM3": {"title": "NJC Scale SMTest 3", "type": "njc", "teaching": False},
    "NJC_SM4": {"title": "NJC Scale SMTest 4", "type": "njc", "teaching": False},
    "NJC_SM5": {"title": "NJC Scale SMTest 5", "type": "njc", "teaching": False},
    "TEACH_MAIN_EW": {
        "title": "Teachers Main England & Wales",
        "type": "teacher_main",
        "increment_date": "2019-09-01",
        "increase_date": "2019-09-01",
        "teaching": True,
        "grades": ["M1", "M2", "M3", "M4", "M5", "M6"],
    },
    "TEACH_UPS_EW": {
        "title": "Teachers UPS England & Wales",
        "type": "teacher_ups",
        "increment_date": "2019-09-01",
        "increase_date": "2019-09-01",
        "teaching": True,
        "grades": ["U1", "U2", "U3"],
    },
    "TEACH_UQ_EW": {
        "title": "Teacher Unqualified",
        "type": "teacher_unqualified",
        "increment_date": "2019-09-01",
        "increase_date": "2019-09-01",
        "teaching": True,
    },
    "TEACH_LEADERSHIP_EW": {
        "title": "Teacher Leadership Group",
        "type": "leadership",
        "increment_date": "2019-09-01",
        "increase_date": "2019-09-01",
        "teaching": True,
        "grades": [f"L{i:02d}" for i in range(1, 44)],  # L01 to L43
    },
    "TEACH_LP_EW": {
        "title": "Teacher Lead Practitioner England & Wales",
        "type": "lead_practitioner",
        "teaching": True,
    },
    "TEACH_SEN": {
        "title": "Teacher SEN Allowance",
        "type": "allowance",
        "teaching": True,
    },
    "TEACH_TLR": {
        "title": "Teacher TLR",
        "type": "allowance",
        "teaching": True,
    },
    "TEACH_TLRLS": {
        "title": "Teacher TLR Local",
        "type": "allowance",
        "teaching": True,
    },
    "SPOT": {
        "title": "Spot Salary",
        "type": "spot",
        "teaching": False,
        "description": "Fixed spot salary, no scale progression",
    },
    "LOCATION_PAYSCALE": {"title": "Location Specific", "type": "location", "teaching": False},
    "IC": {"title": "Import Change Test", "type": "test", "teaching": False},
    "IMPORTTEST": {"title": "Importtest", "type": "test", "teaching": False},
    "NEW": {"title": "New", "type": "custom", "teaching": False},
    "TEST": {"title": "test", "type": "test", "teaching": False},
    "JJ": {"title": "jj", "type": "test", "teaching": False},
    "Z_PR": {"title": "Test PR", "type": "test", "teaching": False},
}

# Standard teacher pay scale points (England & Wales 2024-25)
TEACHER_PAY_POINTS_2024_25 = {
    "MAIN": {
        "M1": 31650, "M2": 33483, "M3": 35674, "M4": 37895, "M5": 40377, "M6": 43607,
    },
    "UPS": {
        "U1": 45646, "U2": 47340, "U3": 49084,
    },
    "LEADERSHIP": {
        "L1": 47185, "L2": 48389, "L3": 49618, "L4": 50872, "L5": 52151,
        "L6": 53380, "L7": 54816, "L8": 55965, "L9": 57252, "L10": 58539,
        "L11": 60019, "L12": 61493, "L13": 62821, "L14": 64414, "L15": 66064,
        "L16": 67667, "L17": 69426, "L18": 71194, "L19": 72744, "L20": 74609,
        "L21": 76530, "L22": 78262, "L23": 80165, "L24": 82108, "L25": 84105,
        "L26": 86157, "L27": 88260, "L28": 90370, "L29": 92556, "L30": 94797,
        "L31": 97076, "L32": 99425, "L33": 101795, "L34": 104217, "L35": 106700,
        "L36": 109214, "L37": 111782, "L38": 114420, "L39": 117100, "L40": 119863,
        "L41": 122673, "L42": 125533, "L43": 128443,
    },
    "UNQUALIFIED": {
        "UQ1": 22637, "UQ2": 24781, "UQ3": 26878, "UQ4": 28969,
        "UQ5": 31077, "UQ6": 33455,
    },
}


# =============================================================================
# SECTION 3: STAFF ROLE GROUPS WITH FINANCE CODE MAPPINGS
# =============================================================================

# Complete role group definitions from DEM003 - Staff Role Groups_ Master Scenario.xlsx
# Each role group maps to specific finance codes for different cost types
STAFF_ROLE_GROUPS = {
    "CAT_GENERAL": {
        "title": "Catering Staff - General",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2700",
            "leave_rebate": "2700",
            "employers_ni": "2705",
            "pension": "2710",
            "minimum_wage_topup": "MINWAGE",
            "living_wage_topup": "LIVWAGE",
            "opt_out_pension": "PENS",
            "other_salary_costs": "2700",
            "adjustments": "2700",
            "allowances": "2700",
        },
        "description": "Catering - Salaries",
    },
    "PREM_CLEAN": {
        "title": "Premises Staff - Cleaning",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2320",
            "leave_rebate": "2320",
            "employers_ni": "2325",
            "pension": "2330",
            "minimum_wage_topup": "MINWAGE",
            "living_wage_topup": "LIVWAGE",
            "opt_out_pension": "PENS",
            "other_salary_costs": "2320",
        },
        "description": "Cleaning staff - Salaries",
    },
    "PREM_GENERAL": {
        "title": "Premises Staff - General Staff",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2300",
            "leave_rebate": "2300",
            "employers_ni": "2305",
            "pension": "2310",
            "minimum_wage_topup": "MINWAGE",
            "living_wage_topup": "LIVWAGE",
            "opt_out_pension": "PENS",
            "other_salary_costs": "2300",
        },
        "description": "Premises Staff - Salaries",
    },
    "SUP_BREAK": {
        "title": "Support Staff - Breakfast Club",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2400",
            "leave_rebate": "2400",
            "employers_ni": "2405",
            "pension": "2410",
        },
        "description": "Breakfast Club - Salaries",
    },
    "SUP_COVER": {
        "title": "Support Staff - Cover Supervisor",
        "teaching": True,  # Note: Cover supervisors count as teaching for some purposes
        "finance_codes": {
            "gross_salary": "2720",
            "leave_rebate": "2720",
            "employers_ni": "2725",
            "pension": "2730",
        },
        "description": "Cover Assistants - Salaries",
    },
    "SUP_FINAD": {
        "title": "Support Staff - Finance & Admin",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2630",
            "leave_rebate": "2630",
            "employers_ni": "2635",
            "pension": "2640",
        },
        "description": "Finance & Admin - Salaries",
    },
    "SUP_GENERAL": {
        "title": "Support Staff - General Staff",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2200",
            "leave_rebate": "2200",
            "employers_ni": "2205",
            "pension": "2210",
        },
        "description": "Support Staff - Salaries",
    },
    "SUP_HLTA": {
        "title": "Support Staff - HLTA",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2250",
            "leave_rebate": "2250",
            "employers_ni": "2255",
            "pension": "2260",
        },
        "description": "HLTA Salaries",
    },
    "SUP_MIDDAY": {
        "title": "Support Staff - Midday Supervisor",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2820",
            "leave_rebate": "2820",
            "employers_ni": "2825",
            "pension": "2830",
        },
        "description": "Midday Supervisor - Salaries",
    },
    "SUP_NURSERY": {
        "title": "Support Staff - Nursery",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2500",
            "leave_rebate": "2500",
            "employers_ni": "2505",
            "pension": "2510",
        },
        "description": "Nursery/Playgroup Staff - Salaries",
    },
    "SUP_PASTORAL": {
        "title": "Support Staff - Pastoral",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2780",
            "leave_rebate": "2780",
            "employers_ni": "2785",
            "pension": "2790",
        },
        "description": "Pastoral Support Manager - Salaries",
    },
    "SUP_SWIM": {
        "title": "Supply Staff - Swimming Staff",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2600",
            "leave_rebate": "2600",
            "employers_ni": "2605",
            "pension": "2610",
        },
        "description": "Swimming/Sports Staff - Salaries",
    },
    "SUP_TECH": {
        "title": "Supply Staff - Technicians",
        "teaching": False,
        "finance_codes": {
            "gross_salary": "2280",
            "leave_rebate": "2280",
            "employers_ni": "2285",
            "pension": "2290",
        },
        "description": "Technicians - Salaries",
    },
    "TEACH": {
        "title": "Teachers",
        "teaching": True,
        "finance_codes": {
            "gross_salary": "2000",
            "leave_rebate": "2000",
            "employers_ni": "2005",
            "pension": "2010",
        },
        "description": "Teachers - Salaries/Allowances",
    },
    "TEACH_SUPPLY": {
        "title": "Teachers - Supply Staff",
        "teaching": True,
        "finance_codes": {
            "gross_salary": "2760",
            "leave_rebate": "2760",
            "employers_ni": "2765",
            "pension": "2770",
        },
        "description": "School Supply Staff - Salaries",
    },
    "TEACH_TLR": {
        "title": "Teachers - TLR",
        "teaching": True,
        "finance_codes": {
            "gross_salary": "2000",
            "leave_rebate": "2000",
            "employers_ni": "2005",
            "pension": "2010",
        },
        "description": "Teachers - Salaries/Allowances (with TLR)",
    },
}


# =============================================================================
# SECTION 4: EQUATED WEEK PATTERNS
# =============================================================================

# Equated week patterns from DEM003 - Equated Week Patterns_ Master Scenario.xlsx
EQUATED_WEEK_PATTERNS = {
    "39WEEKSWORKED": {
        "title": "39 weeks worked",
        "full_time_weeks": 52.143,
        "description": "Standard teacher term-time pattern",
        "typical_roles": ["teachers"],
    },
    "MONTHLYADJUSTMENT": {
        "title": "Monthlyadjustment",
        "full_time_weeks": 3.2439,
        "description": "Monthly adjustment pattern",
        "typical_roles": ["adjustments"],
    },
    "SUPALLYEAR": {
        "title": "Support Staff All Year",
        "full_time_weeks": 52.14,
        "description": "Support staff working all year round",
        "typical_roles": ["support", "admin", "premises"],
    },
    "SUPTTO": {
        "title": "Sup TTO",
        "full_time_weeks": 52.14,
        "description": "Support staff term-time only",
        "typical_roles": ["support", "teaching_assistants"],
    },
    "SUPTTO+1": {
        "title": "Sup TTO +1 44.45/45.44",
        "full_time_weeks": 52.14,
        "description": "Support TTO plus 1 additional day",
        "typical_roles": ["support"],
    },
    "SUPTTO+2": {
        "title": "Support TTO Plus 2",
        "full_time_weeks": 52.14,
        "description": "Support TTO plus 2 additional days",
        "typical_roles": ["support"],
    },
    "TEA_ALLYEAR": {
        "title": "Teaching Staff All Year",
        "full_time_weeks": 52.14,
        "description": "Teaching staff working all year (rare)",
        "typical_roles": ["teachers", "leadership"],
    },
}


def get_equated_week_pattern(role_group: str, is_all_year: bool = False) -> str:
    """
    Determine the appropriate equated week pattern for a role.

    Args:
        role_group: The staff role group code
        is_all_year: Whether the contract is all-year

    Returns:
        The equated week pattern code
    """
    group_info = STAFF_ROLE_GROUPS.get(role_group, {})
    is_teaching = group_info.get("teaching", False)

    if is_teaching:
        return "TEA_ALLYEAR" if is_all_year else "39WEEKSWORKED"
    else:
        return "SUPALLYEAR" if is_all_year else "SUPTTO"


# =============================================================================
# SECTION 5: PENSION SCHEMES
# =============================================================================

PENSION_SCHEMES = {
    "0%": {
        "title": "No Pension",
        "contribution_rate": 0.0,
        "description": "Opted out of pension",
    },
    "TPS": {
        "title": "Teachers Pensions Scheme",
        "contribution_rate": 0.236,  # 23.6% employer contribution
        "description": "Teacher pension scheme - mandatory for teachers",
        "for_teaching": True,
    },
    "LGPS_IMP": {
        "title": "LGPS Imp",
        "contribution_rate": 0.20,  # Varies by band
        "description": "Local Government Pension Scheme",
        "for_teaching": False,
    },
}


def get_default_pension(is_teaching: bool, opted_out: bool = False) -> str:
    """
    Get the default pension scheme for a role type.

    Args:
        is_teaching: Whether this is a teaching role
        opted_out: Whether the staff member has opted out

    Returns:
        Pension scheme code
    """
    if opted_out:
        return "0%"
    return "TPS" if is_teaching else "LGPS_IMP"


# =============================================================================
# SECTION 6: CONTRACT TYPES
# =============================================================================

CONTRACT_TYPES = {
    "PERM": {
        "title": "Permanent",
        "description": "Permanent contract with no end date",
    },
    "FXT": {
        "title": "Fixed Term",
        "description": "Fixed term contract with specified end date",
    },
    "MAT": {
        "title": "Maternity Cover",
        "description": "Temporary cover for maternity leave",
    },
    "ZZZ": {
        "title": "Not Selected",
        "description": "Contract type not yet specified",
    },
}


# =============================================================================
# SECTION 7: FUND CODES
# =============================================================================

FUND_CODES = {
    "GAG": {
        "title": "GAG Fund",
        "description": "General Annual Grant - main school funding",
    },
    "PP": {
        "title": "Pupil Premium",
        "description": "Pupil Premium funding",
    },
    "PE": {
        "title": "PE & Sports Premium",
        "description": "PE and Sports Premium funding",
    },
    "UIFSM": {
        "title": "Universal Infant Free School Meals",
        "description": "UIFSM funding",
    },
    "SCA": {
        "title": "School Condition Allocation",
        "description": "Capital funding for building condition",
    },
    "DFC": {
        "title": "Devolved Formula Capital",
        "description": "Capital funding for equipment and buildings",
    },
}


def get_default_fund_code() -> str:
    """Get the default fund code for contracts."""
    return "GAG"


# =============================================================================
# SECTION 8: ALLOWANCE TYPES
# =============================================================================

ALLOWANCE_TYPES = {
    "TLR1": {
        "title": "TLR1",
        "description": "Teaching and Learning Responsibility 1",
        "min_value": 9272,
        "max_value": 15690,
    },
    "TLR2": {
        "title": "TLR2",
        "description": "Teaching and Learning Responsibility 2",
        "min_value": 3214,
        "max_value": 7847,
    },
    "TLR3": {
        "title": "TLR3",
        "description": "Teaching and Learning Responsibility 3 (fixed term)",
        "min_value": 639,
        "max_value": 3169,
    },
    "SEN1": {
        "title": "SEN Allowance 1",
        "description": "Special Educational Needs Allowance (minimum)",
        "min_value": 2539,
        "max_value": 2539,
    },
    "SEN2": {
        "title": "SEN Allowance 2",
        "description": "Special Educational Needs Allowance (maximum)",
        "min_value": 5009,
        "max_value": 5009,
    },
}


# =============================================================================
# SECTION 9: COLUMN MAPPING FOR IMPORT FILES
# =============================================================================

# Maps import file column names to standardized output names
IMPORT_COLUMN_MAPPINGS = {
    "staff_members": {
        "Code": "StaffMemberCode",
        "Last Name": "LastName",
        "First Name": "FirstName",
        "Pension Opted Out": "PensionOptOut",
        "Service Start Date": "ServiceStartDate",
        "Service End Date": "ServiceEndDate",
        "Date of Birth (Required for Under 25s/Over 65s)": "DateOfBirth",
        "Apprenticeship": "Apprenticeship",
        "Casual": "Casual",
        "Available To All Schools": "AvailableToAllSchools",
        "Available to Schools": "SchoolCodes",
        "Gender": "GenderCode",
    },
    "contracts": {
        "School Code": "SchoolCode",
        "Staff Member Combined": "StaffMemberCode",  # Needs parsing
        "Reference": "Reference",
        "Date From": "DateFrom",
        "Date To": "DateTo",
        "Staff Role Combined": "StaffRoleCode",  # Needs parsing
        "Contract Type Combined": "ContractTypeCode",  # Needs parsing
        "Pay Scale Combined": "PayScaleCode",  # Needs parsing
        "Pay Scale Grade Combined": "PayScaleGradeCode",  # Needs parsing
        "Pay Scale Point Combined": "PayScalePointCode",  # Needs parsing
        "Pension Combined": "PensionCode",  # Needs parsing
        "Equated Week Pattern Combined": "EquatedWeekPatternCode",  # Needs parsing
        "Department Combined": "DepartmentCode",  # Needs parsing
        "Fund Combined": "FundCode",  # Needs parsing
        "Weekly FTE": "WeeklyFteOrHpw",
        "Annual FTE": "AnnualFTE",
        "No Increment": "NoIncrement",
        "Notes": "Notes",
    },
    "pay_scales": {
        "Code": "PayScaleCode",
        "Title": "PayScaleTitle",
        "Increment at Service Start Date": "ServiceIncrementDateEnabled",
        "Increment Date": "IncrementDate",
        "Increase Date": "IncreaseDate",
        "Default Increase Percentage": "IncreasePercentage",
        "Available To All Schools": "AvailableToAllSchools",
        "Available to Schools": "SchoolCodes",
        "Exclude National Insurance": "ExcludeNationalInsurance",
        "Exclude Pension": "ExcludePension",
    },
    "staff_role_groups": {
        "Code": "StaffRoleGroupCode",
        "Title": "Title",
        "Gross Salary Code": "GrossSalaryFinanceCode",  # Needs parsing
        "Leave Rebate Code": "LeaveRebateFinanceCode",  # Needs parsing
        "Employers NI Code": "EmployersNiFinanceCode",  # Needs parsing
        "Pension Code": "PensionFinanceCode",  # Needs parsing
        "Teaching Role Group": "TeachingRoleGroup",
        "Increment Count": "IncrementCount",
    },
}

# Columns that contain combined "CODE: Title" format and need parsing
COMBINED_COLUMNS = [
    "Staff Member Combined",
    "Staff Role Combined",
    "Contract Type Combined",
    "Pay Scale Combined",
    "Pay Scale Grade Combined",
    "Pay Scale Point Combined",
    "Pension Combined",
    "Equated Week Pattern Combined",
    "Department Combined",
    "Fund Combined",
    "Gross Salary Code",
    "Leave Rebate Code",
    "Employers NI Code",
    "Pension Code",
    "Opt Out Pension Code",
    "Other Salary Costs Code",
    "Adjustments Code",
    "Allowances Code",
]


# =============================================================================
# SECTION 10: VALIDATION RULES
# =============================================================================

VALIDATION_RULES = {
    "staff_member_code": {
        "pattern": r"^[A-Za-z0-9_-]+$",
        "max_length": 20,
        "required": True,
    },
    "pay_scale_code": {
        "pattern": r"^[A-Z0-9_]+$",
        "max_length": 30,
        "required": True,
    },
    "finance_code": {
        "pattern": r"^[A-Z0-9_]+$",
        "min_length": 4,
        "max_length": 10,
    },
    "weekly_fte": {
        "min_value": 0.0,
        "max_value": 1.5,  # Can be > 1.0 for overtime
    },
    "annual_salary": {
        "min_value": 10000,
        "max_value": 250000,
    },
}


def validate_staff_member_code(code: str) -> Tuple[bool, str]:
    """Validate a staff member code."""
    if not code:
        return False, "Staff member code is required"
    if len(code) > 20:
        return False, f"Staff member code too long: {len(code)} > 20"
    if not re.match(r"^[A-Za-z0-9_-]+$", code):
        return False, f"Invalid characters in staff member code: {code}"
    return True, ""


def validate_weekly_fte(fte: float) -> Tuple[bool, str]:
    """Validate weekly FTE value."""
    if fte < 0:
        return False, f"Weekly FTE cannot be negative: {fte}"
    if fte > 1.5:
        return False, f"Weekly FTE unusually high: {fte}"
    return True, ""


# =============================================================================
# SECTION 11: HELPER FUNCTIONS
# =============================================================================

def is_teaching_role(role_group: str) -> bool:
    """Check if a role group is a teaching role."""
    group = STAFF_ROLE_GROUPS.get(role_group, {})
    return group.get("teaching", False)


def get_finance_codes_for_role_group(role_group: str) -> Dict[str, str]:
    """Get all finance codes for a role group."""
    group = STAFF_ROLE_GROUPS.get(role_group, {})
    return group.get("finance_codes", {})


def get_salary_finance_code(role_group: str) -> str:
    """Get the salary finance code for a role group."""
    codes = get_finance_codes_for_role_group(role_group)
    return codes.get("gross_salary", "")


def get_ni_finance_code(role_group: str) -> str:
    """Get the NI finance code for a role group."""
    codes = get_finance_codes_for_role_group(role_group)
    return codes.get("employers_ni", "")


def get_pension_finance_code(role_group: str) -> str:
    """Get the pension finance code for a role group."""
    codes = get_finance_codes_for_role_group(role_group)
    return codes.get("pension", "")


def map_role_title_to_group(title: str) -> Optional[str]:
    """
    Attempt to map a role title to a role group code.

    Args:
        title: The role title (e.g., "Kitchen Assistant", "Teacher")

    Returns:
        The role group code if found, None otherwise
    """
    title_lower = title.lower() if title else ""

    # Teaching roles
    if any(t in title_lower for t in ["teacher", "head", "deputy", "assistant head"]):
        return "TEACH"
    if "supply" in title_lower and "teach" in title_lower:
        return "TEACH_SUPPLY"
    if "tlr" in title_lower:
        return "TEACH_TLR"

    # Support roles
    if any(t in title_lower for t in ["hlta", "higher level"]):
        return "SUP_HLTA"
    if any(t in title_lower for t in ["teaching assistant", " ta ", "classroom assistant"]):
        return "SUP_GENERAL"
    if any(t in title_lower for t in ["admin", "office", "secretary", "receptionist"]):
        return "SUP_FINAD"
    if any(t in title_lower for t in ["midday", "lunchtime", "msa"]):
        return "SUP_MIDDAY"
    if any(t in title_lower for t in ["breakfast club"]):
        return "SUP_BREAK"
    if any(t in title_lower for t in ["nursery", "eyfs", "early years"]):
        return "SUP_NURSERY"
    if any(t in title_lower for t in ["pastoral", "welfare", "safeguarding"]):
        return "SUP_PASTORAL"
    if any(t in title_lower for t in ["cover supervisor"]):
        return "SUP_COVER"
    if any(t in title_lower for t in ["technician", "ict", "it support"]):
        return "SUP_TECH"

    # Premises roles
    if any(t in title_lower for t in ["caretaker", "site", "premises", "maintenance"]):
        return "PREM_GENERAL"
    if any(t in title_lower for t in ["cleaner", "cleaning"]):
        return "PREM_CLEAN"

    # Catering roles
    if any(t in title_lower for t in ["cook", "chef", "kitchen", "catering"]):
        return "CAT_GENERAL"

    return None


# =============================================================================
# SECTION 12: DATA TRANSFORMATION FUNCTIONS
# =============================================================================

def transform_contract_row(row: dict) -> dict:
    """
    Transform a contract row from import format to output format.
    Handles combined field parsing and default value assignment.
    """
    transformed = {}

    # Direct mappings
    transformed["SchoolCode"] = row.get("School Code", "")
    transformed["Reference"] = row.get("Reference", "")
    transformed["DateFrom"] = row.get("Date From", "")
    transformed["DateTo"] = row.get("Date To", "")
    transformed["WeeklyFteOrHpw"] = row.get("Weekly FTE", 0)
    transformed["NoIncrement"] = row.get("No Increment", False)
    transformed["Notes"] = row.get("Notes", "")

    # Parse combined fields
    staff_code, _ = parse_combined_field(row.get("Staff Member Combined", ""))
    transformed["StaffMemberCode"] = staff_code

    role_code, _ = parse_combined_field(row.get("Staff Role Combined", ""))
    transformed["StaffRoleCode"] = role_code

    contract_type, _ = parse_combined_field(row.get("Contract Type Combined", ""))
    transformed["ContractTypeCode"] = contract_type or "PERM"

    pay_scale, _ = parse_combined_field(row.get("Pay Scale Combined", ""))
    transformed["PayScaleCode"] = pay_scale

    pay_grade, _ = parse_combined_field(row.get("Pay Scale Grade Combined", ""))
    transformed["PayScaleGradeCode"] = pay_grade

    pay_point, _ = parse_combined_field(row.get("Pay Scale Point Combined", ""))
    transformed["PayScalePointCode"] = pay_point

    pension, _ = parse_combined_field(row.get("Pension Combined", ""))
    transformed["PensionCode"] = pension

    eqw, _ = parse_combined_field(row.get("Equated Week Pattern Combined", ""))
    transformed["EquatedWeekPatternCode"] = eqw

    dept, _ = parse_combined_field(row.get("Department Combined", ""))
    transformed["DepartmentCode"] = dept

    fund, _ = parse_combined_field(row.get("Fund Combined", ""))
    transformed["FundCode"] = fund or "GAG"  # Default to GAG

    return transformed


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Parsing functions
    "parse_combined_field",
    "extract_finance_code",

    # Data dictionaries
    "PAY_SCALES",
    "TEACHER_PAY_POINTS_2024_25",
    "STAFF_ROLE_GROUPS",
    "EQUATED_WEEK_PATTERNS",
    "PENSION_SCHEMES",
    "CONTRACT_TYPES",
    "FUND_CODES",
    "ALLOWANCE_TYPES",
    "IMPORT_COLUMN_MAPPINGS",
    "COMBINED_COLUMNS",
    "VALIDATION_RULES",

    # Helper functions
    "get_equated_week_pattern",
    "get_default_pension",
    "get_default_fund_code",
    "is_teaching_role",
    "get_finance_codes_for_role_group",
    "get_salary_finance_code",
    "get_ni_finance_code",
    "get_pension_finance_code",
    "map_role_title_to_group",

    # Validation functions
    "validate_staff_member_code",
    "validate_weekly_fte",

    # Transformation functions
    "transform_contract_row",
]
