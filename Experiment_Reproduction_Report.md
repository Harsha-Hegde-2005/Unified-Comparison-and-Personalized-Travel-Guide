# Experiment Reproduction & Verification Protocol

**Project:** *Unified Transit Routing System (UTRS) & Coordinated Multi-Agent Journey Recommendation*  
**Environment:** Windows 11 / Python 3.13 / Intel Core i7-13650HX / 32 GB RAM / 1 TB NVMe SSD  
**Target Submission:** ADCOM 2027 / Springer Communications in Computer and Information Science (CCIS)  
**Date of Audit:** October 31, 2026  

---

## 1. Experimental Environment & Setup Verification

To reproduce all numerical metrics, tables, and figures reported in the research paper, the following runtime dependencies and data paths must be present:

* **Python Runtime:** Python 3.10+ (tested on Python 3.13)
* **Required Libraries:** `fastapi`, `uvicorn`, `pandas`, `numpy`, `scipy`, `psutil`, `matplotlib`, `pytest`
* **Core Transit Datasets:**
  * Cleaned Stops: `database/bmtc/processed/bmtc_stop_level_cleaned.csv`
  * Graph Deserialization Cache: `database/bmtc/processed/graph_cache.pkl` ($193,178$ nodes, $193,772$ edges)
  * Reverse Route Definitions: `database/bmtc/processed/reverse_routes_supplement.csv` ($3,959$ routes)
  * SQLite Timetable Engine: `database/gtfs_index.db` ($4,414$ indexed stop norms, $859,996$ timetable entries)
  * Metro Coordinate & Route Cache: `database/metro/metro_coords.json`, `database/metro/fare_matrix.csv`
  * Cab Pricing Rate Cards: `database/cab/fare_config.json`

---

## 2. Command-by-Command Reproduction Protocol

### A. Cold-Start Initialization & Transit Graph Verification
Verifies the $130.77\text{ s}$ cold-start initialization and memory footprint ($143.16\text{ MB} \rightarrow 880.62\text{ MB} \rightarrow 883.84\text{ MB}$).

```powershell
python -c "
import time, psutil, os, pickle
p = psutil.Process()
print('Startup RSS:', round(p.memory_info().rss / (1024*1024), 2), 'MB')
t0 = time.perf_counter()
with open('database/bmtc/processed/graph_cache.pkl', 'rb') as f:
    d = pickle.load(f)
t1 = time.perf_counter()
print('Graph Nodes:', len(d[0]))
print('Graph Edges:', sum(len(v) for v in d[0].values()))
print('Graph Load Time:', round(t1 - t0, 2), 's')
print('Warm RSS:', round(p.memory_info().rss / (1024*1024), 2), 'MB')
"
```
* **Expected Output:**
  * `Startup RSS:` $\approx 143\text{ MB}$
  * `Graph Nodes:` $193178$
  * `Graph Edges:` $193772$
  * `Warm RSS:` $\approx 880\text{ MB}$

---

### B. Reproducing the 20-Corridor Latency Benchmark (Table 6 & Figure 4)
Executes $N=10$ repeated warm-start trials per corridor across all 20 benchmark routes.

```powershell
# Run full corridor benchmark suite
python -c "
from research.scripts.run_experiments import run_comprehensive_experimental_suite
run_comprehensive_experimental_suite(num_trials=10)
"
```
* **Raw Output Location:** `research/experiments/results/benchmark_corridors_results.csv`
* **Verification Command:**
```powershell
python -c "
import pandas as pd
df = pd.read_csv('research/experiments/results/benchmark_corridors_results.csv')
print('Sequential Mean:', round(df['seq_mean_ms'].mean(), 2), 'ms')
print('Parallel Mean:', round(df['par_mean_ms'].mean(), 2), 'ms')
print('Parallel Median:', round(df['par_median_ms'].mean(), 2), 'ms')
print('Parallel P95:', round(df['par_p95_ms'].mean(), 2), 'ms')
print('Average Per-Corridor Speedup:', round(df['speedup_factor'].mean(), 2), 'x')
print('Overall Latency Ratio:', round(df['seq_mean_ms'].mean() / df['par_mean_ms'].mean(), 2), 'x')
"
```
* **Expected Results:**
  * Sequential Mean: **$371.67\text{ ms}$**
  * Parallel Mean: **$235.74\text{ ms}$**
  * Parallel Median: **$203.79\text{ ms}$**
  * Parallel P95: **$453.74\text{ ms}$**
  * Average Speedup: **$1.93\times$**
  * Ratio of Means: **$1.58\times$**

---

### C. Reproducing Baseline Comparisons ($B_1$ to $B_5$ — Table 7)
Evaluates single-objective and multi-objective routing strategies under identical inputs.

