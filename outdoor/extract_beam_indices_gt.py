import os
import re
import pandas as pd
import matplotlib.pyplot as plt

# ==== Beam Angle Mappings ====
RX_BEAM_ANGLES = [0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4,
    -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0,
    1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4,
    18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8,
    36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
TX_BEAM_ANGLES = [0, 45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9,
    30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5,
    13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4,
    -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3,
    -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8,
    -36.3, -37.7, -39.2, -40.6, -42.1, -43.5, -45.0]

# ==== Base Directory ====


base_dir = "<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/sweepData/"



# ==== Match Folder Names ====
pattern = re.compile(r"sc_outdoor_jul2_gain9db_16m_\d+_gt(\d+)")
folders = []

for f in os.listdir(base_dir):
    match = pattern.match(f)
    if match:
        gt_number = int(match.group(1))
        folders.append((gt_number, f))

folders.sort()

# ==== Results ====
results = []

# ==== Process Folders ====
for gt_number, folder in folders:
    csv_path = os.path.join(base_dir, folder, "snr_data.csv")
    if not os.path.exists(csv_path):
        print(f"[WARN] Missing file: {csv_path}")
        continue

    df = pd.read_csv(csv_path, header=None)

    # Get row with max SNR (Column index 3)
    best_row = df.loc[df[3].idxmax()]

    tx_idx = int(best_row[1])  # Column B
    rx_idx = int(best_row[2])  # Column C
    snr = float(best_row[3])  # Column D

    tx_angle = TX_BEAM_ANGLES[tx_idx]
    rx_angle = RX_BEAM_ANGLES[rx_idx]

    results.append({
        "Folder": folder,
        "GT": gt_number,
        "TX Index": tx_idx,
        "TX Angle": tx_angle,
        "RX Index": rx_idx,
        "RX Angle": rx_angle,
        "Max SNR (dB)": snr
    })

# ==== Save and Plot ====
results_df = pd.DataFrame(results).sort_values("GT")
results_df.to_csv("beam_results.csv", index=False)
print("Saved beam_results.csv")

# ==== Plot ====
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(results_df["GT"], results_df["TX Index"], 'bo-', label='TX Beam Index')
plt.plot(results_df["GT"], results_df["RX Index"], 'ro-', label='RX Beam Index')
plt.title("Best Beam Indices")
plt.xlabel("GT Index")
plt.ylabel("Beam Index")
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(results_df["GT"], results_df["TX Angle"], 'bo-', label='TX Beam Angle')
plt.plot(results_df["GT"], results_df["RX Angle"], 'ro-', label='RX Beam Angle')
plt.title("Best Beam Angles (degrees)")
plt.xlabel("GT Index")
plt.ylabel("Beamforming Angle (°)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
