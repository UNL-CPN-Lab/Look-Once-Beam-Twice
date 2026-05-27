"""Project-wide configuration constants.

All tunable values for the VIBE pipeline live here: beambook tables (TX/RX
beam angle vectors), network IPs, file paths (`PROJECT_ROOT`, ground-truth
directory), SNR threshold parameters, camera intrinsics, USRP/Sivers
parameters, serial port for the Arduino rotor, and per-experiment metadata
(gain, distance, location).

Users must edit these placeholders before running anything:
- `PROJECT_ROOT` — absolute path of this repo on your machine
- `JETSON_IP` / `NUC_IP` — UE-side and TX-side host IPs
- `serial_port` — Arduino rotor USB device
- Camera intrinsics (`PIXEL_PITCH`, `FX_MM`, `CX`) for your camera

Several constants (`SNR_QUANTILE`, `ROTOR_SPEED`, `gain`, `distance`,
`location`, `SNR_THRESHOLD`, `REFERENCE_MAX_SNR_DB`, `fixed_tx_beam`,
`GROUND_TRUTH_NAME`) are rewritten in place by the orchestrators while a
sweep runs — see `configurations/README.md` for the full list.

Author: Apala Pramanik
"""

import os
from .utils import snr_percent_db , get_rotation_time_ms # Utility to convert SNR percentage to dB

# === CAMERA CALIBRATION FILES ===
CAMERA_MATRIX_FILE = "camera_matrix.npy"
DIST_COEFFS_FILE = "dist_coeffs.npy"

# === CAMERA PARAMETERS ===
PIXEL_PITCH = 0.003096           # In mm/pixel
FX_MM = 1.879                    # Focal length in mm
CX = 314.3828                    # Optical center x-coordinate

# === EVALUATION PARAMETERS ===
SNR_THRESHOLD = 23.87 
ROTOR_SPEED = 4  # Rotor speed in sec/deg
CAR_SPEED = 5# Car speed in mph
SNR_QUANTILE = 0.95
MAX_BEAM_INDEX = 63
MIN_BEAM_INDEX = 1


# === NETWORK CONFIGURATION (Jetson TX Interface) ===
# Replace these with your host IPs. JETSON_IP is the UE-side host (camera +
# YOLO detector); NUC_IP is the TX-side host running the beam configuration
# over ZMQ. See docs/HARDWARE.md for the network topology.
JETSON_IP = '<JETSON_IP>'
NUC_IP = '<NUC_IP>'
PORT = 5001

# === RADIO PARAMETERS ===
INIT_DELAY = 0.08                # Delay before starting RX host (in seconds)
SAMPLE_SIZE = 2000               # Number of IQ samples to collect
PADDING = 100                    # Padding used for noise floor estimation

# RX Beam Angles (symmetric sweep around 0°)
RX_BEAM_ANGLES = [
     0.0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9,
    -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2,  -8.7,  -7.3,  -5.8,  -4.4,  -2.9,  -1.5,
     0,     1.5,   2.9,   4.4,   5.8,   7.3,   8.7,  10.2,  11.6,  13.1,  14.5,
    16.0,  17.4,  18.9,  20.3,  21.8,  23.2,  24.7,  26.1,  27.6,  29.0,  30.5,
    31.9,  33.4,  34.8,  36.3,  37.7,  39.2,  40.6,  42.1,  43.5,  45.0
]

# TX Beam Angles (same range, mirrored order)
TX_BEAM_ANGLES = [
     0.0,  45.0,  43.5,  42.1,  40.6,  39.2,  37.7,  36.3,  34.8,  33.4,  31.9,
    30.5,  29.0,  27.6,  26.1,  24.7,  23.2,  21.8,  20.3,  18.9,  17.4,  16.0,
    14.5,  13.1,  11.6,  10.2,   8.7,   7.3,   5.8,   4.4,   2.9,   1.5,   0,
    -1.5,  -2.9,  -4.4,  -5.8,  -7.3,  -8.7, -10.2, -11.6, -13.1, -14.5, -16.0,
   -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9,
   -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1, -43.5, -45.0
]

fixed_tx_beam = 27  # Updated from GT extraction

# === EXPERIMENTAL PARAMETERS ===
gain = "8db"
distance = "3m"
location = "sc"  # Updated from automatic.py

# === SERIAL COMMUNICATION PARAMETERS ===
serial_port = "/dev/ttyACM0"     # Serial port used for hardware control
baud_rate = 115200               # Baud rate for serial communication


# === PATH CONFIGURATION ===
# GROUND_TRUTH_NAME is the experiment ID for the ground-truth sweep being
# evaluated. Change per experiment. PROJECT_ROOT must point to the absolute
# path of this repo on your machine (used to resolve sibling scripts and
# ground-truth CSVs).
GROUND_TRUTH_NAME = "optimized_exhaustive_sweep_sc_jul24_gain8db_3m_QT_OAKD_MLP15"
PROJECT_ROOT = "/path/to/Look-Once-Beam-Twice"

# Ground truth files
GROUND_TRUTH_DIR = os.path.join(PROJECT_ROOT, "Adaptive_Beamforming_SC", GROUND_TRUTH_NAME)
GROUND_TRUTH_CSV = os.path.join(GROUND_TRUTH_DIR, "forward_all_snr_data.csv")
BEST_RX_BEAM_CSV = os.path.join(GROUND_TRUTH_DIR, "forward_max_snr_per_angle.csv")

# Script paths
PLOT_EXPERIMENT = os.path.join(PROJECT_ROOT, "configurations", "plot_experiment.py")
# PLOT_GROUND_TRUTH_SCRIPT = os.path.join(PROJECT_ROOT, "plot_ground_truth.py")
# EVAL_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "eval.py")
