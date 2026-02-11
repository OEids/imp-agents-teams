"""
Unit tests for expert agent classes.
"""

import pytest
import pandas as pd
from pathlib import Path

from teams.expert_agents import (
    ExpertAnalyzeAgent, ExpertCleanAgent, ExpertTransformAgent, ExpertBuildAgent,
    ExpertAgentTeam
)


class TestExpertAnalyzeAgent:
    """Test the ExpertAnalyzeAgent functionality."""

    def test_expert_analyze_initialization(self, mock_team_config):
        """Test that ExpertAnalyzeAgent initializes with knowledge."""
        agent = ExpertAnalyzeAgent('S1', mock_team_config)

        assert agent.team_id == 'S1'
        assert agent.phase == 'analyze'
        assert hasattr(agent, 'knowledge')
        assert agent.knowledge.team_name == 'Structure Team'

    def test_expert_analysis_s1(self, mock_team_config, sample_s1_data, temp_dir):
        """Test expert analysis for S1 data."""
        agent = ExpertAnalyzeAgent('S1', mock_team_config)

        # Create test data file
        data_dir = temp_dir / 'data'
        data_dir.mkdir()
        file_path = data_dir / 'coa.xlsx'
        sample_s1_data.to_excel(file_path, index=False)

        report = agent.execute(data_dir)

        assert report.status in ['success', 'warning']
        assert 'expert_insights' in report.details
        insights = report.details['expert_insights']
        assert 'recognized_columns' in insights

    def test_expert_analysis_s2(self, mock_team_config, sample_s2_data, temp_dir):
        """Test expert analysis for S2 data."""
        agent = ExpertAnalyzeAgent('S2', mock_team_config)

        # Create test data file
        data_dir = temp_dir / 'data'
        data_dir.mkdir()
        file_path = data_dir / 'staff.xlsx'
        sample_s2_data.to_excel(file_path, index=False)

        report = agent.execute(data_dir)

        assert report.status in ['success', 'warning']
        assert 'expert_insights' in report.details

    def test_expert_analysis_s3(self, mock_team_config, sample_s3_data, temp_dir):
        """Test expert analysis for S3 data."""
        agent = ExpertAnalyzeAgent('S3', mock_team_config)

        # Create test data file
        data_dir = temp_dir / 'data'
        data_dir.mkdir()
        file_path = data_dir / 'budget.xlsx'
        sample_s3_data.to_excel(file_path, index=False)

        report = agent.execute(data_dir)

        assert report.status in ['success', 'warning']
        assert 'expert_insights' in report.details


class TestExpertCleanAgent:
    """Test the ExpertCleanAgent functionality."""

    def test_expert_clean_initialization(self, mock_team_config):
        """Test that ExpertCleanAgent initializes with knowledge."""
        agent = ExpertCleanAgent('S1', mock_team_config)

        assert agent.team_id == 'S1'
        assert agent.phase == 'clean'
        assert hasattr(agent, 'knowledge')

    def test_expert_clean_s1_finance_codes(self, mock_team_config):
        """Test expert cleaning of S1 finance codes."""
        agent = ExpertCleanAgent('S1', mock_team_config)

        # Data with 6-digit finance codes that need normalizing
        data = pd.DataFrame({
            'finance_code': ['001234', '005678', '001111'],
            'title': ['Dept 1', 'Dept 2', 'Dept 3']
        })

        input_data = {'original_data': data}
        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        # Finance codes should be normalized to 4 digits
        result_codes = agent.data['finance_code'].tolist()
        assert all(len(str(code)) <= 4 for code in result_codes if pd.notna(code))

    def test_expert_clean_s2_pay_scales(self, mock_team_config):
        """Test expert cleaning of S2 pay scales."""
        agent = ExpertCleanAgent('S2', mock_team_config)

        data = pd.DataFrame({
            'payroll_number': ['001', '002', '003'],
            'current_scale_point': ['M1', 'UPS2', 'L8']
        })

        input_data = {'original_data': data}
        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        # Should have processed pay scales
        assert 'expert_normalizations' in report.details

    def test_expert_clean_s3_finance_codes(self, mock_team_config):
        """Test expert cleaning of S3 finance codes."""
        agent = ExpertCleanAgent('S3', mock_team_config)

        data = pd.DataFrame({
            'fund_code': ['FUND001', 'FUND002'],
            'amount': [1000.0, 2000.0]
        })

        input_data = {'original_data': data}
        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']


