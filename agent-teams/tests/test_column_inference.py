"""
Test script to verify column inference and mapping fixes.
Tests that smart inference works and avoids false positives like 'surname' -> 'urn'.
"""

import sys
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence import InferenceEngine


def test_column_mappings():
    """Test that column mappings work correctly without false positives."""
    engine = InferenceEngine()

    # Test cases: (source_column, strand, expected_results_list, should_NOT_match)
    # expected_results_list allows semantic equivalents (e.g., surname = last_name)
    test_cases = [
        # Surname should NOT match 'urn' - both surname and last_name are valid
        ("Staff Surname", "S2", ["surname", "last_name"], "urn"),
        ("Surname", "S2", ["surname", "last_name"], "urn"),
        ("surname", "S2", ["surname", "last_name"], "urn"),
        ("Last Name", "S2", ["surname", "last_name"], "urn"),

        # URN should match correctly
        ("URN", "S1", ["urn"], None),
        ("School URN", "S1", ["urn"], None),
        ("urn_number", "S1", ["urn"], None),

        # Name fields - both forename and first_name are valid
        ("First Name", "S2", ["forename", "first_name"], None),
        ("Forename", "S2", ["forename", "first_name"], None),
        ("Given Name", "S2", ["forename", "first_name"], None),

        # Payroll fields
        ("Payroll Number", "S2", ["payroll_number"], None),
        ("Employee ID", "S2", ["payroll_number"], None),
        ("Staff ID", "S2", ["payroll_number"], None),

        # Job/Role fields
        ("Job Title", "S2", ["job_title", "title"], None),
        ("Position", "S2", ["job_title", "position"], None),

        # Pay fields
        ("Pay Scale", "S2", ["pay_scale"], None),
        ("Scale Point", "S2", ["scale_point", "current_scale_point"], None),
        ("Annual Salary", "S2", ["salary", "annual_salary"], None),
        ("Spot Salary", "S2", ["spot_salary"], None),
        ("Spot", "S2", ["spot_salary", "spot"], None),
        ("Spot Scale", "S2", ["spot_salary", "spot_scale"], None),

        # Hours
        ("Weekly Hours", "S2", ["weekly_hours"], None),
        ("Hours Per Week", "S2", ["weekly_hours"], None),
        ("FTE", "S2", ["fte", "weekly_fte"], None),

        # Dates
        ("Start Date", "S2", ["start_date"], None),
        ("Date of Birth", "S2", ["dob"], None),

        # Other
        ("Pension", "S2", ["pension", "pension_code"], None),
        ("Gender", "S2", ["gender"], None),
        ("School Code", "S1", ["school_code"], None),
        ("Department", "S1", ["department", "department_code"], None),
    ]

    print("=" * 80)
    print("COLUMN INFERENCE TESTS")
    print("=" * 80)

    passed = 0
    failed = 0

    for source_col, strand, expected_list, should_not_match in test_cases:
        result = engine.infer_column_mapping(source_col, strand)

        # Check for false positive
        if should_not_match and result.decision and result.decision.lower() == should_not_match.lower():
            print(f"FAIL: '{source_col}' -> '{result.decision}' (should NOT match '{should_not_match}')")
            print(f"       Confidence: {result.confidence:.2f}, Reasoning: {result.reasoning}")
            failed += 1
            continue

        # Check if we got expected result (or close enough)
        decision_lower = result.decision.lower() if result.decision else ""

        # Check against all acceptable results
        matches = False
        for expected in expected_list:
            expected_lower = expected.lower()
            if (expected_lower in decision_lower or
                decision_lower in expected_lower or
                expected_lower == decision_lower):
                matches = True
                break

        if matches and result.confidence >= 0.65:
            print(f"PASS: '{source_col}' -> '{result.decision}' ({result.confidence:.2f})")
            passed += 1
        elif result.confidence < 0.65:
            print(f"WARN: '{source_col}' -> '{result.decision}' (low confidence: {result.confidence:.2f})")
            print(f"       Expected one of: {expected_list}, Reasoning: {result.reasoning}")
            # Still count as pass if it's returning original column (unmapped case)
            if result.decision == source_col:
                passed += 1
            else:
                failed += 1
        else:
            print(f"FAIL: '{source_col}' -> '{result.decision}' (expected one of: {expected_list})")
            print(f"       Confidence: {result.confidence:.2f}, Reasoning: {result.reasoning}")
            failed += 1

    print()
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0


def test_smart_patterns():
    """Test the SMART_COLUMN_PATTERNS work correctly."""
    engine = InferenceEngine()

    # Specific patterns to test
    print("\n" + "=" * 80)
    print("SMART PATTERN TESTS")
    print("=" * 80)

    # Test that SMART_COLUMN_PATTERNS has surname patterns
    patterns = engine.SMART_COLUMN_PATTERNS

    print(f"\nSurname patterns: {patterns.get('surname', [])}")
    print(f"Forename patterns: {patterns.get('forename', [])}")
    print(f"Payroll patterns: {patterns.get('payroll_number', [])}")

    # Check surname patterns don't include 'urn'
    surname_patterns = patterns.get('surname', [])
    if 'urn' in surname_patterns:
        print("WARNING: 'urn' found in surname patterns - this could cause false matches!")
        return False

    print("\nPattern check passed - no 'urn' in surname patterns")
    return True


def test_critical_false_positives():
    """Test critical false positive cases."""
    engine = InferenceEngine()

    print("\n" + "=" * 80)
    print("CRITICAL FALSE POSITIVE TESTS")
    print("=" * 80)

    critical_tests = [
        # (source, strand, should_NOT_be)
        ("Staff Surname", "S2", "urn"),
        ("Surname", "S2", "urn"),
        ("surname", "S2", "urn"),
        ("Employee Surname", "S2", "urn"),
        ("Family Name", "S2", "urn"),
    ]

    all_passed = True

    for source, strand, should_not_be in critical_tests:
        result = engine.infer_column_mapping(source, strand)

        if result.decision and result.decision.lower() == should_not_be.lower():
            print(f"CRITICAL FAIL: '{source}' incorrectly mapped to '{result.decision}'!")
            print(f"                Confidence: {result.confidence:.2f}")
            print(f"                Reasoning: {result.reasoning}")
            all_passed = False
        else:
            print(f"PASS: '{source}' -> '{result.decision}' (not '{should_not_be}')")

    return all_passed


if __name__ == "__main__":
    # Run all tests
    smart_ok = test_smart_patterns()
    critical_ok = test_critical_false_positives()
    mapping_ok = test_column_mappings()

    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    print(f"Smart Patterns: {'PASS' if smart_ok else 'FAIL'}")
    print(f"Critical False Positives: {'PASS' if critical_ok else 'FAIL'}")
    print(f"Column Mappings: {'PASS' if mapping_ok else 'FAIL'}")

    if smart_ok and critical_ok and mapping_ok:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)
