"""
S1 Import File Format Standards

This module documents the format conventions discovered from analyzing the
official S1 import CSV files in knowledge/S1/import files/.

These standards should be applied to ALL S1 output to ensure compatibility
with the IMP Planner import system.
"""

# =============================================================================
# BOOLEAN FORMAT
# =============================================================================
BOOLEAN_FORMAT = {
    'true': 'True',   # Capitalized, NOT 'true' or 'TRUE' or 'Yes' or '1'
    'false': 'False',  # Capitalized, NOT 'false' or 'FALSE' or 'No' or '0'
}

# All "Enabled" columns use True/False
ENABLED_COLUMNS = [
    'FundEnabled',
    'ActivityEnabled',
    'LedgerEnabled',
    'SchoolHubEnabled',
    'SchoolTypeEnabled',
    'SchoolLocalAuthorityEnabled',
    'SchoolEnabled',
    'DepartmentEnabled',
    'FinanceCodeEnabled',
    'GenderEnabled',
    'CustomGroupingEnabled',
]


# =============================================================================
# CODE FORMATS
# =============================================================================
CODE_FORMATS = {
    # Fund codes - short uppercase (2-7 chars)
    'fund': {
        'format': 'UPPERCASE, 2-7 characters',
        'examples': ['BURS', 'CAP', 'DEFAULT', 'GAG', 'REST', 'UNRF', 'SPPR'],
    },

    # Activity codes - uppercase single words
    'activity': {
        'format': 'UPPERCASE single words',
        'examples': ['BOARDING', 'CATERING', 'DEFAULT', 'EXTENDED', 'NURSERY', 'SCHOOL'],
    },

    # Ledger codes - uppercase
    'ledger': {
        'format': 'UPPERCASE',
        'examples': ['CAPITAL', 'COSTCTR', 'DEFAULT', 'PURCH', 'SALARY', 'TRIPS'],
    },

    # School Hub codes - short uppercase (3-7 chars)
    'school_hub': {
        'format': 'UPPERCASE abbreviations',
        'examples': ['DEFAULT', 'LON', 'MID', 'NORTH', 'SOUTH'],
    },

    # School Type codes - uppercase abbreviations
    'school_type': {
        'format': 'UPPERCASE abbreviations',
        'examples': ['6THFORM', 'ALTER', 'ALTHR', 'CENTRAL', 'INFANT', 'PRIMARY', 'SECONDARY', 'SPECIAL'],
    },

    # Local Authority codes - 3-letter uppercase
    'local_authority': {
        'format': '3-letter UPPERCASE',
        'examples': ['BNT', 'BRM', 'DEFAULT', 'HCK', 'KEN', 'LNS', 'NTS', 'SUR'],
    },

    # School codes - 2-3 letter uppercase
    'school': {
        'format': '2-3 letter UPPERCASE',
        'examples': ['ALE', 'APP', 'EDU', 'GOO', 'GRE', 'LEA', 'LOR', 'MAR', 'MAT', 'MID', 'MIL', 'OUR'],
    },

    # Department codes - uppercase with underscores
    'department': {
        'format': 'UPPERCASE with underscores (PREFIX_SUFFIX)',
        'examples': ['AADM', 'CAP_DFC', 'CUR_ART', 'CUR_ENG', 'EXP_ADM', 'INC_GAG',
                     'PREM_UTL', 'SAL_TEA', 'SAL_TA', 'TRIP_YR7AW'],
        'prefixes': ['A', 'CAP', 'CUR', 'EXP', 'INC', 'PREM', 'SAL', 'TRIP'],
    },

    # Finance codes - numeric (4-6 digits) or alphanumeric
    'finance': {
        'format': '4-6 digit numeric OR alphanumeric with underscores',
        'numeric_examples': ['510100', '515100', '520100', '530100', '550100', '610100'],
        'alpha_examples': ['01FEE_NUR_01', 'A_FTE_ADM', 'WK_FTE_TEA'],
    },

    # Custom Grouping codes - letter + number or ZZZ
    'custom_grouping': {
        'format': 'Letter + Number (A0-W1) or ZZZ/ZB###',
        'examples': ['A0', 'A2', 'A3', 'A4', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5',
                     'C0', 'C1', 'D0', 'E0', 'F0', 'G0', 'G1', 'H0', 'I0', 'L0',
                     'W0', 'W1', 'ZB900', 'ZZZ'],
    },

    # Gender codes - single letter or ZZZ
    'gender': {
        'format': 'Single UPPERCASE letter or ZZZ',
        'examples': ['F', 'M', 'ZZZ'],
    },

    # FinanceCodeTypeCode - specific values
    'finance_code_type': {
        'format': 'UPPERCASE specific values',
        'examples': ['BUDGET', 'STATISTICS'],
    },
}


# =============================================================================
# SCHOOL CODES FORMAT
# =============================================================================
SCHOOL_CODES_FORMAT = {
    # Multi-value format: comma-separated, NO spaces, NO quotes
    'single': 'MIL',
    'multiple': 'LEA,MIL,ALE,APP',  # No spaces after commas
    'all_schools': '',  # Empty when AvailableToAllSchools=True
}

# Standard school codes found in import files
STANDARD_SCHOOL_CODES = [
    'ALE', 'APP', 'EDU', 'GOO', 'GRE', 'LEA',
    'LOR', 'MAR', 'MAT', 'MID', 'MIL', 'OUR'
]


# =============================================================================
# NUMERIC PRECISION
# =============================================================================
NUMERIC_PRECISION = {
    # Teaching hours - up to 2 decimal places
    'teaching_hours': {
        'decimals': 2,
        'examples': [25.0, 27.5, 32.5, 32.43],
    },

    # URN - integer (6 digits typically, 0 for MAT)
    'urn': {
        'type': 'integer',
        'examples': [775026, 775062, 775074, 0],
    },
}


