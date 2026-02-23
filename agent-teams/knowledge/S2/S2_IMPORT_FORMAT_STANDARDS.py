"""
S2 Import File Format Standards

This module documents the format conventions discovered from analyzing the
official S2 import CSV files in knowledge/S2/import files/.

These standards should be applied to ALL S2 output to ensure compatibility
with the IMP Planner import system.
"""

# =============================================================================
# DATE FORMATS
# =============================================================================
DATE_FORMATS = {
    # Full dates use ISO format
    'full_date': 'YYYY-MM-DD',  # e.g., 2024-09-01

    # Partial dates (increment/increase dates) use month/day only
    'partial_date': 'MM/DD',  # e.g., 01/04 (April 1st), 01/09 (September 1st)

    # Financial years
    'financial_year': 'YYYY/YY',  # e.g., 2024/25, 2025/26
}

# Common date values
COMMON_DATES = {
    'fiscal_year_start': '09/01',  # September 1
    'financial_year_start': '04/01',  # April 1
    'contract_start': '2024-09-01',  # Common contract start
    'contract_end': '2025-08-31',  # Common contract end
}


# =============================================================================
# BOOLEAN FORMAT
# =============================================================================
BOOLEAN_FORMAT = {
    'true': 'True',   # Capitalized, NOT 'true' or 'TRUE' or 'Yes' or '1'
    'false': 'False',  # Capitalized, NOT 'false' or 'FALSE' or 'No' or '0'
}


# =============================================================================
# SCHOOL CODES
# =============================================================================
SCHOOL_CODE_FORMAT = {
    # 3-letter uppercase codes
    'format': '3-letter uppercase',
    'examples': ['MAT', 'LEA', 'MID', 'GRE', 'LOR', 'ALE', 'APP', 'EDU'],

    # Multi-value: comma-separated, quoted when multiple
    'single': 'MIL',                    # No quotes for single value
    'multiple': '"MAT,ALE,APP,MAR"',    # Quoted when multiple values
    'multiple_unquoted': 'MAT,ALE,APP,MAR',  # CSV output handles quoting
}


# =============================================================================
# LOCATION VARIANTS (for Pay Scales and Roles)
# =============================================================================
LOCATION_VARIANTS = {
    'EW': 'East/West',
    'FRI': 'Fringe',
    'IL': 'Inner London',
    'OL': 'Outer London',
    'NMW': 'National Minimum Wage (apprentices)',
}


# =============================================================================
# NUMERIC PRECISION
# =============================================================================
NUMERIC_PRECISION = {
    # FTE values: 1 decimal place
    'fte': {
        'decimals': 1,
        'examples': [0.2, 0.4, 0.5, 0.8, 1.0],
    },

    # Hours per week: 1-2 decimal places
    'hours_per_week': {
        'decimals': 2,
        'examples': [37.0, 37.5, 32.5, 32.43, 25.0],
    },

    # Full time weeks: 3 decimal places
    'full_time_weeks': {
        'decimals': 3,
        'examples': [52.143, 52.1429],
    },

    # Pay rates: 2 decimal places
    'pay_rate': {
        'decimals': 2,
        'examples': [50025.00, 478.51, 184.03],
    },

    # Percentages: can be integer or decimal
    'percentage': {
        'decimals': 2,
        'examples': [0, 3, 1.75, 2.25, 92],
    },

    # Scale point numbers: integers
    'scale_point': {
        'type': 'integer',
        'examples': [1, 2, 3, 18, 43],
    },

    # Service years: integers, 99 = unlimited
    'service_years': {
        'type': 'integer',
        'examples': [0, 5, 10, 99],  # 99 means no maximum
    },
}


# =============================================================================
# CODE FORMATS
# =============================================================================
CODE_FORMATS = {
    # Staff Member Code
    'staff_member': {
        'format': '8-digit numeric or prefixed code',
        'examples': ['12842524', '10090559', 'ESTF_001', '1234'],
    },

    # Staff Role Code
    'staff_role': {
        'format': '{ROLE}_{HOURS}_{LOCATION}',
        'examples': ['TEA_32.5_EW', 'ADM_AST_37_EW', 'TA_37_EW', 'HT_32.5_EW'],
    },

    # Staff Role Group Code
    'staff_role_group': {
        'format': '2-4 character uppercase',
        'examples': ['ADM', 'CAT', 'TEA', 'TA', 'LST', 'PRE', 'ESTF_SPO'],
    },

    # Pay Scale Code
    'pay_scale': {
        'format': 'UPPERCASE with underscores',
        'examples': ['MAIN_EW', 'NJC_OL', 'LP_FRI', 'LS_IL', 'APP/NMW', 'KENT'],
    },

    # Pay Scale Point Code
    'pay_scale_point': {
        'format': 'Alphanumeric, varies by scale',
        'examples': ['M1', 'L18', 'UQ1', 'LP01', '2', '30', 'Y1', 'H_01'],
    },

    # Department Code
    'department': {
        'format': 'SAL_{CATEGORY}',
        'examples': ['SAL_TEA', 'SAL_LST', 'SAL_ADM', 'SAL_TA', 'SAL_PRE',
                     'SAL_CAT', 'SAL_COV', 'SAL_MDS', 'SAL_FSW', 'SAL_TEC'],
    },

    # Finance Code
    'finance': {
        'format': '6-digit numeric or text reference',
        'examples': ['625100', '632100', '825100', 'MINWAGE', 'LIVWAGE', 'PENS'],
    },

    # Pension Code
    'pension': {
        'format': 'SCHEME_LOCATION',
        'examples': ['TPS', 'LGPS_BNT', 'LGPS_KEN', 'LGPS_LNS', 'OPTOUT'],
    },

    # Leave Type Code
    'leave_type': {
        'format': 'TYPE_DETAILS',
        'examples': ['MAT_STAT', 'MAT_SUP_>1YR', 'PAT_100', 'SICK_50', 'SPL_90'],
    },

    # Contract Type Code
    'contract_type': {
        'format': 'Short code',
        'examples': ['ZZZ', 'FXT'],  # ZZZ=standard/permanent, FXT=fixed-term
    },

    # Fund Code
    'fund': {
        'format': 'Short code',
        'examples': ['REST', 'BURS'],
    },
}


