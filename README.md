<div align="center">

# ✈️ AeroResolve
### Synthetic Aircraft Health-to-Action Decision-Support Platform
**Operator: AeroBharat Airlines (ABR) • Powered by Snowflake Native AI & Streamlit in Snowflake (SiS)**

[![Snowflake](https://img.shields.io/badge/Snowflake-Native%20AI-29B5E8?logo=snowflake&logoColor=white)](https://www.snowflake.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?logo=streamlit&logoColor=white)](https://aeroresolve.streamlit.app/)
[![Model](https://img.shields.io/badge/Cortex%20LLM-Llama%203.1%208B%20%7C%2070B-purple)](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
[![Tests](https://img.shields.io/badge/Benchmark%20Pass%20Rate-100%25%20(32%2F32)-success)](docs/EVAL_RESULTS.md)
[![Safety](https://img.shields.io/badge/Safety%20Boundary-Human--in--the--Loop-orange)](SECURITY.md)

</div>

---

> ⚠️ **REGULATORY SAFETY NOTICE & NON-AIRWORTHINESS BOUNDARY**:  
> *AeroResolve is a synthetic decision-support platform designed for operational planning, fault diagnosis exploration, and logistics readiness. It does **not** autonomously perform airworthiness determinations or dispatch authorizations. In accordance with DGCA CAR Section 2, FAA 14 CFR § 121, and EASA Part-M regulations, all maintenance actions, deferrals, and return-to-service sign-offs remain under the exclusive final authority of licensed AME / FAA Part 66 certifying engineers and Airline Operations Control (AOC) dispatchers.*

---

## 🌐 Live Application URL

The AeroResolve Operations Cockpit is live and accessible globally:

* **Live Public Cockpit**: [**https://aeroresolve.streamlit.app/**](https://aeroresolve.streamlit.app/)
* **Snowflake Native Backend**: Powered by Snowflake Native AI, Cortex Search & Dynamic Tables
* **Runtime**: Python 3.10 • Streamlit • Snowpark Session & Snowflake Connector

---

## 🎯 Platform Overview

Modern commercial airlines face crippling unscheduled delays when telemetry faults, pilot logbooks, inventory shortages, and flight schedules are trapped in disparate data silos.

**AeroResolve** unifies aircraft telemetry, maintenance records, technical manuals, and turnaround schedules into a **single Snowflake-native multi-agent intelligence platform**:

1. **Deterministic Telemetry & Feature Pipelines**: Real-time sliding-window telemetry aggregation and repeat fault recurrence metrics computed via **Snowflake Dynamic Tables**.
2. **Hybrid Technical Search**: High-dimensional semantic search over Airbus A320 & Boeing 737 AMM/FCOM technical manuals powered by **Snowflake Cortex Search Service**.
3. **Multi-Agent Specialist Swarm**: Five specialized agents orchestrated through Model Context Protocol (MCP) tool dispatching:
   - 🔍 **Health & Telemetry Agent**: Evaluates sensor anomalies against operating envelopes.
   - 🧬 **Root Cause & Technical Manual Agent**: Retrieves AMM procedures and hypothesizes root causes.
   - 🔁 **Repeat Defect Agent**: Identifies recurring 7/30-day defects and warns against premature part swapping.
   - ⏱️ **Ground Readiness & Turnaround Agent**: Verifies parts inventory, certified personnel, ground equipment, and turnaround windows.
   - ⚡ **Operational Impact Agent**: Computes downstream passenger disruption and delay cost projections.
4. **Conversational Engineering Copilot**: Free-form aerospace chat assistant with direct access to Snowflake Cortex LLM, semantic metrics, and technical document embeddings.
5. **Human Approval Gateway**: Strict human-in-the-loop authorization barrier before any draft work order or deferral recommendation is locked into the ERP.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph "Data Ingestion & Snowflake Layer"
        RAW[Raw Telemetry, ACARS, Flight Ops] --> CUR[Curated Dimension & Fact Tables]
        CUR --> DT[Dynamic Tables: Features & Recurrence]
        MANUALS[AMM / FCOM Technical Manuals] --> CORTEX_SEARCH[Cortex Search Service: AERO_TECH_MANUALS_SEARCH]
    end

    subgraph "AeroResolve Multi-Agent Orchestrator (MCP)"
        ORCH[Agent Orchestrator]
        ORCH --> A1[Health Agent]
        ORCH --> A2[Root Cause Agent]
        ORCH --> A3[Repeat Defect Agent]
        ORCH --> A4[Ground Readiness Agent]
        ORCH --> A5[Ops Impact Agent]
        
        A1 & A2 & A3 & A4 & A5 --> MCP[MCP Dispatcher / Snowflake Tools]
        MCP --> CORTEX_LLM[Cortex LLM: Llama 3.1 8B / 70B]
        MCP --> CORTEX_SEARCH
        MCP --> DT
    end

    subgraph "Human-in-the-Loop Cockpit"
        COPILOT[AeroResolve Copilot Chat]
        COCKPIT[Aviation Operations Cockpit]
        GATE{Human Engineer Approval Gate}
        
        ORCH --> COCKPIT
        COCKPIT --> GATE
        GATE -->|Certified Sign-Off| WORKORDER[ERP / MRO Work Order Dispatched]
        GATE -->|Reject / Defer| DEFERRAL[MEL Deferral Logged]
    end
```

---

## 📁 Repository Structure

```text
├── backend/
│   ├── agents/                     # Specialized reasoning agents
│   │   ├── copilot_agent.py        # Conversational AI copilot
│   │   ├── health_agent.py         # Telemetry envelope monitoring
│   │   ├── root_cause_agent.py     # AMM/FCOM troubleshooting & diagnosis
│   │   ├── repeat_defect_agent.py  # 7d/30d recurrence pattern analysis
│   │   ├── ground_readiness_agent.py # Spares, tooling, bay & labor verification
│   │   └── ops_impact_agent.py     # Delay cost & passenger impact projections
│   ├── tools/                      # MCP-compliant Snowflake tool functions
│   │   ├── telemetry_tools.py      # Telemetry queries & window features
│   │   ├── knowledge_tools.py      # Cortex Search & AMM retrieval
│   │   ├── recurrence_tools.py     # Repeat defect scoring & history
│   │   ├── readiness_tools.py      # Station inventory, tech certification & bays
│   │   ├── impact_tools.py         # Flight schedules & delay impact calculation
│   │   └── verification_tools.py   # Ground run-up & post-maintenance verification
│   ├── orchestrator.py             # Multi-agent coordinator & human gate barrier
│   ├── mcp_dispatcher.py           # Tool dispatching with schema validation
│   └── connection.py               # Dual-mode connector (PAT + SiS Snowpark session)
├── frontend/
│   └── streamlit/
│       ├── app.py                  # Operations Cockpit UI (Custom aerospace design)
│       └── environment.yml         # Anaconda package specifications for SiS
├── snowflake/
│   ├── ddl/                        # Table definitions, stages, and streams
│   ├── dynamic_tables/             # Sliding feature and recurrence dynamic tables
│   ├── cortex/                     # Cortex Search service setup & chunking
│   └── semantic/                   # Semantic views and metrics layer
├── data_generator/                 # Realistic telemetry & flight operations synthesis
├── scripts/
│   ├── deploy_streamlit_to_snowflake.py # Automated SiS bundle & deploy pipeline
│   └── run_pipeline.py             # Full end-to-end data pipeline runner
├── tests/
│   ├── agents/                     # Unit & integration tests for all agents
│   └── eval/                       # Benchmark eval suite (32 operational scenarios)
└── docs/                           # Architecture, security, decisions, and demo guides
```

---

## 🧪 Verification & Benchmarks

The platform has undergone rigorous evaluation against realistic commercial aviation failure modes (APU EGT exceedance, bleed air trip, hydraulic EDP pressure drop, avionics cooling fan stall, brake temp overheat):

* **Unit & Integration Suite**: `28/28 passed` (`pytest tests/ -v`)
* **Evaluation Benchmark Suite**: `32/32 passed (100% pass rate)` (`python tests/eval/run_agent_benchmarks.py`)
  - **False Alarm Rate**: `0.0%`
  - **Human Gate Compliance**: `100%` (Zero unauthorized work order dispatches)
  - **Root Cause Accuracy**: `100%` against ground truth AMM references
  - **Audit Logging**: Persisted directly in Snowflake table `AERORESOLVE.EVAL.BENCHMARK_RUN_RESULTS`.

See [docs/EVAL_RESULTS.md](docs/EVAL_RESULTS.md) for detailed metrics and breakdown.

---

## 🚀 Local Quickstart

### 1. Prerequisites
- Python 3.10+
- Snowflake Account with Cortex enabled

### 2. Setup Environment
```bash
git clone https://github.com/Devesh929/aeroresolve.git
cd aeroresolve

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt  # Or install dependencies from environment.yml
```

### 3. Launch Local Streamlit Cockpit
```bash
streamlit run frontend/streamlit/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📄 License & Compliance

Developed for **AeroBharat Airlines (ABR)**. Internal operational decision-support tool.  
All maintenance decisions require authorized human sign-off.