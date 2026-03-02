"""
S2 Staff Role Mappings - Expert Knowledge

This module contains the default staff role codes for each job title,
extracted from the official import files (26_IMPORT_StaffRoles.csv).

The S2 specialist uses this to automatically assign the correct staff role code
based on job title keywords found in customer data.
"""

# =============================================================================
# STAFF ROLE GROUP CODES (StaffRoleGroupCode)
# From XAV001 - StaffRoleGroups.csv and S2_Data_Field_Mappings.xlsx
# =============================================================================
STAFF_ROLE_GROUPS = {
    # Teaching Category
    'TEA': 'Teachers',
    'LST': 'Leadership Teaching',
    'SLT': 'Senior Leadership',
    'SCITT': 'SCITT',
    'STEA_LT': 'Supply Teacher Long Term',
    'STEA_ST': 'Supply Teacher Short Term',

    # Governance Category
    'BRD_DIR': 'Board Director',
    'BRD_IND': 'Board Independent',
    'GOV': 'Governance',
    'OTH_DIR': 'Other Director',

    # Support Category
    'ADM': 'Finance and Admin',
    'APP': 'Apprentice',
    'ASC': 'After School Club',
    'BFC': 'Breakfast Club',
    'CAT': 'Catering Staff',
    'CEN': 'Central',
    'CLE': 'Cleaning Staff',
    'COM': 'Community Facilities Staff',
    'COV': 'Cover Supervisors',
    'CT': 'Caretaker',
    'CUR': 'Curriculum',
    'DEV': 'Development',
    'DRI': 'Driver',
    'EDS': 'Educational Support',
    'EST': 'Estate',
    'ESTF': 'External Staff',
    'ESTF_SPO': 'External Staff - Sports',
    'ESTF_TEA': 'External Staff - Teaching',
    'EXA': 'Exams',
    'EXT': 'External',
    'FIN': 'Finance',
    'FLA': 'First Language Assistant',
    'FSW': 'Family Support Workers',
    'HLTA': 'Higher Level TA',
    'HR': 'Human Resources',
    'INC': 'Inclusion',
    'INV': 'Exam Invigilators',
    'IT': 'IT Support',
    'LIB': 'Librarians',
    'LM': 'Line Manager',
    'LSN': 'Leadership Non-Teaching',
    'LTS': 'Learning Support',
    'MDS': 'Midday Supervisors',
    'NUR': 'Nursery Staff',
    'OTH': 'Other Staff',
    'OUT': 'Outreach',
    'PAS': 'Pastoral',
    'PERI': 'Peripatetic',
    'PRE': 'Site Staff',
    'PS': 'Personal Support',
    'SC': 'School Crossing',
    'SPO': 'Sports',
    'SSUP': 'Senior Support',
    'STA': 'Staff',
    'TA': 'Teaching Assistants',
    'TEC': 'Technicians',
    'WEL': 'Welfare',
}

# Which role groups are teaching (use TPS pension, teaching pay scales)
# From XAV001 and S2_Data_Field_Mappings.xlsx
TEACHING_ROLE_GROUPS = {'LST', 'TEA', 'SLT', 'SCITT', 'STEA_LT', 'STEA_ST'}

# Governance role groups
GOVERNANCE_ROLE_GROUPS = {'BRD_DIR', 'BRD_IND', 'GOV', 'OTH_DIR'}

# Support role groups
SUPPORT_ROLE_GROUPS = {
    'ADM', 'APP', 'ASC', 'BFC', 'CAT', 'CEN', 'CLE', 'COM', 'COV', 'CT',
    'CUR', 'DEV', 'DRI', 'EDS', 'EST', 'ESTF', 'ESTF_SPO', 'ESTF_TEA',
    'EXA', 'EXT', 'FIN', 'FLA', 'FSW', 'HLTA', 'HR', 'INC', 'INV', 'IT',
    'LIB', 'LM', 'LSN', 'LTS', 'MDS', 'NUR', 'OTH', 'OUT', 'PAS', 'PERI',
    'PRE', 'PS', 'SC', 'SPO', 'SSUP', 'STA', 'TA', 'TEC', 'WEL'
}

