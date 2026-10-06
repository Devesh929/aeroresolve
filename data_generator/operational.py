"""
AeroResolve Operational Facts Generator
Generates flights, inventory, tools, rosters, tech logs, and maintenance actions.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from data_generator.config import STATIONS, PARTS, RANDOM_SEED, ProfileConfig
from data_generator.scenarios import SCENARIOS

def generate_operational_facts(dimensions: Dict[str, List[Dict[str, Any]]], profile: ProfileConfig) -> Dict[str, List[Dict[str, Any]]]:
    rng = random.Random(RANDOM_SEED)
    fleet = dimensions["DIM_AIRCRAFT"]
    routes = dimensions["DIM_ROUTE"]
    engineers = dimensions["DIM_ENGINEER"]
    tools = dimensions["DIM_TOOL"]

    # Target reference timestamp for simulation
    now = datetime(2026, 10, 6, 14, 0, 0)
    start_date = now - timedelta(days=profile.history_days)

    flights = []
    fault_events = []
    acars_messages = []
    tech_logs = []
    work_orders = []
    maint_actions = []
    part_movements = []
    rotations = []
    connections = []
    delays = []

    flight_seq = 1
    fault_seq = 1
    action_seq = 1
    wo_seq = 1
    acars_seq = 1

    # Map routes by origin
    routes_by_origin = {}
    for r in routes:
        routes_by_origin.setdefault(r["origin_station"], []).append(r)

    # 1. Generate Historical & Active Flights
    for ac in fleet:
        tail = ac["aircraft_id"]
        current_station = ac["home_base"]
        sim_time = start_date + timedelta(hours=rng.randint(5, 10))

        rotation_order = 1
        while sim_time < now + timedelta(hours=18):
            possible_routes = routes_by_origin.get(current_station, [])
            if not possible_routes:
                possible_routes = [r for r in routes if r["origin_station"] == "DEL"]
                current_station = "DEL"

            chosen_route = rng.choice(possible_routes)
            flight_num = f"AB-{rng.randint(101, 899)}"
            fl_duration = timedelta(minutes=chosen_route["scheduled_flight_time_mins"])
            
            # Special deterministic override for ABR-017 active flight
            if tail == "ABR-017" and (now - timedelta(hours=1)) <= sim_time <= now:
                chosen_route = next(r for r in routes if r["origin_station"] == "BLR" and r["dest_station"] == "DEL")
                flight_num = "AB-402"
                sim_time = now - timedelta(minutes=65)  # 65 minutes into flight (airborne at cruise!)
            
            sched_dep = sim_time
            sched_arr = sched_dep + fl_duration
            
            flight_id = f"FL-{sched_dep.strftime('%Y%m%d')}-{tail.replace('ABR-', '')}-{flight_seq:04d}"
            flight_seq += 1

            status = "LANDED"
            actual_dep = sched_dep + timedelta(minutes=rng.randint(-5, 15))
            actual_arr = sched_arr + timedelta(minutes=rng.randint(-5, 20))

            if sched_dep <= now < sched_arr:
                status = "AIRBORNE"
                actual_arr = None
            elif sched_dep > now:
                status = "SCHEDULED"
                actual_dep = None
                actual_arr = None

            passengers = rng.randint(145, 182)
            connecting_pax = rng.randint(20, 50) if chosen_route["dest_station"] in ["DEL", "BOM", "DXB"] else rng.randint(5, 15)

            flight_rec = {
                "flight_id": flight_id,
                "flight_number": flight_num,
                "aircraft_id": tail,
                "route_id": chosen_route["route_id"],
                "origin_station": chosen_route["origin_station"],
                "dest_station": chosen_route["dest_station"],
                "scheduled_departure_ts": sched_dep.strftime('%Y-%m-%d %H:%M:%S'),
                "actual_departure_ts": actual_dep.strftime('%Y-%m-%d %H:%M:%S') if actual_dep else None,
                "scheduled_arrival_ts": sched_arr.strftime('%Y-%m-%d %H:%M:%S'),
                "actual_arrival_ts": actual_arr.strftime('%Y-%m-%d %H:%M:%S') if actual_arr else None,
                "flight_status": status,
                "passenger_count": passengers,
                "connecting_passenger_count": connecting_pax,
                "delay_departure_minutes": max(0, int((actual_dep - sched_dep).total_seconds() / 60)) if actual_dep else 0,
                "delay_arrival_minutes": max(0, int((actual_arr - sched_arr).total_seconds() / 60)) if actual_arr else 0
            }
            flights.append(flight_rec)

            # Rotation sequence
            rotations.append({
                "rotation_id": f"ROT-{flight_id}",
                "aircraft_id": tail,
                "sequence_order": rotation_order,
                "flight_id": flight_id,
                "turnaround_buffer_mins": 45
            })
            rotation_order += 1

            # International connecting passenger segments
            if chosen_route["dest_station"] in ["DEL", "BOM", "DXB"] and status in ["AIRBORNE", "SCHEDULED"]:
                connections.append({
                    "connection_id": f"CONN-{flight_id}-01",
                    "inbound_flight_id": flight_id,
                    "outbound_flight_id": flight_id, # Linkable in graph
                    "connecting_station": chosen_route["dest_station"],
                    "scheduled_connection_mins": 75,
                    "passenger_count": connecting_pax,
                    "high_value_segment": "CONNECTING_INTL"
                })

            # Next flight begins after ground turnaround
            turnaround = timedelta(minutes=rng.randint(45, 65))
            current_station = chosen_route["dest_station"]
            sim_time = sched_arr + turnaround

    # 2. Inject Deterministic Historical Actions for ABR-017 (Scenarios 1 & 2)
    abr17_past_flights = [f for f in flights if f["aircraft_id"] == "ABR-017" and f["flight_status"] == "LANDED"]
    if len(abr17_past_flights) >= 2:
        # Incident 1: 12 days ago
        f1 = abr17_past_flights[-5] if len(abr17_past_flights) >= 5 else abr17_past_flights[0]
        fe1_id = f"FE-HIST-{fault_seq:04d}"
        fault_seq += 1
        fault_events.append({
            "fault_event_id": fe1_id,
            "flight_id": f1["flight_id"],
            "aircraft_id": "ABR-017",
            "fault_code": "FAULT-21-204",
            "event_ts": f1["scheduled_departure_ts"],
            "flight_phase": "CRUISE",
            "altitude_ft": 34800.0,
            "outside_air_temp_c": -48.5,
            "vibration_index": 1.22,
            "avionics_fan_current_a": 4.1,
            "is_intermittent": True,
            "normalized_on_ground": True,
            "severity": "WARNING"
        })
        acars_messages.append({
            "message_id": f"ACARS-MSG-{acars_seq:04d}",
            "flight_id": f1["flight_id"],
            "aircraft_id": "ABR-017",
            "message_ts": f1["scheduled_departure_ts"],
            "message_type": "FAULT",
            "fault_code": "FAULT-21-204",
            "raw_message_text": "DIAG 212601 AVIONICS DUCT AIRFLOW LO FL348 OAT-48"
        })
        acars_seq += 1
        tech_logs.append({
            "tech_log_id": f"TL-HIST-01",
            "flight_id": f1["flight_id"],
            "aircraft_id": "ABR-017",
            "logged_ts": f1["actual_arrival_ts"],
            "defect_description": "Intermittent AVIONICS DUCT AIRFLOW warning at cruise FL350. Disappeared on descent. Ground test normal: No Fault Found (NFF).",
            "logged_by": "CAPTAIN",
            "rectification_status": "RECTIFIED",
            "mel_reference": None
        })
        wo1_id = f"WO-HIST-{wo_seq:04d}"
        wo_seq += 1
        work_orders.append({
            "work_order_id": wo1_id,
            "aircraft_id": "ABR-017",
            "station_code": f1["dest_station"],
            "fault_event_id": fe1_id,
            "created_ts": f1["actual_arrival_ts"],
            "scheduled_start_ts": f1["actual_arrival_ts"],
            "completed_ts": f1["actual_arrival_ts"],
            "status": "CLOSED",
            "lead_engineer_id": engineers[0]["engineer_id"]
        })
        maint_actions.append({
            "action_id": f"ACT-HIST-{action_seq:04d}",
            "work_order_id": wo1_id,
            "aircraft_id": "ABR-017",
            "station_code": f1["dest_station"],
            "performed_ts": f1["actual_arrival_ts"],
            "action_type_id": "ACT-RESET-COMP",
            "component_type_id": "AV-COMP-01",
            "part_number_used": None,
            "action_notes": "Performed BITE test on AVCC computer. BITE OK. Reset computer circuit breaker. Defect cleared on ground.",
            "is_repeat_defect": False,
            "recurrence_interval_days": None
        })
        action_seq += 1

        # Incident 2: 5 days ago (Repeated defect! False fix replacement)
        f2 = abr17_past_flights[-2]
        fe2_id = f"FE-HIST-{fault_seq:04d}"
        fault_seq += 1
        fault_events.append({
            "fault_event_id": fe2_id,
            "flight_id": f2["flight_id"],
            "aircraft_id": "ABR-017",
            "fault_code": "FAULT-21-204",
            "event_ts": f2["scheduled_departure_ts"],
            "flight_phase": "CRUISE",
            "altitude_ft": 35200.0,
            "outside_air_temp_c": -51.2,
            "vibration_index": 1.28,
            "avionics_fan_current_a": 4.35,
            "is_intermittent": True,
            "normalized_on_ground": True,
            "severity": "WARNING"
        })
        acars_messages.append({
            "message_id": f"ACARS-MSG-{acars_seq:04d}",
            "flight_id": f2["flight_id"],
            "aircraft_id": "ABR-017",
            "message_ts": f2["scheduled_departure_ts"],
            "message_type": "FAULT",
            "fault_code": "FAULT-21-204",
            "raw_message_text": "DIAG 212601 AVIONICS DUCT AIRFLOW LO FL352 RECURRENCE"
        })
        acars_seq += 1
        tech_logs.append({
            "tech_log_id": f"TL-HIST-02",
            "flight_id": f2["flight_id"],
            "aircraft_id": "ABR-017",
            "logged_ts": f2["actual_arrival_ts"],
            "defect_description": "REPEAT DEFECT: Avionics cooling airflow warning recurring during high altitude cruise. Ground BITE test inconclusive.",
            "logged_by": "LINE_ENGINEER",
            "rectification_status": "RECTIFIED",
            "mel_reference": None
        })
        wo2_id = f"WO-HIST-{wo_seq:04d}"
        wo_seq += 1
        work_orders.append({
            "work_order_id": wo2_id,
            "aircraft_id": "ABR-017",
            "station_code": f2["dest_station"],
            "fault_event_id": fe2_id,
            "created_ts": f2["actual_arrival_ts"],
            "scheduled_start_ts": f2["actual_arrival_ts"],
            "completed_ts": f2["actual_arrival_ts"],
            "status": "CLOSED",
            "lead_engineer_id": engineers[1]["engineer_id"]
        })
        maint_actions.append({
            "action_id": f"ACT-HIST-{action_seq:04d}",
            "work_order_id": wo2_id,
            "aircraft_id": "ABR-017",
            "station_code": f2["dest_station"],
            "performed_ts": f2["actual_arrival_ts"],
            "action_type_id": "ACT-SWAP-COMP",
            "component_type_id": "AV-COMP-01",
            "part_number_used": "PART-AVC-902",
            "action_notes": "Suspected intermittent internal relay in AVCC. Removed AVCC computer and installed replacement PART-AVC-902. Ground test sat.",
            "is_repeat_defect": True,
            "recurrence_interval_days": 7.0
        })
        action_seq += 1

    # 3. Part Inventory (Ensuring Scenario 4: DEL stockout, BOM stock=3)
    part_inventory = []
    inv_id = 1
    for s in STATIONS:
        for p in PARTS:
            p_num = p["part_number"]
            qty = rng.randint(2, 6) if s["is_hub"] else rng.randint(0, 2)
            
            # Deterministic scenario 4 override:
            if p_num == "PART-X42-CONN":
                if s["code"] == "DEL":
                    qty = 0  # CRITICAL: Missing at destination!
                elif s["code"] == "BOM":
                    qty = 3  # CRITICAL: 3 units available at Mumbai!
                elif s["code"] == "BLR":
                    qty = 1
            
            part_inventory.append({
                "inventory_id": f"INV-{inv_id:04d}",
                "station_code": s["code"],
                "part_number": p_num,
                "quantity_on_hand": qty,
                "quantity_reserved": 0,
                "minimum_safety_stock": 2 if s["is_hub"] else 1,
                "last_updated_ts": now.strftime('%Y-%m-%d %H:%M:%S')
            })
            inv_id += 1

    # 4. Tool Availability & Engineer Roster
    engineer_roster = []
    rost_id = 1
    today = now.date()
    for e in engineers:
        for d_offset in range(-2, 3):
            shift_d = today + timedelta(days=d_offset)
            engineer_roster.append({
                "roster_id": f"ROST-{rost_id:05d}",
                "engineer_id": e["engineer_id"],
                "station_code": e["station_code"],
                "shift_date": str(shift_d),
                "shift_name": "MORNING" if rost_id % 3 == 0 else ("AFTERNOON" if rost_id % 3 == 1 else "NIGHT"),
                "is_available": True
            })
            rost_id += 1

    tool_availability = []
    ta_id = 1
    for t in tools:
        tool_availability.append({
            "tool_avail_id": f"TA-{ta_id:04d}",
            "tool_id": t["tool_id"],
            "station_code": t["station_code"],
            "status": "AVAILABLE",
            "current_work_order_id": None
        })
        ta_id += 1

    # 5. Station Capability Matrix
    station_capabilities = []
    sc_id = 1
    for s in STATIONS:
        for ata in ["21", "24", "29", "36", "73"]:
            level = "FULL_OVERHAUL" if s["is_hub"] else "INSPECTION_ONLY"
            if s["code"] in ["DEL", "BOM", "BLR"] and ata == "21":
                level = "COMPONENT_REPLACE"
            station_capabilities.append({
                "station_cap_id": f"SCAP-{sc_id:04d}",
                "station_code": s["code"],
                "ata_chapter": ata,
                "capability_level": level,
                "is_active": True
            })
            sc_id += 1

    return {
        "FACT_FLIGHTS": flights,
        "FACT_FAULT_EVENTS": fault_events,
        "FACT_ACARS_MESSAGES": acars_messages,
        "FACT_TECH_LOG": tech_logs,
        "FACT_WORK_ORDERS": work_orders,
        "FACT_MAINTENANCE_ACTIONS": maint_actions,
        "FACT_PART_INVENTORY": part_inventory,
        "FACT_ENGINEER_ROSTER": engineer_roster,
        "FACT_TOOL_AVAILABILITY": tool_availability,
        "FACT_AIRCRAFT_ROTATION": rotations,
        "FACT_PASSENGER_CONNECTIONS": connections,
        "FACT_STATION_CAPABILITY": station_capabilities,
        "FACT_PART_MOVEMENTS": part_movements,
        "FACT_DELAY_EVENTS": delays
    }
