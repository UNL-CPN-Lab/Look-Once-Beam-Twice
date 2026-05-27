"""Project-wide utility functions used by every runner.

Grouped by concern:

- **Beam-book lookups** — `tx_angle_index`, `rx_angle_index`,
  `tx_angle_from_index`, `rx_angle_from_index` convert between Sivers beam
  index and physical angle (using the 64-entry `TX_BEAM_ANGLES` /
  `RX_BEAM_ANGLES` tables).
- **SNR computation** — `calculate_power_metrics` converts raw complex IQ to
  dBm; `calculate_snr_with_min_noise_window` and
  `calculate_snr_with_sliding_correlation` produce SNR estimates by two
  different noise-floor estimation methods.
- **Threshold conversion** — `snr_percent_db` converts a fractional SNR
  threshold (e.g. 0.9) to an absolute dB threshold relative to a captured
  max-SNR; `get_rotation_time_ms` converts a target sweep speed (°/s) to the
  `C:<ms>` value the Arduino rotor firmware expects.
- **Camera → beam-index** — `calculate_beam_indices` runs the pinhole
  projection from a YOLO bounding box to a quantized beam index pair.
- **Hardware / I/O** — `create_socket_connection`, `write_data`,
  `run_interactive_command` (pexpect shell helper for the Sivers Python
  shell).
- **Logging + experiment bookkeeping** — `setup_logging`,
  `save_experiment_metadata`, `log_timing`, `log_thread_timing`, the
  `timing_decorator` / `thread_timing_decorator` factories, and the
  per-thread logging helpers `setup_thread_logging` / `log_thread_event`.

All runners import everything via `from configurations.utils import *`.

Author: Apala Pramanik
"""

import os
import json
import datetime
import logging
import sys
import csv
import time
from functools import wraps
import numpy as np
from math import atan2, degrees
import pexpect
import threading
import pandas as pd
import socket
RX_BEAM_ANGLES = [
     0.0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9,
    -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2,  -8.7,  -7.3,  -5.8,  -4.4,  -2.9,  -1.5,
     0,     1.5,   2.9,   4.4,   5.8,   7.3,   8.7,  10.2,  11.6,  13.1,  14.5,
    16.0,  17.4,  18.9,  20.3,  21.8,  23.2,  24.7,  26.1,  27.6,  29.0,  30.5,
    31.9,  33.4,  34.8,  36.3,  37.7,  39.2,  40.6,  42.1,  43.5,  45.0
]
TX_BEAM_ANGLES = [
     0.0,  45.0,  43.5,  42.1,  40.6,  39.2,  37.7,  36.3,  34.8,  33.4,  31.9,
    30.5,  29.0,  27.6,  26.1,  24.7,  23.2,  21.8,  20.3,  18.9,  17.4,  16.0,
    14.5,  13.1,  11.6,  10.2,   8.7,   7.3,   5.8,   4.4,   2.9,   1.5,   0,
    -1.5,  -2.9,  -4.4,  -5.8,  -7.3,  -8.7, -10.2, -11.6, -13.1, -14.5, -16.0,
   -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9,
   -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1, -43.5, -45.0
]

def tx_angle_index(angle):
    """Return the beam index for a given Tx angle, resolving 0.0 to index 32 only."""
    if angle == 0:
        return 32
    return TX_BEAM_ANGLES.index(angle)

def rx_angle_index(angle):
    """Return the beam index for a given Rx angle, resolving 0.0 to index 32 only."""
    if angle == 0:
        return 32
    return RX_BEAM_ANGLES.index(angle)


def rx_angle_from_index(index):
    """Return the Rx angle corresponding to a given index."""
    if 0 <= index < len(RX_BEAM_ANGLES):
        return RX_BEAM_ANGLES[index]
    raise ValueError(f"Invalid RX beam index: {index}")

def tx_angle_from_index(index):
    """Return the Tx angle corresponding to a given index."""
    if 0 <= index < len(TX_BEAM_ANGLES):
        return TX_BEAM_ANGLES[index]
    raise ValueError(f"Invalid TX beam index: {index}")


