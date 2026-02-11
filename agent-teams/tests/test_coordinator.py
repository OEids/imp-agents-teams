"""
Unit tests for team coordinator.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from teams.coordinator import TeamCoordinator
from teams.expert_agents import ExpertAgentTeam
from teams.base import AgentTeam


class TestTeamCoordinator:
    """Test the TeamCoordinator functionality."""

    def test_coordinator_initialization(self, tmp_path):
        """Test that TeamCoordinator initializes correctly."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        assert coordinator.reports_dir == reports_dir
        assert len(coordinator.teams) == 0

    def test_initialize_teams_basic(self, tmp_path, mock_team_config, mock_template_path):
        """Test initializing teams with basic configuration."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        team_configs = {
            'S1': mock_team_config
        }
        templates = {
            'S1': mock_template_path
        }

        coordinator.initialize_teams(team_configs, templates, use_experts=False)

        assert 'S1' in coordinator.teams
        assert len(coordinator.teams) == 1
        assert isinstance(coordinator.teams['S1'], AgentTeam)

    def test_initialize_teams_expert(self, tmp_path, mock_team_config, mock_template_path):
        """Test initializing teams with expert agents."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        team_configs = {
            'S1': mock_team_config
        }
        templates = {
            'S1': mock_template_path
        }

        coordinator.initialize_teams(team_configs, templates, use_experts=True)

        assert 'S1' in coordinator.teams
        assert len(coordinator.teams) == 1
        assert isinstance(coordinator.teams['S1'], ExpertAgentTeam)

    def test_initialize_teams_missing_template(self, tmp_path, mock_team_config):
        """Test initializing teams when template is missing."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        team_configs = {
            'S1': mock_team_config
        }
        templates = {
            'S1': Path('/nonexistent/template.xlsx')
        }

        coordinator.initialize_teams(team_configs, templates)

        # Team should not be initialized if template doesn't exist
        assert len(coordinator.teams) == 0

    def test_start_session(self, tmp_path):
        """Test starting a session."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        coordinator.start_session()

        assert coordinator.session is not None
        assert coordinator.session.session_id is not None
        assert coordinator.session.started_at is not None

    def test_run_team(self, tmp_path, mock_team_config, mock_template_path):
        """Test running a single team."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        # Initialize team
        team_configs = {'S1': mock_team_config}
        templates = {'S1': mock_template_path}
        coordinator.initialize_teams(team_configs, templates, use_experts=False)

        # Mock the check-in handler
        check_in_handler = Mock()

        # Run team
        coordinator.run_team('S1', check_in_handler)

        # Should have called check-in handler multiple times
        assert check_in_handler.call_count > 0

    def test_run_all_teams(self, tmp_path, mock_team_config, mock_template_path):
        """Test running all teams."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        # Initialize multiple teams
        team_configs = {
            'S1': mock_team_config,
            'S2': {**mock_team_config, 'name': 'Staff Team'},
            'S3': {**mock_team_config, 'name': 'Financial Team'}
        }
        templates = {
            'S1': mock_template_path,
            'S2': mock_template_path,
            'S3': mock_template_path
        }
        coordinator.initialize_teams(team_configs, templates, use_experts=False)

        # Mock the check-in handler
        check_in_handler = Mock()

        # Run all teams
        coordinator.run_all_teams(check_in_handler)

        # Should have called check-in handler multiple times
        assert check_in_handler.call_count > 0

    def test_generate_summary(self, tmp_path):
        """Test generating session summary."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        # Start session and add some mock reports
        coordinator.start_session()

        # Mock some reports
        coordinator.all_reports = [
            Mock(team_id='S1', team_name='Structure Team', phase='analyze', status='success',
                 summary='S1 analyze ok', issues=[]),
            Mock(team_id='S1', team_name='Structure Team', phase='clean', status='success',
                 summary='S1 clean ok', issues=[]),
            Mock(team_id='S2', team_name='Staff Team', phase='analyze', status='warning',
                 summary='S2 analyze warn', issues=[])
        ]

        summary = coordinator.generate_summary()

        assert isinstance(summary, str)
        assert 'S1' in summary
        assert 'S2' in summary
        assert 'Success' in summary
        assert 'Warnings' in summary

    def test_save_session(self, tmp_path):
        """Test saving session data."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        coordinator.start_session()

        # Should not raise an exception
        coordinator.save_session()

        # Check if session file was created
        session_files = list(reports_dir.glob('session_*.json'))
        assert len(session_files) == 1

    def test_interactive_check_in(self, tmp_path):
        """Test interactive check-in handler."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        # Create a mock report
        report = Mock()
        report.team_id = 'S1'
        report.team_name = 'Test Team'
        report.phase = 'analyze'
        report.status = 'success'
        report.summary = 'Test summary'
        report.details = {}
        report.issues = []
        report.recommendations = []
        report.display = Mock()

        # Test interactive check-in (should wait for input)
        with patch('builtins.input', return_value='c'):  # Mock 'continue'
            coordinator.interactive_check_in(report)

    def test_auto_check_in(self, tmp_path):
        """Test auto check-in handler."""
        reports_dir = tmp_path / 'reports'
        coordinator = TeamCoordinator(config={}, reports_dir=reports_dir)

        # Create a mock report
        report = Mock()
        report.status = 'success'

        # Auto check-in should not pause for successful reports
        coordinator.auto_check_in(report)

        # Should not have raised any exceptions
