import os
import pandas as pd
import re

# Beam angle mappings
RX_BEAM_ANGLES = [0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4,
                  -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3,
                  -18.9, -17.4, -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3,
                  -5.8, -4.4, -2.9, -1.5, 0, 1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2,
                  11.6, 13.1, 14.5, 16.0, 17.4, 18.9, 20.3, 21.8, 23.2, 24.7,
                  26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8, 36.3, 37.7, 39.2,
                  40.6, 42.1, 43.5, 45.0]
TX_BEAM_ANGLES = [0, 45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9,
                  30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4,
                  16.0, 14.5, 13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0,
                  -1.5, -2.9, -4.4, -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5,
                  -16.0, -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6,
                  -29.0, -30.5, -31.9, -33.4, -34.8, -36.3, -37.7, -39.2,
                  -40.6, -42.1, -43.5, -45.0]

# ---------- CONFIGURE THESE PATHS ----------
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr16"
output_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr16"
output_csv = os.path.join(base_dir, "forward_all_snr_data.csv")

# ---------- Data Aggregation ----------
all_snr_data = []

for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)

    # Skip if not a directory
    if not os.path.isdir(folder_path):
        continue

    # Extract numeric rotor angle from folder name
    match = re.search(r'\d+', folder)
    if not match:
        print(f"[WARNING] Skipping folder '{folder}' (no angle found).")
        continue

    rotor_angle = int(match.group()) - 90  # Convert to -90 to +90

    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if not os.path.exists(snr_file_path):
        print(f"[WARNING] Missing snr_data.csv in {folder_path}")
        continue

    try:
        df = pd.read_csv(snr_file_path, header=None)
        if df.empty or df.shape[1] < 6:
            print(f"[WARNING] File {snr_file_path} is empty or malformed.")
            continue

        df = df.iloc[:, [1, 3, 5]]  # Tx, Rx, SNR columns
        df.columns = ["Tx Beam Index", "Rx Beam Index", "SNR (dB)"]

        # Map angles from indices
        df["Tx Beam Angle"] = df["Tx Beam Index"].apply(
            lambda i: TX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(TX_BEAM_ANGLES) else None
        )
        df["Rx Beam Angle"] = df["Rx Beam Index"].apply(
            lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(RX_BEAM_ANGLES) else None
        )

        df["Boresight Angle"] = rotor_angle
        all_snr_data.append(df)

        print(f"[INFO] Processed {folder}")

    except Exception as e:
        print(f"[ERROR] Failed to process {snr_file_path}: {e}")

# ---------- Save Output ----------
if all_snr_data:
    df_output = pd.concat(all_snr_data, ignore_index=True)
    df_output = df_output[
        ["Boresight Angle", 
         "Tx Beam Index", "Tx Beam Angle", 
         "Rx Beam Index", "Rx Beam Angle", 
         "SNR (dB)"]
    ]
    df_output = df_output.sort_values(by=["Boresight Angle", "Tx Beam Index", "Rx Beam Index"])
    df_output.to_csv(output_csv, index=False)
    print(f"[SUCCESS] All SNR data saved to: {output_csv}")
else:
    print("[INFO] No valid SNR data found.")
