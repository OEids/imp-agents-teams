# S2 Orchestrator Improvements - 2026-03-13

## Summary

Integrated IMP Planner Knowledge Base to improve S2 output quality and validation.

---

## Changes Made

### 1. IMP Planner Data Model Documentation

**File:** `knowledge/S2/IMP_PLANNER_DATA_MODEL.md`

Comprehensive documentation of IMP Planner data structures extracted from official Knowledge Base:

- **Staff Members**: Mandatory fields, validation rules
- **Contracts**: Teaching vs Support, FTE vs Hours, date validations
- **Pay Scales**: Structure (Scale → Points → Rates → Grades)
- **Staff Roles & Groups**: Teaching vs Support classification
- **Pensions**: LGPS, TPS, opt-out handling
- **Equated Week Patterns (EQWP)**: Term-time, all-year patterns
- **Allowances**: TLR, SEN, custom allowances
- **Adjustments**: Safeguarding, acting allowances
- **Schools & Departments**: Organizational structure

Key insights:
- **Teaching roles use FTE** (0.0-1.0), **Support roles use Hours** per week
- **Service End Date** required for disabled staff members
- **Contract dates** must be within Staff Member service dates
- **School must be attached to Department** on contracts
- **Pensions and Pay Scales** must not be disabled when in use

### 2. S2 Validation Module

**File:** `teams/s2_validation.py`

New validation module implementing IMP Planner business rules:

#### Validation Checks

1. **Staff Members**
   - Required fields present
   - No duplicate staff codes
   - Disabled staff have Service End Date

2. **Contracts**
   - Required fields present
   - Valid FTE (0.0-1.0) for teaching contracts
   - Reasonable hours (<60) for support contracts
   - Contract From < Contract To
   - Contracts within Staff Member service dates
   - Contracts end before Service End Date (if set)

3. **Pay Scales**
   - Required fields present
   - No duplicate codes
   - All scales have pay points

4. **Staff Roles**
   - Required fields present
   - All roles have valid role groups

5. **Pensions**
   - Required fields present
   - No duplicate codes

6. **Equated Week Patterns**
   - Required fields present
   - Weeks between 1-52

#### Usage

```python
from teams.s2_validation import validate_s2_output

validation_result = validate_s2_output(template_sheets)

# Returns:
{
    'passed': True/False,
    'errors': [...],
    'warnings': [...],
    'passed_checks': [...],
    'score': 95.5  # percentage
}
```

### 3. S2 Orchestrator Integration

**File:** `teams/s2_orchestrator.py`

**Agent 7 (Reconciliation)** now runs IMP Planner validation:

```python
# Import validation module
from .s2_validation import validate_s2_output

# In Agent 7 execution:
validation_result = validate_s2_output(template_sheets)
contract.metrics["imp_validation_score"] = validation_result.get('score', 0)
contract.metrics["imp_validation_passed"] = validation_result.get('passed', False)
```

**Metrics added to results:**
- `imp_validation_score`: Validation score (0-100)
- `imp_validation_passed`: Boolean pass/fail
- `imp_validation_errors`: Count of validation errors
- `imp_validation_warnings`: Count of validation warnings

---

## Benefits

### 1. Improved Data Quality
- Validates against official IMP Planner business rules
- Catches data integrity issues before import
- Ensures contracts follow IMP Planner constraints

### 2. Better Error Reporting
- Specific validation errors (e.g., "5 disabled staff have no Service End Date")
- Warnings for data quality issues (e.g., "unusual hours values")
- Passed checks for confirmation (e.g., "All FTE values valid")

### 3. Audit Compliance
- Validation score (0-100%) for quality assessment
- Detailed breakdown of passed/failed checks
- Traceable to IMP Planner Knowledge Base

### 4. Future Enhancement Foundation
- Can easily add more validation rules
- Modular design allows selective validation
- Can be extended to validate against customer-specific rules

---

## Validation Score Calculation

```
score = (passed_checks / total_checks) * 100

where:
  total_checks = errors + warnings + passed_checks
```

A score of:
- **90-100%**: Excellent quality, ready for import
- **75-89%**: Good quality, review warnings
- **60-74%**: Acceptable, fix errors before import
- **<60%**: Poor quality, significant issues found

---

## Example Output

```
Agent 7: Reconciliation & Validation - PASS WITH WARNINGS

Outputs:
  ✓ Output file validated: S2_complete_template_20260313_143022.xlsx
  ✓ Audit score: 87.5%
  ✓ IMP Validation: 92.3% (18 checks passed)
  ✓ Reconciliation order: contracted_hours, weeks_paid, pay_scale_point...
  ✓ Final output: C:\claude\agent-teams\output\S2_complete_template_20260313_143022.xlsx

Warnings:
  IMP Validation: 2 contracts have unusual hours (>50)
  IMP Validation: 3 scales have no pay points

Metrics:
  imp_validation_score: 92.3
  imp_validation_passed: True
  imp_validation_errors: 0
  imp_validation_warnings: 2
```

---

## Source Data

**File:** `knowledge/2026-03-11 - IMP Planner (1).json`

IMP Planner Knowledge Base export containing:
- 15 sections
- 433 articles total
- **Staffing section**: 50 articles
- **System Manual section**: 56 articles

Key articles referenced:
- IMP Planner: Staff Members (System Manual) - ID 360020491580
- IMP Planner: Contracts (System Manual) - ID 360020553379
- IMP Planner: Pay Scales (System Manual) - ID 360020403060
- IMP Planner: Staff Roles (System Manual) - ID 360020404940
- IMP Planner: Pensions (System Manual) - ID 360020405760
- IMP Planner: Equated Week Patterns (System Manual) - ID 360020369660

---

## Next Steps

### Potential Enhancements

1. **Additional Validation Rules**
   - Overlapping contracts check
   - School-Department attachment validation
   - Pay Scale rate validation for contract dates
   - Allowance date range checks

2. **Validation Profiles**
   - Strict mode: All errors must be fixed
   - Standard mode: Errors must be fixed, warnings allowed
   - Permissive mode: Only critical errors block import

3. **Custom Rules**
   - Trust-specific validation rules
   - Customer data quality thresholds
   - Region-specific pay scale ranges

4. **Integration**
   - Pre-flight validation before Agent 6 runs
   - Real-time validation during data extraction
   - Export validation report to Excel sheet

---

## References

- IMP Planner Knowledge Base: https://impsoftware.zendesk.com/hc/en-us
- IMP Software: https://impsoftware.co.uk
- IMP Voice (Feature Requests): https://impplanner.co.uk/ImpVoice/
