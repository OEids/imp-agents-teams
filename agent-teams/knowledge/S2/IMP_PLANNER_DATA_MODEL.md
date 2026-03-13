# IMP Planner Data Model - S2 (Strand 2) Reference

**Source:** IMP Planner Knowledge Base Export (2026-03-11)
**Purpose:** Define the official IMP Planner data structures for S2 template generation

---

## 1. STAFF MEMBERS

### Mandatory Fields
- **Code** - Unique identifier for staff member
- **Title** - Staff member name/title
- **Service Start Date** - Date staff member joined
- **Gender** - Staff member gender
- **Payroll Location** - Where staff member is paid

### Optional Fields
- **Service End Date** - Date staff member left (required if disabled)
- **Date of Birth**
- **Pension Opted Out** - Boolean flag
- **Casual Staff** - Boolean flag
- **Apprentice** - Boolean flag
- **Available to All Schools** - Boolean flag
- **Available to Schools** - List of schools if not available to all

### Validation Rules
- If Staff Member is **disabled**, must have a **Service End Date**
- Service End Date must be >= all Contract End Dates
- Code must be unique across all staff members

---

## 2. CONTRACTS

### Mandatory Fields
- **Staff Member Code** - Links to Staff Members
- **Staff Role Code** - Links to Staff Roles
- **School Code** - Links to Schools
- **Department Code** - Links to Departments
- **Pay Scale Code** - Links to Pay Scales
- **Pay Point** - Point on the pay scale
- **Contract From** - Contract start date
- **Contract To** - Contract end date
- **Pension Code** - Links to Pensions
- **Equated Week Pattern Code** - Links to EQWP
- **FTE** (for teaching) or **Hours** (for support)

### Optional Fields
- **Reference** - Required if multiple contracts overlap with same role/school/department
- **Weeks Paid** - Number of weeks paid
- **Contract Type Code** - Full-time, Part-time, etc.
- **Safeguarded** - Boolean flag
- **TLR** - Teaching & Learning Responsibility allowance
- **SEN** - Special Educational Needs allowance

### Validation Rules
- Cannot have overlapping contracts for same staff member with same role/school/department (unless Reference is different)
- Contract dates must fall within Staff Member Service Start/End dates
- School on contract must be attached to the Department
- Pension on contract must not be disabled
- Pay Scale must be valid and not disabled
- If Staff Role is teaching: must use **FTE** (0.0 - 1.0)
- If Staff Role is support: must use **Hours** per week

---

## 3. PAY SCALES

### Structure
Pay Scales consist of:
1. **Pay Scale** (e.g., "Teachers Main Scale")
2. **Pay Points** (e.g., "M1", "M2", "M3")
3. **Pay Rates** (e.g., £30,000 for M1 in 2024-25)
4. **Pay Grades** (groups of points, e.g., "M1-M6")

### Mandatory Fields (Pay Scale)
- **Code** - Unique identifier (e.g., "TMS")
- **Title** - Display name (e.g., "Teachers Main Scale")
- **Available to All Schools** - Boolean
- **Available to Schools** - List if not available to all

### Mandatory Fields (Pay Point)
- **Code** - Unique identifier within scale (e.g., "M1")
- **Title** - Display name (e.g., "Main Scale Point 1")
- **Sequence** - Order within scale

### Mandatory Fields (Pay Rate)
- **Pay Point Code** - Links to Pay Point
- **Effective From** - Date rate becomes active
- **Annual Rate** - Full-time annual salary

### Mandatory Fields (Pay Grade)
- **Code** - Unique identifier (e.g., "M1-M6")
- **Title** - Display name
- **Pay Points** - List of points in this grade

### Validation Rules
- Pay Scale must have at least one Pay Point
- Pay Point must have at least one Pay Rate
- Pay Rates must have unique Effective From dates
- When allocating to Staff Role, Pay Scale must not be disabled
- Cannot change Pay Scale on Staff Role if contracts are using it

---

## 4. STAFF ROLES

