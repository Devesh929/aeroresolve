"""
AeroResolve Dimensions Generator
Generates realistic dimensional master data for AeroBharat Airlines.
"""

import random
from datetime import date, timedelta
from typing import Dict, List, Any
from data_generator.config import (
    STATIONS, AIRCRAFT_TYPES, COMPONENT_TYPES, FAULT_CODES,
    PARTS, MAINTENANCE_ACTIONS, RANDOM_SEED, ProfileConfig
)

def generate_dimensions(profile: ProfileConfig) -> Dict[str, List[Dict[str, Any]]]:
    rng = random.Random(RANDOM_SEED)

    # 1. Aircraft Types
    dim_aircraft_type = AIRCRAFT_TYPES

    # 2. Stations
    dim_station = [
        {
            "station_code": s["code"],
            "station_name": s["name"],
            "city": s["city"],
            "country": s["country"],
            "is_hub": s["is_hub"],
            "maintenance_tier": s["tier"],
            "has_avionics_shop": s["avionics"],
            "has_engine_shop": s["engine"],
            "latitude": s["lat"],
            "longitude": s["lon"]
        }
        for s in STATIONS
    ]

    # 3. Routes (pairwise between hubs and line stations)
    routes = []
    hub_codes = [s["code"] for s in STATIONS if s["is_hub"]]
    line_codes = [s["code"] for s in STATIONS if not s["is_hub"]]

    for h1 in hub_codes:
        for h2 in hub_codes:
            if h1 != h2:
                routes.append({
                    "route_id": f"{h1}-{h2}",
                    "origin_station": h1,
                    "dest_station": h2,
                    "scheduled_flight_time_mins": rng.randint(90, 160),
                    "distance_nm": rng.randint(650, 1100),
                    "route_type": "DOMESTIC_TRUNK"
                })

    for h in hub_codes:
        for l in line_codes:
            routes.append({
                "route_id": f"{h}-{l}",
                "origin_station": h,
                "dest_station": l,
                "scheduled_flight_time_mins": rng.randint(70, 140),
                "distance_nm": rng.randint(450, 950),
                "route_type": "REGIONAL" if l not in ["DXB", "SIN", "BKK"] else "INTERNATIONAL"
            })
            routes.append({
                "route_id": f"{l}-{h}",
                "origin_station": l,
                "dest_station": h,
                "scheduled_flight_time_mins": rng.randint(70, 140),
                "distance_nm": rng.randint(450, 950),
                "route_type": "REGIONAL" if l not in ["DXB", "SIN", "BKK"] else "INTERNATIONAL"
            })

    # 4. Aircraft Fleet
    fleet = []
    base_date = date(2023, 1, 15)
    for i in range(1, profile.num_aircraft + 1):
        tail = f"ABR-{i:03d}"
        ac_type = "AB-320N" if i % 3 != 0 else "AB-321N"
        home_hub = hub_codes[i % len(hub_codes)]
        delivery = base_date + timedelta(days=(i * 23) % 400)
        flight_hrs = round(rng.uniform(1800.0, 7500.0), 1)
        flight_cycles = int(flight_hrs / 2.1)
        
        status = "ACTIVE"
        if tail == "ABR-017":
            status = "DEGRADED"
        
        fleet.append({
            "aircraft_id": tail,
            "aircraft_type_id": ac_type,
            "serial_number": f"MSN-{10000 + i}",
            "delivery_date": str(delivery),
            "home_base": home_hub,
            "total_flight_hours": flight_hrs,
            "total_flight_cycles": flight_cycles,
            "current_status": status,
            "last_c_check_date": str(delivery + timedelta(days=500))
        })

    if not any(a["aircraft_id"] == "ABR-017" for a in fleet):
        fleet[0]["aircraft_id"] = "ABR-017"
        fleet[0]["current_status"] = "DEGRADED"
    if not any(a["aircraft_id"] == "ABR-042" for a in fleet) and len(fleet) > 1:
        fleet[1]["aircraft_id"] = "ABR-042"

    # 5. Component Serials
    component_serials = []
    c_idx = 1
    for a in fleet:
        for c in COMPONENT_TYPES:
            c_type = c["component_type_id"]
            sn = f"SN-{c_type}-{c_idx:04d}"
            c_idx += 1
            hrs = round(rng.uniform(400.0, 3200.0), 1)
            cycles = int(hrs / 2.0)
            
            health = round(rng.uniform(85.0, 99.5), 2)
            if a["aircraft_id"] == "ABR-017" and c_type in ["WIR-HARN-21", "AV-COMP-01"]:
                health = 61.5
            
            component_serials.append({
                "serial_number": sn,
                "component_type_id": c_type,
                "manufacture_date": str(base_date - timedelta(days=rng.randint(200, 800))),
                "accumulated_hours": hrs,
                "accumulated_cycles": cycles,
                "current_health_score": health,
                "installed_aircraft_id": a["aircraft_id"],
                "status": "INSTALLED"
            })

    # 6. Engineers
    first_names = ["Vikram", "Rajesh", "Pooja", "Amit", "Sneha", "Karan", "Arjun", "Deepak", "Ananya", "Rohan", "Sanjay", "Manoj", "Kavita", "Suresh"]
    last_names = ["Sharma", "Verma", "Patel", "Reddy", "Iyer", "Nair", "Mehta", "Singh", "Mukherjee", "Kulkarni", "Chopra", "Gupta"]
    engineers = []
    e_id = 1
    for s in STATIONS:
        count = 12 if s["is_hub"] else 4
        for _ in range(count):
            eng_id = f"ENG-{e_id:03d}"
            name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
            license_type = rng.choice(["B2_AVIONICS", "B1_MECHANICAL", "DUAL_B1_B2"])
            engineers.append({
                "engineer_id": eng_id,
                "station_code": s["code"],
                "name": name,
                "license_type": license_type,
                "certified_aircraft_type": "AB-320N",
                "years_experience": rng.randint(3, 22)
            })
            e_id += 1

    engineers.append({
        "engineer_id": "ENG-DEL-B2-01",
        "station_code": "DEL",
        "name": "Arun K. Sharma",
        "license_type": "B2_AVIONICS",
        "certified_aircraft_type": "AB-320N",
        "years_experience": 14
    })

    # 7. Specialized Tools
    tools = []
    t_id = 1
    tool_catalog = [
        ("T14-HARN", "T14 Avionics Wiring & Receptacle Diagnostic Harness Tester"),
        ("T08-FLOW", "T08 Pitot & Static Low Airflow Calibration Set"),
        ("T22-FADEC", "T22 FADEC Data Loader & Channel Cross-Talk Analyzer"),
        ("T19-HYD",  "T19 Hydraulic High-Pressure Sensor Ground Check Rig"),
    ]
    for s in STATIONS:
        for t_code, t_desc in tool_catalog:
            if s["is_hub"] or rng.random() > 0.4:
                tools.append({
                    "tool_id": f"TOOL-{t_id:03d}",
                    "tool_code": t_code,
                    "station_code": s["code"],
                    "description": t_desc,
                    "calibration_status": "VALID",
                    "is_serviceable": True
                })
                t_id += 1

    tools.append({
        "tool_id": "TOOL-DEL-T14-01",
        "tool_code": "T14-HARN",
        "station_code": "DEL",
        "description": "T14 Avionics Wiring & Receptacle Diagnostic Harness Tester",
        "calibration_status": "VALID",
        "is_serviceable": True
    })

    # 8. Passenger Segments
    passenger_segments = [
        {"segment_type": "STANDARD", "description": "Standard Economy Class Passenger", "high_value_priority": 1},
        {"segment_type": "BUSINESS", "description": "Premium Business Class Passenger", "high_value_priority": 3},
        {"segment_type": "CONNECTING_INTL", "description": "Passenger Connecting to Onward International Sector", "high_value_priority": 5},
    ]

    return {
        "DIM_AIRCRAFT_TYPE": dim_aircraft_type,
        "DIM_STATION": dim_station,
        "DIM_ROUTE": routes,
        "DIM_COMPONENT_TYPE": COMPONENT_TYPES,
        "DIM_FAULT_CODE": FAULT_CODES,
        "DIM_MAINTENANCE_ACTION": MAINTENANCE_ACTIONS,
        "DIM_AIRCRAFT": fleet,
        "DIM_COMPONENT_SERIAL": component_serials,
        "DIM_ENGINEER": engineers,
        "DIM_TOOL": tools,
        "DIM_PART": PARTS,
        "DIM_PASSENGER_SEGMENT": passenger_segments,
    }
