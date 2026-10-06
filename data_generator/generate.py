"""
AeroResolve Master Synthetic Data Generation & Loading Pipeline
Generates deterministic synthetic datasets for SMALL, DEMO, or LARGE profiles
and loads them into Snowflake with full referential and causal integrity.
"""

import os
import sys
import json
from datetime import datetime
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd

from data_generator.config import PROFILES, ProfileConfig
from data_generator.dimensions import generate_dimensions
from data_generator.operational import generate_operational_facts
from data_generator.telemetry import simulate_flight_telemetry
from data_generator.scenarios import SCENARIOS

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

def load_table(conn, schema: str, table_name: str, records: list):
    if not records:
        print(f"Skipping empty table {schema}.{table_name}")
        return 0

    df = pd.DataFrame(records)
    # Ensure all column names are uppercase matching Snowflake metadata
    df.columns = [c.upper() for c in df.columns]

    cursor = conn.cursor()
    # Truncate existing data to maintain idempotent runs
    cursor.execute(f"TRUNCATE TABLE IF EXISTS {schema}.{table_name}")
    
    # Fast bulk insert using write_pandas
    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name=table_name.upper(),
        schema=schema.upper(),
        auto_create_table=False,
        overwrite=False,
        quote_identifiers=False
    )
    cursor.close()
    print(f"Loaded {schema}.{table_name}: {nrows} rows (success={success})")
    return nrows

