/*
 * combined_rotor_motion.ino
 *
 * Arduino firmware for the UE-side rotor used in VIBE indoor experiments.
 * The UE (with the Sivers RX radio + camera) is mounted on the servo;
 * rotating the servo changes the UE's heading, which emulates the vehicle
 * motion that occurs in the outdoor V2X scenario. The YOLO camera detector
 * on the UE then tracks the (stationary) BS as the UE rotates past it.
 *
 * Serial protocol (115200 baud, line-terminated with \n):
 *   D:<angle>          Discrete: step to <angle> (0..360°) and stop. Used to
 *                      dwell at a target angle during ground-truth capture.
 *   C:<time_in_ms>     Continuous forward: sweep 0° -> 180° smoothly over
 *                      <time_in_ms> milliseconds. Used during live runs.
 *   R:<time_in_ms>     Continuous reverse: same as C but 180° -> 0°.
 *
 * Acknowledgements emitted on Serial after each command:
 *   "Moved to: <angle>°"    after a successful D: command
 *   "Sweep complete."       after C: / R: complete
 *   "Invalid ..."           on bad input
 *
 * Host-side drivers live in each indoor runner folder as
 * `combined_continuous_discrete_rotor.py`.
 *
 * Authors: Avhishek Biswas and Apala Pramanik
 */

#include <Servo.h>

Servo servo;
const int servoPin = 3;           // Servo PWM signal pin
int currentAngle = 0;             // Last commanded angle (0..360°)
bool isSweeping = false;          // True while a C: / R: continuous sweep is running

/**
 * setup()
 *
 * Initialise serial + servo, park the servo at 0°, and print a usage banner
 * the host driver can ignore.
 */
void setup() {
    Serial.begin(115200);
    servo.attach(servoPin);
    moveServoToAngle(0);
    currentAngle = 0;

    Serial.println("Ready.");
    Serial.println("To rotate in DISCRETE mode, send: D:<angle>");
    Serial.println("To rotate in CONTINUOUS mode, send: C:<time_in_ms>");
}

/**
 * loop()
 *
 * Poll the serial port for one command, dispatch by prefix (D: / C: / R:),
 * and emit an ack or error response. New commands are ignored while a
 * continuous sweep is in progress (gated by `isSweeping`) so the host
 * driver can safely send the next command only after seeing the
 * "Sweep complete." line.
 */
void loop() {
    if (!isSweeping && Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();

        // --- D: discrete step to a target angle ---
        if (input.startsWith("D:")) {
            int targetAngle = input.substring(2).toInt();
            if (targetAngle >= 0 && targetAngle <= 360) {
                rotateServoDiscrete(targetAngle);
                Serial.print("Moved to: ");
                Serial.print(targetAngle);
                Serial.println("°");
            } else {
                Serial.println("Invalid DISCRETE angle. Must be 0–360.");
            }

        // --- C: continuous forward sweep (0° -> 180°) ---
        } else if (input.startsWith("C:")) {
            long totalTime_ms = input.substring(2).toInt();
            if (totalTime_ms > 0) {
                Serial.print("Starting CONTINUOUS sweep over ");
                Serial.print(totalTime_ms);
                Serial.println(" ms...");

                isSweeping = true;
                rotateServoContinuous(totalTime_ms);
                isSweeping = false;

                Serial.println("Sweep complete.");
            } else {
                Serial.println("Invalid CONTINUOUS time. Must be > 0.");
            }

        // --- R: continuous reverse sweep (180° -> 0°) ---
        } else if (input.startsWith("R:")) {
            long totalTime_ms = input.substring(2).toInt();
            if (totalTime_ms > 0) {
                Serial.print("Starting CONTINUOUS sweep over ");
                Serial.print(totalTime_ms);
                Serial.println(" ms...");

                isSweeping = true;
                rotateServoContinuousReverse(totalTime_ms);
                isSweeping = false;

                Serial.println("Sweep complete.");
            } else {
                Serial.println("Invalid CONTINUOUS time. Must be > 0.");
            }

        // --- unrecognised input ---
        } else {
            Serial.println("Invalid input. Use D:<angle> or C:<time_in_ms>");
        }
    }
}

