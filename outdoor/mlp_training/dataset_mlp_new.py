import pandas as pd
import numpy as np
import os
import re
import json




def create_training_dataset(results_csv_path, metadata_path, output_csv_path):
    # Load metadata
    with open(metadata_path, "r") as f:
        meta = json.load(f)

    snr_thresh_db = float(meta["Threshold"].split()[0])

    # Load experiment results
    df = pd.read_csv(results_csv_path)
    df.columns = df.columns.str.strip()
 
    df["snr_thresh_db"] = snr_thresh_db

    # Extract relevant columns
    final_df = df[[
        "Boresight",
        "snr_thresh_db",
        "Rx Beam Index (YOLO Predicted)",
        "Initial SNR (dB)",
        "Offset Error"
    ]].dropna()

    # Append to CSV
    final_df.to_csv(output_csv_path, index=False, mode='a', header=not os.path.exists(output_csv_path))
    print(f"Appended {len(final_df)} rows from {results_csv_path}")

# === CONFIGURATION ===
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/optimized/outdoor/Outdoor_Adaptive_Beamforming_SC/mavg_Results"
output_csv_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/optimized/outdoor/mlp_models/offset_dataset_nh_outdoor.csv"


os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
print("Current working directory:", os.getcwd())


# === PROCESS LOOP FOR EVEN EXPERIMENTS ===
for t in range(1, 15, 1):
    experiment_name = f"nh_jul14_gain9db_12db_16m_t{t}"
    experiment_path = os.path.join(exp_base_path, experiment_name)
    results_csv = os.path.join(experiment_path, f"results_{experiment_name}.csv")
    metadata_path = os.path.join(experiment_path, "metadata.json")

    if not os.path.exists(results_csv):
        print(f"[!] Missing results.csv in {experiment_name}, skipping...")
        continue
    if not os.path.exists(metadata_path):
        print(f"[!] Missing metadata.json in {experiment_name}, skipping...")
        continue

    create_training_dataset(results_csv, metadata_path, output_csv_path)
