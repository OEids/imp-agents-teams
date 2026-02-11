"""
Agent Knowledge Base

Contains domain expertise for IMP Planner data processing.
Each team has specialized knowledge about their strand.

Knowledge sourced from:
- S1: Strand 1 Process Notes, Training Notes, Core Data Review
- S2: Process Notes (Structure), Process Notes (Contracts), Build Reconciliation
     + S2_DOMAIN_KNOWLEDGE.py (extracted from import files)
- S3: Strand 3 Workbook Phase 1, Phase 2, Grants and Calculations
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Import S2 domain knowledge from extracted import files
try:
    from knowledge.S2.S2_DOMAIN_KNOWLEDGE import (
        # Parsing functions
        parse_combined_field,
        extract_finance_code,
        # Data dictionaries
        PAY_SCALES as S2_PAY_SCALES,
        TEACHER_PAY_POINTS_2024_25,
        STAFF_ROLE_GROUPS,
        EQUATED_WEEK_PATTERNS,
        PENSION_SCHEMES,
        CONTRACT_TYPES,
        FUND_CODES,
        ALLOWANCE_TYPES,
        IMPORT_COLUMN_MAPPINGS,
        COMBINED_COLUMNS,
        VALIDATION_RULES as S2_VALIDATION_RULES,
        # Helper functions
        get_equated_week_pattern,
        get_default_pension,
        get_default_fund_code,
        is_teaching_role as s2_is_teaching_role,
        get_finance_codes_for_role_group,
        get_salary_finance_code,
        get_ni_finance_code,
        get_pension_finance_code,
        map_role_title_to_group,
        # Validation functions
        validate_staff_member_code,
        validate_weekly_fte,
        # Transformation functions
        transform_contract_row,
    )
    S2_DOMAIN_KNOWLEDGE_AVAILABLE = True
except ImportError:
    S2_DOMAIN_KNOWLEDGE_AVAILABLE = False
    # Define stub functions/dicts if import fails
    def parse_combined_field(value): return (str(value), str(value))
    def extract_finance_code(value): return str(value)
    def transform_contract_row(row): return row
    S2_PAY_SCALES = {}
    STAFF_ROLE_GROUPS = {}
    EQUATED_WEEK_PATTERNS = {}
    COMBINED_COLUMNS = []


@dataclass
class ValidationRule:
    """A specific validation rule with remediation guidance."""
    name: str
    description: str
    check_type: str  # 'format', 'range', 'reference', 'calculation', 'business'
    severity: str    # 'critical', 'error', 'warning', 'info'
    remediation: str


@dataclass
class ColumnMapping:
    """Maps source column variations to standard names."""
    standard_name: str
    variations: List[str]
    data_type: str  # 'text', 'numeric', 'date', 'code'
    required: bool
    format_hint: str = ""


@dataclass
class TemplateSheet:
    """Defines a template sheet structure."""
    sheet_name: str
    description: str
    key_columns: List[str]
    import_order: int  # Order in which sheets should be imported


@dataclass
class DataManipulationSkill:
    """A skill for manipulating source data."""
    name: str
    description: str
    when_to_use: str
    steps: List[str]
    example: Optional[str] = None


@dataclass
class BuildWorkflow:
    """Workflow steps for building a strand."""
    phase: str
    description: str
    steps: List[str]
    outputs: List[str]
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TeamKnowledge:
    """Complete knowledge base for a team."""
    team_id: str
    team_name: str
    description: str
    key_concepts: Dict[str, str]
    column_mappings: List[ColumnMapping]
    validation_rules: List[ValidationRule]
    business_rules: List[str]
    common_issues: List[str]
    remediation_patterns: Dict[str, str]
    # New fields from knowledge articles
    template_sheets: List[TemplateSheet] = field(default_factory=list)
    manipulation_skills: List[DataManipulationSkill] = field(default_factory=list)
    build_workflow: List[BuildWorkflow] = field(default_factory=list)


# =============================================================================
# STRAND 1 KNOWLEDGE - Structure Team
# =============================================================================

S1_KNOWLEDGE = TeamKnowledge(
    team_id="S1",
    team_name="Structure Team",
    description="Handles foundational reference data: finance codes, schools, departments, grouping codes",

    key_concepts={
        "finance_code": "4-digit code identifying an account in the Chart of Accounts (COA). Format: '0001' to '9999'. Leading zeros are significant.",
        "cost_centre": "2-4 character alphanumeric code identifying a location/school. Examples: 'SSF', 'PPC', 'PRU'",
        "department": "3-digit numeric code with leading zeros. Examples: '000', '460', '801'",
        "fund_code": "Single digit or small number identifying funding source. Examples: '1', '5', '30'",
        "grouping_code": "DFE COA groupings used for reporting. Maps finance codes to standard categories.",
        "ledger_code": "Alternative name for finance code in some systems",
        "nominal_code": "Alternative name for finance code (Sage terminology)",
        "account_combination": "Finance code + cost centre + department = unique account identifier",
        "balance_sheet": "Codes 0xxx-3xxx (assets, liabilities, equity) - cost centre often blank",
        "p_and_l": "Codes 4xxx-9xxx (income, expenditure) - cost centre usually required",
    },

    column_mappings=[
        ColumnMapping("finance_code", [
            "code", "account number", "nominal code", "gl code", "ledger code",
            "finance code", "account code", "nlnominalaccounts.accountnumber",
            "nominal", "account", "acc code", "acc no"
        ], "code", True, "4 digits with leading zeros: '0001', '1130', '6300'"),

        ColumnMapping("cost_centre", [
            "cost centre", "site", "school", "location", "accountcostcentre",
            "cc", "cost center", "centre", "school code"
        ], "code", False, "2-4 alphanumeric: 'SSF', 'PPC', 'PRU' - can be blank for balance sheet"),

        ColumnMapping("department", [
            "department", "dept", "department code", "accountdepartment",
            "dept code", "dpt"
        ], "code", False, "3 digits with leading zeros: '000', '460' - can be blank"),

        ColumnMapping("title", [
            "name", "description", "account name", "nominal name", "title",
            "account description", "desc"
        ], "text", True, "Meaningful account description"),

        ColumnMapping("fund_code", [
            "fund", "fund code", "funding code", "fund type"
        ], "code", False, "Single digit: '1', '5'"),

        ColumnMapping("grouping_code", [
            "grouping", "grouping code", "group", "category", "coa grouping"
        ], "code", False, "DFE standard grouping code"),
    ],

    validation_rules=[
        ValidationRule(
            "finance_code_format",
            "Finance codes must be exactly 4 digits after normalization",
            "format", "critical",
            "Pad with leading zeros if <4 digits. Extract numeric portion if mixed with text."
        ),
        ValidationRule(
            "finance_code_unique",
            "Finance code + cost centre + department combination must be unique",
            "business", "error",
            "Remove duplicates or verify they represent different accounts"
        ),
        ValidationRule(
            "cost_centre_consistency",
            "Cost centres must be consistent across all files",
            "reference", "error",
            "Build master list from source files. Use case-insensitive matching."
        ),
        ValidationRule(
            "department_format",
            "Department codes must be 3 digits with leading zeros",
            "format", "warning",
            "Pad 1-2 digit codes with leading zeros: '5' -> '005'"
        ),
        ValidationRule(
            "balance_sheet_cost_centre",
            "Balance sheet accounts (0xxx-3xxx) may have blank cost centre",
            "business", "info",
            "This is expected. Do not flag as error."
        ),
        ValidationRule(
            "account_description",
            "All accounts must have meaningful descriptions",
            "format", "warning",
            "Flag empty or generic descriptions for review"
        ),
    ],

    business_rules=[
        "Same finance code CAN exist at multiple cost centres - the combination is what's unique",
        "Balance sheet accounts (0xxx-3xxx) often have blank cost centre and department",
        "P&L accounts (4xxx-9xxx) should have cost centre assigned",
        "Income codes are typically 4xxx",
        "Expenditure codes are typically 5xxx-9xxx",
        "Staff salary codes are usually 5xxx or 6xxx range",
        "Minimum 50 accounts expected for a typical school",
        "All finance codes used in Strand 2 and 3 must exist in Strand 1 COA",
    ],

    common_issues=[
        "Finance codes exported as 6 digits - need to normalize to 4",
        "Sage exports have header rows (Title:, FileName:, etc.) that need stripping",
        "Database-style column names (Table.FieldName) need normalizing",
        "Same school name appears differently across files (fuzzy match needed)",
        "Missing descriptions for some accounts",
        "Duplicate account combinations from merging files",
    ],

    remediation_patterns={
        "6_digit_code": "Check if first 2 or last 2 digits can be removed. E.g., '625100' might be '6251' or '2510'",
        "leading_zeros_lost": "Convert to string and pad: str(code).zfill(4)",
        "sage_header": "Skip rows starting with Title:, FileName:, Exported On:, Report Name:",
        "cost_centre_case": "Convert all to uppercase: 'ssf' -> 'SSF'",
        "school_name_mapping": "Build lookup from school name to code from master list",
    },

    # Template sheets from AA_New - Strand 1 Standard Workbook API
    template_sheets=[
        TemplateSheet("System Grouping Codes", "DFE COA grouping codes for reporting",
                     ["GroupingCode", "Title", "Level"], 1),
        TemplateSheet("01_Funds", "Fund codes for fund accounting",
                     ["FundCode", "Title", "Enabled"], 2),
        TemplateSheet("02_Activity", "Activity codes grouping departments",
                     ["ActivityCode", "Title"], 3),
        TemplateSheet("03_CustGroup", "Custom grouping codes defined by trust",
                     ["CustGroupCode", "Title"], 4),
        TemplateSheet("04_Ledger", "Ledger codes (typically DEPARTMENTS)",
                     ["LedgerCode", "Title"], 5),
        TemplateSheet("05_SchHub", "School hub codes for regional grouping",
                     ["SchHubCode", "Title"], 6),
        TemplateSheet("06_SchType", "School type codes (Primary, Secondary, etc.)",
                     ["SchTypeCode", "Title"], 7),
        TemplateSheet("07_LocalAuth", "Local authority codes and details",
                     ["LACode", "Title", "LondonWeighting"], 8),
        TemplateSheet("08_Schools", "School/cost centre master list",
                     ["SchoolCode", "Title", "LACode", "SchTypeCode", "SchHubCode"], 9),
        TemplateSheet("09_Depts", "Department codes",
                     ["DeptCode", "Title", "LedgerCode", "ActivityCode"], 10),
        TemplateSheet("10_FinanceCodes Budget", "Finance codes (COA) for budgeting",
                     ["FinanceCode", "Title", "GroupingCode", "LedgerCode", "SchoolCodes"], 11),
    ],

    # Data manipulation skills from Process Notes
    manipulation_skills=[
        DataManipulationSkill(
            "interface_vs_manual_build",
            "Determine whether to use interface or manual build approach",
            "At start of build - check if trust's finance system integrates with IMP",
            [
                "Check Project Scope for finance system (PSF, Sage, XERO, etc.)",
                "If interface available: Configure system settings, send API instructions to trust",
                "If manual build: Request COA export, actuals reports from trust",
                "For interface: Update Parameters tab with API key from Lastpass",
            ],
            "PSF/Iris, Sage Intacct, XERO integrate; Access/manual exports don't"
        ),
        DataManipulationSkill(
            "dfe_coa_mapping",
            "Map trust finance codes to DFE COA grouping codes",
            "When trust uses own COA codes instead of standard DFE codes",
            [
                "Use 'DFE COA Mappings' tab in Core Data Review workbook",
                "For each trust nominal code, identify matching DFE COA code",
                "If no match, mark as 'ZZZ - Needs Mapping/Further Analysis'",
                "Balance sheet codes (0xxx-3xxx) not used in IMP but map if beneficial",
            ],
            "Trust code 1000 'GAG Income' maps to DFE 510100"
        ),
        DataManipulationSkill(
            "combine_location_files",
            "Combine COA files from multiple schools/locations",
            "When trust provides separate files per school",
            [
                "Create master list of all unique finance codes across files",
                "Identify school-specific codes vs trust-wide codes",
                "Set 'Available to All Schools' = FALSE for school-specific codes",
                "Add school codes to 'School Codes' column for restricted codes",
                "Remove duplicates keeping most complete description",
            ]
        ),
        DataManipulationSkill(
            "normalize_finance_codes",
            "Standardize finance code formats",
            "When codes are inconsistent length or format",
            [
                "Convert all to 4-digit string with leading zeros",
                "If 6 digits: typically first 4 are the code (check with trust)",
                "Strip any non-numeric prefixes/suffixes",
                "Validate all codes exist in DFE COA or trust's own COA",
            ],
            "'1' -> '0001', '625100' -> '6251'"
        ),
    ],

    # Build workflow from Process Notes
    build_workflow=[
        BuildWorkflow(
            "template_prep",
            "Prepare the Strand 1 workbook template",
            [
                "Copy latest AA_NEW - Strand 1 Standard Workbook API to Workbook folder",
                "Check version number on Parameters tab",
                "Update API key if using interface build",
                "Verify Strand 1 tabs update with customer data (orange tabs)",
            ],
            ["Configured workbook ready for data entry"],
            []
        ),
        BuildWorkflow(
            "structure_build",
            "Build structural elements (schools, departments, funds)",
            [
                "Update school information from Project Scope",
                "Set correct Local Authority codes and London weightings",
                "Build department codes linked to correct ledger",
                "Configure fund codes if trust uses fund accounting",
                "Set up school hubs and types for reporting",
            ],
            ["08_Schools populated", "09_Depts populated", "01_Funds configured"],
            ["template_prep"]
        ),
        BuildWorkflow(
            "finance_codes_build",
            "Build Chart of Accounts / Finance Codes",
            [
                "Import/enter all finance codes from trust data",
                "Map grouping codes (DFE COA or trust custom)",
                "Set school availability for each code",
                "Link to correct ledger code",
                "Complete DFE COA mapping if not using standard codes",
            ],
            ["10_FinanceCodes Budget populated", "Grouping codes mapped"],
            ["structure_build"]
        ),
        BuildWorkflow(
            "validation_import",
            "Validate and import into IMP Planner",
            [
                "Complete Strand 1 Checklist - ensure no import errors",
                "Use CSV Extraction Tool to generate import files",
                "Import CSVs into IMP Planner in correct order",
                "Complete Import Checklist - verify counts match workbook",
                "Investigate any discrepancies before sign-off",
            ],
            ["Data imported to IMP Planner", "Import Checklist completed"],
            ["finance_codes_build"]
        ),
    ]
)


# =============================================================================
# STRAND 2 KNOWLEDGE - Staff Team
# =============================================================================

S2_KNOWLEDGE = TeamKnowledge(
    team_id="S2",
    team_name="Staff Team",
    description="Handles personnel data: staff members, contracts, pay scales, allowances, pensions",

    key_concepts={
        "payroll_number": "Unique identifier for a staff member. Typically 6 digits but varies.",
        "pay_scale": "Defines salary structure. Main types: Teaching (MPS/UPS/Leadership) and Support (NJC/Trust)",
        "scale_point": "Position on pay scale. Format varies: 'M1', 'UPS2', 'L8', 'SCP11', '10'",
        "fte": "Full Time Equivalent. Decimal 0.0-1.0 representing portion of full-time hours.",
        "tto": "Term Time Only. Staff who work school term weeks only (38-44 weeks vs 52.143)",
        "eqwp": "Equated Weeks Paid. Includes working weeks plus holiday entitlement.",
        "teaching_staff": "Staff on teaching pay scales: MPS, UPS, Leadership, Lead Practitioner",
        "support_staff": "Staff on support pay scales: NJC, Trust Scale, LA Scale",
        "tps": "Teachers' Pension Scheme - for teaching staff",
        "lgps": "Local Government Pension Scheme - for support staff",
        "tlr": "Teaching & Learning Responsibility - additional payment for teachers",
        "sen_allowance": "Special Educational Needs allowance for teachers",
        "contract_type": "Permanent, Fixed Term, Temp, Casual",
        "full_time_hours": "Standard weekly hours for full-time role. Teaching: 32.5, Support: 37",
    },

    column_mappings=[
        ColumnMapping("payroll_number", [
            "unique payroll number", "payroll number", "payroll no", "employee id",
            "staff id", "person identifier", "emp no", "employee number", "usernumber"
        ], "code", True, "Unique staff identifier - typically numeric"),

        ColumnMapping("last_name", [
            "last name", "surname", "family name", "lastname"
        ], "text", True, "Staff surname"),

        ColumnMapping("first_name", [
            "first name", "forename", "given name", "firstname"
        ], "text", True, "Staff first name"),

        ColumnMapping("date_of_birth", [
            "date of birth", "dob", "birth date", "birthdate"
        ], "date", False, "Format: DD/MM/YYYY. Age should be 16-75."),

        ColumnMapping("gender", [
            "gender", "sex"
        ], "text", False, "Male/Female/M/F. If blank, codes as 'ZZZ'"),

        ColumnMapping("service_start_date", [
            "continuous service start", "service start", "start date",
            "service date", "continuous service start (dd/mm/yyyy)"
        ], "date", True, "Used for TTO leave entitlement calculation"),

        ColumnMapping("school_code", [
            "work location", "school", "location", "site",
            "work location (school name or code)", "school code", "school name"
        ], "code", True, "Must match Strand 1 cost centres"),

        ColumnMapping("job_title", [
            "staff role", "job title", "position", "role",
            "staff role or job title name"
        ], "text", True, "Determines if Teaching or Support role"),

        ColumnMapping("finance_code", [
            "gross salary finance code", "finance code", "nominal",
            "gross salary finance code / nominal", "salary code"
        ], "code", True, "Must exist in Strand 1 COA. Usually 4 digits."),

        ColumnMapping("cost_centre", [
            "department code", "cost centre", "department code / cost centre"
        ], "code", True, "Must match Strand 1"),

        ColumnMapping("fund_code", [
            "fund code", "fund", "fund code (if applicable)"
        ], "code", False, "If organization uses fund accounting"),

        ColumnMapping("full_time_hours", [
            "full time hours", "full time hours for role", "ft hours", "fte hours"
        ], "numeric", True, "Teaching: 32.5, Support: typically 37"),

        ColumnMapping("weekly_hours", [
            "weekly hours", "contracted hours", "hours per week", "hours"
        ], "numeric", True, "Must be <= full time hours"),

        ColumnMapping("weekly_fte", [
            "weekly fte", "fte", "annual fte"
        ], "numeric", True, "weekly_hours / full_time_hours. Range: 0.001-1.0"),

        ColumnMapping("weeks_worked", [
            "eqwp/ tto weeks worked", "weeks worked", "working weeks",
            "eqwp/ tto weeks worked per year"
        ], "numeric", True, "TTO: 38-44. Full year: 52.143"),

        ColumnMapping("weeks_paid", [
            "eqwp/ tto weeks paid", "weeks paid", "paid weeks",
            "eqwp/ tto weeks paid per year"
        ], "numeric", True, "Includes holiday entitlement"),

        ColumnMapping("pay_scale", [
            "pay range", "pay scale", "scale", "pay range / scale"
        ], "text", True, "MPS/UPS/Leadership/NJC/Trust Scale etc."),

        ColumnMapping("current_scale_point", [
            "current spine point", "scale point", "point", "current scale point",
            "spine point"
        ], "text", True, "M1/U2/L8/SCP11 etc."),

        ColumnMapping("annual_salary", [
            "annual salary", "salary", "fte salary", "fte annual salary",
            "rate post annual fte"
        ], "numeric", True, "FTE salary - must match pay scale point"),

        ColumnMapping("actual_salary", [
            "actual salary", "pro rata salary"
        ], "numeric", False, "FTE salary x FTE. Calculated field."),

        ColumnMapping("contract_type", [
            "contract type", "employment type", "contract type (perm, fixed term etc)"
        ], "text", False, "Permanent/Fixed Term/Temp/Casual"),

        ColumnMapping("contract_start", [
            "contract start", "start date", "contract start (if after budget period start date)"
        ], "date", False, "If after budget period start"),

        ColumnMapping("contract_end", [
            "contract end", "end date", "contract end (if in budget period)"
        ], "date", False, "Required for Fixed Term contracts"),

        ColumnMapping("pension_scheme", [
            "pension scheme", "pension", "scheme tps/ lgps/ other"
        ], "text", True, "TPS for teaching, LGPS for support"),
    ],

    validation_rules=[
        ValidationRule(
            "payroll_unique",
            "Payroll number must be unique per person (multiple contracts OK)",
            "business", "error",
            "Check if duplicate represents multiple contracts or data error"
        ),
        ValidationRule(
            "fte_calculation",
            "FTE = weekly_hours / full_time_hours (tolerance +/- 0.02)",
            "calculation", "error",
            "Recalculate FTE from hours. Flag if significant mismatch."
        ),
        ValidationRule(
            "salary_vs_scale_point",
            "Salary must match pay scale point value (tolerance +/- 5%)",
            "calculation", "error",
            "Lookup expected salary from pay scale tables. Flag variance."
        ),
        ValidationRule(
            "tto_paid_weeks",
            "Paid weeks must match TTO calculation for site/service length",
            "calculation", "warning",
            "Calculate: working_weeks + (leave_days + bank_holidays) / 5"
        ),
        ValidationRule(
            "pension_scheme_role_match",
            "Teaching roles -> TPS, Support roles -> LGPS",
            "business", "warning",
            "Flag mismatches but may be legitimate edge cases"
        ),
        ValidationRule(
            "finance_code_coa",
            "Finance codes must exist in Strand 1 COA",
            "reference", "critical",
            "Cross-reference against COA master. Suggest corrections."
        ),
        ValidationRule(
            "salary_range",
            "Salary within reasonable range (GBP 15k-GBP 150k typical)",
            "range", "warning",
            "Flag unusual values for review. Leadership can exceed GBP 100k."
        ),
        ValidationRule(
            "age_validation",
            "Staff age should be 16-75 based on DOB",
            "range", "warning",
            "Flag if age <16 (ERROR) or >75 (WARNING)"
        ),
    ],

    business_rules=[
        "One person can have multiple contracts (same payroll, different contract refs)",
        "Teaching staff: MPS (Main Pay Scale) 6 points, UPS (Upper) 3 points, Leadership 43 points",
        "Support staff: NJC spine points typically 1-42",
        "TTO staff work fewer weeks but paid weeks includes holiday entitlement",
        "TTO paid weeks = working weeks + (leave days + bank holidays) / 5",
        "Leave entitlement varies by site and years of service",
        "FTE > 1.0 may indicate multiple contracts - sum and verify",
        "Spot salaries (outside scale) need special handling",
        "Safeguarded staff may have salary higher than current scale point",
    ],

    common_issues=[
        "Concatenated names 'Smith, John' need splitting",
        "Pay scale format variations: 'MPS1', 'M1', 'Main 1', 'Main Scale 1'",
        "Spine point format variations: 'SCP5', 'SCP 5', 'Spine 5', 'Point 5', '5'",
        "FTE calculated differently in source systems",
        "Finance codes may be 6 digits in staff data but 4 in COA",
        "Missing service start dates affect TTO calculations",
        "Incorrect paid weeks due to wrong site leave entitlement",
    ],

    remediation_patterns={
        "name_split": "Split on comma or space: 'Smith, John' -> last='Smith', first='John'",
        "scale_point_normalize": "Extract number, prefix with scale type: 'Spine 5' -> 'SCP5'",
        "teaching_scale_normalize": "MPS/M/Main -> 'MPS', UPS/U/Upper -> 'UPS'",
        "fte_fix": "Calculate: weekly_hours / full_time_hours",
        "salary_mismatch": "Lookup from pay scale table, flag variance with expected value",
        "tto_weeks_fix": "Recalculate using site-specific leave rules and service length",
    },

    # Template sheets from AA_New - Strand 2 Standard Workbook API
    template_sheets=[
        TemplateSheet("19_PayScales", "Pay scale definitions (MPS, UPS, Leadership, NJC)",
                     ["PayScaleCode", "Title", "IncrementDate", "IncreaseDate", "IncreasePercentage",
                      "AvailableToAllSchools", "SchoolCodes"], 1),
        TemplateSheet("20_PayScalePoints", "Pay scale points with rates",
                     ["PayScaleCode", "PayScalePointCode", "Title", "ScalePointNumber",
                      "RateDateFrom", "PayScaleRate", "Enabled"], 2),
        TemplateSheet("22_PayScaleGrades", "Pay scale grades (progression paths)",
                     ["PayScaleCode", "PayScaleGradeCode", "Title", "PointCodes"], 3),
        TemplateSheet("21_PayScaleIncreasePercen", "Future pay increase percentages",
                     ["PayScaleCode", "EffectiveDate", "IncreasePercentage"], 4),
        TemplateSheet("16_AllowanceTypes", "Allowance types (TLR, SEN, etc.)",
                     ["AllowanceTypeCode", "Title", "FinanceCode"], 5),
        TemplateSheet("17_AllowanceTypePoint", "Allowance amounts per point",
                     ["AllowanceTypeCode", "AllowancePointCode", "Amount"], 6),
        TemplateSheet("24_Pensions", "Pension scheme definitions (TPS, LGPS)",
                     ["PensionCode", "Title", "EmployeeRate", "EmployerRate"], 7),
        TemplateSheet("23_EQWPatterns", "Equated weeks patterns for TTO staff",
                     ["EQWPCode", "Title", "WeeksWorked", "WeeksPaid", "ServiceYears"], 8),
        TemplateSheet("26_StfRoleGroup", "Staff role groups with finance codes",
                     ["StaffRoleGroupCode", "Title", "GrossSalaryFinanceCode",
                      "EmployersNIFinanceCode", "PensionFinanceCode"], 9),
        TemplateSheet("27_StfRole", "Staff roles linked to pay scales",
                     ["StaffRoleCode", "Title", "PayScaleCode", "FullTimeHours",
                      "StaffRoleGroupCode", "MonthsServiceBeforeIncrement"], 10),
        TemplateSheet("25_StaffMembers", "Staff member details",
                     ["StaffMemberCode", "Forename", "Surname", "ServiceStartDate",
                      "DateOfBirth", "GenderCode", "AvailableToAllSchools", "SchoolCodes"], 11),
        TemplateSheet("28_ContractsTeachFTE", "Teaching staff contracts (FTE-based)",
                     ["StaffMemberCode", "ContractRef", "SchoolCode", "StaffRoleCode",
                      "AnnualFTE", "PayScaleGradeCode", "PayScalePointCode", "PensionCode",
                      "EQWPCode", "ContractTypeCode", "ContractStart", "ContractEnd"], 12),
        TemplateSheet("29_ContractsSupportHours", "Support staff contracts (hours-based)",
                     ["StaffMemberCode", "ContractRef", "SchoolCode", "StaffRoleCode",
                      "HoursPerWeek", "PayScaleGradeCode", "PayScalePointCode", "PensionCode",
                      "EQWPCode", "ContractTypeCode", "ContractStart", "ContractEnd"], 13),
        TemplateSheet("34_ContractAllowances", "Contract allowances (TLR, SEN payments)",
                     ["ContractID", "AllowanceTypeCode", "AllowancePointCode", "Amount"], 14),
        TemplateSheet("33_ContractAdjustments", "Contract adjustments",
                     ["ContractID", "AdjustmentTypeCode", "Amount", "Notes"], 15),
    ],

    # Data manipulation skills from Process Notes - Strand 2
    manipulation_skills=[
        DataManipulationSkill(
            "pay_scale_setup",
            "Configure pay scales for the trust",
            "At start of Strand 2 build - before staff data",
            [
                "Identify London weighting in use (England & Wales, Inner/Outer London, Fringe)",
                "Delete unused London weighting pay scales from template",
                "For NJC: determine if LA standard or Trust standard pay scale",
                "If LA standard: adjust code to include LA code (e.g., NJC_NYK for North Yorkshire)",
                "If Trust standard: code as MAT_SUP with title 'MAT Support Scale'",
                "Compare provided rates with template - amend any differences",
                "Check increment date, increase date, increase percentage from Project Scope",
                "Restrict pay scales to relevant schools if multiple weightings in use",
            ],
            "Inner London schools use IL_ prefix, Outer London use OL_ prefix"
        ),
        DataManipulationSkill(
            "pay_scale_points_setup",
            "Configure pay scale points and rates",
            "After pay scales are set up",
            [
                "Compare trust-provided rates with template for Teaching scales",
                "Check for 11-point vs 9-point Main-UPS scale (M1-M6 then UPS1-3 vs M1-U3)",
                "For missing/unused points: set Rate to 0 and Enabled to FALSE",
                "Check Rate Date From matches Project Scope date",
                "For Apprentice/NMW: use gov.uk rates, calculate annual: rate * 37 * 52.143",
            ],
            "11-point: M1-M6 increments yearly, UPS1-2 have 2 years each point"
        ),
        DataManipulationSkill(
            "staff_role_group_setup",
            "Set up staff role groups with correct finance codes",
            "Before creating staff roles",
            [
                "Extract unique Gross Salary Finance Codes from staff data (filter out 0 hours)",
                "Finance codes typically 4 or 6 digits (e.g., 2000 or 612100)",
                "Match each finance code to Staff Role Group using Finance Codes Budget tab",
                "Add Employers NI Finance Code and Pension Finance Code for each group",
                "All codes must be under same Ledger Code",
                "If Leadership Non-Teaching requested: find codes for those specific roles",
                "Add A_FTE, WK_FTE, A_FTE_LEAVE_ADJ, WK_FTE_LEAVE_ADJ codes to Finance Codes S2",
            ],
            "Teaching staff -> TEA group, Support staff -> grouped by function (Admin, Site, etc.)"
        ),
        DataManipulationSkill(
            "manipulate_staff_data",
            "Prepare staff data for IMP import",
            "When source data received from trust",
            [
                "Create copy of source data - save original tab untouched",
                "Create 'IMP Staff Data' tab for manipulation",
                "Create columns with IMP headers alongside original columns",
                "Complete Pay Scale, Full Time Hours, Staff Role Group Code columns first",
                "Clean up Staff Role Titles: fix spelling, proper case, standardize variations",
                "Streamline roles: 'Admin Assistant', 'Assistant Admin' -> 'Admin Assistant'",
                "Teachers: consolidate 'Teacher of Maths', 'KS3 Teacher' -> 'Teacher' (keep original in notes)",
                "Exclude 0-hour contracts from staff role creation",
                "Create Staff Roles tab with unique combinations, remove duplicates",
            ],
            "'Administrative Assistant', 'Assistant Admin', 'Admin Assistant' all become 'Admin Assistant'"
        ),
        DataManipulationSkill(
            "staff_role_coding",
            "Create consistent staff role codes",
            "After cleaning staff role titles",
            [
                "Create Staff Role Code column in manipulated workbook",
                "Check for duplicate titles with different Pay Scale or Full Time Hours",
                "If duplicate: adjust title to indicate difference (e.g., 'Admin Assistant - North Yorkshire')",
                "Create codes following pattern in Staff Roles Catalogue",
                "Use XLOOKUP to map codes back to IMP Staff Data tab",
                "Sort roles by Staff Role Group (alphabetically) before copying to workbook",
            ],
            "Use prefix for group: TEA_ for teaching, ADM_ for admin, SIT_ for site staff"
        ),
        DataManipulationSkill(
            "staff_member_coding",
            "Create staff member codes and clean personal data",
            "After staff roles are created",
            [
                "For known staff: use Payroll Number as Staff Member Code",
                "For vacancies: use ZZ_VAC_01, ZZ_VAC_02, etc. with Forename='Role', Surname='Vacancy'",
                "For new joiners without payroll: use ZZ_TBC_01, ZZ_TBC_02, etc.",
                "Clean names: remove role descriptions, contract notes from name fields",
                "Split concatenated names: 'Smith, John' -> Forename='John', Surname='Smith'",
                "Create Gender Code column: Male->M, Female->F, blank->ZZZ",
                "Mark Casual column for 0-hour contracts",
            ],
            "'Jane 16hrs part time, Smith Breakfast Club' -> Forename='Jane', Surname='Smith'"
        ),
        DataManipulationSkill(
            "build_reconciliation",
            "Reconcile built contracts against IMP report",
            "After contracts imported to IMP",
            [
                "Export Staff Details Extract report from IMP (Reporting Suite > Staffing)",
                "If contracts have different dates: run multiple reports by effective date",
                "Remove hidden rows, set conditional formatting on IDs",
                "Round Hours Per Week to 2 decimal places",
                "Map Contract ID from report to source data using combined key (StaffCode+ContractRef+RoleCode)",
                "Create reconciliation columns: IMP value, Match (TRUE/FALSE), Difference, Notes",
                "Review: Contracted Hours, Weeks Paid, Pay Scale Point, FT Annual Rate, Actual Salary",
                "For non-built contracts: add note (0 Hour, Leaver, 0 Budget)",
                "Red font for any items requiring Trust review",
            ],
            "Differences often due to rounding or service band variations in EQWP"
        ),
    ],

    # Build workflow from Process Notes
    build_workflow=[
        BuildWorkflow(
            "template_prep",
            "Prepare the Strand 2 workbook template",
            [
                "Copy latest AA_NEW - Strand 2 Standard Workbook API to Workbook folder",
                "Check version number on Parameters tab",
                "Update API key - orange tabs should update with Strand 1 data",
                "If tabs still show default data, refer to Lead Consultant",
            ],
            ["Configured workbook with Strand 1 structure loaded"],
            []
        ),
        BuildWorkflow(
            "pay_structure_build",
            "Build pay scales, points, grades, allowances",
            [
                "Delete unused London weighting pay scales",
                "Configure NJC as LA or Trust standard",
                "Compare and update pay rates from trust files",
                "Set up pay scale grades (progression paths)",
                "Configure allowance types and points",
                "Set up pension schemes (TPS, LGPS)",
                "Build equated weeks patterns from leave entitlements",
            ],
            ["19_PayScales", "20_PayScalePoints", "22_PayScaleGrades",
             "16_AllowanceTypes", "24_Pensions", "23_EQWPatterns"],
            ["template_prep"]
        ),
        BuildWorkflow(
            "staff_structure_build",
            "Build staff role groups and roles",
            [
                "Extract unique salary finance codes from staff data",
                "Map to Staff Role Groups with NI and Pension codes",
                "Create manipulated workbook with IMP Staff Data tab",
                "Clean and standardize staff role titles",
                "Create unique Staff Role Codes",
                "Link roles to pay scales and full time hours",
            ],
            ["26_StfRoleGroup", "27_StfRole", "Manipulated workbook"],
            ["pay_structure_build"]
        ),
        BuildWorkflow(
            "contracts_build",
            "Build staff members and contracts",
            [
                "Create Staff Member Codes (payroll or ZZ_VAC/ZZ_TBC)",
                "Clean personal data (names, DOB, gender)",
                "Build teaching contracts (FTE-based) to 28_ContractsTeachFTE",
                "Build support contracts (hours-based) to 29_ContractsSupportHours",
                "Add contract allowances (TLR, SEN) to 34_ContractAllowances",
                "Add contract adjustments if applicable",
                "Exclude 0-hour contracts (mark as Casual)",
            ],
            ["25_StaffMembers", "28_ContractsTeachFTE", "29_ContractsSupportHours",
             "34_ContractAllowances"],
            ["staff_structure_build"]
        ),
        BuildWorkflow(
            "validation_reconciliation",
            "Validate, import, and reconcile",
            [
                "Complete Build Checklist - ensure no import errors",
                "Import to IMP Planner",
                "Export Staff Details Extract report",
                "Create Build Reconciliation workbook",
                "Compare Hours, Weeks Paid, Pay Scale Points, Salaries",
                "Document all differences with notes",
                "Flag items for Trust review in red",
            ],
            ["Data imported", "Build Reconciliation complete"],
            ["contracts_build"]
        ),
    ]
)


# =============================================================================
# STRAND 3 KNOWLEDGE - Financial Team
# =============================================================================

S3_KNOWLEDGE = TeamKnowledge(
    team_id="S3",
    team_name="Financial Team",
    description="Handles financial planning: budgets, funding streams, pupil numbers, scenarios",

    key_concepts={
        "scenario": "A budget version/projection. Examples: Base, Optimistic, Worst Case",
        "budget_period": "Financial year for budget. Format: 2024-25",
        "funding_stream": "Source of income: GAG (General Annual Grant), PP (Pupil Premium), etc.",
        "pupil_numbers": "Census/forecast pupil counts driving funding calculations",
        "calculator": "Formula-based calculation for deriving budget values",
        "month_profile": "How annual budget spreads across months (different for income vs expenditure)",
        "brought_forward": "Balance carried from previous year",
        "carry_forward": "Projected balance at year end",
        "per_pupil_rate": "Funding amount per pupil for various grants",
        "actuals": "Historical transaction data for comparison with budget",
    },

    column_mappings=[
        ColumnMapping("finance_code", [
            "finance code", "account code", "nominal", "ledger code",
            "budget code", "gl code"
        ], "code", True, "Must exist in Strand 1 COA. 4 digits."),

        ColumnMapping("cost_centre", [
            "cost centre", "school", "location", "site"
        ], "code", True, "Must match Strand 1"),

        ColumnMapping("fund_code", [
            "fund", "fund code", "funding code"
        ], "code", False, "If using fund accounting"),

        ColumnMapping("amount", [
            "amount", "value", "budget", "total", "budget value"
        ], "numeric", True, "Budget amount. Negative for expenditure common."),

        ColumnMapping("period", [
            "period", "financial year", "budget year", "year"
        ], "text", True, "Format: 2024-25 or similar"),

        ColumnMapping("scenario", [
            "scenario", "version", "budget version"
        ], "text", False, "Base/Optimistic/Worst Case etc."),

        ColumnMapping("pupil_numbers", [
            "pupil numbers", "pupils", "fte pupils", "census", "pupil count"
        ], "numeric", False, "Integer count of pupils"),

        ColumnMapping("funding_rate", [
            "rate", "funding rate", "per pupil rate", "unit rate"
        ], "numeric", False, "GBP per pupil or per unit"),

        ColumnMapping("description", [
            "description", "budget line", "name", "title"
        ], "text", False, "Description of budget line"),

        ColumnMapping("month_profile", [
            "profile", "month profile", "spread"
        ], "text", False, "How budget spreads across months"),
    ],

    validation_rules=[
        ValidationRule(
            "finance_code_coa",
            "All finance codes must exist in Strand 1 COA",
            "reference", "critical",
            "Cross-reference against COA master. Add missing codes to Strand 1."
        ),
        ValidationRule(
            "budget_vs_actuals",
            "Budget lines should exist for accounts with historical spend",
            "reference", "warning",
            "Flag accounts with significant actuals but no budget"
        ),
        ValidationRule(
            "funding_calculation",
            "Funding = pupil_numbers x funding_rate",
            "calculation", "error",
            "Verify calculation matches stated amount"
        ),
        ValidationRule(
            "budget_balance",
            "Income + Expenditure + B/F = C/F",
            "calculation", "warning",
            "Verify budget balances correctly"
        ),
        ValidationRule(
            "staff_cost_reconciliation",
            "Staff budget should align with Strand 2 total salary costs",
            "reference", "warning",
            "Compare budgeted staff costs with calculated from contracts"
        ),
        ValidationRule(
            "negative_values",
            "Negative values may represent expenditure or credits",
            "format", "info",
            "Verify sign convention is consistent"
        ),
    ],

    business_rules=[
        "Income codes (4xxx) typically positive, expenditure (5xxx-9xxx) may be negative",
        "Staff costs from Strand 2 should reconcile with staff budget lines",
        "Pupil-driven funding uses census numbers and per-pupil rates",
        "GAG funding is largest income stream for most academies",
        "Month profiles vary: staff costs = even, grants = front-loaded",
        "Brought forward balance comes from prior year accounts",
        "Scenarios allow what-if analysis without changing base budget",
    ],

    common_issues=[
        "Finance codes don't match Strand 1 COA",
        "Missing pupil numbers for funding calculations",
        "Inconsistent sign conventions (some systems use positive expenditure)",
        "Staff budget doesn't reconcile with actual staff costs",
        "Missing month profiles default to even spread",
    ],

    remediation_patterns={
        "missing_coa_code": "Add to Strand 1 COA or map to existing equivalent",
        "sign_convention": "Standardize: income positive, expenditure negative for variance calc",
        "pupil_calc": "Verify: amount = pupil_numbers x rate. Flag if not within 1%",
        "staff_reconcile": "Compare budget 5xxx/6xxx totals with Strand 2 salary sum",
    },

    # Template sheets from AA_New - Strand 3 Standard Workbook API
    template_sheets=[
        TemplateSheet("Pupils Insert Table", "Raw pupil data entry from census",
                     ["FinanceCode", "SchoolCode", "FinancialYear", "Value"], 1),
        TemplateSheet("Pupils", "Processed pupil numbers for import",
                     ["FinanceCode", "SchoolCode", "FinancialYear", "YearValue"], 2),
        TemplateSheet("Statistics", "Rates and statistics for calculations",
                     ["StatisticCode", "SchoolCode", "Value"], 3),
        TemplateSheet("Funding", "Funding values from statements",
                     ["FinanceCode", "SchoolCode", "FinancialYear", "YearValue"], 4),
        TemplateSheet("14_Calculators", "Calculator definitions",
                     ["CalculatorCode", "Title", "Formula", "Category"], 5),
        TemplateSheet("15_MonthProfiles", "Month profiling patterns",
                     ["MonthProfileCode", "Title", "Sep", "Oct", "Nov", "Dec",
                      "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"], 6),
        TemplateSheet("Income", "Income budget lines for Master scenario",
                     ["FinanceCode", "SchoolCode", "Title", "YearValue",
                      "Calculator", "Calculated", "MonthProfileCode"], 7),
        TemplateSheet("Expenditure", "Expenditure budget lines for Master scenario",
                     ["FinanceCode", "SchoolCode", "Title", "YearValue",
                      "Calculator", "Calculated", "MonthProfileCode"], 8),
        TemplateSheet("ScenarioApBud", "Approved/frozen budget scenario",
                     ["ScenarioCode", "FinanceCode", "SchoolCode", "Title", "YearValue"], 9),
        TemplateSheet("BF Balances", "Brought forward balances",
                     ["FinanceCode", "SchoolCode", "YearValue"], 10),
        TemplateSheet("35_ScenarioRows", "Scenario budget rows for import",
                     ["ScenarioRowID", "FinanceCode", "SchoolCode", "Title"], 11),
        TemplateSheet("36_ScenarioYearValues", "Scenario year values",
                     ["ScenarioRowID", "FinancialYear", "YearValue"], 12),
        TemplateSheet("37_Monthly Values", "Monthly breakdown values",
                     ["ScenarioRowID", "Month", "Value"], 13),
    ],

    # Data manipulation skills from Process Notes - Strand 3
    manipulation_skills=[
        DataManipulationSkill(
            "grant_database_setup",
            "Set up the Grant Database for the trust",
            "At start of Strand 3 - required for all grants",
            [
                "Copy Planner Grant Database to Manipulated > Strand 3 folder",
                "Enter school names, URNs, and codes from Schools tab",
                "Open Queries and Connections > Grant Database Source",
                "Import source folder from Data Manipulation Tools > Grant Database Source",
                "Close and load, then refresh table on Summary tab",
                "Grant database provides: SCA factors, Pupil Premium, DFC, UIFSM numbers",
            ],
            "Grant database pulls ESFA grant figures automatically by URN"
        ),
        DataManipulationSkill(
            "pupil_numbers_entry",
            "Enter census pupil numbers for calculations",
            "After grant database set up",
            [
                "Locate census documents in Customer Supplied Data > Strand 3 > Pupil Numbers",
                "Spring numbers: enter on PUPIL_SPRING_[key stage] - used for DFC, SCA, PE Grant",
                "Autumn numbers: enter on PUPIL_CEN_[year group] - used for RPA",
                "Check for Subsidiary pupils - remove from totals",
                "PLAC & Service: enter on PUPILPREMIUMPLAC/PUPILPREMIUMSERV from Autumn census",
                "High Needs Pre-16: check Table D on funding statement",
                "High Needs Post-16: check fourth page of funding statement",
                "Occupied places: £6,000, Unoccupied: £10,000",
            ],
            "Spring 2023 numbers used for 2024/25 DFC calculation"
        ),
        DataManipulationSkill(
            "funding_statement_check",
            "Reconcile pupil numbers to funding statement",
            "After pupil numbers entered",
            [
                "Refresh Funding Statement Check table",
                "Compare IMP Autumn totals with funding statement numbers",
                "Pre-16: pupil totals on page 3, Post-16: page 1",
                "Variances over 5-10 pupils: flag to Lead Consultant",
                "Enter adjustments on FUNDED_[key stage]_ADJ with opposite sign",
                "Example: -91 variance -> enter 91 on adjustment line",
                "Keep adjustment lines even if zero (used in ICFP)",
            ],
            "Variance may be due to leavers/joiners between census and funding allocation"
        ),
        DataManipulationSkill(
            "dfc_calculation",
            "Calculate Devolved Formula Capital grant",
            "For capital funding allocation",
            [
                "DFC = £4,000 fixed + (£11.25 x weighted pupils)",
                "Weighted pupils: Nursery/Primary=1, Secondary=1.5, Post-16=2, Special/PRU=4.5",
                "Uses January census from TWO years previous",
                "Split into academic year: 7/12ths (Sep-Mar) and 5/12ths (Apr-Aug)",
                "If can't match ESFA weighted pupils: overwrite with grant database values",
                "Use calculators: DFC_CORE (fixed), DFC_PUPIL_[key stage] (per pupil)",
            ],
            "2024/25 DFC uses Spring 2023 pupil numbers"
        ),
        DataManipulationSkill(
            "pe_grant_calculation",
            "Calculate PE and Sports Premium grant",
            "For primary/special schools with eligible pupils",
            [
                "PE Grant = £16,000 core + (£10 x eligible pupils)",
                "Uses January census from previous year",
                "Only for schools with Reception-Y6 pupils",
                "Use calculators: PEG_CORE (£16,000), PEG_PUPIL (£10 rate)",
            ],
            "School with 200 primary pupils: £16,000 + (£10 x 200) = £18,000"
        ),
        DataManipulationSkill(
            "uifsm_calculation",
            "Calculate Universal Infant Free School Meals funding",
            "For schools with Reception-Y2 pupils",
            [
                "Get January and October UIFSM numbers from grant database",
                "Look for 'Total Eligible Meals' element with January/October census",
                "Enter on PUPIL_UIFSM_JAN and PUPIL_UIFSM_OCT in previous year",
                "Annual calculation: (JAN + OCT) / 2 x UIFSM_RATE_FIN (currently £490.20)",
            ],
            "27 Jan meals + 30 Oct meals -> (27+30)/2 x £490.20 = £13,980.70"
        ),
        DataManipulationSkill(
            "budget_manipulation",
            "Manipulate and combine budget files",
            "When customer provides multiple budget files",
            [
                "Save copies to Manipulated folder before editing",
                "Use Power Query to combine multiple budgets: Data > Get Data > From Folder",
                "Remove empty columns and rows",
                "Reorganize columns to match workbook order",
                "Remove £0 budget lines - not needed",
                "Remove locations not required per Project Scope",
                "Income lines: set as NEGATIVE values",
                "Expenditure lines: set as POSITIVE values",
                "Convert formulas to static values before import",
            ],
            "Power Query: Get Data > From Folder > select budget files > Transform"
        ),
        DataManipulationSkill(
            "scenario_setup",
            "Configure budget scenarios",
            "When building Master and Approved budgets",
            [
                "Approved Budget: use code APBUD[year] e.g., APBUD2425",
                "Master Budget: use code MASTER_OG",
                "Master scenario: default scenario with calculated lines (no code)",
                "Keep approved/master as faithful to source as possible",
                "Only adjust coding errors or scope-requested changes",
                "Bespoke budgets: code provided by Lead Consultant",
            ],
            "APBUD2425 = frozen approved budget, MASTER_OG = frozen current budget"
        ),
        DataManipulationSkill(
            "income_expenditure_build",
            "Build Income and Expenditure tabs",
            "For Master scenario budget lines",
            [
                "Copy income lines - ensure NEGATIVE sign in YearValue",
                "Copy expenditure lines - ensure POSITIVE sign",
                "For calculated lines: set Calculator column, Calculated=TRUE, no YearValue",
                "Remove duplicate lines (default + customer) for same grant",
                "For grants (TPAG/TPECG/CSBG): keep customer values if provided",
                "Check each default line: locate in customer budget, enter finance code",
                "Remove unused default lines (e.g., no SCA if not eligible)",
            ],
            "Central Charge income: enter finance code from customer data, keep calculator"
        ),
    ],

    # Build workflow from Process Notes
    build_workflow=[
        BuildWorkflow(
            "phase1_setup",
            "Phase 1: Template, Grant Database, Pupils",
            [
                "Copy latest Strand 3 Standard Workbook to Workbook folder",
                "Update API key on Parameters tab",
                "Update school information from Scope (LA, school type)",
                "Set up Grant Database with school URNs",
                "Enter census pupil numbers (Spring, Autumn, PLAC, Service)",
                "Enter High Needs numbers from funding statements",
                "Complete Funding Statement Check - enter adjustments",
                "Enter UIFSM and Pupil Premium numbers from grant database",
            ],
            ["Grant Database populated", "Pupils tab complete", "Funding Statement Check done"],
            []
        ),
        BuildWorkflow(
            "phase1_statistics",
            "Phase 1: Statistics and Funding",
            [
                "Enter rates and statistics used in calculations",
                "Set up calculators for each grant type",
                "Enter funding values from statements",
                "Configure month profiles (23 standard + bespoke if needed)",
            ],
            ["Statistics tab complete", "Calculators configured"],
            ["phase1_setup"]
        ),
        BuildWorkflow(
            "phase2_budgets",
            "Phase 2: Manipulate and enter budgets",
            [
                "Combine customer budget files using Power Query if needed",
                "Remove £0 lines and unnecessary locations",
                "Standardize sign convention (income negative, expenditure positive)",
                "Identify scenario requirements from Scope",
                "Build ScenarioApBud for Approved budget",
                "Build MASTER_OG for Master budget if different from Approved",
            ],
            ["Manipulated budget file", "ScenarioApBud populated"],
            ["phase1_statistics"]
        ),
        BuildWorkflow(
            "phase2_income_expenditure",
            "Phase 2: Build Income and Expenditure",
            [
                "Enter income lines to Income tab (negative values)",
                "Enter expenditure lines to Expenditure tab (positive values)",
                "Configure calculated lines with correct calculators",
                "Match default grant lines to customer finance codes",
                "Remove unused default lines",
                "Enter Brought Forward balances",
            ],
            ["Income tab complete", "Expenditure tab complete", "BF Balances entered"],
            ["phase2_budgets"]
        ),
        BuildWorkflow(
            "phase2_validation",
            "Phase 2: Validation and completion",
            [
                "Run Funding Check to verify calculations match grant database",
                "Review ScenarioSummary for balance/variance checks",
                "Complete Strand 3 Checklist - fix any import errors",
                "Use CSV Extraction Tool to generate import files",
                "Import to IMP Planner",
                "Complete Import Checklist - verify all counts match",
            ],
            ["Funding Check passed", "Data imported", "Import Checklist complete"],
            ["phase2_income_expenditure"]
        ),
    ]
)


# =============================================================================
# GRANT CALCULATION REFERENCE DATA (from S3 Knowledge)
# =============================================================================

GRANT_CALCULATIONS = {
    "DFC": {
        "name": "Devolved Formula Capital",
        "fixed_sum": 4000,
        "per_pupil_rate": 11.25,
        "weighted_pupils": {
            "nursery_primary": 1.0,
            "secondary": 1.5,
            "post_16": 2.0,
            "special_pru_boarders": 4.5,
        },
        "census_year_offset": -2,  # Uses Spring census from 2 years previous
        "academic_split": {"sep_mar": 7/12, "apr_aug": 5/12},
        "formula": "(£4,000 + £11.25 x weighted pupils) x VA factor",
    },
    "SCA": {
        "name": "School Condition Allocation",
        "per_pupil_rate": 148.50,
        "weighted_pupils": {
            "nursery_primary": 1.0,
            "secondary": 1.5,
            "post_16": 2.0,
            "special_pru_boarders": 4.5,
        },
        "eligibility": {
            "min_schools": 5,
            "min_pupils": 3000,
            "census_date": "September 2023",
        },
        "factors": ["SCA_band", "location_factor", "VA_factor", "PFI_factor"],
        "pfi_rate": 0.5,  # Reduces allocation by half for PFI schools
        "formula": "£148.50 x weighted pupils x SCA band x location factor x VA factor x PFI factor",
    },
    "PE_GRANT": {
        "name": "PE and Sports Premium",
        "core_value": 16000,
        "per_pupil_rate": 10.00,
        "eligible_year_groups": ["Reception", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6"],
        "census_year_offset": -1,  # Uses January census from previous year
        "formula": "£16,000 + (£10 x eligible pupils)",
    },
    "UIFSM": {
        "name": "Universal Infant Free School Meals",
        "rate_per_meal": 490.20,  # Annual rate per eligible pupil
        "eligible_year_groups": ["Reception", "Y1", "Y2"],
        "calculation": "(January_count + October_count) / 2 x rate",
    },
    "PUPIL_PREMIUM": {
        "name": "Pupil Premium",
        "rates_2024_25": {
            "primary_fsm": 1480,
            "secondary_fsm": 1050,
            "lac": 2570,  # Looked After Children
            "plac": 2570,  # Previously Looked After
            "service": 340,  # Service children
        },
    },
    "APPRENTICE_LEVY": {
        "name": "Apprentice Levy",
        "threshold": 3000000,  # Annual pay bill threshold
        "rate": 0.005,  # 0.5% of pay bill above threshold
        "allowance": 15000,  # Annual allowance to offset
        "formula": "((Pay Bill - £3m) x 0.5%) - £15,000 allowance",
    },
    "RPA": {
        "name": "Risk Protection Arrangement",
        "description": "Calculated from Autumn census pupil numbers",
        "uses_autumn_census": True,
    },
}


# =============================================================================
# PAY SCALE REFERENCE DATA
# =============================================================================

PAY_SCALES_2024_25 = {
    "teaching": {
        "MPS": {  # Main Pay Scale (England & Wales)
            1: 31650, 2: 33483, 3: 35674, 4: 37938, 5: 40426, 6: 43607
        },
        "UPS": {  # Upper Pay Scale
            1: 45646, 2: 47340, 3: 49084
        },
        "leadership": {  # Leadership (L1-L43)
            1: 49781, 2: 50978, 3: 52201, 4: 53451, 5: 54732,
            6: 56044, 7: 57391, 8: 58959, 9: 60488, 10: 62104,
            # ... continues to L43
        }
    },
    "support": {
        "NJC": {  # National Joint Council (example values)
            1: 22366, 2: 22737, 3: 23114, 4: 23500, 5: 23893,
            6: 24294, 7: 24702, 8: 25119, 9: 25545, 10: 25979,
            11: 26421, 12: 26873, 13: 27334, 14: 27803, 15: 28282,
            16: 28770, 17: 29269, 18: 29777, 19: 30296, 20: 30825,
            # ... continues
        }
    },
    "full_time_hours": {
        "teaching": 32.5,
        "support": 37.0,
    },
    "weeks_per_year": 52.143,
}


TTO_LEAVE_ENTITLEMENTS = {
    # Site-specific leave entitlements (days)
    "default": {
        "under_5_years": {"leave": 27, "bank_holidays": 8},
        "5_plus_years": {"leave": 32, "bank_holidays": 8},
    },
    "errington": {
        "under_5_years": {"leave": 29, "bank_holidays": 8},
        "5_plus_years": {"leave": 34, "bank_holidays": 8},
    },
    "college_sfca": {
        "under_2_years": {"leave": 24, "bank_holidays": 8},
        "2_to_5_years": {"leave": 26, "bank_holidays": 8},
        "5_plus_years": {"leave": 29, "bank_holidays": 8},
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_team_knowledge(team_id: str) -> TeamKnowledge:
    """Get knowledge base for a specific team."""
    knowledge_map = {
        "S1": S1_KNOWLEDGE,
        "S2": S2_KNOWLEDGE,
        "S3": S3_KNOWLEDGE,
    }
    return knowledge_map.get(team_id)


def calculate_tto_paid_weeks(weeks_worked: float, leave_days: int, bank_holidays: int) -> float:
    """Calculate TTO paid weeks from working weeks and leave entitlement."""
    holiday_weeks = (leave_days + bank_holidays) / 5
    return weeks_worked + holiday_weeks


def calculate_fte(weekly_hours: float, full_time_hours: float) -> float:
    """Calculate FTE from hours."""
    if full_time_hours <= 0:
        return 0.0
    return round(weekly_hours / full_time_hours, 6)


def validate_salary_vs_scale(salary: float, scale_type: str, point: int,
                              tolerance: float = 0.05) -> tuple:
    """
    Validate salary matches pay scale point.
    Returns (is_valid, expected_salary, variance_pct)
    """
    scales = PAY_SCALES_2024_25.get("teaching" if scale_type in ["MPS", "UPS", "leadership"] else "support", {})
    scale = scales.get(scale_type, {})
    expected = scale.get(point)

    if expected is None:
        return (None, None, None)  # Unknown scale/point

    variance = abs(salary - expected) / expected if expected > 0 else 0
    is_valid = variance <= tolerance

    return (is_valid, expected, round(variance * 100, 2))


def normalize_scale_point(point_str: str) -> tuple:
    """
    Normalize pay scale point format.
    Returns (scale_type, point_number)

    Examples:
        'M1', 'MPS1', 'Main 1' -> ('MPS', 1)
        'U2', 'UPS2', 'Upper 2' -> ('UPS', 2)
        'L8', 'Leadership 8' -> ('leadership', 8)
        'SCP11', 'Point 11', '11' -> ('NJC', 11)
    """
    import re

    point_str = str(point_str).strip().upper()

    # Teaching Main
    if re.match(r'^(MPS?|MAIN|M)\s*(\d+)$', point_str):
        match = re.search(r'(\d+)', point_str)
        return ('MPS', int(match.group(1)))

    # Teaching Upper
    if re.match(r'^(UPS?|UPPER|U)\s*(\d+)$', point_str):
        match = re.search(r'(\d+)', point_str)
        return ('UPS', int(match.group(1)))

    # Leadership
    if re.match(r'^(L|LEADERSHIP|LSHIP)\s*(\d+)$', point_str):
        match = re.search(r'(\d+)', point_str)
        return ('leadership', int(match.group(1)))

    # Support NJC
    if re.match(r'^(SCP|SPINE|POINT)?\s*(\d+)$', point_str):
        match = re.search(r'(\d+)', point_str)
        return ('NJC', int(match.group(1)))

    return (None, None)


def normalize_finance_code(code: str) -> str:
    """
    Normalize finance code to 4-digit format with leading zeros.

    Examples:
        '1' -> '0001'
        '12' -> '0012'
        '1130' -> '1130'
        '625100' -> check if '6251' or '2510' makes sense
    """
    import re

    # Convert to string and clean
    code_str = str(code).strip()

    # Extract numeric portion
    numeric = re.sub(r'[^0-9]', '', code_str)

    if not numeric:
        return None

    # If already 4 digits, return as-is
    if len(numeric) == 4:
        return numeric

    # If less than 4 digits, pad with leading zeros
    if len(numeric) < 4:
        return numeric.zfill(4)

    # If more than 4 digits, try common patterns
    if len(numeric) == 6:
        # Try removing first 2 digits
        option1 = numeric[2:]  # '625100' -> '5100'
        # Try removing last 2 digits
        option2 = numeric[:4]  # '625100' -> '6251'
        return option2  # Default to first 4

    return numeric[:4]  # Take first 4 digits


def is_teaching_role(job_title: str) -> bool:
    """Determine if job title indicates a teaching role."""
    teaching_keywords = [
        'teacher', 'head', 'deputy', 'tutor', 'lecturer', 'principal',
        'instructor', 'educator', 'hod', 'curriculum lead'
    ]
    title_lower = str(job_title).lower()
    return any(kw in title_lower for kw in teaching_keywords)


def is_support_role(job_title: str) -> bool:
    """Determine if job title indicates a support role."""
    support_keywords = [
        'assistant', 'officer', 'admin', 'technician', 'cleaner', 'caretaker',
        'receptionist', 'finance', 'hr', 'it', 'maintenance', 'cook', 'chef',
        'midday', 'supervisor', 'coordinator', 'secretary', 'clerk'
    ]
    title_lower = str(job_title).lower()
    return any(kw in title_lower for kw in support_keywords)


# =============================================================================
# S3 GRANT CALCULATION HELPERS
# =============================================================================

def calculate_dfc(pupils_by_keystage: Dict[str, int], va_factor: float = 1.0) -> Dict[str, float]:
    """
    Calculate Devolved Formula Capital grant.

    Args:
        pupils_by_keystage: Dict with keys 'nursery_primary', 'secondary', 'post_16', 'special'
        va_factor: Voluntary Aided factor (typically 1.0)

    Returns:
        Dict with 'total', 'fixed', 'per_pupil', 'sep_mar', 'apr_aug'
    """
    calc = GRANT_CALCULATIONS["DFC"]

    # Calculate weighted pupils
    weighted = 0
    weights = calc["weighted_pupils"]
    weighted += pupils_by_keystage.get("nursery_primary", 0) * weights["nursery_primary"]
    weighted += pupils_by_keystage.get("secondary", 0) * weights["secondary"]
    weighted += pupils_by_keystage.get("post_16", 0) * weights["post_16"]
    weighted += pupils_by_keystage.get("special", 0) * weights["special_pru_boarders"]

    fixed = calc["fixed_sum"]
    per_pupil = calc["per_pupil_rate"] * weighted
    total = (fixed + per_pupil) * va_factor

    return {
        "total": round(total, 2),
        "fixed": fixed,
        "per_pupil": round(per_pupil, 2),
        "weighted_pupils": weighted,
        "sep_mar": round(total * 7/12, 2),
        "apr_aug": round(total * 5/12, 2),
    }


def calculate_pe_grant(eligible_pupils: int) -> Dict[str, float]:
    """
    Calculate PE and Sports Premium grant.

    Args:
        eligible_pupils: Number of pupils in Reception-Y6

    Returns:
        Dict with 'total', 'core', 'per_pupil'
    """
    calc = GRANT_CALCULATIONS["PE_GRANT"]

    core = calc["core_value"]
    per_pupil = calc["per_pupil_rate"] * eligible_pupils
    total = core + per_pupil

    return {
        "total": round(total, 2),
        "core": core,
        "per_pupil": round(per_pupil, 2),
        "eligible_pupils": eligible_pupils,
    }


def calculate_uifsm(january_count: int, october_count: int) -> Dict[str, float]:
    """
    Calculate Universal Infant Free School Meals funding.

    Args:
        january_count: Eligible pupils at January census
        october_count: Eligible pupils at October census

    Returns:
        Dict with 'total', 'average_pupils', 'rate'
    """
    calc = GRANT_CALCULATIONS["UIFSM"]

    average = (january_count + october_count) / 2
    total = average * calc["rate_per_meal"]

    return {
        "total": round(total, 2),
        "average_pupils": average,
        "rate": calc["rate_per_meal"],
        "january_count": january_count,
        "october_count": october_count,
    }


def calculate_pupil_premium(primary_fsm: int = 0, secondary_fsm: int = 0,
                            lac: int = 0, plac: int = 0, service: int = 0) -> Dict[str, float]:
    """
    Calculate Pupil Premium funding.

    Args:
        primary_fsm: Primary FSM pupils
        secondary_fsm: Secondary FSM pupils
        lac: Looked After Children
        plac: Previously Looked After Children
        service: Service children

    Returns:
        Dict with total and breakdown by category
    """
    rates = GRANT_CALCULATIONS["PUPIL_PREMIUM"]["rates_2024_25"]

    breakdown = {
        "primary_fsm": primary_fsm * rates["primary_fsm"],
        "secondary_fsm": secondary_fsm * rates["secondary_fsm"],
        "lac": lac * rates["lac"],
        "plac": plac * rates["plac"],
        "service": service * rates["service"],
    }

    total = sum(breakdown.values())

    return {
        "total": round(total, 2),
        "breakdown": breakdown,
        "pupil_counts": {
            "primary_fsm": primary_fsm,
            "secondary_fsm": secondary_fsm,
            "lac": lac,
            "plac": plac,
            "service": service,
        }
    }


def calculate_apprentice_levy(annual_pay_bill: float) -> Dict[str, float]:
    """
    Calculate Apprentice Levy.

    Args:
        annual_pay_bill: Total annual pay bill

    Returns:
        Dict with levy amount and whether allowance applies
    """
    calc = GRANT_CALCULATIONS["APPRENTICE_LEVY"]

    if annual_pay_bill <= calc["threshold"]:
        return {"levy": 0, "net_levy": 0, "below_threshold": True}

    excess = annual_pay_bill - calc["threshold"]
    levy = excess * calc["rate"]
    net_levy = max(0, levy - calc["allowance"])

    return {
        "levy": round(levy, 2),
        "allowance": calc["allowance"],
        "net_levy": round(net_levy, 2),
        "pay_bill": annual_pay_bill,
        "below_threshold": False,
    }


# =============================================================================
# DATA MANIPULATION HELPERS
# =============================================================================

def standardize_budget_signage(amount: float, is_income: bool) -> float:
    """
    Standardize budget signage: income negative, expenditure positive.

    Args:
        amount: The budget amount
        is_income: True if this is an income line

    Returns:
        Amount with correct sign
    """
    if is_income:
        return -abs(amount)
    else:
        return abs(amount)


def create_staff_role_code(title: str, group_prefix: str) -> str:
    """
    Create a standardized staff role code from title.

    Args:
        title: Staff role title
        group_prefix: Prefix for the group (TEA, ADM, SIT, etc.)

    Returns:
        Standardized code like 'TEA_TEACHER' or 'ADM_ADMIN_ASSISTANT'
    """
    import re

    # Clean and standardize
    clean_title = title.upper().strip()
    clean_title = re.sub(r'[^A-Z0-9\s]', '', clean_title)
    clean_title = re.sub(r'\s+', '_', clean_title)

    # Truncate if too long
    if len(clean_title) > 20:
        clean_title = clean_title[:20]

    return f"{group_prefix}_{clean_title}"


def create_staff_member_code(payroll_number: str, is_vacancy: bool = False,
                             is_tbc: bool = False, sequence: int = 1) -> str:
    """
    Create staff member code from payroll number or vacancy/TBC pattern.

    Args:
        payroll_number: Payroll reference (may be None for vacancies)
        is_vacancy: True if this is a vacancy
        is_tbc: True if payroll number TBC
        sequence: Sequence number for vacancies/TBC

    Returns:
        Staff member code
    """
    if is_vacancy:
        return f"ZZ_VAC_{sequence:02d}"
    elif is_tbc:
        return f"ZZ_TBC_{sequence:02d}"
    else:
        return str(payroll_number).strip()


def split_concatenated_name(full_name: str) -> tuple:
    """
    Split concatenated name into forename and surname.

    Args:
        full_name: Name like 'Smith, John' or 'John Smith'

    Returns:
        Tuple of (forename, surname)
    """
    if not full_name or not full_name.strip():
        return ("", "")

    name = full_name.strip()

    # Handle "Surname, Forename" format
    if ',' in name:
        parts = name.split(',', 1)
        surname = parts[0].strip()
        forename = parts[1].strip() if len(parts) > 1 else ""
        return (forename, surname)

    # Handle "Forename Surname" format
    parts = name.split()
    if len(parts) >= 2:
        forename = parts[0]
        surname = ' '.join(parts[1:])
        return (forename, surname)

    # Single name - assume surname
    return ("", name)


def get_team_manipulation_skills(team_id: str) -> List[DataManipulationSkill]:
    """Get manipulation skills for a specific team."""
    knowledge = get_team_knowledge(team_id)
    return knowledge.manipulation_skills if knowledge else []


def get_team_build_workflow(team_id: str) -> List[BuildWorkflow]:
    """Get build workflow for a specific team."""
    knowledge = get_team_knowledge(team_id)
    return knowledge.build_workflow if knowledge else []


def get_team_template_sheets(team_id: str) -> List[TemplateSheet]:
    """Get template sheets for a specific team."""
    knowledge = get_team_knowledge(team_id)
    return knowledge.template_sheets if knowledge else []


# =============================================================================
# S2 DOMAIN KNOWLEDGE INTEGRATION HELPERS
# =============================================================================

def get_s2_domain_knowledge_status() -> Dict[str, Any]:
    """
    Get status of S2 domain knowledge integration.
    Returns information about available data and functions.
    """
    return {
        "available": S2_DOMAIN_KNOWLEDGE_AVAILABLE,
        "pay_scales_count": len(S2_PAY_SCALES) if S2_DOMAIN_KNOWLEDGE_AVAILABLE else 0,
        "role_groups_count": len(STAFF_ROLE_GROUPS) if S2_DOMAIN_KNOWLEDGE_AVAILABLE else 0,
        "equated_week_patterns_count": len(EQUATED_WEEK_PATTERNS) if S2_DOMAIN_KNOWLEDGE_AVAILABLE else 0,
        "combined_columns": COMBINED_COLUMNS if S2_DOMAIN_KNOWLEDGE_AVAILABLE else [],
    }


def get_s2_pay_scales() -> Dict:
    """Get S2 pay scales dictionary."""
    if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
        return S2_PAY_SCALES
    return {}


def get_s2_staff_role_groups() -> Dict:
    """Get S2 staff role groups dictionary."""
    if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
        return STAFF_ROLE_GROUPS
    return {}


def get_s2_equated_week_patterns() -> Dict:
    """Get S2 equated week patterns dictionary."""
    if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
        return EQUATED_WEEK_PATTERNS
    return {}


def parse_s2_combined_field(value: str) -> tuple:
    """
    Parse a combined field in S2 format "CODE: Title".
    Wrapper for the S2 domain knowledge function.
    """
    if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
        return parse_combined_field(value)
    return (str(value), str(value))


def transform_s2_contract_row(row: dict) -> dict:
    """
    Transform a contract row using S2 domain knowledge.
    Wrapper for the S2 domain knowledge function.
    """
    if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
        return transform_contract_row(row)
    return row
