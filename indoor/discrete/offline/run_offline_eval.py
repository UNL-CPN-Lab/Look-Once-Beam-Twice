import subprocess
import itertools
import os

# === CONFIGURATION FILE PATH ===
CONFIG_PATH = "../configurations/config.py"  # Path to the main configuration file

# === SCRIPTS TO RUN ===
SCRIPTS = [
    "offline_main_basic.py",           # Basic offline beamforming script
    "offline_main_corrective_mavg.py" , # offline script with moving average correction
    "offline_main_corrective_ml.py"   # offline script with MLP correction      
]

# === PARAMETERS TO SWEEP ===
ROTOR_SPEEDS = [5, 2, 1]              # Rotor speeds (in sec/deg) to evaluate
SNR_FACTORS = [0.5, 0.6, 0.7]         # SNR threshold factors to evaluate

def update_config(rotor_speed, snr_factor):
    """
    Modify the config.py file to update ROTOR_SPEED and SNR_THRESHOLD_FACTOR.

    Parameters:
    - rotor_speed (int): New rotor speed to be written.
    - snr_factor (float): New SNR threshold factor to be written.
    """
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()

    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("SNR_THRESHOLD_FACTOR"):
                f.write(f"SNR_THRESHOLD_FACTOR = {snr_factor}\n")
            elif line.strip().startswith("ROTOR_SPEED"):
                f.write(f"ROTOR_SPEED = {rotor_speed}  # Rotor speed in sec/deg\n")
            else:
                f.write(line)

def run_script(script_name, test_number):
    """
    Run a Python script with the provided test number.

    Parameters:
    - script_name (str): Name of the script to run.
    - test_number (str): Identifier for the test case.
    """
    print(f"\n Running: {script_name} with test_number={test_number}")
    try:
        subprocess.run(["python3", script_name, "--test_number", test_number], check=True)
        print(f"Completed: {script_name} ({test_number})")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")

def main():
    """
    Main function to iterate over all rotor speed and SNR threshold combinations.
    For each combination, it updates the config and runs each script with a test number.
    """
    experiment_counter = 1  # Used to label each experiment run

    # Iterate over all combinations of rotor speeds and SNR factors
    for rotor_speed, snr_factor in itertools.product(ROTOR_SPEEDS, SNR_FACTORS):
        print(f"\n Setting config: ROTOR_SPEED={rotor_speed}, SNR_THRESHOLD_FACTOR={snr_factor}")
        update_config(rotor_speed, snr_factor)

        # Run each script with the current config
        for script in SCRIPTS:
            test_number = f"t{experiment_counter}"
            run_script(script, test_number)
            experiment_counter += 1

# === ENTRY POINT ===
if __name__ == "__main__":
    main()
