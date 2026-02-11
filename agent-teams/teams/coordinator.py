"""
Team Coordinator

Manages all three teams (S1, S2, S3) and coordinates check-ins with the user.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field

from .base import AgentTeam, CheckInReport
from .expert_agents import ExpertAgentTeam


@dataclass
class SessionState:
    """Tracks the state of a processing session."""
    session_id: str
    started_at: datetime
    teams: Dict[str, str] = field(default_factory=dict)  # team_id -> current_phase
    completed_phases: List[str] = field(default_factory=list)
    pending_approval: Optional[CheckInReport] = None
    paused: bool = False

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "teams": self.teams,
            "completed_phases": self.completed_phases,
            "paused": self.paused
        }


class TeamCoordinator:
    """
    Coordinates all three teams and manages user check-ins.

    Workflow:
    1. Initialize all teams with their configurations
    2. Run teams sequentially or in parallel
    3. After each phase, pause for user check-in
    4. User can approve, request changes, or stop
    5. Generate final summary report
    """

    def __init__(self, config: Dict, reports_dir: Path):
        self.config = config
        self.reports_dir = reports_dir
        self.teams: Dict[str, AgentTeam] = {}
        self.session: Optional[SessionState] = None
        self.all_reports: List[CheckInReport] = []

        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)

    def initialize_teams(self, team_configs: Dict, templates: Dict, use_experts: bool = True):
        """Initialize all agent teams.

        Args:
            team_configs: Configuration for each team
            templates: Path to templates for each team
            use_experts: If True, use ExpertAgentTeam with domain knowledge (default)
        """
        for team_id, team_config in team_configs.items():
            template_path = templates.get(team_id)
            if template_path and Path(template_path).exists():
                if use_experts:
                    self.teams[team_id] = ExpertAgentTeam(team_id, team_config, template_path)
                    print(f"Initialized {team_config['name']} ({team_id}) with EXPERT knowledge")
                else:
                    self.teams[team_id] = AgentTeam(team_id, team_config, template_path)
                    print(f"Initialized {team_config['name']} ({team_id})")
            else:
                print(f"Warning: Template not found for {team_id}, skipping")

    def start_session(self) -> str:
        """Start a new processing session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session = SessionState(
            session_id=session_id,
            started_at=datetime.now(),
            teams={team_id: "pending" for team_id in self.teams}
        )
        print(f"\nSession started: {session_id}")
        return session_id

    def run_team(self, team_id: str, check_in_handler: Callable[[CheckInReport], bool] = None) -> List[CheckInReport]:
        """
        Run a single team through all phases.

        Args:
            team_id: The team to run (S1, S2, S3)
            check_in_handler: Callback function for check-ins. Returns True to continue, False to pause.

        Returns:
            List of check-in reports from all phases
        """
        if team_id not in self.teams:
            raise ValueError(f"Team {team_id} not found")

        team = self.teams[team_id]
        print(f"\n{'='*70}")
        print(f"STARTING: {team.name}")
        print(f"Focus: {team.team_config['focus']}")
        print(f"{'='*70}")

        reports = []
        phases = ["analyze", "clean", "transform", "build"]

        for phase in phases:
            # Update session state
            if self.session:
                self.session.teams[team_id] = phase

            # Get input for this phase
            if phase == "analyze":
                input_data = team.team_config['data_dir']
            else:
                prev_phase = phases[phases.index(phase) - 1]
                input_data = team.phase_data.get(prev_phase, {})

            # Run the phase
            report = team.run_phase(phase, input_data)
            reports.append(report)
            self.all_reports.append(report)

            # Display the report
            report.display()

            # Handle check-in
            if check_in_handler:
                should_continue = check_in_handler(report)
                if not should_continue:
                    print(f"Paused at {phase} phase. Awaiting user input...")
                    if self.session:
                        self.session.paused = True
                        self.session.pending_approval = report
                    return reports

            # Update completed phases
            if self.session:
                self.session.completed_phases.append(f"{team_id}:{phase}")

        # Mark team as complete
        if self.session:
            self.session.teams[team_id] = "complete"

        return reports

    def run_all_teams(self, check_in_handler: Callable[[CheckInReport], bool] = None) -> Dict[str, List[CheckInReport]]:
        """
        Run all teams sequentially.

        Args:
            check_in_handler: Callback for check-ins

        Returns:
            Dictionary of team_id -> list of reports
        """
        all_team_reports = {}

        for team_id in ["S1", "S2", "S3"]:
            if team_id in self.teams:
                reports = self.run_team(team_id, check_in_handler)
                all_team_reports[team_id] = reports

                # Check if we were paused
                if self.session and self.session.paused:
                    break

        return all_team_reports

    def generate_summary(self) -> str:
        """Generate a summary report of all processing."""
        summary = []
        summary.append("\n" + "="*70)
        summary.append("PROCESSING SUMMARY")
        summary.append("="*70)

        if self.session:
            summary.append(f"Session: {self.session.session_id}")
            summary.append(f"Started: {self.session.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Group reports by team
        team_reports = {}
        for report in self.all_reports:
            if report.team_id not in team_reports:
                team_reports[report.team_id] = []
            team_reports[report.team_id].append(report)

        for team_id, reports in team_reports.items():
            summary.append(f"\n--- {reports[0].team_name} ---")
            for report in reports:
                status_icon = {"success": "[OK]", "warning": "[!!]", "error": "[XX]"}.get(report.status, "[??]")
                summary.append(f"  {status_icon} {report.phase}: {report.summary}")

                if report.issues:
                    for issue in report.issues[:3]:
                        summary.append(f"      ! {issue}")

        # Overall stats
        summary.append(f"\n--- Overall ---")
        total = len(self.all_reports)
        success = len([r for r in self.all_reports if r.status == "success"])
        warnings = len([r for r in self.all_reports if r.status == "warning"])
        errors = len([r for r in self.all_reports if r.status == "error"])

        summary.append(f"  Total phases: {total}")
        summary.append(f"  Success: {success}")
        summary.append(f"  Warnings: {warnings}")
        summary.append(f"  Errors: {errors}")

        summary.append("="*70 + "\n")

        return "\n".join(summary)

    def save_session(self):
        """Save session state and reports to files."""
        if not self.session:
            return

        timestamp = self.session.session_id

        # Save session state
        session_file = self.reports_dir / f"session_{timestamp}.json"
        with open(session_file, 'w') as f:
            json.dump(self.session.to_dict(), f, indent=2)

        # Save all reports
        reports_file = self.reports_dir / f"reports_{timestamp}.json"
        reports_data = [r.to_dict() for r in self.all_reports]
        with open(reports_file, 'w') as f:
            json.dump(reports_data, f, indent=2)

        # Save summary
        summary_file = self.reports_dir / f"summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(self.generate_summary())

        print(f"\nSession saved to: {self.reports_dir}")

    def interactive_check_in(self, report: CheckInReport) -> bool:
        """
        Interactive check-in handler that prompts user for input.

        Returns:
            True to continue, False to pause
        """
        print("\n" + "-"*50)
        print("USER CHECK-IN REQUIRED")
        print("-"*50)

        if report.status == "error":
            print("An error occurred. Please review before continuing.")
        elif report.issues:
            print(f"Found {len(report.issues)} issue(s) to review.")

        while True:
            response = input("\nOptions: [c]ontinue, [p]ause, [d]etails, [q]uit > ").strip().lower()

            if response == 'c':
                return True
            elif response == 'p':
                return False
            elif response == 'd':
                report.display()
            elif response == 'q':
                print("Quitting session...")
                return False
            else:
                print("Invalid option. Use c, p, d, or q.")

    def auto_check_in(self, report: CheckInReport) -> bool:
        """
        Automatic check-in handler that continues on success, pauses on errors.

        Returns:
            True to continue, False to pause
        """
        if report.status == "error":
            print(f"\n[AUTO] Pausing due to error in {report.phase}")
            return False
        return True
