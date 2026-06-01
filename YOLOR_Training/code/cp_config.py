"""Single source of truth for the Camera-Primed retraining pipeline.

Every notebook and script imports paths, dataset registries, the class scheme,
and training hyperparameters from here, so the same code runs on the local
workstation and on the HCC/NRDStor cluster with zero edits.

Project root resolution
-----------------------
1. env `YOLOR_ROOT` (set this in SLURM)
2. first of the known candidates that exists on disk (local, then cluster)

Common overrides (full list at the bottom):
  YOLOR_EPOCHS  YOLOR_BATCH  YOLOR_IMGSZ  YOLOR_PATIENCE  YOLOR_REPLAY_N  YOLOR_MIXUP
"""
from __future__ import annotations

import os
from pathlib import Path

# Reduce CUDA fragmentation on the 12GB shared A2000 (display also uses ~1.6GB).
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


# --- project paths -----------------------------------------------------------

_ROOT_CANDIDATES = [
    "/media/workstation/BiswasFam/VIBE/YOLO_DatasetsandTraining",          # local A2000 box (legacy)
    "/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining",    # HCC / NRDStor (legacy)
]


def _resolve_root() -> Path:
    # 1. Explicit override.
    env = os.environ.get("YOLOR_ROOT")
    if env:
        p = Path(env).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"YOLOR_ROOT={env} does not exist")
        return p
    # 2. Walk up from this file looking for a parent containing YOLOR_Training/.
    #    Makes the release portable: a fresh clone of curly-winner just works.
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "YOLOR_Training").is_dir():
            return parent
    # 3. Author-machine fall-backs (legacy A2000 / HCC layout).
    for c in _ROOT_CANDIDATES:
        if Path(c).exists():
            return Path(c)
    raise FileNotFoundError(
        "Could not locate YOLOR_Training/. Set YOLOR_ROOT to the directory "
        "that contains YOLOR_Training/, or to a directory that contains the "
        "Datasets/ folder.")


PROJECT_ROOT = _resolve_root()
YOLOR_DIR = PROJECT_ROOT / "YOLOR_Training"
DATASETS_ROOT = YOLOR_DIR / "Datasets"

# WORKDIR is where ALL writes go (checkpoints, COCO, logs, P1 labels).
# Defaults to YOLOR_DIR (the project drive locally, NRDStor on HCC); override with
# YOLOR_WORK if you want a different write target. The local drive is
# exFAT (no journaling) — a transient fsync error can interrupt a long run;
# recovery is per-epoch last.pt + save_period=5 + cp_train auto-resume.
WORKDIR = Path(os.environ.get("YOLOR_WORK", YOLOR_DIR)).expanduser()
OUTPUTS = WORKDIR / "outputs"
LOGS = WORKDIR / "logs"
RUNS = WORKDIR / "runs"                # Ultralytics project dir (all training runs)
DATASETS_BUILD = WORKDIR / "datasets"  # symlinked combined datasets + data.yaml

for _d in (WORKDIR, OUTPUTS, LOGS, RUNS, DATASETS_BUILD):
    _d.mkdir(parents=True, exist_ok=True)


def labels_p1_dir(dataset_key: str, split_dirname: str) -> Path:
    """Where the merged P1 labels for one dataset/split live. Auto-created."""
    d = WORKDIR / "labels_p1" / dataset_key / split_dirname
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- source datasets ---------------------------------------------------------
# Same on local and cluster — relative paths only.

DATASETS = {
    "cots":        DATASETS_ROOT / "IndoorCOTSDataset",
    "outdoor":     DATASETS_ROOT / "5G_BaseStation",
    "commercial":  DATASETS_ROOT / "Commercial-mmWave",
    "streetlight": DATASETS_ROOT / "Streetlights",
}

# Streetlights uses 'valid' instead of 'val' on disk.
SPLIT_DIRNAMES = {"cots": "val", "outdoor": "val",
                  "commercial": "val", "streetlight": "valid"}

# `outdoor/train` has ~11k UNLABELLED extras (near-duplicates the user
# deliberately discarded). Feeding them would (a) reintroduce the redundancy
# the user removed and (b) act as pure background — poisoning custom-class
# learning the same way `nc=1` does to COCO classes. So for `outdoor` we
# keep only images that have a manual label. (Cots is fully labelled;
# commercial / streetlight have no extras.)
LABELED_ONLY = {"outdoor"}


# --- class scheme (locked 2026-05-18) ----------------------------------------
# COCO 0-79 always preserved. Custom classes start at 80.

