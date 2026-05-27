import serial # type: ignore
import time



def move_servo_to_angle(arduino, current_angle, target_angle):
    """
    Moves the servo from current_angle to target_angle using a persistent serial connection.

    Parameters:
        arduino (serial.Serial): An open serial connection to the Arduino.
        current_angle (int): The servo's current position (0° to 180°).
        target_angle (int): The desired angle to move to (0° to 180°).

    Returns:
        int: The updated current angle after movement.
    """

    print(f"Moving servo from {current_angle}° to {target_angle}°.")

    if target_angle != current_angle:
        step = 1 if target_angle > current_angle else -1

        for angle in range(current_angle, target_angle + step, step):
            arduino.reset_input_buffer()  # Clear any previous junk
            arduino.write(f"{angle}\n".encode())  # Send angle
            #time.sleep(step_delay)  # Allow servo & Arduino to react

            try:
                response = arduino.readline().decode(errors="replace").strip()
                if response:
                    print(f"[Arduino] {response}")
                else:
                    print("[Warning] No response from Arduino.")
            except Exception as e:
                print(f"[Error] Failed to read response: {e}")

    print(f"Reached {target_angle}°.\n")
    return target_angle


if __name__ == "__main__":
    serial_port = "/dev/ttyACM0"
    baud_rate = 115200
    angle = 90  # Initial angle

    try:
        arduino = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(0.5)  # wait for Arduino reset
  
        angle = move_servo_to_angle(arduino, angle,0) # adjust the angle as needed
        time.sleep(1)  # wait for the servo to stabilize
      

        arduino.close()

    except serial.SerialException as e:
        print(f"[Serial Error] {e}")
