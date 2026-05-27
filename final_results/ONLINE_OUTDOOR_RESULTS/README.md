# Online outdoor results

Recorded results from the **online (live-SNR) outdoor** experiments — UNL campus, UE radio mounted on a vehicle moving along an 80 m straight path, SNR measured in real time. Outdoor is online-only (no offline-replay tree).

Produced by the runners in [outdoor/](../../outdoor/).

## Variants

| Folder | Method | Runner |
|---|---|---|
| `VIBE_MA_RESULTS/` | VIBE-MA — moving-average offset tracking (main proposed) | [outdoor_online_main_mavg.py](../../outdoor/outdoor_online_main_mavg.py) |
| `VIBE_MLP_RESULTS/` | VIBE-MLP — learned offset | [outdoor_online_main_mlp.py](../../outdoor/outdoor_online_main_mlp.py) |
| `VIBE_YOLOR_RESULTS/` | VIBE-YOLOR — camera prior only, no closed loop | [outdoor_online_main_basic.py](../../outdoor/outdoor_online_main_basic.py) |

There is no `VIBE_MA_ABS` (ablation) outdoors. `VIBE_MA_RESULTS/` is organized by vehicle speed × search mode (`1mph_guarded/`, `1mph_noguard/`, `5mph_*`, `8mph_*`, each with its own README); `VIBE_MLP_RESULTS/` and `VIBE_YOLOR_RESULTS/` use experiment-name dirs directly. Leaf folders contain `results_<exp>.csv`, post-processed CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
