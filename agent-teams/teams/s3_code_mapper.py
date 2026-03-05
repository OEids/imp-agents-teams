"""
S3 Code Mapper - Maps customer codes to template codes

Step 3 in the workflow:
1. Upload template
2. Upload raw customer data
3. Map codes (this module) - school codes, finance codes, department codes
4. Run S3 specialist

This module analyzes customer data and proposes mappings to template codes,
allowing users to approve/modify before processing.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import re


@dataclass
class CodeMapping:
    """A proposed code mapping from customer to template."""
    customer_value: str
    customer_description: str  # Additional context from customer data
    proposed_template_code: str
    proposed_template_description: str
    confidence: float
    mapping_type: str  # 'school', 'finance', 'department'
    alternatives: List[Dict[str, str]]  # Other possible matches
    sample_rows: int  # How many rows use this code
    requires_review: bool


@dataclass
class CodeMappingResult:
    """Result of code mapping analysis."""
    school_mappings: List[CodeMapping]
    finance_mappings: List[CodeMapping]
    department_mappings: List[CodeMapping]
    unmapped_schools: List[str]
    unmapped_finance_codes: List[str]
    unmapped_departments: List[str]
    warnings: List[str]
    ready_for_processing: bool


class S3CodeMapper:
    """
    Maps customer codes to template codes.

    Workflow:
    1. Load template reference data (Schools, FinanceCodes, Depts)
    2. Analyze customer data to find unique codes
    3. Propose mappings using fuzzy matching
    4. Return proposals for user approval
    """

    def __init__(self):
        self.template_schools: Dict[str, Dict] = {}  # code -> {title, type, ...}
        self.template_finance_codes: Dict[str, Dict] = {}
        self.template_departments: Dict[str, Dict] = {}
        self.warnings: List[str] = []

    def load_template(self, template_path: Path) -> bool:
        """
        Load reference data from template.

        Args:
            template_path: Path to pre-populated template

        Returns:
            True if loaded successfully
        """
        try:
            xl = pd.ExcelFile(template_path)

            # Load Schools
            if 'Schools' in xl.sheet_names:
                df = pd.read_excel(xl, 'Schools')
                for _, row in df.iterrows():
                    code = str(row.get('SchoolCode', '')).strip()
                    if code and code.lower() != 'nan':
                        self.template_schools[code] = {
                            'title': str(row.get('Title', '')).strip(),
                            'type': str(row.get('SchoolType', '')).strip(),
                            'urn': str(row.get('UniqueReferenceNumber', '')).strip(),
                        }
                print(f"Loaded {len(self.template_schools)} schools from template")
            else:
                self.warnings.append("No 'Schools' sheet found in template")

            # Load Finance Codes
            for sheet_name in ['FinanceCodes Budget', '11_Finance Codes S3', 'FinanceCodes']:
                if sheet_name in xl.sheet_names:
                    df = pd.read_excel(xl, sheet_name)
                    for _, row in df.iterrows():
                        code = str(row.get('FinanceCode', '')).strip()
                        if code and code.lower() != 'nan':
                            self.template_finance_codes[code] = {
                                'title': str(row.get('Title', row.get('Description', ''))).strip(),
                                'type': str(row.get('FinanceCodeTypeCode', '')).strip(),
                                'grouping': str(row.get('GroupingCode', '')).strip(),
                            }
                    print(f"Loaded {len(self.template_finance_codes)} finance codes from {sheet_name}")
                    break
            else:
                self.warnings.append("No finance codes sheet found in template")

            # Load Departments
            if 'Depts' in xl.sheet_names:
                df = pd.read_excel(xl, 'Depts')
                for _, row in df.iterrows():
                    code = str(row.get('DepartmentCode', '')).strip()
                    if code and code.lower() != 'nan':
                        self.template_departments[code] = {
                            'title': str(row.get('Title', '')).strip(),
                        }
                print(f"Loaded {len(self.template_departments)} departments from template")

            return True

        except Exception as e:
            self.warnings.append(f"Error loading template: {str(e)}")
            return False

    def analyze_customer_data(
        self,
        customer_data_dir: Path,
        column_mappings: Dict[str, Dict[str, str]] = None
    ) -> CodeMappingResult:
        """
        Analyze customer data and propose code mappings.

        Args:
            customer_data_dir: Path to customer data files
            column_mappings: Approved column mappings from pre-flight validation

        Returns:
            CodeMappingResult with proposed mappings
        """
        # Collect unique codes from customer data
        customer_schools = {}  # value -> {description, count}
        customer_finance_codes = {}
        customer_departments = {}

        # Find all data files
        files = list(customer_data_dir.glob("*.xlsx")) + \
                list(customer_data_dir.glob("*.xls")) + \
                list(customer_data_dir.glob("*.csv"))
        files = [f for f in files if not f.name.startswith("~$")]

        for file_path in files:
            self._extract_codes_from_file(
                file_path,
                column_mappings or {},
                customer_schools,
                customer_finance_codes,
                customer_departments
            )

        # Generate mappings
        school_mappings = self._generate_school_mappings(customer_schools)
        finance_mappings = self._generate_finance_mappings(customer_finance_codes)
        department_mappings = self._generate_department_mappings(customer_departments)

        # Find unmapped codes
        unmapped_schools = [
            m.customer_value for m in school_mappings
            if m.confidence < 0.5 and not m.proposed_template_code
        ]
        unmapped_finance = [
            m.customer_value for m in finance_mappings
            if m.confidence < 0.5 and not m.proposed_template_code
        ]
        unmapped_depts = [
            m.customer_value for m in department_mappings
            if m.confidence < 0.5 and not m.proposed_template_code
        ]

        # Determine if ready for processing
        low_confidence = sum(1 for m in school_mappings + finance_mappings if m.requires_review)
        ready = low_confidence == 0 and len(unmapped_schools) == 0

        return CodeMappingResult(
            school_mappings=school_mappings,
            finance_mappings=finance_mappings,
            department_mappings=department_mappings,
            unmapped_schools=unmapped_schools,
            unmapped_finance_codes=unmapped_finance,
            unmapped_departments=unmapped_depts,
            warnings=self.warnings,
            ready_for_processing=ready
        )

    def _extract_codes_from_file(
        self,
        file_path: Path,
        column_mappings: Dict,
        customer_schools: Dict,
        customer_finance_codes: Dict,
        customer_departments: Dict
    ):
        """Extract unique codes from a file."""
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
            else:
                # Read first sheet or all sheets
                xl = pd.ExcelFile(file_path)
                for sheet in xl.sheet_names:
                    if any(skip in sheet.lower() for skip in ['guidance', 'notes', 'help']):
                        continue
                    df = pd.read_excel(xl, sheet)
                    self._extract_codes_from_df(
                        df, file_path.name, sheet,
                        column_mappings,
                        customer_schools, customer_finance_codes, customer_departments
                    )
                return

            self._extract_codes_from_df(
                df, file_path.name, 'CSV',
                column_mappings,
                customer_schools, customer_finance_codes, customer_departments
            )

        except Exception as e:
            self.warnings.append(f"Error reading {file_path.name}: {str(e)}")

    def _extract_codes_from_df(
        self,
        df: pd.DataFrame,
        file_name: str,
        sheet_name: str,
        column_mappings: Dict,
        customer_schools: Dict,
        customer_finance_codes: Dict,
        customer_departments: Dict
    ):
        """Extract codes from a DataFrame."""
        # Apply column mappings if available
        file_key = f"{file_name}:{sheet_name}"
        if file_key in column_mappings:
            df = df.rename(columns=column_mappings[file_key])
        elif file_name in column_mappings:
            df = df.rename(columns=column_mappings[file_name])

        # Normalize column names
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if any(x in col_lower for x in ['school', 'location', 'site', 'academy', 'cost centre']):
                col_map[col] = 'school_code'
            elif any(x in col_lower for x in ['finance', 'nominal', 'account', 'gl code', 'code']):
                col_map[col] = 'finance_code'
            elif any(x in col_lower for x in ['department', 'dept', 'cost center']):
                col_map[col] = 'department_code'
            elif any(x in col_lower for x in ['description', 'title', 'name']):
                col_map[col] = 'description'

        if col_map:
            df = df.rename(columns=col_map)

        # Extract school codes
        if 'school_code' in df.columns:
            for _, row in df.iterrows():
                val = str(row.get('school_code', '')).strip()
                if val and val.lower() not in ['nan', 'none', '']:
                    desc = str(row.get('description', '')).strip() if 'description' in df.columns else ''
                    if val not in customer_schools:
                        customer_schools[val] = {'description': desc, 'count': 0}
                    customer_schools[val]['count'] += 1

        # Extract finance codes
        if 'finance_code' in df.columns:
            for _, row in df.iterrows():
                val = str(row.get('finance_code', '')).strip()
                if val and val.lower() not in ['nan', 'none', '']:
                    desc = str(row.get('description', '')).strip() if 'description' in df.columns else ''
                    if val not in customer_finance_codes:
                        customer_finance_codes[val] = {'description': desc, 'count': 0}
                    customer_finance_codes[val]['count'] += 1

        # Extract department codes
        if 'department_code' in df.columns:
            for _, row in df.iterrows():
                val = str(row.get('department_code', '')).strip()
                if val and val.lower() not in ['nan', 'none', '']:
                    desc = str(row.get('description', '')).strip() if 'description' in df.columns else ''
                    if val not in customer_departments:
                        customer_departments[val] = {'description': desc, 'count': 0}
                    customer_departments[val]['count'] += 1

    def _generate_school_mappings(self, customer_schools: Dict) -> List[CodeMapping]:
        """Generate school code mappings."""
        mappings = []

        for cust_code, info in customer_schools.items():
            best_match = None
            best_score = 0
            alternatives = []

            # Try exact match first
            if cust_code in self.template_schools:
                best_match = cust_code
                best_score = 1.0
            else:
                # Fuzzy match against template school codes and titles
                for tmpl_code, tmpl_info in self.template_schools.items():
                    # Match against code
                    score1 = SequenceMatcher(None, cust_code.lower(), tmpl_code.lower()).ratio()
                    # Match against title
                    score2 = SequenceMatcher(None, cust_code.lower(), tmpl_info['title'].lower()).ratio()
                    # Match customer description against title
                    score3 = 0
                    if info['description']:
                        score3 = SequenceMatcher(None, info['description'].lower(), tmpl_info['title'].lower()).ratio()

                    score = max(score1, score2, score3)

                    if score > 0.5:
                        alternatives.append({
                            'code': tmpl_code,
                            'title': tmpl_info['title'],
                            'score': score
                        })

                    if score > best_score:
                        best_score = score
                        best_match = tmpl_code

            # Sort alternatives by score
            alternatives.sort(key=lambda x: x['score'], reverse=True)

            mapping = CodeMapping(
                customer_value=cust_code,
                customer_description=info['description'],
                proposed_template_code=best_match or '',
                proposed_template_description=self.template_schools.get(best_match, {}).get('title', '') if best_match else '',
                confidence=best_score,
                mapping_type='school',
                alternatives=alternatives[:5],
                sample_rows=info['count'],
                requires_review=best_score < 0.8
            )
            mappings.append(mapping)

        return mappings

    def _generate_finance_mappings(self, customer_finance_codes: Dict) -> List[CodeMapping]:
        """Generate finance code mappings."""
        mappings = []

        for cust_code, info in customer_finance_codes.items():
            best_match = None
            best_score = 0
            alternatives = []

            # Try exact match first
            if cust_code in self.template_finance_codes:
                best_match = cust_code
                best_score = 1.0
            else:
                # Fuzzy match
                for tmpl_code, tmpl_info in self.template_finance_codes.items():
                    # Match against code
                    score1 = SequenceMatcher(None, cust_code.lower(), tmpl_code.lower()).ratio()
                    # Match against title/description
                    score2 = 0
                    if info['description'] and tmpl_info['title']:
                        score2 = SequenceMatcher(None, info['description'].lower(), tmpl_info['title'].lower()).ratio()

                    score = max(score1, score2)

                    if score > 0.4:
                        alternatives.append({
                            'code': tmpl_code,
                            'title': tmpl_info['title'],
                            'score': score
                        })

                    if score > best_score:
                        best_score = score
                        best_match = tmpl_code

            alternatives.sort(key=lambda x: x['score'], reverse=True)

            mapping = CodeMapping(
                customer_value=cust_code,
                customer_description=info['description'],
                proposed_template_code=best_match or '',
                proposed_template_description=self.template_finance_codes.get(best_match, {}).get('title', '') if best_match else '',
                confidence=best_score,
                mapping_type='finance',
                alternatives=alternatives[:5],
                sample_rows=info['count'],
                requires_review=best_score < 0.8
            )
            mappings.append(mapping)

        return mappings

    def _generate_department_mappings(self, customer_departments: Dict) -> List[CodeMapping]:
        """Generate department code mappings."""
        mappings = []

        for cust_code, info in customer_departments.items():
            best_match = None
            best_score = 0
            alternatives = []

            if cust_code in self.template_departments:
                best_match = cust_code
                best_score = 1.0
            else:
                for tmpl_code, tmpl_info in self.template_departments.items():
                    score1 = SequenceMatcher(None, cust_code.lower(), tmpl_code.lower()).ratio()
                    score2 = 0
                    if info['description'] and tmpl_info['title']:
                        score2 = SequenceMatcher(None, info['description'].lower(), tmpl_info['title'].lower()).ratio()

                    score = max(score1, score2)

                    if score > 0.4:
                        alternatives.append({
                            'code': tmpl_code,
                            'title': tmpl_info['title'],
                            'score': score
                        })

                    if score > best_score:
                        best_score = score
                        best_match = tmpl_code

            alternatives.sort(key=lambda x: x['score'], reverse=True)

            mapping = CodeMapping(
                customer_value=cust_code,
                customer_description=info['description'],
                proposed_template_code=best_match or '',
                proposed_template_description=self.template_departments.get(best_match, {}).get('title', '') if best_match else '',
                confidence=best_score,
                mapping_type='department',
                alternatives=alternatives[:5],
                sample_rows=info['count'],
                requires_review=best_score < 0.8
            )
            mappings.append(mapping)

        return mappings

    def apply_approved_mappings(
        self,
        approved_mappings: List[Dict]
    ) -> Dict[str, Dict[str, str]]:
        """
        Convert approved code mappings to format for S3 specialist.

        Args:
            approved_mappings: List of approved mappings, each with:
                - customer_value: Original customer code
                - approved_code: User-approved template code
                - mapping_type: 'school', 'finance', or 'department'

        Returns:
            Dict with:
            - school_mappings: {customer_code: template_code}
            - finance_mappings: {customer_code: template_code}
            - department_mappings: {customer_code: template_code}
        """
        result = {
            'school_mappings': {},
            'finance_mappings': {},
            'department_mappings': {}
        }

        for mapping in approved_mappings:
            cust = mapping.get('customer_value', '')
            approved = mapping.get('approved_code', '')
            mtype = mapping.get('mapping_type', '')

            if not cust or not approved:
                continue

            if mtype == 'school':
                result['school_mappings'][cust] = approved
            elif mtype == 'finance':
                result['finance_mappings'][cust] = approved
            elif mtype == 'department':
                result['department_mappings'][cust] = approved

        return result


def run_code_mapping(
    template_path: Path,
    customer_data_dir: Path,
    column_mappings: Dict = None
) -> CodeMappingResult:
    """
    Run code mapping analysis.

    Args:
        template_path: Path to pre-populated template
        customer_data_dir: Path to customer data files
        column_mappings: Approved column mappings (optional)

    Returns:
        CodeMappingResult with proposed mappings for user review
    """
    mapper = S3CodeMapper()
    mapper.load_template(template_path)
    return mapper.analyze_customer_data(customer_data_dir, column_mappings)
