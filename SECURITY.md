# AeroResolve — Security Policy & Practices

## 1. Credential Handling & Zero-Secret Architecture

1. **Zero Secret Storage in Repository**:
   - No passwords, PATs, Jira API keys, GitHub tokens, or private certificates are ever committed to Git.
   - All `.env` files are strictly ignored via `.gitignore`.
   - `.env.example` is maintained with sanitized placeholder values only.
2. **Local Credential Storage**:
   - Snowflake connection credentials use OS-level local secure token storage (`~/.snowflake/token.jwt`) for user `DEVESH929`.
   - Python code dynamically retrieves credentials from environment variables or standard config paths without hardcoding.
3. **Audit Trail Redaction**:
   - Traceability tables in `AERORESOLVE.AUDIT` record user handles and roles but never record authorization secrets or sensitive token headers.

---

## 2. Role-Based Access Control (RBAC) Architecture

- **Dedicated Developer Role**: `AERORESOLVE_DEV`.
- **Principle of Least Privilege**:
  - `ACCOUNTADMIN` and `SECURITYADMIN` are strictly prohibited from day-to-day application workflows.
  - Role `AERORESOLVE_DEV` is granted ownership only on the `AERORESOLVE` database and its 11 schemas, and `USAGE` on warehouse `AERORESOLVE_WH`.
  - External network rules are restricted to allowed Snowflake endpoints and designated MCP connectors.

---

## 3. Simulation Truth vs. Observable Operational Data Separation

To prevent "data leakage" and ensure the AI models and specialist agents reason strictly on observable operational telemetry:
- **Private Evaluation Schema**: `AERORESOLVE.EVAL` (contains `SCENARIO_TRUTH` and `ROOT_CAUSE_TRUTH`).
- **Observable Operational Data**: `AERORESOLVE.CURATED` (contains `FACT_TELEMETRY`, `FACT_FAULT_EVENTS`, `FACT_MAINTENANCE_ACTIONS`).
- **Access Boundary**:
  - Agent tools (`telemetry_tools.py`, `recurrence_tools.py`, `knowledge_tools.py`, `readiness_tools.py`, `impact_tools.py`) **ONLY** query `AERORESOLVE.CURATED` and `AERORESOLVE.SEMANTIC`.
  - Agents have **ZERO ACCESS** to `AERORESOLVE.EVAL.SCENARIO_TRUTH`.
  - The evaluation harness alone queries `AERORESOLVE.EVAL` post-hoc to score predictions against ground truth.

---

## 4. Airworthiness & Regulatory Decision Boundary

> [!CAUTION]
> **Strict Non-Airworthiness Boundary**  
> AeroResolve is an engineering decision-support tool. It is **NEVER** authorized to autonomously make airworthiness, dispatch, Minimum Equipment List (MEL) deferral, return-to-service, or maintenance-release decisions. All maintenance actions and dispatch releases require certified, licensed human authority.

- **System Prompt Safety Directives**:
  All agent system instructions explicitly reinforce that the agent cannot issue maintenance releases or sign off aircraft airworthiness.
- **Human Approval Gate**:
  The orchestrator state machine halts at `AWAITING_HUMAN_APPROVAL`. External MCP work order creation (Jira / GitHub) is programmatically blocked until a licensed controller confirms the decision.

---

## 5. Network & Model Safety

- **Cortex Search Boundary**: Operates exclusively over the internal synthetic technical corpus in `AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS`. No external web crawling or untrusted internet queries are executed.
- **SQL Injection Prevention**: All Snowflake SQL queries in backend tools and agent routines utilize parameterized query bindings (`%s`), preventing arbitrary SQL injection attacks.
