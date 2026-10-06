"""
Unit tests for AeroResolve synthetic data generation logic and causal dynamics.
"""

import pytest
from data_generator.config import PROFILES, STATIONS, COMPONENT_TYPES
from data_generator.dimensions import generate_dimensions
from data_generator.telemetry import simulate_flight_telemetry
from data_generator.scenarios import SCENARIOS

def test_profiles_defined():
    assert "SMALL" in PROFILES
    assert "DEMO" in PROFILES
    assert "LARGE" in PROFILES
    assert "XL" in PROFILES
    assert PROFILES["SMALL"].num_aircraft == 12
    assert PROFILES["DEMO"].num_aircraft == 25

def test_deterministic_dimensions():
    dim1 = generate_dimensions(PROFILES["SMALL"])
    dim2 = generate_dimensions(PROFILES["SMALL"])
    
    # Assert exact determinism with seed
    assert len(dim1["DIM_AIRCRAFT"]) == len(dim2["DIM_AIRCRAFT"])
    assert dim1["DIM_AIRCRAFT"][0]["aircraft_id"] == dim2["DIM_AIRCRAFT"][0]["aircraft_id"]
    assert any(a["aircraft_id"] == "ABR-017" for a in dim1["DIM_AIRCRAFT"])
    assert any(a["aircraft_id"] == "ABR-042" for a in dim1["DIM_AIRCRAFT"])

def test_scenarios_coverage():
    # Must have all 8 deterministic scenarios
    assert len(SCENARIOS) == 8
    scen_ids = [s["scenario_id"] for s in SCENARIOS]
    assert "SCEN-01-GHOST-FAULT" in scen_ids
    assert "SCEN-02-REPEAT-DEFECT" in scen_ids
    assert "SCEN-03-SILENT-DEGRADATION" in scen_ids
    assert "SCEN-04-DESTINATION-NOT-READY" in scen_ids
    assert "SCEN-05-NETWORK-BLAST-RADIUS" in scen_ids
    assert "SCEN-06-REPAIR-VERIFICATION" in scen_ids
    assert "SCEN-07-FLEET-LEARNING" in scen_ids
    assert "SCEN-08-HEALTHY-CONTROL" in scen_ids

def test_causal_telemetry_physics():
    fake_flight = {
        "flight_id": "FL-TEST-001",
        "flight_number": "AB-402",
        "aircraft_id": "ABR-017",
        "scheduled_departure_ts": "2026-10-06 10:00:00",
        "scheduled_flight_time_mins": 90
    }
    telemetry = simulate_flight_telemetry(fake_flight, sample_interval_secs=30)
    assert len(telemetry) > 50

    phases = [t["flight_phase"] for t in telemetry]
    assert "TAXI_OUT" in phases
    assert "TAKEOFF" in phases
    assert "CLIMB" in phases
    assert "CRUISE" in phases
    assert "DESCENT" in phases
    assert "LANDING" in phases

    # Test causal temperature correlation with altitude
    cruise_obs = [t for t in telemetry if t["flight_phase"] == "CRUISE"]
    ground_obs = [t for t in telemetry if t["flight_phase"] in ["TAXI_OUT", "TAXI_IN"]]
    
    assert cruise_obs[0]["altitude_ft"] > 30000
    assert cruise_obs[0]["outside_air_temp_c"] < -35.0  # Cold at altitude
    assert ground_obs[0]["outside_air_temp_c"] > 15.0   # Warm on ground
