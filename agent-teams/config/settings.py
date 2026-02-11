"""
Agent Teams Configuration
"""
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = Path(r"C:\claude")

# Data paths
CUSTOMER_DATA_DIR = PROJECT_ROOT / "customer data"
TEMPLATES_DIR = PROJECT_ROOT / "database planner" / "templates"
DATABASE_DIR = PROJECT_ROOT / "database planner" / "database"
REPORTS_DIR = BASE_DIR / "reports"

# Template files
TEMPLATES = {
    "S1": TEMPLATES_DIR / "AA_New - Strand 1 Standard Workbook API 1.200.xlsx",
    "S2": TEMPLATES_DIR / "AA_New - Strand 2 Standard Workbook API 1.101.xlsx",
    "S3": TEMPLATES_DIR / "AA_New - Strand 3 Standard Workbook API 2.100.xlsx",
}

# Team configurations
TEAMS = {
    "S1": {
        "name": "Structure Team",
        "focus": "Finance codes, schools, departments, grouping codes",
        "description": "Handles foundational reference data that ties everything together",
        "data_dir": CUSTOMER_DATA_DIR / "S1",
        "key_sheets": [
            "System Grouping Codes", "01_Funds", "02_Activity", "03_CustGroup",
            "04_Ledger", "05_SchHub", "06_SchType", "07_LocalAuth",
            "08_Schools", "09_Depts", "10_FinanceCodes Budget"
        ]
    },
    "S2": {
        "name": "Staff Team",
        "focus": "Staff members, contracts, allowances, pensions",
        "description": "Handles all personnel and contract data",
        "data_dir": CUSTOMER_DATA_DIR / "S2",
        "key_sheets": [
            "25_StaffMembers", "28_ContractsTeachFTE", "29_ContractsSupportHours",
            "19_PayScales", "22_PayScaleGrades", "20_PayScalePoints",
            "16_AllowanceTypes", "24_Pensions", "34_ContractAllowances"
        ]
    },
    "S3": {
        "name": "Financial Team",
        "focus": "Budgets, funding streams, pupil numbers",
        "description": "Handles financial planning and scenario data",
        "data_dir": CUSTOMER_DATA_DIR / "S3",
        "key_sheets": [
            "14_Calculators", "15_MonthProfiles", "Pupils", "Funding",
            "Income", "Expenditure", "BF Balances", "35_ScenarioRows",
            "36_ScenarioYearValues", "37_Monthly Values"
        ]
    }
}

# Agent phases (each team runs these in sequence)
PHASES = [
    {
        "id": "analyze",
        "name": "Analysis",
        "description": "Analyze source data structure, identify fields, detect issues"
    },
    {
        "id": "clean",
        "name": "Cleanup",
        "description": "Clean data, handle missing values, normalize formats"
    },
    {
        "id": "transform",
        "name": "Transform",
        "description": "Transform data to match template requirements"
    },
    {
        "id": "build",
        "name": "Build",
        "description": "Build data into template format for import"
    },
    {
        "id": "quality_check",
        "name": "Quality Check",
        "description": "Review all processing, validate against standards, ensure data integrity"
    }
]

# Check-in settings
CHECKIN_AFTER_PHASE = True  # Pause after each phase for user review
