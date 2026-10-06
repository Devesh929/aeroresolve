# AeroResolve — Test Plan & Quality Assurance

## 1. Test Architecture & Coverage Matrix

AeroResolve utilizes an end-to-end multi-tier test framework spanning unit physics, Snowflake data integrity, Cortex Search recall, semantic Gold queries, multi-agent workflow state machines, and a 32-scenario agent benchmark suite.

| Test Suite | File Path | Focus Area | Status | Count |
| :--- | :--- | :--- | :---: | :---: |
| **Data Generator Unit Tests** | `tests/unit/test_generator.py` | Deterministic seeds, profile configurations, scenario injections, causal aerodynamic physics | **PASSED** | 4 |
| **Data Integrity & FK Tests** | `tests/data_quality/test_integrity.py` | Primary keys, foreign key references, zero orphan flights, non-negative inventory, telemetry schema | **PASSED** | 5 |
| **Cortex Search Tests** | `tests/data_quality/test_cortex_search.py` | Technical corpus loading, Cortex Search service status, search relevance for connector micro-fretting | **PASSED** | 2 |
| **Semantic Gold Views** | `tests/data_quality/test_semantic_queries.py` | Semantic view definitions, all 7 Gold Verified Analytical Queries (`V_VERIFIED_*`) | **PASSED** | 8 |
| **Specialist Agents & Loop** | `tests/agents/test_orchestrator_loop.py` | 6 Specialist agents, state transitions, human decision gating, MCP work order dispatch, post-repair verification | **PASSED** | 6 |
| **Benchmark Suite (Pytest)** | `tests/eval/test_benchmarks.py` | Integration test validating 100% pass rate across the 32-scenario benchmark evaluation harness | **PASSED** | 1 |
| **Total Pytest Suite** | `pytest tests/ -v` | Comprehensive automated project verification | **PASSED** | **26 / 26** |

---

## 2. Dedicated Benchmark Evaluation Harness (`tests/eval/run_agent_benchmarks.py`)

AeroResolve includes a dedicated benchmark evaluation harness executing **32 structured scenarios** against Snowflake `AERORESOLVE.EVAL.SCENARIO_TRUTH`, `ROOT_CAUSE_TRUTH`, and fleet baselines:

1. **Suite 1: Core Scenario Truth Benchmarks (8 Scenarios)**
   - `SCEN-01-GHOST-FAULT`: In-flight vibration envelope correlation and rank 1 connector pin root cause isolation.
   - `SCEN-02-REPEAT-DEFECT`: 30-day recurrence detection and ineffective component swap identification.
   - `SCEN-03-SILENT-DEGRADATION`: Subtle sensor trendline creep detection prior to static limit breaches.
   - `SCEN-04-DESTINATION-NOT-READY`: Destination station stockout identification and expedited donor repositioning.
   - `SCEN-05-NETWORK-BLAST-RADIUS`: Downstream sector rotation delay, passenger misconnection, and financial risk quantification.
   - `SCEN-06-REPAIR-VERIFICATION`: Post-repair flight telemetry surveillance and baseline signal normalization confirmation.
   - `SCEN-07-FLEET-LEARNING`: Sister aircraft precedent memory retrieval preventing redundant component swaps.
   - `SCEN-08-HEALTHY-CONTROL`: Benign atmospheric turbulence evaluation without false alarm.

2. **Suite 2: Fleet-Wide Healthy Control Tests (10 Aircraft)**
   - Surveillance across sister aircraft `ABR-003`, `ABR-004`, `ABR-005`, `ABR-006`, `ABR-007`, `ABR-008`, `ABR-010`, `ABR-011`, `ABR-012`, and `ABR-009`.
   - Verifies **Zero False Alarms (FPR = 0.0%)** across nominal operations.

3. **Suite 3: Tool Sequence & Bounded State Machine Guards (8 Tests)**
   - Enforces deterministic sequence order: `HEALTH_AGENT` -> `REPEAT_DEFECT_AGENT` -> `ROOT_CAUSE_AGENT` -> `GROUND_READINESS_AGENT` -> `OPERATIONS_IMPACT_AGENT`.
   - Validates state machine guards preventing illegal state transitions.

4. **Suite 4: Human Safety Gate Compliance (6 Tests)**
   - `SCEN-GATE-01`: Autonomous Action Prohibition (State halts strictly at `AWAITING_HUMAN_APPROVAL`).
   - `SCEN-GATE-02`: Controller Rejection Halts External Dispatch (Zero MCP payloads issued).
   - `SCEN-GATE-03`: Authorized Human Approval Triggers External Work Order Package (Jira dispatch).
   - `SCEN-GATE-04`: Multi-System Dispatch Flexibility (GitHub Work Order).
   - `SCEN-GATE-05`: Permanent Audit Trail Persistence in `AERORESOLVE.AUDIT.HUMAN_APPROVAL`.
   - `SCEN-GATE-06`: Non-Airworthiness Regulatory Disclaimer Adherence.

---

## 3. Evaluation Benchmark Results

- **Total Scenarios Evaluated**: 32
- **Scenarios Passed**: 32 (**100.0% Pass Rate**)
- **Precision**: **100.0%**
- **Recall**: **100.0%**
- **F1-Score**: **1.000**
- **False Positive Rate (FPR)**: **0.0%**
- **Root-Cause Isolation Accuracy**: **100.0%**
- **Human Gate Compliance**: **100.0%**
- **Average Test Latency**: **1.12 seconds**
- **Persistence**: All 32 run results permanently recorded in `AERORESOLVE.EVAL.BENCHMARK_RUN_RESULTS`.
- **Benchmark Report**: Full markdown documentation in `docs/EVAL_RESULTS.md`.

---

## 4. Test Execution Instructions

To execute the test matrix:

```powershell
# Run the complete pytest suite
pytest tests/ -v

# Run the standalone benchmark evaluation runner
python tests/eval/run_agent_benchmarks.py
```
