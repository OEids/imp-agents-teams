"""
S2 Knowledge Update Script
==========================
Extracts domain knowledge from S2 import files and generates
Python code ready to paste into S2_DOMAIN_KNOWLEDGE.py

Usage:
    python update_knowledge.py                    # Extract all
    python update_knowledge.py --pay-scales       # Extract pay scales only
    python update_knowledge.py --role-groups      # Extract role groups only
    python update_knowledge.py --output file.py   # Write to file instead of stdout
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import sys


class S2KnowledgeExtractor:
    """Extracts knowledge from S2 import files."""

    def __init__(self, import_folder: Path = None):
        if import_folder is None:
            import_folder = Path(__file__).parent / "import files"
        self.import_folder = import_folder

    def parse_combined(self, value) -> tuple:
        """Parse 'CODE: Title (extra)' format."""
        if pd.isna(value) or not value:
            return ('', '')
        value = str(value).strip()
        if ':' not in value:
            return (value, value)
        parts = value.split(':', 1)
        code = parts[0].strip()
        title = parts[1].strip()
        if '(' in title:
            title = title.split('(')[0].strip()
        return (code, title)

    def extract_pay_scales(self) -> dict:
        """Extract pay scales from import file."""
        file_path = self.import_folder / "DEM003 - Pay Scales_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)
        scales = {}

        for _, row in df.iterrows():
            code = row['Code']
            scales[code] = {
                'title': row['Title'],
                'increment_date': str(row['Increment Date']).split(' ')[0] if pd.notna(row['Increment Date']) else None,
                'increase_date': str(row['Increase Date']).split(' ')[0] if pd.notna(row['Increase Date']) else None,
                'increase_pct': row.get('Default Increase Percentage', 0),
                'available_all_schools': row.get('Available To All Schools', True),
                'exclude_ni': row.get('Exclude National Insurance', False),
                'exclude_pension': row.get('Exclude Pension', False),
                'teaching': any(t in code.upper() for t in ['TEACH', 'LEADERSHIP', 'UPS', 'UQ']),
            }

        return scales

    def extract_role_groups(self) -> dict:
        """Extract staff role groups with finance code mappings."""
        file_path = self.import_folder / "DEM003 - Staff Role Groups_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)
        groups = {}

        for _, row in df.iterrows():
            code = row['Code']

            # Extract finance codes from combined format
            gross_code, _ = self.parse_combined(row.get('Gross Salary Code', ''))
            leave_code, _ = self.parse_combined(row.get('Leave Rebate Code', ''))
            ni_code, _ = self.parse_combined(row.get('Employers NI Code', ''))
            pension_code, _ = self.parse_combined(row.get('Pension Code', ''))
            min_wage_code, _ = self.parse_combined(row.get('Minimum Wage Topup Code', ''))
            liv_wage_code, _ = self.parse_combined(row.get('Living Wage Topup Code', ''))
            opt_out_code, _ = self.parse_combined(row.get('Opt Out Pension Code', ''))
            other_code, _ = self.parse_combined(row.get('Other Salary Costs Code', ''))
            adj_code, _ = self.parse_combined(row.get('Adjustments Code', ''))
            allow_code, _ = self.parse_combined(row.get('Allowances Code', ''))

            groups[code] = {
                'title': row['Title'],
                'teaching': bool(row.get('Teaching Role Group', False)),
                'increment_count': row.get('Increment Count', 0),
                'finance_codes': {
                    'gross_salary': gross_code,
                    'leave_rebate': leave_code,
                    'employers_ni': ni_code,
                    'pension': pension_code,
                    'minimum_wage_topup': min_wage_code,
                    'living_wage_topup': liv_wage_code,
                    'opt_out_pension': opt_out_code,
                    'other_salary_costs': other_code,
                    'adjustments': adj_code,
                    'allowances': allow_code,
                },
            }

        return groups

    def extract_equated_weeks(self) -> dict:
        """Extract equated week patterns."""
        file_path = self.import_folder / "DEM003 - Equated Week Patterns_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)
        patterns = {}

        for _, row in df.iterrows():
            code = row['Code']
            patterns[code] = {
                'title': row['Title'],
                'full_time_weeks': row.get('Full Time Weeks', 52.14),
                'available_all_schools': row.get('Available To All Schools', True),
            }

        return patterns

    def extract_pensions(self) -> dict:
        """Extract pension schemes."""
        file_path = self.import_folder / "DEM003 - Pensions_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)
        pensions = {}

        for _, row in df.iterrows():
            code = row['Code']
            pensions[code] = {
                'title': row['Title'],
                'available_all_schools': row.get('Available To All Schools', True),
            }

        return pensions

    def extract_staff_roles(self) -> dict:
        """Extract staff roles."""
        file_path = self.import_folder / "DEM003 - Staff Roles_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)
        roles = {}

        for _, row in df.iterrows():
            code = row['Code']

            # Parse combined fields if present
            group_code, _ = self.parse_combined(row.get('Staff Role Group', ''))
            scale_code, _ = self.parse_combined(row.get('Pay Scale', ''))

            roles[code] = {
                'title': row['Title'],
                'role_group': group_code if group_code else None,
                'pay_scale': scale_code if scale_code else None,
                'full_time_hours': row.get('Full Time Hours Per Week', 32.5),
                'is_finance_role': row.get('Is Finance Role', False),
            }

        return roles

    def extract_allowance_types(self) -> dict:
        """Extract allowance types."""
        file_path = self.import_folder / "DEM003 - Allowance Types_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)
        allowances = {}

        for _, row in df.iterrows():
            code = row['Code']
            allowances[code] = {
                'title': row['Title'],
                'increase_date': str(row['Increase Date']).split(' ')[0] if pd.notna(row.get('Increase Date')) else None,
                'increase_pct': row.get('Default Increase Percentage', 0),
                'exclude_ni': row.get('Exclude National Insurance', False),
                'exclude_pension': row.get('Exclude Pension', False),
            }

        return allowances

    def extract_contracts_summary(self) -> dict:
        """Extract unique values from contracts for reference."""
        file_path = self.import_folder / "DEM003 - Contracts_ Master Scenario.xlsx"
        if not file_path.exists():
            print(f"Warning: {file_path} not found", file=sys.stderr)
            return {}

        df = pd.read_excel(file_path)

        # Extract unique values from combined columns
        summary = {
            'contract_types': set(),
            'funds': set(),
            'departments': set(),
            'schools': set(),
        }

        for _, row in df.iterrows():
            ct_code, ct_title = self.parse_combined(row.get('Contract Type Combined', ''))
            if ct_code:
                summary['contract_types'].add((ct_code, ct_title))

            fund_code, fund_title = self.parse_combined(row.get('Fund Combined', ''))
            if fund_code:
                summary['funds'].add((fund_code, fund_title))

            dept_code, dept_title = self.parse_combined(row.get('Department Combined', ''))
            if dept_code:
                summary['departments'].add((dept_code, dept_title))

            school = row.get('School Code', '')
            if school:
                summary['schools'].add(school)

        # Convert sets to sorted lists
        for key in summary:
            summary[key] = sorted(list(summary[key]))

        return summary


def format_dict_as_python(data: dict, name: str, indent: int = 0) -> str:
    """Format a dictionary as Python code."""
    lines = []
    base_indent = "    " * indent
    lines.append(f"{base_indent}{name} = {{")

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f'{base_indent}    "{key}": {{')
            for k, v in value.items():
                if isinstance(v, dict):
                    lines.append(f'{base_indent}        "{k}": {{')
                    for k2, v2 in v.items():
                        lines.append(f'{base_indent}            "{k2}": {repr(v2)},')
                    lines.append(f'{base_indent}        }},')
                elif isinstance(v, str):
                    lines.append(f'{base_indent}        "{k}": "{v}",')
                elif v is None:
                    lines.append(f'{base_indent}        "{k}": None,')
                else:
                    lines.append(f'{base_indent}        "{k}": {v},')
            lines.append(f"{base_indent}    }},")
        else:
            lines.append(f'{base_indent}    "{key}": {repr(value)},')

    lines.append(f"{base_indent}}}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract S2 domain knowledge from import files")
    parser.add_argument('--pay-scales', action='store_true', help="Extract pay scales only")
    parser.add_argument('--role-groups', action='store_true', help="Extract role groups only")
    parser.add_argument('--equated-weeks', action='store_true', help="Extract equated weeks only")
    parser.add_argument('--pensions', action='store_true', help="Extract pensions only")
    parser.add_argument('--staff-roles', action='store_true', help="Extract staff roles only")
    parser.add_argument('--allowances', action='store_true', help="Extract allowance types only")
    parser.add_argument('--contracts', action='store_true', help="Extract contracts summary only")
    parser.add_argument('--output', '-o', type=str, help="Output file (default: stdout)")
    parser.add_argument('--import-folder', type=str, help="Path to import files folder")
    args = parser.parse_args()

    # If no specific flag, extract all
    extract_all = not any([
        args.pay_scales, args.role_groups, args.equated_weeks,
        args.pensions, args.staff_roles, args.allowances, args.contracts
    ])

    import_folder = Path(args.import_folder) if args.import_folder else None
    extractor = S2KnowledgeExtractor(import_folder)

    output_lines = [
        '"""',
        f'S2 Domain Knowledge - Auto-extracted',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Source: {extractor.import_folder}',
        '"""',
        '',
    ]

    if extract_all or args.pay_scales:
        print("Extracting pay scales...", file=sys.stderr)
        pay_scales = extractor.extract_pay_scales()
        output_lines.append(f"# {len(pay_scales)} pay scales extracted")
        output_lines.append(format_dict_as_python(pay_scales, "PAY_SCALES"))
        output_lines.append("")

    if extract_all or args.role_groups:
        print("Extracting role groups...", file=sys.stderr)
        role_groups = extractor.extract_role_groups()
        output_lines.append(f"# {len(role_groups)} role groups extracted")
        output_lines.append(format_dict_as_python(role_groups, "STAFF_ROLE_GROUPS"))
        output_lines.append("")

    if extract_all or args.equated_weeks:
        print("Extracting equated week patterns...", file=sys.stderr)
        eqw = extractor.extract_equated_weeks()
        output_lines.append(f"# {len(eqw)} equated week patterns extracted")
        output_lines.append(format_dict_as_python(eqw, "EQUATED_WEEK_PATTERNS"))
        output_lines.append("")

    if extract_all or args.pensions:
        print("Extracting pensions...", file=sys.stderr)
        pensions = extractor.extract_pensions()
        output_lines.append(f"# {len(pensions)} pension schemes extracted")
        output_lines.append(format_dict_as_python(pensions, "PENSION_SCHEMES"))
        output_lines.append("")

    if extract_all or args.staff_roles:
        print("Extracting staff roles...", file=sys.stderr)
        roles = extractor.extract_staff_roles()
        output_lines.append(f"# {len(roles)} staff roles extracted")
        output_lines.append(format_dict_as_python(roles, "STAFF_ROLES"))
        output_lines.append("")

    if extract_all or args.allowances:
        print("Extracting allowance types...", file=sys.stderr)
        allowances = extractor.extract_allowance_types()
        output_lines.append(f"# {len(allowances)} allowance types extracted")
        output_lines.append(format_dict_as_python(allowances, "ALLOWANCE_TYPES"))
        output_lines.append("")

    if extract_all or args.contracts:
        print("Extracting contracts summary...", file=sys.stderr)
        summary = extractor.extract_contracts_summary()
        output_lines.append("# Contracts summary (unique values found)")
        output_lines.append(f"CONTRACT_TYPES_FOUND = {summary.get('contract_types', [])}")
        output_lines.append(f"FUNDS_FOUND = {summary.get('funds', [])}")
        output_lines.append(f"DEPARTMENTS_FOUND = {summary.get('departments', [])}")
        output_lines.append(f"SCHOOLS_FOUND = {summary.get('schools', [])}")
        output_lines.append("")

    output = "\n".join(output_lines)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)

    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    main()
