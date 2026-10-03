import sys, os
from fastapi.testclient import TestClient

# Add backend directory to path
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, _BACKEND)

from main import app, evaluate_bmtc_short_distance

client = TestClient(app)

def test_evaluate_bmtc_short_distance_high():
    # 0.5 km with 5 direct buses -> HIGH availability
    res = evaluate_bmtc_short_distance(0.5, direct_buses=["201", "500-D", "500-CA", "500-K", "201-Q"])
    assert res is not None
    assert res["is_short_distance"] is True
    assert res["availability"] == "HIGH"
    assert res["recommendation"] == "bmtc"
    assert res["walking_time_mins"] == 6  # (0.5 / 5) * 60 = 6 mins

def test_evaluate_bmtc_short_distance_medium():
    # 0.5 km with 2 direct buses -> MEDIUM availability
    res = evaluate_bmtc_short_distance(0.5, direct_buses=["201", "500-D"])
    assert res is not None
    assert res["availability"] == "MEDIUM"
    assert res["recommendation"] == "both"

def test_evaluate_bmtc_short_distance_low():
    # 0.7 km with 1 direct bus -> LOW availability
    res = evaluate_bmtc_short_distance(0.7, direct_buses=["201"])
    assert res is not None
    assert res["availability"] == "LOW"
    assert res["recommendation"] == "walk"
    assert res["walking_time_mins"] == 8  # (0.7 / 5) * 60 = 8.4 -> 8 mins

def test_evaluate_bmtc_short_distance_none():
    # 0.6 km with 0 direct buses -> NONE availability
    res = evaluate_bmtc_short_distance(0.6, direct_buses=[])
    assert res is not None
    assert res["availability"] == "NONE"
    assert res["recommendation"] == "walk"
    assert res["walking_time_mins"] == 7  # (0.6 / 5) * 60 = 7.2 -> 7 mins

def test_evaluate_bmtc_short_distance_over_1km():
    # 1.0 km -> Not short distance
    assert evaluate_bmtc_short_distance(1.0, direct_buses=["201"]) is None
    # 1.5 km -> Not short distance
    assert evaluate_bmtc_short_distance(1.5, direct_buses=["201"]) is None

def test_compare_endpoint_short_distance_cab_warning():
    # Test coordinates ~0.5 km apart (e.g. within Indiranagar)
    resp = client.post("/api/compare", json={
        "source": "12.9784, 77.6408",
        "destination": "12.9820, 77.6440"
    })
    assert resp.status_code == 200
    data = resp.json()

    # Verify cab short distance warning
    if "cab" in data["results"] and data["results"]["cab"].get("available"):
        cab = data["results"]["cab"]
        if cab.get("distance", 999) < 1.0:
            assert cab.get("is_short_distance") is True
            assert "short_distance_warning" in cab
            assert "drivers may be less likely" in cab["short_distance_warning"]

    # Verify BMTC short distance info if BMTC result returned
    if "bmtc" in data["results"] and data["results"]["bmtc"].get("available"):
        bmtc = data["results"]["bmtc"]
        if bmtc.get("distance", 999) < 1.0:
            assert "short_distance_info" in bmtc
            info = bmtc["short_distance_info"]
            assert info["is_short_distance"] is True
            assert info["availability"] in ["HIGH", "MEDIUM", "LOW", "NONE"]

if __name__ == "__main__":
    print("Running test_evaluate_bmtc_short_distance_high...")
    test_evaluate_bmtc_short_distance_high()
    print("Running test_evaluate_bmtc_short_distance_medium...")
    test_evaluate_bmtc_short_distance_medium()
    print("Running test_evaluate_bmtc_short_distance_low...")
    test_evaluate_bmtc_short_distance_low()
    print("Running test_evaluate_bmtc_short_distance_none...")
    test_evaluate_bmtc_short_distance_none()
    print("Running test_evaluate_bmtc_short_distance_over_1km...")
    test_evaluate_bmtc_short_distance_over_1km()
    print("Running test_compare_endpoint_short_distance_cab_warning...")
    test_compare_endpoint_short_distance_cab_warning()
    print("ALL SHORT DISTANCE TESTS PASSED SUCCESSFULLY!")

