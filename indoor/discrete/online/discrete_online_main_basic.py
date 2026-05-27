from imports import *
import sys
from configurations.utils import *
from configurations.config import *

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)


# Constants
noise_power_list = []  # List to store noise power values for SNR calculation
rotor_ready = 0 # Flag to indicate if the rotor is ready
currentrotorangle = 0  # Tracks the current rotor position
stop_after = None  # time when we should stop YOLO_RX
# Store the last valid YOLO beam index
last_valid_yolo_beam = None  # add this at the top of YOLO_RX as a persistent state


# Load ground truth data 
ground_truth_data = pd.read_csv(GROUND_TRUTH_CSV)
# Load the best Rx beam CSV 
best_rx_beam_df = pd.read_csv(BEST_RX_BEAM_CSV)
best_rx_beam_df.columns = best_rx_beam_df.columns.str.strip()

arduino = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(1)  # wait for Arduino reset

# Function to move servo to a specific angle
def rotor_control(rotor_angle, experiment_dir):
    global currentrotorangle, stop_after
    global rotor_ready
    for target_angle in range(45, 136, 1):  
        print()
        print()
        print('#################################################')
        print(f"[THREAD] Moving rotor to angle: {target_angle}")
        
        move_servo_to_angle(arduino,currentrotorangle, target_angle)
        print()
        print('#################################################')
        currentrotorangle = target_angle
        print(f"[THREAD] Rotor at {target_angle}.")
        time.sleep(ROTOR_SPEED)  # Allow YOLO thread to run 5 times
        if target_angle == 135:
            stop_after = time.time() + ROTOR_SPEED # Set stop time to 10 seconds from now
            print("[ROTOR] Scheduled stopping YOLO_RX in 10 seconds.")
    print("[THREAD] Rotor thread finished.")
    return

# Function to handle YOLO detection and SNR calculation
def YOLO_RX(usrp, rx_streamer, child_tx, child_rx, experiment_dir,Txsock=None):
    global currentrotorangle
    rotor_ready
    experiment_name = os.path.basename(experiment_dir)


    # Open persistent socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((JETSON_IP, PORT))

    # Send HELLO once
    hello_msg = f"HELLO:{experiment_name}"
    sock.sendall(hello_msg.encode())
    response = sock.recv(1024).decode().strip()
    print(f"[MSI YOLO_THREAD] Jetson HELLO response: {response}")

    time.sleep(0.2)
    previous_rotor_angle = None
    Rx_center_beam_index = 32  # default

    
    time.sleep(0.2)
    while True:   
    
            if stop_after and time.time() > stop_after:
                print("[YOLO_RX] 5 seconds passed after rotor reached 135. Exiting YOLO_RX.")
                break    
            print('------------------------------------------------------------------')
            print(f"[YOLO_THREAD] Current rotor angle: {currentrotorangle}")
            print('------------------------------------------------------------------')
            print()
            YOLO_time_start = time.time()

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

            message = f"DETECT:{currentrotorangle}:{timestamp}"
            sock.sendall(message.encode())
            beam_index_str = sock.recv(1024).decode().strip()
            print(f"[Jetson_YOLO_THREAD] Jetson response Received: {beam_index_str}")

            YOLO_time_end = time.time()
            yolo_processing_time = YOLO_time_end - YOLO_time_start

            '''
            If the Jetson returns a valid beam index, use it.
            If Jetson returns "NO_RADIO" or an invalid/empty response:
            If the rotor angle has changed, reset the beam index to 32.
            # If the rotor angle is the same as before, keep using the previous valid beam index.
            After each loop, update the previous_rotor_angle for comparison in the next round.
            '''
            if beam_index_str.isdigit():
                Rx_center_beam_index = int(beam_index_str)
                print("[Jetson_YOLO_THREAD] Radio detected, beam index:", Rx_center_beam_index)
                
            elif beam_index_str == "NO_RADIO" or not beam_index_str:
                if previous_rotor_angle is not None and currentrotorangle != previous_rotor_angle:
                    Rx_center_beam_index = 32
                   
                    print("[Jetson_YOLO_THREAD] No radio or invalid response AND rotor angle changed. Reset beam index to 32.")
                else:
                    print("[Jetson_YOLO_THREAD] No radio or invalid response BUT rotor angle unchanged. Keeping previous beam index:", Rx_center_beam_index)
            else:
                if previous_rotor_angle is not None and currentrotorangle != previous_rotor_angle:
                    Rx_center_beam_index = 32
             
                    print(f"[Jetson_YOLO_THREAD] Invalid response '{beam_index_str}' AND rotor angle changed. Reset beam index to 32.")
                else:
                    print(f"[Jetson_YOLO_THREAD] Invalid response '{beam_index_str}' BUT rotor angle unchanged. Keeping previous beam index:", Rx_center_beam_index)
       
             
            # Update previous rotor angle for next loop
            previous_rotor_angle = currentrotorangle

            # Beamforming
            start_beam_time = time.time()
    
            run_interactive_command(child_tx, f'eder.tx.set_beam({fixed_tx_beam})')
            run_interactive_command(child_rx, f'eder.rx.set_beam({Rx_center_beam_index})')

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, _ = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)
            beam_sweep_time = time.time() - start_beam_time

            # Log result
            csv_filename = f"{experiment_dir}/results_{experiment_name}.csv"
            csv_data = {
                "Timestamp": [timestamp],
                "Boresight Angle": currentrotorangle-90,
                "Jetson Detection": [beam_index_str],
                "Rx Beam Index": [Rx_center_beam_index],
                "Rx Beam Angle": [RX_BEAM_ANGLES[Rx_center_beam_index]],
                "SNR (dB)": [snr_db],
                "Max Power (dBm)": [max_power_dBm],
                "YOLO Time (s)": [yolo_processing_time],
                "Beam Sweep Time (s)": [beam_sweep_time]
            }
            df = pd.DataFrame(csv_data)
            if not os.path.exists(csv_filename):
                df.to_csv(csv_filename, index=False)
            else:
                df.to_csv(csv_filename, mode='a', header=False, index=False)

            print()
            print(f"[YOLO THREAD] Computed SNR for angle {currentrotorangle}, Beam Index: {Rx_center_beam_index}, SNR: {snr_db} dB, Max Power: {max_power_dBm} dBm")
            print()

            


