-- =====================================================================
-- AeroResolve: 01_bootstrap_security.sql
-- Idempotent Security, Role, Warehouse, Database & Schemas Initialization
-- =====================================================================

-- 1. Create Role under SECURITYADMIN
USE ROLE SECURITYADMIN;
CREATE ROLE IF NOT EXISTS AERORESOLVE_DEV
    COMMENT = 'Dedicated engineering & operational role for AeroResolve platform';

GRANT ROLE AERORESOLVE_DEV TO ROLE SYSADMIN;
GRANT ROLE AERORESOLVE_DEV TO USER DEVESH929;

-- 2. Create Warehouse and Database under SYSADMIN / ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS AERORESOLVE_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Dedicated AeroResolve computation warehouse';

GRANT USAGE, OPERATE ON WAREHOUSE AERORESOLVE_WH TO ROLE AERORESOLVE_DEV;

CREATE DATABASE IF NOT EXISTS AERORESOLVE
    COMMENT = 'AeroResolve: Aircraft Health-to-Action Platform Database';

GRANT ALL PRIVILEGES ON DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;

-- 3. Create Schemas
CREATE SCHEMA IF NOT EXISTS AERORESOLVE.RAW
    COMMENT = 'Raw append-only telemetry and streaming ingest';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.CURATED
    COMMENT = 'Cleaned, typed, and deduplicated dimensional and operational tables';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.FEATURES
    COMMENT = 'Dynamic tables, rolling aggregations, and feature store';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.ML
    COMMENT = 'Snowflake ML anomaly detection and AOG prediction models';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.KNOWLEDGE
    COMMENT = 'Unstructured synthetic manuals, procedures, and Cortex Search staging';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.SEMANTIC
    COMMENT = 'Snowflake Semantic Views for governed analytical reasoning';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.AGENTS
    COMMENT = 'Cortex Agent definitions, tool specifications, and prompt registries';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.OPS
    COMMENT = 'Active operational plans, flight tracking, and part repositioning';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.APP
    COMMENT = 'Application state, user preferences, and replay metadata';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.EVAL
    COMMENT = 'Private ground-truth evaluation datasets and benchmark test cases';

CREATE SCHEMA IF NOT EXISTS AERORESOLVE.AUDIT
    COMMENT = 'Audit trails, agent reasoning traces, tool executions, and MCP actions';

-- Grant Schema Privileges to AERORESOLVE_DEV
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;
GRANT ALL PRIVILEGES ON ALL TABLES IN DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;
GRANT ALL PRIVILEGES ON ALL VIEWS IN DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN DATABASE AERORESOLVE TO ROLE AERORESOLVE_DEV;

-- 4. Grant Cortex User Role for AI Features
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE AERORESOLVE_DEV;

-- Success verification
SELECT 'AeroResolve Bootstrap Successfully Completed' AS status;
