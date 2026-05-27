import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker

# === Matplotlib Config (Non-LaTeX, Bold) ===
plt.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'text.usetex': False,
    'font.size': 28,
    'mathtext.fontset': 'dejavusans',
    'font.family': 'DejaVu Sans'
})

# ========== CONFIG ==========
PROJECT_ROOT = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/optimized"
experiment_names = [
    "sc_jul23_gain8db_3m_QT_OAKD_MAVG13",  # Q = 0.95
    "sc_jul23_gain8db_3m_QT_OAKD_MAVG8",   # Q = 0.90
    "sc_jul23_gain8db_3m_QT_OAKD_MAVG3"    # Q = 0.80
]
# snr_quantiles = ["Q₀.₈₀", "Q₀.₉₀", "Q₀.₉₅"]
snr_quantiles = ["Q₀.₉₅", "Q₀.₉₀", "Q₀.₈₀"]  # reversed order for legend

project_dir = os.path.join(PROJECT_ROOT, "indoor", "continuous", "automatic_indoor_evaluations_mavg", "Adaptive_Beamforming_SC")

# ========== COLORS ==========
threshold_colors = ["#b7ce63", "#4ea5ff", "#f8ad9d"]  # pastel thresholds
base_colors = ["#29bf12", "#072ac8", "#f08080"]       # protocol colors

linewidth = 6
marker_size = 9
marker_styles = ["o", "s", "D"]
label_suffixes = ["(Q₀.₉₅)", "(Q₀.₉₀)",  "(Q₀.₈₀)"]

# ========== PLOT ==========
plt.figure(figsize=(14, 8))
sns.set_context("notebook", font_scale=2.0)

for idx, exp_name in enumerate(experiment_names):

    # if idx == 2:
    #     continue
    exp_path = os.path.join(project_dir, exp_name)
    meta_path = os.path.join(exp_path, "metadata.json")
    results_csv = os.path.join(exp_path, f"results_{exp_name}.csv")

    # Load metadata
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    threshold_value = float(str(meta.get("Threshold", "nan")).replace("dB", "").strip())

    # Load results
    adaptive_df = pd.read_csv(results_csv)
   
    # Load results
    adaptive_df = pd.read_csv(results_csv)

    # === Crop data to boresight range [-45, 40] ===
    adaptive_df = adaptive_df[(adaptive_df["Boresight"] >= -45) & (adaptive_df["Boresight"] <= 40)].copy()

    # === Replace SNR (dB) with 7 dB when NO_RADIO is detected ===
    adaptive_df["SNR_Used"] = adaptive_df.apply(
        lambda row: 7.0 if row["Jetson Detection"] == "NO_RADIO" else row["SNR (dB)"],
        axis=1
    )

    # === Outage Probability Calculation ===
    outage_events = (adaptive_df["SNR_Used"] < threshold_value)
    total_count = len(adaptive_df)
    outage_prob = outage_events.sum() / total_count if total_count > 0 else np.nan
    print(f"{exp_name}: Threshold = {threshold_value} dB | Outage Probability (NO_RADIO=7 dB, cropped) = {outage_prob:.3f}")

    # === Set zorders per experiment ===
    snr_zorder = 1 if idx == 2 else 2  # pink line lower, others higher

    # === Plot SNR lines ===
    sns.lineplot(
        data=adaptive_df, x="Boresight", y="SNR_Used",
        marker=marker_styles[idx],
        markersize=marker_size,
        linewidth=linewidth,
        markeredgecolor='none',
        label=f"VIBE-MA{label_suffixes[idx]}",
        color=base_colors[idx],
        ci=None,
        zorder=snr_zorder
    )

    # === Plot threshold lines (always bottom) ===
    plt.axhline(
        y=threshold_value,
        color=threshold_colors[idx],
        linestyle='--',
        linewidth=linewidth,
        label=f"SNR Th. {snr_quantiles[idx]}",
        zorder=0
    )

    # # === Plot Using SNR_Used ===
    # sns.lineplot(
    #     data=adaptive_df, x="Boresight", y="SNR_Used",
    #     marker=marker_styles[idx],
    #     markersize=marker_size,
    #     linewidth=linewidth,
    #     markeredgecolor='none',
    #     label= f"VIBE-MA{label_suffixes[idx]}",
    #     # label="VIBE-YOLOR" if idx == 2 else f"VIBE-MA{label_suffixes[idx]}",
    #     color=base_colors[idx],
    #     ci=None,
    #     zorder=2
    # )




    # # if idx != 2:
    # plt.axhline(
    #     y=threshold_value,
    #     color=threshold_colors[idx],
    #     linestyle='--',
    #     linewidth=linewidth,
    #     label=f"SNR Th. {snr_quantiles[idx]}",
    #     zorder=1
    # )


   


# ========== AXIS ==========
ax = plt.gca()
plt.xticks(rotation=45, fontsize=32)
plt.yticks(fontsize=32)
ax.set_yticks(np.arange(6, 30, 4))
ax.xaxis.set_major_locator(ticker.MultipleLocator(15))
ax.set_ylabel("SNR (dB)", fontsize=32)
ax.set_xlabel("Boresight Angle (°)", fontsize=32)
plt.xlim(-50, 50)
plt.ylim(6, 30)
plt.grid(False)

ax = plt.gca()
handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles, labels,
    loc='upper right',
    bbox_to_anchor=(1.02, 1.0),  
    framealpha=0,
    ncol=3,
    columnspacing=0.5,
    handletextpad=0.3,
    prop={'size': 28}
)

# ========== SAVE ==========
plt.tight_layout()
for fmt in ["png", "svg", "pdf"]:
    plt.savefig(os.path.join(PROJECT_ROOT, f"mode3_oakd.{fmt}"), format=fmt, dpi=600, bbox_inches="tight")

print("Multi-experiment Mode 3 plot saved with thresholds in first column and protocols in second column.")
