
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker

# Load data
base_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_4.5m_14db_monday/results_uniform.csv"


# csv_path = "../Adaptive_Beamforming_NH/test_nh_14db/results.csv"  
base_df = pd.read_csv(base_dir)


base_df["Boresight Angle"] = base_df["Boresight Angle"] - 90





# ---------- PLOT 1: Average SNR per 5° Boresight Bin (Line Plot) ----------


plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

mean_snr = df.groupby("Boresight Angle")["SNR (dB)"].mean().reset_index()
mean_snr = mean_snr.sort_values("Boresight Angle")

sns.lineplot(data=mean_snr, x="Boresight Angle", y="SNR (dB)", marker="o", linewidth=3)


plt.title("Mean Adaptive Beamforming SNR vs Rx Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.ylim(0,50)
plt.xlim(-45,45)
plt.xticks(rotation=45, fontsize=16)
plt.yticks(fontsize=16)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.grid(True)
plt.tight_layout()
plt.savefig("mean_snr_vs_boresight_previous_beam.png", dpi=500)
plt.show()

# ---------- PLOT 2: All SNR Samples by 5° Boresight Bins (Strip Plot) ----------
plt.figure(figsize=(20, 8))

# sns.swarmplot(data=df, x="Boresight Bin", y="SNR (dB)", size=4, alpha=0.8)
sns.stripplot(data=df, x="Boresight Angle", y="SNR (dB)", jitter=True, size=3, alpha=0.6,color="darkblue")


# plt.title("All Adaptive Beamforming SNR Samples ", fontsize=24)
# plt.xlabel("Rx Boresight Angle (°)", fontsize=22)
# plt.ylabel("SNR (dB)", fontsize=22)
# plt.xticks(rotation=45, fontsize=16)
# plt.yticks(fontsize=16)
# plt.ylim(0,50)

# plt.grid(True)
# plt.tight_layout()
# plt.savefig("all_snr_swarm_vs_boresight_.png", dpi=500)
# plt.show()

