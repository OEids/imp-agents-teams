"""
Master Data Import Orchestrator
Coordinates data import across all strand teams (S1, S2, S3)
Detects data type and routes to appropriate strand agent

Mission: Convert ALL customer data into standardized CSV format
See: MY_MISSION_GUIDE.txt for complete understanding
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
import importlib.util
import pandas as pd

class MasterDataImportOrchestrator:
    """
    Routes customer data to the correct strand team agent
    Coordinates multi-strand imports if needed
    """
    
    def __init__(self, knowledge_base_path: str = None):
        """Initialize orchestrator with knowledge base path"""
        if knowledge_base_path is None:
            knowledge_base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.knowledge_base_path = knowledge_base_path
        
        # Load mission guide FIRST
        self._load_mission_guide()
        
        self.agents = {}
        self._load_agents()
    
    def _load_mission_guide(self):
        """Load mission guide to understand standardization goals"""
        guide_path = os.path.join(self.knowledge_base_path, 'MY_MISSION_GUIDE.txt')
        if os.path.exists(guide_path):
            try:
                with open(guide_path, 'r') as f:
                    self.mission_guide = f.read()
                    # Validate core principle
                    if 'CSV IS the goal' in self.mission_guide:
                        print("✓ Orchestrator: Mission understood - CSV standardization is the goal")
                    else:
                        print("⚠ Warning: Mission guide doesn't contain core principle")
            except Exception as e:
                print(f"⚠ Warning: Could not read mission guide: {str(e)}")
                self.mission_guide = None
        else:
            print("⚠ Warning: MY_MISSION_GUIDE.txt not found")
            self.mission_guide = None
    
    def _load_agents(self):
        """Dynamically load all strand agents"""
        strand_paths = {
            'S1': os.path.join(self.knowledge_base_path, 'S1'),
            'S2': os.path.join(self.knowledge_base_path, 'S2'),
            'S3': os.path.join(self.knowledge_base_path, 'S3')
        }
        
        for strand_name, strand_path in strand_paths.items():
            agent_file = os.path.join(strand_path, f'{strand_name}_DataImportAgent.py')
            if os.path.exists(agent_file):
                try:
                    spec = importlib.util.spec_from_file_location(f"{strand_name}_agent", agent_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Get the agent class
                    if strand_name == 'S1':
                        agent_class = module.S1DataImportAgent
                    elif strand_name == 'S2':
                        agent_class = module.S2DataImportAgent
                    elif strand_name == 'S3':
                        agent_class = module.S3DataImportAgent
                    
                    self.agents[strand_name] = {
                        'class': agent_class,
                        'path': strand_path,
                        'module': module
                    }
                    print(f"✓ Loaded {strand_name} agent")
                except Exception as e:
                    print(f"✗ Failed to load {strand_name} agent: {str(e)}")
    
    def detect_strand(self, data: pd.DataFrame) -> Optional[str]:
        """
        Analyze data to determine which strand it belongs to
        Returns: 'S1', 'S2', 'S3', or None
        """
        columns = set(data.columns)
        lower_cols = [col.lower() for col in columns]
        
        # S1 indicators: Schools, Departments, Finance, Funds, Activities
        s1_indicators = ['school', 'department', 'financeCode', 'fund', 'activity', 
                        'ledger', 'customgrouping', 'hub', 'localauthority']
        
        # S2 indicators: Staff, Roles, Pay, Contracts, Equated Weeks
        s2_indicators = ['staff', 'role', 'payroll', 'contract', 'equated', 'salary', 
                        'pension', 'teacher', 'support']
        
        # S3 indicators: Grants, Budget, Planning, Scenario, Savings, Priority
        s3_indicators = ['grant', 'allocation', 'budget', 'planning', 'scenario', 'saving', 
                        'priority', 'phase', 'calculation']
        
        s1_score = sum(1 for col in lower_cols if any(indicator in col for indicator in s1_indicators))
        s2_score = sum(1 for col in lower_cols if any(indicator in col for indicator in s2_indicators))
        s3_score = sum(1 for col in lower_cols if any(indicator in col for indicator in s3_indicators))
        
        # Determine best match
        scores = {'S1': s1_score, 'S2': s2_score, 'S3': s3_score}
        max_strand = max(scores, key=scores.get)
        
        if scores[max_strand] > 0:
            return max_strand
        return None
    
    def process_customer_data(self, file_path: str, force_strand: str = None) -> Dict:
        """
        Main entry point: Process customer data through appropriate strand agent
        
        MISSION: Convert customer data to standardized CSV format (not for templates)
        See MY_MISSION_GUIDE.txt for context
        
        Args:
            file_path: Path to customer data file (CSV, Excel, etc.)
            force_strand: Force processing through specific strand (S1, S2, or S3)
        
        Returns:
            Combined status report
        """
        result = {
            'success': False,
            'input_file': file_path,
            'detected_strand': None,
            'processing_strand': None,
            'strand_results': {},
            'errors': []
        }
        
        try:
            # Load customer data
            if file_path.endswith('.csv'):
                customer_data = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                customer_data = pd.read_excel(file_path)
            else:
                result['errors'].append("Unsupported file format. Use CSV or Excel.")
                return result
            
            result['input_rows'] = len(customer_data)
            
            # Detect appropriate strand
            detected_strand = force_strand or self.detect_strand(customer_data)
            result['detected_strand'] = detected_strand
            
            if not detected_strand or detected_strand not in self.agents:
                result['errors'].append(f"Could not determine appropriate strand or strand not available")
                return result
            
            result['processing_strand'] = detected_strand
            
            # Process through appropriate agent
            agent_info = self.agents[detected_strand]
            agent = agent_info['class'](agent_info['path'])
            strand_result = agent.process_customer_data(customer_data)
            result['strand_results'][detected_strand] = strand_result
            result['success'] = strand_result['success']
            
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def list_available_import_formats(self) -> Dict:
        """List all available CSV import formats per strand"""
        formats = {}
        for strand_name, agent_info in self.agents.items():
            agent_class = agent_info['class']
            # Create dummy instance to list schemas
            try:
                dummy_agent = agent_class(agent_info['path'])
                formats[strand_name] = list(dummy_agent.csv_schemas.keys())
            except:
                formats[strand_name] = []
        return formats
    
    def generate_template(self, strand: str, data_type: str, num_rows: int = 5) -> pd.DataFrame:
        """Generate a template CSV for specific data type"""
        if strand not in self.agents:
            raise ValueError(f"Strand {strand} not available")
        
        agent_class = self.agents[strand]['class']
        agent = agent_class(self.agents[strand]['path'])
        
        if data_type not in agent.csv_schemas:
            raise ValueError(f"Data type {data_type} not available for {strand}")
        
        columns = agent.csv_schemas[data_type]
        template_data = {}
        
        for col in columns:
            if 'Enabled' in col or 'Completed' in col:
                template_data[col] = [True] * num_rows
            elif 'Date' in col:
                template_data[col] = ['YYYY-MM-DD'] * num_rows
            elif 'Code' in col:
                template_data[col] = [f'{col}_001', f'{col}_002', f'{col}_003', 
                                     f'{col}_004', f'{col}_005'][:num_rows]
            elif 'Amount' in col or 'Rate' in col or 'Number' in col:
                template_data[col] = [0.0] * num_rows
            else:
                template_data[col] = [''] * num_rows
        
        return pd.DataFrame(template_data)


def print_usage():
    """Print usage instructions"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         KNOWLEDGE BASE DATA IMPORT SYSTEM                                   ║
