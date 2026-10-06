"""
backend/tools/readiness_tools.py
Specialized tools for Ground Readiness Agent to evaluate destination maintenance capability,
check spare parts inventory, and source expedited spares.
"""
from typing import Dict, Any, List
import snowflake.connector

def check_station_readiness(conn: snowflake.connector.SnowflakeConnection, station_code: str, part_number: str = "PART-X42-CONN", ata_chapter: str = "21") -> Dict[str, Any]:
    """
    Evaluates destination station capability across 3 pillars:
    1. Spare part availability (stock on hand vs reserved)
    2. Station maintenance certification for ATA chapter
    3. Licensed engineers and tooling on duty
    """
    cur = conn.cursor()
    
    # 1. Part stock at station
    cur.execute("""
        SELECT quantity_on_hand, quantity_reserved, (quantity_on_hand - quantity_reserved) AS available
        FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY
        WHERE station_code = %s AND part_number = %s
    """, (station_code, part_number))
    inv_row = cur.fetchone()
    qoh = inv_row[0] if inv_row else 0
    q_res = inv_row[1] if inv_row else 0
    available_stock = inv_row[2] if inv_row else 0

    # 2. Station capability
    cur.execute("""
        SELECT capability_level, is_active
        FROM AERORESOLVE.CURATED.FACT_STATION_CAPABILITY
        WHERE station_code = %s AND ata_chapter = %s
    """, (station_code, ata_chapter))
    cap_row = cur.fetchone()
    cap_level = cap_row[0] if cap_row else "NONE"
    cap_active = bool(cap_row[1]) if cap_row else False

    # 3. Available engineers & tools
    cur.execute("""
        SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_ENGINEER_ROSTER
        WHERE station_code = %s AND is_available = TRUE
    """, (station_code,))
    engineers_count = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_TOOL_AVAILABILITY
        WHERE station_code = %s AND status = 'AVAILABLE'
    """, (station_code,))
    tools_count = cur.fetchone()[0] or 0

    cur.close()

    is_ready = (available_stock > 0) and cap_active and (engineers_count > 0) and (tools_count > 0)
    status_label = "READY" if is_ready else ("PART_STOCKOUT" if available_stock <= 0 else "CAPABILITY_LIMIT")

    return {
        "station_code": station_code,
        "part_number": part_number,
        "ata_chapter": ata_chapter,
        "is_ready_for_touchdown_repair": is_ready,
        "readiness_status": status_label,
        "spares": {
            "quantity_on_hand": qoh,
            "quantity_reserved": q_res,
            "quantity_available": available_stock,
            "stockout": available_stock <= 0
        },
        "station_capability": {
            "capability_level": cap_level,
            "is_active": cap_active
        },
        "resources": {
            "available_engineers_on_duty": engineers_count,
            "available_tooling_sets": tools_count
        }
    }

def find_spare_reposition_source(conn: snowflake.connector.SnowflakeConnection, part_number: str = "PART-X42-CONN", dest_station: str = "DEL") -> Dict[str, Any]:
    """
    Identifies the optimal station to source the missing spare part and calculates logistics lead time.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            pi.station_code,
            s.station_name,
            (pi.quantity_on_hand - pi.quantity_reserved) AS available_stock,
            COALESCE(r.scheduled_flight_time_mins, 150) AS flight_time_mins,
            ROUND(COALESCE(r.scheduled_flight_time_mins, 150) / 60.0, 1) AS flight_hours
        FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY pi
        JOIN AERORESOLVE.CURATED.DIM_STATION s ON pi.station_code = s.station_code
        LEFT JOIN AERORESOLVE.CURATED.DIM_ROUTE r ON r.origin_station = pi.station_code AND r.dest_station = %s
        WHERE pi.part_number = %s AND (pi.quantity_on_hand - pi.quantity_reserved) > 0 AND pi.station_code != %s
        ORDER BY available_stock DESC, flight_time_mins ASC
        LIMIT 1
    """, (dest_station, part_number, dest_station))
    row = cur.fetchone()
    cur.close()

    if not row:
        return {
            "reposition_source_station": None,
            "part_number": part_number,
            "can_reposition": False
        }

    source_station = row[0]
    station_name = row[1]
    stock_avail = row[2]
    flight_mins = row[3]
    total_est_hours = round((flight_mins + 90.0) / 60.0, 1)

    return {
        "reposition_source_station": source_station,
        "source_station_name": station_name,
        "dest_station": dest_station,
        "part_number": part_number,
        "stock_available_at_source": stock_avail,
        "scheduled_flight_time_mins": flight_mins,
        "total_estimated_reposition_hours": total_est_hours,
        "can_reposition": True,
        "logistics_notes": f"Dispatch from {source_station} via next scheduled flight. Ground transfer buffer: 90 mins."
    }

def reserve_demo_part(conn: snowflake.connector.SnowflakeConnection, part_number: str, station_code: str) -> bool:
    """
    Reserves a part in inventory for an active case.
    """
    cur = conn.cursor()
    cur.execute("""
        UPDATE AERORESOLVE.CURATED.FACT_PART_INVENTORY
        SET quantity_reserved = quantity_reserved + 1,
            last_updated_ts = CURRENT_TIMESTAMP()
        WHERE part_number = %s AND station_code = %s AND (quantity_on_hand - quantity_reserved) > 0
    """, (part_number, station_code))
    updated = cur.rowcount > 0
    cur.close()
    return updated
