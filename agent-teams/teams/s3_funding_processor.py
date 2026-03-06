"""
S3 Funding Statement Processor - GAG Funding Extraction

Processes GAG funding statement PDFs (Pre-16 and Post-16) and extracts funding data
for the Funding sheet in S3 template.

This runs as a SEPARATE STEP in the S3 workflow, after code mapping.
Output is merged into the final S3 workbook Funding tab.

Output Schema:
- SchoolCode: 3-letter school code
- Description: IMP funding line description
- YearValue: Extracted funding amount
- Source: PDF filename for audit
- Validated: True if total matches
"""

import pandas as pd
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Optional PDF support
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Import mapping definitions from gag_funding_mapper
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "knowledge" / "S3" / "funding"))
try:
    from gag_funding_mapper import (
        primary_mapping,
        secondary_mapping,
        allthrough_mapping,
        post16_mapping,
        HN_PRE16_DESCRIPTION,
        HN_POST16_DESCRIPTION,
    )
except ImportError:
    # Fallback mappings if import fails
    primary_mapping = {
        "01 - GAG AWPU/Basic Entitlement Primary": "Basic Entitlement - Primary",
        "02 - GAG Deprivation Primary IDACI Band A": "Primary IDACI Band A",
        "03 - GAG Deprivation Primary IDACI Band B": "Primary IDACI Band B",
        "04 - GAG Deprivation Primary IDACI Band C": "Primary IDACI Band C",
        "05 - GAG Deprivation Primary IDACI Band D": "Primary IDACI Band D",
        "06 - GAG Deprivation Primary IDACI Band E": "Primary IDACI Band E",
        "07 - GAG Deprivation Primary IDACI Band F": "Primary IDACI Band F",
        "08 - GAG Deprivation Primary FSM": "Primary FSM",
        "09 - GAG Deprivation Primary FSM6": "Primary FSM6",
        "10 - GAG Prior Attainment Primary": "Primary Low Prior Attainment",
        "11 - GAG EAL Primary": "Primary EAL",
        "12 - GAG Mobility Primary": "Primary Mobility",
        "13 - GAG London Fringe": "London Fringe",
        "14 - GAG Lump Sum Primary": "Primary Lump Sum",
        "15 - GAG PFI": "PFI",
        "16 - GAG Split Sites": "Split Sites",
        "17 - GAG Sparsity": "Sparsity",
        "18 - GAG Minimum per pupil Funding Level": "Min Per Pupil",
        "19 - GAG Minimum Funding Guarantee": "MFG",
        "20 - GAG Funding statement adjustment": "Adjustment",
    }
    secondary_mapping = {
        "01 - GAG AWPU/Basic Entitlement KS3": "Basic Entitlement - KS3",
        "02 - GAG AWPU/Basic Entitlement KS4": "Basic Entitlement - KS4",
        "03 - GAG Deprivation Secondary IDACI Band A": "Secondary IDACI Band A",
        "04 - GAG Deprivation Secondary IDACI Band B": "Secondary IDACI Band B",
        "05 - GAG Deprivation Secondary IDACI Band C": "Secondary IDACI Band C",
        "06 - GAG Deprivation Secondary IDACI Band D": "Secondary IDACI Band D",
        "07 - GAG Deprivation Secondary IDACI Band E": "Secondary IDACI Band E",
        "08 - GAG Deprivation Secondary IDACI Band F": "Secondary IDACI Band F",
        "09 - GAG Deprivation Secondary FSM": "Secondary FSM",
        "10 - GAG Deprivation Secondary FSM6": "Secondary FSM6",
        "11 - GAG Prior Attainment Secondary": "Secondary Low Prior Attainment",
        "12 - GAG EAL Secondary": "Secondary EAL",
        "13 - GAG Mobility Secondary": "Secondary Mobility",
        "14 - GAG London Fringe": "London Fringe",
        "15 - GAG Lump Sum Secondary": "Secondary Lump Sum",
        "16 - GAG PFI": "PFI",
        "17 - GAG Split Sites": "Split Sites",
        "18 - GAG Sparsity": "Sparsity",
        "19 - GAG Minimum per pupil Funding Level": "Min Per Pupil",
        "20 - GAG Minimum Funding Guarantee": "MFG",
        "21 - GAG Funding statement adjustment": "Adjustment",
    }
    allthrough_mapping = {**primary_mapping, **secondary_mapping}
    post16_mapping = {
        "01 - GAG Post 16 Core Programme Funding": "Core Programme Funding",
        "02 - GAG Post 16 Condition of funding Adjustment": "Condition of Funding Adjustment",
        "03 - GAG Post 16 Advanced Maths premium": "Advanced Maths Premium",
        "04 - GAG Post 16 Core maths premium": "Core Maths Premium",
        "05- GAG Post 16 High value courses premium": "High Value Courses Premium",
        "06 - GAG Post 16 Student financial support": "Student Financial Support",
    }
    HN_PRE16_DESCRIPTION = "Pre 16 High Needs"
    HN_POST16_DESCRIPTION = "Post 16 High Needs"


