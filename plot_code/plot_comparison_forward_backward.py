import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

# Load both datasets
forward_df = pd.read_csv("<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr16/forward_max_snr_per_angle.csv")

# Convert Angle to Boresight Angle (0–180 → -90 to +90)
forward_df["Boresight Angle"] = forward_df["Rotor Angle"] - 90

# Plot
plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
             marker="o", linewidth=3, label="Optimal (Full Exhaustive Forward Sweep)", color="darkblue")



# Format axes
plt.title("SNR vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.xlim(-90, 90)
plt.ylim(0,30)


# Set ticks every 5 degrees
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))

plt.grid(True)
plt.legend(fontsize=18)
plt.tight_layout()
plt.savefig("forward_max_snr.png", dpi=500)
plt.show()
