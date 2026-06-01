"""Paper-grade standalone evaluation for any Camera-Primed model.

Two numbers per model:

  COCO retention      : per-class mAP50-95 ratio finetuned/stock on COCO val2017
                        (1.0 = no catastrophic forgetting; <1.0 = degraded).
  Custom-class skill  : mAP50-95 for each of this model's custom classes on its
                        own custom test split (no COCO images mixed in).

Why standalone
--------------
The training process does NO custom metric reading and NO best-checkpoint
selection callback — those hit an Ultralytics in-training-process quirk that
misreports per-class mAP for `coco_passthrough=False` models. Running val in
this separate process is the verified-correct path (the same checkpoint that
reads `custom=0.0` during training scores ~0.83 here).

Output
------
- `outputs/<model_name>_eval.csv` — full per-class table.
- Printed markdown summary (paper-table-friendly).

Usage
-----
  python cp_eval.py --model 5
  python cp_eval.py --model 3 --weights runs/YOLOR-comm-mmWave/weights/last.pt
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cp_config as cfg


# --- yaml + checkpoint helpers ----------------------------------------------

def _coco_val_yaml(model_id: int) -> Path:
    """Write (and return) a data.yaml whose `val:` = COCO val2017, with the
    full {idx: name} map for this model. Used by COCO-retention measurement."""
    nm = cfg.model_name(model_id)
    base = cfg.DATASETS_BUILD / nm
    cv = base / "coco_val" / "images"
    if not cv.exists():
        raise FileNotFoundError(
            f"{cv} missing — run the coco-replay/materialize prep first")
    y = base / f"{nm}_cocoval.yaml"
    cfg.write_data_yaml(y, train=cv, val=cv, test=cv,
                        names=cfg.names_for_model(model_id))
    return y


def _default_checkpoint(model_id: int) -> Path:
    """The released model = `runs/<name>/weights/last.pt`. We deliberately
    do NOT use Ultralytics' `best.pt` — its fitness is COCO-dominated here
    and tends to pick an early near-stock epoch."""
    last = cfg.RUNS / cfg.model_name(model_id) / "weights" / "last.pt"
    if not last.exists():
        raise FileNotFoundError(f"no last.pt at {last}")
    return last


# --- core: per-class mAP via standalone val ---------------------------------

def _per_class_map(weights: str, data_yaml: Path, split: str = "val"
                   ) -> dict[int, tuple[str, float]]:
    """Run `model.val()` and return {class_id: (class_name, mAP50-95)} for
    every class that appears in Ultralytics' `ap_class_index` (i.e. classes
    the validator actually processed). Defaults match standard YOLO reporting
    (conf=0.001, iou=0.7)."""
    from ultralytics import YOLO
    m = YOLO(weights)
    r = m.val(data=str(data_yaml), split=split, project=str(cfg.RUNS),
              name="cp_eval_tmp", exist_ok=True, verbose=False,
              plots=False, save_json=False)
    names = r.names if hasattr(r, "names") else m.names
    return {int(i): (names[int(i)], float(r.box.maps[int(i)]))
            for i in r.box.ap_class_index}


# --- evaluation steps -------------------------------------------------------

def _coco_retention(stock_pt: str, fine_pt: str, model_id: int):
    """Run COCO val2017 twice (stock baseline + finetuned), return both dicts."""
    coco_yaml = _coco_val_yaml(model_id)
    print(f"[1/3] COCO val2017 — stock baseline ...")
    stock_per = _per_class_map(stock_pt, coco_yaml, "val")
    print(f"[2/3] COCO val2017 — {cfg.model_name(model_id)} ...")
    fine_per = _per_class_map(fine_pt, coco_yaml, "val")
    return stock_per, fine_per


def _custom_class_skill(fine_pt: str, model_id: int) -> dict[int, tuple[str, float]]:
    """Run the model's own custom test split, return {cid: (name, mAP)} for
    each of this model's custom class ids (filling 0.0 for any not measured)."""
    nm = cfg.model_name(model_id)
    print(f"[3/3] custom classes — {nm} test split ...")
    yaml = cfg.DATASETS_BUILD / nm / f"{nm}_data.yaml"
    test_per = _per_class_map(fine_pt, yaml, "test")
    return {cid: (cname, test_per.get(cid, (cname, 0.0))[1])
            for cid, cname in cfg.CUSTOM_BY_MODEL[model_id]["classes"].items()}


# --- output: CSV + markdown -------------------------------------------------

