# AeroResolve — Data Dictionary

## Dimensions (`AERORESOLVE.CURATED`)

### `DIM_AIRCRAFT`
- `aircraft_id` (VARCHAR, PK): Unique synthetic identifier (e.g., `ABR-017`).
- `aircraft_type_id` (VARCHAR, FK): References `DIM_AIRCRAFT_TYPE`.
- `serial_number` (VARCHAR): Synthetic manufacturer serial number.
- `delivery_date` (DATE): Synthetic delivery date.
- `total_flight_hours` (FLOAT): Accumulated flight hours.
- `total_flight_cycles` (INT): Accumulated flight cycles.
- `current_status` (VARCHAR): `ACTIVE`, `MAINTENANCE`, `AOG`.
- `home_base` (VARCHAR, FK): References `DIM_STATION`.

### `DIM_AIRCRAFT_TYPE`
- `aircraft_type_id` (VARCHAR, PK): E.g. `AB-320N`, `AB-321N` (fictional narrow-body series).
- `manufacturer` (VARCHAR): Synthetic manufacturer name.
- `engine_type` (VARCHAR): E.g., `TURBOFAN-LEAP-1A`.
- `max_range_nm` (INT): Range in nautical miles.
- `seating_capacity` (INT): Passenger capacity (e.g. 186).

### `DIM_STATION`
- `station_code` (VARCHAR, PK): IATA 3-letter station code (e.g., `DEL`, `BOM`, `BLR`, `HYD`, `MAA`, `CCU`, `PNQ`, `AMD`, `COK`, `GOI`, `JAI`, `LKO`, `GAU`, `DXB`, `SIN`, `BKK`).
- `station_name` (VARCHAR): Full airport / city name.
- `is_hub` (BOOLEAN): TRUE for primary maintenance hubs.
- `country` (VARCHAR): `IND`, `ARE`, `SGP`, `THA`.
- `maintenance_tier` (INT): 1 (Line only), 2 (Intermediate repair & tool store), 3 (Heavy base & major spares).

### `DIM_ROUTE`
- `route_id` (VARCHAR, PK): E.g., `BLR-DEL`.
- `origin_station` (VARCHAR, FK): Station code.
- `dest_station` (VARCHAR, FK): Station code.
- `scheduled_flight_time_mins` (INT): Normal block flight duration.
- `distance_nm` (INT): Distance in nautical miles.

### `DIM_COMPONENT_TYPE`
- `component_type_id` (VARCHAR, PK): E.g., `AV-FAN-01`, `AV-COMP-02`, `WIR-HARN-03`, `BLEED-VALVE-01`.
- `ata_chapter` (VARCHAR): ATA-like chapter (e.g., `21` Air Conditioning/Cooling, `24` Electrical, `36` Pneumatics).
- `description` (VARCHAR): Component technical name.
- `criticality_tier` (VARCHAR): `NO-GO`, `GO-IF`, `CONVENIENCE`.

### `DIM_FAULT_CODE`
- `fault_code` (VARCHAR, PK): Synthetic fault identifier (e.g., `FAULT-21-204` Avionics Cooling Flow Low, `FAULT-21-209` Avionics Rack Temp High).
- `ata_chapter` (VARCHAR): ATA reference chapter.
- `description` (VARCHAR): Diagnostic fault description.
- `severity` (VARCHAR): `CRITICAL`, `WARNING`, `ADVISORY`.
- `mel_reference` (VARCHAR): Synthetic MEL item reference (for decision support context).

### `DIM_PART`
- `part_number` (VARCHAR, PK): E.g., `PART-X42-CONN` (Connector kit X42), `PART-AVF-881` (Cooling fan motor), `PART-AVC-902` (Avionics computer unit).
- `component_type_id` (VARCHAR, FK): References `DIM_COMPONENT_TYPE`.
- `description` (VARCHAR): Part description.
- `standard_cost_inr` (FLOAT): Synthetic unit cost in INR.
- `lead_time_hours` (FLOAT): Procurement / reposition baseline time.

## Facts (`AERORESOLVE.CURATED`)

### `FACT_FLIGHTS`
- `flight_id` (VARCHAR, PK): E.g., `FL-20261006-017-01`.
- `flight_number` (VARCHAR): Fictional flight callsign (e.g., `AB-402`).
- `aircraft_id` (VARCHAR, FK): Synthetic tail number.
- `origin_station` (VARCHAR, FK): Departure airport.
- `dest_station` (VARCHAR, FK): Scheduled arrival airport.
- `scheduled_departure_ts` (TIMESTAMP_NTZ): Scheduled departure.
- `actual_departure_ts` (TIMESTAMP_NTZ): Actual off-block timestamp.
- `scheduled_arrival_ts` (TIMESTAMP_NTZ): Scheduled arrival.
- `actual_arrival_ts` (TIMESTAMP_NTZ): Actual on-block timestamp.
- `flight_status` (VARCHAR): `SCHEDULED`, `AIRBORNE`, `LANDED`, `DELAYED`, `CANCELLED`.
- `passenger_count` (INT): Booked passenger load.

