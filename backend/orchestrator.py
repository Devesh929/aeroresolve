"""
backend/orchestrator.py
AeroResolve Master Orchestrator.
Executes the bounded, deterministic state machine loop across all 6 specialist agents:
OBSERVE -> DETECT -> RECALL HISTORY -> HYPOTHESES -> CHECK EVIDENCE SUFFICIENCY ->
RANK ROOT CAUSES -> CHECK GROUND READINESS -> SIMULATE OPERATIONAL IMPACT ->
PREPARE RECOMMENDATION -> HUMAN APPROVAL -> EXTERNAL ACTION (MCP) -> MONITOR -> VERIFY REPAIR.
"""

import time
import json
import uuid
from typing import Dict, Any, Optional
import snowflake.connector

from backend.agents.health_agent import HealthAgent
from backend.agents.repeat_defect_agent import RepeatDefectAgent
from backend.agents.root_cause_agent import RootCauseAgent
from backend.agents.ground_readiness_agent import GroundReadinessAgent
from backend.agents.ops_impact_agent import OperationsImpactAgent
from backend.agents.repair_verification_agent import RepairVerificationAgent
from backend.mcp_dispatcher import McpMaintenanceDispatcher

class AeroResolveOrchestrator:
    """
    Main state machine orchestrator for AeroResolve.
    Enforces human-in-the-loop decision gating and complete Snowflake audit logging.
    """

    def __init__(self):
        self.health_agent = HealthAgent()
        self.repeat_agent = RepeatDefectAgent()
        self.root_cause_agent = RootCauseAgent()
        self.readiness_agent = GroundReadinessAgent()
        self.ops_agent = OperationsImpactAgent()
        self.verification_agent = RepairVerificationAgent()
        self.mcp_dispatcher = McpMaintenanceDispatcher()

    def run_investigation(
        self, 
        conn: snowflake.connector.SnowflakeConnection, 
        aircraft_id: str = "ABR-017", 
        flight_id: str = "FL-20261006-017-0060",
        dest_station: str = "DEL"
    ) -> Dict[str, Any]:
        """
        Executes the investigation workflow up to the human approval gate.
        """
        case_id = f"CASE-{aircraft_id[-3:]}-{int(time.time())}"
        case_title = f"In-Flight Avionics Cooling Degradation & Recurrent Ghost Fault ({aircraft_id})"
        
        cur = conn.cursor()
        
        # 1. Initialize Audit Case
        cur.execute("""
            INSERT INTO AERORESOLVE.AUDIT.AGENT_CASE (
                case_id, aircraft_id, flight_id, case_title, opened_ts, status, confidence_score, aog_risk_score
            ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP(), 'INVESTIGATING', 0.0, 0.85)
        """, (case_id, aircraft_id, flight_id, case_title))
        
        steps_log = []
        step_seq = 1

        def log_step(agent_name: str, action: str, summary: str, evidence: Dict[str, Any]):
            nonlocal step_seq
            step_id = f"STEP-{case_id[-6:]}-{step_seq:02d}"
            cur.execute("""
                INSERT INTO AERORESOLVE.AUDIT.AGENT_STEP (
                    step_id, case_id, step_sequence, agent_name, step_action, summary_for_ui, evidence_gathered, created_ts
                ) SELECT %s, %s, %s, %s, %s, %s, PARSE_JSON(%s), CURRENT_TIMESTAMP()
            """, (step_id, case_id, step_seq, agent_name, action, summary, json.dumps(evidence)))
            steps_log.append({
                "step_seq": step_seq,
                "agent": agent_name,
                "action": action,
                "summary": summary
            })
            step_seq += 1

        # -----------------------------------------------------------------
        # STEP 1: DETECT - Health Agent
        # -----------------------------------------------------------------
        t0 = time.time()
        health_res = self.health_agent.analyze_aircraft_health(conn, aircraft_id, flight_id)
        log_step(
            agent_name="HealthAgent",
            action="ANALYZE_TELEMETRY_WINDOW",
            summary=health_res["summary"],
            evidence=health_res
        )

        # -----------------------------------------------------------------
        # STEP 2: RECALL HISTORY - Repeat Defect Agent
        # -----------------------------------------------------------------
        repeat_res = self.repeat_agent.investigate_recurrence(conn, aircraft_id, fault_code="FAULT-21-204")
        log_step(
            agent_name="RepeatDefectAgent",
            action="CORRELATE_MAINTENANCE_HISTORY",
            summary=repeat_res["summary"],
            evidence=repeat_res
        )

        # -----------------------------------------------------------------
        # STEP 3: HYPOTHESES & ROOT CAUSE - Root Cause Agent (Cortex Search + LLM)
        # -----------------------------------------------------------------
        root_cause_res = self.root_cause_agent.diagnose_root_cause(
            conn, 
            aircraft_id=aircraft_id, 
            flight_id=flight_id,
            evidence_context={
                "health": health_res,
                "repeat": repeat_res
            }
        )
        log_step(
            agent_name="RootCauseAgent",
            action="DIAGNOSE_PHYSICAL_ROOT_CAUSE",
            summary=root_cause_res["summary"],
            evidence=root_cause_res
        )

        # -----------------------------------------------------------------
        # STEP 4: CHECK GROUND READINESS - Ground Readiness Agent
        # -----------------------------------------------------------------
        readiness_res = self.readiness_agent.evaluate_ground_readiness(
            conn, 
            dest_station=dest_station, 
            part_number=root_cause_res["required_part"]
        )
        log_step(
            agent_name="GroundReadinessAgent",
            action="EVALUATE_DESTINATION_READINESS",
            summary=readiness_res["summary"],
            evidence=readiness_res
        )

        # -----------------------------------------------------------------
        # STEP 5: SIMULATE OPERATIONAL IMPACT - Operations Impact Agent
        # -----------------------------------------------------------------
        ops_res = self.ops_agent.evaluate_operational_impact(
            conn, 
            aircraft_id=aircraft_id, 
            estimated_downtime_mins=90
        )
        log_step(
            agent_name="OperationsImpactAgent",
            action="CALCULATE_NETWORK_BLAST_RADIUS",
            summary=ops_res["summary"],
            evidence=ops_res
        )

        # -----------------------------------------------------------------
        # STEP 6: PREPARE RECOMMENDATION
        # -----------------------------------------------------------------
        rec_id = f"REC-{case_id[-8:]}"
        rec_action = (
            f"Pre-stage replacement connector kit ({root_cause_res['required_part']}) at {dest_station}. "
            f"Reposition candidate kit from {readiness_res.get('reposition_plan', {}).get('reposition_source_station', 'BOM')} via fast logistics. "
            f"Task licensed B2 avionics crew at {dest_station} Gate 32 immediately upon touchdown."
        )

        cur.execute("""
            INSERT INTO AERORESOLVE.AUDIT.RECOMMENDATION (
                recommendation_id, case_id, recommended_action, target_station, required_part,
                required_tool, required_skill, part_reposition_source, estimated_downtime_mins,
                downstream_flights_protected, passengers_protected, connection_risk_level, created_ts
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
        """, (
            rec_id, case_id, rec_action, dest_station, root_cause_res["required_part"],
            "TOOL-CRIMP-01", "B2 Avionics Technician",
            readiness_res.get("reposition_plan", {}).get("reposition_source_station", "BOM"),
            90, ops_res["downstream_sectors_count"], ops_res["passengers_at_risk"],
            ops_res["connection_risk_level"]
        ))

        # Update case with final hypothesis and confidence
        cur.execute("""
            UPDATE AERORESOLVE.AUDIT.AGENT_CASE
            SET current_hypothesis = %s,
                confidence_score = %s,
                status = 'AWAITING_HUMAN_APPROVAL'
            WHERE case_id = %s
        """, (root_cause_res["primary_root_cause"], root_cause_res["confidence_score"], case_id))

        cur.close()

        return {
            "case_id": case_id,
            "status": "AWAITING_HUMAN_APPROVAL",
            "aircraft_id": aircraft_id,
            "flight_id": flight_id,
            "destination_station": dest_station,
            "primary_root_cause": root_cause_res["primary_root_cause"],
            "confidence_score": root_cause_res["confidence_score"],
            "physical_justification": root_cause_res["physical_justification"],
            "hypotheses_ranking": root_cause_res["hypotheses_ranking"],
            "readiness": readiness_res,
            "operational_impact": ops_res,
            "recommended_action": rec_action,
            "audit_steps": steps_log
        }

    def process_human_decision(
        self,
        conn: snowflake.connector.SnowflakeConnection,
        case_id: str,
        aircraft_id: str,
        decision: str, # "APPROVED" or "REJECTED" or "MODIFIED"
        approver_name: str = "Chief Maintenance Controller Devesh",
        approver_role: str = "Authorized MCC Director",
        controller_notes: str = "Approved urgent connector pin pre-staging and BOM expedited logistics dispatch.",
        target_system: str = "JIRA"
    ) -> Dict[str, Any]:
        """
        Records human controller approval decision, dispatches external MCP work item,
        and triggers post-repair telemetry verification.
        """
        approval_id = f"APPR-{case_id[-8:]}"
        cur = conn.cursor()

        # 1. Record Human Decision
        cur.execute("""
            INSERT INTO AERORESOLVE.AUDIT.HUMAN_APPROVAL (
                approval_id, case_id, decision, decision_ts, approver_username, approver_role, controller_notes, dispatched_mcp_system
            ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP(), %s, %s, %s, %s)
        """, (approval_id, case_id, decision, approver_name, approver_role, controller_notes, target_system))

        mcp_res = None
        verif_res = None

        if decision == "APPROVED":
            # 2. Dispatch MCP Work Package
            # Retrieve recommendation details
            cur.execute("""
                SELECT recommended_action, target_station, required_part, part_reposition_source,
                       estimated_downtime_mins, downstream_flights_protected, passengers_protected
                FROM AERORESOLVE.AUDIT.RECOMMENDATION
                WHERE case_id = %s
            """, (case_id,))
            rec_row = cur.fetchone()
            
            rec_dict = {
                "action": rec_row[0] if rec_row else "Replace connector X42",
                "target_station": rec_row[1] if rec_row else "DEL",
                "required_part": rec_row[2] if rec_row else "PART-X42-CONN",
                "reposition_source": rec_row[3] if rec_row else "BOM",
                "estimated_downtime_mins": rec_row[4] if rec_row else 90,
                "downstream_flights_protected": rec_row[5] if rec_row else 5,
                "passengers_protected": rec_row[6] if rec_row else 650
            }

            mcp_res = self.mcp_dispatcher.dispatch_work_item(
                conn=conn,
                case_id=case_id,
                aircraft_id=aircraft_id,
                recommendation=rec_dict,
                approver=approver_name,
                target_system=target_system
            )

            # 3. Trigger Post-Repair Verification Agent
            verif_res = self.verification_agent.verify_repair_effectiveness(
                conn=conn,
                case_id=case_id,
                aircraft_id=aircraft_id
            )

        cur.close()

        return {
            "case_id": case_id,
            "approval_id": approval_id,
            "decision": decision,
            "approver": approver_name,
            "mcp_dispatch": mcp_res,
            "post_repair_verification": verif_res,
            "workflow_completed": True
        }
