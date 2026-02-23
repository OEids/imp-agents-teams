"""
S1 Specialist Agent - Structure Team

Deep analysis and complete template builder for:
- Finance Codes (Chart of Accounts)
- Schools / Cost Centres
- Departments
- Funds
- DFE COA Mappings
- System Grouping Codes

Enhanced with InferenceEngine for intelligent column mapping
and confidence-based decisions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter
import re
import warnings
warnings.filterwarnings('ignore')

# Import Intelligence Module for smart decisions
try:
    from intelligence import InferenceEngine, InferenceResult, ConfidenceLevel
    from intelligence import TemplateRegistry, TemplateFormatter, TemplateWriter
    INFERENCE_AVAILABLE = True
    TEMPLATE_AVAILABLE = True
except ImportError:
    INFERENCE_AVAILABLE = False
    TEMPLATE_AVAILABLE = False

# Shared inference engine instance
_s1_inference_engine: Optional['InferenceEngine'] = None


def get_s1_inference_engine() -> Optional['InferenceEngine']:
    """Get or create the shared InferenceEngine for S1."""
    global _s1_inference_engine
    if _s1_inference_engine is None and INFERENCE_AVAILABLE:
        try:
            _s1_inference_engine = InferenceEngine(hot_reload=False)
        except Exception:
            pass
    return _s1_inference_engine


@dataclass
class ExtractedFinanceCode:
    """Extracted finance code data."""
    code: str
    title: str
    grouping_code: str  # DfE 6-digit code (510100, 612100, etc.)
    custom_grouping: str  # Trust grouping (A0, B0, C0, etc.)
    ledger_code: str
    school_codes: List[str]
    available_to_all: bool
    code_type: str  # income, expenditure, balance_sheet
    finance_code_type: str  # BUDGET, STATISTICS, PUPILNUMBERS, FUNDING, CAPITALFUND, REVENUEFUND
    is_balance_sheet: bool = False
    balance_to_scenario: bool = False


@dataclass
class ExtractedSchool:
    """Extracted school data."""
    code: str
    title: str
    la_code: str
    school_type: str
    school_hub: str
    urn: str
    london_weighting: str = "England & Wales"
    teaching_hours: float = 32.5


@dataclass
class ExtractedDepartment:
    """Extracted department data."""
    code: str
    title: str
    ledger_code: str
    activity_code: str
    school_codes: List[str]
    fund_code: str = "GAG"
    default_finance_code: str = ""


class S1SpecialistAgent:
    """
    Upskilled S1 agent for structure data.

    Builds ALL S1 template sheets:
    - System Grouping Codes
    - Funds
    - Activity
    - Ledger
    - CustGroup
    - SchHub
    - SchType
    - LocalAuth
    - Schools
    - Depts
    - FinanceCodes Budget

    TERMINOLOGY KNOWLEDGE (from IMP Planner Strand 1):
    ================================================
    STRUCTURAL REQUIREMENTS (Essential for build):
    - School Code: Unique identifier for each school
    - Finance Code: Maps to Ledger Code, DFE Grouping Code, Custom Grouping
    - Department Code: Maps to Ledger Code (e.g., MATH, ENG, SCI, ADMIN, FAC)
    - Fund Code: GAG, PP, SCITT, CIF (conditional - only if can't map to Department)

    REPORTING REQUIREMENTS (Optional):
    - School Type: Primary, Secondary, All-Through, Sixth Form, SEN
    - School Hub: Geographic groupings (North, South, London, Midlands)
    - School LA: Local Authority jurisdiction
    - Grouping Code Type: DfE COA mapping (Essential for BFR)
    - Custom Grouping: Trust-defined categorisation
    - Activity: Higher-level grouping of departments
    - Fund Code: Can map to Department when 1:1 relationship exists

    FINANCE CODE FORMATS:
    - 3-digit: 100, 110 (Report Codes)
    - 4-digit: 1000, 2000 (Standard nominals)
    - 5-digit: 11010, 51010
    - 6-digit: 110100, 115210 (Ledger Codes from finance systems)
    - Alpha: EDEQU, EXADM (Cost Centre Codes)
    """

    # Column name patterns for data detection
    FINANCE_CODE_COLUMN_PATTERNS = [
        'code', 'nominal', 'account', 'ledger code', 'finance code',
        'account code', 'nominal code', 'gl code', 'general ledger'
    ]

    FINANCE_CODE_SHEET_PATTERNS = [
        'ledger code', 'cost centre code', 'analysis code', 'report code',
        'finance code', 'chart of account', 'nominal', 'account code',
        'coa', 'gl code', 'general ledger'
    ]

    DEPARTMENT_COLUMN_PATTERNS = [
        'department', 'dept', 'cost centre', 'cost center', 'cc code',
        'departmentcode', 'deptcode', 'cc'
    ]

    FUND_COLUMN_PATTERNS = [
        'fund', 'fund code', 'fundcode', 'funding', 'funding source'
    ]

    SCHOOL_COLUMN_PATTERNS = [
        'school', 'school code', 'schoolcode', 'location', 'site',
        'academy', 'establishment'
    ]

    # Standard fund codes - short alpha codes (2-7 letters, no underscores)
    STANDARD_FUND_CODES = ['GAG', 'PP', 'SCITT', 'CIF', 'UIFSM', 'PE', 'CAP', 'CAPITAL',
                          'REST', 'RESTRICTED', 'UNRF', 'UNRESTRICTED', 'PPREM', 'DEFAULT']

    # Department code prefixes (alpha with underscores)
    DEPARTMENT_PREFIXES = ['A_', 'C_', 'S_', 'M_', 'P_', 'T_', 'ED', 'EX', 'IN', 'ST', 'PR']

    # FinanceCodeTypeCode values
    FINANCE_CODE_TYPES = ['BUDGET', 'STATISTICS', 'PUPILNUMBERS', 'FUNDING', 'CAPITALFUND', 'REVENUEFUND']

    # Patterns to detect FinanceCodeTypeCode from code/title
    STATISTICS_PATTERNS = ['_FTE_', '_RATE', 'LEVY', 'RPI', 'PENS', 'WAGE', 'UPLIFT', 'RETENTION', 'FACTOR']
    PUPILNUMBERS_PATTERNS = ['PUPIL', 'FTE_KS', 'MEALUPTAKE']
    FUNDING_PATTERNS = ['FUND', 'GRANT', 'UIFSM', 'AWPU', 'LUMP']
    CAPITALFUND_PATTERNS = ['CAP_BFWD', 'CAPITAL_BFWD']
    REVENUEFUND_PATTERNS = ['REV_BFWD', 'REVENUE_BFWD']

    # CustomGrouping mappings (Trust-defined categories)
    CUSTOM_GROUPING_MAP = {
        'A0': 'GAG funding',
        'A2': 'Other Govt Grants',
        'A3': 'Private Sector Funding',
        'A4': 'Other Income',
        'B0': 'Teaching Staff',
        'B1': 'Educational Support Staff',
        'B2': 'Premises Staffing',
        'B3': 'Admin Staffing',
        'B4': 'Other Staff',
        'B5': 'Agency Staff',
        'C0': 'Maintenance of Premises',
        'C1': 'Other Occupational Costs',
        'D0': 'Educational Supplies and Services',
        'E0': 'Other Supplies and Services',
        'F0': 'ICT Costs (Non Capital)',
        'G0': 'Staff Development',
        'G1': 'Indirect Employees Expenses',
        'H0': 'Other GAG Expenses',
        'I0': 'Depreciation',
        'L0': 'Direct Revenue Financing',
        'W0': 'Capital Income',
        'W1': 'Capital Expenditure',
        'ZZZ': 'Not Applicable',
    }

    # DfE GroupingCode mappings (6-digit codes for BFR)
    DFE_GROUPING_MAP = {
        # Income codes (5xxxxx)
        '510100': 'GAG Pre-16',
        '510110': 'Academy Bursary Funding',
        '510120': 'Start Up Grants',
        '510150': 'Rates Relief',
        '510200': 'Pupil Premium',
        '510500': 'Teacher Pay Grant',
        '510700': 'GAG Post-16',
        '510950': 'Other EFA/ESFA Grants',
        '515250': 'Self Generated Income',
        '520100': 'SEN Funding',
        '520200': 'Donations/Voluntary',
        '520300': 'Other Government Grants',
        '525750': 'Sponsorship/Bank Interest',
        '530100': 'Other LA Grants',
        '530200': 'PTA/Catering Income',
        '530250': 'Rental Income',
        '530300': 'Insurance Claims',
        '530350': 'Insurance',
        '530600': 'Music Services',
        '530650': 'Sales of Goods/Services',
        '550250': 'DfE Capital Grant (DFC)',
        '550450': 'Other DfE Capital Grant',
        '560300': 'Other Capital Grant',
        '595200': 'Funds Inherited',
        # Staff costs (6xxxxx)
        '610100': 'Leadership Salaries',
        '612100': 'Teachers Salaries',
        '612200': 'Teachers NI',
        '612300': 'Teachers Pension',
        '615100': 'Teaching Assistants Salaries',
        '615150': 'TA Overtime',
        '615200': 'TA NI',
        '615300': 'TA Pension',
        '622100': 'Technicians Salaries',
        '622150': 'Technicians Overtime',
        '622200': 'Technicians NI',
        '622300': 'Technicians Pension',
        '623100': 'Cover Supervisors',
        '623150': 'Cover Supervisors Overtime',
        '623200': 'Cover Supervisors NI',
        '623300': 'Cover Supervisors Pension',
        '625100': 'Admin Staff Salaries',
        '625150': 'Admin Staff Overtime',
        '625300': 'Admin Staff Pension',
        '627100': 'Premises Staff Salaries',
        '627150': 'Premises Staff Overtime',
        '627200': 'Premises Staff NI',
        '627300': 'Premises Staff Pension',
        '632100': 'Catering Staff Salaries',
        '632150': 'Catering Staff Overtime',
        '632200': 'Catering Staff NI',
        '632300': 'Catering Staff Pension',
        '635100': 'Other Support Staff Salaries',
        '635150': 'Other Support Staff Overtime',
        '635200': 'Other Support Staff NI',
        '635300': 'Other Support Staff Pension',
        '640100': 'Pastoral Staff',
        '640200': 'Pastoral Staff NI',
        '640300': 'Pastoral Staff Pension',
        '642100': 'Nursery Staff',
        '642150': 'Nursery Staff Overtime',
        '642200': 'Nursery Staff NI',
        '642300': 'Nursery Staff Pension',
        '647100': 'Other Staff Salaries',
        '647150': 'Other Staff Overtime',
        '647200': 'Other Staff NI',
        '647300': 'Other Staff Pension',
        '650400': 'Agency Teaching Staff',
        '650550': 'Agency Support Staff',
        '675770': 'Staff Absence Insurance',
        # Premises (7xxxxx)
        '710100': 'Building Maintenance',
        '715100': 'Rates',
        '720100': 'Gas',
        '720200': 'Oil',
        '720300': 'Electricity',
        '725200': 'Insurance',
        '730100': 'Cleaning Contract',
        '730200': 'Cleaning Materials',
        '730400': 'Caretaker Supplies',
        '735100': 'Rent',
        '740100': 'Security',
        '740200': 'Security Patrol',
        '760100': 'Grounds/Furniture',
        '760150': 'Water/Sewerage',
        '760250': 'Refuse',
        '760300': 'Hygiene',
        '760350': 'Health & Safety',
        '760500': 'PAT Testing',
        '760550': 'Other Premises',
        # Supplies (8xxxxx)
        '780770': 'Catering Consumables',
        '810100': 'Books',
        '810200': 'Learning Resources/Stationery',
        '810250': 'Equipment (Non-IT)',
        '815100': 'Exam Fees',
        '820100': 'IT Equipment/Consumables',
        '820150': 'Subscriptions',
        '820300': 'IT Support Services',
        '825150': 'Music Services',
        '825200': 'Assessments',
        '825400': 'Work Experience',
        '830100': 'Trips Travel',
        '830150': 'Trips Subsidy/Expenditure',
        '830200': 'Trips Food',
        '830300': 'Trips Insurance',
        '835100': 'Admin Subscriptions',
        '835200': 'Admin Stationery',
        '835220': 'Photocopying',
        '835300': 'Advertising',
        '835320': 'Postage',
        '835350': 'Telephone',
        '835370': 'Mobile Phones',
        '835570': 'Bank Charges',
        '840100': 'Transport/Minibus',
        '840200': 'Agency Costs',
        '850100': 'Course Fees',
        '850150': 'Recruitment/Food',
        '850200': 'Hospitality',
        '850250': 'DBS/Equipment',
        '850300': 'Staff Travel/Maintenance',
        '855100': 'Professional Services Educational',
        '855470': 'Conversion Expenses',
        '860100': 'Audit/Clerking',
        '860200': 'Accountancy (Non-Audit)',
        '870500': 'Lettings Expenditure',
        '880100': 'Student Rewards',
        '880150': 'Student Bursary',
        '880500': 'Head Office Recharge',
        '880550': 'Uniforms/Catering Uniform',
        '893100': 'LGPS Gain/Loss',
        'ZZZ': 'Needs Mapping',
    }

    # London Weighting zones
    LONDON_WEIGHTING_ZONES = [
        'England & Wales',
        'Inner London',
        'Outer London',
        'Fringe',
    ]

    @staticmethod
    def is_finance_code(code: str) -> bool:
        """
        Finance codes are ALWAYS pure numeric, 4-6 digits.
        No letters ever.
        3-digit codes (100, 110) are Report/Grouping codes, not finance codes.
        """
        if not code:
            return False
        code = str(code).strip()
        # Must be pure numeric and 4-6 digits
        # 3-digit codes are Report Codes (DFE groupings)
        return code.isdigit() and 4 <= len(code) <= 6

    @staticmethod
    def is_fund_code(code: str) -> bool:
        """
        Fund codes can be:
        - Single digit: '1', '2', '3', '4' (from finance systems)
        - Short alpha: GAG, CAP, PPREM, REST, UNRF
        No underscores.
        """
        if not code:
            return False
        code = str(code).strip().upper()
        # Single digit funds (from finance system exports)
        if code.isdigit() and len(code) == 1:
            return True
        # Short alpha codes (2-7 letters, no underscore)
        if code.isalpha() and 2 <= len(code) <= 7 and '_' not in code:
            return True
        return False

    @staticmethod
    def is_department_code(code: str) -> bool:
        """
        Department codes (Cost Centres) are alpha with underscores or prefixes.
        Examples: A_FINANCE, C_ENGLISH, S_TEACH, EDEQU, EXADM
        """
        if not code:
            return False
        code = str(code).strip().upper()
        # Contains underscore = definitely department/cost centre
        if '_' in code:
            return True
        # Alpha only with known Cost Centre prefixes
        if code.isalpha() and any(code.startswith(prefix) for prefix in ['ED', 'EX', 'IN', 'ST', 'PR', 'MAT']):
            return True
        return False

    @staticmethod
    def is_activity_code(code: str) -> bool:
        """
        Activity codes are 2-letter codes that group departments.
        Examples: ED, EX, IN, ST, PR, MAT
        """
        if not code:
            return False
        code = str(code).strip().upper()
        return code.isalpha() and 2 <= len(code) <= 3

    @staticmethod
    def is_report_code(code: str) -> bool:
        """
        Report codes are 3-digit numeric codes for DFE groupings.
        Examples: 100, 110, 120, 130
        """
        if not code:
            return False
        code = str(code).strip()
        return code.isdigit() and len(code) == 3

    @staticmethod
    def is_analysis_code(code: str) -> bool:
        """
        Analysis codes are mixed alphanumeric for trips/clubs/activities.
        Examples: ARCAUT2425, ATHLET2526, AUTHORVISIT
        """
        if not code:
            return False
        code = str(code).strip().upper()
        # Mixed alphanumeric (has both letters and numbers) or long alpha
        has_letters = any(c.isalpha() for c in code)
        has_numbers = any(c.isdigit() for c in code)
        # Mixed alphanumeric
        if has_letters and has_numbers and len(code) >= 6:
            return True
        # Long alpha-only codes (8+ chars) without underscore
        if code.isalpha() and len(code) >= 8 and '_' not in code:
            return True
        return False

    @classmethod
    def determine_finance_code_type(cls, code: str, title: str = '') -> str:
        """
        Determine FinanceCodeTypeCode from code pattern and title.
        Returns: BUDGET, STATISTICS, PUPILNUMBERS, FUNDING, CAPITALFUND, or REVENUEFUND
        """
        code_upper = str(code).strip().upper()
        title_upper = str(title).strip().upper() if title else ''

        # Check specific patterns - CAPITALFUND/REVENUEFUND
        if any(p in code_upper for p in cls.CAPITALFUND_PATTERNS):
            return 'CAPITALFUND'
        if any(p in code_upper for p in cls.REVENUEFUND_PATTERNS):
            return 'REVENUEFUND'

        # PUPILNUMBERS - pupil count codes
        if any(p in code_upper for p in cls.PUPILNUMBERS_PATTERNS) or 'PUPIL NUMBER' in title_upper:
            return 'PUPILNUMBERS'

        # FUNDING - funding/grant codes
        if any(p in code_upper for p in cls.FUNDING_PATTERNS) or 'FUNDING' in title_upper:
            return 'FUNDING'

        # STATISTICS - FTE, rates, calculations
        if any(p in code_upper for p in cls.STATISTICS_PATTERNS) or 'FTE' in title_upper or 'RATE' in title_upper:
            return 'STATISTICS'

        # Default to BUDGET for standard numeric codes
        return 'BUDGET'

    @classmethod
    def determine_custom_grouping(cls, code: str, title: str, grouping_code: str = '') -> str:
        """
        Determine CustomGrouping (A0, B0, etc.) from code range and title.
        """
        # Try to infer from numeric code range
        if code.isdigit():
            code_int = int(code)
            # Income codes (1000-1999)
            if 1000 <= code_int < 1050:
                return 'A0'  # GAG funding
            elif 1050 <= code_int < 1100:
                return 'A2'  # Other Govt Grants
            elif 1100 <= code_int < 1200:
                return 'A3'  # Private Sector
            elif 1200 <= code_int < 2000:
                return 'A4'  # Other Income
            # Staff codes (2000-2999)
            elif 2000 <= code_int < 2200:
                return 'B0'  # Teaching Staff
            elif 2200 <= code_int < 2300:
                return 'B1'  # Educational Support
            elif 2300 <= code_int < 2400:
                return 'B2'  # Premises Staffing
            elif 2600 <= code_int < 2700:
                return 'B3'  # Admin Staffing
            elif 2700 <= code_int < 2800:
                return 'B4'  # Other Staff
            elif 2800 <= code_int < 3000:
                return 'B5'  # Agency Staff
            # Premises codes (3000-3999)
            elif 3000 <= code_int < 3100:
                return 'C0'  # Maintenance
            elif 3100 <= code_int < 4000:
                return 'C1'  # Other Occupational
            # Educational supplies (4000-4999)
            elif 4000 <= code_int < 4800:
                return 'D0'  # Educational Supplies
            elif 4800 <= code_int < 5000:
                return 'B5'  # Agency (4800 range)
            # Other supplies (5000-5999)
            elif 5000 <= code_int < 5300:
                return 'E0'  # Other Supplies
            elif 5300 <= code_int < 5400:
                return 'F0'  # ICT Costs
            # Staff development (6000-6999)
            elif 6000 <= code_int < 6100:
                return 'G0'  # Staff Development
            elif 6500 <= code_int < 6600:
                return 'D0'  # Trips
            elif 6900 <= code_int < 7000:
                return 'H0'  # Other GAG
            # Capital (8000-8999)
            elif 8100 <= code_int < 8200:
                return 'W0'  # Capital Income
            elif 8200 <= code_int < 9000:
                return 'W1'  # Capital Expenditure

        # Try to infer from title keywords
        title_lower = title.lower() if title else ''
        if 'gag' in title_lower or 'pre-16' in title_lower or 'post-16' in title_lower:
            return 'A0'
        elif 'pupil premium' in title_lower or 'sen' in title_lower:
            return 'A2'
        elif 'donation' in title_lower or 'sponsor' in title_lower:
            return 'A3'
        elif 'lettings' in title_lower or 'catering income' in title_lower:
            return 'A4'
        elif 'teacher' in title_lower and 'salary' in title_lower:
            return 'B0'
        elif 'support' in title_lower and 'staff' in title_lower:
            return 'B1'
        elif 'premises' in title_lower and 'staff' in title_lower:
            return 'B2'
        elif 'admin' in title_lower and 'staff' in title_lower:
            return 'B3'
        elif 'agency' in title_lower:
            return 'B5'
        elif 'maintenance' in title_lower or 'building' in title_lower:
            return 'C0'
        elif 'cleaning' in title_lower or 'energy' in title_lower or 'gas' in title_lower:
            return 'C1'
        elif 'book' in title_lower or 'learning' in title_lower or 'exam' in title_lower:
            return 'D0'
        elif 'it ' in title_lower or 'computer' in title_lower:
            return 'F0'
        elif 'training' in title_lower or 'course' in title_lower:
            return 'G0'
        elif 'redundancy' in title_lower:
            return 'G1'
        elif 'capital' in title_lower and 'income' in title_lower:
            return 'W0'
        elif 'capital' in title_lower:
            return 'W1'

        return 'ZZZ'

    def __init__(self):
        self.extracted_finance_codes: List[ExtractedFinanceCode] = []
        self.extracted_schools: List[ExtractedSchool] = []
        self.extracted_departments: List[ExtractedDepartment] = []
        self.extracted_funds: List[Dict] = []
        self.issues: List[str] = []
        self.assumptions: List[str] = []

        # Initialize InferenceEngine for intelligent decisions
        self.inference_engine = get_s1_inference_engine()
        self.inference_results: List[Dict] = []  # Track all inference decisions

        # Quality checking - validation results
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        self.duplicates_found: Dict[str, List[str]] = {
            'finance_codes': [],
            'schools': [],
            'departments': [],
            'funds': [],
        }

        self.template_data = {
            "System Grouping Codes": [],
            "CustomGroupings": [],
            "Funds": [],
            "Activity": [],
            "Ledger": [],
            "CustGroup": [],
            "SchHub": [],
            "SchType": [],
            "LocalAuth": [],
            "Schools": [],
            "Depts": [],
            "FinanceCodes Budget": [],
        }

        # Mapping from internal sheet names to official template sheet names
        self.SHEET_NAME_MAPPING = {
            "System Grouping Codes": "System Grouping Codes",
            "CustomGroupings": "03_CustGroup",
            "Funds": "01_Funds",
            "Activity": "02_Activity",
            "Ledger": "04_Ledger",
            "CustGroup": "03_CustGroup",
            "SchHub": "05_SchHub",
            "SchType": "06_SchType",
            "LocalAuth": "07_LocalAuth",
            "Schools": "08_Schools",
            "Depts": "09_Depts",
            "FinanceCodes Budget": "10_FinanceCodes Budget",
        }

        # Initialize template registry and formatter if available
        self.template_registry = None
        self.template_formatter = None
        if TEMPLATE_AVAILABLE:
            try:
                self.template_registry = TemplateRegistry()
                self.template_formatter = TemplateFormatter(self.template_registry)
            except Exception as e:
                self.log(f"[WARN] Could not initialize template registry: {e}")

        # Track extracted custom groupings
        self.custom_groupings_used = set()

        # Tracking for cross-validation
        self.local_authorities = {}
        self.school_types = {}
        self.school_hubs = {}
        self.ledger_codes = {}
        self.activities = {}
        self.fund_codes_used = set()  # Fund codes referenced in data
        self.fund_codes_defined = set()  # Fund codes actually defined
        self.finance_codes_defined = set()  # Finance codes already added (duplicate prevention)

        # External Audit Review tracking
        self.audit_results = {
            "source_vs_output": [],
            "data_integrity": [],
            "domain_checks": [],
            "missing_data": [],
            "data_lineage": [],
        }
        self.audit_passed = True
        self.audit_score = 100.0

        # Track source data for audit comparison
        self.source_finance_codes = set()
        self.source_schools = set()
        self.source_departments = set()

        # Precompute formatting rule sets for faster lookups
        self._format_standard_sets = {
            "boolean_columns": set(self.S1_FORMAT_STANDARDS["boolean_columns"]),
            "boolean_columns_lower": {c.lower() for c in self.S1_FORMAT_STANDARDS["boolean_columns"]},
            "code_columns": set(self.S1_FORMAT_STANDARDS["code_columns"]),
            "code_columns_lower": {c.lower() for c in self.S1_FORMAT_STANDARDS["code_columns"]},
            "multi_value_columns": set(self.S1_FORMAT_STANDARDS["multi_value_columns"]),
            "decimal_columns": self.S1_FORMAT_STANDARDS["decimal_columns"],
            "integer_columns": set(self.S1_FORMAT_STANDARDS["integer_columns"]),
        }

    def log(self, message: str, level: str = "INFO"):
        """Log a message with proper encoding and error handling for Streamlit."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg_str = str(message).replace('\x00', '').replace('\n\n', '\n')
            if len(msg_str) > 10000:
                msg_str = msg_str[:10000] + "... [truncated]"
            output = f"[{timestamp}] [{level}] S1-Specialist: {msg_str}"
            try:
                print(output, flush=True)
            except (OSError, IOError, ValueError):
                try:
                    print(output.encode('ascii', errors='replace').decode('ascii'), flush=True)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_column_mappings(self, df: pd.DataFrame, file_name: str, sheet_name: str = None) -> pd.DataFrame:
        """
        Apply validated column mappings from pre-flight validation.

        Args:
            df: DataFrame to apply mappings to
            file_name: Name of the file being processed
            sheet_name: Optional sheet name for Excel files

        Returns:
            DataFrame with columns renamed according to mappings
        """
        if not hasattr(self, 'column_mappings') or not self.column_mappings:
            return df

        # Try different key formats to find matching mappings
        possible_keys = [
            f"{file_name}:{sheet_name or 'default'}",
            f"{file_name}:default",
            file_name,
        ]

        file_mappings = {}
        for key in possible_keys:
            if key in self.column_mappings:
                file_mappings = self.column_mappings[key]
                break

        if not file_mappings:
            # Also try partial match on file name
            for key, mappings in self.column_mappings.items():
                if file_name in key or key.split(':')[0] in file_name:
                    file_mappings = mappings
                    break

        if file_mappings:
            # Build rename dict: only rename columns that exist in df
            rename_dict = {}
            for source_col, target_col in file_mappings.items():
                if source_col in df.columns and source_col != target_col:
                    rename_dict[source_col] = target_col

            if rename_dict:
                self.log(f"  Applying {len(rename_dict)} column mappings from pre-flight validation")
                df = df.rename(columns=rename_dict)

        return df

    # =========================================================================
    # INTELLIGENT COLUMN MAPPING
    # Uses InferenceEngine for confidence-scored column detection
    # =========================================================================

    def infer_column(self, source_column: str, fallback_patterns: List[str] = None) -> Tuple[str, float]:
        """
        Intelligently map a source column name to standard name.

        Args:
            source_column: Original column name from customer data
            fallback_patterns: Legacy patterns to check if inference unavailable

        Returns:
            Tuple of (mapped_column_name, confidence)
        """
        # Try InferenceEngine first
        if self.inference_engine:
            result = self.inference_engine.infer_column_mapping(
                source_column=source_column,
                strand="S1"
            )

            # Track inference for audit
            self.inference_results.append({
                "type": "column_mapping",
                "source": source_column,
                "result": result.decision,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            })

            if result.confidence >= 0.5:
                if result.requires_review:
                    self.assumptions.append(
                        f"Low confidence column mapping: {source_column} -> {result.decision} ({result.confidence:.0%})"
                    )
                return result.decision, result.confidence

        # Fallback to pattern matching
        if fallback_patterns:
            col_lower = source_column.lower().strip()
            for pattern in fallback_patterns:
                if pattern.lower() in col_lower:
                    return source_column, 0.7

        return source_column, 0.3

    def infer_data_type(self, columns: List[str], sample_data: pd.DataFrame = None) -> Tuple[str, float]:
        """
        Infer what type of S1 data this is (finance_codes, schools, departments, etc.)

        Args:
            columns: List of column names
            sample_data: Optional sample data for deeper analysis

        Returns:
            Tuple of (data_type, confidence)
        """
        if self.inference_engine:
            # Use rules for finance code detection
            cols_str = " ".join(c.lower() for c in columns)

            # Check patterns
            finance_patterns = sum(1 for p in self.FINANCE_CODE_COLUMN_PATTERNS if p in cols_str)
            school_patterns = sum(1 for p in self.SCHOOL_COLUMN_PATTERNS if p in cols_str)
            dept_patterns = sum(1 for p in self.DEPARTMENT_COLUMN_PATTERNS if p in cols_str)
            fund_patterns = sum(1 for p in self.FUND_COLUMN_PATTERNS if p in cols_str)

            scores = {
                'finance_codes': finance_patterns,
                'schools': school_patterns,
                'departments': dept_patterns,
                'funds': fund_patterns
            }

            best_type = max(scores, key=scores.get)
            total = sum(scores.values()) or 1
            confidence = scores[best_type] / total if scores[best_type] > 0 else 0.3

            return best_type, confidence

        return 'unknown', 0.3

    def get_inference_summary(self) -> Dict:
        """Get summary of all inference decisions made."""
        if not self.inference_results:
            return {"total": 0, "high_confidence": 0, "low_confidence": 0}

        high_conf = sum(1 for r in self.inference_results if r.get("confidence", 0) >= 0.9)
        med_conf = sum(1 for r in self.inference_results if 0.7 <= r.get("confidence", 0) < 0.9)
        low_conf = sum(1 for r in self.inference_results if r.get("confidence", 0) < 0.7)

        return {
            "total": len(self.inference_results),
            "high_confidence": high_conf,
            "medium_confidence": med_conf,
            "low_confidence": low_conf,
            "inference_available": self.inference_engine is not None
        }

    def _map_school_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Map customer column names to standard school column names.

        Uses InferenceEngine for intelligent matching, with fallback to pattern matching.
        """
        col_map = {}
        cols_lower = {c.lower(): c for c in columns}

        # Standard school columns we're looking for
        school_patterns = {
            'school_code': ['school_code', 'school_id', 'schoolcode', 'academy_code', 'site_code',
                           'establishment', 'school id', 'school code', 'code'],
            'school_name': ['school_name', 'schoolname', 'academy_name', 'name', 'title',
                           'school name', 'establishment_name', 'school'],
            'la_code': ['la_code', 'local_authority', 'local_auth', 'localauthority', 'la',
                       'local authority', 'la code'],
            'urn': ['urn', 'dfe_number', 'establishment_number', 'unique_reference',
                   'dfe number', 'school urn'],
            'school_type': ['school_type', 'type', 'phase', 'establishment_type', 'school type'],
            'school_hub': ['school_hub', 'hub', 'region', 'area', 'school hub'],
            'london_weighting': ['london_weighting', 'londonweighting', 'london_weight',
                                'weighting', 'london weighting'],
            'teaching_hours': ['teaching_hours', 'teachinghours', 'teaching hours', 'hours'],
        }

        for standard_col, patterns in school_patterns.items():
            # Try InferenceEngine first
            if self.inference_engine:
                for col in columns:
                    result = self.inference_engine.infer_column_mapping(col, 'S1')
                    if result.decision == standard_col and result.confidence >= 0.6:
                        col_map[standard_col] = col
                        break

            # Fallback to pattern matching if not found
            if standard_col not in col_map:
                for pattern in patterns:
                    if pattern in cols_lower:
                        col_map[standard_col] = cols_lower[pattern]
                        break
                    # Also check if pattern is contained in any column name
                    for col_lower, col_original in cols_lower.items():
                        if pattern in col_lower and standard_col not in col_map:
                            col_map[standard_col] = col_original
                            break

        return col_map

    def _map_department_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Map customer column names to standard department column names.

        Uses InferenceEngine for intelligent matching.
        """
        col_map = {}
        cols_lower = {c.lower(): c for c in columns}

        dept_patterns = {
            'department_code': ['department_code', 'dept_code', 'department', 'dept',
                               'cost_centre', 'cost_center', 'cc_code', 'costcentre', 'code'],
            'department_name': ['department_name', 'dept_name', 'name', 'title', 'description'],
            'ledger_code': ['ledger_code', 'ledger', 'gl_code'],
            'activity_code': ['activity_code', 'activity'],
            'fund_code': ['fund_code', 'fund'],
            'school_codes': ['school_codes', 'schools', 'school_code'],
        }

        for standard_col, patterns in dept_patterns.items():
            # Try InferenceEngine first
            if self.inference_engine:
                for col in columns:
                    result = self.inference_engine.infer_column_mapping(col, 'S1')
                    if result.decision == standard_col and result.confidence >= 0.6:
                        col_map[standard_col] = col
                        break

            # Fallback to pattern matching
            if standard_col not in col_map:
                for pattern in patterns:
                    if pattern in cols_lower:
                        col_map[standard_col] = cols_lower[pattern]
                        break
                    for col_lower, col_original in cols_lower.items():
                        if pattern in col_lower and standard_col not in col_map:
                            col_map[standard_col] = col_original
                            break

        return col_map

    # =========================================================================
    # S1 IMPORT FILE FORMAT STANDARDS
    # Based on analysis of knowledge/S1/import files/ CSV templates
    # =========================================================================

    # Standard column mappings to match import file conventions
    S1_FORMAT_STANDARDS = {
        # Boolean columns that should be True/False (capitalized)
        'boolean_columns': [
            'FundEnabled', 'ActivityEnabled', 'LedgerEnabled', 'SchoolHubEnabled',
            'SchoolTypeEnabled', 'SchoolLocalAuthorityEnabled', 'SchoolEnabled',
            'DepartmentEnabled', 'FinanceCodeEnabled', 'GenderEnabled',
            'CustomGroupingEnabled', 'AvailableToAllSchools', 'LondonWeighting',
            'Enabled', 'IsBalanceSheet', 'BalanceToScenario',
        ],
        # Code columns that should be UPPERCASE
        'code_columns': [
            'FundCode', 'ActivityCode', 'LedgerCode', 'SchoolHubCode', 'SchoolTypeCode',
            'SchoolLocalAuthorityCode', 'SchoolCode', 'DepartmentCode', 'FinanceCode',
            'GenderCode', 'CustomGroupingCode', 'GroupingCode', 'FinanceCodeTypeCode',
            'DefaultFinanceCode', 'SchoolHub', 'SchoolType',
        ],
        # Multi-value columns that are comma-separated (no spaces)
        'multi_value_columns': [
            'SchoolCodes',
        ],
        # Numeric columns with specific precision
        'decimal_columns': {
            'TeachingHours': 2,  # 32.5, 32.43
        },
        'integer_columns': [
            'UniqueReferenceNumber',
        ],
    }

    def _format_boolean(self, value) -> str:
        """Format boolean value as True/False string (capitalized, matching import files)."""
        if pd.isna(value) or value == '' or value is None:
            return 'False'
        if isinstance(value, bool):
            return 'True' if value else 'False'
        if isinstance(value, str):
            return 'True' if value.lower() in ('true', 'yes', '1', 'y') else 'False'
        return 'True' if value else 'False'

    def _format_code(self, value, uppercase: bool = True) -> str:
        """Format code values - UPPERCASE, no trailing decimals."""
        if pd.isna(value) or value == '' or value is None:
            return ''

        value = str(value).strip()
        if not value or value.lower() in ('nan', 'none'):
            return ''

        # Remove any trailing .0 from numeric codes
        if value.endswith('.0') and value[:-2].replace('.', '').isdigit():
            value = value[:-2]

        return value.upper() if uppercase else value

    def _format_school_codes(self, value) -> str:
        """
        Format school codes - comma-separated, NO spaces, NO quotes.
        Single: MIL
        Multiple: LEA,MIL,ALE,APP (no spaces after commas)
        """
        if pd.isna(value) or value == '' or value is None:
            return ''

        value = str(value).strip()
        if not value or value.lower() in ('nan', 'none'):
            return ''

        # Remove existing quotes
        value = value.strip('"\'')

        # Split and clean - handle both comma and comma+space
        codes = [c.strip().upper() for c in value.split(',') if c.strip()]

        if not codes:
            return ''

        # Join with comma only (no spaces) - matches import file format
        return ','.join(codes)

    def _format_numeric(self, value, decimals: int = None, is_integer: bool = False):
        """Format numeric value with appropriate precision."""
        if pd.isna(value) or value == '' or value is None:
            return 0 if is_integer else 0.0

        try:
            num = float(value)
            if is_integer:
                return int(num)
            if decimals is not None:
                return round(num, decimals)
            return num
        except (ValueError, TypeError):
            return 0 if is_integer else 0.0

    def _format_dataframe_for_export(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply S1 import file format standards to a DataFrame before export.
        This ensures output matches the expected format from import files.
        """
        if df is None or df.empty:
            return df

        df = df.copy()
        standards = self.S1_FORMAT_STANDARDS
        std_sets = self._format_standard_sets
        boolean_cols = std_sets["boolean_columns"]
        boolean_cols_lower = std_sets["boolean_columns_lower"]
        code_cols = std_sets["code_columns"]
        code_cols_lower = std_sets["code_columns_lower"]
        multi_value_cols = std_sets["multi_value_columns"]
        decimal_cols = std_sets["decimal_columns"]
        integer_cols = std_sets["integer_columns"]

        for col in df.columns:
            col_lower = col.lower()

            # Boolean formatting - check exact match or pattern match
            if col in boolean_cols or col_lower in boolean_cols_lower or col_lower.endswith('enabled') or col_lower == 'availabletoallschools':
                df[col] = df[col].apply(self._format_boolean)

            # Code formatting - UPPERCASE
            elif col in code_cols or col_lower in code_cols_lower or col_lower.endswith('code'):
                # Don't uppercase Title columns
                if 'title' not in col_lower:
                    df[col] = df[col].apply(lambda x: self._format_code(x, uppercase=True))

            # Multi-value columns (school codes) - comma-separated, no spaces
            elif col in multi_value_cols:
                df[col] = df[col].apply(self._format_school_codes)

            # Decimal columns with specific precision
            elif col in decimal_cols:
                decimals = decimal_cols[col]
                df[col] = df[col].apply(lambda x: self._format_numeric(x, decimals=decimals))

            # Integer columns
            elif col in integer_cols:
                df[col] = df[col].apply(lambda x: self._format_numeric(x, is_integer=True))

        return df

    # =========================================================================
    # QUALITY CHECKING & VALIDATION
    # =========================================================================

    def validate_finance_code(self, code: str) -> Tuple[bool, str]:
        """
        Validate finance code format.
        Finance codes are ALWAYS pure numeric, 4-6 digits.
        No letters allowed - alpha codes are Funds or Departments.
        """
        if not code:
            return False, "Empty code"

        code = str(code).strip()

        # Finance codes must be pure numeric
        if not code.isdigit():
            return False, f"Contains letters - not a finance code (may be Fund or Department)"

        # Must be 4-6 digits
        if len(code) < 4:
            return False, f"Too short ({len(code)} digits, need 4-6)"
        if len(code) > 6:
            return False, f"Too long ({len(code)} digits, need 4-6)"

        return True, f"Valid {len(code)}-digit finance code"

    def validate_extracted_data(self) -> Dict[str, Any]:
        """
        Validate all extracted data before building templates.
        Returns validation report.
        """
        self.log("="*60)
        self.log("VALIDATING EXTRACTED DATA")
        self.log("="*60)

        self.validation_errors = []
        self.validation_warnings = []

        # 1. Validate Finance Codes
        self._validate_finance_codes()

        # 2. Validate Schools
        self._validate_schools()

        # 3. Validate Departments
        self._validate_departments()

        # 4. Cross-validate relationships
        self._cross_validate_relationships()

        # 5. Check for duplicates
        self._check_duplicates()

        # Report results
        self.log(f"\nValidation Complete:")
        self.log(f"  Errors: {len(self.validation_errors)}")
        self.log(f"  Warnings: {len(self.validation_warnings)}")

        if self.validation_errors:
            self.log("\nERRORS:")
            for err in self.validation_errors[:10]:
                self.log(f"  - {err}")
            if len(self.validation_errors) > 10:
                self.log(f"  ... and {len(self.validation_errors) - 10} more")

        if self.validation_warnings:
            self.log("\nWARNINGS:")
            for warn in self.validation_warnings[:10]:
                self.log(f"  - {warn}")

        return {
            'valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'duplicates': self.duplicates_found,
        }

    def _validate_finance_codes(self):
        """Validate extracted finance codes."""
        self.log("Validating Finance Codes...")
        seen_codes = set()

        for fc in self.extracted_finance_codes:
            # Check format
            is_valid, msg = self.validate_finance_code(fc.code)
            if not is_valid:
                self.validation_errors.append(f"Finance Code '{fc.code}': {msg}")

            # Check for duplicates
            if fc.code in seen_codes:
                self.duplicates_found['finance_codes'].append(fc.code)
            seen_codes.add(fc.code)

            # Check title exists
            if not fc.title:
                self.validation_warnings.append(f"Finance Code '{fc.code}' has no title/description")

            # Check grouping code
            if fc.grouping_code == 'ZZZ':
                self.validation_warnings.append(f"Finance Code '{fc.code}' needs DFE grouping mapping")

        self.log(f"  Validated {len(self.extracted_finance_codes)} finance codes")

    def _validate_schools(self):
        """Validate extracted schools."""
        self.log("Validating Schools...")
        seen_codes = set()

        for school in self.extracted_schools:
            # Check code exists
            if not school.code:
                self.validation_errors.append("School with empty code found")
                continue

            # Check for duplicates
            if school.code in seen_codes:
                self.duplicates_found['schools'].append(school.code)
            seen_codes.add(school.code)

            # Check title exists
            if not school.title:
                self.validation_warnings.append(f"School '{school.code}' has no title")

            # Check LA code
            if not school.la_code:
                self.validation_warnings.append(f"School '{school.code}' has no Local Authority")

        self.log(f"  Validated {len(self.extracted_schools)} schools")

    def _validate_departments(self):
        """Validate extracted departments."""
        self.log("Validating Departments...")
        seen_codes = set()

        for dept in self.extracted_departments:
            # Check code exists
            if not dept.code:
                self.validation_errors.append("Department with empty code found")
                continue

            # Check for duplicates
            if dept.code in seen_codes:
                self.duplicates_found['departments'].append(dept.code)
            seen_codes.add(dept.code)

            # Check title exists
            if not dept.title:
                self.validation_warnings.append(f"Department '{dept.code}' has no title")

            # Track fund codes used
            if dept.fund_code:
                self.fund_codes_used.add(dept.fund_code)

        self.log(f"  Validated {len(self.extracted_departments)} departments")

    def _cross_validate_relationships(self):
        """Cross-validate relationships between data entities."""
        self.log("Cross-validating relationships...")

        # Check Fund codes used in Departments exist in Funds
        for fund_code in self.fund_codes_used:
            if fund_code not in self.fund_codes_defined and fund_code not in self.STANDARD_FUND_CODES:
                self.validation_warnings.append(
                    f"Fund code '{fund_code}' used in Department but not defined in Funds"
                )

        # Check School codes in Departments exist in Schools
        school_codes = {s.code for s in self.extracted_schools}
        for dept in self.extracted_departments:
            for sc in dept.school_codes:
                if sc and sc not in school_codes:
                    self.validation_warnings.append(
                        f"School code '{sc}' in Department '{dept.code}' not found in Schools"
                    )

    def _check_duplicates(self):
        """Report duplicate findings."""
        self.log("Checking for duplicates...")

        for entity_type, dupes in self.duplicates_found.items():
            if dupes:
                unique_dupes = list(set(dupes))
                self.validation_warnings.append(
                    f"Duplicate {entity_type}: {', '.join(unique_dupes[:5])}"
                    + (f" and {len(unique_dupes) - 5} more" if len(unique_dupes) > 5 else "")
                )

    def validate_output(self) -> Dict[str, Any]:
        """
        Validate output template data against Standard Workbook schema.
        """
        self.log("="*60)
        self.log("VALIDATING OUTPUT AGAINST STANDARD WORKBOOK SCHEMA")
        self.log("="*60)

        output_errors = []
        output_warnings = []

        # Required columns for each sheet
        required_columns = {
            'Schools': ['SchoolLocalAuthority', 'SchoolCode', 'SchoolHub', 'SchoolType',
                       'Title', 'LondonWeighting', 'UniqueReferenceNumber', 'TeachingHours', 'SchoolEnabled'],
            'Depts': ['DepartmentCode', 'Title', 'AvailableToAllSchools', 'SchoolCodes',
                     'ActivityCode', 'FundCode', 'LedgerCode', 'DefaultFinanceCode', 'DepartmentEnabled'],
            'FinanceCodes Budget': ['FinanceCode', 'Title', 'GroupingCode', 'CustomGrouping',
                                    'AvailableToAllSchools', 'SchoolCodes', 'FinanceCodeTypeCode',
                                    'LedgerCode', 'FinanceCodeEnabled', 'BalanceToScenario', 'IsBalanceSheet'],
            'Funds': ['FundCode', 'Title', 'FundEnabled'],
            'LocalAuth': ['SchoolLocalAuthorityCode', 'Title', 'SchoolLocalAuthorityEnabled'],
        }

        for sheet_name, required_cols in required_columns.items():
            data = self.template_data.get(sheet_name, [])

            if not data:
                output_warnings.append(f"Sheet '{sheet_name}' is empty")
                continue

            # Check first row has all required columns
            first_row = data[0]
            missing_cols = [col for col in required_cols if col not in first_row]

            if missing_cols:
                output_errors.append(
                    f"Sheet '{sheet_name}' missing columns: {', '.join(missing_cols)}"
                )

            self.log(f"  {sheet_name}: {len(data)} rows, "
                    f"{'OK' if not missing_cols else f'MISSING: {missing_cols}'}")

        return {
            'valid': len(output_errors) == 0,
            'errors': output_errors,
            'warnings': output_warnings,
        }

    # =========================================================================
    # PHASE 1: DEEP ANALYSIS
    # =========================================================================

    def analyze_customer_data(self, data_dir: Path):
        """Analyze all S1 customer data files."""
        self.log("="*60)
        self.log("PHASE 1: DEEP ANALYSIS OF S1 CUSTOMER DATA")
        self.log("="*60)

        all_files = list(data_dir.rglob("*.xls*")) + list(data_dir.rglob("*.csv"))
        all_files = [f for f in all_files if not f.name.startswith("~$")]

        self.log(f"Found {len(all_files)} files to analyze")

        for file_path in all_files:
            self.log(f"\nAnalyzing: {file_path.name}")
            self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path):
        """Analyze a single file."""
        try:
            # Extract school from filename
            school_name = self._extract_school_from_filename(file_path.name)
            if school_name:
                self._add_school_from_name(school_name, file_path.name)

            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
                # Apply validated column mappings
                df = self._apply_column_mappings(df, file_path.name)
                self._classify_and_extract(df, file_path.name, "CSV")
            else:
                xl = pd.ExcelFile(file_path)
                self.log(f"  Sheets: {xl.sheet_names}")

                # Also try to get school name from first row of first sheet
                if not school_name:
                    school_name = self._extract_school_from_sheet(xl)
                    if school_name:
                        self._add_school_from_name(school_name, file_path.name)

                for sheet in xl.sheet_names:
                    if self._is_skip_sheet(sheet):
                        continue

                    df = self._read_sheet_smart(xl, sheet)
                    if df is not None and len(df) > 0:
                        # Apply validated column mappings
                        df = self._apply_column_mappings(df, file_path.name, sheet)
                        self._classify_and_extract(df, file_path.name, sheet)

        except Exception as e:
            self.issues.append(f"Error analyzing {file_path.name}: {e}")

    def _extract_school_from_filename(self, filename: str) -> Optional[str]:
        """Extract school name from filename like 'Alexander Primary School Chart of Accounts Report.xlsx'."""
        # Remove common suffixes
        name = filename.replace('.xlsx', '').replace('.xls', '').replace('.csv', '')

        # Remove common report suffixes
        for suffix in ['Chart of Accounts Report', 'Chart of Accounts', 'COA Report', 'COA', 'Report']:
            if suffix in name:
                name = name.replace(suffix, '').strip()
                break

        # Clean up
        name = name.strip(' -_')

        if name and len(name) > 2:
            return name
        return None

    def _extract_school_from_sheet(self, xl: pd.ExcelFile) -> Optional[str]:
        """Extract school name from first row of first sheet."""
        try:
            df = pd.read_excel(xl, sheet_name=xl.sheet_names[0], header=None, nrows=1)
            if len(df) > 0:
                first_cell = df.iloc[0, 0]
                if pd.notna(first_cell):
                    name = str(first_cell).strip()
                    # Check if it looks like a school name
                    if any(kw in name.lower() for kw in ['school', 'academy', 'college', 'trust', 'primary', 'secondary']):
                        return name
        except:
            pass
        return None

    def _add_school_from_name(self, school_name: str, source: str):
        """Add a school extracted from filename or sheet header."""
        # Generate a code from the name
        code = self._generate_school_code(school_name)

        # Check for duplicates
        existing_codes = {s.code for s in self.extracted_schools}
        if code in existing_codes:
            return

        # Determine school type from name
        school_type = 'PRIMARY'
        name_lower = school_name.lower()
        if 'secondary' in name_lower:
            school_type = 'SECONDARY'
        elif 'academy' in name_lower:
            school_type = 'ACADEMY'
        elif 'college' in name_lower:
            school_type = 'COLLEGE'
        elif 'trust' in name_lower or 'central' in name_lower or 'mat' in name_lower:
            school_type = 'MAT'

        school = ExtractedSchool(
            code=code,
            title=school_name,
            la_code='DEFAULT',
            school_type=school_type,
            school_hub='DEFAULT',
            urn='',
            london_weighting='England & Wales',
            teaching_hours=32.5 if school_type != 'MAT' else 0,
        )
        self.extracted_schools.append(school)
        self.log(f"  School extracted: {code} - {school_name} ({school_type})")

    def _generate_school_code(self, name: str) -> str:
        """Generate a short code from school name."""
        # Take first letters of significant words
        words = name.split()
        significant_words = [w for w in words if w.lower() not in ['the', 'of', 'and', 'school', 'academy', 'primary', 'secondary']]

        if len(significant_words) >= 2:
            code = ''.join(w[0].upper() for w in significant_words[:3])
        elif significant_words:
            code = significant_words[0][:3].upper()
        else:
            code = name[:3].upper()

        return code

    def _is_skip_sheet(self, sheet: str) -> bool:
        """Check if sheet should be skipped."""
        skip_words = ['guidance', 'notes', 'instructions', 'help', 'checklist', 'validation']
        return any(w in sheet.lower() for w in skip_words)

    def _read_sheet_smart(self, xl: pd.ExcelFile, sheet: str) -> Optional[pd.DataFrame]:
        """Smart read that finds header row."""
        try:
            df_raw = pd.read_excel(xl, sheet, header=None, nrows=20)

            best_row = 0
            best_score = 0

            for idx in range(min(10, len(df_raw))):
                row = df_raw.iloc[idx]
                score = sum(1 for v in row if isinstance(v, str) and len(str(v).strip()) > 2)
                if score > best_score:
                    best_score = score
                    best_row = idx

            df = pd.read_excel(xl, sheet, header=best_row)
            df = df.dropna(how='all')
            df.columns = [self._clean_column_name(c) for c in df.columns]

            return df
        except:
            return None

    def _clean_column_name(self, col: Any) -> str:
        """Standardize column name - recognizes both Standard Workbook and alternate formats."""
        if pd.isna(col):
            return "unnamed"

        col_str = str(col).strip().lower()

        # EXACT mappings first (highest priority) - order matters!
        exact_mappings = {
            # Titles/descriptions - must check BEFORE partial matches
            'cost centre description': 'title',
            'department description': 'title',
            'dept description': 'title',
            'fund description': 'title',
            'school name': 'title',
            'establishment name': 'title',
            'title': 'title',
            'description': 'title',
            'name': 'title',
            # Finance codes
            'nominal': 'finance_code',
            'finance code': 'finance_code',
            'financecode': 'finance_code',
            'account code': 'finance_code',
            # Groupings
            'dfe': 'dfe_code',
            'grouping': 'grouping_code',
            'groupingcode': 'grouping_code',
            # Ledger
            'ledger': 'ledger_code',
            'ledgercode': 'ledger_code',
            # Departments/Cost Centres - EXACT match required
            'cost centre': 'department_code',
            'cost center': 'department_code',
            'costcentre': 'department_code',
            'costcenter': 'department_code',
            'department': 'department_code',
            'departmentcode': 'department_code',
            'deptcode': 'department_code',
            'dept': 'department_code',
            # Schools - recognize both formats
            'estab code': 'school_code',
            'establishment code': 'school_code',
            'schoolcode': 'school_code',
            'school code': 'school_code',
            'location code': 'school_code',
            # Local Authority - recognize both formats
            'schoollocalauthority': 'la_code',
            'schoollocalauthoritycode': 'la_code',
            'lacode': 'la_code',
            'la code': 'la_code',
            'local authority': 'la_code',
            # School Type - recognize both formats
            'schooltype': 'school_type',
            'schtypecode': 'school_type',
            'school type': 'school_type',
            # School Hub - recognize both formats
            'schoolhub': 'school_hub',
            'schhubcode': 'school_hub',
            'school hub': 'school_hub',
            'hub': 'school_hub',
            # URN - recognize both formats
            'uniquereferencenumber': 'urn',
            'unique reference number': 'urn',
            'urn': 'urn',
            # Fund
            'fund code': 'fund_code',
            'fund codes': 'fund_code',
            'fundcode': 'fund_code',
            # Activity
            'activity': 'activity_code',
            'activitycode': 'activity_code',
        }

        # Check EXACT matches first (after normalizing)
        if col_str in exact_mappings:
            return exact_mappings[col_str]

        # Then check for partial matches (less specific patterns)
        partial_mappings = [
            ('description', 'title'),
            ('ledger', 'ledger_code'),
            ('fund', 'fund_code'),
            ('activity', 'activity_code'),
            ('type', 'school_type'),
        ]

        for pattern, standard in partial_mappings:
            if pattern in col_str and col_str not in exact_mappings:
                return standard

        return col_str.replace(' ', '_')

    def _classify_and_extract(self, df: pd.DataFrame, file_name: str, sheet_name: str):
        """
        Classify data type and extract based on FILE NAME, sheet name, and data patterns.

        Classification Rules:
        - Finance Codes: ALWAYS pure numeric (4-6 digits), no letters
        - Funds: Short alpha codes (2-7 letters), no underscores
        - Departments/Cost Centres: Alpha with underscores or prefixes (A_, C_, S_, etc.)
        """
        cols = [str(c).lower() for c in df.columns]
        sheet_lower = sheet_name.lower()
        file_lower = file_name.lower()

        # Combine file name and sheet name for pattern matching
        # This ensures "Cost Centres.xlsx" with "Sheet1" is recognized as department data
        combined_context = f"{file_lower} {sheet_lower}"

        self.log(f"    Classifying: file='{file_name}', sheet='{sheet_name}'")

        # =====================================================================
        # FILE NAME + SHEET NAME based classification (highest priority)
        # =====================================================================

        # COST CENTRES / DEPARTMENTS - check file name AND sheet name
        if ('cost centre' in combined_context or 'cost center' in combined_context or
            'costcentre' in combined_context or 'dept' in combined_context):
            if 'group' not in combined_context:  # Exclude "Cost Centre Groups"
                self._extract_departments(df, sheet_name)
                self.log(f"    -> Departments/Cost Centres extracted from {file_name}/{sheet_name}")
                return

        # SCHOOLS - check file name AND sheet name
        if ('school' in combined_context or 'establishment' in combined_context or
            'location' in combined_context or 'academ' in combined_context):
            # But NOT if it's clearly a different type of file
            if 'fund' not in file_lower and 'finance' not in file_lower:
                self._extract_schools(df)
                self.log(f"    -> Schools extracted from {file_name}/{sheet_name}")
                return

        # FUNDS - check file name AND sheet name
        if 'fund' in combined_context:
            if 'code' in combined_context or 'list' in combined_context:
                self._extract_funds(df, sheet_name)
                self.log(f"    -> Fund codes extracted from {file_name}/{sheet_name}")
                return

        # FINANCE CODES - check file name AND sheet name
        finance_patterns = ['finance code', 'finance cost', 'nominal', 'chart of account',
                           'ledger code', 'analysis code', 'account code']
        if any(p in combined_context for p in finance_patterns):
            self._extract_mixed_codes(df, sheet_name)
            self.log(f"    -> Finance codes extracted from {file_name}/{sheet_name}")
            return

        # DFE MAPPINGS
        if 'dfe' in combined_context or 'mapping' in combined_context:
            self._extract_dfe_mappings(df)
            self.log(f"    -> DFE mappings extracted from {file_name}/{sheet_name}")
            return

        # =====================================================================
        # COLUMN-BASED classification (fallback)
        # =====================================================================

        # Check if columns suggest this is school data
        school_cols = ['school_code', 'schoolcode', 'estab code', 'establishment code',
                       'establishment name', 'school name', 'urn']
        if any(c in cols or c in ' '.join(cols) for c in school_cols):
            self._extract_schools(df)
            self.log(f"    -> Schools extracted (column match)")
            return

        # Check if columns suggest this is department/cost centre data
        dept_cols = ['department_code', 'cost centre', 'cost center', 'costcentre', 'dept']
        if any(c in cols or c in ' '.join(cols) for c in dept_cols):
            self._extract_departments(df, sheet_name)
            self.log(f"    -> Departments extracted (column match)")
            return

        # Check if columns suggest this is finance code data
        fc_cols = ['finance_code', 'nominal', 'account code']
        if any(c in cols for c in fc_cols):
            self._extract_mixed_codes(df, sheet_name)
            self.log(f"    -> Finance codes extracted (column match)")
            return

        # =====================================================================
        # ROW COUNT + DATA PATTERN classification (final fallback)
        # Key insight: Finance codes are ALWAYS the largest dataset
        # Typical counts: Finance Codes > 50, Departments 20-50, Schools/Funds < 20
        # =====================================================================
        row_count = len(df)

        # Analyze first column for code patterns
        first_col = df.columns[0] if len(df.columns) > 0 else None
        if first_col:
            sample = df[first_col].dropna().head(30)
            numeric_codes = 0
            alpha_codes = 0

            for val in sample:
                val_str = str(val).strip().replace('.0', '')
                if val_str.isdigit() and 4 <= len(val_str) <= 6:
                    numeric_codes += 1
                elif val_str.isalpha() or (val_str.isalnum() and not val_str.isdigit()):
                    alpha_codes += 1

            # Finance codes: Large dataset (50+) with numeric 4-6 digit codes
            if row_count >= 50 and numeric_codes >= len(sample) * 0.5:
                self.log(f"    Row count heuristic: {row_count} rows with numeric codes -> Finance Codes")
                self._extract_mixed_codes(df, sheet_name)
                self.log(f"    -> Finance codes extracted (row count heuristic: {row_count} rows)")
                return

            # Departments: Medium dataset (20-50) with alphanumeric codes
            if 20 <= row_count < 100 and alpha_codes >= len(sample) * 0.3:
                # But only if codes have patterns like A_, C_, S_ or underscores
                has_dept_pattern = any(
                    str(v).strip().startswith(('A_', 'C_', 'S_', 'T_')) or '_' in str(v)
                    for v in sample.head(10)
                )
                if has_dept_pattern:
                    self.log(f"    Row count heuristic: {row_count} rows with alpha codes -> Departments")
                    self._extract_departments(df, sheet_name)
                    self.log(f"    -> Departments extracted (row count heuristic: {row_count} rows)")
                    return

            # Funds: Small dataset (<25) with short alpha codes (2-7 chars)
            if row_count < 25 and alpha_codes >= len(sample) * 0.5:
                short_codes = sum(1 for v in sample if 2 <= len(str(v).strip()) <= 7)
                if short_codes >= len(sample) * 0.5:
                    self.log(f"    Row count heuristic: {row_count} rows with short alpha codes -> Funds")
                    self._extract_funds(df, sheet_name)
                    self.log(f"    -> Funds extracted (row count heuristic: {row_count} rows)")
                    return

        self.log(f"    -> No classification match for {file_name}/{sheet_name}")

    def _extract_mixed_codes(self, df: pd.DataFrame, sheet_name: str):
        """
        Extract from sheets that may contain mixed code types.
        Separates Finance Codes, Funds, and Departments based on code patterns.
        Uses intelligent column detection for various formats.
        """
        self.log(f"    Analyzing mixed codes in {sheet_name}...")

        # Find the code and title columns - try multiple strategies
        code_col = None
        title_col = None
        grouping_col = None

        # Strategy 1: Look for explicitly named columns
        for col in df.columns:
            col_lower = str(col).lower().strip()
            col_clean = self._clean_column_name(col)

            if col_clean == 'finance_code' or col_lower == 'code':
                code_col = col
            elif col_clean == 'title' or col_lower in ['title', 'description', 'name']:
                title_col = col
            elif col_clean == 'grouping_code' or col_lower in ['grouping', 'dfe', 'dfe code']:
                grouping_col = col

        # Strategy 2: If no code column found, look for columns with numeric values (4-6 digits)
        if not code_col:
            for col in df.columns:
                # Sample some values from the column
                sample = df[col].dropna().head(20)
                if len(sample) == 0:
                    continue

                # Count how many values look like finance codes (4-6 digit numbers)
                finance_like = 0
                for val in sample:
                    val_str = str(val).strip().replace('.0', '')  # Handle float formatting
                    if val_str.isdigit() and 4 <= len(val_str) <= 6:
                        finance_like += 1

                # If most values look like finance codes, use this column
                if finance_like >= len(sample) * 0.5:  # At least 50% are finance-like
                    code_col = col
                    self.log(f"    Auto-detected code column: '{col}' ({finance_like}/{len(sample)} finance-like values)")
                    break

        # Strategy 3: If still no code column, look for the rightmost numeric column
        if not code_col:
            for col in reversed(list(df.columns)):
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    # Check if values are numeric
                    try:
                        numeric_count = sum(1 for v in sample if str(v).replace('.', '').replace('-', '').isdigit())
                        if numeric_count >= len(sample) * 0.5:
                            code_col = col
                            self.log(f"    Using rightmost numeric column as code: '{col}'")
                            break
                    except:
                        pass

        # Strategy 4: Find title column if not found - look for longest text column
        if not title_col:
            best_col = None
            best_avg_len = 0
            for col in df.columns:
                if col == code_col:
                    continue
                sample = df[col].dropna().head(20)
                if len(sample) == 0:
                    continue
                # Calculate average length of string values
                avg_len = sum(len(str(v)) for v in sample) / len(sample)
                if avg_len > best_avg_len and avg_len > 10:  # Title should be descriptive
                    best_avg_len = avg_len
                    best_col = col

            if best_col:
                title_col = best_col
                self.log(f"    Auto-detected title column: '{title_col}'")

        # Strategy 5: Find custom grouping column (short uppercase alpha codes like INEFA, INGOV)
        custom_grouping_col = None
        if not grouping_col:
            for col in df.columns:
                if col == code_col or col == title_col:
                    continue
                sample = df[col].dropna().head(20)
                if len(sample) == 0:
                    continue
                # Check if values look like custom grouping codes (3-8 uppercase alpha chars)
                grouping_like = 0
                for val in sample:
                    val_str = str(val).strip().upper()
                    if val_str.isalpha() and 3 <= len(val_str) <= 8:
                        grouping_like += 1
                if grouping_like >= len(sample) * 0.5:
                    custom_grouping_col = col
                    self.log(f"    Auto-detected custom grouping column: '{col}' ({grouping_like}/{len(sample)} grouping-like values)")
                    break

        if not code_col:
            self.log(f"    WARNING: Could not find code column in {sheet_name}")
            self.log(f"    Columns available: {list(df.columns)}")
            return

        self.log(f"    Using columns: code='{code_col}', title='{title_col}', grouping='{grouping_col}'")

        counts = {
            'finance': 0,
            'fund': 0,
            'dept': 0,
            'activity': 0,
            'report': 0,
            'analysis': 0,
            'skipped': 0
        }

        for _, row in df.iterrows():
            code = row.get(code_col)
            if pd.isna(code):
                continue

            # Handle float formatting (510100.0 -> 510100)
            code_str = str(code).strip()
            if code_str.endswith('.0'):
                code_str = code_str[:-2]
            # Also handle scientific notation if any
            try:
                if 'e' in code_str.lower() or '.' in code_str:
                    code_str = str(int(float(code_str)))
            except (ValueError, OverflowError):
                pass

            if not code_str or code_str.lower() == 'nan':
                continue

            title = str(row.get(title_col, '')).strip() if title_col else ''
            if title.lower() == 'nan':
                title = ''

            # Get custom grouping value if column was detected
            custom_grp_val = None
            if custom_grouping_col:
                cg = row.get(custom_grouping_col)
                if pd.notna(cg):
                    custom_grp_val = str(cg).strip().upper()

            # Classify based on code pattern (order matters!)
            if self.is_finance_code(code_str):
                # Pure numeric 4-6 digits = Finance Code
                self._add_finance_code(code_str, title, row, custom_grp_val)
                counts['finance'] += 1

            elif self.is_report_code(code_str):
                # 3-digit numeric = Report/DFE Grouping Code
                self._add_report_code(code_str, title)
                counts['report'] += 1

            elif self.is_fund_code(code_str):
                # Single digit or short alpha = Fund
                if self._add_fund(code_str, title):
                    counts['fund'] += 1

            elif self.is_department_code(code_str):
                # Has underscore or prefix = Department/Cost Centre
                self._add_department(code_str, title, row)
                counts['dept'] += 1

            elif self.is_activity_code(code_str):
                # 2-3 letter codes = Activity (department grouping)
                self._add_activity(code_str, title)
                counts['activity'] += 1

            elif self.is_analysis_code(code_str):
                # Mixed alphanumeric = Analysis (trips/clubs)
                self._add_analysis_code(code_str, title)
                counts['analysis'] += 1

            else:
                counts['skipped'] += 1
                # Only warn if it's not obviously a header or empty
                if len(code_str) > 1:
                    self.validation_warnings.append(
                        f"Unknown code pattern in {sheet_name}: '{code_str}' - skipped"
                    )

        # Log summary
        extracted = [f"{v} {k}" for k, v in counts.items() if v > 0 and k != 'skipped']
        self.log(f"    -> Extracted: {', '.join(extracted)}")

    def _add_finance_code(self, code: str, title: str, row: pd.Series = None, detected_custom_grouping: str = None):
        """Add a finance code after validation."""
        # Finance codes must be pure numeric 4-6 digits
        if not self.is_finance_code(code):
            self.validation_warnings.append(f"Rejected non-numeric finance code: '{code}'")
            return

        code_str = self._normalize_finance_code(code)
        if not code_str:
            return

        # Get grouping code (DfE 6-digit) if available
        grouping = 'ZZZ'
        custom_grouping = 'ZZZ'
        finance_code_type = 'BUDGET'

        # Key intelligence: 6-digit codes ARE the DfE grouping codes
        # So if the finance code is 6 digits, use it as the grouping code too
        if len(code_str) == 6 and code_str.isdigit():
            grouping = code_str

        # Use detected custom grouping from column detection
        if detected_custom_grouping and detected_custom_grouping.isalpha():
            custom_grouping = detected_custom_grouping

        if row is not None:
            # DfE Grouping Code (6-digit like 510100) - if not already set
            if grouping == 'ZZZ':
                for col in ['grouping', 'groupingcode', 'dfe', 'report code', 'report_code']:
                    val = row.get(col) if col in row.index else None
                    if pd.notna(val):
                        grouping = str(val).strip()
                        break

            # Custom Grouping (A0, B0, C0, INEFA, INGOV, etc.) - if not already set
            if custom_grouping == 'ZZZ':
                for col in ['custom_grouping', 'customgrouping', 'custom']:
                    val = row.get(col) if col in row.index else None
                    if pd.notna(val):
                        custom_grouping = str(val).strip()
                        break

            # Finance Code Type (from Ledger Type column)
            for col in ['ledger_type', 'ledgertype', 'ledger type', 'type', 'financecodetyp', 'finance_code_type']:
                val = row.get(col) if col in row.index else None
                if pd.notna(val):
                    fc_type = str(val).strip().upper()
                    if fc_type in ['BUDGET', 'STATISTICS', 'PUPILNUMBERS', 'FUNDING', 'CAPITALFUND', 'REVENUEFUND']:
                        finance_code_type = fc_type
                    break

        code_type = self._determine_code_type(code_str)
        is_balance_sheet = code_type == 'balance_sheet'

        # Get ledger code - first try from source data, then infer
        ledger = None
        if row is not None:
            # Check all possible column name variations (case-insensitive)
            ledger_col_names = ['ledger_code', 'ledgercode', 'ledger', 'ledger code',
                               'LedgerCode', 'Ledger Code', 'Ledger', 'LEDGER', 'LEDGERCODE']
            for col in ledger_col_names:
                if col in row.index:
                    val = row.get(col)
                    if pd.notna(val):
                        ledger_val = str(val).strip().upper()
                        if ledger_val and ledger_val.lower() != 'nan':
                            ledger = ledger_val
                            break

        # Fall back to inferring ledger from code/title if not in source
        if not ledger:
            ledger = self._determine_ledger(code_str, title)

        # Track duplicates for reporting but KEEP all source data as-is
        if code_str in self.finance_codes_defined:
            self.duplicates_found['finance_codes'].append(code_str)
        else:
            self.finance_codes_defined.add(code_str)

        fc = ExtractedFinanceCode(
            code=code_str,
            title=title,
            grouping_code=grouping,
            custom_grouping=custom_grouping,
            ledger_code=ledger,
            school_codes=[],
            available_to_all=True,
            code_type=code_type,
            finance_code_type=finance_code_type,
            is_balance_sheet=is_balance_sheet,
            balance_to_scenario=False,
        )
        self.extracted_finance_codes.append(fc)

    def _add_fund(self, code: str, title: str):
        """Add a fund code after validation."""
        code = str(code).strip().upper()

        # Funds can be single digit or short alpha
        if not self.is_fund_code(code):
            # Don't warn - might be valid for other entity type
            return False

        # Check for duplicates
        if code in self.fund_codes_defined:
            return False

        self.fund_codes_defined.add(code)
        self.extracted_funds.append({
            'code': code,
            'title': title if title else code,
        })
        return True

    def _add_report_code(self, code: str, title: str):
        """Add a report/DFE grouping code (3-digit numeric)."""
        code = str(code).strip()
        if not self.is_report_code(code):
            return False

        # Store in system grouping codes for DFE mapping
        if code not in [g.get('code') for g in self.template_data.get('System Grouping Codes', [])]:
            self.template_data['System Grouping Codes'].append({
                'GroupingCode': code,
                'Title': title if title else f"Report Code {code}",
            })
        return True

    def _add_activity(self, code: str, title: str):
        """Add an activity code (2-3 letter department grouping)."""
        code = str(code).strip().upper()
        if not self.is_activity_code(code):
            return False

        # Track activities for department mapping
        if code not in self.activities:
            self.activities[code] = title if title else code
        return True

    def _add_analysis_code(self, code: str, title: str):
        """Add an analysis code (mixed alphanumeric for trips/clubs)."""
        code = str(code).strip().upper()
        # Analysis codes are informational - logged but not used directly in template
        # They may be used for trip tracking or activity budgeting
        self.log(f"    Analysis code found: {code} - {title}")
        return True

    def _add_department(self, code: str, title: str, row: pd.Series = None):
        """Add a department code after validation."""
        code = str(code).strip().upper()

        # Get additional fields if available
        activity = 'DEFAULT'
        fund = 'GAG'
        ledger = 'COSTCTR'

        if row is not None:
            for col in ['activity', 'activitycode']:
                val = row.get(col) if col in row.index else None
                if pd.notna(val):
                    activity = str(val).strip()
                    break
            for col in ['fund', 'fundcode', 'fund code']:
                val = row.get(col) if col in row.index else None
                if pd.notna(val):
                    fund = str(val).strip().upper()
                    break
            for col in ['ledger', 'ledgercode', 'ledger code']:
                val = row.get(col) if col in row.index else None
                if pd.notna(val):
                    ledger = str(val).strip()
                    break

        dept = ExtractedDepartment(
            code=code,
            title=title if title else code,
            ledger_code=ledger,
            activity_code=activity,
            school_codes=[],
            fund_code=fund,
            default_finance_code='',
        )
        self.extracted_departments.append(dept)

    def _extract_funds(self, df: pd.DataFrame, sheet_name: str):
        """Extract fund codes from a dedicated Funds sheet."""
        self.log(f"Extracting funds from {sheet_name}...")

        code_col = None
        title_col = None

        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'code' in col_lower and not code_col:
                code_col = col
            elif col_lower in ['title', 'description', 'name']:
                title_col = col

        if not code_col:
            return

        count = 0
        for _, row in df.iterrows():
            code = row.get(code_col)
            if pd.isna(code):
                continue

            code_str = str(code).strip().upper()
            if not code_str or code_str.lower() == 'nan':
                continue

            title = str(row.get(title_col, '')).strip() if title_col else ''

            self._add_fund(code_str, title)
            count += 1

        self.log(f"  Added {count} fund codes")

    def _extract_finance_codes(self, df: pd.DataFrame, sheet_name: str):
        """
        Extract finance codes from dataframe.
        IMPORTANT: Finance codes are ALWAYS pure numeric (4-6 digits).
        Alpha codes are routed to Funds or Departments.
        """
        code_col = None
        title_col = None
        grouping_col = None
        ledger_col = None

        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower == 'code' and not code_col:
                code_col = col
            elif ('nominal' in col_lower or 'account' in col_lower or 'finance' in col_lower) and not code_col:
                code_col = col
            elif col_lower in ['title', 'description', 'name'] or 'description' in col_lower:
                if not title_col:
                    title_col = col
            elif 'grouping' in col_lower or 'dfe' in col_lower or 'report code' in col_lower:
                if not grouping_col:
                    grouping_col = col
            elif 'ledger' in col_lower and not ledger_col:
                ledger_col = col

        if not code_col:
            return

        finance_count = 0
        skipped_alpha = 0
        skipped_duplicates = 0

        for _, row in df.iterrows():
            code = row.get(code_col)
            if pd.isna(code):
                continue

            code_str = str(code).strip()
            if not code_str or code_str.lower() == 'nan':
                continue

            title = str(row.get(title_col, '')).strip() if title_col else ''
            if title.lower() == 'nan':
                title = ''

            # CRITICAL: Finance codes must be pure numeric
            if not self.is_finance_code(code_str):
                # Route alpha codes to appropriate entity
                if self.is_fund_code(code_str):
                    self._add_fund(code_str.upper(), title)
                elif self.is_department_code(code_str):
                    self._add_department(code_str.upper(), title, row)
                else:
                    skipped_alpha += 1
                    self.validation_warnings.append(
                        f"Skipped non-numeric code in {sheet_name}: '{code_str}'"
                    )
                continue

            # Valid numeric finance code
            code_str = self._normalize_finance_code(code_str)
            if not code_str:
                continue

            # NEVER use defaults - use 'MISSING' if data not found
            grouping = str(row.get(grouping_col, '')).strip() if grouping_col else ''
            if not grouping or grouping.lower() == 'nan':
                grouping = 'MISSING'

            # Get ledger from source data first, then fall back to inference
            ledger = None
            if ledger_col:
                ledger_val = row.get(ledger_col)
                if pd.notna(ledger_val):
                    ledger = str(ledger_val).strip().upper()
                    if ledger.lower() == 'nan':
                        ledger = None

            code_type = self._determine_code_type(code_str)

            # Fall back to inferring ledger if not in source
            if not ledger:
                ledger = self._determine_ledger(code_str, title)

            finance_code_type = self.determine_finance_code_type(code_str, title)
            custom_grouping = self.determine_custom_grouping(code_str, title, grouping)
            is_balance_sheet = code_type == 'balance_sheet'

            # Check for duplicates before adding
            if code_str in self.finance_codes_defined:
                self.duplicates_found['finance_codes'].append(code_str)
                skipped_duplicates += 1
                continue

            self.finance_codes_defined.add(code_str)

            fc = ExtractedFinanceCode(
                code=code_str,
                title=title,
                grouping_code=grouping,
                custom_grouping=custom_grouping,
                ledger_code=ledger,
                school_codes=[],
                available_to_all=True,
                code_type=code_type,
                finance_code_type=finance_code_type,
                is_balance_sheet=is_balance_sheet,
                balance_to_scenario=False,
            )
            self.extracted_finance_codes.append(fc)
            finance_count += 1

        self.log(f"  Extracted {finance_count} finance codes" +
                (f" (skipped {skipped_alpha} alpha codes)" if skipped_alpha else "") +
                (f" (skipped {skipped_duplicates} duplicates)" if skipped_duplicates else ""))

    def _normalize_finance_code(self, code: str) -> str:
        """
        Normalize finance code format.
        Finance codes are ALWAYS pure numeric, 4-6 digits.
        No letters allowed.
        """
        code = str(code).strip()

        # Remove non-numeric characters
        code = re.sub(r'[^\d]', '', code)

        # Skip empty or invalid
        if not code:
            return ''

        # Reject alpha codes completely
        if not code.isdigit():
            return ''

        # Pad short codes (1-3 digits) to 4 digits
        if len(code) < 4:
            code = code.zfill(4)

        # Validate length (4-6 digits)
        if len(code) > 6:
            self.validation_warnings.append(f"Finance code '{code}' exceeds 6 digits")

        return code

    def _determine_code_type(self, code: str) -> str:
        """Determine finance code type from code."""
        if not code or not code[0].isdigit():
            return 'other'

        first_digit = int(code[0])

        if first_digit in [0, 1, 2, 3]:
            return 'balance_sheet'
        elif first_digit in [4, 5]:
            return 'income'
        elif first_digit in [6, 7, 8, 9]:
            return 'expenditure'

        return 'other'

    def _determine_ledger(self, code: str, title: str) -> str:
        """Determine ledger code from finance code and title keywords."""
        title_lower = title.lower() if title else ''
        code_str = str(code).strip()

        # TRIPS ledger - for educational visits and trips
        if 'trip' in title_lower or 'visit' in title_lower or 'excursion' in title_lower:
            return 'TRIPS'

        # CAPITAL ledger - for capital items
        if 'capital' in title_lower or 'dfc' in title_lower or 'cif' in title_lower:
            return 'CAPITAL'
        # Capital codes typically start with 8
        if code_str.isdigit() and code_str.startswith('8'):
            return 'CAPITAL'

        # PREMISES ledger - for building/site costs
        if any(kw in title_lower for kw in ['premises', 'building', 'maintenance', 'cleaning',
                                             'energy', 'gas', 'electric', 'water', 'rates',
                                             'rent', 'security', 'ground']):
            return 'PREMISES'
        # Premises codes typically in 3000-3999 range
        if code_str.isdigit() and 3000 <= int(code_str) < 4000:
            return 'PREMISES'

        # STAFFING ledger - for staff costs
        if any(kw in title_lower for kw in ['staff', 'salary', 'salaries', 'wages', 'ni',
                                             'pension', 'supn', 'teacher', 'support',
                                             'admin', 'catering staff', 'premises staff']):
            return 'COSTCTR'  # Staff costs go to COSTCTR in standard setup
        # Staff codes typically in 2000-2999 range
        if code_str.isdigit() and 2000 <= int(code_str) < 3000:
            return 'COSTCTR'

        # SUPPLIES ledger (optional - often mapped to COSTCTR)
        if any(kw in title_lower for kw in ['supplies', 'equipment', 'books', 'stationery',
                                             'it ', 'computer', 'furniture']):
            return 'COSTCTR'

        # Default to COSTCTR for standard budget items
        return 'COSTCTR'

    def _extract_schools(self, df: pd.DataFrame):
        """
        Extract schools from dataframe - recognizes both Standard Workbook and alternate formats.

        Uses intelligent column mapping to recognize various column name variations:
        - school_code, school_id, academy_code, site_code, establishment
        - school_name, name, title, academy_name
        - la_code, local_authority, local_auth
        - urn, dfe_number, establishment_number
        """
        # Map columns intelligently
        col_map = self._map_school_columns(df.columns.tolist())

        self.log(f"    School column mapping: {col_map}")

        code_col = col_map.get('school_code')
        name_col = col_map.get('school_name') or col_map.get('title')
        la_col = col_map.get('la_code')
        urn_col = col_map.get('urn')
        type_col = col_map.get('school_type')
        hub_col = col_map.get('school_hub')
        lw_col = col_map.get('london_weighting')
        hours_col = col_map.get('teaching_hours')

        if not code_col:
            self.log("    WARNING: No school code column found")
            self.issues.append("School sheet found but no school code column detected")
            return

        extracted_count = 0
        for _, row in df.iterrows():
            code = row.get(code_col)
            if pd.isna(code):
                continue

            code_str = str(code).strip()
            if not code_str or code_str == 'nan':
                continue

            title = str(row.get(name_col, '')).strip() if name_col else ''
            la_code = str(row.get(la_col, '')).strip() if la_col else ''
            urn = str(row.get(urn_col, '')).strip() if urn_col else ''
            school_type = str(row.get(type_col, '')).strip() if type_col else ''
            school_hub = str(row.get(hub_col, '')).strip() if hub_col else ''

            # Extract London Weighting - check mapped column or defaults
            london_weighting = 'England & Wales'
            if lw_col:
                lw_val = row.get(lw_col)
                if pd.notna(lw_val) and str(lw_val).strip() != 'nan':
                    london_weighting = str(lw_val).strip()

            # Extract Teaching Hours
            teaching_hours = 32.5
            if hours_col:
                try:
                    hours_val = row.get(hours_col)
                    teaching_hours = float(hours_val) if pd.notna(hours_val) else 32.5
                except (ValueError, TypeError):
                    teaching_hours = 32.5

            school = ExtractedSchool(
                code=code_str,
                title=title if title != 'nan' else code_str,
                la_code=la_code if la_code != 'nan' else '',
                school_type=school_type if school_type != 'nan' else '',
                school_hub=school_hub if school_hub != 'nan' else '',
                urn=urn if urn != 'nan' else '',
                london_weighting=str(london_weighting),
                teaching_hours=teaching_hours,
            )
            self.extracted_schools.append(school)

            # Track LA
            if school.la_code:
                self.local_authorities[school.la_code] = school.la_code

    def _extract_departments(self, df: pd.DataFrame, sheet_name: str = ""):
        """
        Extract departments/cost centres from dataframe.
        Handles multiple column naming conventions (Cost Centre, Department, etc.)
        """
        self.log(f"Extracting departments from {sheet_name}...")
        count = 0

        # Find the code and title columns dynamically based on cleaned column names
        code_col = None
        title_col = None
        ledger_col = None
        activity_col = None
        fund_col = None

        for col in df.columns:
            col_clean = self._clean_column_name(col)

            if col_clean == 'department_code' and code_col is None:
                code_col = col
            elif col_clean == 'title' and title_col is None:
                title_col = col
            elif col_clean == 'ledger_code':
                ledger_col = col
            elif col_clean == 'activity_code':
                activity_col = col
            elif col_clean == 'fund_code':
                fund_col = col

        self.log(f"    Column mapping: code='{code_col}', title='{title_col}'")

        if not code_col:
            self.log(f"    WARNING: No department/cost centre code column found in columns: {list(df.columns)}")
            return

        for _, row in df.iterrows():
            code = row.get(code_col)
            if pd.isna(code):
                continue

            code_str = str(code).strip().upper()
            if not code_str or code_str.lower() == 'nan':
                continue

            # Reject pure numeric codes - those are finance codes
            if code_str.isdigit():
                if self.is_finance_code(code_str):
                    title_val = row.get(title_col, '') if title_col else ''
                    self._add_finance_code(code_str, str(title_val).strip(), row)
                continue

            # Get title from title column or use code as fallback
            if title_col and title_col in row.index:
                title = str(row.get(title_col, code_str)).strip()
            else:
                title = code_str

            # NEVER use defaults - use 'MISSING' if data not found
            ledger = str(row.get(ledger_col, '')).strip() if ledger_col else ''
            activity = str(row.get(activity_col, '')).strip() if activity_col else ''
            fund = str(row.get(fund_col, '')).strip() if fund_col else ''

            # Check for duplicate
            if any(d.code == code_str for d in self.extracted_departments):
                continue

            dept = ExtractedDepartment(
                code=code_str,
                title=title if title.lower() != 'nan' else code_str,
                ledger_code=ledger if ledger and ledger.lower() != 'nan' else 'MISSING',
                activity_code=activity if activity and activity.lower() != 'nan' else 'MISSING',
                school_codes=[],
                fund_code=fund.upper() if fund and fund.lower() != 'nan' else 'MISSING',
                default_finance_code='',
            )
            self.extracted_departments.append(dept)
            self.source_departments.add(code_str)
            count += 1

        self.log(f"  Extracted {count} departments")

    def _extract_dfe_mappings(self, df: pd.DataFrame):
        """Extract DFE COA mappings."""
        # Update existing finance codes with DFE grouping codes
        for _, row in df.iterrows():
            code = row.get('finance_code') or row.get('code')
            dfe = row.get('dfe_code') or row.get('grouping_code')

            if pd.isna(code) or pd.isna(dfe):
                continue

            code_str = self._normalize_finance_code(str(code))
            dfe_str = str(dfe).strip()

            # Update matching finance code
            for fc in self.extracted_finance_codes:
                if fc.code == code_str:
                    fc.grouping_code = dfe_str
                    break

    # =========================================================================
    # PHASE 2: BUILD ALL TEMPLATE SHEETS
    # =========================================================================

    def build_all_templates(self) -> Dict[str, pd.DataFrame]:
        """Build ALL S1 template sheets."""
        self.log("\n" + "="*60)
        self.log("PHASE 2: BUILDING ALL S1 TEMPLATE SHEETS")
        self.log("="*60)

        self._build_system_grouping_codes()
        self._build_custom_groupings()
        self._build_funds()
        self._build_activity()
        self._build_ledger()
        self._build_cust_group()
        self._build_sch_hub()
        self._build_sch_type()
        self._build_local_auth()
        self._build_schools()
        self._build_depts()
        self._build_finance_codes_budget()

        # Convert to DataFrames and apply S1 import file format standards
        self.log("\nApplying S1 import file format standards...")
        result = {}
        for sheet_name, data in self.template_data.items():
            if data:
                df = pd.DataFrame(data)
                # Apply formatting standards to match import file conventions
                df = self._format_dataframe_for_export(df)
                result[sheet_name] = df
                self.log(f"  {sheet_name}: {len(data)} rows (formatted)")

        return result

    def _build_system_grouping_codes(self):
        """Build System Grouping Codes sheet."""
        self.log("Building System Grouping Codes...")

        # DFE standard grouping codes
        dfe_codes = [
            ("510100", "GAG Pre-16", "I01"),
            ("510200", "Pupil Premium", "I02"),
            ("510700", "GAG Post-16", "I03"),
            ("520100", "Other DFE Grants", "I04"),
            ("530100", "Other Government Grants", "I05"),
            ("610100", "Staff Costs - Leadership", "E01"),
            ("612100", "Staff Costs - Teachers", "E02"),
            ("615100", "Staff Costs - Teaching Assistants", "E03"),
            ("625100", "Staff Costs - Admin", "E04"),
            ("700100", "Premises", "E05"),
            ("750100", "Supplies & Services", "E06"),
            ("ZZZ", "Needs Mapping", "Z01"),
        ]

        for code, title, level in dfe_codes:
            self.template_data["System Grouping Codes"].append({
                "GroupingCode": code,
                "Title": title,
                "Level": level,
                "GroupingCodeEnabled": True,
            })

    def _build_custom_groupings(self):
        """Build CustomGroupings sheet - Trust-defined categories (A0, B0, etc.)."""
        self.log("Building CustomGroupings...")

        # Build from the standard mapping
        for code, title in self.CUSTOM_GROUPING_MAP.items():
            self.template_data["CustomGroupings"].append({
                "CustomGroupingCode": code,
                "Title": title,
                "CustomGroupingEnabled": True,
            })

    def _build_funds(self):
        """Build Funds sheet."""
        self.log("Building Funds...")

        # Standard funds matching DEM003 import format
        default_funds = [
            ("CAP", "CAP Fund"),
            ("DEFAULT", "Default Fund"),
            ("GAG", "GAG Fund"),
            ("PPREM", "PPREM Fund"),
            ("REST", "REST Fund"),
            ("UNRF", "UNRF Fund"),
        ]

        added_codes = set()

        # Add extracted funds first
        if self.extracted_funds:
            for fund in self.extracted_funds:
                code = fund.get('code', '')
                title = fund.get('title', code)
                if code and code not in added_codes:
                    self.template_data["Funds"].append({
                        "FundCode": code,
                        "Title": title,
                        "FundEnabled": True,
                    })
                    added_codes.add(code)

        # Add default funds if not already present
        for code, title in default_funds:
            if code not in added_codes:
                self.template_data["Funds"].append({
                    "FundCode": code,
                    "Title": title,
                    "FundEnabled": True,
                })
                added_codes.add(code)

    def _build_activity(self):
        """Build Activity sheet - matching DEM003 import format."""
        self.log("Building Activity...")

        # Standard activities matching DEM003 format
        default_activities = [
            ("DEFAULT", "Default (no) Activity"),
            ("SPORTS", "SPORTS"),
            ("CURRICULUM", "Curriculum"),
            ("SUPPORT", "Support Services"),
            ("PREMISES", "Premises"),
            ("GOVERNANCE", "Governance"),
            ("CENTRAL", "Central Services"),
        ]

        added_codes = set()

        # Add any activities found in extracted data
        for activity_code, activity_title in self.activities.items():
            if activity_code and activity_code not in added_codes:
                self.template_data["Activity"].append({
                    "ActivityCode": activity_code,
                    "Title": activity_title,
                    "ActivityEnabled": True,
                })
                added_codes.add(activity_code)

        # Add default activities if not already present
        for code, title in default_activities:
            if code not in added_codes:
                self.template_data["Activity"].append({
                    "ActivityCode": code,
                    "Title": title,
                    "ActivityEnabled": True,
                })
                added_codes.add(code)

    def _build_ledger(self):
        """Build Ledger sheet - matching DEM003 import format with all common ledger types."""
        self.log("Building Ledger...")

        # Standard ledgers - includes all common types
        ledgers = [
            ("CAPITAL", "Capital"),
            ("COSTCTR", "Cost Centres"),
            ("DEFAULT", "Default Ledger needs remapping"),
            ("PREMISES", "Premises"),
            ("STAFFING", "Staffing"),
            ("SUPPLIES", "Supplies & Services"),
            ("TRIPS", "Trips"),
            ("ZZZ_IMP", "IMP codes"),
        ]

        added_codes = set()

        # Add any ledger codes found in extracted data
        for fc in self.extracted_finance_codes:
            if fc.ledger_code and fc.ledger_code not in added_codes:
                # Check if it's a standard code or new one
                is_standard = any(fc.ledger_code == l[0] for l in ledgers)
                if not is_standard:
                    self.template_data["Ledger"].append({
                        "LedgerCode": fc.ledger_code,
                        "Title": fc.ledger_code,
                        "LedgerEnabled": True,
                    })
                    added_codes.add(fc.ledger_code)

        for dept in self.extracted_departments:
            if dept.ledger_code and dept.ledger_code not in added_codes:
                is_standard = any(dept.ledger_code == l[0] for l in ledgers)
                if not is_standard:
                    self.template_data["Ledger"].append({
                        "LedgerCode": dept.ledger_code,
                        "Title": dept.ledger_code,
                        "LedgerEnabled": True,
                    })
                    added_codes.add(dept.ledger_code)

        # Add standard ledgers
        for code, title in ledgers:
            if code not in added_codes:
                self.template_data["Ledger"].append({
                    "LedgerCode": code,
                    "Title": title,
                    "LedgerEnabled": True,
                })
                added_codes.add(code)

    def _build_cust_group(self):
        """Build CustGroup sheet."""
        self.log("Building CustGroup...")

        self.template_data["CustGroup"].append({
            "CustGroupCode": "ZZZ",
            "Title": "Unmapped",
            "CustGroupEnabled": True,
        })

    def _build_sch_hub(self):
        """Build SchHub sheet."""
        self.log("Building SchHub...")

        # Create from extracted schools if available
        hubs_created = set()

        if self.extracted_schools:
            for school in self.extracted_schools:
                if school.school_hub and school.school_hub not in hubs_created:
                    self.template_data["SchHub"].append({
                        "SchHubCode": school.school_hub,
                        "Title": school.school_hub,
                        "SchHubEnabled": True,
                    })
                    hubs_created.add(school.school_hub)

        # Add default if none
        if not self.template_data["SchHub"]:
            self.template_data["SchHub"].append({
                "SchHubCode": "DEFAULT",
                "Title": "Default Hub",
                "SchHubEnabled": True,
            })

    def _build_sch_type(self):
        """Build SchType sheet."""
        self.log("Building SchType...")

        types = [
            ("PRIMARY", "Primary"),
            ("SECONDARY", "Secondary"),
            ("SPECIAL", "Special"),
            ("AP", "Alternative Provision"),
            ("ALL_THROUGH", "All-Through"),
            ("NURSERY", "Nursery"),
            ("MAT", "MAT Central"),
        ]

        for code, title in types:
            self.template_data["SchType"].append({
                "SchTypeCode": code,
                "Title": title,
                "SchTypeEnabled": True,
            })

    def _build_local_auth(self):
        """Build LocalAuth sheet."""
        self.log("Building LocalAuth...")

        # From extracted or defaults
        if self.local_authorities:
            for la_code in self.local_authorities:
                self.template_data["LocalAuth"].append({
                    "SchoolLocalAuthorityCode": la_code,
                    "Title": la_code,
                    "SchoolLocalAuthorityEnabled": True,
                })
        else:
            self.template_data["LocalAuth"].append({
                "SchoolLocalAuthorityCode": "DEFAULT",
                "Title": "Default LA",
                "SchoolLocalAuthorityEnabled": True,
            })

    def _build_schools(self):
        """Build Schools sheet - outputs Standard Workbook format, accepts multiple input formats."""
        self.log("Building Schools...")

        if self.extracted_schools:
            for school in self.extracted_schools:
                self.template_data["Schools"].append({
                    "SchoolLocalAuthority": school.la_code or "DEFAULT",
                    "SchoolCode": school.code,
                    "SchoolHub": school.school_hub or "DEFAULT",
                    "SchoolType": school.school_type or "PRIMARY",
                    "Title": school.title,
                    "LondonWeighting": school.london_weighting,
                    "UniqueReferenceNumber": school.urn,
                    "TeachingHours": school.teaching_hours,
                    "SchoolEnabled": True,
                })
        else:
            # Add MAT default
            self.template_data["Schools"].append({
                "SchoolLocalAuthority": "DEFAULT",
                "SchoolCode": "MAT",
                "SchoolHub": "DEFAULT",
                "SchoolType": "MAT",
                "Title": "MAT Central",
                "LondonWeighting": "England & Wales",
                "UniqueReferenceNumber": "",
                "TeachingHours": 0,
                "SchoolEnabled": True,
            })

    def _build_depts(self):
        """Build Depts sheet - outputs Standard Workbook format, accepts multiple input formats."""
        self.log("Building Depts...")

        if self.extracted_departments:
            for dept in self.extracted_departments:
                self.template_data["Depts"].append({
                    "DepartmentCode": dept.code,
                    "Title": dept.title,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": ",".join(dept.school_codes) if dept.school_codes else "",
                    "ActivityCode": dept.activity_code,
                    "FundCode": dept.fund_code,
                    "LedgerCode": dept.ledger_code,
                    "DefaultFinanceCode": dept.default_finance_code,
                    "DepartmentEnabled": True,
                })
        else:
            # Standard departments
            standard_depts = [
                ("STCH", "Staff Teaching", "STAFFING", "CURRICULUM", "GAG"),
                ("SFIN", "Staff Finance", "STAFFING", "SUPPORT", "GAG"),
                ("SPREM", "Staff Premises", "STAFFING", "PREMISES", "GAG"),
                ("CURRICULUM", "Curriculum", "COSTCTR", "CURRICULUM", "GAG"),
                ("ADMIN", "Administration", "COSTCTR", "SUPPORT", "GAG"),
                ("PREMISES", "Premises", "PREMISES", "PREMISES", "GAG"),
                ("DEFAULT", "Default", "DEFAULT", "SUPPORT", "DEFAULT"),
            ]

            for code, title, ledger, activity, fund in standard_depts:
                self.template_data["Depts"].append({
                    "DepartmentCode": code,
                    "Title": title,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "ActivityCode": activity,
                    "FundCode": fund,
                    "LedgerCode": ledger,
                    "DefaultFinanceCode": "",
                    "DepartmentEnabled": True,
                })

    def _build_finance_codes_budget(self):
        """Build FinanceCodes Budget sheet - outputs Standard Workbook format with proper types."""
        self.log("Building FinanceCodes Budget...")

        if self.extracted_finance_codes:
            for fc in self.extracted_finance_codes:
                # Track custom grouping used
                if fc.custom_grouping and fc.custom_grouping != 'ZZZ':
                    self.custom_groupings_used.add(fc.custom_grouping)

                self.template_data["FinanceCodes Budget"].append({
                    "IsBalanceSheet": fc.is_balance_sheet,
                    "GroupingCode": fc.grouping_code,
                    "CustomGrouping": fc.custom_grouping,
                    "FinanceCode": fc.code,
                    "Title": fc.title,
                    "AvailableToAllSchools": fc.available_to_all,
                    "SchoolCodes": ",".join(fc.school_codes) if fc.school_codes else "",
                    "FinanceCodeTypeCode": fc.finance_code_type,
                    "LedgerCode": fc.ledger_code,
                    "FinanceCodeEnabled": True,
                    "BalanceToScenario": fc.balance_to_scenario,
                })

    # =========================================================================
    # EXTERNAL AUDIT REVIEW
    # =========================================================================

    def perform_external_audit(self, customer_data_dir: Path) -> Dict[str, Any]:
        """
        External Audit Review - Compare source data against processed output.
        Validates data integrity, completeness, and accuracy.
        """
        self.log("\n" + "="*60)
        self.log("EXTERNAL AUDIT REVIEW")
        self.log("="*60)

        # Reset audit results
        self.audit_results = {
            "source_vs_output": [],
            "data_integrity": [],
            "domain_checks": [],
            "missing_data": [],
            "data_lineage": [],
        }
        self.audit_passed = True
        self.audit_score = 100.0

        # 1. Source vs Output comparison
        self._audit_source_vs_output()

        # 2. Data integrity checks
        self._audit_data_integrity()

        # 3. Domain-specific checks
        self._audit_domain_rules()

        # 4. Missing/incomplete data
        self._audit_missing_data()

        # 5. Data lineage verification
        self._audit_data_lineage(customer_data_dir)

        # Calculate final audit score
        self._calculate_audit_score()

        # Log audit summary
        self._log_audit_summary()

        # Generate detailed report with explanations
        self.detailed_audit_report = self._generate_detailed_audit_report()

        return {
            "passed": self.audit_passed,
            "score": self.audit_score,
            "results": self.audit_results,
            "detailed_report": self.detailed_audit_report,
        }

    def _audit_source_vs_output(self):
        """Compare source data counts against output."""
        self.log("Auditing: Source vs Output comparison...")

        checks = []

        # Finance codes
        source_fc_count = len(self.source_finance_codes)
        output_fc_count = len(self.extracted_finance_codes)
        fc_match = source_fc_count == output_fc_count or source_fc_count == 0

        checks.append({
            "check": "Finance Codes Count",
            "source_count": source_fc_count,
            "output_count": output_fc_count,
            "passed": fc_match,
            "severity": "error" if not fc_match and source_fc_count > 0 else "info",
            "details": f"Source: {source_fc_count}, Output: {output_fc_count}"
        })

        # Schools
        source_sch_count = len(self.source_schools)
        output_sch_count = len(self.extracted_schools)
        sch_match = source_sch_count == output_sch_count or source_sch_count == 0

        checks.append({
            "check": "Schools Count",
            "source_count": source_sch_count,
            "output_count": output_sch_count,
            "passed": sch_match,
            "severity": "error" if not sch_match and source_sch_count > 0 else "info",
            "details": f"Source: {source_sch_count}, Output: {output_sch_count}"
        })

        # Departments
        source_dept_count = len(self.source_departments)
        output_dept_count = len(self.extracted_departments)
        dept_match = source_dept_count == output_dept_count or source_dept_count == 0

        checks.append({
            "check": "Departments Count",
            "source_count": source_dept_count,
            "output_count": output_dept_count,
            "passed": dept_match,
            "severity": "warning" if not dept_match and source_dept_count > 0 else "info",
            "details": f"Source: {source_dept_count}, Output: {output_dept_count}"
        })

        # Check for missing finance codes
        if self.source_finance_codes:
            output_codes = {fc.code for fc in self.extracted_finance_codes}
            missing_codes = self.source_finance_codes - output_codes
            if missing_codes:
                checks.append({
                    "check": "Missing Finance Codes",
                    "passed": False,
                    "severity": "error",
                    "details": f"Missing: {', '.join(list(missing_codes)[:10])}" +
                              (f" (+{len(missing_codes)-10} more)" if len(missing_codes) > 10 else "")
                })
                self.audit_passed = False

        self.audit_results["source_vs_output"] = checks

    def _audit_data_integrity(self):
        """Check data integrity - duplicates, nulls, format consistency."""
        self.log("Auditing: Data integrity...")

        checks = []

        # Check for duplicate finance codes - warn but don't fail (preserve source data)
        fc_codes = [fc.code for fc in self.extracted_finance_codes]
        fc_counts = Counter(fc_codes)
        fc_duplicates = [code for code, count in fc_counts.items() if count > 1]

        if fc_duplicates:
            # Source has duplicates - warn but keep data as-is
            checks.append({
                "check": "Finance Code Uniqueness",
                "passed": True,  # Don't fail audit - source data preserved
                "severity": "warning",
                "details": f"Source duplicates (kept): {', '.join(fc_duplicates[:5])}"
            })
        else:
            checks.append({
                "check": "Finance Code Uniqueness",
                "passed": True,
                "severity": "info",
                "details": "All unique"
            })

        # Check for duplicate school codes - O(n) using Counter
        sch_codes = [s.code for s in self.extracted_schools]
        sch_counts = Counter(sch_codes)
        sch_duplicates = [code for code, count in sch_counts.items() if count > 1]
        checks.append({
            "check": "School Code Uniqueness",
            "passed": len(sch_duplicates) == 0,
            "severity": "error" if sch_duplicates else "info",
            "details": f"Duplicates: {', '.join(sch_duplicates[:5])}" if sch_duplicates else "All unique"
        })
        if sch_duplicates:
            self.audit_passed = False

        # Check for duplicate department codes - O(n) using Counter
        dept_codes = [d.code for d in self.extracted_departments]
        dept_counts = Counter(dept_codes)
        dept_duplicates = [code for code, count in dept_counts.items() if count > 1]
        checks.append({
            "check": "Department Code Uniqueness",
            "passed": len(dept_duplicates) == 0,
            "severity": "warning" if dept_duplicates else "info",
            "details": f"Duplicates: {', '.join(dept_duplicates[:5])}" if dept_duplicates else "All unique"
        })

        # Check finance code format consistency
        numeric_codes = [fc.code for fc in self.extracted_finance_codes if fc.code.isdigit()]
        alpha_codes = [fc.code for fc in self.extracted_finance_codes if not fc.code.isdigit()]
        checks.append({
            "check": "Finance Code Format",
            "passed": len(alpha_codes) == 0,  # Should all be numeric
            "severity": "warning" if alpha_codes else "info",
            "details": f"Numeric: {len(numeric_codes)}, Alpha: {len(alpha_codes)}"
        })

        self.audit_results["data_integrity"] = checks

    def _audit_domain_rules(self):
        """Check domain-specific business rules."""
        self.log("Auditing: Domain rules...")

        checks = []

        # Check all finance codes have valid ledger codes
        valid_ledgers = {'COSTCTR', 'CAPITAL', 'PREMISES', 'STAFFING', 'SUPPLIES', 'TRIPS', 'DEFAULT', 'ZZZ_IMP'}
        invalid_ledger_fc = [fc for fc in self.extracted_finance_codes
                            if fc.ledger_code and fc.ledger_code not in valid_ledgers]
        checks.append({
            "check": "Valid Ledger Codes",
            "passed": len(invalid_ledger_fc) == 0,
            "severity": "warning" if invalid_ledger_fc else "info",
            "details": f"Invalid: {len(invalid_ledger_fc)}" if invalid_ledger_fc else "All valid"
        })

        # Check finance codes have titles
        no_title_fc = [fc for fc in self.extracted_finance_codes if not fc.title or fc.title == fc.code]
        checks.append({
            "check": "Finance Codes Have Titles",
            "passed": len(no_title_fc) == 0,
            "severity": "warning" if no_title_fc else "info",
            "details": f"Missing titles: {len(no_title_fc)}" if no_title_fc else "All have titles"
        })

        # Check schools have required fields
        incomplete_schools = [s for s in self.extracted_schools
                            if not s.code or not s.title]
        checks.append({
            "check": "Schools Have Required Fields",
            "passed": len(incomplete_schools) == 0,
            "severity": "error" if incomplete_schools else "info",
            "details": f"Incomplete: {len(incomplete_schools)}" if incomplete_schools else "All complete"
        })
        if incomplete_schools:
            self.audit_passed = False

        # Check departments have fund codes
        no_fund_depts = [d for d in self.extracted_departments if not d.fund_code]
        checks.append({
            "check": "Departments Have Fund Codes",
            "passed": len(no_fund_depts) == 0,
            "severity": "warning" if no_fund_depts else "info",
            "details": f"Missing fund: {len(no_fund_depts)}" if no_fund_depts else "All have funds"
        })

        # Check GroupingCode validity (should be 6-digit or ZZZ)
        invalid_grouping = [fc for fc in self.extracted_finance_codes
                          if fc.grouping_code and fc.grouping_code != 'ZZZ'
                          and not (fc.grouping_code.isdigit() and len(fc.grouping_code) == 6)]
        checks.append({
            "check": "Valid Grouping Codes",
            "passed": len(invalid_grouping) == 0,
            "severity": "warning" if invalid_grouping else "info",
            "details": f"Invalid: {len(invalid_grouping)}" if invalid_grouping else "All valid"
        })

        # Check CustomGrouping validity
        # Valid: DfE standard codes (A0, B0, C0), customer codes (alphabetic 3-8 chars), or ZZZ
        valid_standard = set(self.CUSTOM_GROUPING_MAP.keys())
        valid_standard.add('ZZZ')  # Unmapped is technically valid

        def is_valid_custom_grouping(cg):
            if not cg:
                return False
            if cg in valid_standard:
                return True
            # Customer's own custom grouping codes (INEFA, INGOV, etc.) are valid
            if cg.isalpha() and 2 <= len(cg) <= 10:
                return True
            return False

        unmapped_custom = [fc for fc in self.extracted_finance_codes if fc.custom_grouping == 'ZZZ']
        invalid_custom = [fc for fc in self.extracted_finance_codes
                        if not is_valid_custom_grouping(fc.custom_grouping)]

        # Count how many are mapped (not ZZZ)
        mapped_count = len(self.extracted_finance_codes) - len(unmapped_custom)
        mapped_pct = (mapped_count / len(self.extracted_finance_codes) * 100) if self.extracted_finance_codes else 0

        checks.append({
            "check": "Custom Groupings Assigned",
            "passed": mapped_pct >= 50,  # At least 50% should have custom groupings
            "severity": "warning" if mapped_pct < 50 else "info",
            "details": f"Mapped: {mapped_count}/{len(self.extracted_finance_codes)} ({mapped_pct:.1f}%)"
        })

        self.audit_results["domain_checks"] = checks

    def _audit_missing_data(self):
        """Check for missing or incomplete data."""
        self.log("Auditing: Missing data...")

        checks = []

        # Check if we have any finance codes
        checks.append({
            "check": "Finance Codes Extracted",
            "passed": len(self.extracted_finance_codes) > 0,
            "severity": "error" if len(self.extracted_finance_codes) == 0 else "info",
            "details": f"Count: {len(self.extracted_finance_codes)}"
        })

        # Check if we have any schools
        checks.append({
            "check": "Schools Extracted",
            "passed": len(self.extracted_schools) > 0,
            "severity": "warning" if len(self.extracted_schools) == 0 else "info",
            "details": f"Count: {len(self.extracted_schools)}"
        })

        # Check for ZZZ grouping codes (unmapped)
        unmapped_fc = [fc for fc in self.extracted_finance_codes if fc.grouping_code == 'ZZZ']
        unmapped_pct = (len(unmapped_fc) / len(self.extracted_finance_codes) * 100) if self.extracted_finance_codes else 0
        checks.append({
            "check": "Finance Codes Mapped to DfE",
            "passed": unmapped_pct < 50,
            "severity": "warning" if unmapped_pct >= 50 else "info",
            "details": f"Unmapped: {len(unmapped_fc)} ({unmapped_pct:.1f}%)"
        })

        # Check for ZZZ custom groupings (unmapped)
        unmapped_cg = [fc for fc in self.extracted_finance_codes if fc.custom_grouping == 'ZZZ']
        unmapped_cg_pct = (len(unmapped_cg) / len(self.extracted_finance_codes) * 100) if self.extracted_finance_codes else 0
        checks.append({
            "check": "Finance Codes Have Custom Grouping",
            "passed": unmapped_cg_pct < 50,
            "severity": "warning" if unmapped_cg_pct >= 50 else "info",
            "details": f"Unmapped: {len(unmapped_cg)} ({unmapped_cg_pct:.1f}%)"
        })

        self.audit_results["missing_data"] = checks

    def _audit_data_lineage(self, customer_data_dir: Path):
        """Verify data lineage - track where data came from."""
        self.log("Auditing: Data lineage...")

        checks = []

        # Count source files processed
        source_files = list(customer_data_dir.rglob("*.xls*")) + list(customer_data_dir.rglob("*.csv"))
        source_files = [f for f in source_files if not f.name.startswith("~$")]

        checks.append({
            "check": "Source Files Processed",
            "passed": len(source_files) > 0,
            "severity": "error" if len(source_files) == 0 else "info",
            "details": f"Files: {len(source_files)}"
        })

        # Record source file names
        checks.append({
            "check": "Source File List",
            "passed": True,
            "severity": "info",
            "details": ", ".join([f.name for f in source_files[:5]]) +
                      (f" (+{len(source_files)-5} more)" if len(source_files) > 5 else "")
        })

        self.audit_results["data_lineage"] = checks

    def _calculate_audit_score(self):
        """Calculate overall audit score based on check results."""
        total_checks = 0
        passed_checks = 0
        error_count = 0
        warning_count = 0

        for category, checks in self.audit_results.items():
            for check in checks:
                total_checks += 1
                if check.get("passed", True):
                    passed_checks += 1
                elif check.get("severity") == "error":
                    error_count += 1
                elif check.get("severity") == "warning":
                    warning_count += 1

        # Calculate score: errors = -10 points, warnings = -5 points
        if total_checks > 0:
            base_score = (passed_checks / total_checks) * 100
            penalty = (error_count * 10) + (warning_count * 5)
            self.audit_score = max(0, base_score - penalty)
        else:
            self.audit_score = 0

        # Audit fails if score < 60 or any critical errors
        if self.audit_score < 60 or error_count > 0:
            self.audit_passed = False

    def _log_audit_summary(self):
        """Log audit summary."""
        self.log("\n" + "-"*40)
        self.log("AUDIT SUMMARY")
        self.log("-"*40)
        self.log(f"  Audit Score: {self.audit_score:.1f}%")
        self.log(f"  Audit Passed: {self.audit_passed}")

        for category, checks in self.audit_results.items():
            errors = [c for c in checks if not c.get("passed") and c.get("severity") == "error"]
            warnings = [c for c in checks if not c.get("passed") and c.get("severity") == "warning"]

            if errors or warnings:
                self.log(f"\n  {category}:")
                for check in errors:
                    self.log(f"    ERROR: {check['check']} - {check['details']}")
                for check in warnings:
                    self.log(f"    WARNING: {check['check']} - {check['details']}")

        self.log("-"*40)

    def _generate_detailed_audit_report(self) -> Dict[str, Any]:
        """
        Generate a detailed audit report with explanations and recommendations.
        This provides a human-readable breakdown of what's missing and why.
        """
        detailed_report = {
            "summary": {
                "score": self.audit_score,
                "passed": self.audit_passed,
                "total_issues": 0,
                "critical_issues": 0,
                "warnings": 0,
            },
            "issues": [],
            "recommendations": [],
            "data_quality_breakdown": {},
        }

        # Analyze each category and generate detailed explanations
        for category, checks in self.audit_results.items():
            category_issues = []

            for check in checks:
                if not check.get("passed", True):
                    issue = self._explain_audit_issue(category, check)
                    if issue:
                        category_issues.append(issue)
                        detailed_report["issues"].append(issue)
                        detailed_report["summary"]["total_issues"] += 1

                        if check.get("severity") == "error":
                            detailed_report["summary"]["critical_issues"] += 1
                        elif check.get("severity") == "warning":
                            detailed_report["summary"]["warnings"] += 1

            if category_issues:
                detailed_report["data_quality_breakdown"][category] = category_issues

        # Generate recommendations based on issues found
        detailed_report["recommendations"] = self._generate_recommendations(detailed_report["issues"])

        return detailed_report

    def _explain_audit_issue(self, category: str, check: Dict) -> Dict[str, Any]:
        """Generate a detailed explanation for a specific audit issue."""
        check_name = check.get("check", "Unknown")
        severity = check.get("severity", "info")
        details = check.get("details", "")

        # Build explanation based on check type
        explanation = {
            "category": category,
            "check": check_name,
            "severity": severity,
            "details": details,
            "what_is_missing": "",
            "why_it_matters": "",
            "how_to_fix": "",
            "affected_records": [],
        }

        # Source vs Output issues
        if category == "source_vs_output":
            if "Finance Codes Count" in check_name:
                source = check.get("source_count", 0)
                output = check.get("output_count", 0)
                diff = source - output
                explanation["what_is_missing"] = f"{diff} finance codes from the source data were not extracted"
                explanation["why_it_matters"] = "Missing finance codes will cause budget lines to fail validation when imported into IMP Planner"
                explanation["how_to_fix"] = "Check the source file format. Ensure finance codes are in a column labeled 'Code', 'Finance Code', or 'COA Code'. Verify no filtering is excluding valid codes."

            elif "Schools Count" in check_name:
                source = check.get("source_count", 0)
                output = check.get("output_count", 0)
                diff = source - output
                explanation["what_is_missing"] = f"{diff} schools from the source data were not extracted"
                explanation["why_it_matters"] = "Missing schools will prevent staff and budget allocation to those schools"
                explanation["how_to_fix"] = "Verify school names/codes in source match expected formats. Check for merged cells or hidden rows in Excel."

            elif "Departments Count" in check_name:
                source = check.get("source_count", 0)
                output = check.get("output_count", 0)
                diff = source - output
                explanation["what_is_missing"] = f"{diff} departments from the source data were not extracted"
                explanation["why_it_matters"] = "Missing departments affect cost centre allocation and reporting structure"
                explanation["how_to_fix"] = "Check department column headers match expected names. Ensure no blank rows split the data."

            elif "Missing Finance Codes" in check_name:
                explanation["what_is_missing"] = f"Specific finance codes not found in output: {details}"
                explanation["why_it_matters"] = "These codes exist in source but weren't processed - may indicate parsing errors"
                explanation["how_to_fix"] = "Review the source file for these specific codes. Check for special characters, leading zeros, or formatting issues."

        # Data Integrity issues
        elif category == "data_integrity":
            if "Duplicate" in check_name:
                explanation["what_is_missing"] = "Data contains duplicate entries that should be unique"
                explanation["why_it_matters"] = f"Duplicates cause import errors and data inconsistency. {details}"
                explanation["how_to_fix"] = "Review source data for unintentional duplicates. If duplicates are valid (e.g., same code, different descriptions), consider using unique identifiers."
                # Extract affected records
                if "codes" in details.lower():
                    codes = details.replace("Duplicates: ", "").split(", ")
                    explanation["affected_records"] = codes[:20]

            elif "Null" in check_name or "Empty" in check_name:
                explanation["what_is_missing"] = "Required fields contain empty or null values"
                explanation["why_it_matters"] = "Empty required fields will cause validation failures during import"
                explanation["how_to_fix"] = "Fill in missing values in source data or configure default values."

        # Domain checks (missing data)
        elif category == "missing_data" or category == "domain_checks":
            if "URN" in check_name:
                explanation["what_is_missing"] = "Schools are missing their Unique Reference Number (URN)"
                explanation["why_it_matters"] = "URN is required for DfE reporting and school identification"
                explanation["how_to_fix"] = "Look up URNs from Get Information About Schools (GIAS) database. Add URN column to source data."
                if "affected" in details.lower() or "schools" in details.lower():
                    explanation["affected_records"] = [s.strip() for s in details.split(":")[1].split(",")[:10]] if ":" in details else []

            elif "LA Code" in check_name:
                explanation["what_is_missing"] = "Schools are missing their Local Authority code"
                explanation["why_it_matters"] = "LA codes are required for funding calculations and regional reporting"
                explanation["how_to_fix"] = "Add LA codes based on school location. Standard 3-digit codes (e.g., 873 for Cambridgeshire)."

            elif "Fund Code" in check_name:
                explanation["what_is_missing"] = "Departments are missing fund code assignments"
                explanation["why_it_matters"] = "Fund codes determine which budget fund the department draws from"
                explanation["how_to_fix"] = "Assign appropriate fund codes (01=General, 02=Delegated, etc.) to each department."

        # Data Lineage issues
        elif category == "data_lineage":
            if "No Source" in check_name:
                explanation["what_is_missing"] = "Cannot trace extracted data back to source files"
                explanation["why_it_matters"] = "Data lineage is essential for audit trails and debugging"
                explanation["how_to_fix"] = "Ensure source files are in the correct customer data folder before processing."

        return explanation

    def _generate_recommendations(self, issues: List[Dict]) -> List[Dict[str, str]]:
        """Generate prioritized recommendations based on issues found."""
        recommendations = []
        seen_recs = set()

        # Priority 1: Critical data missing
        critical_issues = [i for i in issues if i.get("severity") == "error"]
        if critical_issues:
            for issue in critical_issues:
                rec = {
                    "priority": "HIGH",
                    "category": issue.get("category", ""),
                    "action": issue.get("how_to_fix", "Review and fix critical data issues"),
                    "reason": issue.get("why_it_matters", ""),
                }
                rec_key = f"{rec['category']}:{rec['action'][:50]}"
                if rec_key not in seen_recs:
                    recommendations.append(rec)
                    seen_recs.add(rec_key)

        # Priority 2: Data quality warnings
        warning_issues = [i for i in issues if i.get("severity") == "warning"]
        if warning_issues:
            for issue in warning_issues:
                rec = {
                    "priority": "MEDIUM",
                    "category": issue.get("category", ""),
                    "action": issue.get("how_to_fix", "Review data quality warnings"),
                    "reason": issue.get("why_it_matters", ""),
                }
                rec_key = f"{rec['category']}:{rec['action'][:50]}"
                if rec_key not in seen_recs:
                    recommendations.append(rec)
                    seen_recs.add(rec_key)

        # Add general recommendations if no source data was found
        if not self.source_finance_codes and not self.source_schools:
            recommendations.insert(0, {
                "priority": "HIGH",
                "category": "data_source",
                "action": "Add customer data files to the S1 folder before processing",
                "reason": "No source data was detected - the system needs customer Excel/CSV files to extract from",
            })

        # Add recommendation for low scores
        if self.audit_score < 80 and self.audit_score >= 60:
            recommendations.append({
                "priority": "LOW",
                "category": "data_quality",
                "action": "Review and clean source data to improve audit score",
                "reason": f"Current score ({self.audit_score:.1f}%) indicates data quality issues that may cause problems during import",
            })

        return recommendations

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def process(self, customer_data_dir: Path, output_dir: Path, column_mappings: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """Main processing entry point with quality checking and external audit.

        Args:
            customer_data_dir: Path to customer data files
            output_dir: Path to save output
            column_mappings: Optional dict of validated column mappings from pre-flight validation
        """
        # Store column mappings for use during processing
        self.column_mappings = column_mappings or {}

        self.log("="*60)
        self.log("S1 SPECIALIST AGENT - STARTING PROCESSING")
        self.log("="*60)

        # Phase 1: Analysis - Extract data from customer files
        self.analyze_customer_data(customer_data_dir)

        # Phase 2: Validate extracted data
        extraction_validation = self.validate_extracted_data()

        # Phase 3: Build templates
        template_sheets = self.build_all_templates()

        # Phase 4: Validate output against Standard Workbook schema
        output_validation = self.validate_output()

        # Phase 5: External Audit Review
        audit_results = self.perform_external_audit(customer_data_dir)

        # Save output
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"S1_complete_template_{timestamp}.xlsx"

        # Phase 6: Format data to match official template schema
        template_warnings = []
        formatted_sheets = {}

        self.log("\nPHASE 6: FORMATTING FOR OFFICIAL TEMPLATE")
        self.log("-" * 40)

        for internal_name, df in template_sheets.items():
            if len(df) == 0:
                continue

            # Get official template sheet name
            official_name = self.SHEET_NAME_MAPPING.get(internal_name, internal_name)

            # Apply template formatting if available
            if self.template_formatter and official_name in self.template_registry.list_sheets("S1"):
                formatted_df, warnings = self.template_formatter.format_dataframe(
                    df, "S1", official_name
                )
                formatted_sheets[official_name] = formatted_df
                if warnings:
                    template_warnings.extend([f"{official_name}: {w}" for w in warnings])
                    self.log(f"  {official_name}: {len(df)} rows (formatted, {len(warnings)} warnings)")
                else:
                    self.log(f"  {official_name}: {len(df)} rows (formatted)")
            else:
                # No template schema, use as-is with official name
                formatted_sheets[official_name] = df
                self.log(f"  {official_name}: {len(df)} rows (no schema)")

        if template_warnings:
            self.log(f"\n[WARN] Template formatting warnings: {len(template_warnings)}")
            for w in template_warnings[:5]:
                self.log(f"  - {w}")

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in formatted_sheets.items():
                if len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Summary with validation and audit results
            summary_data = {
                "Metric": [
                    "Finance Codes Extracted",
                    "Schools Extracted",
                    "Departments Extracted",
                    "Local Authorities",
                    "Extraction Errors",
                    "Extraction Warnings",
                    "Output Validation Errors",
                    "Duplicates Found",
                    "---",
                    "AUDIT SCORE",
                    "AUDIT PASSED",
                ],
                "Value": [
                    len(self.extracted_finance_codes),
                    len(self.extracted_schools),
                    len(self.extracted_departments),
                    len(self.local_authorities),
                    len(self.validation_errors),
                    len(self.validation_warnings),
                    len(output_validation.get('errors', [])),
                    sum(len(d) for d in self.duplicates_found.values()),
                    "---",
                    f"{self.audit_score:.1f}%",
                    "YES" if self.audit_passed else "NO",
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="_Summary", index=False)

            # Validation Report sheet
            validation_report = []
            for err in self.validation_errors:
                validation_report.append({"Type": "ERROR", "Message": err})
            for warn in self.validation_warnings:
                validation_report.append({"Type": "WARNING", "Message": warn})
            for err in output_validation.get('errors', []):
                validation_report.append({"Type": "OUTPUT ERROR", "Message": err})
            if validation_report:
                pd.DataFrame(validation_report).to_excel(writer, sheet_name="_Validation", index=False)

            # External Audit Report sheet
            audit_report = []
            for category, checks in self.audit_results.items():
                for check in checks:
                    audit_report.append({
                        "Category": category,
                        "Check": check.get("check", ""),
                        "Passed": "YES" if check.get("passed", True) else "NO",
                        "Severity": check.get("severity", "info").upper(),
                        "Details": check.get("details", ""),
                    })
            if audit_report:
                pd.DataFrame(audit_report).to_excel(writer, sheet_name="_Audit_Report", index=False)

            # Detailed Audit Report sheet - with explanations and recommendations
            detailed_issues = []
            for issue in self.detailed_audit_report.get("issues", []):
                detailed_issues.append({
                    "Category": issue.get("category", ""),
                    "Check": issue.get("check", ""),
                    "Severity": issue.get("severity", "").upper(),
                    "What Is Missing": issue.get("what_is_missing", ""),
                    "Why It Matters": issue.get("why_it_matters", ""),
                    "How To Fix": issue.get("how_to_fix", ""),
                    "Affected Records": ", ".join(issue.get("affected_records", [])[:10]),
                })
            if detailed_issues:
                pd.DataFrame(detailed_issues).to_excel(writer, sheet_name="_Audit_Details", index=False)

            # Recommendations sheet
            recommendations = self.detailed_audit_report.get("recommendations", [])
            if recommendations:
                rec_data = []
                for rec in recommendations:
                    rec_data.append({
                        "Priority": rec.get("priority", ""),
                        "Category": rec.get("category", ""),
                        "Action Required": rec.get("action", ""),
                        "Reason": rec.get("reason", ""),
                    })
                pd.DataFrame(rec_data).to_excel(writer, sheet_name="_Recommendations", index=False)

        self.log(f"\nOutput saved to: {output_file}")

        # Determine overall success (includes audit)
        has_critical_errors = (
            len(self.validation_errors) > 0 or
            len(output_validation.get('errors', [])) > 0 or
            not self.audit_passed
        )

        return {
            "success": not has_critical_errors and len(self.issues) == 0,
            "output_file": output_file,
            "template_sheets": template_sheets,
            "issues": self.issues,
            "validation": {
                "extraction": extraction_validation,
                "output": output_validation,
            },
            "audit": {
                "passed": self.audit_passed,
                "score": self.audit_score,
                "results": self.audit_results,
                "detailed_report": self.detailed_audit_report,
            },
            "summary": {
                "finance_codes": len(self.extracted_finance_codes),
                "schools": len(self.extracted_schools),
                "departments": len(self.extracted_departments),
                "validation_errors": len(self.validation_errors),
                "validation_warnings": len(self.validation_warnings),
                "audit_score": self.audit_score,
                "audit_passed": self.audit_passed,
            }
        }


def run_s1_specialist(customer_data_dir: Path, output_dir: Path, column_mappings: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
    """Run the S1 specialist agent.

    Args:
        customer_data_dir: Path to customer data files
        output_dir: Path to save output
        column_mappings: Optional dict of validated column mappings from pre-flight validation

    Returns:
        Processing result dictionary
    """
    agent = S1SpecialistAgent()
    return agent.process(customer_data_dir, output_dir, column_mappings=column_mappings)
