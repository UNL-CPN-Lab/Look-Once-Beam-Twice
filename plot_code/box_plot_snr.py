import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

# Path to your CSV file
# csv_path = "Adaptive_Beamforming_KW/exp1_10sec_rotor/results.csv"  
csv_path = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_4.5m_14db_monday/results_uniform.csv"


# Load the data
df = pd.read_csv(csv_path)



# Map angles from 0–180 to -90 to +90 (boresight centered)
df["Boresight Angle"] = df["Boresight Angle"] - 90

# Sort for consistent plotting
df = df.sort_values(by="Boresight Angle")

# Set larger font sizes
sns.set_context("notebook", font_scale=2.0)

# Create the box plot
plt.figure(figsize=(20, 8))  # Increase figure size to match bigger fonts
sns.boxplot(x='Boresight Angle', y='SNR (dB)', data=df)

# Customize plot
plt.title("Adaptive Beamforming SNR Distribution vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.xticks(rotation=45, fontsize=16)
plt.yticks(fontsize=16)
# Grid every 5 degrees
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.grid(True)

# plt.xlim(-45,45)
plt.ylim(0,50)
plt.grid(True)
plt.tight_layout()

# Save and show
plt.savefig("adaptive_bf_snr_boxplot_boresight.png", dpi=500)
plt.show()