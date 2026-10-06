# AeroResolve — Master 23-Step Live Demonstration Script

> **"Don't wait for the aircraft to become AOG. Make the ground ready while it is still in the air."**  
> **Platform**: AeroResolve (Aircraft Health-to-Action Decision-Support Platform)  
> **Carrier**: AeroBharat Airlines (ABR)  
> **Scenario Aircraft**: `ABR-017` (Airbus A320neo family equivalent)  
> **En Route**: Flight `AB-402` (Bengaluru `BLR` to Delhi `DEL`)  
> **Audience**: Aviation Maintenance Controllers, Fleet Technical Directors, Airline CIOs

---

## Pre-Flight Setup & Launch

1. **Verify Environment**:
   ```powershell
   .\.venv\Scripts\activate
   pytest tests/ -v
   ```
   *Expected*: 26 passed in ~110 seconds.

2. **Launch Operations Cockpit**:
   ```powershell
   .\.venv\Scripts\streamlit.exe run frontend\streamlit\app.py
   ```
   *Expected*: Browser opens high-density dark aviation command center at `http://localhost:8501`.

---

## Act 1: The Airborne Signal & Emerging Degradation

3. **Fleet Radar & Global Metrics (Overview)**:
   - Point to top metric bar: 12 Active Aircraft, 800 Flight Sectors, 302,400+ Telemetry Observations (24.2M Sensor Channels).
   - Point to fleet status: 11 aircraft NOMINAL, 1 aircraft (`ABR-017`) flagged with active in-flight degradation.

4. **Aircraft Selection**:
   - In sidebar, ensure Aircraft is set to `ABR-017` and Flight is `FL-20261006-017-0060` (or `FL-DEMO-ABR-017`).
   - Destination Station: `DEL` (Indira Gandhi International Airport, Delhi).

5. **Multi-Channel Telemetry Divergence Graph**:
   - Scroll to the telemetry divergence chart:
     - **Avionics Cooling Fan Current**: Creeping from nominal baseline 2.2A up to 4.7A.
     - **Avionics Rack Temperature**: Climbing to 41.8°C (static warning limit is 42.0°C).
     - **Cruise Flight Envelope**: Altitude 34,000 ft, OAT -52°C, vibration index 1.28.
   - *Key Talking Point*: *"Traditional aircraft threshold alarms remain GREEN. Conventional maintenance wouldn't know anything is wrong until the plane reaches the gate or an in-flight warning fires. AeroResolve detects the multi-variate drift 45 minutes before touchdown."*

6. **The Intermittent "Ghost Fault" Spike**:
   - At time mark T+45min in cruise, the ACARS fault code triggers:
     - `FAULT-21-204`: *Avionics Cooling Air Flow Low*.
   - Because the aircraft is at -52°C with high cruise vibration, the discrepancy triggers intermittently.
   - *Key Talking Point*: *"When this aircraft lands in Delhi, the temperature will rise to +32°C, vibration stops, and ground engineers running BITE tests will find zero fault found (NFF). It's a classic ghost fault."*

---

## Act 2: Multi-Agent Autonomous Investigation Loop

7. **Trigger Investigation**:
   - Click the blue button: **[🚀 LAUNCH INVESTIGATION]**.
   - Show the 5-step agent execution timeline unfolding in real-time.

8. **Agent 1: Health Agent (Telemetry Window)**:
   - Expands sensor window: 18 fan current excursions outside nominal range.
   - Statistical divergence: +3.2σ from fleet baseline.
   - Output: `ANOMALY_CONFIRMED`.

9. **Agent 2: Repeat Defect Agent (30-Day Tech Log Correlation)**:
   - Recalls historical records for `ABR-017`:
     - 12 days ago: `FAULT-21-204` logged at DEL -> Action: BITE reset performed.
     - 5 days ago: `FAULT-21-204` logged at BOM -> Action: Avionics Ventilation Computer (AVCC) replaced.
   - Output: `REPEAT DEFECT CONFIRMED`. Prior component swap was **INEFFECTIVE**.
   - *Key Talking Point*: *"AeroResolve stops the vicious cycle of swapping computers. The computer was swapped 5 days ago and the fault came right back. The problem is NOT the computer."*

10. **Agent 3: Root Cause Agent (Cortex Search + LLM Reasoning)**:
    - Queries Snowflake Cortex Search Service `AERO_TECH_MANUALS_SEARCH` over 10 technical manuals.
    - Matches Technical Advisory `SIL-21-042` and `EAD-2026-21-09`:
      > *"Wiring harness connector X42 in avionics extraction circuit can develop pin micro-fretting corrosion under high vibration and cold cruise (-45°C), creating high-resistance spikes that simulate computer failure."*
    - Cortex LLM (`llama3.1-8b`) ranks hypotheses:
      - **Rank 1**: Wiring Harness Connector X42 Pin Micro-Fretting (Confidence: **88%**)
      - **Rank 2**: Avionics Ventilation Computer Board Failure (Confidence: **8%** — *Rejected due to ineffective swap 5 days ago*)
      - **Rank 3**: Cooling Fan Impeller Obstruction (Confidence: **4%** — *Rejected due to ground nominal current*)
    - Required Part: `PART-X42-CONN` (Connector Kit X42).

---

## Act 3: Destination Readiness & Network Blast Radius

11. **Agent 4: Ground Readiness Agent (Delhi Station Audit)**:
    - Audits `DEL` station resources:
      - B2 Licensed Avionics Engineers: **4 on duty** (READY)
      - Specialized Crimping Tool `TOOL-CRIMP-01`: **AVAILABLE** (READY)
      - Spare Part `PART-X42-CONN`: **0 AVAILABLE (STOCKOUT ALERT!)**
    - *Key Talking Point*: *"If we waited for the plane to land, the engineer would walk to the warehouse shelf, find ZERO units in stock, and the aircraft would be grounded (AOG) for hours."*

