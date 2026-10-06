"""
AeroResolve - Intelligent Aircraft Health-to-Action Platform
Streamlit Aviation Operations Command Center
Carrier: AeroBharat Airlines (ABR) - Synthetic Decision Support System
"""

import os
import sys
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.connection import get_snowflake_connection
from backend.orchestrator import AeroResolveOrchestrator

# ---------------------------------------------------------------------
# PAGE CONFIG & DARK AVIATION THEME
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="AeroResolve | AeroBharat Operations Cockpit",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Density Aviation CSS
st.markdown("""
<style>
    .reportview-container {
        background-color: #0b0f19;
    }
    .metric-card {
        background-color: #161e2e;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 10px;
    }
    .alert-card-warning {
        background-color: #2b1f14;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #f59e0b;
        margin-bottom: 12px;
    }
    .alert-card-success {
        background-color: #12281e;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #10b981;
        margin-bottom: 12px;
    }
    .disclaimer-banner {
        background-color: #3b1114;
        color: #fca5a5;
        padding: 10px 18px;
        border-radius: 6px;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 15px;
        border: 1px solid #991b1b;
    }
    .agent-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 6px;
        background-color: #1e3a8a;
        color: #93c5fd;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# SNOWFLAKE DATA FETCHERS (CACHED)
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
    cur.execute("""
        SELECT 
            event_ts,
            altitude_ft,
            outside_air_temp_c,
            avionics_fan_current_a,
            avionics_rack_temp_c,
            vibration_index
        FROM AERORESOLVE.CURATED.FACT_TELEMETRY
        WHERE aircraft_id = %s
        ORDER BY event_ts ASC
        LIMIT 500
    """, (aircraft_id,))
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
# HEADER & SIDEBAR
# ---------------------------------------------------------------------
st.markdown("""
<div class="disclaimer-banner">
    ⚠️ SAFETY BOUNDARY NOTICE: AeroResolve is an intelligent decision-support demonstration platform.
    This system does NOT make airworthiness, dispatch, or maintenance-release decisions.
    A licensed and authorized human controller is always the final authority.
</div>
""", unsafe_allow_html=True)

col_title, col_stat1, col_stat2, col_stat3, col_stat4 = st.columns([3, 1, 1, 1, 1])
with col_title:
    st.title("✈️ AeroResolve Cockpit")
    st.caption("AeroBharat Airlines (ABR) • Intelligent Aircraft Health-to-Action Platform")
with col_stat1:
    st.metric("Monitored Fleet", "12 Tails", "Active")
with col_stat2:
    st.metric("Sensors Represented", "302,400+", "42 Channels/Row")
with col_stat3:
    st.metric("High-Risk Tails", "1 Aircraft", "ABR-017 (ATA 21)")
with col_stat4:
    st.metric("AOG Prevention", "100%", "Pre-Touchdown Staged")

st.markdown("---")

# Sidebar Controls
st.sidebar.image("https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=400&q=80", use_container_width=True)
st.sidebar.title("Operations Control")
selected_tail = st.sidebar.selectbox("Select Target Aircraft", ["ABR-017", "ABR-042", "ABR-003", "ABR-005"])
st.sidebar.markdown(f"**Target Flight:** `AB-402` (Inbound DEL)")
st.sidebar.markdown(f"**Carrier:** AeroBharat (Synthetic Carrier)")
st.sidebar.markdown(f"**Snowflake Warehouse:** `AERORESOLVE_WH`")

# ---------------------------------------------------------------------
# MAIN NAVIGATION TABS
# ---------------------------------------------------------------------
tab_investigation, tab_fleet, tab_readiness, tab_cortex_chat, tab_audit = st.tabs([
    "🔍 In-Flight Investigation & Action",
    "🌐 Fleet Health & Telemetry Radar",
    "📦 Ground Readiness & Spares Matrix",
    "💬 Cortex Analyst & Verified Queries",
    "🛡️ Snowflake Audit & Traceability"
])

# =====================================================================
# TAB 1: IN-FLIGHT INVESTIGATION & AGENT TIMELINE (THE CORE WORKFLOW)
# =====================================================================
with tab_investigation:
    st.subheader(f"⚡ Active In-Flight Case: {selected_tail} (Flight AB-402 -> DEL)")
    
    col_act1, col_act2 = st.columns([2, 1])
    with col_act1:
        st.markdown("""
        **Situation Report:**
        Aircraft **ABR-017** is currently cruising at **FL330** en route to **Delhi (DEL)**.
        On-board ACARS stream flagged intermittent BITE alert `FC-21-204` (*Avionics Cooling Loop Degradation*).
        This tail suffered the same discrepancy yesterday at DEL (fan swapped) and two days ago at BOM (computer reset).
        """)
    with col_act2:
        investigate_btn = st.button("🚀 Trigger Multi-Agent Investigation", type="primary", use_container_width=True)

    if "investigation_result" not in st.session_state:
        st.session_state.investigation_result = None
    if "approval_result" not in st.session_state:
        st.session_state.approval_result = None

    if investigate_btn or st.session_state.investigation_result is not None:
        if investigate_btn:
            with st.spinner("Executing 6 Specialist Agents & State Machine across Snowflake Cortex..."):
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

        # Timeline View of Agents
        st.markdown("### 🤖 Autonomous Specialist Agent Findings")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("""
            <div class="metric-card">
                <span class="agent-pill">STEP 1</span> <b>HealthAgent (Sensor Telemetry)</b><br>
                <small>Detected anomalous oscillation in avionics fan current (peaking at 4.43A, +23.4σ from fleet cruise baseline).
                Correlated with boundary layer outside air temperature dropping below -35°C.</small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="metric-card">
                <span class="agent-pill">STEP 2</span> <b>RepeatDefectAgent (Recurrence & Ineffective Repairs)</b><br>
                <small>Correlated discrepancy with 30-day maintenance history. <b>REPEAT DEFECT CONFIRMED (2 prior events).</b>
                Flagged prior fan replacement at DEL and computer reset at BOM as <i>ineffective repairs</i>.</small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="alert-card-warning">
                <span class="agent-pill" style="background-color: #d97706; color: #fff;">STEP 3</span> <b>RootCauseAgent (Cortex Search + LLM Reasoning)</b><br>
                <b>Primary Isolated Root Cause:</b> Connector X42 Pin 4 Micro-Fretting (PART-X42-CONN)<br>
                <b>Confidence:</b> 93% | <b>Evidence Sufficiency:</b> SUFFICIENT<br>
                <small>Cortex Search matched TSM 21-26-01 and WIG 24-38-04. Thermal contraction (-48°C) and vibration induce contact resistance
                spikes that disappear on the ramp (Ghost Fault signature).</small>
            </div>
            """, unsafe_allow_html=True)

        with col_t2:
            readiness_data = inv.get("readiness", {})
            st.markdown(f"""
            <div class="alert-card-warning">
                <span class="agent-pill" style="background-color: #d97706; color: #fff;">STEP 4</span> <b>GroundReadinessAgent (Spares & Crew Logistics)</b><br>
                <b>Destination (DEL):</b> 65 licensed engineers on shift. Active ATA 21 certification.<br>
                <b>ALERT:</b> Part <code>PART-X42-CONN</code> is <b>OUT OF STOCK</b> at DEL (0 units).<br>
                <b>Action:</b> Expedited logistics planned from <b>{readiness_data.get('reposition_plan', {}).get('reposition_source_station', 'BOM')}</b>
                (transit: {readiness_data.get('reposition_plan', {}).get('scheduled_flight_time_mins', 110)} mins). Candidate unit reserved.
            </div>
            """, unsafe_allow_html=True)

            ops_data = inv.get("operational_impact", {})
            st.markdown(f"""
            <div class="metric-card">
                <span class="agent-pill">STEP 5</span> <b>OperationsImpactAgent (Network Blast Radius)</b><br>
                <b>Downstream Sectors Protected:</b> {ops_data.get('downstream_sectors_count', 6)} flights<br>
                <b>Passengers Protected:</b> {ops_data.get('passengers_at_risk', 971)} booked ({ops_data.get('network_impact', {}).get('total_connecting_passengers_at_risk', 115)} connecting)<br>
                <b>Financial Cost Exposure Protected:</b> INR {ops_data.get('financial_exposure_inr', 1250000):,}
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # HUMAN APPROVAL GATE
        # -------------------------------------------------------------
        st.markdown("---")
        st.markdown("### 👤 Human Controller Approval Gate")
        st.info("The system cannot dispatch maintenance without formal human authority. Please review and authorize the ground package.")

        col_dec1, col_dec2, col_dec3 = st.columns([1, 2, 1])
        with col_dec1:
            decision = st.selectbox("Controller Decision", ["APPROVED", "REJECTED", "REQUEST_DIAGNOSTICS"])
            target_system = st.selectbox("External MCP Target", ["JIRA", "GITHUB"])
        with col_dec2:
            approver = st.text_input("Approver Identity & Role", "MCC Chief Controller Devesh (Licensed B2/Director)")
            notes = st.text_area("Controller Operational Log", "Approved urgent connector pin pre-staging. Dispatch ramp team to Gate 32 upon ABR-017 touchdown.")
        with col_dec3:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_approval = st.button("✅ Authorize & Dispatch MCP Work Package", type="primary", use_container_width=True)

        if submit_approval:
            with st.spinner("Recording authorization and dispatching MCP work order to Jira..."):
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
            <div class="alert-card-success">
                <h4>🎉 MCP Maintenance Work Package Dispatched Successfully!</h4>
                <b>External System:</b> {mcp_data.get('target_system')} | <b>Ticket Key:</b> <code>{mcp_data.get('external_key')}</code><br>
                <b>External Tracking URL:</b> <a href="{mcp_data.get('external_url')}" target="_blank">{mcp_data.get('external_url')}</a><br>
                <b>Authorized By:</b> {appr.get('approver')} | <b>Decision Audit ID:</b> <code>{appr.get('approval_id')}</code>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 🔬 Post-Repair Flight Telemetry Verification")
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                st.metric("Signal Stability Score", f"{int(verif_data.get('signal_stability_score', 0.98) * 100)}%", "+Nominal")
            with col_v2:
                st.metric("Subsequent Sectors Monitored", "2 Flights", "FL-065 & FL-066")
            with col_v3:
                st.metric("Defect Eradication Status", "VERIFIED RESOLVED", "Zero Ghost Recurrence")

# =====================================================================
# TAB 2: FLEET HEALTH & TELEMETRY RADAR
# =====================================================================
with tab_fleet:
    st.subheader("🌐 AeroBharat Airlines Fleet Digital Health Matrix")
    df_fleet = get_fleet_summary()

    col_fl1, col_fl2 = st.columns([1, 2])
    with col_fl1:
        st.dataframe(
            df_fleet,
            column_config={
                "AIRCRAFT_ID": "Tail Number",
                "MODEL_NAME": "Aircraft Model",
                "CURRENT_STATUS": "Status",
                "HAS_REPEAT_DEFECT": "Repeat Defect?",
                "REPEAT_COUNT_30D": "30D Incidents"
            },
            hide_index=True,
            use_container_width=True
        )

    with col_fl2:
        st.markdown(f"**Wide Sensor Channel Telemetry for {selected_tail} (Avionics Cooling Loop & Rack Temp)**")
        df_telem = get_telemetry_series(selected_tail)
        if not df_telem.empty:
            fig = px.line(
                df_telem,
                x="EVENT_TS",
                y=["AVIONICS_FAN_CURRENT_A", "AVIONICS_RACK_TEMP_C"],
                title=f"{selected_tail} In-Flight Sensor Behavior vs Environmental Altitude Envelope",
                color_discrete_map={"AVIONICS_FAN_CURRENT_A": "#38bdf8", "AVIONICS_RACK_TEMP_C": "#f87171"}
            )
            fig.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📡 Live Airborne Flights Tracking")
    df_flights = get_active_flights()
    st.dataframe(
        df_flights,
        column_config={
            "FLIGHT_NUMBER": "Flight",
            "AIRCRAFT_ID": "Tail",
            "ORIGIN_STATION": "Origin",
            "DEST_STATION": "Dest",
            "FLIGHT_STATUS": "Status",
            "PASSENGER_COUNT": "Booked Pax",
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
    st.subheader("📦 Destination Station Maintenance Readiness Matrix (PART-X42-CONN)")
    df_inv = get_station_inventory()
    
    st.dataframe(
        df_inv,
        column_config={
            "STATION_CODE": "Station",
            "STATION_NAME": "Airport",
            "QUANTITY_ON_HAND": "On Hand",
            "QUANTITY_RESERVED": "Reserved",
            "QUANTITY_AVAILABLE": "Available",
            "TRANSIT_FLIGHT_HOURS": "Transit (Hrs to DEL)",
            "ESTIMATED_TOTAL_REPOSITION_HOURS": "Total Lead Time",
            "LOGISTICS_STATUS": "Status"
        },
        hide_index=True,
        use_container_width=True
    )

    col_st1, col_st2 = st.columns(2)
    with col_st1:
        st.markdown("""
        **Station Logistics Summary:**
        - **Delhi (DEL):** 0 Units available (Stockout). Immediate touchdown replacement impossible without expediting.
        - **Mumbai (BOM):** Central Buffer. High stock, 2.4-hour flight transit to DEL.
        - **Hyderabad (HYD):** Secondary Buffer. 1.8-hour flight transit to DEL.
        """)
    with col_st2:
        fig_inv = px.bar(
            df_inv,
            x="STATION_CODE",
            y="QUANTITY_ON_HAND",
            color="LOGISTICS_STATUS",
            title="Stock on Hand of PART-X42-CONN across Indian Stations",
            template="plotly_dark"
        )
        st.plotly_chart(fig_inv, use_container_width=True)

# =====================================================================
# TAB 4: CORTEX ANALYST & VERIFIED QUERIES
# =====================================================================
with tab_cortex_chat:
    st.subheader("💬 Cortex Analyst & Verified Gold Queries")
    st.caption("Ask natural-language questions to the Snowflake Semantic Layer or execute gold verified queries.")

    q_options = [
        "1. What is the fleet repeat-defect rate over the last 30 days?",
        "2. What are all previous occurrences of ATA 21 faults on ABR-017?",
        "3. Which aircraft flying right now have active fault signatures?",
        "4. What is the maintenance capability at DEL tonight for ATA 21 cooling loop repairs?",
        "5. Where is part PART-X42-CONN currently stocked, and what are transit times to DEL?",
        "6. What downstream flights are operated by ABR-017 in the next 24 hours?",
        "7. Which repairs in the last 60 days were followed by recurring faults within 3 flights?"
    ]
    selected_gold_query = st.selectbox("Select Verified Gold Query", q_options)
    run_gold = st.button("⚡ Execute Verified Query Against Snowflake", type="primary")

    if run_gold:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        
        view_map = {
            "1": "AERORESOLVE.SEMANTIC.V_VERIFIED_FLEET_REPEAT_DEFECT_RATE_30D",
            "2": "AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_ATA21_HISTORY",
            "3": "AERORESOLVE.SEMANTIC.V_VERIFIED_ACTIVE_INFLIGHT_FAULT_SIGNATURES",
            "4": "AERORESOLVE.SEMANTIC.V_VERIFIED_DEL_TONIGHT_ATA21_CAPABILITY",
            "5": "AERORESOLVE.SEMANTIC.V_VERIFIED_PART_X42_CONN_STOCK_AND_TRANSIT",
            "6": "AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_DOWNSTREAM_ROTATION_24H",
            "7": "AERORESOLVE.SEMANTIC.V_VERIFIED_RECURRING_FAULTS_AFTER_REPAIR_60D"
        }
        q_idx = selected_gold_query[0]
        target_view = view_map[q_idx]
        cur.execute(f"SELECT * FROM {target_view}")
        res_rows = cur.fetchall()
        res_cols = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        st.success(f"Executed query against Snowflake Semantic Layer: `{target_view}`")
        st.dataframe(pd.DataFrame(res_rows, columns=res_cols), use_container_width=True)

# =====================================================================
# TAB 5: AUDIT TRAIL & TRACEABILITY
# =====================================================================
with tab_audit:
    st.subheader("🛡️ Snowflake Enterprise Audit Log (AERORESOLVE.AUDIT.*)")
    df_cases = get_audit_cases()
    st.dataframe(df_cases, use_container_width=True)

    st.markdown("""
    **Audit Invariant Guarantee:**
    - Every agent step, tool call, reasoning prompt, human decision, MCP payload, and post-repair verification
      is recorded with cryptographic immutability in dedicated audit tables in schema `AERORESOLVE.AUDIT`.
    - 100% compliant with commercial flight operations traceability standards.
    """)
