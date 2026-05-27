# VIBE-YOLOR — online outdoor results

Results for **VIBE-YOLOR** (camera prior only, no closed loop) from the outdoor experiments — UNL campus, UE radio mounted on a moving vehicle, SNR measured in real time. Open-loop baseline: the beam is taken directly from the YOLO prediction with no offset correction or search.

- **Produced by:** [outdoor/outdoor_online_main_basic.py](../../../outdoor/outdoor_online_main_basic.py)
- **Algorithm:** YOLO-predicted beam selected as-is. No threshold-triggered correction or nearby-beam search — the gap between this and the closed-loop variants is the value the loop adds.

## Layout

Experiment-name dirs directly (no speed/guard split), TX gain 9 dB / RX gain 12 dB over a 16 m link, July 13–14:

- `sc_jul13_gain9db_12db_16m_t1/`
- `nh_jul14_gain9db_12db_16m_t1/` … `t3/`

Each leaf run dir contains `results_<exp>.csv`, post-processed CSVs, `metadata.json` (logs vehicle speed, threshold, etc.), and per-metric plots (PNG).

Author: Apala Pramanik
