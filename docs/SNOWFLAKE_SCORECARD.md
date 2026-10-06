# AeroResolve — Snowflake Feature Scorecard

Every Snowflake feature utilized in AeroResolve is tracked here along with its specific operational rationale.

| Snowflake Feature | Status | Architectural Rationale in AeroResolve |
| :--- | :---: | :--- |
| **Snowflake Core Tables** | [x] | Stores 12 dimensional and 17 operational fact entities partitioned by aircraft and time (42 tables deployed across 11 schemas). |
| **Stages / Data Loading** | [x] | Loads partitioned columnar batches representing fleet telemetry and operational records with full referential integrity. |
| **Snowpipe Streaming** | [ ] | Replays live flight observations in accelerated time (fallback: micro-batch ingest). |
| **Dynamic Tables** | [x] | Declaratively computes rolling health metrics, repeat defect scores, and station readiness. |
| **Streams** | [x] | Captures newly flagged high-risk degradation anomalies or in-flight fault events. |
| **Tasks** | [x] | Triggers investigation workflows upon new fault stream events. |
| **Snowflake ML Anomaly Detection** | [ ] | Multi-series anomaly detection on avionics fan current, vibration index, and rack temperature. |
| **Snowflake ML Classification** | [ ] | Evaluates probability of downstream Aircraft-on-Ground (AOG) delay. |
| **Semantic Views** | [ ] | Business ontology connecting Aircraft -> Flight -> Telemetry -> Fault -> Components -> Spares. |
| **Verified Queries** | [ ] | Deterministic gold queries guaranteeing precision for executive fleet health inquiries. |
| **Cortex Search** | [ ] | Hybrid semantic/keyword search over synthetic troubleshooting manuals & engineering advisories. |
| **Cortex Agent (Orchestrator)** | [ ] | Central reasoning engine directing the multi-step investigation loop. |
| **Specialist Agents / Toolsets** | [ ] | Dedicated agents for Health, Repeat Defects, Root Cause, Ground Readiness, Ops Impact, and Verification. |
| **Agent Skills** | [ ] | Standard operating procedures for flight envelope comparison, blast radius calculation, and case closure. |
| **Custom Tools (UDFs/Procs)** | [ ] | Custom domain procedures for station part reservation, envelope comparison, and audit logging. |
| **Code Execution** | [ ] | Secure analytical computation for scenario simulations and blast radius matrices. |
| **Data-to-Chart** | [ ] | Visual signal comparisons and flight timeline chart generation for human controllers. |
| **Agent Evaluations** | [ ] | Systematic 30-50 question evaluation benchmark measuring tool selection and correctness. |
| **Agent Observability** | [ ] | End-to-end tracing in `AUDIT.AGENT_STEP` and `AUDIT.TOOL_CALL`. |
| **Data Lineage** | [ ] | Explicit traceability from raw telemetry to semantic view to agent recommendation to Jira ticket. |
| **MCP Connector** | [ ] | Model Context Protocol integration with Atlassian Jira / GitHub for human-approved work orders. |
| **Streamlit in Snowflake** | [ ] | Operational command center UI for operations controllers and maintenance engineers. |
| **SPCS React Deployment** | [ ] | High-density dark-mode React operations cockpit if SPCS is enabled. |
| **CoCo CLI Throughout** | [x] | Cortex Code CLI (`cortex` v1.1.104) installed and utilized for development and object generation. |
