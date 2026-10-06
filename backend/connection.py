"""
backend/connection.py
Centralized Snowflake connection provider for AeroResolve.
"""
import os
import snowflake.connector

class _SnowparkConnectionProxy:
    """Wrapper around active Snowpark session connection to prevent accidental closure in SiS."""
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        # In SiS, do not close the underlying active Snowpark session connection
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)

def get_snowflake_connection(schema: str = "CURATED"):
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        conn = session.connection
        if schema:
            try:
                conn.cursor().execute(f"USE SCHEMA AERORESOLVE.{schema}")
            except Exception:
                pass
        return _SnowparkConnectionProxy(conn)
    except Exception:
        pass

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
