"""
S2 Data Validation Module

Validates S2 template data against IMP Planner data model rules.
Based on IMP Planner Knowledge Base (2026-03-11).
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, date
import pandas as pd


class S2Validator:
    """Validates S2 template data according to IMP Planner business rules."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_checks = []

    def validate_all(self, template_sheets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Run all validation checks on template sheets.

        Returns dict with:
            - passed: bool
            - errors: list of error messages
            - warnings: list of warning messages
            - passed_checks: list of passed check messages
            - score: validation score (0-100)
        """
        self.errors = []
        self.warnings = []
        self.passed_checks = []

        # Run all checks
        self._validate_staff_members(template_sheets.get('StaffMembers'))
        self._validate_contracts(template_sheets.get('ContractsTeachFTE'),
                                template_sheets.get('ContractsSupportHours'),
                                template_sheets.get('StaffMembers'))
        self._validate_pay_scales(template_sheets.get('PayScales'),
                                 template_sheets.get('PayScalePoints'))
        self._validate_staff_roles(template_sheets.get('StfRole'),
                                  template_sheets.get('StfRoleGroup'))
        self._validate_pensions(template_sheets.get('Pensions'))
        self._validate_eqwp(template_sheets.get('EqwPattern'))

        # Calculate score
        total_checks = len(self.errors) + len(self.warnings) + len(self.passed_checks)
        score = (len(self.passed_checks) / total_checks * 100) if total_checks > 0 else 0

        return {
            'passed': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'passed_checks': self.passed_checks,
            'score': score
        }

    def _validate_staff_members(self, df: Optional[pd.DataFrame]):
        """Validate Staff Members data."""
        if df is None or len(df) == 0:
            self.warnings.append("No Staff Members data to validate")
            return

        check_name = "Staff Members"

        # Check mandatory fields
        required_fields = ['StaffMemberCode', 'Forename', 'Surname', 'ServiceStartDate', 'GenderCode']
        missing_fields = [f for f in required_fields if f not in df.columns]

        if missing_fields:
            self.errors.append(f"{check_name}: Missing required fields: {', '.join(missing_fields)}")
        else:
            self.passed_checks.append(f"{check_name}: All required fields present")

        # Check for duplicate staff codes
        if 'StaffMemberCode' in df.columns:
            duplicates = df[df.duplicated('StaffMemberCode', keep=False)]
            if len(duplicates) > 0:
                codes = duplicates['StaffMemberCode'].unique()
                self.errors.append(f"{check_name}: Duplicate staff codes found: {', '.join(map(str, codes[:5]))}")
            else:
                self.passed_checks.append(f"{check_name}: No duplicate staff codes")

        # Check disabled staff have service end dates
        if 'IsDisabled' in df.columns and 'ServiceEndDate' in df.columns:
            disabled_no_end = df[(df['IsDisabled'] == True) & (df['ServiceEndDate'].isna())]
            if len(disabled_no_end) > 0:
                self.errors.append(f"{check_name}: {len(disabled_no_end)} disabled staff members have no Service End Date")
            else:
                self.passed_checks.append(f"{check_name}: All disabled staff have Service End Date")

    def _validate_contracts(self, teach_df: Optional[pd.DataFrame],
                           support_df: Optional[pd.DataFrame],
                           staff_df: Optional[pd.DataFrame]):
        """Validate Contracts data."""
        check_name = "Contracts"

        if teach_df is None and support_df is None:
            self.warnings.append(f"{check_name}: No contracts data to validate")
            return

        # Combine teaching and support contracts
        contracts = []
        if teach_df is not None and len(teach_df) > 0:
            contracts.append(teach_df)
        if support_df is not None and len(support_df) > 0:
            contracts.append(support_df)

        if not contracts:
            self.warnings.append(f"{check_name}: No contracts to validate")
            return

        all_contracts = pd.concat(contracts, ignore_index=True)

        # Check mandatory fields
        required_fields = ['StaffMemberCode', 'StfRoleCode', 'SchoolCode', 'DepartmentCode',
                          'PayScaleCode', 'ContractFromDate', 'ContractToDate', 'PensionCode',
                          'EqwPatternCode']
        missing_fields = [f for f in required_fields if f not in all_contracts.columns]

        if missing_fields:
            self.errors.append(f"{check_name}: Missing required fields: {', '.join(missing_fields)}")
        else:
            self.passed_checks.append(f"{check_name}: All required fields present")

        # Check FTE vs Hours
        if teach_df is not None and 'FTE' in teach_df.columns:
            invalid_fte = teach_df[(teach_df['FTE'] < 0) | (teach_df['FTE'] > 1)]
            if len(invalid_fte) > 0:
                self.errors.append(f"{check_name} (Teaching): {len(invalid_fte)} contracts have invalid FTE (must be 0.0-1.0)")
            else:
                self.passed_checks.append(f"{check_name} (Teaching): All FTE values valid")

        if support_df is not None and 'ContractedHours' in support_df.columns:
            invalid_hours = support_df[(support_df['ContractedHours'] <= 0) | (support_df['ContractedHours'] > 60)]
            if len(invalid_hours) > 0:
                self.warnings.append(f"{check_name} (Support): {len(invalid_hours)} contracts have unusual hours (<0 or >60)")
            else:
                self.passed_checks.append(f"{check_name} (Support): All hours values reasonable")

        # Check contract dates
        if 'ContractFromDate' in all_contracts.columns and 'ContractToDate' in all_contracts.columns:
            # Convert to datetime
            all_contracts['ContractFromDate'] = pd.to_datetime(all_contracts['ContractFromDate'], errors='coerce')
            all_contracts['ContractToDate'] = pd.to_datetime(all_contracts['ContractToDate'], errors='coerce')

            invalid_dates = all_contracts[all_contracts['ContractFromDate'] > all_contracts['ContractToDate']]
            if len(invalid_dates) > 0:
                self.errors.append(f"{check_name}: {len(invalid_dates)} contracts have From date after To date")
            else:
                self.passed_checks.append(f"{check_name}: All contract dates valid")

        # Check contracts against staff member service dates
        if staff_df is not None and 'StaffMemberCode' in all_contracts.columns:
            if 'ServiceStartDate' in staff_df.columns and 'ServiceEndDate' in staff_df.columns:
                staff_df['ServiceStartDate'] = pd.to_datetime(staff_df['ServiceStartDate'], errors='coerce')
                staff_df['ServiceEndDate'] = pd.to_datetime(staff_df['ServiceEndDate'], errors='coerce')

                merged = all_contracts.merge(staff_df[['StaffMemberCode', 'ServiceStartDate', 'ServiceEndDate']],
                                            on='StaffMemberCode', how='left')

                # Check contracts start after service start
                invalid_start = merged[merged['ContractFromDate'] < merged['ServiceStartDate']]
                if len(invalid_start) > 0:
                    self.warnings.append(f"{check_name}: {len(invalid_start)} contracts start before staff service start date")

                # Check contracts end before service end (if service end is set)
                invalid_end = merged[(merged['ServiceEndDate'].notna()) &
                                    (merged['ContractToDate'] > merged['ServiceEndDate'])]
                if len(invalid_end) > 0:
                    self.errors.append(f"{check_name}: {len(invalid_end)} contracts end after staff service end date")

    def _validate_pay_scales(self, scales_df: Optional[pd.DataFrame],
                            points_df: Optional[pd.DataFrame]):
        """Validate Pay Scales data."""
        check_name = "Pay Scales"

        if scales_df is None or len(scales_df) == 0:
            self.warnings.append(f"{check_name}: No pay scales to validate")
            return

        # Check mandatory fields
        required_fields = ['PayScaleCode', 'PayScaleTitle']
        missing_fields = [f for f in required_fields if f not in scales_df.columns]

        if missing_fields:
            self.errors.append(f"{check_name}: Missing required fields: {', '.join(missing_fields)}")
        else:
            self.passed_checks.append(f"{check_name}: All required fields present")

        # Check for duplicate codes
        if 'PayScaleCode' in scales_df.columns:
            duplicates = scales_df[scales_df.duplicated('PayScaleCode', keep=False)]
            if len(duplicates) > 0:
                codes = duplicates['PayScaleCode'].unique()
                self.errors.append(f"{check_name}: Duplicate scale codes: {', '.join(map(str, codes[:5]))}")
            else:
                self.passed_checks.append(f"{check_name}: No duplicate codes")

        # Check each scale has points
        if points_df is not None and 'PayScaleCode' in points_df.columns:
            scales_with_points = points_df['PayScaleCode'].unique()
            scales_without_points = [code for code in scales_df['PayScaleCode']
                                    if code not in scales_with_points]

            if scales_without_points:
                self.warnings.append(f"{check_name}: {len(scales_without_points)} scales have no pay points")
            else:
                self.passed_checks.append(f"{check_name}: All scales have pay points")

    def _validate_staff_roles(self, roles_df: Optional[pd.DataFrame],
                             groups_df: Optional[pd.DataFrame]):
        """Validate Staff Roles data."""
        check_name = "Staff Roles"

        if roles_df is None or len(roles_df) == 0:
            self.warnings.append(f"{check_name}: No staff roles to validate")
            return

        # Check mandatory fields
        required_fields = ['StfRoleCode', 'StfRoleTitle', 'StfRoleGroupCode', 'PayScaleCode']
        missing_fields = [f for f in required_fields if f not in roles_df.columns]

        if missing_fields:
            self.errors.append(f"{check_name}: Missing required fields: {', '.join(missing_fields)}")
        else:
            self.passed_checks.append(f"{check_name}: All required fields present")

        # Check role groups exist
        if groups_df is not None and 'StfRoleGroupCode' in roles_df.columns:
            valid_groups = groups_df['StfRoleGroupCode'].unique() if 'StfRoleGroupCode' in groups_df.columns else []
            orphan_roles = roles_df[~roles_df['StfRoleGroupCode'].isin(valid_groups)]

            if len(orphan_roles) > 0:
                self.errors.append(f"{check_name}: {len(orphan_roles)} roles have invalid role group codes")
            else:
                self.passed_checks.append(f"{check_name}: All roles have valid role groups")

    def _validate_pensions(self, df: Optional[pd.DataFrame]):
        """Validate Pensions data."""
        check_name = "Pensions"

        if df is None or len(df) == 0:
            self.warnings.append(f"{check_name}: No pensions to validate")
            return

        # Check mandatory fields
        required_fields = ['PensionCode', 'PensionTitle']
        missing_fields = [f for f in required_fields if f not in df.columns]

        if missing_fields:
            self.errors.append(f"{check_name}: Missing required fields: {', '.join(missing_fields)}")
        else:
            self.passed_checks.append(f"{check_name}: All required fields present")

        # Check for duplicate codes
        if 'PensionCode' in df.columns:
            duplicates = df[df.duplicated('PensionCode', keep=False)]
            if len(duplicates) > 0:
                self.errors.append(f"{check_name}: Duplicate pension codes found")
            else:
                self.passed_checks.append(f"{check_name}: No duplicate codes")

    def _validate_eqwp(self, df: Optional[pd.DataFrame]):
        """Validate Equated Week Patterns data."""
        check_name = "Equated Week Patterns"

        if df is None or len(df) == 0:
            self.warnings.append(f"{check_name}: No EQWP to validate")
            return

        # Check mandatory fields
        required_fields = ['EqwPatternCode', 'EqwPatternTitle', 'FullTimeWeeks']
        missing_fields = [f for f in required_fields if f not in df.columns]

        if missing_fields:
            self.errors.append(f"{check_name}: Missing required fields: {', '.join(missing_fields)}")
        else:
            self.passed_checks.append(f"{check_name}: All required fields present")

        # Check weeks are valid (1-52)
        if 'FullTimeWeeks' in df.columns:
            invalid_weeks = df[(df['FullTimeWeeks'] <= 0) | (df['FullTimeWeeks'] > 52)]
            if len(invalid_weeks) > 0:
                self.errors.append(f"{check_name}: {len(invalid_weeks)} patterns have invalid weeks (must be 1-52)")
            else:
                self.passed_checks.append(f"{check_name}: All weeks values valid")


def validate_s2_output(template_sheets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Convenience function to validate S2 template output.

    Args:
        template_sheets: Dict of sheet names to DataFrames

    Returns:
        Validation result dict with passed, errors, warnings, score
    """
    validator = S2Validator()
    return validator.validate_all(template_sheets)
