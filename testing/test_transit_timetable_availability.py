"""
testing/test_transit_timetable_availability.py
==============================================
Validates operating hours and timetable availability checks for:
- BMTC Bus (05:00 AM - 11:30 PM regular network; 24/7 for KIA routes)
- Namma Metro (05:00 AM - 11:00 PM Mon-Sat; 07:00 AM - 11:00 PM Sun)
- Compare / Journey Planner filtering and late-night cab prioritization
"""

import sys
import os
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_BACKEND = os.path.join(_ROOT, "backend")

if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from backend.main import is_metro_operational, is_bmtc_operational, metro_plan, bmtc_plan, compare, JourneyRequest, CompareRequest


def test_is_metro_operational_hours():
    # 2:00 AM Thursday -> Metro must be closed
    dt_2am = datetime(2026, 11, 5, 2, 0)
    is_op, next_svc, reason = is_metro_operational(dt_2am)
    assert not is_op
    assert next_svc == "05:00 AM"
    assert "closed" in reason.lower()

    # 10:00 AM Thursday -> Metro must be operational
    dt_10am = datetime(2026, 11, 5, 10, 0)
    is_op, next_svc, reason = is_metro_operational(dt_10am)
    assert is_op

    # 6:00 AM Sunday -> Metro opens at 7:00 AM on Sunday, so must be closed
    dt_sun_6am = datetime(2026, 11, 8, 6, 0)
    is_op, next_svc, reason = is_metro_operational(dt_sun_6am)
    assert not is_op
    assert next_svc == "07:00 AM"

    # 7:30 AM Sunday -> Metro operational
    dt_sun_730am = datetime(2026, 11, 8, 7, 30)
    is_op, next_svc, reason = is_metro_operational(dt_sun_730am)
    assert is_op


def test_is_bmtc_operational_hours():
    # 2:00 AM regular bus (500D) -> Must be closed
    dt_2am = datetime(2026, 11, 5, 2, 0)
    is_op, next_svc, reason = is_bmtc_operational(dt_2am, ["500D", "356"])
    assert not is_op
    assert next_svc == "05:00 AM"
    assert "not operational" in reason.lower() or "do not operate" in reason.lower()

    # 2:00 AM 24/7 airport route (KIA-9) -> Operational
    is_op, next_svc, reason = is_bmtc_operational(dt_2am, ["KIA-9"])
    assert is_op

    # 10:00 AM regular bus -> Operational
    dt_10am = datetime(2026, 11, 5, 10, 0)
    is_op, next_svc, reason = is_bmtc_operational(dt_10am, ["500D"])
    assert is_op


def test_metro_plan_midnight_closed():
    req = JourneyRequest(
        source="Majestic Metro Station",
        destination="Indiranagar Metro Station",
        time="02:00",
        preference="cost"
    )
    res = metro_plan(req)
    assert res["available"] is False
    assert res["operational"] is False
    assert res["service_status"] == "closed"
    assert res["next_service"] in ["05:00 AM", "07:00 AM"]


def test_bmtc_plan_midnight_closed():
    req = JourneyRequest(
        source="Kempegowda Bus Station",
        destination="Indiranagar Police Station",
        time="02:00",
        preference="cost"
    )
    res = bmtc_plan(req)
    assert res["available"] is False
    assert res["operational"] is False
    assert res["service_status"] == "closed"
    assert "05:00 AM" in res["next_service"]


def test_compare_midnight_prioritizes_247_modes():
    # At 2:00 AM, BMTC and Metro are non-operational, so compare must recommend Cab or Car
    req = CompareRequest(
        source="Majestic",
        destination="Indiranagar",
        time="02:00",
        preference="cost"
    )
    res = compare(req)
    results = res["results"]

    # Metro and regular BMTC must not be operational
    assert results["metro"]["available"] is False or results["metro"].get("operational") is False
    assert results["bmtc"]["available"] is False or results["bmtc"].get("operational") is False

    # Cab or Car must be recommended
    rec_mode = None
    for m, d in results.items():
        if d.get("recommended"):
            rec_mode = m
            break

    assert rec_mode in ["cab", "car"], f"Expected Cab or Car recommended at 2 AM, but got {rec_mode}"
