"""USRP B200-mini configuration shim used by the fullsweep scripts.

Exposes `uhd_builder(...)` — initialises the USRP with internal clock + time
source, sets TX/RX rate / gain / bandwidth / antenna / centre frequency, and
returns `(tx_streamer, rx_streamer, usrp)` ready for streaming. Defaults are
1 MS/s sample rate, 480 MHz tune frequency, `sc16` over-the-wire / `fc32`
host-side format, single channel.

Replace `<USRP_SERIAL>` with your USRP's serial before running (find it via
`uhd_find_devices`).

Author: Avhishek Biswas
"""

from gnuradio import uhd as gnu_uhd
import uhd
import time

import logging


from distutils.version import StrictVersion



def uhd_builder(args="",gain=70,rate=1e6,otw="sc16",cpu="fc32"):
    """Initialise the USRP and return (tx_streamer, rx_streamer, usrp).

    Args:
        args (str): Unused passthrough placeholder (kept for compatibility).
        gain (float): Unused — caller sets gain on the streamer directly. The
            internal `set_tx_gain(0)` / `set_rx_gain(0)` calls intentionally
            leave the USRP at unity so amplification is controlled externally
            (Sivers chain).
        rate (float): Sample rate in samples/sec; also used as TX/RX bandwidth.
        otw (str): On-the-wire IQ format. `"sc16"` = 16-bit complex.
        cpu (str): Host-side IQ format. `"fc32"` = 32-bit float complex.

    Returns:
        list[tx_streamer, rx_streamer, usrp]
    """
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
