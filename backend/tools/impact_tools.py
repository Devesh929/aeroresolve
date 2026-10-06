"""
backend/tools/impact_tools.py
Specialized tools for Operations Impact Agent to calculate downstream flight rotations,
passenger connection blast radius, and financial downtime risk.
"""
from typing import Dict, Any, List
import snowflake.connector

def calculate_network_impact(
    conn: snowflake.connector.SnowflakeConnection, 
    aircraft_id: str, 
    estimated_downtime_mins: int = 90
) -> Dict[str, Any]:
    """
    Evaluates the operational blast radius if the aircraft is grounded for unscheduled repair.
    Computes downstream flights affected, booked passenger impact, connecting passenger misconnections,
    and direct financial cost exposure.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            ar.sequence_order,
            f.flight_id,
            f.flight_number,
            f.origin_station,
            f.dest_station,
            f.scheduled_departure_ts,
            f.scheduled_arrival_ts,
            ar.turnaround_buffer_mins,
            f.passenger_count,
            f.connecting_passenger_count
        FROM AERORESOLVE.CURATED.FACT_AIRCRAFT_ROTATION ar
        JOIN AERORESOLVE.CURATED.FACT_FLIGHTS f ON ar.flight_id = f.flight_id
        WHERE f.aircraft_id = %s 
          AND f.scheduled_departure_ts >= CURRENT_TIMESTAMP()
        ORDER BY ar.sequence_order ASC
        LIMIT 6
    """, (aircraft_id,))
    rows = cur.fetchall()
    
    if not rows:
        # Fallback to future flights if current timestamp is ahead
        cur.execute("""
            SELECT 
                ar.sequence_order,
                f.flight_id,
                f.flight_number,
                f.origin_station,
                f.dest_station,
                f.scheduled_departure_ts,
                f.scheduled_arrival_ts,
                ar.turnaround_buffer_mins,
                f.passenger_count,
                f.connecting_passenger_count
            FROM AERORESOLVE.CURATED.FACT_AIRCRAFT_ROTATION ar
            JOIN AERORESOLVE.CURATED.FACT_FLIGHTS f ON ar.flight_id = f.flight_id
            WHERE f.aircraft_id = %s AND f.flight_status = 'SCHEDULED'
            ORDER BY ar.sequence_order ASC
            LIMIT 6
        """, (aircraft_id,))
        rows = cur.fetchall()

    cur.close()

    downstream_flights = []
    total_pax = 0
    total_conn_pax = 0
    accumulated_delay_mins = max(0, estimated_downtime_mins - 45) # Ground buffer is ~45 mins

    for r in rows:
        pax = r[8] or 150
        conn_pax = r[9] or 25
        total_pax += pax
        total_conn_pax += conn_pax
        downstream_flights.append({
            "sequence": r[0],
            "flight_id": r[1],
            "flight_number": r[2],
            "route": f"{r[3]} -> {r[4]}",
            "departure": str(r[5]),
            "arrival": str(r[6]),
            "buffer_mins": r[7],
            "passengers": pax,
            "connecting_passengers": conn_pax
        })

    # Financial Exposure Formula based on COST_ASSUMPTIONS
    # Delay cost: INR 3,200 per delay minute
    # Misconnection care: INR 12,500 per connecting passenger
    # AOG downtime: INR 185,000 per downtime hour
    downtime_hours = round(estimated_downtime_mins / 60.0, 2)
    aog_direct_loss = round(downtime_hours * 185000.0, 2)
    delay_operational_cost = round(accumulated_delay_mins * 3200.0, 2)
    misconnection_compensation_cost = round(total_conn_pax * 12500.0, 2)
    total_exposure_inr = round(aog_direct_loss + delay_operational_cost + misconnection_compensation_cost, 2)

    risk_level = "CRITICAL" if total_conn_pax > 50 or total_exposure_inr > 1000000 else "HIGH"

    return {
        "aircraft_id": aircraft_id,
        "estimated_downtime_mins": estimated_downtime_mins,
        "downstream_sectors_at_risk": len(downstream_flights),
        "total_passengers_impacted": total_pax,
        "total_connecting_passengers_at_risk": total_conn_pax,
        "financial_exposure": {
            "aog_hourly_loss_inr": aog_direct_loss,
            "operational_delay_cost_inr": delay_operational_cost,
            "passenger_misconnection_care_inr": misconnection_compensation_cost,
            "total_risk_inr": total_exposure_inr
        },
        "connection_risk_level": risk_level,
        "downstream_rotation_schedule": downstream_flights
    }
