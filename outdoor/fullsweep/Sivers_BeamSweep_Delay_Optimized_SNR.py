import sys
import os

# This file lives in outdoor/fullsweep/. Add outdoor/ so the local
# `import uhd_conf as ucf` finds outdoor/uhd_conf.py, and add the repo root so
# `from configurations...` resolves (two levels up).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import datetime
import time
import threading
import numpy as np
import uhd
import multiprocessing as mp
import pexpect
import shutil
import uhd_conf as ucf
import csv

import Sivers_Plot_Tx_Rx_Heatmaps as heatmap


from configurations.utils import *
from configurations.config import *


## Constants
child_rx = None
child_tx = None
noise_power_avg = 0
noise_power_list = []


'''
Rx Process: Receives signals, calculates SNR, and tracks max/min SNR
'''

def rx_host(usrp, rx_streamer, start_time, child_rx, sweep_mode, experiment_dir, SAMPLE_SIZE, Txsock=None):
    metadata = uhd.types.RXMetadata()
    csv_filename = os.path.join(experiment_dir, "snr_data.csv")
    timestamp_csv_filename = os.path.join(experiment_dir, "iteration_timestamps.csv")
    snr_list = []
    iteration_timestamps = []

    # Directory to save individual iteration files
    recv_signal_dir = os.path.join(experiment_dir, "recv_signal")
    os.makedirs(recv_signal_dir, exist_ok=True)

    # Prepare and issue the stream command
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = False
    stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
    rx_streamer.issue_stream_cmd(stream_cmd)

    num_tx_beams = 64 if sweep_mode == 'F' else 1

    # Master buffer to hold final iteration data for all Tx and Rx beams
    master_buffer = np.zeros((num_tx_beams, 64, SAMPLE_SIZE), dtype=np.complex64)

    # List to accumulate all iteration data for file saving later.
    recv_files_data = []

    tx_beam_range = range(64) if sweep_mode == 'F' else [tx_beam]

    for tx_idx, tx_beam in enumerate(tx_beam_range):
        tic = time.time()

        print(f"\nSetting Tx Beam: {tx_beam}")

        if Txsock:
                try:
                    Txsock.sendall(f"SET_TX_BEAM:{tx_beam}".encode())
                    print(f"[SOCKET] Sent SET_TX_BEAM:{tx_beam} to TX server.")
                except Exception as e:
                    print(f"[SOCKET ERROR] Failed to send beam index {tx_beam}: {e}")

        tx_buffer = np.zeros((64, SAMPLE_SIZE), dtype=np.complex64)

        for rx_beam in range(64):
            rx_command = f'eder.rx.set_beam({rx_beam})'
            run_interactive_command(child_rx, rx_command)

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            # Avhi - removed the beam stabilization loop
            for iter_num in range(30):
                iter_start_time = time.time()  # Capture iteration start time
                
                rx_streamer.recv(recv_signal, metadata)
                
                iter_end_time = time.time()  # Capture iteration end time
                
                # Store the timestamp data
                iteration_timestamps.append([tx_beam, rx_beam, iter_num, iter_start_time, iter_end_time, iter_end_time - iter_start_time])

                # Store a copy of the received data along with its identifiers
                recv_files_data.append((tx_beam, rx_beam, iter_num, np.copy(recv_signal)))

            # Power and Noise calculation
            IQ_power_dBm, avg_power_dBm, max_power_dBm = calculate_power_metrics(recv_signal) 
            # snr_db, noise_power_avg = calculate_snr_with_sliding_correlation(IQ_power_dBm, lag=10, window_size=100,  noise_power_list=noise_power_list)
            snr_db, noise_power_avg = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size = PADDING,noise_power_list=noise_power_list)
            
            # Append SNR data
            snr_list.append([SAMPLE_SIZE, tx_beam, rx_beam, snr_db])

            print(f"SNR for TX - {tx_beam}, Rx-{rx_beam}, SNR - {snr_db:.2f} dB, Noise Power: {noise_power_avg:.2f} dBm")

            # Store the final iteration’s data in the Tx buffer
            tx_buffer[rx_beam, :] = recv_signal

        # Save the current Tx beam’s data into the master buffer
        master_buffer[tx_idx, :, :] = tx_buffer

        toc = time.time()
        print(f'Data collection duration for Tx {tx_beam}: {toc - tic:.2f} seconds')
   
    
    
    # Write the aggregated SNR data to a CSV file
    print("\nWriting SNR data to CSV file...")
    with open(csv_filename, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows(snr_list)

    # Write the iteration timestamps to a CSV file
    print("\nWriting iteration timestamps to CSV file...")
    with open(timestamp_csv_filename, mode='a', newline='') as timestamp_file:
        csv_writer = csv.writer(timestamp_file)
        csv_writer.writerow(["Tx_Beam", "Rx_Beam", "Iteration", "Start_Time", "End_Time", "Duration"])
        csv_writer.writerows(iteration_timestamps)

    # Write the aggregated master buffer data (final iteration for each beam pair) to files
    print("\nWriting master buffer Tx beam data to files...")
    for tx_idx, tx_beam in enumerate(tx_beam_range):
        filename = os.path.join(experiment_dir, f'tx_beam_{tx_beam}.dat')
        master_buffer[tx_idx, :, :].tofile(filename)
        print(f'Saved {filename}')

    rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
    print("\nRx process complete. Data stored in:", experiment_dir)


    
def main(tx_streamer, rx_streamer, sweep_mode, experiment_name, tx_beam, experiment_dir):


    print(f"\nStarting Experiment: {experiment_name}")
    print(f"Mode: {'Full Sweep' if sweep_mode == 'F' else f'Single Sweep (Tx Beam {tx_beam})'}\n")
    
    # === Step 1: Create socket to remote TX server ===
    Txsock = create_socket_connection(ip='<TX_HOST_IP>', port=5002)
    if not Txsock:
        print(" Failed to connect to TX socket. Exiting.")
        return False
    
    # === Step 2: Tell TX server to begin Sivers setup ===
    try:
        Txsock.sendall(b"START_TX")
        print("[SOCKET] Sent START_TX to TX server.")

        # === Wait for ACK from TX server ===
        ack = Txsock.recv(1024).decode().strip()
        if ack == "TX_READY":
            print("[SOCKET] Received TX_READY from TX server.")
        else:
            print(f"[SOCKET ERROR] Unexpected ACK: {ack}")
            return False
    except Exception as e:
        print(f"[SOCKET ERROR] Failed during START_TX handshake: {e}")
        return False

    

    '''
    Start the Sivers Receiver
    '''
    print("Sivers Receiver Initializing .....")
    # Spawn the interactive command
    child_rx = pexpect.spawn('./start.sh <SIVERS_RX_SERIAL>')

    # Open a log file inside the experiment directory
    logfile_rx_path = os.path.join(experiment_dir, "logfile_rx.txt")
    logfile_rx = open(logfile_rx_path, "wb")

    # Set the logfile attribute of the child object
    child_rx.logfile = logfile_rx

    # Wait for the password prompt, and send the password
    child_rx.expect('\[sudo\] password for .+: ')
    child_rx.sendline('<SUDO_PASSWORD>')
    print('Sent password.')

    # Enable the receiver
    run_interactive_command(child_rx, 'eder.init()')
    run_interactive_command(child_rx, 'eder.rx_setup(60.48e9)')
    run_interactive_command(child_rx, 'eder.rx_enable()')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bfrf\',0xF)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb1\',0x99)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb2\',0x99)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb3\',0x99)')


    start_time = usrp.get_time_now().get_real_secs() + INIT_DELAY

    # Start RX thread
    rx_process = threading.Thread(
        target=rx_host, args=(usrp, rx_streamer, start_time, child_rx, sweep_mode,  experiment_dir, SAMPLE_SIZE, Txsock)
    )

    rx_process.start()

    print("Sending signal to stop! ........ ")

    rx_process.join()

    print('Data Receiving Done ..... ')
    


    # Disable Sivers devices
    print("\nDisabling the Sivers receiver and transmitter.....")
    run_interactive_command(child_rx, 'eder.rx_disable()')
 

    # Close the log files
    logfile_rx.close()
    print('Log files closed.')

    return True

