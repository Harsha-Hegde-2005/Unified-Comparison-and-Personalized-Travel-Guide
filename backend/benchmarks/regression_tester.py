"""
regression_tester.py
====================
Regression testing engine to compare current benchmark run results against
a previous benchmark run (JSON summary or CSV log).
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List, Optional, Tuple


class RegressionTester:
    """Compares current benchmark results against a previous benchmark run."""

    @staticmethod
    def compare_runs(
        current_metrics: Dict[str, Any],
        current_results: List[Dict[str, Any]],
        previous_path: str
    ) -> Dict[str, Any]:
        """
        Loads previous benchmark run metrics/results and performs comparison.
        """
        prev_metrics, prev_results = RegressionTester._load_previous_run(previous_path)
        if not prev_metrics:
            return {
                "status": "ERROR",
                "message": f"Could not load previous benchmark run from {previous_path}"
            }

        prev_valid_rate = prev_metrics.get("valid_route_rate_pct", 0.0)
        curr_valid_rate = current_metrics.get("valid_route_rate_pct", 0.0)
        valid_rate_shift_pct = round(curr_valid_rate - prev_valid_rate, 2)

        prev_p50 = prev_metrics.get("median_latency_ms", 0.0)
        curr_p50 = current_metrics.get("median_latency_ms", 0.0)
        median_latency_shift_ms = round(curr_p50 - prev_p50, 2)

        prev_fare_err = prev_metrics.get("avg_fare_error_inr", 0.0)
        curr_fare_err = current_metrics.get("avg_fare_error_inr", 0.0)
        fare_error_shift_inr = round(curr_fare_err - prev_fare_err, 2)

        # Compare individual test cases by test_id
        prev_map = {r["test_id"]: r["validation_status"] for r in prev_results if "test_id" in r}
        curr_map = {r["test_id"]: r["validation_status"] for r in current_results if "test_id" in r}

        new_failures = []
        fixed_failures = []

        for tid, curr_st in curr_map.items():
            prev_st = prev_map.get(tid)
            if prev_st == "PASSED" and curr_st != "PASSED":
                new_failures.append({
                    "test_id": tid,
                    "previous_status": prev_st,
                    "current_status": curr_st
                })
            elif prev_st != "PASSED" and curr_st == "PASSED":
                fixed_failures.append({
                    "test_id": tid,
                    "previous_status": prev_st,
                    "current_status": curr_st
                })

        reg_status = "REGRESSION_DETECTED" if (new_failures or valid_rate_shift_pct < -1.0) else "NO_REGRESSION"

        return {
            "status": reg_status,
            "previous_file": previous_path,
            "previous_valid_rate_pct": prev_valid_rate,
            "current_valid_rate_pct": curr_valid_rate,
            "valid_rate_shift_pct": valid_rate_shift_pct,
            "previous_median_latency_ms": prev_p50,
            "current_median_latency_ms": curr_p50,
            "median_latency_shift_ms": median_latency_shift_ms,
            "fare_error_shift_inr": fare_error_shift_inr,
            "new_failures": new_failures,
            "fixed_failures": fixed_failures,
            "new_failures_count": len(new_failures),
            "fixed_failures_count": len(fixed_failures)
        }

    @staticmethod
    def _load_previous_run(path: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Loads previous run from JSON summary or CSV results file."""
        if not os.path.exists(path):
            return None, []

        if path.endswith(".json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
                return metrics, metrics.get("results", [])
            except Exception:
                return None, []
        elif path.endswith(".csv"):
            try:
                results = []
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row["latency_ms"] = float(row.get("latency_ms", 0.0))
                        row["options_found"] = int(row.get("options_found", 0))
                        results.append(row)
                
                # Compute quick metrics from CSV rows
                from metrics_calculator import BenchmarkMetricsCalculator
                metrics = BenchmarkMetricsCalculator.calculate_summary_metrics(results)
                return metrics, results
            except Exception:
                return None, []
        return None, []