### Mandatory Fields
- **Code** - Unique identifier (e.g., "TCHR_KS2")
- **Title** - Display name (e.g., "KS2 Class Teacher")
- **Staff Role Group Code** - Links to Staff Role Groups (e.g., "TEACH")
- **Pay Scale Code** - Links to Pay Scales
- **Is Teaching Role** - Boolean flag
- **Is Support Role** - Boolean flag
- **FTE Hours** - Full-time equivalent hours for this role

### Optional Fields
- **Available to All Schools** - Boolean
- **Available to Schools** - List if not available to all
- **Is Finance Role** - Boolean flag

### Validation Rules
- Cannot be both Teaching and Support role
- Must be either Teaching OR Support
- FTE Hours required for all roles
- Staff Role Group must match role type (teaching groups for teaching roles, support groups for support roles)
- Cannot change if contracts are using the role

---

## 5. STAFF ROLE GROUPS

### Purpose
Groups similar roles together for reporting and finance mapping (e.g., "Teaching Staff", "Support Staff", "Leadership")

### Mandatory Fields
- **Code** - Unique identifier (e.g., "TEACH", "SUPP", "LEAD")
- **Title** - Display name (e.g., "Teaching Staff")
- **Is Teaching Group** - Boolean flag
- **Finance Code** - Gross salary finance code for this group

### Common Groups
- **Teaching Groups**: Teachers, Leadership
- **Support Groups**: Admin, Technicians, Cleaners, Catering, Site

### Validation Rules
- Finance Code must be valid and not disabled
- Every contract must map to exactly one Staff Role Group
- Cannot have orphan or unmapped finance codes

---

## 6. PENSIONS

### Mandatory Fields
- **Code** - Unique identifier (e.g., "LGPS", "TPS")
- **Title** - Display name (e.g., "Local Government Pension Scheme")
- **Available to All Schools** - Boolean
- **Available to Schools** - List if not available to all

### Pension Percentage Rates
- **Effective From** - Date rate becomes active
- **Employer Percentage** - Employer contribution %
- **Employee Percentage** - Employee contribution % (can be tiered)

### Common Schemes
- **LGPS** - Local Government Pension Scheme (support staff)
- **TPS** - Teachers' Pension Scheme (teachers)
- **No Pension** - For pension opt-outs

### Validation Rules
- Pension on contract must not be disabled
- If Staff Member has "Pension Opted Out" = true, should use "No Pension" scheme
- Percentage rates must have unique Effective From dates

---

## 7. EQUATED WEEK PATTERNS (EQWP)

### Purpose
Defines how many weeks a staff member is paid over the year (term-time only, all year, etc.)

### Mandatory Fields
- **Code** - Unique identifier (e.g., "52WK", "39WK", "44WK")
- **Title** - Display name (e.g., "All Year Round (52 weeks)")
- **Full-Time Weeks** - Number of weeks at full time

### Equated Week Pattern Rates
- **Effective From** - Date rate becomes active
- **Weeks** - Number of weeks (can be same as Full-Time Weeks or different for part-year)

### Common Patterns
- **52WK** - All year round (52 weeks)
- **39WK** - Term time only (39 weeks)
- **44WK** - Term time plus holidays (44 weeks)

### Validation Rules
- EQWP must have at least one rate
- Rates must have unique Effective From dates
- Weeks value must be > 0 and <= 52

---

## 8. ALLOWANCES

### Types
- **TLR (Teaching & Learning Responsibility)** - Additional payments for teaching staff
- **SEN (Special Educational Needs)** - Additional payments for SEN responsibilities
- **Trust-Specific** - Custom allowances defined by the trust

### Mandatory Fields (Allowance Type)
- **Code** - Unique identifier (e.g., "TLR1", "TLR2A", "SEN1")
- **Title** - Display name (e.g., "TLR 1")
- **Annual Amount** - Full-time annual amount

### Mandatory Fields (Contract Allowance)
- **Contract ID** - Links to Contract
- **Allowance Type Code** - Links to Allowance Type
- **Effective From** - Start date
- **Effective To** - End date
- **Amount or Percentage** - Override default amount if needed

