"""
AeroResolve Causal Telemetry Generator
Generates wide multivariate sensor observations governed by latent degradation models and flight physics.
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Iterator
import pyarrow as pa
import pyarrow.parquet as pq
from data_generator.config import RANDOM_SEED, ProfileConfig

def simulate_flight_telemetry(flight: Dict[str, Any], sample_interval_secs: int = 15) -> List[Dict[str, Any]]:
    rng = random.Random(f"{RANDOM_SEED}_{flight['flight_id']}")
    
    sched_dep = datetime.strptime(flight["scheduled_departure_ts"], '%Y-%m-%d %H:%M:%S')
    # Duration in seconds
    duration_mins = flight.get("scheduled_flight_time_mins", 120)
    total_secs = duration_mins * 60
    
    tail = flight["aircraft_id"]
    is_demo_target = (tail == "ABR-017" and flight["flight_number"] == "AB-402")
    is_healthy_control = (tail == "ABR-009")

    # Latent aircraft degradation score (0-100)
    base_fan_current = 3.25
    if tail == "ABR-017":
        # Scenario 3: Fan current creep (Silent degradation)
        base_fan_current = 4.35
    elif tail == "ABR-042":
        base_fan_current = 3.85

    observations = []
    num_samples = max(10, total_secs // sample_interval_secs)

    for i in range(num_samples):
        progress = i / float(num_samples)
        t_offset = i * sample_interval_secs
        event_time = sched_dep + timedelta(seconds=t_offset)

        # 1. Flight Phase & Flight Physics
        if progress < 0.08:
            phase = "TAXI_OUT"
            alt = 800.0 + rng.uniform(-10, 10)
            spd = rng.uniform(10, 25)
            n1 = 28.0 + rng.uniform(-1, 1)
            oat = 28.0 + rng.uniform(-1, 2)
        elif progress < 0.15:
            phase = "TAKEOFF"
            alt = 1200.0 + (progress - 0.08) / 0.07 * 3500.0
            spd = 140.0 + (progress - 0.08) / 0.07 * 110.0
            n1 = 92.0 + rng.uniform(-1, 1)
            oat = 25.0 - (alt / 1000.0) * 1.98
        elif progress < 0.35:
            phase = "CLIMB"
            alt_prog = (progress - 0.15) / 0.20
            alt = 4700.0 + alt_prog * 30300.0  # Climbs up to 35,000 ft
            spd = 250.0 + alt_prog * 180.0
            n1 = 86.0 + rng.uniform(-1, 1)
            oat = 25.0 - (alt / 1000.0) * 2.05
        elif progress < 0.75:
            phase = "CRUISE"
            alt = 35000.0 + math.sin(i * 0.1) * 80.0 + rng.uniform(-20, 20)
            spd = 455.0 + rng.uniform(-5, 5)
            n1 = 78.5 + rng.uniform(-0.8, 0.8)
            oat = -48.0 + rng.uniform(-2.5, 1.5)  # Severe cold high altitude
        elif progress < 0.88:
            phase = "DESCENT"
            desc_prog = (progress - 0.75) / 0.13
            alt = 35000.0 - desc_prog * 29000.0
            spd = 420.0 - desc_prog * 180.0
            n1 = 45.0 + rng.uniform(-2, 2)
            oat = -48.0 + desc_prog * 65.0
        elif progress < 0.95:
            phase = "APPROACH"
            app_prog = (progress - 0.88) / 0.07
            alt = 6000.0 - app_prog * 5200.0
            spd = 240.0 - app_prog * 105.0
            n1 = 55.0 + rng.uniform(-1, 1)
            oat = 18.0 + rng.uniform(-1, 1)
        elif progress < 0.98:
            phase = "LANDING"
            alt = 800.0 + rng.uniform(0, 50)
            spd = 135.0 + rng.uniform(-5, 5)
            n1 = 65.0 + rng.uniform(-2, 2)
            oat = 28.0 + rng.uniform(-1, 1)
        else:
            phase = "TAXI_IN"
            alt = 800.0 + rng.uniform(-5, 5)
            spd = rng.uniform(8, 20)
            n1 = 26.0 + rng.uniform(-1, 1)
            oat = 29.0 + rng.uniform(-1, 1)

        cabin_alt = min(7800.0, alt * 0.22 + 400.0)

        # 2. Vibration Index
        vib = 0.52 + rng.uniform(-0.06, 0.08)
        if phase == "TAKEOFF":
            vib += 0.35
        elif phase == "CRUISE":
            if is_demo_target:
                # Scenario 1: Elevated vibration at cruise
                vib = 1.24 + rng.uniform(-0.08, 0.12)
            elif is_healthy_control and 0.45 < progress < 0.55:
                # Scenario 8: Transient benign turbulence spike
                vib = 1.32 + rng.uniform(-0.05, 0.08)

        # 3. Avionics Extraction Fan Current & Rack Temp
        fan_current = base_fan_current + rng.uniform(-0.08, 0.08)
        rack_temp = 32.5 + (fan_current - 3.2) * 5.2 + rng.uniform(-0.5, 0.5)

        # Scenario 1 & 2 In-Flight Ghost Fault Trigger:
        # Occurs during cruise at high altitude (> 32,000 ft), severe cold (< -42C), elevated vibration (> 1.15)
        if is_demo_target and phase == "CRUISE" and progress > 0.42:
            # Micro-fretting intermittency causes resistance spike -> current anomaly & flow sensor drop
            fan_current = 4.85 + math.sin(i * 0.4) * 0.45
            rack_temp += 4.8

        # 4. Engine & Auxiliary Channels
        egt = 610.0 + n1 * 1.8 + rng.uniform(-5, 5)
        n2 = n1 * 1.08 + rng.uniform(-0.5, 0.5)
        fuel_flow = max(420.0, n1 * 26.5 + rng.uniform(-20, 20))
        oil_press = 58.0 + rng.uniform(-1.5, 1.5)
        oil_temp = 82.0 + (n1 / 100.0) * 18.0 + rng.uniform(-1, 1)

        elec_bus_v = 115.0 + rng.uniform(-0.8, 0.8)
        batt_v = 28.1 + rng.uniform(-0.2, 0.2)
        gen1_load = 48.0 + rng.uniform(-3, 3)
        gen2_load = 47.0 + rng.uniform(-3, 3)
        apu_gen_load = 0.0 if alt > 15000 else 12.0

        pack1_temp = 18.0 + rng.uniform(-1, 1)
        pack2_temp = 18.2 + rng.uniform(-1, 1)
        bleed_press = 42.0 + rng.uniform(-1.5, 1.5)

        hyd_green = 3000.0 + rng.uniform(-40, 40)
        hyd_blue = 3010.0 + rng.uniform(-35, 35)
        hyd_yellow = 2995.0 + rng.uniform(-40, 40)

        brake_temp_l = 145.0 + (280.0 if phase in ["LANDING", "TAXI_IN"] else 0.0) + rng.uniform(-5, 5)
        brake_temp_r = brake_temp_l + rng.uniform(-3, 3)

        flap_deg = 0.0
        slat_deg = 0.0
        if phase in ["TAKEOFF", "CLIMB"]:
            flap_deg, slat_deg = 15.0, 18.0
        elif phase in ["APPROACH", "LANDING"]:
            flap_deg, slat_deg = 35.0, 27.0

        obs = {
            "flight_id": flight["flight_id"],
            "aircraft_id": tail,
            "event_ts": event_time.strftime('%Y-%m-%d %H:%M:%S'),
            "flight_phase": phase,
            "altitude_ft": round(alt, 1),
            "airspeed_kts": round(spd, 1),
            "outside_air_temp_c": round(oat, 1),
            "cabin_altitude_ft": round(cabin_alt, 1),
            "engine_1_n1": round(n1, 2),
            "engine_2_n1": round(n1 + rng.uniform(-0.2, 0.2), 2),
            "engine_1_egt_c": round(egt, 1),
            "engine_2_egt_c": round(egt + rng.uniform(-2, 2), 1),
            "engine_1_n2": round(n2, 2),
            "engine_2_n2": round(n2 + rng.uniform(-0.2, 0.2), 2),
            "fuel_flow_1_kgh": round(fuel_flow, 1),
            "fuel_flow_2_kgh": round(fuel_flow + rng.uniform(-10, 10), 1),
            "oil_pressure_1_psi": round(oil_press, 1),
            "oil_pressure_2_psi": round(oil_press + rng.uniform(-0.5, 0.5), 1),
            "oil_temp_1_c": round(oil_temp, 1),
            "oil_temp_2_c": round(oil_temp + rng.uniform(-0.8, 0.8), 1),
            "avionics_fan_current_a": round(fan_current, 2),
            "avionics_rack_temp_c": round(rack_temp, 1),
            "vibration_index": round(vib, 2),
            "elec_bus_voltage_v": round(elec_bus_v, 1),
            "battery_voltage_v": round(batt_v, 2),
            "generator_1_load_pct": round(gen1_load, 1),
            "generator_2_load_pct": round(gen2_load, 1),
            "apu_generator_load_pct": round(apu_gen_load, 1),
            "pack_1_temp_c": round(pack1_temp, 1),
            "pack_2_temp_c": round(pack2_temp, 1),
            "pack_1_flow_kgs": 1.25,
            "pack_2_flow_kgs": 1.24,
            "bleed_1_pressure_psi": round(bleed_press, 1),
            "bleed_2_pressure_psi": round(bleed_press + rng.uniform(-0.5, 0.5), 1),
            "cabin_differential_pressure_psi": round(max(0.0, (alt - cabin_alt) * 0.00028), 2),
            "hydraulic_press_green_psi": round(hyd_green, 1),
            "hydraulic_press_blue_psi": round(hyd_blue, 1),
            "hydraulic_press_yellow_psi": round(hyd_yellow, 1),
            "hydraulic_quantity_green_pct": 94.0,
            "brake_temp_left_c": round(brake_temp_l, 1),
            "brake_temp_right_c": round(brake_temp_r, 1),
            "flap_position_deg": flap_deg,
            "slat_position_deg": slat_deg,
            "rudder_trim_deg": 0.0,
            "pitch_angle_deg": 2.5 if phase == "CRUISE" else (12.0 if phase == "TAKEOFF" else -3.0),
            "roll_angle_deg": 0.0,
            "vertical_speed_fpm": 0.0 if phase == "CRUISE" else (1800.0 if phase == "CLIMB" else -1500.0)
        }
        observations.append(obs)

    return observations
