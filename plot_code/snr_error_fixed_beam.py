import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np



# ----------- Define experiment path and name -----------
experiment_path = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/FixedBeamSweep/nh_apr15_gain13db_3m_t1_los"
experiment_name = "nh_apr15_gain13db_3m_t1_los"
snr_data = []

# ----------- Extract and Average SNR per rx_angle + boresight -----------
for folder in os.listdir(experiment_path):
    if folder.startswith("rx_"):
        try:
            rx_index = int(folder.split("_")[1])
        except ValueError:
            print(f"[WARNING] Skipping folder '{folder}', cannot extract rx_index")
            continue

        rx_path = os.path.join(experiment_path, folder)

        for angle_folder in os.listdir(rx_path):
            if angle_folder.startswith("angle_"):
                try:
                    angle_index = int(angle_folder.split("_")[1])
                    boresight_angle = angle_index - 90
                    snr_file = os.path.join(rx_path, angle_folder, "snr_data.csv")

                    if not os.path.exists(snr_file):
                        print(f"[SKIPPED] Missing file: {snr_file}")
                        continue

                    df = pd.read_csv(snr_file, header=None, sep=None, engine='python')
                    if df.shape[1] < 7:
                        print(f"[SKIPPED] {snr_file} has only {df.shape[1]} columns")
                        continue

                    df.columns = ["sample_size", "tx_idx", "tx_angle", "rx_index", "rx_angle", "boresight", "snr"]

                    avg_snr = df["snr"].mean()
                    rx_angle = df["rx_angle"].iloc[0]

                    snr_data.append({
                        "rx_angle": rx_angle,
                        "boresight": boresight_angle,
                        "avg_snr": avg_snr
                    })

                except Exception as e:
                    print(f"[ERROR] angle folder '{angle_folder}' in '{folder}': {e}")
                    continue

# ----------- Create DataFrame -----------
if not snr_data:
    raise RuntimeError("No SNR data collected.")
# Clean up RX angle precision


full_df = pd.DataFrame(snr_data)

full_df["rx_angle"] = full_df["rx_angle"].round(1)# Clean up RX angle precision

# Step 1: Global maximum SNR
global_max_snr = full_df["avg_snr"].max()

# Step 2: Maximum SNR per RX angle
max_snr_per_rx = full_df.groupby("rx_angle")["avg_snr"].max().reset_index()
max_snr_per_rx.columns = ["rx_angle", "rx_max_snr"]

# Step 3: Error from global max
max_snr_per_rx["snr_error_from_global"] = global_max_snr - max_snr_per_rx["rx_max_snr"]

# Optional: Display or save results
print(max_snr_per_rx.sort_values("rx_angle"))


# Save the error data to CSV
error_csv_path = os.path.join(experiment_path, f"snr_error_from_global_{experiment_name}.csv")
max_snr_per_rx.to_csv(error_csv_path, index=False)
print(f"Saved SNR error CSV to: {error_csv_path}")


import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(
    max_snr_per_rx["rx_angle"],
    max_snr_per_rx["snr_error_from_global"],
    marker='o',
    linestyle='-',
    color='crimson'
)

plt.title("SNR Error per RX Beam Angle", fontsize=20)
plt.xlabel("RX Beam Angle (°)", fontsize=16)
plt.ylabel("SNR Error from Global Max (dB)", fontsize=16)
plt.xticks(rotation=45, fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True)
plt.tight_layout()

# Save the plot
error_plot_base = f"snr_error_from_global_plot_{experiment_name}"
for ext in ['png', 'svg', 'eps']:
    plt.savefig(os.path.join(experiment_path, f"{error_plot_base}.{ext}"), format=ext)

plt.show()
