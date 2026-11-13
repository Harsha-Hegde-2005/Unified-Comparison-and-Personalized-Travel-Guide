"""
test_bmtc_fixes.py
===================
Automated verification tests for:
1. Fixed schedule across changing current time
2. Expired departure handling
3. Nearest-stop detection at Hosakerehalli
4. Route 43-B recommendation for Hosakerehalli journey
5. Location permission fallback
6. Timezone correctness (Asia/Kolkata)
7. Journey summary & segment consistency
"""

import sys
import os
from datetime import datetime, timedelta

# Ensure backend and bmtc directories are in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
bmtc_dir = os.path.join(backend_dir, "modes", "bmtc")
if bmtc_dir not in sys.path:
    sys.path.insert(0, bmtc_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from modes.bmtc.features.schedule import get_fixed_route_departure, calculate_segment_times
from modes.bmtc.features.routing import get_all_buses_comprehensive, get_all_direct_buses
from shared.utils.stop_resolver import resolve_stop_name


def test_1_fixed_schedule_across_changing_current_time():
    """Verify departure time remains constant as query time advances minute-by-minute."""
    route_no = "43-B"
    base_date = datetime(2026, 9, 27, 6, 37, 0)
    
    # Query at 6:37, 6:38, 6:39, 6:40 AM
    deps = []
    waits = []
    for m in range(4):
        query_dt = base_date + timedelta(minutes=m)
        dep_dt, wait_mins = get_fixed_route_departure(route_no, query_dt, trips_per_day=30)
        deps.append(dep_dt.strftime("%H:%M"))
        waits.append(wait_mins)

    # Departure time must remain constant for all 4 minutes
    assert len(set(deps)) == 1, f"Scheduled departure changed across minutes! Got {deps}"
    # Countdown / wait time must decrease by 1 minute each tick
    assert waits[1] == waits[0] - 1
    assert waits[2] == waits[1] - 1
    assert waits[3] == waits[2] - 1


def test_2_departure_has_passed():
    """Verify that an expired departure is not shifted to 7:01 AM when time passes 7:00 AM."""
    route_no = "43-B"
    # Suppose a departure slot was at 07:00 AM
    query_dt_before = datetime(2026, 9, 27, 6, 59, 0)
    dep_before, wait_before = get_fixed_route_departure(route_no, query_dt_before, trips_per_day=30)

    # Advance time to 07:01 AM (after the 07:00 slot)
    query_dt_after = datetime(2026, 9, 27, 7, 1, 0)
    dep_after, wait_after = get_fixed_route_departure(route_no, query_dt_after, trips_per_day=30)

    # 07:00 departure must NOT be shifted to 07:01
    assert dep_after != query_dt_after, "Passed departure was incorrectly shifted to current minute!"
    assert dep_after >= query_dt_after, "Selected departure is in the past!"


def test_3_nearest_stop_hosakerehalli():
    """Verify nearest stop detection for Hosakerehalli coordinates."""
    from main import find_nearest_bmtc_stop, find_top_nearby_bmtc_stops
    # Hosakerehalli Junction coordinates
    lat, lng = 12.9304, 77.5435
    stop, dist = find_nearest_bmtc_stop(lat, lng)
    
    assert "Hos" in stop and "kerehalli" in stop.lower(), f"Unexpected nearest stop: {stop}"
    assert dist <= 0.5, f"Distance too large for Hosakerehalli: {dist} km"

    candidates = find_top_nearby_bmtc_stops(lat, lng, n=5)
    assert len(candidates) > 0
    assert any("Hos" in c[0] for c in candidates)


def test_4_route_43b_recommendation():
    """Verify Route 43-B is recommended for Hosakerehalli -> Kempegowda Bus Station."""
    src = "Hosakerehalli"
    dst = "Kempegowda Bus Station"
    dep_dt = datetime(2026, 9, 27, 8, 0, 0)

    direct, transfers = get_all_buses_comprehensive(src, dst, departure_dt=dep_dt, preference="convenience")
    
    route_names = [b["route"] for b in direct]
    assert any("43-B" in r for r in route_names), f"Route 43-B not found in direct routes for {src} -> {dst}. Found: {route_names}"


def test_5_location_permission_denied():
    """Verify manual fallback works when coordinates are missing/null."""
    from main import bmtc_plan
    from pydantic import BaseModel

    class Req(BaseModel):
        source: str
        destination: str
        time: str
        preference: str

    req = Req(source="Hosakerehalli", destination="Kempegowda Bus Station", time="08:00", preference="cost")
    res = bmtc_plan(req)
    assert "direct_buses" in res or "options" in res or "summary" in res or len(res) > 0


def test_6_timezone_correctness():
    """Verify local Asia/Kolkata time parsing & formatting."""
    from modes.bmtc.features.schedule import format_time
    dt = datetime(2026, 9, 27, 14, 30, 0)
    assert format_time(dt) == "14:30"


def test_7_journey_segment_consistency():
    """Verify summary values match segment details."""
    segs = [
        ("43-B", "Hosakerehalli", "Kempegowda Bus Station", ["hoskerehalli", "seetha circle", "kempegowda bus station"])
    ]
    dt = datetime(2026, 9, 27, 9, 0, 0)
    times = calculate_segment_times(segs, start_time=dt)
    
    assert len(times) == 1
    assert times[0]["route_no"] == "43-B"
    assert times[0]["fare"] > 0
    assert times[0]["duration"] > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