def run_pipeline(profile_name: str = "SMALL"):
    profile = PROFILES.get(profile_name.upper())
    if not profile:
        raise ValueError(f"Unknown profile: {profile_name}. Available: {list(PROFILES.keys())}")

    print(f"\n=======================================================")
    print(f"AERORESOLVE SYNTHETIC DATA GENERATOR: PROFILE={profile.profile_name}")
    print(f"Aircraft: {profile.num_aircraft} | History: {profile.history_days} days | Sample Interval: {profile.telemetry_sample_interval_secs}s")
    print(f"=======================================================\n")

    conn = get_snowflake_connection()

    # 1. Generate Dimensions
    print(">>> Generating Dimensions...")
    dims = generate_dimensions(profile)
    for t_name, rows in dims.items():
        load_table(conn, "CURATED", t_name, rows)

    # 2. Generate Operational Facts
    print("\n>>> Generating Operational Facts & Scenario Incidents...")
    facts = generate_operational_facts(dims, profile)
    for t_name, rows in facts.items():
        if rows:
            load_table(conn, "CURATED", t_name, rows)

    # 3. Generate Evaluation Ground-Truth Tables
    print("\n>>> Loading Private Evaluation Truth Tables...")
    scenario_truth_rows = []
    root_cause_truth_rows = []
    expected_action_rows = []
    expected_sequence_rows = []

    act_idx = 1
    seq_idx = 1
    for s in SCENARIOS:
        scenario_truth_rows.append({
            "scenario_id": s["scenario_id"],
            "scenario_name": s["scenario_name"],
            "aircraft_id": s["aircraft_id"],
            "target_flight_id": f"FL-DEMO-{s['aircraft_id']}",
            "injected_defect_type": s["injected_defect_type"],
            "true_root_cause": s["true_root_cause"],
            "environmental_trigger_envelope": json.dumps(s.get("environmental_trigger", {})),
            "is_ghost_fault": s["is_ghost_fault"],
            "prior_recurrence_count": s["prior_recurrence_count"],
            "expected_destination_station": s.get("expected_destination_station"),
            "expected_missing_part": s.get("expected_missing_part"),
            "expected_reposition_source": s.get("expected_reposition_source"),
            "healthy_control_case": s.get("healthy_control_case", False)
        })

        root_cause_truth_rows.append({
            "truth_id": f"TRUTH-{s['scenario_id']}",
            "scenario_id": s["scenario_id"],
            "aircraft_id": s["aircraft_id"],
            "primary_root_cause": s["true_root_cause"],
            "secondary_root_cause": None,
            "false_hypothesis": s.get("false_hypothesis", "N/A"),
            "why_false_hypothesis_fails": s.get("why_false_hypothesis_fails", "N/A")
        })

        for act in s.get("expected_agent_sequence", []):
            expected_action_rows.append({
                "expected_action_id": f"EXP-ACT-{act_idx:04d}",
                "scenario_id": s["scenario_id"],
                "step_order": act["order"],
                "expected_agent": act["agent"],
                "expected_action_type": act["action"],
                "min_acceptable_confidence": act["min_conf"]
            })
            act_idx += 1

            expected_sequence_rows.append({
                "sequence_id": f"EXP-SEQ-{seq_idx:04d}",
                "scenario_id": s["scenario_id"],
                "expected_tool_name": f"TOOL_{act['agent']}_{act['action']}",
                "sequence_order": act["order"],
                "is_mandatory": True
            })
            seq_idx += 1

    load_table(conn, "EVAL", "SCENARIO_TRUTH", scenario_truth_rows)
    load_table(conn, "EVAL", "ROOT_CAUSE_TRUTH", root_cause_truth_rows)
    load_table(conn, "EVAL", "EXPECTED_AGENT_ACTION", expected_action_rows)
    load_table(conn, "EVAL", "EXPECTED_TOOL_SEQUENCE", expected_sequence_rows)

    # 4. Generate Causal Telemetry
    print("\n>>> Generating Causal Wide Telemetry for Flights...")
    all_flights = facts["FACT_FLIGHTS"]
    priority_flights = [f for f in all_flights if f["aircraft_id"] in ["ABR-017", "ABR-042", "ABR-009"] or f["flight_status"] in ["AIRBORNE", "LANDED"]][:30]
    
    telemetry_records = []
    total_obs = 0
    for idx, fl in enumerate(priority_flights, 1):
        fl_telemetry = simulate_flight_telemetry(fl, sample_interval_secs=profile.telemetry_sample_interval_secs)
        telemetry_records.extend(fl_telemetry)
        total_obs += len(fl_telemetry)
        if idx % 10 == 0 or idx == len(priority_flights):
            print(f"Simulated telemetry for {idx}/{len(priority_flights)} sectors ({total_obs} rows generated)...")

    # Load Telemetry
    print(f"\nLoading {len(telemetry_records)} Telemetry rows into CURATED.FACT_TELEMETRY...")
    channels_per_row = 42
    total_sensor_measurements = len(telemetry_records) * channels_per_row
    print(f"Total Telemetry Rows: {len(telemetry_records):,}")
    print(f"Total Individual Sensor Measurements Represented: {total_sensor_measurements:,}")
    
    load_table(conn, "CURATED", "FACT_TELEMETRY", telemetry_records)

    # 5. Populate Active Ingestion Stream for Live Replay
    abr17_telemetry = [t for t in telemetry_records if t["aircraft_id"] == "ABR-017"][:60]
    if abr17_telemetry:
        load_table(conn, "RAW", "RAW_TELEMETRY_STREAM", abr17_telemetry)

    print("\n>>> Running Post-Load Integrity Assertions...")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.DIM_AIRCRAFT")
    ac_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_FLIGHTS")
    fl_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_TELEMETRY")
    te_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY WHERE quantity_on_hand < 0")
    neg_inv = cursor.fetchone()[0]
    cursor.execute("SELECT quantity_on_hand FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY WHERE station_code = 'DEL' AND part_number = 'PART-X42-CONN'")
    del_stock = cursor.fetchone()[0]
    cursor.execute("SELECT quantity_on_hand FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY WHERE station_code = 'BOM' AND part_number = 'PART-X42-CONN'")
    bom_stock = cursor.fetchone()[0]

    print(f"Integrity check:")
    print(f" - Aircraft: {ac_cnt}")
    print(f" - Flights: {fl_cnt}")
    print(f" - Telemetry Rows: {te_cnt}")
    print(f" - Negative Inventory Assertions: {neg_inv} (Must be 0)")
    print(f" - DEL Stock for PART-X42-CONN: {del_stock} (Must be 0)")
    print(f" - BOM Stock for PART-X42-CONN: {bom_stock} (Must be 3)")

    assert neg_inv == 0, "Integrity failure: negative inventory found!"
    assert del_stock == 0, "Scenario failure: DEL stock must be 0!"
    assert bom_stock == 3, "Scenario failure: BOM stock must be 3!"
    print("\nALL POST-LOAD INTEGRITY CHECKS PASSED PERFECTLY!\n")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    prof = "SMALL"
    if len(sys.argv) > 1:
        prof = sys.argv[1]
    run_pipeline(prof)
