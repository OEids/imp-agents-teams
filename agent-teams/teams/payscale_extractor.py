"""
Payscale Extractor Expert
=========================

An expert module for extracting pay scales, allowances, and related data from
various Excel formats commonly used in UK education sector.

Supported Formats:
-----------------
1. Simple two-column format (Point, Value)
2. Multi-year grid format with SCP points
3. NJC grading structure with bands
4. Section-based format (Main Scale, Upper, Leadership, TLR, SEN sections)
5. TMPS/UPS naming convention
6. Lead Practitioner scales
7. Allowance lists (TLR, SEN, Mileage, etc.)

Point Code Patterns:
-------------------
- Teaching Main: M1-M6, TMPS1-TMPS6, MPS1-MPS6
- Teaching Upper: U1-U3, UPS1-UPS3
- Leadership: L1-L50, L01-L50, LD1-LD50
- Support/NJC: SCP1-SCP43, numeric 1-43
- Lead Practitioner: LP1-LP16, numeric under LP section
- Unqualified Teacher: UQT1-UQT6

Allowance Patterns:
------------------
- TLR: TLR1, TLR2, TLR3, TLR1A, TLR1B, TLR1C, TLR2A, TLR2B, TLR2C
- SEN: SEN1, SEN2
- Other: Mileage, Telephone, London Weighting
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PayScalePoint:
    """A single pay scale point with rate."""
    code: str           # Normalized code (M1, U1, L01, 1, etc.)
    title: str          # Display title
    number: int         # Numeric order
    rate: float         # Annual salary rate
    date_from: str      # Effective date
    original_code: str = ""  # Original code from source


@dataclass
class PayScale:
    """A complete pay scale with all points."""
    code: str           # Scale code (MAIN, LS, MAT_SUP, LP, UQT)
    title: str          # Scale title
    scale_type: str     # teaching, leadership, support, lead_practitioner, unqualified
    points: List[PayScalePoint]
    grades: List[Dict] = field(default_factory=list)  # Grade ranges
    increment_date: str = ""
    increase_date: str = ""
    london_weighting: str = "England & Wales"


@dataclass
class AllowancePoint:
    """A single allowance point."""
    code: str           # TLR1A, SEN1, etc.
    title: str          # Display title
    amount: float       # Annual amount
    original_code: str = ""


@dataclass
class AllowanceType:
    """An allowance type with all points."""
    code: str           # TLR, SEN, etc.
    title: str          # Full title
    points: List[AllowancePoint]
    increase_date: str = "2025-09-01"


class PayScaleExtractor:
    """
    Expert extractor for pay scales and allowances from various Excel formats.
    """

    def __init__(self):
        self.pay_scales: List[PayScale] = []
        self.allowances: List[AllowanceType] = []
        self.grades: List[Dict] = []
        self.log_messages: List[str] = []

        # Track what's been found to avoid duplicates
        self.scales_found: Set[str] = set()
        self.allowances_found: Set[str] = set()

    def log(self, message: str):
        """Log a message."""
        self.log_messages.append(message)
        print(f"[PayScaleExtractor] {message}")

    def extract_from_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract all pay scales and allowances from an Excel file.

        Returns dict with 'pay_scales', 'allowances', 'grades'
        """
        self.log(f"Processing file: {file_path.name}")

        try:
            xl = pd.ExcelFile(file_path)

            for sheet_name in xl.sheet_names:
                # Skip guidance/help sheets
                if sheet_name.lower() in ['guidance', 'notes', 'instructions', 'help', 'info']:
                    continue

                self.log(f"  Analyzing sheet: {sheet_name}")
                df = pd.read_excel(xl, sheet_name, header=None)

                if df.empty or len(df) < 2:
                    continue

                # Detect and extract based on sheet content
                self._extract_from_sheet(df, sheet_name)

        except Exception as e:
            self.log(f"Error processing file: {e}")

        return {
            'pay_scales': self.pay_scales,
            'allowances': self.allowances,
            'grades': self.grades,
        }

    def extract_from_dataframe(self, df: pd.DataFrame, sheet_name: str = "Unknown") -> Dict[str, Any]:
        """Extract from a dataframe directly."""
        self._extract_from_sheet(df, sheet_name)
        return {
            'pay_scales': self.pay_scales,
            'allowances': self.allowances,
            'grades': self.grades,
        }

    def _extract_from_sheet(self, df: pd.DataFrame, sheet_name: str):
        """Analyze and extract from a single sheet."""
        sheet_lower = sheet_name.lower()

        # Detect sheet type and extract accordingly
        if self._is_simple_point_value_format(df):
            self._extract_simple_format(df, sheet_name)
        elif self._is_section_based_format(df):
            self._extract_section_format(df, sheet_name)
        elif self._is_njc_grid_format(df):
            self._extract_njc_grid_format(df, sheet_name)
        elif self._is_multi_year_grid_format(df):
            self._extract_multi_year_format(df, sheet_name)
        elif self._is_allowance_list_format(df):
            self._extract_allowance_list_format(df, sheet_name)
        elif self._is_tlr_employee_format(df):
            self._extract_tlr_employee_format(df, sheet_name)
        else:
            # Try generic extraction
            self._extract_generic(df, sheet_name)

    # =========================================================================
    # FORMAT DETECTION
    # =========================================================================

    def _is_simple_point_value_format(self, df: pd.DataFrame) -> bool:
        """Check if this is a simple 2-3 column format with point codes and values."""
        if df.shape[1] < 2 or df.shape[1] > 6:
            return False

        # Look for point codes in first few columns
        for col_idx in range(min(4, df.shape[1])):
            col_vals = df.iloc[:, col_idx].dropna().astype(str).tolist()
            # Extended pattern to catch more formats
            point_pattern = r'^(M[1-6]|U[1-3]|L\d+|UQT\s*\d|TLR|SEN|LP?\d+|\d+[ABC]?|TMPS\s*\d|UPS\s*\d)$'
            matches = sum(1 for v in col_vals if re.match(point_pattern, v.strip(), re.IGNORECASE))
            if matches >= 3:
                return True
        return False

    def _is_section_based_format(self, df: pd.DataFrame) -> bool:
        """Check if this has section headers like 'Main Scale', 'Upper', 'Leadership'."""
        text = ' '.join(df.iloc[:, :3].fillna('').astype(str).values.flatten()).lower()
        section_keywords = ['main scale', 'upper pay', 'leadership', 'tlr', 'sen allowance',
                          'lead practitioner', 'unqualified']
        return sum(1 for kw in section_keywords if kw in text) >= 2

    def _is_njc_grid_format(self, df: pd.DataFrame) -> bool:
        """Check if this is NJC grading format with Grade/Scale/Band columns."""
        text = ' '.join(df.iloc[:10, :].fillna('').astype(str).values.flatten()).lower()
        njc_keywords = ['njc', 'spine', 'grade', 'scale', 'band', 'scp']
        return sum(1 for kw in njc_keywords if kw in text) >= 3

    def _is_multi_year_grid_format(self, df: pd.DataFrame) -> bool:
        """Check if this has multiple year columns with rates."""
        # Look for year patterns in header rows
        for row_idx in range(min(5, len(df))):
            row_text = ' '.join(df.iloc[row_idx, :].fillna('').astype(str).tolist()).lower()
            year_pattern = r'(202[0-9]|apr|sep|april|september)'
            if len(re.findall(year_pattern, row_text)) >= 2:
                return True
        return False

    def _is_allowance_list_format(self, df: pd.DataFrame) -> bool:
        """Check if this is an allowance list with Type/Value columns."""
        header_text = ' '.join(df.iloc[:3, :].fillna('').astype(str).values.flatten()).lower()
        return 'type' in header_text and ('value' in header_text or 'amount' in header_text)

    def _is_tlr_employee_format(self, df: pd.DataFrame) -> bool:
        """Check if this is employee-level TLR data."""
        header_text = ' '.join(df.iloc[:2, :].fillna('').astype(str).values.flatten()).lower()
        return 'emp' in header_text and 'tlr' in header_text

    # =========================================================================
    # EXTRACTION METHODS
    # =========================================================================

    def _extract_simple_format(self, df: pd.DataFrame, sheet_name: str):
        """Extract from simple point-value format."""
        self.log(f"    Extracting simple format from {sheet_name}")

        # Find point column and value column
        point_col = None
        value_col = None

        # Extended pattern for point codes
        point_pattern = r'^(M[1-6]|U[1-3]|L\d+|UQT\s*\d*|TLR|SEN|LP?\d+|\d+[ABC]?|TMPS\s*\d|UPS\s*\d)$'

        for col_idx in range(min(4, df.shape[1])):
            col_vals = df.iloc[:, col_idx].dropna().astype(str).tolist()
            matches = sum(1 for v in col_vals if re.match(point_pattern, v.strip(), re.IGNORECASE))
            if matches >= 3:
                point_col = col_idx
                break

        # Value column is usually right after point column or last numeric column
        if point_col is not None:
            for col_idx in range(point_col + 1, df.shape[1]):
                col_vals = df.iloc[:, col_idx].dropna()
                numeric_count = sum(1 for v in col_vals if self._is_salary_value(v))
                if numeric_count >= 3:
                    value_col = col_idx
                    break

        if point_col is None or value_col is None:
            # Try alternative: look for any column with salary values
            for col_idx in range(df.shape[1] - 1, -1, -1):
                col_vals = df.iloc[:, col_idx].dropna()
                numeric_count = sum(1 for v in col_vals if self._is_salary_value(v))
                if numeric_count >= 3:
                    value_col = col_idx
                    # Point column is the one before with strings
                    for pc in range(col_idx - 1, -1, -1):
                        pc_vals = df.iloc[:, pc].dropna().astype(str).tolist()
                        if any(re.match(point_pattern, v.strip(), re.IGNORECASE) for v in pc_vals):
                            point_col = pc
                            break
                    break

        if point_col is None or value_col is None:
            return

        # Extract points grouped by scale type
        current_section = None
        teaching_main = []
        teaching_upper = []
        leadership = []
        lead_practitioner = []
        unqualified = []
        support = []
        tlr_points = []
        sen_points = []

        for idx, row in df.iterrows():
            point_val = row.iloc[point_col]
            rate_val = row.iloc[value_col]

            # Check for section header
            row_text = ' '.join(row.fillna('').astype(str).tolist()).lower()
            if 'main scale' in row_text or 'main pay' in row_text:
                current_section = 'main'
                continue
            elif 'upper' in row_text and 'pay' in row_text:
                current_section = 'upper'
                continue
            elif 'leadership' in row_text:
                current_section = 'leadership'
                continue
            elif 'lead practitioner' in row_text:
                current_section = 'lead_practitioner'
                continue
            elif 'unqualified' in row_text or 'uqt' in row_text:
                current_section = 'unqualified'
                continue
            elif 'tlr' in row_text and not pd.notna(rate_val):
                current_section = 'tlr'
                continue
            elif 'sen' in row_text and 'pension' not in row_text and not pd.notna(rate_val):
                current_section = 'sen'
                continue

            if not pd.notna(point_val) or not pd.notna(rate_val):
                continue

            point_str = str(point_val).strip()
            rate = self._parse_rate(rate_val)

            if rate is None or rate <= 0:
                continue

            # Categorize the point
            point_lower = point_str.lower()

            if current_section == 'tlr' or point_lower.startswith('tlr') or re.match(r'^\d[abc]$', point_lower, re.IGNORECASE):
                code = self._normalize_tlr_code(point_str)
                tlr_points.append(AllowancePoint(code=code, title=code, amount=rate, original_code=point_str))
            elif current_section == 'sen' or point_lower.startswith('sen'):
                code = self._normalize_sen_code(point_str)
                sen_points.append(AllowancePoint(code=code, title=code, amount=rate, original_code=point_str))
            elif point_lower.startswith('m') or point_lower.startswith('tmps') or point_lower.startswith('mps') or current_section == 'main':
                code = self._normalize_main_point(point_str)
                num = self._extract_point_number(point_str)
                teaching_main.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_lower.startswith('u') or point_lower.startswith('ups') or current_section == 'upper':
                code = self._normalize_upper_point(point_str)
                num = self._extract_point_number(point_str)
                teaching_upper.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_lower.startswith('l') or point_lower.startswith('ld') or current_section == 'leadership':
                code = self._normalize_leadership_point(point_str)
                num = self._extract_point_number(point_str)
                leadership.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif current_section == 'lead_practitioner':
                num = self._extract_point_number(point_str)
                code = f"LP{num}"
                lead_practitioner.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif current_section == 'unqualified' or point_lower.startswith('uqt'):
                code = self._normalize_uqt_point(point_str)
                num = self._extract_point_number(point_str)
                unqualified.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_str.isdigit():
                # Pure numeric - likely support scale
                num = int(point_str)
                support.append(PayScalePoint(code=str(num), title=f"Point {num}", number=num, rate=rate, date_from='2025-04-01', original_code=point_str))

        # Create pay scales
        self._add_pay_scale('MAIN', 'Teachers Main Pay Scale', 'teaching', teaching_main + teaching_upper)
        self._add_pay_scale('LS', 'Leadership Pay Scale', 'leadership', leadership)
        self._add_pay_scale('LP', 'Lead Practitioner', 'lead_practitioner', lead_practitioner)
        self._add_pay_scale('UQT', 'Unqualified Teacher Scale', 'unqualified', unqualified)
        self._add_pay_scale('MAT_SUP', 'MAT Support Scale', 'support', support)

        # Create allowances
        self._add_allowance('TLR', 'Teaching and Learning Responsibility', tlr_points)
        self._add_allowance('SEN', 'Special Educational Needs', sen_points)

    def _extract_section_format(self, df: pd.DataFrame, sheet_name: str):
        """Extract from section-based format with headers."""
        self.log(f"    Extracting section-based format from {sheet_name}")
        # This uses similar logic to simple format but more section-aware
        self._extract_simple_format(df, sheet_name)

    def _extract_njc_grid_format(self, df: pd.DataFrame, sheet_name: str):
        """Extract from NJC grid format with grades and bands."""
        self.log(f"    Extracting NJC grid format from {sheet_name}")

        # Find header row
        header_row = self._find_header_row(df, ['spine', 'point', 'scp', 'annual', 'salary'])
        if header_row is None:
            header_row = 0

        # Find columns
        point_col = None
        salary_col = None
        grade_col = None
        band_col = None

        headers = df.iloc[header_row].fillna('').astype(str).tolist()
        for idx, h in enumerate(headers):
            h_lower = h.lower()
            if 'point' in h_lower or 'scp' in h_lower or 'spine' in h_lower:
                point_col = idx
            elif 'salary' in h_lower or 'annual' in h_lower:
                salary_col = idx
            elif 'grade' in h_lower and grade_col is None:
                grade_col = idx
            elif 'band' in h_lower:
                band_col = idx

        # Also check for date columns
        date_cols = []
        for idx, h in enumerate(headers):
            if re.search(r'202[0-9]|apr|april', str(h).lower()):
                date_cols.append(idx)

        if salary_col is None and date_cols:
            # Use most recent date column as salary
            salary_col = date_cols[-1]

        if point_col is None or salary_col is None:
            return

        # Extract points
        support_points = []
        grades_map = {}  # grade_name -> {from_point, to_point}
        current_grade = None

        for idx in range(header_row + 1, len(df)):
            row = df.iloc[idx]
            point_val = row.iloc[point_col]
            salary_val = row.iloc[salary_col]

            # Track grade
            if grade_col is not None:
                grade_val = row.iloc[grade_col]
                if pd.notna(grade_val) and str(grade_val).strip():
                    current_grade = str(grade_val).strip()

            if not pd.notna(point_val):
                continue

            point_str = str(point_val).strip()

            # Clean point number (remove asterisks, etc.)
            point_num_match = re.search(r'\d+', point_str)
            if not point_num_match:
                continue
            point_num = int(point_num_match.group())

            rate = self._parse_rate(salary_val)
            if rate is None or rate <= 0:
                continue

            support_points.append(PayScalePoint(
                code=str(point_num),
                title=f"Point {point_num}",
                number=point_num,
                rate=rate,
                date_from='2025-04-01',
                original_code=point_str
            ))

            # Track grades
            if current_grade:
                if current_grade not in grades_map:
                    grades_map[current_grade] = {'from': point_num, 'to': point_num}
                else:
                    grades_map[current_grade]['to'] = point_num

        # Create support pay scale
        self._add_pay_scale('MAT_SUP', 'MAT Support Scale (NJC)', 'support', support_points)

        # Create grades
        for grade_name, range_info in grades_map.items():
            self.grades.append({
                'code': grade_name.replace(' ', '_').upper(),
                'title': grade_name,
                'pay_scale_code': 'MAT_SUP',
                'from_point': range_info['from'],
                'to_point': range_info['to'],
            })

    def _extract_multi_year_format(self, df: pd.DataFrame, sheet_name: str):
        """Extract from multi-year grid format."""
        self.log(f"    Extracting multi-year format from {sheet_name}")

        # Find the year columns and use most recent
        year_cols = []
        header_row = None

        for row_idx in range(min(10, len(df))):
            row = df.iloc[row_idx]
            for col_idx, val in enumerate(row):
                val_str = str(val).lower() if pd.notna(val) else ''
                # Look for 2025, 2024, or date patterns
                if re.search(r'202[5-9]|2025|2024', val_str):
                    year_cols.append((col_idx, val_str))
                    if header_row is None:
                        header_row = row_idx

        if not year_cols or header_row is None:
            # Try generic extraction
            self._extract_generic(df, sheet_name)
            return

        # Use most recent year column (prefer 2025)
        best_col = max(year_cols, key=lambda x: ('2025' in x[1], '2024' in x[1], x[0]))[0]

        # Find point code column
        point_col = 0  # Usually first column

        # Detect scale type from sheet name
        sheet_lower = sheet_name.lower()

        teaching_main = []
        teaching_upper = []
        leadership = []
        support = []
        lead_practitioner = []
        unqualified = []

        current_section = None

        for idx in range(header_row + 1, len(df)):
            row = df.iloc[idx]

            # Check for section markers
            row_text = ' '.join(row.fillna('').astype(str).tolist()).lower()
            if 'teacher scales' in row_text or 'main' in row_text:
                current_section = 'main'
                continue
            elif 'upper' in row_text:
                current_section = 'upper'
                continue
            elif 'leadership' in row_text:
                current_section = 'leadership'
                continue
            elif 'lead practitioner' in row_text:
                current_section = 'lead_practitioner'
                continue
            elif 'unqualified' in row_text:
                current_section = 'unqualified'
                continue
            elif 'njc' in row_text or 'support' in row_text:
                current_section = 'support'
                continue

            point_val = row.iloc[point_col]
            rate_val = row.iloc[best_col]

            if not pd.notna(point_val):
                continue

            point_str = str(point_val).strip()
            rate = self._parse_rate(rate_val)

            if rate is None or rate <= 0:
                continue

            point_lower = point_str.lower()

            # Categorize
            if point_lower.startswith('tmps') or point_lower.startswith('mps') or point_lower.startswith('m'):
                code = self._normalize_main_point(point_str)
                num = self._extract_point_number(point_str)
                teaching_main.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_lower.startswith('ups') or point_lower.startswith('u'):
                code = self._normalize_upper_point(point_str)
                num = self._extract_point_number(point_str)
                teaching_upper.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_lower.startswith('l') and not point_lower.startswith('lead'):
                code = self._normalize_leadership_point(point_str)
                num = self._extract_point_number(point_str)
                leadership.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_lower.startswith('uqt') or current_section == 'unqualified':
                code = self._normalize_uqt_point(point_str)
                num = self._extract_point_number(point_str)
                unqualified.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_str.isdigit() and current_section == 'lead_practitioner':
                num = int(point_str)
                lead_practitioner.append(PayScalePoint(code=f"LP{num}", title=f"LP{num}", number=num, rate=rate, date_from='2025-09-01', original_code=point_str))
            elif point_str.isdigit():
                num = int(point_str)
                support.append(PayScalePoint(code=str(num), title=f"Point {num}", number=num, rate=rate, date_from='2025-04-01', original_code=point_str))

        # Create scales
        self._add_pay_scale('MAIN', 'Teachers Main Pay Scale', 'teaching', teaching_main + teaching_upper)
        self._add_pay_scale('LS', 'Leadership Pay Scale', 'leadership', leadership)
        self._add_pay_scale('LP', 'Lead Practitioner', 'lead_practitioner', lead_practitioner)
        self._add_pay_scale('UQT', 'Unqualified Teacher Scale', 'unqualified', unqualified)
        self._add_pay_scale('MAT_SUP', 'MAT Support Scale', 'support', support)

    def _extract_allowance_list_format(self, df: pd.DataFrame, sheet_name: str):
        """Extract from allowance list format (Type, Value, Notes)."""
        self.log(f"    Extracting allowance list format from {sheet_name}")

        # Find header row
        header_row = self._find_header_row(df, ['type', 'value', 'amount'])
        if header_row is None:
            header_row = 0

        headers = df.iloc[header_row].fillna('').astype(str).str.lower().tolist()

        type_col = None
        value_col = None

        for idx, h in enumerate(headers):
            if 'type' in h or 'name' in h or 'description' in h:
                type_col = idx
            elif 'value' in h or 'amount' in h or 'annual' in h:
                value_col = idx

        if type_col is None or value_col is None:
            return

        # Group by allowance type
        allowances_map = {}  # type_code -> list of amounts

        for idx in range(header_row + 1, len(df)):
            row = df.iloc[idx]
            type_val = row.iloc[type_col]
            amount_val = row.iloc[value_col]

            if not pd.notna(type_val) or not pd.notna(amount_val):
                continue

            type_str = str(type_val).strip().upper()
            amount = self._parse_rate(amount_val)

            if amount is None or amount <= 0:
                continue

            # Categorize
            if 'TLR' in type_str:
                type_code = 'TLR'
            elif 'SEN' in type_str and 'PENSION' not in type_str:
                type_code = 'SEN'
            elif 'MILEAGE' in type_str:
                type_code = 'MILEAGE'
            elif 'TELEPHONE' in type_str:
                type_code = 'TELEPHONE'
            elif 'LONDON' in type_str:
                type_code = 'LONDON'
            else:
                type_code = 'OTHER'

            if type_code not in allowances_map:
                allowances_map[type_code] = set()
            allowances_map[type_code].add(amount)

        # Create allowance types
        type_titles = {
            'TLR': 'Teaching and Learning Responsibility',
            'SEN': 'Special Educational Needs',
            'MILEAGE': 'Mileage Allowance',
            'TELEPHONE': 'Telephone Allowance',
            'LONDON': 'London Weighting',
            'OTHER': 'Other Allowance',
        }

        for type_code, amounts in allowances_map.items():
            points = []
            for idx, amount in enumerate(sorted(amounts, reverse=True), 1):
                points.append(AllowancePoint(
                    code=f"{type_code}{idx}",
                    title=f"{type_titles.get(type_code, type_code)} {idx}",
                    amount=amount
                ))
            self._add_allowance(type_code, type_titles.get(type_code, type_code), points)

    def _extract_tlr_employee_format(self, df: pd.DataFrame, sheet_name: str):
        """Extract TLR values from employee-level data."""
        self.log(f"    Extracting TLR employee format from {sheet_name}")

        # Find TLR and Annual columns
        header_row = 0
        headers = df.iloc[0].fillna('').astype(str).str.lower().tolist()

        tlr_col = None
        annual_col = None

        for idx, h in enumerate(headers):
            if 'tlr' in h and tlr_col is None:
                tlr_col = idx
            elif 'annual' in h:
                annual_col = idx

        if annual_col is None:
            # Try to find any numeric column
            for idx, h in enumerate(headers):
                if idx != tlr_col:
                    col_vals = df.iloc[1:, idx].dropna()
                    if len(col_vals) > 0 and all(self._is_salary_value(v) for v in col_vals.head(3)):
                        annual_col = idx
                        break

        if annual_col is None:
            return

        # Collect unique TLR amounts
        tlr_amounts = set()

        for idx in range(1, len(df)):
            amount_val = df.iloc[idx, annual_col]
            if pd.notna(amount_val):
                amount = self._parse_rate(amount_val)
                if amount and amount > 0:
                    tlr_amounts.add(amount)

        if tlr_amounts:
            points = []
            for idx, amount in enumerate(sorted(tlr_amounts, reverse=True), 1):
                points.append(AllowancePoint(
                    code=f"TLR{idx}",
                    title=f"TLR {idx}",
                    amount=amount
                ))
            self._add_allowance('TLR', 'Teaching and Learning Responsibility', points)

    def _extract_generic(self, df: pd.DataFrame, sheet_name: str):
        """Generic extraction when format isn't clearly identified."""
        self.log(f"    Attempting generic extraction from {sheet_name}")

        # Look for any point-like values and associated rates
        teaching_points = []
        support_points = []
        leadership_points = []

        for row_idx, row in df.iterrows():
            for col_idx, val in enumerate(row[:-1]):  # Skip last column
                if not pd.notna(val):
                    continue

                val_str = str(val).strip()

                # Check if this looks like a point code
                point_match = re.match(r'^(M|U|L|TMPS|UPS|MPS|LP|UQT)?\s*(\d+)([ABC])?$', val_str, re.IGNORECASE)
                if point_match:
                    # Look for rate in next column
                    rate_val = row.iloc[col_idx + 1] if col_idx + 1 < len(row) else None
                    rate = self._parse_rate(rate_val)

                    if rate and rate > 1000:
                        prefix = (point_match.group(1) or '').upper()
                        num = int(point_match.group(2))
                        suffix = (point_match.group(3) or '').upper()

                        if prefix in ['M', 'TMPS', 'MPS'] or (not prefix and num <= 6):
                            code = f"M{num}"
                            teaching_points.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=val_str))
                        elif prefix in ['U', 'UPS']:
                            code = f"U{num}"
                            teaching_points.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=val_str))
                        elif prefix == 'L' or (not prefix and num > 6 and num <= 50):
                            code = f"L{num:02d}"
                            leadership_points.append(PayScalePoint(code=code, title=code, number=num, rate=rate, date_from='2025-09-01', original_code=val_str))
                        elif not prefix:
                            support_points.append(PayScalePoint(code=str(num), title=f"Point {num}", number=num, rate=rate, date_from='2025-04-01', original_code=val_str))

        self._add_pay_scale('MAIN', 'Teachers Main Pay Scale', 'teaching', teaching_points)
        self._add_pay_scale('LS', 'Leadership Pay Scale', 'leadership', leadership_points)
        self._add_pay_scale('MAT_SUP', 'MAT Support Scale', 'support', support_points)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _add_pay_scale(self, code: str, title: str, scale_type: str, points: List[PayScalePoint]):
        """Add a pay scale if it has points and isn't duplicate."""
        if not points or code in self.scales_found:
            return

        # Deduplicate points by code
        seen = set()
        unique_points = []
        for p in sorted(points, key=lambda x: x.number):
            if p.code not in seen:
                seen.add(p.code)
                unique_points.append(p)

        if not unique_points:
            return

        self.pay_scales.append(PayScale(
            code=code,
            title=title,
            scale_type=scale_type,
            points=unique_points,
            increment_date='2025-09-01' if scale_type != 'support' else '2025-04-01',
            increase_date='2025-09-01' if scale_type != 'support' else '2025-04-01',
        ))
        self.scales_found.add(code)
        self.log(f"      Added {code} scale with {len(unique_points)} points")

    def _add_allowance(self, code: str, title: str, points: List[AllowancePoint]):
        """Add an allowance type if it has points and isn't duplicate."""
        if not points or code in self.allowances_found:
            return

        # Deduplicate by amount
        seen = set()
        unique_points = []
        for p in sorted(points, key=lambda x: -x.amount):
            if p.amount not in seen:
                seen.add(p.amount)
                unique_points.append(p)

        # Renumber
        for idx, p in enumerate(unique_points, 1):
            p.code = f"{code}{idx}"
            p.title = f"{title} {idx}"

        if not unique_points:
            return

        self.allowances.append(AllowanceType(
            code=code,
            title=title,
            points=unique_points,
        ))
        self.allowances_found.add(code)
        self.log(f"      Added {code} allowance with {len(unique_points)} points")

    def _find_header_row(self, df: pd.DataFrame, keywords: List[str]) -> Optional[int]:
        """Find the header row containing keywords."""
        for row_idx in range(min(10, len(df))):
            row_text = ' '.join(df.iloc[row_idx].fillna('').astype(str).tolist()).lower()
            if sum(1 for kw in keywords if kw in row_text) >= 2:
                return row_idx
        return None

    def _is_salary_value(self, val) -> bool:
        """Check if value looks like a salary."""
        if not pd.notna(val):
            return False
        try:
            num = float(str(val).replace('£', '').replace(',', '').strip())
            return num > 1000 or (num > 0 and num < 100)  # Annual or hourly
        except:
            return False

    def _parse_rate(self, val) -> Optional[float]:
        """Parse a rate value."""
        if not pd.notna(val):
            return None
        try:
            val_str = str(val).replace('£', '').replace(',', '').replace(' ', '').strip()
            # Handle "Point X deleted" etc
            if 'delete' in val_str.lower() or 'n/a' in val_str.lower():
                return None
            rate = float(val_str)
            # Convert hourly to annual if needed
            if 0 < rate < 100:
                rate = rate * 37 * 52.143
            return rate if rate > 0 else None
        except:
            return None

    def _extract_point_number(self, code: str) -> int:
        """Extract numeric part from point code."""
        match = re.search(r'\d+', str(code))
        return int(match.group()) if match else 0

    def _normalize_main_point(self, code: str) -> str:
        """Normalize main pay scale point (M1-M6)."""
        num = self._extract_point_number(code)
        return f"M{min(num, 6)}"

    def _normalize_upper_point(self, code: str) -> str:
        """Normalize upper pay scale point (U1-U3)."""
        num = self._extract_point_number(code)
        return f"U{min(num, 3)}"

    def _normalize_leadership_point(self, code: str) -> str:
        """Normalize leadership point (L01-L50)."""
        num = self._extract_point_number(code)
        return f"L{num:02d}"

    def _normalize_uqt_point(self, code: str) -> str:
        """Normalize unqualified teacher point (UQT1-UQT6)."""
        num = self._extract_point_number(code)
        return f"UQT{num}"

    def _normalize_tlr_code(self, code: str) -> str:
        """Normalize TLR code (TLR1, TLR1A, TLR2B, etc.)."""
        code_upper = code.upper().strip()
        # Handle formats like "1A", "2B", "TLR1A", etc.
        match = re.match(r'(TLR)?(\d)([ABC])?', code_upper)
        if match:
            num = match.group(2)
            suffix = match.group(3) or ''
            return f"TLR{num}{suffix}"
        return f"TLR{code_upper}"

    def _normalize_sen_code(self, code: str) -> str:
        """Normalize SEN code."""
        num = self._extract_point_number(code)
        return f"SEN{num}" if num > 0 else "SEN1"