# =============================================================================
# STAFF ROLE GROUP FINANCE CODES
# From XAV001 - StaffRoleGroups.csv and S2_Data_Field_Mappings.xlsx
# These are the official finance codes for each role group
# =============================================================================
STAFF_ROLE_GROUP_FINANCE_CODES = {
    # Teaching roles
    'LST': {
        'GrossSalaryFinanceCode': '610100',
        'EmployersNiFinanceCode': '610200',
        'PensionFinanceCode': '610300',
        'WeeklyFteFinanceCode': 'WK_FTE_LST',
        'AnnualFteFinanceCode': 'A_FTE_LST',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_LST',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_LST',
        'TeachingRoleGroup': True,
    },
    'LSN': {
        'GrossSalaryFinanceCode': '625100',
        'EmployersNiFinanceCode': '625200',
        'PensionFinanceCode': '625300',
        'WeeklyFteFinanceCode': 'WK_FTE_LSN',
        'AnnualFteFinanceCode': 'A_FTE_LSN',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_LSN',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_LSN',
        'TeachingRoleGroup': False,
    },
    'TEA': {
        'GrossSalaryFinanceCode': '612100',
        'EmployersNiFinanceCode': '612200',
        'PensionFinanceCode': '612300',
        'WeeklyFteFinanceCode': 'WK_FTE_TEA',
        'AnnualFteFinanceCode': 'A_FTE_TEA',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_TEA',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_TEA',
        'TeachingRoleGroup': True,
    },

    # Support roles
    'TA': {
        'GrossSalaryFinanceCode': '615100',
        'EmployersNiFinanceCode': '615200',
        'PensionFinanceCode': '615300',
        'WeeklyFteFinanceCode': 'WK_FTE_TA',
        'AnnualFteFinanceCode': 'A_FTE_TA',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_TA',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_TA',
        'TeachingRoleGroup': False,
    },
    'ADM': {
        'GrossSalaryFinanceCode': '625100',
        'EmployersNiFinanceCode': '625200',
        'PensionFinanceCode': '625300',
        'WeeklyFteFinanceCode': 'WK_FTE_ADM',
        'AnnualFteFinanceCode': 'A_FTE_ADM',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_ADM',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_ADM',
        'TeachingRoleGroup': False,
    },
    'CAT': {
        'GrossSalaryFinanceCode': '2700',
        'EmployersNiFinanceCode': '2705',
        'PensionFinanceCode': '2710',
        'WeeklyFteFinanceCode': 'WK_FTE_CAT',
        'AnnualFteFinanceCode': 'A_FTE_CAT',
        'TeachingRoleGroup': False,
    },
    'CLE': {
        'GrossSalaryFinanceCode': '630100',
        'EmployersNiFinanceCode': '630200',
        'PensionFinanceCode': '630300',
        'WeeklyFteFinanceCode': 'WK_FTE_CLE',
        'AnnualFteFinanceCode': 'A_FTE_CLE',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_CLE',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_CLE',
        'TeachingRoleGroup': False,
    },
    'PRE': {
        'GrossSalaryFinanceCode': '627100',
        'EmployersNiFinanceCode': '627200',
        'PensionFinanceCode': '627300',
        'WeeklyFteFinanceCode': 'WK_FTE_PRE',
        'AnnualFteFinanceCode': 'A_FTE_PRE',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_PRE',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_PRE',
        'TeachingRoleGroup': False,
    },
    'MDS': {
        'GrossSalaryFinanceCode': '635100',
        'EmployersNiFinanceCode': '635200',
        'PensionFinanceCode': '635300',
        'WeeklyFteFinanceCode': 'WK_FTE_MDS',
        'AnnualFteFinanceCode': 'A_FTE_MDS',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_MDS',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_MDS',
        'TeachingRoleGroup': False,
    },
    'NUR': {
        'GrossSalaryFinanceCode': '637100',
        'EmployersNiFinanceCode': '637200',
        'PensionFinanceCode': '637300',
        'WeeklyFteFinanceCode': 'WK_FTE_NUR',
        'AnnualFteFinanceCode': 'A_FTE_NUR',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_NUR',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_NUR',
        'TeachingRoleGroup': False,
    },
    'TEC': {
        'GrossSalaryFinanceCode': '622100',
        'EmployersNiFinanceCode': '622200',
        'PensionFinanceCode': '622300',
        'WeeklyFteFinanceCode': 'WK_FTE_TEC',
        'AnnualFteFinanceCode': 'A_FTE_TEC',
        'WeeklyLeaveAdjCode': 'WK_FTE_LEAVE_ADJ_TEC',
        'AnnualLeaveAdjCode': 'A_FTE_LEAVE_ADJ_TEC',
        'TeachingRoleGroup': False,
    },
    'LIB': {
        'GrossSalaryFinanceCode': '620100',
        'EmployersNiFinanceCode': '620200',
        'PensionFinanceCode': '620300',
        'WeeklyFteFinanceCode': 'WK_FTE_LIB',
        'AnnualFteFinanceCode': 'A_FTE_LIB',
        'TeachingRoleGroup': False,
    },
    'FSW': {
        'GrossSalaryFinanceCode': '640100',
        'EmployersNiFinanceCode': '640200',
        'PensionFinanceCode': '640300',
        'WeeklyFteFinanceCode': 'WK_FTE_FSW',
        'AnnualFteFinanceCode': 'A_FTE_FSW',
        'TeachingRoleGroup': False,
    },
    'COV': {
        'GrossSalaryFinanceCode': '2720',
        'EmployersNiFinanceCode': '2725',
        'PensionFinanceCode': '2730',
        'WeeklyFteFinanceCode': 'WK_FTE_COV',
        'AnnualFteFinanceCode': 'A_FTE_COV',
        'TeachingRoleGroup': False,
    },
    'COM': {
        'GrossSalaryFinanceCode': '645100',
        'EmployersNiFinanceCode': '645200',
        'PensionFinanceCode': '645300',
        'WeeklyFteFinanceCode': 'WK_FTE_COM',
        'AnnualFteFinanceCode': 'A_FTE_COM',
        'TeachingRoleGroup': False,
    },
    'OTH': {
        'GrossSalaryFinanceCode': '650400',
        'EmployersNiFinanceCode': '650410',
        'PensionFinanceCode': '650420',
        'WeeklyFteFinanceCode': 'WK_FTE_OTH',
        'AnnualFteFinanceCode': 'A_FTE_OTH',
        'TeachingRoleGroup': False,
    },
    'EDS': {
        'GrossSalaryFinanceCode': '619100',
        'EmployersNiFinanceCode': '619200',
        'PensionFinanceCode': '619300',
        'WeeklyFteFinanceCode': 'WK_FTE_EDS',
        'AnnualFteFinanceCode': 'A_FTE_EDS',
        'TeachingRoleGroup': False,
    },
    'INV': {
        'GrossSalaryFinanceCode': '642100',
        'EmployersNiFinanceCode': '642200',
        'PensionFinanceCode': '642300',
        'WeeklyFteFinanceCode': 'WK_FTE_INV',
        'AnnualFteFinanceCode': 'A_FTE_INV',
        'TeachingRoleGroup': False,
    },
}


