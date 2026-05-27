
import serial
import datetime
from imports import *
import re
import zmq

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)


from configurations.utils import *
from configurations.config import *




# Constants
noise_power_list = []  # List to store noise power values for SNR calculation
currentrotorangle = 0  # Tracks the current rotor position
beam_offset_history = deque(maxlen=20)
last_valid_yolo_beam = None  # add this at the top of YOLO_RX as a persistent state
start_event = threading.Event()
beam_index_str = None  # Initialize beam_index_str to store the last valid beam index from YOLO
zmq_context = zmq.Context()



# NeighborSearch Algorithm (Updated)
def search_nearby_beams(center_beam,  child_rx, rx_streamer, Txsock=None):
    best_beam = center_beam
    best_snr = -np.inf
    best_power = -np.inf
    best_offset = 0
    beams_checked = 0

    # First, check the adjusted (center) beam
    run_interactive_command(child_rx, f'eder.rx.set_beam({center_beam})')
    
    rx_angle2 = rx_angle_from_index(center_beam)
    try:
        tx_index2 = tx_angle_index(rx_angle2)
    except ValueError:
        print(f"[ERROR] RX angle {rx_angle2} not found in TX_BEAM_ANGLES.")
        tx_index2 = 32  # fallback
    
    if Txsock:
        
        try:
            Txsock.send_string(f"SET_TX_BEAM:{tx_index2}")
            ack = Txsock.recv_string().strip()
            print(f"[ZMQ] TX server responded to beam set: {ack}")

        except socket.timeout:
            print(f"[SOCKET TIMEOUT] TX beam {tx_index2} send timed out.")
        except Exception as e:
            print(f"[SOCKET ERROR] {e}")


    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
    metadata = uhd.types.RXMetadata()
    for _ in range(30):
        rx_streamer.recv(recv_signal, metadata)

    IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
    snr_db, _ = calculate_snr_with_min_noise_window(
        IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
    )
    beams_checked += 1


    if snr_db >= SNR_THRESHOLD:
        return center_beam, snr_db, 0, max_power_dBm, beams_checked

    # Otherwise, search all nearby beams until bounds exhausted
    best_snr = snr_db
    best_power = max_power_dBm
    offset = 1

    while True:
        searched_any = False

        for direction in [-1, 1]:
            new_beam = center_beam + direction * offset
            if new_beam < MIN_BEAM_INDEX or new_beam > MAX_BEAM_INDEX:
                continue

            searched_any = True

            run_interactive_command(child_rx, f'eder.rx.set_beam({new_beam})')
            rx_angle3 = rx_angle_from_index(new_beam)
            try:
                tx_index3 = tx_angle_index(rx_angle3)
            except ValueError:
                print(f"[ERROR] RX angle {tx_index3} not found in TX_BEAM_ANGLES.")
                tx_index3 = 30  # fallback


            if Txsock:
                try:
                    Txsock.send_string(f"SET_TX_BEAM:{tx_index3}")
                    ack = Txsock.recv_string().strip()
                    print(f"[ZMQ] TX server responded to beam set: {ack}")

                except socket.timeout:
                    print(f"[SOCKET TIMEOUT] TX beam {tx_index3} send timed out.")
                except Exception as e:
                    print(f"[SOCKET ERROR] {e}")

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, _ = calculate_snr_with_min_noise_window(
                IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
            )
            beams_checked += 1

         
            
            if snr_db >= SNR_THRESHOLD:
                # return center_beam, snr_db, 0, max_power_dBm, beams_checked
                return new_beam, snr_db, direction * offset, max_power_dBm, beams_checked


            if snr_db > best_snr:
                best_snr = snr_db
                best_beam = new_beam
                best_power = max_power_dBm
                best_offset = direction * offset

        if not searched_any:
            break  # Stop if no new valid beams can be searched

        offset += 1

    # No beam passed threshold → return best SNR found
    return best_beam, best_snr, best_offset, best_power, beams_checked




# # NeighborSearch Algorithm
# def search_nearby_beams(center_beam, child_rx, rx_streamer, Txsock=None):
#     best_beam = center_beam
#     best_snr = -np.inf
#     best_power = -np.inf
#     best_offset = 0
#     beams_checked = 0

