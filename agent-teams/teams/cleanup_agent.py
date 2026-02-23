"""
Cleanup Agent - Automatically removes old template/report files.

Cleans up generated output files older than specified retention period.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import shutil


class CleanupAgent:
    """Agent that cleans up old generated files."""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.reports_dir = self.base_dir / "reports"
        self.output_dir = self.base_dir / "output"
        self.log_messages = []

    def log(self, msg: str):
        """Log a message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {msg}")
        try:
            print(f"[Cleanup] {msg}")
        except UnicodeEncodeError:
            print(f"[Cleanup] {msg.encode('ascii', 'replace').decode('ascii')}")

    def get_old_files(self, days: int = 1, patterns: List[str] = None) -> List[Path]:
        """Get files older than specified days."""
        if patterns is None:
            patterns = [
                "S1_complete_template_*.xlsx",
                "S2_complete_template_*.xlsx",
                "S3_complete_template_*.xlsx",
                "S1_*.xlsx",
                "S2_*.xlsx",
                "S3_*.xlsx",
            ]

        cutoff = datetime.now() - timedelta(days=days)
        old_files = []

        # Check reports directory
        if self.reports_dir.exists():
            for pattern in patterns:
                for file in self.reports_dir.glob(pattern):
                    if file.is_file():
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if mtime < cutoff:
                            old_files.append(file)

        # Check output directory
        if self.output_dir.exists():
            for pattern in patterns:
                for file in self.output_dir.glob(pattern):
                    if file.is_file():
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if mtime < cutoff:
                            old_files.append(file)

        return old_files

    def get_todays_files(self, patterns: List[str] = None) -> List[Path]:
        """Get files created today."""
        if patterns is None:
            patterns = [
                "S1_complete_template_*.xlsx",
                "S2_complete_template_*.xlsx",
                "S3_complete_template_*.xlsx",
            ]

        today = datetime.now().date()
        todays_files = []

        # Check reports directory
        if self.reports_dir.exists():
            for pattern in patterns:
                for file in self.reports_dir.glob(pattern):
                    if file.is_file():
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if mtime.date() == today:
                            todays_files.append(file)

        # Check output directory
        if self.output_dir.exists():
            for pattern in patterns:
                for file in self.output_dir.glob(pattern):
                    if file.is_file():
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if mtime.date() == today:
                            todays_files.append(file)

        return todays_files

    def cleanup_old_files(self, days: int = 1, dry_run: bool = False) -> Dict[str, Any]:
        """Remove files older than specified days."""
        self.log("="*60)
        self.log(f"CLEANUP AGENT - Removing files older than {days} day(s)")
        self.log("="*60)

        old_files = self.get_old_files(days)

        if not old_files:
            self.log("No old files found to clean up.")
            return {
                "success": True,
                "files_removed": 0,
                "files": [],
                "space_freed": 0,
            }

        self.log(f"Found {len(old_files)} files to remove:")

        removed_files = []
        total_size = 0

        for file in old_files:
            size = file.stat().st_size
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            self.log(f"  - {file.name} ({size/1024:.1f} KB, modified: {mtime.strftime('%Y-%m-%d %H:%M')})")

            if not dry_run:
                try:
                    file.unlink()
                    removed_files.append(str(file))
                    total_size += size
                except Exception as e:
                    self.log(f"    ERROR: Could not remove: {e}")
            else:
                removed_files.append(str(file))
                total_size += size

        if dry_run:
            self.log(f"\n[DRY RUN] Would remove {len(removed_files)} files ({total_size/1024:.1f} KB)")
        else:
            self.log(f"\nRemoved {len(removed_files)} files ({total_size/1024:.1f} KB freed)")

        return {
            "success": True,
            "files_removed": len(removed_files),
            "files": removed_files,
            "space_freed": total_size,
            "dry_run": dry_run,
        }

    def cleanup_except_latest(self, keep_count: int = 1) -> Dict[str, Any]:
        """Keep only the latest N files per strand, remove the rest."""
        self.log("="*60)
        self.log(f"CLEANUP AGENT - Keeping latest {keep_count} file(s) per strand")
        self.log("="*60)

        removed_files = []
        total_size = 0

        for strand in ["S1", "S2", "S3"]:
            pattern = f"{strand}_complete_template_*.xlsx"
            files = []

            # Collect files from reports dir
            if self.reports_dir.exists():
                files.extend(list(self.reports_dir.glob(pattern)))

            # Collect files from output dir
            if self.output_dir.exists():
                files.extend(list(self.output_dir.glob(pattern)))

            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            # Keep the latest N, remove the rest
            files_to_remove = files[keep_count:]

            if files_to_remove:
                self.log(f"\n{strand}: Keeping {min(len(files), keep_count)}, removing {len(files_to_remove)}")

                for file in files_to_remove:
                    size = file.stat().st_size
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    self.log(f"  - Removing: {file.name} ({mtime.strftime('%Y-%m-%d %H:%M')})")

                    try:
                        file.unlink()
                        removed_files.append(str(file))
                        total_size += size
                    except Exception as e:
                        self.log(f"    ERROR: {e}")
            else:
                self.log(f"\n{strand}: {len(files)} file(s) - nothing to remove")

        self.log(f"\nTotal: Removed {len(removed_files)} files ({total_size/1024:.1f} KB freed)")

        return {
            "success": True,
            "files_removed": len(removed_files),
            "files": removed_files,
            "space_freed": total_size,
        }

    def end_of_day_cleanup(self) -> Dict[str, Any]:
        """
        End of day cleanup - removes all but the latest template for each strand.
        Call this at the end of each day to clean up intermediate outputs.
        """
        self.log("="*60)
        self.log("END OF DAY CLEANUP")
        self.log("="*60)

        # Keep only the latest file for each strand
        result = self.cleanup_except_latest(keep_count=1)

        self.log("\nEnd of day cleanup complete.")

        return result

    def get_storage_summary(self) -> Dict[str, Any]:
        """Get summary of current storage usage."""
        summary = {
            "total_files": 0,
            "total_size": 0,
            "by_strand": {},
            "by_date": {},
        }

        for strand in ["S1", "S2", "S3"]:
            pattern = f"{strand}_*.xlsx"
            files = []

            if self.reports_dir.exists():
                files.extend(list(self.reports_dir.glob(pattern)))
            if self.output_dir.exists():
                files.extend(list(self.output_dir.glob(pattern)))

            strand_size = sum(f.stat().st_size for f in files)
            summary["by_strand"][strand] = {
                "count": len(files),
                "size": strand_size,
            }
            summary["total_files"] += len(files)
            summary["total_size"] += strand_size

            # Group by date
            for file in files:
                date_str = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d")
                if date_str not in summary["by_date"]:
                    summary["by_date"][date_str] = {"count": 0, "size": 0}
                summary["by_date"][date_str]["count"] += 1
                summary["by_date"][date_str]["size"] += file.stat().st_size

        return summary


