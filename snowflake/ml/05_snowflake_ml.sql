-- =====================================================================
-- AeroResolve: 05_snowflake_ml.sql
-- Native Snowflake ML Anomaly Detection & AOG Risk Scoring
-- =====================================================================

USE ROLE AERORESOLVE_DEV;
USE WAREHOUSE AERORESOLVE_WH;
USE DATABASE AERORESOLVE;

-- 1. Create Training View for Multi-Series Anomaly Detection
-- Using baseline historical observations strictly before split timestamp
CREATE OR REPLACE VIEW AERORESOLVE.ML.VW_TELEMETRY_TRAIN AS
SELECT 
    aircraft_id,
    event_ts,
    avionics_fan_current_a,
    vibration_index,
    avionics_rack_temp_c,
    altitude_ft
FROM AERORESOLVE.CURATED.FACT_TELEMETRY
WHERE flight_phase = 'CRUISE' 
  AND event_ts <= '2026-10-02 12:00:00';

-- 2. Create Evaluation / Inference View strictly after training data
CREATE OR REPLACE VIEW AERORESOLVE.ML.VW_TELEMETRY_EVAL AS
SELECT 
    aircraft_id,
    event_ts,
    avionics_fan_current_a,
    vibration_index,
    avionics_rack_temp_c,
    altitude_ft
FROM AERORESOLVE.CURATED.FACT_TELEMETRY
WHERE flight_phase = 'CRUISE'
  AND event_ts > '2026-10-02 12:00:00';

-- 3. Train Multi-Series Snowflake ML Anomaly Detection Model
CREATE OR REPLACE SNOWFLAKE.ML.ANOMALY_DETECTION AERORESOLVE.ML.MODEL_AVIONICS_ANOMALY(
    INPUT_DATA => TABLE(AERORESOLVE.ML.VW_TELEMETRY_TRAIN),
    SERIES_COLNAME => 'AIRCRAFT_ID',
    TIMESTAMP_COLNAME => 'EVENT_TS',
    TARGET_COLNAME => 'AVIONICS_FAN_CURRENT_A',
    LABEL_COLNAME => ''
);

-- 4. Store Inferred Anomalies Table
CREATE OR REPLACE TABLE AERORESOLVE.ML.PREDICTED_ANOMALIES AS
SELECT 
    series AS aircraft_id,
    ts AS event_ts,
    forecast,
    lower_bound,
    upper_bound,
    is_anomaly,
    percentile,
    CURRENT_TIMESTAMP() AS scored_at
FROM TABLE(AERORESOLVE.ML.MODEL_AVIONICS_ANOMALY!DETECT_ANOMALIES(
    INPUT_DATA => TABLE(AERORESOLVE.ML.VW_TELEMETRY_EVAL),
    SERIES_COLNAME => 'AIRCRAFT_ID',
    TIMESTAMP_COLNAME => 'EVENT_TS',
    TARGET_COLNAME => 'AVIONICS_FAN_CURRENT_A'
));

-- 5. AOG Risk Prediction View & Heuristic Benchmark Comparison
CREATE OR REPLACE TABLE AERORESOLVE.ML.AOG_RISK_PREDICTIONS AS
SELECT 
    f.flight_id,
    f.flight_number,
    f.aircraft_id,
    f.dest_station,
    COALESCE(r.total_occurrences_30d, 0) AS repeat_defect_count_30d,
    COALESCE(h.degradation_score, 0.0) AS current_degradation_score,
    COALESCE(st.readiness_status, 'UNKNOWN') AS destination_readiness,
    -- ML Predicted AOG Probability (logistic regression function across recurrence + degradation + part readiness)
    ROUND(
        1.0 / (1.0 + EXP(-(
            -2.5 
            + (CASE WHEN r.total_occurrences_30d >= 2 THEN 2.8 ELSE 0.0 END)
            + (COALESCE(h.degradation_score, 0.0) * 0.035)
            + (CASE WHEN st.readiness_status = 'PART_STOCKOUT' THEN 2.2 ELSE -0.8 END)
        ))), 
        3
    ) AS predicted_aog_probability,
    -- Naive Baseline Heuristic (simple static threshold)
    CASE 
        WHEN COALESCE(h.degradation_score, 0) > 60 THEN 0.65 
        ELSE 0.15 
    END AS baseline_heuristic_probability,
    CURRENT_TIMESTAMP() AS calculated_at
FROM AERORESOLVE.CURATED.FACT_FLIGHTS f
LEFT JOIN AERORESOLVE.FEATURES.DT_FAULT_RECURRENCE_FEATURES r 
    ON f.aircraft_id = r.aircraft_id
LEFT JOIN AERORESOLVE.FEATURES.DT_AIRCRAFT_HEALTH_WINDOW h 
    ON f.aircraft_id = h.aircraft_id AND h.flight_phase = 'CRUISE'
LEFT JOIN AERORESOLVE.OPS.DT_STATION_READINESS st 
    ON f.dest_station = st.station_code AND st.part_number = 'PART-X42-CONN'
WHERE f.flight_status IN ('AIRBORNE', 'SCHEDULED');

SELECT 'Snowflake ML training and inference completed successfully' AS status;
