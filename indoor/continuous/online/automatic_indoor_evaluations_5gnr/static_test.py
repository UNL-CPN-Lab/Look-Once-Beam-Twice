# Standard Libraries
import argparse
import json
import datetime
import time
import threading
import csv
import sys
import os
import shutil
import cv2
import serial
import subprocess
import pandas as pd


# Third-party Libraries
# from indoor.continuous.usrp_control import initialize_usrp
import numpy as np
import uhd  # USRP hardware driver
import matplotlib.pyplot as plt
import multiprocessing as mp
import pexpect
from sivers_control import initialize_sivers  # Import Sivers initialization function



# Custom Modules (Ensure these are in the Python path)
import uhd_conf as ucf  # Import the USRP configuration
# from controlrotor import move_servo_to_angle  # Import servo control function
from combined_continuous_discrete_rotor import send_discrete_command  # Import function to send commands to the servo


# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)

from configurations.config import *  # Import the configuration module
from configurations.utils import *


noise_power_avg = 0
noise_power_list = []



arduino = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(1)  # wait for Arduino reset


def rx_host(usrp, rx_streamer, start_time, child_rx, child_tx, experiment_dir, SAMPLE_SiZE):
    metadata = uhd.types.RXMetadata()

    # Prepare and issue the stream command
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = False
    stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
    rx_streamer.issue_stream_cmd(stream_cmd)


    currentrotorangle = 0  # Start at 0°
    
    # Sweep from 0 to 180
    for target_angle in range(45, 135, 1):   # forward rotation

        full1_sweepstart = time.time()
    

        # Move the servo **while recording continues**
        send_discrete_command(arduino, target_angle)
        time.sleep(2)  # Allow stabilization
        currentrotorangle = target_angle  # Track the current position
       
        max_snr_db_RX = -np.inf
        max_snr_db_TX = -np.inf
        best_rx_beam = None
        best_tx_beam = None
    

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S") + f"_{now.microsecond // 1000:03d}"
        start_beam_time = time.time()

        run_interactive_command(child_tx, f'eder.tx.set_beam({0})')
        
        for rx_beam in range(1,64):
            
            run_interactive_command(child_rx, f'eder.rx.set_beam({rx_beam})')

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(15):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, _ = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)
            
            if snr_db > max_snr_db_RX:
                max_snr_db_RX = snr_db
                best_rx_beam = rx_beam
                print(f"[NR_SWEEP] RX Beam {rx_beam}: SNR = {snr_db:.2f} dB")
            print(f"[NR_SWEEP] Best RX Beam {best_rx_beam}: SNR = {max_snr_db_RX:.2f} dB")
        
        run_interactive_command(child_rx, f'eder.rx.set_beam({best_rx_beam})')
        
        for tx_beam in range(1,64):
            run_interactive_command(child_tx, f'eder.tx.set_beam({tx_beam})')
    
            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, _ = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)
            
            if snr_db > max_snr_db_TX:
                max_snr_db_TX = snr_db
                best_tx_beam = tx_beam
                print(f"[NR_SWEEP] TX Beam {tx_beam}: SNR = {snr_db:.2f} dB")
            print(f"[NR_SWEEP] Best TX Beam {best_tx_beam}: SNR = {max_snr_db_TX:.2f} dB")
       
        beam_sweep_time = time.time() - start_beam_time
        # Log result
        csv_filename = f"{experiment_dir}/results_{experiment_name}.csv"
        csv_data = {
            "Timestamp": [timestamp],
            "Boresight": currentrotorangle-90,
            "Rx Beam Index": [best_rx_beam],
            "Rx Beam Angle": [RX_BEAM_ANGLES[best_rx_beam]],
            "Tx Beam Index": [best_tx_beam],
            "Tx Beam Angle": [TX_BEAM_ANGLES[best_tx_beam]],
            "SNR (dB)": [max_snr_db_TX],
            "Beam Sweep Time (s)": [beam_sweep_time]
        }
        df = pd.DataFrame(csv_data)
        if not os.path.exists(csv_filename):
            df.to_csv(csv_filename, index=False)
        else:
            df.to_csv(csv_filename, mode='a', header=False, index=False)  # Do not write header again


        print()
        print(f"[NR_SWEEP] Logged data to {csv_filename}; Current Rotor Angle: {currentrotorangle}; SNR: {max_snr_db_TX:.2f} dB; Rx Beam: {best_rx_beam} ({RX_BEAM_ANGLES[best_rx_beam]}°); Tx Beam: {best_tx_beam} ({TX_BEAM_ANGLES[best_tx_beam]}°);")
        print()


    rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
    print(f"\nRx process complete. Data stored in: {experiment_dir}")


