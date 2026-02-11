"""
Finished Workbook Patterns

Patterns extracted from COR004 finished workbooks.
These represent the exact formats and coding standards used in production builds.
"""

from typing import Dict, List, Any

# =============================================================================
# S2 PATTERNS - Staff Team
# =============================================================================

S2_PAY_SCALE_PATTERNS = {
    "teaching_scales": {
        "MAIN": {
            "code": "MAIN",
            "title": "Teachers Main",
            "increment_date": "2021-09-01",  # September for teaching
            "increase_percentage": 2,
            "includes_ups": True,  # M1-M6 then U1-U3 on same scale
        },
        "UQ": {
            "code": "UQ",
            "title": "Teachers Unqualified",
            "increment_date": "2021-09-01",
            "increase_percentage": 2,
            "points": ["UQ1", "UQ2", "UQ3", "UQ4", "UQ5", "UQ6"],
        },
        "LS": {
            "code": "LS",
            "title": "Leadership Group",
            "increment_date": "2021-09-01",
            "increase_percentage": 2,
            "points_range": (1, 43),  # L01-L43
        },
    },
    "support_scales": {
        "NJC": {
            "code_pattern": "NJC_{LA}",  # e.g., NJC_CHE for Cheshire East
            "title_pattern": "NJC - {LA_Name}",
            "increment_date": "2021-04-01",  # April for support
            "service_increment_enabled": True,
        },
        "APP_NMW": {
            "code": "APP_NMW",
            "title": "Apprentice / NMW Scale",
            "increment_date": "2022-04-01",
            "increase_percentage": 2,
        },
    },
    "special_scales": {
        "CEO": {
            "code": "CEO",
            "title": "CEO Scale",
            "available_to_all_schools": False,
            "school_codes": "MAT",  # Only available to MAT
        },
    },
}

S2_PAY_SCALE_POINT_PATTERNS = {
    "main_scale": {
        "points": ["M1", "M2", "M3", "M4", "M5", "M6", "U1", "U2", "U3"],
        "scale_point_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "rate_date_format": "YYYY-MM-DD",
    },
    "leadership": {
        "point_format": "L{:02d}",  # L01, L02, etc.
        "range": (1, 43),
    },
    "njc": {
        "point_format": "{point}",  # Just the number
        "grade_format": "CHE_{grade:02d}",  # CHE_01, CHE_02, etc.
    },
}

S2_PAY_SCALE_GRADE_PATTERNS = {
    "teaching": {
        "MAIN_UPS": {"title": "Teachers Main through UPS", "from": "M1", "to": "U3", "numbers": (1, 9)},
        "MAIN": {"title": "Teachers Main Scale only", "from": "M1", "to": "M6", "numbers": (1, 6)},
        "UPS": {"title": "Teachers Upper Scale only", "from": "U1", "to": "U3", "numbers": (7, 9)},
    },
    "leadership": {
        "format": "L{from:02d}-L{to:02d}",  # e.g., L02-L06
        "title_format": "Leadership scp L{from:02d}-L{to:02d}",
    },
    "njc": {
        "format": "CHE_{grade:02d}",  # e.g., CHE_04
        "title_format": "Grade {grade}",
    },
}

