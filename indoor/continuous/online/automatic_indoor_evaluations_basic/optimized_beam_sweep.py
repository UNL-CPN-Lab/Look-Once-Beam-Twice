# Standard Libraries
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

# Third-party Libraries
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


child_rx = None
child_tx = None

noise_power_avg = 0
noise_power_list = []



arduino = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(1)  # wait for Arduino reset


def rx_host(usrp, rx_streamer, start_time, child_rx, child_tx, experiment_dir, sample_size):
    metadata = uhd.types.RXMetadata()

    # Prepare and issue the stream command
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = False
    stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
    rx_streamer.issue_stream_cmd(stream_cmd)


    currentrotorangle = 0  # Start at 0°
    
    # Sweep from 0 to 180
    for target_angle in range(25, 166, 5):   # forward rotation

        full1_sweepstart = time.time()
        angle_dir = os.path.join(experiment_dir, f"angle_{target_angle-90}")
        os.makedirs(angle_dir, exist_ok=True)

        csv_filename = os.path.join(angle_dir, "snr_data.csv")
      

        # Move the servo **while recording continues**
        send_discrete_command(arduino, target_angle)
        time.sleep(5)  # Allow stabilization
        currentrotorangle = target_angle  # Track the current position
        
        

        tx_beam_center = 32
        tx_beam_range = range(max(1, tx_beam_center - 5), min(64, tx_beam_center + 6))
        
        rx_target_angle = -(currentrotorangle - 90)
        
        if rx_target_angle == 0:
            rx_beam_center = 32
        else:
            rx_beam_center = np.argmin(np.abs(np.array(RX_BEAM_ANGLES) - rx_target_angle))



        rx_beam_range = range(max(1, rx_beam_center - 10), min(64, rx_beam_center + 11))
                              
        master_buffer = np.zeros((len(tx_beam_range), len(rx_beam_range), sample_size), dtype=np.complex64)

        snr_list = []

        for tx_idx, tx_beam in enumerate(tx_beam_range):

            tic = time.time()
            tx_command = f'eder.tx.set_beam({tx_beam})'
            print(f"\nSetting Tx Beam: {tx_beam}")
            run_interactive_command(child_tx, tx_command)

            tx_buffer = np.zeros((len(rx_beam_range), sample_size), dtype=np.complex64)
            

            for rx_idx, rx_beam in enumerate(rx_beam_range):
                rx_command = f'eder.rx.set_beam({rx_beam})'
                run_interactive_command(child_rx, rx_command)

                recv_signal = np.zeros(sample_size, dtype=np.complex64)

                for iter_num in range(30):
                    rx_streamer.recv(recv_signal, metadata)

                rx_streamer.recv(recv_signal, metadata)

                # Power and Noise calculation
                IQ_power_dBm, avg_power_dBm, max_power_dBm = calculate_power_metrics(recv_signal) 
                snr_db ,noise_power_avg = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=padding,noise_power_list=noise_power_list)
                
                
                # Append SNR data
                tx_angle = TX_BEAM_ANGLES[tx_beam]
                rx_angle = RX_BEAM_ANGLES[rx_beam]
                
                snr_list.append([sample_size, tx_beam, tx_angle, rx_beam, rx_angle, snr_db])

                print(f"SNR for TX:{tx_angle}, Rx:{rx_angle},Power:{max_power_dBm} ,SNR: {snr_db:.2f} dB, Noise Power: {noise_power_avg:.2f} dBm")

                # Store the final iteration’s data in the Tx buffer
                tx_buffer[rx_idx, :] = recv_signal


            # Save the current Tx beam’s data into the master buffer
            master_buffer[tx_idx, :, :] = tx_buffer

            toc = time.time()
            print(f'Data collection duration for Tx {tx_beam}: {toc - tic:.2f} seconds')

        print("\nWriting SNR data to CSV file...")
        with open(csv_filename, mode='a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Sample size", "Tx Beam Index", "Tx Beam Angle", "Rx Beam Index", "Rx Beam Angle", "SNR (dB)"])
            csv_writer.writerows(snr_list)

        print("\nWriting master buffer Tx beam data to files...")
        for tx_idx, tx_beam in enumerate(tx_beam_range):
            filename = os.path.join(angle_dir, f'tx_beam_{tx_beam}.dat')
            master_buffer[tx_idx, :, :].tofile(filename)
            print(f'Saved {filename}')

        full1_sweepend = time.time()
        print(f"\nTotal Full Sweep time at Rotor Angle {target_angle}°: {full1_sweepend - full1_sweepstart:.2f} seconds")
 

    rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
    print(f"\nRx process complete. Data stored in: {experiment_dir}")



    
def main(tx_streamer, rx_streamer,experiment_name,  experiment_dir):
    print(f"\nStarting Experiment: {experiment_name}")
   
    #Initialize Sivers
    child_tx, child_rx, logfile_tx,  logfile_rx, _ = initialize_sivers(experiment_dir)

    start_time = usrp.get_time_now().get_real_secs() + INIT_DELAY

    # Start RX thread
    rx_process = threading.Thread(
        target=rx_host, args=(usrp, rx_streamer, start_time, child_rx, child_tx, experiment_dir, sample_size)
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
    sample_size = 2000
    padding = 200
    INIT_DELAY = 0.08  # Initial delay before transmission
    recv_signal = np.zeros(sample_size, dtype=np.complex64)  # Received signal buffer

    # Define main directory for data storage
    BASE_DIR = "<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/gain13db"
    os.makedirs(BASE_DIR, exist_ok=True)

    # Setup logging
    log_filename = os.path.join(BASE_DIR, "experiment_log.txt")
    with open(log_filename, "w") as log_file:
        sys.stdout = Logger(log_file)
        sys.stderr = Logger(log_file)  # Capture errors as well

        print(f"\n=== Experiment Started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
         # === Format directory name ===
        experiment_name = GROUND_TRUTH_NAME
        
        # Create experiment directory
        experiment_dir = os.path.join(BASE_DIR, experiment_name)
        os.makedirs(experiment_dir, exist_ok=True)

        # Save experiment metadata
        metadata = {
            "experiment_name": experiment_name,
            "experiment_directory": experiment_dir,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        metadata_filename = os.path.join(experiment_dir, "experiment_metadata.json")
        with open(metadata_filename, "w") as metadata_file:
            json.dump(metadata, metadata_file, indent=4)

        print(f"\nExperiment metadata saved to {metadata_filename}")

        # Initialize USRP
        tx_streamer, rx_streamer, usrp = ucf.uhd_builder(args="", gain=76, rate=1e6)
        time.sleep(1)

        # Start experiment
        start_time = time.time()
        main(tx_streamer, rx_streamer, experiment_name, experiment_dir)

        print(f"\nTotal experiment duration: {time.time() - start_time:.2f} seconds")
        



        # Reset stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # Copy log file to experiment folder
        shutil.copy(log_filename, os.path.join(experiment_dir, "experiment_log.txt"))
        print(f"Experiment log saved at: {os.path.join(experiment_dir, 'experiment_log.txt')}")
