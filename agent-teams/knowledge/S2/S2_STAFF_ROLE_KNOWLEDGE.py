"""
S2 Staff Role Coding Knowledge
Generated from: S2 Coding - SRGs and Staff Roles.xlsx

This module provides the official staff role codes and staff role group codes
that the S2 agent uses when customer data does not include these codes.

The S2 agent MUST use this knowledge to:
1. Generate StaffRoleCode from job title when not provided
2. Generate StaffRoleGroupCode from role when not provided
3. Validate existing codes against official list
"""

# =============================================================================
# STAFF ROLE GROUPS (59 codes)
# Maps group code to (title, weekly_fte_code, annual_fte_code)
# =============================================================================
STAFF_ROLE_GROUPS = {
    "ADM": ("Staff Costs - Finance and Admin-Wages and salaries", "WK_FTE_ADM", "A_FTE_ADM"),
    "APP": ("Staff Costs - Apprentice Staff-Wages and salaries", "WK_FTE_APP", "A_FTE_APP"),
    "ASC": ("Staff Costs - After School Club Staff-Wages and salaries", "WK_FTE_ASC", "A_FTE_ASC"),
    "BFC": ("Staff Costs - Breakfast Club Staff-Wages and salaries", "WK_FTE_BFC", "A_FTE_BFC"),
    "BRD_DIR": ("Staff Costs - Boarding Staff - Direct-Wages and salaries", "WK_FTE_BRD_DIR", "A_FTE_BRD_DIR"),
    "BRD_IND": ("Staff Costs - Boarding Staff - Indirect-Wages and salaries", "WK_FTE_BRD_IND", "A_FTE_BRD_IND"),
    "CAT": ("Staff Costs - Catering Staff-Wages and salaries", "WK_FTE_CAT", "A_FTE_CAT"),
    "CEN": ("Staff Costs - Central Staff-Wages and salaries", "WK_FTE_CEN", "A_FTE_CEN"),
    "CLE": ("Staff Costs - Cleaning Staff-Wages and salaries", "WK_FTE_CLE", "A_FTE_CLE"),
    "COM": ("Staff Costs - Community Facilities Staff-Wages and salaries", "WK_FTE_COM", "A_FTE_COM"),
    "COV": ("Staff Costs - Cover Supervisors-Wages and salaries", "WK_FTE_COV", "A_FTE_COV"),
    "CT": ("Staff Costs - Caretaker-Wages and salaries", "WK_FTE_CT", "A_FTE_CT"),
    "CUR": ("Staff Costs - Curriculum Support-Wages and salaries", "WK_FTE_CUR", "A_FTE_CUR"),
    "DEV": ("Staff Costs - Development Staff-Wages and salaries", "WK_FTE_DEV", "A_FTE_DEV"),
    "DRI": ("Staff Costs - Drivers-Wages and salaries", "WK_FTE_DRI", "A_FTE_DRI"),
    "EDS": ("Staff Costs - Education Support-Wages and salaries", "WK_FTE_EDS", "A_FTE_EDS"),
    "EST": ("Staff Costs - Estates & Buildings Staff-Wages and salaries", "WK_FTE_EST", "A_FTE_EST"),
    "EXA": ("Staff Costs - Exam Staff-Wages and salaries", "WK_FTE_EXA", "A_FTE_EXA"),
    "EXT": ("Staff Costs - Extended Schools Staff-Wages and salaries", "WK_FTE_EXT", "A_FTE_EXT"),
    "FIN": ("Staff Costs - Finance Staff-Wages and salaries", "WK_FTE_FIN", "A_FTE_FIN"),
    "FLA": ("Staff Costs - Foreign Language Assistants-Wages and salaries", "WK_FTE_FLA", "A_FTE_FLA"),
    "FSW": ("Staff Costs - Family Support Workers-Wages and salaries", "WK_FTE_FSW", "A_FTE_FSW"),
    "GOV": ("Staff Costs - Governance Staff-Wages and salaries", "WK_FTE_GOV", "A_FTE_GOV"),
    "HLTA": ("Staff Costs - Higher Level Teaching Assistants-Wages and salaries", "WK_FTE_HLTA", "A_FTE_HLTA"),
    "HR": ("Staff Costs - HR Staff-Wages and salaries", "WK_FTE_HR", "A_FTE_HR"),
    "INC": ("Staff Costs - Inclusion Staff-Wages and salaries", "WK_FTE_INC", "A_FTE_INC"),
    "INV": ("Staff Costs - Exam Invigilators-Wages and salaries", "WK_FTE_INV", "A_FTE_INV"),
    "IT": ("Staff Costs - IT Staff-Wages and salaries", "WK_FTE_IT", "A_FTE_IT"),
    "LIB": ("Staff Costs - Librarians-Wages and salaries", "WK_FTE_LIB", "A_FTE_LIB"),
    "LM": ("Staff Costs - Learning Mentors-Wages and salaries", "WK_FTE_LM", "A_FTE_LM"),
    "LSA": ("Staff Costs - Learning Support Assistants-Wages and salaries", "WK_FTE_LSA", "A_FTE_LSA"),
    "LSN": ("Staff Costs - Leadership Non-Teaching-Wages and salaries", "WK_FTE_LSN", "A_FTE_LSN"),
    "LST": ("Staff Costs - Leadership Teaching-Wages and salaries", "WK_FTE_LST", "A_FTE_LST"),
    "LTS": ("Staff Costs - Lunchtime Supervisors-Wages and salaries", "WK_FTE_LTS", "A_FTE_LTS"),
    "MAR": ("Staff Costs - Marketing Staff-Wages and salaries", "WK_FTE_MAR", "A_FTE_MAR"),
    "MDS": ("Staff Costs - Midday Supervisors-Wages and salaries", "WK_FTE_MDS", "A_FTE_MDS"),
    "MUS": ("Staff Costs - Music Staff-Wages and salaries", "WK_FTE_MUS", "A_FTE_MUS"),
    "NUR": ("Staff Costs - Nursery Staff-Wages and salaries", "WK_FTE_NUR", "A_FTE_NUR"),
    "OTH": ("Staff Costs - Other Staff-Wages and salaries", "WK_FTE_OTH", "A_FTE_OTH"),
    "OTH_DIR": ("Staff Costs - Other Staff Direct Costs-Wages and salaries", "WK_FTE_OTH_DIR", "A_FTE_OTH_DIR"),
    "OUT": ("Staff Costs - Outreach Staff-Wages and salaries", "WK_FTE_OUT", "A_FTE_OUT"),
    "PAS": ("Staff Costs - Pastoral Staff-Wages and salaries", "WK_FTE_PAS", "A_FTE_PAS"),
    "PERI": ("Staff Costs - Peri Music Staff-Wages and salaries", "WK_FTE_PERI", "A_FTE_PERI"),
    "PRE": ("Staff Costs - Site Staff-Wages and salaries", "WK_FTE_PRE", "A_FTE_PRE"),
    "PS": ("Staff Costs - Pupil Support-Wages and salaries", "WK_FTE_PS", "A_FTE_PS"),
    "SC": ("Staff Costs - Sports Coach-Wages and salaries", "WK_FTE_SC", "A_FTE_SC"),
    "SCITT": ("Staff Costs - SCITT Staff-Wages and salaries", "WK_FTE_SCITT", "A_FTE_SCITT"),
    "SLT": ("Staff Costs - SLT-Wages and salaries", "WK_FTE_SLT", "A_FTE_SLT"),
    "SPO": ("Staff Costs - Sports Staff-Wages and salaries", "WK_FTE_SPO", "A_FTE_SPO"),
    "SSUP": ("Staff Costs - Supply Support Staff-Wages and salaries", "WK_FTE_SSUP", "A_FTE_SSUP"),
    "STA": ("Staff Costs - Supply Teaching Assistants-Wages and salaries", "WK_FTE_STA", "A_FTE_STA"),
    "STEA_LT": ("Staff Costs - Supply Teachers - Long Term-Wages and salaries", "WK_FTE_STEA_LT", "A_FTE_STEA_LT"),
    "STEA_ST": ("Staff Costs - Supply Teachers - Short Term-Wages and salaries", "WK_FTE_STEA_ST", "A_FTE_STEA_ST"),
    "TA": ("Staff Costs - Teaching Assistants-Wages and salaries", "WK_FTE_TA", "A_FTE_TA"),
    "TEA": ("Staff Costs - Teachers-Wages and salaries", "WK_FTE_TEA", "A_FTE_TEA"),
    "TEC": ("Staff Costs - Technicians-Wages and salaries", "WK_FTE_TEC", "A_FTE_TEC"),
    "TUT": ("Staff Costs - Home Tutors-Wages and salaries", "WK_FTE_TUT", "A_FTE_TUT"),
    "WAC": ("Staff Costs - Wrap Around Care-Wages and salaries", "WK_FTE_WAC", "A_FTE_WAC"),
    "WEL": ("Staff Costs - Wellbeing Staff-Wages and salaries", "WK_FTE_WEL", "A_FTE_WEL"),
}

