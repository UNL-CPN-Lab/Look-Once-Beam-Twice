import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set global bold and large font sizes (only valid rcParams!)
plt.rcParams.update({
    'font.size': 16,
    'font.weight': 'bold',
    'axes.titlesize': 30,
    'axes.titleweight': 'bold',
    'axes.labelsize': 38,
    'axes.labelweight': 'bold',
    'xtick.labelsize': 34,
    'ytick.labelsize': 34,
    'legend.fontsize': 24,
    'legend.title_fontsize': 26,
})

# Base directory and file name
base_dir = "Adaptive_Beamforming_SC"
folder_prefix = "optimized_exhaustive_sweep_sc_jun26_gain8db_3m_MAVG"
csv_filename = "forward_max_snr_per_angle.csv"

# Start figure
fig, ax = plt.subplots(figsize=(20, 10))

# Loop through each experiment and plot its CDF
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

    snr_values = df['SNR (dB)'].dropna().values
    if len(snr_values) == 0:
        print(f"[Empty] No valid SNR in {path}")
        continue

    # Compute CDF
    snr_sorted = np.sort(snr_values)
    cdf = np.arange(1, len(snr_sorted) + 1) / len(snr_sorted)

    # Print mean CDF value
    mean_cdf = np.mean(cdf)
    print(f"Exp {i}: Mean CDF value = {mean_cdf:.4f}")

    # Plot with thick line
    ax.plot(snr_sorted, cdf, label=f"Exp {i}", linewidth=3)

# Finalize plot
ax.set_title("CDF of SNR (dB) for Each Experiment", weight='bold')
ax.set_xlabel("SNR (dB)", weight='bold')
ax.set_ylabel("CDF", weight='bold')
ax.grid(True)
ax.set_xlim(right=50)
ax.legend(loc="lower right")

# Make tick labels bold
ax.tick_params(axis='both', which='major', labelsize=34)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_weight('bold')

plt.tight_layout()

# Save
output_file = "snr_cdf_by_experiment.png"
plt.savefig(output_file, dpi=300)
print(f"\nPlot saved as: {output_file}")
