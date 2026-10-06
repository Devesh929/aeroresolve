-- =====================================================================
-- AeroResolve: 02_create_tables.sql
-- Idempotent Core DDL for Dimensions, Facts, Raw Streams, Evaluation, Audit
-- =====================================================================

USE ROLE AERORESOLVE_DEV;
USE WAREHOUSE AERORESOLVE_WH;
USE DATABASE AERORESOLVE;

-- ---------------------------------------------------------------------
-- 1. BASE INDEPENDENT DIMENSIONS (AERORESOLVE.CURATED)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_AIRCRAFT_TYPE (
    aircraft_type_id VARCHAR(50) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    engine_type VARCHAR(100) NOT NULL,
    seating_capacity INT NOT NULL,
    max_range_nm INT NOT NULL,
    ceiling_altitude_ft INT NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_STATION (
    station_code VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(10) NOT NULL,
    is_hub BOOLEAN NOT NULL DEFAULT FALSE,
    maintenance_tier INT NOT NULL,
    has_avionics_shop BOOLEAN NOT NULL DEFAULT FALSE,
    has_engine_shop BOOLEAN NOT NULL DEFAULT FALSE,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_ROUTE (
    route_id VARCHAR(50) PRIMARY KEY,
    origin_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    dest_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    scheduled_flight_time_mins INT NOT NULL,
    distance_nm INT NOT NULL,
    route_type VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_COMPONENT_TYPE (
    component_type_id VARCHAR(50) PRIMARY KEY,
    ata_chapter VARCHAR(10) NOT NULL,
    description VARCHAR(255) NOT NULL,
    criticality_tier VARCHAR(20) NOT NULL,
    mean_time_between_unscheduled_removal_hrs FLOAT
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_FAULT_CODE (
    fault_code VARCHAR(50) PRIMARY KEY,
    ata_chapter VARCHAR(10) NOT NULL,
    fault_title VARCHAR(255) NOT NULL,
    fault_description VARCHAR(1000),
    severity VARCHAR(20) NOT NULL,
    mel_reference VARCHAR(50),
    requires_ground_isolation BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_MAINTENANCE_ACTION (
    action_type_id VARCHAR(50) PRIMARY KEY,
    action_category VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL,
    estimated_duration_mins INT NOT NULL,
    skill_level_required VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_PASSENGER_SEGMENT (
    segment_type VARCHAR(50) PRIMARY KEY,
    description VARCHAR(100) NOT NULL,
    high_value_priority INT NOT NULL
);

-- ---------------------------------------------------------------------
-- 2. DEPENDENT ENTITY DIMENSIONS (AERORESOLVE.CURATED)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_AIRCRAFT (
    aircraft_id VARCHAR(50) PRIMARY KEY,
    aircraft_type_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT_TYPE(aircraft_type_id),
    serial_number VARCHAR(100) NOT NULL,
    delivery_date DATE NOT NULL,
    home_base VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    total_flight_hours FLOAT NOT NULL DEFAULT 0.0,
    total_flight_cycles INT NOT NULL DEFAULT 0,
    current_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    last_c_check_date DATE
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_COMPONENT_SERIAL (
    serial_number VARCHAR(100) PRIMARY KEY,
    component_type_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_COMPONENT_TYPE(component_type_id),
    manufacture_date DATE NOT NULL,
    accumulated_hours FLOAT NOT NULL DEFAULT 0.0,
    accumulated_cycles INT NOT NULL DEFAULT 0,
    current_health_score FLOAT NOT NULL DEFAULT 100.0,
    installed_aircraft_id VARCHAR(50) REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    status VARCHAR(50) NOT NULL DEFAULT 'INSTALLED'
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_ENGINEER (
    engineer_id VARCHAR(50) PRIMARY KEY,
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    name VARCHAR(100) NOT NULL,
    license_type VARCHAR(50) NOT NULL,
    certified_aircraft_type VARCHAR(50) NOT NULL,
    years_experience INT NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_TOOL (
    tool_id VARCHAR(50) PRIMARY KEY,
    tool_code VARCHAR(50) NOT NULL,
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    description VARCHAR(255) NOT NULL,
    calibration_status VARCHAR(50) NOT NULL DEFAULT 'VALID',
    is_serviceable BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.DIM_PART (
    part_number VARCHAR(50) PRIMARY KEY,
    component_type_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_COMPONENT_TYPE(component_type_id),
    part_name VARCHAR(150) NOT NULL,
    standard_unit_cost_inr FLOAT NOT NULL,
    lead_time_hours FLOAT NOT NULL,
    weight_kg FLOAT NOT NULL
);

-- ---------------------------------------------------------------------
-- 3. OPERATIONAL FACTS (AERORESOLVE.CURATED)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_FLIGHTS (
    flight_id VARCHAR(50) PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    route_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_ROUTE(route_id),
    origin_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    dest_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    scheduled_departure_ts TIMESTAMP_NTZ NOT NULL,
    actual_departure_ts TIMESTAMP_NTZ,
    scheduled_arrival_ts TIMESTAMP_NTZ NOT NULL,
    actual_arrival_ts TIMESTAMP_NTZ,
    flight_status VARCHAR(50) NOT NULL DEFAULT 'SCHEDULED',
    passenger_count INT NOT NULL DEFAULT 160,
    connecting_passenger_count INT NOT NULL DEFAULT 35,
    delay_departure_minutes INT NOT NULL DEFAULT 0,
    delay_arrival_minutes INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_TELEMETRY (
    flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    event_ts TIMESTAMP_NTZ NOT NULL,
    flight_phase VARCHAR(30) NOT NULL,
    altitude_ft FLOAT NOT NULL,
    airspeed_kts FLOAT NOT NULL,
    outside_air_temp_c FLOAT NOT NULL,
    cabin_altitude_ft FLOAT NOT NULL,
    engine_1_n1 FLOAT NOT NULL,
    engine_2_n1 FLOAT NOT NULL,
    engine_1_egt_c FLOAT NOT NULL,
    engine_2_egt_c FLOAT NOT NULL,
    engine_1_n2 FLOAT NOT NULL,
    engine_2_n2 FLOAT NOT NULL,
    fuel_flow_1_kgh FLOAT NOT NULL,
    fuel_flow_2_kgh FLOAT NOT NULL,
    oil_pressure_1_psi FLOAT NOT NULL,
    oil_pressure_2_psi FLOAT NOT NULL,
    oil_temp_1_c FLOAT NOT NULL,
    oil_temp_2_c FLOAT NOT NULL,
    avionics_fan_current_a FLOAT NOT NULL,
    avionics_rack_temp_c FLOAT NOT NULL,
    vibration_index FLOAT NOT NULL,
    elec_bus_voltage_v FLOAT NOT NULL,
    battery_voltage_v FLOAT NOT NULL,
    generator_1_load_pct FLOAT NOT NULL,
    generator_2_load_pct FLOAT NOT NULL,
    apu_generator_load_pct FLOAT NOT NULL,
    pack_1_temp_c FLOAT NOT NULL,
    pack_2_temp_c FLOAT NOT NULL,
    pack_1_flow_kgs FLOAT NOT NULL,
    pack_2_flow_kgs FLOAT NOT NULL,
    bleed_1_pressure_psi FLOAT NOT NULL,
    bleed_2_pressure_psi FLOAT NOT NULL,
    cabin_differential_pressure_psi FLOAT NOT NULL,
    hydraulic_press_green_psi FLOAT NOT NULL,
    hydraulic_press_blue_psi FLOAT NOT NULL,
    hydraulic_press_yellow_psi FLOAT NOT NULL,
    hydraulic_quantity_green_pct FLOAT NOT NULL,
    brake_temp_left_c FLOAT NOT NULL,
    brake_temp_right_c FLOAT NOT NULL,
    flap_position_deg FLOAT NOT NULL,
    slat_position_deg FLOAT NOT NULL,
    rudder_trim_deg FLOAT NOT NULL,
    pitch_angle_deg FLOAT NOT NULL,
    roll_angle_deg FLOAT NOT NULL,
    vertical_speed_fpm FLOAT NOT NULL,
    PRIMARY KEY (aircraft_id, event_ts)
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_ACARS_MESSAGES (
    message_id VARCHAR(50) PRIMARY KEY,
    flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    message_ts TIMESTAMP_NTZ NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    fault_code VARCHAR(50) REFERENCES AERORESOLVE.CURATED.DIM_FAULT_CODE(fault_code),
    raw_message_text VARCHAR(1000) NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_FAULT_EVENTS (
    fault_event_id VARCHAR(50) PRIMARY KEY,
    flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    fault_code VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_FAULT_CODE(fault_code),
    event_ts TIMESTAMP_NTZ NOT NULL,
    flight_phase VARCHAR(30) NOT NULL,
    altitude_ft FLOAT NOT NULL,
    outside_air_temp_c FLOAT NOT NULL,
    vibration_index FLOAT NOT NULL,
    avionics_fan_current_a FLOAT NOT NULL,
    is_intermittent BOOLEAN NOT NULL DEFAULT FALSE,
    normalized_on_ground BOOLEAN NOT NULL DEFAULT FALSE,
    severity VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_TECH_LOG (
    tech_log_id VARCHAR(50) PRIMARY KEY,
    flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    logged_ts TIMESTAMP_NTZ NOT NULL,
    defect_description VARCHAR(2000) NOT NULL,
    logged_by VARCHAR(100) NOT NULL,
    rectification_status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    mel_reference VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_WORK_ORDERS (
    work_order_id VARCHAR(50) PRIMARY KEY,
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    fault_event_id VARCHAR(50) REFERENCES AERORESOLVE.CURATED.FACT_FAULT_EVENTS(fault_event_id),
    created_ts TIMESTAMP_NTZ NOT NULL,
    scheduled_start_ts TIMESTAMP_NTZ NOT NULL,
    completed_ts TIMESTAMP_NTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    lead_engineer_id VARCHAR(50) REFERENCES AERORESOLVE.CURATED.DIM_ENGINEER(engineer_id)
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_MAINTENANCE_ACTIONS (
    action_id VARCHAR(50) PRIMARY KEY,
    work_order_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_WORK_ORDERS(work_order_id),
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    performed_ts TIMESTAMP_NTZ NOT NULL,
    action_type_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_MAINTENANCE_ACTION(action_type_id),
    component_type_id VARCHAR(50) REFERENCES AERORESOLVE.CURATED.DIM_COMPONENT_TYPE(component_type_id),
    part_number_used VARCHAR(50) REFERENCES AERORESOLVE.CURATED.DIM_PART(part_number),
    action_notes VARCHAR(2000) NOT NULL,
    is_repeat_defect BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_interval_days FLOAT
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_COMPONENT_INSTALL_REMOVAL (
    movement_id VARCHAR(50) PRIMARY KEY,
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    serial_number VARCHAR(100) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_COMPONENT_SERIAL(serial_number),
    movement_type VARCHAR(20) NOT NULL,
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    movement_ts TIMESTAMP_NTZ NOT NULL,
    hours_at_movement FLOAT NOT NULL,
    cycles_at_movement INT NOT NULL,
    reason VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_PART_INVENTORY (
    inventory_id VARCHAR(50) PRIMARY KEY,
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    part_number VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_PART(part_number),
    quantity_on_hand INT NOT NULL DEFAULT 0,
    quantity_reserved INT NOT NULL DEFAULT 0,
    minimum_safety_stock INT NOT NULL DEFAULT 1,
    last_updated_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_PART_MOVEMENTS (
    movement_id VARCHAR(50) PRIMARY KEY,
    part_number VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_PART(part_number),
    source_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    dest_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    quantity INT NOT NULL,
    shipped_ts TIMESTAMP_NTZ NOT NULL,
    estimated_arrival_ts TIMESTAMP_NTZ NOT NULL,
    actual_arrival_ts TIMESTAMP_NTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'IN_TRANSIT',
    associated_case_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_ENGINEER_ROSTER (
    roster_id VARCHAR(50) PRIMARY KEY,
    engineer_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_ENGINEER(engineer_id),
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    shift_date DATE NOT NULL,
    shift_name VARCHAR(50) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_TOOL_AVAILABILITY (
    tool_avail_id VARCHAR(50) PRIMARY KEY,
    tool_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_TOOL(tool_id),
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    status VARCHAR(50) NOT NULL DEFAULT 'AVAILABLE',
    current_work_order_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_AIRCRAFT_ROTATION (
    rotation_id VARCHAR(50) PRIMARY KEY,
    aircraft_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_AIRCRAFT(aircraft_id),
    sequence_order INT NOT NULL,
    flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    turnaround_buffer_mins INT NOT NULL DEFAULT 45
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_DELAY_EVENTS (
    delay_event_id VARCHAR(50) PRIMARY KEY,
    flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    delay_type VARCHAR(50) NOT NULL,
    delay_minutes INT NOT NULL,
    estimated_cost_inr FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_PASSENGER_CONNECTIONS (
    connection_id VARCHAR(50) PRIMARY KEY,
    inbound_flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    outbound_flight_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.CURATED.FACT_FLIGHTS(flight_id),
    connecting_station VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    scheduled_connection_mins INT NOT NULL,
    passenger_count INT NOT NULL DEFAULT 12,
    high_value_segment VARCHAR(50) DEFAULT 'STANDARD'
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_STATION_CAPABILITY (
    station_cap_id VARCHAR(50) PRIMARY KEY,
    station_code VARCHAR(10) NOT NULL REFERENCES AERORESOLVE.CURATED.DIM_STATION(station_code),
    ata_chapter VARCHAR(10) NOT NULL,
    capability_level VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.CURATED.FACT_AGENT_ACTIONS (
    action_record_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    aircraft_id VARCHAR(50) NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    details VARIANT,
    action_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- 4. RAW STREAM TABLES (AERORESOLVE.RAW)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.RAW.RAW_TELEMETRY_STREAM (
    ingest_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    flight_id VARCHAR(50),
    aircraft_id VARCHAR(50),
    event_ts TIMESTAMP_NTZ,
    flight_phase VARCHAR(30),
    altitude_ft FLOAT,
    airspeed_kts FLOAT,
    outside_air_temp_c FLOAT,
    cabin_altitude_ft FLOAT,
    engine_1_n1 FLOAT,
    engine_2_n1 FLOAT,
    engine_1_egt_c FLOAT,
    engine_2_egt_c FLOAT,
    engine_1_n2 FLOAT,
    engine_2_n2 FLOAT,
    fuel_flow_1_kgh FLOAT,
    fuel_flow_2_kgh FLOAT,
    oil_pressure_1_psi FLOAT,
    oil_pressure_2_psi FLOAT,
    oil_temp_1_c FLOAT,
    oil_temp_2_c FLOAT,
    avionics_fan_current_a FLOAT,
    avionics_rack_temp_c FLOAT,
    vibration_index FLOAT,
    elec_bus_voltage_v FLOAT,
    battery_voltage_v FLOAT,
    generator_1_load_pct FLOAT,
    generator_2_load_pct FLOAT,
    apu_generator_load_pct FLOAT,
    pack_1_temp_c FLOAT,
    pack_2_temp_c FLOAT,
    pack_1_flow_kgs FLOAT,
    pack_2_flow_kgs FLOAT,
    bleed_1_pressure_psi FLOAT,
    bleed_2_pressure_psi FLOAT,
    cabin_differential_pressure_psi FLOAT,
    hydraulic_press_green_psi FLOAT,
    hydraulic_press_blue_psi FLOAT,
    hydraulic_press_yellow_psi FLOAT,
    hydraulic_quantity_green_pct FLOAT,
    brake_temp_left_c FLOAT,
    brake_temp_right_c FLOAT,
    flap_position_deg FLOAT,
    slat_position_deg FLOAT,
    rudder_trim_deg FLOAT,
    pitch_angle_deg FLOAT,
    roll_angle_deg FLOAT,
    vertical_speed_fpm FLOAT
);

-- ---------------------------------------------------------------------
-- 5. PRIVATE EVALUATION TRUTH TABLES (AERORESOLVE.EVAL)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.EVAL.SCENARIO_TRUTH (
    scenario_id VARCHAR(50) PRIMARY KEY,
    scenario_name VARCHAR(100) NOT NULL,
    aircraft_id VARCHAR(50) NOT NULL,
    target_flight_id VARCHAR(50) NOT NULL,
    injected_defect_type VARCHAR(100) NOT NULL,
    true_root_cause VARCHAR(255) NOT NULL,
    environmental_trigger_envelope VARIANT,
    is_ghost_fault BOOLEAN NOT NULL DEFAULT FALSE,
    prior_recurrence_count INT NOT NULL DEFAULT 0,
    expected_destination_station VARCHAR(10),
    expected_missing_part VARCHAR(50),
    expected_reposition_source VARCHAR(10),
    healthy_control_case BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.EVAL.ROOT_CAUSE_TRUTH (
    truth_id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.EVAL.SCENARIO_TRUTH(scenario_id),
    aircraft_id VARCHAR(50) NOT NULL,
    primary_root_cause VARCHAR(255) NOT NULL,
    secondary_root_cause VARCHAR(255),
    false_hypothesis VARCHAR(255) NOT NULL,
    why_false_hypothesis_fails VARCHAR(1000) NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.EVAL.EXPECTED_AGENT_ACTION (
    expected_action_id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.EVAL.SCENARIO_TRUTH(scenario_id),
    step_order INT NOT NULL,
    expected_agent VARCHAR(50) NOT NULL,
    expected_action_type VARCHAR(100) NOT NULL,
    min_acceptable_confidence FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.EVAL.EXPECTED_TOOL_SEQUENCE (
    sequence_id VARCHAR(50) PRIMARY KEY,
    scenario_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.EVAL.SCENARIO_TRUTH(scenario_id),
    expected_tool_name VARCHAR(100) NOT NULL,
    sequence_order INT NOT NULL,
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 6. AUDIT & TRACEABILITY TABLES (AERORESOLVE.AUDIT)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.AGENT_CASE (
    case_id VARCHAR(50) PRIMARY KEY,
    aircraft_id VARCHAR(50) NOT NULL,
    flight_id VARCHAR(50),
    case_title VARCHAR(255) NOT NULL,
    opened_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    status VARCHAR(50) NOT NULL DEFAULT 'INVESTIGATING',
    current_hypothesis VARCHAR(500),
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    aog_risk_score FLOAT NOT NULL DEFAULT 0.0,
    closed_ts TIMESTAMP_NTZ,
    repair_effective BOOLEAN
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.AGENT_STEP (
    step_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.AUDIT.AGENT_CASE(case_id),
    step_sequence INT NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    step_action VARCHAR(255) NOT NULL,
    summary_for_ui VARCHAR(1000) NOT NULL,
    evidence_gathered VARIANT,
    created_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.TOOL_CALL (
    call_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.AUDIT.AGENT_CASE(case_id),
    agent_name VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_parameters VARIANT NOT NULL,
    output_summary VARCHAR(2000) NOT NULL,
    execution_time_ms INT NOT NULL,
    executed_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.RECOMMENDATION (
    recommendation_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.AUDIT.AGENT_CASE(case_id),
    recommended_action VARCHAR(500) NOT NULL,
    target_station VARCHAR(10) NOT NULL,
    required_part VARCHAR(50),
    required_tool VARCHAR(50),
    required_skill VARCHAR(50),
    part_reposition_source VARCHAR(10),
    estimated_downtime_mins INT NOT NULL,
    downstream_flights_protected INT NOT NULL,
    passengers_protected INT NOT NULL,
    connection_risk_level VARCHAR(20) NOT NULL,
    created_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.HUMAN_APPROVAL (
    approval_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.AUDIT.AGENT_CASE(case_id),
    decision VARCHAR(20) NOT NULL,
    decision_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    approver_username VARCHAR(100) NOT NULL,
    approver_role VARCHAR(100) NOT NULL,
    controller_notes VARCHAR(1000),
    dispatched_mcp_system VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.EXTERNAL_ACTION (
    external_action_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.AUDIT.AGENT_CASE(case_id),
    target_system VARCHAR(50) NOT NULL,
    external_key VARCHAR(100) NOT NULL,
    external_url VARCHAR(500),
    action_payload VARIANT,
    status VARCHAR(50) NOT NULL DEFAULT 'CREATED',
    created_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS AERORESOLVE.AUDIT.REPAIR_VERIFICATION (
    verification_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES AERORESOLVE.AUDIT.AGENT_CASE(case_id),
    aircraft_id VARCHAR(50) NOT NULL,
    verification_flight_id VARCHAR(50) NOT NULL,
    monitored_sectors_count INT NOT NULL DEFAULT 1,
    anomaly_recurred BOOLEAN NOT NULL DEFAULT FALSE,
    signal_stability_score FLOAT NOT NULL,
    verification_status VARCHAR(50) NOT NULL,
    verified_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- 7. OPS CONFIGURATION TABLES (AERORESOLVE.OPS)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS AERORESOLVE.OPS.COST_ASSUMPTIONS (
    cost_metric VARCHAR(50) PRIMARY KEY,
    unit_cost_inr FLOAT NOT NULL,
    description VARCHAR(255) NOT NULL
);

INSERT INTO AERORESOLVE.OPS.COST_ASSUMPTIONS (cost_metric, unit_cost_inr, description)
SELECT 'AOG_DOWNTIME_PER_HOUR', 185000.0, 'Direct revenue and overhead loss per hour of unscheduled AOG'
WHERE NOT EXISTS (SELECT 1 FROM AERORESOLVE.OPS.COST_ASSUMPTIONS WHERE cost_metric = 'AOG_DOWNTIME_PER_HOUR');

INSERT INTO AERORESOLVE.OPS.COST_ASSUMPTIONS (cost_metric, unit_cost_inr, description)
SELECT 'DELAY_MINUTE_OPERATIONAL', 3200.0, 'Direct ground, gate, and crew overtime cost per minute of delay'
WHERE NOT EXISTS (SELECT 1 FROM AERORESOLVE.OPS.COST_ASSUMPTIONS WHERE cost_metric = 'DELAY_MINUTE_OPERATIONAL');

INSERT INTO AERORESOLVE.OPS.COST_ASSUMPTIONS (cost_metric, unit_cost_inr, description)
SELECT 'PASSENGER_MISCONNECTION_CARE', 12500.0, 'Hotel, meal voucher, rebooking & compensation per missed connection'
WHERE NOT EXISTS (SELECT 1 FROM AERORESOLVE.OPS.COST_ASSUMPTIONS WHERE cost_metric = 'PASSENGER_MISCONNECTION_CARE');

INSERT INTO AERORESOLVE.OPS.COST_ASSUMPTIONS (cost_metric, unit_cost_inr, description)
SELECT 'EXPEDITED_SPARE_LOGISTICS', 45000.0, 'Fast-cargo repositioning fee for urgent Line Station spares'
WHERE NOT EXISTS (SELECT 1 FROM AERORESOLVE.OPS.COST_ASSUMPTIONS WHERE cost_metric = 'EXPEDITED_SPARE_LOGISTICS');

SELECT 'Table creation completed successfully' AS status;
