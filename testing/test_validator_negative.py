"""
test_validator_negative.py
===========================
Automated unit test suite that feeds deliberately corrupted journey responses into the
JourneyEvaluator to verify that invalid or unverified journeys are correctly rejected.
"""

import os
import sys
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
_BENCHMARKS_DIR = os.path.join(_PROJECT_ROOT, "backend", "benchmarks")

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _BENCHMARKS_DIR not in sys.path:
    sys.path.insert(0, _BENCHMARKS_DIR)

from gtfs_reference_adapter import GTFSReferenceAdapter
from evaluator import JourneyEvaluator


@pytest.fixture
def evaluator():
    adapter = GTFSReferenceAdapter()
    return JourneyEvaluator(adapter)


@pytest.fixture
def base_test_case():
    return {
        "test_id": "NEG_TEST_001",
        "origin": "Kempegowda Bus Station",
        "destination": "Central Silk Board",
        "travel_date": "2026-09-28",
        "departure_time": "08:30",
        "journey_type": "direct",
        "expected_test_conditions": {"service_expected": True}
    }


def test_neg_01_non_existent_route_id(evaluator, base_test_case):
    """Case 1: Route ID that does not exist in GTFS reference feed."""
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "routes": ["NON_EXISTENT_ROUTE_9999"],
            "boarding_stops": ["Kempegowda Bus Station"],
            "alighting_stops": ["Central Silk Board"],
            "legs": [{
                "leg_index": 0,
                "leg_type": "bus",
                "route_id": "NON_EXISTENT_ROUTE_9999",
                "boarding_stop": "Kempegowda Bus Station",
                "alighting_stop": "Central Silk Board"
            }]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["bus_route_existence"]["status"] == "FAIL"


def test_neg_02_missing_route_id(evaluator, base_test_case):
    """Case 2: Bus leg with missing/empty route ID."""
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "routes": [""],
            "legs": [{
                "leg_index": 0,
                "leg_type": "bus",
                "route_id": "",
                "boarding_stop": "Kempegowda Bus Station",
                "alighting_stop": "Central Silk Board"
            }]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["bus_route_existence"]["status"] == "FAIL"


def test_neg_03_wrong_stop_sequence(evaluator, base_test_case):
    """Case 5: Boarding stop occurs AFTER alighting stop in sequence."""
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "routes": ["500-D"],
            "boarding_stops": ["Hebbal"],
            "alighting_stops": ["Central Silk Board"],
            "legs": [{
                "leg_index": 0,
                "leg_type": "bus",
                "route_id": "500-D",
                "boarding_stop": "Hebbal",               # Seq 35
                "alighting_stop": "Central Silk Board"   # Seq 1
            }]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["bus_stop_sequence"]["status"] == "FAIL"


def test_neg_04_direct_journey_with_multiple_bus_legs(evaluator, base_test_case):
    """Case 9: Direct journey expected but contains multiple bus legs."""
    base_test_case["journey_type"] = "direct"
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "transfers": 1,
            "routes": ["201-J", "500-D"],
            "legs": [
                {
                    "leg_index": 0,
                    "leg_type": "bus",
                    "route_id": "201-J",
                    "boarding_stop": "Kempegowda Bus Station",
                    "alighting_stop": "Banashankari"
                },
                {
                    "leg_index": 1,
                    "leg_type": "bus",
                    "route_id": "500-D",
                    "boarding_stop": "Banashankari",
                    "alighting_stop": "Central Silk Board"
                }
            ]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["direct_journey_expectation"]["status"] == "FAIL"


def test_neg_05_disconnected_transfer_endpoints(evaluator, base_test_case):
    """Case 7: Transfer journey with disconnected transfer endpoints (>500m apart)."""
    base_test_case["journey_type"] = "transfer"
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "transfers": 1,
            "routes": ["201-J", "500-D"],
            "legs": [
                {
                    "leg_index": 0,
                    "leg_type": "bus",
                    "route_id": "201-J",
                    "boarding_stop": "Kempegowda Bus Station",
                    "alighting_stop": "Hebbal"  # North Bengaluru
                },
                {
                    "leg_index": 1,
                    "leg_type": "bus",
                    "route_id": "500-D",
                    "boarding_stop": "Electronic City",  # South Bengaluru (~25km away)
                    "alighting_stop": "Central Silk Board"
                }
            ]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["transfer_continuity"]["status"] == "FAIL"


def test_neg_06_excessive_walking_distance(evaluator, base_test_case):
    """Case 8: Walking leg with excessive distance (>1.5km)."""
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "routes": ["500-D"],
            "legs": [
                {
                    "leg_index": 0,
                    "leg_type": "walk",
                    "route_id": "Walk",
                    "boarding_stop": "Kempegowda Bus Station",
                    "alighting_stop": "Indiranagar",
                    "distance_km": 5.0,  # 5 km walk!
                    "duration_mins": 60.0
                },
                {
                    "leg_index": 1,
                    "leg_type": "bus",
                    "route_id": "500-D",
                    "boarding_stop": "Indiranagar",
                    "alighting_stop": "Central Silk Board"
                }
            ]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["walk_feasibility"]["status"] == "FAIL"


def test_neg_07_unreached_destination(evaluator, base_test_case):
    """Case 10: Final leg alighting stop is unassigned or missing."""
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "routes": ["500-D"],
            "legs": [{
                "leg_index": 0,
                "leg_type": "bus",
                "route_id": "500-D",
                "boarding_stop": "Kempegowda Bus Station",
                "alighting_stop": "N/A"
            }]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "FAILED_VALIDATION"
    assert eval_out["checks"]["destination_reachability"]["status"] == "FAIL"


def test_neg_08_empty_no_route_when_expected(evaluator, base_test_case):
    """Case 11: Empty route options when service was expected."""
    api_res = {
        "is_success": True,
        "options_count": 0,
        "all_options": []
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] == "NO_ROUTE_FOUND"
    assert eval_out["is_missing_route"] is True


def test_pos_01_valid_direct_journey(evaluator, base_test_case):
    """Positive test: Perfectly valid direct journey passes evaluation."""
    base_test_case["origin"] = "Central Silk Board"
    base_test_case["destination"] = "Hebbal"
    api_res = {
        "is_success": True,
        "options_count": 1,
        "recommended_option": {
            "mode": "bmtc",
            "routes": ["500-D"],
            "boarding_stops": ["Central Silk Board"],
            "alighting_stops": ["Hebbal"],
            "legs": [{
                "leg_index": 0,
                "leg_type": "bus",
                "route_id": "500-D",
                "boarding_stop": "Central Silk Board",
                "alighting_stop": "Hebbal",
                "fare_inr": 30.0,
                "duration_mins": 55.0
            }]
        }
    }
    eval_out = evaluator.evaluate_test_result(base_test_case, api_res)
    assert eval_out["validation_status"] in ("PASSED", "UNVERIFIED")
    assert eval_out["checks"]["bus_route_existence"]["status"] == "PASS"
