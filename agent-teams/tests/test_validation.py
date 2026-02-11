"""
Unit tests for validation components.
"""

import pytest
import pandas as pd

from teams.validation import (
    DataValidator, DataComparator, AssumptionTracker,
    ValidationResult, ValidationSeverity
)


class TestDataValidator:
    """Test the DataValidator functionality."""

    def test_validator_initialization(self):
        """Test that DataValidator initializes correctly."""
        validator = DataValidator('S1')
        assert validator.team_id == 'S1'
        assert len(validator.results) == 0

    def test_validate_empty_data(self):
        """Test validation with empty dataframe."""
        validator = DataValidator('S1')
        df = pd.DataFrame()

        validator.validate_all(df)

        # Should have at least one validation result
        assert len(validator.results) > 0
        assert any('empty_data' in r.check_name for r in validator.results)

    def test_validate_good_data(self, sample_s1_data):
        """Test validation with good data."""
        validator = DataValidator('S1')

        validator.validate_all(sample_s1_data)

        assert len(validator.results) > 0
        # Should have mostly passing results
        passed = sum(1 for r in validator.results if r.passed)
        assert passed >= len(validator.results) * 0.7  # At least 70% pass

    def test_validate_duplicate_rows(self):
        """Test validation detects duplicate rows."""
        validator = DataValidator('S1')
        df = pd.DataFrame({
            'col1': ['A', 'A', 'B'],
            'col2': [1, 1, 2]
        })

        validator.validate_all(df)

        duplicate_checks = [r for r in validator.results if 'duplicate' in r.check_name.lower()]
        assert len(duplicate_checks) > 0

    def test_validate_null_values(self):
        """Test validation detects null values."""
        validator = DataValidator('S1')
        df = pd.DataFrame({
            'col1': ['A', None, 'B'],
            'col2': [1, 2, None]
        })

        validator.validate_all(df)

        null_checks = [r for r in validator.results if 'null' in r.check_name.lower()]
        assert len(null_checks) > 0

    def test_get_summary(self, sample_s1_data):
        """Test getting validation summary."""
        validator = DataValidator('S1')
        validator.validate_all(sample_s1_data)

        summary = validator.get_summary()

        assert 'total_checks' in summary
        assert 'passed' in summary
        assert 'errors' in summary
        assert summary['total_checks'] == len(validator.results)


class TestDataComparator:
    """Test the DataComparator functionality."""

    def test_comparator_initialization(self):
        """Test that DataComparator initializes correctly."""
        comparator = DataComparator()
        assert comparator.original_data is None

    def test_capture_original(self, sample_s1_data):
        """Test capturing original data."""
        comparator = DataComparator()
        comparator.capture_original(sample_s1_data)

        assert comparator.original_data is not None
        assert len(comparator.original_data) == len(sample_s1_data)

    def test_compare_identical_data(self, sample_s1_data):
        """Test comparing identical data."""
        comparator = DataComparator()
        comparator.capture_original(sample_s1_data)

        result = comparator.compare(sample_s1_data)

        assert 'original' in result
        assert 'new' in result
        assert result['original']['rows'] == result['new']['rows']

    def test_compare_modified_data(self, sample_s1_data):
        """Test comparing modified data."""
        comparator = DataComparator()
        comparator.capture_original(sample_s1_data)

        # Modify data
        modified = sample_s1_data.drop(0)  # Remove first row
        modified['new_col'] = 'test'  # Add column

        result = comparator.compare(modified)

        assert result['original']['rows'] == len(sample_s1_data)
        assert result['new']['rows'] == len(modified)
        assert result['new']['columns'] == len(modified.columns)


class TestAssumptionTracker:
    """Test the AssumptionTracker functionality."""

    def test_tracker_initialization(self):
        """Test that AssumptionTracker initializes correctly."""
        tracker = AssumptionTracker('S1')
        assert tracker.team_id == 'S1'
        assert len(tracker.assumptions) == 0

    def test_add_assumption(self):
        """Test adding an assumption."""
        tracker = AssumptionTracker('S1')

        tracker.add(
            category='test',
            description='Test assumption',
            reason='For testing',
            impact='None',
            confidence='high',
            affected_records=5
        )

        assert len(tracker.assumptions) == 1
        assumption = tracker.assumptions[0]
        assert assumption.category == 'test'
        assert assumption.confidence == 'high'

    def test_get_all_assumptions(self):
        """Test getting all assumptions."""
        tracker = AssumptionTracker('S1')

        tracker.add(category='test1', description='Test 1', reason='Test', impact='None', confidence='high')
        tracker.add(category='test2', description='Test 2', reason='Test', impact='None', confidence='low')

        all_assumptions = tracker.get_all()

        assert len(all_assumptions) == 2
        assert all('category' in a for a in all_assumptions)

    def test_get_low_confidence(self):
        """Test getting low confidence assumptions."""
        tracker = AssumptionTracker('S1')

        tracker.add(category='high', description='High conf', reason='Test', impact='None', confidence='high')
        tracker.add(category='low', description='Low conf', reason='Test', impact='None', confidence='low')
        tracker.add(category='medium', description='Med conf', reason='Test', impact='None', confidence='medium')

        low_conf = tracker.get_low_confidence()

        assert len(low_conf) == 1
        assert low_conf[0].confidence == 'low'

    def test_mapping_assumption(self):
        """Test adding mapping assumption."""
        tracker = AssumptionTracker('S1')

        tracker.add_mapping_assumption(
            source_col='old_name',
            target_col='new_name',
            mapping_type='renamed'
        )

        assert len(tracker.assumptions) == 1
        assumption = tracker.assumptions[0]
        assert 'old_name' in assumption.description
        assert 'new_name' in assumption.description

    def test_type_conversion_assumption(self):
        """Test adding type conversion assumption."""
        tracker = AssumptionTracker('S1')

        tracker.add_type_conversion_assumption(
            column='test_col',
            from_type='str',
            to_type='int',
            count=10
        )

        assert len(tracker.assumptions) == 1
        assumption = tracker.assumptions[0]
        assert 'test_col' in assumption.description
        assert 'str' in assumption.description
        assert 'int' in assumption.description

    def test_format_assumption(self):
        """Test adding format assumption."""
        tracker = AssumptionTracker('S1')

        tracker.add_format_assumption(
            column='test_col',
            format_applied='uppercase',
            count=5
        )

        assert len(tracker.assumptions) == 1
        assumption = tracker.assumptions[0]
        assert 'test_col' in assumption.description
        assert 'uppercase' in assumption.description

    def test_duplicate_handling_assumption(self):
        """Test adding duplicate handling assumption."""
        tracker = AssumptionTracker('S1')

        tracker.add_duplicate_handling_assumption(
            strategy='keep_first',
            count=3
        )

        assert len(tracker.assumptions) == 1
        assumption = tracker.assumptions[0]
        assert 'duplicate' in assumption.description.lower()
        assert '3' in assumption.description
