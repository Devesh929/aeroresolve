"""
scripts/deploy_streamlit_to_snowflake.py
Deploys AeroResolve Operations Cockpit as a Streamlit in Snowflake (SiS) application.
"""

import os
import sys
import shutil
import glob

# Ensure workspace root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.connection import get_snowflake_connection

def prepare_stage_bundle(bundle_dir: str):
    """Prepares a clean staging directory with all required app and backend files."""
    if os.path.exists(bundle_dir):
        shutil.rmtree(bundle_dir)
    os.makedirs(bundle_dir, exist_ok=True)

    # 1. Copy app.py and environment.yml
    shutil.copy("frontend/streamlit/app.py", os.path.join(bundle_dir, "app.py"))
    shutil.copy("frontend/streamlit/environment.yml", os.path.join(bundle_dir, "environment.yml"))

    # 2. Copy backend package excluding __pycache__
    def ignore_pycache(dir, files):
        return [f for f in files if f == "__pycache__" or f.endswith(".pyc")]

    shutil.copytree("backend", os.path.join(bundle_dir, "backend"), ignore=ignore_pycache)
    print(f"[OK] Prepared deployment bundle in {bundle_dir}")

def upload_bundle_to_snowflake(bundle_dir: str, stage_name: str = "AERORESOLVE.APP.STREAMLIT_STAGE"):
    """Connects to Snowflake, ensures stage exists, and uploads bundle files."""
    conn = get_snowflake_connection(schema="APP")
    cur = conn.cursor()

    # 1. Create Stage if not exists
    print(f"[*] Ensuring stage {stage_name} exists...")
    cur.execute(f"CREATE STAGE IF NOT EXISTS {stage_name} DIRECTORY = (ENABLE = TRUE);")

    # 2. Find all files to upload
    abs_bundle_dir = os.path.abspath(bundle_dir)
    uploaded_count = 0
    for root, dirs, files in os.walk(abs_bundle_dir):
        # Skip pycache if any
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        rel_dir = os.path.relpath(root, abs_bundle_dir)
        stage_dir = "" if rel_dir == "." else rel_dir.replace("\\", "/")

        for file in files:
            if file.endswith(".pyc"):
                continue
            local_file_path = os.path.join(root, file).replace("\\", "/")
            stage_target = f"@{stage_name}/{stage_dir}/" if stage_dir else f"@{stage_name}/"
            
            # Snowflake PUT command requires forward slashes
            put_sql = f"PUT 'file://{local_file_path}' {stage_target} AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
            print(f"[*] Uploading {file} to {stage_target}...")
            cur.execute(put_sql)
            res = cur.fetchall()
            print(f"    -> {res[0][0]}: {res[0][4] if len(res[0]) > 4 else 'UPLOADED'}")
            uploaded_count += 1

    # 3. Refresh stage directory
    print(f"[*] Refreshing stage directory {stage_name}...")
    cur.execute(f"ALTER STAGE {stage_name} REFRESH;")

    # 4. List staged files
    print(f"[*] Listing files in stage {stage_name}:")
    cur.execute(f"LIST @{stage_name};")
    staged_files = cur.fetchall()
    for row in staged_files:
        print(f"    - {row[0]} ({row[1]} bytes)")

    # 5. Create or Replace Streamlit Application Object
    streamlit_name = "AERORESOLVE.APP.AERORESOLVE_COCKPIT"
    print(f"[*] Creating Streamlit application {streamlit_name}...")
    create_sql = f"""
    CREATE OR REPLACE STREAMLIT {streamlit_name}
      ROOT_LOCATION = '@{stage_name}'
      MAIN_FILE = 'app.py'
      QUERY_WAREHOUSE = 'AERORESOLVE_WH'
      TITLE = 'AeroResolve Operations Cockpit';
    """
    cur.execute(create_sql)
    print(f"[OK] Streamlit application {streamlit_name} created successfully!")

    # 6. Show Streamlit details
    cur.execute("SHOW STREAMLITS LIKE 'AERORESOLVE_COCKPIT' IN SCHEMA AERORESOLVE.APP;")
    app_info = cur.fetchall()
    cols = [d[0] for d in cur.description]
    app_dict = dict(zip(cols, app_info[0])) if app_info else {}
    print("\n" + "="*70)
    print(" STREAMLIT IN SNOWFLAKE DEPLOYMENT COMPLETE")
    print("="*70)
    for k, v in app_dict.items():
        print(f"  {k}: {v}")
    
    # Snowsight direct URL
    snowsight_url = "https://app.snowflake.com/me-central2.gcp/io91337/#/streamlit-apps/AERORESOLVE.APP.AERORESOLVE_COCKPIT"
    print("="*70)
    print(f"  LIVE SNOWSIGHT URL:\n  {snowsight_url}")
    print("="*70)

    cur.close()
    conn.close()

if __name__ == "__main__":
    bundle_path = os.path.join("deploy", "sis_bundle")
    prepare_stage_bundle(bundle_path)
    upload_bundle_to_snowflake(bundle_path)