S2_STAFF_ROLE_GROUP_PATTERNS = {
    # Standard 15 Staff Role Groups with DFE finance code patterns
    "LST": {
        "code": "LST",
        "title": "Staff Costs - Leadership Teaching-Wages and salaries",
        "gross_salary_fc": "610100",
        "ni_fc": "610200",
        "pension_fc": "610300",
        "teaching": True,
    },
    "LSN": {
        "code": "LSN",
        "title": "Staff Costs - Leadership Non-Teaching-Wages and salaries",
        "gross_salary_fc": "611100",
        "ni_fc": "611200",
        "pension_fc": "611300",
        "teaching": False,
    },
    "TEA": {
        "code": "TEA",
        "title": "Staff Costs - Teachers-Wages and salaries",
        "gross_salary_fc": "612100",
        "ni_fc": "612200",
        "pension_fc": "612300",
        "teaching": True,
    },
    "TA": {
        "code": "TA",
        "title": "Staff Costs - Teaching Assistants-Wages and salaries",
        "gross_salary_fc": "615100",
        "ni_fc": "615200",
        "pension_fc": "615300",
        "teaching": False,
    },
    "EDS": {
        "code": "EDS",
        "title": "Staff Costs - Educational Support-Wages and salaries",
        "gross_salary_fc": "619100",
        "ni_fc": "619200",
        "pension_fc": "619300",
        "teaching": False,
    },
    "LIB": {
        "code": "LIB",
        "title": "Staff Costs - Librarians-Wages and salaries",
        "gross_salary_fc": "620100",
        "ni_fc": "620200",
        "pension_fc": "620300",
        "teaching": False,
    },
    "TEC": {
        "code": "TEC",
        "title": "Staff Costs - Technicians-Wages and salaries",
        "gross_salary_fc": "622100",
        "ni_fc": "622200",
        "pension_fc": "622300",
        "teaching": False,
    },
    "ADM": {
        "code": "ADM",
        "title": "Staff Costs - Finance and Admin-Wages and salaries",
        "gross_salary_fc": "625100",
        "ni_fc": "625200",
        "pension_fc": "625300",
        "teaching": False,
    },
    "PRE": {
        "code": "PRE",
        "title": "Staff Costs - Site Staff-Wages and salaries",
        "gross_salary_fc": "627100",
        "ni_fc": "627200",
        "pension_fc": "627300",
        "teaching": False,
    },
    "CLE": {
        "code": "CLE",
        "title": "Staff Costs - Cleaning Staff-Wages and salaries",
        "gross_salary_fc": "630100",
        "ni_fc": "630200",
        "pension_fc": "630300",
        "teaching": False,
    },
    "MDS": {
        "code": "MDS",
        "title": "Staff Costs - Midday Supervisors-Wages and salaries",
        "gross_salary_fc": "635100",
        "ni_fc": "635200",
        "pension_fc": "635300",
        "teaching": False,
    },
    "NUR": {
        "code": "NUR",
        "title": "Staff Costs - Nursery Staff-Wages and salaries",
        "gross_salary_fc": "637100",
        "ni_fc": "637200",
        "pension_fc": "637300",
        "teaching": False,
    },
    "FSW": {
        "code": "FSW",
        "title": "Staff Costs - Family Support Workers-Wages and salaries",
        "gross_salary_fc": "640100",
        "ni_fc": "640200",
        "pension_fc": "640300",
        "teaching": False,
    },
    "OTH": {
        "code": "OTH",
        "title": "Staff Costs - Other Staff-Wages and salaries",
        "gross_salary_fc": "647100",
        "ni_fc": "647200",
        "pension_fc": "647300",
        "teaching": False,
    },
    "TEA_SS": {
        "code": "TEA_SS",
        "title": "Staff Costs - Teaching Supply Staff-Wages and salaries",
        "gross_salary_fc": "650400",
        "ni_fc": "650410",
        "pension_fc": "650420",
        "teaching": True,
    },
}

# FTE Finance Code pattern for each Staff Role Group
S2_FTE_CODE_PATTERN = {
    "weekly_fte": "WK_FTE_{srg}",
    "annual_fte": "A_FTE_{srg}",
    "weekly_leave_adj": "WK_FTE_LEAVE_ADJ_{srg}",
    "annual_leave_adj": "A_FTE_LEAVE_ADJ_{srg}",
}

S2_STAFF_ROLE_PATTERNS = {
    "teaching_roles": {
        "CEO": {"group": "LST", "scale": "CEO", "hours": 32.436, "mat_only": True},
        "HOS": {"group": "LST", "scale": "LS", "hours": 32.436, "title": "Head of School"},
        "HT": {"group": "LST", "scale": "LS", "hours": 32.436, "title": "Headteacher"},
        "DHT": {"group": "LST", "scale": "LS", "hours": 32.436, "title": "Deputy Headteacher"},
        "AHT": {"group": "LST", "scale": "LS", "hours": 32.436, "title": "Assistant Headteacher"},
        "LST": {"group": "TEA", "scale": "LS", "hours": 32.436, "title": "Leadership Teacher"},
        "AHT_MAIN": {"group": "TEA", "scale": "MAIN", "hours": 32.436, "title": "Assistant Headteacher - Main Scale"},
        "TEA": {"group": "TEA", "scale": "MAIN", "hours": 32.436, "title": "Teacher"},
        "UQ_TEA": {"group": "TEA", "scale": "UQ", "hours": 32.436, "title": "Unqualified Teacher"},
    },
    "support_roles": {
        "CFO": {"group": "LSN", "scale": "LS", "hours": 37, "title": "Chief Financial Officer", "finance_role": True},
        "ADM": {"group": "ADM", "scale": "NJC", "hours": 37, "title": "Admin Assistant"},
        "ADM_TL": {"group": "ADM", "scale": "NJC", "hours": 37, "title": "Admin Team Leader"},
        "REC": {"group": "ADM", "scale": "NJC", "hours": 37, "title": "Receptionist"},
        "TA": {"group": "TA", "scale": "NJC", "hours": 37, "title": "Teaching Assistant"},
        "HLTA": {"group": "TA", "scale": "NJC", "hours": 37, "title": "Higher Level Teaching Assistant"},
        "TEC": {"group": "TEC", "scale": "NJC", "hours": 37, "title": "Technician"},
        "CLN": {"group": "CLE", "scale": "NJC", "hours": 37, "title": "Cleaner"},
        "CAR": {"group": "PRE", "scale": "NJC", "hours": 37, "title": "Caretaker"},
        "MDS": {"group": "MDS", "scale": "NJC", "hours": 37, "title": "Midday Supervisor"},
    },
    "full_time_hours": {
        "teaching": 32.436,
        "support": 37.0,
    },
}