/**
 * rotateServoDiscrete(targetAngle)
 *
 * Step one degree at a time from `currentAngle` to `targetAngle` with a
 * 10 ms pause between steps. Stepping (rather than jumping straight to
 * the target) prevents the servo from drawing a current spike and keeps
 * the rotor's angular velocity bounded, which matters when the radio
 * payload on the rotor is heavy.
 *
 * @param targetAngle  Destination angle in degrees (0..360°).
 */
void rotateServoDiscrete(int targetAngle) {
    int stepDelay = 10;  // ms per 1° step — tune for servo torque + payload mass

    if (targetAngle == currentAngle) return;

    if (targetAngle > currentAngle) {
        for (int angle = currentAngle + 1; angle <= targetAngle; angle++) {
            moveServoToAngle(angle);
            delay(stepDelay);
        }
    } else {
        for (int angle = currentAngle - 1; angle >= targetAngle; angle--) {
            moveServoToAngle(angle);
            delay(stepDelay);
        }
    }

    currentAngle = targetAngle;
}

/**
 * rotateServoContinuousReverse(totalTime_ms)
 *
 * Smooth sweep from 180° down to 0° over `totalTime_ms` milliseconds. Used
 * for the return leg of two-way trajectories. Parks the servo at 180° first
 * (with a 1 s settle), then walks down in 1° steps with `totalTime_ms / 180`
 * delay between steps.
 *
 * @param totalTime_ms  Total sweep duration in milliseconds (> 0).
 */
void rotateServoContinuousReverse(long totalTime_ms) {
    moveServoToAngle(180);
    currentAngle = 180;
    delay(1000);  // let the servo settle at the start point

    int stepSize = 1;
    int steps = 180 / stepSize;
    long delayPerStep = totalTime_ms / steps;

    for (int angle = 180; angle >= 0; angle -= stepSize) {
        moveServoToAngle(angle);
        delay(delayPerStep);
    }

    currentAngle = 0;
}


/**
 * rotateServoContinuous(totalTime_ms)
 *
 * Smooth sweep from 0° up to 180° over `totalTime_ms` milliseconds. This is
 * the primary trajectory used during live VIBE experiments: the host driver
 * converts a target speed (°/s) into the right millisecond duration via
 * `configurations/utils.get_rotation_time_ms()`. Parks at 0° first (with a
 * 1 s settle), then walks up in 1° steps with `totalTime_ms / 180` delay
 * between steps.
 *
 * @param totalTime_ms  Total sweep duration in milliseconds (> 0).
 */
void rotateServoContinuous(long totalTime_ms) {
    moveServoToAngle(0);
    currentAngle = 0;
    delay(1000);  // let the servo settle at the start point

    int stepSize = 1;
    int steps = 180 / stepSize;
    long delayPerStep = totalTime_ms / steps;

    for (int angle = 0; angle <= 180; angle += stepSize) {
        moveServoToAngle(angle);
        delay(delayPerStep);
    }

    currentAngle = 180;
}

/**
 * moveServoToAngle(angle)
 *
 * Low-level primitive used by all three motion modes above. Clamps `angle`
 * into [0°, 360°] and converts it to a PWM pulse width in the servo's
 * accepted range (800..1970 µs for this hobby servo). The mapping was
 * calibrated empirically for the testbed's servo; **calibrate for your own
 * servo by adjusting the `map(angle, 0, 360, 800, 1970)` call** if your
 * mechanical sweep range or pulse-width range differs.
 *
 * Also echoes the new angle on Serial as "Angle: <angle>" so the host
 * driver can track motion progress.
 *
 * @param angle  Target angle in degrees; clamped to [0, 360].
 */
void moveServoToAngle(int angle) {
    angle = constrain(angle, 0, 360);
    int pwmSignal = map(angle, 0, 360, 800, 1970);
    servo.writeMicroseconds(pwmSignal);

    Serial.print("Angle: ");
    Serial.println(angle);
}
