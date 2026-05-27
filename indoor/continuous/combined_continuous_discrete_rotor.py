import serial
import time

# === CONFIGURATION ===
SERIAL_PORT = "/dev/ttyACM0"  # Adjust based on your system (e.g., COM3 on Windows)
BAUD_RATE = 115200
WAIT_TIME = 2  # Time to wait for Arduino to initialize

# === CONNECT TO ARDUINO ===
def connect_to_arduino():
    print(f"[INFO] Connecting to {SERIAL_PORT} at {BAUD_RATE}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(WAIT_TIME)
    print("[INFO] Connected.")
    return ser

# === SEND DISCRETE ROTATION COMMAND ===
def send_discrete_command(ser, angle):
    command = f"D:{angle}\n"
    print(f"[TEST] Sending discrete command: {command.strip()}")
    ser.write(command.encode())
    time.sleep(1)

# === SEND CONTINUOUS ROTATION COMMAND ===
def send_continuous_command(ser, duration_ms):
    command = f"C:{duration_ms}\n"
    print(f"[TEST] Sending continuous command: {command.strip()}")
    ser.write(command.encode())
    # Wait for full sweep to complete
    time.sleep(duration_ms / 1000 + 2)

# === MAIN TEST FUNCTION ===
def main():
    ser = connect_to_arduino()

    # === DISCRETE TEST: Sweep from 45° to 135° in 1° steps ===
    # for angle in range(45, 136, 1):
    send_discrete_command(ser, 0)

    # # === CONTINUOUS TEST: Full sweep in 10 seconds ===
    # send_continuous_command(ser, 10000)

    ser.close()
    print("[INFO] Test complete.")

if __name__ == "__main__":
    main()
