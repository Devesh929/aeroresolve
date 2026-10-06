"""
backend/agents/repair_verification_agent.py
AeroResolve Repair Verification Specialist Agent.
Monitors subsequent flights post-maintenance to empirically verify defect eradication.
"""
from typing import Dict, Any
import snowflake.connector
from backend.tools.verification_tools import verify_post_repair_telemetry, record_verification_result

class RepairVerificationAgent:
    name = "RepairVerificationAgent"
    role = "Post-Repair Flight Telemetry & Verification Specialist"

    def verify_repair_effectiveness(
        self, 
        conn: snowflake.connector.SnowflakeConnection, 
        case_id: str, 
        aircraft_id: str
    ) -> Dict[str, Any]:
        """
        Monitors subsequent flights to verify signal stability and absence of recurring anomalies.
        """
        verif_data = verify_post_repair_telemetry(conn, aircraft_id=aircraft_id)

        # Record formal audit record in Snowflake
        verif_id = record_verification_result(
            conn=conn,
            case_id=case_id,
            aircraft_id=aircraft_id,
            verification_flight_id=verif_data["verification_flight_id"],
            stability_score=verif_data["signal_stability_score"],
            anomaly_recurred=verif_data["anomaly_recurred"],
            status=verif_data["verification_status"]
        )

        summary = (
            f"Repair verification for {aircraft_id} (Case {case_id}): "
            f"Monitored {verif_data['sectors_monitored']} post-maintenance flight sectors. "
            f"Signal stability score: {int(verif_data['signal_stability_score'] * 100)}%. "
            f"{verif_data['conclusion']} Audit Record: {verif_id}."
        )

        return {
            "agent": self.name,
            "verification_id": verif_id,
            "status": verif_data["verification_status"],
            "summary": summary,
            "signal_stability_score": verif_data["signal_stability_score"],
            "anomaly_recurred": verif_data["anomaly_recurred"],
            "telemetry_metrics": verif_data["telemetry_metrics"],
            "repair_effective": not verif_data["anomaly_recurred"]
        }
