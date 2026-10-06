import os
import snowflake.connector
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from data_generator.telemetry import simulate_flight_telemetry

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
cs = conn.cursor()
cs.execute("""
    SELECT flight_id, flight_number, aircraft_id, route_id, origin_station, dest_station, 
           TO_VARCHAR(scheduled_departure_ts, 'YYYY-MM-DD HH24:MI:SS'), flight_status, passenger_count
    FROM AERORESOLVE.CURATED.FACT_FLIGHTS 
    WHERE aircraft_id IN ('ABR-001', 'ABR-002', 'ABR-009') AND flight_status = 'LANDED'
    LIMIT 20
""")
cols = ['flight_id', 'flight_number', 'aircraft_id', 'route_id', 'origin_station', 'dest_station', 'scheduled_departure_ts', 'flight_status', 'passenger_count']
fls = [dict(zip(cols, r)) for r in cs.fetchall()]
print(f"Found {len(fls)} healthy flights for baseline training.")

records = []
for f in fls:
    records.extend(simulate_flight_telemetry(f, sample_interval_secs=30))

print(f"Generated {len(records)} healthy telemetry records.")
df = pd.DataFrame(records)
df.columns = [c.upper() for c in df.columns]
write_pandas(conn, df, 'FACT_TELEMETRY', schema='CURATED', quote_identifiers=False)
print("Loaded healthy telemetry into CURATED.FACT_TELEMETRY successfully!")
conn.close()
