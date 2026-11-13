"""
run_benchmark.py
================
CLI Runner for the BMTC Route Benchmarking and Evaluation Module.

Usage:
  python backend/benchmarks/run_benchmark.py
  python backend/benchmarks/run_benchmark.py --compare-with backend/benchmarks/results/benchmark_summary_latest.json
  python backend/benchmarks/run_benchmark.py --mode http --max-options 8
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from api_adapter import JourneyAPIAdapter
from gtfs_reference_adapter import GTFSReferenceAdapter
from evaluator import JourneyEvaluator
from metrics_calculator import BenchmarkMetricsCalculator
from report_generator import BenchmarkReportGenerator
from regression_tester import RegressionTester


def run_benchmark(
    dataset_path: str,
    output_dir: str,
    mode: str = "direct",
    max_options: int = 5,
    compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """Executes the full BMTC route benchmark suite."""
    print("=" * 75)
    print("  BMTC ROUTE ENGINE BENCHMARK & EVALUATION RUNNER")
    print("=" * 75)
    print(f"Dataset Path : {dataset_path}")
    print(f"Output Dir   : {output_dir}")
    print(f"Execution    : {mode.upper()} mode")
    print("-" * 75)

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data.get("test_cases", [])
    print(f"Loaded {len(test_cases)} test cases from dataset.")

    # 1. Initialize Adapters
    print("Initializing GTFS Reference Adapter...")
    ref_adapter = GTFSReferenceAdapter()
    print(f"Reference Data Source: {ref_adapter.get_source_name()}")

    print(f"Initializing Journey API Adapter ({mode} mode)...")
    api_adapter = JourneyAPIAdapter(mode=mode)

    evaluator = JourneyEvaluator(ref_adapter)

    # 2. Execute Test Cases & Evaluate
    print(f"\nExecuting {len(test_cases)} test cases...\n")
    evaluation_results = []

    for idx, tc in enumerate(test_cases, 1):
        tid = tc.get("test_id", f"TC_{idx}")
        name = tc.get("name", tid)
        print(f"[{idx:02d}/{len(test_cases):02d}] {tid}: {name}...", end="", flush=True)

        api_res = api_adapter.execute_test_case(tc, max_options=max_options)
        eval_res = evaluator.evaluate_test_result(tc, api_res)
        evaluation_results.append(eval_res)

        st = eval_res["validation_status"]
        lat = eval_res["latency_ms"]
        print(f" -> {st} ({lat} ms)")

    # 3. Calculate Summary Metrics
    print("\nCalculating benchmark summary metrics...")
    summary_metrics = BenchmarkMetricsCalculator.calculate_summary_metrics(evaluation_results)

    # 4. Perform Regression Comparison if requested
    regression_info = None
    if compare_with:
        print(f"\nPerforming regression comparison with {compare_with}...")
        regression_info = RegressionTester.compare_runs(summary_metrics, evaluation_results, compare_with)
        summary_metrics["regression_comparison"] = regression_info

    # 5. Output Reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, f"benchmark_results_{timestamp}.csv")
    json_path = os.path.join(output_dir, f"benchmark_summary_{timestamp}.json")
    html_path = os.path.join(output_dir, f"benchmark_report_{timestamp}.html")

    # Latest symlink / copy paths for easy regression referencing
    json_latest = os.path.join(output_dir, "benchmark_summary_latest.json")

    print(f"\nGenerating reports...")
    BenchmarkReportGenerator.generate_csv_report(evaluation_results, csv_path)
    print(f"  [CSV Log]     : {csv_path}")

    BenchmarkReportGenerator.generate_json_summary(summary_metrics, json_path)
    BenchmarkReportGenerator.generate_json_summary(summary_metrics, json_latest)
    print(f"  [JSON Metrics]: {json_path}")

    BenchmarkReportGenerator.generate_html_report(summary_metrics, evaluation_results, html_path, regression_info)
    print(f"  [HTML Report] : {html_path}")

    # 6. Print Console Summary Table
    dists = summary_metrics.get("distributions", {})
    ref_f = dists.get("ref_fare", {})
    gt_f = dists.get("gt_fare", {})
    ref_d = dists.get("ref_duration", {})
    gt_d = dists.get("gt_duration", {})
    lat_d = summary_metrics.get("latency", {})

    print("\n" + "=" * 75)
    print("  BENCHMARK SUMMARY & AUDIT RESULTS")
    print("=" * 75)
    print(f"  Total Test Cases Evaluated : {summary_metrics['total_test_cases']}")
    print(f"  Passed Cases (Strict Check): {summary_metrics.get('passed_count', 0)}")
    print(f"  Unverified Cases           : {summary_metrics.get('unverified_count', 0)}")
    print(f"  Validation Failures        : {summary_metrics.get('failed_validation_count', 0)}")
    print(f"  Valid Route Rate           : {summary_metrics['valid_route_rate_pct']}%")
    print(f"  Route Coverage Rate        : {summary_metrics['route_coverage_pct']}%")
    print(f"  Stop Sequence Correctness  : {summary_metrics['stop_sequence_correctness_pct']}%")
    print(f"  Transfer Validity Rate     : {summary_metrics['transfer_validity_rate_pct']}%")
    print("-" * 75)
    print(f"  Fare Error vs Ref (MAE/Med): Rs. {ref_f.get('mae', 0.0)} / Rs. {ref_f.get('median_ae', 0.0)} (Sample: {ref_f.get('sample_count', 0)})")
    print(f"  Fare Error vs GT  (MAE/Med): Rs. {gt_f.get('mae', 0.0)} / Rs. {gt_f.get('median_ae', 0.0)} (Sample: {gt_f.get('sample_count', 0)})")
    print(f"  Time Error vs Ref (MAE/Med): {ref_d.get('mae', 0.0)}m / {ref_d.get('median_ae', 0.0)}m (Sample: {ref_d.get('sample_count', 0)})")
    print(f"  Time Error vs GT  (MAE/Med): {gt_d.get('mae', 0.0)}m / {gt_d.get('median_ae', 0.0)}m (Sample: {gt_d.get('sample_count', 0)})")
    print("-" * 75)
    print(f"  Cold-Start Latency (1st req): {lat_d.get('cold_start_ms', 0.0)} ms")
    print(f"  Warm Request Latency P50/P95: {lat_d.get('warm_p50_ms', summary_metrics['median_latency_ms'])} ms / {lat_d.get('warm_p95_ms', summary_metrics['p95_latency_ms'])} ms")
    print(f"  Timeout / Error Rate       : {summary_metrics['timeout_error_rate_pct']}%")
    print(f"  Missing Route Cases        : {summary_metrics['missing_route_cases_count']}")
    print(f"  False Positive Recs        : {summary_metrics['false_positive_recommendations_count']}")
    
    if regression_info:
        print("-" * 75)
        print(f"  REGRESSION STATUS          : {regression_info['status']}")
        print(f"  Valid Rate Shift           : {regression_info['valid_rate_shift_pct']:+.2f}%")
        print(f"  Median Latency Shift       : {regression_info['median_latency_shift_ms']:+.2f} ms")
        print(f"  New Failure Regressions    : {regression_info['new_failures_count']}")
        print(f"  Fixed Test Cases           : {regression_info['fixed_failures_count']}")

    print("=" * 75)
    return summary_metrics


def main():
    parser = argparse.ArgumentParser(description="BMTC Route Engine Benchmark and Evaluation Module")
    parser.add_argument(
        "--dataset",
        default=os.path.join(_HERE, "dataset.json"),
        help="Path to test dataset JSON file (default: backend/benchmarks/dataset.json)"
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(_HERE, "results"),
        help="Directory to store CSV, JSON, and HTML benchmark results (default: backend/benchmarks/results)"
    )
    parser.add_argument(
        "--mode",
        choices=["direct", "http"],
        default="direct",
        help="Execution mode: 'direct' to call python bmtc_plan directly, 'http' to query HTTP API endpoint"
    )
    parser.add_argument(
        "--max-options",
        type=int,
        default=5,
        help="Maximum route options to request per test case (default: 5)"
    )
    parser.add_argument(
        "--compare-with",
        default=None,
        help="Path to previous benchmark summary JSON or CSV to run regression comparison"
    )

    args = parser.parse_args()
    run_benchmark(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        mode=args.mode,
        max_options=args.max_options,
        compare_with=args.compare_with
    )


if __name__ == "__main__":
    main()
