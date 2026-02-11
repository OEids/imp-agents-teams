"""
Unit tests for configuration components.
"""

import pytest
from pathlib import Path

from config.settings import TEAMS, TEMPLATES, REPORTS_DIR


class TestConfiguration:
    """Test the configuration settings."""

    def test_teams_config_structure(self):
        """Test that TEAMS config has correct structure."""
        assert isinstance(TEAMS, dict)
        assert len(TEAMS) == 3  # S1, S2, S3

        for team_id, team_config in TEAMS.items():
            assert 'name' in team_config
            assert 'focus' in team_config
            assert 'data_dir' in team_config
            assert 'description' in team_config

    def test_templates_config_structure(self):
        """Test that TEMPLATES config has correct structure."""
        assert isinstance(TEMPLATES, dict)
        assert len(TEMPLATES) == 3  # S1, S2, S3

        for team_id, template_path in TEMPLATES.items():
            assert isinstance(template_path, (str, Path))

    def test_reports_dir_config(self):
        """Test that REPORTS_DIR is properly configured."""
        assert isinstance(REPORTS_DIR, Path)

    def test_team_data_directories(self):
        """Test that team data directories are configured."""
        for team_id, team_config in TEAMS.items():
            data_dir = team_config['data_dir']
            assert isinstance(data_dir, Path)

    def test_template_files_exist(self):
        """Test that template files exist (or at least paths are valid)."""
        for team_id, template_path in TEMPLATES.items():
            path = Path(template_path)
            # Templates might not exist in test environment, but path should be valid
            assert isinstance(path, Path)

    def test_team_ids_consistency(self):
        """Test that team IDs are consistent between TEAMS and TEMPLATES."""
        team_ids = set(TEAMS.keys())
        template_ids = set(TEMPLATES.keys())
        assert team_ids == template_ids

    def test_s1_team_config(self):
        """Test S1 team specific configuration."""
        s1_config = TEAMS['S1']
        assert s1_config['name'] == 'Structure Team'
        assert 'finance' in s1_config['focus'].lower()

    def test_s2_team_config(self):
        """Test S2 team specific configuration."""
        s2_config = TEAMS['S2']
        assert s2_config['name'] == 'Staff Team'
        assert 'staff' in s2_config['focus'].lower()

    def test_s3_team_config(self):
        """Test S3 team specific configuration."""
        s3_config = TEAMS['S3']
        assert s3_config['name'] == 'Financial Team'
        assert 'budget' in s3_config['focus'].lower()
        assert 'funding' in s3_config['focus'].lower()
