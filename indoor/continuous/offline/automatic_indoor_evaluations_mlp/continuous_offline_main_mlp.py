"""VIBE-MLP offline runner — indoor, continuous rotor.

Launched once per experiment by `offline_automatic_mlp_main.py`. Same shape as
the online VIBE-MLP runner (YOLO → `OffsetMLP`-predicted offset) except SNR is
looked up in a pre-collected ground-truth CSV (`GROUND_TRUTH_CSV` from
config.py) instead of being measured live. The hardware (Sivers TX/RX, USRP,
rotor) is still driven so the experiment behaves identically from the runtime
side; only the SNR observation is replayed. Per-step results are appended to
`Adaptive_Beamforming_SC/<experiment_name>/results_<experiment_name>.csv`.

Requires trained MLP weights `offset_mlp_model_sc_jul20_offline.pt` and
matching scaler `offset_scaler_sc_jul20_offline.pkl` in this folder. The `.pt`
file is not bundled with the repo — train one with `train_mlp.py` from the
sibling [../automatic_indoor_evaluations_mlp/](../automatic_indoor_evaluations_mlp/) folder.

Invoked as: `python3 continuous_offline_main_mlp.py --test_number <id>`.

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
ground_truth_data = pd.read_csv(GROUND_TRUTH_CSV)

ground_truth_data["Tx Beam Index"] = pd.to_numeric(ground_truth_data["Tx Beam Index"], errors="coerce")
ground_truth_data["Rx Beam Index"] = pd.to_numeric(ground_truth_data["Rx Beam Index"], errors="coerce")
ground_truth_data["SNR (dB)"] = pd.to_numeric(ground_truth_data["SNR (dB)"], errors="coerce")

last_valid_yolo_beam = None  # add this at the top of YOLO_RX as a persistent state
start_event = threading.Event()
beam_offset_history = deque(maxlen=10)  # stores last 10 offsets

class OffsetMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim=128):
        super(OffsetMLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim)
        self.norm3 = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(0.2)
        self.fc4 = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = torch.relu(self.norm1(self.fc1(x)))
        x = torch.relu(self.norm2(self.fc2(x)))
        x = self.dropout(torch.relu(self.norm3(self.fc3(x))))
        return self.fc4(x)

# Load model + scaler
device = torch.device("cpu")
model = OffsetMLP(input_dim=4)


model.load_state_dict(torch.load("offset_mlp_model_sc_jul20_offline.pt", map_location=device))
model.eval()


scaler = joblib.load("offset_scaler_sc_jul20_offline.pkl")

# Function to predict offset using the trained model
def predict_offset(model, scaler, input_vector):
    """
    input_vector = [boresight, threshold_snr, yolo_predicted_beam, snr_yolo]
    """
    model.eval()
    X_scaled = scaler.transform([input_vector])
    X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
    with torch.no_grad():
        pred = model(X_tensor).item()
    return round(pred)


#Function to get RX beam index from angle
def get_rx_beam_index_from_angle(angle, RX_BEAM_ANGLES):
    for idx, ang in enumerate(RX_BEAM_ANGLES):
        if ang == angle:
            return idx
    return None  # or raise an error


def get_snr_from_ground_truth(boresight_angle, tx_beam_index, rx_beam_index):
    """
    Extract SNR from the ground truth data for the corresponding TX and RX beam angles, boresight angle,
    TX beam index, and RX beam index.

    Arguments:
    boresight_angle -- The boresight angle.
    tx_beam_index -- Transmit beam index.
    rx_beam_index -- Receive beam index.

    Returns:
    SNR value (in dB) if found, otherwise None.
    """
    # Filter ground truth data by the additional parameters (boresight angle, tx beam index, rx beam index)
    snr_data = ground_truth_data[
        (ground_truth_data['Boresight'] == boresight_angle) &
        (ground_truth_data['Tx Beam Index'] == tx_beam_index) &
        (ground_truth_data['Rx Beam Index'] == rx_beam_index)
    ]

    print(f"[DEBUG] Searching for SNR with boresight={boresight_angle}, tx={tx_beam_index}, rx={rx_beam_index}")
    # Return SNR if data is found
    if not snr_data.empty:
        return snr_data['SNR (dB)'].values[0]
    else:
        # If no data found, return None
        print(f"[WARN] No SNR found for boresight={boresight_angle}, tx={tx_beam_index}, rx={rx_beam_index}")
        return None


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
def YOLO_RX(experiment_dir):
    global currentrotorangle
    global last_valid_yolo_beam
    
    print("[YOLO_RX] Waiting for synchronization signal to start processing...")
    start_event.wait()
    print("[YOLO_RX] Synchronization received. Starting YOLO inference.")

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

    
    print("[YOLO_RX] Waiting for rotor to enter [45, 135] range...")
    while currentrotorangle > 160 or currentrotorangle < 25:
        time.sleep(0.1)
    print("[YOLO_RX] Rotor in range. Starting main loop.")
    while currentrotorangle >= 25 and currentrotorangle <= 160:
    
 
        print('------------------------------------------------------------------')
        print(f"[YOLO_THREAD] Current rotor angle: {currentrotorangle}")
        print('------------------------------------------------------------------')
        print()
        YOLO_time_start = time.time()

     

        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S") + f"_{now.microsecond // 1000:03d}"

        message = f"DETECT:{currentrotorangle}:{timestamp}"
        sock.sendall(message.encode())
        beam_index_str = sock.recv(1024).decode().strip()
        print(f"[Jetson_YOLO_THREAD] Jetson response Received: {beam_index_str}")

        YOLO_time_end = time.time()
        yolo_processing_time = YOLO_time_end - YOLO_time_start
        
        if beam_index_str.isdigit():
                Rx_center_beam_index = int(beam_index_str)
                last_valid_yolo_beam = Rx_center_beam_index
                print("[Jetson_YOLO_THREAD] Radio detected, beam index:", Rx_center_beam_index)
                
        elif beam_index_str == "NO_RADIO": 
            if last_valid_yolo_beam is not None:
                Rx_center_beam_index = last_valid_yolo_beam
                print("[Jetson_YOLO_THREAD] No radio detected, using last valid beam index:", Rx_center_beam_index)
            else:
                Rx_center_beam_index = 32
                print("[Jetson_YOLO_THREAD] No radio detected and no previous beam index.]")
        else:
            # If the response is not a valid beam index, reset to default
            if last_valid_yolo_beam is not None:
                Rx_center_beam_index = last_valid_yolo_beam
                print(f"[Jetson_YOLO_THREAD] Invalid response '{beam_index_str}', using last valid beam index:", Rx_center_beam_index)
            else:
                Rx_center_beam_index = 32
                print(f"[Jetson_YOLO_THREAD] Invalid response '{beam_index_str}', resetting beam index to 32.")
                

        # Update previous rotor angle for next loop
        previous_rotor_angle = currentrotorangle

        # Beamforming
        start_beam_time = time.time()
        
        snr_yolo = get_snr_from_ground_truth(currentrotorangle-90, fixed_tx_beam, Rx_center_beam_index)

       
        if beam_index_str.isdigit():

            # --- Step 2: If SNR is high, keep YOLO beam ---
            if snr_yolo >= SNR_THRESHOLD:
                selected_beam = Rx_center_beam_index
                final_snr_db = snr_yolo
                offset_error = 0
                beams_checked = 1
                adjustment_type = "YOLO"

            else:
                # Predict offset using the model
                boresight = currentrotorangle - 90
                threshold_snr = SNR_THRESHOLD
                yolo_predicted_beam = Rx_center_beam_index
                snr_yolo = snr_yolo if snr_yolo is not None else -100
                

                input_vector = [
                boresight,
                threshold_snr,                      
                yolo_predicted_beam,
                snr_yolo ]                      

                
                predicted_offset = predict_offset(model, scaler, input_vector)

                adjusted_beam_index = Rx_center_beam_index + predicted_offset
                adjusted_beam_index = max(MIN_BEAM_INDEX, min(MAX_BEAM_INDEX, adjusted_beam_index))
                
                snr_adjusted = get_snr_from_ground_truth(currentrotorangle-90, 30, adjusted_beam_index)

          

                # if snr_adjusted >= SNR_THRESHOLD:
                #     selected_beam = adjusted_beam_index
                #     final_snr_db = snr_adjusted
                #     offset_error = predicted_offset
                #     beams_checked = 2
                #     adjustment_type = "OffsetCorrected"

            
                # Ensure adjusted_beam_index is always defined
                if snr_adjusted >= SNR_THRESHOLD:
                    selected_beam = adjusted_beam_index
                    final_snr_db = snr_adjusted
                    offset_error = predicted_offset
                    beams_checked = 2
                    adjustment_type = "OffsetCorrected"
                else:
                    selected_beam = Rx_center_beam_index
                    final_snr_db = snr_adjusted
                    offset_error = predicted_offset
                    beams_checked = 2
                    adjustment_type = "OffsetFailed"

               

        else:
            #SAFE DEFAULT ASSIGNMENTS
            selected_beam = None
            final_snr_db = None
            offset_error = None
            beams_checked = 1
            adjustment_type = "CenterFallback"
            adjusted_beam_index = 32
            print("[YOLO_THREAD] Beamformed at center; Skipped beam correction due to invalid YOLO beam prediction.")


        beam_sweep_time = time.time() - start_beam_time


        # Log result
        csv_filename = f"{experiment_dir}/results_{experiment_name}.csv"
        csv_data = {
            "Timestamp": [timestamp],
            "Boresight": currentrotorangle-90,
            "Jetson Detection": [beam_index_str],
            "Rx Beam Index": [Rx_center_beam_index],
            "Rx Beam Angle": [RX_BEAM_ANGLES[Rx_center_beam_index]],
            "Initial SNR (dB)": [snr_yolo],
            "YOLO Time (s)": [yolo_processing_time],
            "Beam Sweep Time (s)": [beam_sweep_time],
            "Rx Beam Index (YOLO Predicted)": [Rx_center_beam_index],
            "Rx Beam Index (Selected)": [selected_beam],
            "Adjustment Method": [adjustment_type],
            "Beams Checked in Search": [beams_checked],
            "Adjusted Beam Index": [adjusted_beam_index],
            "Adjusted Beam Angle": [RX_BEAM_ANGLES[adjusted_beam_index]],
            "SNR (dB)": [final_snr_db],
            "Offset Error": [offset_error],
            "Beam Offset History": [list(beam_offset_history)],
        
        }
        df = pd.DataFrame(csv_data)
        if not os.path.exists(csv_filename):
            df.to_csv(csv_filename, index=False)
        else:
            df.to_csv(csv_filename, mode='a', header=False, index=False)  # Do not write header again

        print()
        snr_str = f"{final_snr_db:.2f}" if isinstance(final_snr_db, (float, int)) else "N/A"
      
      



def main():
    """Main function to control servo, handle YOLO detection, and plot SNR vs. rotor angle."""

    time.sleep(4)

    # Initialize Directories
    main_directory = "Adaptive_Beamforming_SC"
    os.makedirs(main_directory, exist_ok=True)

    # === Collect user inputs ===
    mode = "3"
 
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
        # "Threshold Factor": f"{SNR_THRESHOLD_FACTOR}",
        # "reference_max_snr_db": f"{REFERENCE_MAX_SNR_DB}",
        "Threshold": SNR_THRESHOLD,
        "Algorithm": "Adaptive Beamforming",
        
       
    }

    setup_logging(experiment_dir)
    save_experiment_metadata(experiment_dir, experiment_name,metadata_content)
    
  

    
    
    rotation_time_ms = get_rotation_time_ms(ROTOR_SPEED)  # Time to rotate the antenna
    rotor_thread = threading.Thread(target=send_rotation_command, args=(rotation_time_ms,), daemon=True)
    rotor_thread.start()

    # Start the camera capture thread
    capture_thread = threading.Thread(target=YOLO_RX, args=(experiment_dir,), daemon=True)
    capture_thread.start()
    
    # Allow everything to get set up before starting
    time.sleep(1.5)
    print("[MAIN] Synchronizing both threads now...")
    start_event.set()  # Unblocks both threads simultaneously

    capture_thread.join()
    rotor_thread.join()


    print("\n[INFO] Generating plots using plot_all.py ...")


    # Set environment variables for plot script
    os.environ["PLOT_MODE"] = mode
    os.environ["EXPERIMENT_NAME"] = experiment_name
    os.environ["EXPERIMENT_PATH"] = os.path.abspath(experiment_dir)
    os.environ["GROUND_TRUTH_PATH"] = GROUND_TRUTH_DIR
    os.environ["GROUND_TRUTH_NAME"] = GROUND_TRUTH_NAME
    os.environ["ALGORITHM_NAME"] = "Adaptive Beamforming + MLP"
   


    # Run plotting script
    try:
        subprocess.run(["python3", PLOT_EXPERIMENT], check=True)        
        print("[SUCCESS] Plotting completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to generate plots: {e}")

    # === CALL THE EVALUATION SCRIPT ===
    print("\n[INFO] Running evaluation summary script...")


    try:
        subprocess.run(["python3", "eval.py", experiment_name])
        print("[SUCCESS] Evaluation script completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to evaluate experiment: {e}")

    
    #close the loggers
    print('[SUCCESS]Complete.')



    print('[SUCCESS]Log files closed.')
    


    return



if __name__ == "__main__":
    main()
 
    
