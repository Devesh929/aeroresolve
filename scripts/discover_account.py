import os
import json
import snowflake.connector

token_path = os.path.expanduser('~/.snowflake/token.jwt')
conn = snowflake.connector.connect(
    user='DEVESH929',
    account='YGUIPVK-XK89675',
    authenticator='PROGRAMMATIC_ACCESS_TOKEN',
    token_file_path=token_path
)

cursor = conn.cursor()

def run_query(sql, fetch_all=True):
    try:
        cursor.execute(sql)
        if fetch_all:
            return True, cursor.fetchall()
        return True, cursor.fetchone()
    except Exception as e:
        return False, str(e)

print("=== ACCOUNT CONTEXT ===")
ok, ctx = run_query("SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_VERSION()")
print("Context:", ctx if ok else "Error: " + ctx)

account_id = ctx[0][0] if ok else "UNKNOWN"
region = ctx[0][1] if ok else "UNKNOWN"
role = ctx[0][2] if ok else "UNKNOWN"
warehouse = ctx[0][3] if ok else "UNKNOWN"
version = ctx[0][4] if ok else "UNKNOWN"

print("\n=== WAREHOUSES ===")
ok, whs = run_query("SHOW WAREHOUSES")
print(f"Warehouses found: {len(whs) if ok else whs}")
if ok:
    for w in whs:
        print(f" - {w[0]}: size={w[3]}, state={w[4]}")

print("\n=== CORTEX BASE MODELS ===")
ok, models = run_query("SHOW CORTEX BASE MODELS")
model_names = []
if ok:
    print(f"Models found ({len(models)}):")
    for m in models:
        # column names usually: model_name, etc.
        m_name = m[0]
        model_names.append(m_name)
        print(f" - {m_name}")
else:
    print("SHOW CORTEX BASE MODELS failed:", models)

print("\n=== CORTEX SEARCH AVAILABILITY ===")
ok, cs_check = run_query("SHOW CORTEX SEARCH SERVICES")
print("Cortex Search Service:", "AVAILABLE" if ok else f"FAIL: {cs_check}")

print("\n=== CORTEX LLM FUNCTION TEST (COMPLETE) ===")
ok, cortex_complete = run_query("SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-7b', 'Say hello')")
if not ok:
    # Try with another model or check error
    ok2, cortex_complete2 = run_query("SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', 'Say hello')")
    print("Cortex COMPLETE with mistral-7b:", cortex_complete)
    print("Cortex COMPLETE with snowflake-arctic:", cortex_complete2 if not ok2 else "SUCCESS")
else:
    print("Cortex COMPLETE SUCCESS:", cortex_complete[0][0][:50] if cortex_complete else "Empty")

print("\n=== ML FUNCTIONS AVAILABILITY ===")
ok, ml_check = run_query("SELECT SNOWFLAKE.ML.ANOMALY_DETECTION")
print("SNOWFLAKE.ML.ANOMALY_DETECTION check:", ok, ml_check[:100] if not ok else "Found")

print("\n=== SNOWPARK CONTAINER SERVICES (SPCS) ===")
ok, compute_pools = run_query("SHOW COMPUTE POOLS")
print("SPCS Compute Pools:", "AVAILABLE" if ok else f"UNAVAILABLE / ERROR: {compute_pools}")

print("\n=== STREAMLIT AVAILABILITY ===")
ok, streamlits = run_query("SHOW STREAMLITS")
print("Streamlits:", "AVAILABLE" if ok else f"ERROR: {streamlits}")

print("\n=== DYNAMIC TABLES AVAILABILITY ===")
ok, dt_check = run_query("SHOW DYNAMIC TABLES")
print("Dynamic Tables:", "AVAILABLE" if ok else f"ERROR: {dt_check}")

print("\n=== STREAMS & TASKS ===")
ok_s, streams = run_query("SHOW STREAMS")
ok_t, tasks = run_query("SHOW TASKS")
print(f"Streams: {'AVAILABLE' if ok_s else streams}, Tasks: {'AVAILABLE' if ok_t else tasks}")

print("\n=== CROSS-REGION INFERENCE CONFIG ===")
ok, cross_region = run_query("SHOW PARAMETERS LIKE 'ENABLE_CORTEX_CROSS_REGION' IN ACCOUNT")
print("ENABLE_CORTEX_CROSS_REGION:", cross_region if ok else "Error: " + str(cross_region))

cursor.close()
conn.close()
