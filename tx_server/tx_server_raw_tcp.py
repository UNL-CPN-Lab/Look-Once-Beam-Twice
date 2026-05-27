import socket
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
    # Spawn the interactive command
    # Open a log file in binary write mode
    logfile_tx = open("logfile_tx.txt", "wb")
    child_tx = pexpect.spawn('sudo ./start_sivers.sh <SIVERS_TX_SERIAL_ALT>', timeout=None)  # No timeout

    # Set the logfile attribute of the child object
    child_tx.logfile = logfile_tx

    try:
        # Check for the password prompt
        index = child_tx.expect(['\[sudo\] password for .+: ', pexpect.TIMEOUT], timeout=10)
        
        if index == 0:
            # Password prompt found, send the password
            child_tx.sendline('<SUDO_PASSWORD>')
            print('Sent password.')
        else:
            # No password prompt, continue
            print('No password prompt found, continuing...')
    except pexpect.EOF:
        print("The process has exited prematurely.")
    
    # Enable the transmitter
    run_interactive_command(child_tx, 'eder.init()')
    run_interactive_command(child_tx, 'eder.tx_setup(60.48e9)')
    run_interactive_command(child_tx, 'eder.tx_enable()')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_gain\',0x03)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bb_iq_gain\',0xFF)')
    run_interactive_command(child_tx, 'eder.regs.wr(\'tx_bfrf_gain\',0xFF)')

    return child_tx, logfile_tx

def handle_client_connection(conn, child_tx, logfile_tx):
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            print(f"[SERVER] Received from client: {data}")

            if data == "START_TX":
                # Initialize and enable transmitter
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

            conn.send(response.encode())

    except Exception as e:
        print(f"[SERVER ERROR] {e}")

    finally:
        print("[SERVER] Connection closed.")


def main():
    host = '0.0.0.0'  # server will bind to all available interfaces
    port = 5002  # port to listen on

    child_tx, logfile_tx = start_sivers_transmitter()

    server_socket = socket.socket()  # instantiate
    server_socket.bind((host, port))  # bind to the port
    server_socket.listen(1)  # configure how many clients the server can listen to simultaneously
    print("Server is listening on port", port)

    while True:
        conn, address = server_socket.accept()  # accept new connection
        print("Connection from: " + str(address))
        handle_client_connection(conn, child_tx, logfile_tx)

if __name__ == '__main__':
    main()