### `FACT_TELEMETRY` (Wide Observation Table)
- `flight_id` (VARCHAR, FK)
- `aircraft_id` (VARCHAR, FK)
- `event_ts` (TIMESTAMP_NTZ, Sort/Cluster key)
- `flight_phase` (VARCHAR): `TAXI_OUT`, `TAKEOFF`, `CLIMB`, `CRUISE`, `DESCENT`, `APPROACH`, `LANDING`, `TAXI_IN`.
- `altitude_ft` (FLOAT)
- `airspeed_kts` (FLOAT)
- `outside_air_temp_c` (FLOAT)
- `cabin_altitude_ft` (FLOAT)
- `engine_1_n1` (FLOAT), `engine_2_n1` (FLOAT)
- `engine_1_egt_c` (FLOAT), `engine_2_egt_c` (FLOAT)
- `hydraulic_press_a_psi` (FLOAT), `hydraulic_press_b_psi` (FLOAT)
- `elec_bus_voltage_v` (FLOAT), `battery_voltage_v` (FLOAT)
- `avionics_fan_current_a` (FLOAT)
- `avionics_rack_temp_c` (FLOAT)
- `vibration_index` (FLOAT)
- `fuel_flow_1_kgh` (FLOAT), `fuel_flow_2_kgh` (FLOAT)
- `oil_pressure_1_psi` (FLOAT), `oil_pressure_2_psi` (FLOAT)
- `oil_temp_1_c` (FLOAT), `oil_temp_2_c` (FLOAT)
- `pack_temp_c` (FLOAT)
- `bleed_pressure_psi` (FLOAT)
- `apu_egt_c` (FLOAT)
- `brake_temp_c` (FLOAT)
- `generator_load_pct` (FLOAT)
... (Additional synthetic channels up to 60-80 channels)

### `FACT_FAULT_EVENTS`
- `fault_event_id` (VARCHAR, PK)
- `flight_id` (VARCHAR, FK)
- `aircraft_id` (VARCHAR, FK)
- `fault_code` (VARCHAR, FK)
- `event_ts` (TIMESTAMP_NTZ)
- `flight_phase` (VARCHAR)
- `altitude_ft` (FLOAT)
- `outside_air_temp_c` (FLOAT)
- `vibration_index` (FLOAT)
- `is_intermittent` (BOOLEAN)
- `reported_by` (VARCHAR): `ACARS_BITE`, `PILOT_TECHLOG`.

### `FACT_MAINTENANCE_ACTIONS`
- `action_id` (VARCHAR, PK)
- `aircraft_id` (VARCHAR, FK)
- `fault_event_id` (VARCHAR, FK)
- `station_code` (VARCHAR, FK)
- `performed_ts` (TIMESTAMP_NTZ)
- `action_type` (VARCHAR): `RESET_COMPUTER`, `REPLACE_UNIT`, `INSPECT_HARNESS`, `CLEAN_FILTER`.
- `action_summary` (VARCHAR)
- `component_type_id` (VARCHAR, FK)
- `part_number_used` (VARCHAR, FK)
- `is_repeat_defect` (BOOLEAN)
- `was_effective` (BOOLEAN): Latent simulation ground-truth status.

### `FACT_PART_INVENTORY`
- `inventory_id` (VARCHAR, PK)
- `station_code` (VARCHAR, FK)
- `part_number` (VARCHAR, FK)
- `quantity_on_hand` (INT)
- `quantity_reserved` (INT)
- `minimum_threshold` (INT)
- `last_updated_ts` (TIMESTAMP_NTZ)

## Audit & Traceability Schema (`AERORESOLVE.AUDIT`)

### `AGENT_CASE`
- `case_id` (VARCHAR, PK): E.g., `CASE-017-1728219000`
- `aircraft_id` (VARCHAR, FK): Tail identifier
- `flight_id` (VARCHAR, FK): Flight sector under investigation
- `case_title` (VARCHAR): Summary discrepancy title
- `opened_ts` (TIMESTAMP_NTZ): Trigger timestamp
- `closed_ts` (TIMESTAMP_NTZ): Resolution timestamp
- `status` (VARCHAR): `INVESTIGATING`, `AWAITING_HUMAN_APPROVAL`, `EXTERNAL_WORK_ITEM_CREATED`, `RESOLVED`
- `current_hypothesis` (VARCHAR): Top ranked physical root cause
- `confidence_score` (FLOAT): 0.0 to 1.0 confidence
- `aog_risk_score` (FLOAT): Predicted AOG probability

