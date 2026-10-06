"""
AeroResolve Data Generator Configuration
Contains fleet profiles, station coordinates, components, and deterministic seeds.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

RANDOM_SEED = 42

@dataclass
class ProfileConfig:
    profile_name: str
    num_aircraft: int
    history_days: int
    sectors_per_day_range: Tuple[int, int]
    telemetry_sample_interval_secs: int
    wide_sensors_count: int

PROFILES: Dict[str, ProfileConfig] = {
    "SMALL": ProfileConfig(
        profile_name="SMALL",
        num_aircraft=12,
        history_days=7,
        sectors_per_day_range=(3, 4),
        telemetry_sample_interval_secs=30,
        wide_sensors_count=45
    ),
    "DEMO": ProfileConfig(
        profile_name="DEMO",
        num_aircraft=25,
        history_days=30,
        sectors_per_day_range=(4, 5),
        telemetry_sample_interval_secs=15,
        wide_sensors_count=45
    ),
    "LARGE": ProfileConfig(
        profile_name="LARGE",
        num_aircraft=160,
        history_days=365,
        sectors_per_day_range=(5, 6),
        telemetry_sample_interval_secs=5,
        wide_sensors_count=60
    ),
    "XL": ProfileConfig(
        profile_name="XL",
        num_aircraft=250,
        history_days=730,
        sectors_per_day_range=(6, 7),
        telemetry_sample_interval_secs=5,
        wide_sensors_count=80
    ),
}

AIRLINE_CODE = "AB"
AIRLINE_NAME = "AeroBharat Airlines"

STATIONS = [
    {"code": "DEL", "name": "Indira Gandhi International", "city": "Delhi", "country": "IND", "is_hub": True, "tier": 3, "avionics": True, "engine": True, "lat": 28.5562, "lon": 77.1000},
    {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj International", "city": "Mumbai", "country": "IND", "is_hub": True, "tier": 3, "avionics": True, "engine": True, "lat": 19.0896, "lon": 72.8656},
    {"code": "BLR", "name": "Kempegowda International", "city": "Bengaluru", "country": "IND", "is_hub": True, "tier": 3, "avionics": True, "engine": True, "lat": 13.1986, "lon": 77.7066},
    {"code": "HYD", "name": "Rajiv Gandhi International", "city": "Hyderabad", "country": "IND", "is_hub": True, "tier": 2, "avionics": True, "engine": False, "lat": 17.2403, "lon": 78.4294},
    {"code": "MAA", "name": "Chennai International", "city": "Chennai", "country": "IND", "is_hub": True, "tier": 2, "avionics": True, "engine": False, "lat": 12.9941, "lon": 80.1709},
    {"code": "CCU", "name": "Netaji Subhash Chandra Bose International", "city": "Kolkata", "country": "IND", "is_hub": True, "tier": 2, "avionics": True, "engine": False, "lat": 22.6547, "lon": 88.4467},
    {"code": "PNQ", "name": "Pune Airport", "city": "Pune", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 18.5822, "lon": 73.9197},
    {"code": "AMD", "name": "Sardar Vallabhbhai Patel International", "city": "Ahmedabad", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 23.0772, "lon": 72.6347},
    {"code": "COK", "name": "Cochin International", "city": "Kochi", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 10.1520, "lon": 76.3922},
    {"code": "GOI", "name": "Dabolim / Manohar International", "city": "Goa", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 15.3808, "lon": 73.8314},
    {"code": "JAI", "name": "Jaipur International", "city": "Jaipur", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 26.8242, "lon": 75.8122},
    {"code": "LKO", "name": "Chaudhary Charan Singh International", "city": "Lucknow", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 26.7606, "lon": 80.8893},
    {"code": "GAU", "name": "Lokpriya Gopinath Bordoloi International", "city": "Guwahati", "country": "IND", "is_hub": False, "tier": 1, "avionics": False, "engine": False, "lat": 26.1061, "lon": 91.5859},
    {"code": "DXB", "name": "Dubai International", "city": "Dubai", "country": "ARE", "is_hub": False, "tier": 2, "avionics": True, "engine": False, "lat": 25.2532, "lon": 55.3657},
    {"code": "SIN", "name": "Singapore Changi Airport", "city": "Singapore", "country": "SGP", "is_hub": False, "tier": 2, "avionics": True, "engine": False, "lat": 1.3644, "lon": 103.9915},
    {"code": "BKK", "name": "Suvarnabhumi International", "city": "Bangkok", "country": "THA", "is_hub": False, "tier": 2, "avionics": True, "engine": False, "lat": 13.6900, "lon": 100.7501},
]

AIRCRAFT_TYPES = [
    {
        "aircraft_type_id": "AB-320N",
        "model_name": "AeroBharat 320 Neo-Family",
        "manufacturer": "Bharat Aerospace Consortium",
        "engine_type": "LEAP-1A26 Turbofan",
        "seating_capacity": 186,
        "max_range_nm": 3400,
        "ceiling_altitude_ft": 39000
    },
    {
        "aircraft_type_id": "AB-321N",
        "model_name": "AeroBharat 321 Neo-Family",
        "manufacturer": "Bharat Aerospace Consortium",
        "engine_type": "LEAP-1A32 Turbofan",
        "seating_capacity": 222,
        "max_range_nm": 4000,
        "ceiling_altitude_ft": 39000
    }
]

COMPONENT_TYPES = [
    {"component_type_id": "AV-COMP-01", "ata_chapter": "21", "description": "Avionics Ventilation & Cooling Computer (AVCC)", "criticality_tier": "NO-GO", "mean_time_between_unscheduled_removal_hrs": 4200.0},
    {"component_type_id": "AV-FAN-01",  "ata_chapter": "21", "description": "Avionics Extract Cooling Blower Fan", "criticality_tier": "NO-GO", "mean_time_between_unscheduled_removal_hrs": 3600.0},
    {"component_type_id": "WIR-HARN-21", "ata_chapter": "21", "description": "Avionics Bay Temperature Sensor & Ground Wiring Harness", "criticality_tier": "NO-GO", "mean_time_between_unscheduled_removal_hrs": 12000.0},
    {"component_type_id": "ENG-FADEC-01", "ata_chapter": "73", "description": "Full Authority Digital Engine Control Unit", "criticality_tier": "NO-GO", "mean_time_between_unscheduled_removal_hrs": 8500.0},
    {"component_type_id": "HYD-PUMP-01",  "ata_chapter": "29", "description": "Engine Driven Hydraulic Pump (Green System)", "criticality_tier": "NO-GO", "mean_time_between_unscheduled_removal_hrs": 5100.0},
    {"component_type_id": "BLEED-VALVE-01", "ata_chapter": "36", "description": "High Pressure Pneumatic Bleed Air Valve", "criticality_tier": "GO-IF", "mean_time_between_unscheduled_removal_hrs": 4800.0},
    {"component_type_id": "ELEC-GEN-01",  "ata_chapter": "24", "description": "Integrated Drive Generator (IDG)", "criticality_tier": "NO-GO", "mean_time_between_unscheduled_removal_hrs": 6000.0},
]

FAULT_CODES = [
    {"fault_code": "FAULT-21-204", "ata_chapter": "21", "fault_title": "Avionics Cooling Low Flow Warning", "fault_description": "Low airflow sensor threshold reached in avionics extraction duct at cruise", "severity": "WARNING", "mel_reference": "21-26-01", "requires_ground_isolation": True},
    {"fault_code": "FAULT-21-209", "ata_chapter": "21", "fault_title": "Avionics Equipment Bay Overheat", "fault_description": "Avionics bay ambient temperature exceeding continuous rating limit", "severity": "CRITICAL", "mel_reference": "NO-GO", "requires_ground_isolation": True},
    {"fault_code": "FAULT-24-101", "ata_chapter": "24", "fault_title": "AC Bus 1 Voltage Transitory Spike", "fault_description": "Transient voltage instability on Main AC Bus 1", "severity": "WARNING", "mel_reference": "24-21-01", "requires_ground_isolation": False},
    {"fault_code": "FAULT-36-302", "ata_chapter": "36", "fault_title": "Bleed Air Overpressure Left Engine", "fault_description": "Pneumatic regulator hunting leading to pressure fluctuation", "severity": "WARNING", "mel_reference": "36-11-02", "requires_ground_isolation": False},
    {"fault_code": "FAULT-29-105", "ata_chapter": "29", "fault_title": "Green Hydraulic Low Pressure Transitory", "fault_description": "Pressure transducer signal intermittent during rapid climb", "severity": "ADVISORY", "mel_reference": "29-31-01", "requires_ground_isolation": True},
]

PARTS = [
    {"part_number": "PART-X42-CONN", "component_type_id": "WIR-HARN-21", "part_name": "Connector Kit X42 Harness Repair Set", "standard_unit_cost_inr": 18500.0, "lead_time_hours": 4.0, "weight_kg": 1.2},
    {"part_number": "PART-AVC-902",   "component_type_id": "AV-COMP-01",  "part_name": "Avionics Cooling Computer Unit", "standard_unit_cost_inr": 420000.0, "lead_time_hours": 18.0, "weight_kg": 8.5},
    {"part_number": "PART-AVF-881",   "component_type_id": "AV-FAN-01",   "part_name": "Avionics Extraction Fan Assembly", "standard_unit_cost_inr": 165000.0, "lead_time_hours": 12.0, "weight_kg": 6.8},
    {"part_number": "PART-BLD-401",   "component_type_id": "BLEED-VALVE-01", "part_name": "Pneumatic Regulation Valve Assembly", "standard_unit_cost_inr": 95000.0, "lead_time_hours": 16.0, "weight_kg": 12.0},
    {"part_number": "PART-HYD-505",   "component_type_id": "HYD-PUMP-01",  "part_name": "Hydraulic Pump Seal & Coupling Kit", "standard_unit_cost_inr": 48000.0, "lead_time_hours": 8.0, "weight_kg": 4.5},
]

MAINTENANCE_ACTIONS = [
    {"action_type_id": "ACT-RESET-COMP", "action_category": "RESET", "description": "Avionics Computer BITE Reset and Power Cycle", "estimated_duration_mins": 25, "skill_level_required": "B2_AVIONICS"},
    {"action_type_id": "ACT-SWAP-COMP",  "action_category": "SWAP",  "description": "Replace Avionics Cooling Computer Unit", "estimated_duration_mins": 90, "skill_level_required": "B2_AVIONICS"},
    {"action_type_id": "ACT-INSP-HARN",  "action_category": "INSPECT", "description": "Inspect Wiring Harness & Connector Pin Tension (Tool T14)", "estimated_duration_mins": 60, "skill_level_required": "B2_AVIONICS"},
    {"action_type_id": "ACT-REPAIR-HARN", "action_category": "HARNESS_REPAIR", "description": "Replace Connector Kit X42 and Re-pin Harness", "estimated_duration_mins": 85, "skill_level_required": "B2_AVIONICS"},
    {"action_type_id": "ACT-SWAP-FAN",   "action_category": "SWAP",  "description": "Remove and Replace Avionics Extract Fan Assembly", "estimated_duration_mins": 110, "skill_level_required": "B2_AVIONICS"},
    {"action_type_id": "ACT-CLEAN-DUCT", "action_category": "CLEAN", "description": "Clean and Inspect Extraction Duct & Filter Mesh", "estimated_duration_mins": 40, "skill_level_required": "B1_MECHANICAL"},
]
