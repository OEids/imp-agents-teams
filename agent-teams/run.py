"""
Agent Teams Runner

Main entry point for running the 3-team agent system.

Usage:
    python run.py                    # Interactive mode with check-ins
    python run.py --team S1          # Run only Structure team
    python run.py --team S2          # Run only Staff team
    python run.py --team S3          # Run only Financial team
    python run.py --auto             # Auto mode (pause only on errors)
    python run.py --status           # Show current status
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import TEAMS, TEMPLATES, REPORTS_DIR
from teams.coordinator import TeamCoordinator
from teams.expert_agents import ExpertAgentTeam
from teams.knowledge import get_team_knowledge


def print_banner():
    """Print welcome banner."""
    print("""
    +------------------------------------------------------------------+
    |                     AGENT TEAM SYSTEM                            |
    |                                                                  |
    |   S1: Structure Team  - Finance codes, schools, departments      |
    |   S2: Staff Team      - Staff members, contracts, allowances     |
    |   S3: Financial Team  - Budgets, funding, pupil numbers          |
    |                                                                  |
    |   Each team runs 4 phases: Analyze -> Clean -> Transform -> Build |
    |   Check-ins after each phase for your review                     |
    +------------------------------------------------------------------+
    """)



def print_status(coordinator: TeamCoordinator):
    """Print status of all teams."""
    print("\n--- TEAM STATUS ---")
    for team_id, team in coordinator.teams.items():
        config = team.team_config
        data_dir = config['data_dir']
        files = list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.xlsm')) if data_dir.exists() else []
        files = [f for f in files if not f.name.startswith('~$')]

        print(f"\n{team_id}: {config['name']}")
        print(f"   Focus: {config['focus']}")
        print(f"   Data folder: {data_dir}")
        print(f"   Files found: {len(files)}")
        for f in files[:3]:
            print(f"      - {f.name}")
        if len(files) > 3:
            print(f"      ... and {len(files) - 3} more")


def main():
    parser = argparse.ArgumentParser(
        description='Run Agent Teams for data processing',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--team', choices=['S1', 'S2', 'S3'],
                        help='Run specific team only')
    parser.add_argument('--auto', action='store_true',
                        help='Auto mode - continue unless errors occur')
    parser.add_argument('--status', action='store_true',
                        help='Show status of all teams')
    parser.add_argument('--no-checkin', action='store_true',
                        help='Skip check-ins (run all phases automatically)')

    args = parser.parse_args()

    print_banner()

    # Initialize coordinator
    coordinator = TeamCoordinator(
        config={"teams": TEAMS, "templates": TEMPLATES},
        reports_dir=REPORTS_DIR
    )

    # Initialize teams
    coordinator.initialize_teams(TEAMS, TEMPLATES)

    if args.status:
        print_status(coordinator)
        return 0

    if not coordinator.teams:
        print("ERROR: No teams could be initialized. Check template paths.")
        return 1

    # Start session
    coordinator.start_session()

    # Determine check-in handler
    if args.no_checkin:
        check_in_handler = None
    elif args.auto:
        check_in_handler = coordinator.auto_check_in
    else:
        check_in_handler = coordinator.interactive_check_in

    # Run teams
    try:
        if args.team:
            # Run specific team
            if args.team in coordinator.teams:
                coordinator.run_team(args.team, check_in_handler)
            else:
                print(f"ERROR: Team {args.team} not available")
                return 1
        else:
            # Run all teams
            coordinator.run_all_teams(check_in_handler)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")

    # Generate and display summary
    summary = coordinator.generate_summary()
    print(summary)

    # Save session
    coordinator.save_session()

    return 0


if __name__ == '__main__':
    sys.exit(main())
