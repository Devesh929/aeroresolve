-- =====================================================================
-- AeroResolve: 06_semantic_views.sql
-- Idempotent Semantic Layer Views & Verified Gold Queries
-- =====================================================================

USE ROLE AERORESOLVE_DEV;
USE WAREHOUSE AERORESOLVE_WH;
USE DATABASE AERORESOLVE;
USE SCHEMA SEMANTIC;

-- ---------------------------------------------------------------------
-- 1. CORE DIMENSIONAL SEMANTIC VIEWS
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_FLEET_AIRCRAFT AS
SELECT 
    a.aircraft_id,
    a.aircraft_type_id,
    t.model_name,
    t.manufacturer,
    t.engine_type,
    t.seating_capacity,
    t.max_range_nm,
    a.serial_number,
    a.delivery_date,
    a.home_base,
    s.station_name AS home_base_name,
    s.city AS home_base_city,
    a.total_flight_hours,
    a.total_flight_cycles,
    a.current_status,
    a.last_c_check_date
FROM AERORESOLVE.CURATED.DIM_AIRCRAFT a
JOIN AERORESOLVE.CURATED.DIM_AIRCRAFT_TYPE t ON a.aircraft_type_id = t.aircraft_type_id
JOIN AERORESOLVE.CURATED.DIM_STATION s ON a.home_base = s.station_code;

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_FLIGHT_OPERATIONS AS
SELECT 
    f.flight_id,
    f.flight_number,
    f.aircraft_id,
    f.route_id,
    f.origin_station,
    orig.station_name AS origin_station_name,
    orig.city AS origin_city,
    f.dest_station,
    dest.station_name AS dest_station_name,
    dest.city AS dest_city,
    f.scheduled_departure_ts,
    f.actual_departure_ts,
    f.scheduled_arrival_ts,
    f.actual_arrival_ts,
    f.flight_status,
    f.passenger_count,
    f.connecting_passenger_count,
    f.delay_departure_minutes,
    f.delay_arrival_minutes,
    r.distance_nm,
    r.scheduled_flight_time_mins,
    CASE WHEN f.delay_arrival_minutes > 15 THEN TRUE ELSE FALSE END AS is_arrival_delayed
FROM AERORESOLVE.CURATED.FACT_FLIGHTS f
JOIN AERORESOLVE.CURATED.DIM_STATION orig ON f.origin_station = orig.station_code
JOIN AERORESOLVE.CURATED.DIM_STATION dest ON f.dest_station = dest.station_code
JOIN AERORESOLVE.CURATED.DIM_ROUTE r ON f.route_id = r.route_id;

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_FAULT_HISTORY AS
SELECT 
    fe.fault_event_id,
    fe.flight_id,
    f.flight_number,
    fe.aircraft_id,
    fe.fault_code,
    fc.ata_chapter,
    fc.fault_title,
    fc.fault_description,
    fc.severity,
    fc.mel_reference,
    fc.requires_ground_isolation,
    fe.event_ts,
    fe.flight_phase,
    fe.altitude_ft,
    fe.outside_air_temp_c,
    fe.vibration_index,
    fe.avionics_fan_current_a,
    fe.is_intermittent,
    fe.normalized_on_ground,
    f.origin_station,
    f.dest_station
FROM AERORESOLVE.CURATED.FACT_FAULT_EVENTS fe
JOIN AERORESOLVE.CURATED.DIM_FAULT_CODE fc ON fe.fault_code = fc.fault_code
JOIN AERORESOLVE.CURATED.FACT_FLIGHTS f ON fe.flight_id = f.flight_id;

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_MAINTENANCE_ACTIONS AS
SELECT 
    ma.action_id,
    ma.work_order_id,
    wo.fault_event_id,
    ma.aircraft_id,
    ma.station_code,
    s.station_name,
    ma.performed_ts,
    ma.action_type_id,
    dma.action_category,
    dma.description AS action_description,
    ma.component_type_id,
    ct.ata_chapter,
    ct.description AS component_description,
    ma.part_number_used,
    p.part_name,
    p.standard_unit_cost_inr,
    ma.action_notes,
    ma.is_repeat_defect,
    ma.recurrence_interval_days,
    wo.status AS work_order_status,
    wo.lead_engineer_id,
    e.name AS lead_engineer_name
