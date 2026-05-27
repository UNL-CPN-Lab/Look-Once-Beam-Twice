

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Experiment list
base_filenames = [
    "sc_jul13_gain9db_12db_16m_t1",
    "sc_jul13_gain9db_12db_16m_t2",
    "sc_jul13_gain9db_12db_16m_t3",
    "sc_jul13_gain9db_12db_16m_t4",
    "sc_jul13_gain9db_12db_16m_t5",

    "nh_jul14_gain9db_12db_16m_t2",
    "nh_jul14_gain9db_12db_16m_t3",
    "nh_jul14_gain9db_12db_16m_t4",
    "nh_jul14_gain9db_12db_16m_t5",
    "nh_jul14_gain9db_12db_16m_t6",

    "nh_jul14_gain9db_12db_16m_t11",
    "nh_jul14_gain9db_12db_16m_t12",
    "nh_jul14_gain9db_12db_16m_t13",
    "nh_jul14_gain9db_12db_16m_t14",
    "nh_jul14_gain9db_12db_16m_t15"
]

# Corresponding threshold labels
labels = [
    "VIBE + MA for 11dB SNR Th.",
    "VIBE + MA for 14dB SNR Th.",
    "VIBE + MA for 17dB SNR Th.",
    "VIBE + MA for 20dB SNR Th.",
    "VIBE + MA for 23dB SNR Th.",

    "VIBE + MA for 11dB SNR Th.",
    "VIBE + MA for 14dB SNR Th.",
    "VIBE + MA for 17dB SNR Th.",
    "VIBE + MA for 20dB SNR Th.",
    "VIBE + MA for 23dB SNR Th.",

    "VIBE + MA for 11dB SNR Th.",
    "VIBE + MA for 14dB SNR Th.",
    "VIBE + MA for 17dB SNR Th.",
    "VIBE + MA for 20dB SNR Th.",
    "VIBE + MA for 23dB SNR Th."
]

# Flipped color palettes
green_palette = ["#bfd200", "#aacc00", "#80b918", "#55a630", "#2b9348", "#007f5f"]

pink_red_palette = ["#ff85a1", "#ff7096", "#ff5c8a", "#ff477e", "#ff0a54"]
blue_palette = ["#a2c2e0", "#6fa3d9", "#3b84d1", "#1f66c9", "#0048c0"]
cdf_colors = green_palette + pink_red_palette+ blue_palette

# Marker styles
markers = ['o', 's', 'D', '^', 'v', 'X', 'P', '*', '<', '>']

# Base folder
base_path = "mavg_Results"

# Setup plot
plt.figure(figsize=(12, 8))

# Containers to group by threshold label
grouped_labels = {
    "VIBE + MA for 11dB SNR Th.": [],
    "VIBE + MA for 14dB SNR Th.": [],
    "VIBE + MA for 17dB SNR Th.": [],
    "VIBE + MA for 20dB SNR Th.": [],
    "VIBE + MA for 23dB SNR Th.": []
}

# Loop through each experiment
for i, base_filename in enumerate(base_filenames):
    experiment_folder = os.path.join(base_path, base_filename)
    csv_filename = f"results_{base_filename}.csv"
    csv_path = os.path.join(experiment_folder, csv_filename)
    metadata_path = os.path.join(experiment_folder, "metadata.json")

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

    sorted_snr = np.sort(snr_values)
    cdf = np.arange(1, len(sorted_snr) + 1) / len(sorted_snr)

    # Load threshold
    threshold = None
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            threshold = metadata.get("Threshold", None)
            if threshold is not None:
                try:
                    threshold = float(str(threshold).lower().replace('db', '').strip())
                except ValueError:
                    print(f"[WARNING] Threshold '{threshold}' in {metadata_path} is not a valid number.")
                    threshold = None

    # Plot line
    cdf_color = cdf_colors[i % len(cdf_colors)]
    marker = markers[i % len(markers)]
    label = labels[i]

    line, = plt.plot(
        sorted_snr, cdf,
        label=label,  # grouped manually later
        linewidth=3,
        marker=marker,
        color=cdf_color,
        markevery=max(1, len(sorted_snr) // 20),
        markersize=6
    )

    grouped_labels[label].append(line)

    # Threshold line (if within range)
    if threshold is not None:
        if sorted_snr.min() <= threshold <= sorted_snr.max():
            plt.axvline(x=threshold, linestyle='--', color='black', linewidth=2, alpha=0.8, ymin=0.02, ymax=0.98)
        else:
            print(f"[NOTE] Threshold {threshold} dB for {base_filename} is outside data range "
                  f"({sorted_snr.min():.2f} dB to {sorted_snr.max():.2f} dB)")

# # Build legend
# custom_legend_lines = []
# custom_legend_labels = []

# # Add one line per SNR group
# for label, lines in grouped_labels.items():
#     if lines:
#         custom_legend_lines.append(lines[0])
#         custom_legend_labels.append(label)

# # Add speed group colors
# custom_legend_lines += [
#     Line2D([0], [0], color=green_palette[0], lw=3),
#     Line2D([0], [0], color=pink_red_palette[0], lw=3),
#     Line2D([0], [0], color=blue_palette[0], lw=3)
# ]
# custom_legend_labels += ["1 mph Trials", "5 mph Trials", "8 mph Trials"]


# Build legend
custom_legend_lines = []
custom_legend_labels = []

# Add one hollow marker per SNR group (no color line)
for label, lines in grouped_labels.items():
    if lines:
        marker = lines[0].get_marker()
        custom_legend_lines.append(Line2D(
            [0], [0],
            marker=marker,
            color='black',
            markerfacecolor='white',
            markeredgewidth=1.5,
            markersize=8,
            linestyle='None'
        ))
        custom_legend_labels.append(label)

# Add speed group color lines
custom_legend_lines += [
    Line2D([0], [0], color=green_palette[3], lw=3),
    Line2D([0], [0], color=pink_red_palette[3], lw=3),
    Line2D([0], [0], color=blue_palette[3], lw=3)
]
custom_legend_labels += ["1 mph Trials", "5 mph Trials", "8 mph Trials"]





# Final plot formatting
plt.xlabel("SNR (dB)", fontsize=16, fontweight='bold')
plt.ylabel("CDF", fontsize=16, fontweight='bold')
# plt.title("CDF of SNR (dB) Across Multiple Experiments", fontsize=18, fontweight='bold')

plt.xticks(np.arange(5, 40, 5), fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
plt.grid(True)
plt.legend(custom_legend_lines, custom_legend_labels, fontsize=10, loc='lower right', ncol=2)
plt.tight_layout()

# Save
output_base = "combined_snr_cdf_grouped_speed_legend"
plt.savefig(f"{output_base}.png")
plt.savefig(f"{output_base}.svg")
plt.savefig(f"{output_base}.eps")

# plt.show()