* **Raw Output Location:** `research/experiments/results/baselines_comparison.csv`
* **Verification Command:**
```powershell
python -c "
import pandas as pd
df = pd.read_csv('research/experiments/results/baselines_comparison.csv')
for idx, r in df.iterrows():
    print(f\"{r['baseline_id']}: Mean={r['mean_latency_ms']}ms, TopMode={r['top_mode']}, Score={r['utility_score']}\")
"
```
* **Expected Results:**
  * $B_1$ (Shortest-Time): $371.66\text{ ms}$, Car, $46.2\text{ min}$, ₹$131.0$
  * $B_2$ (Lowest-Cost): $305.61\text{ ms}$, Metro, $48.0\text{ min}$, ₹$84.0$
  * $B_3$ (Static Sum): $370.93\text{ ms}$, Metro, $48.0\text{ min}$, ₹$84.0$
  * $B_4$ (Monolithic Context): $325.69\text{ ms}$, Metro, $48.0\text{ min}$, ₹$84.0$
  * $B_5$ (Coordinated MAS): $66.45\text{ ms}$ (Median $19.80\text{ ms}$, P95 $262.70\text{ ms}$)

---

### D. Reproducing Component Ablations ($A_0$ to $A_4$ — Table 8 & Figure 5)
Evaluates the contribution of discrete agents under heavy rain ($90\%$) and traffic congestion ($1.5\times$).

* **Raw Output Location:** `research/experiments/results/ablation_study_results.csv`
* **Verification Command:**
```powershell
python -c "
import pandas as pd
df = pd.read_csv('research/experiments/results/ablation_study_results.csv')
base_score = df.loc[df['ablation_id']=='A0', 'utility_score'].values[0]
for idx, r in df.iterrows():
    diff = round(((r['utility_score'] - base_score) / base_score) * 100, 1)
    diff_str = 'Baseline' if r['ablation_id']=='A0' else f\"{diff:+}%\"
    print(f\"{r['ablation_id']} ({r['ablation_name']}): Score={r['utility_score']}, Change={diff_str}\")
"
```
* **Expected Results:**
  * $A_0$ (Full MAS): **$82.3$** (*Baseline*)
  * $A_1$ (No Weather): **$84.0$** (**$+2.1\%$**)
  * $A_2$ (No Traffic): **$82.3$** (**$0.0\%$**)
  * $A_3$ (No Preferences): **$77.2$** (**$-6.2\%$**)
  * $A_4$ (No Coordination): **$50.0$** (**$-39.2\%$**)

---

### E. Reproducing Concurrency & Scalability ($C=1$ to $50$ — Table 11 & Figure 6)
Executes $M=5$ repeated load-test trials across increasing concurrent client threads.

* **Raw Output Location:** `research/experiments/results/scalability_concurrency_results.csv`
* **Verification Command:**
```powershell
python -c "
import pandas as pd
df = pd.read_csv('research/experiments/results/scalability_concurrency_results.csv')
for idx, r in df.iterrows():
    print(f\"C={int(r['concurrent_requests'])}: Throughput={r['throughput_qps']} QPS, MeanLat={r['mean_latency_ms']}ms, P95={r['p95_latency_ms']}ms, Failures={r['failure_rate_percent']}%\")
"
```
* **Expected Results:**
  * $C=1$: $1.73\text{ QPS}$, Mean $571.60\text{ ms}$, Failures $0.0\%$
  * $C=5$: $39.24\text{ QPS}$, Mean $113.81\text{ ms}$, Failures $0.0\%$ (Short route sampling)
  * $C=10$: $13.29\text{ QPS}$, Mean $275.57\text{ ms}$, P95 $647.63\text{ ms}$, Failures $0.0\%$ (Arterial straggler bottleneck)
  * $C=25$: $39.47\text{ QPS}$, Mean $344.03\text{ ms}$, Failures $0.0\%$
  * $C=50$: $83.85\text{ QPS}$, Mean $379.99\text{ ms}$, Failures $0.0\%$ (Full CPU thread saturation)

---

### F. Automated Test Suite Verification (Pytest)
Validates RAG factual retrieval, TTFT generation budget, and hallucination tolerance.

```powershell
pytest testing/test_abstract_and_rag_verification.py -v
```
* **Expected Output:**
  * `test_cold_start_gtfs_initialization`: **PASSED**
  * `test_warm_start_20_corridor_benchmark_latency`: **PASSED**
  * `test_concurrency_scalability_50_qps`: **PASSED**
  * `test_component_ablation_39_percent_drop`: **PASSED**
  * `test_rag_retrieval_latency`: **PASSED** ($8.42\text{ ms}$)
  * `test_rag_first_token_generation_budget`: **PASSED** ($210.50\text{ ms}$)
  * `test_rag_hallucination_zero_tolerance`: **PASSED** ($0.0\%$ on verified transit entities)

---

## 3. Disclosed Reproduction Boundaries

1. **Third-Party API Paywalls**: Commercial ride-hailing services (Ola, Uber) do not provide public, unmetered rate APIs. Dynamic cab estimates are calibrated via offline tariff models validated against 50 real-world ride samples ($\text{MAPE} = 8.34\%$).
2. **Public Routing Fallback**: The public demo OSRM server (`router.project-osrm.org`) is subject to network rate-limiting. When unavailable, the engine falls back deterministically to Haversine distance calibrated with a road tortuosity factor of $\tau = 1.30$.
3. **Hardware Specifics**: Latencies reflect an Intel Core i7-13650HX with fast NVMe storage; running on low-tier hardware without in-memory caching will yield higher cold-start graph deserialization times.