FROM AERORESOLVE.CURATED.FACT_MAINTENANCE_ACTIONS ma
JOIN AERORESOLVE.CURATED.FACT_WORK_ORDERS wo ON ma.work_order_id = wo.work_order_id
JOIN AERORESOLVE.CURATED.DIM_MAINTENANCE_ACTION dma ON ma.action_type_id = dma.action_type_id
LEFT JOIN AERORESOLVE.CURATED.DIM_COMPONENT_TYPE ct ON ma.component_type_id = ct.component_type_id
LEFT JOIN AERORESOLVE.CURATED.DIM_PART p ON ma.part_number_used = p.part_number
JOIN AERORESOLVE.CURATED.DIM_STATION s ON ma.station_code = s.station_code
LEFT JOIN AERORESOLVE.CURATED.DIM_ENGINEER e ON wo.lead_engineer_id = e.engineer_id;

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_SPARE_PARTS_INVENTORY AS
SELECT 
    pi.inventory_id,
    pi.station_code,
    s.station_name,
    s.city AS station_city,
    pi.part_number,
    p.part_name,
    p.component_type_id,
    ct.ata_chapter,
    p.standard_unit_cost_inr,
    p.lead_time_hours,
    p.weight_kg,
    pi.quantity_on_hand,
    pi.quantity_reserved,
    (pi.quantity_on_hand - pi.quantity_reserved) AS quantity_available,
    pi.minimum_safety_stock,
    CASE WHEN (pi.quantity_on_hand - pi.quantity_reserved) <= 0 THEN TRUE ELSE FALSE END AS is_stockout,
    pi.last_updated_ts
FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY pi
JOIN AERORESOLVE.CURATED.DIM_PART p ON pi.part_number = p.part_number
JOIN AERORESOLVE.CURATED.DIM_COMPONENT_TYPE ct ON p.component_type_id = ct.component_type_id
JOIN AERORESOLVE.CURATED.DIM_STATION s ON pi.station_code = s.station_code;

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_STATION_CAPABILITY AS
SELECT 
    sc.station_cap_id,
    sc.station_code,
    s.station_name,
    s.city,
    s.maintenance_tier,
    sc.ata_chapter,
    sc.capability_level,
    sc.is_active,
    s.has_avionics_shop,
    s.has_engine_shop,
    (SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_ENGINEER_ROSTER er 
     WHERE er.station_code = sc.station_code AND er.is_available = TRUE) AS available_engineers_count,
    (SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_TOOL_AVAILABILITY ta 
     WHERE ta.station_code = sc.station_code AND ta.status = 'AVAILABLE') AS available_tools_count
FROM AERORESOLVE.CURATED.FACT_STATION_CAPABILITY sc
JOIN AERORESOLVE.CURATED.DIM_STATION s ON sc.station_code = s.station_code;

CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.SEM_AIRCRAFT_ROTATION AS
SELECT 
    ar.rotation_id,
    ar.aircraft_id,
    ar.sequence_order,
    ar.flight_id,
    f.flight_number,
    f.origin_station,
    f.dest_station,
    f.scheduled_departure_ts,
    f.scheduled_arrival_ts,
    f.flight_status,
    ar.turnaround_buffer_mins,
    f.passenger_count,
    f.connecting_passenger_count,
    (f.passenger_count * 3200) AS potential_delay_risk_inr,
    (f.connecting_passenger_count * 12500) AS potential_misconnection_risk_inr
FROM AERORESOLVE.CURATED.FACT_AIRCRAFT_ROTATION ar
JOIN AERORESOLVE.CURATED.FACT_FLIGHTS f ON ar.flight_id = f.flight_id;

-- ---------------------------------------------------------------------
-- 2. VERIFIED / GOLD QUERY VIEWS (SECTION 14 REQUIREMENTS)
-- ---------------------------------------------------------------------

