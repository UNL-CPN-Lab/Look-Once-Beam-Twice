import os
import sys
import pandas as pd
import json
import datetime


# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)


from configurations.config import *

# === Argument check ===
if len(sys.argv) != 2:
    print("Usage: python generate_summary_row.py <experiment_name>")
    sys.exit(1)

experiment_name = sys.argv[1]  # e.g., "sc_jun14_gain8db_3m_t31"

# experiment_name = "sc_jul18_gain8db_3m_Off_AB1" 

# === Paths and Constants ===
project_dir = os.path.join(PROJECT_ROOT, "indoor", "continuous", "online", "automatic_indoor_evaluations_mlp","Adaptive_Beamforming_SC")
experiment_path = os.path.join(project_dir,  experiment_name)
summary_dir = os.path.join(project_dir, "summary_logs")
today = datetime.datetime.today()
date = today.strftime("%b").lower() + str(today.day)
summary_csv_path = os.path.join(summary_dir, f"online_evaluation_experiments_results_summary_{date}_oakd.csv")


os.makedirs(summary_dir, exist_ok=True)

def clean_step1(exp_path, exp_name):
    input_csv = os.path.join(exp_path, f"results_{exp_name}.csv")
    output_csv = os.path.join(exp_path, f"cleaned_results_{exp_name}.csv")
    df = pd.read_csv(input_csv)

    # Define the Boresight angle range: [-32, +22] 65 for oakd
    lower_bound = -40
    upper_bound = 40

    # Keep rows where Boresight is within range 
    keep_rows = df["Boresight"].between(lower_bound, upper_bound) 

    df_cleaned = df[keep_rows]

    df_cleaned.to_csv(output_csv, index=False)
    # print(f"[INFO] Cleaned data saved to {output_csv}")
    return output_csv


def clean_step2(exp_path, exp_name):
    import warnings

    cleaned_csv = os.path.join(exp_path, f"cleaned_results_{exp_name}.csv")
    output_csv = os.path.join(exp_path, f"balanced_results_{exp_name}.csv")

    df = pd.read_csv(cleaned_csv)

    if "Boresight" not in df.columns:
        raise KeyError("[ERROR] 'Boresight' column not found in cleaned CSV.")

    counts = df["Boresight"].value_counts()
    Q1 = counts.quantile(0.25)
    Q3 = counts.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    min_required = max(1, int(lower_bound))

    valid_angles = counts[counts >= min_required].index
    df_filtered = df[df["Boresight"].isin(valid_angles)]

    # print("[DEBUG] Angle counts (all):")
    # print(counts)
    # print("[DEBUG] Min required per angle:", min_required)
    # print("[DEBUG] Valid angles:", list(valid_angles))
    # print("[DEBUG] Filtered DataFrame shape:", df_filtered.shape)

    if df_filtered.empty or len(valid_angles) == 0:
        warnings.warn("[WARNING] No valid angles found — skipping balancing. Writing empty CSV.")
        df_filtered.to_csv(output_csv, index=False)
        return output_csv

    final_sample_n = df_filtered["Boresight"].value_counts().min()

    if final_sample_n < 1:
        warnings.warn("[WARNING] Not enough samples per angle to perform balancing.")
        df_filtered.to_csv(output_csv, index=False)
        return output_csv

    if len(valid_angles) == 1:
        print("[INFO] Only one valid angle found — skipping group sampling.")
        df_balanced = df_filtered
    else:
        df_balanced = df_filtered.groupby("Boresight").sample(n=final_sample_n, random_state=42)

    # print(f"[DEBUG] Final sample count per angle: {final_sample_n}")
    # print(f"[DEBUG] Total balanced samples: {len(df_balanced)}")

    df_balanced.to_csv(output_csv, index=False)
    return output_csv


try:
    # === Step 1 and 2: Clean and Balance ===
    _ = clean_step1(experiment_path, experiment_name)
    balanced_csv_path = clean_step2(experiment_path, experiment_name)


    # === Load metadata ===
    metadata_path = os.path.join(experiment_path, "metadata.json")
    with open(metadata_path, "r") as meta_file:
        metadata = json.load(meta_file)

    algorithm_name = metadata.get("Algorithm", "N/A")
    SNR_THRESHOLD = float(str(metadata.get("Threshold", "nan")).replace("dB", "").strip())
    REFERENCE_MAX_SNR_DB = float(metadata.get("reference_max_snr_db", "nan"))
    SNR_THRESHOLD_FACTOR = float(metadata.get("Threshold Factor", "nan"))
    ROTOR_SPEED = metadata.get("rotor_speed", "nan")

    # === Load balanced results and compute metrics ===
    df = pd.read_csv(balanced_csv_path)
    # df_balanced = df[df["Boresight"].notna()].copy().sort_values(by="Boresight").reset_index(drop=True)
    
    df_balanced = df[df["Boresight"].notna()].copy().reset_index(drop=True)




    # outage_events = df_balanced["SNR (dB)"] < SNR_THRESHOLD
    outage_events = (df_balanced["SNR (dB)"] < SNR_THRESHOLD) | (df_balanced["Jetson Detection"] == "NO_RADIO")
    outage_probability = outage_events.sum() / len(df_balanced) if len(df_balanced) > 0 else float('nan')
    avg_beamforming_time = df_balanced["Beam Sweep Time (s)"].mean()
    avg_yolo_time = df_balanced["YOLO Time (s)"].mean()
    total_time = avg_beamforming_time + avg_yolo_time


    new_row = {
        "Experiment": experiment_name,
        "SNR Threshold (dB)": SNR_THRESHOLD,
        "Rotor Speed": ROTOR_SPEED,
        "Algorithm": algorithm_name,
        "Total Samples After Balancing": len(df_balanced),
        "Outage Probability": outage_probability,
        "Average Beamforming Time (s)": avg_beamforming_time,
        "Average YOLO Time (s)": avg_yolo_time,
        "Total Time (s)": total_time
    }

    # === Append to or update summary CSV ===
    if os.path.exists(summary_csv_path):
        summary_df = pd.read_csv(summary_csv_path)
    
        summary_df = summary_df[summary_df["Experiment"] != experiment_name]
        summary_df = pd.concat([summary_df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        summary_df = pd.DataFrame([new_row])

    summary_df.to_csv(summary_csv_path, index=False)
    print(f"[SUCCESS] Summary updated for {experiment_name}")

except Exception as e:
    print(f"[ERROR] Failed to process {experiment_name}: {e}")
