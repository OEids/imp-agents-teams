# S2 Staff Build - User Preparation Guide

This guide explains what users must do BEFORE and AFTER running the S2 agent to ensure a successful staff/payroll build.

---

## BEFORE YOU START

### 1. Two Upload Modes Available

Same as S3, the system supports two modes:

#### Mode A: Raw Data Upload
- Upload raw staff/HR export files
- Agent will analyse, map columns, infer roles
- Staff Role Groups and codes will be inferred from job titles
- Use when starting fresh or no template exists

#### Mode B: Pre-populated Template Upload
- Upload the template workbook FIRST
- Then upload raw staff data
- Agent extracts reference data from template:
  - Pay Scales and Points
  - Staff Role Groups (SRGs)
  - Staff Roles
  - Pension schemes
  - EQW Patterns
  - Allowance Types
- Use when template already configured for this trust

---

### 2. Required Input Files

| File Type | Required | What It Contains |
|-----------|----------|------------------|
| Staff List/HR Export | YES | Staff members, contracts, salaries |
| Pay Scales | YES | Teacher and Support pay scale points |
| Allowances | Optional | TLRs, SEN, other allowances |
| Pension Rates | Optional | LGPS/Teachers' Pension rates |
| EQW Patterns | Optional | Equated week patterns |

---

### 3. Staff Data File Requirements

The agent needs these fields from staff data. Column names may vary:

#### Essential Fields
| Field | Common Column Names |
|-------|---------------------|
| Staff Name | Name, Employee Name, Forename/Surname |
| Job Title | Post, Role, Position, Job Title |
| Contract Type | Teaching/Support, Contract Type |
| FTE | FTE, Hours, Full Time Equivalent |
| Salary/Point | Salary, Pay Point, Scale Point, Spinal |
| Start Date | Start Date, Contract Start, Appointment Date |
| School | Location, School, Cost Centre |

#### Optional But Recommended
| Field | Common Column Names |
|-------|---------------------|
| End Date | End Date, Leaving Date, Contract End |
| Pay Scale | Pay Scale, Scale, Band |
| Allowances | TLR, SEN Allowance, Allowance Amount |
| NI Category | NI Cat, NI Category, National Insurance |
| Pension Scheme | Pension, Pension Scheme, LGPS/TPS |

---

### 4. Pay Scale Files

The agent can import pay scales from:
- Excel files with scale names and point values
- Teacher Pay Scales (Main, Upper, Leadership)
- NJC/Support Pay Scales (Spinal points)

**File should contain:**
- Scale/Band name
- Point numbers
- Annual salary values
- Effective dates (if multiple years)

---

## SHEETS NOT PROCESSED BY AGENT

### Reference Data (From Template)
| Sheet | Source | Notes |
|-------|--------|-------|
| `PayScales` | Template or Import | Pay scale definitions |
| `PayScalePoints` | Template or Import | Salary points per scale |
| `PayScaleGrades` | Template or Import | Grade definitions |
| `Pensions` | Template | LGPS/TPS rates |
| `EQWPatterns` | Template | Equated week patterns |
| `StfRoleGroup` | Template | Staff Role Group definitions |

### Manual Entry May Be Required
| Sheet | Action Required |
|-------|-----------------|
| `AllowanceTypes` | Define TLR, SEN, other allowance types |
| `AllowanceIncreasePercen` | Set annual increase percentages |
| `PayScaleIncreasePercen` | Set annual pay increases |
| `ContractAdjustments` | Manually entered adjustments |

---

## STAFF ROLE MAPPING

### How the Agent Maps Roles

The agent infers Staff Role Group (SRG) from job titles:

| Job Title Contains | Maps To SRG |
|-------------------|-------------|
| Teacher, Head of, Subject Lead | TEA (Teaching) |
| TA, Teaching Assistant | SAS (Support - Academic) |
| Admin, Office, Secretary | SAD (Support - Admin) |
| Caretaker, Cleaner, Site | SPR (Support - Premises) |
| SENCO, SEN Coordinator | SEN |
| Headteacher, Principal | LEA (Leadership) |
| Business Manager, Finance | SBM |

### When Mapping Fails

If the agent cannot determine the role:
- Staff member assigned to `OTH` (Other) group
- Review `StfRole` sheet post-build
- Manually assign correct role codes

---

## CONTRACT TYPES

The agent creates separate sheets for:

| Contract Type | Output Sheet | Key Fields |
|--------------|--------------|------------|
| Teaching Staff | `ContractsTeachFTE` | FTE, Pay Scale, TLRs |
| Support Staff | `ContractsSupportHours` | Hours, Weeks, Hourly Rate |
| Allowances | `ContractAllowances` | Allowance Type, Amount |
| Adjustments | `ContractAdjustments` | Adjustment Type, Value |

