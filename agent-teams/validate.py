#!/usr/bin/env python
"""
Validation script - Run this before testing to catch common errors.

Usage:
    python validate.py           # Quick validation
    python validate.py --full    # Full validation with import tests
"""
import subprocess
import sys
import os

# Files to validate
CORE_FILES = [
    "teams/s1_specialist.py",
    "teams/s2_specialist.py",
    "teams/s3_specialist.py",
    "teams/expert_agents.py",
    "teams/payscale_extractor.py",
    "teams/master_orchestrator.py",
    "app.py",
]

def run_pyflakes(files):
    """Run pyflakes static analysis."""
    print("=" * 60)
    print("STATIC ANALYSIS (pyflakes)")
    print("=" * 60)

    errors = []
    for filepath in files:
        if not os.path.exists(filepath):
            continue
        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", filepath],
            capture_output=True,
            text=True
        )
        if result.stdout:
            # Filter to only show serious issues (undefined names, etc.)
            for line in result.stdout.splitlines():
                # Skip "imported but unused" warnings
                if "imported but unused" in line:
                    continue
                # Skip f-string placeholder warnings
                if "f-string is missing placeholders" in line:
                    continue
                # Skip "assigned to but never used" warnings
                if "assigned to but never used" in line:
                    continue
                # Keep undefined name errors - these are critical!
                if "undefined name" in line:
                    errors.append(line)
                    print(f"  ERROR: {line}")
                # Keep redefinition warnings
                elif "redefinition" in line:
                    print(f"  WARN:  {line}")

    if not errors:
        print("  No critical errors found")
    return len(errors) == 0


def run_compile_check(files):
    """Run Python compile check on all files."""
    print("\n" + "=" * 60)
    print("COMPILE CHECK (syntax errors)")
    print("=" * 60)

    errors = []
    for filepath in files:
        if not os.path.exists(filepath):
            continue
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", filepath],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            errors.append(filepath)
            print(f"  FAIL: {filepath}")
            print(f"        {result.stderr}")
        else:
            print(f"  OK:   {filepath}")

    return len(errors) == 0


def run_import_check():
    """Try importing all modules to catch AttributeErrors at class definition time."""
    print("\n" + "=" * 60)
    print("IMPORT CHECK (catches missing methods/attributes)")
    print("=" * 60)

    errors = []

    modules_to_import = [
        ("teams.s1_specialist", "S1SpecialistAgent"),
        ("teams.s2_specialist", "S2SpecialistAgent"),
        ("teams.s3_specialist", "S3SpecialistAgent"),
        ("teams.expert_agents", None),
        ("teams.payscale_extractor", "PayScaleExtractor"),
    ]

    for module_name, class_name in modules_to_import:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                cls = getattr(module, class_name)
                # Try to instantiate (catches some AttributeErrors)
                # Don't actually run it, just check it exists
                print(f"  OK:   {module_name}.{class_name}")
            else:
                print(f"  OK:   {module_name}")
        except AttributeError as e:
            errors.append(f"{module_name}: {e}")
            print(f"  FAIL: {module_name} - {e}")
        except ImportError as e:
            errors.append(f"{module_name}: {e}")
            print(f"  FAIL: {module_name} - {e}")
        except Exception as e:
            # Other errors during import
            errors.append(f"{module_name}: {e}")
            print(f"  FAIL: {module_name} - {type(e).__name__}: {e}")

    return len(errors) == 0


def main():
    """Run validation checks."""
    full_mode = "--full" in sys.argv

    print("\nVALIDATING CODE...")
    print(f"Mode: {'Full' if full_mode else 'Quick'}\n")

    # Change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    all_passed = True

    # Always run compile check
    if not run_compile_check(CORE_FILES):
        all_passed = False

    # Always run pyflakes
    if not run_pyflakes(CORE_FILES):
        all_passed = False

    # Full mode: also run import check
    if full_mode:
        if not run_import_check():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("VALIDATION PASSED")
    else:
        print("VALIDATION FAILED - Fix errors before testing!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
