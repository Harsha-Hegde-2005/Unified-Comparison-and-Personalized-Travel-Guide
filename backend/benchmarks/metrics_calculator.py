"""
metrics_calculator.py
==================
Calculates overall quantitative benchmark metrics across all test case evaluations,
including distribution summaries (MAE, MedAE, MaxAE, sample sizes) and separate
cold-start vs warm request latency statistics.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


class BenchmarkMetricsCalculator:
    """Calculates summary performance metrics for a benchmark evaluation run."""

    @staticmethod
    def calculate_summary_metrics(evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_cases = len(evaluation_results)
        if total_cases == 0:
            return {}

        passed_count = sum(1 for r in evaluation_results if r["validation_status"] == "PASSED")
        failed_val_count = sum(1 for r in evaluation_results if r["validation_status"] == "FAILED_VALIDATION")
        unverified_count = sum(1 for r in evaluation_results if r["validation_status"] == "UNVERIFIED")
        no_route_count = sum(1 for r in evaluation_results if r["validation_status"] == "NO_ROUTE_FOUND")
        error_count = sum(1 for r in evaluation_results if r["validation_status"] == "ERROR")

        # 1. Valid Route Rate (%)
        # Executable = total - errors
        executable_cases = [r for r in evaluation_results if r["validation_status"] != "ERROR"]
        valid_route_rate_pct = round((passed_count / len(executable_cases) * 100.0), 2) if executable_cases else 0.0

        # 2. Route Coverage (%)
        cases_with_options = sum(1 for r in evaluation_results if r["options_found"] > 0)
        route_coverage_pct = round((cases_with_options / total_cases * 100.0), 2)

        # 3. Stop-Sequence Correctness (%)
        seq_valid_count = sum(1 for r in evaluation_results if r.get("sequence_valid", False) and r["options_found"] > 0)
        evaluated_seq_cases = sum(1 for r in evaluation_results if r["options_found"] > 0)
        stop_sequence_correctness_pct = round((seq_valid_count / evaluated_seq_cases * 100.0), 2) if evaluated_seq_cases else 0.0

        # 4. Transfer Validity Rate (%)
        transfer_cases = [r for r in evaluation_results if r.get("transfers_count", 0) > 0 and r["options_found"] > 0]
        valid_transfers_count = sum(1 for r in transfer_cases if r.get("transfer_valid", False))
        transfer_validity_rate_pct = round((valid_transfers_count / len(transfer_cases) * 100.0), 2) if transfer_cases else 100.0

        # 5. Error Distribution Stats for Fares and Durations
        ref_fare_errors = [r["fare_error_inr"] for r in evaluation_results if r.get("fare_error_inr") is not None]
        gt_fare_errors = [r["gt_fare_error_inr"] for r in evaluation_results if r.get("gt_fare_error_inr") is not None]
        
        ref_duration_errors = [r["duration_error_min"] for r in evaluation_results if r.get("duration_error_min") is not None]
        gt_duration_errors = [r["gt_duration_error_min"] for r in evaluation_results if r.get("gt_duration_error_min") is not None]

        fare_ref_stats = BenchmarkMetricsCalculator._calc_distribution_stats(ref_fare_errors, total_cases)
        fare_gt_stats = BenchmarkMetricsCalculator._calc_distribution_stats(gt_fare_errors, total_cases)
        duration_ref_stats = BenchmarkMetricsCalculator._calc_distribution_stats(ref_duration_errors, total_cases)
        duration_gt_stats = BenchmarkMetricsCalculator._calc_distribution_stats(gt_duration_errors, total_cases)

        # 6. Separate Cold-Start and Warm Latency Metrics (ms)
        all_latencies = [r["latency_ms"] for r in evaluation_results]
        cold_start_latency_ms = all_latencies[0] if all_latencies else 0.0
        
        warm_latencies = all_latencies[1:] if len(all_latencies) > 1 else all_latencies
        
        warm_p50 = BenchmarkMetricsCalculator._calc_percentile(warm_latencies, 0.50)
        warm_p95 = BenchmarkMetricsCalculator._calc_percentile(warm_latencies, 0.95)
        overall_p50 = BenchmarkMetricsCalculator._calc_percentile(all_latencies, 0.50)
        overall_p95 = BenchmarkMetricsCalculator._calc_percentile(all_latencies, 0.95)

        # 7. Timeout and Error Rates (%)
        timeout_error_rate_pct = round((error_count / total_cases * 100.0), 2)

        # 8. Missing-Route Cases & False Positive Counts
        missing_route_count = sum(1 for r in evaluation_results if r.get("is_missing_route", False))
        false_positive_count = sum(1 for r in evaluation_results if r.get("is_false_positive", False))

        # 9. Breakdown Metrics
        breakdown_by_type = BenchmarkMetricsCalculator._calculate_group_breakdown(evaluation_results, "journey_type")
        breakdown_by_period = BenchmarkMetricsCalculator._calculate_group_breakdown(evaluation_results, "departure_period")
        breakdown_by_preference = BenchmarkMetricsCalculator._calculate_group_breakdown(evaluation_results, "preference")

        return {
            "total_test_cases": total_cases,
            "passed_count": passed_count,
            "failed_validation_count": failed_val_count,
            "unverified_count": unverified_count,
            "no_route_found_count": no_route_count,
            "error_count": error_count,
            "valid_route_rate_pct": valid_route_rate_pct,
            "route_coverage_pct": route_coverage_pct,
            "stop_sequence_correctness_pct": stop_sequence_correctness_pct,
            "transfer_validity_rate_pct": transfer_validity_rate_pct,
            
            # Legacy fields for backward compatibility
            "avg_fare_error_inr": fare_ref_stats["mae"],
            "avg_gt_fare_error_inr": fare_gt_stats["mae"],
            "mean_abs_travel_time_error_min": duration_ref_stats["mae"],
            "mean_abs_gt_travel_time_error_min": duration_gt_stats["mae"],
            "median_latency_ms": warm_p50,
            "p95_latency_ms": warm_p95,
            
            # Error distribution details
            "distributions": {
                "ref_fare": fare_ref_stats,
                "gt_fare": fare_gt_stats,
                "ref_duration": duration_ref_stats,
                "gt_duration": duration_gt_stats
            },
            
            # Latency details
            "latency": {
                "cold_start_ms": cold_start_latency_ms,
                "warm_p50_ms": warm_p50,
                "warm_p95_ms": warm_p95,
                "overall_p50_ms": overall_p50,
                "overall_p95_ms": overall_p95,
                "warm_sample_count": len(warm_latencies)
            },

            "timeout_error_rate_pct": timeout_error_rate_pct,
            "missing_route_cases_count": missing_route_count,
            "false_positive_recommendations_count": false_positive_count,
            "breakdown": {
                "by_journey_type": breakdown_by_type,
                "by_departure_period": breakdown_by_period,
                "by_preference": breakdown_by_preference
            }
        }

    @staticmethod
    def _calc_distribution_stats(values: List[float], total_cases: int) -> Dict[str, Any]:
        if not values:
            return {
                "mae": 0.0,
                "median_ae": 0.0,
                "max_ae": 0.0,
                "sample_count": 0,
                "missing_count": total_cases
            }
        sorted_v = sorted(values)
        n = len(sorted_v)
        mae = round(sum(sorted_v) / n, 2)
        med_ae = round(sorted_v[n // 2], 2)
        max_ae = round(sorted_v[-1], 2)
        return {
            "mae": mae,
            "median_ae": med_ae,
            "max_ae": max_ae,
            "sample_count": n,
            "missing_count": total_cases - n
        }

    @staticmethod
    def _calc_percentile(values: List[float], percentile: float) -> float:
        if not values:
            return 0.0
        sorted_v = sorted(values)
        n = len(sorted_v)
        idx = int(math.ceil(percentile * n)) - 1
        return round(sorted_v[min(max(0, idx), n - 1)], 2)

    @staticmethod
    def _calculate_group_breakdown(results: List[Dict[str, Any]], group_key: str) -> Dict[str, Dict[str, Any]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in results:
            val = str(r.get(group_key, "unknown"))
            groups.setdefault(val, []).append(r)

        breakdown = {}
        for g_name, items in groups.items():
            tot = len(items)
            passed = sum(1 for x in items if x["validation_status"] == "PASSED")
            cov = sum(1 for x in items if x["options_found"] > 0)
            avg_lat = round(sum(x["latency_ms"] for x in items) / tot, 2)
            
            breakdown[g_name] = {
                "total_cases": tot,
                "passed_count": passed,
                "valid_rate_pct": round((passed / tot * 100.0), 2) if tot else 0.0,
                "coverage_pct": round((cov / tot * 100.0), 2) if tot else 0.0,
                "avg_latency_ms": avg_lat
            }
        return breakdown
