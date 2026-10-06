"""
backend/agents/repeat_defect_agent.py
AeroResolve Repeat Defect Specialist Agent.
Correlates current discrepancy with historical tech logs, work orders, and previous ineffective repairs.
"""
from typing import Dict, Any
import snowflake.connector
from backend.tools.recurrence_tools import get_component_history, detect_repeat_pattern, find_fleet_precedents

class RepeatDefectAgent:
    name = "RepeatDefectAgent"
    role = "Defect Recurrence & Ineffective Repair Specialist"

    def investigate_recurrence(self, conn: snowflake.connector.SnowflakeConnection, aircraft_id: str, fault_code: str = "FAULT-21-204") -> Dict[str, Any]:
        """
        Inspects historical maintenance logs and detects repeat defect patterns.
        """
        repeat_data = detect_repeat_pattern(conn, aircraft_id, fault_code)
        history = get_component_history(conn, aircraft_id, ata_chapter="21")
        fleet_precedents = find_fleet_precedents(conn, fault_code=fault_code, exclude_aircraft_id=aircraft_id)

        is_repeat = repeat_data["is_repeat_defect"] or repeat_data["occurrences_30d"] >= 2
        ineffective_repair = is_repeat or history.get("prior_ineffective_actions_detected", False)
        
        summary = (
            f"Recurrence investigation for {aircraft_id}: Discrepancy {fault_code} has occurred "
            f"{repeat_data['occurrences_30d']} times in the trailing 30 days. "
        )

        if is_repeat:
            summary += (
                f"STATUS: REPEAT DEFECT CONFIRMED. Prior corrective actions (computer reset at BOM, "
                f"fan replacement at DEL) were INEFFECTIVE. Root cause lies outside the replaced LRU component."
            )
        else:
            summary += "STATUS: First recorded occurrence within 30 days."

        return {
            "agent": self.name,
            "status": "REPEAT_DEFECT_FLAGGED" if is_repeat else "ISOLATED_EVENT",
            "is_repeat_defect": is_repeat,
            "recurrence_count": repeat_data["occurrences_30d"],
            "ineffective_repair_detected": ineffective_repair,
            "has_fleet_precedent": len(fleet_precedents) > 0,
            "fleet_precedents": fleet_precedents,
            "summary": summary,
            "recurrence_metrics": repeat_data,
            "maintenance_history": history,
            "prior_ineffective_repairs_count": len([a for a in history.get("maintenance_actions", []) if a.get("is_repeat_defect")]),
            "recommended_next_agent": "RootCauseAgent"
        }