S2_CONTRACT_PATTERNS = {
    "teaching": {
        "reference_suffix": "A",  # StaffMemberCode + 'A'
        "department_code": "STCH",  # Standard Teaching
        "eqwp_code": "AYR",  # All Year Round
        "pension_code": "TPS",
        "contract_type": "PERM",
        "uses_fte": True,  # WeeklyFteOrHpw is FTE (0-1)
    },
    "support": {
        "reference_suffix": "A",
        "department_code": "SFIN",  # Standard Finance/Support
        "eqwp_pattern": "{LA}_{weeks}.0W",  # e.g., CHE_40.0W
        "pension_pattern": "LGPS_{LA}",  # e.g., LGPS_CHE
        "contract_type": "PERM",
        "uses_hours": True,  # WeeklyFteOrHpw is actual hours
    },
}

S2_EQWP_PATTERNS = {
    "all_year": {
        "code": "AYR",
        "title": "All Year Round",
        "equated_weeks": 52.143,
        "full_time_weeks": 52.143,
        "service_years_from": 0,
        "service_years_to": 99,
    },
    "tto_pattern": {
        "code_format": "{LA}_{weeks}.0W",  # e.g., CHE_38.0W
        "title_format": "{weeks}.0 Weeks Worked - {LA_Name}",
        "service_bands": [
            {"years_from": 0, "years_to": 4, "leave_adjustment": -0.992},
            {"years_from": 5, "years_to": 99, "leave_adjustment": 0},
        ],
    },
}

S2_PENSION_PATTERNS = {
    "TPS": {
        "code": "TPS",
        "title": "Teachers Pension Scheme",
        "percentage": 28.68,
        "rate_date": "2024-04-01",
    },
    "LGPS": {
        "code_pattern": "LGPS_{LA}",  # e.g., LGPS_CHE
        "title_pattern": "LGPS - {LA_Name}",
        "percentage": 21.90,  # Varies by LA
        "rate_date": "2025-04-01",
    },
    "OPTOUT": {
        "code": "OPTOUT",
        "title": "Opted Out 0%",
        "percentage": 0,
    },
}


# =============================================================================
# S3 PATTERNS - Financial Team
# =============================================================================

S3_PUPIL_PATTERNS = {
    "spring_census": {
        "code_format": "PUPIL_SPRING_{keystage}",  # KS3, KS4, KS5
        "description_format": "{keystage} Spring Census Pupil Numbers",
        "notes": {
            "KS3": "Year 7, 8, and 9 Students From Table 3 of School census collection: Spring",
            "KS4": "Year 10 & 11 Students From Table 3 of School census collection: Spring",
            "KS5": "Year 12, 13, and 14 Students From Table 3 of School census collection: Spring",
        },
        "year_offset": -2,  # Uses Spring from 2 years prior for DFC
    },
    "autumn_census": {
        "code_format": "PUPIL_CEN_{year:02d}",  # 07, 08, 09, 10, 11, 12, 13, 14
        "description_format": "Year {year} Pupil Numbers - Autumn Census",
        "notes": "From Table 3 of School census collection: Autumn",
        "calculator_pattern": "PUPILY{prev_year:02d}_LY",  # Links to last year
    },
    "pupil_premium": {
        "PUPILPREMIUMPLAC": {
            "description": "Pupil Premium PLAC Numbers",
            "notes": "Post Looked After Children number From Table 5 of School census collection: Autumn",
        },
        "PUPILPREMIUMSER": {
            "description": "Pupil Premium Service Numbers",
            "notes": "Service Children number From Table 5 of School census collection: Autumn",
        },
        "PUPILPREMIUM_PRI": {
            "description": "Pupil Premium Numbers Primary",
            "notes": "From DFE Pupil Premium spreadsheet",
        },
        "PUPILPREMIUM_SEC": {
            "description": "Pupil Premium Numbers Secondary",
            "notes": 'From DFE Pupil Premium spreadsheet, column "Number of Secondary pupils eligible for the Deprivation Pupil Premium"',
        },
    },
}

