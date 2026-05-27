import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# === Config ===
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
t1_name = "nh_may7_gain14db_3m_t1"  # MLP
t2_name = "nh_may7_gain14db_3m_t2"  # Moving Avg
snr_threshold = 14.39  # 50% of 17.4 dB

# === Load CSVs ===
t1_csv = os.path.join(exp_base_path, t1_name, "results_nh_may7_gain14db_3m_t1.csv")
t2_csv = os.path.join(exp_base_path, t2_name, "results_nh_may7_gain14db_3m_t2.csv")
t1 = pd.read_csv(t1_csv)
t2 = pd.read_csv(t2_csv)

# === Filter only rows where a radio was detected ===
t1 = t1[t1["Jetson Detection"].str.isnumeric()]
t2 = t2[t2["Jetson Detection"].str.isnumeric()]

t1 = t1[(t1["Boresight Angle"] >= -25) & (t1["Boresight Angle"] <= 30)]
t2 = t2[(t2["Boresight Angle"] >= -25) & (t2["Boresight Angle"] <= 30)]


# === Compute outage ===
# === Compute outage probability (corrected) ===
outage_t1 = (t1["SNR (dB)"] < snr_threshold).sum() / len(t1)
outage_t2 = (t2["SNR (dB)"] < snr_threshold).sum() / len(t2)

# === Compute beamforming time ===
t1["Beamforming Time"] = t1["Beam Sweep Time (s)"] * t1["Beams Checked in Search"]
t2["Beamforming Time"] = t2["Beam Sweep Time (s)"] * t2["Beams Checked in Search"]
avg_time_t1 = t1["Beamforming Time"].mean()
avg_time_t2 = t2["Beamforming Time"].mean()

# === Create box plots for Beams Checked and Offset Degrees ===
t1["Method"] = "MLP"
t2["Method"] = "Moving Avg"
combined = pd.concat([t1, t2], axis=0)

# === Plotting ===
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
colors = ['tab:orange', 'tab:cyan']

# 1. Outage Probability
axs[0, 0].bar(["MLP", "Moving Avg"], [outage_t1, outage_t2], color=colors)
axs[0, 0].set_title("Outage Probability")
axs[0, 0].set_ylabel("Probability")
axs[0, 0].grid(True)

# 2. Average Beamforming Time
axs[0, 1].bar(["MLP", "Moving Avg"], [avg_time_t1, avg_time_t2], color=colors)
axs[0, 1].set_title("Avg. Beamforming Time per Angle")
axs[0, 1].set_ylabel("Time (s)")
axs[0, 1].grid(True)

# 3. Box plot - Beams Checked
combined.boxplot(column="Beams Checked in Search", by="Method", ax=axs[1, 0], patch_artist=True,
                 boxprops=dict(facecolor='lightblue', color='black'),
                 medianprops=dict(color='black'))
axs[1, 0].set_title("Beams Checked")
axs[1, 0].set_ylabel("Count")
axs[1, 0].grid(True)

# 4. Box plot - Offset Degrees
combined.boxplot(column="Offset Error", by="Method", ax=axs[1, 1], patch_artist=True,
                 boxprops=dict(facecolor='lightcoral', color='black'),
                 medianprops=dict(color='black'))
axs[1, 1].set_title("Offset Degrees")
axs[1, 1].set_ylabel("Degrees")
axs[1, 1].grid(True)

# Final touches
for ax in axs.flat:
    ax.set_xlabel("")
fig.suptitle("MLP vs. Moving Avg Beamforming Performance", fontsize=16)
plt.tight_layout()
plt.subplots_adjust(top=0.9)

# Save and show
# plot_path = "/mnt/data/mlp_vs_avg_bright_plots.png"
# plt.savefig(plot_path)
plt.show()
