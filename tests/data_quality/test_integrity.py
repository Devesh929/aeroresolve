"""
Data Quality and Referential Integrity Tests against Snowflake
Validates that synthetic data adheres to real-world aviation database constraints.
"""

import os
import pytest
import snowflake.connector

@pytest.fixture(scope="module")
def sf_conn():
    token_path = os.path.expanduser('~/.snowflake/token.jwt')
    conn = snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE'
    )
    yield conn
    conn.close()

def test_aircraft_fleet_loaded(sf_conn):
    cs = sf_conn.cursor()
    cs.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.DIM_AIRCRAFT")
    cnt = cs.fetchone()[0]
    assert cnt >= 12, "Fleet size should be at least 12 aircraft"
    
    # Verify ABR-017 exists
    cs.execute("SELECT aircraft_id, current_status FROM AERORESOLVE.CURATED.DIM_AIRCRAFT WHERE aircraft_id = 'ABR-017'")
    row = cs.fetchone()
    assert row is not None, "Target demo aircraft ABR-017 must exist"
    assert row[1] == 'DEGRADED', "ABR-017 status should be DEGRADED"
    cs.close()

def test_no_orphan_flights(sf_conn):
    cs = sf_conn.cursor()
    cs.execute("""
        SELECT COUNT(*) 
        FROM AERORESOLVE.CURATED.FACT_FLIGHTS f
        LEFT JOIN AERORESOLVE.CURATED.DIM_AIRCRAFT a ON f.aircraft_id = a.aircraft_id
        WHERE a.aircraft_id IS NULL
    """)
    orphan_cnt = cs.fetchone()[0]
    assert orphan_cnt == 0, "Found orphan flights with no valid aircraft_id"
    cs.close()

def test_part_inventory_integrity(sf_conn):
    cs = sf_conn.cursor()
    # No negative stock
    cs.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY WHERE quantity_on_hand < 0")
    neg_cnt = cs.fetchone()[0]
    assert neg_cnt == 0, "No negative inventory allowed"

    # Scenario 4 stock assertions
    cs.execute("SELECT quantity_on_hand FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY WHERE station_code = 'DEL' AND part_number = 'PART-X42-CONN'")
    del_qty = cs.fetchone()[0]
    assert del_qty == 0, "DEL stock for connector X42 must be 0"

    cs.execute("SELECT quantity_on_hand FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY WHERE station_code = 'BOM' AND part_number = 'PART-X42-CONN'")
    bom_qty = cs.fetchone()[0]
    assert bom_qty == 3, "BOM stock for connector X42 must be 3"
    cs.close()

def test_telemetry_wide_columns(sf_conn):
    cs = sf_conn.cursor()
    cs.execute("SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_TELEMETRY")
    cnt = cs.fetchone()[0]
    assert cnt > 5000, "Should have several thousand telemetry records"

    # Verify sensor values are within non-null physical bounds
    cs.execute("""
        SELECT 
            MIN(altitude_ft), MAX(altitude_ft),
            MIN(outside_air_temp_c), MAX(outside_air_temp_c),
            MIN(avionics_fan_current_a), MAX(avionics_fan_current_a)
        FROM AERORESOLVE.CURATED.FACT_TELEMETRY
    """)
    row = cs.fetchone()
    min_alt, max_alt, min_temp, max_temp, min_fan, max_fan = row
    assert min_alt >= 500.0, f"Unreasonable min altitude: {min_alt}"
    assert max_alt <= 41000.0, f"Unreasonable max altitude: {max_alt}"
    assert min_temp <= -30.0, f"Cruise temperature should be subzero: {min_temp}"
    assert min_fan > 2.0 and max_fan < 10.0, f"Fan current out of range: {min_fan}-{max_fan}"
    cs.close()

def test_scenario_ground_truth_loaded(sf_conn):
    cs = sf_conn.cursor()
    cs.execute("SELECT COUNT(*) FROM AERORESOLVE.EVAL.SCENARIO_TRUTH")
    cnt = cs.fetchone()[0]
    assert cnt == 8, f"Expected 8 ground truth scenarios, got {cnt}"

    cs.execute("SELECT true_root_cause FROM AERORESOLVE.EVAL.SCENARIO_TRUTH WHERE scenario_id = 'SCEN-01-GHOST-FAULT'")
    cause = cs.fetchone()[0]
    assert "micro-fretting" in cause.lower() or "connector" in cause.lower()
    cs.close()