# =============================================================================
# STAFF ROLES (363 codes)
# Maps role code to title
# =============================================================================
STAFF_ROLES = {
    "HT": "Headteacher",
    "DHT": "Deputy Headteacher",
    "AHT": "Assistant Headteacher",
    "EHT": "Executive Headteacher",
    "CEO": "Chief Executive Officer",
    "COO": "Chief Operations Officer",
    "CFO": "Chief Financial Officer",
    "TEA": "Teacher",
    "UQT": "Unqualified Teacher",
    "TA": "Teaching Assistant",
    "HLTA": "Higher Level Teaching Assistant",
    "LIB": "Librarian",
    "SBM": "School Business Manager",
    "FIN_MGR": "Finance Manager",
    "FIN_AST": "Finance Assistant",
    "HR_MGR": "HR Manager",
    "HR_AST": "HR Assistant",
    "ADM_MGR": "Admin Manager",
    "ADM_AST": "Admin Assistant",
    "REC": "Receptionist",
    "CT": "Caretaker",
    "SITE_MGR": "Site Manager",
    "SITE_AST": "Site Assistant",
    "CLE": "Cleaner",
    "CAT_MGR": "Catering Manager",
    "CAT_AST": "Catering Assistant",
    "MDS": "Midday Supervisor",
    "NUR_MGR": "Nursery Manager",
    "NUR_NUR": "Nursery Nurse",
    "FSW": "Family Support Worker",
    "INV": "Exam Invigilators",
    "EXT": "Extended Schools",
    "OTH": "Other Staff",
    "HOD": "Head of Department",
    "SUB_LDR": "Subject Leader",
    "MUS_TUT": "Music Tutor",
    "ADM": "Administrator",
    "CLER_GOV": "Clerk to the Governors",
    "COM_MAR_OFF": "Communications & Marketing Officer",
    "DATA_MGR": "Data Manager",
    "EXA_OFF": "Exams Officer",
    "FIN_ADM": "Finance Administrator",
    "FIN_OFF": "Finance Officer",
    "OFF_MGR": "Office Manager",
    "PAS_SUP_MGR": "Pastoral Support Manager",
    "COV_SUP": "Cover Supervisor",
    "FLA": "Foreign Language Assistant",
    "LRC_CO": "Learning Resource Centre Coordinator",
    "SITE_MGR_AST": "Assistant Site Manager",
    "SITE_OP": "Site Operative",
    "IT_NET_MGR": "IT Network Manager",
    "TEC_SNR": "Senior Technician",
    "TEC": "Technician",
    "AP": "Assistant Principal",
    "VP": "Vice Principal",
    "SVP": "Senior Vice Principal",
    "DIR_EDU": "Director of Education",
    "HO_GOV": "Head of Governance",
    "OP_MGR": "Operations Manager",
    "FAC_LDR": "Faculty Leader",
    "HOF": "Head of Faculty",
    "LP": "Lead Practitioner",
    "LST": "Leadership Teacher",
    "ADM_OFF": "Admin Officer",
    "ATT_OFF": "Attendance Officer",
    "CAR_OFF": "Careers Officer",
    "COM_MGR": "Compliance Manager",
    "HR_OFF": "HR Officer",
    "MUS_ADM": "Music Admin",
    "PAY_MGR": "Payroll Manager",
    "PA": "Personal Assistant",
    "PRO_LD": "Project Lead",
    "REP_AST": "Reprographics Assistant",
    "RES_AST": "Resources Assistant",
    "RES_MGR": "Resources Manager",
    "SFG_MGR": "Safeguarding Manager",
    "SFG_OFF": "Safeguarding Officer",
    "ADM_AST_SNR": "Senior Admin Assistant",
    "ADM_SNR": "Senior Administrator",
    "LIB_AST": "Library Assistant",
    "LIB_MGR": "Library Manager",
    "SENCO_AST": "Assistant SENCO",
    "BEH_INC_MGR": "Behaviour & Inclusion Manager",
    "BEH_OFF": "Behaviour Officer",
    "COU": "Counsellor",
    "ELSA": "Emotional Literacy Support Assistant",
    "INC_OFF": "Inclusion Officer",
    "INC_SUP": "Inclusion Support",
    "LM": "Learning Mentor",
    "LSA": "Learning Support Assistant",
    "PAS_MGR": "Pastoral Manager",
    "PAS_MEN": "Pastoral Mentor",
    "PAS_OFF": "Pastoral Officer",
    "PAS_MGR_SNR": "Senior Pastoral Manager",
    "COV_AST": "Cover Assistant",
    "COV_COA": "Cover Coach",
    "COV_TEA": "Cover Teacher",
    "SITE_MGR_DEP": "Deputy Site Manager",
    "EST_MGR": "Estates Manager",
    "SITE_STF": "Site Staff",
    "CAR_ADV": "Careers Advisor",
    "CAR_LD": "Careers Lead",
    "COV_MGR": "Cover Manager",
    "EXA_AST": "Exams Assistant",
    "MED_OFF": "Medical Officer",
    "THEA_MGR": "Theatre Manager",
    "BEH_SUP": "Behaviour Support",
    "OTH_DIR": "Other Staff - Support Costs",
    "PRI": "Principal",
    "SAP": "Senior Assistant Principal",
    "CFOO": "Chief Finance & Operations Officer",
    "HO_FIN_EST": "Head of Finance & Estates",
    "SIP": "School Improvement Partner",
    "PRO_LDR": "Progress Leader",
    "CUR_LDR_AST": "Assistant Curriculum Leader",
    "CUR_LDR": "Curriculum Leader",
    "EYFS_LD": "EYFS Lead",
    "NUR_AST": "Nursery Assistant",
    "INC_MGR_AST": "Assistant Inclusion Manager",
    "COM_ADM": "Communications Administrator",
    "DSL": "Designated Safeguarding Lead",
    "DSO": "Designated Support Officer",
    "ENR_CO": "Enrichment Coordinator",
    "EXA_MGR": "Exams Manager",
    "PSO": "Pastoral Support Officer",
    "ASC_AST": "After School Club Assistant",
    "BFC_AST": "Breakfast Club Assistant",
    "BFC_SUP": "Breakfast Club Supervisor",
    "EXT_AST": "Extended Schools Assistant",
    "EXT_SUP": "Extended Schools Supervisor",
    "PLAY_WRK": "Play Worker",
    "EXEC_AST": "Executive Assistant",
    "HR_ADV": "HR Advisor",
    "PAY_OFF": "Payroll Officer",
    "REP_TEC": "Reprographics Technician",
    "FIN_OFF_SNR": "Senior Finance Officer",
    "COOK_AST": "Assistant Cook",
    "COOK_SNR": "Senior Cook",
    "LTA": "Lunchtime Assistant",
    "LTS": "Lunchtime Supervisor",
    "LTS_SNR": "Senior Lunchtime Supervisor",
    "FAC_AST": "Facilities Assistant",
    "FAC_MGR": "Facilities Manager",
    "CT_SNR": "Senior Caretaker",
    "FAC_AST_SNR": "Senior Facilities Assistant",
    "SITE_SUP": "Site Supervisor",
    "CLE_SNR": "Senior Cleaner",
    "EP": "Executive Principal",
    "AVP": "Assistant Vice Principal",
    "STR_DIR": "Strategic Director",
    "AHOF": "Assistant Head of Faculty",
    "YR_LDR": "Year Leader",
    "ATT_AST": "Attendance Assistant",
    "CPO": "Chief People Officer",
    "CSO": "Chief Safeguarding Officer",
    "DATA_LDR": "Data Leader",
    "GOV_LDR": "Governance Leader",
    "TA_APP": "Apprentice Teaching Assistant",
    "SBO": "School Business Officer",
    "EWO": "Education Welfare Officer",
    "INC_MGR": "Inclusion Manager",
    "INC_TL": "Inclusion Team Leader",
    "LEA_PRO_MGR": "Learning Progress Manager",
    "LEA_PRO_OFF": "Learning Progress Officer",
    "LIT_CO": "Literacy Coordinator",
    "NET_MGR": "Network Manager",
    "PAS_LDR": "Pastoral Leader",
    "SSL": "Student Support Lead",
    "SWO": "Student Welfare Officer",
    "SYS_ADM": "Systems Administrator",
    "BM": "Business Manager",
    "ASC_LDR": "After School Club Leader",
    "DIR_HR": "Director of HR",
    "DIR_INC": "Director of Inclusion",
    "DIR_SFG": "Director of Safeguarding",
    "SITE_OFF": "Site Officer",
    "FLO": "Family Liaison Officer",
    "SALT": "Speech & Language Therapist",
    "DDSL": "Deputy Designated Safeguarding Lead",
    "HR_DIR": "HR Director",
    "IT_SUP_LD": "IT Support Lead",
    "IT_TEC": "IT Technician",
    "OP_OFF": "Operations Officer",
    "FSA": "Family Support Assistant",
    "PLO": "Parent Liaison Officer",
    "CHAP": "Chaplain",
    "BFC_LDR": "Breakfast Club Leader",
    "BFC_MGR": "Breakfast Club Manager",
    "ASC_MGR": "After School Club Manager",
    "ASC_SUP": "After School Club Supervisor",
    "OOS_AST": "Out of School Assistant",
    "OOS_SUP": "Out of School Supervisor",
    "OOS_LDR": "Out of School Leader",
    "OOS_MGR": "Out of School Manager",
    "OOS_CO": "Out of School Coordinator",
    "ACAD_MEN": "Academic Mentor",
    "ADM_LDR": "Admin Leader",
    "ADM_CO": "Admin Coordinator",
    "ATT_MGR": "Attendance Manager",
    "CHEF_AST": "Assistant Chef",
    "CHEF": "Chef",
    "BSO": "Behaviour Support Officer",
    "DATA_OFF": "Data Officer",
    "DATA_ADM": "Data Administrator",
    "DATA_ENG": "Data Engineer",
    "DATA_CO": "Data Coordinator",
    "DIR_CUR": "Director of Curriculum",
    "DIR_GOV": "Director of Governance",
    "DIR_IT": "Director of IT",
    "DIR_SUB": "Subject Director",
    "DIR_PRI_EDU": "Director of Primary Education",
    "DIR_SEC_EDU": "Director of Secondary Education",
    "EAL_CO": "EAL Coordinator",
    "EAL_LD": "EAL Lead",
    "EYP": "Early Years Practitioner",
    "EST_OFF": "Estates Officer",
    "EXA_CO": "Exams Coordinator",
    "EXA_LD": "Exams Lead",
    "FEL": "Family Engagement Lead",
    "DIR_FIN": "Director of Finance",
    "GOV_MGR": "Governance Manager",
    "GOV_OFF": "Governance Officer",
    "HOS": "Head of School",
    "HK": "Housekeeper",
    "INC_ADM": "Inclusion Administrator",
    "INC_CO": "Inclusion Coordinator",
    "INC_LD": "Inclusion Lead",
    "INT_LD": "Intervention Lead",
    "LIB_CO": "Library Coordinator",
    "MAIN_OFF": "Maintenance Officer",
    "MAN_ACC": "Management Accountant",
    "NUR_APP": "Nursery Apprentice",
    "NUR_PRA": "Nursery Practitioner",
    "NUR_SUP": "Nursery Supervisor",
    "OFF_AST": "Office Assistant",
    "OFF_CO": "Office Coordinator",
    "DIR_OP": "Director of Operations",
    "PAS_CO": "Pastoral Coordinator",
    "PRE_AST": "Premises Assistant",
    "PRE_MGR": "Premises Manager",
    "PRE_OFF": "Premises Officer",
    "PRE_SUP": "Premises Supervisor",
    "REP_CO": "Reprographics Coordinator",
    "REP_OFF": "Reprographics Officer",
    "RM_LDR": "Room Leader",
    "RM_MGR": "Room Manager",
    "RM_CO": "Room Coordinator",
    "SIC": "Second in Charge",
    "SENCO": "SENCO",
    "SENDCO": "SEND Coordinator",
    "SPO_CO": "Sports Coordinator",
    "WAC_LD": "Wrap Around Care Lead",
    "WAC_AST": "Wrap Around Care Assistant",
    "WAC_MGR": "Wrap Around Care Manager",
    "WAC_CO": "Wrap Around Care Coordinator",
    "WAC_SUP": "Wrap Around Care Supervisor",
    "AAHT": "Associate Assistant Headteacher",
    "SIL": "School Improvement Lead",
    "STR_LD": "Strategic Lead",
    "DPO": "Data Protection Officer",
    "HOY": "Head of Year",
    "AHOY": "Assistant Head of Year",
    "SSA": "Student Support Assistant",
    "SSM": "Student Support Manager",
    "PLAY_LDR": "Play Leader",
    "COM_OFF": "Communications Officer",
    "CUR_MGR": "Curriculum Manager",
    "DHOC": "Deputy Head of Centre",
    "HOC": "Head of Centre",
    "IT_SYS_AST": "IT Systems Assistant",
    "IT_SYS_DEV": "IT Systems Developer",
    "IT_SYS_OFF": "IT Systems Officer",
    "MH_LD": "Mental Health Lead",
    "PAS_LD": "Pastoral Lead",
    "MAR_MGR": "Marketing Manager",
    "HR_OFF_SNR": "Senior HR Officer",
    "TUT": "Tutor",
    "PAS_SUP": "Pastoral Support",
    "DIR_PD": "Director of Personal Development",
    "KS_LD": "Key Stage Lead",
    "LSM": "Learning Support Mentor",
    "WEL_LD": "Wellbeing Lead",
    "WEL_OFF": "Wellbeing Officer",
    "DOE_MGR": "DofE Manager",
    "DOE_AST": "DofE Assistant",
    "SIMS_MGR": "SIMS Manager",
    "HS_LD": "Health & Safety Lead",
    "HS_MGR": "Health & Safety Manager",
    "PAY_AST": "Payroll Assistant",
    "SYS_MGR_AST": "Assistant Systems Manager",
    "AAP": "Associate Assistant Principal",
    "BSW": "Behaviour Support Worker",
    "CARE_AST": "Care Assistant",
    "DIR_FAC": "Director of Facilities",
    "DUTY_MGR": "Duty Manager",
    "FA": "First Aider",
    "FAC_CO": "Facilities Coordinator",
    "FAC_SUP": "Facilities Supervisor",
    "HR_CO": "HR Coordinator",
    "MUS_LD": "Music Lead",
    "NUR_LD": "Nurture Lead",
    "BASC_AST": "Before & After School Club Assistant",
    "BASC_MGR": "Before & After School Club Manager",
    "CAT_SUP": "Catering Supervisor",
    "CLE_MGR": "Cleaning Manager",
    "CLE_SUP": "Cleaning Supervisor",
    "COOK": "Cook",
    "DATA_AST": "Data Assistant",
    "DIR_ACH": "Director of Achievement",
    "DIR_LRN": "Director of Learning",
    "FAC_LD": "Faculty Lead",
    "FSO": "Family Support Officer",
    "GOV_PRO": "Governance Professional",
    "LSO": "Learning Support Officer",
    "MDSA": "Midday Supervisory Assistant",
    "NUR_OFF": "Nursery Officer",
    "PAS_AST": "Pastoral Assistant",
    "OUT_WRK": "Outreach Worker",
    "LTO": "Lunchtime Organiser",
    "MDA": "Midday Assistant",
    "CT_AST": "Assistant Caretaker",
    "CT_DEP": "Deputy Caretaker",
    "BUR": "Bursar",
    "BASC_CO": "Before & After School Club Coordinator",
    "BASC_LDR": "Before & After School Club Leader",
    "MDC": "Midday Coordinator",
    "SMDS": "Senior Midday Supervisor",
    "SITE_APP": "Site Apprentice",
    "EY_EDU": "Early Years Educator",
    "EY_LD": "Early Years Lead",
    "FLW": "Family Link Worker",
    "INC_AST": "Inclusion Assistant",
    "INC_MEN": "Inclusion Mentor",
    "EY_EDU_SNR": "Senior Early Years Educator",
    "EVE_MGR": "Events Manager",
    "FIN_LD": "Finance Lead",
    "HO_EST": "Head of Estates",
    "ICT_MGR": "ICT Manager",
    "OFF_ADM": "Office Administrator",
    "WEB_MGR": "Web Manager",
    "WEL_ADM": "Welfare Administrator",
    "DCFO": "Deputy Chief Financial Officer",
    "DCOO": "Deputy Chief Operating Officer",
    "SIL_SNR": "Senior School Improvement Lead",
    "ASSO_TEA": "Associate Teacher",
    "COM_SUP": "Communication Support Worker",
    "FA_LD": "First Aid Lead",
    "ACC_MGR": "Accounts Manager",
    "ACC_OFF": "Accounts Officer",
    "OFF_APP": "Office Apprentice",
    "REC_OFF": "Recruitment Officer",
    "SEN_ADM": "SEN Administrator",
    "SEN_AST": "SEN Assistant",
    "SEN_SUP": "SEN Support",
    "CASH_COL": "Cash Collector",
    "KIT_AST": "Kitchen Assistant",
    "KIT_MGR": "Kitchen Manager",
    "UNIT_MGR": "Unit Manager",
    "EXT_LDR": "Extended Schools Leader",
    "EDU_PAR": "Education Partner",
    "IMP_LD": "Improvement Lead",
    "TEA_NUR": "Nursery Teacher",
    "ASC_PW": "After School Club Playworker",
}