'''
Uncomment to run the script as a standalone program
'''
if __name__ == "__main__":
    # Define the sample sizes to iterate over and store the signal
  
    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)  # Received signal buffer

    # Ensure the sweepData directory exists
    main_directory = "<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/sweepData"
    os.makedirs(main_directory, exist_ok=True)

    # Set up logging
    log_filename = os.path.join(main_directory, "experiment_log.txt")
    log_file = open(log_filename, "w")

    # Redirect stdout and stderr to log file (while still printing to terminal)
    class Logger(object):
        def __init__(self, file):
            self.terminal = sys.stdout  # Keep original stdout
            self.log = file

        def write(self, message):
            self.terminal.write(message)  # Print to terminal
            self.log.write(message)  # Save to log file

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(log_file)
    sys.stderr = Logger(log_file)  # Capture errors as well

    print(f"\n=== Experiment Started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")


    
    # Ask the user for sweep type
    while True:
        print("\nSelect Sweep Mode:")
        print("1. Full Sweep")
        print("2. Single Sweep")
        sweep_mode = input("Enter 1 for Full Sweep or 2 for Single Sweep: ").strip()
        
        if sweep_mode in ['1', '2']:
            sweep_mode = 'F' if sweep_mode == '1' else 'S'
            break
        print("Invalid input! Please enter 1 or 2.")

  

    # === Collect user inputs ===
    location = input("Enter the location (e.g., nh; kh): ").strip()

    # Automatically get date in 'apr3' format
    today = datetime.datetime.today()
    date = today.strftime("%b").lower() + str(today.day)

    gain = input("Enter the gain setting (e.g., 15db): ").strip()
    distance = input("Enter the distance (e.g., 10m): ").strip()
    test_number = input("Enter the test number (e.g., t1): ").strip()

    # === Format directory name ===
    experiment_name = f"{location}_{date}_gain{gain}_{distance}_{test_number}"



    # Define the experiment directory inside sweepData
    experiment_dir = os.path.join(main_directory, experiment_name)
    os.makedirs(experiment_dir, exist_ok=True)  # Ensure experiment directory exists

    # If single sweep, ask for Tx beam
    tx_beam = None
    if sweep_mode == 'S':
        while True:
            try:
                tx_beam = int(input("Enter the Tx beam number (0-63) for the single sweep: ").strip())
                if 0 <= tx_beam <= 63:
                    break
                else:
                    print("Invalid beam number! Please enter a value between 0 and 63.")
            except ValueError:
                print("Invalid input! Please enter an integer between 0 and 63.")

    

    # Create metadata for the experiment
    experiment_metadata = {
        "experiment_name": experiment_name,
        "experiment_directory": experiment_dir,
        "sweep_type": "Full Sweep" if sweep_mode == 'F' else "Single Sweep",
        "tx_beam": tx_beam if sweep_mode == 'S' else "N/A",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "gain": gain,
        "distance": distance,
        "test_number": test_number,
        "sample_size": SAMPLE_SIZE,
        "padding": PADDING
    }

    # Save metadata to a JSON file inside the experiment directory
    metadata_filename = os.path.join(experiment_dir, "experiment_metadata.json")
    with open(metadata_filename, "w") as metadata_file:
        json.dump(experiment_metadata, metadata_file, indent=4)

    print(f"\nExperiment metadata saved to {metadata_filename}")

    # Getting the USRP ready
    tx_streamer, rx_streamer, usrp = ucf.uhd_builder(args="", gain=76, rate=1e6)

    time.sleep(1)
    start_time = time.time()

    # Launching the Sivers and the communication process
    main(tx_streamer, rx_streamer, sweep_mode, experiment_name, tx_beam, experiment_dir)

    print("\nTotal time to experiment: ", time.time() - start_time)

    '''
    This will plot the heatmap and return the best beam in dBm
    '''
    heatmap.plotheatmap(experiment_dir,SAMPLE_SIZE)
    
    summary_csv_path = os.path.join(main_directory, "experiment_snr_summary.csv")
    append_experiment_summary(experiment_dir, experiment_name, summary_csv_path)


    # Close log file
    sys.stdout = sys.__stdout__  # Reset stdout
    sys.stderr = sys.__stderr__  # Reset stderr
    log_file.close()

    # Copy log file to the experiment folder
    shutil.copy(log_filename, os.path.join(experiment_dir, "experiment_log.txt"))

    print(f"Experiment log saved at: {log_filename}")



