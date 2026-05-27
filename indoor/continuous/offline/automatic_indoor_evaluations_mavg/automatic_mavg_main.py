"""Orchestrator for VIBE-MA offline indoor evaluations (continuous rotor).

Replays SNR from a pre-collected ground-truth sweep instead of measuring it
live. Iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations; for each, runs
`run_ground_truth_data_extraction.py` to compute thresholds, then launches
`continuous_offline_main_mavg.py` for the live experiment. The source
ground-truth name (built from `date`, `location`, `gain`, `distance`,
`test_number`) must already exist on disk — see the folder README for how to
point this at your own pre-collected sweep. Console output is mirrored to
`automatic_evaluation_terminal_log.txt`.

Run from this folder: `python3 offline_automatic_mavg_main.py`.

Author: Apala Pramanik
"""

import subprocess
import os
import time
import itertools
import datetime
import pandas as pd
import sys

# Make `configurations` importable so we can derive paths from PROJECT_ROOT.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from configurations.config import PROJECT_ROOT

# === LOGGER SETUP ===
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", buffering=1)

    def write(self, message):
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        self.terminal.write(message)
        if message.strip():
            self.log.write(timestamp + message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

logfile_name = "automatic_evaluation_terminal_log.txt"
sys.stdout = Logger(logfile_name)
sys.stderr = Logger(logfile_name)

start_time = time.time()
print("\n[LOG] Automatic evaluation pipeline started at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# === CONFIGURATION ===
CONFIG_PATH = "../../../../configurations/config.py"  # Path to your config file

# ROTOR_SPEEDS = [0.25, 0.5, 1, 2, 4]  # Rotor speeds (deg/sec)
# SNR_QUANTILE = [0.8,0.9,0.95]  # Normalized SNR threshold factors

ROTOR_SPEEDS = [0.25,0.5,1,2,4]#Rotor speeds (deg/sec)
SNR_QUANTILE = [0.8,0.9,0.95]  # Normalized SNR threshold factors

# === SCRIPT PATHS ===
GROUND_SWEEP_SCRIPT = "optimized_beam_sweep.py"
ONLINE_SCRIPT = "continuous_offline_main_mavg.py"
PLOT_GROUND_TRUTH_SCRIPT = "plot_ground_truth.py"

# === CONFIG UPDATE HELPERS ===
def update_fixed_tx_beam_in_config(tx_index):
 
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("fixed_tx_beam"):
                f.write(f"fixed_tx_beam = {tx_index}  # Updated from GT extraction\n")
            else:
                f.write(line)



def update_ground_truth_name_in_config(new_name):
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("GROUND_TRUTH_NAME"):
                f.write(f'GROUND_TRUTH_NAME = "{new_name}"\n')
            else:
                f.write(line)

def update_experiment_parameters_in_config(location, gain, distance):
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("gain"):
                f.write(f'gain = "{gain}"\n')
            elif line.strip().startswith("distance"):
                f.write(f'distance = "{distance}"\n')
            elif line.strip().startswith("location"):
                f.write(f'location = "{location}"  # Updated from automatic.py\n')
            else:
                f.write(line)

def update_config(rotor_speed, snr_quantile):
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if "SNR_QUANTILE" in line:
                f.write(f"SNR_QUANTILE = {snr_quantile}\n")
            elif "ROTOR_SPEED" in line:
                f.write(f"ROTOR_SPEED = {rotor_speed}  # Rotor speed in sec/deg\n")
            else:
                f.write(line)

def update_reference_max_snr(avg_snr_db):
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("REFERENCE_MAX_SNR_DB"):
                f.write(f'REFERENCE_MAX_SNR_DB = {avg_snr_db:.2f}  # Auto-updated from GT\n')
            else:
                f.write(line)



# === SCRIPT RUNNER ===
def run_python(script_name, extra_args=None):
    cmd = ["python3", script_name]
    if extra_args:
        cmd.extend(extra_args)
    print(f"\n[RUNNING] {script_name} {' '.join(extra_args) if extra_args else ''}")
    subprocess.run(cmd, check=True)

# === MAIN PIPELINE ===
def main():

        
        print("----------------------------------------------------------------------------------------------------------")
        
        print("\n[STEP 1] Updating GROUND_TRUTH_NAME in config.py...")
        
        print("----------------------------------------------------------------------------------------------------------")
        
        
        today = datetime.datetime.today()
        date = today.strftime("%b").lower() + str(today.day)
        location = "sc"
        gain = "8db"
        distance = "3m"
        # Identifier of the pre-collected ground-truth sweep being replayed.
        # All four offline variants share the same source ground truth so
        # their results are directly comparable. Edit to match the experiment
        # ID of your own captured sweep.
        test_number = "offline_basic"
        GROUND_TRUTH_NAME_NEW = f"optimized_exhaustive_sweep_{location}_{date}_gain{gain}_{distance}_{test_number}"
        update_experiment_parameters_in_config(location, gain, distance)
        update_ground_truth_name_in_config(GROUND_TRUTH_NAME_NEW)
        
        print("----------------------------------------------------------------------------------------------------------")

        print("\n[STEP 2] Running Optimized Beam Sweep...")
        
        print("----------------------------------------------------------------------------------------------------------")
        
        # run_python(GROUND_SWEEP_SCRIPT)
        
        print("----------------------------------------------------------------------------------------------------------")
        
        print("\n[STEP 3] Extracting Ground Truth Data...")
        experiment_counter = 1
        print("----------------------------------------------------------------------------------------------------------")
        for snr_quantile, rotor_speed in itertools.product(SNR_QUANTILE, ROTOR_SPEEDS):
            update_config(rotor_speed, snr_quantile)
            try:
                extract_cmd = [
                    "python3",
                    "run_ground_truth_data_extraction.py",
                    GROUND_TRUTH_NAME_NEW,
                    str(snr_quantile)
                ]
                result = subprocess.run(extract_cmd, capture_output=True, text=True, check=True) 
                print("[INFO] Extraction complete.")
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print("[ERROR] Extraction failed:")
                print(e.stderr)
            
            
            print("----------------------------------------------------------------------------------------------------------")

            print("\n[STEP 4] Plotting Ground Truth Results...")
            
            print("----------------------------------------------------------------------------------------------------------")
            
            
            os.environ["GROUND_TRUTH_NAME"] = GROUND_TRUTH_NAME_NEW
            os.environ["GROUND_TRUTH_PATH"] = os.path.join(
                PROJECT_ROOT,
                "indoor", "continuous", "offline", "automatic_indoor_evaluations_mavg",
                "Adaptive_Beamforming_SC",
                GROUND_TRUTH_NAME_NEW,
            )
            # run_python(PLOT_GROUND_TRUTH_SCRIPT)
            
            #----------------------------------------------------------------------------------------------------------

            print("\n[STEP 5] Updating Reference Max SNR from Ground Truth CSV...")
            
            
            print("----------------------------------------------------------------------------------------------------------")
            
            csv_path = os.path.join(os.environ["GROUND_TRUTH_PATH"], "forward_max_snr_per_angle.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df.columns = [c.lower().strip() for c in df.columns]
                angle_col = [col for col in df.columns if 'angle' in col][0]
                snr_col = [col for col in df.columns if 'snr' in col][0]
                filtered = df[(df[angle_col] >= -30) & (df[angle_col] <= 30)]
                avg_snr = filtered[snr_col].mean()
                print(f"[INFO] Reference Max SNR (boresight ±30°) = {avg_snr:.2f} dB")
                update_reference_max_snr(avg_snr)
            else:
                print(f"[WARNING] Ground truth CSV not found at {csv_path}. Skipping SNR update.")
                
            print("----------------------------------------------------------------------------------------------------------")

            print("\n[STEP 6] Running Adaptive Beamforming Experiments...")
            
            print("----------------------------------------------------------------------------------------------------------")
            
            
            os.environ['PLOT_MODE'] = '4'
          
            print(f"\n[INFO] Running Adaptive Beamforming for SNR={snr_quantile}, RotorSpeed={rotor_speed}")
            test_number = f"off_OAKD_MAVG{experiment_counter}"
            run_python(ONLINE_SCRIPT, ["--test_number", test_number])
            experiment_counter += 1
        
    #----------------------------------------------------------------------------------------------------------

# === EXECUTION ===
if __name__ == "__main__":
    main()
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n[LOG] Automatic evaluation pipeline completed at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(f"[LOG] Total execution time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
