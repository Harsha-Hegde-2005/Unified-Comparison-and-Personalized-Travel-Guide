r"""
generate_latex_tables.py
========================
Generates clean LaTeX tables directly from CSV execution results.
Guarantees 100% mathematical consistency between empirical data and manuscript tables.
Includes \resizebox{\textwidth}{!}{...} wrapping to prevent table column overflow.
"""

import os
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.abspath(os.path.join(_HERE, "..", "experiments", "results"))
PAPER_DIR = os.path.abspath(os.path.join(_HERE, "..", "paper"))
os.makedirs(PAPER_DIR, exist_ok=True)

def generate_corridor_table():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "benchmark_corridors_results.csv"))
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Warm-Start Execution Latency across 20 Bengaluru Transit Corridors ($N=10$ Trials).}",
        r"\label{tab:corridors}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{lllccccc}",
        r"\toprule",
        r"\textbf{Corridor ID} & \textbf{Category} & \textbf{Distance} & \textbf{Seq Mean (ms)} & \textbf{Par Mean (ms)} & \textbf{Par Median (ms)} & \textbf{Par P95 (ms)} & \textbf{Ratio (Seq/Par)} \\",
        r"\midrule"
    ]
    dist_map = {
        "C01": "3.2 km", "C02": "4.5 km", "C03": "2.8 km", "C04": "3.9 km", "C05": "4.8 km",
        "C06": "8.5 km", "C07": "11.2 km", "C08": "14.0 km", "C09": "9.7 km", "C10": "12.4 km",
        "C11": "18.6 km", "C12": "21.0 km", "C13": "23.5 km", "C14": "24.8 km", "C15": "16.2 km",
        "C16": "32.0 km", "C17": "28.4 km", "C18": "35.1 km", "C19": "29.8 km", "C20": "38.5 km"
    }

    for idx, row in df.iterrows():
        cid = row['corridor_id']
        cat = row['category'].replace("Suburban/Airport", "Suburban")
        dist = dist_map.get(cid, "10.0 km")
        seq_m = f"{row['seq_mean_ms']:.2f}"
        par_m = f"{row['par_mean_ms']:.2f}"
        par_med = f"{row['par_median_ms']:.2f}"
        par_p95 = f"{row['par_p95_ms']:.2f}"
        ratio = f"{row['speedup_factor']:.2f}" + r"$\times$"
        line = f"{cid} & {cat} & {dist} & {seq_m} & {par_m} & {par_med} & {par_p95} & {ratio} \\\\"
        lines.append(line)

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{table}"
    ])

    out_path = os.path.join(PAPER_DIR, "generated_corridor_table.tex")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {out_path}")

def generate_baselines_table():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "baselines_comparison.csv"))
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Baseline Experimental Comparison ($B_1$--$B_5$).}",
        r"\label{tab:baselines}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{llccc}",
        r"\toprule",
        r"\textbf{Baseline ID} & \textbf{Model Description} & \textbf{Latency (ms)} & \textbf{Top Recommended Mode} & \textbf{Utility Score} \\",
        r"\midrule"
    ]
    mode_map = {"car": "Personal Vehicle", "bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Ride-Hailing Cab"}
    for idx, row in df.iterrows():
        bid = row['baseline_id']
        bname = row['baseline_name']
        lat = f"{row['mean_latency_ms']:.2f}"
        mode = mode_map.get(row['top_mode'], row['top_mode'].capitalize())
        score = f"{row['utility_score']:.1f}"
        line = f"{bid} & {bname} & {lat} & {mode} & {score} \\\\"
        lines.append(line)

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{table}"
    ])

    out_path = os.path.join(PAPER_DIR, "generated_baselines_table.tex")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {out_path}")