COCO_NC = 80

CUSTOM_BY_MODEL = {
    1: {"name": "cots",        "classes": {80: "radio"}},
    2: {"name": "outdoor",     "classes": {80: "5G BS", 81: "LampPost"}},
    3: {"name": "commercial",  "classes": {80: "radio", 81: "mmWave radio"}},
    4: {"name": "streetlight", "classes": {80: "streetlight"}},
    5: {"name": "unified",     "classes": {80: "radio", 81: "5G BS",
                                           82: "LampPost", 83: "mmWave radio",
                                           84: "streetlight"}},
}

# Source label class id -> our scheme. `coco_passthrough=True` keeps source
# COCO ids 0-79 unchanged (only datasets that carry real manual COCO boxes).
# Custom ids go through `map`. Anything else is DROPPED (returns None).
MANUAL_REMAP = {
    "cots":        {"coco_passthrough": True,  "map": {80: 80}},
    "outdoor":     {"coco_passthrough": True,  "map": {82: 80, 83: 81}},
    "commercial":  {"coco_passthrough": False, "map": {0: 80, 1: 81}},
    "streetlight": {"coco_passthrough": False, "map": {0: 80}},
}


def remap_manual_class(dataset_key: str, cls: int):
    """Translate a source label class id to the model's scheme. Returns the
    new id, or None if the box should be dropped (unmapped + not a passthrough
    COCO id)."""
    r = MANUAL_REMAP[dataset_key]
    if cls in r["map"]:
        return r["map"][cls]
    if r["coco_passthrough"] and 0 <= cls < COCO_NC:
        return cls
    return None


# --- model registry ----------------------------------------------------------
# Used as the run dir (`runs/<name>/`), combined dataset dir + data.yaml, the
# 2-hour status log filename, and the SLURM job name. Keep these stable once a
# run has started — renaming mid-run breaks resume/checkpoint paths.

MODEL_NAMES = {
    1: "YOLOR-radio",         # COCO 0-79 + radio                  (IndoorCOTS)
    2: "YOLOR-5GBS",          # COCO 0-79 + 5G BS, LampPost        (Outdoor)
    3: "YOLOR-comm-mmWave",   # COCO 0-79 + mmWave radio           (IndoorCommercial)
    4: "YOLOR-Streetlights",  # COCO 0-79 + streetlight            (Streetlights)
    5: "YOLOR",               # COCO 0-79 + all five (combined release)
}


def model_name(model_id: int) -> str:
    """Canonical release name for a model id."""
    return MODEL_NAMES[model_id]


COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag",
    "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon",
    "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
    "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant",
    "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]
assert len(COCO_NAMES) == COCO_NC


def names_for_model(model_id: int) -> dict[int, str]:
    """Full {idx: name} map for `model_id` = COCO 0-79 + this model's customs."""
    m = {i: n for i, n in enumerate(COCO_NAMES)}
    m.update(CUSTOM_BY_MODEL[model_id]["classes"])
    return m


# --- COCO data ---------------------------------------------------------------
# Used for replay-training AND retention eval. Pre-stage COCO on HCC and set
# YOLOR_COCO to skip the download step.

COCO_DIR = Path(os.environ.get("YOLOR_COCO", WORKDIR / "coco"))
COCO_REPLAY_TRAIN_IMAGES = int(os.environ.get("YOLOR_REPLAY_N", "8000"))


# --- stock teacher weights ---------------------------------------------------

def stock_yolo11x() -> str:
    """Path to the stock yolo11x.pt (teacher for P1 + training init).
    Falls back to the Ultralytics auto-download name if no local copy found."""
    env = os.environ.get("YOLOR_YOLO11X")
    if env and Path(env).exists():
        return env
    for c in [PROJECT_ROOT / "RawDataset" / "yolo11x.pt",
              PROJECT_ROOT / "models 2" / "yolo11x.pt",
              YOLOR_DIR / "yolo11x.pt"]:
        if c.exists():
            return str(c)
    return "yolo11x.pt"


# --- hardware profile -> imgsz / batch ---------------------------------------

def _gpu_name() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
    except Exception:
        pass
    return "cpu"


