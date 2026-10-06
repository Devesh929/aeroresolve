"""
backend/agents/ops_impact_agent.py
AeroResolve Operations Impact Specialist Agent.
Predicts downstream network rotation blast radius, passenger misconnections, and financial downtime risk.
"""
from typing import Dict, Any
import snowflake.connector
from backend.tools.impact_tools import calculate_network_impact

class OperationsImpactAgent:
    name = "OperationsImpactAgent"
    role = "Network Operations & Financial Blast Radius Specialist"

    def evaluate_operational_impact(
        self, 
        conn: snowflake.connector.SnowflakeConnection, 
        aircraft_id: str, 
        estimated_downtime_mins: int = 90
    ) -> Dict[str, Any]:
        """
        Calculates downstream rotation vulnerability and financial exposure.
        """
        impact = calculate_network_impact(conn, aircraft_id=aircraft_id, estimated_downtime_mins=estimated_downtime_mins)

        summary = (
            f"Operations blast radius for {aircraft_id}: If unmitigated, grounding affects "
            f"{impact['downstream_sectors_at_risk']} downstream sectors, risking "
            f"{impact['total_passengers_impacted']} booked passengers and "
            f"{impact['total_connecting_passengers_at_risk']} high-value transfer connections. "
            f"Total financial exposure: INR {impact['financial_exposure']['total_risk_inr']:,} "
            f"(Delay: INR {impact['financial_exposure']['operational_delay_cost_inr']:,}, "
            f"Misconnection care: INR {impact['financial_exposure']['passenger_misconnection_care_inr']:,})."
        )

        return {
            "agent": self.name,
            "status": "IMPACT_QUANTIFIED",
            "summary": summary,
            "network_impact": impact,
            "connection_risk_level": impact["connection_risk_level"],
            "downstream_sectors_count": impact["downstream_sectors_at_risk"],
            "passengers_at_risk": impact["total_passengers_impacted"],
            "financial_exposure_inr": impact["financial_exposure"]["total_risk_inr"],
            "recommended_next_agent": "AeroResolveOrchestrator"
        }
