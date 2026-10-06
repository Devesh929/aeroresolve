"""
AeroResolve Live Flight Replay Simulator
Simulates accelerated real-time telemetry streaming from airborne aircraft into Snowflake.
Default speed: 1 real second = 30 synthetic flight seconds.
"""

import os
import sys
import time
import math
import argparse
from datetime import datetime, timedelta
import snowflake.connector
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from data_generator.config import STATIONS

def get_snowflake_connection():
    token_path = os.path.expanduser('~/.snowflake/token.jwt')
    return snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE'
    )

class LiveFlightSimulator:
    def __init__(self, aircraft_id: str = "ABR-017", speed_multiplier: int = 30):
        self.aircraft_id = aircraft_id
        self.flight_number = "AB-402"
        self.origin = "BLR"
        self.destination = "DEL"
        self.flight_id = f"FL-LIVE-{aircraft_id}"
        self.speed_multiplier = speed_multiplier
        
        # Coordinates
        self.orig_lat, self.orig_lon = 13.1986, 77.7066
        self.dest_lat, self.dest_lon = 28.5562, 77.1000
        self.total_flight_mins = 130
        self.total_flight_secs = self.total_flight_mins * 60
        self.elapsed_flight_secs = 2200  # Start already in climb/early cruise for lively demo
        
        self.fault_injected = False
        self.anomaly_detected = False
        self.conn = get_snowflake_connection()

    def step(self, real_interval_secs: float = 1.0) -> dict:
        self.elapsed_flight_secs += int(real_interval_secs * self.speed_multiplier)
        if self.elapsed_flight_secs > self.total_flight_secs:
            self.elapsed_flight_secs = self.total_flight_secs

        progress = self.elapsed_flight_secs / float(self.total_flight_secs)

        # GPS coordinate interpolation
        cur_lat = self.orig_lat + (self.dest_lat - self.orig_lat) * progress
        cur_lon = self.orig_lon + (self.dest_lon - self.orig_lon) * progress
        heading = 358.0  # Northbound BLR -> DEL

        # Aerodynamic state based on flight progress
        if progress < 0.12:
            phase = "TAKEOFF"
            alt = 1200.0 + progress / 0.12 * 3500.0
            spd = 160.0 + progress / 0.12 * 100.0
            n1 = 92.0
            oat = 24.0
        elif progress < 0.35:
            phase = "CLIMB"
            climb_prog = (progress - 0.12) / 0.23
            alt = 4700.0 + climb_prog * 30100.0
            spd = 260.0 + climb_prog * 180.0
            n1 = 86.5
            oat = 24.0 - (alt / 1000.0) * 2.05
        elif progress < 0.78:
            phase = "CRUISE"
            alt = 34800.0 + math.sin(self.elapsed_flight_secs * 0.05) * 60.0
            spd = 458.0
            n1 = 78.4
            oat = -48.5  # Severe cold
        elif progress < 0.94:
            phase = "DESCENT"
            desc_prog = (progress - 0.78) / 0.16
            alt = 34800.0 - desc_prog * 30000.0
            spd = 380.0 - desc_prog * 140.0
            n1 = 48.0
            oat = -48.5 + desc_prog * 65.0
        else:
            phase = "APPROACH"
            alt = 3200.0
            spd = 180.0
            n1 = 56.0
            oat = 22.0

        cabin_alt = min(7600.0, alt * 0.22 + 400.0)

        # Causal Avionics Signal Modeling
        fan_current = 4.38 + math.sin(self.elapsed_flight_secs * 0.1) * 0.08
        vib = 0.55
        fault_code = None
        fault_title = None

        if self.aircraft_id == "ABR-017":
            # Scenario 1 trigger envelope: Cruise altitude > 32,000 ft + OAT < -42C + elevated vibration
            if alt > 32000.0 and oat < -42.0:
                vib = 1.26  # Elevated vibration
                self.anomaly_detected = True

                # When vibration and cold combine for more than 40 minutes into flight, micro-fretting causes intermittent fault
                if progress > 0.45:
                    self.fault_injected = True
                    fan_current = 4.88 + math.sin(self.elapsed_flight_secs * 0.3) * 0.42
                    fault_code = "FAULT-21-204"
                    fault_title = "Avionics Cooling Low Flow Warning"

        rack_temp = 34.0 + (fan_current - 3.2) * 5.5

        # Build telemetry record
        now_ts = datetime.utcnow()
        telemetry_row = {
            "FLIGHT_ID": self.flight_id,
            "AIRCRAFT_ID": self.aircraft_id,
            "EVENT_TS": now_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "FLIGHT_PHASE": phase,
            "ALTITUDE_FT": round(alt, 1),
            "AIRSPEED_KTS": round(spd, 1),
            "OUTSIDE_AIR_TEMP_C": round(oat, 1),
            "CABIN_ALTITUDE_FT": round(cabin_alt, 1),
            "ENGINE_1_N1": round(n1, 2),
            "ENGINE_2_N1": round(n1, 2),
            "ENGINE_1_EGT_C": round(615.0 + n1 * 1.5, 1),
            "ENGINE_2_EGT_C": round(614.0 + n1 * 1.5, 1),
            "ENGINE_1_N2": round(n1 * 1.08, 2),
            "ENGINE_2_N2": round(n1 * 1.08, 2),
            "FUEL_FLOW_1_KGH": 850.0,
            "FUEL_FLOW_2_KGH": 850.0,
            "OIL_PRESSURE_1_PSI": 58.5,
            "OIL_PRESSURE_2_PSI": 58.2,
            "OIL_TEMP_1_C": 85.0,
            "OIL_TEMP_2_C": 85.5,
            "AVIONICS_FAN_CURRENT_A": round(fan_current, 2),
            "AVIONICS_RACK_TEMP_C": round(rack_temp, 1),
            "VIBRATION_INDEX": round(vib, 2),
            "ELEC_BUS_VOLTAGE_V": 115.2,
            "BATTERY_VOLTAGE_V": 28.2,
            "GENERATOR_1_LOAD_PCT": 48.0,
            "GENERATOR_2_LOAD_PCT": 47.5,
            "APU_GENERATOR_LOAD_PCT": 0.0,
            "PACK_1_TEMP_C": 18.0,
            "PACK_2_TEMP_C": 18.2,
            "PACK_1_FLOW_KGS": 1.25,
            "PACK_2_FLOW_KGS": 1.24,
            "BLEED_1_PRESSURE_PSI": 42.1,
            "BLEED_2_PRESSURE_PSI": 42.0,
            "CABIN_DIFFERENTIAL_PRESSURE_PSI": round(max(0.0, (alt - cabin_alt) * 0.00028), 2),
            "HYDRAULIC_PRESS_GREEN_PSI": 3000.0,
            "HYDRAULIC_PRESS_BLUE_PSI": 3010.0,
            "HYDRAULIC_PRESS_YELLOW_PSI": 2995.0,
            "HYDRAULIC_QUANTITY_GREEN_PCT": 94.0,
            "BRAKE_TEMP_LEFT_C": 140.0,
            "BRAKE_TEMP_RIGHT_C": 140.0,
            "FLAP_POSITION_DEG": 0.0,
            "SLAT_POSITION_DEG": 0.0,
            "RUDDER_TRIM_DEG": 0.0,
            "PITCH_ANGLE_DEG": 2.5,
            "ROLL_ANGLE_DEG": 0.0,
            "VERTICAL_SPEED_FPM": 0.0
        }

        # 1. Ingest into Snowflake RAW and CURATED
        df_telem = pd.DataFrame([telemetry_row])
        write_pandas(self.conn, df_telem, "RAW_TELEMETRY_STREAM", schema="RAW", quote_identifiers=False)
        write_pandas(self.conn, df_telem, "FACT_TELEMETRY", schema="CURATED", quote_identifiers=False)

        # 2. Update ACTIVE_FLIGHT_TRACKER in Snowflake
        tracker_sql = f"""
        MERGE INTO AERORESOLVE.OPS.ACTIVE_FLIGHT_TRACKER target
        USING (SELECT
            '{self.aircraft_id}' AS aircraft_id,
            '{self.flight_id}' AS flight_id,
            '{self.flight_number}' AS flight_number,
            '{self.origin}' AS origin,
            '{self.destination}' AS destination,
            '{phase}' AS current_phase,
            {alt} AS current_altitude_ft,
            {spd} AS current_speed_kts,
            {oat} AS outside_air_temp_c,
            {fan_current} AS avionics_fan_current_a,
            {vib} AS vibration_index,
            {rack_temp} AS avionics_rack_temp_c,
            {str(self.anomaly_detected).upper()} AS anomaly_detected,
            {f"'{fault_code}'" if fault_code else "NULL"} AS active_fault_code,
            {f"'{fault_title}'" if fault_title else "NULL"} AS active_fault_title,
            'CASE-ABR-017-001' AS investigation_case_id,
            {cur_lat} AS latitude,
            {cur_lon} AS longitude,
            {heading} AS heading_deg,
            {self.elapsed_flight_secs} AS elapsed_flight_seconds,
            CURRENT_TIMESTAMP() AS last_telemetry_ts
        ) src
        ON target.aircraft_id = src.aircraft_id
        WHEN MATCHED THEN UPDATE SET
            target.current_phase = src.current_phase,
            target.current_altitude_ft = src.current_altitude_ft,
            target.current_speed_kts = src.current_speed_kts,
            target.outside_air_temp_c = src.outside_air_temp_c,
            target.avionics_fan_current_a = src.avionics_fan_current_a,
            target.vibration_index = src.vibration_index,
            target.avionics_rack_temp_c = src.avionics_rack_temp_c,
            target.anomaly_detected = src.anomaly_detected,
            target.active_fault_code = src.active_fault_code,
            target.active_fault_title = src.active_fault_title,
            target.latitude = src.latitude,
            target.longitude = src.longitude,
            target.heading_deg = src.heading_deg,
            target.elapsed_flight_seconds = src.elapsed_flight_seconds,
            target.last_telemetry_ts = src.last_telemetry_ts,
            target.updated_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT (
            aircraft_id, flight_id, flight_number, origin, destination,
            current_phase, current_altitude_ft, current_speed_kts, outside_air_temp_c,
            avionics_fan_current_a, vibration_index, avionics_rack_temp_c,
            anomaly_detected, active_fault_code, active_fault_title, investigation_case_id,
            latitude, longitude, heading_deg, elapsed_flight_seconds, last_telemetry_ts, updated_at
        ) VALUES (
            src.aircraft_id, src.flight_id, src.flight_number, src.origin, src.destination,
            src.current_phase, src.current_altitude_ft, src.current_speed_kts, src.outside_air_temp_c,
            src.avionics_fan_current_a, src.vibration_index, src.avionics_rack_temp_c,
            src.anomaly_detected, src.active_fault_code, src.active_fault_title, src.investigation_case_id,
            src.latitude, src.longitude, src.heading_deg, src.elapsed_flight_seconds, src.last_telemetry_ts, CURRENT_TIMESTAMP()
        )
        """
        cs = self.conn.cursor()
        cs.execute(tracker_sql)
        cs.close()

        status_summary = {
            "time": now_ts.strftime('%H:%M:%S'),
            "tail": self.aircraft_id,
            "flight": self.flight_number,
            "phase": phase,
            "alt_ft": round(alt, 0),
            "oat_c": round(oat, 1),
            "fan_a": round(fan_current, 2),
            "vib": round(vib, 2),
            "anomaly": self.anomaly_detected,
            "fault": fault_code or "NONE"
        }
        return status_summary

    def close(self):
        if self.conn:
            self.conn.close()

def run_simulation(ticks: int = 10, speed: int = 30):
    print(f"Starting AeroResolve Live Replay Simulator ({ticks} ticks, speed {speed}x)...")
    sim = LiveFlightSimulator(aircraft_id="ABR-017", speed_multiplier=speed)
    try:
        for t in range(1, ticks + 1):
            stat = sim.step(real_interval_secs=1.0)
            print(f"[{t}/{ticks}] {stat['time']} | {stat['tail']} ({stat['flight']}) | Phase: {stat['phase']} | Alt: {stat['alt_ft']}ft | OAT: {stat['oat_c']}C | Fan: {stat['fan_a']}A | Vib: {stat['vib']} | Anomaly: {stat['anomaly']} | Fault: {stat['fault']}")
            time.sleep(1.0)
    finally:
        sim.close()
    print("Simulation batch completed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AeroResolve Live Flight Replay Simulator")
    parser.add_argument("--ticks", type=int, default=5, help="Number of real-time ticks to simulate")
    parser.add_argument("--speed", type=int, default=30, help="Simulation speed multiplier (1s real = Ns flight)")
    args = parser.parse_args()
    run_simulation(ticks=args.ticks, speed=args.speed)