def get_finance_codes_for_role_group(role_group: str) -> dict:
    """
    Get finance codes for a role group from XAV001 data.
    Returns empty dict if role group not found.
    """
    return STAFF_ROLE_GROUP_FINANCE_CODES.get(role_group, {})

# =============================================================================
# LOCATION VARIANTS & DEFAULT HOURS
# From S2_Data_Field_Mappings.xlsx sheet 7_Location_Hours
# =============================================================================
LOCATION_VARIANTS = {
    'EW': {'name': 'England & Wales', 'teaching_hours': 32.5, 'support_hours': 37.0, 'pay_scale_suffix': '_EW'},
    'FRI': {'name': 'Fringe', 'teaching_hours': 32.43, 'support_hours': 37.0, 'pay_scale_suffix': '_FRI'},
    'IL': {'name': 'Inner London', 'teaching_hours': 25.0, 'support_hours': 36.0, 'pay_scale_suffix': '_IL'},
    'OL': {'name': 'Outer London', 'teaching_hours': 27.5, 'support_hours': 37.5, 'pay_scale_suffix': '_OL'},
    'KEN': {'name': 'Kent', 'teaching_hours': 32.5, 'support_hours': 37.0, 'pay_scale_suffix': '_KEN'},
    'NMW': {'name': 'National Minimum Wage', 'teaching_hours': 37.0, 'support_hours': 37.0, 'pay_scale_suffix': '_NMW'},
}

# Default location when not specified
DEFAULT_LOCATION = 'EW'

