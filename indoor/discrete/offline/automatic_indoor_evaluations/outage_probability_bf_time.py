import os
import pandas as pd
import json


# Set up root directory
root_dir = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/experiments/Adaptive_Beamforming_SC"

# Destination for summary logs
summary_dir = os.path.join(root_dir, "summary_logs")
os.makedirs(summary_dir, exist_ok=True)

# Summary CSV
summary_csv_path = os.path.join(summary_dir, "online_evaluation_experiments_results_summary_balanced_data.csv")
summary_rows = []

# Loop over experiments
for i in range(1, 46):
    test_number = f"t{i}"
    experiment_name = f"sc_jun14_gain8db_3m_{test_number}"
    experiment_path = os.path.join(root_dir, experiment_name)

    try:
        # Load metadata.json
        metadata_path = os.path.join(experiment_path, "metadata.json")
        with open(metadata_path, "r") as meta_file:
            metadata = json.load(meta_file)

        # Extract values
        algorithm_name = metadata.get("algorithm_name", "N/A")
        REFERENCE_MAX_SNR_DB = metadata.get("REFERENCE_MAX_SNR_DB", None)
        SNR_THRESHOLD_FACTOR = metadata.get("SNR_THRESHOLD_FACTOR", None)
        SNR_THRESHOLD = metadata.get("SNR_THRESHOLD", None)
        ROTOR_SPEED = metadata.get("ROTOR_SPEED", "N/A")

        # Load balanced results
        csv_filename = f"balanced_results_{experiment_name}.csv"
        csv_path = os.path.join(experiment_path, csv_filename)
        df = pd.read_csv(csv_path)

        # Filter and analyze
        df_radio = df[df["Jetson Detection"] != "NO_RADIO"].copy()
        df_balanced = df_radio[df_radio["Boresight Angle"].notna()].copy()
        df_balanced = df_balanced.sort_values(by="Boresight Angle").reset_index(drop=True)

        outage_events = df_balanced["SNR (dB)"] < SNR_THRESHOLD
        outage_probability = outage_events.sum() / len(df_balanced) if len(df_balanced) > 0 else float('nan')
        avg_beamforming_time = df_balanced["Beam Sweep Time (s)"].mean()
        avg_yolo_time = df_balanced["YOLO Time (s)"].mean()

        summary_rows.append({
            "Experiment": experiment_name,
            "SNR Threshold (dB)": SNR_THRESHOLD,
            "SNR Threshold Factor": SNR_THRESHOLD_FACTOR,
            "Reference Max SNR (dB)": REFERENCE_MAX_SNR_DB,
            "Rotor Speed": ROTOR_SPEED,
            "Algorithm": algorithm_name,
            "Total Samples After Balancing": len(df_balanced),
            "Outage Probability": outage_probability,
            "Average Beamforming Time (s)": avg_beamforming_time,
            "Average YOLO Time (s)": avg_yolo_time
        })

    except Exception as e:
        print(f"[ERROR] Failed to process {experiment_name}: {e}")

# Write final summary CSV
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(summary_csv_path, index=False)
# import ace_tools as tools; tools.display_dataframe_to_user(name="Evaluation Summary", dataframe=summary_df)

