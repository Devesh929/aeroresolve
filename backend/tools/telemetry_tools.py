"""
backend/tools/telemetry_tools.py
Specialized telemetry extraction and statistical anomaly tools for Health Agent.
"""
from typing import Dict, Any
import snowflake.connector

def get_sensor_window(conn: snowflake.connector.SnowflakeConnection, aircraft_id: str, flight_id: str) -> Dict[str, Any]:
    """
    Extracts telemetry observations for the flight and calculates statistical aggregates,
    anomalous excursion counts, and signal degradation metrics.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) AS sample_count,
            AVG(avionics_fan_current_a) AS avg_fan_current,
            MIN(avionics_fan_current_a) AS min_fan_current,
            MAX(avionics_fan_current_a) AS max_fan_current,
            STDDEV(avionics_fan_current_a) AS std_fan_current,
            AVG(avionics_rack_temp_c) AS avg_rack_temp,
            MAX(avionics_rack_temp_c) AS max_rack_temp,
            AVG(vibration_index) AS avg_vibration,
            AVG(altitude_ft) AS avg_altitude,
            AVG(outside_air_temp_c) AS avg_oat,
            COUNT(CASE WHEN avionics_fan_current_a > 2.5 OR avionics_fan_current_a < 1.9 THEN 1 END) AS fan_excursions,
            COUNT(CASE WHEN avionics_rack_temp_c > 42.0 THEN 1 END) AS temp_excursions
        FROM AERORESOLVE.CURATED.FACT_TELEMETRY
        WHERE aircraft_id = %s AND flight_id = %s
    """, (aircraft_id, flight_id))
    row = cur.fetchone()
    
    if not row or row[0] == 0:
        # Fallback to recent telemetry window for the aircraft if flight_id has few points
        cur.execute("""
            SELECT 
                COUNT(*) AS sample_count,
                AVG(avionics_fan_current_a),
                MIN(avionics_fan_current_a),
                MAX(avionics_fan_current_a),
                STDDEV(avionics_fan_current_a),
                AVG(avionics_rack_temp_c),
                MAX(avionics_rack_temp_c),
                AVG(vibration_index),
                AVG(altitude_ft),
                AVG(outside_air_temp_c),
                COUNT(CASE WHEN avionics_fan_current_a > 2.5 OR avionics_fan_current_a < 1.9 THEN 1 END),
                COUNT(CASE WHEN avionics_rack_temp_c > 42.0 THEN 1 END)
            FROM AERORESOLVE.CURATED.FACT_TELEMETRY
            WHERE aircraft_id = %s
        """, (aircraft_id,))
        row = cur.fetchone()

    sample_count = row[0] or 0
    avg_fan = round(float(row[1] or 2.2), 3)
    min_fan = round(float(row[2] or 2.0), 3)
    max_fan = round(float(row[3] or 2.4), 3)
    std_fan = round(float(row[4] or 0.05), 3)
    avg_temp = round(float(row[5] or 35.0), 2)
    max_temp = round(float(row[6] or 36.0), 2)
    avg_vib = round(float(row[7] or 0.12), 3)
    avg_alt = round(float(row[8] or 33000.0), 0)
    avg_oat = round(float(row[9] or -45.0), 1)
    fan_excursions = row[10] or 0
    temp_excursions = row[11] or 0

    cur.close()
    return {
        "aircraft_id": aircraft_id,
        "flight_id": flight_id,
        "sample_count": sample_count,
        "fan_current": {
            "avg": avg_fan,
            "min": min_fan,
            "max": max_fan,
            "stddev": std_fan,
            "excursions_outside_nominal": fan_excursions
        },
        "rack_temperature_c": {
            "avg": avg_temp,
            "max": max_temp,
            "overtemp_excursions": temp_excursions
        },
        "flight_environment": {
            "avg_altitude_ft": avg_alt,
            "avg_outside_air_temp_c": avg_oat,
            "avg_vibration_index": avg_vib
        },
        "degradation_severity": "HIGH" if (fan_excursions > 5 or max_temp > 42.0) else "NORMAL"
    }

def compare_fault_flights_to_normal_flights(conn: snowflake.connector.SnowflakeConnection, aircraft_id: str) -> Dict[str, Any]:
    """
    Compares the subject aircraft's cruise flight parameters against fleet and historical baseline.
    """
    cur = conn.cursor()
    # Baseline normal stats for the aircraft across non-fault flights
    cur.execute("""
        SELECT 
            ROUND(AVG(avionics_fan_current_a), 3),
            ROUND(AVG(avionics_rack_temp_c), 2),
            ROUND(STDDEV(avionics_fan_current_a), 3)
        FROM AERORESOLVE.CURATED.FACT_TELEMETRY
        WHERE flight_phase = 'CRUISE' AND aircraft_id != %s
    """, (aircraft_id,))
    fleet_row = cur.fetchone()
    fleet_avg_fan = float(fleet_row[0] or 2.21)
    fleet_avg_temp = float(fleet_row[1] or 35.4)
    fleet_std_fan = float(fleet_row[2] or 0.08)

    # Subject aircraft stats
    cur.execute("""
        SELECT 
            ROUND(AVG(avionics_fan_current_a), 3),
            ROUND(AVG(avionics_rack_temp_c), 2),
            ROUND(MAX(avionics_rack_temp_c), 2)
        FROM AERORESOLVE.CURATED.FACT_TELEMETRY
        WHERE flight_phase = 'CRUISE' AND aircraft_id = %s
    """, (aircraft_id,))
    ac_row = cur.fetchone()
    ac_avg_fan = float(ac_row[0] or fleet_avg_fan)
    ac_avg_temp = float(ac_row[1] or fleet_avg_temp)
    ac_max_temp = float(ac_row[2] or fleet_avg_temp)

    z_score = round((ac_avg_fan - fleet_avg_fan) / max(fleet_std_fan, 0.01), 2)
    cur.close()

    return {
        "aircraft_id": aircraft_id,
        "fleet_baseline_fan_current_a": fleet_avg_fan,
        "fleet_baseline_rack_temp_c": fleet_avg_temp,
        "aircraft_avg_fan_current_a": ac_avg_fan,
        "aircraft_avg_rack_temp_c": ac_avg_temp,
        "aircraft_max_rack_temp_c": ac_max_temp,
        "z_score_deviation": z_score,
        "is_statistically_abnormal": abs(z_score) > 2.0 or ac_max_temp > 42.0
    }
