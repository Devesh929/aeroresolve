# AeroResolve: Intelligent Aircraft Health-to-Action Platform

> **"Don't wait for the aircraft to become AOG. Make the ground ready while it is still in the air."**

---

## 1. Executive Summary

**AeroResolve** is an intelligent Aircraft Health-to-Action decision-support platform designed for modern commercial aviation engineering and maintenance operations. It detects emerging degradation before static warning thresholds trigger, investigates intermittent "ghost faults" by correlating flight envelope conditions, reconstructs probable physical root causes using multi-source evidence (high-frequency telemetry, ACARS fault messages, technical logs, component histories, and technical documentation via Snowflake Cortex Search & Cortex LLMs), evaluates destination station readiness (spares, tooling, certified personnel), predicts downstream operational blast radius and Aircraft-on-Ground (AOG) risk, orchestrates proactive ground maintenance packages, and monitors post-repair flights to verify whether the repair actually eliminated the defect signature.

The platform is modeled around synthetic Indian carrier **AeroBharat Airlines (ABR)** operating a fleet of 12 commercial narrow-body aircraft across 6 major hubs (DEL, BOM, BLR, HYD, CCU, MAA) and 10 regional/international destinations.

---

## 2. Critical Safety & Compliance Boundary

> [!CAUTION]
> **Synthetic Decision-Support Demonstration Only**  
> AeroResolve is NOT an aircraft airworthiness system and must **NEVER** autonomously make airworthiness, dispatch, Minimum Equipment List (MEL), return-to-service, or maintenance-release decisions. All maintenance actions and dispatch releases require certified, licensed human authority. All data, airline names (*AeroBharat Airlines*), aircraft tail numbers, flights, passengers, and sensor measurements generated for this project are 100% synthetic and do NOT represent any real-world airline, aircraft, or incident.

---

## 3. Core Workflow & Platform Capabilities

1. **Emerging Degradation Detection**: Snowflake ML multi-series anomaly detection and statistical trend analysis identifying subtle sensor creep before hard threshold breach.
2. **Ghost Fault Isolation**: Correlating transient faults with altitude, outside air temperature (OAT), vibration, and phase of flight to isolate environmental envelopes where faults trigger and disappear.
3. **Repeat Defect & Ineffective Repair Tracking**: Distinguishing palliative component swaps/resets from persistent physical root causes (e.g. rack wiring harness micro-fretting).
4. **Unified Evidence Synthesis**: Combining structured telemetry, ACARS messages, tech logs, and unstructured maintenance manuals via **Snowflake Cortex Search Service** (`AERO_TECH_MANUALS_SEARCH`) and **Cortex LLM reasoning** (`llama3.1-8b`).
5. **Destination Ground Readiness Audit**: Auditing destination station capabilities, engineer rosters, tooling, and part inventory; generating automated repositioning options when required (e.g., BOM -> DEL).
6. **Network Blast Radius & AOG Prediction**: Quantifying downstream flight rotation delays, passenger connection risks, and synthetic financial exposure.
7. **Strict Human-in-the-Loop Orchestration**: Mandatory human controller approval gate before dispatching work orders to external systems (Jira / GitHub via MCP). Zero autonomous actions.
8. **Post-Repair Effectiveness Verification**: Automated telemetry surveillance on subsequent sectors to confirm signal normalization (`REPAIR_EFFECTIVE_VERIFIED`).
9. **Fleet-Wide Case Memory**: Semantic precedent retrieval surfacing historical proven resolutions when sister aircraft exhibit similar signatures (e.g. ABR-042 matching ABR-017).
10. **Gold Verified Analytical Semantic Layer**: 7 dimensional views and 7 gold verified analytical views (`V_VERIFIED_*`) for natural language and deterministic business intelligence.

---

## 4. Current Status & Verification Baseline

- **Snowflake Database**: `AERORESOLVE` across 11 dedicated schemas (`RAW`, `CURATED`, `FEATURES`, `ML`, `KNOWLEDGE`, `SEMANTIC`, `AGENTS`, `OPS`, `APP`, `EVAL`, `AUDIT`).
- **Data Scale**: 12 aircraft tails, 800 flights, 302,400+ wide sensor observations (24.2M+ individual sensor channel measurements).
- **Test Suite**: **26/26 tests passing in pytest** (`tests/agents/`, `tests/data_quality/`, `tests/eval/`, `tests/unit/`).
- **Benchmark Suite**: **32/32 scenarios passed (100% pass rate)** in `tests/eval/run_agent_benchmarks.py`, 0.0% false alarm rate, 100% human gate compliance.
- **Operations Cockpit**: Dark aviation operations cockpit built in Streamlit (`frontend/streamlit/app.py`).

---

## 5. Repository Structure

```
coco_cli/
|-- PROJECT.md                      # Platform overview and mission
|-- ARCHITECTURE.md                 # System architecture, data flow & security
|-- BUILD_LOG.md                    # Progressive implementation phase log
|-- DECISIONS.md                    # Architectural decision records (ADRs)
|-- DEMO_SCRIPT.md                  # 23-step live demonstration walkthrough
|-- DATA_DICTIONARY.md              # 42 table schemas and semantic views
|-- TEST_PLAN.md                    # Comprehensive test strategy and results
|-- SECURITY.md                     # Security, RBAC, and credential hygiene
|-- COST_NOTES.md                   # Warehouse sizing and token economics
|-- SNOWFLAKE_OBJECTS.md            # Catalog of deployed Snowflake objects
|-- pytest.ini                      # Pytest runner configuration
|-- .env.example                    # Sanitized environment template
|-- backend/                        # Central connection, 6 specialist agents, tools, MCP dispatcher
|-- frontend/                       # Streamlit command center operations cockpit
|-- snowflake/                      # DDL, dynamic tables, streams, ML models, semantic views, Cortex search
|-- tests/                          # 26 automated unit, data quality, agent loop, and benchmark tests
|-- docs/                           # Capability audits, scorecard, benchmark evaluation results
```
