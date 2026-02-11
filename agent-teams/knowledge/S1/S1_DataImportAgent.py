"""
S1 Data Import Agent
Recognizes non-template format customer data and maps it to import files
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

# Mission: Convert ALL customer data into standardized CSV format
# See: MY_MISSION_GUIDE.txt for complete understanding

class S1DataImportAgent:
    """
    Agent for importing non-template format data into Strand 1
    Detects data format, locates correct import CSV, and updates template
    """
    
    def __init__(self, strand_folder: str = None):
        """Initialize agent with strand folder path"""
        if strand_folder is None:
            strand_folder = os.path.dirname(os.path.abspath(__file__))
        
        self.strand_folder = strand_folder
        self.import_folder = os.path.join(strand_folder, "import files")
        
        # Load mission guide
        self._load_mission_guide()
        
        self.template_file = self._locate_template()
        self.import_files = self._load_import_files()
        
        # Mission-aligned: These CSVs ARE the standardized format, not intermediate files
        # CSV structure mappings for S1
        self.csv_schemas = {
            'Activities': ['ActivityCode', 'Title', 'ActivityEnabled'],
            'CustomGroupings': ['CustomGroupingCode', 'Title', 'CustomGroupingEnabled'],
            'Departments': ['ActivityCode', 'DepartmentCode', 'Title', 'AvailableToAllSchools', 
                          'SchoolCodes', 'FundCode', 'LedgerCode', 'DefaultFinanceCode', 'DepartmentEnabled'],
            'Funds': ['FundCode', 'Title', 'FundEnabled'],
            'Ledgers': ['LedgerCode', 'Title', 'LedgerEnabled'],
            'SchoolHubs': ['SchoolHubCode', 'Title', 'SchoolHubEnabled'],
            'SchoolLocalAuthorities': ['SchoolLocalAuthorityCode', 'Title', 'SchoolLocalAuthorityEnabled'],
            'Schools': ['SchoolLocalAuthority', 'SchoolCode', 'SchoolHub', 'SchoolType', 'Title',
                       'LondonWeighting', 'UniqueReferenceNumber', 'TeachingHours', 'SchoolEnabled'],
            'SchoolTypes': ['SchoolTypeCode', 'Title', 'SchoolTypeEnabled'],
            'Users': ['UserName', 'PhoneNumber', 'Email', 'AccessAllSchools', 'AccessAllDepartments',
                     'SchoolCodes', 'DepartmentCodes', 'Administrator', 'ProfileCode', 'Enabled'],
            'FinanceCodes': ['IsBalanceSheet', 'GroupingCode', 'CustomGrouping', 'FinanceCode', 'Title',
                            'AvailableToAllSchools', 'SchoolCodes', 'FinanceCodeTypeCode', 'LedgerCode',
                            'FinanceCodeEnabled', 'BalanceToScenario'],
            'ContractTypes': ['ContractTypeCode', 'Title', 'ContractTypeEnabled'],
            'Genders': ['GenderCode', 'Title', 'GenderEnabled']
        }
    
    def _locate_template(self) -> str:
        """Locate the Strand 1 template Excel file"""
        for file in os.listdir(self.strand_folder):
            if 'Strand 1' in file and 'Standard Workbook' in file and file.endswith('.xlsx'):
                return os.path.join(self.strand_folder, file)
        raise FileNotFoundError("Strand 1 template workbook not found")
    
    def _load_mission_guide(self):
        """Load mission guide to understand standardization goals"""
        guide_path = os.path.join(os.path.dirname(self.strand_folder), 'MY_MISSION_GUIDE.txt')
        if os.path.exists(guide_path):
            try:
                with open(guide_path, 'r') as f:
                    self.mission_guide = f.read()
                    # Validate core principle
                    if 'CSV IS the goal' in self.mission_guide:
                        print("✓ S1 Agent: Mission understood - CSV standardization is the goal")
            except:
                self.mission_guide = None
        else:
            self.mission_guide = None
    
    def _load_import_files(self) -> Dict[str, pd.DataFrame]:
        """Load all import CSV files into memory"""
        import_files = {}
        if os.path.exists(self.import_folder):
            for file in os.listdir(self.import_folder):
                if file.startswith('DEM003') and file.endswith('.csv'):
                    file_path = os.path.join(self.import_folder, file)
                    name = file.replace('DEM003 - ', '').replace('.csv', '')
                    import_files[name] = pd.read_csv(file_path)
        return import_files
    
    def detect_data_format(self, data: pd.DataFrame) -> Tuple[str, bool]:
        """
        Detect if data is in template format or needs mapping
        Returns: (data_type, is_template_format)
        """
        columns = set(data.columns)
        
        # Check against known CSV schemas
        for csv_name, csv_columns in self.csv_schemas.items():
            csv_column_set = set(csv_columns)
            if csv_column_set == columns:
                return (csv_name, True)
            # Check for partial match (likely template format)
            if len(csv_column_set & columns) >= len(csv_columns) * 0.8:
                return (csv_name, True)
        
        return ('Unknown', False)
    
    def locate_import_file(self, data_type: str) -> Optional[str]:
        """Locate the appropriate import CSV file for the data type"""
        for file_name in self.import_files.keys():
            if file_name.lower() == data_type.lower():
                return file_name
        
        # Try fuzzy matching
        for file_name in self.import_files.keys():
            if data_type.lower() in file_name.lower() or file_name.lower() in data_type.lower():
                return file_name
        
        return None
    
    def map_customer_data_to_csv(self, customer_data: pd.DataFrame, 
                                 target_csv: str) -> pd.DataFrame:
        """Map customer data to CSV format"""
        if target_csv not in self.csv_schemas:
            raise ValueError(f"Unknown CSV type: {target_csv}")
        
        target_columns = self.csv_schemas[target_csv]
        mapped_data = pd.DataFrame()
        
        # Intelligent column mapping
        for target_col in target_columns:
            # Try exact match first
            if target_col in customer_data.columns:
                mapped_data[target_col] = customer_data[target_col]
            # Try fuzzy match
            else:
                for cust_col in customer_data.columns:
                    if target_col.lower().replace('code', '').replace('title', '') in \
                       cust_col.lower().replace('code', '').replace('title', ''):
                        mapped_data[target_col] = customer_data[cust_col]
                        break
                else:
                    # Use default value if column not found
                    if 'Code' in target_col:
                        mapped_data[target_col] = ''
                    elif 'Title' in target_col:
                        mapped_data[target_col] = ''
                    elif 'Enabled' in target_col:
                        mapped_data[target_col] = True
                    else:
                        mapped_data[target_col] = ''
        
        return mapped_data
    
    def process_customer_data(self, customer_data: pd.DataFrame) -> Dict:
        """
        Main process: analyze customer data and import it
        Returns: status report
        """
        status = {
            'success': False,
            'data_type': None,
            'is_template_format': False,
            'import_file': None,
            'rows_processed': 0,
            'errors': []
        }
        
        try:
            # Step 1: Detect format
            data_type, is_template = self.detect_data_format(customer_data)
            status['data_type'] = data_type
            status['is_template_format'] = is_template
            
            if is_template:
                status['success'] = True
                status['rows_processed'] = len(customer_data)
                return status
            
            # Step 2: Find import file
            import_file = self.locate_import_file(data_type)
            if not import_file:
                status['errors'].append(f"Could not locate import file for {data_type}")
                return status
            
            status['import_file'] = import_file
            
            # Step 3: Map customer data
            mapped_data = self.map_customer_data_to_csv(customer_data, import_file)
            
            # Step 4: Update import file
            import_path = os.path.join(self.import_folder, f"DEM003 - {import_file}.csv")
            merged_data = pd.concat([self.import_files[import_file], mapped_data], 
                                   ignore_index=True)
            merged_data = merged_data.drop_duplicates(keep='last')
            merged_data.to_csv(import_path, index=False)
            
            status['success'] = True
            status['rows_processed'] = len(mapped_data)
            
        except Exception as e:
            status['errors'].append(str(e))
        
        return status


def import_customer_data(file_path: str, strand_folder: str = None) -> Dict:
    """
    Main entry point: Import customer data from file
    
    Args:
        file_path: Path to customer data file (CSV, Excel, etc.)
        strand_folder: Path to strand folder (defaults to S1)
    
    Returns:
        Status report
    """
    agent = S1DataImportAgent(strand_folder)
    
    # Load customer data
    if file_path.endswith('.csv'):
        customer_data = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        customer_data = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")
    
    # Process
    result = agent.process_customer_data(customer_data)
    
    # Return status
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    # Example usage
    print("S1 Data Import Agent initialized")
    print("Use import_customer_data(file_path) to import customer data")
