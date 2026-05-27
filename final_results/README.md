# Final results

Curated experiment results backing the figures and tables in the paper. Each experiment directory holds its per-step result CSVs, a `metadata.json` config snapshot, and per-metric plots. 

## Tree

```
final_results/
├── ONLINE_INDOOR_RESULTS/     # live-SNR indoor runs
│   ├── VIBE_MA_RESULTS/       #   VIBE-MA (moving-average offset)
│   ├── VIBE_MA_ABS_RESULTS/   #   VIBE-MA ablation (no history fallback)
│   ├── VIBE_MLP_RESULTS/      #   VIBE-MLP (learned offset)
│   └── VIBE_YOLOR_RESULTS/    #   VIBE-YOLOR (camera prior only)
├── OFFLINE_INDOOR_RESULTS/    # replayed-SNR indoor runs (same 4 variants)
│   └── VIBE_{MA,MA_ABS,MLP,YOLOR}_RESULTS/
└── ONLINE_OUTDOOR_RESULTS/    # live-SNR outdoor runs (UNL campus)
    ├── VIBE_MA_RESULTS/       #   split by speed × guard: {1,5,8}mph_{guarded,noguard}/
    ├── VIBE_MLP_RESULTS/
    └── VIBE_YOLOR_RESULTS/    #   (no MA-ABS ablation outdoors)
```

### Sub-structure

- **Indoor variant folders** split by camera FOV: `nfov_results/` (Intel RealSense D435, 60°) and `wfov_results/` (Luxonis OAK-D, 90°). `VIBE_MA_ABS_RESULTS` is NFOV-only (no split).
- **Outdoor `VIBE_MA_RESULTS`** splits by vehicle speed and search mode: `1mph_guarded/`, `1mph_noguard/`, `5mph_*`, `8mph_*`. `VIBE_MLP_RESULTS` / `VIBE_YOLOR_RESULTS` use experiment-name dirs directly.
- **Leaf (per-experiment) folders** are named `<location>_<date>_gain<g>_<dist>_<test>` and contain:
  - `results_<exp>.csv` — per-step log (rotor/boresight angle, YOLO-predicted beam, selected beam, SNR, adjustment method, timing).
  - `cleaned_results_<exp>.csv`, `balanced_results_<exp>.csv` — post-processed by `eval.py`.
  - `metadata.json` — config snapshot (location, gain, distance, threshold, algorithm).
  - Per-metric plots (`*_<exp>.png` shipped): `number_of_beams_checked`, `offset_error_deg`, SNR/outage, etc.
  - A per-FOV summary `online_evaluation_experiments_results_summary_<date>.csv`.

## Which code produced each tree

| Results tree | Produced by | Variant → runner |
|---|---|---|
| `ONLINE_INDOOR_RESULTS/` | [indoor/continuous/online/](../indoor/continuous/online/) orchestrators | `VIBE_MA` → `automatic_indoor_evaluations_mavg/`, `VIBE_MA_ABS` → `..._mavg_absent/`, `VIBE_MLP` → `..._mlp/`, `VIBE_YOLOR` → `..._basic/` |
| `OFFLINE_INDOOR_RESULTS/` | [indoor/continuous/offline/](../indoor/continuous/offline/) orchestrators | same variant→folder mapping under `offline/` |
| `ONLINE_OUTDOOR_RESULTS/` | [outdoor/](../outdoor/) runners | `VIBE_MA` → [outdoor_online_main_mavg.py](../outdoor/outdoor_online_main_mavg.py), `VIBE_MLP` → [outdoor_online_main_mlp.py](../outdoor/outdoor_online_main_mlp.py), `VIBE_YOLOR` → [outdoor_online_main_basic.py](../outdoor/outdoor_online_main_basic.py) |

The variant tokens map to the paper methods: **VIBE-MA** = moving-average offset tracking (main proposed), **VIBE-MLP** = learned offset, **VIBE-YOLOR** = camera-prior baseline, **VIBE-MA-ABS** = MA ablation with the history fallback disabled. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the full variant ↔ algorithm mapping.

## Notes

- These are *recorded* results — to regenerate, run the corresponding runner against your own hardware/ground truth (see each runner folder's README).
- Only PNG plots are tracked; the SVG/EPS copies are gitignored (vector formats are large and redundant with the PNGs).

Author: Apala Pramanik
