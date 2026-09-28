"""
report_generator.py
===================
Generates CSV results files, JSON summary metrics, and a comprehensive HTML dashboard report
containing audit disclaimers, status breakdowns, error distribution tables, and latency profiles.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class BenchmarkReportGenerator:
    """Generates CSV result logs, JSON metric summaries, and HTML visual reports."""

    @staticmethod
    def generate_csv_report(evaluation_results: List[Dict[str, Any]], output_path: str):
        """Generates a structured CSV file with one row per test case run."""
        fieldnames = [
            "test_id",
            "name",
            "origin",
            "destination",
            "travel_date",
            "departure_time",
            "departure_period",
            "journey_type",
            "preference",
            "options_found",
            "recommended_mode",
            "recommended_routes",
            "boarding_stops",
            "alighting_stops",
            "transfers_count",
            "validation_status",
            "failure_reasons",
            "route_exists_valid",
            "sequence_valid",
            "service_day_valid",
            "transfer_valid",
            "time_valid",
            "is_missing_route",
            "is_false_positive",
            "fare_predicted_inr",
            "fare_reference_inr",
            "fare_error_inr",
            "duration_predicted_min",
            "duration_reference_min",
            "duration_error_min",
            "gt_has_observation",
            "gt_actual_route",
            "gt_actual_fare_inr",
            "gt_actual_duration_mins",
            "gt_fare_error_inr",
            "gt_duration_error_min",
            "latency_ms",
            "reference_source"
        ]

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in evaluation_results:
                row = {k: r.get(k) for k in fieldnames}
                row["failure_reasons"] = " | ".join(r.get("failure_reasons", []))
                writer.writerow(row)

    @staticmethod
    def generate_json_summary(summary_metrics: Dict[str, Any], output_path: str):
        """Saves summary metrics as JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary_metrics, f, indent=2)

    @staticmethod
    def generate_html_report(
        summary_metrics: Dict[str, Any],
        evaluation_results: List[Dict[str, Any]],
        output_path: str,
        regression_comparison: Optional[Dict[str, Any]] = None
    ):
        """Generates an HTML visual report with metrics dashboard, disclaimers, and breakdown tables."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        tot = summary_metrics.get("total_test_cases", 0)
        passed_c = summary_metrics.get("passed_count", 0)
        failed_c = summary_metrics.get("failed_validation_count", 0)
        unverified_c = summary_metrics.get("unverified_count", 0)
        no_route_c = summary_metrics.get("no_route_found_count", 0)
        error_c = summary_metrics.get("error_count", 0)

        valid_rate = summary_metrics.get("valid_route_rate_pct", 0.0)
        coverage = summary_metrics.get("route_coverage_pct", 0.0)
        seq_rate = summary_metrics.get("stop_sequence_correctness_pct", 0.0)
        xfer_rate = summary_metrics.get("transfer_validity_rate_pct", 0.0)

        dists = summary_metrics.get("distributions", {})
        ref_f = dists.get("ref_fare", {})
        gt_f = dists.get("gt_fare", {})
        ref_d = dists.get("ref_duration", {})
        gt_d = dists.get("gt_duration", {})

        lat_data = summary_metrics.get("latency", {})
        cold_lat = lat_data.get("cold_start_ms", summary_metrics.get("median_latency_ms", 0.0))
        warm_p50 = lat_data.get("warm_p50_ms", summary_metrics.get("median_latency_ms", 0.0))
        warm_p95 = lat_data.get("warm_p95_ms", summary_metrics.get("p95_latency_ms", 0.0))

        breakdown = summary_metrics.get("breakdown", {})
        by_type = breakdown.get("by_journey_type", {})
        by_period = breakdown.get("by_departure_period", {})
        by_pref = breakdown.get("by_preference", {})

        # Regression alert section if present
        reg_html = ""
        if regression_comparison:
            reg_status = regression_comparison.get("status", "NO_REGRESSION")
            status_color = "#10B981" if reg_status == "NO_REGRESSION" else "#EF4444"
            shift_rate = regression_comparison.get("valid_rate_shift_pct", 0.0)
            shift_lat = regression_comparison.get("median_latency_shift_ms", 0.0)
            new_fails = regression_comparison.get("new_failures", [])
            fixed_fails = regression_comparison.get("fixed_failures", [])

            reg_html = f"""
            <div class="card" style="border-left: 6px solid {status_color}; margin-bottom: 24px;">
                <h2>Regression Test Comparison Status: <span style="color: {status_color}">{reg_status}</span></h2>
                <p><strong>Compared With:</strong> {regression_comparison.get('previous_file', 'Previous Run')}</p>
                <div class="metrics-grid" style="margin-top: 16px;">
                    <div class="metric-box">
                        <div class="metric-value">{shift_rate:+.2f}%</div>
                        <div class="metric-label">Valid Rate Shift</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value">{shift_lat:+.2f} ms</div>
                        <div class="metric-label">Warm Latency Shift</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value">{len(new_fails)}</div>
                        <div class="metric-label">New Regressions</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value">{len(fixed_fails)}</div>
                        <div class="metric-label">Fixed Cases</div>
                    </div>
                </div>
            </div>
            """

        # Table rows for detailed test cases
        test_rows_html = ""
        for r in evaluation_results:
            st = r["validation_status"]
            if st == "PASSED":
                badge_class = "badge-passed"
            elif st == "FAILED_VALIDATION":
                badge_class = "badge-failed"
            elif st == "UNVERIFIED":
                badge_class = "badge-unverified"
            else:
                badge_class = "badge-warn"

            reasons = ", ".join(r.get("failure_reasons", [])) or "None"
            gt_text = f"Observed: {r.get('gt_actual_route', 'N/A')}" if r.get("gt_has_observation") else "No Field Log"
            
            # Per-check status summary
            checks_map = r.get("checks", {})
            checks_pills = ""
            for c_name, c_info in checks_map.items():
                c_st = c_info.get("status", "N/A")
                p_class = "pill-pass" if c_st == "PASS" else "pill-fail" if c_st == "FAIL" else "pill-unverified" if c_st == "UNVERIFIED" else "pill-na"
                short_name = c_name.replace("bus_", "").replace("_expectation", "").replace("_active", "").replace("_validity", "")
                checks_pills += f'<span class="pill {p_class}" title="{c_info.get("reason", "")}">{short_name}: {c_st}</span> '

            test_rows_html += f"""
            <tr>
                <td><code>{r['test_id']}</code></td>
                <td><strong>{r['name']}</strong><br><small>{r['origin']} → {r['destination']}</small></td>
                <td>{r['departure_period']} / {r['departure_time']}</td>
                <td>{r['recommended_routes'] or 'None'}</td>
                <td><span class="badge {badge_class}">{st}</span></td>
                <td><div style="font-size: 11px;">{checks_pills}</div></td>
                <td>Rs. {r.get('fare_predicted_inr') or 0} <br><small>(Ref: Rs. {r.get('fare_reference_inr') or 'N/A'})</small></td>
                <td>{r.get('duration_predicted_min') or 0}m <br><small>(Ref: {r.get('duration_reference_min') or 'N/A'}m)</small></td>
                <td>{r['latency_ms']} ms</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BMTC Route Engine Benchmark Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0F172A; color: #F8FAFC; margin: 0; padding: 24px; }}
        .container {{ max-width: 1300px; margin: 0 auto; }}
        header {{ border-bottom: 2px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }}
        h1 {{ margin: 0; color: #38BDF8; font-size: 28px; }}
        p {{ color: #94A3B8; margin: 4px 0 0 0; }}
        .disclaimer-banner {{ background-color: #1E293B; border-left: 6px solid #F59E0B; padding: 16px; border-radius: 6px; margin-bottom: 24px; font-size: 14px; line-height: 1.5; color: #CBD5E1; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .metric-box {{ background-color: #1E293B; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #334155; }}
        .metric-value {{ font-size: 26px; font-weight: bold; color: #38BDF8; margin-bottom: 4px; }}
        .metric-label {{ font-size: 12px; color: #94A3B8; text-transform: uppercase; tracking: 0.05em; }}
        .card {{ background-color: #1E293B; border-radius: 8px; padding: 20px; border: 1px solid #334155; margin-bottom: 24px; }}
        h2 {{ margin-top: 0; color: #F1F5F9; font-size: 18px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
        th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background-color: #0F172A; color: #94A3B8; font-weight: 600; }}
        tr:hover {{ background-color: #26354A; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .badge-passed {{ background-color: #065F46; color: #34D399; }}
        .badge-failed {{ background-color: #991B1B; color: #FCA5A5; }}
        .badge-unverified {{ background-color: #374151; color: #9CA3AF; }}
        .badge-warn {{ background-color: #92400E; color: #FDE68A; }}
        .pill {{ display: inline-block; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-bottom: 2px; }}
        .pill-pass {{ background-color: #064E3B; color: #6EE7B7; }}
        .pill-fail {{ background-color: #7F1D1D; color: #FCA5A5; }}
        .pill-unverified {{ background-color: #1F2937; color: #9CA3AF; }}
        .pill-na {{ background-color: #334155; color: #CBD5E1; }}
        code {{ background-color: #0F172A; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #38BDF8; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>BMTC Route Benchmarking & Audit Dashboard</h1>
            <p>Automated Leg-Aware GTFS Reference & Ground-Truth Field Verification Report | Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="disclaimer-banner">
            <strong>⚠️ Audit & Validation Methodology Notice:</strong><br>
            Automated benchmark validation evaluates engine recommendations against local BMTC GTFS reference files (<code>database/bmtc</code>) and verified field ground-truth logs.
            Validation checks are strict and leg-aware. A case status of <strong>UNVERIFIED</strong> indicates that reference stop-sequence or schedule data was missing or required fuzzy matching.
            Passing automated validation confirms compliance with implemented checks, but does not guarantee 100% real-world route operating accuracy under dynamic road conditions.
        </div>

        {reg_html}

        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value">{valid_rate:.1f}%</div>
                <div class="metric-label">Valid Route Rate</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{coverage:.1f}%</div>
                <div class="metric-label">Route Coverage</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{passed_c} / {tot}</div>
                <div class="metric-label">Passed Cases</div>
            </div>
            <div class="metric-box">
                <div class="metric-value" style="color: #9CA3AF;">{unverified_c}</div>
                <div class="metric-label">Unverified Cases</div>
            </div>
            <div class="metric-box">
                <div class="metric-value" style="color: #FCA5A5;">{failed_c}</div>
                <div class="metric-label">Validation Failures</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{cold_lat:.0f} ms</div>
                <div class="metric-label">Cold-Start Latency</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{warm_p50:.0f} ms</div>
                <div class="metric-label">Warm Latency (P50)</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{warm_p95:.0f} ms</div>
                <div class="metric-label">Warm Latency (P95)</div>
            </div>
        </div>

        <div class="card">
            <h2>Error Distributions & Metric Sample Sizes</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric Dimension</th>
                        <th>Reference Source</th>
                        <th>MAE (Mean)</th>
                        <th>MedAE (Median)</th>
                        <th>MaxAE (Max)</th>
                        <th>Valid Sample Count</th>
                        <th>Excluded / Missing</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Fare Error (INR)</strong></td>
                        <td>GTFS Distance/Stage Ref</td>
                        <td>Rs. {ref_f.get('mae', 0.0)}</td>
                        <td>Rs. {ref_f.get('median_ae', 0.0)}</td>
                        <td>Rs. {ref_f.get('max_ae', 0.0)}</td>
                        <td>{ref_f.get('sample_count', 0)}</td>
                        <td>{ref_f.get('missing_count', 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Fare Error (INR)</strong></td>
                        <td>Field Ground Truth Log</td>
                        <td>Rs. {gt_f.get('mae', 0.0)}</td>
                        <td>Rs. {gt_f.get('median_ae', 0.0)}</td>
                        <td>Rs. {gt_f.get('max_ae', 0.0)}</td>
                        <td>{gt_f.get('sample_count', 0)}</td>
                        <td>{gt_f.get('missing_count', 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Travel Time Error (mins)</strong></td>
                        <td>GTFS Estimated Schedule Ref</td>
                        <td>{ref_d.get('mae', 0.0)} mins</td>
                        <td>{ref_d.get('median_ae', 0.0)} mins</td>
                        <td>{ref_d.get('max_ae', 0.0)} mins</td>
                        <td>{ref_d.get('sample_count', 0)}</td>
                        <td>{ref_d.get('missing_count', 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Travel Time Error (mins)</strong></td>
                        <td>Field Ground Truth Log</td>
                        <td>{gt_d.get('mae', 0.0)} mins</td>
                        <td>{gt_d.get('median_ae', 0.0)} mins</td>
                        <td>{gt_d.get('max_ae', 0.0)} mins</td>
                        <td>{gt_d.get('sample_count', 0)}</td>
                        <td>{gt_d.get('missing_count', 0)}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>Performance Breakdown</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
                <div>
                    <h3>By Journey Type</h3>
                    <table>
                        <tr><th>Type</th><th>Cases</th><th>Passed</th><th>Valid %</th></tr>
                        {''.join(f"<tr><td>{k}</td><td>{v['total_cases']}</td><td>{v['passed_count']}</td><td>{v['valid_rate_pct']}%</td></tr>" for k, v in by_type.items())}
                    </table>
                </div>
                <div>
                    <h3>By Departure Period</h3>
                    <table>
                        <tr><th>Period</th><th>Cases</th><th>Passed</th><th>Valid %</th></tr>
                        {''.join(f"<tr><td>{k}</td><td>{v['total_cases']}</td><td>{v['passed_count']}</td><td>{v['valid_rate_pct']}%</td></tr>" for k, v in by_period.items())}
                    </table>
                </div>
                <div>
                    <h3>By Preference</h3>
                    <table>
                        <tr><th>Preference</th><th>Cases</th><th>Passed</th><th>Valid %</th></tr>
                        {''.join(f"<tr><td>{k}</td><td>{v['total_cases']}</td><td>{v['passed_count']}</td><td>{v['valid_rate_pct']}%</td></tr>" for k, v in by_pref.items())}
                    </table>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Detailed Evaluation Results ({tot} Test Runs)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test ID</th>
                        <th>Journey Query</th>
                        <th>Period / Time</th>
                        <th>Recommended Route(s)</th>
                        <th>Overall Status</th>
                        <th>Leg-Aware Checks Breakdown</th>
                        <th>Fare</th>
                        <th>Duration</th>
                        <th>Latency</th>
                    </tr>
                </thead>
                <tbody>
                    {test_rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
