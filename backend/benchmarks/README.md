# BMTC Route Benchmarking and Evaluation Module

An automated, standalone benchmark runner, GTFS reference evaluator, performance metrics calculator, and regression testing suite for the BMTC Journey Assistant routing engine.

---

## 1. Module Overview & Architecture

The benchmark module evaluates the BMTC journey planner without modifying or replacing the existing routing engine architecture. It measures accuracy, route validity, latency, fare precision, and travel time against structured **BMTC GTFS reference feeds** as well as **real-world ground-truth field observations**.

### Architecture Layout

```
backend/benchmarks/
├── __init__.py                  # Package initialization
├── dataset.json                 # Configurable test dataset (52 test cases + ground-truth field observations)
├── api_adapter.py               # Adapter for executing journey planning requests & measuring latency
├── gtfs_reference_adapter.py    # Modular reference data adapter for GTFS feeds
├── evaluator.py                 # Evaluates route existence, stop sequence, service days, & transfer validity
├── metrics_calculator.py        # Computes quantitative metrics (Valid Rate, Coverage, MAE, P50/P95 Latency)
├── report_generator.py          # Generates CSV raw logs, JSON metrics, and HTML visual dashboard
├── regression_tester.py         # Compares current run against previous benchmark runs for regressions
├── run_benchmark.py             # Main CLI executable runner
└── README.md                    # Documentation & usage guide
```

---

## 2. Local Execution Commands

### A. Run Complete Benchmark (Direct Python Engine Call)

```bash
python backend/benchmarks/run_benchmark.py
```

### B. Run Benchmark Against HTTP Server Endpoint (`http://127.0.0.1:8000/api/bmtc/plan`)

*(Ensure `uvicorn main:app --reload --app-dir backend` is running)*

```bash
python backend/benchmarks/run_benchmark.py --mode http --max-options 5
```

### C. Run Benchmark with Regression Testing Against Previous Run

```bash
python backend/benchmarks/run_benchmark.py --compare-with backend/benchmarks/results/benchmark_summary_latest.json
```

---

## 3. Procedure to Add New Test Cases & Ground-Truth Field Observations

All test cases are configured inside `backend/benchmarks/dataset.json`.

### A. Test Case Structure

To add a new test case, append a JSON object to the `test_cases` list:

```json
{
  "test_id": "BMTC_BENCH_053",
  "name": "Silk Board to Electronic City Peak Commute",
  "origin": "Central Silk Board",
  "destination": "Electronic City Wipro Gate",
  "origin_stop_id": "CSB_001",
  "destination_stop_id": "EC_001",
  "travel_date": "2026-09-28",
  "departure_time": "08:30",
  "departure_period": "morning_peak",
  "journey_type": "direct",
  "preference": "fastest",
  "expected_test_conditions": {
    "service_expected": true,
    "max_transfers": 0,
    "min_options": 1
  },
  "ground_truth": {
    "has_observation": true,
    "actual_route_taken": "500-EB",
    "actual_fare_inr": 25.0,
    "actual_duration_mins": 35.0,
    "actual_boarding_stop": "Central Silk Board",
    "actual_alighting_stop": "Electronic City Wipro Gate",
    "observation_date": "2026-09-25",
    "notes": "Field observation on 500-EB Volvo line during morning peak"
  }
}
```

### Ground-Truth Field Observation Guidelines
- Set `"has_observation": true` when actual bus ride data has been recorded in the field.
- The evaluator cleanly separates **GTFS reference data validation** from **Ground-Truth field observation comparison**, ensuring predictions are separately evaluated against empirical field observations.

---

## 4. Procedure to Update Reference GTFS Dataset

The reference adapter (`gtfs_reference_adapter.py`) uses a modular interface (`BaseReferenceAdapter`).

### A. Updating Existing GTFS Data Files
Replace or update the files in:
- `database/bmtc/raw/` (`routes.txt`, `stop_times.txt`, `stops.txt`, `trips.txt`)
- `database/bmtc/processed/` (`bmtc_stop_level_cleaned.csv`, `stops_clean.csv`)

### B. Configuring a Custom Reference Adapter
If a new GTFS-RT feed or external database source is available, create a subclass of `BaseReferenceAdapter` inside `gtfs_reference_adapter.py`:

```python
class CustomLiveReferenceAdapter(BaseReferenceAdapter):
    def get_source_name(self) -> str:
        return "Live BMTC API / GTFS-RT Feed"
    
    def verify_route_exists(self, route_name: str) -> bool:
        # Implement custom lookup
        pass
    ...
```

Then pass `CustomLiveReferenceAdapter()` into `JourneyEvaluator` in `run_benchmark.py`.

---

## 5. Definition of Benchmark Metrics

| Metric | Definition & Formula |
| :--- | :--- |
| **Valid Route Rate (%)** | Percentage of executable test cases where recommended routes pass all GTFS reference validations (route existence, stop sequence order, service operating day, transfer feasibility). |
| **Route Coverage (%)** | Percentage of test cases where at least 1 journey option is returned by the engine. |
| **Stop-Sequence Correctness (%)** | Percentage of evaluated route legs where boarding stop precedes alighting stop in the GTFS route sequence. |
| **Transfer Validity Rate (%)** | Percentage of 1-transfer routes where transfer stops match or are within 500m walking distance with feasible buffer time. |
| **Average Fare Error (INR)** | Mean absolute difference `\|fare_predicted - fare_reference\|` (and separately vs Ground-Truth field observations). |
| **Mean Absolute Travel Time Error (mins)** | Mean absolute difference `\|duration_predicted - duration_reference\|` (and separately vs Ground-Truth field observations). |
| **Median (P50) & P95 Latency (ms)** | Median and 95th percentile backend engine response execution latency in milliseconds. |
| **Timeout & Error Rate (%)** | Percentage of test runs that resulted in a HTTP/Backend exception or timeout. |
| **Missing Route Cases Count** | Count of test cases expecting service where the engine returned 0 options. |
| **False Positive Recommendations** | Count of recommended journeys that failed GTFS reference validation. |

---

## 6. Generated Reports

Each benchmark run automatically writes 3 output artifacts to `backend/benchmarks/results/`:
1. `benchmark_results_<timestamp>.csv`: Detailed CSV log with 1 row per test case.
2. `benchmark_summary_<timestamp>.json`: Machine-readable summary metrics.
3. `benchmark_report_<timestamp>.html`: Visual HTML report with performance breakdown tables and latency metrics.
