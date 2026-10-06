# AeroResolve — Snowflake Cost & Credit Optimization Notes

## 1. Warehouse Sizing & Auto-Suspend Strategy

| Object | Size | Credits / Hour | Auto-Suspend | Auto-Resume | Target Workload |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `AERORESOLVE_WH` | **X-Small** | 1 credit / hr | **60 seconds** | **TRUE** | Interactive queries, Dynamic Tables, ML models, Cortex Search Service, Agent tools |

- **Aggressive Auto-Suspend**: Configured to 60 seconds of inactivity to minimize idle compute burn.
- **Single Warehouse Simplicity**: Both queries, Cortex search indexing, and dynamic tables share `AERORESOLVE_WH` during development, eliminating multi-warehouse overhead.

---

## 2. Token Economics & LLM Inference Costs

AeroResolve benchmarks revealed key cost and latency differences between Cortex LLM models:

| Component | Model / Engine | Prompt Tokens | Completion Tokens | Latency | Cost per Investigation |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Telemetry Anomaly** | Snowflake ML (Multi-series) | N/A | N/A | 0.85s | Negligible |
| **Technical Manual Retrieval** | Cortex Search Service | ~150 | ~1,200 | 0.42s | Negligible |
| **Root Cause Reasoning** | `llama3.1-8b` (Cortex Complete) | ~1,850 | ~420 | **1.09s** | **~\$0.0004** |
| **Readiness & Network Query** | Snowflake Semantic SQL | N/A | N/A | 0.35s | Standard warehouse |
| **Total End-to-End** | Multi-Agent Pipeline | **~2,000** | **~420** | **~2.8s** | **< \$0.001** |

> [!TIP]
> **Model Selection Decision (ADR-007)**:  
> Testing showed that `llama3.1-70b` required 12–15 seconds per call due to cross-region routing, whereas `llama3.1-8b` completes in 1.09s with identical structured JSON adherence and physical root-cause accuracy, reducing LLM token cost by **~85%**.

---

## 3. Storage & Schema Optimization (Wide vs. Narrow)

- **Wide Telemetry Structure**: Telemetry is stored as wide rows with 42+ sensor columns rather than narrow Entity-Attribute-Value (EAV).
  - *Narrow EAV Approach*: 7,200 rows × 42 sensors = 302,400 rows (at Large profile: 50M rows × 80 sensors = 4 Billion rows).
  - *Wide Row Approach*: 7,200 rows storing all 42 channels simultaneously.
  - *Savings*: Eliminates 40x row metadata overhead, micro-partition bloat, and compression degradation in Snowflake.

---

## 4. Profile Scaling Guidelines

- **SMALL** (Active): 12 aircraft, 800 flights, 7,200 wide telemetry rows (302,400 sensor observations). Total credit consumption for full run: **< 0.15 credits**.
- **DEMO**: 20 aircraft, 30 days, ~50,000 wide telemetry rows. Fast rebuild in < 3 minutes.
- **LARGE**: 150–200 aircraft, 12 months, ~50 Million wide telemetry rows (4 Billion sensor observations). Target for final production stress testing with dedicated warehouse sizing.
- **XL**: Optional extreme stress testing mode; only run with explicit administrative approval.

---

## 5. Practical Cost Impact Summary

- **Cost per Investigation Case**: **< \$0.001** in compute and LLM tokens.
- **Value Generated**: Preventing a single 115-minute international departure delay (`DEL-DXB`) saves an estimated **₹14.8 Lakhs (~ \$17,800 USD)** in direct delay compensation, passenger rebooking, and hotel accommodation.
- **ROI**: Demonstrates over **10,000x cost-to-value ratio** in commercial airline operations.
