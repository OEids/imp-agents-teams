# MEMORY.md - Long-Term Memory

> **READ THIS FIRST EVERY SESSION**
> Last updated: 2026-02-19

## Pre-Test Validation (ALWAYS RUN THIS)

```bash
python validate.py        # Quick check - syntax + undefined names
python validate.py --full # Full check - also tests imports
```

Run this BEFORE testing with `streamlit run app.py`. Catches:
- Syntax errors
- Undefined variable/method names (like `self._parse_date`)
- Missing attributes

---

## Who You Are

- Working on **agent-teams** project - a multi-strand data processing system
- Domain: Education/School financial planning (UK schools, MATs - Multi-Academy Trusts)
- Technical: Python, pandas, Excel processing, Streamlit apps

---

## Active Projects

### Agent-Teams System
- **Purpose**: Process customer data into standardized templates for school budget planning
- **Three Strands**:
  - S1 (Structure): School organizational data
  - S2 (Staff): Staff members, contracts, pay scales, allowances
  - S3 (Financial): Financial/budget data
- **Key Components**:
  - `app.py` - Streamlit UI
  - `teams/s2_specialist.py` - S2 data processor
  - `teams/payscale_extractor.py` - Extracts pay scales from Excel files
  - `teams/expert_agents.py` - Multi-phase agent orchestration
- **Customer Data Location**: `C:\claude\customer data\S2\`
- **Knowledge Base**: `knowledge/S2/` (DEM003 format templates - FOR SCHEMA ONLY)

---

## Key Decisions & Why

### 2026-02-12: Data Source Architecture Fix
- **Decision**: Customer data is PRIMARY source; knowledge base is for FORMAT only
- **Why**: System was incorrectly pulling 580 staff from DEM003 import files instead of 825 from actual customer data
- **Implementation**: Added DataProvenance tracking, restructured process() phases, protected build methods from overwriting customer data

---

## Lessons Learned / Mistakes to Avoid

### 2026-02-19: Undefined Method Calls
- **Mistake**: Code called `self._parse_date()` but method never existed - used `format_date_uk()` instead
- **Fix**: Replaced all `self._parse_date(val)` with `format_date_uk(val)` (module-level function)
- **Rule**: After editing code, ALWAYS run `python -m py_compile <file>` to catch syntax/attribute errors
- **Prevention**: Add a pre-commit check or test that imports all modules to catch AttributeErrors early

### 2026-02-12
- **Mistake**: Sheet detection picked "Staff Contract Checklist" over "Staff Contract Information"
- **Fix**: Prioritize sheets with "Information" in name, exclude "Checklist"
- **Rule**: Always check Excel sheet names carefully - similar names can cause wrong data source

---

## Your Preferences

*(To be learned over time)*

---

## Communication Style

*(To be learned over time)*

---

## What Annoys You

*(To be learned over time)*

---

## Goals

*(To be learned over time)*

---

## Daily Journals Index

- [2026-02-12](memory/2026-02-12.md) - First session, data source fix, memory system created