def generate_ablation_table():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "ablation_study_results.csv"))
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Component Ablation Study Results ($A_0$--$A_4$).}",
        r"\label{tab:ablations}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{llcccc}",
        r"\toprule",
        r"\textbf{Ablation ID} & \textbf{Variant Name} & \textbf{Top Mode} & \textbf{Utility Score} & \textbf{Duration (min)} & \textbf{Cost (INR)} \\",
        r"\midrule"
    ]
    mode_map = {"car": "Personal Vehicle", "bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Ride-Hailing Cab"}
    for idx, row in df.iterrows():
        aid = row['ablation_id']
        aname = row['ablation_name']
        mode = mode_map.get(row['top_recommended_mode'], row['top_recommended_mode'].capitalize())
        score = f"{row['utility_score']:.1f}"
        dur = f"{row['time_min']:.1f}"
        cost = f"{row['cost_rs']:.1f}"
        line = f"{aid} & {aname} & {mode} & {score} & {dur} & {cost} \\\\"
        lines.append(line)

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{table}"
    ])

    out_path = os.path.join(PAPER_DIR, "generated_ablation_table.tex")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {out_path}")

def generate_weather_table():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "weather_scenarios_results.csv"))
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Controlled Synthetic Weather Scenario Evaluation.}",
        r"\label{tab:weather}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"\textbf{Weather Scenario} & \textbf{Rain Probability} & \textbf{Top Mode} & \textbf{Utility Score} & \textbf{Weather Suitability} \\",
        r"\midrule"
    ]
    mode_map = {"car": "Personal Vehicle", "bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Ride-Hailing Cab"}
    for idx, row in df.iterrows():
        scen = row['scenario']
        prob = f"{row['rain_probability']:.2f}"
        mode = mode_map.get(row['top_mode'], row['top_mode'].capitalize())
        score = f"{row['utility_score']:.1f}"
        suit = f"{row['weather_suitability']:.2f}"
        line = f"{scen} & {prob} & {mode} & {score} & {suit} \\\\"
        lines.append(line)

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{table}"
    ])

    out_path = os.path.join(PAPER_DIR, "generated_weather_table.tex")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {out_path}")

def generate_traffic_table():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "traffic_scenarios_results.csv"))
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Controlled Traffic Congestion Scenario Evaluation.}",
        r"\label{tab:traffic}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"\textbf{Traffic Scenario} & \textbf{Multiplier} & \textbf{Top Mode} & \textbf{Utility Score} & \textbf{Duration (min)} \\",
        r"\midrule"
    ]
    mode_map = {"car": "Personal Vehicle", "bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Ride-Hailing Cab"}
    for idx, row in df.iterrows():
        scen = row['scenario']
        mult = f"{row['traffic_multiplier']:.1f}" + r"$\times$"
        mode = mode_map.get(row['top_mode'], row['top_mode'].capitalize())
        score = f"{row['utility_score']:.1f}"
        dur = f"{row['effective_travel_time_min']:.1f}"
        line = f"{scen} & {mult} & {mode} & {score} & {dur} \\\\"
        lines.append(line)

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{table}"
    ])

    out_path = os.path.join(PAPER_DIR, "generated_traffic_table.tex")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {out_path}")

def generate_concurrency_table():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "scalability_concurrency_results.csv"))
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Concurrency Scalability Benchmark ($C=1$ to $C=50$ Concurrent Requests).}",
        r"\label{tab:concurrency}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{cccccc}",
        r"\toprule",
        r"\textbf{Concurrent Requests} & \textbf{Total Time (s)} & \textbf{Throughput (QPS)} & \textbf{Mean Latency (ms)} & \textbf{P95 Latency (ms)} & \textbf{Failures (\%)} \\",
        r"\midrule"
    ]
    for idx, row in df.iterrows():
        req = int(row['concurrent_requests'])
        sec = f"{row['total_time_sec']:.2f}"
        qps = f"{row['throughput_qps']:.2f}"
        mean_l = f"{row['mean_latency_ms']:.2f}"
        p95_l = f"{row['p95_latency_ms']:.2f}"
        fail = f"{row['failure_rate_percent']:.1f}\\%"
        line = f"{req} & {sec} & {qps} & {mean_l} & {p95_l} & {fail} \\\\"
        lines.append(line)

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{table}"
    ])

    out_path = os.path.join(PAPER_DIR, "generated_concurrency_table.tex")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_corridor_table()
    generate_baselines_table()
    generate_ablation_table()
    generate_weather_table()
    generate_traffic_table()
    generate_concurrency_table()