# =============================================================================
# ROLE TO GROUP MAPPING
# Maps staff role codes to their default staff role group
# =============================================================================
ROLE_TO_GROUP = {
    # Leadership - Teaching
    "HT": "LST", "DHT": "LST", "AHT": "LST", "EHT": "LST", "PRI": "LST", "EP": "LST",
    "VP": "LST", "SVP": "LST", "AVP": "LST", "AP": "LST", "SAP": "LST", "AAP": "LST",
    "HOS": "LST", "HOC": "LST", "DHOC": "LST", "AAHT": "LST",

    # Leadership - Non-Teaching
    "CEO": "LSN", "COO": "LSN", "CFO": "LSN", "CFOO": "LSN", "CPO": "LSN", "CSO": "LSN",
    "DCFO": "LSN", "DCOO": "LSN", "STR_DIR": "LSN",

    # Teachers
    "TEA": "TEA", "UQT": "TEA", "ASSO_TEA": "TEA", "TEA_NUR": "TEA",
    "HOD": "TEA", "SUB_LDR": "TEA", "HOF": "TEA", "AHOF": "TEA", "FAC_LDR": "TEA",
    "LP": "TEA", "LST": "TEA", "CUR_LDR": "TEA", "CUR_LDR_AST": "TEA",
    "YR_LDR": "TEA", "KS_LD": "TEA", "EYFS_LD": "TEA", "EY_LD": "TEA",
    "HOY": "TEA", "AHOY": "TEA", "PRO_LDR": "TEA", "SIC": "TEA",
    "SENCO": "TEA", "SENDCO": "TEA",

    # Teaching Assistants
    "TA": "TA", "TA_APP": "TA",

    # Higher Level Teaching Assistants
    "HLTA": "HLTA",

    # Learning Support Assistants
    "LSA": "LSA", "ELSA": "LSA", "LSM": "LSM", "LSO": "LSA",

    # Learning Mentors
    "LM": "LM", "ACAD_MEN": "LM",

    # Cover
    "COV_SUP": "COV", "COV_AST": "COV", "COV_COA": "COV", "COV_TEA": "COV", "COV_MGR": "COV",

    # Admin/Finance
    "SBM": "ADM", "BM": "ADM", "SBO": "ADM", "BUR": "ADM",
    "ADM": "ADM", "ADM_MGR": "ADM", "ADM_AST": "ADM", "ADM_OFF": "ADM",
    "ADM_SNR": "ADM", "ADM_AST_SNR": "ADM", "ADM_LDR": "ADM", "ADM_CO": "ADM",
    "REC": "ADM", "PA": "ADM", "EXEC_AST": "ADM", "OFF_MGR": "ADM",
    "OFF_AST": "ADM", "OFF_CO": "ADM", "OFF_ADM": "ADM", "OFF_APP": "ADM",

    # Finance
    "FIN_MGR": "FIN", "FIN_AST": "FIN", "FIN_ADM": "FIN", "FIN_OFF": "FIN",
    "FIN_OFF_SNR": "FIN", "FIN_LD": "FIN", "DIR_FIN": "FIN",
    "PAY_MGR": "FIN", "PAY_OFF": "FIN", "PAY_AST": "FIN",
    "ACC_MGR": "FIN", "ACC_OFF": "FIN", "MAN_ACC": "FIN", "CASH_COL": "FIN",

    # HR
    "HR_MGR": "HR", "HR_AST": "HR", "HR_OFF": "HR", "HR_ADV": "HR",
    "HR_DIR": "HR", "HR_CO": "HR", "HR_OFF_SNR": "HR", "DIR_HR": "HR",
    "REC_OFF": "HR",

    # IT
    "IT_NET_MGR": "IT", "IT_TEC": "IT", "IT_SUP_LD": "IT",
    "IT_SYS_AST": "IT", "IT_SYS_DEV": "IT", "IT_SYS_OFF": "IT",
    "NET_MGR": "IT", "SYS_ADM": "IT", "SYS_MGR_AST": "IT",
    "ICT_MGR": "IT", "WEB_MGR": "IT", "DIR_IT": "IT",

    # Data
    "DATA_MGR": "ADM", "DATA_OFF": "ADM", "DATA_ADM": "ADM",
    "DATA_ENG": "ADM", "DATA_CO": "ADM", "DATA_LDR": "ADM", "DATA_AST": "ADM",
    "SIMS_MGR": "ADM", "DPO": "ADM",

    # Exams
    "EXA_OFF": "EXA", "EXA_AST": "EXA", "EXA_MGR": "EXA", "EXA_CO": "EXA", "EXA_LD": "EXA",
    "INV": "INV",

    # Caretaker/Site
    "CT": "CT", "CT_SNR": "CT", "CT_AST": "CT", "CT_DEP": "CT",
    "SITE_MGR": "PRE", "SITE_AST": "PRE", "SITE_MGR_AST": "PRE", "SITE_MGR_DEP": "PRE",
    "SITE_OP": "PRE", "SITE_STF": "PRE", "SITE_OFF": "PRE", "SITE_SUP": "PRE", "SITE_APP": "PRE",
    "PRE_MGR": "PRE", "PRE_AST": "PRE", "PRE_OFF": "PRE", "PRE_SUP": "PRE",
    "FAC_MGR": "PRE", "FAC_AST": "PRE", "FAC_AST_SNR": "PRE", "FAC_CO": "PRE", "FAC_SUP": "PRE",
    "MAIN_OFF": "PRE", "HK": "PRE",

    # Estates
    "EST_MGR": "EST", "EST_OFF": "EST", "HO_EST": "EST", "DIR_FAC": "EST",

    # Cleaning
    "CLE": "CLE", "CLE_SNR": "CLE", "CLE_MGR": "CLE", "CLE_SUP": "CLE",

    # Catering
    "CAT_MGR": "CAT", "CAT_AST": "CAT", "CAT_SUP": "CAT",
    "COOK": "CAT", "COOK_AST": "CAT", "COOK_SNR": "CAT",
    "CHEF": "CAT", "CHEF_AST": "CAT",
    "KIT_MGR": "CAT", "KIT_AST": "CAT",

    # Midday
    "MDS": "MDS", "MDSA": "MDS", "MDA": "MDS", "MDC": "MDS", "SMDS": "MDS",

    # Lunchtime
    "LTS": "LTS", "LTS_SNR": "LTS", "LTA": "LTS", "LTO": "LTS",

    # Nursery
    "NUR_MGR": "NUR", "NUR_NUR": "NUR", "NUR_AST": "NUR", "NUR_APP": "NUR",
    "NUR_PRA": "NUR", "NUR_SUP": "NUR", "NUR_OFF": "NUR", "NUR_LD": "NUR",
    "EYP": "NUR", "EY_EDU": "NUR", "EY_EDU_SNR": "NUR", "RM_LDR": "NUR", "RM_MGR": "NUR", "RM_CO": "NUR",

    # Inclusion/SEN
    "INC_MGR": "INC", "INC_MGR_AST": "INC", "INC_OFF": "INC", "INC_SUP": "INC",
    "INC_ADM": "INC", "INC_CO": "INC", "INC_LD": "INC", "INC_TL": "INC",
    "INC_AST": "INC", "INC_MEN": "INC", "DIR_INC": "INC",
    "SENCO_AST": "INC", "SEN_ADM": "INC", "SEN_AST": "INC", "SEN_SUP": "INC",
    "BEH_INC_MGR": "INC", "BEH_OFF": "INC", "BEH_SUP": "INC", "BSO": "INC", "BSW": "INC",
    "INT_LD": "INC",

    # Pastoral
    "PAS_MGR": "PAS", "PAS_MGR_SNR": "PAS", "PAS_MEN": "PAS", "PAS_OFF": "PAS",
    "PAS_SUP_MGR": "PAS", "PAS_LDR": "PAS", "PAS_CO": "PAS", "PAS_LD": "PAS",
    "PAS_SUP": "PAS", "PAS_AST": "PAS", "PSO": "PAS",
    "COU": "PAS", "MH_LD": "PAS",

    # Pupil Support
    "SSL": "PS", "SSA": "PS", "SSM": "PS", "SWO": "PS",
    "LEA_PRO_MGR": "PS", "LEA_PRO_OFF": "PS",

    # Safeguarding
    "SFG_MGR": "ADM", "SFG_OFF": "ADM", "DSL": "ADM", "DDSL": "ADM", "DIR_SFG": "ADM",

    # Family Support
    "FSW": "FSW", "FSA": "FSW", "FSO": "FSW", "FLO": "FSW", "PLO": "FSW", "FLW": "FSW", "FEL": "FSW",

    # Wellbeing
    "WEL_LD": "WEL", "WEL_OFF": "WEL", "WEL_ADM": "WEL",
    "MED_OFF": "WEL", "FA": "WEL", "FA_LD": "WEL", "HS_LD": "WEL", "HS_MGR": "WEL",
    "CARE_AST": "WEL",

    # Governance
    "CLER_GOV": "GOV", "HO_GOV": "GOV", "GOV_MGR": "GOV", "GOV_OFF": "GOV",
    "GOV_LDR": "GOV", "GOV_PRO": "GOV", "DIR_GOV": "GOV",

    # Library
    "LIB": "LIB", "LIB_AST": "LIB", "LIB_MGR": "LIB", "LIB_CO": "LIB", "LRC_CO": "LIB",

    # Technicians
    "TEC": "TEC", "TEC_SNR": "TEC", "REP_AST": "TEC", "REP_TEC": "TEC", "REP_CO": "TEC", "REP_OFF": "TEC",

    # Music
    "MUS_TUT": "MUS", "MUS_ADM": "MUS", "MUS_LD": "MUS",
    "PERI": "PERI",

    # Marketing/Communications
    "COM_MAR_OFF": "MAR", "MAR_MGR": "MAR", "COM_OFF": "MAR", "COM_ADM": "MAR", "COM_SUP": "MAR",
    "EVE_MGR": "MAR",

    # Careers
    "CAR_OFF": "ADM", "CAR_ADV": "ADM", "CAR_LD": "ADM",

    # Attendance
    "ATT_OFF": "ADM", "ATT_AST": "ADM", "ATT_MGR": "ADM", "EWO": "ADM",

    # Resources
    "RES_AST": "ADM", "RES_MGR": "ADM",

    # Operations
    "OP_MGR": "LSN", "OP_OFF": "ADM", "DIR_OP": "LSN", "DUTY_MGR": "ADM",

    # Compliance
    "COM_MGR": "ADM",

    # Curriculum Support
    "CUR_MGR": "CUR", "LIT_CO": "CUR", "EAL_CO": "CUR", "EAL_LD": "CUR",
    "DIR_CUR": "CUR", "DIR_EDU": "CUR", "DIR_LRN": "CUR", "DIR_ACH": "CUR",
    "DIR_PD": "CUR", "DIR_PRI_EDU": "CUR", "DIR_SEC_EDU": "CUR", "DIR_SUB": "CUR",

    # Extended Schools
    "EXT": "EXT", "EXT_AST": "EXT", "EXT_SUP": "EXT", "EXT_LDR": "EXT", "ENR_CO": "EXT",

    # After School Club
    "ASC_AST": "ASC", "ASC_LDR": "ASC", "ASC_MGR": "ASC", "ASC_SUP": "ASC", "ASC_PW": "ASC",

    # Breakfast Club
    "BFC_AST": "BFC", "BFC_SUP": "BFC", "BFC_LDR": "BFC", "BFC_MGR": "BFC",

    # Before & After School Club
    "BASC_AST": "ASC", "BASC_MGR": "ASC", "BASC_CO": "ASC", "BASC_LDR": "ASC",

    # Out of School
    "OOS_AST": "EXT", "OOS_SUP": "EXT", "OOS_LDR": "EXT", "OOS_MGR": "EXT", "OOS_CO": "EXT",

    # Wrap Around Care
    "WAC_LD": "WAC", "WAC_AST": "WAC", "WAC_MGR": "WAC", "WAC_CO": "WAC", "WAC_SUP": "WAC",

    # Play Workers
    "PLAY_WRK": "EXT", "PLAY_LDR": "EXT",

    # Sports
    "SC": "SC", "SPO_CO": "SPO",

    # Foreign Language
    "FLA": "FLA",

    # Outreach
    "OUT_WRK": "OUT",

    # Tutors
    "TUT": "TUT",

    # Chaplain
    "CHAP": "OTH",

    # SCITT
    "SCITT": "SCITT", "SIP": "SCITT", "SIL": "SCITT", "SIL_SNR": "SCITT",
    "IMP_LD": "SCITT", "EDU_PAR": "SCITT",

    # Theatre
    "THEA_MGR": "OTH",

    # DofE
    "DOE_MGR": "EXT", "DOE_AST": "EXT",

    # Unit Manager
    "UNIT_MGR": "OTH",

    # Project
    "PRO_LD": "ADM", "STR_LD": "LSN",

    # SALT
    "SALT": "INC",

    # Drivers
    "DRI": "DRI",

    # Other
    "OTH": "OTH", "OTH_DIR": "OTH_DIR",
    "HO_FIN_EST": "FIN",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_role_code_from_title(title: str) -> str:
    """
    Infer staff role code from job title.
    Returns the best matching role code or 'OTH' if no match.
    """
    if not title:
        return "OTH"

    title_lower = title.lower().strip()

    # Build reverse lookup: title -> code
    title_to_code = {v.lower(): k for k, v in STAFF_ROLES.items()}

    # Exact match
    if title_lower in title_to_code:
        return title_to_code[title_lower]

    # Keyword matching (ordered by specificity)
    keyword_map = [
        # Leadership
        ("executive headteacher", "EHT"), ("executive principal", "EP"),
        ("headteacher", "HT"), ("head teacher", "HT"),
        ("deputy headteacher", "DHT"), ("deputy head", "DHT"),
        ("assistant headteacher", "AHT"), ("assistant head", "AHT"),
        ("principal", "PRI"), ("vice principal", "VP"), ("assistant principal", "AP"),
        ("chief executive", "CEO"), ("chief operating", "COO"), ("chief financial", "CFO"),

        # Teachers
        ("teacher", "TEA"), ("unqualified teacher", "UQT"),
        ("head of department", "HOD"), ("head of faculty", "HOF"),
        ("subject leader", "SUB_LDR"), ("curriculum leader", "CUR_LDR"),
        ("lead practitioner", "LP"), ("senco", "SENCO"),

        # Teaching Assistants
        ("higher level teaching assistant", "HLTA"), ("hlta", "HLTA"),
        ("teaching assistant", "TA"),
        ("learning support assistant", "LSA"),

        # Admin
        ("school business manager", "SBM"), ("business manager", "BM"),
        ("finance manager", "FIN_MGR"), ("finance officer", "FIN_OFF"),
        ("finance assistant", "FIN_AST"),
        ("hr manager", "HR_MGR"), ("hr officer", "HR_OFF"), ("hr assistant", "HR_AST"),
        ("admin manager", "ADM_MGR"), ("admin officer", "ADM_OFF"),
        ("admin assistant", "ADM_AST"), ("administrator", "ADM"),
        ("receptionist", "REC"), ("office manager", "OFF_MGR"),
        ("personal assistant", "PA"), ("executive assistant", "EXEC_AST"),

        # Site
        ("site manager", "SITE_MGR"), ("caretaker", "CT"),
        ("cleaner", "CLE"), ("cleaning", "CLE"),
        ("premises", "PRE_MGR"), ("facilities", "FAC_MGR"),

        # Catering
        ("catering manager", "CAT_MGR"), ("catering assistant", "CAT_AST"),
        ("cook", "COOK"), ("chef", "CHEF"), ("kitchen", "KIT_AST"),

        # Midday
        ("midday supervisor", "MDS"), ("midday", "MDS"),
        ("lunchtime supervisor", "LTS"), ("lunchtime", "LTS"),

        # Nursery
        ("nursery manager", "NUR_MGR"), ("nursery nurse", "NUR_NUR"),
        ("nursery assistant", "NUR_AST"), ("nursery", "NUR_AST"),
        ("early years", "EYP"),

        # Inclusion/SEN
        ("inclusion manager", "INC_MGR"), ("inclusion", "INC_SUP"),
        ("behaviour", "BEH_OFF"), ("sen ", "SEN_AST"),

        # Pastoral
        ("pastoral manager", "PAS_MGR"), ("pastoral", "PAS_OFF"),
        ("counsellor", "COU"), ("mentor", "LM"),

        # IT
        ("it manager", "IT_NET_MGR"), ("it technician", "IT_TEC"),
        ("network manager", "NET_MGR"), ("systems", "SYS_ADM"),

        # Exams
        ("exams officer", "EXA_OFF"), ("exams", "EXA_OFF"),
        ("invigilator", "INV"),

        # Library
        ("librarian", "LIB"), ("library", "LIB_AST"),

        # Technician
        ("technician", "TEC"),

        # Cover
        ("cover supervisor", "COV_SUP"), ("cover", "COV_SUP"),

        # Extended/Clubs
        ("after school", "ASC_AST"), ("breakfast club", "BFC_AST"),
        ("wrap around", "WAC_AST"), ("extended school", "EXT"),

        # Family
        ("family support", "FSW"), ("family liaison", "FLO"),

        # Safeguarding
        ("safeguarding", "SFG_OFF"), ("dsl", "DSL"),

        # Governance
        ("clerk", "CLER_GOV"), ("governance", "GOV_OFF"),

        # Data
        ("data manager", "DATA_MGR"), ("data", "DATA_OFF"),

        # Attendance
        ("attendance", "ATT_OFF"),

        # Payroll
        ("payroll", "PAY_OFF"),

        # Sports
        ("sports coach", "SC"), ("sports", "SPO_CO"),

        # Music
        ("music", "MUS_TUT"),
    ]

    for keyword, code in keyword_map:
        if keyword in title_lower:
            return code

    # No match found - intelligently generate a code using official patterns
    return _generate_role_code(title)


def _generate_role_code(title: str) -> str:
    """
    Intelligently generate a staff role code using official formatting patterns.

    Patterns learned from 363 official codes:
    - Single word: 2-4 letter abbreviation (TEA, HT, CT, CLE, HLTA)
    - Two words: PREFIX_SUFFIX format (FIN_MGR, HR_AST, ADM_OFF)
    - Three+ words: Abbreviate key parts (BEH_INC_MGR, PAS_SUP_MGR)

    Common suffixes: _MGR, _AST, _OFF, _LDR, _CO, _SUP, _ADM, _SNR, _APP, _TEC
    Common prefixes by department: FIN_, HR_, ADM_, IT_, DATA_, PAS_, INC_, etc.
    """
    import re

    if not title:
        return "OTH"

    # Clean title
    title_clean = title.upper().strip()
    title_clean = re.sub(r'[^A-Z0-9\s]', '', title_clean)
    words = title_clean.split()

    if not words:
        return "OTH"

    # Common role suffixes and their abbreviations
    suffix_map = {
        'MANAGER': 'MGR',
        'ASSISTANT': 'AST',
        'OFFICER': 'OFF',
        'LEADER': 'LDR',
        'COORDINATOR': 'CO',
        'SUPERVISOR': 'SUP',
        'ADMINISTRATOR': 'ADM',
        'SENIOR': 'SNR',
        'APPRENTICE': 'APP',
        'TECHNICIAN': 'TEC',
        'DIRECTOR': 'DIR',
        'LEAD': 'LD',
        'WORKER': 'WRK',
        'SUPPORT': 'SUP',
        'DEPUTY': 'DEP',
        'HEAD': 'HO',
    }

    # Common department prefixes and their abbreviations
    prefix_map = {
        'FINANCE': 'FIN',
        'FINANCIAL': 'FIN',
        'HUMAN RESOURCES': 'HR',
        'ADMIN': 'ADM',
        'ADMINISTRATION': 'ADM',
        'ADMINISTRATIVE': 'ADM',
        'INFORMATION TECHNOLOGY': 'IT',
        'DATA': 'DATA',
        'PASTORAL': 'PAS',
        'INCLUSION': 'INC',
        'BEHAVIOUR': 'BEH',
        'ATTENDANCE': 'ATT',
        'CATERING': 'CAT',
        'CLEANING': 'CLE',
        'SITE': 'SITE',
        'PREMISES': 'PRE',
        'FACILITIES': 'FAC',
        'NURSERY': 'NUR',
        'LIBRARY': 'LIB',
        'EXAMS': 'EXA',
        'EXAM': 'EXA',
        'COVER': 'COV',
        'MARKETING': 'MAR',
        'COMMUNICATIONS': 'COM',
        'GOVERNANCE': 'GOV',
        'WELLBEING': 'WEL',
        'SAFEGUARDING': 'SFG',
        'CAREERS': 'CAR',
        'SPORTS': 'SPO',
        'MUSIC': 'MUS',
        'CURRICULUM': 'CUR',
        'RESOURCES': 'RES',
        'PAYROLL': 'PAY',
        'ACCOUNTS': 'ACC',
        'ESTATES': 'EST',
        'OPERATIONS': 'OP',
        'OFFICE': 'OFF',
        'STUDENT': 'STU',
        'PUPIL': 'PUP',
        'LEARNING': 'LEA',
        'TEACHING': 'TEA',
        'FAMILY': 'FAM',
        'EXTENDED': 'EXT',
        'RECEPTION': 'REC',
        'SCIENCE': 'SCI',
        'ENGLISH': 'ENG',
        'MATHS': 'MAT',
        'MATHEMATICS': 'MAT',
    }

    # Try to identify prefix (department) and suffix (role type)
    prefix = None
    suffix = None
    middle_parts = []

    # Check for multi-word prefixes first
    title_upper = ' '.join(words)
    for dept, abbrev in prefix_map.items():
        if title_upper.startswith(dept):
            prefix = abbrev
            # Remove prefix words from list
            dept_word_count = len(dept.split())
            words = words[dept_word_count:]
            break

    # Check last word for suffix
    if words:
        last_word = words[-1]
        if last_word in suffix_map:
            suffix = suffix_map[last_word]
            words = words[:-1]

    # If no prefix found, try single word prefix
    if not prefix and words:
        first_word = words[0]
        if first_word in prefix_map:
            prefix = prefix_map[first_word]
            words = words[1:]
        elif len(first_word) <= 4:
            prefix = first_word[:3]
            words = words[1:]

    # Build the code
    if prefix and suffix:
        if words:
            # Include middle part: PREFIX_MID_SUFFIX
            mid = '_'.join(w[:3] for w in words[:1])
            code = f"{prefix}_{mid}_{suffix}" if mid else f"{prefix}_{suffix}"
        else:
            code = f"{prefix}_{suffix}"
    elif prefix:
        if words:
            # PREFIX_REMAINING
            remaining = '_'.join(w[:3] for w in words[:2])
            code = f"{prefix}_{remaining}" if remaining else prefix
        else:
            code = prefix
    elif suffix:
        if words:
            # REMAINING_SUFFIX
            remaining = '_'.join(w[:3] for w in words[:2])
            code = f"{remaining}_{suffix}" if remaining else suffix
        else:
            code = suffix
    else:
        # No recognizable pattern - create from words
        if len(words) == 1:
            code = words[0][:6]
        elif len(words) == 2:
            code = f"{words[0][:3]}_{words[1][:3]}"
        else:
            # Take first 3 letters of first 2-3 significant words
            code = '_'.join(w[:3] for w in words[:3])

    # Ensure code isn't too long (max ~12 chars like official codes)
    if len(code) > 12:
        parts = code.split('_')
        if len(parts) > 2:
            code = '_'.join(parts[:2])

    return code


def get_group_from_role(role_code: str) -> str:
    """
    Get staff role group code from staff role code.
    Returns the default group or intelligently infers from code pattern.
    """
    # First check official mappings
    if role_code in ROLE_TO_GROUP:
        return ROLE_TO_GROUP[role_code]

    # Intelligently infer group from code prefix
    return _infer_group_from_code(role_code)


def _infer_group_from_code(role_code: str) -> str:
    """
    Infer staff role group from a generated role code based on prefix patterns.

    Uses the same prefix patterns as official codes to determine group.
    """
    if not role_code:
        return "OTH"

    code_upper = role_code.upper()

    # Prefix to group mapping (based on official code patterns)
    prefix_to_group = {
        # Teaching
        'TEA': 'TEA', 'UQT': 'TEA', 'HOD': 'TEA', 'HOF': 'TEA', 'SUB': 'TEA',
        'CUR': 'CUR', 'LP': 'TEA', 'SENCO': 'TEA', 'SEN': 'INC',

        # Leadership
        'HT': 'LST', 'DHT': 'LST', 'AHT': 'LST', 'EHT': 'LST', 'PRI': 'LST',
        'EP': 'LST', 'VP': 'LST', 'AP': 'LST', 'HOS': 'LST', 'HOC': 'LST',
        'CEO': 'LSN', 'COO': 'LSN', 'CFO': 'LSN', 'DIR': 'LSN', 'STR': 'LSN',

        # Teaching Assistants
        'TA': 'TA', 'HLTA': 'HLTA',
        'LSA': 'LSA', 'LSM': 'LM', 'LM': 'LM',

        # Admin
        'ADM': 'ADM', 'OFF': 'ADM', 'REC': 'ADM', 'PA': 'ADM',
        'SBM': 'ADM', 'BM': 'ADM', 'BUR': 'ADM', 'SBO': 'ADM',
        'DATA': 'ADM', 'SIMS': 'ADM', 'DPO': 'ADM',
        'ATT': 'ADM', 'CAR': 'ADM', 'RES': 'ADM',

        # Finance
        'FIN': 'FIN', 'PAY': 'FIN', 'ACC': 'FIN',

        # HR
        'HR': 'HR',

        # IT
        'IT': 'IT', 'NET': 'IT', 'SYS': 'IT', 'ICT': 'IT', 'WEB': 'IT',

        # Exams
        'EXA': 'EXA', 'INV': 'INV',

        # Site/Premises
        'CT': 'CT', 'SITE': 'PRE', 'PRE': 'PRE', 'FAC': 'PRE', 'MAIN': 'PRE', 'HK': 'PRE',
        'EST': 'EST',

        # Cleaning
        'CLE': 'CLE',

        # Catering
        'CAT': 'CAT', 'COOK': 'CAT', 'CHEF': 'CAT', 'KIT': 'CAT',

        # Midday/Lunchtime
        'MDS': 'MDS', 'MDA': 'MDS', 'MDC': 'MDS',
        'LTS': 'LTS', 'LTA': 'LTS', 'LTO': 'LTS',

        # Nursery/Early Years
        'NUR': 'NUR', 'EYP': 'NUR', 'EY': 'NUR', 'RM': 'NUR',

        # Inclusion/SEN
        'INC': 'INC', 'BEH': 'INC', 'INT': 'INC', 'SALT': 'INC',

        # Pastoral
        'PAS': 'PAS', 'PSO': 'PAS', 'COU': 'PAS', 'MH': 'PAS',

        # Pupil/Student Support
        'SS': 'PS', 'SSL': 'PS', 'SSA': 'PS', 'SSM': 'PS', 'SWO': 'PS',
        'LEA': 'PS',

        # Safeguarding
        'SFG': 'ADM', 'DSL': 'ADM', 'DDSL': 'ADM',

        # Family Support
        'FSW': 'FSW', 'FSA': 'FSW', 'FSO': 'FSW', 'FLO': 'FSW', 'PLO': 'FSW', 'FLW': 'FSW',
        'FAM': 'FSW',

        # Wellbeing
        'WEL': 'WEL', 'MED': 'WEL', 'FA': 'WEL', 'HS': 'WEL', 'CARE': 'WEL',

        # Governance
        'CLER': 'GOV', 'GOV': 'GOV',

        # Library
        'LIB': 'LIB', 'LRC': 'LIB',

        # Technicians
        'TEC': 'TEC', 'REP': 'TEC',

        # Music
        'MUS': 'MUS', 'PERI': 'PERI',

        # Marketing
        'MAR': 'MAR', 'COM': 'MAR', 'EVE': 'MAR',

        # Cover
        'COV': 'COV',

        # Extended/Clubs
        'EXT': 'EXT', 'ENR': 'EXT', 'DOE': 'EXT', 'PLAY': 'EXT',
        'ASC': 'ASC', 'BFC': 'BFC', 'BASC': 'ASC', 'OOS': 'EXT',
        'WAC': 'WAC',

        # Sports
        'SC': 'SC', 'SPO': 'SPO',

        # Foreign Language
        'FLA': 'FLA',

        # Outreach
        'OUT': 'OUT',

        # Tutors
        'TUT': 'TUT',

        # Operations
        'OP': 'ADM',

        # SCITT
        'SCITT': 'SCITT', 'SIP': 'SCITT', 'SIL': 'SCITT', 'IMP': 'SCITT', 'EDU': 'SCITT',

        # Additional patterns for generated codes
        'MEN': 'PAS',  # Mental health
        'DIG': 'IT',   # Digital
        'STU': 'PS',   # Student
        'PUP': 'PS',   # Pupil
        'COMM': 'MAR', # Communications (longer form)
        'ENG': 'ADM',  # Engagement
    }

    # Check exact code first
    if code_upper in prefix_to_group:
        return prefix_to_group[code_upper]

    # Check prefixes (before underscore)
    if '_' in code_upper:
        prefix = code_upper.split('_')[0]
        if prefix in prefix_to_group:
            return prefix_to_group[prefix]

    # Check if code starts with any known prefix
    for prefix, group in prefix_to_group.items():
        if code_upper.startswith(prefix):
            return group

    return "OTH"


def get_group_from_title(title: str) -> str:
    """
    Get staff role group code from job title.
    First finds the role code, then maps to group.
    """
    role_code = get_role_code_from_title(title)
    return get_group_from_role(role_code)


def is_teaching_role(role_code: str) -> bool:
    """Check if a role code is a teaching role."""
    teaching_groups = {"TEA", "LST", "STEA_LT", "STEA_ST"}
    group = get_group_from_role(role_code)
    return group in teaching_groups


def is_support_role(role_code: str) -> bool:
    """Check if a role code is a support role."""
    return not is_teaching_role(role_code)


def validate_role_code(code: str) -> bool:
    """Check if a role code is valid."""
    return code in STAFF_ROLES


def validate_group_code(code: str) -> bool:
    """Check if a group code is valid."""
    return code in STAFF_ROLE_GROUPS
