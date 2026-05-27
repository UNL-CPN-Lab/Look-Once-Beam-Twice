import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

# Load both datasets
forward_df = pd.read_csv("/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/nh_forward_sweep_14db_3m/forward_max_snr_per_angle.csv")

# forward_df = pd.read_csv("/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/nh_forward_sweep_14db_3m/forward_max_snr_per_angle.csv")
center_df = pd.read_csv("/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/nh_forward_sweep_14db_3m/snr_tx32_rx32_forward.csv")

# Sort by angle for consistent plotting
forward_df = forward_df.sort_values(by="Rotor Angle")
center_df = center_df.sort_values(by="Rotor Angle")

# Plot settings
plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

# Plot both lines
sns.lineplot(data=forward_df, x="Rotor Angle", y="SNR (dB)",
             marker="o", linewidth=3, label="Optimal(Full Exhaustive Forward Sweep)", color="darkblue")

sns.lineplot(data=center_df, x="Rotor Angle", y="SNR (dB)",
             marker="s", linewidth=3, label=" 0 dergree - 0 dergree", color="firebrick")

# Axis settings
plt.title("SNR vs Rx Boresight Angle", fontsize=24)
plt.xlabel("Rx Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.xlim(-45, 45)
plt.ylim(0,50)

# Set X-axis limits and ticks
ax = plt.gca()
ax.set_xlim(0, 180)
ax.xaxis.set_major_locator(ticker.MultipleLocator(5))

# Rename x-axis tick labels from 0–180 to -90 to +90
tick_locs = list(range(0, 181, 5))
tick_labels = [str(x - 90) for x in tick_locs]
ax.set_xticks(tick_locs)
ax.set_xticklabels(tick_labels)

# Grid and legend
plt.grid(True)
plt.legend(fontsize=18)
plt.tight_layout()
plt.savefig("forward_0degree_snr_vs_boresight.png", dpi=500)
plt.show()