def extract_payscales_from_folder(folder_path: Path) -> Dict[str, Any]:
    """
    Extract all pay scales and allowances from a folder of Excel files.

    Args:
        folder_path: Path to folder containing xlsx files

    Returns:
        Dict with 'pay_scales', 'allowances', 'grades', 'logs'

    Raises:
        FileNotFoundError: If folder does not exist
        ValueError: If no xlsx files found in folder
    """
    folder_path = Path(folder_path)

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    xlsx_files = [f for f in folder_path.glob('*.xlsx') if not f.name.startswith('~$')]

    if not xlsx_files:
        raise ValueError(f"No xlsx files found in folder: {folder_path}")

    extractor = PayScaleExtractor()

    for f in xlsx_files:
        extractor.extract_from_file(f)

    result = {
        'pay_scales': extractor.pay_scales,
        'allowances': extractor.allowances,
        'grades': extractor.grades,
        'logs': extractor.log_messages,
    }

    if not result['pay_scales']:
        extractor.log("WARNING: No pay scales were imported from the files")

    return result


def get_default_payscales_folder() -> Path:
    """Get the default payscales folder path relative to this module."""
    module_dir = Path(__file__).parent.parent
    return module_dir / "knowledge" / "S2" / "payscales example"


# Test function
if __name__ == '__main__':
    import sys

    # Allow folder path as command line argument
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = get_default_payscales_folder()

    print(f"Looking for payscales in: {folder}")

    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}")
        print("Usage: python payscale_extractor.py [folder_path]")
        sys.exit(1)

    xlsx_files = list(folder.glob('*.xlsx'))
    if not xlsx_files:
        print(f"ERROR: No xlsx files found in folder: {folder}")
        sys.exit(1)

    print(f"Found {len(xlsx_files)} xlsx files")

    try:
        result = extract_payscales_from_folder(folder)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("\n" + "="*60)
    print("EXTRACTION RESULTS")
    print("="*60)

    if not result['pay_scales']:
        print("\nWARNING: No payscales were imported!")
        print("Check that the xlsx files contain recognizable pay scale data.")
    else:
        print(f"\nPay Scales Found: {len(result['pay_scales'])}")
        for ps in result['pay_scales']:
            print(f"  {ps.code}: {ps.title} ({len(ps.points)} points)")
            for p in ps.points[:5]:
                print(f"    - {p.code}: GBP {p.rate:,.2f}")
            if len(ps.points) > 5:
                print(f"    ... and {len(ps.points) - 5} more")

    if not result['allowances']:
        print("\nNo allowances found.")
    else:
        print(f"\nAllowances Found: {len(result['allowances'])}")
        for al in result['allowances']:
            print(f"  {al.code}: {al.title} ({len(al.points)} points)")
            for p in al.points:
                print(f"    - {p.code}: GBP {p.amount:,.2f}")

    print(f"\nGrades Found: {len(result['grades'])}")
    for g in result['grades'][:10]:
        print(f"  {g['code']}: Points {g['from_point']}-{g['to_point']}")
