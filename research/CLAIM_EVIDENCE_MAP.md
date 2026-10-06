# CLAIM TO EVIDENCE TRACEABILITY MAPPING
**Conference**: 31st International Conference on Advanced Computing and Communications (ADCOM 2027)  
**Paper Title**: A Centrally Coordinated Multi-Agent Architecture for Personalized and Context-Aware Multimodal Urban Mobility Recommendation  
**Purpose**: Internal traceability map linking every manuscript assertion in `main.tex` to exact CSV/JSON data files, Python execution functions, and code line numbers.  

---

## Traceability Mapping Table

| Assertion ID | Manuscript Claim Text (`main.tex`) | Supporting CSV / JSON Artifact | Source Function & File | Code Lines | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C1** | "Cold-start initialization required 204.22 s." | `experiment_summary_stats.json` (`cold_start_overhead_ms`: `204224.39`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L90-L115) | L90-L115 | **VERIFIED & MATCHED** |
| **C2** | "After initialization, warm-state RSS was 811.38 MB, with a measured peak RSS of 883.77 MB." | `experiment_summary_stats.json` (`warm_rss_mb`: `811.38`, `peak_rss_mb`: `883.77`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L112-L120) | L112-L120 | **VERIFIED & MATCHED** |
| **C3** | "Average sequential warm latency across corridors is 2.75 ms, while parallel warm latency averages 3.43 ms (median: 2.90 ms, P95: 5.82 ms)." | `benchmark_corridors_results.csv` & `experiment_summary_stats.json` | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L125-L220) | L125-L220 | **VERIFIED & MATCHED** |
| **C4** | "Monolithic context-aware routing (B4) achieves a mean latency of 3.12 ms ... while Coordinated MAS (B5) achieves 4.83 ms." | `baselines_comparison.csv` (`B4`: `3.12`, `B5`: `4.83`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L225-L235) | L225-L235 | **VERIFIED & MATCHED** |
| **C5** | "Disabling multi-agent candidate coordination (A4) causes a 47.5% relative reduction in utility score (95.3 -> 50.0)." | `ablation_study_results.csv` (`A0`: `95.3`, `A4`: `50.0`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L236-L280) | L236-L280 | **VERIFIED & MATCHED** |
| **C6** | "Peak system throughput reaches 231.69 QPS at C=5 concurrent requests ... maintaining 194.54 QPS at C=50." | `scalability_concurrency_results.csv` (`C=5`: `231.69`, `C=50`: `194.54`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L358-L408) | L358-L408 | **VERIFIED & MATCHED** |
| **C7** | "Weather Agent progressively reduces weather suitability from 1.00 to 0.92, adjusting utility (97.3 -> 96.5)." | `weather_scenarios_results.csv` (`Clear`: `1.00`/`97.3`, `Heavy Rain`: `0.92`/`96.5`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L285-L320) | L285-L320 | **VERIFIED & MATCHED** |
| **C8** | "Under high gridlock (2.0x), the traffic-dependent utility penalty adjusts the score from 94.8 to 89.8." | `traffic_scenarios_results.csv` (`1.0x`: `94.8`, `2.0x`: `89.8`) | `run_comprehensive_experimental_suite()` in [`run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py#L321-L357) | L321-L357 | **VERIFIED & MATCHED** |
