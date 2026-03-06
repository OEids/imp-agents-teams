"""
S3 Census Processor - Separate Step for Pupil Numbers

Processes school census files (HTML/PDF) and extracts pupil data
for the Pupils sheet in S3 template.

This runs as a SEPARATE STEP before/after S3 specialist,
and output is merged into the final S3 workbook.

Output Format (Pupils sheet):
- FinanceCode: PUPIL_CEN_07, PUPIL_SPRING_KS3, PUPILPREMIUMPLAC, etc.
- SchoolCode: 3-letter school code
- LedgerCode: DEFAULT
- DepartmentCode: DEFAULT
- MonthProfileCode: MONTHLY
- Description: "Year 7 Pupil Numbers - Autumn Census"
- Notes: "From Table 3 of School census collection: Autumn"
- FinancialYearCode: 2024/25
- YearValue: The pupil count
"""

import pandas as pd
import re
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def get_current_academic_year() -> str:
    """
    Get current academic year as 2-digit string.
    Academic year runs Sep-Aug, so:
    - Sep 2024 to Aug 2025 = "24"
    - Sep 2025 to Aug 2026 = "25"
    """
    now = datetime.now()
    # If we're in Sep-Dec, use current year; if Jan-Aug, use previous year
    if now.month >= 9:
        return str(now.year)[-2:]
    else:
        return str(now.year - 1)[-2:]