def hardware_profile() -> dict:
    """Pick imgsz and batch from GPU class. Override with YOLOR_IMGSZ / YOLOR_BATCH.

    On the 12GB A2000 we pin a small batch (autobatch misjudges with the
    desktop also using GPU memory and OOMs mid-run); ≥32GB cards get batch 8.
    """
    gpu = _gpu_name()
    big = any(k in gpu for k in ("V100", "A100", "A40", "H100", "RTX 6000",
                                 "A6000", "L40"))
    imgsz = int(os.environ.get("YOLOR_IMGSZ", "768" if big else "640"))
    batch = int(os.environ.get("YOLOR_BATCH", "8" if big else "4"))
    return {"gpu": gpu, "imgsz": imgsz, "batch": batch, "big_gpu": big}


# --- training recipe ---------------------------------------------------------
# Reconciled recipe: user's aug stack + cos_lr + close_mosaic for clean late
# epochs. `imgsz` / `batch` come from hardware_profile (above) at use-time.

TRAIN_HYP = dict(
    epochs=int(os.environ.get("YOLOR_EPOCHS", "200")),

    # patience=0 DISABLES Ultralytics' early-stop. Required: the combined val
    # is ~92% COCO, so Ultralytics' fitness (0.1*mAP50 + 0.9*mAP50-95) is
    # highest at ~epoch 1 (model still ≈ stock COCO-expert), and mosaic
    # suppresses val mAP until close_mosaic. Any finite patience would
    # early-stop on the near-stock epoch-1 checkpoint. Let cos_lr +
    # close_mosaic run the full schedule; cp_eval picks the released model.
    patience=int(os.environ.get("YOLOR_PATIENCE", "0")),

    lr0=0.01,
    weight_decay=0.0005,
    save_period=5,
    cos_lr=True,
    warmup_epochs=5,
    close_mosaic=20,

    augment=True,
    mosaic=1.0,
    mixup=0.1,             # user used 0.2; 0.1 is the rigor value (YOLOR_MIXUP overrides)
    fliplr=0.5,
    hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
    translate=0.1,
    scale=0.5,
    shear=0.0,

    seed=0,
    verbose=True,
)
if os.environ.get("YOLOR_MIXUP"):
    TRAIN_HYP["mixup"] = float(os.environ["YOLOR_MIXUP"])


# --- yaml writer -------------------------------------------------------------

def write_data_yaml(path: Path, train, val, test, names: dict[int, str]) -> Path:
    """Write an Ultralytics data.yaml. `train`/`val`/`test` may be a single
    path or a list of paths; `names` is an {idx: name} dict."""
    import yaml

    def _norm(x):
        return [str(p) for p in x] if isinstance(x, (list, tuple)) else str(x)

    cfg_data = {
        "train": _norm(train),
        "val":   _norm(val),
        "test":  _norm(test),
        "nc":    len(names),
        "names": {int(k): v for k, v in sorted(names.items())},
    }
    path = Path(path)
    with open(path, "w") as f:
        yaml.safe_dump(cfg_data, f, default_flow_style=False, sort_keys=False)
    return path


# --- CLI summary -------------------------------------------------------------

def summary() -> None:
    """Print a one-screen summary of resolved config (useful sanity check)."""
    hp = hardware_profile()
    print("Camera-Primed config")
    print(f"  PROJECT_ROOT : {PROJECT_ROOT}")
    print(f"  on cluster?  : {'NRDStor' in str(PROJECT_ROOT)}")
    print(f"  YOLOR_DIR       : {YOLOR_DIR}")
    print(f"  COCO_DIR     : {COCO_DIR}  (exists={COCO_DIR.exists()})")
    print(f"  stock yolo11x: {stock_yolo11x()}")
    print(f"  GPU          : {hp['gpu']}")
    print(f"  imgsz/batch  : {hp['imgsz']} / {hp['batch']}")
    print(f"  epochs       : {TRAIN_HYP['epochs']}  (patience {TRAIN_HYP['patience']})")
    for d, p in DATASETS.items():
        print(f"  dataset[{d:11s}]: {p}  (exists={p.exists()})")


# --- env-var reference -------------------------------------------------------
#   YOLOR_ROOT     override project root (set in SLURM on HCC)
#   YOLOR_WORK     override write target (default = YOLOR_DIR)
#   YOLOR_COCO     path to a pre-staged COCO dir (skip download)
#   YOLOR_YOLO11X  path to stock yolo11x.pt
#   YOLOR_EPOCHS  YOLOR_PATIENCE          training schedule
#   YOLOR_IMGSZ   YOLOR_BATCH             hardware overrides
#   YOLOR_MIXUP   YOLOR_REPLAY_N          recipe / data-slice overrides
#   YOLOR_FORCE_PSEUDO=1               redo a split that's already pseudo-labelled


if __name__ == "__main__":
    summary()
