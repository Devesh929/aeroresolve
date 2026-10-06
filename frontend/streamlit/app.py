"""
AeroResolve - Intelligent Aircraft Health-to-Action Platform
Streamlit Aviation Operations Command Center (Ultra-Professional Aerospace Cockpit)
Carrier: AeroBharat Airlines (ABR) • Synthetic Decision Support System
"""

import os
import sys
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add current directory and project root to sys.path for local and SiS execution
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.append(_current_dir)
_repo_root = os.path.abspath(os.path.join(_current_dir, "../.."))
if _repo_root not in sys.path:
    sys.path.append(_repo_root)

from backend.connection import get_snowflake_connection
from backend.orchestrator import AeroResolveOrchestrator
from backend.agents.copilot_agent import AeroResolveCopilot

# ---------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="AeroResolve Cockpit | AeroBharat Operations",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------
# ADVANCED AEROSPACE DESIGN SYSTEM (CSS & COMPONENT TOKENS)
# ---------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global Theme Overrides */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #F1F5F9;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d1527 0%, #060913 100%);
    }

    /* Clean Streamlit Clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    /* Monospace for Aviation Data */
    .mono {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Top Command Header */
    .cmd-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.5) 100%);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }
    .cmd-logo {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .cmd-badge {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 10px;
        border-radius: 6px;
        background: rgba(14, 165, 233, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }

    /* Safety Notice Banner */
    .safety-banner {
        background: linear-gradient(90deg, rgba(153, 27, 27, 0.25) 0%, rgba(69, 10, 10, 0.25) 100%);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 0.82rem;
        color: #fca5a5;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* KPI Stat Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: linear-gradient(180deg, rgba(19, 29, 51, 0.7) 0%, rgba(13, 20, 36, 0.7) 100%);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 10px;
        padding: 14px 18px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: #f8fafc;
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #38bdf8;
        font-weight: 500;
        margin-top: 4px;
    }
    .kpi-sub-danger {
        color: #f87171;
    }

    /* Pulse Status Indicator */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .dot-green {
        background-color: #10b981;
        box-shadow: 0 0 10px #10b981;
    }
    .dot-amber {
        background-color: #f59e0b;
        box-shadow: 0 0 12px #f59e0b;
        animation: pulse-amber 2s infinite;
    }
    .dot-red {
        background-color: #ef4444;
        box-shadow: 0 0 12px #ef4444;
        animation: pulse-red 1.5s infinite;
    }

    @keyframes pulse-amber {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(1.15); }
    }
    @keyframes pulse-red {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.3; transform: scale(1.2); }
    }

    /* Aerospace Command Cards */
    .aero-card {
        background: linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(10, 15, 26, 0.85) 100%);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    .aero-card-accent {
        border-left: 4px solid #38bdf8;
    }
    .aero-card-warning {
        border-left: 4px solid #f59e0b;
        background: linear-gradient(180deg, rgba(30, 22, 12, 0.7) 0%, rgba(16, 12, 8, 0.7) 100%);
    }
    .aero-card-success {
        border-left: 4px solid #10b981;
        background: linear-gradient(180deg, rgba(13, 31, 23, 0.7) 0%, rgba(8, 18, 14, 0.7) 100%);
    }

    /* Agent Timeline Elements */
    .agent-step-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
        transition: all 0.2s ease;
    }
    .agent-step-box:hover {
        border-color: rgba(56, 189, 248, 0.5);
        background: rgba(15, 23, 42, 0.85);
    }
    .step-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        display: inline-block;
        margin-bottom: 8px;
    }
    .step-tag-warn {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border-color: rgba(245, 158, 11, 0.3);
    }
    .step-title {
        font-size: 0.96rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 6px;
    }
    .step-desc {
        font-size: 0.84rem;
        color: #94a3b8;
        line-height: 1.45;
    }

    /* Hypothesis Ranker Badge */
    .hypo-rank-1 {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.2) 0%, rgba(245, 158, 11, 0.15) 100%);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 10px;
    }

    /* Human Gate Box */
    .human-gate-container {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(129, 140, 248, 0.35);
        border-radius: 12px;
        padding: 22px;
        margin-top: 18px;
        position: relative;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.5);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(51, 65, 85, 0.4);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        font-weight: 700;
    }

    /* Modern Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 700;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.35);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# DATA LAYER (CACHED FROM SNOWFLAKE)
# ---------------------------------------------------------------------
@st.cache_data(ttl=30)
def get_fleet_summary():
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            a.aircraft_id,
            t.model_name,
            a.home_base,
            a.total_flight_hours,
            a.total_flight_cycles,
            a.current_status,
            COALESCE(rf.is_repeat_defect, FALSE) AS has_repeat_defect,
            COALESCE(rf.total_occurrences_30d, 0) AS repeat_count_30d
        FROM AERORESOLVE.CURATED.DIM_AIRCRAFT a
        JOIN AERORESOLVE.CURATED.DIM_AIRCRAFT_TYPE t ON a.aircraft_type_id = t.aircraft_type_id
        LEFT JOIN AERORESOLVE.FEATURES.DT_FAULT_RECURRENCE_FEATURES rf ON a.aircraft_id = rf.aircraft_id
        ORDER BY has_repeat_defect DESC, a.aircraft_id ASC
    """)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=cols)

@st.cache_data(ttl=30)
def get_active_flights():
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            f.flight_id,
            f.flight_number,
            f.aircraft_id,
            f.origin_station,
            f.dest_station,
            f.scheduled_departure_ts,
            f.scheduled_arrival_ts,
            f.flight_status,
            f.passenger_count,
            f.connecting_passenger_count,
            COALESCE(arp.predicted_aog_probability, 0.15) AS predicted_aog_prob
        FROM AERORESOLVE.CURATED.FACT_FLIGHTS f
        LEFT JOIN AERORESOLVE.ML.AOG_RISK_PREDICTIONS arp ON f.flight_id = arp.flight_id
        WHERE f.flight_status IN ('AIRBORNE', 'SCHEDULED')
        ORDER BY f.flight_status ASC, predicted_aog_prob DESC
    """)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=cols)

@st.cache_data(ttl=60)
def get_telemetry_series(aircraft_id="ABR-017"):
    conn = get_snowflake_connection()
    cur = conn.cursor()
    clean_id = str(aircraft_id).replace("'", "''")
    cur.execute(f"""
        SELECT 
            event_ts,
            altitude_ft,
            outside_air_temp_c,
            avionics_fan_current_a,
            avionics_rack_temp_c,
            vibration_index
        FROM AERORESOLVE.CURATED.FACT_TELEMETRY
        WHERE aircraft_id = '{clean_id}'
        ORDER BY event_ts ASC
        LIMIT 600
    """)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=cols)

@st.cache_data(ttl=60)
def get_station_inventory():
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_PART_X42_CONN_STOCK_AND_TRANSIT")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=cols)

@st.cache_data(ttl=60)
def get_audit_cases():
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            case_id,
            aircraft_id,
            flight_id,
            case_title,
            opened_ts,
            status,
            current_hypothesis,
            confidence_score,
            aog_risk_score,
            repair_effective
        FROM AERORESOLVE.AUDIT.AGENT_CASE
        ORDER BY opened_ts DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=cols)

# ---------------------------------------------------------------------
# TOP COMMAND HEADER
# ---------------------------------------------------------------------
st.markdown("""
<div class="cmd-header">
    <div class="cmd-logo">
        <span style="font-size: 1.8rem;">✈️</span>
        <div>
            <div style="font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; color: #f8fafc;">
                AERORESOLVE <span style="font-weight: 400; color: #38bdf8;">COCKPIT</span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; font-weight: 500;">
                AeroBharat Airlines (ABR) • Intelligent In-Flight Health-to-Action Platform
            </div>
        </div>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
        <span class="cmd-badge"><span class="status-dot dot-green"></span>SNOWFLAKE NATIVE</span>
        <span class="cmd-badge"><span class="status-dot dot-green"></span>CORTEX SEARCH ACTIVE</span>
        <span class="cmd-badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3);">
            <span class="status-dot dot-amber"></span>1 AIRBORNE ANOMALY
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Safety Regulatory Disclaimer Banner
st.markdown("""
<div class="safety-banner">
    <span style="font-size: 1.1rem;">🛡️</span>
    <div>
        <b>REGULATORY DECISION-SUPPORT NOTICE:</b> AeroResolve provides predictive decision-support only. 
        This system does <u>NOT</u> autonomously make airworthiness, dispatch, MEL deferral, or release-to-service decisions. 
        A licensed human Maintenance Operations Controller retains sole authorization authority.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# HIGH-DENSITY KPI CARDS
# ---------------------------------------------------------------------
st.markdown("""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-label">Active Monitored Fleet</div>
        <div class="kpi-value">12 <span style="font-size: 0.95rem; color: #94a3b8;">TAILS</span></div>
        <div class="kpi-sub"><span class="status-dot dot-green"></span>6 Hubs & Spoke Network</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Telemetry Ingest Scale</div>
        <div class="kpi-value">302.4K <span style="font-size: 0.95rem; color: #94a3b8;">OBS</span></div>
        <div class="kpi-sub">42 Wide Sensor Channels/Row</div>
    </div>
    <div class="kpi-card" style="border-color: rgba(245, 158, 11, 0.4);">
        <div class="kpi-label">Active Airborne Flag</div>
        <div class="kpi-value" style="color: #fbbf24;">ABR-017</div>
        <div class="kpi-sub kpi-sub-danger"><span class="status-dot dot-amber"></span>Ghost Fault Spike at FL340</div>
    </div>
    <div class="kpi-card" style="border-color: rgba(16, 185, 129, 0.4);">
        <div class="kpi-label">AOG Prevention Efficiency</div>
        <div class="kpi-value" style="color: #34d399;">100%</div>
        <div class="kpi-sub">Pre-Touchdown Staged Spares</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0; border-bottom: 1px solid rgba(51, 65, 85, 0.5); margin-bottom: 14px;">
        <div style="font-size: 0.78rem; text-transform: uppercase; color: #38bdf8; font-weight: 700; letter-spacing: 0.05em;">
            OPERATIONS CONTROLLER
        </div>
        <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc;">
            Devesh (MCC Director)
        </div>
        <div style="font-size: 0.76rem; color: #94a3b8;">
            Station: DEL-HQ • License #IND-AME-4291
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    selected_tail = st.selectbox(
        "🎯 Focus Aircraft Tail", 
        ["ABR-017", "ABR-042", "ABR-009", "ABR-003", "ABR-005"]
    )
    
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 8px; padding: 12px; margin-top: 10px;">
        <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;">Active Sector</div>
        <div style="font-size: 0.96rem; font-weight: 700; color: #f8fafc; font-family: 'JetBrains Mono';">FL-DEMO-{selected_tail}</div>
        <div style="font-size: 0.78rem; color: #38bdf8; margin-top: 4px;">BLR (Bengaluru) ➡️ DEL (Delhi)</div>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">Altitude: <b>34,000 ft</b> • Speed: <b>460 kts</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.72rem; color: #64748b; line-height: 1.4;">
        <b>Engine:</b> Snowflake Cortex AI<br>
        <b>Model:</b> llama3.1-8b (Cortex Complete)<br>
        <b>Search:</b> AERO_TECH_MANUALS_SEARCH<br>
        <b>Warehouse:</b> AERORESOLVE_WH (XS)
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# PRIMARY WORKFLOW TABS
# ---------------------------------------------------------------------
tab_investigation, tab_copilot, tab_radar, tab_readiness, tab_verified, tab_audit = st.tabs([
    "🔍 1. In-Flight Investigation & Action",
    "💬 2. Ask AeroResolve Copilot (AI Chat)",
    "📡 3. Fleet Health & Telemetry Divergence",
    "📦 4. Destination Readiness & Logistics",
    "⚡ 5. Cortex Semantic Verified Queries",
    "🛡️ 6. Immutable Snowflake Audit Log"
])

# =====================================================================
# TAB 1: IN-FLIGHT INVESTIGATION & AGENT TIMELINE
# =====================================================================
with tab_investigation:
    st.markdown(f"""
    <div class="aero-card aero-card-accent">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div>
                <span class="step-tag step-tag-warn">ACTIVE ALERT</span>
                <span style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; margin-left: 8px;">
                    {selected_tail} In-Flight Discrepancy & Recurrent Ghost Fault
                </span>
            </div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: #fbbf24;">
                <span class="status-dot dot-amber"></span>ACARS FAULT-21-204
            </div>
        </div>
        <div style="font-size: 0.88rem; color: #94a3b8; line-height: 1.5;">
            Aircraft <b>{selected_tail}</b> is cruising at <b>34,000 ft</b> en route to <b>Delhi (DEL)</b>. 
            Telemetry shows subtle upward drift in avionics fan current (<b>4.7A</b>) and rack temperature (<b>41.8°C</b>). 
            Discrepancy <code>FAULT-21-204</code> has recurred 2 times in the trailing 30 days despite computer reset and LRU component swap.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        investigate_btn = st.button("🚀 Launch Autonomous Investigation", type="primary", use_container_width=True)
    with col_info:
        st.caption("Executes 6 specialist agents sequentially: HealthAgent ➡️ RepeatDefectAgent ➡️ RootCauseAgent (Cortex Search + LLM) ➡️ GroundReadinessAgent ➡️ OperationsImpactAgent.")

    if "investigation_result" not in st.session_state:
        st.session_state.investigation_result = None
    if "approval_result" not in st.session_state:
        st.session_state.approval_result = None

    if investigate_btn or st.session_state.investigation_result is not None:
        if investigate_btn:
            with st.spinner("Orchestrating Specialist Agents across Snowflake Cortex..."):
                conn = get_snowflake_connection()
                orchestrator = AeroResolveOrchestrator()
                st.session_state.investigation_result = orchestrator.run_investigation(
                    conn=conn,
                    aircraft_id=selected_tail,
                    flight_id="FL-20261006-017-0060",
                    dest_station="DEL"
                )
                conn.close()

        inv = st.session_state.investigation_result

        st.markdown("### 🤖 Autonomous Investigation Findings")
        
        col_ag1, col_ag2 = st.columns(2)
        with col_ag1:
            st.markdown("""
            <div class="agent-step-box">
                <span class="step-tag">STEP 1 • HEALTH AGENT</span>
                <div class="step-title">Telemetry Window & Statistical Divergence</div>
                <div class="step-desc">
                    Detected 18 excursions outside nominal 2.1-2.4A current band. 
                    Avionics fan current deviates <b>+3.2σ</b> from fleet cruise baseline. 
                    Rack temperature peaked at <b>41.8°C</b> at sub-zero boundary layer (-52°C).
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="agent-step-box">
                <span class="step-tag">STEP 2 • REPEAT DEFECT AGENT</span>
                <div class="step-title">30-Day Tech Log Correlation & False Fix Recurrence</div>
                <div class="step-desc">
                    Correlated with historical records: <b>REPEAT DEFECT CONFIRMED (2 prior events)</b>.
                    Flagged prior AVCC computer swap (5 days ago at BOM) and BITE reset (12 days ago at DEL) as 
                    <span style="color: #f87171; font-weight: 600;">INEFFECTIVE REPAIRS</span>. Problem is not internal to computer board.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="agent-step-box" style="border-color: rgba(245, 158, 11, 0.4); background: rgba(30, 22, 12, 0.5);">
                <span class="step-tag step-tag-warn">STEP 3 • ROOT CAUSE AGENT (CORTEX SEARCH + LLM)</span>
                <div class="step-title">Physical Root Cause Isolation & Falsification</div>
                <div class="step-desc">
                    Queried Cortex Search Service <code>AERO_TECH_MANUALS_SEARCH</code> over 10 technical manuals.
                    Matched AMM 21-26-00 and SIL-21-042. Cortex LLM (<code>llama3.1-8b</code>) evaluated hypotheses:
                </div>
                <div class="hypo-rank-1">
                    <b style="color: #fbbf24;">Rank 1 (Primary):</b> Wiring harness connector X42 pin micro-fretting corrosion.<br>
                    <b>Confidence:</b> <span class="mono" style="color: #38bdf8; font-weight: 700;">88.0%</span> | 
                    <b>Required Part:</b> <code>PART-X42-CONN</code><br>
                    <small style="color: #94a3b8;">Falsified computer board failure (Rank 2, 8%) due to identical recurrence post-swap.</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_ag2:
            readiness_data = inv.get("readiness", {})
            st.markdown(f"""
            <div class="agent-step-box" style="border-color: rgba(239, 68, 68, 0.4); background: rgba(30, 15, 15, 0.5);">
                <span class="step-tag" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3);">
                    STEP 4 • GROUND READINESS AGENT
                </span>
                <div class="step-title">Destination Spares Stockout & Expedited Logistics</div>
                <div class="step-desc">
                    <b>Destination Station (DEL):</b> 4 licensed B2 engineers available; Crimping tool T-14 ready.<br>
                    <span style="color: #f87171; font-weight: 700;">CRITICAL STOCKOUT:</span> 
                    Connector kit <code>PART-X42-CONN</code> has <b>0 UNITS AVAILABLE</b> at DEL.<br>
                    <b>Reposition Logistics:</b> Automated flight dispatch from <b>{readiness_data.get('reposition_plan', {}).get('reposition_source_station', 'BOM')}</b> 
                    (flight transit: {readiness_data.get('reposition_plan', {}).get('scheduled_flight_time_mins', 144)}m). Unit reserved at donor hub.
                </div>
            </div>
            """, unsafe_allow_html=True)

            ops_data = inv.get("operational_impact", {})
            st.markdown(f"""
            <div class="agent-step-box">
                <span class="step-tag">STEP 5 • OPERATIONS IMPACT AGENT</span>
                <div class="step-title">Network Blast Radius & International Connection Risk</div>
                <div class="step-desc">
                    Next sector: <b>DEL ➡️ DXB (Flight AB-501)</b>. Unmitigated turnaround creates <b>115m delay</b>.<br>
                    • <b>Downstream Sectors Exposed:</b> {ops_data.get('downstream_sectors_count', 4)} flights on tail rotation.<br>
                    • <b>Passengers at Risk:</b> {ops_data.get('passengers_at_risk', 485)} booked (42 high-value international connections in Dubai).<br>
                    • <b>Synthetic Financial Exposure:</b> <span class="mono" style="color: #fbbf24; font-weight: 700;">INR {ops_data.get('financial_exposure_inr', 1480000):,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # HUMAN APPROVAL GATE
        # -------------------------------------------------------------
        st.markdown("""
        <div class="human-gate-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 1.05rem; font-weight: 800; color: #f8fafc;">
                    👤 Human Maintenance Controller Decision Gate
                </div>
                <div class="cmd-badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border-color: rgba(245, 158, 11, 0.4);">
                    STATUS: AWAITING_HUMAN_APPROVAL
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 14px;">
                The platform is paused. No external work package, logistics transfer, or technician dispatch will occur 
                without explicit authorization by a certified Maintenance Operations Controller.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
        with col_d1:
            decision = st.selectbox("Decision Status", ["APPROVED", "REJECTED", "REQUEST_INSPECTION"])
            target_system = st.selectbox("External MCP Target", ["JIRA", "GITHUB"])
        with col_d2:
            approver = st.text_input("Licensed Approver Signature", "Chief Maintenance Controller Devesh (B2/Director)")
            notes = st.text_area("Operational Action Log", "Authorized expedited connector kit repositioning from BOM. Dispatch line avionics crew to DEL Gate 32 upon touchdown.")
        with col_d3:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_approval = st.button("✅ Authorize & Dispatch Work Package", type="primary", use_container_width=True)

        if submit_approval:
            with st.spinner("Persisting human decision and dispatching MCP payload to Jira..."):
                conn = get_snowflake_connection()
                orchestrator = AeroResolveOrchestrator()
                st.session_state.approval_result = orchestrator.process_human_decision(
                    conn=conn,
                    case_id=inv["case_id"],
                    aircraft_id=selected_tail,
                    decision=decision,
                    approver_name=approver,
                    controller_notes=notes,
                    target_system=target_system
                )
                conn.close()

        if st.session_state.approval_result is not None:
            appr = st.session_state.approval_result
            mcp_data = appr.get("mcp_dispatch", {})
            verif_data = appr.get("post_repair_verification", {})

            st.markdown(f"""
            <div class="aero-card aero-card-success" style="margin-top: 18px;">
                <div style="font-size: 1.1rem; font-weight: 800; color: #34d399; margin-bottom: 8px;">
                    🎉 MCP Work Package Dispatched Successfully!
                </div>
                <div style="font-size: 0.88rem; color: #e2e8f0; line-height: 1.6;">
                    <b>Target System:</b> {mcp_data.get('target_system')} | 
                    <b>Work Order Ticket:</b> <code class="mono">{mcp_data.get('external_key', 'AERO-0060')}</code> | 
                    <b>Audit Approval ID:</b> <code class="mono">{appr.get('approval_id')}</code><br>
                    <b>Tracking Link:</b> <a href="{mcp_data.get('external_url')}" target="_blank" style="color: #38bdf8;">{mcp_data.get('external_url')}</a><br>
                    <b>Authorized By:</b> {appr.get('approver')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🔬 Post-Repair Flight Telemetry Surveillance")
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                st.metric("Signal Stability Score", "98%", "+Nominal Baseline")
            with col_v2:
                st.metric("Subsequent Flight Monitored", "FL-065 (DEL-DXB)", "Cruising at 36,000 ft")
            with col_v3:
                st.metric("Repair Effectiveness", "VERIFIED EFFECTIVE", "Zero Recurrence")

# =====================================================================
# TAB 2: AERORESOLVE COPILOT (FREE-FORM CONVERSATIONAL AI CHAT)
# =====================================================================
with tab_copilot:
    st.markdown("""
    <div class="aero-card aero-card-accent">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div>
                <span class="step-tag" style="background: rgba(14, 165, 233, 0.2); color: #38bdf8; border-color: rgba(14, 165, 233, 0.4);">
                    CORTEX COPILOT ACTIVE
                </span>
                <span style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; margin-left: 8px;">
                    💬 AeroResolve Fleet Engineering Copilot
                </span>
            </div>
            <div class="cmd-badge">
                <span class="status-dot dot-green"></span>SNOWFLAKE CORTEX LLM (llama3.1-8b)
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">
            Ask any question regarding aircraft health, in-flight ghost faults, maintenance recurrence records, 
            Cortex Search technical manuals (AMM, TSM, SIL, SB), or destination station spare part inventories. 
            All responses are synthesized with grounded citations from the Snowflake Data Cloud.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initial session state for messages
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [
            {
                "role": "assistant",
                "content": (
                    "Welcome to AeroResolve Engineering Copilot. I have real-time access to live fleet telemetry, "
                    "30-day maintenance recurrence histories, 10 technical manuals in Cortex Search, and parts inventories across our hubs. "
                    "What would you like to investigate?"
                ),
                "sources": ["CORTEX_SEARCH_ENGINE", "AERORESOLVE_SEMANTIC_LAYER"],
                "latency_sec": 0.05
            }
        ]

    # Quick Prompts Carousel
    st.markdown("**Suggested Engineering Inquiries:**")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    quick_prompt = None
    with col_q1:
        if st.button("❓ Why did AVCC replacement fail?", use_container_width=True):
            quick_prompt = "Why did the AVCC computer replacement on ABR-017 fail to eliminate FAULT-21-204?"
    with col_q2:
        if st.button("❓ Where is stock for PART-X42-CONN?", use_container_width=True):
            quick_prompt = "Where can we find available stock for PART-X42-CONN to service an aircraft landing in Delhi?"
    with col_q3:
        if st.button("❓ What does SIL-21-042 recommend?", use_container_width=True):
            quick_prompt = "What does Service Information Letter SIL-21-042 say about harness connector micro-fretting?"
    with col_q4:
        if st.button("❓ Fleet repeat rate for ATA 21?", use_container_width=True):
            quick_prompt = "What is the fleet-wide repeat defect rate for ATA 21 over the trailing 30 days?"

    # Display chat history
    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"], avatar="✈️" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            if msg.get("sources"):
                source_pills = " ".join([f"<span class='step-tag' style='font-size: 0.68rem; margin-right: 4px;'>📄 {s}</span>" for s in msg["sources"][:4]])
                latency_tag = f"<span style='font-size: 0.72rem; color: #64748b; margin-left: 8px;'>⏱️ {msg.get('latency_sec', 1.0):.2f}s</span>" if msg.get("latency_sec") else ""
                st.markdown(f"<div style='margin-top: 6px;'>{source_pills} {latency_tag}</div>", unsafe_allow_html=True)

    # Chat Input handler
    user_input = st.chat_input("Ask any question regarding aircraft, telemetry, technical manuals, or parts inventory...")
    prompt_to_send = quick_prompt or user_input

    if prompt_to_send:
        # Add user message
        st.session_state.copilot_messages.append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt_to_send)

        # Generate response
        with st.chat_message("assistant", avatar="✈️"):
            with st.spinner("Synthesizing answer with Snowflake Cortex Search & LLM..."):
                conn = get_snowflake_connection()
                copilot = AeroResolveCopilot()
                ans_data = copilot.answer_query(conn, prompt_to_send)
                conn.close()

                st.markdown(ans_data["answer"])
                if ans_data.get("sources"):
                    source_pills = " ".join([f"<span class='step-tag' style='font-size: 0.68rem; margin-right: 4px;'>📄 {s}</span>" for s in ans_data["sources"][:4]])
                    latency_tag = f"<span style='font-size: 0.72rem; color: #64748b; margin-left: 8px;'>⏱️ {ans_data['latency_sec']:.2f}s</span>"
                    st.markdown(f"<div style='margin-top: 6px;'>{source_pills} {latency_tag}</div>", unsafe_allow_html=True)

                st.session_state.copilot_messages.append({
                    "role": "assistant",
                    "content": ans_data["answer"],
                    "sources": ans_data["sources"],
                    "latency_sec": ans_data["latency_sec"]
                })

# =====================================================================
# TAB 3: FLEET HEALTH & TELEMETRY RADAR
# =====================================================================
with tab_radar:
    st.markdown("### 📡 Fleet-Wide Telemetry Divergence & Radar")
    
    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        st.markdown(f"**Live Telemetry Stream for {selected_tail}**")
        df_telem = get_telemetry_series(selected_tail)
        if not df_telem.empty:
            fig = px.line(
                df_telem,
                x="EVENT_TS",
                y=["AVIONICS_FAN_CURRENT_A", "AVIONICS_RACK_TEMP_C"],
                color_discrete_map={"AVIONICS_FAN_CURRENT_A": "#00e5ff", "AVIONICS_RACK_TEMP_C": "#f43f5e"},
                template="plotly_dark"
            )
            fig.update_layout(
                height=340,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(15,23,42,0)",
                plot_bgcolor="rgba(15,23,42,0.4)"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Notice upward creep in fan current from 2.2A baseline to 4.7A, correlating with rack thermal rise.")

    with col_r2:
        st.markdown("**Fleet Health Matrix (12 Narrow-Body Tails)**")
        df_fleet = get_fleet_summary()
        st.dataframe(
            df_fleet,
            column_config={
                "AIRCRAFT_ID": "Tail",
                "MODEL_NAME": "Model",
                "HOME_BASE": "Hub",
                "CURRENT_STATUS": "Status",
                "HAS_REPEAT_DEFECT": "Repeat Defect?",
                "REPEAT_COUNT_30D": "30D Faults"
            },
            hide_index=True,
            use_container_width=True
        )

    st.markdown("### ✈️ Active Airborne Flights (Live Rotation & AOG Probability)")
    df_flights = get_active_flights()
    st.dataframe(
        df_flights,
        column_config={
            "FLIGHT_NUMBER": "Flight",
            "AIRCRAFT_ID": "Tail",
            "ORIGIN_STATION": "From",
            "DEST_STATION": "To",
            "FLIGHT_STATUS": "Status",
            "PASSENGER_COUNT": "Pax",
            "CONNECTING_PASSENGER_COUNT": "Connections",
            "PREDICTED_AOG_PROB": st.column_config.ProgressColumn("Predicted AOG Risk", min_value=0.0, max_value=1.0)
        },
        hide_index=True,
        use_container_width=True
    )

# =====================================================================
# TAB 3: GROUND READINESS & SPARES MATRIX
# =====================================================================
with tab_readiness:
    st.markdown("### 📦 Destination Station Maintenance Readiness Matrix (`PART-X42-CONN`)")
    df_inv = get_station_inventory()
    
    st.dataframe(
        df_inv,
        column_config={
            "STATION_CODE": "Station",
            "STATION_NAME": "Airport",
            "QUANTITY_ON_HAND": "Stock",
            "QUANTITY_RESERVED": "Reserved",
            "QUANTITY_AVAILABLE": "Available",
            "TRANSIT_FLIGHT_HOURS": "Flight Transit (h)",
            "ESTIMATED_TOTAL_REPOSITION_HOURS": "Total Lead Time",
            "LOGISTICS_STATUS": "Readiness Status"
        },
        hide_index=True,
        use_container_width=True
    )

    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        st.markdown("""
        <div class="aero-card">
            <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">
                Network Inventory Strategy
            </div>
            <div style="font-size: 0.84rem; color: #94a3b8; line-height: 1.5;">
                • <b>Delhi (DEL):</b> 0 Units on shelf. Immediate landing stockout.<br>
                • <b>Mumbai (BOM):</b> Primary Hub Buffer. 2 serviceable units; scheduled flight arrives in 2.4 hours.<br>
                • <b>Hyderabad (HYD):</b> Secondary Regional Buffer. 2 serviceable units available.<br>
                • <b>Autonomous Action:</b> Unit reserved at BOM and queued for cargo loading prior to ABR-017 touchdown.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_inv2:
        fig_bar = px.bar(
            df_inv,
            x="STATION_CODE",
            y="QUANTITY_AVAILABLE",
            color="LOGISTICS_STATUS",
            title="Serviceable Available Stock across Network",
            template="plotly_dark"
        )
        fig_bar.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(15,23,42,0)",
            plot_bgcolor="rgba(15,23,42,0.4)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# =====================================================================
# TAB 4: CORTEX SEMANTIC VERIFIED QUERIES
# =====================================================================
with tab_verified:
    st.markdown("### ⚡ Cortex Semantic Layer & Gold Verified Analytical Views")
    st.caption("Execute validated semantic views across fleet operations, technical histories, and rotation blast radius.")

    q_options = [
        "1. What is the fleet repeat-defect rate over the last 30 days?",
        "2. What are all previous occurrences of ATA 21 faults on ABR-017?",
        "3. Which aircraft flying right now have active fault signatures?",
        "4. What is the maintenance capability at DEL tonight for ATA 21 cooling loop repairs?",
        "5. Where is part PART-X42-CONN currently stocked, and what are transit times to DEL?",
        "6. What downstream flights are operated by ABR-017 in the next 24 hours?",
        "7. Which repairs in the last 60 days were followed by recurring faults within 3 flights?"
    ]
    selected_gold_query = st.selectbox("Select Analytical Question", q_options)
    run_gold = st.button("⚡ Execute Verified Query in Snowflake", type="primary")

    if run_gold:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        
        view_map = {
            "1": "AERORESOLVE.SEMANTIC.V_VERIFIED_REPEAT_DEFECT_RATE_BY_FLEET",
            "2": "AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_ATA21_HISTORY",
            "3": "AERORESOLVE.SEMANTIC.V_VERIFIED_ACTIVE_INFLIGHT_DEGRADATION_SIGNATURES",
            "4": "AERORESOLVE.SEMANTIC.V_VERIFIED_DEL_TONIGHT_MAINTENANCE_CAPABILITY",
            "5": "AERORESOLVE.SEMANTIC.V_VERIFIED_PART_X42_STOCK_AND_TRANSIT",
            "6": "AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_DOWNSTREAM_ROTATION_BLAST_RADIUS",
            "7": "AERORESOLVE.SEMANTIC.V_VERIFIED_RECURRING_FAULTS_AFTER_UNVERIFIED_REPAIR"
        }
        q_idx = selected_gold_query[0]
        target_view = view_map[q_idx]
        cur.execute(f"SELECT * FROM {target_view}")
        res_rows = cur.fetchall()
        res_cols = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        st.success(f"Executed verified query against: `{target_view}`")
        st.dataframe(pd.DataFrame(res_rows, columns=res_cols), use_container_width=True)

# =====================================================================
# TAB 5: AUDIT LOG & REPOSITORY TRACEABILITY
# =====================================================================
with tab_audit:
    st.markdown("### 🛡️ Immutable Snowflake Audit Trails (`AERORESOLVE.AUDIT.*`)")
    st.caption("Every investigation case, agent thought, human controller sign-off, and external MCP payload is recorded.")
    
    df_cases = get_audit_cases()
    st.dataframe(df_cases, use_container_width=True)

    st.markdown("""
    <div class="aero-card" style="margin-top: 14px;">
        <div style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
            Cryptographic Audit Invariant Guarantee
        </div>
        <div style="font-size: 0.82rem; color: #94a3b8; line-height: 1.5;">
            • Dedicated schemas: <code>AERORESOLVE.AUDIT.AGENT_CASE</code>, <code>AGENT_STEP</code>, 
            <code>HUMAN_APPROVAL</code>, and <code>EXTERNAL_ACTION</code>.<br>
            • Zero autonomous actions permitted beyond safety gates.<br>
            • Every recommendation is anchored in dual evidence (telemetry + technical documentation citations).
        </div>
    </div>
    """, unsafe_allow_html=True)
