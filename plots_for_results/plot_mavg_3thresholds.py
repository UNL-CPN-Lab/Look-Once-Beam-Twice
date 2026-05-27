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
    "sc_jul21_gain8db_3m_QT_MAVG13",  # Q = 0.95
    "sc_jul21_gain8db_3m_QT_MAVG8",   # Q = 0.90
    "sc_jul21_gain8db_3m_QT_MAVG3"    # Q = 0.80
]
# snr_quantiles = ["Q₀.₈₀", "Q₀.₉₀", "Q₀.₉₅"]
snr_quantiles = ["Q₀.₉₅", "Q₀.₉₀", "Q₀.₈₀"]  # reversed order for legend

project_dir = os.path.join(PROJECT_ROOT, "indoor", "continuous", "automatic_indoor_evaluations_mavg", "Adaptive_Beamforming_SC")

# ========== COLORS ==========
threshold_colors = ["#b7ce63", "#4ea5ff", "#ff8fab"]  # pastel thresholds
base_colors = ["#29bf12", "#072ac8", "#ff006e"]       # protocol colors

linewidth = 6
marker_size = 9
marker_styles = ["o", "s", "D"]
label_suffixes = ["(Q₀.₉₅)", "(Q₀.₉₀)", " "]

# ========== PLOT ==========
plt.figure(figsize=(14, 8))
sns.set_context("notebook", font_scale=2.0)

for idx, exp_name in enumerate(experiment_names):
    exp_path = os.path.join(project_dir, exp_name)
    meta_path = os.path.join(exp_path, "metadata.json")
    results_csv = os.path.join(exp_path, f"results_{exp_name}.csv")

    # Load metadata
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    threshold_value = float(str(meta.get("Threshold", "nan")).replace("dB", "").strip())

    # Load results
    adaptive_df = pd.read_csv(results_csv)
    # adaptive_df = adaptive_df[adaptive_df["Jetson Detection"] != "NO_RADIO"].copy()
    # adaptive_df = adaptive_df[(adaptive_df["Boresight"] >= -45) & (adaptive_df["Boresight"] <= 45)]

    # Threshold lines (only for first two experiments)

    # === Calculate outage probability ===
    # snr_values = adaptive_df["SNR (dB)"].dropna()
    # outage_count = (snr_values < threshold_value).sum()
    # total_count = len(snr_values)
    # outage_prob = outage_count / total_count if total_count > 0 else np.nan

    # print(f"{exp_name}: Threshold = {threshold_value} dB | Outage Probability = {outage_prob:.3f}")

    # === Replace SNR (dB) with Initial SNR where NO_RADIO is detected ===
    # if "Initial SNR" in adaptive_df.columns:
    #     adaptive_df["SNR_Used"] = adaptive_df.apply(
    #         lambda row: row["Initial SNR"] if row["Jetson Detection"] == "NO_RADIO" else row["SNR (dB)"],
    #         axis=1
    #     )
    # else:
    #     # Fallback to original SNR column if Initial SNR does not exist
    #     adaptive_df["SNR_Used"] = adaptive_df["SNR (dB)"]

    # === Replace SNR (dB) with 7 dB when NO_RADIO is detected ===
    # adaptive_df["SNR_Used"] = adaptive_df.apply(
    #     lambda row: 7.0 if row["Jetson Detection"] == "NO_RADIO" else row["SNR (dB)"],
    #     axis=1
    # )



    # outage_events = (adaptive_df["SNR_Used"] < threshold_value)
    # total_count = len(adaptive_df)
    # outage_prob = outage_events.sum() / total_count if total_count > 0 else np.nan
    # print(f"{exp_name}: Threshold = {threshold_value} dB | Outage Probability (NO_RADIO = 7 dB) = {outage_prob:.3f}")


    
    # # Protocol curves
    # sns.lineplot(
    #     data=adaptive_df, x="Boresight", y="SNR (dB)",
    #     marker=marker_styles[idx],
    #     markersize=marker_size,
    #     linewidth=linewidth,
    #     markeredgecolor='none',
    #     label="VIBE-YOLOR" if idx == 2 else f"VIBE-MA{label_suffixes[idx]}",
    #     color=base_colors[idx],
    #     ci=None,
    #     zorder=2
    # )
#     sns.lineplot(
#     data=adaptive_df, x="Boresight", y="SNR_Used",
#     marker=marker_styles[idx],
#     markersize=marker_size,
#     linewidth=linewidth,
#     markeredgecolor='none',
#     label="VIBE-YOLOR" if idx == 2 else f"VIBE-MA{label_suffixes[idx]}",
#     color=base_colors[idx],
#     ci=None,
#     zorder=2
# )
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

    # === Plot Using SNR_Used ===
    sns.lineplot(
        data=adaptive_df, x="Boresight", y="SNR_Used",
        marker=marker_styles[idx],
        markersize=marker_size,
        linewidth=linewidth,
        markeredgecolor='none',
        label="VIBE-YOLOR" if idx == 2 else f"VIBE-MA{label_suffixes[idx]}",
        color=base_colors[idx],
        ci=None,
        zorder=2
    )




    if idx != 2:
        plt.axhline(
            y=threshold_value,
            color=threshold_colors[idx],
            linestyle='--',
            linewidth=linewidth,
            label=f"SNR Th. {snr_quantiles[idx]}",
            zorder=1
        )


# ========== AXIS ==========
ax = plt.gca()
plt.xticks(rotation=45, fontsize=32)
plt.yticks(fontsize=32)
ax.set_yticks(np.arange(17, 22, 1))
ax.xaxis.set_major_locator(ticker.MultipleLocator(15))
ax.set_ylabel("SNR (dB)", fontsize=32)
ax.set_xlabel("Boresight Angle (°)", fontsize=32)
plt.xlim(-45, 45)
plt.ylim(17, 21.5)
plt.grid(False)

ax = plt.gca()
handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles, labels,
    loc='upper right',
    framealpha=0,
    ncol=3,             #  just 2 columns
    columnspacing=0.5,
    handletextpad=0.3,
    prop={'size': 28}
)

# ========== SAVE ==========
plt.tight_layout()
for fmt in ["png", "svg", "pdf"]:
    plt.savefig(os.path.join(PROJECT_ROOT, f"mode3.{fmt}"), format=fmt, dpi=600, bbox_inches="tight")

print("Multi-experiment Mode 3 plot saved with thresholds in first column and protocols in second column.")
