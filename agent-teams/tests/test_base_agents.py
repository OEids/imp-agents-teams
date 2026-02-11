"""
Unit tests for base agent classes.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from teams.base import (
    AnalyzeAgent, CleanAgent, TransformAgent, BuildAgent,
    AgentTeam, CheckInReport
)


class TestAnalyzeAgent:
    """Test the AnalyzeAgent functionality."""

    def test_analyze_agent_initialization(self, mock_team_config):
        """Test that AnalyzeAgent initializes correctly."""
        agent = AnalyzeAgent('S1', mock_team_config)
        assert agent.team_id == 'S1'
        assert agent.phase == 'analyze'
        assert agent.data is None

    def test_analyze_no_files(self, mock_team_config, temp_dir):
        """Test analysis when no data files are present."""
        agent = AnalyzeAgent('S1', mock_team_config)

        # Create empty directory
        data_dir = temp_dir / 'empty'
        data_dir.mkdir()

        report = agent.execute(data_dir)

        assert report.status == 'error'
        assert 'No data files found' in report.summary
        assert len(report.issues) > 0

    def test_analyze_with_excel_file(self, mock_team_config, temp_dir, sample_s1_data):
        """Test analysis with a valid Excel file."""
        agent = AnalyzeAgent('S1', mock_team_config)

        # Create test data file
        data_dir = temp_dir / 'data'
        data_dir.mkdir()
        file_path = data_dir / 'test.xlsx'
        sample_s1_data.to_excel(file_path, index=False)

        report = agent.execute(data_dir)

        assert report.status in ['success', 'warning']
        assert report.details['files_found'] == 1
        assert report.details['total_records'] == len(sample_s1_data)
        assert 'Code' in agent.data.columns


class TestCleanAgent:
    """Test the CleanAgent functionality."""

    def test_clean_agent_initialization(self, mock_team_config):
        """Test that CleanAgent initializes correctly."""
        agent = CleanAgent('S1', mock_team_config)
        assert agent.team_id == 'S1'
        assert agent.phase == 'clean'

    def test_clean_no_data(self, mock_team_config):
        """Test cleaning with no input data."""
        agent = CleanAgent('S1', mock_team_config)

        report = agent.execute({})

        assert report.status == 'error'
        assert 'Cannot clean data' in report.summary

    def test_clean_with_data(self, mock_team_config, sample_s1_data):
        """Test cleaning with valid data."""
        agent = CleanAgent('S1', mock_team_config)

        input_data = {'original_data': sample_s1_data}

        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        assert report.details['records_input'] == len(sample_s1_data)
        assert 'cleaned_data' in agent.metadata


class TestTransformAgent:
    """Test the TransformAgent functionality."""

    def test_transform_agent_initialization(self, mock_team_config):
        """Test that TransformAgent initializes correctly."""
        agent = TransformAgent('S1', mock_team_config)
        assert agent.team_id == 'S1'
        assert agent.phase == 'transform'

    def test_transform_no_data(self, mock_team_config):
        """Test transformation with no input data."""
        agent = TransformAgent('S1', mock_team_config)

        report = agent.execute({})

        assert report.status == 'error'
        assert 'No data available for transformation' in report.summary

    def test_transform_with_data(self, mock_team_config, sample_s1_data):
        """Test transformation with valid data."""
        agent = TransformAgent('S1', mock_team_config)

        input_data = {'cleaned_data': sample_s1_data, 'original_data': sample_s1_data}

        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        assert 'transformed_data' in agent.metadata


class TestBuildAgent:
    """Test the BuildAgent functionality."""

    def test_build_agent_initialization(self, mock_team_config, mock_template_path):
        """Test that BuildAgent initializes correctly."""
        agent = BuildAgent('S1', mock_team_config, mock_template_path)
        assert agent.team_id == 'S1'
        assert agent.phase == 'build'
        assert agent.template_path == mock_template_path

    def test_build_no_data(self, mock_team_config, mock_template_path):
        """Test building with no input data."""
        agent = BuildAgent('S1', mock_team_config, mock_template_path)

        report = agent.execute({})

        assert report.status == 'error'
        assert 'No data available for template building' in report.summary

    def test_build_with_data(self, mock_team_config, mock_template_path, sample_s1_data, temp_dir):
        """Test building with valid data."""
        agent = BuildAgent('S1', mock_team_config, mock_template_path)

        input_data = {
            'transformed_data': sample_s1_data,
            'original_data': sample_s1_data
        }

        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        assert 'output_path' in report.details
        assert Path(report.details['output_path']).exists()


class TestAgentTeam:
    """Test the AgentTeam functionality."""

    def test_agent_team_initialization(self, mock_team_config, mock_template_path):
        """Test that AgentTeam initializes correctly."""
        team = AgentTeam('S1', mock_team_config, mock_template_path)

        assert team.team_id == 'S1'
        assert len(team.agents) == 4  # analyze, clean, transform, build
        assert all(phase in team.agents for phase in ['analyze', 'clean', 'transform', 'build'])

    def test_run_single_phase(self, mock_team_config, mock_template_path, temp_dir):
        """Test running a single phase."""
        team = AgentTeam('S1', mock_team_config, mock_template_path)

        # Create test data directory
        data_dir = temp_dir / 'data'
        data_dir.mkdir()

        report = team.run_phase('analyze', data_dir)

        assert isinstance(report, CheckInReport)
        assert report.phase == 'analyze'
        assert report.team_id == 'S1'

    def test_run_all_phases(self, mock_team_config, mock_template_path, temp_dir, sample_s1_data):
        """Test running all phases."""
        team = AgentTeam('S1', mock_team_config, mock_template_path)

        # Create test data file
        data_dir = temp_dir / 'data'
        data_dir.mkdir()
        file_path = data_dir / 'test.xlsx'
        sample_s1_data.to_excel(file_path, index=False)

        # Mock the team config to use our test directory
        team.team_config['data_dir'] = data_dir

        reports = team.run_all()

        assert len(reports) == 4
        assert all(isinstance(r, CheckInReport) for r in reports)
        phases = [r.phase for r in reports]
        assert set(phases) == {'analyze', 'clean', 'transform', 'build'}