# Reverse mappings: PDF field name -> IMP Description
PRIMARY_REVERSE = {v: k for k, v in primary_mapping.items()}
SECONDARY_REVERSE = {v: k for k, v in secondary_mapping.items()}
ALLTHROUGH_REVERSE = {v: k for k, v in allthrough_mapping.items()}
POST16_REVERSE = {v: k for k, v in post16_mapping.items()}


class FundingStatementProcessor:
    """Process GAG funding statement PDFs and extract funding data."""

    # Pre-16 funding line patterns (regex patterns to match in PDF text)
    PRE16_PATTERNS = {
        # Primary patterns
        "Basic Entitlement - Primary": [
            r"Basic Entitlement.*?Primary.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Primary Basic Entitlement.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"AWPU Primary.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Primary IDACI Band A": [r"Primary IDACI Band A.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary IDACI Band B": [r"Primary IDACI Band B.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary IDACI Band C": [r"Primary IDACI Band C.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary IDACI Band D": [r"Primary IDACI Band D.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary IDACI Band E": [r"Primary IDACI Band E.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary IDACI Band F": [r"Primary IDACI Band F.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary FSM": [r"Primary FSM(?!\d|6).*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary FSM6": [r"Primary FSM6.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary Low Prior Attainment": [
            r"Primary Low Prior Attainment.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Primary Prior Attainment.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Primary EAL": [r"Primary EAL.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary Mobility": [r"Primary Mobility.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Primary Lump Sum": [r"Primary Lump Sum.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        # Secondary patterns
        "Basic Entitlement - KS3": [
            r"Basic Entitlement.*?KS3.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"KS3 Basic Entitlement.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"AWPU KS3.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Basic Entitlement - KS4": [
            r"Basic Entitlement.*?KS4.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"KS4 Basic Entitlement.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"AWPU KS4.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Secondary IDACI Band A": [r"Secondary IDACI Band A.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary IDACI Band B": [r"Secondary IDACI Band B.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary IDACI Band C": [r"Secondary IDACI Band C.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary IDACI Band D": [r"Secondary IDACI Band D.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary IDACI Band E": [r"Secondary IDACI Band E.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary IDACI Band F": [r"Secondary IDACI Band F.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary FSM": [r"Secondary FSM(?!\d|6).*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary FSM6": [r"Secondary FSM6.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary Low Prior Attainment": [
            r"Secondary Low Prior Attainment.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Secondary Prior Attainment.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Secondary EAL": [r"Secondary EAL.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary Mobility": [r"Secondary Mobility.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Secondary Lump Sum": [r"Secondary Lump Sum.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        # Shared patterns
        "London Fringe": [r"London Fringe.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "PFI": [r"PFI.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Split Sites": [r"Split Sites.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Sparsity": [r"Sparsity.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"],
        "Min Per Pupil": [
            r"Minimum per pupil.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Min Per Pupil.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "MFG": [
            r"Minimum Funding Guarantee.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"MFG.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Adjustment": [
            r"(?<!Condition of )Funding statement adjustment.*?(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Adjustment(?! for condition).*?(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "High Needs Pre-16": [
            r"High Needs.*?Pre.?16.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Pre.?16 High Needs.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
    }

    # Post-16 funding line patterns
    POST16_PATTERNS = {
        "Core Programme Funding": [
            r"Core Programme Funding.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Programme funding.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Condition of Funding Adjustment": [
            r"Condition of Funding Adjustment.*?(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Condition of funding.*?(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Advanced Maths Premium": [
            r"Advanced Maths Premium.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Adv Maths.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Core Maths Premium": [
            r"Core Maths Premium.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Core maths.*?premium.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "High Value Courses Premium": [
            r"High Value Courses Premium.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"High value.*?premium.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "High Needs Post-16": [
            r"High Needs.*?Post.?16.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Post.?16 High Needs.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
        "Student Financial Support": [
            r"Student Financial Support.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Financial support.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"Bursary.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        ],
    }

    # Total allocation pattern
    TOTAL_PATTERN = r"Total\s+(?:Allocation|funding).*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"

    def __init__(self, school_codes_df: pd.DataFrame = None):
        """
        Initialize funding processor.

        Args:
            school_codes_df: DataFrame with school codes (columns: SchoolCode, Title, SchoolType)
        """
        self.school_codes_df = school_codes_df
        self.pre16_data = {}  # school_code -> {field: value}
        self.post16_data = {}  # school_code -> {field: value}
        self.unextractable = []
        self.processing_log = []

    def log(self, message: str):
        """Add to processing log."""
        self.processing_log.append(message)

    def match_school(self, school_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Match school name to school code.

        Returns:
            Tuple of (school_code, school_type)
        """
        if not school_name or self.school_codes_df is None:
            return None, None

        school_name_clean = school_name.upper().replace('_', ' ').strip()
        # Remove common prefixes/suffixes for matching
        school_name_clean = re.sub(r'\s+(ACADEMY|SCHOOL|PRIMARY|SECONDARY|COLLEGE)\s*$', '', school_name_clean)

        for _, row in self.school_codes_df.iterrows():
            title = str(row.get('Title', '')).upper().replace('_', ' ').strip()
            if not title or title in ['DEFAULT', 'CENTRAL', 'NAN']:
                continue

            school_code = row.get('SchoolCode', '')
            school_type = str(row.get('SchoolType', 'PRIMARY')).upper()

            # Exact match
            if school_name_clean == title:
                return school_code, school_type

            # Remove suffixes from title too
            title_clean = re.sub(r'\s+(ACADEMY|SCHOOL|PRIMARY|SECONDARY|COLLEGE)\s*$', '', title)
            if school_name_clean == title_clean:
                return school_code, school_type

            # Partial match
            if school_name_clean in title or title in school_name_clean:
                return school_code, school_type

            if school_name_clean in title_clean or title_clean in school_name_clean:
                return school_code, school_type

        return None, None

    def extract_school_name_from_pdf(self, text: str) -> Optional[str]:
        """Extract school name from PDF text."""
        # Common patterns in GAG statements
        patterns = [
            r"Academy:\s*([^\n]+)",
            r"School:\s*([^\n]+)",
            r"Institution:\s*([^\n]+)",
            r"(?:GAG|Funding)\s+(?:Statement|Allocation)\s+(?:for\s+)?([A-Za-z][A-Za-z\s]+(?:Academy|School|College))",
            r"^([A-Za-z][A-Za-z\s]+(?:Academy|School|College))",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                if len(name) > 5:  # Reasonable school name length
                    return name

        return None

    def detect_statement_type(self, text: str, filename: str) -> str:
        """
        Detect if this is a Pre-16 or Post-16 funding statement.

        Returns:
            'pre16' or 'post16'
        """
        text_lower = text.lower()
        filename_lower = filename.lower()

        # Check filename first
        if '16-19' in filename_lower or 'post-16' in filename_lower or 'post16' in filename_lower:
            return 'post16'
        if 'pre-16' in filename_lower or 'pre16' in filename_lower or 'gag' in filename_lower:
            return 'pre16'

        # Check content
        post16_indicators = ['16-19', 'post-16', 'sixth form', 'core programme funding', 'student financial support']
        pre16_indicators = ['pre-16', 'basic entitlement', 'idaci band', 'fsm6', 'lump sum']

        post16_count = sum(1 for ind in post16_indicators if ind in text_lower)
        pre16_count = sum(1 for ind in pre16_indicators if ind in text_lower)

        if post16_count > pre16_count:
            return 'post16'
        return 'pre16'

    def parse_amount(self, amount_str: str) -> float:
        """Parse currency amount string to float."""
        if not amount_str:
            return 0.0
        # Remove currency symbols and commas
        cleaned = re.sub(r'[£$,\s]', '', str(amount_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def extract_pre16_data(self, text: str) -> Dict[str, float]:
        """Extract Pre-16 funding data from PDF text."""
        data = {}

        for field_name, patterns in self.PRE16_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = self.parse_amount(match.group(1))
                    if value > 0 or field_name == "Adjustment":  # Adjustment can be negative
                        data[field_name] = value
                        break

        # Extract total allocation
        total_match = re.search(self.TOTAL_PATTERN, text, re.IGNORECASE)
        if total_match:
            data["Total Allocation"] = self.parse_amount(total_match.group(1))

        return data

    def extract_post16_data(self, text: str) -> Dict[str, float]:
        """Extract Post-16 funding data from PDF text."""
        data = {}

        for field_name, patterns in self.POST16_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = self.parse_amount(match.group(1))
                    if value > 0 or field_name == "Condition of Funding Adjustment":
                        data[field_name] = value
                        break

        # Extract total allocation
        total_match = re.search(self.TOTAL_PATTERN, text, re.IGNORECASE)
        if total_match:
            data["Total Allocation"] = self.parse_amount(total_match.group(1))

        return data

    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a single GAG funding PDF.

        Returns:
            Dict with extracted data and metadata
        """
        if not PDF_AVAILABLE:
            return {'success': False, 'reason': 'PDF support not installed (pdfplumber)'}

        text = ""
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            return {'success': False, 'reason': f'PDF read error: {str(e)}'}

        if len(text.strip()) < 100:
            return {'success': False, 'reason': 'Could not extract text from PDF'}

        # Extract school name and match to code
        school_name = self.extract_school_name_from_pdf(text)
        school_code, school_type = self.match_school(school_name)

        # Detect statement type
        statement_type = self.detect_statement_type(text, pdf_path.name)

        # Extract funding data
        if statement_type == 'pre16':
            funding_data = self.extract_pre16_data(text)
        else:
            funding_data = self.extract_post16_data(text)

        if not funding_data:
            return {
                'success': False,
                'reason': 'No funding data extracted',
                'school_name': school_name,
                'school_code': school_code,
                'statement_type': statement_type
            }

        return {
            'success': school_code is not None,
            'school_name': school_name,
            'school_code': school_code,
            'school_type': school_type,
            'statement_type': statement_type,
            'funding_data': funding_data,
            'source_file': pdf_path.name
        }

    def process_funding_file(self, filepath: Path):
        """Process a single funding statement file."""
        filename = filepath.name
        ext = filepath.suffix.lower()

        self.log(f"Processing: {filename}")

        if ext != '.pdf':
            self.unextractable.append({
                'School Code': '',
                'Document Name': filename,
                'Expected School': '',
                'Statement Type': '',
                'Reason': f'Unsupported file type: {ext}'
            })
            self.log(f"  FAILED: Unsupported file type: {ext}")
            return

        result = self.process_pdf(filepath)

        if not result.get('success'):
            self.unextractable.append({
                'School Code': result.get('school_code', ''),
                'Document Name': filename,
                'Expected School': result.get('school_name', ''),
                'Statement Type': result.get('statement_type', ''),
                'Reason': result.get('reason', 'Unknown error')
            })
            self.log(f"  FAILED: {result.get('reason', 'Unknown error')}")
            return

        school_code = result['school_code']
        statement_type = result['statement_type']
        funding_data = result['funding_data']
        source_file = result['source_file']

        # Store data by school
        if statement_type == 'pre16':
            if school_code not in self.pre16_data:
                self.pre16_data[school_code] = {'_source': source_file, '_school_type': result.get('school_type', 'PRIMARY')}
            self.pre16_data[school_code].update(funding_data)
        else:
            if school_code not in self.post16_data:
                self.post16_data[school_code] = {'_source': source_file}
            self.post16_data[school_code].update(funding_data)

        self.log(f"  SUCCESS: {school_code} ({statement_type}) - {len(funding_data)} values extracted")

    def get_mapping_for_school_type(self, school_type: str) -> dict:
        """Get the appropriate reverse mapping based on school type."""
        school_type_upper = str(school_type).upper()
        if 'ALLTHROUGH' in school_type_upper or 'ALL-THROUGH' in school_type_upper:
            return ALLTHROUGH_REVERSE
        elif 'SECONDARY' in school_type_upper:
            return SECONDARY_REVERSE
        elif 'PRIMARY' in school_type_upper:
            return PRIMARY_REVERSE
        else:
            return PRIMARY_REVERSE

    def create_funding_updates(self) -> pd.DataFrame:
        """
        Create DataFrame of funding updates for the Funding tab.

        Returns:
            DataFrame with columns: SchoolCode, Description, YearValue, Source, Validated
        """
        rows = []

        # Process Pre-16 data
        for school_code, data in self.pre16_data.items():
            source_file = data.get('_source', '')
            school_type = data.get('_school_type', 'PRIMARY')
            reverse_mapping = self.get_mapping_for_school_type(school_type)

            for field_name, value in data.items():
                if field_name.startswith('_') or field_name == 'Total Allocation':
                    continue
                if value == 0:
                    continue

                # Map PDF field name to IMP Description
                imp_description = reverse_mapping.get(field_name)
                if not imp_description:
                    # Check if it's High Needs
                    if field_name == "High Needs Pre-16":
                        imp_description = HN_PRE16_DESCRIPTION
                    else:
                        continue  # Skip unmapped fields

                rows.append({
                    'SchoolCode': school_code,
                    'Description': imp_description,
                    'YearValue': value,
                    'Source': source_file,
                    'StatementType': 'Pre-16'
                })

        # Process Post-16 data
        for school_code, data in self.post16_data.items():
            source_file = data.get('_source', '')

            for field_name, value in data.items():
                if field_name.startswith('_') or field_name == 'Total Allocation':
                    continue
                if value == 0:
                    continue

                # Map PDF field name to IMP Description
                imp_description = POST16_REVERSE.get(field_name)
                if not imp_description:
                    # Check if it's High Needs
                    if field_name == "High Needs Post-16":
                        imp_description = HN_POST16_DESCRIPTION
                    else:
                        continue

                rows.append({
                    'SchoolCode': school_code,
                    'Description': imp_description,
                    'YearValue': value,
                    'Source': source_file,
                    'StatementType': 'Post-16'
                })

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        return df

    def validate_totals(self) -> List[Dict]:
        """
        Validate that extracted values sum to Total Allocation.

        Returns:
            List of validation results per school
        """
        validation_results = []

        # Validate Pre-16 totals
        for school_code, data in self.pre16_data.items():
            expected_total = data.get('Total Allocation', 0)
            if expected_total == 0:
                continue

            # Sum all component values
            calculated_total = sum(
                v for k, v in data.items()
                if not k.startswith('_') and k != 'Total Allocation'
            )

            diff = abs(expected_total - calculated_total)
            status = "PASS" if diff < 1 else "FAIL"

            validation_results.append({
                'SchoolCode': school_code,
                'Type': 'Pre-16 GAG',
                'Expected': expected_total,
                'Calculated': calculated_total,
                'Difference': diff,
                'Status': status
            })

        # Validate Post-16 totals
        for school_code, data in self.post16_data.items():
            expected_total = data.get('Total Allocation', 0)
            if expected_total == 0:
                continue

            calculated_total = sum(
                v for k, v in data.items()
                if not k.startswith('_') and k != 'Total Allocation'
            )

            diff = abs(expected_total - calculated_total)
            status = "PASS" if diff < 2 else "FAIL"  # Slightly higher tolerance for Post-16

            validation_results.append({
                'SchoolCode': school_code,
                'Type': 'Post-16',
                'Expected': expected_total,
                'Calculated': calculated_total,
                'Difference': diff,
                'Status': status
            })

        return validation_results

    def process_folder(self, funding_folder: Path) -> Dict[str, Any]:
        """
        Process all funding PDFs in a folder.

        Args:
            funding_folder: Path to folder containing GAG funding PDFs

        Returns:
            Dict with:
            - funding_updates: DataFrame for Funding tab updates
            - validation_results: List of validation results
            - unextractable: List of files that couldn't be processed
            - summary: Processing summary
            - log: Processing log
        """
        self.pre16_data = {}
        self.post16_data = {}
        self.unextractable = []
        self.processing_log = []

        self.log("=" * 50)
        self.log("FUNDING STATEMENT PROCESSOR - STARTING")
        self.log("=" * 50)

        if not funding_folder.exists():
            self.log(f"Folder not found: {funding_folder}")
            return {
                'success': False,
                'funding_updates': pd.DataFrame(),
                'validation_results': [],
                'unextractable': [],
                'summary': {'error': 'Folder not found'},
                'log': self.processing_log
            }

        # Find PDF files
        pdf_files = list(funding_folder.glob('*.pdf'))
        pdf_files.extend(funding_folder.glob('**/*.pdf'))
        pdf_files = list(set(pdf_files))  # Remove duplicates

        self.log(f"Found {len(pdf_files)} PDF files")

        for filepath in pdf_files:
            if filepath.name.startswith('~$'):
                continue
            self.process_funding_file(filepath)

        # Create outputs
        funding_df = self.create_funding_updates()
        validation_results = self.validate_totals()

        self.log("\n" + "=" * 50)
        self.log("FUNDING PROCESSING COMPLETE")
        self.log(f"  Pre-16 schools: {len(self.pre16_data)}")
        self.log(f"  Post-16 schools: {len(self.post16_data)}")
        self.log(f"  Funding rows: {len(funding_df)}")
        self.log(f"  Unextractable files: {len(self.unextractable)}")
        self.log("=" * 50)

        return {
            'success': True,
            'funding_updates': funding_df,
            'validation_results': validation_results,
            'unextractable': self.unextractable,
            'summary': {
                'pre16_schools': len(self.pre16_data),
                'post16_schools': len(self.post16_data),
                'funding_rows': len(funding_df),
                'failed_count': len(self.unextractable),
                'total_processed': len(pdf_files),
                'validation_passed': sum(1 for v in validation_results if v['Status'] == 'PASS'),
                'validation_failed': sum(1 for v in validation_results if v['Status'] == 'FAIL'),
            },
            'log': self.processing_log
        }


def run_funding_processor(
    funding_folder: Path,
    school_codes_df: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Run funding processor as a separate step.

    Args:
        funding_folder: Path to folder with GAG funding PDFs
        school_codes_df: DataFrame with school codes for matching

    Returns:
        Processing result with:
        - funding_updates: DataFrame with funding values to update
        - validation_results: List of validation results
        - unextractable: List of files that couldn't be processed
        - summary: Processing summary
        - log: Processing log messages
    """
    processor = FundingStatementProcessor(school_codes_df=school_codes_df)
    return processor.process_folder(funding_folder)


def get_funding_files(folder: Path) -> List[Path]:
    """Get list of funding PDF files in a folder."""
    files = list(folder.glob('*.pdf'))
    return [f for f in files if not f.name.startswith('~$')]
