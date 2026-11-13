# Phase 1: Forensic Repository Audit & Repair Plan

## Executive Summary
This document presents a forensic scientific audit of the research package for the paper:
> *"A Coordinated Multi-Agent Decision Framework for Personalized and Context-Aware Multimodal Urban Mobility Recommendation"* (ADCOM 2027 Submission).

Every claim in `main.tex` and `PROJECT_AUDIT.md` was cross-referenced against the actual code (`research/mas/`, `backend/`) and generated data (`research/experiments/results/`). Inconsistencies between paper text and empirical codebase output have been identified, classified, and provided with explicit repair actions in accordance with the **Absolute Scientific Integrity Rule**.

---

## 1. Claim Classification Matrix

| ID | Manuscript Claim | Ground-Truth Code / Data Evidence | Classification | Required Repair Action |
| :--- | :--- | :--- | :---: | :--- |
| **C1** | *"34.8% reduction in mean recommendation latency (3.54 ms vs 5.43 ms)"* | `benchmark_corridors_results.csv` shows sequential mean $7,431.79\text{ ms}$ (due to C01 cold-start GTFS load of $95,508.87\text{ ms}$) and parallel mean $12.19\text{ ms}$. The $5.43\text{ ms}$ / $3.54\text{ ms}$ values were hardcoded in text. | **UNSUPPORTED** | Execute $N=30$ repeated warm-start benchmark trials after 1 warm-up run. Report exact Warm-Start mean, median, P95, P99, and Cold-Start overhead in separate tables. |
| **C2** | *"66.3% reduction in 95th percentile latency"* | Raw dataset single run did not separate cold-start GTFS load ($95.5\text{s}$) from warm query processing. | **UNSUPPORTED** | Calculate empirical $P_{95}$ latency over 30 warm-start trials and update manuscript text with exact empirical $P_{95}$ delta. |
| **C3** | *"Dynamic weather exposure modeling increases overall utility by 22.7%"* | `ablation_study_results.csv` showed top score dropped from $96.5$ to $97.3$ because `car` dominated every route due to static hardcoded parameters in `PersonalVehicleAgent`. | **UNSUPPORTED** | Fix `PersonalVehicleAgent` to use dynamic origin-destination coordinates. Implement true agent disabling for ablations ($A_1$ disabling ContextAgent weather module). Re-run weather ablation and report exact empirical delta. |
| **C4** | *"Executes a multi-criteria Pareto normalization algorithm"* | `agents.py` line 342 computes min-max normalized weighted sum $U(j) = \sum w_k f_k(j)$, NOT Pareto dominance / Pareto front extraction. | **UNSUPPORTED** | Accurately rename method throughout paper, code, text, tables, and figures as **Weighted Multi-Criteria Utility Aggregation** $U(j) = \sum w_k f_k(j)$. |
| **C5** | *"Asynchronous contract-net consensus algorithm"* | `coordinator.py` uses Python `ThreadPoolExecutor` to execute mobility agents in parallel. It is a centralized parallel coordinator, not a decentralized contract-net negotiation protocol. | **PARTIALLY SUPPORTED** | Clarify the architecture as a **Parallel Coordinated Multi-Agent Decision Framework** using typed agent messages (`REQUEST_ROUTE`, `CANDIDATE_ROUTE`), explicitly distinguishing parallel candidate generation from decentralized consensus. |
| **C6** | *"Personal vehicle fuel cost and driving time estimates"* | `PersonalVehicleAgent` in `agents.py` used static constants: `dist_km = 12.0`, `cost = 81.6`, `time_val = 28.8` regardless of corridor origin/destination. | **UNSUPPORTED** | Update `PersonalVehicleAgent` to resolve origin/destination coordinates dynamically, compute Haversine/road distance $D_{\text{veh}}$, and calculate fuel cost $C_{\text{fuel}} = (D_{\text{veh}} / \text{mileage}) \times \text{fuel\_price}$ dynamically per corridor. |
| **C7** | *"Baselines B1 to B5 evaluate distinct decision strategies"* | Baselines $B_1$ to $B_5$ in `run_experiments.py` set dictionary weights, but `CoordinatorAgent.rank_candidates` was called identically without isolating single-objective time ($B_1$) or single-objective cost ($B_2$). | **PARTIALLY SUPPORTED** | Re-implement baselines: $B_1$ ranks purely by travel time score $f_t(T_i)$, $B_2$ purely by monetary fare score $f_c(C_i)$, $B_3$ by static weighted sum without weather/traffic, $B_4$ by monolithic sequential execution, and $B_5$ by parallel coordinated MAS. |
| **C8** | *"Scalability throughput of 439.5 QPS"* | `scalability_concurrency_results.csv` and `experiment_summary_stats.json` were missing or incomplete in the previous artifact package. | **UNSUPPORTED** | Run concurrency benchmark for $C \in \{1, 5, 10, 25, 50, 100\}$ concurrent requests, record QPS, latency, memory, failure rate, and save output directly into `scalability_concurrency_results.csv` and `experiment_summary_stats.json`. |

---

## 2. Forensic Audit Findings Summary

1. **Cold-Start vs. Warm-Start Confounding**:
   - The first run of Experiment 1 included the GTFS graph load overhead ($95,508.87\text{ ms}$), causing an artificial $34,730.5\times$ speedup calculation for Corridor C01. Subsequent queries operated on warm memory (~1.8ms - 5.5ms).
   - *Fix*: The experimental suite will explicitly execute 1 warm-up run to load GTFS graphs into memory, followed by $N = 30$ measured warm-start trials. Cold-start initialization time will be reported separately as system startup overhead ($T_{\text{init}}$).

2. **Personal Vehicle Agent Hardcoding**:
   - `PersonalVehicleAgent` returned static values ($12\text{ km}$, ₹81.6, 28.8 min) for all routes, causing `car` to artificially win every single corridor evaluation.
   - *Fix*: Refactor `PersonalVehicleAgent` to resolve route-specific geographic coordinates, compute real driving distance $D$, driving time $T = D / V_{\text{speed}}$, and fuel cost $C = D \times \text{cost\_per\_km}$.

3. **Terminology Alignment (Pareto vs. Weighted Sum)**:
   - The manuscript claimed "Pareto optimization" while the codebase implemented normalized weighted sum scalarization.
   - *Fix*: Consistently update all manuscript text, mathematical formulations, figures, tables, and code docstrings to **Weighted Multi-Criteria Utility Aggregation** $U(j) = \sum w_k f_k(j)$.

4. **True Ablation Isolation**:
   - Previous ablations altered environmental inputs rather than disabling agent modules.
   - *Fix*: Implement explicit boolean flags in agent configurations (`enable_weather=False`, `enable_traffic=False`, `enable_preferences=False`, `enable_coordination=False`) to guarantee true component ablation.
