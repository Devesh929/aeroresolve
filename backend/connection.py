"""
backend/connection.py
Centralized Snowflake connection provider for AeroResolve.
"""
import os
import snowflake.connector

def get_snowflake_connection(schema: str = "CURATED"):
    token_path = os.path.expanduser('~/.snowflake/token.jwt')
    conn = snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE',
        schema=schema
    )
    return conn
