r"""
generate_plots.py
=================
Generates publication-quality high-DPI plots for the Springer CCIS manuscript directly from CSV files.
Produces Figures 5, 6, 7, and 8 stored under research/figures/.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set publication style parameters
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#e0e0e0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

_HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.abspath(os.path.join(_HERE, "..", "experiments", "results"))
FIGURES_DIR = os.path.abspath(os.path.join(_HERE, "..", "figures"))
os.makedirs(FIGURES_DIR, exist_ok=True)


def plot_corridor_warm_latency():
    csv_path = os.path.join(RESULTS_DIR, "benchmark_corridors_results.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    x = np.arange(len(df))
    width = 0.35

    rects1 = ax.bar(x - width/2, df["seq_mean_ms"], width, label="Sequential B4 (Monolithic)", color="#e74c3c", alpha=0.85)
    rects2 = ax.bar(x + width/2, df["par_mean_ms"], width, label="Parallel B5 (Coordinated MAS)", color="#2ecc71", alpha=0.85)

    ax.set_ylabel("Warm-Start Latency (ms)", fontsize=11, fontweight="bold")
    ax.set_title("Figure 5: Warm-Start Latency Comparison Across 20 Bengaluru Transit Corridors (N=30 Trials)", fontsize=11, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(df["corridor_id"], rotation=45, ha="right", fontsize=9)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
    ax.grid(axis="y")

    plt.tight_layout()
    plot_path = os.path.join(FIGURES_DIR, "fig5_latency_comparison.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved Figure 5 to {plot_path}")


def plot_ablation_study():
    csv_path = os.path.join(RESULTS_DIR, "ablation_study_results.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(7, 4), dpi=300)
    colors = ["#2ecc71", "#e67e22", "#e74c3c", "#9b59b6", "#3498db"]
    bars = ax.barh(df["ablation_name"], df["utility_score"], color=colors[:len(df)], alpha=0.85)

    ax.set_xlabel("Weighted Multi-Criteria Utility Score (0 - 100)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 6: System Component Ablation Study Impact (A0 - A4)", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlim(0, 100)
    ax.grid(axis="x")

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, f"{width:.1f}", ha="left", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plot_path = os.path.join(FIGURES_DIR, "fig6_ablation_results.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved Figure 6 to {plot_path}")


def plot_concurrency_scalability():
    csv_path = os.path.join(RESULTS_DIR, "scalability_concurrency_results.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    fig, ax1 = plt.subplots(figsize=(7, 4), dpi=300)

    color = "#2980b9"
    ax1.set_xlabel("Concurrent User Requests", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Throughput (QPS)", color=color, fontsize=10, fontweight="bold")
    line1 = ax1.plot(df["concurrent_requests"], df["throughput_qps"], color=color, marker="o", linewidth=2.5, label="Throughput (QPS)")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()
    color = "#e67e22"
    ax2.set_ylabel("Mean Latency per Request (ms)", color=color, fontsize=10, fontweight="bold")
    line2 = ax2.plot(df["concurrent_requests"], df["mean_latency_ms"], color=color, marker="s", linestyle="--", linewidth=2.5, label="Mean Latency (ms)")
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title("Figure 7: System Scalability & QPS Throughput Under Concurrent Workload", fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    plot_path = os.path.join(FIGURES_DIR, "fig7_concurrency_scalability.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved Figure 7 to {plot_path}")


def plot_weather_scenarios():
    csv_path = os.path.join(RESULTS_DIR, "weather_scenarios_results.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(7, 4), dpi=300)
    bars = ax.bar(df["scenario"], df["utility_score"], color=["#f1c40f", "#3498db", "#2980b9", "#8e44ad"], alpha=0.85)

    ax.set_ylabel("Journey Utility Score (0 - 100)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 8: Impact of Controlled Synthetic Weather Scenarios on Recommendation", fontsize=11, fontweight="bold", pad=12)
    ax.set_ylim(0, 100)
    ax.grid(axis="y")

    for bar, mode in zip(bars, df["top_mode"]):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1.5, f"{height:.1f}\n({mode.upper()})", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    plot_path = os.path.join(FIGURES_DIR, "fig8_weather_scenarios.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved Figure 8 to {plot_path}")


if __name__ == "__main__":
    plot_corridor_warm_latency()
    plot_ablation_study()
    plot_concurrency_scalability()
    plot_weather_scenarios()