#     # First, check the adjusted (center) beam
#     run_interactive_command(child_rx, f'eder.rx.set_beam({center_beam})')
#     if Txsock:
        # try:
        #     Txsock.sendall(f"SET_TX_BEAM:{center_beam}".encode())
        #     print(f"[SOCKET] Sent SET_TX_BEAM:{center_beam} to TX server.")
        # except Exception as e:
        #     print(f"[SOCKET ERROR] Failed to send beam index {center_beam}: {e}")
   

#     recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
#     metadata = uhd.types.RXMetadata()
#     for _ in range(30):
#         rx_streamer.recv(recv_signal, metadata)

#     IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
#     snr_db, _ = calculate_snr_with_min_noise_window(
#         IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
#     )
#     beams_checked += 1

#     # If center beam meets threshold, use it directly
#     if snr_db >= snr_percent_db(SNR_THRESHOLD_FACTOR, REFERENCE_MAX_SNR_DB):
#         return center_beam, snr_db, 0, max_power_dBm, beams_checked

#     # Otherwise, search nearby beams
#     best_snr = snr_db
#     best_power = max_power_dBm

#     for offset in range(1, 10):  # skip 0 because center already checked
#         for direction in [-1, 1]:
#             new_beam = center_beam + direction * offset
#             if new_beam < MIN_BEAM_INDEX or new_beam > MAX_BEAM_INDEX:
#                 continue

#             run_interactive_command(child_rx, f'eder.rx.set_beam({new_beam})')
#             if Txsock:
                # try:
                #     Txsock.sendall(f"SET_TX_BEAM:{new_beam}".encode())
                #     print(f"[SOCKET] Sent SET_TX_BEAM:{new_beam} to TX server.")
                # except Exception as e:
                #     print(f"[SOCKET ERROR] Failed to send beam index {new_beam}: {e}")
        

#             recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
#             for _ in range(30):
#                 rx_streamer.recv(recv_signal, metadata)

#             IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
#             snr_db, _ = calculate_snr_with_min_noise_window(
#                 IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
#             )
#             beams_checked += 1

#             # Return first beam that meets threshold
#             if snr_db >=  snr_percent_db(SNR_THRESHOLD_FACTOR, REFERENCE_MAX_SNR_DB):
#                 return new_beam, snr_db, direction * offset, max_power_dBm, beams_checked

#             # Otherwise, keep track of best beam so far
#             if snr_db > best_snr:
#                 best_snr = snr_db
#                 best_beam = new_beam
#                 best_power = max_power_dBm
#                 best_offset = direction * offset

#     # No beam passed threshold → fallback to best SNR found
#     return best_beam, best_snr, best_offset, best_power, beams_checked


