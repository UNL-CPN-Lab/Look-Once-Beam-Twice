import os
import sys

# This file lives in outdoor/alt_runners/. Make outdoor/ importable so the
# `from imports import *` below finds outdoor/imports.py.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import serial
import datetime
from imports import *
import re


# Add the repo root so `from configurations...` works (two levels up from here).
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)


from configurations.utils import *
from configurations.config import *

# Constants
noise_power_list = []  # List to store noise power values for SNR calculation
currentrotorangle = 0  # Tracks the current rotor position

last_valid_yolo_beam = None  # add this at the top of YOLO_RX as a persistent state
start_event = threading.Event()
beam_index_str = None  # Initialize beam_index_str to store the last valid beam index from YOLO
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


_MLP_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "mlp_models")
model.load_state_dict(torch.load(os.path.join(_MLP_MODELS_DIR, "offset_mlp_model_sc.pt"), map_location=device))
model.eval()


scaler = joblib.load(os.path.join(_MLP_MODELS_DIR, "offset_scaler_sc.pkl"))

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





# Function to handle YOLO detection and SNR calculation
def YOLO_RX(usrp, rx_streamer,  child_rx, experiment_dir, Txsock=None):

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


    Rx_center_beam_index = 32  # default

    # Wait until rotor angle enters desired window
    print("[YOLO_RX] Waiting for rotor to enter [45, 135] range...")
    try:
        while True:

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
            
        

            # Beamforming
            start_beam_time = time.time()

          
            rx_angle = rx_angle_index[Rx_center_beam_index]
            try:
                tx_index = tx_angle_index(rx_angle)
            except ValueError:
                print(f"[ERROR] RX angle {tx_index} not found in TX_BEAM_ANGLES.")
                tx_index = 32  # fallback

         
            if Txsock:
                try:
                    Txsock.sendall(f"SET_TX_BEAM:{tx_index}\n".encode())
                except socket.timeout:
                    print(f"[SOCKET TIMEOUT] TX beam {tx_index} send timed out.")
                except Exception as e:
                    print(f"[SOCKET ERROR] {e}")

            run_interactive_command(child_rx, f'eder.rx.set_beam({Rx_center_beam_index})')

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_yolo, _ = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)
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

                    run_interactive_command(child_rx, f'eder.rx.set_beam({adjusted_beam_index})')
            
                    rx_angle2 = rx_angle_index[adjusted_beam_index]
                    try:
                        tx_index2 = tx_angle_index(rx_angle2)
                    except ValueError:
                        print(f"[ERROR] RX angle {tx_index2} not found in TX_BEAM_ANGLES.")
                        tx_index2 = 32  # fallback
         
                    if Txsock:
                        try:
                            Txsock.sendall(f"SET_TX_BEAM:{tx_index2}\n".encode())
                        except socket.timeout:
                            print(f"[SOCKET TIMEOUT] TX beam {tx_index2} send timed out.")
                        except Exception as e:
                            print(f"[SOCKET ERROR] {e}")

                   
                            
            

                    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
                    for _ in range(30):
                        rx_streamer.recv(recv_signal, metadata)

                    IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
                    snr_adjusted, _ = calculate_snr_with_min_noise_window(
                        IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
                    )

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
            
            try:
                final_rx_angle = rx_angle_from_index(Rx_center_beam_index)
                final_tx_index = tx_angle_index(-final_rx_angle)
            except Exception as e:
                print(f"[ERROR] Could not compute TX index from selected beam {Rx_center_beam_index}: {e}")
                
            final_tx_angle = tx_angle_from_index(final_tx_index)


            # Log result
            csv_filename = f"{experiment_dir}/results_{experiment_name}.csv"
            csv_data = {
                "Timestamp": [timestamp],
                "Boresight": currentrotorangle-90,
                "Jetson Detection": [beam_index_str],
                "Rx Beam Index": [Rx_center_beam_index],
                "Rx Beam Angle": [RX_BEAM_ANGLES[Rx_center_beam_index]],
                "Initial SNR (dB)": [snr_yolo],
                "Initial Max Power (dBm)": [max_power_dBm],
                "Max Power (dBm)": [max_power_dBm],
                "YOLO Time (s)": [yolo_processing_time],
                "Beam Sweep Time (s)": [beam_sweep_time],
                "Rx Beam Index (YOLO Predicted)": [Rx_center_beam_index],
                "Rx Beam Index (Selected)": [selected_beam],
                "Tx Beam Index": final_tx_index,
                "Tx Beam Angle": final_tx_angle,
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
            power_str = f"{max_power_dBm:.2f}" if isinstance(max_power_dBm, (float, int)) else "N/A"

            print(f"[YOLO THREAD] Final beam selected: {selected_beam}, SNR: {snr_str} dB, Max Power: {power_str} dBm, Beams Checked: {beams_checked}, Rotor Angle: {currentrotorangle}")

    except KeyboardInterrupt:
        print("[YOLO_RX] Keyboard interrupt received. Exiting YOLO_RX thread.")


            


def main():
    """Main function to control servo, handle YOLO detection, and plot SNR vs. rotor angle."""

    time.sleep(2)

    # Initialize Directories
    main_directory = "Outdoor_Adaptive_Beamforming_SC/mlp_Results"
    os.makedirs(main_directory, exist_ok=True)
    
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


    # === Collect user inputs ===
    location = input("Enter the location (e.g., nh or kh): ").strip()
    gain = input("Enter the gain setting (e.g., 15db): ").strip()
    distance = input("Enter the distance (e.g., 10m): ").strip()
    test_number = input("Enter the test number (e.g., t1): ").strip()

    # Automatically get date in 'jul2' format
    today = datetime.datetime.today()
    date = today.strftime("%b").lower() + str(today.day)

    # === Format experiment name ===
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
        "car_speed": f"{CAR_SPEED} mph",
        "Threshold" : f"{SNR_THRESHOLD} dB",
        "Threshold Quantile": f"{SNR_QUANTILE}",
        "Algorithm": "Adaptive Beamforming",
        
       
    }

    setup_logging(experiment_dir)
    save_experiment_metadata(experiment_dir, experiment_name,metadata_content)
    
    # Initialize USRP
    print("\n[INFO] Initializing USRP...")
    usrp, rx_streamer, _ = initialize_usrp()

    #Initialize Sivers
    child_rx, logfile_rx,_ = initialize_sivers_RX(experiment_dir)

    
    # Start the camera capture thread
    capture_thread = threading.Thread(target=YOLO_RX, args=(usrp, rx_streamer, child_rx,experiment_dir,Txsock), daemon=True)
    capture_thread.start()
    
    # Allow everything to get set up before starting
    time.sleep(1.5)
    print("[MAIN] Synchronizing both threads now...")
    start_event.set()  # Unblocks both threads simultaneously

    capture_thread.join()

    
    # Disable Sivers devices
    print("\nDisabling the Sivers receiver and transmitter.....")
    run_interactive_command(child_rx, 'eder.rx_disable()')

    print("[INFO] Sivers devices disabled.")
    # Close the Sivers processes


    print("\n[INFO] Generating plots using plot_all.py ...")

    #close the loggers
    print('[SUCCESS]Complete.')


    # Close the log files
    logfile_rx.close()


    print('[SUCCESS]Log files closed.')
    
    return



if __name__ == "__main__":
    main()
 
    