### Validation Rules
- Allowance dates must fall within Contract dates
- Teaching allowances (TLR, SEN) should only be on teaching contracts
- Allowances can be pro-rated for part-time staff

---

## 9. ADJUSTMENTS

### Purpose
One-off or recurring adjustments to salary (e.g., safeguarding, acting allowances)

### Mandatory Fields
- **Contract ID** - Links to Contract
- **Adjustment Type Code** - Links to Adjustment Types
- **Effective From** - Start date
- **Effective To** - End date
- **Amount or Percentage** - Adjustment value
- **Is Recurring** - Boolean flag

### Validation Rules
- Adjustment dates must fall within Contract dates
- Cannot have overlapping adjustments of same type on same contract

---

## 10. SCHOOLS & DEPARTMENTS

### Schools
- **Code** - Unique identifier
- **Title** - School name
- **Finance Code** - For budget mapping

### Departments
- **Code** - Unique identifier
- **Title** - Department name
- **School Code** - Links to parent school
- **Finance Code** - For budget mapping

### Validation Rules
- Department must belong to a School
- School on Contract must be attached to the Department on Contract
- Finance codes must be valid and not disabled

---

## KEY VALIDATION RULES (SYSTEM HEALTH CHECKS)

1. **Staff Member Disabled Check**
   - If disabled, must have Service End Date
   - All contracts must end <= Service End Date

2. **Pension Check**
   - Pension on contract must not be disabled

3. **School-Department Check**
   - School on contract must be attached to the Department

4. **Overlapping Contracts Check**
   - No overlapping contracts for same staff/role/school/department (unless Reference differs)

5. **Pay Scale Check**
   - Pay Scale must not be disabled
   - Pay Point must exist on Pay Scale
   - Pay Rate must exist for Point for contract dates

6. **Staff Role Group Check**
   - Every contract must map to exactly one Staff Role Group
   - No orphan or unmapped finance codes

7. **Date Validation**
   - Contract dates within Staff Member service dates
   - Allowance dates within Contract dates
   - Adjustment dates within Contract dates

---

## STRAND 2 BUILD ORDER

The S2 build process must follow this order to ensure referential integrity:

1. **Pensions** - Load pension schemes first
2. **Equated Week Patterns** - Load EQWP codes
3. **Pay Scales** - Load scales, points, rates, grades
4. **Staff Role Groups** - Define role groupings
5. **Staff Roles** - Define roles and link to groups/pay scales
6. **Schools & Departments** - Load organizational structure
7. **Staff Members** - Load staff records
8. **Contracts** - Load contracts (references all above)
9. **Allowances** - Load allowances (references contracts)
10. **Adjustments** - Load adjustments (references contracts)

---

## COMMON CODING PATTERNS

### Pay Scale Codes
- **TMS** - Teachers Main Scale
- **UPS** - Upper Pay Scale
- **LEAD** - Leadership Scale
- **SUPP** - Support Staff Scale
- **SPOT** - Spot Salary (single point)

### Staff Role Group Codes
- **TEACH** - Teaching Staff
- **LEAD** - Leadership
- **ADMIN** - Administration
- **TECH** - Technicians
- **CLEAN** - Cleaning Staff
- **CATER** - Catering Staff
- **SITE** - Site Staff

### EQWP Codes
- **52WK** - All year (52 weeks)
- **39WK** - Term time (39 weeks)
- **44WK** - Term + holidays (44 weeks)

### Pension Codes
- **LGPS** - Local Government Pension Scheme
- **TPS** - Teachers' Pension Scheme
- **NOPEN** - No Pension

---

## NOTES FOR S2 SPECIALIST AGENT

- Always validate dates: Contract dates must be within Staff Member service dates
- Always validate relationships: School must link to Department, Role must link to Pay Scale
- Always check for disabled records: Pensions, Pay Scales, Staff Roles must be enabled
- Always maintain referential integrity: Build in the correct order (see Build Order above)
- Always handle overlapping contracts: Use Reference field if needed
- Always map to Finance Codes: Every contract must map to a Staff Role Group with a Finance Code
- Always validate FTE vs Hours: Teaching = FTE (0.0-1.0), Support = Hours per week