# =============================================================================
# JOB TITLE TO ROLE CODE MAPPINGS
# Maps common job title keywords to (StaffRoleGroupCode, RoleCodePrefix)
# =============================================================================
JOB_TITLE_MAPPINGS = {
    # =========================================================================
    # LEADERSHIP - TEACHING (LST)
    # =========================================================================
    'headteacher': ('LST', 'HT'),
    'head teacher': ('LST', 'HT'),
    'head': ('LST', 'HT'),
    'principal': ('LST', 'HT'),
    'executive headteacher': ('LST', 'EHT'),
    'executive head': ('LST', 'EHT'),
    'exec head': ('LST', 'EHT'),
    'deputy headteacher': ('LST', 'DHT'),
    'deputy head': ('LST', 'DHT'),
    'dep head': ('LST', 'DHT'),
    'vice principal': ('LST', 'DHT'),
    'assistant headteacher': ('LST', 'AHT'),
    'assistant head': ('LST', 'AHT'),
    'asst head': ('LST', 'AHT'),

    # =========================================================================
    # LEADERSHIP - NON-TEACHING (LSN)
    # =========================================================================
    'chief executive': ('LSN', 'CEO'),
    'ceo': ('LSN', 'CEO'),
    'chief financial officer': ('LSN', 'CFO'),
    'cfo': ('LSN', 'CFO'),
    'chief operations officer': ('LSN', 'COO'),
    'coo': ('LSN', 'COO'),
    'director of finance': ('LSN', 'CFO'),
    'finance director': ('LSN', 'CFO'),
    'operations director': ('LSN', 'COO'),

    # =========================================================================
    # TEACHERS (TEA)
    # =========================================================================
    'teacher': ('TEA', 'TEA'),
    'class teacher': ('TEA', 'TEA'),
    'classroom teacher': ('TEA', 'TEA'),
    'qualified teacher': ('TEA', 'TEA'),
    'main scale teacher': ('TEA', 'TEA'),
    'upper pay scale': ('TEA', 'TEA_UPS'),
    'ups teacher': ('TEA', 'TEA_UPS'),
    'unqualified teacher': ('TEA', 'UQT'),
    'trainee teacher': ('TEA', 'UQT'),
    'lead practitioner': ('TEA', 'LP'),
    'advanced skills teacher': ('TEA', 'LP'),
    'ast': ('TEA', 'LP'),

    # =========================================================================
    # TEACHING ASSISTANTS (TA)
    # =========================================================================
    'teaching assistant': ('TA', 'TA'),
    'ta': ('TA', 'TA'),
    'classroom assistant': ('TA', 'TA'),
    'learning support assistant': ('TA', 'TA'),
    'lsa': ('TA', 'TA'),
    'higher level teaching assistant': ('TA', 'HLTA'),
    'hlta': ('TA', 'HLTA'),
    'sen teaching assistant': ('TA', 'TA'),
    'sen ta': ('TA', 'TA'),
    '1:1 support': ('TA', 'TA'),
    'one to one': ('TA', 'TA'),
    'apprentice ta': ('TA', 'APP_TA'),
    'ta apprentice': ('TA', 'APP_TA'),

    # =========================================================================
    # ADMIN & FINANCE (ADM)
    # =========================================================================
    'school business manager': ('ADM', 'SBM'),
    'sbm': ('ADM', 'SBM'),
    'business manager': ('ADM', 'SBM'),
    'office manager': ('ADM', 'ADM_MGR'),
    'admin manager': ('ADM', 'ADM_MGR'),
    'administration manager': ('ADM', 'ADM_MGR'),
    'admin assistant': ('ADM', 'ADM_AST'),
    'administration assistant': ('ADM', 'ADM_AST'),
    'administrative assistant': ('ADM', 'ADM_AST'),
    'school administrator': ('ADM', 'ADM_AST'),
    'administrator': ('ADM', 'ADM_AST'),
    'admin officer': ('ADM', 'ADM_AST'),
    'finance manager': ('ADM', 'FIN_MGR'),
    'finance officer': ('ADM', 'FIN_MGR'),
    'bursar': ('ADM', 'FIN_MGR'),
    'finance assistant': ('ADM', 'FIN_AST'),
    'accounts assistant': ('ADM', 'FIN_AST'),
    'hr manager': ('ADM', 'HR_MGR'),
    'human resources manager': ('ADM', 'HR_MGR'),
    'hr officer': ('ADM', 'HR_MGR'),
    'hr assistant': ('ADM', 'HR_AST'),
    'human resources assistant': ('ADM', 'HR_AST'),
    'receptionist': ('ADM', 'REC'),
    'reception': ('ADM', 'REC'),
    'front desk': ('ADM', 'REC'),
    'school secretary': ('ADM', 'ADM_AST'),
    'secretary': ('ADM', 'ADM_AST'),
    'clerk': ('ADM', 'ADM_AST'),
    'data manager': ('ADM', 'ADM_MGR'),
    'exams officer': ('ADM', 'ADM_AST'),
    'attendance officer': ('ADM', 'ADM_AST'),
    'apprentice admin': ('ADM', 'APP_ADM'),
    'admin apprentice': ('ADM', 'APP_ADM'),

    # =========================================================================
    # PREMISES (PRE)
    # =========================================================================
    'site manager': ('PRE', 'SITE_MGR'),
    'premises manager': ('PRE', 'SITE_MGR'),
    'facilities manager': ('PRE', 'SITE_MGR'),
    'estate manager': ('PRE', 'SITE_MGR'),
    'site assistant': ('PRE', 'SITE_AST'),
    'premises assistant': ('PRE', 'SITE_AST'),
    'caretaker': ('PRE', 'CT'),
    'janitor': ('PRE', 'CT'),
    'assistant caretaker': ('PRE', 'AST_CT'),
    'groundsman': ('PRE', 'SITE_AST'),
    'groundskeeper': ('PRE', 'SITE_AST'),
    'maintenance': ('PRE', 'SITE_AST'),

    # =========================================================================
    # CATERING (CAT)
    # =========================================================================
    'catering manager': ('CAT', 'CAT_MGR'),
    'kitchen manager': ('CAT', 'CAT_MGR'),
    'head cook': ('CAT', 'CAT_MGR'),
    'chef': ('CAT', 'CAT_MGR'),
    'head chef': ('CAT', 'CAT_MGR'),
    'catering assistant': ('CAT', 'CAT_AST'),
    'kitchen assistant': ('CAT', 'CAT_AST'),
    'cook': ('CAT', 'CAT_AST'),
    'dinner lady': ('CAT', 'CAT_AST'),
    'food service': ('CAT', 'CAT_AST'),

    # =========================================================================
    # CLEANING (CLE)
    # =========================================================================
    'cleaner': ('CLE', 'CLE'),
    'cleaning staff': ('CLE', 'CLE'),
    'domestic': ('CLE', 'CLE'),
    'housekeeping': ('CLE', 'CLE'),

    # =========================================================================
    # MIDDAY SUPERVISORS (MDS)
    # =========================================================================
    'midday supervisor': ('MDS', 'MDS'),
    'midday assistant': ('MDS', 'MDS'),
    'lunchtime supervisor': ('MDS', 'MDS'),
    'lunch supervisor': ('MDS', 'MDS'),
    'mds': ('MDS', 'MDS'),
    'playground supervisor': ('MDS', 'MDS'),

    # =========================================================================
    # NURSERY (NUR)
    # =========================================================================
    'nursery manager': ('NUR', 'NUR_MGR'),
    'nursery nurse': ('NUR', 'NUR_NUR'),
    'nursery assistant': ('NUR', 'NUR_NUR'),
    'early years practitioner': ('NUR', 'NUR_NUR'),
    'eyp': ('NUR', 'NUR_NUR'),
    'early years': ('NUR', 'NUR_NUR'),

    # =========================================================================
    # TECHNICIANS (TEC)
    # =========================================================================
    'technician': ('TEC', 'TEC'),
    'ict technician': ('TEC', 'TEC'),
    'it technician': ('TEC', 'TEC'),
    'science technician': ('TEC', 'TEC'),
    'lab technician': ('TEC', 'TEC'),
    'network manager': ('TEC', 'TEC'),
    'it support': ('TEC', 'TEC'),
    'technical support': ('TEC', 'TEC'),

    # =========================================================================
    # LIBRARIAN (LIB)
    # =========================================================================
    'librarian': ('LIB', 'LIB'),
    'library assistant': ('LIB', 'LIB'),
    'library manager': ('LIB', 'LIB'),

    # =========================================================================
    # FAMILY SUPPORT (FSW)
    # =========================================================================
    'family support worker': ('FSW', 'FSW'),
    'family liaison': ('FSW', 'FSW'),
    'pastoral support': ('FSW', 'FSW'),
    'welfare officer': ('FSW', 'FSW'),
    'home school liaison': ('FSW', 'FSW'),
    'safeguarding': ('FSW', 'FSW'),

    # =========================================================================
    # COVER SUPERVISORS (COV)
    # =========================================================================
    'cover supervisor': ('COV', 'COV_SUP'),
    'cover manager': ('COV', 'COV_SUP'),
    'supply cover': ('COV', 'COV_SUP'),

    # =========================================================================
    # COMMUNITY / BEFORE & AFTER SCHOOL (COM)
    # =========================================================================
    'before and after school': ('COM', 'BASC'),
    'breakfast club': ('COM', 'BASC'),
    'after school club': ('COM', 'BASC'),
    'wrap around care': ('COM', 'BASC'),
    'extended services': ('COM', 'BASC'),

    # =========================================================================
    # EXTERNAL STAFF (ESTF)
    # =========================================================================
    'sports coach': ('ESTF_SPO', 'ESTF_SPO'),
    'pe coach': ('ESTF_SPO', 'ESTF_SPO'),
    'external sports': ('ESTF_SPO', 'ESTF_SPO'),
    'agency teacher': ('ESTF_TEA', 'ESTF_TEA'),
    'supply teacher': ('ESTF_TEA', 'ESTF_TEA'),
    'external teacher': ('ESTF_TEA', 'ESTF_TEA'),

    # =========================================================================
    # OTHER (OTH) - Catch-all
    # =========================================================================
    'other': ('OTH', 'OTH'),
    'staff': ('OTH', 'OTH'),
}

