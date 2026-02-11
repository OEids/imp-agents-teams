"""
Data Processor

Transforms customer data into IMP Planner template format.
Each team has specialized processors for their strand.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re

from .knowledge import (
    get_team_knowledge, get_team_template_sheets,
    normalize_finance_code, normalize_scale_point,
    split_concatenated_name, create_staff_member_code, create_staff_role_code,
    is_teaching_role, is_support_role,
    PAY_SCALES_2024_25
)


@dataclass
class ProcessingResult:
    """Result of data processing."""
    success: bool
    template_sheets: Dict[str, pd.DataFrame]
    issues: List[str]
    assumptions: List[str]
    summary: Dict[str, Any]


class BaseDataProcessor:
    """Base class for data processors."""

    def __init__(self, team_id: str):
        self.team_id = team_id
        self.knowledge = get_team_knowledge(team_id)
        self.template_sheets = get_team_template_sheets(team_id)
        self.issues = []
        self.assumptions = []

    def log(self, message: str):
        """Log a processing message."""
        print(f"[{self.team_id}] {message}")

    def add_issue(self, issue: str):
        """Record an issue found during processing."""
        self.issues.append(issue)

    def add_assumption(self, assumption: str):
        """Record an assumption made during processing."""
        self.assumptions.append(assumption)


class S2DataProcessor(BaseDataProcessor):
    """
    Processes Strand 2 (Staff) data into template format.

    Input: Customer staffing files with contract data
    Output: Data ready for S2 template sheets
    """

    def __init__(self):
        super().__init__("S2")
        self.staff_data = []
        self.pay_scales_data = None
        self.schools = set()
        self.finance_codes = set()
        self.staff_roles = {}
        self.staff_members = {}

    def process(self, customer_data_dir: Path) -> ProcessingResult:
        """
        Process all S2 customer data.

        Args:
            customer_data_dir: Path to customer data folder

        Returns:
            ProcessingResult with template-ready DataFrames
        """
        self.log("Starting S2 data processing...")

        # 1. Load all source files
        self._load_source_files(customer_data_dir)

        # 2. Process pay scales
        pay_scales_df = self._process_pay_scales()
        pay_scale_points_df = self._process_pay_scale_points()

        # 3. Process staff data
        staff_roles_df = self._process_staff_roles()
        staff_role_groups_df = self._process_staff_role_groups()
        staff_members_df = self._process_staff_members()

        # 4. Process contracts
        contracts_teach_df = self._process_contracts_teaching()
        contracts_support_df = self._process_contracts_support()

        # Build result
        template_sheets = {
            "19_PayScales": pay_scales_df,
            "20_PayScalePoints": pay_scale_points_df,
            "26_StfRoleGroup": staff_role_groups_df,
            "27_StfRole": staff_roles_df,
            "25_StaffMembers": staff_members_df,
            "28_ContractsTeachFTE": contracts_teach_df,
            "29_ContractsSupportHours": contracts_support_df,
        }

        summary = {
            "total_staff": len(self.staff_members),
            "total_contracts": len(self.staff_data),
            "teaching_contracts": len(contracts_teach_df) if contracts_teach_df is not None else 0,
            "support_contracts": len(contracts_support_df) if contracts_support_df is not None else 0,
            "staff_roles": len(self.staff_roles),
            "schools": list(self.schools),
        }

        self.log(f"Processing complete: {summary['total_staff']} staff, {summary['total_contracts']} contracts")

        return ProcessingResult(
            success=len(self.issues) == 0,
            template_sheets=template_sheets,
            issues=self.issues,
            assumptions=self.assumptions,
            summary=summary
        )

    def _load_source_files(self, data_dir: Path):
        """Load all source data files."""
        self.log(f"Loading source files from {data_dir}")

        # Find staffing files
        for f in data_dir.glob("**/*.xls*"):
            if f.name.startswith("~$"):
                continue

            self.log(f"  Reading {f.name}")

            try:
                xl = None
                # Try multiple engines for reading Excel files
                try:
                    xl = pd.ExcelFile(f, engine='openpyxl')
                except Exception as e1:
                    try:
                        xl = pd.ExcelFile(f, engine='xlrd')
                    except Exception as e2:
                        # Try direct read_excel
                        try:
                            xls_dict = pd.read_excel(f, sheet_name=None)
                            if xls_dict:
                                for sheet_name, sheet_data in xls_dict.items():
                                    if "contract" in sheet_name.lower() and "check" not in sheet_name.lower():
                                        df = sheet_data
                                        if df is not None and len(df) > 0:
                                            df.columns = [self._clean_column_name(c) for c in df.columns]
                                            self.staff_data.append({
                                                "file": f.name,
                                                "sheet": sheet_name,
                                                "data": df
                                            })
                                if "pay scale" in f.name.lower():
                                    self.log(f"  Pay scales loaded from {f.name}")
                                continue
                        except Exception as e3:
                            self.add_issue(f"Error reading {f.name}: Multiple engine failures - {e1} | {e2} | {e3}")
                            continue

                if xl is None:
                    continue

                # Check for pay scales
                if "pay scale" in f.name.lower():
                    self.pay_scales_data = xl
                    self._extract_pay_scales(xl)

                # Check for staff contract sheets
                for sheet in xl.sheet_names:
                    sheet_lower = sheet.lower()
                    if "contract" in sheet_lower and "check" not in sheet_lower:
                        df = self._read_staff_sheet(xl, sheet, f.name)
                        if df is not None and len(df) > 0:
                            self.staff_data.append({
                                "file": f.name,
                                "sheet": sheet,
                                "data": df
                            })

            except Exception as e:
                self.add_issue(f"Error reading {f.name}: {e}")

    def _read_staff_sheet(self, xl: pd.ExcelFile, sheet: str, filename: str) -> Optional[pd.DataFrame]:
        """Read and normalize a staff contract sheet."""
        try:
            # Read raw data
            df = pd.read_excel(xl, sheet, header=None)

            # Find header row (look for recognizable headers)
            header_row = None
            for idx, row in df.iterrows():
                row_str = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
                if 'last name' in row_str or 'surname' in row_str or 'payroll' in row_str:
                    header_row = idx
                    break

            if header_row is None:
                # Try using row 1 as header
                header_row = 1

            # Re-read with proper header
            df = pd.read_excel(xl, sheet, header=header_row)

            # Clean column names
            df.columns = [self._clean_column_name(c) for c in df.columns]

            # Remove empty rows
            df = df.dropna(how='all')

            # Add source info
            df['_source_file'] = filename
            df['_source_sheet'] = sheet

            return df

        except Exception as e:
            self.add_issue(f"Error reading sheet {sheet}: {e}")
            return None

    def _clean_column_name(self, col: Any) -> str:
        """Clean and standardize column name."""
        col_str = str(col).strip()

        # Map common variations to standard names
        mappings = {
            'last name': 'surname',
            'surname': 'surname',
            'first name': 'forename',
            'forename': 'forename',
            'unique payroll': 'payroll_number',
            'payroll number': 'payroll_number',
            'employee id': 'payroll_number',
            'continuous service': 'service_start_date',
            'service start': 'service_start_date',
            'work location': 'school_code',
            'school name': 'school_code',
            'location': 'school_code',
            'staff role': 'job_title',
            'job title': 'job_title',
            'gross salary finance': 'finance_code',
            'finance code': 'finance_code',
            'nominal': 'finance_code',
            'department code': 'cost_centre',
            'cost centre': 'cost_centre',
            'fund code': 'fund_code',
            'full time hours': 'full_time_hours',
            'weekly hours': 'weekly_hours',
            'hours per week': 'weekly_hours',
            'weekly fte': 'fte',
            'annual fte': 'fte',
            'weeks worked': 'weeks_worked',
            'tto weeks worked': 'weeks_worked',
            'weeks paid': 'weeks_paid',
            'tto weeks paid': 'weeks_paid',
            'pay scale': 'pay_scale',
            'pay range': 'pay_scale',
            'scale point': 'scale_point',
            'current scale point': 'scale_point',
            'spine point': 'scale_point',
            'grade': 'grade',
            'max scale point': 'grade',
            'annual salary': 'annual_salary',
            'fte salary': 'annual_salary',
            'actual salary': 'actual_salary',
            'pension': 'pension_scheme',
            'contract type': 'contract_type',
            'contract start': 'contract_start',
            'contract end': 'contract_end',
            'date of birth': 'dob',
            'dob': 'dob',
            'gender': 'gender',
            'contract reference': 'contract_ref',
        }

        col_lower = col_str.lower()
        for pattern, standard in mappings.items():
            if pattern in col_lower:
                return standard

        return col_str

    def _extract_pay_scales(self, xl: pd.ExcelFile):
        """Extract pay scale information from pay scales file."""
        self.log("  Extracting pay scales...")

        for sheet in xl.sheet_names:
            sheet_lower = sheet.lower()
            if 'teaching' in sheet_lower:
                self._extract_teaching_scales(xl, sheet)
            elif 'support' in sheet_lower:
                self._extract_support_scales(xl, sheet)

    def _extract_teaching_scales(self, xl: pd.ExcelFile, sheet: str):
        """Extract teaching pay scales."""
        # Placeholder - will be customized per customer data format
        self.add_assumption("Using default teaching pay scales (MPS, UPS, Leadership)")

    def _extract_support_scales(self, xl: pd.ExcelFile, sheet: str):
        """Extract support pay scales."""
        # Placeholder - will be customized per customer data format
        self.add_assumption("Using default support pay scales (NJC)")

    def _process_pay_scales(self) -> pd.DataFrame:
        """Generate pay scales template data."""
        self.log("Processing pay scales...")

        # Default pay scales
        scales = [
            {"PayScaleCode": "MPS_EW", "Title": "Teachers Main Pay Scale (England & Wales)",
             "IncrementDate": "01/09/2025", "IncreaseDate": "01/09/2025", "IncreasePercentage": 0,
             "AvailableToAllSchools": True, "SchoolCodes": ""},
            {"PayScaleCode": "UPS_EW", "Title": "Upper Pay Scale (England & Wales)",
             "IncrementDate": "01/09/2025", "IncreaseDate": "01/09/2025", "IncreasePercentage": 0,
             "AvailableToAllSchools": True, "SchoolCodes": ""},
            {"PayScaleCode": "LEAD_EW", "Title": "Leadership (England & Wales)",
             "IncrementDate": "01/09/2025", "IncreaseDate": "01/09/2025", "IncreasePercentage": 0,
             "AvailableToAllSchools": True, "SchoolCodes": ""},
            {"PayScaleCode": "MAT_SUP", "Title": "MAT Support Scale",
             "IncrementDate": "01/04/2025", "IncreaseDate": "01/04/2025", "IncreasePercentage": 0,
             "AvailableToAllSchools": True, "SchoolCodes": ""},
        ]

        return pd.DataFrame(scales)

    def _process_pay_scale_points(self) -> pd.DataFrame:
        """Generate pay scale points template data."""
        self.log("Processing pay scale points...")

        points = []

        # MPS points
        mps_rates = PAY_SCALES_2024_25["teaching"]["MPS"]
        for point, rate in mps_rates.items():
            points.append({
                "PayScaleCode": "MPS_EW",
                "PayScalePointCode": f"M{point}",
                "Title": f"Main {point}",
                "ScalePointNumber": point,
                "RateDateFrom": "01/09/2024",
                "PayScaleRate": rate,
                "Enabled": True
            })

        # UPS points
        ups_rates = PAY_SCALES_2024_25["teaching"]["UPS"]
        for point, rate in ups_rates.items():
            points.append({
                "PayScaleCode": "UPS_EW",
                "PayScalePointCode": f"U{point}",
                "Title": f"Upper {point}",
                "ScalePointNumber": point,
                "RateDateFrom": "01/09/2024",
                "PayScaleRate": rate,
                "Enabled": True
            })

        # NJC points (sample)
        njc_rates = PAY_SCALES_2024_25["support"]["NJC"]
        for point, rate in njc_rates.items():
            points.append({
                "PayScaleCode": "MAT_SUP",
                "PayScalePointCode": f"SCP{point}",
                "Title": f"Spine Point {point}",
                "ScalePointNumber": point,
                "RateDateFrom": "01/04/2024",
                "PayScaleRate": rate,
                "Enabled": True
            })

        return pd.DataFrame(points)

    def _process_staff_roles(self) -> pd.DataFrame:
        """Generate staff roles from contract data."""
        self.log("Processing staff roles...")

        roles = []

        for source in self.staff_data:
            df = source['data']

            if 'job_title' in df.columns:
                for _, row in df.iterrows():
                    title = str(row.get('job_title', '')).strip()
                    if not title or title == 'nan':
                        continue

                    # Determine role type
                    if is_teaching_role(title):
                        role_type = 'teaching'
                        group = 'TEA'
                        pay_scale = 'MPS_EW'
                        ft_hours = 32.5
                    else:
                        role_type = 'support'
                        group = 'SUP'
                        pay_scale = 'MAT_SUP'
                        ft_hours = row.get('full_time_hours', 37) or 37

                    # Clean title
                    clean_title = self._clean_staff_role_title(title)

                    # Create code
                    code = create_staff_role_code(clean_title, group)

                    if code not in self.staff_roles:
                        self.staff_roles[code] = {
                            "StaffRoleCode": code,
                            "Title": clean_title,
                            "PayScaleCode": pay_scale,
                            "FullTimeHours": ft_hours,
                            "StaffRoleGroupCode": f"SRG_{group}",
                            "MonthsServiceBeforeIncrement": 0 if role_type == 'teaching' else 6,
                            "AvailableToAllSchools": True,
                            "SchoolCodes": "",
                        }

        return pd.DataFrame(list(self.staff_roles.values()))

    def _clean_staff_role_title(self, title: str) -> str:
        """Clean and standardize staff role title."""
        # Remove job codes like "J55 - "
        title = re.sub(r'^[A-Z]\d+\s*[-:]\s*', '', title)

        # Proper case
        title = title.strip().title()

        # Standardize common variations
        replacements = {
            'Ta ': 'Teaching Assistant ',
            'Hlta': 'HLTA',
            'Senco': 'SENCO',
            'Ict': 'ICT',
            'Pe ': 'PE ',
            'Eyfs': 'EYFS',
        }
        for old, new in replacements.items():
            title = title.replace(old, new)

        return title.strip()

    def _process_staff_role_groups(self) -> pd.DataFrame:
        """Generate staff role groups."""
        self.log("Processing staff role groups...")

        # Collect unique finance codes from staff data
        teaching_codes = set()
        support_codes = set()

        for source in self.staff_data:
            df = source['data']
            if 'finance_code' in df.columns and 'job_title' in df.columns:
                for _, row in df.iterrows():
                    fc = str(row.get('finance_code', '')).strip()
                    title = str(row.get('job_title', ''))
                    if fc and fc != 'nan':
                        fc = normalize_finance_code(fc) or fc
                        self.finance_codes.add(fc)
                        if is_teaching_role(title):
                            teaching_codes.add(fc)
                        else:
                            support_codes.add(fc)

        groups = [
            {
                "StaffRoleGroupCode": "SRG_TEA",
                "Title": "Teaching Staff",
                "GrossSalaryFinanceCode": list(teaching_codes)[0] if teaching_codes else "2000",
                "EmployersNIFinanceCode": "2010",
                "PensionFinanceCode": "2020",
            },
            {
                "StaffRoleGroupCode": "SRG_SUP",
                "Title": "Support Staff",
                "GrossSalaryFinanceCode": list(support_codes)[0] if support_codes else "2700",
                "EmployersNIFinanceCode": "2710",
                "PensionFinanceCode": "2720",
            },
        ]

        self.add_assumption(f"Using finance codes: Teaching={teaching_codes}, Support={support_codes}")

        return pd.DataFrame(groups)

    def _process_staff_members(self) -> pd.DataFrame:
        """Generate staff members from contract data."""
        self.log("Processing staff members...")

        members = []
        vacancy_count = 0
        tbc_count = 0

        for source in self.staff_data:
            df = source['data']

            for _, row in df.iterrows():
                # Get payroll number
                payroll = row.get('payroll_number', '')
                payroll_str = str(payroll).strip() if pd.notna(payroll) else ''

                # Get names
                surname = str(row.get('surname', '')).strip()
                forename = str(row.get('forename', '')).strip()

                # Handle missing data
                if not payroll_str or payroll_str == 'nan':
                    if 'vacancy' in surname.lower() or 'vacancy' in forename.lower():
                        vacancy_count += 1
                        code = create_staff_member_code('', is_vacancy=True, sequence=vacancy_count)
                    else:
                        tbc_count += 1
                        code = create_staff_member_code('', is_tbc=True, sequence=tbc_count)
                else:
                    code = create_staff_member_code(payroll_str)

                if code in self.staff_members:
                    continue  # Already processed

                # Get school
                school = str(row.get('school_code', '')).strip()
                if school and school != 'nan':
                    self.schools.add(school)

                # Get dates
                service_start = row.get('service_start_date', '')
                dob = row.get('dob', '')

                # Get gender
                gender = str(row.get('gender', 'ZZZ')).strip().upper()
                if gender in ['M', 'MALE']:
                    gender = 'M'
                elif gender in ['F', 'FEMALE']:
                    gender = 'F'
                else:
                    gender = 'ZZZ'

                member = {
                    "StaffMemberCode": code,
                    "Forename": forename if forename != 'nan' else '',
                    "Surname": surname if surname != 'nan' else '',
                    "ServiceStartDate": service_start if pd.notna(service_start) else '',
                    "ServiceEndDate": '',
                    "DateOfBirth": dob if pd.notna(dob) else '',
                    "GenderCode": gender,
                    "Apprenticeship": False,
                    "PensionOptOut": False,
                    "AvailableToAllSchools": True,
                    "SchoolCodes": school,
                    "PayrollLocation": school,
                    "Casual": False,
                }

                self.staff_members[code] = member
                members.append(member)

        return pd.DataFrame(members)

    def _process_contracts_teaching(self) -> pd.DataFrame:
        """Generate teaching contracts."""
        self.log("Processing teaching contracts...")

        contracts = []

        for source in self.staff_data:
            df = source['data']

            for _, row in df.iterrows():
                job_title = str(row.get('job_title', ''))

                if not is_teaching_role(job_title):
                    continue

                # Get staff member code
                payroll = row.get('payroll_number', '')
                payroll_str = str(payroll).strip() if pd.notna(payroll) else ''

                if not payroll_str or payroll_str == 'nan':
                    continue

                staff_code = create_staff_member_code(payroll_str)

                # Get role code
                clean_title = self._clean_staff_role_title(job_title)
                role_code = create_staff_role_code(clean_title, 'TEA')

                # Get contract details
                fte = row.get('fte', 1.0)
                if pd.isna(fte):
                    fte = 1.0

                school = str(row.get('school_code', '')).strip()
                contract_ref = str(row.get('contract_ref', '')).strip()

                # Scale point - handle various formats
                scale_point_raw = row.get('scale_point', '')
                try:
                    if pd.isna(scale_point_raw) or str(scale_point_raw).strip() in ['', 'nan']:
                        scale_point = ''
                    else:
                        scale_point = str(scale_point_raw).strip().split('\n')[0]
                except:
                    scale_point = ''

                scale_type, point_num = normalize_scale_point(scale_point)
                if scale_type == 'MPS':
                    point_code = f"M{point_num}"
                elif scale_type == 'UPS':
                    point_code = f"U{point_num}"
                elif scale_type == 'leadership':
                    point_code = f"L{point_num}"
                elif point_num:
                    point_code = f"M{point_num}"  # Default to MPS if just a number
                else:
                    point_code = scale_point if scale_point else "M1"

                contract = {
                    "StaffMemberCode": staff_code,
                    "ContractRef": contract_ref if contract_ref != 'nan' else '',
                    "SchoolCode": school if school != 'nan' else '',
                    "StaffRoleCode": role_code,
                    "AnnualFTE": float(fte),
                    "PayScaleGradeCode": "",
                    "PayScalePointCode": point_code,
                    "PensionCode": "TPS",
                    "EQWPCode": "FULL_YEAR",
                    "ContractTypeCode": "PERM",
                    "ContractStart": "",
                    "ContractEnd": "",
                }

                contracts.append(contract)

        return pd.DataFrame(contracts)

    def _process_contracts_support(self) -> pd.DataFrame:
        """Generate support staff contracts."""
        self.log("Processing support contracts...")

        contracts = []

        for source in self.staff_data:
            df = source['data']

            for _, row in df.iterrows():
                job_title = str(row.get('job_title', ''))

                if is_teaching_role(job_title):
                    continue

                # Skip 0-hour contracts
                hours = row.get('weekly_hours', 0)
                if pd.isna(hours) or float(hours) == 0:
                    continue

                # Get staff member code
                payroll = row.get('payroll_number', '')
                payroll_str = str(payroll).strip() if pd.notna(payroll) else ''

                if not payroll_str or payroll_str == 'nan':
                    continue

                staff_code = create_staff_member_code(payroll_str)

                # Get role code
                clean_title = self._clean_staff_role_title(job_title)
                role_code = create_staff_role_code(clean_title, 'SUP')

                school = str(row.get('school_code', '')).strip()
                contract_ref = str(row.get('contract_ref', '')).strip()

                # Scale point - handle various formats
                scale_point_raw = row.get('scale_point', '')
                try:
                    if pd.isna(scale_point_raw) or str(scale_point_raw).strip() in ['', 'nan']:
                        scale_point = ''
                    else:
                        scale_point = str(scale_point_raw).strip().split('\n')[0]
                except:
                    scale_point = ''

                scale_type, point_num = normalize_scale_point(scale_point)
                if point_num:
                    point_code = f"SCP{point_num}"
                else:
                    point_code = scale_point if scale_point else "SCP1"

                # Weeks
                weeks_paid = row.get('weeks_paid', 52.143)
                if pd.isna(weeks_paid):
                    weeks_paid = 52.143

                contract = {
                    "StaffMemberCode": staff_code,
                    "ContractRef": contract_ref if contract_ref != 'nan' else '',
                    "SchoolCode": school if school != 'nan' else '',
                    "StaffRoleCode": role_code,
                    "HoursPerWeek": float(hours),
                    "PayScaleGradeCode": "",
                    "PayScalePointCode": point_code,
                    "PensionCode": "LGPS",
                    "EQWPCode": "TTO_38" if float(weeks_paid) < 50 else "FULL_YEAR",
                    "ContractTypeCode": "PERM",
                    "ContractStart": "",
                    "ContractEnd": "",
                }

                contracts.append(contract)

        return pd.DataFrame(contracts)


def process_s2_data(customer_data_dir: Path, output_dir: Path) -> ProcessingResult:
    """
    Main entry point for S2 data processing.

    Args:
        customer_data_dir: Path to customer S2 data
        output_dir: Path to save output files

    Returns:
        ProcessingResult with all template data
    """
    processor = S2DataProcessor()
    result = processor.process(customer_data_dir)

    # Save outputs
    if result.success or result.template_sheets:
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"S2_template_data_{timestamp}.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in result.template_sheets.items():
                if df is not None and len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Add summary sheet
            summary_df = pd.DataFrame([result.summary])
            summary_df.to_excel(writer, sheet_name='_Summary', index=False)

            # Add issues sheet
            if result.issues:
                issues_df = pd.DataFrame({'Issues': result.issues})
                issues_df.to_excel(writer, sheet_name='_Issues', index=False)

            # Add assumptions sheet
            if result.assumptions:
                assumptions_df = pd.DataFrame({'Assumptions': result.assumptions})
                assumptions_df.to_excel(writer, sheet_name='_Assumptions', index=False)

        print(f"Output saved to: {output_file}")

    return result
