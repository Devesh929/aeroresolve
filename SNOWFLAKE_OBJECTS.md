# AeroResolve — Snowflake Objects Inventory

## 1. Security & Compute Infrastructure
- **Role**: `AERORESOLVE_DEV` (Non-accountadmin developer role granted to `DEVESH929`)
- **Database**: `AERORESOLVE`
- **Warehouse**: `AERORESOLVE_WH` (Size: X-Small, auto-suspend: 60s, auto-resume: TRUE)
- **Cortex Cross-Region Inference**: Enabled (`ANY_REGION` configuration)

---

## 2. Schemas (11 Total)
1. `AERORESOLVE.RAW`: Staging and ingest stream tables.
2. `AERORESOLVE.CURATED`: Core star-schema dimensional and fact tables.
3. `AERORESOLVE.FEATURES`: Declarative feature stores and dynamic tables.
4. `AERORESOLVE.ML`: ML feature views, models, and anomaly detection functions.
5. `AERORESOLVE.KNOWLEDGE`: Technical manuals, service bulletins, and Cortex Search service.
6. `AERORESOLVE.SEMANTIC`: Curated semantic views and gold verified analytical views.
7. `AERORESOLVE.AGENTS`: Agent tool definitions, state machine logs, and prompt models.
8. `AERORESOLVE.OPS`: Operational cost assumptions, flight rotations, and network impacts.
9. `AERORESOLVE.APP`: Application cache and UI configuration metadata.
10. `AERORESOLVE.EVAL`: Private scenario ground truth, expected actions, tool sequences, and benchmark run results.
11. `AERORESOLVE.AUDIT`: Complete immutable audit trails, cases, steps, human approvals, MCP actions, and repair surveillance.

---

## 3. Curated Dimensional Tables (`AERORESOLVE.CURATED`)
- `DIM_AIRCRAFT`: Fleet tails, serial numbers, delivery dates, flight hours/cycles.
- `DIM_AIRCRAFT_TYPE`: Aircraft families, engine types, MTOW, passenger capacities.
- `DIM_COMPONENT_TYPE`: Component definitions, ATA chapters, MTBF, OEM part numbers.
- `DIM_COMPONENT_SERIAL`: Individual serial numbers, accumulated flight hours/cycles.
- `DIM_FAULT_CODE`: Fault codes, ATA chapters, criticality, MEL dispatch categories.
- `DIM_MAINTENANCE_ACTION`: Standard corrective action taxonomy (BITE reset, swap, harness repair).
- `DIM_STATION`: Hubs and spoke stations, coordinates, timezones, night curfew hours.
- `DIM_ROUTE`: Origin-destination pairs, scheduled block times, air distances.
- `DIM_ENGINEER`: Certified engineers, station assignments, ATA certification privileges.
- `DIM_TOOL`: Calibrated maintenance tools, calibration expiry dates, station allocations.
- `DIM_PART`: Consumable and rotable part numbers, lead times, replacement costs.
- `DIM_PASSENGER_SEGMENT`: Passenger classes, priority ratings, misconnection compensation limits.

---

## 4. Operational Fact Tables (`AERORESOLVE.CURATED`)
- `FACT_FLIGHTS`: Scheduled and executed flights, block times, origin/destination.
- `FACT_TELEMETRY`: Wide-column high-frequency sensor readings (42 sensor channels per row).
- `FACT_FAULT_EVENTS`: In-flight and ground ACARS-like fault codes, flight phases.
- `FACT_TECH_LOG`: Pilot and technician logbook defect write-ups and deferrals.
- `FACT_MAINTENANCE_ACTIONS`: Performed maintenance actions, replacement parts, stations.
- `FACT_COMPONENT_INSTALL_REMOVAL`: Component install/removal tracking, tail numbers.
- `FACT_WORK_ORDERS`: Scheduled and unscheduled maintenance work packages.
- `FACT_ACARS_MESSAGES`: In-flight downlink messages, raw and parsed text.
- `FACT_DELAY_EVENTS`: Delay durations, delay root causes, sub-allocations.
- `FACT_PART_INVENTORY`: Real-time stock levels, quantities on hand, reserved quantities.
- `FACT_PART_MOVEMENTS`: Inventory transfers, shipment orders, transit times.
- `FACT_ENGINEER_ROSTER`: Engineer duty rosters, shift schedules, station coverage.
- `FACT_STATION_CAPABILITY`: Station certification levels by ATA chapter.
- `FACT_TOOL_AVAILABILITY`: Calibrated tool set availability and reservation status.
- `FACT_AIRCRAFT_ROTATION`: Tail rotation flight chains, turnaround buffers.
- `FACT_PASSENGER_CONNECTIONS`: Inbound/outbound passenger connections, minimum connection times (MCT).
- `FACT_AGENT_ACTIONS`: Historical automated system events and trigger logs.

---