def run_cleanup(days: int = 1, dry_run: bool = False) -> Dict[str, Any]:
    """Run cleanup for files older than specified days."""
    agent = CleanupAgent()
    return agent.cleanup_old_files(days, dry_run)


def run_end_of_day_cleanup() -> Dict[str, Any]:
    """Run end of day cleanup - keeps only latest file per strand."""
    agent = CleanupAgent()
    return agent.end_of_day_cleanup()


def get_storage_summary() -> Dict[str, Any]:
    """Get storage usage summary."""
    agent = CleanupAgent()
    return agent.get_storage_summary()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--end-of-day":
            result = run_end_of_day_cleanup()
        elif sys.argv[1] == "--dry-run":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            result = run_cleanup(days, dry_run=True)
        elif sys.argv[1] == "--summary":
            summary = get_storage_summary()
            print("\nStorage Summary:")
            print(f"  Total files: {summary['total_files']}")
            print(f"  Total size: {summary['total_size']/1024:.1f} KB")
            print("\nBy Strand:")
            for strand, data in summary["by_strand"].items():
                print(f"  {strand}: {data['count']} files ({data['size']/1024:.1f} KB)")
            print("\nBy Date:")
            for date, data in sorted(summary["by_date"].items(), reverse=True):
                print(f"  {date}: {data['count']} files ({data['size']/1024:.1f} KB)")
            result = summary
        else:
            days = int(sys.argv[1])
            result = run_cleanup(days)
    else:
        # Default: clean files older than 1 day
        result = run_cleanup(1)

    if isinstance(result, dict) and "files_removed" in result:
        print(f"\nResult: {result['files_removed']} files removed")
