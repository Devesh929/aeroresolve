-- =====================================================================
-- AeroResolve: 04_streams_and_tasks.sql
-- Event-Driven Stream & Task Pipeline for In-Flight Technical Fault Detection
-- =====================================================================

USE ROLE AERORESOLVE_DEV;
USE WAREHOUSE AERORESOLVE_WH;
USE DATABASE AERORESOLVE;

-- 1. Stream on In-Flight Fault Events Table
CREATE OR REPLACE STREAM AERORESOLVE.CURATED.STREAM_NEW_FAULT_EVENTS
    ON TABLE AERORESOLVE.CURATED.FACT_FAULT_EVENTS
    APPEND_ONLY = TRUE
    COMMENT = 'Captures newly emitted ACARS/BITE in-flight technical fault events for investigation';

-- 2. Stream on High-Risk Telemetry Ingestion
CREATE OR REPLACE STREAM AERORESOLVE.RAW.STREAM_TELEMETRY_INGEST
    ON TABLE AERORESOLVE.RAW.RAW_TELEMETRY_STREAM
    APPEND_ONLY = TRUE
    COMMENT = 'Captures newly arrived live telemetry packets for anomaly inspection';

-- 3. Stored Procedure to Initialize Investigation Case upon New Fault
CREATE OR REPLACE PROCEDURE AERORESOLVE.AGENTS.SP_INIT_FAULT_INVESTIGATION()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    rows_processed INT := 0;
BEGIN
    -- Insert new agent cases from stream
    INSERT INTO AERORESOLVE.AUDIT.AGENT_CASE (
        case_id, aircraft_id, flight_id, case_title, opened_ts, status,
        current_hypothesis, confidence_score, aog_risk_score
    )
    SELECT 
        'CASE-' || s.aircraft_id || '-' || TO_VARCHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD-HH24MISS'),
        s.aircraft_id,
        s.flight_id,
        'In-Flight Fault: ' || s.fault_code || ' on ' || s.aircraft_id,
        CURRENT_TIMESTAMP(),
        'INVESTIGATING',
        'Initial Alert: ' || s.fault_code || ' detected at ' || s.altitude_ft || 'ft',
        0.50,
        0.75
    FROM AERORESOLVE.CURATED.STREAM_NEW_FAULT_EVENTS s
    WHERE s.METADATA$ACTION = 'INSERT';

    rows_processed := SQLROWCOUNT;
    RETURN 'Processed ' || rows_processed || ' new fault events into investigation cases.';
END;
$$;

-- 4. Serverless / Warehouse Task Triggered on Stream Data
CREATE OR REPLACE TASK AERORESOLVE.AGENTS.TASK_PROCESS_IN_FLIGHT_FAULTS
    WAREHOUSE = AERORESOLVE_WH
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('AERORESOLVE.CURATED.STREAM_NEW_FAULT_EVENTS')
AS
    CALL AERORESOLVE.AGENTS.SP_INIT_FAULT_INVESTIGATION();

-- Suspend task by default until activated to control credit spend (Operating Principle & Cost guardrail)
ALTER TASK AERORESOLVE.AGENTS.TASK_PROCESS_IN_FLIGHT_FAULTS SUSPEND;

SELECT 'Streams, Procedure, and Task created successfully' AS status;
