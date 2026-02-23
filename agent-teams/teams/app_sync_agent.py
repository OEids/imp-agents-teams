"""
App Sync Agent - Automatically keeps app.py in sync with specialist agents.

This agent analyzes the return structures and capabilities of S1, S2, S3 specialists
and updates app.py to correctly display all metrics and features.
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SpecialistMetric:
    """Represents a metric returned by a specialist."""
    name: str
    key: str
    source: str  # 'summary', 'result', etc.
    data_type: str  # 'int', 'list', 'bool', 'float'


@dataclass
class SyncReport:
    """Report of sync analysis."""
    specialist: str
    missing_in_app: List[SpecialistMetric]
    extra_in_app: List[str]
    type_mismatches: List[Dict]
    suggestions: List[str]


class AppSyncAgent:
    """Agent that keeps app.py synchronized with specialist agents."""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.teams_dir = self.base_dir / "teams"
        self.app_file = self.base_dir / "app.py"
        self.log_messages = []

        # Known metric mappings for each specialist
        self.specialist_files = {
            "S1": self.teams_dir / "s1_specialist.py",
            "S2": self.teams_dir / "s2_specialist.py",
            "S3": self.teams_dir / "s3_specialist.py",
        }

    def log(self, msg: str):
        """Log a message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {msg}")
        # Handle Windows encoding issues
        try:
            print(f"[AppSync] {msg}")
        except UnicodeEncodeError:
            print(f"[AppSync] {msg.encode('ascii', 'replace').decode('ascii')}")

    def extract_return_structure(self, filepath: Path) -> Dict[str, Any]:
        """Extract the return structure from a specialist's process method."""
        if not filepath.exists():
            return {}

        content = filepath.read_text(encoding='utf-8', errors='ignore')

        # Find the main return statement in process method
        structure = {
            "summary_fields": [],
            "result_fields": [],
            "capabilities": [],
        }

        # Look for summary dict pattern
        summary_pattern = r'"summary":\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
        summary_match = re.search(summary_pattern, content, re.DOTALL)

        if summary_match:
            summary_content = summary_match.group(1)
            # Extract field names and their types
            field_pattern = r'"(\w+)":\s*([^,\n]+)'
            for match in re.finditer(field_pattern, summary_content):
                field_name = match.group(1)
                field_value = match.group(2).strip()

                # Determine type
                if 'len(' in field_value:
                    if 'list(' in field_value or 'schools' in field_name.lower():
                        data_type = 'list'
                    else:
                        data_type = 'int'
                elif field_value in ['True', 'False'] or 'passed' in field_name.lower():
                    data_type = 'bool'
                elif 'score' in field_name.lower():
                    data_type = 'float'
                else:
                    data_type = 'int'

                structure["summary_fields"].append(SpecialistMetric(
                    name=self._key_to_display_name(field_name),
                    key=field_name,
                    source='summary',
                    data_type=data_type
                ))

        # Look for top-level result fields
        result_patterns = [
            (r'"customer_data_loaded":', 'customer_data_loaded', 'bool'),
            (r'"data_source_warnings":', 'data_source_warnings', 'list'),
            (r'"audit":', 'audit', 'dict'),
            (r'"validation":', 'validation', 'dict'),
        ]

        for pattern, field_name, data_type in result_patterns:
            if re.search(pattern, content):
                structure["result_fields"].append(SpecialistMetric(
                    name=self._key_to_display_name(field_name),
                    key=field_name,
                    source='result',
                    data_type=data_type
                ))

        return structure

    def extract_app_display_fields(self, team_id: str) -> List[str]:
        """Extract what fields app.py currently displays for a team."""
        if not self.app_file.exists():
            return []

        content = self.app_file.read_text(encoding='utf-8', errors='ignore')

        fields = []

        # Find the render_processing function and look for team-specific sections
        # The pattern is: if team_id == "S1": or elif team_id == "S1":
        # within the summary display section

        # Look for patterns like: summary.get("field_name"
        # within the context of team_id checks

        # First find the render_processing function
        render_section = re.search(r'def render_processing.*?(?=\ndef |\Z)', content, re.DOTALL)
        if not render_section:
            return []

        render_content = render_section.group(0)

        # Find the team-specific section
        # Only match elif team_id at the same indentation level (12 spaces for this structure)
        team_pattern = rf'(?:if|elif) team_id == "{team_id}":(.*?)(?=\n            elif team_id|\n        # Template|\Z)'
        team_match = re.search(team_pattern, render_content, re.DOTALL)

        if team_match:
            section = team_match.group(1)

            # Find all summary.get calls - these are the displayed summary fields
            get_pattern = r'summary\.get\(["\'](\w+)["\']'
            for match in re.finditer(get_pattern, section):
                field = match.group(1)
                if field not in fields:
                    fields.append(field)

            # Find result.get calls for non-standard fields
            # Note: result may be stored in a variable first
            result_pattern = r'result\.get\(["\'](\w+)["\']'
            for match in re.finditer(result_pattern, section):
                field = match.group(1)
                # Only include special result fields, not standard ones
                if field in ['customer_data_loaded', 'data_source_warnings'] and field not in fields:
                    fields.append(field)

            # Also check for variable assignments from result.get
            var_pattern = r'(\w+)\s*=\s*result\.get\(["\'](\w+)["\']'
            for match in re.finditer(var_pattern, section):
                field = match.group(2)
                if field in ['customer_data_loaded', 'data_source_warnings'] and field not in fields:
                    fields.append(field)

        return fields

    def _key_to_display_name(self, key: str) -> str:
        """Convert a key like 'staff_members' to 'Staff Members'."""
        return key.replace('_', ' ').title()

    def analyze_sync(self, team_id: str) -> SyncReport:
        """Analyze sync status between specialist and app.py for a team."""
        specialist_file = self.specialist_files.get(team_id)
        if not specialist_file:
            return SyncReport(team_id, [], [], [], [f"Unknown team: {team_id}"])

        # Get what specialist returns
        specialist_structure = self.extract_return_structure(specialist_file)
        specialist_keys = set()
        for metric in specialist_structure.get("summary_fields", []):
            specialist_keys.add(metric.key)

        # Add special result-level fields that should be tracked
        special_result_fields = set()
        for field in specialist_structure.get("result_fields", []):
            if field.key in ['customer_data_loaded', 'data_source_warnings']:
                special_result_fields.add(field.key)

        # Get what app displays
        app_fields = set(self.extract_app_display_fields(team_id))

        # Find discrepancies - only for summary fields
        missing_in_app = []
        for metric in specialist_structure.get("summary_fields", []):
            if metric.key not in app_fields:
                missing_in_app.append(metric)

        # Check special result fields
        for field in specialist_structure.get("result_fields", []):
            if field.key in ['customer_data_loaded', 'data_source_warnings']:
                if field.key not in app_fields:
                    missing_in_app.append(field)

        # Extra fields - only flag if they're not in specialist summary
        extra_in_app = [f for f in app_fields if f not in specialist_keys and f not in special_result_fields]

        suggestions = []
        if missing_in_app:
            suggestions.append(f"Add metrics for: {', '.join(m.key for m in missing_in_app)}")
        if extra_in_app:
            suggestions.append(f"Remove or update metrics: {', '.join(extra_in_app)}")

        return SyncReport(
            specialist=team_id,
            missing_in_app=missing_in_app,
            extra_in_app=extra_in_app,
            type_mismatches=[],
            suggestions=suggestions
        )

    def generate_metrics_code(self, team_id: str) -> str:
        """Generate the metrics display code for a team based on specialist output."""
        specialist_file = self.specialist_files.get(team_id)
        if not specialist_file:
            return ""

        structure = self.extract_return_structure(specialist_file)
        summary_fields = structure.get("summary_fields", [])
        result_fields = structure.get("result_fields", [])

        lines = []

        # Group metrics into rows of 4
        metric_fields = [f for f in summary_fields if f.data_type in ('int', 'float')]
        bool_fields = [f for f in summary_fields if f.data_type == 'bool']
        list_fields = [f for f in summary_fields if f.data_type == 'list']

        # Generate column metrics
        row_num = 0
        for i in range(0, len(metric_fields), 4):
            row = metric_fields[i:i+4]
            col_var = "cols" if row_num == 0 else f"cols{row_num + 1}"
            lines.append(f"                {col_var} = st.columns(4)")

            for j, field in enumerate(row):
                if field.data_type == 'float' and 'score' in field.key.lower():
                    lines.append(f'                {col_var}[{j}].metric("{field.name}", f"{{summary.get(\'{field.key}\', 0):.1f}}%")')
                else:
                    lines.append(f'                {col_var}[{j}].metric("{field.name}", summary.get("{field.key}", 0))')

            # Pad with empty metrics if needed
            for j in range(len(row), 4):
                lines.append(f'                {col_var}[{j}].metric("", "")')

            row_num += 1

        # Handle list fields (like schools)
        for field in list_fields:
            lines.append(f'                {field.key} = summary.get("{field.key}", [])')
            lines.append(f'                st.metric("{field.name}", len({field.key}) if isinstance({field.key}, list) else {field.key})')

        # Handle bool fields (like audit_passed)
        for field in bool_fields:
            if 'audit' in field.key.lower() and 'passed' in field.key.lower():
                lines.append(f'')
                lines.append(f'                # Show audit status')
                lines.append(f'                if summary.get("audit_passed", False):')
                lines.append(f'                    audit_score = summary.get("audit_score", 0)')
                lines.append(f'                    st.success(f"✅ External Audit PASSED with score {{audit_score:.1f}}%")')
                lines.append(f'                elif summary.get("audit_score", 0) > 0:')
                lines.append(f'                    audit_score = summary.get("audit_score", 0)')
                lines.append(f'                    st.warning(f"⚠️ External Audit FAILED with score {{audit_score:.1f}}%")')

        # Handle result-level fields
        for field in result_fields:
            if field.key == 'customer_data_loaded':
                lines.append(f'')
                lines.append(f'                # Show customer data load status')
                lines.append(f'                if result.get("customer_data_loaded", False):')
                lines.append(f'                    st.success("✅ Customer data successfully loaded and processed")')
                lines.append(f'                else:')
                lines.append(f'                    st.warning("⚠️ No customer data files found - using defaults")')

            elif field.key == 'data_source_warnings':
                lines.append(f'')
                lines.append(f'                # Show data source warnings')
                lines.append(f'                data_warnings = result.get("data_source_warnings", [])')
                lines.append(f'                if data_warnings:')
                lines.append(f'                    with st.expander(f"📋 Data Source Warnings ({{len(data_warnings)}})", expanded=False):')
                lines.append(f'                        for warning in data_warnings:')
                lines.append(f'                            st.warning(warning)')

        return '\n'.join(lines)

    def run_sync_check(self) -> Dict[str, SyncReport]:
        """Run sync check for all teams."""
        self.log("="*60)
        self.log("APP SYNC AGENT - CHECKING SYNCHRONIZATION")
        self.log("="*60)

        reports = {}

        for team_id in ["S1", "S2", "S3"]:
            self.log(f"\nAnalyzing {team_id}...")
            report = self.analyze_sync(team_id)
            reports[team_id] = report

            if report.missing_in_app:
                self.log(f"  [!] Missing in app.py: {[m.key for m in report.missing_in_app]}")
            if report.extra_in_app:
                self.log(f"  [!] Extra in app.py (not in specialist): {report.extra_in_app}")
            if not report.missing_in_app and not report.extra_in_app:
                self.log(f"  [OK] {team_id} is in sync")

        return reports

    def generate_sync_report(self) -> str:
        """Generate a human-readable sync report."""
        reports = self.run_sync_check()

        lines = [
            "# App Sync Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        all_synced = True

        for team_id, report in reports.items():
            lines.append(f"## {team_id}")

            if not report.missing_in_app and not report.extra_in_app:
                lines.append("✅ Fully synchronized")
            else:
                all_synced = False

                if report.missing_in_app:
                    lines.append("### Missing in app.py:")
                    for metric in report.missing_in_app:
                        lines.append(f"- `{metric.key}` ({metric.data_type}) - {metric.name}")

                if report.extra_in_app:
                    lines.append("### Extra fields in app.py (may need removal):")
                    for field in report.extra_in_app:
                        lines.append(f"- `{field}`")

                if report.suggestions:
                    lines.append("### Suggestions:")
                    for suggestion in report.suggestions:
                        lines.append(f"- {suggestion}")

            lines.append("")

        if all_synced:
            lines.append("---")
            lines.append("✅ All teams are synchronized!")

        return '\n'.join(lines)


def run_app_sync_check() -> Dict[str, Any]:
    """Run the app sync agent and return results."""
    agent = AppSyncAgent()
    reports = agent.run_sync_check()

    return {
        "synced": all(
            not r.missing_in_app and not r.extra_in_app
            for r in reports.values()
        ),
        "reports": {
            team_id: {
                "missing_in_app": [m.key for m in r.missing_in_app],
                "extra_in_app": r.extra_in_app,
                "suggestions": r.suggestions,
            }
            for team_id, r in reports.items()
        },
        "log": agent.log_messages,
    }


def generate_sync_report() -> str:
    """Generate a sync report."""
    agent = AppSyncAgent()
    return agent.generate_sync_report()


def watch_for_changes(callback=None):
    """Watch specialist files for changes and trigger sync check."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("[!] watchdog not installed. Run: pip install watchdog")
        return

    class SpecialistChangeHandler(FileSystemEventHandler):
        def __init__(self, agent):
            self.agent = agent
            self.last_check = None

        def on_modified(self, event):
            if event.is_directory:
                return

            # Only react to specialist files
            if any(name in event.src_path for name in ['s1_specialist.py', 's2_specialist.py', 's3_specialist.py']):
                import time
                current_time = time.time()

                # Debounce - only check every 2 seconds
                if self.last_check and (current_time - self.last_check) < 2:
                    return

                self.last_check = current_time
                print(f"\n[!] Detected change in: {Path(event.src_path).name}")

                # Run sync check
                reports = self.agent.run_sync_check()

                all_synced = all(
                    not r.missing_in_app and not r.extra_in_app
                    for r in reports.values()
                )

                if not all_synced:
                    print("\n[!] APP.PY MAY NEED UPDATES!")
                    for team_id, report in reports.items():
                        if report.missing_in_app:
                            print(f"  {team_id} missing: {[m.key for m in report.missing_in_app]}")

                if callback:
                    callback(reports)

    agent = AppSyncAgent()
    handler = SpecialistChangeHandler(agent)
    observer = Observer()
    observer.schedule(handler, str(agent.teams_dir), recursive=False)

    print("[AppSync] Watching for specialist file changes...")
    print("[AppSync] Press Ctrl+C to stop")

    observer.start()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        # Watch mode
        watch_for_changes()
    else:
        # Run sync check
        result = run_app_sync_check()

        print("\n" + "="*60)
        print("SYNC REPORT")
        print("="*60)

        if result["synced"]:
            print("[OK] All teams are synchronized with app.py")
        else:
            print("[!] Sync issues found:")
            for team_id, report in result["reports"].items():
                if report["missing_in_app"] or report["extra_in_app"]:
                    print(f"\n{team_id}:")
                    if report["missing_in_app"]:
                        print(f"  Missing: {report['missing_in_app']}")
                    if report["extra_in_app"]:
                        print(f"  Extra: {report['extra_in_app']}")