S3_STATISTICS_PATTERNS = {
    "uplift_factors": {
        "UPLIFT_PUPILASCL%": "Pupil ASCL Uplift %",
        "UPLIFT_PUPILEXP%": "Pupil Expenditure Uplift %",
        "UPLIFT_PUPILGAG%": "Pupil GAG Uplift %",
        "UPLIFT_PUPILINC%": "Pupil Income Uplift %",
        "UPLIFT_PUPILPOST16%": "Pupil Post 16 GAG Uplift %",
        "UPLIFT_PUPILRPI%": "Pupil RPI Uplift %",
    },
    "calculator_mappings": {
        "PUPILASCL_FACTOR": "Percentage change combined with ASCL Uplift",
        "PUPILEXP_FACTOR": "Percentage change combined with Expenditure Uplift",
        "PUPILGAG_FACTOR": "Percentage change combined with GAG Uplift",
        "PUPILINC_FACTOR": "Percentage change combined with Income Uplift",
        "PUPILPOST16_FACTOR": "Percentage change combined with Post 16 GAG Uplift",
        "PUPILRPI_FACTOR": "Percentage change combined with RPI Uplift",
    },
}

S3_INCOME_PATTERNS = {
    "gag_funding": {
        "code": "510100",
        "description": "GAG Funding",
        "department": "IGAG",
        "calculator": "FUNDING_GAG",
    },
    "gag_post16": {
        "code": "510700",
        "description": "GAG Post 16 Funding",
        "department": "IGAG",
        "calculator": "FUNDING_16_19",
    },
    "central_contribution": {
        "code": "530990",
        "description": "Central Contribution from Schools",
        "department": "TCT_CS",  # Trust Central
        "calculator": "CENTRALCHG_MAT",
        "school": "MAT",  # Only at MAT level
    },
    "pupil_premium": {
        "code": "510200",
        "description": "Pupil Premium",
        "calculator": "PUPPREMIUM_CALC",
    },
    "uifsm": {
        "code": "510250",
        "description": "UIFSM Income",
        "calculator": "UIFSM_CALC",
    },
    "pe_grant": {
        "code": "510400",
        "description": "PE and Sports Grant",
        "calculator": "PE_GRANT_CALC",
    },
}

S3_EXPENDITURE_PATTERNS = {
    "central_charge": {
        "code": "835170",
        "description": "Central Charge School",
        "department": "ADMINSER",
        "calculator": "CENTRALCHG_SCH",
    },
    "dfc": {
        "code": "770102",
        "description": "DFC Expenditure",
        "department": "EXDFC",
        "ledger": "CAPITAL",
        "calculator": "DFC_EXP",
    },
    "staff_costs": {
        # Linked to S2 StfRoleGroup finance codes
        "pattern": "6XXXXX",
        "ledger": "COSTCTR",
    },
}

S3_SCENARIO_PATTERNS = {
    "approved_budget": {
        "code_format": "APBUD{yy1}{yy2}",  # e.g., APBUD2526
        "description": "Approved Budget for {year1}/{year2}",
    },
    "master_budget": {
        "code": "MASTER_OG",
        "description": "Master Budget (Original)",
    },
    "default": {
        "code": None,  # Master scenario has no code
        "includes_calculations": True,
    },
}

S3_BF_BALANCE_PATTERNS = {
    "capital": {
        "code": "CAP_BFWD_RES",
        "description": "Brought Forward Balance Capital",
    },
    "revenue": {
        "code": "REV_BFWD_RES",
        "description": "Brought Forward Balance Revenue",
    },
}

