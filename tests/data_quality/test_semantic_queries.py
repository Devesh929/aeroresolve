"""
tests/data_quality/test_semantic_queries.py
Validation of Snowflake Semantic Layer views and the 7 Verified Gold Queries.
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
        database='AERORESOLVE',
        schema='SEMANTIC'
    )
    yield conn
    conn.close()

def test_semantic_views_exist(sf_conn):
    """Ensure all core semantic views exist in schema SEMANTIC."""
    cur = sf_conn.cursor()
    cur.execute("SHOW VIEWS IN SCHEMA AERORESOLVE.SEMANTIC")
    views = [row[1] for row in cur.fetchall()]
    
    expected_views = [
        "SEM_FLEET_AIRCRAFT",
        "SEM_FLIGHT_OPERATIONS",
        "SEM_FAULT_HISTORY",
        "SEM_MAINTENANCE_ACTIONS",
        "SEM_SPARE_PARTS_INVENTORY",
        "SEM_STATION_CAPABILITY",
        "SEM_AIRCRAFT_ROTATION",
        "V_VERIFIED_FLEET_REPEAT_DEFECT_RATE_30D",
        "V_VERIFIED_ABR017_ATA21_HISTORY",
        "V_VERIFIED_ACTIVE_INFLIGHT_FAULT_SIGNATURES",
        "V_VERIFIED_DEL_TONIGHT_ATA21_CAPABILITY",
        "V_VERIFIED_PART_X42_CONN_STOCK_AND_TRANSIT",
        "V_VERIFIED_ABR017_DOWNSTREAM_ROTATION_24H",
        "V_VERIFIED_RECURRING_FAULTS_AFTER_REPAIR_60D"
    ]
    for ev in expected_views:
        assert ev in views, f"Expected view {ev} not found in SEMANTIC schema"

def test_query_1_fleet_repeat_defect_rate(sf_conn):
    """Query 1: What is the fleet repeat-defect rate over the last 30 days?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_FLEET_REPEAT_DEFECT_RATE_30D")
    row = cur.fetchone()
    assert row is not None
    repeat_count, total_actions, repeat_pct = row
    assert total_actions >= 0
    if total_actions > 0:
        assert 0.0 <= repeat_pct <= 100.0

def test_query_2_abr017_ata21_history(sf_conn):
    """Query 2: What are all previous occurrences of ATA 21 faults on ABR-017?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_ATA21_HISTORY")
    rows = cur.fetchall()
    assert len(rows) > 0, "ABR-017 should have historical ATA 21 fault events"
    for r in rows:
        aircraft_id = r[1]
        ata_chapter = r[5]
        assert aircraft_id == "ABR-017"
        assert ata_chapter == "21"

def test_query_3_active_inflight_signatures(sf_conn):
    """Query 3: Which aircraft flying right now have active fault signatures?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_ACTIVE_INFLIGHT_FAULT_SIGNATURES")
    rows = cur.fetchall()
    # In SMALL profile flight FL-20261006-017-0060 is AIRBORNE with fault event
    assert len(rows) >= 1
    found_abr017 = any(r[2] == "ABR-017" for r in rows)
    assert found_abr017, "ABR-017 should be an active airborne flight with fault signature"

def test_query_4_del_tonight_capability(sf_conn):
    """Query 4: What is the maintenance capability at DEL tonight for ATA 21 cooling loop repairs?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_DEL_TONIGHT_ATA21_CAPABILITY")
    row = cur.fetchone()
    assert row is not None
    station_code = row[0]
    ata_chapter = row[3]
    cap_level = row[4]
    engineers = row[7]
    assert station_code == "DEL"
    assert ata_chapter == "21"
    assert cap_level in ("COMPONENT_REPLACE", "OVERHAUL", "LINE_REPLACE")
    assert engineers > 0

def test_query_5_part_x42_conn_stock_and_transit(sf_conn):
    """Query 5: Where is part PART-X42-CONN currently stocked, and what are transit times to DEL?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_PART_X42_CONN_STOCK_AND_TRANSIT")
    rows = cur.fetchall()
    assert len(rows) > 0
    
    # Check that DEL has 0 on hand, and BOM has >= 3 on hand
    del_row = [r for r in rows if r[0] == "DEL"][0]
    bom_row = [r for r in rows if r[0] == "BOM"][0]
    assert del_row[4] == 0, "DEL stock of PART-X42-CONN must be 0"
    assert bom_row[4] >= 3, "BOM physical stock on hand of PART-X42-CONN must be at least 3"
    assert bom_row[6] >= 0, "BOM available unreserved stock must be >= 0"
    assert bom_row[7] > 0, "BOM to DEL transit time must be positive"

def test_query_6_abr017_downstream_rotation(sf_conn):
    """Query 6: What downstream flights are operated by ABR-017 in the next 24 hours?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_DOWNSTREAM_ROTATION_24H")
    rows = cur.fetchall()
    assert len(rows) >= 3, "ABR-017 should have multiple downstream sectors"
    first_downstream = rows[0]
    assert first_downstream[4] == "DEL" or first_downstream[5] == "DEL", "Next sector departs from or arrives into DEL"

def test_query_7_recurring_faults_after_repair(sf_conn):
    """Query 7: Which repairs in the last 60 days were followed by recurring faults within 3 flights?"""
    cur = sf_conn.cursor()
    cur.execute("SELECT * FROM AERORESOLVE.SEMANTIC.V_VERIFIED_RECURRING_FAULTS_AFTER_REPAIR_60D")
    rows = cur.fetchall()
    # Must return repeat defect records
    for r in rows:
        assert r[10] is True, "is_repeat_defect must be True"
