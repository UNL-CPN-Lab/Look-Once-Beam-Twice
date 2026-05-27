import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Global font styling
plt.rcParams.update({
    'font.size': 14,
    'font.weight': 'bold',
    'axes.titlesize': 24,
    'axes.labelsize': 24,
    'axes.labelweight': 'bold',
    'legend.fontsize': 16,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
})

# Setup
base_dir = "Adaptive_Beamforming_SC"
folder_prefix = "optimized_exhaustive_sweep_sc_jun26_gain8db_3m_MAVG"
csv_filename = "forward_all_snr_data.csv"

all_snr = []
labels = []

# CDF plot
fig_cdf, ax_cdf = plt.subplots(figsize=(20, 10))

# Loop through experiments
for i in range(1, 16):
    folder = f"{folder_prefix}{i}"
    path = os.path.join(base_dir, folder, csv_filename)

    if not os.path.isfile(path):
        print(f"[Missing] {path}")
        continue

    df = pd.read_csv(path)

    if 'SNR (dB)' not in df.columns:
        print(f"[Warning] 'SNR (dB)' not found in {path}")
        continue

    # snr_values = df['SNR (dB)'].dropna().astype(float).values
    # Strip and coerce to numeric, forcing errors to NaN, then drop them
    df['SNR (dB)'] = pd.to_numeric(df['SNR (dB)'], errors='coerce')
    snr_values = df['SNR (dB)'].dropna().values


    if len(snr_values) == 0:
        print(f"[Empty] No valid SNR in {path}")
        continue

    all_snr.append(snr_values.tolist())  # convert to list of floats

    labels.append(f"Exp {i}")

    # Plot CDF
    snr_sorted = np.sort(snr_values)
    cdf = np.arange(1, len(snr_sorted) + 1) / len(snr_sorted)
    ax_cdf.plot(snr_sorted, cdf, label=f"Exp {i}", linewidth=2.5)

# Finalize CDF plot
ax_cdf.set_title("CDF of All SNR (dB) Values Across Experiments", weight='bold')
ax_cdf.set_xlabel("SNR (dB)", weight='bold')
ax_cdf.set_ylabel("CDF", weight='bold')
ax_cdf.grid(True)
ax_cdf.set_xlim(right=50)
ax_cdf.legend(loc="lower right")
for label in ax_cdf.get_xticklabels() + ax_cdf.get_yticklabels():
    label.set_weight('bold')
fig_cdf.tight_layout()
fig_cdf.savefig("full_snr_cdf.png", dpi=300)
print("\nSaved: full_snr_cdf.png")

# -----------------------------
# Boxplot of SNRs across experiments
# -----------------------------
fig_box, ax_box = plt.subplots(figsize=(20, 10))
ax_box.boxplot(all_snr, labels=labels, patch_artist=True, showfliers=True)
ax_box.set_title("Boxplot of All SNR (dB) Values Across Experiments", weight='bold')
ax_box.set_xlabel("Experiment", weight='bold')
ax_box.set_ylabel("SNR (dB)", weight='bold')
ax_box.grid(True)
for label in ax_box.get_xticklabels() + ax_box.get_yticklabels():
    label.set_weight('bold')
fig_box.tight_layout()
fig_box.savefig("full_snr_boxplot.png", dpi=300)
print("\nSaved: full_snr_boxplot.png")
