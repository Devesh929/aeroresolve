-- =====================================================================
-- AeroResolve: 07_cortex_search.sql
-- Cortex Search Service for Aircraft Technical Manuals & Maintenance Notes
-- =====================================================================

USE ROLE AERORESOLVE_DEV;
USE WAREHOUSE AERORESOLVE_WH;
USE DATABASE AERORESOLVE;
USE SCHEMA KNOWLEDGE;

-- Create Cortex Search Service over TECHNICAL_DOCUMENTS
CREATE OR REPLACE CORTEX SEARCH SERVICE AERORESOLVE.KNOWLEDGE.AERO_TECH_MANUALS_SEARCH
    ON content
    ATTRIBUTES ata_chapter, doc_type
    WAREHOUSE = AERORESOLVE_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            doc_id,
            title,
            ata_chapter,
            doc_type,
            summary,
            content
        FROM AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS
    );

SELECT 'Cortex Search Service created successfully' AS status;