# NeighborSearch Algorithm (With Guardrails ±10 Beams)
def search_nearby_beams_guarded(center_beam, child_rx, rx_streamer, Txsock=None):
    best_beam = center_beam
    best_snr = -np.inf
    best_power = -np.inf
    best_offset = 0
    beams_checked = 0

    # First, check the center beam
    run_interactive_command(child_rx, f'eder.rx.set_beam({center_beam})')

    rx_angle2 = rx_angle_from_index(center_beam)
    try:
        tx_index2 = tx_angle_index(rx_angle2)
    except ValueError:
        print(f"[ERROR] RX angle {rx_angle2} not found in TX_BEAM_ANGLES.")
        tx_index2 = 32  # fallback

    if Txsock:
        try:
            Txsock.send_string(f"SET_TX_BEAM:{tx_index2}")
            ack = Txsock.recv_string().strip()
            print(f"[ZMQ] TX server responded to beam set: {ack}")
        except socket.timeout:
            print(f"[SOCKET TIMEOUT] TX beam {tx_index2} send timed out.")
        except Exception as e:
            print(f"[SOCKET ERROR] {e}")

    recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
    metadata = uhd.types.RXMetadata()
    for _ in range(30):
        rx_streamer.recv(recv_signal, metadata)

    IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
    snr_db, _ = calculate_snr_with_min_noise_window(
        IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
    )
    beams_checked += 1

    if snr_db >= SNR_THRESHOLD:
        return center_beam, snr_db, 0, max_power_dBm, beams_checked

    # Search only ±10 beams
    best_snr = snr_db
    best_power = max_power_dBm
    for offset in range(1, 11):  # offset = 1 to 10
        for direction in [-1, 1]:
            new_beam = center_beam + direction * offset
            if new_beam < MIN_BEAM_INDEX or new_beam > MAX_BEAM_INDEX:
                continue

            run_interactive_command(child_rx, f'eder.rx.set_beam({new_beam})')
            rx_angle3 = rx_angle_from_index(new_beam)
            try:
                tx_index3 = tx_angle_index(rx_angle3)
            except ValueError:
                print(f"[ERROR] RX angle {rx_angle3} not found in TX_BEAM_ANGLES.")
                tx_index3 = 32  # fallback

            if Txsock:
                try:
                    Txsock.send_string(f"SET_TX_BEAM:{tx_index3}")
                    ack = Txsock.recv_string().strip()
                    print(f"[ZMQ] TX server responded to beam set: {ack}")
                except socket.timeout:
                    print(f"[SOCKET TIMEOUT] TX beam {tx_index3} send timed out.")
                except Exception as e:
                    print(f"[SOCKET ERROR] {e}")

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, _ = calculate_snr_with_min_noise_window(
                IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list
            )
            beams_checked += 1

            if snr_db >= SNR_THRESHOLD:
                return new_beam, snr_db, direction * offset, max_power_dBm, beams_checked

            if snr_db > best_snr:
                best_snr = snr_db
                best_beam = new_beam
                best_power = max_power_dBm
                best_offset = direction * offset

    return best_beam, best_snr, best_offset, best_power, beams_checked



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
                    print("[Jetson_YOLO_THREAD] No radio detected and no previous beam index.")
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

            run_interactive_command(child_rx, f'eder.rx.set_beam({Rx_center_beam_index})')
            rx_angle = rx_angle_from_index(Rx_center_beam_index)
            try:
                tx_index = tx_angle_index(rx_angle)
            except ValueError:
                print(f"[ERROR] RX angle {tx_index} not found in TX_BEAM_ANGLES.")
                tx_index = 32  # fallback
        

            if Txsock:
                try:
                    Txsock.send_string(f"SET_TX_BEAM:{tx_index}")
                    ack = Txsock.recv_string().strip()
                    print(f"[ZMQ] TX server responded to beam set: {ack}")

                except socket.timeout:
                    print(f"[SOCKET TIMEOUT] TX beam {tx_index} send timed out.")
                except Exception as e:
                    print(f"[SOCKET ERROR] {e}")
                
            

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_yolo, _ = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)
            if beam_index_str.isdigit():

                # --- Step 2: If SNR is high, keep YOLO beam ---
                if snr_yolo >= SNR_THRESHOLD:
                # if snr_yolo >= snr_percent_db(SNR_THRESHOLD_FACTOR, REFERENCE_MAX_SNR_DB):
                    selected_beam = Rx_center_beam_index
                    final_snr_db = snr_yolo
                    offset_error = 0
                    beams_checked = 1
                    adjustment_type = "YOLO"
                else:
                    # --- Step 3: Try adjusted beam (YOLO + avg offset) ---
                    avg_offset = int(np.mean(beam_offset_history)) if beam_offset_history else 0
                    adjusted_beam_index = Rx_center_beam_index + avg_offset
                    adjusted_beam_index = max(MIN_BEAM_INDEX, min(MAX_BEAM_INDEX, adjusted_beam_index))

                    run_interactive_command(child_rx, f'eder.rx.set_beam({adjusted_beam_index})')
                    rx_angle4 = rx_angle_from_index(adjusted_beam_index)
                    try:
                        tx_index4 = tx_angle_index(rx_angle4)
                    except ValueError:
                        print(f"[ERROR] RX angle {tx_index4} not found in TX_BEAM_ANGLES.")
                        tx_index4 = 32  # fallback

                    if Txsock:
                        try:
                            Txsock.send_string(f"SET_TX_BEAM:{tx_index4}")
                            ack = Txsock.recv_string().strip()
                            print(f"[ZMQ] TX server responded to beam set: {ack}")

                        except socket.timeout:
                            print(f"[SOCKET TIMEOUT] TX beam {tx_index4} send timed out.")
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
                        offset_error = avg_offset
                        beams_checked = 2
                        adjustment_type = "OffsetCorrected"
                    else:
                        # --- Step 4: Search nearby beams ---
                        selected_beam, final_snr_db, offset_error, max_power_dBm, beams_checked = search_nearby_beams(
                            adjusted_beam_index, child_rx,  rx_streamer, Txsock=Txsock
                        )
                        adjustment_type = "NeighborSearch"

                # --- Step 5: Update offset history 
                # beam_offset_history.append(offset_error)
                # --- Step 5: Update offset history only if SNR threshold is met ---
                threshold_met = (
                    final_snr_db is not None and
                    isinstance(final_snr_db, (int, float)) and
                    final_snr_db >= SNR_THRESHOLD 
                    # final_snr_db >= snr_percent_db(SNR_THRESHOLD_FACTOR, REFERENCE_MAX_SNR_DB)
                )

                if threshold_met:
                    beam_offset_history.append(offset_error)
                    print(f"[INFO] Offset {offset_error} added to moving average history.")
                else:
                    print("[INFO] Offset not added to history since SNR threshold was not met.")


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
            
            final_tx_index = None
            final_tx_angle = None
            try:
                if selected_beam is not None:
                    final_rx_angle = rx_angle_from_index(selected_beam)
                    final_tx_index = tx_angle_index(-final_rx_angle)
                    final_tx_angle = tx_angle_from_index(final_tx_index)
                else:
                    print("[WARNING] selected_beam is None. Skipping TX angle computation.")
            except Exception as e:
                print(f"[ERROR] Could not compute TX index from selected beam {selected_beam}: {e}")



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
                "TX Beam Index": final_tx_index,
                "TX Beam Angle": final_tx_angle,
                "Adjustment Method": [adjustment_type],
                "Beams Checked in Search": [beams_checked],
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

    time.sleep(4)

    # Initialize Directories
    main_directory = "Outdoor_Adaptive_Beamforming_SC/mavg_Results"
    os.makedirs(main_directory, exist_ok=True)
    
    Txsock = zmq_context.socket(zmq.REQ)

    Txsock.connect(f"tcp://{NUC_IP}:5555")


    try:
        Txsock.send_string("START_TX")
        print("[ZMQ] Sent START_TX to TX server.")

        ack = Txsock.recv_string().strip()
        if ack == "TX_READY":
            print("[ZMQ] Received TX_READY from TX server.")
        else:
            print(f"[ZMQ ERROR] Unexpected ACK: {ack}")
            return False
    except Exception as e:
        print(f"[ZMQ ERROR] Failed during START_TX handshake: {e}")
        return False


    # === Collect user inputs ===

 
    # Automatically get date in 'apr3' format
    today = datetime.datetime.today()
    date = today.strftime("%b").lower() + str(today.day)


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
        "Algorithm": "Adaptive Beamforming + Mavg",
        
       
    }

    setup_logging(experiment_dir)
    save_experiment_metadata(experiment_dir, experiment_name,metadata_content)
    
    # Initialize USRP
    print("\n[INFO] Initializing USRP...")
    usrp, rx_streamer, _ = initialize_usrp()

    #Initialize Sivers
    child_rx, logfile_rx,_ = initialize_sivers_RX(experiment_dir)

    
    # Start the camera capture thread
    capture_thread = threading.Thread(target=YOLO_RX, args=(usrp, rx_streamer, child_rx,experiment_dir,Txsock,), daemon=True)
    capture_thread.start()
    
    # Allow everything to get set up before starting
    time.sleep(1.5)
    print("[MAIN] Synchronizing both threads now...")
    start_event.set()  # Unblocks both threads simultaneously

    capture_thread.join()

    
    # Disable Sivers devices
    print("\nDisabling the Sivers receiver .....")
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
 
    