def main():
    """Main function to control servo, handle YOLO detection, and plot SNR vs. rotor angle."""

    move_servo_to_angle(arduino, 10, 0)
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
        "rotor_speed": f"{ROTOR_SPEED}",
        "Threshold Factor": f"{SNR_THRESHOLD_FACTOR}",
        "reference_max_snr_db": f"{REFERENCE_MAX_SNR_DB}",
        "Threshold": snr_percent_db(SNR_THRESHOLD_FACTOR, REFERENCE_MAX_SNR_DB),
        "Algorithm": "Adaptive Beamforming",
       
    }

    setup_logging(experiment_dir)
    save_experiment_metadata(experiment_dir, experiment_name,metadata_content)
    
    # Initialize USRP
    print("\n[INFO] Initializing USRP...")
    usrp, rx_streamer, _ = initialize_usrp()

    #Initialize Sivers
    child_tx, child_rx, logfile_tx,  logfile_rx, _ = initialize_sivers(experiment_dir)

    
    

    rotor_thread = threading.Thread(target=rotor_control, args=(currentrotorangle,experiment_dir), daemon=True)
    rotor_thread.start()

    # Start the camera capture thread
    capture_thread = threading.Thread(target=YOLO_RX, args=(usrp, rx_streamer, child_tx, child_rx,experiment_dir), daemon=True)
    capture_thread.start()

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
    os.environ["ALGORITHM_NAME"] = "Adaptive Beamforming"
    os.environ["OPTION"] = "A"  # Choose between "A" or "B" for beamforming time calculation


    # Run plotting script
    try:
        subprocess.run(["python3", PLOT_EXPERIMENT], check=True)        
        print("[SUCCESS] Plotting completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to generate plots: {e}")

    # === CALL THE EVALUATION SCRIPT ===
    print("\n[INFO] Running evaluation summary script...")


    try:
        subprocess.run(["python3", EVAL_SCRIPT_PATH], check=True)
        print("[SUCCESS] Evaluation summary completed.")
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
 