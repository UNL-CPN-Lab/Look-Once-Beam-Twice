"""Fixed-beam SNR collection for outdoor deployments (no rotor).

Outdoor variant of `fixed_beam_snr_collection.py` — pins TX and RX to a
single beam pair and records SNR continuously while the UE moves along the
test path (real vehicle motion, no servo). Used to capture ground-truth
power-vs-position traces.

Run: `python3 outdoor_fixed_beam.py` (from this folder).

Author: Apala Pramanik
"""

import os
import time
import datetime
import numpy as np
import threading
import pexpect
import sys
import json
import uhd
import csv
from configurations.utils import *
from configurations.config import *
import uhd_conf as ucf
import Sivers_Plot_Tx_Rx_Heatmaps as heatmap
import shutil

## Constants
child_rx = None
child_tx = None
noise_power_avg = 0
noise_power_list = []


# Global constants
TX_BEAM = 32
RX_BEAM = 32
STOP_FLAG = threading.Event()


# RX thread: streams IQ from the USRP at a fixed beam pair while the UE
# vehicle moves along the test path; writes per-iteration SNR + raw IQ.
def rx_fixed_beam(usrp, rx_streamer, start_time, child_rx, child_tx, experiment_dir, SAMPLE_SIZE):
    metadata = uhd.types.RXMetadata()
    csv_filename = os.path.join(experiment_dir, "snr_data.csv")
    timestamp_csv_filename = os.path.join(experiment_dir, "iteration_timestamps.csv")
    snr_list = []
    iteration_timestamps = []

    recv_signal_dir = os.path.join(experiment_dir, "recv_signal")
    os.makedirs(recv_signal_dir, exist_ok=True)

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = False
    stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
    rx_streamer.issue_stream_cmd(stream_cmd)

    print(f"\nSetting Tx Beam: {TX_BEAM}")
    run_interactive_command(child_tx, f"eder.tx.set_beam({TX_BEAM})")
    print(f"\nSetting Rx Beam: {RX_BEAM}")
    run_interactive_command(child_rx, f"eder.rx.set_beam({RX_BEAM})")

    print(f"\nReceiving at Tx={TX_BEAM}, Rx={RX_BEAM}. Press Ctrl+C to stop...\n")

    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)

    try:
        iter_num = 0
        while True:
            iter_start = time.time()
            rx_streamer.recv(recv_signal, metadata)
            iter_end = time.time()

            # Save signal
            filename = os.path.join(recv_signal_dir, f'tx{TX_BEAM}_rx{RX_BEAM}_iter{iter_num}.dat')
            recv_signal.astype(np.complex64).tofile(filename)

            # Power/SNR
            IQ_power_dBm, avg_power_dBm, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, noise_power_avg = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)

            snr_list.append([SAMPLE_SIZE, TX_BEAM, RX_BEAM, snr_db])
            iteration_timestamps.append([TX_BEAM, RX_BEAM, iter_num, iter_start, iter_end, iter_end - iter_start])

            print(f"[{iter_num:03d}] SNR = {snr_db:.2f} dB | Noise = {noise_power_avg:.2f} dBm | Duration = {iter_end - iter_start:.3f}s")

            iter_num += 1

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping reception gracefully...")

    finally:
        rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))

        # Write CSVs
        print("Writing data to CSV files...")
        with open(csv_filename, 'a', newline='') as f:
            csv.writer(f).writerows(snr_list)
        with open(timestamp_csv_filename, 'a', newline='') as f:
            csv.writer(f).writerows(iteration_timestamps)

        print("Rx process complete. Data stored in:", experiment_dir)



# Entry-point: initialise Sivers TX/RX via pexpect, kick off the RX thread,
# and wait for it to drain.
def run_fixed_beam_experiment(tx_streamer, rx_streamer, experiment_name, TX_BEAM, experiment_dir):


    # Start TX
    print("Initializing TX...")
    child_tx = pexpect.spawn('./start.sh <SIVERS_TX_SERIAL>')
    logfile_tx_path = os.path.join(experiment_dir, "logfile_tx.txt")
    logfile_tx = open(logfile_tx_path, "wb")
    child_tx.logfile = logfile_tx
    child_tx.expect('\[sudo\] password for .+: ')
    child_tx.sendline('<SUDO_PASSWORD>')
    print('Sent password.')
    run_interactive_command(child_tx, 'eder.init()')
    run_interactive_command(child_tx, 'eder.tx_setup(60.48e9)')
    run_interactive_command(child_tx, 'eder.tx_enable()')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_gain\',0x03)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_iq_gain\',0x88)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bfrf_gain\',0x88)')

    print("\nSivers Transmitter device started !!!\n")

    # Start RX
    print("Initializing RX...")
    child_rx = pexpect.spawn('./start.sh <SIVERS_RX_SERIAL>')
    logfile_rx_path = os.path.join(experiment_dir, "logfile_rx.txt")
    logfile_rx = open(logfile_rx_path, "wb")
    child_rx.logfile = logfile_rx
    child_rx.expect('\[sudo\] password for .+: ')
    child_rx.sendline('<SUDO_PASSWORD>')
    print('Sent password.')
    run_interactive_command(child_rx, 'eder.init()')
    run_interactive_command(child_rx, 'eder.rx_setup(60.48e9)')
    run_interactive_command(child_rx, 'eder.rx_enable()')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bfrf\',0xF)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb1\',0x88)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb2\',0x88)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb3\',0x88)')
    
    start_time = usrp.get_time_now().get_real_secs() + INIT_DELAY
    
    # Start RX thread
    rx_process = threading.Thread(
        target=rx_fixed_beam, args=(usrp, rx_streamer, start_time, child_rx, child_tx, experiment_dir, SAMPLE_SIZE))
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


if __name__ == "__main__":
    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)  # Received signal buffer
    
    date = datetime.datetime.today().strftime('%b%d').lower()
    exp_name = f"fixed_beam_{date}_tx32_rx32"
    main_dir = "<DATA_ROOT>/mmWaveSSD/Schorr_Center/Fixed_Beam_Experiment"
    experiment_dir = os.path.join(main_dir, exp_name)
    os.makedirs(experiment_dir, exist_ok=True)
   

    # Set up logging
    log_filename = os.path.join(main_dir, "experiment_log.txt")
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
    experiment_dir = os.path.join(main_dir, experiment_name)
    os.makedirs(experiment_dir, exist_ok=True)  # Ensure experiment directory exists

    # Create metadata for the experiment
    experiment_metadata = {
        "experiment_name": experiment_name,
        "experiment_directory": experiment_dir,
        "sweep_type": "Fixed Sweep",
        "tx_beam": TX_BEAM ,
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
    
    #Getting the USRP ready
    tx_streamer, rx_streamer, usrp = ucf.uhd_builder(args="", gain=76, rate=1e6)

    time.sleep(1)
    start_time = time.time()


    run_fixed_beam_experiment(tx_streamer, rx_streamer, experiment_name, TX_BEAM, experiment_dir)
    
    print("\nTotal time to experiment: ", time.time() - start_time)

    '''
    This will plot the heatmap and return the best beam in dBm
    '''
    heatmap.plotheatmap(experiment_dir,SAMPLE_SIZE)

    # Close log file
    sys.stdout = sys.__stdout__  # Reset stdout
    sys.stderr = sys.__stderr__  # Reset stderr
    log_file.close()

    # Copy log file to the experiment folder
    shutil.copy(log_filename, os.path.join(experiment_dir, "experiment_log.txt"))

    print(f"Experiment log saved at: {log_filename}")
