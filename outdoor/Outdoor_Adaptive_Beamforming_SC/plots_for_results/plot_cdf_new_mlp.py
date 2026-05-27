import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

# === Selected MLP Experiments (only 3) ===
base_filenames = [
    "nh_jul14_gain9db_12db_16m_t1",   # 5 mph - 11 dB
    "nh_jul14_gain9db_12db_16m_t1",   # 5 mph - 17 dB
    "nh_jul14_gain9db_12db_16m_t1"    # 5 mph - 23 dB
]

labels = [
    "VIBE-MLP: At 5 mph - 11 dB Th.",
    "VIBE-MLP: At 5 mph - 17 dB Th.",
    "VIBE-MLP: At 5 mph - 23 dB Th."
]

# Colors & markers
cdf_colors = ["#ff0a54", "#1f66c9", "#2b9348"]
markers = ['o', 's', 'D']
hardcoded_thresholds = [11, 17, 23]

base_path = "mlp_Results"

# === Plot ===
plt.figure(figsize=(10, 10))

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

    # === Compute CDF of (threshold - SNR) ===
    snr_diff = threshold - snr_values
    sorted_diff = np.sort(snr_diff)
    cdf = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff)

    # === Print data for later analysis ===
    # print(f"\n=== Data for {labels[i]} ===")
    # print(pd.DataFrame({"Margin_from_Threshold_dB": sorted_diff, "CDF": cdf}).head(10))  # first 10 rows
    # print(f"Total Points: {len(sorted_diff)}\n")

    # === Interpolate to find CDF where Margin_from_Threshold_dB = 0 ===
    if np.any(sorted_diff < 0) and np.any(sorted_diff > 0):
        cdf_at_zero = np.interp(0, sorted_diff, cdf)   # linear interpolation
        print(f"--> CDF at x=0 for {labels[i]}: {cdf_at_zero:.3f} ({cdf_at_zero*100:.1f}%)")
    else:
        print(f"--> x=0 is outside the data range for {labels[i]}")

    # === Plot ===
    plt.plot(sorted_diff, cdf,
             linewidth=6,
             marker=markers[i],
             color=cdf_colors[i],
             label=labels[i],
             markevery=max(1, len(sorted_diff) // 20),
             markersize=14)

# === Axis Labels (No LaTeX) ===
# plt.xlabel("Margin from Threshold (dB)", fontsize=72)
# plt.ylabel("CDF", fontsize=42)

# === X/Y ticks and limits ===
plt.xlim(-25, 25)
plt.xticks([-20, 0, 20], fontsize=52)


ax = plt.gca()
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.3))
# plt.yticks([])

# Keep y-tick positions but hide their labels
ax.set_yticklabels([])

# Hide tick marks but keep grid lines
ax.tick_params(left=False)

# === Dashed Grid ===
plt.grid(True, linestyle='--', linewidth=1.5, alpha=0.6)

# === Add vertical gray line at x = 0 ===
ax.axvline(x=0, color="gray", linestyle="--", linewidth=4, alpha=0.9, zorder=5)


# === Legend without LaTeX ===
# plt.legend(fontsize=22, frameon=False, loc="lower right")

# === Save Figures ===
output_base = "cdf_mlp_cleaned"
for ext in ["png", "svg", "pdf"]:
    plt.savefig(f"{output_base}.{ext}", bbox_inches='tight')