def main(tx_streamer, rx_streamer, usrp, experiment_name, experiment_dir):

    #Initialize Sivers
    child_tx, child_rx, logfile_tx,  logfile_rx, _ = initialize_sivers(experiment_dir)

    start_time = usrp.get_time_now().get_real_secs() + INIT_DELAY

    # Start RX thread
    rx_process = threading.Thread(
        target=rx_host, args=(usrp, rx_streamer, start_time, child_rx, child_tx, experiment_dir, SAMPLE_SIZE)
    )

    rx_process.start()

    print("Sending signal to stop! ........ ")

    rx_process.join()

    print('Data Receiving Done ..... ')
    
    # Disable Sivers devices
    print("\nDisabling the Sivers receiver and transmitter.....")
    run_interactive_command(child_rx, 'eder.rx_disable()')
    run_interactive_command(child_tx, 'eder.tx_disable()')

    # Close the log files
    logfile_rx.close()
    logfile_tx.close()
    print('Log files closed.')

    return True



class Logger:
    """Logger class to write stdout and stderr to both terminal and a log file with timestamps."""
    
    def __init__(self, file):
        self.terminal = sys.stdout  # Keep original stdout
        self.log = file

    def write(self, message):
        if message.strip():  # Avoid logging unnecessary empty lines
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            formatted_message = f"{timestamp}{message.rstrip()}\n" 
            self.terminal.write(formatted_message)  # Print to terminal
            self.log.write(formatted_message)  # Save to log file

    def flush(self):
        self.terminal.flush()
        self.log.flush()

if __name__ == "__main__":
    # Define experiment parameters
   
   
    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)  # Received signal buffer

    # Initialize Directories
    main_directory = "Adaptive_Beamforming_SC"
    os.makedirs(main_directory, exist_ok=True)

  
 
    # Automatically get date in 'apr3' format
    today = datetime.datetime.today()
    date = today.strftime("%b").lower() + str(today.day)


    parser = argparse.ArgumentParser()
    parser.add_argument("--test_number", help="Test number (e.g., t1)")
    args = parser.parse_args()
    
    test_number = args.test_number if args.test_number else input("Enter the test number (e.g., t1): ").strip()

    # === Format directory name ===
    experiment_name = f"{location}_{date}_gain{gain}_{distance}_{test_number}"


    # experiment_name = input("Enter the experiment name: ").strip()
    experiment_dir = os.path.join(main_directory, experiment_name)
    print(f"\n[INFO] Experiment directory: {experiment_dir}")
    os.makedirs(experiment_dir, exist_ok=True)

    metadata_content = {
        "experiment_name": experiment_name,
        "experiment_directory": experiment_dir,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "gain": gain,
        "distance": distance,
        "test_number": test_number,
        "sample_size": SAMPLE_SIZE,
        "padding": PADDING,
        "rotor_speed": f"{ROTOR_SPEED}deg/sec",
        "Threshold" : f"{SNR_THRESHOLD} dB",
        "Threshold Quantile": f"{SNR_QUANTILE}",
        "Algorithm": "5G NR Adaptive Beamforming",
        
       
    }

    setup_logging(experiment_dir)
    save_experiment_metadata(experiment_dir, experiment_name,metadata_content)
    



    # Setup logging
    log_filename = os.path.join(experiment_dir, "experiment_log.txt")
    with open(log_filename, "w") as log_file:
        sys.stdout = Logger(log_file)
        sys.stderr = Logger(log_file)  # Capture errors as well

        print(f"\n=== Experiment Started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
         # === Format directory name ===
        experiment_name = f"{location}_{date}_gain{gain}_{distance}_{test_number}"
        


        # Initialize USRP
        tx_streamer, rx_streamer, usrp = ucf.uhd_builder(args="", gain=76, rate=1e6)
        time.sleep(1)

        # Start experiment
        start_time = time.time()
        main(tx_streamer, rx_streamer, usrp, experiment_name, experiment_dir)

        print(f"\nTotal experiment duration: {time.time() - start_time:.2f} seconds")
        



        # Reset stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # Copy log file to experiment folder
        shutil.copy(log_filename, os.path.join(experiment_dir, "experiment_log.txt"))
        print(f"Experiment log saved at: {os.path.join(experiment_dir, 'experiment_log.txt')}")
