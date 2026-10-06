-- =====================================================================
-- AeroResolve: 03_dynamic_tables.sql
-- Declarative Feature Engineering Pipelines via Snowflake Dynamic Tables
-- =====================================================================

USE ROLE AERORESOLVE_DEV;
USE WAREHOUSE AERORESOLVE_WH;
USE DATABASE AERORESOLVE;

-- 1. Rolling Aircraft Health Window (FEATURES.DT_AIRCRAFT_HEALTH_WINDOW)
CREATE OR REPLACE DYNAMIC TABLE AERORESOLVE.FEATURES.DT_AIRCRAFT_HEALTH_WINDOW
    TARGET_LAG = '2 MINUTES'
    WAREHOUSE = AERORESOLVE_WH
    COMMENT = 'Rolling window telemetry statistics for real-time degradation detection'
AS
SELECT 
    aircraft_id,
    flight_phase,
    COUNT(*) AS observation_count,
    ROUND(AVG(avionics_fan_current_a), 3) AS avg_fan_current_a,
    ROUND(MAX(avionics_fan_current_a), 3) AS max_fan_current_a,
    ROUND(COALESCE(STDDEV(avionics_fan_current_a), 0.0), 3) AS stddev_fan_current_a,
    ROUND(AVG(vibration_index), 3) AS avg_vibration,
    ROUND(MAX(vibration_index), 3) AS max_vibration,
    ROUND(AVG(avionics_rack_temp_c), 2) AS avg_rack_temp_c,
    ROUND(MAX(avionics_rack_temp_c), 2) AS max_rack_temp_c,
    ROUND(AVG(outside_air_temp_c), 1) AS avg_oat_c,
    ROUND(AVG(altitude_ft), 0) AS avg_altitude_ft,
    -- Degradation Score (0 to 100): Weighted formula based on deviation from nominal (3.2A baseline)
    ROUND(LEAST(100.0, GREATEST(0.0, (AVG(avionics_fan_current_a) - 3.2) * 55.0 + (AVG(vibration_index) - 0.5) * 45.0)), 1) AS degradation_score,
    MAX(event_ts) AS last_telemetry_ts
FROM AERORESOLVE.CURATED.FACT_TELEMETRY
GROUP BY aircraft_id, flight_phase;

-- 2. Fault Recurrence & Repeat Defect Features (FEATURES.DT_FAULT_RECURRENCE_FEATURES)
CREATE OR REPLACE DYNAMIC TABLE AERORESOLVE.FEATURES.DT_FAULT_RECURRENCE_FEATURES
    TARGET_LAG = '2 MINUTES'
    WAREHOUSE = AERORESOLVE_WH
    COMMENT = 'Calculates repeat defect frequency and prior maintenance effectiveness per aircraft'
AS
SELECT 
    f.aircraft_id,
    f.fault_code,
    COUNT(DISTINCT f.fault_event_id) AS total_occurrences_30d,
    CASE WHEN COUNT(DISTINCT f.fault_event_id) >= 2 THEN TRUE ELSE FALSE END AS is_repeat_defect,
    MAX(f.event_ts) AS latest_fault_ts,
    COALESCE(MAX(m.action_type_id), 'NO_PRIOR_ACTION') AS last_maintenance_action_type,
    COUNT(DISTINCT m.action_id) AS prior_maintenance_attempts,
    -- Repeat defect risk rating
    CASE 
        WHEN COUNT(DISTINCT f.fault_event_id) >= 3 THEN 'CRITICAL_REPEAT'
        WHEN COUNT(DISTINCT f.fault_event_id) = 2 THEN 'REPEAT_DEFECT'
        ELSE 'FIRST_OCCURRENCE'
    END AS repeat_status_label
FROM AERORESOLVE.CURATED.FACT_FAULT_EVENTS f
LEFT JOIN AERORESOLVE.CURATED.FACT_MAINTENANCE_ACTIONS m 
    ON f.aircraft_id = m.aircraft_id
GROUP BY f.aircraft_id, f.fault_code;

-- 3. Station Readiness Matrix (OPS.DT_STATION_READINESS)
CREATE OR REPLACE DYNAMIC TABLE AERORESOLVE.OPS.DT_STATION_READINESS
    TARGET_LAG = '2 MINUTES'
    WAREHOUSE = AERORESOLVE_WH
    COMMENT = 'Evaluates destination station maintenance readiness (spares, tooling, licensed engineers)'
AS
SELECT 
    s.station_code,
    s.station_name,
    s.is_hub,
    p.part_number,
    p.part_name,
    COALESCE(inv.quantity_on_hand, 0) AS quantity_on_hand,
    COALESCE(inv.quantity_reserved, 0) AS quantity_reserved,
    (COALESCE(inv.quantity_on_hand, 0) - COALESCE(inv.quantity_reserved, 0)) AS net_available_stock,
    -- Available B2 Avionics Engineers
    COALESCE(eng.b2_count, 0) AS b2_engineers_available,
    -- Available Harness Tool T14
    COALESCE(tool.t14_count, 0) AS tool_t14_available,
    -- Composite Readiness Evaluation
    CASE 
        WHEN (COALESCE(inv.quantity_on_hand, 0) - COALESCE(inv.quantity_reserved, 0)) <= 0 THEN 'PART_STOCKOUT'
        WHEN COALESCE(eng.b2_count, 0) = 0 THEN 'NO_B2_ENGINEER'
        WHEN COALESCE(tool.t14_count, 0) = 0 THEN 'TOOL_UNAVAILABLE'
        ELSE 'FULLY_READY'
    END AS readiness_status
FROM AERORESOLVE.CURATED.DIM_STATION s
CROSS JOIN AERORESOLVE.CURATED.DIM_PART p
LEFT JOIN AERORESOLVE.CURATED.FACT_PART_INVENTORY inv
    ON s.station_code = inv.station_code AND p.part_number = inv.part_number
LEFT JOIN (
    SELECT station_code, COUNT(*) AS b2_count
    FROM AERORESOLVE.CURATED.DIM_ENGINEER
    WHERE license_type IN ('B2_AVIONICS', 'DUAL_B1_B2')
    GROUP BY station_code
) eng ON s.station_code = eng.station_code
LEFT JOIN (
    SELECT station_code, COUNT(*) AS t14_count
    FROM AERORESOLVE.CURATED.DIM_TOOL
    WHERE tool_code = 'T14-HARN' AND is_serviceable = TRUE
    GROUP BY station_code
) tool ON s.station_code = tool.station_code;

SELECT 'Dynamic Tables created successfully' AS status;
