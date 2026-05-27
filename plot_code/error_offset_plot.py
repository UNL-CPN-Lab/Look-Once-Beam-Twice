import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------- 1. Define experiment path ----------
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
experiment_name = "nh_apr21_gain13db_3m_t6"
experiment_path = os.path.join(exp_base_path, experiment_name)
csv_path = os.path.join(experiment_path, "results.csv")

# ---------- 2. Load CSV ----------
df = pd.read_csv(csv_path)

# ---------- 3. RX Beam Index to Angle Mapping ----------
RX_BEAM_ANGLES = [
    0.0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9,
    -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0.0,
    1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4,
    18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8,
    36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0
]

# ---------- 4. Compute Angles and Offset Errors ----------
df["predicted_angle"] = df["Rx Beam Index (YOLO Predicted)"].map(
    lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
)
df["selected_angle"] = df["Rx Beam Index (Selected)"].map(
    lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
)
df["offset_error_deg"] = abs(df["predicted_angle"] - df["selected_angle"])
df["offset_error_pct"] = (df["offset_error_deg"] / 90.0) * 100  # 90° as reference max

# ---------- 5. Plot Bar Graph ----------
plt.figure(figsize=(12, 6))
plt.bar(df["Boresight Angle"], df["offset_error_pct"])
plt.title("Offset Error Percentage: YOLO Predicted vs Selected RX Beam Angle", fontsize=16)
plt.xlabel("Boresight Angle (°)", fontsize=14)
plt.ylabel("Offset Error (%)", fontsize=14)
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# Save in multiple formats
plot_base_name = f"beam_error_offset_{experiment_name}"
plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.png"), format='png')
plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.svg"), format='svg')
plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.eps"), format='eps')
plt.show()