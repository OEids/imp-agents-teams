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
from config.settings import TEAMS as SETTINGS_TEAMS


import os

def env_path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser()

BASE_DIR = Path(__file__).parent

# Use env vars, fall back to project-local folders (portable)
DATA_ROOT = env_path("IMP_DATA_ROOT", BASE_DIR / "data")
CUSTOMER_DATA_DIR = env_path("IMP_CUSTOMER_DATA_DIR", DATA_ROOT / "customer_data")
TEMPLATES_DIR = env_path("IMP_TEMPLATES_DIR", DATA_ROOT / "templates")

KNOWLEDGE_DIR = BASE_DIR / "knowledge"
REPORTS_DIR = env_path("IMP_REPORTS_DIR", BASE_DIR / "reports")

SCOPE_DOCS_DIR = REPORTS_DIR / "scope_docs"
LC_DOCS_DIR = REPORTS_DIR / "lc_docs"

LC_LOCATIONS_FILE = BASE_DIR / "config" / "lc_locations.json"
PROJECTS_FILE = BASE_DIR / "config" / "projects.json"


# Page config
st.set_page_config(
    page_title="IMP Agent Teams",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
BASE_DIR = Path(__file__).parent
CUSTOMER_DATA_DIR = Path(r"C:\claude\customer data")
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
REPORTS_DIR = BASE_DIR / "reports"
TEMPLATES_DIR = Path(r"C:\claude\database planner\templates")
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
            "DFE COA mapping & finance code normalization",
            "School/department/fund extraction",
            "System grouping codes & ledger setup",
            "Auto-builds: FinanceCodes, Schools, Depts, Funds, Activity, Ledger",
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
            "Grant calculations (DFC, SCA, PE, UIFSM, Pupil Premium)",
            "Pupil number processing (Spring/Autumn census)",
            "Budget manipulation and scenarios",
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


def run_team_processing(team_id: str) -> dict:
    """Run the data processing for a team using specialist agents."""
    customer_dir = CUSTOMER_DATA_DIR / team_id
    output_dir = REPORTS_DIR

    if team_id == "S1":
        from teams.s1_specialist import run_s1_specialist
        result = run_s1_specialist(customer_dir, output_dir)
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
        result = run_s2_specialist(customer_dir, output_dir)
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
        result = run_s3_specialist(customer_dir, output_dir)
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
            st.success("Watching for new files...")
        else:
            st.info("Manual processing mode")

        st.markdown("---")

        # Quick stats
        st.subheader("📊 Quick Stats")
        for team_id in TEAMS:
            files = get_customer_files(team_id)
            reports = get_recent_reports(team_id)
            st.metric(f"{team_id} Files", len(files), f"{len(reports)} reports")


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
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Capabilities")
        for cap in team["capabilities"]:
            st.markdown(f"- {cap}")

    with col2:
        st.subheader("📚 Knowledge Base")
        knowledge_dir = KNOWLEDGE_DIR / team_id
        if knowledge_dir.exists():
            for f in knowledge_dir.iterdir():
                if not f.name.startswith("."):
                    icon = "📄" if f.suffix in [".docx", ".doc"] else "📊"
                    st.markdown(f"{icon} {f.name}")
        else:
            st.info("No knowledge files found")


def render_data_upload(team_id: str):
    """Render the data upload section."""
    st.subheader("📤 Upload Customer Data")

    upload_dir = CUSTOMER_DATA_DIR / team_id
    st.caption(f"Upload to: {upload_dir}")

    uploaded_files = st.file_uploader(
        f"Upload files for {team_id}",
        type=["xlsx", "xlsm", "xls", "csv"],
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
            run_team_processing(team_id)


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
                cols2[2].metric("Allowances", summary.get("allowances", 0))
                cols2[3].metric("Schools", len(summary.get("schools", [])))
            elif team_id == "S1":
                cols = st.columns(4)
                cols[0].metric("Finance Codes", summary.get("finance_codes", 0))
                cols[1].metric("Schools", summary.get("schools", 0))
                cols[2].metric("Departments", summary.get("departments", 0))
                cols[3].metric("Funds", summary.get("funds", 0))
            elif team_id == "S3":
                cols = st.columns(4)
                cols[0].metric("Pupil Records", summary.get("pupils", 0))
                cols[1].metric("Grants", summary.get("grants", 0))
                cols[2].metric("Budget Lines", summary.get("budget_lines", 0))
                cols[3].metric("Scenarios", summary.get("scenarios", 0))

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

        # Issues
        if result.get("issues"):
            with st.expander(f"⚠️ Issues ({len(result['issues'])})", expanded=True):
                for issue in result["issues"]:
                    st.error(issue)

        # Assumptions
        if result.get("assumptions"):
            with st.expander(f"📝 Assumptions ({len(result['assumptions'])})"):
                for assumption in result["assumptions"]:
                    st.info(assumption)

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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload & Files",
        "⚙️ Process",
        "📊 Reports",
        "👁️ Preview"
    ])

    with tab1:
        render_data_upload(team_id)
        st.markdown("---")
        render_customer_files(team_id)

    with tab2:
        render_processing(team_id)

    with tab3:
        render_reports(team_id)

    with tab4:
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
