r"""
diagnose_agents.py
==================
Diagnostic verification tool for Multi-Agent System (MAS) Candidate Generation.
Verifies that BMTC, Metro, Cab, and Personal Vehicle agents generate valid CandidateJourney
proposals across representative Bengaluru OD pairs.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from research.mas.agent_interface import AgentObservation
from research.mas.coordinator import MultiAgentSystemCoordinator
from research.scripts.run_experiments import BENCHMARK_CORRIDORS


def run_agent_diagnostic():
    print("=" * 80, flush=True)
    print("MULTI-AGENT MOBILITY SYSTEM DIAGNOSTIC VERIFICATION", flush=True)
    print("=" * 80, flush=True)

    coord = MultiAgentSystemCoordinator()

    # Pre-warm
    print("\nWarming up agent planners...", flush=True)
    coord.warm_up()
    print("Warm-up complete!\n", flush=True)

    summary_table = []

    for corr in BENCHMARK_CORRIDORS:
        cid = corr["id"]
        cname = corr["name"]
        src = corr["source"]
        dst = corr["destination"]

        obs = AgentObservation(source=src, destination=dst)
        res = coord.run_sequential(obs)

        recs = res.get("recommendations", [])
        exps = res.get("explanations", {})

        # Count candidates per mode
        modes_found = {}
        for item in recs:
            c = item["candidate"]
            modes_found[c.mode] = {
                "cost": round(c.cost, 1),
                "time_min": round(c.time_min, 1),
                "score": item["score"]
            }

        # Check agent execution results
        bmtc_res = getattr(coord.bmtc_agent, "last_result", None)
        metro_res = getattr(coord.metro_agent, "last_result", None)
        cab_res = getattr(coord.cab_agent, "last_result", None)
        veh_res = getattr(coord.veh_agent, "last_result", None)

        bmtc_status = bmtc_res.status if bmtc_res else "unknown"
        metro_status = metro_res.status if metro_res else "unknown"
        cab_status = cab_res.status if cab_res else "unknown"
        veh_status = veh_res.status if veh_res else "unknown"

        top_winner = recs[0]["candidate"].mode if recs else "none"
        top_score = recs[0]["score"] if recs else 0.0

        summary_table.append({
            "id": cid,
            "corridor": cname,
            "total_candidates": len(recs),
            "bmtc_status": bmtc_status,
            "metro_status": metro_status,
            "cab_status": cab_status,
            "veh_status": veh_status,
            "winner": top_winner,
            "top_score": top_score,
            "modes_detail": modes_found
        })

        print(f"[{cid}] {src} -> {dst}", flush=True)
        print(f"  Total Candidates: {len(recs)}", flush=True)
        print(f"  BMTC: {bmtc_status} | Metro: {metro_status} | Cab: {cab_status} | Car: {veh_status}", flush=True)
        print(f"  Top Choice: {top_winner.upper()} (Score: {top_score})", flush=True)
        for mode, d in modes_found.items():
            print(f"    - {mode.upper()}: Rs.{d['cost']}, {d['time_min']} min, Utility Score: {d['score']}", flush=True)
        print("-" * 60, flush=True)

    # Print Summary statistics across all 20 corridors
    print("\n" + "=" * 80, flush=True)
    print("DIAGNOSTIC SUMMARY ACROSS ALL 20 CORRIDORS", flush=True)
    print("=" * 80, flush=True)
    total_corridors = len(summary_table)
    bmtc_avail = sum(1 for row in summary_table if row["bmtc_status"] == "success")
    metro_avail = sum(1 for row in summary_table if row["metro_status"] == "success")
    cab_avail = sum(1 for row in summary_table if row["cab_status"] == "success")
    veh_avail = sum(1 for row in summary_table if row["veh_status"] == "success")
    multi_candidate_count = sum(1 for row in summary_table if row["total_candidates"] > 1)

    print(f"Total Corridors Tested: {total_corridors}", flush=True)
    print(f"BMTC Candidates Available: {bmtc_avail}/{total_corridors}", flush=True)
    print(f"Metro Candidates Available: {metro_avail}/{total_corridors}", flush=True)
    print(f"Cab Candidates Available: {cab_avail}/{total_corridors}", flush=True)
    print(f"Personal Vehicle Candidates Available: {veh_avail}/{total_corridors}", flush=True)
    print(f"Corridors evaluating MULTIPLE candidates: {multi_candidate_count}/{total_corridors}", flush=True)
    print("=" * 80, flush=True)

    return summary_table


if __name__ == "__main__":
    run_agent_diagnostic()