def _write_eval_csv(out_path: Path,
                    stock_per: dict[int, tuple[str, float]],
                    fine_per:  dict[int, tuple[str, float]],
                    custom_ap: dict[int, tuple[str, float]]) -> None:
    """Write the per-class CSV (80 COCO rows + 5 custom rows + a blank gap)."""
    with open(out_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["class_id", "class_name", "stock_mAP50_95",
                    "finetuned_mAP50_95", "retention"])
        for cid in range(cfg.COCO_NC):
            cname = cfg.COCO_NAMES[cid]
            b = stock_per.get(cid, (cname, 0.0))[1]
            f = fine_per.get(cid, (cname, 0.0))[1]
            ret = (f / b) if b > 1e-9 else float("nan")
            w.writerow([cid, cname, f"{b:.4f}", f"{f:.4f}",
                        f"{ret:.4f}" if ret == ret else "nan"])
        w.writerow([])
        w.writerow(["# custom classes (custom test split)"])
        w.writerow(["class_id", "class_name", "stock_mAP50_95",
                    "finetuned_mAP50_95", "retention"])
        for cid, (cname, ap) in custom_ap.items():
            w.writerow([cid, cname, "", f"{ap:.4f}", ""])


def _mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def _print_summary(model_id: int, ft: Path,
                   stock_per, fine_per, custom_ap, csv_path: Path) -> None:
    """Paper-table-friendly markdown summary printed to stdout."""
    nm = cfg.model_name(model_id)
    rets = [fine_per.get(c, (None, 0.0))[1] / stock_per[c][1]
            for c in stock_per if stock_per[c][1] > 1e-9]
    stock_mean = _mean([v[1] for v in stock_per.values()])
    fine_mean = _mean([v[1] for v in fine_per.values()])
    mean_custom = _mean([ap for _, ap in custom_ap.values()])
    mean_ret = _mean(rets)

    # 8 worst-retained COCO classes
    rows = []
    for cid, (cname, sb) in stock_per.items():
        if sb < 1e-9:
            continue
        fb = fine_per.get(cid, (cname, 0.0))[1]
        rows.append((cid, cname, sb, fb, fb / sb))
    worst = sorted(rows, key=lambda r: r[4])[:8]

    print(f"\n## {nm} — paper-grade eval\n")
    print(f"- checkpoint: `{ft.name}`")
    print(f"- mean COCO retention vs stock: **{mean_ret:.3f}** "
          f"(1.0 = no forgetting)")
    print(f"- stock mean COCO mAP50-95: {stock_mean:.3f}  →  "
          f"finetuned: {fine_mean:.3f}")
    print(f"- custom classes (mean mAP50-95: **{mean_custom:.3f}**):")
    for cid, (cname, ap) in custom_ap.items():
        print(f"  - **{cname}** (id {cid}): mAP50-95 = **{ap:.3f}**")
    print(f"\nWorst-retained COCO classes:\n")
    print("| class | stock | finetuned | retention |")
    print("|---|---|---|---|")
    for _, cname, sb, fb, rr in worst:
        print(f"| {cname} | {sb:.3f} | {fb:.3f} | {rr:.3f} |")
    print(f"\nFull per-class table → `{csv_path}`")


# --- main entry point -------------------------------------------------------

def evaluate_model(model_id: int, weights: str | None = None) -> Path:
    """Evaluate one Camera-Primed model. Writes the CSV, prints the summary,
    returns the CSV path. Override `weights` to evaluate a non-default
    checkpoint (e.g. a post-hoc-selected epoch)."""
    nm = cfg.model_name(model_id)
    ft = Path(weights) if weights else _default_checkpoint(model_id)
    if not ft.exists():
        raise FileNotFoundError(f"fine-tuned weights not found: {ft}")
    stock = cfg.stock_yolo11x()

    print(f"=== cp_eval: {nm} (model {model_id}) ===")
    print(f"  finetuned : {ft}")
    print(f"  stock     : {stock}")

    stock_per, fine_per = _coco_retention(stock, str(ft), model_id)
    custom_ap = _custom_class_skill(str(ft), model_id)

    csv_path = cfg.OUTPUTS / f"{nm}_eval.csv"
    _write_eval_csv(csv_path, stock_per, fine_per, custom_ap)
    _print_summary(model_id, ft, stock_per, fine_per, custom_ap, csv_path)
    return csv_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", type=int, required=True, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--weights", default=None,
                    help="checkpoint path (default: runs/<name>/weights/last.pt)")
    a = ap.parse_args()
    evaluate_model(a.model, a.weights)
