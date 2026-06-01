"""P1 pseudo-labelling: complete COCO supervision so the model can't forget it.

Why
---
A custom dataset only hand-labels its new class (e.g. `radio`). Every COCO
object in those images is *unlabelled*, so YOLO learns "person/tv/... =
background" and un-learns COCO. We run the *stock* yolo11x.pt (which still
knows all 80 COCO classes) over every training image and write its
high-confidence detections into the label file as ground truth, MERGED with
the manual labels.

Merge rule (manual labels are authoritative)
--------------------------------------------
- keep every manual box unchanged (COCO and custom alike, after remapping
  source ids to our scheme)
- add a teacher box only if it does NOT overlap any manual box (IoU <= drop)

This fills the gaps without duplicating or overwriting human annotation.

Output goes to a sibling `labels_p1/` dir; originals are never touched.
Idempotent: re-running skips splits whose output dir is already populated
unless YOLOR_FORCE_PSEUDO=1 is set.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

import cp_config as cfg

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")
PRED_BATCH = 16  # passing all paths at once OOMs a 12GB GPU; chunk small


# --- bbox utilities ----------------------------------------------------------

def _xywhn_to_xyxy(b: np.ndarray) -> np.ndarray:
    """Convert normalized [cx, cy, w, h] boxes to normalized [x1, y1, x2, y2]."""
    x, y, w, h = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([x - w / 2, y - h / 2, x + w / 2, y + h / 2], axis=-1)


def _iou_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise IoU between every box in `a` and every box in `b` (both xyxy)."""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)), dtype=np.float32)
    a = a[:, None, :]
    b = b[None, :, :]
    ix1 = np.maximum(a[..., 0], b[..., 0]); iy1 = np.maximum(a[..., 1], b[..., 1])
    ix2 = np.minimum(a[..., 2], b[..., 2]); iy2 = np.minimum(a[..., 3], b[..., 3])
    inter = np.clip(ix2 - ix1, 0, None) * np.clip(iy2 - iy1, 0, None)
    area_a = np.clip(a[..., 2] - a[..., 0], 0, None) * np.clip(a[..., 3] - a[..., 1], 0, None)
    area_b = np.clip(b[..., 2] - b[..., 0], 0, None) * np.clip(b[..., 3] - b[..., 1], 0, None)
    union = area_a + area_b - inter
    return np.where(union > 0, inter / union, 0.0).astype(np.float32)


def _read_label_file(p: Path) -> np.ndarray:
    """Read a YOLO label file -> (N, 5) array of [cls, cx, cy, w, h]. Empty
    file or missing returns (0, 5)."""
    if not p.exists() or p.stat().st_size == 0:
        return np.zeros((0, 5), dtype=np.float32)
    rows = []
    for line in p.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 5:
            rows.append([float(x) for x in parts[:5]])
    return np.asarray(rows, dtype=np.float32) if rows else np.zeros((0, 5), np.float32)


# --- per-split image discovery ----------------------------------------------

def _list_images(img_dir: Path) -> list[Path]:
    """Sorted list of image files in `img_dir` (skips macOS resource forks)."""
    return sorted(p for p in img_dir.iterdir()
                  if p.suffix.lower() in IMG_EXTS
                  and not p.name.startswith("._"))


def _keep_only_labeled(imgs: list[Path], man_dir: Path) -> list[Path]:
    """Drop images that have no manual label file. Used for `outdoor` (whose
    raw split mixes labelled frames with ~11k unlabelled near-duplicates that
    the user deliberately discarded)."""
    return [p for p in imgs if (man_dir / (p.stem + ".txt")).exists()]


def _is_split_already_pseudolabelled(out_dir: Path, n_imgs: int) -> bool:
    """True if `out_dir` already has at least one .txt per input image.
    Lets prep be re-run cheaply; bypass with YOLOR_FORCE_PSEUDO=1."""
    if os.environ.get("YOLOR_FORCE_PSEUDO"):
        return False
    done = sum(1 for q in out_dir.iterdir()
               if q.suffix == ".txt" and not q.name.startswith("._"))
    return n_imgs > 0 and done >= n_imgs


# --- per-image label assembly ------------------------------------------------

def _remap_manual(dataset_key: str, raw: np.ndarray) -> np.ndarray:
    """Map source-dataset class ids to the model's scheme; drop any unmapped.

    Returns (M, 5) with cols [cls, cx, cy, w, h], cls in the model scheme.
    Teacher COCO pseudo-boxes (0..79) are NOT routed through here.
    """
    out = []
    for row in raw:
        new_cls = cfg.remap_manual_class(dataset_key, int(row[0]))
        if new_cls is not None:
            out.append((new_cls, row[1], row[2], row[3], row[4]))
    return np.asarray(out, dtype=np.float32) if out else np.zeros((0, 5), np.float32)


def _format_yolo_line(cls: int, cx: float, cy: float, w: float, h: float) -> str:
    """One YOLO label line: class + normalized cx cy w h, 6-decimal precision."""
    return f"{int(cls)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


