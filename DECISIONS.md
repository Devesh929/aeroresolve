# AeroResolve — Architectural Decision Records (ADRs)

## ADR-001: Synthetic Data Boundary & Zero-Real-World Claim
- **Context**: The project operates in commercial aviation engineering decision support.
- **Decision**: All tail numbers (`ABR-xxx`), airlines (*AeroBharat Airlines*), routes, telemetry parameters, maintenance logs, and scenarios are strictly synthetic. No claim shall be made linking any synthetic failure scenario to real-world airline operations or incidents.
- **Status**: Accepted & Enforced.

## ADR-002: Airworthiness & Human-in-the-Loop Authority
- **Context**: Autonomous AI systems cannot legally make airworthiness or dispatch decisions in aviation.
- **Decision**: AeroResolve provides decision support only. All maintenance preparations, parts movements, and work orders require human review and authorization. AeroResolve explicitly refuses to sign airworthiness or dispatch releases.
- **Status**: Accepted & Enforced.

## ADR-003: Wide Telemetry Table Design vs Narrow EAV
- **Context**: High-frequency telemetry (every 5 seconds across 150+ aircraft over months) generates hundreds of millions of data points. Storing one row per sensor channel would create 5+ billion rows and huge metadata overhead in Snowflake.
- **Decision**: Store telemetry as wide timestamped records (42+ sensor columns per row). Metrics in the UI will report both `TELEMETRY ROWS` and `TOTAL SENSOR OBSERVATIONS REPRESENTED`.
- **Status**: Accepted.

## ADR-004: Native Snowflake Capabilities as First-Class Citizens
- **Context**: Choosing between external Python orchestration vs native Snowflake features.
- **Decision**: Utilize Dynamic Tables for continuous declarative ELT, Snowflake ML Anomaly Detection for signal monitoring, Cortex Search for maintenance documentation, Semantic Views for structured natural language analytics, and Cortex Agents for multi-step reasoning. Local Python is limited to synthetic generation, simulation replay, and client tooling.
- **Status**: Accepted.

## ADR-005: Dual Evidence Guardrail for High-Confidence Root Cause
- **Context**: Intermittent "ghost faults" often lead to premature component swaps ("reset computer", "replace computer") when the root issue is wiring/connector degradation.
- **Decision**: AeroResolve's investigation loop must require >= 2 independent evidence types (e.g. telemetry environmental correlation + tech log failure history, or Cortex Search manual troubleshooting guidance) before assigning >80% confidence to a physical root-cause recommendation.
- **Status**: Accepted.

## ADR-006: Dedicated Role `AERORESOLVE_DEV` & Principle of Least Privilege
- **Context**: Running applications as `ACCOUNTADMIN` violates security best practices and exposes the entire Snowflake account.
- **Decision**: Created dedicated role `AERORESOLVE_DEV` with specific schema privileges across `AERORESOLVE.*` and warehouse `AERORESOLVE_WH`. Developer user `DEVESH929` uses this role for all operations.
- **Status**: Accepted & Enforced.

## ADR-007: Cortex LLM Model Selection: `llama3.1-8b` for Low-Latency Agent Reasoning
- **Context**: Cross-region inference for `llama3.1-70b` took 12–15 seconds per call, causing agent workflow latency > 30 seconds.
- **Decision**: Adopt `llama3.1-8b` as the default reasoning LLM for real-time agent diagnosis. `llama3.1-8b` achieves 1.09s latency with 100% adherence to JSON schemas and identical physical root cause accuracy.
- **Status**: Accepted.

## ADR-008: Snowflake SQL Variant Insert Pattern using `SELECT ..., PARSE_JSON(...)`
- **Context**: Snowflake SQL raises compilation errors when `PARSE_JSON(...)` is used inside `INSERT INTO ... VALUES (...)` clauses.
- **Decision**: Standardize all JSON audit and telemetry inserts to use `INSERT INTO ... SELECT %s, ..., PARSE_JSON(%s), CURRENT_TIMESTAMP()`.
- **Status**: Accepted.

## ADR-009: Strict Human Decision Gate Before External Action (Zero Autonomous MCP Dispatch)
- **Context**: Automated creation of maintenance work packages without human approval could cause unnecessary physical component requisitions and logistics movements.
- **Decision**: The state machine strictly halts at `AWAITING_HUMAN_APPROVAL`. MCP dispatchers (Jira/GitHub) are triggered ONLY when a licensed controller registers an explicit `APPROVED` decision in `AERORESOLVE.AUDIT.HUMAN_APPROVAL`.
- **Status**: Accepted & Enforced.

## ADR-010: Idempotent Inventory Reservation and Release Cycle
- **Context**: Repeated automated test runs decrement inventory at primary hubs, which could shift the optimal donor station over time.
- **Decision**: All automated benchmark evaluation harnesses idempotently reset inventory reservations (`quantity_reserved = 0`) before evaluation runs, ensuring deterministic test execution.
- **Status**: Accepted.

## ADR-011: Standardized Model Context Protocol (MCP) Work Package Format
- **Context**: Integration with enterprise work tracking systems requires structured, auditable payloads.
- **Decision**: Adopt standardized MCP maintenance payload format containing tail number, station, part number, donor reposition source, downtime estimate, protected passenger count, and approver signature, persisting full payloads to `AERORESOLVE.AUDIT.EXTERNAL_ACTION`.
- **Status**: Accepted.