# =============================================================================
# FTE TRACKING CODES
# =============================================================================
FTE_CODE_PATTERNS = {
    'weekly_fte': 'WK_FTE_{ROLE}',           # e.g., WK_FTE_ADM, WK_FTE_TEA
    'annual_fte': 'A_FTE_{ROLE}',            # e.g., A_FTE_ADM, A_FTE_TEA
    'weekly_leave_adj': 'WK_FTE_LEAVE_ADJ_{ROLE}',  # e.g., WK_FTE_LEAVE_ADJ_ADM
    'annual_leave_adj': 'A_FTE_LEAVE_ADJ_{ROLE}',   # e.g., A_FTE_LEAVE_ADJ_ADM
}


# =============================================================================
# EMPTY VALUE HANDLING
# =============================================================================
EMPTY_VALUES = {
    # Use empty string for missing values
    'string': '',

    # ScenarioCode is typically empty (global scenario)
    'scenario_code': '',

    # Reference and Notes fields often empty
    'reference': '',
    'notes': '',

    # DateTo often empty for ongoing items
    'date_to': '',

    # Values that should NOT be used for empty
    'invalid': ['nan', 'NaN', 'None', 'null', 'N/A', '#N/A'],
}


# =============================================================================
# COLUMN NAME MAPPINGS (customer data -> import file format)
# =============================================================================
COLUMN_MAPPINGS = {
    # Staff Members
    'Staff Number': 'StaffMemberCode',
    'Staff Code': 'StaffMemberCode',
    'Surname': 'LastName',
    'Forename': 'FirstName',
    'First Name': 'FirstName',
    'Gender': 'GenderCode',
    'DOB': 'DateOfBirth',
    'Date of Birth': 'DateOfBirth',
    'Start Date': 'ServiceStartDate',
    'Service Start': 'ServiceStartDate',

    # Contracts
    'Contract Start': 'DateFrom',
    'Contract End': 'DateTo',
    'FTE': 'WeeklyFteOrHpw',
    'Hours': 'WeeklyFteOrHpw',
    'Pay Point': 'PayScalePointCode',
    'Scale Point': 'PayScalePointCode',
    'Grade': 'PayScaleGradeCode',

    # Pay Scales
    'Scale': 'PayScaleCode',
    'Pay Scale': 'PayScaleCode',
    'Increment Date': 'IncrementDate',

    # General
    'Available': 'AvailableToAllSchools',
    'Enabled': 'Enabled',
    'Schools': 'SchoolCodes',
}


# =============================================================================
# VALIDATION RULES
# =============================================================================
VALIDATION_RULES = {
    # Required fields (should never be empty)
    'required_fields': {
        'StaffMembers': ['StaffMemberCode', 'LastName', 'FirstName'],
        'StaffRoles': ['StaffRoleCode', 'StaffRoleGroupCode', 'PayScaleCode'],
        'Contracts': ['SchoolCode', 'StaffMemberCode', 'StaffRoleCode', 'DateFrom'],
        'PayScales': ['PayScaleCode', 'PayScaleTitle'],
        'PayScalePoints': ['PayScaleCode', 'PayScalePointCode', 'ScalePointNumber'],
    },

    # Value ranges
    'ranges': {
        'WeeklyFteOrHpw': (0.0, 1.0),  # For FTE
        'FullTimeHoursPerWeek': (0.0, 50.0),
        'ScalePointNumber': (1, 100),
        'ServiceYearsFrom': (0, 99),
        'ServiceYearsTo': (0, 99),
        'IncreasePercentage': (0, 100),
        'RebatePercentage': (0, 100),
        'PensionPercentage': (0, 100),
    },
}


def validate_date_format(date_str: str, partial: bool = False) -> bool:
    """Validate date string matches expected format."""
    import re
    if not date_str:
        return True  # Empty is valid

    if partial:
        return bool(re.match(r'^\d{2}/\d{2}$', date_str))
    else:
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))


def validate_boolean(value) -> bool:
    """Check if value is valid boolean format."""
    return value in ('True', 'False', True, False)


def validate_school_code(code: str) -> bool:
    """Validate school code format."""
    import re
    if not code:
        return True  # Empty is valid
    # Single code: 2-4 uppercase letters
    # Multiple: comma-separated
    codes = code.split(',')
    return all(re.match(r'^[A-Z]{2,4}$', c.strip()) for c in codes)