def _merge_one_image(dataset_key: str, manual_raw: np.ndarray, teacher_res,
                     iou_drop: float) -> tuple[list[str], int, int, int]:
    """Build the merged YOLO label lines for one image.

    Returns (lines, kept_manual, added_pseudo, dropped_pseudo) so the caller
    can write the .txt and accumulate stats. A teacher box is dropped if it
    overlaps ANY manual box at IoU > iou_drop.
    """
    manual = _remap_manual(dataset_key, manual_raw)
    manual_xyxy = (_xywhn_to_xyxy(manual[:, 1:5]) if len(manual)
                   else np.zeros((0, 4), np.float32))
    lines = [_format_yolo_line(int(c), *r)
             for c, r in zip(manual[:, 0], manual[:, 1:5])]
    kept_manual = len(manual)

    if teacher_res.boxes is None or len(teacher_res.boxes) == 0:
        return lines, kept_manual, 0, 0

    p_cls = teacher_res.boxes.cls.cpu().numpy().astype(int)
    p_xywhn = teacher_res.boxes.xywhn.cpu().numpy()
    p_xyxy = _xywhn_to_xyxy(p_xywhn)

    if manual_xyxy.shape[0]:
        max_overlap = _iou_matrix(p_xyxy, manual_xyxy).max(axis=1)
    else:
        max_overlap = np.zeros(len(p_xyxy))

    added = dropped = 0
    for i in range(len(p_xyxy)):
        if max_overlap[i] > iou_drop:
            dropped += 1
            continue
        cx, cy, w, h = p_xywhn[i]
        lines.append(_format_yolo_line(int(p_cls[i]), cx, cy, w, h))
        added += 1
    return lines, kept_manual, added, dropped


# --- main --------------------------------------------------------------------

def _split_dir_name(dataset_key: str, split: str) -> str:
    """Translate the canonical 'val' to whatever the source dataset calls it
    ('valid' for streetlight). 'train' and 'test' pass through unchanged."""
    return cfg.SPLIT_DIRNAMES[dataset_key] if split == "val" else split


def pseudolabel_dataset(dataset_key: str,
                        splits=("train", "val", "test"),
                        conf: float = 0.5,
                        iou_drop: float = 0.5,
                        model_path: str | None = None) -> dict:
    """Run P1 pseudo-labelling for one dataset across the listed splits.

    Writes merged manual+teacher labels into `WORKDIR/labels_p1/<ds>/<split>/`.
    The source dataset is read-only. Returns a per-split stats dict.
    """
    from ultralytics import YOLO

    ds_root = cfg.DATASETS[dataset_key]
    model = YOLO(model_path or cfg.stock_yolo11x())
    stats: dict[str, dict] = {}

    for split in splits:
        sdir = _split_dir_name(dataset_key, split)
        img_dir = ds_root / sdir / "images"
        man_dir = ds_root / sdir / "labels"
        if not img_dir.exists():
            print(f"[skip] {dataset_key}/{sdir}: no images dir")
            continue
        out_dir = cfg.labels_p1_dir(dataset_key, sdir)

        imgs = _list_images(img_dir)
        if dataset_key in cfg.LABELED_ONLY:
            before = len(imgs)
            imgs = _keep_only_labeled(imgs, man_dir)
            print(f"[labeled-only] {dataset_key}/{sdir}: keeping {len(imgs)}"
                  f"/{before} images that have a manual label")

        if _is_split_already_pseudolabelled(out_dir, len(imgs)):
            print(f"[skip] {dataset_key}/{sdir}: already pseudo-labelled "
                  f"({len(imgs)} imgs); set YOLOR_FORCE_PSEUDO=1 to redo")
            stats[split] = {"images": len(imgs), "skipped": True,
                            "out_dir": str(out_dir)}
            continue

        kept_manual_tot = added_tot = dropped_tot = 0

        for s in range(0, len(imgs), PRED_BATCH):
            chunk = imgs[s:s + PRED_BATCH]
            teacher_res = model.predict(source=[str(p) for p in chunk],
                                        conf=conf, imgsz=640, half=True,
                                        verbose=False)
            for img_path, res in zip(chunk, teacher_res):
                manual_raw = _read_label_file(man_dir / (img_path.stem + ".txt"))
                lines, km, ap, dp = _merge_one_image(
                    dataset_key, manual_raw, res, iou_drop)
                (out_dir / (img_path.stem + ".txt")).write_text(
                    "\n".join(lines) + ("\n" if lines else ""))
                kept_manual_tot += km
                added_tot += ap
                dropped_tot += dp

        stats[split] = {"images": len(imgs),
                        "manual_kept": kept_manual_tot,
                        "pseudo_added": added_tot,
                        "pseudo_dropped": dropped_tot,
                        "out_dir": str(out_dir)}
        print(f"[{dataset_key}/{split}] imgs={len(imgs)} "
              f"manual={kept_manual_tot} pseudo+={added_tot} "
              f"pseudo_dropped={dropped_tot} -> {out_dir}")

    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", default="cots", choices=list(cfg.DATASETS))
    ap.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--iou-drop", type=float, default=0.5)
    a = ap.parse_args()
    pseudolabel_dataset(a.dataset, tuple(a.splits), a.conf, a.iou_drop)