## 5. Raw Ingestion & Pipeline Objects
- `AERORESOLVE.RAW.STREAM_TELEMETRY_INGEST`: Variant landing table for live telemetry packets.
- `AERORESOLVE.RAW.STRM_RAW_TELEMETRY`: Standard table stream tracking new telemetry inserts.
- `AERORESOLVE.RAW.SP_PROCESS_STREAM_TELEMETRY()`: Stored procedure parsing JSON packets into curated tables.
- `AERORESOLVE.RAW.TSK_PROCESS_RAW_TELEMETRY`: 1-minute automated task processing the telemetry stream.

---

## 6. Dynamic Tables (`AERORESOLVE.FEATURES` & `OPS`)
- `AERORESOLVE.FEATURES.DT_AIRCRAFT_HEALTH_WINDOW`: Rolling 10-flight aggregate sensor metrics and z-scores.
- `AERORESOLVE.FEATURES.DT_FAULT_RECURRENCE_FEATURES`: 30-day regulatory repeat defect indicators and ineffective repair flags.
- `AERORESOLVE.OPS.DT_STATION_READINESS`: Live station inventory availability, certified engineers, and tool sets.

---

## 7. Machine Learning Objects (`AERORESOLVE.ML`)
- `AERORESOLVE.ML.V_ML_TELEMETRY_TRAINING`: Feature view standardizing multi-series sensor telemetry for training.
- `AERORESOLVE.ML.ML_AIRCRAFT_TELEMETRY_ANOMALY`: Multi-series anomaly detection model identifying multi-variate signal drift.

---

## 8. Unstructured Knowledge & Cortex Search (`AERORESOLVE.KNOWLEDGE`)
- `AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS`: 10 synthetic technical manuals, AMM, TSM, SIL, and SB documents.
- `AERORESOLVE.KNOWLEDGE.AERO_TECH_MANUALS_SEARCH`: Cortex Search Service indexing technical manuals by content, ATA chapter, and title.

---

## 9. Semantic Layer Views (`AERORESOLVE.SEMANTIC`)
- **Dimensional Semantic Views**:
  - `SEM_FLEET_AIRCRAFT`
  - `SEM_FLIGHT_OPERATIONS`
  - `SEM_FAULT_HISTORY`
  - `SEM_MAINTENANCE_ACTIONS`
  - `SEM_SPARE_PARTS_INVENTORY`
  - `SEM_STATION_CAPABILITY`
  - `SEM_AIRCRAFT_ROTATION`
- **Gold Verified Analytical Views (`V_VERIFIED_*`)**:
  - `V_VERIFIED_REPEAT_DEFECT_RATE_BY_FLEET`
  - `V_VERIFIED_ABR017_ATA21_HISTORY`
  - `V_VERIFIED_ACTIVE_INFLIGHT_DEGRADATION_SIGNATURES`
  - `V_VERIFIED_DEL_TONIGHT_MAINTENANCE_CAPABILITY`
  - `V_VERIFIED_PART_X42_STOCK_AND_TRANSIT`
  - `V_VERIFIED_ABR017_DOWNSTREAM_ROTATION_BLAST_RADIUS`
  - `V_VERIFIED_RECURRING_FAULTS_AFTER_UNVERIFIED_REPAIR`
- **Cortex Semantic Model**: `snowflake/semantic/aeroresolve_semantic_model.yaml`.

---

## 10. Audit, Traceability & Evaluation Tables (`AERORESOLVE.AUDIT` & `EVAL`)
- `AERORESOLVE.AUDIT.AGENT_CASE`: High-level investigation cases, status, confidence, AOG risk.
- `AERORESOLVE.AUDIT.AGENT_STEP`: Step-by-step audit records with JSON evidence for each agent.
- `AERORESOLVE.AUDIT.RECOMMENDATION`: Detailed maintenance recommendations, required parts, downstream sectors.
- `AERORESOLVE.AUDIT.HUMAN_APPROVAL`: Permanent record of controller authorizations, timestamps, and notes.
- `AERORESOLVE.AUDIT.EXTERNAL_ACTION`: Full MCP payloads and external reference URLs for Jira/GitHub tickets.
- `AERORESOLVE.AUDIT.REPAIR_SURVEILLANCE`: Post-repair flight monitoring records, stability scores, and verification status.
- `AERORESOLVE.EVAL.SCENARIO_TRUTH`: Ground-truth benchmark definitions for 8 core scenarios.
- `AERORESOLVE.EVAL.ROOT_CAUSE_TRUTH`: Physical root causes and false hypotheses for falsification testing.
- `AERORESOLVE.EVAL.EXPECTED_AGENT_ACTION`: Expected agent actions and minimum acceptable confidence thresholds.
- `AERORESOLVE.EVAL.EXPECTED_TOOL_SEQUENCE`: Expected deterministic tool invocation sequences.
- `AERORESOLVE.EVAL.BENCHMARK_RUN_RESULTS`: Immutable log of all 32 benchmark execution runs, pass/fail status, and latency.
