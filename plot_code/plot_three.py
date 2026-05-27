import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
from matplotlib.colors import to_rgba
from configurations.utils import snr_percent_db

# ========== CONFIG ==========
PROJECT_ROOT = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/optimized"
experiment_names = ["sc_jun30_gain8db_3m_QT_MAVG13", "sc_jun30_gain8db_3m_QT_MAVG8", "sc_jun30_gain8db_3m_QT_MAVG3"]
snr_quantiles = [r"$\mathbf{Q_{0.95}}$", r"$\mathbf{Q_{0.90}}$", r"$\mathbf{Q_{0.80}}$"]

project_dir = os.path.join(PROJECT_ROOT, "indoor", "continuous", "automatic_indoor_evaluations_mavg", "Adaptive_Beamforming_SC")

# Define pastel colors
pastel_green = (0.6, 0.8, 0.6)
pastel_blue = (0.6, 0.75, 0.95)
pastel_purple = (0.75, 0.6, 0.85)

# Function to darken a color
def darken_color(color, factor=0.8):
    return tuple(max(min(c * factor, 1.0), 0.0) for c in color)

# Create darker versions for plotting results
dark_green = darken_color(pastel_green)
dark_blue = darken_color(pastel_blue)
dark_purple = darken_color(pastel_purple)

# Use darker for results, pastel for threshold
base_colors = [dark_green, dark_blue, dark_purple]
threshold_colors = [pastel_green, pastel_blue, pastel_purple]

linewidth = 25
marker_size = 45
marker_styles = ["o", "s", "D"]
label_suffixes = ["(Exp 1)", "(Exp 2)", "(Exp 3)"]

# ========== PLOT SETUP ==========
plt.figure(figsize=(40, 30))
sns.set_context("notebook", font_scale=2.0)

for idx, exp_name in enumerate(experiment_names):
    exp_path = os.path.join(project_dir, exp_name)
    meta_path = os.path.join(exp_path, "metadata.json")
    results_csv = os.path.join(exp_path, f"results_{exp_name}.csv")

    # Load metadata
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    # snr_threshold_factor = float(meta.get("Threshold Factor", 0.6))
    # reference_max_snr = float(meta.get("reference_max_snr_db", 40.0))
    threshold_value = float(str(meta.get("Threshold", "nan")).replace("dB", "").strip())

    # Load results
    adaptive_df = pd.read_csv(results_csv)
    adaptive_df = adaptive_df[adaptive_df["Jetson Detection"] != "NO_RADIO"].copy()
    adaptive_df = adaptive_df[(adaptive_df["Boresight"] >= -35) & (adaptive_df["Boresight"] <= 35)]

    # Plot threshold line (pastel color) first (lower z-order)
    plt.axhline(
        y=threshold_value,
        color=threshold_colors[idx],
        linestyle='--',
        linewidth=linewidth,
        label=f"SNR Th : {snr_quantiles[idx]}",
        zorder=1
    )

    # Plot result line second (higher z-order)
    sns.lineplot(
        data=adaptive_df, x="Boresight", y="SNR (dB)",
        marker=marker_styles[idx],
        markersize=marker_size,
        linewidth=linewidth,
        markeredgecolor='none',
        label=f"YOLOR+M.Avg{label_suffixes[idx]}",
        color=base_colors[idx],
        errorbar=None, 
        zorder=2
    )



# ========== AXIS & SAVE ==========
plt.xlabel("Boresight Angle (°)", fontsize=75, fontweight='bold')
plt.ylabel("SNR (dB)", fontsize=75, fontweight='bold')
plt.xticks(rotation=45, fontsize=75, fontweight='bold')
plt.yticks(fontsize=75, fontweight='bold')
plt.xlim(-30, 30)
plt.ylim(33, 42)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(15))
plt.grid(True)
plt.legend(loc='upper right', prop={'weight': 'bold', 'size': 70}, frameon=True)
plt.tight_layout()

save_name = "_".join(experiment_names)
plt.savefig(os.path.join(PROJECT_ROOT, f"mode3_multi_{save_name}.png"), format="png")
plt.savefig(os.path.join(PROJECT_ROOT, f"mode3_multi_{save_name}.svg"), format="svg")
plt.savefig(os.path.join(PROJECT_ROOT, f"mode3_multi_{save_name}.eps"), format="eps")

print("Multi-experiment Mode 3 plot with pastel threshold lines saved.")
