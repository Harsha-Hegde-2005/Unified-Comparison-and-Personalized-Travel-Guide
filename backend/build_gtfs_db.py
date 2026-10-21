import os
import sys
import sqlite3
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _REPO)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "modes", "bmtc"))

import pandas as pd
from core.config import GTFS_STOP_TIMES, GTFS_TRIPS, GTFS_ROUTES, GTFS_STOPS

db_path = os.path.join(_REPO, "database", "gtfs_index.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except Exception:
        pass

print("Building GTFS SQLite Schedule Index at:", db_path)
t0 = time.time()
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Stops table
print("Indexing stops...")
gtfs_stops = pd.read_csv(GTFS_STOPS, dtype={"stop_id": str, "stop_name": str})

def clean_stop_name(name):
    if not isinstance(name, str):
        return name
    for p in ["CS-", "CS "]:
        if name.upper().startswith(p):
            return name[len(p):].strip()
    return name

gtfs_stops["clean_name"] = gtfs_stops["stop_name"].apply(clean_stop_name)
gtfs_stops["stop_norm"] = gtfs_stops["clean_name"].str.strip().str.lower()
gtfs_stops[["stop_id", "clean_name", "stop_norm"]].to_sql("stops", conn, if_exists="replace", index=False)
cur.execute("CREATE INDEX IF NOT EXISTS idx_stops_norm ON stops(stop_norm);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_stops_id ON stops(stop_id);")

# 2. Join routes, trips, stop_times
print("Joining routes, trips and stop_times...")
trips = pd.read_csv(GTFS_TRIPS, dtype={"route_id": str, "trip_id": str})
routes = pd.read_csv(GTFS_ROUTES, dtype={"route_id": str, "route_short_name": str})
merged_trips = trips.merge(routes[["route_id", "route_short_name"]], on="route_id", how="inner")

stop_times = pd.read_csv(GTFS_STOP_TIMES, dtype={"trip_id": str, "stop_id": str, "stop_sequence": int})
st = stop_times.merge(merged_trips[["trip_id", "route_short_name"]], on="trip_id", how="inner")
st = st[["route_short_name", "stop_id", "stop_sequence", "departure_time", "arrival_time", "trip_id"]].dropna(subset=["route_short_name", "departure_time"])

print("Writing route_stop_times to sqlite...")
st.to_sql("route_stop_times", conn, if_exists="replace", index=False)
cur.execute("CREATE INDEX IF NOT EXISTS idx_rst_route ON route_stop_times(route_short_name);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_rst_trip ON route_stop_times(trip_id);")
conn.commit()

print(f"Built gtfs_index.db successfully in {time.time()-t0:.2f}s! Size: {os.path.getsize(db_path)/1024/1024:.2f} MB")
conn.close()