S3_CALCULATOR_PATTERNS = {
    "dfc": {
        "core": "DFC_CORE",
        "pupil": "DFC_PUPIL_{keystage}",
        "expenditure": "DFC_EXP",
    },
    "funding": {
        "gag": "FUNDING_GAG",
        "post16": "FUNDING_16_19",
    },
    "central_charge": {
        "school": "CENTRALCHG_SCH",
        "mat": "CENTRALCHG_MAT",
    },
    "pupil_premium": {
        "factor": "PUPPREMIUM_FACTOR",
    },
    "zero": "0%_CALC",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_srg_for_role(role_title: str) -> str:
    """Determine Staff Role Group code from role title."""
    role_lower = role_title.lower()

    # Leadership
    if any(kw in role_lower for kw in ['head', 'principal', 'ceo', 'director']):
        if 'deputy' in role_lower or 'assistant' in role_lower:
            return 'LST'  # Leadership Teaching
        return 'LST'

    # Teachers
    if any(kw in role_lower for kw in ['teacher', 'tutor', 'lecturer']):
        return 'TEA'

    # Teaching Assistants
    if any(kw in role_lower for kw in ['teaching assistant', 'ta ', 'hlta', 'lsa']):
        return 'TA'

    # Admin
    if any(kw in role_lower for kw in ['admin', 'office', 'secretary', 'receptionist', 'finance']):
        return 'ADM'

    # Site Staff
    if any(kw in role_lower for kw in ['caretaker', 'site', 'maintenance', 'groundsman']):
        return 'PRE'

    # Cleaning
    if any(kw in role_lower for kw in ['clean', 'domestic']):
        return 'CLE'

    # Technicians
    if any(kw in role_lower for kw in ['technician', 'ict', 'it support']):
        return 'TEC'

    # Midday
    if any(kw in role_lower for kw in ['midday', 'lunchtime', 'msa']):
        return 'MDS'

    # Catering
    if any(kw in role_lower for kw in ['catering', 'cook', 'kitchen', 'chef']):
        return 'OTH'  # Often goes to OTH

    # Educational Support
    if any(kw in role_lower for kw in ['support', 'welfare', 'pastoral', 'mentor']):
        return 'EDS'

    # Default to OTH
    return 'OTH'


def create_role_code(title: str, srg: str) -> str:
    """Create a short role code from title."""
    import re

    # Common abbreviations
    abbreviations = {
        'assistant': 'AST',
        'headteacher': 'HT',
        'teacher': '',  # Often omitted
        'technician': '',
        'manager': 'MGR',
        'officer': 'OFF',
        'coordinator': 'COORD',
        'leader': 'TL',
    }

    title_clean = title.upper().strip()

    # Check for known roles first
    known_roles = {
        'CEO': 'CEO',
        'HEADTEACHER': 'HT',
        'DEPUTY HEADTEACHER': 'DHT',
        'ASSISTANT HEADTEACHER': 'AHT',
        'TEACHER': 'TEA',
        'TEACHING ASSISTANT': 'TA',
        'HIGHER LEVEL TEACHING ASSISTANT': 'HLTA',
        'RECEPTIONIST': 'REC',
        'CLEANER': 'CLN',
        'CARETAKER': 'CAR',
        'MIDDAY SUPERVISOR': 'MDS',
    }

    for known, code in known_roles.items():
        if known in title_clean:
            return code

    # Generate code from initials
    words = re.findall(r'[A-Z][a-z]*', title)
    if words:
        code = ''.join(w[0] for w in words[:3])
        return f"{srg}_{code}" if len(code) < 3 else code

    return f"{srg}_ROLE"


def get_finance_codes_for_srg(srg_code: str) -> dict:
    """Get all finance codes for a Staff Role Group."""
    srg = S2_STAFF_ROLE_GROUP_PATTERNS.get(srg_code, {})
    if not srg:
        return {}

    return {
        "gross_salary": srg.get("gross_salary_fc"),
        "ni": srg.get("ni_fc"),
        "pension": srg.get("pension_fc"),
        "weekly_fte": f"WK_FTE_{srg_code}",
        "annual_fte": f"A_FTE_{srg_code}",
        "weekly_leave_adj": f"WK_FTE_LEAVE_ADJ_{srg_code}",
        "annual_leave_adj": f"A_FTE_LEAVE_ADJ_{srg_code}",
    }
