import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---- Font setup ----
plt.rcParams.update({
    'font.size': 14,
    'font.weight': 'bold',
    'axes.titlesize': 24,
    'axes.labelsize': 24,
    'axes.labelweight': 'bold',
    'legend.fontsize': 18,
    'xtick.labelsize': 22,
    'ytick.labelsize': 22,
})

# ---- SNR Threshold Conversion Function ----
def snr_percent_db(percentage, max_snr_db):
    if percentage <= 0 or percentage > 1:
        raise ValueError("Percentage must be between 0 and 1 (exclusive of 0).")
    return max_snr_db + 10 * np.log10(percentage)

# ---- Setup ----
base_dir = "Adaptive_Beamforming_SC"
folder_prefix = "optimized_exhaustive_sweep_sc_jun26_gain8db_3m_MAVG"
csv_filename = "forward_all_snr_data.csv"

all_snr = []
labels = []
threshold_lines = {0.4: [], 0.6: [], 0.8: []}  # For storing threshold values per experiment

# ---- Start plot ----
fig_cdf, ax_cdf = plt.subplots(figsize=(20, 10))

# ---- Loop through experiments ----
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

    df['SNR (dB)'] = pd.to_numeric(df['SNR (dB)'], errors='coerce')
    snr_values = df['SNR (dB)'].dropna().values

    if len(snr_values) == 0:
        print(f"[Empty] No valid SNR in {path}")
        continue

    all_snr.append(snr_values.tolist())
    labels.append(f"Exp {i}")

    # Plot individual CDF
    snr_sorted = np.sort(snr_values)
    cdf = np.arange(1, len(snr_sorted) + 1) / len(snr_sorted)
    ax_cdf.plot(snr_sorted, cdf, label=f"Exp {i}", linewidth=2.5)

    # ---- Compute threshold SNRs based on max SNR ----
    max_snr_db = np.max(snr_values)
    for factor in [0.4, 0.6, 0.8]:
        th_db = snr_percent_db(factor, max_snr_db)
        threshold_lines[factor].append(th_db)

# ---- Global quantiles (for comparison) ----
all_snr_flat = np.concatenate(all_snr)
q70 = np.quantile(all_snr_flat, 0.70)
q80 = np.quantile(all_snr_flat, 0.80)
q90 = np.quantile(all_snr_flat, 0.90)
q95 = np.quantile(all_snr_flat, 0.95)
q99 = np.quantile(all_snr_flat, 0.99)

print(f"\nGlobal Quantile Thresholds (from full sweep data):")
print(f"  70th percentile SNR_th: {q70:.2f} dB")
print(f"  80th percentile SNR_th: {q80:.2f} dB")
print(f"  90th percentile SNR_th: {q90:.2f} dB")
print(f"  95th percentile SNR_th: {q95:.2f} dB")
print(f"  99th percentile SNR_th: {q99:.2f} dB")

# ---- Plot global quantiles ----
ax_cdf.axvline(q70, color='red', linestyle='--', linewidth=5, label='70th Percentile')
ax_cdf.axvline(q80, color='orange', linestyle='--', linewidth=5, label='80th Percentile')
ax_cdf.axvline(q90, color='green', linestyle='--', linewidth=5, label='90th Percentile')
ax_cdf.axvline(q95, color='green', linestyle='--', linewidth=5, label='95th Percentile')
ax_cdf.axvline(q99, color='green', linestyle='--', linewidth=5, label='99th Percentile')

# ---- Plot prior used SNR thresholds (mean across experiments) ----
for factor, color, label in zip([0.4, 0.6, 0.8], ['purple', 'blue', 'black'], ['40%', '60%', '80%']):
    mean_th = np.mean(threshold_lines[factor])
    ax_cdf.axvline(mean_th, color=color, linestyle=':', linewidth=5, label=f'{label} of Max SNR')

    print(f"Mean threshold at {label}: {mean_th:.2f} dB")

# ---- Finalize Plot ----
ax_cdf.set_title("CDF of All SNR (dB) with Prior Thresholds", weight='bold')
ax_cdf.set_xlabel("SNR (dB)", weight='bold')
ax_cdf.set_ylabel("CDF", weight='bold')
ax_cdf.grid(True)
ax_cdf.set_xlim(right=50)
ax_cdf.legend(loc="lower right")
for label in ax_cdf.get_xticklabels() + ax_cdf.get_yticklabels():
    label.set_weight('bold')
fig_cdf.tight_layout()
fig_cdf.savefig("full_snr_cdf_with_threshold_lines.png", dpi=300)

print("\nPlot saved as: full_snr_cdf_with_threshold_lines.png")
