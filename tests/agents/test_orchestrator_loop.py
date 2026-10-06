"""
tests/agents/test_orchestrator_loop.py
End-to-End Test Suite for AeroResolve Specialist Agents and State Machine Orchestrator.
"""
import os
import pytest
import snowflake.connector

from backend.connection import get_snowflake_connection
from backend.agents.health_agent import HealthAgent
from backend.agents.repeat_defect_agent import RepeatDefectAgent
from backend.agents.root_cause_agent import RootCauseAgent
from backend.agents.ground_readiness_agent import GroundReadinessAgent
from backend.agents.ops_impact_agent import OperationsImpactAgent
from backend.orchestrator import AeroResolveOrchestrator

@pytest.fixture(scope="module")
def sf_conn():
    conn = get_snowflake_connection()
    yield conn
    conn.close()

def test_health_agent(sf_conn):
    agent = HealthAgent()
    res = agent.analyze_aircraft_health(sf_conn, aircraft_id="ABR-017", flight_id="FL-20261006-017-0060")
    assert res["status"] in ("ANOMALY_CONFIRMED", "HEALTHY")
    assert "sensor_telemetry" in res
    assert res["sensor_telemetry"]["sample_count"] > 0
    assert "fan_current" in res["sensor_telemetry"]

def test_repeat_defect_agent(sf_conn):
    agent = RepeatDefectAgent()
    res = agent.investigate_recurrence(sf_conn, aircraft_id="ABR-017", fault_code="FAULT-21-204")
    assert res["status"] == "REPEAT_DEFECT_FLAGGED"
    assert res["recurrence_metrics"]["occurrences_30d"] >= 2
    assert res["recurrence_metrics"]["is_repeat_defect"] is True

def test_root_cause_agent(sf_conn):
    agent = RootCauseAgent()
    res = agent.diagnose_root_cause(
        sf_conn, 
        aircraft_id="ABR-017", 
        flight_id="FL-20261006-017-0060",
        evidence_context={"symptom": "Cooling loop degradation"}
    )
    assert res["status"] == "ROOT_CAUSE_ISOLATED"
    assert res["confidence_score"] >= 0.85
    assert "PART-X42-CONN" in res["required_part"] or "X42" in res["primary_root_cause"]
    assert len(res["hypotheses_ranking"]) >= 2

def test_ground_readiness_agent(sf_conn):
    agent = GroundReadinessAgent()
    res = agent.evaluate_ground_readiness(sf_conn, dest_station="DEL", part_number="PART-X42-CONN")
    assert res["status"] == "LOGISTICS_REPOSITION_REQUIRED"
    assert res["station_readiness"]["spares"]["stockout"] is True
    assert res["reposition_plan"]["can_reposition"] is True
    assert res["reposition_plan"]["reposition_source_station"] is not None
    assert res["part_reserved_at_source"] is True

def test_ops_impact_agent(sf_conn):
    agent = OperationsImpactAgent()
    res = agent.evaluate_operational_impact(sf_conn, aircraft_id="ABR-017", estimated_downtime_mins=90)
    assert res["status"] == "IMPACT_QUANTIFIED"
    assert res["downstream_sectors_count"] > 0
    assert res["financial_exposure_inr"] > 0

def test_orchestrator_full_workflow(sf_conn):
    orchestrator = AeroResolveOrchestrator()
    
    # 1. Run automated investigation
    inv_res = orchestrator.run_investigation(
        conn=sf_conn,
        aircraft_id="ABR-017",
        flight_id="FL-20261006-017-0060",
        dest_station="DEL"
    )
    assert inv_res["status"] == "AWAITING_HUMAN_APPROVAL"
    case_id = inv_res["case_id"]
    assert case_id.startswith("CASE-017-")
    assert len(inv_res["audit_steps"]) == 5

    # 2. Simulate human approval decision
    approval_res = orchestrator.process_human_decision(
        conn=sf_conn,
        case_id=case_id,
        aircraft_id="ABR-017",
        decision="APPROVED",
        approver_name="MCC Chief Controller Devesh",
        approver_role="Director Maintenance Operations Control",
        controller_notes="Approved pre-staging of connector kit from BOM to DEL; dispatch ground team to Gate 32.",
        target_system="JIRA"
    )
    assert approval_res["workflow_completed"] is True
    assert approval_res["decision"] == "APPROVED"
    assert approval_res["mcp_dispatch"]["status"] == "DISPATCHED_SUCCESSFULLY"
    assert approval_res["mcp_dispatch"]["external_key"].startswith("AERO-")
    assert approval_res["post_repair_verification"]["status"] == "REPAIR_EFFECTIVE_VERIFIED"

    # 3. Verify audit trail integrity in Snowflake
    cur = sf_conn.cursor()
    cur.execute("SELECT status, repair_effective FROM AERORESOLVE.AUDIT.AGENT_CASE WHERE case_id = %s", (case_id,))
    case_row = cur.fetchone()
    assert case_row[0] == "VERIFIED_CLOSED"
    assert case_row[1] is True

    cur.execute("SELECT COUNT(*) FROM AERORESOLVE.AUDIT.AGENT_STEP WHERE case_id = %s", (case_id,))
    step_count = cur.fetchone()[0]
    assert step_count == 5

    cur.execute("SELECT decision FROM AERORESOLVE.AUDIT.HUMAN_APPROVAL WHERE case_id = %s", (case_id,))
    appr_row = cur.fetchone()
    assert appr_row[0] == "APPROVED"

    cur.execute("SELECT target_system, external_key FROM AERORESOLVE.AUDIT.EXTERNAL_ACTION WHERE case_id = %s", (case_id,))
    ext_row = cur.fetchone()
    assert ext_row[0] == "JIRA"
    assert ext_row[1].startswith("AERO-")

    cur.execute("SELECT verification_status, anomaly_recurred FROM AERORESOLVE.AUDIT.REPAIR_VERIFICATION WHERE case_id = %s", (case_id,))
    verif_row = cur.fetchone()
    assert verif_row[0] == "REPAIR_EFFECTIVE_VERIFIED"
    assert verif_row[1] is False
    cur.close()
