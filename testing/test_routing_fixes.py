"""
testing/test_routing_fixes.py
=============================
Tests verifying the fixes for distance calculation, proximity route joining, and time filtering.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_hosa_road_to_hope_farm_distance():
    """Verify that Hosa Road to Hope Farm route distance is accurate (not using the teleportation bug)."""
    resp = client.post("/api/bmtc/plan", json={
        "source": "hosa road",
        "destination": "hope farm"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    # The actual distance is ~17-18km. The bug caused it to show 9.4km.
    assert data["distance"] >= 15.0


def test_electronic_city_to_koli_farm_gate_transfer():
    """Verify that we suggest a route via T. John College / Tjohn College Cross."""
    resp = client.post("/api/bmtc/plan", json={
        "source": "electronic city",
        "destination": "koli farm gate bannerghatta road"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    
    # Check if we find a transfer using 378 (or V-378) and 365 (or 366, 367, 370, 372)
    # The segments should be present
    segments = data["segments"]
    assert len(segments) > 0
    routes = [s["route"] for s in segments]
    
    # We should have found a transfer route using 378
    assert any("378" in r for r in routes)


def test_preferred_time_propagation():
    """Verify that passing a preferred time calculates segment times starting from that time."""
    preferred_time = "15:00"
    resp = client.post("/api/bmtc/plan", json={
        "source": "electronic city",
        "destination": "koli farm gate bannerghatta road",
        "time": preferred_time
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    
    # The first segment's departure should be after or equal to the requested time (15:00)
    segments = data["segments"]
    assert len(segments) > 0
    first_dep = segments[0]["departure"]
    dep_h, dep_m = map(int, first_dep.split(":"))
    
    # Should depart at or after 15:00
    assert (dep_h * 60 + dep_m) >= (15 * 60)
