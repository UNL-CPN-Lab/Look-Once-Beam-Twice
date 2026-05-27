
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'text.usetex': False,
    'font.size': 28,
    'mathtext.fontset': 'dejavusans',
    'font.family': 'DejaVu Sans'
})

# Experiment list
base_filenames = [
    "sc_jul24_gain9db_12db_16m_t1", "sc_jul24_gain9db_12db_16m_t1", "sc_jul24_gain9db_12db_16m_t1",
    "sc_jul24_gain9db_12db_16m_t1", "sc_jul24_gain9db_12db_16m_t1",
    "nh_jul14_gain9db_12db_16m_t1", "nh_jul14_gain9db_12db_16m_t1", "nh_jul14_gain9db_12db_16m_t1",
    "nh_jul14_gain9db_12db_16m_t1", "nh_jul14_gain9db_12db_16m_t1",
    "nh_jul14_gain9db_12db_16m_t2", "nh_jul14_gain9db_12db_16m_t2", "nh_jul14_gain9db_12db_16m_t2",
    "nh_jul14_gain9db_12db_16m_t2", "nh_jul14_gain9db_12db_16m_t2"
]

# Corresponding threshold labels
labels = [
    "VIBE-MLP:11dB SNR Th.", "VIBE-MLP:14dB SNR Th.", "VIBE-MLP:17dB SNR Th.",
    "VIBE-MLP:20dB SNR Th.", "VIBE-MLP:23dB SNR Th.",
    "VIBE-MLP:11dB SNR Th.", "VIBE-MLP:14dB SNR Th.", "VIBE-MLP:17dB SNR Th.",
    "VIBE-MLP:20dB SNR Th.", "VIBE-MLP:23dB SNR Th.",
    "VIBE-MLP:11dB SNR Th.", "VIBE-MLP:14dB SNR Th.", "VIBE-MLP:17dB SNR Th.",
    "VIBE-MLP:20dB SNR Th.", "VIBE-MLP:23dB SNR Th."
]


# Color palettes
green_palette = ["#bfd200", "#aacc00", "#80b918", "#55a630", "#2b9348", "#007f5f"]
pink_red_palette = ["#ff85a1", "#ff7096", "#ff5c8a", "#ff477e", "#ff0a54"]
blue_palette = ["#a2c2e0", "#6fa3d9", "#3b84d1", "#1f66c9", "#0048c0"]
cdf_colors =  pink_red_palette + blue_palette + green_palette

# Marker styles
markers = ['o', 's', 'D', '^', 'v', 'X', 'P', '*', '<', '>']

# Base folder
base_path = "mlp_Results"
plt.figure(figsize=(12, 8))

# Group for legend
grouped_labels = {
    "VIBE-MLP:11dB SNR Th.": [],
    "VIBE-MLP:14dB SNR Th.": [],
    "VIBE-MLP:17dB SNR Th.": [],
    "VIBE-MLP:20dB SNR Th.": [],
    "VIBE-MLP:23dB SNR Th.": []
}

# === Hardcoded thresholds ===
hardcoded_thresholds = [11, 14, 17, 20, 23] * 3  # Repeat 3 times for 15 trials

# Loop through experiments
for i, (base_filename, threshold) in enumerate(zip(base_filenames, hardcoded_thresholds)):
    experiment_folder = os.path.join(base_path, base_filename)
    csv_filename = f"results_{base_filename}.csv"
    csv_path = os.path.join(experiment_folder, csv_filename)

    if not os.path.exists(csv_path):
        print(f"[WARNING] CSV not found: {csv_path}")
        continue

    df = pd.read_csv(csv_path)
    if "SNR (dB)" not in df.columns:
        print(f"[WARNING] 'SNR (dB)' column missing in {csv_filename}")
        continue

    snr_values = df["SNR (dB)"].dropna().values

    if len(snr_values) == 0:
        print(f"[WARNING] No valid SNR values in {csv_filename}")
        continue

    # Subtract threshold
    snr_diff = threshold - snr_values
    sorted_diff = np.sort(snr_diff)
    cdf = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff)

    # Plot
    color = cdf_colors[i % len(cdf_colors)]
    marker = markers[i % len(markers)]
    label = labels[i]

    line, = plt.plot(
        sorted_diff, cdf,
        label=label,
        linewidth=5,
        marker=marker,
        color=color,
        markevery=max(1, len(sorted_diff) // 20),
        markersize=12
    )
    grouped_labels[label].append(line)

# === Legend setup ===
custom_legend_lines = []
custom_legend_labels = []

# === VIBE-MLP SNR Th. header using invisible marker for alignment
custom_legend_lines.append(Line2D(
    [0], [0],
    marker='o',  # Use same marker type for alignment
    color='white',  # Invisible
    markerfacecolor='white',
    markeredgecolor='white',
    linestyle='None'
))
custom_legend_labels.append("VIBE-MLP SNR Th.")

# === Thresholds with different markers
threshold_values = [11, 14, 17, 20, 23]
threshold_markers = ['o', 's', 'D', '^', 'v']  # circle, square, diamond, triangle_up, triangle_down

for th, mk in zip(threshold_values, threshold_markers):
    custom_legend_lines.append(Line2D(
        [0], [0],
        marker=mk,
        color='black',
        markerfacecolor='white',
        markeredgewidth=2,
        markersize=12,
        linewidth=8,
        linestyle='None'
    ))
    custom_legend_labels.append(f"{th} dB")

# === Trial Speed section
custom_legend_lines.append(Line2D(
    [0], [0],
    marker='o',  # Dummy again for alignment
    color='white',
    markerfacecolor='white',
    markeredgecolor='white',
    linestyle='None'
))
custom_legend_labels.append("Trial Speed")

custom_legend_lines += [
    Line2D([0], [0], color=pink_red_palette[3], lw=3),
    Line2D([0], [0], color=blue_palette[3], lw=3),
    Line2D([0], [0], color=green_palette[3], lw=3)
]
custom_legend_labels += ["1 mph", "5 mph", "8 mph"]

# === Apply legend
plt.legend(
    custom_legend_lines,
    custom_legend_labels,
    loc='upper left',
    ncol=1,
    prop={'size': 24, 'weight': 'bold'},
    framealpha=0,
    frameon=False
)
plt.xlabel("Margin from Threshold", fontsize=26, fontweight='bold')
plt.ylabel("CDF", fontsize=26, fontweight='bold')
plt.xticks(np.arange(-35, 35, 10), fontsize=26, fontweight='bold')
plt.yticks(fontsize=26, fontweight='bold')
# plt.grid(True)
plt.axvline(x=0, linestyle='--', color='grey', linewidth=4, alpha=0.8)



plt.tight_layout()

# Save
output_base = "combined_snr_minus_threshold_cdf_mlp"

plt.savefig(f"{output_base}.png", bbox_inches='tight')
plt.savefig(f"{output_base}.svg", bbox_inches='tight')
plt.savefig(f"{output_base}.eps", bbox_inches='tight')
plt.savefig(f"{output_base}.pdf", bbox_inches='tight')  # Tight PDF