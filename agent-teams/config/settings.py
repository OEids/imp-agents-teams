"""
Agent Teams Configuration

Reads user settings from user_config.json for data directory locations.

Includes Intelligence Module configuration for:
- Confidence thresholds
- Learning engine settings
- Rule hot-reload options
"""
from pathlib import Path
import json
from datetime import datetime

# Base paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = Path(__file__).parent
USER_CONFIG_FILE = CONFIG_DIR / "user_config.json"

# Intelligence module paths
RULES_DIR = CONFIG_DIR / "rules"
SCHEMAS_DIR = CONFIG_DIR / "schemas"
LEARNING_DIR = BASE_DIR / "memory"

# Default paths (used if config doesn't exist)
DEFAULT_PROJECT_ROOT = Path(r"C:\claude")
DEFAULT_CUSTOMER_DATA_DIR = DEFAULT_PROJECT_ROOT / "customer data"
DEFAULT_TEMPLATES_DIR = DEFAULT_PROJECT_ROOT / "database planner" / "templates"


def load_user_config() -> dict:
    """Load user configuration from JSON file."""
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_user_config(config: dict) -> bool:
    """Save user configuration to JSON file."""
    try:
        config['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError:
        return False


def get_data_directory() -> Path:
    """Get the customer data directory from config."""
    config = load_user_config()
    data_dir = config.get('data_directory', str(DEFAULT_CUSTOMER_DATA_DIR))
    return Path(data_dir)


def set_data_directory(path: str) -> bool:
    """Set the customer data directory in config."""
    config = load_user_config()
    config['data_directory'] = str(path)
    return save_user_config(config)


def get_templates_directory() -> Path:
    """Get the templates directory from config."""
    config = load_user_config()
    templates_dir = config.get('templates_directory', str(DEFAULT_TEMPLATES_DIR))
    return Path(templates_dir)


def set_templates_directory(path: str) -> bool:
    """Set the templates directory in config."""
    config = load_user_config()
    config['templates_directory'] = str(path)
    return save_user_config(config)


def get_reports_directory() -> Path:
    """Get the reports directory from config."""
    config = load_user_config()
    reports_dir = config.get('reports_directory', 'reports')
    # If relative path, make it relative to BASE_DIR
    reports_path = Path(reports_dir)
    if not reports_path.is_absolute():
        reports_path = BASE_DIR / reports_dir
    return reports_path


def set_reports_directory(path: str) -> bool:
    """Set the reports directory in config."""
    config = load_user_config()
    config['reports_directory'] = str(path)
    return save_user_config(config)


# Load config-based paths
CUSTOMER_DATA_DIR = get_data_directory()
TEMPLATES_DIR = get_templates_directory()
REPORTS_DIR = get_reports_directory()
DATABASE_DIR = DEFAULT_PROJECT_ROOT / "database planner" / "database"

# Template files
TEMPLATES = {
    "S1": TEMPLATES_DIR / "AA_New - Strand 1 Standard Workbook API 1.200.xlsx",
    "S2": TEMPLATES_DIR / "AA_New - Strand 2 Standard Workbook API 1.101.xlsx",
    "S3": TEMPLATES_DIR / "AA_New - Strand 3 Standard Workbook API 2.100.xlsx",
}

# Team configurations - dynamically use CUSTOMER_DATA_DIR
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
    },
    {
        "id": "audit",
        "name": "External Audit",
        "description": "Compare source data against output, verify accuracy, generate reconciliation report"
    }
]

# Check-in settings
CHECKIN_AFTER_PHASE = True  # Pause after each phase for user review


def refresh_paths():
    """Refresh all path variables from config. Call after changing config."""
    global CUSTOMER_DATA_DIR, TEMPLATES_DIR, REPORTS_DIR, TEAMS

    CUSTOMER_DATA_DIR = get_data_directory()
    TEMPLATES_DIR = get_templates_directory()
    REPORTS_DIR = get_reports_directory()

    # Update team data directories
    for team_id in TEAMS:
        TEAMS[team_id]['data_dir'] = CUSTOMER_DATA_DIR / team_id


# =============================================================================
# Intelligence Module Configuration
# =============================================================================

# Confidence thresholds for automated decisions
INTELLIGENCE_CONFIG = {
    # Confidence thresholds
    "confidence": {
        "high_threshold": 0.90,      # >90% - Auto-process silently
        "medium_threshold": 0.70,    # 70-90% - Auto-process with logged assumption
        # <70% - Auto-process with WARNING for post-review
    },

    # Behavior settings
    "behavior": {
        "auto_proceed": True,        # Auto-proceed with warnings (no blocking prompts)
        "log_assumptions": True,     # Log all assumptions made
        "enable_learning": True,     # Learn from user corrections
        "hot_reload_rules": False,   # Hot-reload YAML rules on change
    },

    # Paths
    "paths": {
        "rules_dir": str(RULES_DIR),
        "schemas_dir": str(SCHEMAS_DIR),
        "learning_dir": str(LEARNING_DIR),
    },

    # Reasoning trail settings
    "reasoning": {
        "capture_trails": True,      # Capture full reasoning trails
        "max_trail_steps": 100,      # Maximum steps per trail
        "export_format": "json",     # Export format for trails
    }
}


def get_intelligence_config() -> dict:
    """Get intelligence module configuration."""
    config = load_user_config()
    return config.get('intelligence', INTELLIGENCE_CONFIG)


def set_intelligence_config(intelligence_config: dict) -> bool:
    """Set intelligence module configuration."""
    config = load_user_config()
    config['intelligence'] = intelligence_config
    return save_user_config(config)


def get_confidence_thresholds():
    """Get confidence threshold settings."""
    config = get_intelligence_config()
    return config.get('confidence', INTELLIGENCE_CONFIG['confidence'])
