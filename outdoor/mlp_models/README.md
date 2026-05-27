# Outdoor · MLP datasets + scalers + weights

Trained artifacts and training data for the outdoor VIBE-MLP variant. These files are loaded by the `*_mlp.py` runners (canonical + alt_runners) and produced by [../mlp_training/](../mlp_training/).

## What's here

| File | Role |
|---|---|
| `offset_dataset_<name>.csv` | Training data — rows of `[Boresight, snr_thresh_db, YOLO-predicted beam, Initial SNR, Offset Error]` aggregated from prior VIBE-MA runs. Consumed by `train_mlp.py`. |
| `offset_scaler_<name>.pkl` | `sklearn.preprocessing.StandardScaler` fitted on the input columns of the dataset. Same `<name>` as the matching dataset/model. The runners load this and call `scaler.transform(...)` before forward-passing the MLP. |
| `offset_mlp_model_<name>.pt` | Trained PyTorch state dict for `OffsetMLP` (3 hidden layers, 128 units each). **Not bundled with the repo** — train one with `python3 ../mlp_training/train_mlp.py` after building a dataset. |

The `<name>` suffix indicates the recording location and date / camera (e.g. `nh_outdoor`, `sc_outdoor`, `sc`). Pair a `_scaler` and a `_model` with the dataset they were trained on.

## Naming convention

| Suffix | Meaning |
|---|---|
| `_nh_outdoor` | Nebraska Hall outdoor campus dataset |
| `_sc_outdoor` | Schorr Center outdoor dataset |
| `_sc` | (Older) Schorr Center indoor-style outdoor dataset |

## Which file does each runner load?

| Runner | Weights | Scaler |
|---|---|---|
| [../outdoor_online_main_mlp.py](../outdoor_online_main_mlp.py) | `offset_mlp_model_nh_outdoor.pt` | `offset_scaler_nh_outdoor.pkl` |
| [../alt_runners/tcp_mlp.py](../alt_runners/tcp_mlp.py) | `offset_mlp_model_sc.pt` | `offset_scaler_sc.pkl` |
| [../alt_runners/usb_mlp.py](../alt_runners/usb_mlp.py) | `offset_mlp_model_sc.pt` | `offset_scaler_sc.pkl` |

Edit those filenames in the runner if you want to swap in a different trained pair.

## Adding a new trained model

1. Build the dataset: `cd ../mlp_training && python3 dataset_mlp_new.py` — appends to `offset_dataset_<name>.csv` in this folder.
2. Train: `python3 train_mlp.py` — writes `offset_mlp_model_<name>.pt` + `offset_scaler_<name>.pkl` into this folder.
3. Update the `torch.load(...)` / `joblib.load(...)` filenames in the runner you want to use.

Author: Apala Pramanik
