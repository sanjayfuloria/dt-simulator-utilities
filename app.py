import streamlit as st
import json
from datetime import datetime
import pandas as pd

# ─── Google Sheets Integration ───
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


# ─── Page Config ───
st.set_page_config(
    page_title="Digital Transformation Simulator — Indian Utility Company",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
    .stApp { font-family: 'DM Sans', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #0B1120 0%, #1a2744 50%, #0d2137 100%);
        padding: 28px 32px; border-radius: 12px; margin-bottom: 24px;
        border: 1.5px solid #1e3a5f; position: relative; overflow: hidden;
    }
    .main-header::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.04;
        background-image: repeating-linear-gradient(45deg, transparent, transparent 35px, #fff 35px, #fff 36px);
    }
    .main-header h1 { color: #F1F5F9; font-size: 24px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 4px 0; position: relative; }
    .main-header p { color: #94A3B8; font-size: 13px; letter-spacing: 0.04em; text-transform: uppercase; margin: 0; position: relative; }
    .subprocess-card {
        background: #1E293B; border-radius: 10px; padding: 16px 20px; margin-top: 10px; margin-bottom: 10px;
    }
    .sp-title { font-size: 15px; font-weight: 700; margin: 0 0 10px 0; }
    .sp-label { font-size: 11px; font-weight: 700; color: #94A3B8; letter-spacing: 0.08em; text-transform: uppercase; margin: 0 0 4px 0; }
    .sp-label-pain { font-size: 11px; font-weight: 700; color: #F87171; letter-spacing: 0.08em; text-transform: uppercase; margin: 10px 0 4px 0; }
    .sp-text { font-size: 13px; color: #CBD5E1; line-height: 1.6; margin: 0; }
    .sp-text-pain { font-size: 13px; color: #FCA5A5; line-height: 1.6; margin: 0; }
    .stat-card {
        background: #0F172A; border: 1.5px solid #1E293B; border-radius: 10px; padding: 16px 18px; text-align: center;
    }
    .stat-value { font-size: 28px; font-weight: 800; margin: 0; }
    .stat-label { font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin: 4px 0 0 0; }
    .content-block { background: #1E293B; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; }
    .content-label { font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 6px 0; }
    .content-text { font-size: 13px; line-height: 1.7; margin: 0; white-space: pre-wrap; }
    .tag { display: inline-block; padding: 3px 10px; font-size: 10px; font-weight: 600; border-radius: 20px; margin: 2px 4px 2px 0; }
    .tag-tech { background: rgba(59,130,246,0.1); color: #60A5FA; }
    .tag-challenge { background: rgba(245,158,11,0.1); color: #FCD34D; }
    .impact-badge { padding: 4px 12px; font-size: 10px; font-weight: 700; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.04em; }
    .footer { text-align: center; padding: 20px; font-size: 11px; color: #475569; border-top: 1px solid #1E293B; margin-top: 40px; }
    .info-box { background: #0F172A; border: 1.5px solid #1E293B; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; }
    .info-box h3 { color: #F1F5F9; margin: 0 0 6px; }
    .info-box p { color: #94A3B8; font-size: 14px; line-height: 1.6; margin: 0; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Data Definitions ───

COMPANY_NAME = "PowerGrid Bharat Utilities Ltd."

WORKFLOWS = [
    {
        "id": "generation", "icon": "⚡", "title": "Power Generation", "color": "#E8590C",
        "description": "Thermal, solar, wind, and hydro power generation plants across multiple states",
        "sub_processes": [
            {"id": "gen-planning", "title": "Capacity Planning & Demand Forecasting",
             "current": "Manual demand estimation based on historical consumption data and seasonal patterns. Engineers use spreadsheets and past records to predict load requirements.",
             "pain": "Inaccurate forecasts lead to either over-generation (wasted fuel) or under-generation (load shedding). Planning cycle takes 2-3 weeks."},
            {"id": "gen-ops", "title": "Plant Operations & Monitoring",
             "current": "Control room operators monitor SCADA systems with manual log entries. Shift-based monitoring with physical inspection rounds every 4 hours.",
             "pain": "Delayed detection of equipment anomalies. High dependency on experienced operators. No predictive maintenance — reactive repairs cause unplanned outages."},
            {"id": "gen-fuel", "title": "Fuel Procurement & Inventory",
             "current": "Coal/gas procurement through government e-auctions and long-term contracts. Inventory tracked via manual registers and monthly reconciliation.",
             "pain": "Fuel pilferage (~3-5%), delayed deliveries, quality disputes with suppliers, and poor visibility into real-time stock levels."},
            {"id": "gen-env", "title": "Environmental Compliance & Emissions",
             "current": "Quarterly emission reports filed manually. Pollution control equipment maintained on fixed schedules. Compliance tracked in physical files.",
             "pain": "Risk of CPCB/SPCB penalties due to delayed reporting. No real-time emission monitoring. Difficulty meeting tightening norms under National Clean Air Programme."},
        ],
    },
    {
        "id": "transmission", "icon": "🔌", "title": "Transmission & Grid Management", "color": "#1971C2",
        "description": "High-voltage transmission lines, substations, and grid balancing across the network",
        "sub_processes": [
            {"id": "trans-grid", "title": "Grid Load Balancing & Dispatch",
             "current": "State Load Despatch Centre (SLDC) coordinates with generators via phone and SCADA. Merit order dispatch done semi-manually.",
             "pain": "Frequency deviations and grid instability. Slow response to sudden demand spikes. Interstate power exchange settlement delays."},
            {"id": "trans-maintain", "title": "Transmission Line Maintenance",
             "current": "Periodic patrolling by linesmen on foot/vehicle. Fault detection through consumer complaints or protection relay trips.",
             "pain": "Long fault detection time (hours in rural areas). Safety risks to maintenance crews. Vegetation encroachment causes ~15% of outages."},
            {"id": "trans-loss", "title": "Transmission Loss Monitoring",
             "current": "Aggregate Technical & Commercial (AT&C) losses calculated monthly from meter readings at substations. Typically 20-40% in many state utilities.",
             "pain": "Inability to pinpoint loss locations. Theft detection relies on raids. Huge revenue leakage — ₹1.5+ lakh crore annually across India."},
            {"id": "trans-asset", "title": "Substation & Transformer Management",
             "current": "Asset register maintained in paper/Excel. Transformer oil testing done periodically. Load monitoring via local meters.",
             "pain": "Transformer failures due to overloading (especially in summer). No life-cycle cost tracking. Replacement decisions are reactive."},
        ],
    },
    {
        "id": "distribution", "icon": "🏘️", "title": "Distribution & Last Mile", "color": "#2F9E44",
        "description": "Local distribution network serving residential, commercial, industrial, and agricultural consumers",
        "sub_processes": [
            {"id": "dist-meter", "title": "Metering & Meter Reading",
             "current": "Mix of electromechanical and electronic meters. Monthly manual reading by meter readers visiting each premises. Data entry into billing system.",
             "pain": "Human errors in readings, estimated billing disputes, meter tampering (~8-12% of connections), and inability to detect real-time theft."},
            {"id": "dist-billing", "title": "Billing & Revenue Collection",
             "current": "Billing cycle of 30-60 days. Bills generated centrally and distributed via postal/hand delivery. Payment at collection centers, post offices, and select digital channels.",
             "pain": "High billing errors (~5-7%), delayed collections, long queues at payment centers, and poor penetration of digital payments in rural areas."},
            {"id": "dist-outage", "title": "Outage Management & Restoration",
             "current": "Consumers report outages via phone to local office. Linesman dispatched based on verbal location. Restoration tracked manually.",
             "pain": "Average restoration time 4-8 hours. No automated outage detection. Multiple consumers reporting the same fault flood call centers."},
            {"id": "dist-newconn", "title": "New Connection & Load Enhancement",
             "current": "Paper application at local office. Site survey by Junior Engineer. Approval chain through multiple levels. Physical file movement.",
             "pain": "30-90 day turnaround for new connections. Corruption in queue management. Lack of transparency — applicants can't track status."},
        ],
    },
    {
        "id": "customer", "icon": "👥", "title": "Customer Service & Experience", "color": "#9C36B5",
        "description": "Consumer grievance handling, communication, and service delivery across urban and rural areas",
        "sub_processes": [
            {"id": "cust-grievance", "title": "Grievance Registration & Resolution",
             "current": "Complaints via phone, walk-in, or written application. Registered in complaint register. Resolution tracked manually with periodic reviews.",
             "pain": "Average resolution time 7-15 days. No escalation automation. Consumers lack visibility into complaint status. Repeated follow-ups needed."},
            {"id": "cust-comm", "title": "Consumer Communication & Awareness",
             "current": "Newspaper ads for tariff changes. Pamphlets for safety awareness. Annual consumer meets in district headquarters.",
             "pain": "Low reach in rural areas. No personalized communication. Consumers unaware of subsidy schemes, energy-saving tips, or tariff slabs."},
            {"id": "cust-subsidy", "title": "Subsidy & Tariff Management",
             "current": "State government subsidies for agriculture and BPL consumers. Manual verification of eligibility. Subsidy reconciliation done quarterly.",
             "pain": "Leakage in subsidy delivery. Ghost connections claiming subsidies. Delayed government reimbursement creates cash flow issues."},
        ],
    },
    {
        "id": "finance", "icon": "💰", "title": "Finance & Regulatory", "color": "#E67700",
        "description": "Financial management, regulatory compliance, tariff filings, and government reporting",
        "sub_processes": [
            {"id": "fin-tariff", "title": "Tariff Filing & Regulatory Compliance",
             "current": "Annual Revenue Requirement (ARR) filing with State Electricity Regulatory Commission (SERC). Multi-year tariff petitions prepared manually.",
             "pain": "Complex data compilation from multiple departments. Inconsistent data formats. Tariff orders often delayed, creating revenue uncertainty."},
            {"id": "fin-revenue", "title": "Revenue Assurance & Audit",
             "current": "Internal audit team conducts periodic checks. Revenue reconciliation between billing, collection, and bank statements done monthly.",
             "pain": "Revenue leakage through billing errors, unauthorized connections, and collection shortfalls. Audit coverage limited to ~10% of transactions."},
            {"id": "fin-procurement", "title": "Procurement & Supply Chain",
             "current": "GeM portal for standard items. Tender-based procurement for capital items. Inventory managed at division/circle level warehouses.",
             "pain": "Long procurement cycles (3-6 months for capital items). Inventory mismatch between warehouses. Obsolete stock accumulation."},
        ],
    },
    {
        "id": "hr", "icon": "🏢", "title": "Human Resources & Safety", "color": "#C92A2A",
        "description": "Workforce management, training, safety compliance, and organizational development",
        "sub_processes": [
            {"id": "hr-workforce", "title": "Workforce Planning & Deployment",
             "current": "Staff allocation based on sanctioned posts and seniority. Transfer/posting through annual counseling. Attendance via physical registers.",
             "pain": "Skill mismatch in deployments. Large workforce nearing retirement (~40% in many utilities). Resistance to technology adoption among field staff."},
            {"id": "hr-safety", "title": "Safety Management & Incident Reporting",
             "current": "Safety protocols communicated via circulars. Incident reporting through written reports. Monthly safety meetings at divisional level.",
             "pain": "~500+ fatal electrical accidents annually in India. Under-reporting of near-misses. Outdated safety equipment. No real-time hazard alerts."},
            {"id": "hr-training", "title": "Training & Skill Development",
             "current": "Classroom training at regional training centers. On-the-job training by senior staff. Annual training calendar with fixed programs.",
             "pain": "Training not aligned with technology upgrades. Limited hands-on practice for new systems. No assessment of training effectiveness."},
        ],
    },
    {
        "id": "renewable", "icon": "☀️", "title": "Renewable Energy Integration", "color": "#0CA678",
        "description": "Solar rooftop, net metering, green energy procurement, and RPO compliance",
        "sub_processes": [
            {"id": "ren-solar", "title": "Solar Rooftop & Net Metering",
             "current": "Application-based process for rooftop solar. Bidirectional meter installation by utility. Monthly net metering adjustment in bills.",
             "pain": "Application processing takes 2-6 months. Technical assessment for grid compatibility done manually. Billing system struggles with net metering calculations."},
            {"id": "ren-rpo", "title": "Renewable Purchase Obligation (RPO)",
             "current": "RPO compliance tracked annually. Green certificates purchased from power exchanges. RE procurement through separate PPAs.",
             "pain": "Many state utilities fail to meet RPO targets. RE intermittency creates grid management challenges. Forecasting RE generation is difficult."},
            {"id": "ren-ev", "title": "EV Charging Infrastructure",
             "current": "Pilot EV charging stations in select cities. Separate tariff category for EV charging. Basic load management for charging stations.",
             "pain": "Grid infrastructure not ready for mass EV adoption. No smart charging or V2G capability. Tariff design for EV charging still evolving."},
        ],
    },
]

DT_CATEGORIES = [
    "IoT & Sensors", "AI/ML & Analytics", "Cloud Computing", "Mobile & Apps",
    "Blockchain", "RPA & Automation", "Digital Twin", "Cybersecurity",
    "GIS & Spatial", "AR/VR", "5G & Connectivity", "Other",
]

CHALLENGE_CATEGORIES = [
    "Legacy Systems Integration", "Budget & Funding", "Workforce Resistance",
    "Data Quality & Availability", "Regulatory Barriers", "Cybersecurity Risks",
    "Vendor Lock-in", "Rural Connectivity", "Change Management",
    "Scalability", "Privacy Concerns", "Other",
]

TIMELINE_OPTIONS = ["0-6 months (Quick Win)", "6-12 months (Medium Term)", "1-2 years (Strategic)", "2+ years (Transformational)"]
IMPACT_OPTIONS = ["Low — Incremental improvement", "Medium — Significant efficiency gains", "High — Fundamental process change", "Transformational — New business model"]


# ─── Google Sheets Functions ───

def get_gsheet_connection():
    if not GSPREAD_AVAILABLE:
        return None, "gspread library not installed"
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client, None
    except Exception as e:
        return None, str(e)


def get_or_create_worksheet(client, spreadsheet_url):
    try:
        sh = client.open_by_url(spreadsheet_url)
    except Exception as e:
        return None, f"Could not open spreadsheet: {e}"

    HEADERS = [
        "Timestamp", "Student Name", "Student ID", "Workflow Area",
        "Sub-Process", "DT Solution", "Technology Categories",
        "Challenges", "Challenge Categories", "Implementation Roadmap",
        "Timeline", "Impact Level",
    ]
    try:
        ws = sh.worksheet("Submissions")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="Submissions", rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)
    existing = ws.row_values(1)
    if not existing:
        ws.append_row(HEADERS)
    return ws, None


def save_to_gsheet(ws, entry):
    row = [
        entry["timestamp"], entry["student_name"], entry["student_id"],
        entry["workflow_title"], entry["subprocess_title"], entry["dt_solution"],
        ", ".join(entry["dt_categories"]), entry["challenges"],
        ", ".join(entry["challenge_categories"]), entry["implementation"],
        entry["timeline"], entry["impact"],
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


def load_from_gsheet(ws):
    return ws.get_all_records()


# ─── Google Sheets Auto-Connect ───
# *** INSTRUCTOR: Paste your Google Sheet URL below ***
GOOGLE_SHEET_URL = ""  https://docs.google.com/spreadsheets/d/1Ja1QU7Fhz9vcDiKOe5z8gbmT3accQWy9Yb-npm7VSjQ/edit?gid=0#gid=0"


def auto_connect_gsheet():
    """Silently connect to Google Sheet using secrets + hardcoded URL."""
    if "gsheet_ws" in st.session_state and st.session_state["gsheet_ws"] is not None:
        return  # Already connected

    sheet_url = GOOGLE_SHEET_URL
    if not sheet_url:
        st.session_state["gsheet_ws"] = None
        return

    has_secrets = False
    try:
        _ = st.secrets["gcp_service_account"]
        has_secrets = True
    except (KeyError, FileNotFoundError):
        pass

    if not has_secrets:
        st.session_state["gsheet_ws"] = None
        return

    client, err = get_gsheet_connection()
    if err:
        st.session_state["gsheet_ws"] = None
        return

    ws, err = get_or_create_worksheet(client, sheet_url)
    if err:
        st.session_state["gsheet_ws"] = None
        return

    st.session_state["gsheet_ws"] = ws


# ─── Main App ───

def main():
    st.markdown(f"""
    <div class="main-header">
        <h1>⚡ {COMPANY_NAME}</h1>
        <p>Digital Transformation Simulation — Managing Digital Transformation Course</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-connect Google Sheets in the background
    auto_connect_gsheet()

    if "local_submissions" not in st.session_state:
        st.session_state["local_submissions"] = []

    # ── Top-level Tabs (always visible, no sidebar needed) ──
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏭 Explore Workflows",
        "✍️ Submit Analysis",
        "📊 Submissions Dashboard",
        "⚙️ Settings",
    ])

    with tab1:
        render_explore()

    with tab2:
        render_submit()

    with tab3:
        render_dashboard()

    with tab4:
        render_settings()

    st.markdown("""
    <div class="footer">
        Digital Transformation Simulation · IFHE Center for Distance and Online Education · Managing Digital Transformation Course
    </div>
    """, unsafe_allow_html=True)


# ─── Settings Page (for instructor) ───

def render_settings():
    st.markdown("""
    <div class="info-box">
        <h3>⚙️ Connection Settings</h3>
        <p>This page shows the Google Sheets connection status. Students can ignore this tab — it is for the instructor.</p>
    </div>
    """, unsafe_allow_html=True)

    # Show connection status
    ws = st.session_state.get("gsheet_ws")
    if ws:
        st.success("✅ Connected to Google Sheet successfully!")
        st.caption(f"Sheet URL: {GOOGLE_SHEET_URL}")
    elif GOOGLE_SHEET_URL:
        st.warning("⚠️ Google Sheet URL is set but connection failed. Check secrets and sheet sharing permissions.")

        # Manual retry
        if st.button("🔄 Retry Connection"):
            st.session_state.pop("gsheet_ws", None)
            auto_connect_gsheet()
            st.rerun()
    else:
        st.info("ℹ️ Running in **local mode** — submissions are saved in session memory only.")
        st.markdown("**To connect Google Sheets:**")
        st.markdown("1. Set `GOOGLE_SHEET_URL` at the top of `app.py`")
        st.markdown("2. Add your service account credentials in Streamlit Secrets")
        st.markdown("3. Share the Google Sheet with your service account email as Editor")

    # Manual URL override (for testing)
    with st.expander("Manual Google Sheet URL (override)"):
        manual_url = st.text_input(
            "Google Sheet URL",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Use this to test with a different sheet. The hardcoded URL in app.py takes priority if set.",
        )
        if manual_url and st.button("Connect"):
            has_secrets = False
            try:
                _ = st.secrets["gcp_service_account"]
                has_secrets = True
            except (KeyError, FileNotFoundError):
                pass

            if has_secrets:
                client, err = get_gsheet_connection()
                if err:
                    st.error(f"Connection error: {err}")
                else:
                    ws, err = get_or_create_worksheet(client, manual_url)
                    if err:
                        st.error(err)
                    else:
                        st.session_state["gsheet_ws"] = ws
                        st.success("✅ Connected!")
                        st.rerun()
            else:
                st.error("No Google credentials found in Streamlit Secrets.")


# ─── Explore Page ───

def render_explore():
    st.markdown("""
    <div class="info-box">
        <h3>🏭 Utility Company Workflows</h3>
        <p>Explore the end-to-end operations of <strong style="color: #CBD5E1;">PowerGrid Bharat Utilities Ltd.</strong>
        — a state-owned power utility serving 2.8 crore consumers across urban and rural areas.
        Click each workflow to understand current processes and pain points, then submit your digital transformation analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    for wf in WORKFLOWS:
        with st.expander(f"{wf['icon']}  {wf['title']}  —  {wf['description']}", expanded=False):
            for sp in wf["sub_processes"]:
                st.markdown(f"""
                <div class="subprocess-card" style="border-left: 3px solid {wf['color']};">
                    <p class="sp-title" style="color: {wf['color']};">{sp['title']}</p>
                    <p class="sp-label">CURRENT STATE</p>
                    <p class="sp-text">{sp['current']}</p>
                    <p class="sp-label-pain">PAIN POINTS</p>
                    <p class="sp-text-pain">{sp['pain']}</p>
                </div>
                """, unsafe_allow_html=True)


# ─── Submit Page ───

def render_submit():
    st.markdown("""
    <div class="info-box">
        <h3>✍️ Submit Your Digital Transformation Analysis</h3>
        <p>Select a workflow and sub-process, then describe your proposed digital transformation solution, challenges, and implementation roadmap.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Student Name *", placeholder="Full Name")
    with col2:
        student_id = st.text_input("Student / Roll Number *", placeholder="e.g., MBA2024-042")

    wf_options = {f"{wf['icon']} {wf['title']}": wf["id"] for wf in WORKFLOWS}
    selected_wf_label = st.selectbox("Select Workflow Area *", ["— Select —"] + list(wf_options.keys()))

    selected_wf = None
    selected_sp = None

    if selected_wf_label != "— Select —":
        wf_id = wf_options[selected_wf_label]
        selected_wf = next(wf for wf in WORKFLOWS if wf["id"] == wf_id)
        sp_options = {sp["title"]: sp["id"] for sp in selected_wf["sub_processes"]}
        selected_sp_label = st.selectbox("Select Sub-Process *", ["— Select —"] + list(sp_options.keys()))

        if selected_sp_label != "— Select —":
            sp_id = sp_options[selected_sp_label]
            selected_sp = next(sp for sp in selected_wf["sub_processes"] if sp["id"] == sp_id)
            st.markdown(f"""
            <div class="subprocess-card" style="border-left: 3px solid {selected_wf['color']};">
                <p class="sp-title" style="color: {selected_wf['color']};">📋 Context: {selected_sp['title']}</p>
                <p class="sp-label">CURRENT STATE</p>
                <p class="sp-text">{selected_sp['current']}</p>
                <p class="sp-label-pain">PAIN POINTS</p>
                <p class="sp-text-pain">{selected_sp['pain']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    dt_solution = st.text_area(
        "Your Digital Transformation Solution *",
        placeholder="Describe the digital technologies and approach you would deploy to transform this process. Be specific about tools, platforms, architecture, and expected outcomes.",
        height=150,
    )

    st.markdown("**Technology Categories Used:**")
    dt_cat_cols = st.columns(4)
    dt_categories = []
    for i, cat in enumerate(DT_CATEGORIES):
        with dt_cat_cols[i % 4]:
            if st.checkbox(cat, key=f"dt_{cat}"):
                dt_categories.append(cat)

    st.markdown("---")

    challenges = st.text_area(
        "Key Challenges & Barriers *",
        placeholder="What are the major challenges in implementing this digital transformation? Consider technology, people, process, regulatory, and financial barriers specific to Indian utility context.",
        height=120,
    )

    st.markdown("**Challenge Categories:**")
    ch_cat_cols = st.columns(4)
    challenge_categories = []
    for i, cat in enumerate(CHALLENGE_CATEGORIES):
        with ch_cat_cols[i % 4]:
            if st.checkbox(cat, key=f"ch_{cat}"):
                challenge_categories.append(cat)

    st.markdown("---")

    implementation = st.text_area(
        "Implementation Roadmap (Optional)",
        placeholder="Outline the phased implementation steps — pilot, scale, and full rollout. Include stakeholder engagement plan.",
        height=100,
    )

    col1, col2 = st.columns(2)
    with col1:
        timeline = st.selectbox("Estimated Timeline", TIMELINE_OPTIONS, index=1)
    with col2:
        impact = st.selectbox("Expected Impact Level", IMPACT_OPTIONS, index=1)

    st.markdown("")
    can_submit = all([student_name, student_id, selected_wf, selected_sp, dt_solution, challenges])

    if st.button("📤 Submit Analysis", type="primary", disabled=not can_submit, use_container_width=True):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "student_name": student_name,
            "student_id": student_id,
            "workflow_id": selected_wf["id"],
            "workflow_title": selected_wf["title"],
            "subprocess_id": selected_sp["id"],
            "subprocess_title": selected_sp["title"],
            "dt_solution": dt_solution,
            "dt_categories": dt_categories,
            "challenges": challenges,
            "challenge_categories": challenge_categories,
            "implementation": implementation,
            "timeline": timeline,
            "impact": impact.split(" — ")[0],
        }
        ws = st.session_state.get("gsheet_ws")
        if ws:
            try:
                save_to_gsheet(ws, entry)
                st.success("✅ Submission saved to Google Sheet!")
                st.balloons()
            except Exception as e:
                st.error(f"Error saving to Google Sheet: {e}")
                st.session_state["local_submissions"].append(entry)
                st.info("Saved locally as fallback.")
        else:
            st.session_state["local_submissions"].append(entry)
            st.success("✅ Submission saved locally! (Connect Google Sheet for persistent shared storage)")
            st.balloons()

    if not can_submit:
        st.caption("Please fill in all required fields (*) to submit.")


# ─── Dashboard Page ───

def render_dashboard():
    st.markdown("""
    <div class="info-box">
        <h3>📊 Submissions Dashboard</h3>
        <p>View and analyze all student submissions. Filter by workflow area, search by student, and explore patterns across the class.</p>
    </div>
    """, unsafe_allow_html=True)

    ws = st.session_state.get("gsheet_ws")
    entries = []

    if ws:
        try:
            with st.spinner("Loading from Google Sheet..."):
                records = load_from_gsheet(ws)
            for r in records:
                entries.append({
                    "timestamp": r.get("Timestamp", ""),
                    "student_name": r.get("Student Name", ""),
                    "student_id": str(r.get("Student ID", "")),
                    "workflow_title": r.get("Workflow Area", ""),
                    "subprocess_title": r.get("Sub-Process", ""),
                    "dt_solution": r.get("DT Solution", ""),
                    "dt_categories": [c.strip() for c in str(r.get("Technology Categories", "")).split(",") if c.strip()],
                    "challenges": r.get("Challenges", ""),
                    "challenge_categories": [c.strip() for c in str(r.get("Challenge Categories", "")).split(",") if c.strip()],
                    "implementation": r.get("Implementation Roadmap", ""),
                    "timeline": r.get("Timeline", ""),
                    "impact": r.get("Impact Level", ""),
                })
            st.caption(f"📡 Loaded {len(entries)} submissions from Google Sheet")
        except Exception as e:
            st.error(f"Error loading from Google Sheet: {e}")
            entries = st.session_state.get("local_submissions", [])
    else:
        entries = st.session_state.get("local_submissions", [])
        if entries:
            st.caption(f"💾 Showing {len(entries)} local submissions (connect Google Sheet for shared data)")

    if not entries:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #0F172A; border-radius: 12px; border: 1.5px solid #1E293B;">
            <div style="font-size: 48px; margin-bottom: 12px;">📭</div>
            <p style="color: #64748B; font-size: 14px;">No submissions yet. Switch to "Submit Analysis" to add the first entry.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Stats
    unique_students = len(set(e.get("student_id", "") for e in entries))
    wf_covered = len(set(e.get("workflow_title", "") for e in entries))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><p class="stat-value" style="color: #3B82F6;">{len(entries)}</p><p class="stat-label">Total Submissions</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><p class="stat-value" style="color: #10B981;">{wf_covered} / {len(WORKFLOWS)}</p><p class="stat-label">Workflows Covered</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><p class="stat-value" style="color: #F59E0B;">{unique_students}</p><p class="stat-label">Unique Students</p></div>', unsafe_allow_html=True)
    with col4:
        impacts = [e.get("impact", "") for e in entries]
        impact_counts = {k: impacts.count(k) for k in ["Low", "Medium", "High", "Transformational"]}
        top_impact = max(impact_counts, key=impact_counts.get) if impacts else "—"
        st.markdown(f'<div class="stat-card"><p class="stat-value" style="color: #8B5CF6;">{top_impact}</p><p class="stat-label">Most Common Impact</p></div>', unsafe_allow_html=True)

    st.markdown("")

    # Charts
    col_left, col_right = st.columns(2)
    tech_counts = {}
    for e in entries:
        for c in e.get("dt_categories", []):
            tech_counts[c] = tech_counts.get(c, 0) + 1
    if tech_counts:
        with col_left:
            st.markdown("##### 🔧 Most Proposed Technologies")
            tech_df = pd.DataFrame(sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:8], columns=["Technology", "Count"])
            st.bar_chart(tech_df.set_index("Technology"), color="#3B82F6")

    ch_counts = {}
    for e in entries:
        for c in e.get("challenge_categories", []):
            ch_counts[c] = ch_counts.get(c, 0) + 1
    if ch_counts:
        with col_right:
            st.markdown("##### ⚠️ Most Cited Challenges")
            ch_df = pd.DataFrame(sorted(ch_counts.items(), key=lambda x: x[1], reverse=True)[:8], columns=["Challenge", "Count"])
            st.bar_chart(ch_df.set_index("Challenge"), color="#F59E0B")

    wf_counts = {}
    for e in entries:
        wt = e.get("workflow_title", "Unknown")
        wf_counts[wt] = wf_counts.get(wt, 0) + 1
    if wf_counts:
        st.markdown("##### 📊 Submissions by Workflow Area")
        wf_df = pd.DataFrame(sorted(wf_counts.items(), key=lambda x: x[1], reverse=True), columns=["Workflow", "Submissions"])
        st.bar_chart(wf_df.set_index("Workflow"), color="#10B981")

    st.markdown("---")

    # Filter
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        wf_filter = st.selectbox("Filter by Workflow", ["All"] + [wf["title"] for wf in WORKFLOWS])
    with col_f2:
        search = st.text_input("Search by Student Name or ID", placeholder="Type to search...")

    filtered = entries
    if wf_filter != "All":
        filtered = [e for e in filtered if e.get("workflow_title") == wf_filter]
    if search:
        sl = search.lower()
        filtered = [e for e in filtered if sl in e.get("student_name", "").lower() or sl in e.get("student_id", "").lower()]

    st.markdown(f"**Showing {len(filtered)} of {len(entries)} submissions**")

    # Submission cards
    for entry in reversed(filtered):
        impact = entry.get("impact", "Medium")
        ic_map = {"Low": ("#6B7280", "rgba(107,114,128,0.1)"), "Medium": ("#FCD34D", "rgba(245,158,11,0.1)"), "High": ("#F87171", "rgba(220,38,38,0.1)"), "Transformational": ("#A78BFA", "rgba(124,58,237,0.1)")}
        ic, ibg = ic_map.get(impact, ("#94A3B8", "rgba(148,163,184,0.1)"))
        tech_tags = "".join(f'<span class="tag tag-tech">{c}</span>' for c in entry.get("dt_categories", []))
        ch_tags = "".join(f'<span class="tag tag-challenge">{c}</span>' for c in entry.get("challenge_categories", []))
        impl_block = ""
        if entry.get("implementation"):
            impl_block = f'<div class="content-block"><p class="content-label" style="color: #8B5CF6;">IMPLEMENTATION ROADMAP</p><p class="content-text" style="color: #C4B5FD;">{entry["implementation"]}</p></div>'

        with st.expander(f"📄  {entry.get('subprocess_title', 'N/A')}  —  {entry.get('student_name', 'N/A')} ({entry.get('student_id', '')})  |  {entry.get('timestamp', '')}"):
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <span style="font-size: 12px; color: #94A3B8;"><strong>Workflow:</strong> {entry.get('workflow_title', '')}</span>
                &nbsp;|&nbsp;
                <span style="font-size: 12px; color: #94A3B8;"><strong>Timeline:</strong> {entry.get('timeline', '')}</span>
                &nbsp;|&nbsp;
                <span class="impact-badge" style="color: {ic}; background: {ibg};">{impact}</span>
            </div>
            <div style="margin-bottom: 12px;">{tech_tags} {ch_tags}</div>
            <div class="content-block"><p class="content-label" style="color: #10B981;">PROPOSED DT SOLUTION</p><p class="content-text" style="color: #CBD5E1;">{entry.get('dt_solution', '')}</p></div>
            <div class="content-block"><p class="content-label" style="color: #F59E0B;">CHALLENGES & BARRIERS</p><p class="content-text" style="color: #FDE68A;">{entry.get('challenges', '')}</p></div>
            {impl_block}
            """, unsafe_allow_html=True)

    # Export
    if entries:
        st.markdown("---")
        st.markdown("##### 📥 Export All Submissions")
        df_export = pd.DataFrame([{
            "Timestamp": e.get("timestamp", ""), "Student Name": e.get("student_name", ""),
            "Student ID": e.get("student_id", ""), "Workflow Area": e.get("workflow_title", ""),
            "Sub-Process": e.get("subprocess_title", ""), "DT Solution": e.get("dt_solution", ""),
            "Technology Categories": ", ".join(e.get("dt_categories", [])),
            "Challenges": e.get("challenges", ""),
            "Challenge Categories": ", ".join(e.get("challenge_categories", [])),
            "Implementation Roadmap": e.get("implementation", ""),
            "Timeline": e.get("timeline", ""), "Impact Level": e.get("impact", ""),
        } for e in entries])
        st.download_button("⬇️ Download as CSV", df_export.to_csv(index=False).encode("utf-8"),
                          "dt_simulation_submissions.csv", "text/csv", use_container_width=True)


if __name__ == "__main__":
    main()
