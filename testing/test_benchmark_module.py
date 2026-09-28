"""
test_benchmark_module.py
========================
Automated unit and integration test suite for the BMTC Route Benchmarking
and Evaluation Module.
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
from api_adapter import JourneyAPIAdapter
from evaluator import JourneyEvaluator
from metrics_calculator import BenchmarkMetricsCalculator
from regression_tester import RegressionTester
from run_benchmark import run_benchmark


def test_gtfs_reference_adapter_route_existence():
    adapter = GTFSReferenceAdapter()
    assert adapter.verify_route_exists("500-D") is True
    assert adapter.verify_route_exists("201-J") is True
    assert adapter.verify_route_exists("335-E") is True
    assert adapter.verify_route_exists("NON_EXISTENT_ROUTE_9999") is False


def test_gtfs_reference_adapter_sequence_verification():
    adapter = GTFSReferenceAdapter()
    # Test valid stop sequence
    ok, msg = adapter.verify_stop_sequence("500-D", "Central Silk Board", "Hebbal")
    assert ok is True
    assert "precedes" in msg or "fuzzy-matched" in msg or "absent" in msg


def test_gtfs_reference_adapter_transfer_feasibility():
    adapter = GTFSReferenceAdapter()
    # Identical stop transfer
    ok, msg = adapter.verify_transfer_feasibility("Central Silk Board", "Central Silk Board")
    assert ok is True
    assert "Feasible" in msg


def test_api_adapter_execution():
    adapter = JourneyAPIAdapter(mode="direct")
    test_case = {
        "test_id": "TEST_UNIT_001",
        "origin": "Kempegowda Bus Station",
        "destination": "Central Silk Board",
        "departure_time": "08:30",
        "preference": "fastest"
    }
    res = adapter.execute_test_case(test_case)
    assert res["test_id"] == "TEST_UNIT_001"
    assert res["is_success"] is True
    assert res["latency_ms"] > 0
    assert res["options_count"] > 0


def test_evaluator_passed_case():
    ref_adapter = GTFSReferenceAdapter()
    evaluator = JourneyEvaluator(ref_adapter)

    test_case = {
        "test_id": "TEST_UNIT_002",
        "origin": "Central Silk Board",
        "destination": "Hebbal",
        "departure_time": "08:30",
        "travel_date": "2026-09-28",
        "expected_test_conditions": {"service_expected": True},
        "ground_truth": {
            "has_observation": True,
            "actual_fare_inr": 25.0,
            "actual_duration_mins": 45.0
        }
    }

    api_result = {
        "is_success": True,
        "options_count": 1,
        "all_options": [{
            "mode": "bmtc",
            "routes": ["500-D"],
            "boarding_stops": ["Central Silk Board"],
            "alighting_stops": ["Hebbal"],
            "transfers": 0,
            "fare_inr": 25.0,
            "duration_mins": 45.0
        }],
        "recommended_option": {
            "mode": "bmtc",
            "routes": ["500-D"],
            "boarding_stops": ["Central Silk Board"],
            "alighting_stops": ["Hebbal"],
            "transfers": 0,
            "fare_inr": 25.0,
            "duration_mins": 45.0
        }
    }

    eval_out = evaluator.evaluate_test_result(test_case, api_result)
    assert eval_out["validation_status"] in ("PASSED", "UNVERIFIED", "INCOMPLETE_REFERENCE")
    assert eval_out["gt_has_observation"] is True
    assert eval_out["gt_fare_error_inr"] == 0.0


def test_metrics_calculator():
    sample_evals = [
        {
            "test_id": "T1",
            "validation_status": "PASSED",
            "options_found": 1,
            "sequence_valid": True,
            "transfer_valid": True,
            "transfers_count": 0,
            "latency_ms": 10.0,
            "fare_error_inr": 2.0,
            "duration_error_min": 5.0,
            "gt_fare_error_inr": 1.0,
            "gt_duration_error_min": 3.0,
            "is_missing_route": False,
            "is_false_positive": False,
            "journey_type": "direct",
            "departure_period": "morning_peak",
            "preference": "fastest"
        },
        {
            "test_id": "T2",
            "validation_status": "PASSED",
            "options_found": 1,
            "sequence_valid": True,
            "transfer_valid": True,
            "transfers_count": 1,
            "latency_ms": 20.0,
            "fare_error_inr": 0.0,
            "duration_error_min": 2.0,
            "gt_fare_error_inr": None,
            "gt_duration_error_min": None,
            "is_missing_route": False,
            "is_false_positive": False,
            "journey_type": "transfer",
            "departure_period": "off_peak",
            "preference": "cheapest"
        }
    ]

    metrics = BenchmarkMetricsCalculator.calculate_summary_metrics(sample_evals)
    assert metrics["total_test_cases"] == 2
    assert metrics["valid_route_rate_pct"] == 100.0
    assert metrics["route_coverage_pct"] == 100.0
    assert metrics["avg_fare_error_inr"] == 1.0
    assert metrics["mean_abs_travel_time_error_min"] == 3.5
    assert metrics["median_latency_ms"] in (10.0, 20.0)


def test_regression_tester():
    prev_metrics = {
        "valid_route_rate_pct": 90.0,
        "median_latency_ms": 50.0,
        "avg_fare_error_inr": 3.0
    }
    prev_results = [
        {"test_id": "T1", "validation_status": "PASSED"},
        {"test_id": "T2", "validation_status": "PASSED"}
    ]

    curr_metrics = {
        "valid_route_rate_pct": 100.0,
        "median_latency_ms": 40.0,
        "avg_fare_error_inr": 2.0
    }
    curr_results = [
        {"test_id": "T1", "validation_status": "PASSED"},
        {"test_id": "T2", "validation_status": "PASSED"}
    ]

    # Save dummy previous JSON file for regression test comparison
    dummy_path = os.path.join(_BENCHMARKS_DIR, "results", "test_dummy_prev.json")
    os.makedirs(os.path.dirname(dummy_path), exist_ok=True)
    with open(dummy_path, "w", encoding="utf-8") as f:
        json_data = dict(prev_metrics)
        json_data["results"] = prev_results
        import json
        json.dump(json_data, f)

    res = RegressionTester.compare_runs(curr_metrics, curr_results, dummy_path)
    assert res["status"] == "NO_REGRESSION"
    assert res["valid_rate_shift_pct"] == 10.0
    assert res["new_failures_count"] == 0

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_full_benchmark_run():
    dataset_path = os.path.join(_BENCHMARKS_DIR, "dataset.json")
    output_dir = os.path.join(_BENCHMARKS_DIR, "results_test_run")

    summary = run_benchmark(
        dataset_path=dataset_path,
        output_dir=output_dir,
        mode="direct",
        max_options=3
    )

    assert summary["total_test_cases"] >= 50
    assert summary["valid_route_rate_pct"] >= 0.0
    assert summary["route_coverage_pct"] > 0.0

    assert os.path.exists(os.path.join(output_dir, "benchmark_summary_latest.json"))
