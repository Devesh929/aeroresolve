"""
backend/agents/health_agent.py
AeroResolve Health Specialist Agent.
Analyzes in-flight sensor streams, detects subtle parameter drift, and quantifies degradation severity.
"""
from typing import Dict, Any
import snowflake.connector
from backend.tools.telemetry_tools import get_sensor_window, compare_fault_flights_to_normal_flights

class HealthAgent:
    name = "HealthAgent"
    role = "Digital Fleet Health & Telemetry Specialist"

    def analyze_aircraft_health(self, conn: snowflake.connector.SnowflakeConnection, aircraft_id: str, flight_id: str) -> Dict[str, Any]:
        """
        Gathers sensor window, statistical deviation, and fleet baseline comparison.
        """
        sensor_window = get_sensor_window(conn, aircraft_id, flight_id)
        comparison = compare_fault_flights_to_normal_flights(conn, aircraft_id)

        findings = []
        if sensor_window["fan_current"]["excursions_outside_nominal"] > 0:
            findings.append(f"Detected {sensor_window['fan_current']['excursions_outside_nominal']} fan current excursions outside nominal 2.1-2.4A range.")
        if sensor_window["rack_temperature_c"]["max"] > 40.0:
            findings.append(f"Avionics rack temperature peaked at {sensor_window['rack_temperature_c']['max']}°C (threshold 42°C).")
        if comparison["z_score_deviation"] > 2.0:
            findings.append(f"Avionics fan current deviates +{comparison['z_score_deviation']}σ from fleet baseline.")

        summary = (
            f"Health assessment for {aircraft_id} on flight {flight_id}: "
            f"Sensor metrics indicate active thermal and current drift at altitude. "
            f"{' '.join(findings)}"
        )

        return {
            "agent": self.name,
            "status": "ANOMALY_CONFIRMED" if findings else "HEALTHY",
            "summary": summary,
            "sensor_telemetry": sensor_window,
            "baseline_comparison": comparison,
            "recommended_next_agent": "RepeatDefectAgent"
        }
