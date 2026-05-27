"""5G NR baseline online runner — indoor, continuous rotor.

Launched once per experiment by `automatic_5gnr_main.py`. Implements the
hierarchical 5G NR baseline used to benchmark VIBE-MA / VIBE-MLP / VIBE-YOLOR.
At every rotor angle the runner:

1. Pins TX to beam 0 and sweeps all RX beams (1..63) to find the best SNR.
2. Pins RX to that best beam and sweeps all TX beams (1..63) to find the best.
3. Logs the resulting `(best_rx, best_tx)` pair and SNR.

This is an exhaustive sequential search; there is no camera prior and no remote
YOLO service involved. Per-step results are appended to
`Adaptive_Beamforming_SC/<experiment_name>/results_<experiment_name>.csv`.

Invoked as: `python3 continuous_online_main_5gnr.py --test_number <id>`.

Author: Apala Pramanik
"""

import serial
import time
from imports import *
import re

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)


from configurations.utils import *
from configurations.config import *

# Constants
noise_power_list = []  # List to store noise power values for SNR calculation
currentrotorangle = 0  # Tracks the current rotor position

last_valid_yolo_beam = None  # add this at the top of YOLO_RX as a persistent state
start_event = threading.Event()



def send_rotation_command(rotation_time_ms):
    global currentrotorangle
    
    print("[ROTATION] Waiting for synchronization signal to start rotation...")
    start_event.wait()  # BLOCK until main thread sets the event
    print("[ROTATION] Synchronization received. Starting rotation.")
 
    try:
        arduino = serial.Serial(serial_port, baud_rate, timeout=2)
        time.sleep(2)  # Give time for Arduino to reset
        print(f"[INFO] Connected to {serial_port}")
    except Exception as e:
        print(f"[ERROR] Could not connect: {e}")
        return

    try:
        command = f"C:{rotation_time_ms}\n"
        print(f"[INFO] Sending command: {command.strip()}")
        arduino.write(command.encode())
        time.sleep(0.1)  # Give Arduino time to process

        # Read Arduino feedback
        while True:
            line = arduino.readline().decode().strip()
            if line:
                print(f"[ARDUINO] {line}")

                # Try to extract angle
                if "Angle:" in line:
                    try:
                        angle_match = re.search(r"Angle:\s*(\d+)", line)
                        if angle_match:
                            currentrotorangle = int(angle_match.group(1))
                            print(f"[INFO] Updated current rotor angle to {currentrotorangle}")
                    except Exception as e:
                        print(f"[WARN] Failed to parse angle: {e}")

            if "Sweep complete" in line:
                break

    except Exception as e:
        print(f"[ERROR] Communication failed: {e}")
    finally:
        arduino.close()
        print("[INFO] Serial connection closed.")



# Function to handle YOLO detection and SNR calculation
def NR_SWEEP(usrp, rx_streamer, child_tx, child_rx, experiment_dir):
    global currentrotorangle
    global last_valid_yolo_beam
    
    print("[NR_SWEEP] Waiting for synchronization signal to start processing...")
    start_event.wait()
    print("[NR_SWEEP] Synchronization received. Starting YOLO inference.")

    experiment_name = os.path.basename(experiment_dir)


 
    previous_rotor_angle = None
  

    # Wait until rotor angle enters desired window
    print("[NR_SWEEP] Waiting for rotor to enter [45, 135] range...")
  
    
        
    while currentrotorangle <= 135:
        
        if currentrotorangle < 45:
            time.sleep(0.05)
            continue

        print('------------------------------------------------------------------')
        print(f"[NR_SWEEP] Current rotor angle: {currentrotorangle}")
        print('------------------------------------------------------------------')
        print()
        
     

        # Start radio streaming
        start_time = usrp.get_time_now().get_real_secs() + INIT_DELAY
        metadata = uhd.types.RXMetadata()
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = False
        stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
        rx_streamer.issue_stream_cmd(stream_cmd)

        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S") + f"_{now.microsecond // 1000:03d}"

      
        max_snr_db_RX = -np.inf
        max_snr_db_TX = -np.inf
        best_rx_beam = None
        best_tx_beam = None
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
                
        # Update previous rotor angle for next loop
        previous_rotor_angle = currentrotorangle


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



def main():
    """Main function to control servo, handle YOLO detection, and plot SNR vs. rotor angle."""

    time.sleep(4)

    # Initialize Directories
    main_directory = "Adaptive_Beamforming_SC"
    os.makedirs(main_directory, exist_ok=True)

    # === Collect user inputs ===
    mode = "2"
 
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
    
    # Initialize USRP
    print("\n[INFO] Initializing USRP...")
    usrp, rx_streamer, _ = initialize_usrp()

    #Initialize Sivers
    child_tx, child_rx, logfile_tx,  logfile_rx, _ = initialize_sivers(experiment_dir)

    
    
    rotation_time_ms = get_rotation_time_ms(ROTOR_SPEED)  # Time to rotate the antenna
    rotor_thread = threading.Thread(target=send_rotation_command, args=(rotation_time_ms,), daemon=True)
    rotor_thread.start()

    # Start the camera capture thread
    capture_thread = threading.Thread(target=NR_SWEEP, args=(usrp, rx_streamer, child_tx, child_rx,experiment_dir,), daemon=True)
    capture_thread.start()
    
    # Allow everything to get set up before starting
    time.sleep(1.5)
    print("[MAIN] Synchronizing both threads now...")
    start_event.set()  # Unblocks both threads simultaneously

    capture_thread.join()
    rotor_thread.join()
    
    # Disable Sivers devices
    print("\nDisabling the Sivers receiver and transmitter.....")
    run_interactive_command(child_rx, 'eder.rx_disable()')
    run_interactive_command(child_tx, 'eder.tx_disable()')
    print("[INFO] Sivers devices disabled.")
    # Close the Sivers processes


    print("\n[INFO] Generating plots using plot_all.py ...")


    # Set environment variables for plot script
    os.environ["PLOT_MODE"] = mode
    os.environ["EXPERIMENT_NAME"] = experiment_name
    os.environ["EXPERIMENT_PATH"] = os.path.abspath(experiment_dir)
    os.environ["GROUND_TRUTH_PATH"] = GROUND_TRUTH_DIR
    os.environ["GROUND_TRUTH_NAME"] = GROUND_TRUTH_NAME
    os.environ["ALGORITHM_NAME"] = "5G NR Adaptive Beamforming"
   


    
    # === CALL THE EVALUATION SCRIPT ===
    print("\n[INFO] Running evaluation summary script...")


    try:
        subprocess.run(["python3", "eval.py", experiment_name])
        print("[SUCCESS] Evaluation script completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to evaluate experiment: {e}")

    
    #close the loggers
    print('[SUCCESS]Complete.')


    # Close the log files
    logfile_rx.close()
    logfile_tx.close()

    print('[SUCCESS]Log files closed.')
    


    return



if __name__ == "__main__":
    main()
 
    
