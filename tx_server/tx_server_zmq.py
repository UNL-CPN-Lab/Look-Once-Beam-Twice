import zmq
import os
import pexpect
import time
import sys

# Add the repo root to sys.path so the `configurations` package is importable
# when this server is launched from inside the tx_server/ folder.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from configurations.utils import run_interactive_command


def start_sivers_transmitter():
    '''
    Start the Sivers Transmitter
    '''
    print("Sivers Transmitter Initializing .....")
    logfile_tx = open("logfile_tx.txt", "wb")
    child_tx = pexpect.spawn('sudo ./start_sivers.sh <SIVERS_TX_SERIAL_ALT>', timeout=None)
    child_tx.logfile = logfile_tx

    try:
        index = child_tx.expect(['\[sudo\] password for .+: ', pexpect.TIMEOUT], timeout=10)
        if index == 0:
            child_tx.sendline('<SUDO_PASSWORD>')
            print('Sent password.')
        else:
            print('No password prompt found, continuing...')
    except pexpect.EOF:
        print("The process has exited prematurely.")

    run_interactive_command(child_tx, 'eder.init()')
    run_interactive_command(child_tx, 'eder.tx_setup(60.48e9)')
    run_interactive_command(child_tx, 'eder.tx_enable()')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_gain\',0x03)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_iq_gain\',0xFF)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bfrf_gain\',0xFF)')

    return child_tx, logfile_tx


def handle_zmq_server(socket, child_tx, logfile_tx):
    while True:
        try:
            data = socket.recv_string().strip()
            print(f"[SERVER] Received from client: {data}")

            if data == "START_TX":
                run_interactive_command(child_tx, 'eder.init()')
                run_interactive_command(child_tx, 'eder.tx_setup(60.48e9)')
                run_interactive_command(child_tx, 'eder.tx_enable()')
                run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_gain\',0x03)')
                run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_iq_gain\',0xFF)')
                run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bfrf_gain\',0xFF)')
                response = "TX_READY"

            elif data.startswith("SET_TX_BEAM:"):
                try:
                    tx_beam = int(data.split(":")[1])
                    tx_command = f'eder.tx.set_beam({tx_beam})'
                    run_interactive_command(child_tx, tx_command)
                    response = f"TX_BEAM_SET:{tx_beam}"
                except ValueError:
                    response = "ERROR: Invalid beam index"

            elif data == "STOP_TX":
                print("\nDisabling the Sivers transmitter...")
                run_interactive_command(child_tx, 'eder.tx_disable()')
                logfile_tx.close()
                print("TX log file closed.\n")
                response = "TX_STOPPED"

            else:
                response = "ERROR: Unknown command"

            socket.send_string(response)

        except Exception as e:
            print(f"[ZMQ SERVER ERROR] {e}")
            socket.send_string("ERROR: Internal server error")


def main():
    port = 5555  # must match the ZMQ clients in outdoor/outdoor_online_main_*.py

    # Start the Sivers hardware
    child_tx, logfile_tx = start_sivers_transmitter()

    # ZMQ setup
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{port}")
    print(f"[ZMQ SERVER] Listening on port {port}...")

    handle_zmq_server(socket, child_tx, logfile_tx)


if __name__ == '__main__':
    main()
