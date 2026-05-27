import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker

# Load data
base_dir1 = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_4.5m_14db_monday/results_uniform.csv"
base_dir2 = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_4.5m_14db_monday_previous_beam/results_uniform.csv"
base_dir3 = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_4.5m_14db_monday_3beams/results_uniform.csv"

base_df = pd.read_csv(base_dir1)
previous_df = pd.read_csv(base_dir2)
beams3_df = pd.read_csv(base_dir3)

# Adjust Boresight
for df in [base_df, previous_df, beams3_df]:
    df["Boresight Angle"] = df["Boresight Angle"] - 90

# ---------- SCATTER PLOT of All SNR Points ----------
plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

plt.scatter(beams3_df["Boresight Angle"], beams3_df["SNR (dB)"],
            label="3-Beam Max SNR", s=50, marker="^", color="green")
plt.scatter(previous_df["Boresight Angle"], previous_df["SNR (dB)"],
            label="Default Previous Beam", s=50, marker="s", color="blue")
plt.scatter(base_df["Boresight Angle"], base_df["SNR (dB)"],
            label="Default 0 degree Beam", s=50, marker="o", color="red")

# Formatting
plt.title("Adaptive Beamforming SNR vs Rx Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.ylim(0, 50)
plt.xlim(-45, 45)
plt.xticks(rotation=45, fontsize=16)
plt.yticks(fontsize=16)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.grid(True)
plt.legend(fontsize=18)
plt.tight_layout()
plt.savefig("scatter_snr_vs_boresight_all_methods.png", dpi=500)
plt.show()