# =============================================================================
# EMPTY VALUE HANDLING
# =============================================================================
EMPTY_VALUES = {
    # Use empty string for missing optional values
    'optional_empty': '',

    # SchoolCodes empty when AvailableToAllSchools=True
    'school_codes_when_all': '',

    # DefaultFinanceCode often empty
    'default_finance_code': '',

    # Values that should NOT be used for empty
    'invalid': ['nan', 'NaN', 'None', 'null', 'N/A', '#N/A'],
}


# =============================================================================
# FILE STRUCTURE PATTERNS
# =============================================================================
FILE_PATTERNS = {
    # Simple reference tables (3 columns: Code, Title, Enabled)
    'simple_reference': {
        'columns': ['Code', 'Title', 'Enabled'],
        'files': ['Funds', 'Activities', 'Ledger', 'Hubs', 'SchoolTypes', 'LocalAuth', 'Genders', 'CustomGroup'],
    },

    # Schools table (8 columns with relationships)
    'schools': {
        'columns': ['SchoolCode', 'SchoolHub', 'SchoolType', 'Title',
                    'LondonWeighting', 'UniqueReferenceNumber', 'TeachingHours', 'SchoolEnabled'],
    },

    # Departments table (9 columns with relationships)
    'departments': {
        'columns': ['DepartmentCode', 'Title', 'AvailableToAllSchools', 'SchoolCodes',
                    'ActivityCode', 'FundCode', 'LedgerCode', 'DefaultFinanceCode', 'DepartmentEnabled'],
    },

    # Finance codes table (9 columns)
    'finance_codes': {
        'columns': ['FinanceCode', 'Title', 'GroupingCode', 'CustomGrouping',
                    'AvailableToAllSchools', 'SchoolCodes', 'FinanceCodeTypeCode',
                    'LedgerCode', 'FinanceCodeEnabled'],
    },
}


# =============================================================================
# CUSTOM GROUPING HIERARCHY
# =============================================================================
CUSTOM_GROUPING_HIERARCHY = {
    # Income categories (A#)
    'A0': 'GAG funding',
    'A2': 'Other Government Grants',
    'A3': 'Private Sector Funding',
    'A4': 'Other Income',

    # Staff categories (B#)
    'B0': 'Teaching Staff',
    'B1': 'Educational Support Staff',
    'B2': 'Premises Staffing',
    'B3': 'Admin Staffing',
    'B4': 'Other Staff',
    'B5': 'Agency Staff',

    # Costs categories (C#-I#)
    'C0': 'Maintenance of Premises',
    'C1': 'Other Occupational Costs',
    'D0': 'Educational Supplies and Services',
    'E0': 'Other Supplies and Services',
    'F0': 'ICT Costs (Non Capital)',
    'G0': 'Staff Development',
    'G1': 'Indirect Employees Expenses',
    'H0': 'Other GAG Expenses',
    'I0': 'Depreciation',

    # Financing (L#)
    'L0': 'Direct Revenue Financing',

    # Capital (W#)
    'W0': 'Capital Income',
    'W1': 'Capital Expenditure',

    # Balance sheet (ZB###)
    'ZB900': 'Land & Buildings',

    # Not applicable
    'ZZZ': 'Not Applicable',
}


# =============================================================================
# DFE GROUPING CODE PREFIXES
# =============================================================================
DFE_CODE_PREFIXES = {
    '51': 'DfE Revenue Grants',
    '52': 'Other Government Grants',
    '53': 'Other Income',
    '55': 'Capital Grants',
    '57': 'Boarding Income',
    '61': 'Staff Costs',
    '62': 'Premises',
    '63': 'Educational Supplies',
    '64': 'Other Costs',
    '65': 'Capital Expenditure',
}


# =============================================================================
# VALIDATION RULES
# =============================================================================
VALIDATION_RULES = {
    # Required fields (should never be empty)
    'required_fields': {
        'Funds': ['FundCode', 'Title'],
        'Activities': ['ActivityCode', 'Title'],
        'Schools': ['SchoolCode', 'Title', 'SchoolHub', 'SchoolType'],
        'Departments': ['DepartmentCode', 'Title', 'ActivityCode', 'FundCode', 'LedgerCode'],
        'FinanceCodes': ['FinanceCode', 'Title', 'GroupingCode', 'CustomGrouping', 'FinanceCodeTypeCode', 'LedgerCode'],
    },

    # Foreign key relationships
    'foreign_keys': {
        'Schools.SchoolHub': 'Hubs.SchoolHubCode',
        'Schools.SchoolType': 'SchoolTypes.SchoolTypeCode',
        'Departments.ActivityCode': 'Activities.ActivityCode',
        'Departments.FundCode': 'Funds.FundCode',
        'Departments.LedgerCode': 'Ledger.LedgerCode',
        'FinanceCodes.LedgerCode': 'Ledger.LedgerCode',
        'FinanceCodes.CustomGrouping': 'CustomGroup.CustomGroupingCode',
    },
}


def validate_code_format(code: str, code_type: str) -> bool:
    """Validate code format matches expected pattern."""
    if not code:
        return False

    code = str(code).strip().upper()

    if code_type == 'school':
        return len(code) in (2, 3) and code.isalpha()
    elif code_type == 'local_authority':
        return len(code) == 3 and code.isalpha()
    elif code_type == 'finance':
        return code.isdigit() and 4 <= len(code) <= 6
    elif code_type == 'gender':
        return code in ('F', 'M', 'ZZZ')

    return True


def validate_boolean(value) -> bool:
    """Check if value is valid boolean format."""
    return value in ('True', 'False', True, False)