# Optional imports
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OCR support for scanned PDFs
OCR_AVAILABLE = False
POPPLER_PATH = None
NUMPY_AVAILABLE = False
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageFilter, ImageOps

    # Set tesseract path - check common locations
    tesseract_paths = [
        Path(__file__).parent.parent / "tesseract.exe",  # agent-teams folder
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for tpath in tesseract_paths:
        if tpath.exists():
            pytesseract.pytesseract.tesseract_cmd = str(tpath)
            OCR_AVAILABLE = True
            break

    # Set poppler path for pdf2image
    poppler_paths = [
        Path(__file__).parent.parent / "poppler" / "poppler-24.08.0" / "Library" / "bin",
        Path(__file__).parent.parent / "poppler" / "bin",
        Path(r"C:\Program Files\poppler\bin"),
    ]
    for ppath in poppler_paths:
        if ppath.exists() and (ppath / "pdftoppm.exe").exists():
            POPPLER_PATH = str(ppath)
            break

    # Try to import numpy for advanced image processing
    try:
        import numpy as np
        NUMPY_AVAILABLE = True
    except ImportError:
        pass

except ImportError:
    pass


def preprocess_image_for_ocr(image):
    """
    Preprocess image to improve OCR accuracy.
    - Convert to grayscale
    - Apply contrast enhancement
    - Apply sharpening
    - Convert to binary (threshold)
    """
    # Convert to grayscale
    if image.mode != 'L':
        gray = image.convert('L')
    else:
        gray = image

    # Enhance contrast
    gray = ImageOps.autocontrast(gray, cutoff=2)

    # Apply slight sharpening
    gray = gray.filter(ImageFilter.SHARPEN)

    # Apply binary threshold using numpy if available
    if NUMPY_AVAILABLE:
        import numpy as np
        img_array = np.array(gray)
        # Adaptive threshold - use mean of local area
        threshold = 140
        img_array = ((img_array > threshold) * 255).astype(np.uint8)
        gray = Image.fromarray(img_array)

    return gray


class CensusProcessor:
    """Process census files and extract pupil numbers."""

    YEAR_GROUPS = ['E1', 'E2', 'N1', 'N2', 'R', '1', '2', '3', '4', '5', '6',
                   '7', '8', '9', '10', '11', '12', '13', '14']

    # Finance code mappings for Autumn Census (individual year groups)
    AUTUMN_FINANCE_CODES = {
        'R': ('PUPIL_CEN_00', 'Reception Pupil Numbers - Autumn Census'),
        '1': ('PUPIL_CEN_01', 'Year 1 Pupil Numbers - Autumn Census'),
        '2': ('PUPIL_CEN_02', 'Year 2 Pupil Numbers - Autumn Census'),
        '3': ('PUPIL_CEN_03', 'Year 3 Pupil Numbers - Autumn Census'),
        '4': ('PUPIL_CEN_04', 'Year 4 Pupil Numbers - Autumn Census'),
        '5': ('PUPIL_CEN_05', 'Year 5 Pupil Numbers - Autumn Census'),
        '6': ('PUPIL_CEN_06', 'Year 6 Pupil Numbers - Autumn Census'),
        '7': ('PUPIL_CEN_07', 'Year 7 Pupil Numbers - Autumn Census'),
        '8': ('PUPIL_CEN_08', 'Year 8 Pupil Numbers - Autumn Census'),
        '9': ('PUPIL_CEN_09', 'Year 9 Pupil Numbers - Autumn Census'),
        '10': ('PUPIL_CEN_10', 'Year 10 Pupil Numbers - Autumn Census'),
        '11': ('PUPIL_CEN_11', 'Year 11 Pupil Numbers - Autumn Census'),
        '12': ('PUPIL_CEN_12', 'Year 12 Pupil Numbers - Autumn Census'),
        '13': ('PUPIL_CEN_13', 'Year 13 Pupil Numbers - Autumn Census'),
        '14': ('PUPIL_CEN_14', 'Year 14 Pupil Numbers - Autumn Census'),
        'PLAC': ('PUPILPREMIUMPLAC', 'Pupil Premium PLAC Numbers'),
        'Service': ('PUPILPREMIUMSER', 'Pupil Premium Service Numbers'),
    }

    # Finance code mappings for Spring Census (key stages)
    SPRING_FINANCE_CODES = {
        'Nursery': ('PUPIL_SPRING_NUR', 'Nursery Spring Census Pupil Numbers'),
        'Reception': ('PUPIL_SPRING_FS', 'Foundation Stage Spring Census Pupil Numbers'),
        'KS1': ('PUPIL_SPRING_KS1', 'KS1 Spring Census Pupil Numbers'),
        'KS2': ('PUPIL_SPRING_KS2', 'KS2 Spring Census Pupil Numbers'),
        'KS3': ('PUPIL_SPRING_KS3', 'KS3 Spring Census Pupil Numbers'),
        'KS4': ('PUPIL_SPRING_KS4', 'KS4 Spring Census Pupil Numbers'),
        'KS5': ('PUPIL_SPRING_KS5', 'KS5 Spring Census Pupil Numbers'),
    }

    # Calculator codes for year groups
    CALCULATOR_CODES = {
        'PUPIL_CEN_00': '0%_CALC',
        'PUPIL_CEN_01': 'PUPILY00_LY',
        'PUPIL_CEN_02': 'PUPILY01_LY',
        'PUPIL_CEN_03': 'PUPILY02_LY',
        'PUPIL_CEN_04': 'PUPILY03_LY',
        'PUPIL_CEN_05': 'PUPILY04_LY',
        'PUPIL_CEN_06': 'PUPILY05_LY',
        'PUPIL_CEN_07': '0%_CALC',
        'PUPIL_CEN_08': 'PUPILY07_LY',
        'PUPIL_CEN_09': 'PUPILY08_LY',
        'PUPIL_CEN_10': 'PUPILY09_LY',
        'PUPIL_CEN_11': 'PUPILY10_LY',
        'PUPIL_CEN_12': '0%_CALC',
        'PUPIL_CEN_13': 'PUPILY12_LY',
        'PUPIL_CEN_14': 'PUPILY13_LY',
        'PUPILPREMIUMPLAC': 'PUPPREMIUM_FACTOR',
        'PUPILPREMIUMSER': 'PUPPREMIUM_FACTOR',
    }

    def __init__(self, school_codes_df: pd.DataFrame = None):
        """
        Initialize census processor.

        Args:
            school_codes_df: DataFrame with school codes (columns: SchoolCode, Title)
        """
        self.school_codes_df = school_codes_df
        self.october_data = {}
        self.spring_data = {}
        self.unextractable = []
        self.processing_log = []

    def log(self, message: str):
        """Add to processing log."""
        self.processing_log.append(message)

    def match_school(self, school_name: str) -> Optional[str]:
        """Match school name to school code."""
        if not school_name or self.school_codes_df is None:
            return None

        school_name_clean = school_name.upper().replace('_', ' ').strip()

        for _, row in self.school_codes_df.iterrows():
            title = str(row.get('Title', '')).upper().replace('_', ' ').strip()
            if not title or title in ['DEFAULT', 'CENTRAL', 'NAN']:
                continue

            # Exact match
            if school_name_clean == title:
                return row['SchoolCode']

            # Flexible suffix matching
            suffixes = ['PRIMARY SCHOOL', 'SCHOOL', 'ACADEMY', 'COLLEGE', 'PRIMARY']
            for suffix in suffixes:
                if school_name_clean + ' ' + suffix == title or title + ' ' + suffix == school_name_clean:
                    return row['SchoolCode']

            # Partial match
            if school_name_clean in title or title in school_name_clean:
                return row['SchoolCode']

        return None

    def match_school_from_filename(self, filename: str) -> Optional[str]:
        """
        Try to match school code directly from filename.
        E.g., "BPS Autumn Census.pdf" -> matches SchoolCode "BPS"
        """
        if self.school_codes_df is None:
            return None

        # Extract potential school code from start of filename
        # Common patterns: "BPS_Census.pdf", "BPS Autumn Census.pdf", "BPS-Census.pdf"
        filename_clean = Path(filename).stem.upper()

        # Get all valid school codes from template
        valid_codes = set()
        for _, row in self.school_codes_df.iterrows():
            code = str(row.get('SchoolCode', '')).upper().strip()
            if code and code not in ['DEFAULT', 'CENTRAL', 'NAN', '']:
                valid_codes.add(code)

        # Check if filename starts with a school code
        for code in valid_codes:
            # Match at start of filename followed by separator or space
            if filename_clean.startswith(code + '_') or \
               filename_clean.startswith(code + ' ') or \
               filename_clean.startswith(code + '-') or \
               filename_clean == code:
                return code

        # Also check if the code appears as a distinct word in the filename
        filename_parts = re.split(r'[_\s\-]+', filename_clean)
        for part in filename_parts:
            if part in valid_codes:
                return part

        return None

    def extract_census_type_from_content(self, content: str) -> tuple:
        """Extract census type and year from document content."""
        match = re.search(r'School census collection:\s*(autumn|spring)\s*(\d{4})', content, re.IGNORECASE)
        if match:
            census_type = 'Oct' if match.group(1).lower() == 'autumn' else 'Spring'
            year = match.group(2)[-2:]
            return census_type, year
        return None, None

    def extract_census_type_from_filename(self, filename: str) -> tuple:
        """Extract census type from filename."""
        filename_upper = filename.upper()
        year_match = re.search(r'(\d{2})', filename)
        year = year_match.group(1) if year_match else None

        if any(x in filename_upper for x in ['OCT', 'AUTUMN']):
            return 'Oct', year
        elif any(x in filename_upper for x in ['JAN', 'SPRING']):
            return 'Spring', year
        return None, year

    def extract_school_name(self, content: str) -> Optional[str]:
        """Extract school name from Summary for: field."""
        match = re.search(r'Summary for:\s*</b>([^<]+)', content, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            la_match = re.search(r'(.+?)(?:Local authority|$)', name, re.IGNORECASE)
            return la_match.group(1).strip() if la_match else name

        match = re.search(r'Summary for:\s*([^\n<]+)', content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def extract_table3_data(self, content: str) -> dict:
        """Extract year group data from Table 3."""
        data = {yg: 0 for yg in self.YEAR_GROUPS}

        # First try HTML parsing (for HTML files)
        if BS4_AVAILABLE and '<table' in content.lower():
            table3_match = re.search(r'Table 3:(.*?)(?=Table \d+:|$)', content, re.DOTALL | re.IGNORECASE)
            if table3_match:
                table3_content = table3_match.group(1)
                soup = BeautifulSoup(table3_content, 'html.parser')
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            yg_cell = cells[0].get_text(strip=True)
                            yg = yg_cell.upper().replace('YEAR ', '').replace('RECEPTION', 'R')
                            if yg in ['E1', 'E2', 'N1', 'N2', 'R'] or yg.isdigit():
                                if yg.isdigit():
                                    yg = str(int(yg))
                                if yg in data:
                                    try:
                                        # cells[1] is "Total number of pupils"
                                        total_val = int(cells[1].get_text(strip=True) or 0)
                                        data[yg] = total_val
                                    except (ValueError, IndexError):
                                        pass
                    if sum(data.values()) > 0:
                        return data

        # Fallback: text-based extraction (for OCR/PDF text)
        # Look for patterns like "Year 7" or "Reception" followed by numbers
        # Census format: Year group | Headcount | C | M | Total
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match year group patterns
            # Pattern: "Reception 45 23 22 45" or "Year 7 120 60 60 120"
            # Also: "R 45 23 22" or "7 120 60 60"
            patterns = [
                # "Reception" or "Year X" at start
                r'^(Reception|Year\s*(\d+))\s+(\d+)\s+(\d+)\s+(\d+)',
                # Just the year number at start
                r'^(\d{1,2})\s+(\d+)\s+(\d+)\s+(\d+)',
                # Nursery patterns
                r'^(N1|N2|Nursery\s*1|Nursery\s*2)\s+(\d+)\s+(\d+)\s+(\d+)',
                # Early Years
                r'^(E1|E2)\s+(\d+)\s+(\d+)\s+(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    yg = None
                    c_val = 0
                    m_val = 0

                    if 'Reception' in str(groups[0]).title():
                        yg = 'R'
                        c_val = int(groups[2]) if len(groups) > 2 else 0
                        m_val = int(groups[3]) if len(groups) > 3 else 0
                    elif groups[0].upper() in ['N1', 'N2', 'E1', 'E2']:
                        yg = groups[0].upper()
                        c_val = int(groups[1]) if len(groups) > 1 else 0
                        m_val = int(groups[2]) if len(groups) > 2 else 0
                    elif 'Year' in str(groups[0]):
                        yg = groups[1]  # The number after "Year"
                        c_val = int(groups[3]) if len(groups) > 3 else 0
                        m_val = int(groups[4]) if len(groups) > 4 else 0
                    elif groups[0].isdigit():
                        yg = str(int(groups[0]))
                        c_val = int(groups[2]) if len(groups) > 2 else 0
                        m_val = int(groups[3]) if len(groups) > 3 else 0

                    if yg and yg in data:
                        data[yg] = c_val + m_val
                    break

        return data

    def extract_table5_data(self, content: str) -> dict:
        """Extract PLAC and Service data from Table 5."""
        data = {'PLAC': 0, 'Service': 0}

        # Try text-based extraction first (works for both HTML text and OCR)
        # Look for PLAC/Post looked after patterns
        plac_match = re.search(r'(?:Post[- ]?looked[- ]?after|PLAC)[^\d]*(\d+)', content, re.IGNORECASE)
        if plac_match:
            data['PLAC'] = int(plac_match.group(1))

        # Look for Service children patterns
        service_match = re.search(r'(?:Service\s+children|Service\s+child)[^\d]*(\d+)', content, re.IGNORECASE)
        if service_match:
            data['Service'] = int(service_match.group(1))

        # If found data, return early
        if data['PLAC'] > 0 or data['Service'] > 0:
            return data

        # Fallback to HTML parsing
        if not BS4_AVAILABLE:
            return data

        table5_match = re.search(r'Table 5:(.*?)(?=Table \d+:|$)', content, re.DOTALL | re.IGNORECASE)
        if not table5_match:
            return data

        table5_content = table5_match.group(1)
        soup = BeautifulSoup(table5_content, 'html.parser')
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                try:
                    value = int(cells[-1].get_text(strip=True) or 0)
                except ValueError:
                    value = 0

                if 'post looked after' in label or 'plac' in label:
                    data['PLAC'] = value
                elif 'service children' in label:
                    data['Service'] = value

        return data

    def process_html_file(self, filepath: Path) -> dict:
        """Process an HTML census file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {'success': False, 'reason': f'Read error: {str(e)}'}

        school_name = self.extract_school_name(content)
        school_code = self.match_school(school_name)

        # Fallback: try to match school code from filename (e.g., "BPS_Census.pdf" -> "BPS")
        if school_code is None:
            school_code = self.match_school_from_filename(filepath.name)

        census_type, year = self.extract_census_type_from_content(content)

        if not census_type:
            census_type, year = self.extract_census_type_from_filename(str(filepath))

        table3_data = self.extract_table3_data(content)
        table5_data = self.extract_table5_data(content) if census_type == 'Oct' else {}

        # Build specific error reason if failed
        reason = None
        if school_code is None and census_type is None:
            reason = f"School not matched ('{school_name}') and census type not detected"
        elif school_code is None:
            reason = f"School not matched: '{school_name}' not found in template Schools tab"
        elif census_type is None:
            reason = "Census type not detected (Autumn/Spring)"

        return {
            'school_name': school_name,
            'school_code': school_code,
            'census_type': census_type,
            'year': year,
            'year_groups': table3_data,
            'table5': table5_data,
            'success': school_code is not None and census_type is not None,
            'reason': reason
        }

    def extract_text_with_ocr(self, filepath: Path) -> str:
        """Extract text from scanned PDF using OCR."""
        if not OCR_AVAILABLE:
            return ""

        try:
            # Convert PDF pages to images (use poppler_path if available)
            if POPPLER_PATH:
                images = convert_from_path(str(filepath), dpi=300, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(str(filepath), dpi=300)

            text = ""
            for i, image in enumerate(images):
                # Extract text from each page image
                page_text = pytesseract.image_to_string(image)
                if page_text:
                    text += page_text + "\n"

            return text
        except Exception as e:
            self.log(f"OCR error: {e}")
            return ""

    def extract_table_with_ocr(self, filepath: Path) -> dict:
        """
        Extract Table 3 data from scanned PDF using OCR with positional data.
        Uses word positions to reconstruct table structure.
        """
        if not OCR_AVAILABLE:
            return {}

        data = {yg: 0 for yg in self.YEAR_GROUPS}

        try:
            # Convert PDF pages to images at higher DPI for better OCR
            if POPPLER_PATH:
                images = convert_from_path(str(filepath), dpi=300, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(str(filepath), dpi=300)

            for page_num, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = preprocess_image_for_ocr(image)

                # Use OCR config optimized for sparse text with numbers
                # PSM 6 = Assume uniform block of text
                # PSM 11 = Sparse text. Find as much text as possible in no particular order
                ocr_config = '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '

                # Get OCR data with bounding boxes using preprocessed image
                ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT, config=ocr_config)

                # Build list of words with positions
                words = []
                for i in range(len(ocr_data['text'])):
                    text = ocr_data['text'][i].strip()
                    conf = int(ocr_data['conf'][i])
                    if text and conf > 20:  # Lower threshold to catch more text
                        words.append({
                            'text': text,
                            'x': ocr_data['left'][i],
                            'y': ocr_data['top'][i],
                            'w': ocr_data['width'][i],
                            'h': ocr_data['height'][i],
                            'conf': conf
                        })

                # Calculate dynamic y_tolerance based on typical row height
                if words:
                    avg_height = sum(w['h'] for w in words) / len(words)
                    y_tolerance = max(15, avg_height * 0.5)  # At least 15px or half row height
                else:
                    y_tolerance = 15

                # Group words into rows (same y position within tolerance)
                rows = []

                for word in sorted(words, key=lambda w: w['y']):
                    added_to_row = False
                    for row in rows:
                        # Check if word is on same row (similar y position)
                        avg_y = sum(w['y'] for w in row) / len(row)
                        if abs(word['y'] - avg_y) < y_tolerance:
                            row.append(word)
                            added_to_row = True
                            break
                    if not added_to_row:
                        rows.append([word])

                # Sort words within each row by x position (left to right)
                for row in rows:
                    row.sort(key=lambda w: w['x'])

                # Now look for year group patterns in rows
                for row in rows:
                    row_text = ' '.join(w['text'] for w in row)
                    row_text_upper = row_text.upper()

                    # Extract numbers from row
                    numbers = re.findall(r'\b(\d{1,4})\b', row_text)
                    if len(numbers) < 1:
                        continue

                    # Check for year group indicators
                    year_group = None

                    # Check Reception
                    if 'RECEPTION' in row_text_upper or row_text_upper.strip().startswith('R '):
                        year_group = 'R'
                    # Check for "Year X" pattern
                    elif 'YEAR' in row_text_upper:
                        year_match = re.search(r'YEAR\s*(\d{1,2})', row_text_upper)
                        if year_match:
                            yg_num = year_match.group(1)
                            if yg_num in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14']:
                                year_group = yg_num
                    # Check N1, N2, E1, E2
                    elif re.match(r'^[NE][12]\b', row_text_upper.strip()):
                        match = re.match(r'^([NE][12])\b', row_text_upper.strip())
                        if match:
                            year_group = match.group(1).upper()
                    # Check standalone number at start (e.g., "7  45  23  22")
                    else:
                        # First word might be year group number
                        first_word = row[0]['text'].strip() if row else ''
                        if first_word.isdigit() and first_word in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14']:
                            year_group = first_word
                            # Remove first number from numbers list since it's the year group
                            if numbers and numbers[0] == first_word:
                                numbers = numbers[1:]

                    if year_group and year_group in data and numbers:
                        # Get the pupil count - typically the first or second number is total
                        # In census Table 3: YearGroup | Total | C | M
                        # We want the Total (first number after year group)
                        try:
                            # Use first number as total pupil count
                            total = int(numbers[0])
                            if total > 0 and total < 2000:  # Sanity check
                                data[year_group] = total
                                self.log(f"  OCR extracted: Year {year_group} = {total}")
                        except (ValueError, IndexError):
                            pass

            # If primary method didn't extract much, try fallback
            total_extracted = sum(data.values())
            if total_extracted == 0:
                self.log("  Primary OCR extraction found nothing, trying fallback method...")
                data = self._ocr_fallback_extraction(filepath)

            return data

        except Exception as e:
            self.log(f"OCR table extraction error: {e}")
            return {}

    def _ocr_fallback_extraction(self, filepath: Path) -> dict:
        """
        Fallback OCR extraction using plain text with flexible pattern matching.
        Also looks for table-based data in the census format.
        """
        data = {yg: 0 for yg in self.YEAR_GROUPS}

        try:
            if POPPLER_PATH:
                images = convert_from_path(str(filepath), dpi=300, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(str(filepath), dpi=300)

            for page_num, image in enumerate(images):
                # Preprocess and get plain text
                processed = preprocess_image_for_ocr(image)
                # Use PSM 6 = Assume uniform block of text
                text = pytesseract.image_to_string(processed, config='--psm 6')

                lines = text.split('\n')

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Check Reception patterns
                    if re.search(r'recep', line, re.IGNORECASE):
                        nums = re.findall(r'\b(\d{1,3})\b', line)
                        for n in nums:
                            val = int(n)
                            if 5 < val < 150:  # Reasonable class size
                                data['R'] = val
                                self.log(f"  Page {page_num+1}: Reception = {val}")
                                break

                    # Check Year X patterns  (e.g. "Year 1", "Y1", etc)
                    year_match = re.search(r'(?:year|y)\s*(\d{1,2})\b', line, re.IGNORECASE)
                    if year_match:
                        yg = year_match.group(1)
                        if yg in data:
                            # Find numbers after the year group mention
                            rest = line[year_match.end():]
                            nums = re.findall(r'\b(\d{1,3})\b', rest)
                            for n in nums:
                                val = int(n)
                                if 5 < val < 150:
                                    data[yg] = val
                                    self.log(f"  Page {page_num+1}: Year {yg} = {val}")
                                    break

                    # Check N1/N2 patterns
                    n_match = re.search(r'\b(n[12])\b', line, re.IGNORECASE)
                    if n_match:
                        yg = n_match.group(1).upper()
                        if yg in data:
                            rest = line[n_match.end():]
                            nums = re.findall(r'\b(\d{1,3})\b', rest)
                            for n in nums:
                                val = int(n)
                                if 1 < val < 100:
                                    data[yg] = val
                                    self.log(f"  Page {page_num+1}: {yg} = {val}")
                                    break

                # Also try extracting from Table 2 format which shows age-based data
                # In autumn census: Age 4 = Reception, Age 5 = Year 1, etc.
                # This can be useful if Table 3 is not clear
                self._extract_from_age_table(text, data)

            return data
        except Exception as e:
            self.log(f"Fallback OCR error: {e}")
            return data

    def _extract_from_age_table(self, text: str, data: dict):
        """
        Extract pupil numbers from Table 2 (age-based data).
        In autumn census: Age 4 (as at 31 Aug) = Reception pupils, etc.
        """
        # Look for patterns like: age | date_range | number
        # Example: 5 01/09/2018 - 31/08/2019 30
        lines = text.split('\n')

        # Age to year group mapping (for autumn census, age as at 31 Aug)
        # Age 4 = Reception, Age 5 = Year 1, Age 6 = Year 2, etc.
        age_to_yg = {
            '4': 'R', '5': '1', '6': '2', '7': '3', '8': '4',
            '9': '5', '10': '6', '11': '7', '12': '8', '13': '9',
            '14': '10', '15': '11', '16': '12', '17': '13', '18': '14'
        }

        for line in lines:
            # Pattern: starts with age number, has date range, ends with pupil count(s)
            # Example: "[7 01/09/2016 - 31/08/2017] 30 / NO"
            match = re.search(r'\b(\d{1,2})\s+\d{2}/\d{2}/\d{4}.*?(\d{1,3})\b', line)
            if match:
                age = match.group(1)
                count = int(match.group(2))
                if age in age_to_yg and 1 <= count <= 200:
                    yg = age_to_yg[age]
                    if data.get(yg, 0) == 0:  # Don't overwrite if already found
                        data[yg] = count
                        self.log(f"  Age table: Age {age} -> Year {yg} = {count}")

    def extract_school_name_from_ocr(self, filepath: Path) -> Optional[str]:
        """Extract school name from scanned PDF using OCR."""
        if not OCR_AVAILABLE:
            return None

        try:
            # Convert just first page at high DPI
            if POPPLER_PATH:
                images = convert_from_path(str(filepath), dpi=300, first_page=1, last_page=1, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(str(filepath), dpi=300, first_page=1, last_page=1)

            if images:
                # Preprocess for better OCR
                processed = preprocess_image_for_ocr(images[0])
                text = pytesseract.image_to_string(processed)

                # Look for "Summary for:" pattern
                match = re.search(r'Summary for[:\s]+([A-Za-z\s]+?)(?:Local|LA|$)', text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

                # Try alternative patterns
                match = re.search(r'School[:\s]+([A-Za-z\s]+?)(?:Primary|Academy|$)', text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

                # Look for school name in header area (common census format)
                match = re.search(r'(?:census|collection)[:\s]+.+?(?:for|from)[:\s]+([A-Za-z\s]+?)(?:\n|$)', text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

            return None
        except Exception as e:
            self.log(f"OCR school name extraction error: {e}")
            return None

    def process_pdf_file(self, filepath: Path) -> dict:
        """Process a PDF census file."""
        if not PDF_AVAILABLE:
            return {'success': False, 'reason': 'PDF support not installed (pdfplumber)'}

        content = ""
        use_ocr = False
        table3_data = {yg: 0 for yg in self.YEAR_GROUPS}

        # First try pdfplumber (for text-based PDFs)
        try:
            with pdfplumber.open(str(filepath)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
        except Exception as e:
            return {'success': False, 'reason': f'PDF read error: {str(e)}'}

        # If no text extracted, try OCR (for scanned PDFs)
        if len(content.strip()) < 100:
            if OCR_AVAILABLE:
                self.log(f"  No text found, trying OCR with table extraction...")
                use_ocr = True

                # Use improved table extraction for scanned PDFs
                table3_data = self.extract_table_with_ocr(filepath)

                # Also get text content for school name and census type
                content = self.extract_text_with_ocr(filepath)

                if len(content.strip()) < 50 and sum(table3_data.values()) == 0:
                    return {'success': False, 'reason': 'OCR could not extract data from scanned PDF'}
            else:
                return {'success': False, 'reason': 'Scanned PDF - OCR not available (install pytesseract)'}

        school_name = self.extract_school_name(content)
        school_code = self.match_school(school_name)

        # Fallback: try to match school code from filename (e.g., "BPS_Census.pdf" -> "BPS")
        if school_code is None:
            school_code = self.match_school_from_filename(filepath.name)

        # Try OCR-specific school name extraction if still no match
        if school_code is None and use_ocr:
            ocr_school_name = self.extract_school_name_from_ocr(filepath)
            if ocr_school_name:
                school_code = self.match_school(ocr_school_name)
                if school_code:
                    school_name = ocr_school_name

        census_type, year = self.extract_census_type_from_content(content)

        if not census_type:
            census_type, year = self.extract_census_type_from_filename(str(filepath))

        # For non-OCR PDFs, extract table data from text content
        if not use_ocr:
            table3_data = self.extract_table3_data(content)

        table5_data = self.extract_table5_data(content) if census_type == 'Oct' else {}

        total = sum(table3_data.values())
        if total == 0:
            return {
                'success': False,
                'reason': 'No pupil data extracted from PDF (table extraction failed)',
                'school_name': school_name,
                'school_code': school_code,
                'census_type': census_type,
                'year': year
            }

        # Build specific error reason if failed
        reason = None
        if school_code is None and census_type is None:
            reason = f"School not matched ('{school_name}') and census type not detected"
        elif school_code is None:
            reason = f"School not matched: '{school_name}' not found in template Schools tab"
        elif census_type is None:
            reason = "Census type not detected (Autumn/Spring)"

        return {
            'school_name': school_name,
            'school_code': school_code,
            'census_type': census_type,
            'year': year,
            'year_groups': table3_data,
            'table5': table5_data,
            'success': school_code is not None and census_type is not None,
            'reason': reason
        }

    def process_census_file(self, filepath: Path):
        """Process a single census file."""
        filename = filepath.name
        ext = filepath.suffix.lower()

        self.log(f"Processing: {filename}")

        if ext in ['.html', '.htm']:
            result = self.process_html_file(filepath)
        elif ext == '.pdf':
            result = self.process_pdf_file(filepath)
        else:
            result = {'success': False, 'reason': f'Unsupported file type: {ext}'}

        if not result.get('success'):
            self.unextractable.append({
                'School Code': result.get('school_code', ''),
                'Document Name': filename,
                'Expected School': result.get('school_name', ''),
                'Census Type': f"{result.get('census_type', '')} {result.get('year', '')}".strip(),
                'Reason': result.get('reason', 'Unknown error')
            })
            self.log(f"  FAILED: {result.get('reason', 'Unknown error')}")
            return

        col_name = f"{result['school_code']} {result['census_type']} {result['year']}"

        if result['census_type'] == 'Oct':
            self.october_data[col_name] = {
                **result['year_groups'],
                'PLAC': result['table5'].get('PLAC', 0),
                'Service': result['table5'].get('Service', 0)
            }
        else:
            self.spring_data[col_name] = result['year_groups']

        self.log(f"  SUCCESS: {col_name}")

    def create_october_sheet(self) -> pd.DataFrame:
        """Create October Census DataFrame."""
        if not self.october_data:
            return pd.DataFrame()

        rows = self.YEAR_GROUPS + ['TOTAL', 'PLAC', 'Service']
        df = pd.DataFrame(index=rows)

        for col, data in sorted(self.october_data.items()):
            col_data = []
            for yg in self.YEAR_GROUPS:
                col_data.append(data.get(yg, 0))
            col_data.append(sum(data.get(yg, 0) for yg in self.YEAR_GROUPS))  # TOTAL
            col_data.append(data.get('PLAC', 0))
            col_data.append(data.get('Service', 0))
            df[col] = col_data

        df.index.name = 'Year Group'
        return df

    def create_spring_sheet(self) -> pd.DataFrame:
        """Create Spring Census DataFrame (legacy format)."""
        if not self.spring_data:
            return pd.DataFrame()

        rows = ['EY', 'Nursery', 'Reception', 'KS1', 'KS2', 'KS3', 'KS4', 'KS5', 'TOTAL']
        df = pd.DataFrame(index=rows)

        for col, data in sorted(self.spring_data.items()):
            ey = data.get('E1', 0) + data.get('E2', 0)
            nursery = data.get('N1', 0) + data.get('N2', 0)
            reception = data.get('R', 0)
            ks1 = sum(data.get(str(y), 0) for y in [1, 2])
            ks2 = sum(data.get(str(y), 0) for y in [3, 4, 5, 6])
            ks3 = sum(data.get(str(y), 0) for y in [7, 8, 9])
            ks4 = sum(data.get(str(y), 0) for y in [10, 11])
            ks5 = sum(data.get(str(y), 0) for y in [12, 13, 14])
            total = ey + nursery + reception + ks1 + ks2 + ks3 + ks4 + ks5
            df[col] = [ey, nursery, reception, ks1, ks2, ks3, ks4, ks5, total]

        df.index.name = 'Key Stage'
        return df

    def create_pupils_sheet(self, financial_year: str = None) -> pd.DataFrame:
        """
        Create Pupils sheet in the S3 template format.

        Args:
            financial_year: Financial year code (e.g., "2024/25"). If None, derived from census year.

        Returns:
            DataFrame with columns matching Pupils sheet format
        """
        rows = []

        # Process October (Autumn) census data
        for col_key, data in self.october_data.items():
            # Parse column key: "SCHOOLCODE Oct YY"
            parts = col_key.split()
            if len(parts) >= 3:
                school_code = parts[0]
                census_year = parts[-1]  # Last 2 digits of year
            else:
                school_code = col_key
                census_year = get_current_academic_year()  # Dynamic default

            # Derive financial year from census year (e.g., Oct 24 = 2024/25)
            year_code = financial_year or f"20{census_year}/{int(census_year)+1:02d}"

            # Add row for each year group
            for yg, value in data.items():
                if yg in self.AUTUMN_FINANCE_CODES and value > 0:
                    finance_code, description = self.AUTUMN_FINANCE_CODES[yg]
                    calc_code = self.CALCULATOR_CODES.get(finance_code, '0%_CALC')

                    notes = "From Table 3 of School census collection: Autumn"
                    if yg == 'PLAC':
                        notes = "Post Looked After Children number From Table 5 of School census collection: Autumn"
                    elif yg == 'Service':
                        notes = "Service Children number From Table 5 of School census collection: Autumn"

                    rows.append({
                        'FinanceCode': finance_code,
                        'SchoolCode': school_code,
                        'LedgerCode': 'DEFAULT',
                        'DepartmentCode': 'DEFAULT',
                        'FundCode': None,
                        'CalculatorCode': calc_code,
                        'MonthProfileCode': 'MONTHLY',
                        'Description': description,
                        'Notes': notes,
                        'YearNotes': None,
                        'MatEditOnly': False,
                        'FinancialYearCode': year_code,
                        'Calculated': False,
                        'YearValue': value
                    })

        # Process Spring census data
        for col_key, data in self.spring_data.items():
            # Parse column key: "SCHOOLCODE Spring YY"
            parts = col_key.split()
            if len(parts) >= 3:
                school_code = parts[0]
                census_year = parts[-1]
            else:
                school_code = col_key
                census_year = get_current_academic_year()  # Dynamic default

            # Spring census year code (e.g., Spring 25 = 2024/25)
            prev_year = int(census_year) - 1
            year_code = financial_year or f"20{prev_year:02d}/{census_year}"

            # Calculate key stage totals
            nursery = data.get('N1', 0) + data.get('N2', 0)
            reception = data.get('R', 0)
            ks1 = sum(data.get(str(y), 0) for y in [1, 2])
            ks2 = sum(data.get(str(y), 0) for y in [3, 4, 5, 6])
            ks3 = sum(data.get(str(y), 0) for y in [7, 8, 9])
            ks4 = sum(data.get(str(y), 0) for y in [10, 11])
            ks5 = sum(data.get(str(y), 0) for y in [12, 13, 14])

            spring_values = {
                'Nursery': nursery,
                'Reception': reception,
                'KS1': ks1,
                'KS2': ks2,
                'KS3': ks3,
                'KS4': ks4,
                'KS5': ks5,
            }

            for ks_name, value in spring_values.items():
                if value > 0 and ks_name in self.SPRING_FINANCE_CODES:
                    finance_code, description = self.SPRING_FINANCE_CODES[ks_name]

                    notes_map = {
                        'Nursery': 'Nursery Students From Table 3 of School census collection: Spring',
                        'Reception': 'Reception Students From Table 3 of School census collection: Spring',
                        'KS1': 'Year 1 & 2 Students From Table 3 of School census collection: Spring',
                        'KS2': 'Year 3, 4, 5, 6 Students From Table 3 of School census collection: Spring',
                        'KS3': 'Year 7, 8, and 9 Students From Table 3 of School census collection: Spring',
                        'KS4': 'Year 10 & 11 Students From Table 3 of School census collection: Spring',
                        'KS5': 'Year 12, 13, and 14 Students From Table 3 of School census collection: Spring',
                    }

                    rows.append({
                        'FinanceCode': finance_code,
                        'SchoolCode': school_code,
                        'LedgerCode': 'DEFAULT',
                        'DepartmentCode': 'DEFAULT',
                        'FundCode': None,
                        'CalculatorCode': finance_code,  # Spring uses same code
                        'MonthProfileCode': 'MONTHLY',
                        'Description': description,
                        'Notes': notes_map.get(ks_name, ''),
                        'YearNotes': None,
                        'MatEditOnly': False,
                        'FinancialYearCode': year_code,
                        'Calculated': False,
                        'YearValue': value
                    })

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Reorder columns to match template
        column_order = [
            'FinanceCode', 'SchoolCode', 'LedgerCode', 'DepartmentCode',
            'FundCode', 'CalculatorCode', 'MonthProfileCode', 'Description',
            'Notes', 'YearNotes', 'MatEditOnly', 'FinancialYearCode',
            'Calculated', 'YearValue'
        ]
        df = df[[c for c in column_order if c in df.columns]]

        return df

    def process_folder(self, census_folder: Path, financial_year: str = None) -> Dict[str, Any]:
        """
        Process all census files in a folder.

        Args:
            census_folder: Path to folder containing census files
            financial_year: Financial year code (e.g., "2024/25") for output

        Returns:
            Dict with:
            - pupils_sheet: DataFrame in Pupils sheet format (for S3 template)
            - october_census: DataFrame for October census (legacy)
            - spring_census: DataFrame for Spring census (legacy)
            - unextractable: List of files that couldn't be processed
            - summary: Processing summary
        """
        self.october_data = {}
        self.spring_data = {}
        self.unextractable = []
        self.processing_log = []

        self.log("=" * 50)
        self.log("CENSUS PROCESSOR - STARTING")
        self.log("=" * 50)

        if not census_folder.exists():
            self.log(f"Folder not found: {census_folder}")
            return {
                'success': False,
                'pupils_sheet': pd.DataFrame(),
                'october_census': pd.DataFrame(),
                'spring_census': pd.DataFrame(),
                'unextractable': [],
                'summary': {'error': 'Folder not found'},
                'log': self.processing_log
            }

        # Find census files
        census_files = []
        for ext in ['.html', '.htm', '.pdf']:
            census_files.extend(census_folder.glob(f'*{ext}'))
            census_files.extend(census_folder.glob(f'**/*{ext}'))

        census_files = list(set(census_files))  # Remove duplicates

        self.log(f"Found {len(census_files)} census files")

        for filepath in census_files:
            if filepath.name.startswith('~$'):
                continue
            self.process_census_file(filepath)

        # Create output DataFrames
        pupils_df = self.create_pupils_sheet(financial_year)
        october_df = self.create_october_sheet()
        spring_df = self.create_spring_sheet()

        self.log("\n" + "=" * 50)
        self.log("CENSUS PROCESSING COMPLETE")
        self.log(f"  October census columns: {len(self.october_data)}")
        self.log(f"  Spring census columns: {len(self.spring_data)}")
        self.log(f"  Pupils sheet rows: {len(pupils_df)}")
        self.log(f"  Unextractable files: {len(self.unextractable)}")
        self.log("=" * 50)

        return {
            'success': True,
            'pupils_sheet': pupils_df,
            'october_census': october_df,
            'spring_census': spring_df,
            'unextractable': self.unextractable,
            'summary': {
                'october_count': len(self.october_data),
                'spring_count': len(self.spring_data),
                'pupils_rows': len(pupils_df),
                'failed_count': len(self.unextractable),
                'total_processed': len(census_files)
            },
            'log': self.processing_log
        }


def run_census_processor(
    census_folder: Path,
    school_codes_df: pd.DataFrame = None,
    financial_year: str = None
) -> Dict[str, Any]:
    """
    Run census processor as a separate step.

    Args:
        census_folder: Path to folder with census files (HTML/PDF)
        school_codes_df: DataFrame with school codes for matching
        financial_year: Financial year code (e.g., "2024/25")

    Returns:
        Processing result with:
        - pupils_sheet: DataFrame in Pupils sheet format (for S3 template)
        - october_census: DataFrame for October census
        - spring_census: DataFrame for Spring census
        - unextractable: List of files that couldn't be processed
        - summary: Processing summary
        - log: Processing log messages
    """
    processor = CensusProcessor(school_codes_df=school_codes_df)
    return processor.process_folder(census_folder, financial_year=financial_year)


def is_census_file(filepath: Path) -> bool:
    """Check if a file is a census file (HTML/PDF)."""
    ext = filepath.suffix.lower()
    return ext in ['.html', '.htm', '.pdf']


def get_census_files(folder: Path) -> List[Path]:
    """Get list of census files in a folder."""
    files = []
    for ext in ['.html', '.htm', '.pdf']:
        files.extend(folder.glob(f'*{ext}'))
    return [f for f in files if not f.name.startswith('~$')]
