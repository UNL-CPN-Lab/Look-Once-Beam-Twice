

'''
Extract SNR values for Tx Beam 32 and Rx Beam 32 from all angle folders
'''
import os
import pandas as pd 
import re

# Define the base directory
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr16"
exp_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr16"
output_csv = os.path.join(base_dir, "snr_tx30_rx32_forward.csv")

# List to store extracted data
snr_data_tx32_rx32 = []

# Iterate through angle directories
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)

    # Extract numeric angle from folder name
    match = re.search(r'\d+', folder)
    if not match:
        print(f"[WARNING] Skipping folder '{folder}' (no numeric angle found).")
        continue
    angle = int(match.group())

    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.isdir(folder_path) and os.path.exists(snr_file_path):
        try:
            print(f"[INFO] Processing: {snr_file_path}")

            # Read CSV without header
            df = pd.read_csv(snr_file_path, header=None)

            if df.empty or df.shape[1] < 4:
                print(f"[WARNING] {snr_file_path} is empty or has insufficient columns.")
                continue

            # Drop first column and assign column names
            # df = df.iloc[:, 1:]
            # df.columns = ["Tx Beam "", "Rx Beam ", "SNR (dB)"]

            df = df.iloc[:, [2, 4, 5]]
            df.columns = ["Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"]

            # Filter for Tx Beam = 32 and Rx Beam = 32
            df_filtered = df[(df["Tx Beam Angle"] == 2.9) & (df["Rx Beam Angle"] == 0)]

            if df_filtered.empty:
                print(f"[WARNING] No data for Tx Beam 32 and Rx Beam 32 in {snr_file_path}.")
                continue

            # Take the SNR value for Tx Beam 32 and Rx Beam 32
            snr_value = df_filtered.iloc[0]["SNR (dB)"]

            # Append to the list
            snr_data_tx32_rx32.append([angle, snr_value])

        except Exception as e:
            print(f"[ERROR] Could not process {snr_file_path}: {e}")

# Save to CSV if data exists
if snr_data_tx32_rx32:
    df_output = pd.DataFrame(snr_data_tx32_rx32, columns=["Rotor Angle", "SNR (dB)"])
    df_output = df_output.sort_values(by="Rotor Angle")
    df_output.to_csv(output_csv, index=False)
    print(f"[SUCCESS] SNR summary for Tx30-Rx32 saved to: {output_csv}")
else:
    print("[INFO] No valid SNR data for Tx Beam 32 and Rx Beam 32 found.")
