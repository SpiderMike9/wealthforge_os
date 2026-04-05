"""
WealthForge OS v3.0
Elite Multi-Page Financial Dashboard & Agency Life Operating System
Built with Streamlit + Google Sheets + Groq Llama-3 + Make.com Webhooks
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
import requests
from datetime import datetime, date
from typing import Dict
from google.oauth2.service_account import Credentials
from groq import Groq

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WealthForge OS v3.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# SCHWAB CSS  (core untouched + mobile-responsive media queries added)
# ─────────────────────────────────────────────────────────────────
SCHWAB_CSS = """
<style>
/* ── GLOBAL ────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

/* ── SIDEBAR ────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #111128 100%);
    border-right: 1px solid #1e1e3a;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #c8c8e0 !important;
    font-size: 0.95rem;
    padding: 6px 0;
    cursor: pointer;
    transition: color 0.2s;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    color: #7c6af7 !important;
}

/* ── METRIC CARDS ────────────────────────────────── */
.metric-card {
    background: linear-gradient(135deg, #12122a 0%, #1a1a3a 100%);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
    margin-bottom: 16px;
}
.metric-card:hover {
    transform: translateY(-3px);
    border-color: #7c6af7;
}
.metric-card .label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #7878a0;
    margin-bottom: 8px;
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.1;
}
.metric-card .value.positive { color: #4ade80; }
.metric-card .value.negative { color: #f87171; }
.metric-card .value.accent   { color: #7c6af7; }

/* ── MENTOR CHAT ─────────────────────────────────── */
.chat-container {
    background: #12122a;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 12px;
}
.chat-bubble-user {
    background: #1e1e4a;
    border-radius: 12px 12px 2px 12px;
    padding: 10px 15px;
    margin: 8px 0 8px 40px;
    font-size: 0.9rem;
    color: #d0d0f0;
    text-align: right;
}
.chat-bubble-mentor {
    background: linear-gradient(135deg, #1a1a35 0%, #25254a 100%);
    border-left: 3px solid #7c6af7;
    border-radius: 2px 12px 12px 12px;
    padding: 10px 15px;
    margin: 8px 40px 8px 0;
    font-size: 0.9rem;
    color: #e0e0ff;
    line-height: 1.6;
}
.mentor-avatar {
    font-size: 1.6rem;
    margin-right: 8px;
}

/* ── SECTION HEADERS ─────────────────────────────── */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #ffffff;
    border-bottom: 2px solid #7c6af7;
    padding-bottom: 8px;
    margin-bottom: 20px;
}

/* ── BUTTONS ─────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #5b4de0 0%, #7c6af7 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: opacity 0.2s, transform 0.15s;
    cursor: pointer;
}
.stButton > button:hover {
    opacity: 0.85;
    transform: translateY(-1px);
}
.stButton > button.secondary {
    background: #1e1e3a;
    border: 1px solid #3a3a6a;
}

/* ── DATAFRAME ───────────────────────────────────── */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* ── LOGIN CARD ──────────────────────────────────── */
.login-card {
    background: linear-gradient(135deg, #12122a 0%, #1e1e3a 100%);
    border: 1px solid #2a2a5a;
    border-radius: 16px;
    padding: 40px 48px;
    max-width: 440px;
    margin: 80px auto;
    text-align: center;
    box-shadow: 0 20px 60px rgba(124, 106, 247, 0.15);
}
.login-title {
    font-size: 2rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.5px;
}
.login-subtitle {
    color: #7878a0;
    font-size: 0.9rem;
    margin-top: 6px;
    margin-bottom: 28px;
}

/* ── PROGRESS / XP BAR ───────────────────────────── */
.xp-bar-wrap {
    background: #1a1a35;
    border-radius: 999px;
    height: 12px;
    overflow: hidden;
    margin: 6px 0 12px;
}
.xp-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #7c6af7, #a78bfa);
    border-radius: 999px;
    transition: width 0.6s ease;
}

/* ── WEBHOOK STATUS BADGE ────────────────────────── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 8px;
}
.badge-success { background: #14532d; color: #4ade80; }
.badge-error   { background: #7f1d1d; color: #f87171; }
.badge-pending { background: #1e3a5f; color: #60a5fa; }

/* ── MOBILE RESPONSIVE MEDIA QUERIES ─────────────── */
@media (max-width: 768px) {
    .metric-card {
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .metric-card .value {
        font-size: 1.5rem;
    }
    .chat-bubble-user  { margin-left: 10px;  }
    .chat-bubble-mentor { margin-right: 10px; }
    .chat-container { max-height: 300px; padding: 14px; }
    .login-card { padding: 28px 20px; margin: 30px auto; }
    .login-title { font-size: 1.5rem; }
    section[data-testid="stSidebar"] { min-width: 220px !important; }
    .section-header { font-size: 1.1rem; }
    /* Stack columns on mobile */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .stPlotlyChart { width: 100% !important; }
}

@media (max-width: 480px) {
    .metric-card .value { font-size: 1.2rem; }
    .stButton > button  { width: 100%; font-size: 0.85rem; }
    .chat-bubble-user, .chat-bubble-mentor { font-size: 0.82rem; }
}
</style>
"""

st.markdown(SCHWAB_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
SPREADSHEET_NAME = "WealthForge OS 7-Tab Master Database"

SHEET_TABS = {
    "Ledger":              ["Date", "Description", "Category", "Type", "Quadrant", "Amount", "Tags", "Notes"],
    "CRM_Leads":           ["Date_Added", "Business_Name", "Niche", "Pipeline_Stage", "Deal_Value", "Probability_Pct", "Next_Action_Date"],
    "Outreach_Tracker":    ["Date", "Prospect_Name", "Platform", "Loom_Video_Link", "Response_Received", "Follow_Up_Date"],
    "Active_Clients":      ["Client_Name", "Service_Tier", "Make_Zap_Status", "Monthly_Revenue", "Onboarding_Date"],
    "Daily4F":             ["Date", "Faith_Score", "Fitness_Score", "Finances_Score", "Family_Score", "Schedule_Adherence", "Coach_Status"],
    "Gamification_Tiers":  ["User_ID", "Literacy_Test_Score", "Wealth_Tier", "Total_XP", "Unlocked_Advisors"],
    "System_Logs":         ["Timestamp", "Webhook_Event", "Source", "SMS_Sent_Status", "Calendar_Updated", "Error_Logs"],
}

NAV_PAGES = [
    "📊 Wealth Ledger",
    "🤝 Agency DealFlow & Clients",
    "💪 4F Daily Matrix",
    "🎮 Wealth Profile",
    "⚙️ System Logs",
]

# Webhook URLs – resolved lazily at call-time so no secrets file is required at startup
def _get_secret(key: str, default: str = "") -> str:
    """Safely read a Streamlit secret, returning default if secrets are unavailable."""
    try:
        return st.secrets[key]
    except Exception:
        return default

def _get_webhook_url(key: str, placeholder: str) -> str:
    return _get_secret(key, placeholder)

# ─────────────────────────────────────────────────────────────────
# AI MENTOR BOARD – 6 PERSONAS
# ─────────────────────────────────────────────────────────────────
ADVISORS = {
    "Ryan Stewman – Apex Coach": {
        "emoji": "🦁",
        "tagline": "4Fs. Law of Averages. No Excuses.",
        "system": (
            "You are Ryan Stewman, the Apex Predator Coach. You speak in direct, aggressive, "
            "high-energy language. You hold people ruthlessly accountable using the 4Fs framework: "
            "Faith, Fitness, Finances, and Family. You cite the Law of Averages constantly. "
            "You despise excuses. Every answer ends with a sharp challenge to take immediate action. "
            "When given financial or daily-metric data, you find the weak point and call it out."
        ),
    },
    "Robert Kiyosaki – Cashflow Architect": {
        "emoji": "🏦",
        "tagline": "Assets. Quadrants. Financial IQ.",
        "system": (
            "You are Robert Kiyosaki, author of Rich Dad Poor Dad. You bluntly distinguish between "
            "assets and liabilities, the CASHFLOW Quadrant (E, S, B, I), and passive income. "
            "You challenge conventional school-job-retire thinking. You use simple metaphors and "
            "bold statements. When given ledger or financial data, you identify where the person is "
            "trapped in the wrong quadrant and prescribe asset acquisition."
        ),
    },
    "Donald Trump – Empire Builder": {
        "emoji": "🏗️",
        "tagline": "Real Estate. Leverage. Think BIG.",
        "system": (
            "You are Donald Trump, real estate mogul and empire builder. You speak superlatively — "
            "things are always the best, the biggest, the most tremendous. You focus on leverage, "
            "negotiation, branding, and scale. You believe in going after massive deals and never "
            "settling for small. When given data, you look for the biggest opportunity and advise "
            "how to go 10x larger through deal-making and bold branding."
        ),
    },
    "Jordan Belfort – The Closer": {
        "emoji": "🎯",
        "tagline": "Straight Line. High-Ticket. Close Everything.",
        "system": (
            "You are Jordan Belfort, creator of the Straight Line Persuasion System. You are a "
            "relentless sales machine focused on closing high-ticket deals. You speak about tonality, "
            "certainty, and the three tens (certain about product, company, and you). You push "
            "relentless prospecting and follow-up. When given CRM or outreach data, you identify "
            "stalled deals and give a precise script or strategy to close them immediately."
        ),
    },
    "Sean Carter – The Mogul": {
        "emoji": "👑",
        "tagline": "Equity. Ownership. Streets to Boardroom.",
        "system": (
            "You are Sean Carter (Jay-Z), cultural mogul and business architect. You speak with "
            "calm authority about equity over income, ownership, cultural branding, and building "
            "generational wealth. You reference your journey from street hustler to billionaire "
            "business owner. You advise on brand partnerships, licensing, and never selling "
            "yourself short. When given data, you identify where ownership and equity can replace "
            "service-based income."
        ),
    },
    "Warren Buffett – Value Compounder": {
        "emoji": "📈",
        "tagline": "Circle of Competence. Patience. Compound.",
        "system": (
            "You are Warren Buffett, the Oracle of Omaha. You speak in calm, folksy wisdom about "
            "staying within your circle of competence, buying quality assets at fair prices, and "
            "the miraculous power of compounding. You are skeptical of speculation and love "
            "long-term thinking. You quote Benjamin Graham and Charlie Munger. When given financial "
            "data, you assess the quality of cash flows and advise on patience and discipline."
        ),
    },
}

# Default mentor per page
PAGE_DEFAULT_MENTOR = {
    "📊 Wealth Ledger":              "Robert Kiyosaki – Cashflow Architect",
    "🤝 Agency DealFlow & Clients":  "Jordan Belfort – The Closer",
    "💪 4F Daily Matrix":            "Ryan Stewman – Apex Coach",
    "🎮 Wealth Profile":             "Sean Carter – The Mogul",
    "⚙️ System Logs":               "Warren Buffett – Value Compounder",
}

# ─────────────────────────────────────────────────────────────────
# GOOGLE SHEETS  –  DATA LAYER
# ─────────────────────────────────────────────────────────────────
def _sheets_configured() -> bool:
    """Return True if GCP service account credentials are present in secrets."""
    try:
        _ = st.secrets["gcp_service_account"]
        return True
    except Exception:
        return False


def _get_gspread_client() -> gspread.Client:
    """Authenticate with Google Sheets via service-account credentials stored in Streamlit secrets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def _clean_df(df: pd.DataFrame, tab_name: str) -> pd.DataFrame:
    """Normalise column types, handle nulls, and coerce known numeric/date columns."""
    df.columns = [c.strip() for c in df.columns]
    df = df.replace({"": None, "N/A": None, "n/a": None, "-": None})

    DATE_COLS = {
        "Ledger":           ["Date"],
        "CRM_Leads":        ["Date_Added", "Next_Action_Date"],
        "Outreach_Tracker": ["Date", "Follow_Up_Date"],
        "Active_Clients":   ["Onboarding_Date"],
        "Daily4F":          ["Date"],
        "Gamification_Tiers": [],
        "System_Logs":      ["Timestamp"],
    }
    NUMERIC_COLS = {
        "Ledger":           ["Amount"],
        "CRM_Leads":        ["Deal_Value", "Probability_Pct"],
        "Active_Clients":   ["Monthly_Revenue"],
        "Daily4F":          ["Faith_Score", "Fitness_Score", "Finances_Score", "Family_Score", "Schedule_Adherence"],
        "Gamification_Tiers": ["Literacy_Test_Score", "Total_XP"],
        "Outreach_Tracker": [],
        "System_Logs":      [],
    }

    for col in DATE_COLS.get(tab_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in NUMERIC_COLS.get(tab_name, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[$,%]", "", regex=True), errors="coerce")

    return df.dropna(how="all")


def _render_sheets_setup_guide() -> None:
    """Render a step-by-step setup guide when Google Sheets is not yet configured."""
    st.markdown("""
<div style="background:#1a1a2e;border:1px solid #7c6af7;border-radius:12px;padding:28px 32px;max-width:780px;margin:0 auto;">
<div style="font-size:1.4rem;font-weight:700;color:#ffffff;margin-bottom:6px;">🔌 Google Sheets Not Connected</div>
<div style="color:#9090b0;font-size:0.9rem;margin-bottom:24px;">Follow these 4 steps to wire your WealthForge OS database.</div>

<div style="color:#ffffff;font-weight:600;margin-bottom:6px;">Step 1 — Create a Google Cloud Service Account</div>
<div style="color:#b0b0cc;font-size:0.88rem;margin-bottom:16px;">
1. Go to <a href="https://console.cloud.google.com/" target="_blank" style="color:#7c6af7;">console.cloud.google.com</a><br>
2. Create a new project (or select an existing one)<br>
3. Navigate to <b>APIs & Services → Credentials</b><br>
4. Click <b>Create Credentials → Service Account</b><br>
5. Give it any name, click <b>Done</b><br>
6. Click the service account → <b>Keys</b> tab → <b>Add Key → JSON</b><br>
7. A <code>.json</code> file will download — keep it safe
</div>

<div style="color:#ffffff;font-weight:600;margin-bottom:6px;">Step 2 — Enable the Google Sheets & Drive APIs</div>
<div style="color:#b0b0cc;font-size:0.88rem;margin-bottom:16px;">
In your GCP project go to <b>APIs & Services → Library</b> and enable:<br>
• <b>Google Sheets API</b><br>
• <b>Google Drive API</b>
</div>

<div style="color:#ffffff;font-weight:600;margin-bottom:6px;">Step 3 — Share your Sheet with the service account</div>
<div style="color:#b0b0cc;font-size:0.88rem;margin-bottom:16px;">
Open your Google Sheet named <code>WealthForge OS 7-Tab Master Database</code><br>
Click <b>Share</b> and add the service account email (looks like <code>name@project.iam.gserviceaccount.com</code>)<br>
Give it <b>Viewer</b> (or Editor) access.
</div>

<div style="color:#ffffff;font-weight:600;margin-bottom:6px;">Step 4 — Add credentials to Streamlit secrets</div>
<div style="color:#b0b0cc;font-size:0.88rem;margin-bottom:8px;">
Create the file <code>.streamlit/secrets.toml</code> in your project root (or paste into the Streamlit Cloud secrets UI) with this structure:
</div>
<pre style="background:#0d0d1a;border:1px solid #2a2a4a;border-radius:8px;padding:16px;font-size:0.78rem;color:#a0f0c0;overflow-x:auto;">[gcp_service_account]
type                        = "service_account"
project_id                  = "your-project-id"
private_key_id              = "abc123..."
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n"
client_email                = "your-sa@your-project.iam.gserviceaccount.com"
client_id                   = "123456789"
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"

GROQ_API_KEY               = "gsk_..."
MAKE_SMS_WEBHOOK_URL       = "https://hook.make.com/YOUR_SMS_HOOK"
MAKE_CALENDAR_WEBHOOK_URL  = "https://hook.make.com/YOUR_CAL_HOOK"

[app_users]
LeadForge1 = "MikeJones1"
admin      = "wealthforge2025"</pre>
<div style="color:#7878a0;font-size:0.78rem;margin-top:12px;">
💡 Copy every value directly from the downloaded JSON file. For <code>private_key</code>, keep the <code>\n</code> escape sequences exactly as they appear in the JSON.
</div>
</div>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet_tab(tab_name: str) -> pd.DataFrame:
    """Fetch a single tab from the master Google Sheet, clean it, and cache for 5 minutes."""
    if not _sheets_configured():
        return pd.DataFrame(columns=SHEET_TABS[tab_name])
    try:
        client = _get_gspread_client()
        sheet  = client.open(SPREADSHEET_NAME)
        ws     = sheet.worksheet(tab_name)
        records = ws.get_all_records(expected_headers=SHEET_TABS[tab_name])
        df = pd.DataFrame(records)
        return _clean_df(df, tab_name)
    except Exception as exc:
        st.warning(f"⚠️ Could not load **{tab_name}**: {exc}")
        return pd.DataFrame(columns=SHEET_TABS[tab_name])


# Convenience: load multiple tabs
def load_multi(*tabs) -> Dict[str, pd.DataFrame]:
    return {t: load_sheet_tab(t) for t in tabs}


# ─────────────────────────────────────────────────────────────────
# MAKE.COM WEBHOOK FUNCTIONS
# ─────────────────────────────────────────────────────────────────
def trigger_make_sms_webhook(payload: dict) -> dict:
    """
    Fire the Make.com SMS automation webhook.
    Returns a result dict with keys: success (bool), message (str).
    """
    try:
        resp = requests.post(
            _get_webhook_url("MAKE_SMS_WEBHOOK_URL", "https://hook.make.com/PLACEHOLDER_SMS"),
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return {"success": True, "message": f"SMS webhook fired ✅  (HTTP {resp.status_code})"}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "SMS webhook timed out ⏱️"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "SMS webhook – connection error 🔌"}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "message": f"SMS webhook HTTP error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"SMS webhook unexpected error: {e}"}


def trigger_make_calendar_webhook(payload: dict) -> dict:
    """
    Fire the Make.com Calendar automation webhook.
    Returns a result dict with keys: success (bool), message (str).
    """
    try:
        resp = requests.post(
            _get_webhook_url("MAKE_CALENDAR_WEBHOOK_URL", "https://hook.make.com/PLACEHOLDER_CALENDAR"),
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return {"success": True, "message": f"Calendar webhook fired ✅  (HTTP {resp.status_code})"}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Calendar webhook timed out ⏱️"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Calendar webhook – connection error 🔌"}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "message": f"Calendar webhook HTTP error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Calendar webhook unexpected error: {e}"}


# ─────────────────────────────────────────────────────────────────
# LOGIN  (core logic untouched)
# ─────────────────────────────────────────────────────────────────
def render_login_screen() -> bool:
    """Render the login card. Returns True if authenticated, False otherwise."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        """
        <div class="login-card">
            <div class="login-title">⚡ WealthForge OS</div>
            <div class="login-subtitle">v3.0 · Elite Operator Access</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        username = st.text_input("Username", placeholder="Enter username", key="login_user")
        password = st.text_input("Password", placeholder="Enter password", type="password", key="login_pass")

        if st.button("🔐 Access the OS", use_container_width=True):
            try:
                valid_users: dict = dict(st.secrets["app_users"])
            except Exception:
                valid_users = {
                    "admin":      "wealthforge2025",
                    "LeadForge1": "MikeJones1",
                }
            if username in valid_users and valid_users[username] == password:
                st.session_state.authenticated = True
                st.session_state.username      = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Speak the password, operator.")

    return st.session_state.get("authenticated", False)


# ─────────────────────────────────────────────────────────────────
# GROQ LLAMA-3 CHAT ENGINE
# ─────────────────────────────────────────────────────────────────
def get_groq_client() -> Groq:
    api_key = _get_secret("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not found in secrets.toml.")
    return Groq(api_key=api_key)


def build_context_summary(page: str) -> str:
    """Build a compact data summary string to inject into the AI's system prompt."""
    try:
        if page == "📊 Wealth Ledger":
            df = load_sheet_tab("Ledger")
            income  = df[df["Type"].str.lower() == "income"]["Amount"].sum() if "Type" in df.columns else 0
            expense = df[df["Type"].str.lower() == "expense"]["Amount"].sum() if "Type" in df.columns else 0
            return (
                f"LEDGER SNAPSHOT | Rows: {len(df)} | "
                f"Total Income: ${income:,.2f} | Total Expenses: ${expense:,.2f} | "
                f"Net: ${income - expense:,.2f}"
            )

        elif page == "🤝 Agency DealFlow & Clients":
            crm    = load_sheet_tab("CRM_Leads")
            clients = load_sheet_tab("Active_Clients")
            pipeline_val = crm["Deal_Value"].sum() if "Deal_Value" in crm.columns else 0
            mrr          = clients["Monthly_Revenue"].sum() if "Monthly_Revenue" in clients.columns else 0
            return (
                f"CRM SNAPSHOT | Leads: {len(crm)} | Pipeline Value: ${pipeline_val:,.2f} | "
                f"Active Clients: {len(clients)} | MRR: ${mrr:,.2f}"
            )

        elif page == "💪 4F Daily Matrix":
            df = load_sheet_tab("Daily4F")
            if df.empty:
                return "4F SNAPSHOT | No entries logged yet."
            last = df.sort_values("Date", ascending=False).iloc[0]
            return (
                f"4F LATEST ENTRY | Date: {last.get('Date', 'N/A')} | "
                f"Faith: {last.get('Faith_Score', '?')}/10 | "
                f"Fitness: {last.get('Fitness_Score', '?')}/10 | "
                f"Finances: {last.get('Finances_Score', '?')}/10 | "
                f"Family: {last.get('Family_Score', '?')}/10 | "
                f"Schedule Adherence: {last.get('Schedule_Adherence', '?')}%"
            )

        elif page == "🎮 Wealth Profile":
            df = load_sheet_tab("Gamification_Tiers")
            if df.empty:
                return "WEALTH PROFILE | No gamification data yet."
            top = df.sort_values("Total_XP", ascending=False).iloc[0]
            return (
                f"TOP PROFILE | Tier: {top.get('Wealth_Tier', '?')} | "
                f"XP: {top.get('Total_XP', 0):,} | "
                f"Test Score: {top.get('Literacy_Test_Score', '?')}"
            )

        elif page == "⚙️ System Logs":
            df = load_sheet_tab("System_Logs")
            errors = df["Error_Logs"].notna().sum() if "Error_Logs" in df.columns else 0
            return (
                f"SYSTEM LOGS | Total Events: {len(df)} | Errors Logged: {errors}"
            )

        return "No specific context available."
    except Exception as e:
        return f"Context load error: {e}"


def render_mentor_chat(page: str) -> None:
    """Render the full AI Mentor Boardroom UI for the given page."""
    st.markdown('<div class="section-header">🧠 AI Mentor Boardroom</div>', unsafe_allow_html=True)

    default_mentor = PAGE_DEFAULT_MENTOR.get(page, list(ADVISORS.keys())[0])
    mentor_keys    = list(ADVISORS.keys())
    default_idx    = mentor_keys.index(default_mentor)

    selected_mentor = st.selectbox(
        "Select Your Mentor",
        options=mentor_keys,
        index=default_idx,
        format_func=lambda k: f"{ADVISORS[k]['emoji']} {k}",
        key=f"mentor_select_{page}",
    )

    advisor = ADVISORS[selected_mentor]
    st.markdown(
        f'<span class="mentor-avatar">{advisor["emoji"]}</span> '
        f'<span style="color:#a0a0c0;font-size:0.85rem;font-style:italic;">{advisor["tagline"]}</span>',
        unsafe_allow_html=True,
    )

    # Initialise per-page chat history
    chat_key = f"chat_history_{page}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Render chat history
    chat_html = '<div class="chat-container">'
    for msg in st.session_state[chat_key]:
        if msg["role"] == "user":
            chat_html += f'<div class="chat-bubble-user">{msg["content"]}</div>'
        else:
            chat_html += f'<div class="chat-bubble-mentor"><b>{advisor["emoji"]} {selected_mentor.split("–")[0].strip()}</b><br>{msg["content"]}</div>'
    if not st.session_state[chat_key]:
        chat_html += '<div style="color:#4a4a6a;font-size:0.85rem;text-align:center;padding:30px 0;">Ask your mentor anything about this page\'s data…</div>'
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_query = st.text_input(
            "Your question",
            placeholder=f"Ask {selected_mentor.split('–')[0].strip()} something…",
            label_visibility="collapsed",
            key=f"chat_input_{page}",
        )
    with col_btn:
        send = st.button("Send ➤", key=f"chat_send_{page}", use_container_width=True)

    if send and user_query.strip():
        context_summary = build_context_summary(page)
        system_prompt = (
            f"{advisor['system']}\n\n"
            f"CURRENT DASHBOARD PAGE: {page}\n"
            f"LIVE DATA CONTEXT: {context_summary}\n\n"
            "Use this data to give hyper-relevant, personalised advice. "
            "Be concise yet impactful — no more than 250 words."
        )

        # Build message list for Groq
        messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state[chat_key][-8:]:   # keep last 8 turns for context
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_query})

        with st.spinner(f"{advisor['emoji']} {selected_mentor.split('–')[0].strip()} is thinking…"):
            try:
                groq_client = get_groq_client()
                response = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=messages,
                    max_tokens=400,
                    temperature=0.82,
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                reply = f"⚠️ Mentor temporarily offline: {e}"

        st.session_state[chat_key].append({"role": "user",      "content": user_query})
        st.session_state[chat_key].append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state[chat_key]:
        if st.button("🗑️ Clear Chat", key=f"clear_chat_{page}"):
            st.session_state[chat_key] = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────
# HELPER: METRIC CARD HTML
# ─────────────────────────────────────────────────────────────────
def metric_card(label: str, value: str, cls: str = "") -> str:
    return (
        f'<div class="metric-card">'
        f'<div class="label">{label}</div>'
        f'<div class="value {cls}">{value}</div>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────
# PAGE RENDERERS
# ─────────────────────────────────────────────────────────────────

# ── 1. WEALTH LEDGER ─────────────────────────────────────────────
def render_wealth_ledger() -> None:
    st.markdown('<div class="section-header">📊 Wealth Ledger</div>', unsafe_allow_html=True)

    with st.spinner("Loading ledger…"):
        df = load_sheet_tab("Ledger")

    if df.empty:
        if not _sheets_configured():
            _render_sheets_setup_guide()
        else:
            st.info("No ledger data found. Ensure your Sheet is shared with the service account and has data.")
        render_mentor_chat("📊 Wealth Ledger")
        return

    # ── KPI Row
    total_income  = df[df["Type"].str.lower() == "income"]["Amount"].sum()  if "Type" in df.columns else 0
    total_expense = df[df["Type"].str.lower() == "expense"]["Amount"].sum() if "Type" in df.columns else 0
    net           = total_income - total_expense
    num_entries   = len(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric_card("Total Income",   f"${total_income:,.0f}",  "positive"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card("Total Expenses", f"${total_expense:,.0f}", "negative"), unsafe_allow_html=True)
    with c3:
        net_cls = "positive" if net >= 0 else "negative"
        st.markdown(metric_card("Net Position", f"${net:,.0f}", net_cls), unsafe_allow_html=True)
    with c4: st.markdown(metric_card("Entries",        str(num_entries),          "accent"),  unsafe_allow_html=True)

    # ── Filters
    sel_cat  = "All"
    sel_type = "All"
    with st.expander("🔎 Filter Ledger", expanded=False):
        fc1, fc2 = st.columns(2)
        categories = ["All"] + sorted(df["Category"].dropna().unique().tolist()) if "Category" in df.columns else ["All"]
        types      = ["All"] + sorted(df["Type"].dropna().unique().tolist())     if "Type"     in df.columns else ["All"]
        sel_cat  = fc1.selectbox("Category", categories)
        sel_type = fc2.selectbox("Type",     types)

    filtered = df.copy()
    if sel_cat  != "All" and "Category" in filtered.columns:
        filtered = filtered[filtered["Category"] == sel_cat]
    if sel_type != "All" and "Type" in filtered.columns:
        filtered = filtered[filtered["Type"] == sel_type]


    # ── Charts
    ch1, ch2 = st.columns(2)
    with ch1:
        if "Category" in filtered.columns and "Amount" in filtered.columns:
            cat_sum = filtered.groupby("Category")["Amount"].sum().reset_index()
            fig = px.bar(cat_sum, x="Category", y="Amount", title="Spend by Category",
                         color="Amount", color_continuous_scale="Purples",
                         template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with ch2:
        if "Quadrant" in filtered.columns and "Amount" in filtered.columns:
            quad_sum = filtered.groupby("Quadrant")["Amount"].sum().reset_index()
            fig2 = px.pie(quad_sum, names="Quadrant", values="Amount",
                          title="Cashflow by Quadrant",
                          color_discrete_sequence=px.colors.sequential.Purples_r,
                          template="plotly_dark")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

    # ── Data table
    st.subheader("📋 Ledger Entries")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.divider()
    render_mentor_chat("📊 Wealth Ledger")


# ── 2. AGENCY DEALFLOW & CLIENTS ─────────────────────────────────
def render_agency_dealflow() -> None:
    st.markdown('<div class="section-header">🤝 Agency DealFlow & Clients</div>', unsafe_allow_html=True)

    if not _sheets_configured():
        _render_sheets_setup_guide()
        st.divider()
        render_mentor_chat("🤝 Agency DealFlow & Clients")
        return

    with st.spinner("Loading CRM data…"):
        data = load_multi("CRM_Leads", "Outreach_Tracker", "Active_Clients")
        crm      = data["CRM_Leads"]
        outreach = data["Outreach_Tracker"]
        clients  = data["Active_Clients"]

    # ── KPI Row
    pipeline_value = crm["Deal_Value"].sum()       if ("Deal_Value"       in crm.columns     and not crm.empty)     else 0
    mrr            = clients["Monthly_Revenue"].sum() if ("Monthly_Revenue" in clients.columns and not clients.empty) else 0
    open_outreach  = len(outreach[outreach["Response_Received"].str.lower().str.strip() == "no"]) \
                     if ("Response_Received" in outreach.columns and not outreach.empty) else len(outreach)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric_card("Pipeline Value",   f"${pipeline_value:,.0f}", "accent"),   unsafe_allow_html=True)
    with c2: st.markdown(metric_card("Monthly Recurring", f"${mrr:,.0f}",           "positive"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card("Active Clients",   str(len(clients)),          "accent"),   unsafe_allow_html=True)
    with c4: st.markdown(metric_card("Awaiting Reply",   str(open_outreach),         "negative"), unsafe_allow_html=True)

    # ── Webhook Button
    st.markdown("#### ⚡ Automation")
    if st.button("📱 Fire Accountability SMS", key="sms_webhook_btn"):
        payload = {
            "event":        "accountability_sms",
            "triggered_by": st.session_state.get("username", "operator"),
            "timestamp":    datetime.utcnow().isoformat(),
            "pipeline_value": pipeline_value,
            "open_outreach":  open_outreach,
        }
        result = trigger_make_sms_webhook(payload)
        badge_cls = "badge-success" if result["success"] else "badge-error"
        st.markdown(
            f'{result["message"]} <span class="badge {badge_cls}">{"OK" if result["success"] else "FAIL"}</span>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Pipeline chart
    if not crm.empty and "Pipeline_Stage" in crm.columns and "Deal_Value" in crm.columns:
        stage_sum = crm.groupby("Pipeline_Stage")["Deal_Value"].sum().reset_index()
        fig = px.funnel(stage_sum, x="Deal_Value", y="Pipeline_Stage",
                        title="Pipeline Funnel by Stage",
                        template="plotly_dark",
                        color_discrete_sequence=["#7c6af7"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # ── Tables
    t1, t2, t3 = st.tabs(["🎯 CRM Leads", "📬 Outreach Tracker", "✅ Active Clients"])
    with t1:
        st.dataframe(crm,      use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(outreach, use_container_width=True, hide_index=True)
    with t3:
        st.dataframe(clients,  use_container_width=True, hide_index=True)

    st.divider()
    render_mentor_chat("🤝 Agency DealFlow & Clients")


# ── 3. 4F DAILY MATRIX ───────────────────────────────────────────
def render_four_f_matrix() -> None:
    st.markdown('<div class="section-header">💪 4F Daily Matrix</div>', unsafe_allow_html=True)

    with st.spinner("Loading 4F data…"):
        df = load_sheet_tab("Daily4F")

    score_cols = ["Faith_Score", "Fitness_Score", "Finances_Score", "Family_Score"]

    if df.empty:
        if not _sheets_configured():
            _render_sheets_setup_guide()
        else:
            st.info("No 4F data found yet. Start logging your daily scores in the Daily4F tab.")
    else:
        df_sorted = df.sort_values("Date", ascending=False)
        latest    = df_sorted.iloc[0]

        # ── KPI Row – latest scores
        cols = st.columns(4)
        labels = ["Faith", "Fitness", "Finances", "Family"]
        for i, (col_name, label) in enumerate(zip(score_cols, labels)):
            val = latest.get(col_name, 0) or 0
            with cols[i]:
                st.markdown(metric_card(f"⚡ {label}", f"{val}/10", "accent"), unsafe_allow_html=True)

        # ── Adherence KPI
        adh = latest.get("Schedule_Adherence", 0) or 0
        st.markdown(metric_card("📅 Schedule Adherence", f"{adh}%", "positive"), unsafe_allow_html=True)

        # ── Radar Chart
        fig = go.Figure(go.Scatterpolar(
            r    = [latest.get(c, 0) or 0 for c in score_cols],
            theta = labels,
            fill  = "toself",
            line  = dict(color="#7c6af7"),
            fillcolor = "rgba(124,106,247,0.15)",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], color="#4a4a6a"),
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            title="Latest 4F Radar",
            title_font_color="#ffffff",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Trend lines
        trend_df = df_sorted[score_cols + ["Date"]].set_index("Date").sort_index()
        fig2 = px.line(trend_df, title="4F Score Trends",
                       template="plotly_dark",
                       color_discrete_sequence=["#7c6af7", "#4ade80", "#f59e0b", "#60a5fa"])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📋 4F Log")
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

    # ── Webhook Button
    st.divider()
    st.markdown("#### ⚡ Automation")
    if st.button("📅 Sync Daily Schedule", key="calendar_webhook_btn"):
        payload = {
            "event":        "sync_daily_schedule",
            "triggered_by": st.session_state.get("username", "operator"),
            "timestamp":    datetime.utcnow().isoformat(),
            "date":         str(date.today()),
        }
        result = trigger_make_calendar_webhook(payload)
        badge_cls = "badge-success" if result["success"] else "badge-error"
        st.markdown(
            f'{result["message"]} <span class="badge {badge_cls}">{"OK" if result["success"] else "FAIL"}</span>',
            unsafe_allow_html=True,
        )

    st.divider()
    render_mentor_chat("💪 4F Daily Matrix")


# ── 4. WEALTH PROFILE (GAMIFICATION) ─────────────────────────────
def render_wealth_profile() -> None:
    st.markdown('<div class="section-header">🎮 Wealth Profile</div>', unsafe_allow_html=True)

    with st.spinner("Loading profile data…"):
        df = load_sheet_tab("Gamification_Tiers")

    TIER_COLORS = {
        "Bronze": "#cd7f32", "Silver": "#c0c0c0", "Gold": "#ffd700",
        "Platinum": "#e5e4e2", "Diamond": "#b9f2ff", "Apex": "#7c6af7",
    }
    TIER_ORDER = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Apex"]

    if df.empty:
        if not _sheets_configured():
            _render_sheets_setup_guide()
        else:
            st.info("No profile data found. Add rows to the Gamification_Tiers tab.")
        render_mentor_chat("🎮 Wealth Profile")
        return

    # ── Top operator card
    top_user = df.sort_values("Total_XP", ascending=False).iloc[0]
    tier      = top_user.get("Wealth_Tier", "Bronze")
    xp        = int(top_user.get("Total_XP", 0) or 0)
    tier_idx  = TIER_ORDER.index(tier) if tier in TIER_ORDER else 0
    xp_pct    = min(100, int((tier_idx / (len(TIER_ORDER) - 1)) * 100))

    tier_color = TIER_COLORS.get(tier, "#7c6af7")
    st.markdown(
        f"""
        <div class="metric-card" style="border-color:{tier_color};">
            <div class="label">TOP OPERATOR</div>
            <div class="value" style="color:{tier_color};">{tier} Tier</div>
            <div style="color:#a0a0c0;margin-top:6px;font-size:0.9rem;">
                {xp:,} XP · Literacy Score: {top_user.get('Literacy_Test_Score','?')}
            </div>
        </div>
        <div style="margin-bottom:8px;color:#7878a0;font-size:0.8rem;">TIER PROGRESS</div>
        <div class="xp-bar-wrap">
            <div class="xp-bar-fill" style="width:{xp_pct}%;background:linear-gradient(90deg,{tier_color},{tier_color}88);"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tier distribution
    if "Wealth_Tier" in df.columns:
        tier_counts = df["Wealth_Tier"].value_counts().reset_index()
        tier_counts.columns = ["Tier", "Count"]
        fig = px.bar(tier_counts, x="Tier", y="Count",
                     title="Operator Tier Distribution",
                     color="Tier",
                     color_discrete_map=TIER_COLORS,
                     template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # ── XP leaderboard
    if "Total_XP" in df.columns:
        st.subheader("🏆 XP Leaderboard")
        lb = df.sort_values("Total_XP", ascending=False)[["User_ID", "Wealth_Tier", "Total_XP", "Literacy_Test_Score"]].head(10)
        st.dataframe(lb, use_container_width=True, hide_index=True)

    # ── Unlocked advisors
    st.subheader("🔓 Unlocked Advisors")
    for _, row in df.iterrows():
        advisors_str = str(row.get("Unlocked_Advisors", ""))
        if advisors_str and advisors_str.lower() != "nan":
            st.markdown(f"**{row.get('User_ID','User')}** → {advisors_str}")

    st.divider()
    render_mentor_chat("🎮 Wealth Profile")


# ── 5. SYSTEM LOGS ────────────────────────────────────────────────
def render_system_logs() -> None:
    st.markdown('<div class="section-header">⚙️ System Logs</div>', unsafe_allow_html=True)

    with st.spinner("Loading system logs…"):
        df = load_sheet_tab("System_Logs")

    if df.empty:
        if not _sheets_configured():
            _render_sheets_setup_guide()
        else:
            st.info("No system logs found. Webhook events will appear here once fired.")
        render_mentor_chat("⚙️ System Logs")
        return

    total_events = len(df)
    errors       = df["Error_Logs"].notna().sum()          if "Error_Logs"      in df.columns else 0
    sms_sent     = (df["SMS_Sent_Status"] == "Sent").sum() if "SMS_Sent_Status" in df.columns else 0
    cal_updated  = (df["Calendar_Updated"] == "Yes").sum() if "Calendar_Updated" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric_card("Total Events",     str(total_events), "accent"),   unsafe_allow_html=True)
    with c2: st.markdown(metric_card("Errors Logged",    str(errors),       "negative"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card("SMS Sent",         str(sms_sent),     "positive"), unsafe_allow_html=True)
    with c4: st.markdown(metric_card("Calendar Synced",  str(cal_updated),  "positive"), unsafe_allow_html=True)

    # ── Event timeline
    if "Timestamp" in df.columns and "Webhook_Event" in df.columns:
        fig = px.scatter(
            df.sort_values("Timestamp"),
            x="Timestamp", y="Webhook_Event",
            color="Source" if "Source" in df.columns else None,
            title="Webhook Event Timeline",
            template="plotly_dark",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # ── Error log filter
    show_errors = st.checkbox("🔴 Show only error rows")
    display_df  = df[df["Error_Logs"].notna()] if show_errors and "Error_Logs" in df.columns else df

    st.subheader("📋 Raw Logs")
    st.dataframe(display_df.sort_values("Timestamp", ascending=False) if "Timestamp" in display_df.columns else display_df,
                 use_container_width=True, hide_index=True)

    st.divider()
    render_mentor_chat("⚙️ System Logs")


# ─────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────────
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:20px 0 10px;">
                <div style="font-size:2rem;">⚡</div>
                <div style="font-size:1.1rem;font-weight:700;color:#ffffff;">WealthForge OS</div>
                <div style="font-size:0.72rem;color:#5a5a7a;margin-top:2px;">v3.0 · Elite Operator</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user = st.session_state.get("username", "Operator")
        st.markdown(
            f'<div style="text-align:center;color:#7878a0;font-size:0.8rem;margin-bottom:16px;">'
            f'👤 {user}</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        selected_page = st.radio(
            "Navigation",
            NAV_PAGES,
            label_visibility="collapsed",
            key="main_nav",
        )

        st.divider()

        # Cache refresh
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")

        # ── Secrets / connection status panel
        with st.expander("🔍 Connection Status", expanded=False):
            # Google Sheets
            sheets_ok = _sheets_configured()
            st.markdown(
                f"**Google Sheets:** {'🟢 Connected' if sheets_ok else '🔴 No credentials'}",
                unsafe_allow_html=True,
            )
            if sheets_ok:
                try:
                    email = st.secrets["gcp_service_account"].get("client_email", "unknown")
                    st.caption(f"SA: `{email}`")
                except Exception:
                    pass

            # Groq
            groq_key = _get_secret("GROQ_API_KEY", "")
            st.markdown(
                f"**Groq AI:** {'🟢 Key set' if groq_key else '🔴 No GROQ_API_KEY'}",
            )

            # Webhooks
            sms_url = _get_secret("MAKE_SMS_WEBHOOK_URL", "")
            cal_url = _get_secret("MAKE_CALENDAR_WEBHOOK_URL", "")
            st.markdown(f"**SMS Webhook:** {'🟢 Set' if sms_url and 'PLACEHOLDER' not in sms_url else '🟡 Placeholder'}")
            st.markdown(f"**Calendar Webhook:** {'🟢 Set' if cal_url and 'PLACEHOLDER' not in cal_url else '🟡 Placeholder'}")

            # Sheet name check
            st.caption(f"Sheet: `{SPREADSHEET_NAME}`")

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown(
            '<div style="position:absolute;bottom:16px;width:100%;text-align:center;'
            'color:#3a3a5a;font-size:0.7rem;">WealthForge OS © 2025</div>',
            unsafe_allow_html=True,
        )

    return selected_page


# ─────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────
def main() -> None:
    # ── Authentication gate (core logic untouched)
    if not render_login_screen():
        st.stop()

    # ── Sidebar nav
    active_page = render_sidebar()

    # ── Route to the correct page renderer
    if active_page == "📊 Wealth Ledger":
        render_wealth_ledger()

    elif active_page == "🤝 Agency DealFlow & Clients":
        render_agency_dealflow()

    elif active_page == "💪 4F Daily Matrix":
        render_four_f_matrix()

    elif active_page == "🎮 Wealth Profile":
        render_wealth_profile()

    elif active_page == "⚙️ System Logs":
        render_system_logs()

    else:
        st.error("Unknown page selected. Please refresh.")


if __name__ == "__main__":
    main()
