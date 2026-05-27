"""USRP B200-mini configuration shim used by the ground-truth collection scripts.

Replace `<USRP_SERIAL>` with your USRP's serial before running.


"""

from gnuradio import uhd as gnu_uhd
import uhd
import time

import logging


from distutils.version import StrictVersion


# Initialise the USRP and return (tx_streamer, rx_streamer, usrp); defaults
# are 1 MS/s sample rate, 480 MHz centre, sc16 over-the-wire / fc32 host-side.
def uhd_builder(args="",gain=70,rate=1e6,otw="sc16",cpu="fc32"):
    # init usrp
    usrp=uhd.usrp.MultiUSRP(",".join(("serial=<USRP_SERIAL>", "dboard_clock_rate=20e6")))

    print("USRP Creating .... ")
    usrp.set_clock_source("internal")
    usrp.set_time_source("internal")
    print("Setting device timestamp to 0...")
    usrp.set_time_now(uhd.types.TimeSpec(0.0))
 
    ## configure RF
    usrp.set_tx_rate(rate)
    usrp.set_tx_gain(0)
    usrp.set_tx_antenna("TX/RX")
    usrp.set_tx_bandwidth(rate)    
    usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(480e6), 0)


    usrp.set_rx_rate(rate)
    usrp.set_rx_gain(0)
    usrp.set_rx_antenna("RX2")
    usrp.set_rx_bandwidth(rate)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(480e6), 0)

    ## extract streamer
    st_args = uhd.usrp.StreamArgs(cpu, otw)
    st_args.channels=[0]
    
    tx_streamer = usrp.get_tx_stream(st_args)
    rx_streamer = usrp.get_rx_stream(st_args)

    print("")
    print(" USRP created .... ")
    return[tx_streamer,rx_streamer,usrp]
