import os
import sys
import snowflake.connector

def execute_sql(file_path):
    print(f"Executing SQL file: {file_path}")
    token_path = os.path.expanduser('~/.snowflake/token.jwt')
    conn = snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE'
    )
    cursor = conn.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Use Snowflake connector native execute_string which parses multi-statement scripts properly
    res_cursors = conn.execute_string(sql_content)
    for idx, c in enumerate(res_cursors, 1):
        try:
            res = c.fetchall()
            q = c.query.replace('\n', ' ').strip()[:70]
            print(f"[{idx}] OK: {q}...")
        except Exception as e:
            print(f"[{idx}] Status for {c.query[:50]}: {e}")

    print("All statements executed successfully!")
    cursor.close()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python execute_sql_file.py <path_to_sql_file>")
        sys.exit(1)
    execute_sql(sys.argv[1])