║         Multi-Strand Intelligent Data Import                               ║
╚════════════════════════════════════════════════════════════════════════════╝

QUICK START:
───────────

1. IMPORT CUSTOMER DATA (Any Format):
   
   from master_orchestrator import MasterDataImportOrchestrator
   
   orchestrator = MasterDataImportOrchestrator()
   result = orchestrator.process_customer_data('path/to/customer_data.csv')
   print(result)

2. FORCE SPECIFIC STRAND:
   
   result = orchestrator.process_customer_data('data.csv', force_strand='S2')

3. LIST AVAILABLE FORMATS:
   
   formats = orchestrator.list_available_import_formats()
   for strand, types in formats.items():
       print(f"{strand}: {', '.join(types)}")

4. GENERATE TEMPLATE:
   
   template = orchestrator.generate_template('S1', 'Schools', num_rows=10)
   template.to_csv('schools_template.csv', index=False)

WORKFLOW:
─────────

1. Customer provides data in ANY format (CSV, Excel, custom spreadsheet)
2. System detects data type and appropriate strand
3. Agent maps data to correct CSV import format
4. Import files are updated with new customer data
5. Data is ready for template workbook import

SUPPORTED STRANDS:
──────────────────

S1 - School Data Management
   - Schools, Departments, Funds, Activities, Users
   - Finance Codes, Ledgers, Groupings
   
S2 - Staff Management
   - Staff Roles, Role Groups, Contracts
   - Pay Scales, Pensions, Equated Weeks
   - Staff Members
   
S3 - Grants & Planning
   - Grants, Funding Allocations, Budget Scenarios
   - Savings, Priorities, Planning Data
   - Calculations, Adjustments, Phases

ERROR HANDLING:
────────────────

If data format is not recognized:
- Check column naming conventions
- Ensure required identifier columns exist (Code, Title, etc.)
- See templates for expected format

SUPPORT:
─────────

For troubleshooting, check the agent logs for detailed mapping information.
Each agent tracks column mapping and data transformation steps.
""")


if __name__ == "__main__":
    print_usage()
    
    # Example: Initialize orchestrator
    print("\nInitializing Orchestrator...")
    orchestrator = MasterDataImportOrchestrator()
    
    # Show available formats
    print("\nAvailable Import Formats:")
    formats = orchestrator.list_available_import_formats()
    for strand, types in formats.items():
        print(f"\n{strand}:")
        for dtype in types:
            print(f"  • {dtype}")
