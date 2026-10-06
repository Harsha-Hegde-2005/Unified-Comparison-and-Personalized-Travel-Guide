# Coordinated Multi-Agent Urban Mobility Recommendation Framework
**Target Conference**: 31st International Conference on Advanced Computing and Communications (ADCOM 2027)  
**Track**: Track 3 – Core Multi-Agent Systems and Collaborative Reasoning  
**Target Publication**: Springer Communications in Computer and Information Science (CCIS)  

---

## Executive Overview

This repository contains the complete, reproducible research implementation, empirical benchmark suite, automated LaTeX table generator, and paper manuscript for the paper titled:

> **"A Centrally Coordinated Multi-Agent Architecture for Personalized and Context-Aware Multimodal Urban Mobility Recommendation"**

The system decomposes heterogeneous urban transport modes in Bengaluru, India (BMTC public buses, Namma Metro rapid rail, ride-hailing cabs, and personal motor vehicles) into specialized mobility agents and coordination services modeled by formal 5-tuple policies $A_i = (O_i, S_i, G_i, A_i, \pi_i)$ with typed inter-agent message contracts.

---

## Repository Structure

```
research/
├── mas/
│   ├── agent_interface.py    # Typed structs (AgentMessage, AgentObservation) & BaseAgent class
│   ├── agents.py             # 8 specialized mobility & environmental agent implementations
│   └── coordinator.py        # Asynchronous coordinator with warm caching & baseline overrides
├── scripts/
│   ├── run_experiments.py          # Empirical benchmark suite runner (Phases 4-15)
│   ├── generate_plots.py           # Publication-quality plot renderer (Figures 5-8)
│   ├── generate_latex_tables.py    # Automated LaTeX table generator
│   └── verify_paper_numbers.py     # Programmatic quantitative verification auditor
├── experiments/
│   └── results/                    # CSVs & JSON stats generated automatically
├── figures/                        # 300 DPI PNG figures generated directly from CSVs
├── paper/
│   ├── main.tex                    # Springer LLNCS manuscript with included generated tables
│   ├── references.bib              # 23 verified references with DOIs
│   └── generated_*.tex             # Programmatically generated LaTeX tables
├── AUDIT_REPAIR_REPORT.md         # Phase 1 forensic audit classification table
├── CLAIM_EVIDENCE_MAP.md          # Internal claim-to-code/CSV traceability map
├── FINAL_SUBMISSION_AUDIT.md      # 25-point scientific compliance checklist
├── VERSION_CONSISTENCY_REPORT.md  # Deliverable verification matrix
└── PEER_REVIEWS.md                # Simulated double-blind peer review report (Score: 7.8/10)
```

---

## Reproduction Instructions

To execute the entire empirical suite, regenerate all figures, build the LaTeX tables, and verify the manuscript numbers programmatically, run:

```bash
# 1. Execute full empirical benchmarking suite (Cold-start, Corridors, Baselines, Ablations, Concurrency)
python research/scripts/run_experiments.py

# 2. Render publication-quality high-DPI plots from generated CSV data
python research/scripts/generate_plots.py

# 3. Generate automated LaTeX tables for main.tex
python research/scripts/generate_latex_tables.py

# 4. Run programmatic paper numbers verification audit
python research/scripts/verify_paper_numbers.py
```

---

## Key Empirical Findings

1. **Cold-Start vs. Warm-Start Isolation**: Initial GTFS schedule graph construction (193k nodes, 193k edges, 3,959 routes) requires $204.22\text{ s}$ cold-start overhead ($811.38\text{ MB}$ warm RSS memory). Warm-start candidate evaluations execute in milliseconds ($2.75\text{ ms}$ sequential vs. $3.43\text{ ms}$ parallel average warm latency).
2. **Multi-Agent Coordination Overhead**: On ultra-fast in-memory evaluations, parallel thread pool management and Python lock contention introduce a $24.7\%$ latency overhead ($3.43\text{ ms}$ vs. $2.75\text{ ms}$) across 20 corridors ($N=10$ trials). This overhead represents a trade-off for modular agent isolation and extensibility.
3. **Concurrency Scalability**: Under concurrent client benchmarking, system throughput reaches a peak of $231.69\text{ QPS}$ at $C=5$ concurrent requests and sustains $194.54\text{ QPS}$ at $C=50$ ($0.0\%$ failure rate).
4. **Component Ablations**: Disabling candidate coordination ($A_4$) results in a $47.5\%$ relative reduction in utility score ($95.3 \rightarrow 50.0$), indicating the importance of coordinated candidate aggregation.
