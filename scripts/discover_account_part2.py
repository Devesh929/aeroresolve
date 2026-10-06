import os
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

print("=== ACCOUNT PARAMETERS (CORTEX) ===")
ok, res = run_query("SHOW PARAMETERS LIKE '%CORTEX%' IN ACCOUNT")
if ok:
    for r in res:
        print(f"Param: {r[0]} = {r[1]} (default={r[2]})")
else:
    print("Error:", res)

print("\n=== TEST CORTEX MODELS ===")
test_models = ['mistral-7b', 'mistral-large2', 'llama3-8b', 'llama3.1-8b', 'llama3.1-70b', 'claude-3-5-sonnet', 'snowflake-arctic', 'gemini-1.5-flash', 'cortex-analyst']
for m in test_models:
    ok, res = run_query(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{m}', 'Ping')")
    if ok:
        print(f" - {m}: SUCCESS ({str(res[0][0])[:30].strip()})")
    else:
        print(f" - {m}: FAILED ({str(res)[:100]})")

print("\n=== CHECK ML FUNCTIONS SYNTAX ===")
ok, res = run_query("SHOW USER LIBRARIES IN SYSTEM$PACKAGES")
# check if snowflake.ml is available

print("\n=== CHECK SEMANTIC VIEW CAPABILITY ===")
# test parsing of SEMANTIC VIEW
ok, res = run_query("SHOW VIEWS LIKE '%SEMANTIC%'")
print("Semantic views check:", ok, res)

print("\n=== CHECK CORTEX AGENT / REST API ===")
# test cortex agent role/functions
ok, res = run_query("SHOW ROLES LIKE '%CORTEX%'")
print("Cortex roles:", res if ok else "Error: " + str(res))

cursor.close()
conn.close()
