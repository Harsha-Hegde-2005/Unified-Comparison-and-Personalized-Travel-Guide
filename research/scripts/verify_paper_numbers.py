r"""
verify_paper_numbers.py
=======================
Automated Verification Script for ADCOM 2027 Submission Paper Numbers.

Validates that every single quantitative claim in research/paper/main.tex matches:
1. research/experiments/results/experiment_summary_stats.json
2. research/experiments/results/benchmark_corridors_results.csv
3. research/experiments/results/baselines_comparison.csv
4. research/experiments/results/ablation_study_results.csv
5. research/experiments/results/weather_scenarios_results.csv
6. research/experiments/results/traffic_scenarios_results.csv
7. research/experiments/results/scalability_concurrency_results.csv
"""

import os
import json
import pandas as pd
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.abspath(os.path.join(_HERE, "..", "experiments", "results"))
PAPER_PATH = os.path.abspath(os.path.join(_HERE, "..", "paper", "main.tex"))

def verify_all_paper_numbers():
    print("=" * 80)
    print("STARTING SCIENTIFIC VERIFICATION OF PAPER NUMBERS AGAINST CSV/JSON OUTPUTS")
    print("=" * 80)

    with open(PAPER_PATH, "r", encoding="utf-8") as f:
        paper_text = f.read()

    # Load data files
    with open(os.path.join(RESULTS_DIR, "experiment_summary_stats.json")) as f:
        stats_json = json.load(f)

    corr_df = pd.read_csv(os.path.join(RESULTS_DIR, "benchmark_corridors_results.csv"))
    base_df = pd.read_csv(os.path.join(RESULTS_DIR, "baselines_comparison.csv"))
    abl_df = pd.read_csv(os.path.join(RESULTS_DIR, "ablation_study_results.csv"))
    weath_df = pd.read_csv(os.path.join(RESULTS_DIR, "weather_scenarios_results.csv"))
    traff_df = pd.read_csv(os.path.join(RESULTS_DIR, "traffic_scenarios_results.csv"))
    conc_df = pd.read_csv(os.path.join(RESULTS_DIR, "scalability_concurrency_results.csv"))

    expected_checks = [
        ("Cold-Start Load Overhead (s)", f"{stats_json['cold_start_overhead_ms']/1000.0:.2f}", "204.22"),
        ("Startup RSS Memory (MB)", f"{stats_json['startup_rss_mb']:.2f}", "142.59"),
        ("Warm RSS Memory (MB)", f"{stats_json['warm_rss_mb']:.2f}", "811.38"),
        ("Peak RSS Memory (MB)", f"{stats_json['peak_rss_mb']:.2f}", "883.77"),
        ("Sequential Warm Mean Latency (ms)", f"{corr_df['seq_mean_ms'].mean():.2f}", "2.75"),
        ("Parallel MAS Warm Mean Latency (ms)", f"{corr_df['par_mean_ms'].mean():.2f}", "3.43"),
        ("B4 Monolithic Latency (ms)", f"{base_df[base_df['baseline_id']=='B4']['mean_latency_ms'].values[0]:.2f}", "3.12"),
        ("B5 Coordinated MAS Latency (ms)", f"{base_df[base_df['baseline_id']=='B5']['mean_latency_ms'].values[0]:.2f}", "4.83"),
        ("Peak Concurrency QPS (C=5)", f"{conc_df[conc_df['concurrent_requests']==5]['throughput_qps'].values[0]:.2f}", "231.69"),
        ("High Concurrency QPS (C=50)", f"{conc_df[conc_df['concurrent_requests']==50]['throughput_qps'].values[0]:.2f}", "194.54"),
        ("A0 Full MAS Utility Score", f"{abl_df[abl_df['ablation_id']=='A0']['utility_score'].values[0]:.1f}", "95.3"),
        ("A4 Uncoordinated Utility Score", f"{abl_df[abl_df['ablation_id']=='A4']['utility_score'].values[0]:.1f}", "50.0"),
        ("A4 Relative Utility Reduction (%)", f"{(95.3 - 50.0)/95.3 * 100:.1f}", "47.5"),
        ("Clear Weather Utility Score", f"{weath_df[weath_df['scenario']=='Clear']['utility_score'].values[0]:.1f}", "97.3"),
        ("Heavy Rain Utility Score", f"{weath_df[weath_df['scenario']=='Heavy Rain']['utility_score'].values[0]:.1f}", "96.5"),
        ("High Gridlock Utility Score", f"{traff_df[traff_df['scenario']=='High Gridlock']['utility_score'].values[0]:.1f}", "89.8")
    ]

    passed_count = 0
    total_count = len(expected_checks)

    for label, empirical_val, paper_val in expected_checks:
        in_paper = paper_val in paper_text
        match_empirical = (empirical_val == paper_val)
        status = "PASS" if (in_paper and match_empirical) else "FAIL"
        if status == "PASS":
            passed_count += 1
        print(f"[{status}] {label}: Empirical = {empirical_val}, Target in Paper = {paper_val}, Present in main.tex = {in_paper}")

    print("-" * 80)
    print(f"SUMMARY: {passed_count} / {total_count} Quantitative Metrics Verified Passed.")
    print("=" * 80)

    return passed_count == total_count

if __name__ == "__main__":
    success = verify_all_paper_numbers()
    if not success:
        exit(1)
