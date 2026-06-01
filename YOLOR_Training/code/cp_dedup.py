"""Drop near-duplicate frames from video-derived dataset splits.

Outdoor and IndoorCommercial are video captures — many consecutive frames are
visually identical. Training on them overfits a handful of scenes, and near-
duplicates straddling train/val/test inflate metrics. We use a perceptual
hash (dHash) to keep one image per group of visually-similar frames.

Algorithm
---------
1. Compute a 64-bit dHash per image.
2. Group images by trial/sequence prefix (so unrelated scenes are never
   compared, and a single trial cannot leak across splits when this is run
   before splitting). Falls back to one global group if filenames are too
   diverse to form useful groups (e.g. Roboflow timestamp+hash names).
3. Within each group, scan left-to-right and keep an image iff its dHash is
   >= `threshold` Hamming bits away from every already-kept image's hash.

Output
------
`WORKDIR/dedup/<dataset>/<split>/{images,labels}/` — symlinks to the kept
frames only. Originals are never modified. A `dedup_report.csv` records
per-group kept/dropped counts. The unified model 5 build links these
filtered keep-sets into `datasets/YOLOR/<ds>_train/` when called with
`--dedup-splits train` (see cp_coco_replay.materialize).
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

from PIL import Image

import cp_config as cfg

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


# --- hashing -----------------------------------------------------------------

def dhash(path: Path, size: int = 8) -> int:
    """64-bit difference hash of an image (row-wise brightness gradient).

    Two visually similar images have a small Hamming distance between their
    hashes; identical-content frames produce identical hashes.
    """
    img = Image.open(path).convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(img.getdata())
    bits = 0
    for r in range(size):
        row = r * (size + 1)
        for c in range(size):
            bits = (bits << 1) | (1 if px[row + c] > px[row + c + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    """Hamming distance between two integer hashes (number of differing bits)."""
    return bin(a ^ b).count("1")


# --- grouping ----------------------------------------------------------------

def group_key(stem: str) -> str:
    """Trial/sequence prefix used to group related frames.

    Examples:
      'test-2_trial1_1000'        -> 'test-2_trial1'
      'image_01_10-29-39_png.rf.<hash>' -> 'image_01_10-29-39'
    Returns the whole stem if no recognized pattern.
    """
    s = re.split(r"[._]rf[._]", stem)[0]        # drop Roboflow hash suffix
    m = re.match(r"^(.*?)[ _-]?\d+$", s)        # drop trailing frame index
    return m.group(1) if m else s


def _images_in(d: Path) -> list[Path]:
    """Sorted list of usable image files in `d` (skips macOS resource forks)."""
    return sorted(p for p in d.iterdir()
                  if p.suffix.lower() in IMG_EXTS
                  and not p.name.startswith("._"))


def _build_groups(img_paths: list[Path]) -> dict[str, list[Path]]:
    """Group images by their trial prefix.

    If almost every image gets its own group (would defeat dedup), collapses
    to a single global group so the dHash filter still has something to compare.
    """
    groups: dict[str, list[Path]] = {}
    for p in img_paths:
        groups.setdefault(group_key(p.stem), []).append(p)

    n_imgs = sum(len(v) for v in groups.values())
    if n_imgs and len(groups) >= 0.8 * n_imgs:
        print(f"  [dedup] degenerate grouping ({len(groups)} groups / "
              f"{n_imgs} imgs) -> single global group")
        return {"__global__": [p for v in groups.values() for p in v]}
    return groups


# --- per-group keep selection ------------------------------------------------

def _select_kept_in_group(imgs: list[Path], threshold: int) -> list[Path]:
    """Greedy left-to-right scan: keep an image iff its dHash is >= `threshold`
    Hamming bits from every previously-kept image in the same group.
    Images that fail to hash (corrupt file etc.) are skipped with a warning.
    """
    kept: list[Path] = []
    kept_hashes: list[int] = []
    for p in imgs:
        try:
            h = dhash(p)
        except Exception as e:                            # noqa: BLE001
            print(f"  [warn] hash failed {p.name}: {e}")
            continue
        if all(hamming(h, k) >= threshold for k in kept_hashes):
            kept.append(p)
            kept_hashes.append(h)
    return kept


# --- output materialization --------------------------------------------------

def _fresh_dir(out: Path) -> None:
    """Clear any prior dedup-run symlinks under `out`.

    Without this, stale symlinks from an old (larger) keep-set would mask the
    fact that the new run kept fewer frames.
    """
    for sub in ("images", "labels"):
        if (out / sub).exists():
            shutil.rmtree(out / sub)
        (out / sub).mkdir(parents=True, exist_ok=True)


def _link_kept(kept: list[Path], img_src: Path, lbl_src: Path, out: Path) -> None:
    """Symlink each kept image and its sibling label (if present) into `out`."""
    for p in kept:
        sources = [("images", img_src / p.name),
                   ("labels", lbl_src / (p.stem + ".txt"))]
        for sub, src in sources:
            dst = out / sub / src.name
            if src.exists() and not dst.exists():
                dst.symlink_to(src)


def _write_report(rows: list[tuple[str, int, int, int]], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "frames_in", "kept", "dropped"])
        w.writerows(rows)


# --- main --------------------------------------------------------------------

def dedup_split(dataset_key: str, split: str, threshold: int = 5) -> dict:
    """Filter one split of one dataset down to a visually-diverse keep-set.

    Writes symlinks under `WORKDIR/dedup/<dataset>/<split>/`. Originals are
    never touched. Idempotent: the output dir is cleared first so re-running
    always reflects the current `threshold`.
    """
    ds = cfg.DATASETS[dataset_key]
    sdir = cfg.SPLIT_DIRNAMES[dataset_key] if split == "val" else split
    img_dir = ds / sdir / "images"
    lbl_dir = ds / sdir / "labels"
    if not img_dir.exists():
        raise FileNotFoundError(img_dir)

    out = cfg.WORKDIR / "dedup" / dataset_key / sdir
    _fresh_dir(out)

    groups = _build_groups(_images_in(img_dir))
    report: list[tuple[str, int, int, int]] = []
    kept_total = seen_total = 0

    for gk, imgs in sorted(groups.items()):
        kept = _select_kept_in_group(imgs, threshold)
        _link_kept(kept, img_dir, lbl_dir, out)
        seen_total += len(imgs)
        kept_total += len(kept)
        report.append((gk, len(imgs), len(kept), len(imgs) - len(kept)))

    rep_csv = out / "dedup_report.csv"
    _write_report(report, rep_csv)

    stats = {
        "dataset":  dataset_key,
        "split":    sdir,
        "groups":   len(groups),
        "in":       seen_total,
        "kept":     kept_total,
        "dropped":  seen_total - kept_total,
        "kept_pct": round(100 * kept_total / max(seen_total, 1), 1),
        "out":      str(out),
        "report":   str(rep_csv),
    }
    print(f"[dedup {dataset_key}/{sdir}] groups={stats['groups']} "
          f"in={stats['in']} kept={stats['kept']} "
          f"dropped={stats['dropped']} ({stats['kept_pct']}% kept) -> {out}")
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", required=True,
                    choices=["outdoor", "commercial", "cots", "streetlight"])
    ap.add_argument("--splits", nargs="+", default=["train"])
    ap.add_argument("--threshold", type=int, default=5,
                    help="min Hamming distance to keep (higher = more aggressive)")
    a = ap.parse_args()
    for s in a.splits:
        dedup_split(a.dataset, s, a.threshold)