# =============================================================================
# PAY SCALE MAPPINGS BY ROLE GROUP
# =============================================================================
PAY_SCALE_BY_ROLE_GROUP = {
    # Teaching roles use teaching pay scales
    'LST': {'EW': 'LS_EW', 'FRI': 'LS_FRI', 'IL': 'LS_IL', 'OL': 'LS_OL'},
    'LSN': {'EW': 'LS_EW', 'FRI': 'LS_FRI', 'IL': 'LS_IL', 'OL': 'LS_OL'},
    'TEA': {'EW': 'MAIN_EW', 'FRI': 'MAIN_FRI', 'IL': 'MAIN_IL', 'OL': 'MAIN_OL'},

    # Support roles use NJC pay scales
    'ADM': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'TA': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'CAT': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'CLE': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'PRE': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'MDS': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'NUR': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'TEC': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'LIB': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'FSW': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'COV': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'COM': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},
    'OTH': {'EW': 'NJC_EW', 'FRI': 'NJC_FRI', 'IL': 'NJC_IL', 'OL': 'NJC_OL', 'KEN': 'KENT'},

    # External staff
    'ESTF_SPO': {'default': 'ESTF'},
    'ESTF_TEA': {'default': 'ESTF'},
}

# =============================================================================
# DEPARTMENT CODE MAPPINGS BY ROLE GROUP
# From S2_Data_Field_Mappings.xlsx sheet 6_Department_Codes
# =============================================================================
DEPARTMENT_BY_ROLE_GROUP = {
    'LST': 'SAL_LST',      # Leadership Teaching
    'LSN': 'SAL_LST',      # Leadership Non-Teaching (often same dept)
    'SLT': 'SAL_LST',      # Senior Leadership
    'TEA': 'SAL_TEA',      # Teachers
    'TA': 'SAL_TA',        # Teaching Assistants
    'ADM': 'SAL_ADM',      # Admin
    'CAT': 'SAL_CAT',      # Catering
    'CLE': 'SAL_CLE',      # Cleaning
    'PRE': 'SAL_PRE',      # Premises
    'MDS': 'SAL_MDS',      # Midday Supervisors
    'NUR': 'SAL_NUR',      # Nursery
    'TEC': 'SAL_TEC',      # Technicians
    'LIB': 'SAL_LIB',      # Librarians
    'FSW': 'SAL_FSW',      # Family Support
    'COV': 'SAL_COV',      # Cover Supervisors
    'COM': 'SAL_COM',      # Community
    'OTH': 'SAL_OTH',      # Other
    'EDS': 'SAL_EDS',      # Educational Support
    'ESTF': 'SAL_EXT',     # External Staff
    'ESTF_SPO': 'SAL_EXT', # External Staff - Sports
    'ESTF_TEA': 'SAL_EXT', # External Staff - Teaching
}