class TestExpertTransformAgent:
    """Test the ExpertTransformAgent functionality."""

    def test_expert_transform_initialization(self, mock_team_config):
        """Test that ExpertTransformAgent initializes with knowledge."""
        agent = ExpertTransformAgent('S1', mock_team_config)

        assert agent.team_id == 'S1'
        assert agent.phase == 'transform'
        assert hasattr(agent, 'knowledge')

    def test_expert_transform_s1(self, mock_team_config, sample_s1_data):
        """Test expert transformation for S1."""
        agent = ExpertTransformAgent('S1', mock_team_config)

        input_data = {
            'cleaned_data': sample_s1_data,
            'original_data': sample_s1_data
        }

        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        assert 'transformed_data' in agent.metadata

    def test_expert_transform_s2(self, mock_team_config, sample_s2_data):
        """Test expert transformation for S2."""
        agent = ExpertTransformAgent('S2', mock_team_config)

        input_data = {
            'cleaned_data': sample_s2_data,
            'original_data': sample_s2_data
        }

        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        assert 'transformed_data' in agent.metadata


class TestExpertBuildAgent:
    """Test the ExpertBuildAgent functionality."""

    def test_expert_build_initialization(self, mock_team_config, mock_template_path):
        """Test that ExpertBuildAgent initializes with knowledge."""
        agent = ExpertBuildAgent('S1', mock_team_config, mock_template_path)

        assert agent.team_id == 'S1'
        assert agent.phase == 'build'
        assert hasattr(agent, 'knowledge')

    def test_expert_build_output(self, mock_team_config, mock_template_path, sample_s1_data, temp_dir):
        """Test expert build output generation."""
        agent = ExpertBuildAgent('S1', mock_team_config, mock_template_path)

        input_data = {
            'transformed_data': sample_s1_data,
            'original_data': sample_s1_data
        }

        report = agent.execute(input_data)

        assert report.status in ['success', 'warning']
        assert 'output_path' in report.details
        output_path = Path(report.details['output_path'])
        assert output_path.exists()

        # Check that output contains multiple sheets
        import openpyxl
        wb = openpyxl.load_workbook(output_path)
        sheet_names = wb.sheetnames
        assert 'Data' in sheet_names
        assert 'Validation' in sheet_names
        assert 'Assumptions' in sheet_names
        assert 'Data_Comparison' in sheet_names


class TestExpertAgentTeam:
    """Test the ExpertAgentTeam functionality."""

    def test_expert_team_initialization(self, mock_team_config, mock_template_path):
        """Test that ExpertAgentTeam initializes correctly."""
        team = ExpertAgentTeam('S1', mock_team_config, mock_template_path)

        assert team.team_id == 'S1'
        assert len(team.agents) == 4
        assert all(isinstance(agent, (ExpertAnalyzeAgent, ExpertCleanAgent,
                                     ExpertTransformAgent, ExpertBuildAgent))
                  for agent in team.agents.values())

    def test_expert_team_knowledge(self, mock_team_config, mock_template_path):
        """Test that ExpertAgentTeam has knowledge."""
        team = ExpertAgentTeam('S1', mock_team_config, mock_template_path)

        knowledge = team.get_knowledge_summary()
        assert 'team' in knowledge
        assert 'key_concepts' in knowledge
        assert 'column_mappings' in knowledge
        assert knowledge['team'] == 'Structure Team'

    def test_expert_team_run_all(self, mock_team_config, mock_template_path, temp_dir, sample_s1_data):
        """Test running all phases with expert agents."""
        team = ExpertAgentTeam('S1', mock_team_config, mock_template_path)

        # Create test data file
        data_dir = temp_dir / 'data'
        data_dir.mkdir()
        file_path = data_dir / 'test.xlsx'
        sample_s1_data.to_excel(file_path, index=False)

        # Update team config
        team.team_config['data_dir'] = data_dir

        reports = team.run_all()

        assert len(reports) == 4
        phases = [r.phase for r in reports]
        assert set(phases) == {'analyze', 'clean', 'transform', 'build'}

        # Check that expert insights are included
        analyze_report = next(r for r in reports if r.phase == 'analyze')
        assert 'expert_insights' in analyze_report.details
