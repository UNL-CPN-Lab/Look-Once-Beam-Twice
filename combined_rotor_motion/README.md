# Arduino rotor firmware

Arduino sketch that drives the rotor servo used to emulate UE motion in the **indoor** experiments (the outdoor experiments use a real moving vehicle, no servo). Implements a simple serial command protocol over `/dev/ttyACM0` @ 115200 baud.

## Command protocol

| Command | Meaning |
|---|---|
| `D:<angle>` | **Discrete.** Step to `<angle>` (0–360°) and stop. Used during ground-truth capture to dwell at each target angle. |
| `C:<ms>` | **Continuous forward.** Sweep 0° → 180° smoothly over `<ms>` milliseconds. Used during the live experiment. |
| `R:<ms>` | **Continuous reverse.** Same as `C:` but 180° → 0°. |

The sketch acknowledges every command (`Moved to: <angle>°` for discrete, `Sweep complete.` for continuous) so host-side scripts can poll for completion. Invalid commands are echoed with an error message.

## Hardware

- Single hobby servo on pin 3.
- PWM mapping: `angle ∈ [0°, 360°]` → `pulse ∈ [800, 1970] µs` (`servo.writeMicroseconds`). Calibrate this map for your specific servo by adjusting the `map(angle, 0, 360, 800, 1970)` line if your servo's mechanical range differs.
- Discrete step delay: 10 ms per degree.
- Continuous mode: 1° step granularity, delay-per-step = `totalTime_ms / 180`.

## Flashing

```bash
# In the Arduino IDE: open combined_rotor_motion.ino, select your board (e.g. Uno),
# select the USB port, and click Upload.
#
# Or from the command line with arduino-cli:
arduino-cli compile --fqbn arduino:avr:uno combined_rotor_motion
arduino-cli upload  --fqbn arduino:avr:uno --port /dev/ttyACM0 combined_rotor_motion
```

## Host-side driver

The Python host driver lives in each indoor runner folder as `combined_continuous_discrete_rotor.py` and exposes:

- `send_discrete_command(ser, angle)` — sends `D:<angle>\n`
- `send_continuous_command(ser, duration_ms)` — sends `C:<duration_ms>\n` and waits for `Sweep complete.`

The outdoor experiments do not import these — the UE is mounted on a real vehicle moving along the test path, so no serial commands are issued from the runner.

See [docs/HARDWARE.md](../docs/HARDWARE.md) for wiring and full host-side details.

Author: Apala Pramanik