# =============================================================================
# FULL-TIME HOURS BY ROLE TYPE
# =============================================================================
HOURS_BY_ROLE_TYPE = {
    # Teaching staff - varies by location
    'teaching': {
        'EW': 32.5,
        'FRI': 32.43,
        'IL': 25.0,
        'OL': 27.5,
    },
    # Support staff - varies by location
    'support': {
        'EW': 37.0,
        'FRI': 37.0,
        'IL': 36.0,
        'OL': 37.5,
        'KEN': 37.0,
    },
}

# Note: TEACHING_ROLE_GROUPS and SUPPORT_ROLE_GROUPS defined at top of file


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_role_group_from_title(job_title: str) -> tuple:
    """
    Get the StaffRoleGroupCode and RoleCodePrefix from a job title.

    Args:
        job_title: The job title to look up (e.g., "Teaching Assistant", "Headteacher")

    Returns:
        Tuple of (StaffRoleGroupCode, RoleCodePrefix) or ('OTH', 'OTH') if not found
    """
    if not job_title:
        return ('OTH', 'OTH')

    title_lower = job_title.lower().strip()

    # Try exact match first
    if title_lower in JOB_TITLE_MAPPINGS:
        return JOB_TITLE_MAPPINGS[title_lower]

    # Try partial match (check if any keyword is in the title)
    for keyword, mapping in JOB_TITLE_MAPPINGS.items():
        if keyword in title_lower:
            return mapping

    # Default to Other
    return ('OTH', 'OTH')


