# VIBE-MA — online outdoor results

Results for **VIBE-MA** (moving-average offset tracking, the main proposed method) from the outdoor experiments — UNL campus, UE radio mounted on a vehicle moving along an 80 m straight path, SNR measured in real time.

- **Produced by:** [outdoor/outdoor_online_main_mavg.py](../../../outdoor/outdoor_online_main_mavg.py)
- **Algorithm:** YOLO-predicted beam → if below threshold, correct by `prediction + mean(offset history)` → else nearby-beam search. Offsets that meet the threshold feed the moving-average history.

## Layout

Organized by **vehicle speed × search mode**, each with its own README:

- `1mph_guarded/`, `5mph_guarded/`, `8mph_guarded/` — guarded search (restricted beam-index range around the prediction).
- `1mph_noguard/`, `5mph_noguard/`, `8mph_noguard/` — unguarded search (full sweep on fallback).

All runs are at TX gain 9 dB / RX gain 12 dB over a 16 m link. Each leaf run dir contains `results_<exp>.csv`, post-processed CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
