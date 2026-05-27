import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.ticker import MaxNLocator

# === Matplotlib Config ===
plt.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'text.usetex': False,
    'font.size': 28,
    'mathtext.fontset': 'dejavusans',
    'font.family': 'DejaVu Sans'
})


# === File Paths and Labels ===
experiment_folder = "mavg_Results"
base_filename = "sc_jul13_gain9db_12db_16m"

thresholds_info = {
    "t7": (11, (0.75, 0.6, 0.85)),  # pastel_purple
    "t8": (14, (0.6, 0.75, 0.95)),  # pastel_blue
    "t9": (17, (0.6, 0.8, 0.6)),    # pastel_green
    "t10": (20, (1.0, 0.75, 0.5)),   # pastel_orange
    "t11": (23, (1.0, 0.5, 0.5))     # pastel_red
}
# Construct CSV paths
csv_files = {
    t: os.path.join(experiment_folder, f"{base_filename}_{t}", f"results_{base_filename}_{t}.csv")
    for t in thresholds_info
}

# === Initialize Lists ===
beamforming_times = []
beams_checked = []
threshold_labels = []

# === Load and Process Clean Data ===
for label, file_path in csv_files.items():
    threshold_db, _ = thresholds_info[label]
    df = pd.read_csv(file_path)

    # Drop invalid rows
    df = df.dropna(subset=["YOLO Time (s)", "Beam Sweep Time (s)", "Beams Checked in Search"])
    df = df[
        (df["YOLO Time (s)"] >= 0) &
        (df["Beam Sweep Time (s)"] >= 0) &
        (df["Beams Checked in Search"] >= 0)
    ]

    # Compute total time
    total_time_sec = df["YOLO Time (s)"] + df["Beam Sweep Time (s)"]

    beamforming_times.extend(total_time_sec.tolist())
    beams_checked.extend(df["Beams Checked in Search"].tolist())
    # threshold_labels.extend([f"{threshold_db} dB"] * len(df))
    threshold_labels.extend([f"{threshold_db}"] * len(df))

# === Create DataFrame ===
data = pd.DataFrame({
    "Threshold (dB)": threshold_labels,
    "Beamforming Time (s)": beamforming_times,
    "Beams Checked": beams_checked
})

# === Color and order ===
# threshold_order = [f"{info[0]} dB" for info in thresholds_info.values()]

threshold_order = [str(info[0]) for info in thresholds_info.values()]

custom_palette = [info[1] for info in thresholds_info.values()]
palette_dict = dict(zip(threshold_order, custom_palette))

# === Output file base names ===
# bf_plot_base = os.path.join(experiment_folder, "beamforming_time_without_guard_1mph")
beams_plot_base = os.path.join(experiment_folder, "beams_checked_without_guard")

# === Violin Plot: Beamforming Time ===
# plt.figure(figsize=(8, 6))
# sns.violinplot(
#     x="Threshold (dB)", y="Beamforming Time (s)",
#     data=data, order=threshold_order, palette=palette_dict, cut=0
# )
# plt.title("Beamforming Time per Threshold with Guard", fontsize=16, fontweight="bold")
# plt.xlabel("Threshold (dB)", fontsize=14, fontweight="bold")
# plt.ylabel("Beamforming Time (s)", fontsize=14, fontweight="bold")
# plt.xticks(fontsize=12, fontweight="bold")
# plt.yticks(fontsize=12, fontweight="bold")
# plt.ylim(0, 12)
# plt.grid(True)
# plt.tight_layout()
# for ext in ['png', 'svg', 'eps']:
#     plt.savefig(f"{bf_plot_base}.{ext}", format=ext, dpi=300)
# plt.close()

# === Calculate aggregated statistics for beamforming time and beams checked ===
stats_summary = data.groupby("Threshold (dB)").agg(
    avg_beamforming_time=("Beamforming Time (s)", "mean"),
    std_beamforming_time=("Beamforming Time (s)", "std"),
    avg_beams_checked=("Beams Checked", "mean"),
    std_beams_checked=("Beams Checked", "std"),
    count=("Beamforming Time (s)", "count")
).reset_index()

# === Print the summary for quick view ===
print("\n=== Beamforming Statistics Per Threshold ===")
print(stats_summary.to_string(index=False))

# === Violin Plot: Beams Checked ===
plt.figure(figsize=(8, 6))
sns.violinplot(
    x="Threshold (dB)", y="Beams Checked",
    data=data, order=threshold_order, palette=palette_dict, cut=0
)
# plt.title("Beams Checked per Threshold without Guard", fontsize=16, fontweight="bold")
plt.xlabel("", fontsize=28)
plt.ylabel("Beams Checked", fontsize=28)
plt.xticks(fontsize=28)
plt.yticks(fontsize=28)
plt.ylim(0, 64)
plt.grid(axis='both', linestyle='--', alpha=0.5)  # dashed grid for both x and y
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(f"{beams_plot_base}.{ext}", format=ext, dpi=600)
plt.close()

# box plot beams checked
# plt.figure(figsize=(12, 6))
# sns.boxplot(
#     x="Threshold (dB)", y="Beams Checked",
#     data=data, order=threshold_order, palette=palette_dict
# )

# === Use Boxenplot for better distribution visibility ===
# sns.boxenplot(
#     x="Threshold (dB)", y="Beams Checked",
#     data=data,
#     order=threshold_order,
#     palette=palette_dict,
#     linewidth=2,
#     k_depth='full'
# )

# # Add stripplot overlay to show all data points
# sns.stripplot(
#     x="Threshold (dB)",
#     y="Beams Checked",
#     data=data,
#     order=threshold_order,
#     color='black',
#     size=5,
#     jitter=True,
#     alpha=0.6
# )
# plt.title("Beams Checked per Threshold with Guards", fontsize=16, fontweight="bold")
# plt.xlabel("SNR Threshold (dB)", fontsize=22, fontweight="bold")
# plt.ylabel("Beams Checked", fontsize=22, fontweight="bold")
# plt.xticks(fontsize=22, fontweight="bold")
# plt.yticks(fontsize=22, fontweight="bold")
# plt.ylim(0, 64)
# plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
# plt.grid(True)
# plt.tight_layout()
# for ext in ['png', 'svg', 'eps', 'pdf']:
#     plt.savefig(f"{beams_plot_base}.{ext}", format=ext, dpi=600)
# plt.close()