12. **Automated Repositioning Logistics**:
    - Ground Readiness Agent scans network inventory:
      - Mumbai (`BOM`): 2 serviceable units available.
      - Hyderabad (`HYD`): 2 serviceable units available.
    - Evaluates scheduled flights: Flight from BOM to DEL scheduled in 30 mins (flight time: 144 mins).
    - Reserves 1 unit at BOM and generates expedited cargo logistics package arriving ahead of the aircraft.

13. **Agent 5: Operations Impact Agent (Network Blast Radius)**:
    - Evaluates aircraft rotation schedule:
      - Next sector: `DEL` -> `DXB` (Flight `AB-501`, International departure, 186 passengers).
      - Turnaround window: 75 minutes.
    - Simulates unmitigated turnaround delay: **115 minutes delay**.
    - Downstream impact:
      - **4 subsequent sectors** disrupted on aircraft rotation.
      - **485 passengers** delayed.
      - **42 international connections** at Dubai (`DXB`) broken (London, New York, Frankfurt).
      - Synthetic financial risk: **₹14,80,000 (INR 14.8 Lakhs)** in delay penalties, hotel accommodation, and rebooking.
    - Connection Risk Level: `HIGH_RISK`.

---

## Act 4: Licensed Human Decision Gate & MCP Action

14. **Human Decision Gate (Safety Boundary)**:
    - Point to the Amber Safety Banner:
      > *"Decision-Support Platform Only. Certified human Maintenance Operations Controller approval required before dispatch."*
    - Notice that status is strictly: `AWAITING_HUMAN_APPROVAL`.
    - Zero autonomous work packages have been sent to Jira or logistics.

15. **Controller Review & Authorization**:
    - Enter Controller Name: `Chief Maintenance Controller Devesh`.
    - Role: `Authorized MCC Director`.
    - Action Target: `JIRA (Line Maintenance Dispatch)`.
    - Click **[✅ APPROVE PRE-STAGING & EXPEDITED LOGISTICS]**.

16. **Model Context Protocol (MCP) Work Package Creation**:
    - System instantly issues structured MCP payload.
    - Generated External Work Order: `AERO-0060` (or `AERO-017`).
    - Dispatched to Atlassian Jira / MRO line maintenance.
    - Payload logged immutably into `AERORESOLVE.AUDIT.EXTERNAL_ACTION` in Snowflake.

---

## Act 5: Post-Repair Surveillance & Fleet Learning

17. **Physical Repair Execution (Simulated)**:
    - Aircraft lands at Delhi Gate 32.
    - Connector kit `PART-X42-CONN` pre-staged from BOM fast flight.
    - Avionics technician inspects connector X42: pin micro-fretting confirmed. Connector assembly serviced in 65 minutes.
    - Turnaround completed on time without missing international departure to DXB.

18. **Subsequent Flight Surveillance (Repair Verification Agent)**:
    - View Post-Repair Surveillance tab.
    - Flight `DEL-DXB` monitored at 36,000 ft cruise.
    - Telemetry confirmed stable:
      - Fan current: **2.21A** (Nominal).
      - Excursions: **0**.
      - Anomaly recurred: **FALSE**.
      - Status: **`REPAIR_EFFECTIVE_VERIFIED`** (Confidence: 96%).
    - *Key Talking Point*: *"We closed the loop. We don't just order repairs; we verify in the air that the failure actually stopped recurring."*

19. **Fleet Learning & Precedent Memory (Sister Aircraft `ABR-042`)**:
    - Switch aircraft in sidebar to sister aircraft `ABR-042`.
    - Telemetry shows early upward current vibration divergence (similar early signature).
    - Repeat Defect Agent queries fleet memory:
      - Instantly surfaces resolved case `ABR-017`:
        > *"Sister aircraft ABR-017 experienced identical symptoms; computer swap failed; connector X42 pin service resolved defect."*
    - Directly guides engineering team to inspect connector X42, saving 2 wasted computer swaps and ₹45,000 in unnecessary maintenance cycles!

---

## Act 6: Executive Cortex Semantic Layer Analytics

20. **Cortex Verified Query Explorer**:
    - Switch to the "Semantic Intelligence" tab.
    - Run Query 1: *Fleet Repeat Defect Rate by ATA Chapter*.
      - Demonstrates ATA 21 (Air Conditioning) has highest recurrence rate in fleet.
    - Run Query 4: *Delhi Station Maintenance Capability Tonight*.
      - Demonstrates live shift capacity and tooling across stations.
    - Run Query 5: *Part Stock & Repositioning Routing*.
      - Confirms dynamic inventory across all 16 network stations.

21. **Snowflake Architecture Scorecard**:
    - Show that every single component is 100% native:
      - Dynamic Tables (`DT_*`)
      - Cortex Search Service (`AERO_TECH_MANUALS_SEARCH`)
      - Cortex LLMs (`llama3.1-8b`)
      - Semantic Views (`SEM_*` and `V_VERIFIED_*`)
      - Snowflake ML Anomaly Detection

22. **Auditing & Governance**:
    - Show `AERORESOLVE.AUDIT` schema:
      - `AGENT_CASE`
      - `AGENT_STEP`
      - `HUMAN_APPROVAL`
      - `EXTERNAL_ACTION`
      - `REPAIR_SURVEILLANCE`
      - `BENCHMARK_RUN_RESULTS`

23. **Closing Tagline**:
    > *"Don't wait for the aircraft to become AOG.  
    > Make the ground ready while it is still in the air.  
    > That is AeroResolve."*