---

## AFTER THE BUILD

### 1. Review Staff Role Assignments

Check `StfRole` sheet for:
- Staff assigned to `OTH` (Other) - need manual correction
- Incorrect role group mappings
- Missing subject-specific codes (e.g., TEA_MAT for Maths Teacher)

---

### 2. Verify Pay Scale Links

Check contracts have correct pay scale links:
- Teaching staff → Teacher Pay Scale (MPS, UPS, Leadership)
- Support staff → NJC/Local scale

**Common Issues:**
- Scale name mismatch → Staff shows no salary
- Point not found → Check PayScalePoints sheet

---

### 3. Check Contract Dates

Verify in `ContractsTeachFTE` and `ContractsSupportHours`:
- Start dates are correct
- End dates set for leavers/fixed-term
- No future start dates for current staff

**Date Format:** UK format `DD/MM/YY`

---

### 4. Review FTE/Hours

| Contract Type | Check |
|--------------|-------|
| Teaching | FTE should be 0.0-1.0 |
| Support | Hours per week realistic (e.g., 37, 20) |
| Support | Weeks per year correct (52, 44, 38) |

---

### 5. Verify Finance Codes

Check `Finance Codes S2` has correct mappings:
- Teaching salary codes (611xxx)
- Support salary codes (621xxx, 625xxx)
- NI codes
- Pension codes

---

### 6. Allowances

Review `ContractAllowances` for:
- TLR amounts correct
- SEN allowances assigned to correct staff
- Allowance types exist in `AllowanceTypes`

---

## COMMON ISSUES & FIXES

### Issue: Staff showing in wrong role group
**Cause:** Job title not recognized
**Fix:**
1. Add mapping to `S2_STAFF_ROLE_MAPPINGS.py`
2. Or manually correct in `StfRole` sheet

### Issue: No salary calculated
**Cause:** Pay scale/point mismatch
**Fix:**
1. Check `PayScales` has the scale name
2. Check `PayScalePoints` has the point number
3. Verify contract links to correct scale

### Issue: Support hours showing as FTE
**Cause:** Staff incorrectly classified as Teaching
**Fix:** Check contract type field, move to `ContractsSupportHours`

### Issue: Dates in wrong format
**Cause:** Source data used US format (MM/DD/YYYY)
**Fix:** Agent attempts UK parsing, but verify dates manually

### Issue: Duplicate staff members
**Cause:** Same person with multiple rows in source
**Fix:** Review source data - may be multiple contracts (valid) or duplicates (remove)

### Issue: Missing pension contributions
**Cause:** Pension scheme not linked
**Fix:**
1. Check `Pensions` sheet has scheme defined
2. Verify staff contract has pension scheme set

---

## FILE CHECKLIST

Before running the agent, confirm:

- [ ] Staff data file available (CSV/Excel)
- [ ] Pay scales file available
- [ ] Template workbook uploaded (if using template mode)
- [ ] Staff data has required columns (Name, Title, FTE/Hours, Salary)
- [ ] Dates are in recognizable format

After the build, verify:

- [ ] All staff members appear in `StaffMembers`
- [ ] Teaching contracts in `ContractsTeachFTE`
- [ ] Support contracts in `ContractsSupportHours`
- [ ] No staff in `OTH` role group (or review if correct)
- [ ] Pay scales linked correctly
- [ ] Allowances populated
- [ ] Finance codes correct
- [ ] Dates in UK format (DD/MM/YY)

---

## DATA FIELD MAPPINGS

The agent tries to map these common column names:

| Target Field | Common Source Columns |
|--------------|----------------------|
| StaffMemberCode | Employee ID, Staff Code, Payroll No |
| Forename | First Name, Forename, Given Name |
| Surname | Last Name, Surname, Family Name |
| JobTitle | Post, Role, Position, Job Title |
| SchoolCode | School, Location, Site, Cost Centre |
| FTE | FTE, Full Time Equivalent |
| Hours | Hours, Contracted Hours, Weekly Hours |
| Weeks | Weeks, Term Weeks, Working Weeks |
| PayScale | Scale, Pay Scale, Band |
| PayPoint | Point, Spinal Point, Scale Point |
| Salary | Salary, Annual Salary, FTE Salary |
| StartDate | Start Date, Appointment Date |
| EndDate | End Date, Leaving Date |
| NI_Category | NI Cat, NI Category |
| PensionScheme | Pension, Scheme |

---

## CONTACT

If the agent produces unexpected results, check:
1. Column names in source data
2. Pay scale definitions
3. Staff role mappings
4. Agent log for warnings/assumptions made
