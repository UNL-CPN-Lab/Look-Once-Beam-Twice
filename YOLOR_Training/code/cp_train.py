"""Headless trainer for any Camera-Primed model.

Usage
-----
  python cp_train.py --model 1                 # probe + ETA only (safe)
  python cp_train.py --model 1 --run           # real training to convergence
  python cp_train.py --model 1 --run --fresh   # ignore existing last.pt

Behaviour
---------
- safe by default: omit `--run` and the script does a 1-epoch timing probe +
  ETA only, then exits (no long run by accident)
- resume-aware: if `last.pt` exists, training resumes from it (SLURM
  preemption-then-resubmit is transparent); override with `--fresh`
- lightweight status log: a 2-hourly status line at
  `logs/<run_name>_status.log` for cluster-side tailing
- YOLOR_RUN_NAME env var overrides the run dir name (lets two parallel trainings
  of the same model land in separate runs/<name>/, status logs, and sentinels)

Training is *only* training — no in-callback metric reading or custom
best-checkpoint selection. All eval + final-model selection happens in
`cp_eval.py` (separate process): Ultralytics' in-training-process
per-class mAP is unreliable for `coco_passthrough=False` models, but a
standalone `model.val()` is fine.
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import cp_config as cfg

STATUS_EVERY_H = 2.0


# --- small helpers ----------------------------------------------------------

def _fmt_seconds(s: float) -> str:
    return str(timedelta(seconds=int(s)))


def run_name(model_id: int) -> str:
    """Name of the `runs/<name>/` subdir (and status log, and sentinel).
    Overridable via YOLOR_RUN_NAME — lets two parallel runs of the same model
    land in their own dirs without colliding."""
    return os.environ.get("YOLOR_RUN_NAME", cfg.model_name(model_id))


def last_ckpt(model_id: int) -> Path:
    return cfg.RUNS / run_name(model_id) / "weights" / "last.pt"


def data_yaml_for(model_id: int) -> Path:
    nm = cfg.model_name(model_id)
    y = cfg.DATASETS_BUILD / nm / f"{nm}_data.yaml"
    if not y.exists():
        raise FileNotFoundError(
            f"{y} missing. Run the data-prep step first "
            f"(01_pseudolabel + 02_coco_replay/materialize).")
    return y


def _print_release_note(save_dir) -> None:
    """Point the reader at the released checkpoint (`last.pt`, not `best.pt`).
    `best.pt` is COCO-fitness-biased here."""
    w = Path(save_dir) / "weights"
    last = w / "last.pt"
    if last.exists():
        print(f"[done] converged model -> {last}")
        print(f"[done] (ignore {w/'best.pt'} - Ultralytics fitness pick, "
              f"COCO-biased; cp_eval picks the released checkpoint)")
    else:
        print(f"[done] no last.pt at {last} - run did not complete")


# --- status logger callback -------------------------------------------------

def _status_logger_cb(model_id: int, total_epochs: int):
    """Return an `on_fit_epoch_end` callback that writes a status line at most
    every 2h (plus one at the final epoch). The callback closes over
    `state` so it can remember the last write time across calls."""
    nm = run_name(model_id)                      # honors YOLOR_RUN_NAME
    log = cfg.LOGS / f"{nm}_status.log"
    state = {"t0": time.time(), "last": 0.0}

    def cb(trainer):
        now = time.time()
        ep = trainer.epoch + 1
        # rate-limit: skip unless 2h have passed OR this is the final epoch
        if now - state["last"] < STATUS_EVERY_H * 3600 and ep < total_epochs:
            return
        state["last"] = now
        elapsed = now - state["t0"]
        per_ep = elapsed / max(ep, 1)
        eta = per_ep * (total_epochs - ep)
        m = getattr(trainer, "metrics", {}) or {}
        line = (f"{datetime.now():%Y-%m-%d %H:%M:%S} | {nm} "
                f"| epoch {ep}/{total_epochs} "
                f"| mAP50={m.get('metrics/mAP50(B)', float('nan')):.4f} "
                f"| mAP50-95={m.get('metrics/mAP50-95(B)', float('nan')):.4f} "
                f"| elapsed={_fmt_seconds(elapsed)} | eta={_fmt_seconds(eta)}")
        with open(log, "a") as f:
            f.write(line + "\n")
        print("[STATUS] " + line, flush=True)

    return cb, log


# --- training stages --------------------------------------------------------

def _build_common_kwargs(model_id: int) -> dict:
    """Hyperparameters + hardware-specific overrides, ready to splat into
    `YOLO.train(**kwargs)`."""
    hp = cfg.hardware_profile()
    common = dict(cfg.TRAIN_HYP)
    common.update(imgsz=hp["imgsz"], batch=hp["batch"], device=0,
                  project=str(cfg.RUNS), data=str(data_yaml_for(model_id)))
    return common


def _resume_from_checkpoint(ckpt: Path, model_id: int, total_epochs: int) -> None:
    """SLURM preemption-resubmit path: load `last.pt` and resume the schedule."""
    from ultralytics import YOLO
    print(f"=== Camera-Primed: RESUME {run_name(model_id)} from {ckpt} ===")
    cb, log = _status_logger_cb(model_id, total_epochs)
    print(f"[resume] 2-hour status -> {log}")
    rmodel = YOLO(str(ckpt))
    rmodel.add_callback("on_fit_epoch_end", cb)
    res = rmodel.train(resume=True)
    _print_release_note(res.save_dir)


def _probe_one_epoch(model_id: int, common: dict, total_epochs: int) -> float:
    """Train one quick epoch (no mosaic close, no save) just to estimate the
    per-epoch wall time. Returns the wall seconds the probe took (which
    over-estimates because it includes one-time dataset caching)."""
    from ultralytics import YOLO
    print("\n[probe] timing 1 epoch (includes one-time caching; over-estimates)...")
    t0 = time.time()
    m = YOLO(cfg.stock_yolo11x())
    probe = dict(common)
    probe.update(epochs=1, close_mosaic=0, save_period=-1,
                 name=f"{run_name(model_id)}_probe",
                 exist_ok=True, verbose=False)
    m.train(**probe)
    t1 = time.time() - t0
    eta = t1 * total_epochs
    print(f"[probe] 1 epoch ~= {_fmt_seconds(t1)}")
    print(f"[ETA ] full {total_epochs} ep  ~= {_fmt_seconds(eta)}  "
          f"(finish ~ {datetime.now() + timedelta(seconds=eta):%Y-%m-%d %H:%M})")
    return t1


def _fresh_full_train(model_id: int, common: dict, total_epochs: int) -> None:
    """From-scratch training run. Reuses `common` (already has imgsz/batch/data)."""
    from ultralytics import YOLO
    print("\n[run] starting full training ...")
    cb, log = _status_logger_cb(model_id, total_epochs)
    print(f"[run] 2-hour status -> {log}")
    model = YOLO(cfg.stock_yolo11x())
    model.add_callback("on_fit_epoch_end", cb)
    res = model.train(name=run_name(model_id), exist_ok=True, **common)
    _print_release_note(res.save_dir)


# --- top-level orchestrator -------------------------------------------------

def train(model_id: int, run: bool, fresh: bool = False):
    """Train one Camera-Primed model.

    Three modes (decided by args + on-disk state):
      - `run=False`               : probe + ETA only (safe default, no long run)
      - `run=True` + ckpt exists  : resume from `last.pt` (transparent to SLURM)
      - `run=True` + ckpt missing
        or `fresh=True`           : 1-epoch probe + full from-scratch training
    """
    common = _build_common_kwargs(model_id)
    epochs = cfg.TRAIN_HYP["epochs"]

    # Resume path (SLURM preempt-resubmit).
    ckpt = last_ckpt(model_id)
    if run and not fresh and ckpt.exists():
        _resume_from_checkpoint(ckpt, model_id, epochs)
        return

    # Header for fresh / probe-only runs.
    hp = cfg.hardware_profile()
    print(f"=== Camera-Primed train: {run_name(model_id)} (model {model_id}) ===")
    print(f"  data   : {common['data']}")
    print(f"  init   : {cfg.stock_yolo11x()}")
    print(f"  gpu    : {hp['gpu']}  imgsz={hp['imgsz']} batch={hp['batch']}")
    print(f"  epochs : {epochs}  save_period={cfg.TRAIN_HYP.get('save_period', -1)}")

    _probe_one_epoch(model_id, common, epochs)

    if not run:
        print("\n[safe] probe only. Re-run with --run to start the full training.")
        return

    _fresh_full_train(model_id, common, epochs)


# --- CLI --------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", type=int, default=1, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--run", action="store_true",
                    help="actually train (omit = probe + ETA only)")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore an existing checkpoint and start from scratch")
    a = ap.parse_args()
    train(a.model, a.run, a.fresh)