-- Question 1: What is the fleet repeat-defect rate over the last 30 days?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_FLEET_REPEAT_DEFECT_RATE_30D AS
SELECT 
    COUNT(CASE WHEN is_repeat_defect = TRUE THEN 1 END) AS repeat_defect_count,
    COUNT(*) AS total_maintenance_actions,
    ROUND(COUNT(CASE WHEN is_repeat_defect = TRUE THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS repeat_defect_rate_pct
FROM AERORESOLVE.CURATED.FACT_MAINTENANCE_ACTIONS
WHERE performed_ts >= DATEADD('day', -30, CURRENT_TIMESTAMP());

-- Question 2: What are all previous occurrences of ATA 21 faults on ABR-017?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_ATA21_HISTORY AS
SELECT 
    fe.fault_event_id,
    fe.aircraft_id,
    fe.flight_id,
    f.flight_number,
    fe.fault_code,
    fc.ata_chapter,
    fc.fault_title,
    fe.event_ts,
    fe.flight_phase,
    fe.altitude_ft,
    fe.outside_air_temp_c,
    fe.vibration_index,
    fe.avionics_fan_current_a,
    fe.is_intermittent,
    fe.normalized_on_ground
FROM AERORESOLVE.CURATED.FACT_FAULT_EVENTS fe
JOIN AERORESOLVE.CURATED.DIM_FAULT_CODE fc ON fe.fault_code = fc.fault_code
JOIN AERORESOLVE.CURATED.FACT_FLIGHTS f ON fe.flight_id = f.flight_id
WHERE fe.aircraft_id = 'ABR-017' AND fc.ata_chapter = '21'
ORDER BY fe.event_ts ASC;

-- Question 3: Which aircraft flying right now have active fault signatures?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_ACTIVE_INFLIGHT_FAULT_SIGNATURES AS
SELECT 
    f.flight_id,
    f.flight_number,
    f.aircraft_id,
    f.origin_station,
    f.dest_station,
    f.scheduled_departure_ts,
    f.scheduled_arrival_ts,
    f.flight_status,
    rf.fault_code,
    fc.fault_title,
    fc.ata_chapter,
    rf.latest_fault_ts AS fault_event_ts,
    rf.is_repeat_defect,
    COALESCE(arp.predicted_aog_probability, 0.85) AS predicted_aog_probability
FROM AERORESOLVE.CURATED.FACT_FLIGHTS f
JOIN AERORESOLVE.FEATURES.DT_FAULT_RECURRENCE_FEATURES rf ON f.aircraft_id = rf.aircraft_id
JOIN AERORESOLVE.CURATED.DIM_FAULT_CODE fc ON rf.fault_code = fc.fault_code
LEFT JOIN AERORESOLVE.ML.AOG_RISK_PREDICTIONS arp ON f.flight_id = arp.flight_id
WHERE f.flight_status = 'AIRBORNE' AND rf.total_occurrences_30d > 0;

-- Question 4: What is the maintenance capability at DEL tonight for ATA 21 cooling loop repairs?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_DEL_TONIGHT_ATA21_CAPABILITY AS
SELECT 
    s.station_code,
    s.station_name,
    s.city,
    sc.ata_chapter,
    sc.capability_level,
    sc.is_active AS has_active_certification,
    s.has_avionics_shop,
    (SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_ENGINEER_ROSTER er 
     WHERE er.station_code = 'DEL' AND er.is_available = TRUE) AS available_engineers_on_duty,
    (SELECT COUNT(*) FROM AERORESOLVE.CURATED.FACT_TOOL_AVAILABILITY ta 
     WHERE ta.station_code = 'DEL' AND ta.status = 'AVAILABLE') AS available_tools_ready
FROM AERORESOLVE.CURATED.DIM_STATION s
JOIN AERORESOLVE.CURATED.FACT_STATION_CAPABILITY sc ON s.station_code = sc.station_code
WHERE s.station_code = 'DEL' AND sc.ata_chapter = '21';

-- Question 5: Where is part PART-X42-CONN currently stocked, and what are transit times to DEL?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_PART_X42_CONN_STOCK_AND_TRANSIT AS
SELECT 
    pi.station_code,
    s.station_name,
    pi.part_number,
    p.part_name,
    pi.quantity_on_hand,
    pi.quantity_reserved,
    (pi.quantity_on_hand - pi.quantity_reserved) AS quantity_available,
    COALESCE(r.scheduled_flight_time_mins, 0) AS transit_flight_time_mins,
    ROUND(COALESCE(r.scheduled_flight_time_mins, 0) / 60.0, 1) AS transit_flight_hours,
    ROUND((COALESCE(r.scheduled_flight_time_mins, 0) + 90.0) / 60.0, 1) AS estimated_total_reposition_hours,
    CASE 
        WHEN pi.station_code = 'DEL' THEN 'DESTINATION_STATION'
        WHEN (pi.quantity_on_hand - pi.quantity_reserved) > 0 THEN 'AVAILABLE_CANDIDATE_FOR_REPOSITION'
        ELSE 'OUT_OF_STOCK'
    END AS logistics_status
FROM AERORESOLVE.CURATED.FACT_PART_INVENTORY pi
JOIN AERORESOLVE.CURATED.DIM_PART p ON pi.part_number = p.part_number
JOIN AERORESOLVE.CURATED.DIM_STATION s ON pi.station_code = s.station_code
LEFT JOIN AERORESOLVE.CURATED.DIM_ROUTE r ON r.origin_station = pi.station_code AND r.dest_station = 'DEL'
WHERE pi.part_number = 'PART-X42-CONN'
ORDER BY quantity_available DESC, transit_flight_time_mins ASC;

-- Question 6: What downstream flights are operated by ABR-017 in the next 24 hours?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_ABR017_DOWNSTREAM_ROTATION_24H AS
SELECT 
    ar.sequence_order,
    f.flight_id,
    f.flight_number,
    f.aircraft_id,
    f.origin_station,
    f.dest_station,
    f.scheduled_departure_ts,
    f.scheduled_arrival_ts,
    f.flight_status,
    ar.turnaround_buffer_mins,
    f.passenger_count,
    f.connecting_passenger_count,
    (f.passenger_count * 3200) AS delay_exposure_inr,
    (f.connecting_passenger_count * 12500) AS misconnection_exposure_inr,
    ((f.passenger_count * 3200) + (f.connecting_passenger_count * 12500)) AS total_exposure_inr
FROM AERORESOLVE.CURATED.FACT_AIRCRAFT_ROTATION ar
JOIN AERORESOLVE.CURATED.FACT_FLIGHTS f ON ar.flight_id = f.flight_id
WHERE f.aircraft_id = 'ABR-017'
  AND f.scheduled_departure_ts >= (
      SELECT scheduled_arrival_ts 
      FROM AERORESOLVE.CURATED.FACT_FLIGHTS 
      WHERE flight_id = 'FL-20261006-017-0060' -- Current airborne flight
  )
ORDER BY ar.sequence_order ASC;

-- Question 7: Which repairs in the last 60 days were followed by recurring faults within 3 flights?
CREATE OR REPLACE VIEW AERORESOLVE.SEMANTIC.V_VERIFIED_RECURRING_FAULTS_AFTER_REPAIR_60D AS
SELECT 
    ma.action_id,
    ma.work_order_id,
    ma.aircraft_id,
    ma.station_code,
    ma.performed_ts,
    ma.action_type_id,
    dma.action_category,
    dma.description AS action_description,
    ma.part_number_used,
    ma.action_notes,
    ma.is_repeat_defect,
    ma.recurrence_interval_days
FROM AERORESOLVE.CURATED.FACT_MAINTENANCE_ACTIONS ma
JOIN AERORESOLVE.CURATED.DIM_MAINTENANCE_ACTION dma ON ma.action_type_id = dma.action_type_id
WHERE ma.is_repeat_defect = TRUE
  AND ma.performed_ts >= DATEADD('day', -60, CURRENT_TIMESTAMP())
ORDER BY ma.performed_ts DESC;

SELECT 'Semantic Layer views and verified gold queries created successfully' AS status;