### `AGENT_STEP`
- `step_id` (VARCHAR, PK): E.g., `STEP-017-01`
- `case_id` (VARCHAR, FK): Case reference
- `step_sequence` (INT): 1 to 5 deterministic execution order
- `agent_name` (VARCHAR): Executing specialist agent
- `step_action` (VARCHAR): Specific tool action taken
- `summary_for_ui` (VARCHAR): Human-readable synopsis
- `evidence_gathered` (VARIANT): Structured JSON payload of telemetry/manual evidence
- `created_ts` (TIMESTAMP_NTZ)

### `HUMAN_APPROVAL`
- `approval_id` (VARCHAR, PK): Unique decision identifier
- `case_id` (VARCHAR, FK): Associated agent case
- `decision` (VARCHAR): `APPROVED`, `REJECTED`, `MODIFIED`
- `decision_ts` (TIMESTAMP_NTZ): Human action timestamp
- `approver_username` (VARCHAR): Licensed controller name
- `approver_role` (VARCHAR): Authorized operational title
- `controller_notes` (VARCHAR): Discretionary engineer rationale
- `dispatched_mcp_system` (VARCHAR): `JIRA`, `GITHUB`

### `EXTERNAL_ACTION`
- `external_action_id` (VARCHAR, PK): MCP dispatch identifier
- `case_id` (VARCHAR, FK): Case reference
- `target_system` (VARCHAR): `JIRA` or `GITHUB`
- `external_key` (VARCHAR): External ticket identifier (e.g. `AERO-0060`)
- `external_url` (VARCHAR): Direct link to ticket
- `action_payload` (VARIANT): Full Model Context Protocol JSON payload
- `status` (VARCHAR): `CREATED`, `DISPATCHED_SUCCESSFULLY`
- `created_ts` (TIMESTAMP_NTZ)

### `REPAIR_SURVEILLANCE`
- `surveillance_id` (VARCHAR, PK): Post-repair surveillance identifier
- `case_id` (VARCHAR, FK): Case reference
- `aircraft_id` (VARCHAR, FK): Aircraft monitored
- `verification_flight_id` (VARCHAR, FK): Subsequent flight sector
- `signal_stability_score` (FLOAT): 0.0 to 1.0 stability index
- `anomaly_recurred` (BOOLEAN): False if repair was effective
- `repair_status` (VARCHAR): `REPAIR_EFFECTIVE_VERIFIED`, `RECURRENCE_DETECTED`
- `verified_ts` (TIMESTAMP_NTZ)

## Private Evaluation Schema (`AERORESOLVE.EVAL`)

### `SCENARIO_TRUTH`
- `scenario_id` (VARCHAR, PK): E.g., `SCEN-01-GHOST-FAULT`
- `scenario_name` (VARCHAR): Test scenario title
- `aircraft_id` (VARCHAR): Target test aircraft
- `target_flight_id` (VARCHAR): Target flight
- `injected_defect_type` (VARCHAR): Injected failure category
- `true_root_cause` (VARCHAR): Latent ground-truth physical explanation
- `environmental_trigger_envelope` (VARIANT): Altitude, temp, and vibration trigger ranges
- `is_ghost_fault` (BOOLEAN): Disappears on ground
- `prior_recurrence_count` (INT): Historical recurrence count
- `expected_destination_station` (VARCHAR): Expected arrival airport
- `expected_missing_part` (VARCHAR): Stockout part number
- `expected_reposition_source` (VARCHAR): Optimal reposition donor hub
- `healthy_control_case` (BOOLEAN): True for negative controls

### `BENCHMARK_RUN_RESULTS`
- `run_id` (VARCHAR, PK): Unique evaluation run ID
- `scenario_id` (VARCHAR, FK): Scenario tested
- `scenario_name` (VARCHAR): Test scenario title
- `aircraft_id` (VARCHAR): Aircraft evaluated
- `test_type` (VARCHAR): Defect, Control, Sequence, or Safety Gate
- `passed` (BOOLEAN): True if criteria satisfied
- `predicted_root_cause` (VARCHAR): Agent's isolated root cause
- `true_root_cause` (VARCHAR): Ground truth explanation
- `confidence_score` (FLOAT): Agent confidence
- `execution_duration_sec` (FLOAT): Elapsed test execution latency
- `evaluation_notes` (VARCHAR): Specific test verification observations
- `created_at` (TIMESTAMP_NTZ): Benchmark execution timestamp

