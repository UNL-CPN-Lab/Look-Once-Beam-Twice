# usrp_control.py

import uhd
import time
import uhd_conf as ucf

def initialize_usrp():
    """
    Initializes the USRP and returns the necessary handles.
    
    Returns:
        usrp (uhd.usrp.MultiUSRP): USRP instance.
        rx_streamer (uhd.usrp.Streamer): Receiver streamer instance.
        setup_time (float): Time taken to initialize the USRP.
    """
    start_time = time.time()
    tx_streamer, rx_streamer, usrp = ucf.uhd_builder(args="", gain=76, rate=1e6)
    setup_time = time.time() - start_time
    return usrp, rx_streamer, setup_time