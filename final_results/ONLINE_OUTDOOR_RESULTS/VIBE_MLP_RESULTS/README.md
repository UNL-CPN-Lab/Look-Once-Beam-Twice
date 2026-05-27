# VIBE-MLP — online outdoor results

Results for **VIBE-MLP** (learned offset correction) from the outdoor experiments — UNL campus, UE radio mounted on a moving vehicle, SNR measured in real time.

- **Produced by:** [outdoor/outdoor_online_main_mlp.py](../../../outdoor/outdoor_online_main_mlp.py)
- **Algorithm:** YOLO-predicted beam → if below threshold, correct by `prediction + MLP(features)` where the offset is predicted by a small trained network → else nearby-beam search.

## Layout

Experiment-name dirs directly (no speed/guard split), TX gain 9 dB / RX gain 12 dB over a 16 m link, July 24:

- `sc_jul24_gain9db_12db_16m_t1/`
- `nh_jul24_gain9db_12db_16m_t2/`

Each leaf run dir contains `results_<exp>.csv`, post-processed CSVs, `metadata.json` (logs vehicle speed, threshold, etc.), and per-metric plots (PNG).

Author: Apala Pramanik
