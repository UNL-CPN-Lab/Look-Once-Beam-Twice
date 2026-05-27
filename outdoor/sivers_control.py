# sivers_control.py

import os
import time
import pexpect
import sys



# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from configurations.utils import run_interactive_command


def initialize_sivers(experiment_dir):
    """
    Initializes the Sivers transmitter and receiver.
    
    Args:
        experiment_dir (str): Directory to store log files.
    
    Returns:
        child_tx (pexpect.spawn): Sivers transmitter process.
        child_rx (pexpect.spawn): Sivers receiver process.
        logfile_tx (file object): Log file for transmitter.
        logfile_rx (file object): Log file for receiver.
        setup_time (float): Time taken to initialize both Sivers devices.
    """
    start_time = time.time()

    print("Initializing Sivers Transmitter...")
    child_tx = pexpect.spawn('./start.sh <SIVERS_TX_SERIAL>')
    logfile_tx_path = os.path.join(experiment_dir, "logfile_tx.txt")
    logfile_tx = open(logfile_tx_path, "wb")
    child_tx.logfile = logfile_tx

    child_tx.expect('\[sudo\] password for .+: ')
    child_tx.sendline('<SUDO_PASSWORD>')
    
    run_interactive_command(child_tx, 'eder.init()')
    run_interactive_command(child_tx, 'eder.tx_setup(60.48e9)')
    run_interactive_command(child_tx, 'eder.tx_enable()')

    #dont touch tx_bb_gain: keep it max at 0x03
    #set all same: FOR 13db = 0XDD, 14db = 0XEE, 15db = 0XFF
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_gain\',0x03)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_iq_gain\',0x88)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bfrf_gain\',0x88)')

    print("Initializing Sivers Receiver...")
    child_rx = pexpect.spawn('./start.sh <SIVERS_RX_SERIAL>')
    logfile_rx_path = os.path.join(experiment_dir, "logfile_rx.txt")
    logfile_rx = open(logfile_rx_path, "wb")
    child_rx.logfile = logfile_rx

    child_rx.expect('\[sudo\] password for .+: ')
    child_rx.sendline('<SUDO_PASSWORD>')

    run_interactive_command(child_rx, 'eder.init()')
    run_interactive_command(child_rx, 'eder.rx_setup(60.48e9)')
    run_interactive_command(child_rx, 'eder.rx_enable()')

    #set all same: FOR 13db = 0XDD, 14db = 0XEE, 15db = 0XFF
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bfrf\',0xF)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb1\',0x88)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb2\',0x88)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb3\',0x88)')
    time.sleep(2) 

    setup_time = time.time() - start_time
    return child_tx, child_rx, logfile_tx, logfile_rx, setup_time



def initialize_sivers_RX(experiment_dir):
    """
    Initializes the Sivers transmitter and receiver.
    
    Args:
        experiment_dir (str): Directory to store log files.
    
    Returns:
        child_tx (pexpect.spawn): Sivers transmitter process.
        child_rx (pexpect.spawn): Sivers receiver process.
        logfile_tx (file object): Log file for transmitter.
        logfile_rx (file object): Log file for receiver.
        setup_time (float): Time taken to initialize both Sivers devices.
    """
    start_time = time.time()

    # print("Initializing Sivers Transmitter...")
    # child_tx = pexpect.spawn('./start.sh <SIVERS_TX_SERIAL_ALT>')
    # logfile_tx_path = os.path.join(experiment_dir, "logfile_tx.txt")
    # logfile_tx = open(logfile_tx_path, "wb")
    # child_tx.logfile = logfile_tx

    # child_tx.expect('\[sudo\] password for .+: ')
    # child_tx.sendline('<SUDO_PASSWORD>')
    
    # run_interactive_command(child_tx, 'eder.init()')
    # run_interactive_command(child_tx, 'eder.tx_setup(60.48e9)')
    # run_interactive_command(child_tx, 'eder.tx_enable()')

    # #dont touch tx_bb_gain: keep it max at 0x03
    # #set all same: FOR 13db = 0XDD, 14db = 0XEE, 15db = 0XFF
    # run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_gain\',0x03)')
    # run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_iq_gain\',0xDD)')
    # run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bfrf_gain\',0xDD)')

    print("Initializing Sivers Receiver...")
    child_rx = pexpect.spawn('./start.sh <SIVERS_RX_SERIAL>')
    logfile_rx_path = os.path.join(experiment_dir, "logfile_rx.txt")
    logfile_rx = open(logfile_rx_path, "wb")
    child_rx.logfile = logfile_rx

    child_rx.expect('\[sudo\] password for .+: ')
    child_rx.sendline('<SUDO_PASSWORD>')

    run_interactive_command(child_rx, 'eder.init()')
    run_interactive_command(child_rx, 'eder.rx_setup(60.48e9)')
    run_interactive_command(child_rx, 'eder.rx_enable()')

    #set all same: FOR 13db = 0XDD, 14db = 0XEE, 15db = 0XFF
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bfrf\',0xF)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb1\',0x99)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb2\',0x99)')
    run_interactive_command(child_rx, 'eder.regs.wr(\'rx_gain_ctrl_bb3\',0x99)')

    setup_time = time.time() - start_time
    return  child_rx, logfile_rx, setup_time

