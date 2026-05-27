import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

# Load the already processed error CSV
output_path = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_apr11_gain13db_3m_t2_tx27"
csv_path = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_apr11_gain13db_3m_t2_tx27/rx_beam_errors.csv"
df = pd.read_csv(csv_path)

# Create a binned column for boxplot/heatmap grouping
df["boresight_bin"] = df["boresight"].round()

# Set a consistent plot style
sns.set(style="whitegrid")

def save_plot(fig, name):
    for ext in ['png', 'svg', 'eps']:
        fig.savefig(f"{output_path}/{name}.{ext}", format=ext)

# ---------- Plot 1: Histogram of RX Beam Angle Error ----------
fig, ax = plt.subplots(figsize=(12, 5))
sns.histplot(df["rx_beam_angle_error"], bins=50, kde=True, color='orange', label="Angle Error", stat="density", ax=ax)
ax.set_title("Histogram of RX Beam Angle Error", fontsize=18)
ax.set_xlabel("RX Beam Angle Error (°)", fontsize=14)
ax.set_ylabel("Density", fontsize=14)
ax.legend()
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
ax.grid(True, which='both')
plt.tight_layout()
save_plot(fig, "hist_rx_beam_angle_error")
plt.show()

# ---------- Plot 2: Histogram of RX Beam Index Error ----------
fig, ax = plt.subplots(figsize=(12, 5))
sns.histplot(df["rx_beam_index_error"], bins=50, kde=True, color='blue', label="Index Error", stat="density", ax=ax)
ax.set_title("Histogram of RX Beam Index Error", fontsize=18)
ax.set_xlabel("RX Beam Index Error", fontsize=14)
ax.set_ylabel("Density", fontsize=14)
ax.legend()
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
ax.grid(True, which='both')
plt.tight_layout()
save_plot(fig, "hist_rx_beam_index_error")
plt.show()

# ---------- Plot 3: Angle Error vs Boresight ----------
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["boresight"], df["rx_beam_angle_error"], '.', alpha=0.5, label="Angle Error", color="orange")
ax.set_title("RX Beam Angle Error vs Boresight", fontsize=18)
ax.set_xlabel("Boresight Angle (°)", fontsize=14)
ax.set_ylabel("Angle Error (°)", fontsize=14)
ax.legend()
ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
ax.grid(True, which='both')
plt.tight_layout()
save_plot(fig, "scatter_rx_beam_angle_error")
plt.show()

# ---------- Plot 4: Index Error vs Boresight ----------
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["boresight"], df["rx_beam_index_error"], '.', alpha=0.5, label="Index Error", color="blue")
ax.set_title("RX Beam Index Error vs Boresight", fontsize=18)
ax.set_xlabel("Boresight Angle (°)", fontsize=14)
ax.set_ylabel("Index Error", fontsize=14)
ax.legend()
ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
ax.grid(True, which='both')
plt.tight_layout()
save_plot(fig, "scatter_rx_beam_index_error")
plt.show()


