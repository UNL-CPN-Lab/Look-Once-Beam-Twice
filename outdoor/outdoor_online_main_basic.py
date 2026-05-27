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
zmq_context = zmq.Context()

last_valid_yolo_beam = None  # add this at the top of YOLO_RX as a persistent state
start_event = threading.Event()
beam_index_str = None  # Initialize beam_index_str to store the last valid beam index from YOLO





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
    send_jetson_hello = time.time()
    hello_msg = f"HELLO:{experiment_name}"
    sock.sendall(hello_msg.encode())
    response = sock.recv(1024).decode().strip()
    received_jetson_hello = time.time()-send_jetson_hello
    print(f"[MSI YOLO_THREAD] Jetson HELLO response: {response}")


    print(f"[MSI YOLO_THREAD] Jetson HELLO response: {response}")

    start_time = usrp.get_time_now().get_real_secs() + INIT_DELAY
    
    Rx_center_beam_index = 32  # default
    metadata = uhd.types.RXMetadata()
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = False
    stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
    rx_streamer.issue_stream_cmd(stream_cmd)


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
            
            # metadata = uhd.types.RXMetadata()
            # stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
            # stream_cmd.stream_now = False
            # stream_cmd.time_spec = uhd.types.TimeSpec(start_time)
            # rx_streamer.issue_stream_cmd(stream_cmd)

            
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + f"_{now.microsecond // 1000:03d}"
             
            jetson_comm_start_time = time.time()  # Start time for communication with Jetson
            message = f"DETECT:{currentrotorangle}:{timestamp}"
            sock.sendall(message.encode())
            beam_index_str = sock.recv(1024).decode().strip()
            jetson_comm_time = time.time() - jetson_comm_start_time
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
            set_tx_beam_time = time.time()

            # run_interactive_command(child_tx, f'eder.tx.set_beam({Rx_center_beam_index})')
            rx_angle = rx_angle_from_index(Rx_center_beam_index)
            try:
                tx_index = tx_angle_index(-rx_angle)
            except ValueError:
                print(f"[ERROR] RX angle {rx_angle} not found in TX_BEAM_ANGLES.")
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
                    
            tx_beam_setting_time = time.time() - set_tx_beam_time
            
            set_rx_beam_time = time.time()

            run_interactive_command(child_rx, f'eder.rx.set_beam({Rx_center_beam_index})')
            
            rx_beam_setting_time = time.time() - set_rx_beam_time
            
            received_data_time_start = time.time()

            recv_signal = np.zeros(SAMPLE_SIZE, dtype=np.complex64)
            stabilization_start = time.time()
            for _ in range(30):
                rx_streamer.recv(recv_signal, metadata)
            stabilization_time = time.time() - stabilization_start

            IQ_power_dBm, _, max_power_dBm = calculate_power_metrics(recv_signal)
            snr_db, _ = calculate_snr_with_min_noise_window(IQ_power_dBm, window_size=PADDING, noise_power_list=noise_power_list)
            receive_time = time.time() - received_data_time_start
            
            try:
                final_rx_angle = rx_angle_from_index(Rx_center_beam_index)
                final_tx_index = tx_angle_index(final_rx_angle)
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
                "Rx Beam Angle": final_rx_angle,
                "Tx Beam Index": final_tx_index,
                "Tx Beam Angle": final_tx_angle,
                "SNR (dB)": [snr_db],
                "YOLO Time (s)": [yolo_processing_time],
                "Data Receiving Time (s)": [receive_time],
                "TX Beam setting time(s)": [tx_beam_setting_time],
                "RX Beam setting time(s)": [rx_beam_setting_time],
                "Jetson Communication Time (s)": [jetson_comm_time],
                "Received hello jetson(s)": [received_jetson_hello],
                "Stabilization Time (s)": [stabilization_time]
            }
            df = pd.DataFrame(csv_data)
            if not os.path.exists(csv_filename):
                df.to_csv(csv_filename, index=False)
            else:
                df.to_csv(csv_filename, mode='a', header=False, index=False)  # Do not write header again

        

            print()
            print(f"[YOLO THREAD] Computed SNR for angle {currentrotorangle}, Beam Index: {Rx_center_beam_index}, SNR: {snr_db} dB, Max Power: {max_power_dBm} dBm")
            print()
    except KeyboardInterrupt:
        print("[YOLO_RX] Keyboard interrupt received. Exiting YOLO_RX thread.")


            


def main():
    """Main function to control servo, handle YOLO detection, and plot SNR vs. rotor angle."""

    time.sleep(4)

    # Initialize Directories
    main_directory = "Outdoor_Adaptive_Beamforming_SC/yolor_Results"
    os.makedirs(main_directory, exist_ok=True)
    
    # === Step 1: Create ZMQ socket to remote TX server ===
    Txsock = zmq_context.socket(zmq.REQ)
    Txsock.connect(f"tcp://{NUC_IP}:5555")


    # === Step 2: Tell TX server to begin Sivers setup ===
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
        "Algorithm": "Adaptive Beamforming"
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
 
    