def build_staff_role_code(job_title: str, location: str = 'EW', hours: float = None) -> str:
    """
    Build the full StaffRoleCode from job title and location.

    Args:
        job_title: The job title (e.g., "Teaching Assistant")
        location: Location code (EW, FRI, IL, OL, KEN)
        hours: Override hours (uses default if not specified)

    Returns:
        Full StaffRoleCode (e.g., "TA_37_EW")
    """
    role_group, role_prefix = get_role_group_from_title(job_title)

    # Determine hours based on role type
    if hours is None:
        if role_group in TEACHING_ROLE_GROUPS:
            hours = HOURS_BY_ROLE_TYPE['teaching'].get(location, 32.5)
        else:
            hours = HOURS_BY_ROLE_TYPE['support'].get(location, 37.0)

    # Format hours (remove .0 if whole number)
    hours_str = str(hours) if hours % 1 != 0 else str(int(hours))

    # Build the code
    return f"{role_prefix}_{hours_str}_{location}"


def get_pay_scale_for_role(role_group: str, location: str = 'EW') -> str:
    """
    Get the appropriate pay scale code for a role group and location.

    Args:
        role_group: StaffRoleGroupCode (e.g., 'TEA', 'TA', 'ADM')
        location: Location code (EW, FRI, IL, OL, KEN)

    Returns:
        PayScaleCode (e.g., 'MAIN_EW', 'NJC_EW')
    """
    scales = PAY_SCALE_BY_ROLE_GROUP.get(role_group, {})
    return scales.get(location, scales.get('default', 'NJC_EW'))


def get_department_for_role(role_group: str) -> str:
    """
    Get the department code for a role group.

    Args:
        role_group: StaffRoleGroupCode (e.g., 'TEA', 'TA', 'ADM')

    Returns:
        DepartmentCode (e.g., 'SAL_TEA', 'SAL_TA')
    """
    return DEPARTMENT_BY_ROLE_GROUP.get(role_group, 'SAL_OTH')


def is_teaching_role(role_group: str) -> bool:
    """Check if a role group is a teaching role (uses teaching pay scales)."""
    return role_group in TEACHING_ROLE_GROUPS


def get_all_role_codes_for_job(job_title: str) -> list:
    """
    Get all possible StaffRoleCodes for a job title across all locations.

    Args:
        job_title: The job title (e.g., "Teaching Assistant")

    Returns:
        List of all possible role codes for different locations
    """
    role_group, role_prefix = get_role_group_from_title(job_title)
    codes = []

    if role_group in TEACHING_ROLE_GROUPS:
        for loc, hours in HOURS_BY_ROLE_TYPE['teaching'].items():
            hours_str = str(hours) if hours % 1 != 0 else str(int(hours))
            codes.append(f"{role_prefix}_{hours_str}_{loc}")
    else:
        for loc, hours in HOURS_BY_ROLE_TYPE['support'].items():
            hours_str = str(hours) if hours % 1 != 0 else str(int(hours))
            codes.append(f"{role_prefix}_{hours_str}_{loc}")

    return codes


# =============================================================================
# KEYWORD PRIORITY ORDER (for matching)
# =============================================================================
# When multiple keywords could match, longer/more specific ones should win
KEYWORD_PRIORITY = [
    # Most specific first
    'executive headteacher', 'deputy headteacher', 'assistant headteacher',
    'higher level teaching assistant', 'senior teaching assistant',
    'school business manager', 'finance manager', 'admin manager', 'hr manager',
    'site manager', 'catering manager', 'nursery manager',
    'chief executive', 'chief financial officer', 'chief operations officer',
    'lead practitioner', 'unqualified teacher', 'cover supervisor',
    'family support worker', 'midday supervisor',
    # Then less specific
    'headteacher', 'teacher', 'teaching assistant', 'receptionist',
    'cleaner', 'caretaker', 'librarian', 'technician',
    # Generic last
    'assistant', 'manager', 'staff',
]


# =============================================================================
# CROSS-REFERENCE HELPER - CHECK OTHER KNOWLEDGE SOURCES
# =============================================================================

