"""
backend/agents/ground_readiness_agent.py
AeroResolve Ground Readiness Specialist Agent.
Assesses destination station spares, technician certification, and tooling. Orchestrates expedited parts logistics.
"""
from typing import Dict, Any
import snowflake.connector
from backend.tools.readiness_tools import check_station_readiness, find_spare_reposition_source, reserve_demo_part

class GroundReadinessAgent:
    name = "GroundReadinessAgent"
    role = "Destination Maintenance & Logistics Readiness Specialist"

    def evaluate_ground_readiness(
        self, 
        conn: snowflake.connector.SnowflakeConnection, 
        dest_station: str, 
        part_number: str = "PART-X42-CONN"
    ) -> Dict[str, Any]:
        """
        Assesses station readiness. If part is out of stock, automatically locates
        repositioning candidate station and reserves spare part.
        """
        readiness = check_station_readiness(conn, station_code=dest_station, part_number=part_number)
        
        reposition_plan = None
        part_reserved = False

        if readiness["spares"]["stockout"]:
            reposition_plan = find_spare_reposition_source(conn, part_number=part_number, dest_station=dest_station)
            if reposition_plan["can_reposition"]:
                source_stn = reposition_plan["reposition_source_station"]
                part_reserved = reserve_demo_part(conn, part_number=part_number, station_code=source_stn)

        summary = (
            f"Destination readiness for {dest_station}: Station has {readiness['resources']['available_engineers_on_duty']} "
            f"licensed engineers on duty and active ATA certification. "
        )

        if readiness["spares"]["stockout"]:
            summary += (
                f"ALERT: {part_number} is OUT OF STOCK at {dest_station}. "
                f"Expedited logistics planned from {reposition_plan['reposition_source_station']} "
                f"(flight transit: {reposition_plan['scheduled_flight_time_mins']} mins, total est: {reposition_plan['total_estimated_reposition_hours']}h). "
                f"Candidate part unit reserved at {reposition_plan['reposition_source_station']}."
            )
        else:
            summary += f"Spares ready: {readiness['spares']['quantity_available']} units of {part_number} available."

        return {
            "agent": self.name,
            "status": "LOGISTICS_REPOSITION_REQUIRED" if readiness["spares"]["stockout"] else "STATION_FULLY_READY",
            "summary": summary,
            "station_readiness": readiness,
            "reposition_plan": reposition_plan,
            "part_reserved_at_source": part_reserved,
            "recommended_next_agent": "OperationsImpactAgent"
        }
