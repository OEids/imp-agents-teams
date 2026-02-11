"""
Pytest configuration and fixtures for agent teams testing.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def mock_team_config():
    """Mock team configuration for testing."""
    return {
        'name': 'Test Team',
        'focus': 'Test data processing',
        'data_dir': Path('/tmp/test_data'),
        'description': 'Test team for unit testing'
    }


@pytest.fixture
def mock_template_path(tmp_path):
    """Mock template path for testing."""
    template = tmp_path / 'template.xlsx'
    # Create a minimal template file
    df = pd.DataFrame({
        'code': ['001', '002'],
        'title': ['Test Item 1', 'Test Item 2'],
        'type': ['A', 'B']
    })
    df.to_excel(template, index=False)
    return template


@pytest.fixture
def sample_s1_data():
    """Sample S1 (Structure) data for testing."""
    return pd.DataFrame({
        'Code': ['001', '002', '003'],
        'Title': ['Finance Department', 'IT Department', 'HR Department'],
        'Type': ['DEPT', 'DEPT', 'DEPT'],
        'Parent Code': ['', '', ''],
        'Active': ['Y', 'Y', 'Y'],
        'Grouping Code': ['FIN', 'IT', 'HR']
    })


@pytest.fixture
def sample_s2_data():
    """Sample S2 (Staff) data for testing."""
    return pd.DataFrame({
        'Payroll Number': ['001', '002', '003'],
        'Last Name': ['Smith', 'Johnson', 'Williams'],
        'First Name': ['John', 'Jane', 'Bob'],
        'Date of Birth': ['1980-01-01', '1985-05-15', '1990-12-31'],
        'Gender': ['M', 'F', 'M'],
        'Service Start Date': ['2020-01-01', '2019-06-01', '2021-03-15'],
        'School Code': ['SCH001', 'SCH002', 'SCH003'],
        'Job Title': ['Teacher', 'Teaching Assistant', 'Head Teacher'],
        'Finance Code': ['1001', '1002', '1003'],
        'Weekly Hours': [37.5, 30.0, 40.0],
        'Weekly FTE': [1.0, 0.8, 1.0],
        'Annual Salary': [35000, 25000, 45000],
        'Contract Type': ['Permanent', 'Permanent', 'Permanent'],
        'Pension Scheme': ['TPS', 'TPS', 'TPS']
    })


@pytest.fixture
def sample_s3_data():
    """Sample S3 (Financial) data for testing."""
    return pd.DataFrame({
        'Fund Code': ['FUND001', 'FUND002'],
        'Activity Code': ['ACT001', 'ACT002'],
        'Ledger Code': ['LED001', 'LED002'],
        'Amount': [10000.50, -5000.25],
        'Period': ['2024-01', '2024-01'],
        'Scenario': ['Budget', 'Budget'],
        'Pupil Numbers': [150, 200],
        'Funding Rate': [65.50, 45.25]
    })


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for testing."""
    return tmp_path


@pytest.fixture
def mock_validator():
    """Mock data validator for testing."""
    validator = Mock()
    validator.results = []
    validator.get_summary.return_value = {
        'total_checks': 5,
        'passed': 4,
        'errors': 1,
        'critical_issues': 0
    }
    return validator


@pytest.fixture
def mock_comparator():
    """Mock data comparator for testing."""
    comparator = Mock()
    comparator.compare.return_value = {
        'original': {'rows': 10, 'columns': 5, 'null_count': 2},
        'new': {'rows': 9, 'columns': 6, 'null_count': 1},
        'changes': {
            'rows_removed': 1,
            'columns_added': 1,
            'nulls_reduced': 1
        }
    }
    return comparator


@pytest.fixture
def mock_assumptions():
    """Mock assumption tracker for testing."""
    assumptions = Mock()
    assumptions.assumptions = [
        Mock(category='test', confidence='high', description='Test assumption')
    ]
    assumptions.get_low_confidence.return_value = []
    assumptions.get_all.return_value = [
        {
            'category': 'test',
            'confidence': 'high',
            'description': 'Test assumption',
            'reason': 'For testing',
            'impact': 'None',
            'affected_records': 5
        }
    ]
    return assumptions
