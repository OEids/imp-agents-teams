"""
S1 Specialist Agent - Structure Team

Deep analysis and complete template builder for:
- Finance Codes (Chart of Accounts)
- Schools / Cost Centres
- Departments
- Funds
- DFE COA Mappings
- System Grouping Codes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ExtractedFinanceCode:
    """Extracted finance code data."""
    code: str
    title: str
    grouping_code: str
    ledger_code: str
    school_codes: List[str]
    available_to_all: bool
    code_type: str  # income, expenditure, balance_sheet


@dataclass
class ExtractedSchool:
    """Extracted school data."""
    code: str
    title: str
    la_code: str
    school_type: str
    school_hub: str
    urn: str


@dataclass
class ExtractedDepartment:
    """Extracted department data."""
    code: str
    title: str
    ledger_code: str
    activity_code: str
    school_codes: List[str]


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
    """

    def __init__(self):
        self.extracted_finance_codes: List[ExtractedFinanceCode] = []
        self.extracted_schools: List[ExtractedSchool] = []
        self.extracted_departments: List[ExtractedDepartment] = []
        self.extracted_funds: List[Dict] = []
        self.issues: List[str] = []
        self.assumptions: List[str] = []

        self.template_data = {
            "System Grouping Codes": [],
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

        # Tracking
        self.local_authorities = {}
        self.school_types = {}
        self.school_hubs = {}
        self.ledger_codes = {}
        self.activities = {}

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
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
                self._classify_and_extract(df, file_path.name, "CSV")
            else:
                xl = pd.ExcelFile(file_path)
                self.log(f"  Sheets: {xl.sheet_names}")

                for sheet in xl.sheet_names:
                    if self._is_skip_sheet(sheet):
                        continue

                    df = self._read_sheet_smart(xl, sheet)
                    if df is not None and len(df) > 0:
                        self._classify_and_extract(df, file_path.name, sheet)

        except Exception as e:
            self.issues.append(f"Error analyzing {file_path.name}: {e}")

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
        """Standardize column name."""
        if pd.isna(col):
            return "unnamed"

        col_str = str(col).strip().lower()

        mappings = {
            'nominal': 'finance_code',
            'finance code': 'finance_code',
            'account code': 'finance_code',
            'code': 'code',
            'title': 'title',
            'description': 'title',
            'name': 'title',
            'dfe': 'dfe_code',
            'grouping': 'grouping_code',
            'ledger': 'ledger_code',
            'cost centre': 'cost_centre',
            'department': 'department',
            'school': 'school_code',
            'location': 'school_code',
            'fund': 'fund_code',
            'la': 'la_code',
            'local authority': 'la_code',
            'urn': 'urn',
            'type': 'school_type',
        }

        for pattern, standard in mappings.items():
            if pattern in col_str:
                return standard

        return col_str.replace(' ', '_')

    def _classify_and_extract(self, df: pd.DataFrame, file_name: str, sheet_name: str):
        """Classify data type and extract."""
        cols = [str(c).lower() for c in df.columns]
        sheet_lower = sheet_name.lower()

        # Finance codes / COA
        if any(c in cols for c in ['finance_code', 'nominal', 'account']):
            self._extract_finance_codes(df, sheet_name)
            self.log(f"    -> Finance codes extracted")

        # Schools
        elif 'school' in sheet_lower or any(c in cols for c in ['urn', 'school_code']):
            self._extract_schools(df)
            self.log(f"    -> Schools extracted")

        # Departments
        elif 'dept' in sheet_lower or 'cost centre' in sheet_lower:
            self._extract_departments(df)
            self.log(f"    -> Departments extracted")

        # DFE Mapping
        elif 'dfe' in sheet_lower or 'mapping' in sheet_lower:
            self._extract_dfe_mappings(df)
            self.log(f"    -> DFE mappings extracted")

    def _extract_finance_codes(self, df: pd.DataFrame, sheet_name: str):
        """Extract finance codes from dataframe."""
        code_col = None
        title_col = None
        grouping_col = None

        for col in df.columns:
            col_lower = str(col).lower()
            if 'code' in col_lower and not code_col:
                code_col = col
            elif 'title' in col_lower or 'description' in col_lower:
                title_col = col
            elif 'grouping' in col_lower or 'dfe' in col_lower:
                grouping_col = col

        if not code_col:
            return

        for _, row in df.iterrows():
            code = row.get(code_col)
            if pd.isna(code):
                continue

            code_str = str(code).strip()
            if not code_str or code_str == 'nan':
                continue

            # Normalize code
            code_str = self._normalize_finance_code(code_str)

            title = str(row.get(title_col, '')).strip() if title_col else ''
            if title == 'nan':
                title = ''

            grouping = str(row.get(grouping_col, 'ZZZ')).strip() if grouping_col else 'ZZZ'
            if grouping == 'nan':
                grouping = 'ZZZ'

            # Determine code type from code range
            code_type = self._determine_code_type(code_str)

            # Determine ledger
            ledger = self._determine_ledger(code_str, title)

            fc = ExtractedFinanceCode(
                code=code_str,
                title=title,
                grouping_code=grouping,
                ledger_code=ledger,
                school_codes=[],
                available_to_all=True,
                code_type=code_type,
            )
            self.extracted_finance_codes.append(fc)

    def _normalize_finance_code(self, code: str) -> str:
        """Normalize finance code format."""
        code = str(code).strip()

        # Remove non-alphanumeric except underscore
        code = re.sub(r'[^\w]', '', code)

        # If 6 digits, take first 4 (common pattern)
        if len(code) == 6 and code.isdigit():
            code = code[:4]

        # Pad to 4 digits if numeric
        if code.isdigit() and len(code) < 4:
            code = code.zfill(4)

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
        """Determine ledger code from finance code."""
        title_lower = title.lower()

        if 'capital' in title_lower:
            return 'CAPITAL'
        elif 'staff' in title_lower or 'salary' in title_lower:
            return 'STAFFING'
        elif 'premises' in title_lower or 'building' in title_lower:
            return 'PREMISES'
        elif 'supplies' in title_lower:
            return 'SUPPLIES'

        return 'COSTCTR'

    def _extract_schools(self, df: pd.DataFrame):
        """Extract schools from dataframe."""
        for _, row in df.iterrows():
            code = row.get('school_code') or row.get('code')
            if pd.isna(code):
                continue

            code_str = str(code).strip()
            if not code_str or code_str == 'nan':
                continue

            title = str(row.get('title', '')).strip()
            la_code = str(row.get('la_code', '')).strip()
            urn = str(row.get('urn', '')).strip()
            school_type = str(row.get('school_type', '')).strip()

            school = ExtractedSchool(
                code=code_str,
                title=title if title != 'nan' else code_str,
                la_code=la_code if la_code != 'nan' else '',
                school_type=school_type if school_type != 'nan' else '',
                school_hub='',
                urn=urn if urn != 'nan' else '',
            )
            self.extracted_schools.append(school)

            # Track LA
            if school.la_code:
                self.local_authorities[school.la_code] = school.la_code

    def _extract_departments(self, df: pd.DataFrame):
        """Extract departments from dataframe."""
        for _, row in df.iterrows():
            code = row.get('code') or row.get('department')
            if pd.isna(code):
                continue

            code_str = str(code).strip()
            if not code_str or code_str == 'nan':
                continue

            title = str(row.get('title', code_str)).strip()
            ledger = str(row.get('ledger_code', 'COSTCTR')).strip()

            dept = ExtractedDepartment(
                code=code_str,
                title=title if title != 'nan' else code_str,
                ledger_code=ledger if ledger != 'nan' else 'COSTCTR',
                activity_code='ACTIVITY',
                school_codes=[],
            )
            self.extracted_departments.append(dept)

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

        result = {}
        for sheet_name, data in self.template_data.items():
            if data:
                result[sheet_name] = pd.DataFrame(data)
                self.log(f"  {sheet_name}: {len(data)} rows")

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

    def _build_funds(self):
        """Build Funds sheet."""
        self.log("Building Funds...")

        # Default funds
        funds = [
            ("GAG", "General Annual Grant", True),
            ("PP", "Pupil Premium", True),
            ("CAPITAL", "Capital", True),
            ("RESTRICTED", "Restricted", True),
            ("UNRESTRICTED", "Unrestricted", True),
        ]

        for code, title, enabled in funds:
            self.template_data["Funds"].append({
                "FundCode": code,
                "Title": title,
                "FundEnabled": enabled,
            })

    def _build_activity(self):
        """Build Activity sheet."""
        self.log("Building Activity...")

        activities = [
            ("CURRICULUM", "Curriculum"),
            ("SUPPORT", "Support Services"),
            ("PREMISES", "Premises"),
            ("GOVERNANCE", "Governance"),
            ("CENTRAL", "Central Services"),
        ]

        for code, title in activities:
            self.template_data["Activity"].append({
                "ActivityCode": code,
                "Title": title,
                "ActivityEnabled": True,
            })

    def _build_ledger(self):
        """Build Ledger sheet."""
        self.log("Building Ledger...")

        ledgers = [
            ("COSTCTR", "Cost Centre"),
            ("STAFFING", "Staffing"),
            ("PREMISES", "Premises"),
            ("SUPPLIES", "Supplies & Services"),
            ("CAPITAL", "Capital"),
            ("DEFAULT", "Default"),
        ]

        for code, title in ledgers:
            self.template_data["Ledger"].append({
                "LedgerCode": code,
                "Title": title,
                "LedgerEnabled": True,
            })

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
                    "LACode": la_code,
                    "Title": la_code,
                    "LondonWeighting": "England & Wales",
                    "LAEnabled": True,
                })
        else:
            self.template_data["LocalAuth"].append({
                "LACode": "DEFAULT",
                "Title": "Default LA",
                "LondonWeighting": "England & Wales",
                "LAEnabled": True,
            })

    def _build_schools(self):
        """Build Schools sheet."""
        self.log("Building Schools...")

        if self.extracted_schools:
            for school in self.extracted_schools:
                self.template_data["Schools"].append({
                    "SchoolCode": school.code,
                    "Title": school.title,
                    "LACode": school.la_code or "DEFAULT",
                    "SchTypeCode": school.school_type or "PRIMARY",
                    "SchHubCode": school.school_hub or "DEFAULT",
                    "URN": school.urn,
                    "SchoolEnabled": True,
                    "IsMAT": school.school_type == "MAT",
                })
        else:
            # Add MAT default
            self.template_data["Schools"].append({
                "SchoolCode": "MAT",
                "Title": "MAT Central",
                "LACode": "DEFAULT",
                "SchTypeCode": "MAT",
                "SchHubCode": "DEFAULT",
                "URN": "",
                "SchoolEnabled": True,
                "IsMAT": True,
            })

    def _build_depts(self):
        """Build Depts sheet."""
        self.log("Building Depts...")

        if self.extracted_departments:
            for dept in self.extracted_departments:
                self.template_data["Depts"].append({
                    "DeptCode": dept.code,
                    "Title": dept.title,
                    "LedgerCode": dept.ledger_code,
                    "ActivityCode": dept.activity_code,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "DeptEnabled": True,
                })
        else:
            # Standard departments
            standard_depts = [
                ("STCH", "Staff Teaching", "STAFFING", "CURRICULUM"),
                ("SFIN", "Staff Finance", "STAFFING", "SUPPORT"),
                ("SPREM", "Staff Premises", "STAFFING", "PREMISES"),
                ("CURRICULUM", "Curriculum", "COSTCTR", "CURRICULUM"),
                ("ADMIN", "Administration", "COSTCTR", "SUPPORT"),
                ("PREMISES", "Premises", "PREMISES", "PREMISES"),
                ("DEFAULT", "Default", "DEFAULT", "SUPPORT"),
            ]

            for code, title, ledger, activity in standard_depts:
                self.template_data["Depts"].append({
                    "DeptCode": code,
                    "Title": title,
                    "LedgerCode": ledger,
                    "ActivityCode": activity,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": "",
                    "DeptEnabled": True,
                })

    def _build_finance_codes_budget(self):
        """Build FinanceCodes Budget sheet."""
        self.log("Building FinanceCodes Budget...")

        if self.extracted_finance_codes:
            for fc in self.extracted_finance_codes:
                self.template_data["FinanceCodes Budget"].append({
                    "FinanceCode": fc.code,
                    "Title": fc.title,
                    "FinanceCodeTypeCode": "BUDGET",
                    "GroupingCode": fc.grouping_code,
                    "CustomGrouping": "ZZZ",
                    "LedgerCode": fc.ledger_code,
                    "AvailableToAllSchools": fc.available_to_all,
                    "SchoolCodes": ",".join(fc.school_codes) if fc.school_codes else "",
                    "FinanceCodeEnabled": True,
                    "IsBalanceSheet": fc.code_type == 'balance_sheet',
                })

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def process(self, customer_data_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Main processing entry point."""
        self.log("="*60)
        self.log("S1 SPECIALIST AGENT - STARTING PROCESSING")
        self.log("="*60)

        # Phase 1: Analysis
        self.analyze_customer_data(customer_data_dir)

        # Phase 2: Build templates
        template_sheets = self.build_all_templates()

        # Save output
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"S1_complete_template_{timestamp}.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in template_sheets.items():
                if len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Summary
            summary_data = {
                "Metric": [
                    "Finance Codes",
                    "Schools",
                    "Departments",
                    "Local Authorities",
                    "Issues",
                ],
                "Value": [
                    len(self.extracted_finance_codes),
                    len(self.extracted_schools),
                    len(self.extracted_departments),
                    len(self.local_authorities),
                    len(self.issues),
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="_Summary", index=False)

        self.log(f"\nOutput saved to: {output_file}")

        return {
            "success": len(self.issues) == 0,
            "output_file": output_file,
            "template_sheets": template_sheets,
            "issues": self.issues,
            "summary": {
                "finance_codes": len(self.extracted_finance_codes),
                "schools": len(self.extracted_schools),
                "departments": len(self.extracted_departments),
            }
        }


def run_s1_specialist(customer_data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Run the S1 specialist agent."""
    agent = S1SpecialistAgent()
    return agent.process(customer_data_dir, output_dir)
