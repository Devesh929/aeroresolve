"""
backend/connection.py
Centralized Snowflake connection provider for AeroResolve.
Supports:
1. Streamlit in Snowflake (SiS) via get_active_session()
2. Streamlit Community Cloud via st.secrets["snowflake"]
3. Local execution via ~/.snowflake/token.jwt or environment variables
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
    # 1. Streamlit in Snowflake (SiS)
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

    # 2. Streamlit Community Cloud (st.secrets)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "snowflake" in st.secrets:
            sf_conf = st.secrets["snowflake"]
            kwargs = {
                "user": sf_conf.get("user", "DEVESH929"),
                "account": sf_conf.get("account", "YGUIPVK-XK89675"),
                "role": sf_conf.get("role", "AERORESOLVE_DEV"),
                "warehouse": sf_conf.get("warehouse", "AERORESOLVE_WH"),
                "database": sf_conf.get("database", "AERORESOLVE"),
                "schema": schema or sf_conf.get("schema", "CURATED")
            }
            if "token" in sf_conf:
                kwargs["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
                kwargs["token"] = str(sf_conf["token"]).strip()
            elif "password" in sf_conf:
                kwargs["password"] = sf_conf["password"]
            elif "token_file_path" in sf_conf:
                kwargs["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
                kwargs["token_file_path"] = sf_conf["token_file_path"]
            return snowflake.connector.connect(**kwargs)
    except Exception:
        pass

    # 3. Local fallback (PAT token file or environment variables)
    token_path = os.environ.get("SNOWFLAKE_TOKEN_FILE", os.path.expanduser('~/.snowflake/token.jwt'))
    if os.path.exists(token_path):
        return snowflake.connector.connect(
            user=os.environ.get("SNOWFLAKE_USER", "DEVESH929"),
            account=os.environ.get("SNOWFLAKE_ACCOUNT", "YGUIPVK-XK89675"),
            authenticator='PROGRAMMATIC_ACCESS_TOKEN',
            token_file_path=token_path,
            role=os.environ.get("SNOWFLAKE_ROLE", "AERORESOLVE_DEV"),
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "AERORESOLVE_WH"),
            database=os.environ.get("SNOWFLAKE_DATABASE", "AERORESOLVE"),
            schema=schema
        )
    elif "SNOWFLAKE_PASSWORD" in os.environ:
        return snowflake.connector.connect(
            user=os.environ.get("SNOWFLAKE_USER", "DEVESH929"),
            account=os.environ.get("SNOWFLAKE_ACCOUNT", "YGUIPVK-XK89675"),
            password=os.environ["SNOWFLAKE_PASSWORD"],
            role=os.environ.get("SNOWFLAKE_ROLE", "AERORESOLVE_DEV"),
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "AERORESOLVE_WH"),
            database=os.environ.get("SNOWFLAKE_DATABASE", "AERORESOLVE"),
            schema=schema
        )

    # Final PAT fallback
    return snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE',
        schema=schema
    )