def lookup_with_fallback(job_title: str, field: str = 'role_group') -> tuple:
    """
    Look up staff data with fallback to other knowledge sources.
    Returns (value, source, is_assumption) tuple.

    Args:
        job_title: The job title to look up
        field: What to look up ('role_group', 'finance_code', 'pay_scale', 'department')

    Returns:
        Tuple of (value, source_name, is_assumption)
        - value: The looked up value
        - source_name: Where the data came from ('XAV001', 'IMPORT_FILES', 'DOMAIN_KNOWLEDGE', 'ASSUMPTION')
        - is_assumption: True if this is an assumption, False if from known data
    """
    # Try this knowledge base first (XAV001 data)
    role_group, role_prefix = get_role_group_from_title(job_title)

    if field == 'role_group':
        if role_group != 'OTH' or job_title.lower() == 'other':
            return (role_group, 'XAV001_STAFF_ROLE_MAPPINGS', False)
        else:
            # Not found - this is an assumption
            return ('OTH', 'ASSUMPTION', True)

    elif field == 'finance_code':
        # Finance codes should come from actual data in staff contract tabs
        # Check XAV001 - StaffRoleGroups.csv first (this is known data)
        finance_codes = STAFF_ROLE_GROUP_FINANCE_CODES.get(role_group)
        if finance_codes:
            return (finance_codes, 'XAV001_STAFF_ROLE_GROUPS', False)

        # Try domain knowledge as secondary source
        try:
            from knowledge.S2.S2_DOMAIN_KNOWLEDGE import STAFF_ROLE_GROUPS as DOMAIN_SRG
            if role_group in DOMAIN_SRG:
                return (DOMAIN_SRG[role_group], 'S2_DOMAIN_KNOWLEDGE', False)
        except ImportError:
            pass

        # IMPORTANT: Do not assume finance codes - they must come from actual data
        # Return empty and flag as needing data from contract tabs
        return ({}, 'NEEDS_DATA_FROM_CONTRACT_TABS', True)

    elif field == 'pay_scale':
        pay_scale = PAY_SCALE_BY_ROLE_GROUP.get(role_group, {})
        if pay_scale:
            return (pay_scale, 'XAV001_STAFF_ROLE_MAPPINGS', False)

        # Try domain knowledge
        try:
            from knowledge.S2.S2_DOMAIN_KNOWLEDGE import PAY_SCALES as DOMAIN_PS
            # Search for matching pay scale
            for code, data in DOMAIN_PS.items():
                if data.get('teaching') == is_teaching_role(role_group):
                    return ({role_group: code}, 'S2_DOMAIN_KNOWLEDGE', False)
        except ImportError:
            pass

        return ({}, 'ASSUMPTION', True)

    elif field == 'department':
        dept = DEPARTMENT_BY_ROLE_GROUP.get(role_group)
        if dept:
            return (dept, 'XAV001_STAFF_ROLE_MAPPINGS', False)
        return ('SAL_OTH', 'ASSUMPTION', True)

    return (None, 'UNKNOWN', True)


def get_complete_staff_info(job_title: str, location: str = 'EW') -> dict:
    """
    Get complete staff information with source tracking.
    Flags any assumptions made.

    Args:
        job_title: The job title (e.g., "Teaching Assistant")
        location: Location code (EW, FRI, IL, OL)

    Returns:
        Dictionary with staff info and assumption flags
    """
    result = {
        'job_title': job_title,
        'location': location,
        'assumptions': [],
        'sources': [],
    }

    # Role Group
    role_group, source, is_assumption = lookup_with_fallback(job_title, 'role_group')
    result['role_group'] = role_group
    result['sources'].append(f"role_group: {source}")
    if is_assumption:
        result['assumptions'].append(f"Role group '{role_group}' is an assumption - job title '{job_title}' not found in knowledge")

    # Get role prefix
    _, role_prefix = get_role_group_from_title(job_title)
    result['role_prefix'] = role_prefix

    # Build role code
    result['role_code'] = build_staff_role_code(job_title, location)

    # Finance codes
    finance_codes, source, is_assumption = lookup_with_fallback(job_title, 'finance_code')
    result['finance_codes'] = finance_codes
    result['sources'].append(f"finance_codes: {source}")
    if is_assumption:
        result['assumptions'].append(f"Finance codes not found in knowledge for role group '{role_group}'")

    # Pay scale
    pay_scale_info, source, is_assumption = lookup_with_fallback(job_title, 'pay_scale')
    pay_scale = pay_scale_info.get(location) or pay_scale_info.get('default', '')
    result['pay_scale'] = pay_scale
    result['sources'].append(f"pay_scale: {source}")
    if is_assumption:
        result['assumptions'].append(f"Pay scale is an assumption for role group '{role_group}'")

    # Department
    dept, source, is_assumption = lookup_with_fallback(job_title, 'department')
    result['department'] = dept
    result['sources'].append(f"department: {source}")
    if is_assumption:
        result['assumptions'].append(f"Department '{dept}' is an assumption for role group '{role_group}'")

    # Teaching flag
    result['is_teaching'] = is_teaching_role(role_group)

    return result
