import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from main import app

client = TestClient(app)
IST = ZoneInfo("Asia/Kolkata")

# Test Route 1: CHRIST University, Hosur Road to Nexus Koramangala
# On 2026-07-15 morning (08:43)
resp = client.post("/api/cab/estimate", json={
    "src_lat": 12.93574,
    "src_lng": 77.60595,
    "dst_lat": 12.93483,
    "dst_lng": 77.61134,
    "time": "08:43",
    "provider": "rapido"
})

print("Status Code:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    rapido_res = data["results"].get("rapido", {})
    estimates = {est["vehicle_name"]: est["cost"] for est in rapido_res.get("estimates", [])}
    print("Estimates for Route 1 Morning:")
    for vname, cost in estimates.items():
        print(f"  {vname}: {cost}")
else:
    print("Error:", resp.text)
