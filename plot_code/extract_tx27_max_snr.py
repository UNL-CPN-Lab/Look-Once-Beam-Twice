import os
import pandas as pd
import re

# Beam angle mappings (not used in final CSV but still available)
RX_BEAM_ANGLES = [0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4, -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0, 1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4, 18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8, 36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
TX_BEAM_ANGLES = [0, 45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9, 30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5, 13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4, -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1, -43.5, -45.0]

# Directories
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr16"
exp_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr16"
output_csv = os.path.join(base_dir, "tx30_max_snr.csv")

# Result list
filtered_data = []

# Loop over folders
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)

    # Parse rotor angle
    match = re.search(r'\d+', folder)
    if not match:
        print(f"[WARNING] Skipping folder '{folder}' (no numeric angle found).")
        continue
    angle = int(match.group())
    boresight_angle = angle - 90

    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.isdir(folder_path) and os.path.exists(snr_file_path):
        try:
            print(f"[INFO] Processing: {snr_file_path}")
            df = pd.read_csv(snr_file_path, header=None)

            if df.empty or df.shape[1] < 4:
                print(f"[WARNING] {snr_file_path} is empty or has insufficient columns.")
                continue

            # Extract relevant columns
            df = df.iloc[:, [1, 3, 5]]
            df.columns = ["Tx Beam Index", "Rx Beam Index", "SNR (dB)"]

            # Filter rows for Tx beam index 32
            tx32_df = df[df["Tx Beam Index"] == 30]

            if not tx32_df.empty:
                # Find row with max SNR
                max_row = tx32_df.loc[tx32_df["SNR (dB)"].idxmax()]
                filtered_data.append({
                    "Boresight Angle": boresight_angle,
                    "Tx Beam Index": int(max_row["Tx Beam Index"]),
                    "Rx Beam Index": int(max_row["Rx Beam Index"]),
                    "SNR (dB)": max_row["SNR (dB)"]
                })

        except Exception as e:
            print(f"[ERROR] Could not process {snr_file_path}: {e}")

# Save results
if filtered_data:
    df_filtered = pd.DataFrame(filtered_data)
    df_filtered = df_filtered.sort_values(by=["Boresight Angle"])
    df_filtered.to_csv(output_csv, index=False)
    print(f"[SUCCESS] Filtered Tx=32 Max SNR data saved to: {output_csv}")
else:
    print("[INFO] No valid data for Tx Beam Index 32 found.")