def append_experiment_summary(experiment_dir, experiment_name, summary_csv_path):
    snr_csv_path = os.path.join(experiment_dir, "snr_data.csv")
    
    try:
        df = pd.read_csv(snr_csv_path, header=None, names=["SAMPLE_SIZE", "TX", "RX", "SNR_dB"])
        
        max_snr = df["SNR_dB"].max()
        percentiles = df["SNR_dB"].quantile([0.70, 0.80, 0.90, 0.95]).values
        try:
            center_snr = df[(df["TX"] == 32) & (df["RX"] == 32)]["SNR_dB"].values[0]
        except IndexError:
            center_snr = np.nan  # fallback if center not present
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary_data = [
            experiment_name, timestamp, round(max_snr, 2), round(center_snr, 2),
            round(percentiles[0], 2), round(percentiles[1], 2),
            round(percentiles[2], 2), round(percentiles[3], 2)
        ]
        
        header = [
            "Experiment", "Timestamp", "Max_SNR", "Center_SNR",
            "70th_Percentile", "80th_Percentile", "90th_Percentile", "95th_Percentile"
        ]
        
        file_exists = os.path.exists(summary_csv_path)
        with open(summary_csv_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(summary_data)
        
        print(f"Summary appended to {summary_csv_path}")
        
    except Exception as e:
        print(f"Error processing SNR summary: {e}")



def get_rotation_time_ms(speed_deg_per_sec):
    """
    Converts rotation speed (in deg/sec) to total time (in milliseconds) for a 180° sweep.

    Args:
        speed_deg_per_sec (float): Rotation speed in degrees per second.

    Returns:
        int: Total rotation time in milliseconds.
    """
    if speed_deg_per_sec <= 0:
        raise ValueError("Speed must be greater than 0 deg/sec.")
    
    total_time_sec = 180 / speed_deg_per_sec
    return int(total_time_sec * 1000)


def snr_percent_db(percentage, max_snr_db):
    """
    Convert a percentage of SNR to dB scale.

    Parameters:
    - percentage: float, e.g., 0.8 for 80%
    - max_snr_db: float, max SNR in dB

    Returns:
    - snr_db: float, the SNR at the given percentage in dB
    """
    if percentage <= 0 or percentage > 1:
        raise ValueError("Percentage must be between 0 and 1 (exclusive of 0).")
    
    threshold_snr_db = max_snr_db + 10 * np.log10(percentage)
    return threshold_snr_db

def calculate_snr_with_sliding_correlation(IQ_power_dBm, lag, window_size, noise_power_list):
    """
    Computes SNR using a sliding correlator approach 
    A lagged cross-correlation is used to estimate stable noise floor.
    
    Parameters:
    - IQ_power_dBm: list or np.array of power in dBm
    - lag: lag to apply for correlation (sliding step)
    - window_size: number of samples in each correlation window
    - noise_power_list: list to which estimated noise powers are appended
    """
    IQ_power_dBm = np.array(IQ_power_dBm)
    n = len(IQ_power_dBm)

    # Ensure valid parameters
    if window_size + lag > n:
        raise ValueError("Window size plus lag must be less than or equal to the signal length.")

    # === Sliding Correlator (auto-correlation of power signal) ===
    correlations = []
    for i in range(n - lag - window_size + 1):
        ref_window = IQ_power_dBm[i : i + window_size]
        lagged_window = IQ_power_dBm[i + lag : i + lag + window_size]
        
        # Pearson correlation
        if np.std(ref_window) == 0 or np.std(lagged_window) == 0:
            corr = 0
        else:
            corr = np.corrcoef(ref_window, lagged_window)[0, 1]
        
        correlations.append(corr)

    # Invert correlation to interpret as noise (lower correlation => more noise-like)
    inverted_corr = 1 - np.array(correlations)

    # Estimate noise level using 10th percentile of inverted correlations (low correlation → noise)
    noise_estimation_metric = np.percentile(inverted_corr, 10)

    # For power-based estimate, estimate noise as low power percentile
    min_noise_power_dBm = np.percentile(IQ_power_dBm, 10)
    signal_power_dBm = np.percentile(IQ_power_dBm, 90)

    # Update noise power list
    noise_power_list.append(min_noise_power_dBm)

    # Average noise in linear domain
    noise_power_linear = 10 ** (np.array(noise_power_list) / 10)
    noise_power_avg_linear = np.mean(noise_power_linear)
    noise_power_avg = 10 * np.log10(noise_power_avg_linear)

    # Compute SNR in dB
    SNR_dB = signal_power_dBm - noise_power_avg

    return SNR_dB, noise_power_avg


def calculate_snr_with_min_noise_window(IQ_power_dBm, window_size,noise_power_list):
    """
    Computes SNR by estimating the noise power as a percentile-based window.
    SNR = Signal Power - Estimated Noise Power
    """
    # Ensure window_size is valid
    valid_window_size = max(1, min(window_size, len(IQ_power_dBm)))  # Adjust to a valid range
    
    # Compute moving average power over the valid window size
    if valid_window_size > 1:
        noise_power_dBm = np.convolve(IQ_power_dBm, np.ones(valid_window_size)/valid_window_size, mode='valid')
    else:
        noise_power_dBm = IQ_power_dBm  # If only one sample, no convolution is possible

    # Check if noise_power_dBm is empty before proceeding
    if len(noise_power_dBm) == 0:
        print("Warning: Noise power array is empty. Using default noise level.")
        return -np.inf, -np.inf  # Return default values
    
    # Find the noise power using the 10th percentile instead of the absolute minimum
    min_noise_power_dBm = np.percentile(noise_power_dBm, 10)  # Avoid extreme outliers

    # Find signal power
    signal_power_dBm = np.percentile(IQ_power_dBm, 90)  # Use the 90th percentile for stability

    noise_power_list.append(min_noise_power_dBm)

    # Average noise in linear domain
    noise_power_linear = 10 ** (np.array(noise_power_list) / 10)
    noise_power_avg_linear = np.mean(noise_power_linear)
    noise_power_avg = 10 * np.log10(noise_power_avg_linear)

    # Compute SNR in dB
    SNR_dB = signal_power_dBm - noise_power_avg  # More stable estimate

    return SNR_dB, noise_power_avg

def calculate_power_metrics(complex_signal):
    # Extract the I and Q components from the complex signal
    I = complex_signal.real
    Q = complex_signal.imag
    
    # Calculate IQ magnitude for each sample in millivolts (mV) for each sample
    IQ_magnitude = np.sqrt(I**2 + Q**2)
    
    # Calculate IQ power for each sample in milliwatts (mW) for each sample
    IQ_power_mW = (IQ_magnitude**2) / 50.0

    # Avoid log(0) issue by replacing zeros with a small value
    IQ_power_mW = np.where(IQ_power_mW == 0, 1e-12, IQ_power_mW)
    
    # Convert the power values to dBm for each sample
    IQ_power_dBm = 10 * np.log10(IQ_power_mW) -9 # 7 is the calibration value
    
    # Calculate average and maximum power in dBm for the whole complex signal
    avg_power_dBm = np.mean(IQ_power_dBm)
    max_power_dBm = np.percentile(IQ_power_dBm, 95) #np.max(IQ_power_dBm)
    
    return IQ_power_dBm,avg_power_dBm, max_power_dBm

def create_socket_connection(ip, port=5002):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        print(f"[SOCKET] Connected to {ip}:{port}")
        return sock
    except socket.error as e:
        print(f"[SOCKET ERROR] {e}")
        return None

def write_data(fname, recv_queue):
    """
    Write received data packets from a queue to a binary file.

    Parameters:
    - fname (str): Output file name.
    - recv_queue (queue.Queue): Queue containing received packets.

    Returns:
    - None
    """
    with open(fname, "wb") as f:  
        while recv_queue.qsize() > 0:
            recv_packet = recv_queue.get(True)
            np.array(recv_packet).tofile(f)  # Ensure recv_packet is a NumPy array


def calculate_beam_indices(annotated_image, x_min, x_max, u_center, pixel_pitch, fx_mm, Rx_beam_angles):
    """
    Calculate closest beam angles and their indices based on bounding box coordinates.

    Args:
        annotated_image (numpy.ndarray): The annotated image.
        x_min (int): Minimum x-coordinate of bounding box.
        x_max (int): Maximum x-coordinate of bounding box.
        u_center (int): Center x-coordinate of bounding box.
        pixel_pitch (float): Pixel pitch of the camera.
        fx_mm (float): Focal length in mm.
        Rx_beam_angles (list): List of Rx beam angles.

    Returns:
        tuple: Annotated image and indices of closest beam angles (min, max, center).
    """
    X_min_mm = (x_min - 320) * pixel_pitch
    X_max_mm = (x_max - 320) * pixel_pitch
    X_center_mm = (u_center - 320) * pixel_pitch

    theta_min_degrees = degrees(atan2(X_min_mm, fx_mm))
    theta_max_degrees = degrees(atan2(X_max_mm, fx_mm))
    theta_center_degrees = degrees(atan2(X_center_mm, fx_mm))

    closest_beam_angle_min = min(Rx_beam_angles, key=lambda x: abs(x - theta_min_degrees))
    closest_beam_angle_max = min(Rx_beam_angles, key=lambda x: abs(x - theta_max_degrees))
    closest_beam_angle_center = min(Rx_beam_angles, key=lambda x: abs(x - theta_center_degrees))

    Rx_min_beam_index = Rx_beam_angles.index(closest_beam_angle_min) + 1
    Rx_max_beam_index = Rx_beam_angles.index(closest_beam_angle_max) + 1
    Rx_center_beam_index = Rx_beam_angles.index(closest_beam_angle_center) + 1

    return annotated_image, Rx_min_beam_index, Rx_max_beam_index, Rx_center_beam_index

#---------------------------------------------------------- LOGGING FUNCTIONS -------------------------------------------------------------------------------------------------------

log_lock = threading.Lock()  # Prevents race conditions
log_file_path = None  # Store log file path globally

def setup_thread_logging(experiment_dir):
    """Initialize thread logging by creating a CSV file."""
    global log_file_path
    log_file_path = os.path.join(experiment_dir, "thread_timing.csv")
    
    with open(log_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Thread", "Event", "Timestamp"])  # Write CSV header

def log_thread_event(thread_name, event):
    """Logs start and end times for threads and writes immediately to CSV."""
    timestamp = time.time()
    
    with log_lock:
        with open(log_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([thread_name, event, timestamp])

    print(f"[TIMING] {thread_name} - {event} at {timestamp:.4f}")


def setup_logging(experiment_dir):
    log_filename = os.path.join(experiment_dir, "experiment_log.txt")
    log_file = open(log_filename, "w")

    class Logger(object):
        def __init__(self, file):
            self.terminal = sys.stdout
            self.log = file

        def write(self, message):
            if message.strip():  # Avoid logging empty lines
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"[{timestamp}] {message}"
                message = f" {message}"
            self.terminal.write(message)
            self.log.write(message)

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(log_file)
    sys.stderr = Logger(log_file)

def save_experiment_metadata(experiment_dir, experiment_name, metadata):
    """Saves experiment metadata including timestamp and name."""

    with open(os.path.join(experiment_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
    logging.info("Experiment metadata saved.")

def log_timing(experiment_dir, function_name, start_time, end_time):
    """Logs timing information of a function to timing.csv."""
    
    # Ensure experiment directory exists
    if not os.path.exists(experiment_dir):
        os.makedirs(experiment_dir)

    csv_file = os.path.join(experiment_dir, "timing.csv")

    # Ensure file creation before writing
    write_header = not os.path.exists(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["Function", "Start Time", "End Time", "Duration (s)"])
        writer.writerow([function_name, start_time, end_time, round(end_time - start_time, 4)])


def timing_decorator(experiment_dir):
    """Decorator to log function execution time to timing.csv."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Ensure experiment directory is passed correctly
            if not isinstance(experiment_dir, str) or not os.path.exists(experiment_dir):
                raise ValueError(f"Invalid experiment directory: {experiment_dir}")

            result = func(*args, **kwargs)
            end_time = time.time()

            log_timing(experiment_dir, func.__name__, start_time, end_time)
            return result
        return wrapper
    return decorator


def log_thread_timing(experiment_dir, thread_name, start_time, end_time):
    """Logs thread execution timing for concurrency analysis."""
    csv_file = os.path.join(experiment_dir, "thread_timing.csv")
    write_header = not os.path.exists(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["Thread", "Start Time", "End Time", "Duration (s)"])
        writer.writerow([thread_name, start_time, end_time, round(end_time - start_time, 4)])


def thread_timing_decorator(experiment_dir):
    """Decorator to log thread execution timing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logging.info(f"Thread {func.__name__} started at {start_time}")
            result = func(*args, **kwargs)
            end_time = time.time()
            logging.info(f"Thread {func.__name__} ended at {end_time}")
            log_thread_timing(experiment_dir, func.__name__, start_time, end_time)
            return result
        return wrapper
    return decorator

def run_interactive_command(child, command):
    try:
        # Wait for the interactive prompt, and send the command
        child.expect('>>>')
        child.sendline(command)
        print('Sending command: {}'.format(command))
    except pexpect.ExceptionPexpect as e:
        print('Failed to run command "{}": {}'.format(command, e))