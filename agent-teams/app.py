"""
IMP Planner Agent Teams - Web Application

A web interface for managing and running the S1, S2, S3 agent teams.
"""
from docx import Document

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# Import config settings
from config.settings import (
    TEAMS as SETTINGS_TEAMS,
    get_data_directory,
    set_data_directory,
    get_templates_directory,
    set_templates_directory,
    get_reports_directory,
    set_reports_directory,
    load_user_config,
    refresh_paths,
    INTELLIGENCE_CONFIG,
    get_intelligence_config,
)

# Import Intelligence Module (optional)
try:
    from intelligence import InferenceEngine, ConfidenceLevel
    INFERENCE_AVAILABLE = True
except ImportError:
    INFERENCE_AVAILABLE = False

# Import PreFlightValidator (optional)
try:
    from teams.preflight_validator import PreFlightValidator, validate_files
    PREFLIGHT_AVAILABLE = True
except ImportError:
    PREFLIGHT_AVAILABLE = False

import os

# Page config
st.set_page_config(
    page_title="IMP Agent Teams",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base paths
BASE_DIR = Path(__file__).parent

# Load paths from config
CUSTOMER_DATA_DIR = get_data_directory()
TEMPLATES_DIR = get_templates_directory()
REPORTS_DIR = get_reports_directory()

KNOWLEDGE_DIR = BASE_DIR / "knowledge"
SCOPE_DOCS_DIR = REPORTS_DIR / "scope_docs"
LC_LOCATIONS_FILE = BASE_DIR / "config" / "lc_locations.json"
PROJECTS_FILE = BASE_DIR / "config" / "projects.json"
LC_DOCS_DIR = REPORTS_DIR / "lc_docs"

# Ensure directories exist
REPORTS_DIR.mkdir(exist_ok=True)
for strand in ["S1", "S2", "S3"]:
    (CUSTOMER_DATA_DIR / strand).mkdir(parents=True, exist_ok=True)


# =============================================================================
# TEAM DEFINITIONS
# =============================================================================

TEAMS = {
    "S1": {
        "name": "Structure Team",
        "icon": "🏗️",
        "color": "#4CAF50",
        "description": "Specialist Agent - Handles finance codes, schools, departments, and Chart of Accounts",
        "capabilities": [
            "🤖 Deep analysis of customer structure data",
            "📊 Auto Chart of Accounts extraction from customer files",
            "DFE COA mapping & finance code normalization",
            "School/department extraction with URN/LA lookup",
            "Validation & External Audit with scoring",
            "Auto-builds: FinanceCodes, Schools, Depts, Activity, Ledger",
        ],
        "template": "AA_New - Strand 1 Standard Workbook API",
        "knowledge_files": ["Strand 1 Process Notes.xlsx", "Strand 1 Training Notes.xlsx"],
    },
    "S2": {
        "name": "Staff Team",
        "icon": "👥",
        "color": "#2196F3",
        "description": "Specialist Agent - Processes staff contracts, pay scales, and personnel data",
        "capabilities": [
            "🤖 Deep analysis extracts ALL pay scales & points",
            "📊 Auto pay scale extraction from customer Excel files",
            "Pay scale setup (MPS, UPS, Leadership, NJC)",
            "Staff role classification (15 DFE groups)",
            "Contract building (Teaching FTE / Support Hours)",
            "Allowance extraction (TLR, SEN, etc.)",
            "Auto-builds: PayScales, StaffMembers, Contracts, EQWPatterns",
        ],
        "template": "AA_New - Strand 2 Standard Workbook API",
        "knowledge_files": ["Process Notes - Strand 2 (Structure).docx", "Process Notes - Strand 2 (Contracts).docx"],
    },
    "S3": {
        "name": "Financial Team",
        "icon": "💰",
        "color": "#FF9800",
        "description": "Specialist Agent - Manages budgets, grants, funding, and pupil numbers",
        "capabilities": [
            "🤖 Deep analysis of budget & financial data",
            "📊 Auto pupil number extraction from census data",
            "Grant calculations (DFC, SCA, PE, UIFSM, Pupil Premium)",
            "Income/Expenditure line processing",
            "Validation & External Audit with scoring",
            "Auto-builds: Pupils, Funding, Calculators, Income, Expenditure",
        ],
        "template": "AA_New - Strand 3 Standard Workbook API",
        "knowledge_files": ["Strand 3 - Workbook - Phase 1.docx", "Strand 3 - Workbook - Phase 2.docx"],
    },
}


# =============================================================================
# SESSION STATE
# =============================================================================

if "processing_status" not in st.session_state:
    st.session_state.processing_status = {}
if "auto_process" not in st.session_state:
    st.session_state.auto_process = False
if "selected_team" not in st.session_state:
    st.session_state.selected_team = "S2"
# Pre-flight validation state
if "column_mappings" not in st.session_state:
    st.session_state.column_mappings = {}  # team_id -> mapping dict
if "mapping_validated" not in st.session_state:
    st.session_state.mapping_validated = {}  # team_id -> bool
if "validation_results" not in st.session_state:
    st.session_state.validation_results = {}  # team_id -> FileValidationResult dict
if "preflight_validator" not in st.session_state:
    st.session_state.preflight_validator = None
if "custom_mappings" not in st.session_state:
    st.session_state.custom_mappings = {}  # stores custom typed mappings


# =============================================================================
# STANDARD FIELD NAMES FOR COLUMN MAPPING
# =============================================================================

# All valid S2 field names that users can map to
S2_FIELD_OPTIONS = [
    # Staff identification
    "payroll_number", "employee_id", "staff_code", "staff_id",
    # Names
    "surname", "forename", "first_name", "last_name", "name", "title",
    # Job/Role
    "job_title", "position", "role", "post", "staff_role_code", "staff_role_group",
    # School/Location
    "school_code", "school", "cost_centre", "department", "location",
    # Hours & FTE
    "weekly_hours", "ft_hours", "full_time_hours", "fte", "weekly_fte",
    "hours_per_week", "contracted_hours", "hours",
    # Pay scales
    "pay_scale", "pay_scale_type", "pay_scale_code", "scale", "grade",
    "scale_point", "current_scale_point", "scp", "point", "spine_point",
    # Salary
    "annual_salary", "salary", "actual_salary", "gross_salary", "rate",
    # Pension
    "pension", "pension_code", "pension_scheme",
    # Dates
    "service_start_date", "start_date", "contract_start", "hire_date",
    "end_date", "leave_date", "date_of_birth", "dob",
    # Contract
    "contract_ref", "contract_type", "reference", "contract_code",
    # Other
    "gender", "ni_number", "national_insurance",
    "eqw", "eqw_pattern", "weeks_worked", "weeks_paid",
    "finance_code", "fund_code", "nominal_code",
    # Allowances
    "allowance_type", "allowance_code", "tlr", "sen_allowance",
]

# All valid S1 field names
S1_FIELD_OPTIONS = [
    "finance_code", "fund_code", "activity_code", "ledger_code",
    "school_code", "school_name", "urn", "la_code",
    "department_code", "department_name",
    "cost_centre", "nominal_code", "description",
]

# All valid S3 field names
S3_FIELD_OPTIONS = [
    "school_code", "pupil_count", "fte_pupils",
    "grant_code", "grant_name", "grant_amount",
    "income_code", "expenditure_code", "budget_amount",
]

def get_field_options_for_strand(strand: str) -> list:
    """Get all valid field names for a strand."""
    if strand == "S1":
        return S1_FIELD_OPTIONS
    elif strand == "S2":
        return S2_FIELD_OPTIONS
    elif strand == "S3":
        return S3_FIELD_OPTIONS
    return []

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_customer_files(team_id: str) -> list:
    """Get list of customer data files for a team."""
    team_dir = CUSTOMER_DATA_DIR / team_id
    files = []
    if team_dir.exists():
        for ext in ["*.xlsx", "*.xlsm", "*.xls", "*.csv"]:
            files.extend(team_dir.rglob(ext))
    return [f for f in files if not f.name.startswith("~$")]


def get_recent_reports(team_id: str, limit: int = 5) -> list:
    """Get recent report files for a team."""
    # Look for both old format and new specialist agent format
    reports = list(REPORTS_DIR.glob(f"{team_id}_*.xlsx"))
    reports += list(REPORTS_DIR.glob(f"{team_id}_complete_template_*.xlsx"))
    # Also check output folder
    output_dir = BASE_DIR / "output"
    if output_dir.exists():
        reports += list(output_dir.glob(f"{team_id}_*.xlsx"))
        reports += list(output_dir.glob(f"{team_id}_complete_template_*.xlsx"))
    # Remove duplicates and sort
    reports = list(set(reports))
    reports.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return reports[:limit]


def run_team_processing(team_id: str, column_mappings: dict = None) -> dict:
    """Run the data processing for a team using specialist agents.

    Args:
        team_id: The team/strand to process (S1, S2, S3)
        column_mappings: Optional dict of validated column mappings from pre-flight validation

    Returns:
        Processing result dictionary
    """
    customer_dir = CUSTOMER_DATA_DIR / team_id
    output_dir = REPORTS_DIR

    # Get validated mappings from session state if not provided
    if column_mappings is None:
        column_mappings = st.session_state.column_mappings.get(team_id, {})

    if team_id == "S1":
        from teams.s1_specialist import run_s1_specialist
        result = run_s1_specialist(customer_dir, output_dir, column_mappings=column_mappings)
        return {
            "success": result.get("success", False),
            "summary": result.get("summary", {}),
            "issues": result.get("issues", []),
            "assumptions": result.get("assumptions", []),
            "output_file": result.get("output_file"),
            "template_sheets": result.get("template_sheets", {})
        }
    elif team_id == "S2":
        from teams.s2_specialist import run_s2_specialist
        result = run_s2_specialist(customer_dir, output_dir, column_mappings=column_mappings)
        return {
            "success": result.get("success", False),
            "summary": result.get("summary", {}),
            "issues": result.get("issues", []),
            "assumptions": result.get("assumptions", []),
            "output_file": result.get("output_file"),
            "template_sheets": result.get("template_sheets", {})
        }
    elif team_id == "S3":
        from teams.s3_specialist import run_s3_specialist
        result = run_s3_specialist(customer_dir, output_dir, column_mappings=column_mappings)
        return {
            "success": result.get("success", False),
            "summary": result.get("summary", {}),
            "issues": result.get("issues", []),
            "assumptions": result.get("assumptions", []),
            "output_file": result.get("output_file"),
            "template_sheets": result.get("template_sheets", {})
        }
    else:
        return {
            "success": False,
            "summary": {},
            "issues": [f"{team_id} processor not recognized"],
            "assumptions": [],
            "output_file": None,
            "template_sheets": {}
        }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _split_lines(value: str) -> list:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _k(prefix: str, name: str) -> str:
    return f"{prefix}_{name}"


def _extract_text_from_upload(uploaded_file) -> str:
    if not uploaded_file:
        return ""
    if isinstance(uploaded_file, Path):
        name = uploaded_file.name.lower()
        if name.endswith(".txt"):
            return uploaded_file.read_text(encoding="utf-8", errors="ignore")
        if name.endswith(".json"):
            try:
                payload = json.loads(uploaded_file.read_text(encoding="utf-8", errors="ignore"))
                return _extract_text_from_json(payload)
            except Exception:
                return ""
        if name.endswith(".docx"):
            doc = Document(str(uploaded_file))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return ""

    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")
    if name.endswith(".json"):
        try:
            payload = json.loads(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
            return _extract_text_from_json(payload)
        except Exception:
            return ""
    if name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ""


def _extract_text_from_json(payload) -> str:
    """Best-effort extraction for transcript JSON shapes."""
    if payload is None:
        return ""
    # Common shapes: {"text": "..."} or {"transcript": "..."}
    if isinstance(payload, dict):
        for key in ["text", "transcript", "content", "body", "sentence"]:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        # Fireflies-like: {"utterances":[{"speaker":"", "text":""}, ...]}
        for key in ["utterances", "segments", "results", "messages"]:
            items = payload.get(key)
            if isinstance(items, list):
                lines = []
                for item in items:
                    if isinstance(item, dict):
                        text = item.get("text") or item.get("content") or item.get("utterance") or item.get("sentence")
                        speaker = item.get("speaker") or item.get("name")
                        if text:
                            line = f"{speaker}: {text}" if speaker else str(text)
                            lines.append(line)
                if lines:
                    return "\n".join(lines)
        # Nested structures: try values that are lists
        for value in payload.values():
            if isinstance(value, list):
                lines = []
                for item in value:
                    if isinstance(item, dict):
                        text = item.get("text") or item.get("content") or item.get("utterance") or item.get("sentence")
                        if text:
                            lines.append(str(text))
                if lines:
                    return "\n".join(lines)
        return ""
    if isinstance(payload, list):
        lines = []
        for item in payload:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("utterance") or item.get("sentence")
                speaker = item.get("speaker") or item.get("name")
                if text:
                    line = f"{speaker}: {text}" if speaker else str(text)
                    lines.append(line)
            elif isinstance(item, str):
                lines.append(item)
        return "\n".join(lines)
    if isinstance(payload, str):
        return payload
    return ""


def _list_scope_templates() -> list:
    templates = []
    if KNOWLEDGE_DIR.exists():
        for path in KNOWLEDGE_DIR.rglob("*.docx"):
            if "scope" in path.name.lower():
                templates.append(path)
    return sorted(templates)


def _load_projects() -> list:
    if PROJECTS_FILE.exists():
        try:
            data = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
            projects = data.get("projects", [])
            return [p for p in projects if isinstance(p, str) and p.strip()]
        except Exception:
            return []
    return []


def _get_project_dir(project: str, strand_id: str) -> Path:
    return CUSTOMER_DATA_DIR / project / strand_id


def _get_uploaded_sheet_names(project: str, strand_id: str) -> set:
    uploaded = set()
    if not project:
        return uploaded
    folder = _get_project_dir(project, strand_id)
    if not folder.exists():
        return uploaded
    for file in folder.rglob("*"):
        if file.name.startswith("~$"):
            continue
        if file.suffix.lower() in [".xlsx", ".xlsm", ".xls"]:
            try:
                xl = pd.ExcelFile(file)
                for sheet in xl.sheet_names:
                    uploaded.add(sheet)
            except Exception:
                continue
    return uploaded


def _load_lc_locations() -> list:
    if LC_LOCATIONS_FILE.exists():
        try:
            data = json.loads(LC_LOCATIONS_FILE.read_text(encoding="utf-8"))
            locations = data.get("locations", [])
            return [loc for loc in locations if isinstance(loc, str) and loc.strip()]
        except Exception:
            return []
    return []


def _slugify_local(value: str) -> str:
    cleaned = []
    for ch in value.strip().lower():
        if ch.isalnum():
            cleaned.append(ch)
        elif ch in [" ", "-", "_"]:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "customer"


def _render_lc_documents(locations: list, customers: list, key_prefix: str = "lc"):
    st.subheader("Project Documentation")
    st.caption("Store and download project documents by customer and location.")

    if not locations:
        st.info("No locations configured. Edit config/lc_locations.json to add locations.")
        return

    customer_options = customers + ["(New customer)"]
    customer_choice = st.selectbox("Customer", customer_options, key=_k(key_prefix, "docs_customer"))
    if customer_choice == "(New customer)":
        customer_name = st.text_input("Customer name", key=_k(key_prefix, "docs_customer_name"))
    else:
        customer_name = customer_choice

    location = st.selectbox("Location", locations, key=_k(key_prefix, "docs_location"))
    if not customer_name.strip():
        st.info("Enter a customer name to manage documents.")
        return

    customer_dir = LC_DOCS_DIR / _slugify_local(customer_name)
    location_dir = customer_dir / _slugify_local(location)
    location_dir.mkdir(parents=True, exist_ok=True)

    uploaded = st.file_uploader(
        "Upload documents",
        type=None,
        accept_multiple_files=True,
        key=_k(key_prefix, f"docs_{location}")
    )
    if uploaded:
        for file in uploaded:
            out_path = location_dir / file.name
            with open(out_path, "wb") as f:
                f.write(file.getbuffer())
        st.success(f"Uploaded {len(uploaded)} file(s) for {customer_name} / {location}.")

    files = sorted(location_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        st.info("No documents uploaded for this location.")
        return

    for doc in files:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{doc.name}**")
            st.caption(datetime.fromtimestamp(doc.stat().st_mtime).strftime("%Y-%m-%d %H:%M"))
        with col2:
            with open(doc, "rb") as f:
                st.download_button(
                    "Download",
                    data=f.read(),
                    file_name=doc.name,
                    key=_k(key_prefix, f"dl_doc_{customer_name}_{location}_{doc.name}")
                )


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/robot-2.png", width=80)
        st.title("IMP Agent Teams")
        st.markdown("---")

        st.caption(f"Data folder: {CUSTOMER_DATA_DIR}")
        st.markdown("---")

        # Team selection
        st.subheader("Select Team")
        for team_id, team in TEAMS.items():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"### {team['icon']}")
            with col2:
                if st.button(f"{team['name']}", key=f"btn_{team_id}", use_container_width=True):
                    st.session_state.selected_team = team_id

        st.markdown("---")

        # Auto-processing toggle
        st.subheader("⚡ Auto-Processing")
        auto = st.toggle("Enable auto-processing", value=st.session_state.auto_process)
        st.session_state.auto_process = auto
        if auto:
            st.success("✅ ON - Auto-process uploads")
            # Show process all button when auto-processing is on
            if st.button("🚀 Process All Teams", use_container_width=True):
                for tid in TEAMS:
                    files = get_customer_files(tid)
                    if files:
                        with st.spinner(f"Processing {tid}..."):
                            result = run_team_processing(tid)
                            st.session_state.processing_status[tid] = result
                st.success("All teams processed!")
                st.rerun()
        else:
            st.info("Manual mode")

        st.markdown("---")

        # Quick stats
        st.subheader("📊 Quick Stats")
        for team_id in TEAMS:
            files = get_customer_files(team_id)
            reports = get_recent_reports(team_id)
            st.metric(f"{team_id} Files", len(files), f"{len(reports)} reports")

        st.markdown("---")

        # App Sync Check
        st.subheader("🔄 App Sync")
        if st.button("Check Sync Status", use_container_width=True):
            try:
                from teams.app_sync_agent import run_app_sync_check
                result = run_app_sync_check()
                if result["synced"]:
                    st.success("All teams synchronized!")
                else:
                    for tid, report in result["reports"].items():
                        if report["missing_in_app"]:
                            st.warning(f"{tid}: Missing {report['missing_in_app']}")
            except Exception as e:
                st.error(f"Sync check failed: {e}")

        st.markdown("---")

        # Cleanup Controls
        st.subheader("🧹 Cleanup")
        cleanup_col1, cleanup_col2 = st.columns(2)
        with cleanup_col1:
            if st.button("End of Day", use_container_width=True, help="Keep only latest file per strand"):
                try:
                    from teams.cleanup_agent import run_end_of_day_cleanup
                    result = run_end_of_day_cleanup()
                    if result["files_removed"] > 0:
                        st.success(f"Removed {result['files_removed']} files")
                    else:
                        st.info("No files to clean up")
                except Exception as e:
                    st.error(f"Cleanup failed: {e}")
        with cleanup_col2:
            if st.button("View Storage", use_container_width=True):
                try:
                    from teams.cleanup_agent import get_storage_summary
                    summary = get_storage_summary()
                    st.caption(f"Total: {summary['total_files']} files ({summary['total_size']/1024:.1f} KB)")
                    for strand, data in summary["by_strand"].items():
                        st.caption(f"  {strand}: {data['count']} files")
                except Exception as e:
                    st.error(f"Error: {e}")

        # Remove Customer Data button
        if st.button("🗑️ Remove Customer Data", use_container_width=True, help="Remove all customer data files"):
            st.session_state.show_remove_confirm = True

        if st.session_state.get("show_remove_confirm", False):
            st.warning("⚠️ This will delete all customer data files!")
            remove_scope = st.radio(
                "Select scope:",
                ["Current team only", "All teams"],
                key="remove_scope",
                horizontal=True
            )
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Confirm Delete", use_container_width=True, type="primary"):
                    try:
                        files_removed = 0
                        if remove_scope == "Current team only":
                            team_dir = CUSTOMER_DATA_DIR / st.session_state.selected_team
                            if team_dir.exists():
                                for f in team_dir.rglob("*"):
                                    if f.is_file() and not f.name.startswith("~$"):
                                        f.unlink()
                                        files_removed += 1
                        else:
                            for strand in ["S1", "S2", "S3"]:
                                strand_dir = CUSTOMER_DATA_DIR / strand
                                if strand_dir.exists():
                                    for f in strand_dir.rglob("*"):
                                        if f.is_file() and not f.name.startswith("~$"):
                                            f.unlink()
                                            files_removed += 1
                        st.session_state.show_remove_confirm = False
                        st.success(f"Removed {files_removed} customer data file(s)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error removing files: {e}")
            with col_cancel:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_remove_confirm = False
                    st.rerun()

        st.markdown("---")

        # Settings Section
        st.subheader("⚙️ Settings")

        # Data Directory Setting
        current_data_dir = str(get_data_directory())
        st.caption("Data Directory:")
        new_data_dir = st.text_input(
            "Data Directory",
            value=current_data_dir,
            key="data_dir_input",
            label_visibility="collapsed",
            help="Path to customer data folder"
        )

        if new_data_dir != current_data_dir:
            if st.button("Save Data Directory", use_container_width=True):
                if Path(new_data_dir).exists():
                    if set_data_directory(new_data_dir):
                        st.success("Data directory updated!")
                        st.rerun()  # Reloads module with new config
                    else:
                        st.error("Failed to save config")
                else:
                    st.warning("Directory does not exist")

        # Templates Directory Setting
        current_templates_dir = str(get_templates_directory())
        st.caption("Templates Directory:")
        new_templates_dir = st.text_input(
            "Templates Directory",
            value=current_templates_dir,
            key="templates_dir_input",
            label_visibility="collapsed",
            help="Path to template workbooks"
        )

        if new_templates_dir != current_templates_dir:
            if st.button("Save Templates Directory", use_container_width=True):
                if Path(new_templates_dir).exists():
                    if set_templates_directory(new_templates_dir):
                        st.success("Templates directory updated!")
                        st.rerun()  # Reloads module with new config
                    else:
                        st.error("Failed to save config")
                else:
                    st.warning("Directory does not exist")

        # Show current config
        with st.expander("View Config"):
            config = load_user_config()
            st.json(config)

        # Intelligence Module Settings
        if INFERENCE_AVAILABLE:
            st.markdown("---")
            st.subheader("🧠 Intelligence")

            intel_config = get_intelligence_config()
            conf_thresholds = intel_config.get("confidence", {})

            st.caption(f"High: >{conf_thresholds.get('high_threshold', 0.9):.0%}")
            st.caption(f"Medium: >{conf_thresholds.get('medium_threshold', 0.7):.0%}")

            behavior = intel_config.get("behavior", {})
            if behavior.get("enable_learning"):
                st.success("Learning: ON")
            else:
                st.info("Learning: OFF")

            with st.expander("Intelligence Stats"):
                try:
                    from teams.expert_agents import get_inference_engine
                    engine = get_inference_engine()
                    if engine:
                        stats = engine.get_stats()
                        st.json(stats)
                    else:
                        st.info("InferenceEngine not initialized")
                except Exception as e:
                    st.error(f"Error: {e}")


def render_team_overview(team_id: str):
    """Render the team overview section."""
    team = TEAMS[team_id]

    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {team['color']}22, {team['color']}11);
                padding: 20px; border-radius: 10px; border-left: 5px solid {team['color']};">
        <h1>{team['icon']} {team['name']}</h1>
        <p style="font-size: 1.2em; color: #666;">{team['description']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # Capabilities
    st.subheader("🎯 Capabilities")
    for cap in team["capabilities"]:
        st.markdown(f"- {cap}")


def render_data_upload(team_id: str):
    """Render the data upload section."""
    st.subheader("📤 Upload Customer Data")

    # Show auto-processing status
    if st.session_state.auto_process:
        st.success("⚡ Auto-processing is **ON** - Files will be processed immediately after upload")

    upload_dir = CUSTOMER_DATA_DIR / team_id
    st.caption(f"Upload to: {upload_dir}")

    uploaded_files = st.file_uploader(
        f"Upload files for {team_id}",
        type=["xlsx", "xlsm", "xls", "csv", "pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"upload_{team_id}"
    )

    if uploaded_files:
        upload_dir.mkdir(parents=True, exist_ok=True)

        for uploaded_file in uploaded_files:
            file_path = upload_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Uploaded: {uploaded_file.name}")

        if st.session_state.auto_process:
            st.info("🔄 Auto-processing triggered...")
            with st.spinner(f"Running {team_id} Specialist Agent..."):
                result = run_team_processing(team_id)
                st.session_state.processing_status[team_id] = result
                if result.get("success"):
                    st.success("✅ Auto-processing completed!")
                else:
                    st.warning("⚠️ Auto-processing completed with issues")


def render_customer_files(team_id: str):
    """Render the customer files section."""
    st.subheader("📁 Customer Data Files")

    files = get_customer_files(team_id)
    base_path = CUSTOMER_DATA_DIR / team_id

    st.caption(f"Data folder: {base_path}")

    if not files:
        st.info(f"No customer data files found for {team_id}. Upload files above.")
        return

    # Group by subfolder
    file_groups = {}
    for f in files:
        try:
            rel_path = f.relative_to(base_path)
            folder = str(rel_path.parent) if rel_path.parent != Path(".") else "Root"
        except ValueError:
            folder = "Root"
        if folder not in file_groups:
            file_groups[folder] = []
        file_groups[folder].append(f)

    for folder, folder_files in file_groups.items():
        with st.expander(f"📂 {folder} ({len(folder_files)} files)", expanded=folder == "Root"):
            for f in folder_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"📄 **{f.name}**")
                with col2:
                    st.caption(format_file_size(f.stat().st_size))
                with col3:
                    st.caption(datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"))


def render_processing(team_id: str):
    """Render the processing section."""
    st.subheader("⚙️ Process Data")

    # Show auto-processing status
    if st.session_state.auto_process:
        st.success("⚡ **Auto-Processing ENABLED** - Files will be processed automatically on upload")
    else:
        st.caption("💡 Enable auto-processing in sidebar to automatically process uploaded files")

    # Show specialist agent info
    agent_info = {
        "S1": "Structure Specialist - Finance codes, schools, departments, COA mapping",
        "S2": "Staff Specialist - Pay scales, staff roles, contracts, allowances",
        "S3": "Financial Specialist - Budgets, grants, pupil numbers, scenarios"
    }
    st.info(f"🤖 **{agent_info.get(team_id, 'Specialist Agent')}**")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button(f"🚀 Run {team_id} Specialist Agent", type="primary", use_container_width=True):
            with st.spinner(f"Running {team_id} Specialist Agent..."):
                result = run_team_processing(team_id)
                st.session_state.processing_status[team_id] = result

    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    with col3:
        if st.button("🗑️ Clear Results", use_container_width=True):
            if team_id in st.session_state.processing_status:
                del st.session_state.processing_status[team_id]
                st.rerun()

    # Show results
    if team_id in st.session_state.processing_status:
        result = st.session_state.processing_status[team_id]

        if result["success"]:
            st.success("✅ Processing completed successfully!")
        else:
            st.warning("⚠️ Processing completed with issues")

        # Summary metrics - team specific
        summary = result.get("summary", {})
        if summary:
            if team_id == "S2":
                cols = st.columns(4)
                cols[0].metric("Staff Members", summary.get("staff_members", 0))
                cols[1].metric("Staff Roles", summary.get("staff_roles", 0))
                cols[2].metric("Teaching Contracts", summary.get("teaching_contracts", 0))
                cols[3].metric("Support Contracts", summary.get("support_contracts", 0))

                cols2 = st.columns(4)
                cols2[0].metric("Pay Scales", summary.get("pay_scales", 0))
                cols2[1].metric("Pay Scale Points", summary.get("pay_scale_points", 0))
                audit_score = summary.get("audit_score", 0)
                cols2[2].metric("Audit Score", f"{audit_score:.1f}%")
                cols2[3].metric("Audit Passed", "YES" if summary.get("audit_passed", False) else "NO")

                # Show customer data load status
                customer_data_loaded = result.get("customer_data_loaded", False)
                if customer_data_loaded:
                    st.success("✅ Customer data successfully loaded and processed")
                else:
                    st.warning("⚠️ No customer data files found - using defaults")

                # Show audit status
                if summary.get("audit_passed", False):
                    st.success(f"✅ External Audit PASSED with score {audit_score:.1f}%")
                elif audit_score > 0:
                    st.warning(f"⚠️ External Audit FAILED with score {audit_score:.1f}%")

                # Show data source warnings
                data_warnings = result.get("data_source_warnings", [])
                if data_warnings:
                    with st.expander(f"📋 Data Source Warnings ({len(data_warnings)})", expanded=False):
                        for warning in data_warnings:
                            st.warning(warning)

                # Show detailed audit report for S2
                audit_data = result.get("audit", {})
                detailed_report = audit_data.get("detailed_report", {})
                if detailed_report:
                    issues = detailed_report.get("issues", [])
                    recommendations = detailed_report.get("recommendations", [])

                    if issues:
                        with st.expander(f"🔍 Audit Details - What's Missing & Why ({len(issues)} issues)", expanded=not summary.get("audit_passed", False)):
                            for issue in issues:
                                severity_icon = "🔴" if issue.get("severity") == "error" else "🟡" if issue.get("severity") == "warning" else "🔵"
                                st.markdown(f"### {severity_icon} {issue.get('check', 'Unknown Issue')}")
                                st.markdown(f"**Category:** {issue.get('category', '').replace('_', ' ').title()}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**What's Missing:**")
                                    st.info(issue.get("what_is_missing", "N/A"))
                                with col2:
                                    st.markdown("**Why It Matters:**")
                                    st.warning(issue.get("why_it_matters", "N/A"))

                                st.markdown("**How To Fix:**")
                                st.success(issue.get("how_to_fix", "N/A"))
                                st.markdown("---")

                    if recommendations:
                        with st.expander(f"💡 Recommendations ({len(recommendations)})", expanded=False):
                            for rec in recommendations:
                                priority_color = "🔴" if rec.get("priority") == "HIGH" else "🟡" if rec.get("priority") == "MEDIUM" else "🟢"
                                st.markdown(f"{priority_color} **[{rec.get('priority', '')}]** {rec.get('action', '')}")
                                st.caption(f"Reason: {rec.get('reason', '')}")

            elif team_id == "S1":
                cols = st.columns(4)
                cols[0].metric("Finance Codes", summary.get("finance_codes", 0))
                cols[1].metric("Schools", summary.get("schools", 0))
                cols[2].metric("Departments", summary.get("departments", 0))
                cols[3].metric("Validation Errors", summary.get("validation_errors", 0))

                cols2 = st.columns(4)
                cols2[0].metric("Validation Warnings", summary.get("validation_warnings", 0))
                audit_score = summary.get("audit_score", 0)
                cols2[1].metric("Audit Score", f"{audit_score:.1f}%")
                cols2[2].metric("Audit Passed", "YES" if summary.get("audit_passed", False) else "NO")
                cols2[3].empty()  # Placeholder

                # Show audit status
                if summary.get("audit_passed", False):
                    st.success(f"✅ External Audit PASSED with score {audit_score:.1f}%")
                elif audit_score > 0:
                    st.warning(f"⚠️ External Audit FAILED with score {audit_score:.1f}%")

                # Show detailed audit report if available
                audit_data = result.get("audit", {})
                detailed_report = audit_data.get("detailed_report", {})
                if detailed_report:
                    issues = detailed_report.get("issues", [])
                    recommendations = detailed_report.get("recommendations", [])

                    if issues:
                        with st.expander(f"🔍 Audit Details - What's Missing & Why ({len(issues)} issues)", expanded=not summary.get("audit_passed", False)):
                            for issue in issues:
                                severity_icon = "🔴" if issue.get("severity") == "error" else "🟡" if issue.get("severity") == "warning" else "🔵"
                                st.markdown(f"### {severity_icon} {issue.get('check', 'Unknown Issue')}")
                                st.markdown(f"**Category:** {issue.get('category', '').replace('_', ' ').title()}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**What's Missing:**")
                                    st.info(issue.get("what_is_missing", "N/A"))
                                with col2:
                                    st.markdown("**Why It Matters:**")
                                    st.warning(issue.get("why_it_matters", "N/A"))

                                st.markdown("**How To Fix:**")
                                st.success(issue.get("how_to_fix", "N/A"))

                                affected = issue.get("affected_records", [])
                                if affected:
                                    st.markdown(f"**Affected Records:** `{', '.join(affected[:10])}`" +
                                              (f" (+{len(affected)-10} more)" if len(affected) > 10 else ""))
                                st.markdown("---")

                    if recommendations:
                        with st.expander(f"💡 Recommendations ({len(recommendations)})", expanded=False):
                            for rec in recommendations:
                                priority_color = "🔴" if rec.get("priority") == "HIGH" else "🟡" if rec.get("priority") == "MEDIUM" else "🟢"
                                st.markdown(f"{priority_color} **[{rec.get('priority', '')}]** {rec.get('action', '')}")
                                st.caption(f"Reason: {rec.get('reason', '')}")

            elif team_id == "S3":
                cols = st.columns(4)
                cols[0].metric("Pupil Records", summary.get("pupils", 0))
                cols[1].metric("Grants", summary.get("grants", 0))
                cols[2].metric("Income Lines", summary.get("income_lines", 0))
                cols[3].metric("Expenditure Lines", summary.get("expenditure_lines", 0))

                cols2 = st.columns(4)
                schools = summary.get("schools", [])
                cols2[0].metric("Schools", len(schools) if isinstance(schools, list) else schools)
                audit_score = summary.get("audit_score", 0)
                cols2[1].metric("Audit Score", f"{audit_score:.1f}%")
                cols2[2].metric("Audit Passed", "YES" if summary.get("audit_passed", False) else "NO")
                cols2[3].empty()  # Placeholder

                # Show audit status
                if summary.get("audit_passed", False):
                    st.success(f"✅ External Audit PASSED with score {audit_score:.1f}%")
                elif audit_score > 0:
                    st.warning(f"⚠️ External Audit FAILED with score {audit_score:.1f}%")

                # Show detailed audit report for S3
                audit_data = result.get("audit", {})
                detailed_report = audit_data.get("detailed_report", {})
                if detailed_report:
                    issues = detailed_report.get("issues", [])
                    recommendations = detailed_report.get("recommendations", [])

                    if issues:
                        with st.expander(f"🔍 Audit Details - What's Missing & Why ({len(issues)} issues)", expanded=not summary.get("audit_passed", False)):
                            for issue in issues:
                                severity_icon = "🔴" if issue.get("severity") == "error" else "🟡" if issue.get("severity") == "warning" else "🔵"
                                st.markdown(f"### {severity_icon} {issue.get('check', 'Unknown Issue')}")
                                st.markdown(f"**Category:** {issue.get('category', '').replace('_', ' ').title()}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**What's Missing:**")
                                    st.info(issue.get("what_is_missing", "N/A"))
                                with col2:
                                    st.markdown("**Why It Matters:**")
                                    st.warning(issue.get("why_it_matters", "N/A"))

                                st.markdown("**How To Fix:**")
                                st.success(issue.get("how_to_fix", "N/A"))
                                st.markdown("---")

                    if recommendations:
                        with st.expander(f"💡 Recommendations ({len(recommendations)})", expanded=False):
                            for rec in recommendations:
                                priority_color = "🔴" if rec.get("priority") == "HIGH" else "🟡" if rec.get("priority") == "MEDIUM" else "🟢"
                                st.markdown(f"{priority_color} **[{rec.get('priority', '')}]** {rec.get('action', '')}")
                                st.caption(f"Reason: {rec.get('reason', '')}")

        # Template sheets built
        template_sheets = result.get("template_sheets", {})
        if template_sheets:
            with st.expander(f"📋 Template Sheets Built ({len(template_sheets)})", expanded=True):
                sheet_cols = st.columns(3)
                for idx, (sheet_name, df) in enumerate(template_sheets.items()):
                    col_idx = idx % 3
                    rows = len(df) if hasattr(df, '__len__') else 0
                    status = "✅" if rows > 0 else "⚪"
                    sheet_cols[col_idx].markdown(f"{status} **{sheet_name}**: {rows} rows")

        # S2-specific: Quick summary of processing details (full data in Excel output)
        if team_id == "S2":
            created_codes = result.get("created_role_codes", [])
            created_groups = result.get("created_role_groups", [])
            assumptions_list = result.get("assumptions", [])
            skipped_staff = result.get("skipped_staff", [])

            if created_codes or created_groups or assumptions_list or skipped_staff:
                with st.expander("📋 Processing Details (see output file for full data)", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Role Codes Created", len(created_codes))
                    col2.metric("Role Groups Created", len(created_groups))
                    col3.metric("Assumptions Made", len(assumptions_list))
                    col4.metric("Staff Skipped", len(skipped_staff))

                    st.caption("Full details available in output Excel file sheets: _CreatedRoleCodes, _CreatedRoleGroups, _Assumptions, _SkippedStaff")

                    if skipped_staff:
                        st.warning(f"⚠️ {len(skipped_staff)} staff records were skipped - check _SkippedStaff sheet for details")

        # Issues
        if result.get("issues"):
            with st.expander(f"⚠️ Issues ({len(result['issues'])})", expanded=True):
                for issue in result["issues"]:
                    st.error(issue)

        # Assumptions (for non-S2 teams, or as fallback)
        if team_id != "S2" and result.get("assumptions"):
            with st.expander(f"📝 Assumptions ({len(result['assumptions'])})"):
                for assumption in result["assumptions"]:
                    st.info(assumption)

        # Inference Details (if available)
        inference_result = result.get("inference_result")
        if inference_result:
            with st.expander("🧠 Inference Details", expanded=False):
                st.markdown("**Strand Detection Analysis**")

                # Confidence display
                confidence = inference_result.get("confidence", 0)
                conf_level = inference_result.get("confidence_level", "unknown")
                decision = inference_result.get("decision", "N/A")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Decision", decision)
                with col2:
                    st.metric("Confidence", f"{confidence:.0%}")
                with col3:
                    # Color-code confidence level
                    level_colors = {"high": "🟢", "medium": "🟡", "low": "🔴"}
                    st.metric("Level", f"{level_colors.get(conf_level, '⚪')} {conf_level.upper()}")

                # Reasoning
                reasoning = inference_result.get("reasoning", [])
                if reasoning:
                    st.markdown("**Reasoning:**")
                    for reason in reasoning:
                        st.markdown(f"- {reason}")

                # Alternatives
                alternatives = inference_result.get("alternatives", [])
                if alternatives:
                    st.markdown("**Alternatives Considered:**")
                    for alt in alternatives[:3]:
                        st.caption(f"• {alt.get('strand', 'N/A')}: {alt.get('confidence', 0):.0%}")

                # Review flag
                if inference_result.get("requires_review"):
                    st.warning("⚠️ This decision was flagged for review due to low confidence")

        # Reasoning Trail (for debugging)
        reasoning_trail = result.get("reasoning_trail")
        if reasoning_trail and st.checkbox("Show Full Reasoning Trail", key=f"trail_{team_id}"):
            with st.expander("🔍 Full Reasoning Trail (Debug)", expanded=False):
                st.json(reasoning_trail)

        # Download output
        output_file = result.get("output_file")
        if output_file and Path(output_file).exists():
            with open(output_file, "rb") as f:
                st.download_button(
                    label="📥 Download Template Data",
                    data=f.read(),
                    file_name=Path(output_file).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )


def render_reports(team_id: str):
    """Render the reports section."""
    st.subheader("📊 Recent Reports")

    reports = get_recent_reports(team_id, limit=10)

    if not reports:
        st.info("No reports generated yet. Run processing to create reports.")
        return

    for report in reports:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"📄 **{report.name}**")
        with col2:
            st.caption(datetime.fromtimestamp(report.stat().st_mtime).strftime("%Y-%m-%d %H:%M"))
        with col3:
            with open(report, "rb") as f:
                st.download_button(
                    "⬇️",
                    data=f.read(),
                    file_name=report.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{report.name}"
                )


def render_preview(team_id: str):
    """Render data preview section."""
    st.subheader("👁️ Data Preview")

    # Get latest report
    reports = get_recent_reports(team_id, limit=1)

    if not reports:
        st.info("No processed data to preview. Run processing first.")
        return

    report_file = reports[0]

    try:
        xl = pd.ExcelFile(report_file)

        selected_sheet = st.selectbox("Select sheet to preview", xl.sheet_names)

        if selected_sheet:
            df = pd.read_excel(xl, selected_sheet)

            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input("🔍 Search", placeholder="Filter rows...")
            with col2:
                max_rows = st.slider("Max rows", 10, 100, 25)

            # Apply filter
            if search:
                mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                df = df[mask]

            st.dataframe(df.head(max_rows), use_container_width=True)
            st.caption(f"Showing {min(len(df), max_rows)} of {len(df)} rows")

    except Exception as e:
        st.error(f"Error loading preview: {e}")


# =============================================================================
# VALIDATE & MAP TAB
# =============================================================================

def render_validate_and_map(team_id: str):
    """Render the Validate & Map tab for pre-flight column validation."""
    st.subheader("Validate & Map Columns")

    if not PREFLIGHT_AVAILABLE:
        st.warning("Pre-flight validation module not available. Install required dependencies.")
        return

    # Initialize validator if needed
    if st.session_state.preflight_validator is None:
        try:
            st.session_state.preflight_validator = PreFlightValidator()
        except Exception as e:
            st.error(f"Failed to initialize validator: {e}")
            return

    validator = st.session_state.preflight_validator

    # Step 1: File Selection
    st.markdown("### Step 1: Select Files to Validate")

    files = get_customer_files(team_id)

    if not files:
        st.info(f"No customer data files found for {team_id}. Upload files in the 'Upload & Files' tab first.")
        return

    # File checkboxes
    selected_files = []
    cols = st.columns(2)
    for idx, f in enumerate(files[:10]):  # Limit to 10 files
        col_idx = idx % 2
        with cols[col_idx]:
            if st.checkbox(f.name, key=f"validate_file_{f.name}_{team_id}", value=True):
                selected_files.append(f)

    if not selected_files:
        st.info("Select at least one file to validate.")
        return

    # Validate button
    if st.button("Analyze Selected Files", type="primary", use_container_width=True):
        with st.spinner("Analyzing columns..."):
            results = {}
            for file_path in selected_files:
                try:
                    result = validator.validate_file(file_path, strand=team_id)
                    key = f"{result.file_name}:{result.sheet_name or 'default'}"
                    results[key] = result
                except Exception as e:
                    st.error(f"Error validating {file_path.name}: {e}")

            st.session_state.validation_results[team_id] = results
            st.success(f"Analyzed {len(results)} file(s)")

    # Step 2: Show Results
    if team_id in st.session_state.validation_results and st.session_state.validation_results[team_id]:
        results = st.session_state.validation_results[team_id]

        st.markdown("### Step 2: Column Analysis Results")

        for file_key, result in results.items():
            with st.expander(f"**{result.file_name}** ({result.row_count} rows, {result.column_count} columns)", expanded=True):
                # Summary metrics
                summary = result.mapping_summary
                cols = st.columns(5)
                cols[0].metric("Matched", summary['matched'], help="Exact or variation matches")
                cols[1].metric("Review", summary['review'], help="Fuzzy matches needing review")
                cols[2].metric("Unmapped", summary['unmapped'], help="Could not map")
                cols[3].metric("Corrected", summary['corrected'], help="User corrections applied")
                cols[4].metric("Ignored", summary['ignored'], help="Columns marked to ignore")

                # Strand detection
                if result.detected_strand:
                    confidence_color = "green" if result.strand_confidence >= 0.8 else "orange" if result.strand_confidence >= 0.6 else "red"
                    st.markdown(f"**Detected Strand:** {result.detected_strand} (:{confidence_color}[{result.strand_confidence:.0%}])")

                # Warnings
                if result.warnings:
                    for warning in result.warnings:
                        st.warning(warning)

                # Column mappings by status
                if result.matched_columns:
                    # Filter out blank columns
                    matched_cols = [c for c in result.matched_columns if c.source_column and c.source_column.strip()]
                    if matched_cols:
                        st.markdown("**Matched Columns (auto-accepted)**")
                        matched_df = pd.DataFrame([
                            {"Source": c.source_column, "Mapped To": c.mapped_to, "Confidence": f"{c.confidence:.0%}"}
                            for c in matched_cols
                        ])
                        st.dataframe(matched_df, use_container_width=True, hide_index=True)

                if result.review_columns:
                    # Filter out blank columns
                    review_cols = [m for m in result.review_columns if m.source_column and m.source_column.strip()]
                    if review_cols:
                        st.markdown("**Review Suggested (fuzzy matches)**")
                        for mapping in review_cols:
                            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                            mapping_key = f"{file_key}_{mapping.source_column}"
                            with col1:
                                st.text(mapping.source_column)
                            with col2:
                                # Dropdown with fuzzy matches + all standard fields + custom option
                                fuzzy_options = [mapping.mapped_to or ""] + [alt[0] for alt in mapping.alternatives]
                                fuzzy_options = [opt for opt in fuzzy_options if opt]  # Remove empty

                                # Add all standard field options (exclude duplicates)
                                all_fields = get_field_options_for_strand(team_id)
                                standard_options = [f for f in all_fields if f not in fuzzy_options]

                                # Build final options: fuzzy matches first, then separator, then all fields
                                options = fuzzy_options.copy()
                                if standard_options:
                                    options.append("── All Fields ──")
                                    options.extend(standard_options)
                                options.append("-- Type custom --")
                                options.append("-- Ignore this column --")
                                options.append("-- Keep original --")

                                selected = st.selectbox(
                                    "Map to",
                                    options,
                                    key=f"map_{mapping_key}",
                                    label_visibility="collapsed"
                                )

                                if selected == "-- Type custom --":
                                    custom_value = st.text_input(
                                        "Custom mapping",
                                        key=f"custom_{mapping_key}",
                                        placeholder="Type column name...",
                                        label_visibility="collapsed"
                                    )
                                    # Store in session state for persistence
                                    if custom_value.strip():
                                        if "custom_mappings" not in st.session_state:
                                            st.session_state.custom_mappings = {}
                                        st.session_state.custom_mappings[mapping_key] = custom_value.strip()
                                        mapping.user_override = custom_value.strip()
                                    elif mapping_key in st.session_state.get("custom_mappings", {}):
                                        # Retrieve from session state if already set
                                        mapping.user_override = st.session_state.custom_mappings[mapping_key]
                                elif selected == "-- Ignore this column --":
                                    mapping.ignored = True
                                    mapping.user_override = None
                                elif selected == "-- Keep original --":
                                    mapping.user_override = mapping.source_column
                                elif selected == "── All Fields ──":
                                    pass  # Separator, do nothing
                                elif selected != mapping.mapped_to:
                                    mapping.user_override = selected
                            with col3:
                                st.caption(f"Score: {mapping.confidence:.0%}")
                            with col4:
                                # Sample values
                                if mapping.sample_values:
                                    st.caption(f"e.g., {str(mapping.sample_values[0])[:20]}")

                if result.unmapped_columns:
                    # Filter out blank columns
                    unmapped_cols = [m for m in result.unmapped_columns if m.source_column and m.source_column.strip()]
                    if unmapped_cols:
                        st.markdown("**Unmapped Columns (needs manual mapping)**")
                        for mapping in unmapped_cols:
                            col1, col2, col3 = st.columns([3, 4, 3])
                            mapping_key = f"unmap_{file_key}_{mapping.source_column}"
                            with col1:
                                st.text(mapping.source_column)
                            with col2:
                                # Get suggestions + all standard fields + custom option
                                suggestions = [alt[0] for alt in mapping.alternatives] if mapping.alternatives else []

                                # Add all standard field options (exclude duplicates)
                                all_fields = get_field_options_for_strand(team_id)
                                standard_options = [f for f in all_fields if f not in suggestions]

                                # Build options: suggestions first, then all fields, then actions
                                options = suggestions.copy()
                                if standard_options:
                                    options.append("── All Fields ──")
                                    options.extend(standard_options)
                                options.append("-- Type custom --")
                                options.append("-- Ignore this column --")
                                options.append("-- Keep original --")

                                # Default to first option
                                default_idx = 0

                                selected = st.selectbox(
                                    "Map to",
                                    options,
                                    key=f"select_{mapping_key}",
                                    label_visibility="collapsed",
                                    index=default_idx
                                )

                                if selected == "-- Type custom --":
                                    custom_value = st.text_input(
                                        "Custom mapping",
                                        key=f"custom_{mapping_key}",
                                        placeholder="Type column name...",
                                        label_visibility="collapsed"
                                    )
                                    # Store in session state for persistence
                                    if custom_value.strip():
                                        if "custom_mappings" not in st.session_state:
                                            st.session_state.custom_mappings = {}
                                        st.session_state.custom_mappings[mapping_key] = custom_value.strip()
                                        mapping.user_override = custom_value.strip()
                                    elif mapping_key in st.session_state.get("custom_mappings", {}):
                                        # Retrieve from session state if already set
                                        mapping.user_override = st.session_state.custom_mappings[mapping_key]
                                elif selected == "-- Ignore this column --":
                                    mapping.ignored = True
                                elif selected == "-- Keep original --":
                                    mapping.user_override = mapping.source_column
                                elif selected == "── All Fields ──":
                                    pass  # Separator, do nothing
                                else:
                                    mapping.user_override = selected
                            with col3:
                                if mapping.sample_values:
                                    st.caption(f"e.g., {str(mapping.sample_values[0])[:20]}")

        # Step 3: Confirm & Proceed
        st.markdown("### Step 3: Confirm & Proceed")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Mappings", type="primary", use_container_width=True):
                # Collect all final mappings, including custom values from session state
                all_mappings = {}
                custom_maps = st.session_state.get("custom_mappings", {})

                for file_key, result in results.items():
                    file_mappings = {}
                    for mapping in result.column_mappings:
                        # Check for custom mapping in session state first
                        review_key = f"{file_key}_{mapping.source_column}"
                        unmap_key = f"unmap_{file_key}_{mapping.source_column}"

                        if review_key in custom_maps:
                            file_mappings[mapping.source_column] = custom_maps[review_key]
                        elif unmap_key in custom_maps:
                            file_mappings[mapping.source_column] = custom_maps[unmap_key]
                        elif mapping.final_mapping:
                            file_mappings[mapping.source_column] = mapping.final_mapping

                    all_mappings[file_key] = file_mappings

                st.session_state.column_mappings[team_id] = all_mappings
                st.session_state.mapping_validated[team_id] = True
                st.success("Mappings confirmed! You can now proceed to Process tab.")

        with col2:
            if st.button("Clear & Re-analyze", use_container_width=True):
                if team_id in st.session_state.validation_results:
                    del st.session_state.validation_results[team_id]
                if team_id in st.session_state.column_mappings:
                    del st.session_state.column_mappings[team_id]
                if team_id in st.session_state.mapping_validated:
                    del st.session_state.mapping_validated[team_id]
                # Clear custom mappings for this team
                st.session_state.custom_mappings = {k: v for k, v in st.session_state.custom_mappings.items() if team_id not in k}
                st.rerun()

        # Show validation status
        if st.session_state.mapping_validated.get(team_id, False):
            st.success("Mappings have been validated and confirmed.")

            # Show final mappings summary
            with st.expander("View Final Mappings"):
                all_mappings = st.session_state.column_mappings.get(team_id, {})
                for file_key, mappings in all_mappings.items():
                    st.markdown(f"**{file_key}**")
                    if mappings:
                        mapping_df = pd.DataFrame([
                            {"Source": k, "Mapped To": v}
                            for k, v in mappings.items()
                        ])
                        st.dataframe(mapping_df, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No mappings")


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application entry point."""
    render_sidebar()

    team_id = st.session_state.selected_team

    # Main content area
    render_team_overview(team_id)

    st.markdown("---")

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload & Files",
        "Validate & Map",
        "⚙️ Process",
        "📊 Reports",
        "👁️ Preview"
    ])

    with tab1:
        render_data_upload(team_id)
        st.markdown("---")
        render_customer_files(team_id)

    with tab2:
        render_validate_and_map(team_id)

    with tab3:
        render_processing(team_id)

    with tab4:
        render_reports(team_id)

    with tab5:
        render_preview(team_id)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888;'>"
        "IMP Planner Agent Teams v2.0 | Specialist Agents | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
