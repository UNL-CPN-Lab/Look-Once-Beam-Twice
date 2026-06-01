"""Release-grade dataset packaging + label translation.

Each released dataset is shipped as:

    <dataset>/
    ├── FullDataset/
    │   ├── Images/   (every paired image, flat)
    │   └── Labels/   (every paired YOLO label, flat)
    └── splits/
        ├── train.txt (one stem per line — the paper's train split)
        ├── val.txt
        └── test.txt

This module has four jobs:

  build_manifest_from_splits   our release prep: scan existing
                               <dataset>/{train,val,test}/{images,labels}/ dirs
                               and write `splits/*.txt`.
  build_splits_from_manifest   end-user prep: read `splits/*.txt` and link
                               `<dataset>/{train,val,test}/{images,labels}/`
                               from `FullDataset/`.
  discover_and_materialize     end-user one-shot: scan a folder of unpacked
                               datasets and run `build_splits_from_manifest`
                               for each.
  translate_labels_for_unified second-stage label remap for the unified YOLOR
                               model: convert per-model class ids (from
                               cp_pseudolabel's labels_p1/) into unified ids
                               (labels_p1_m5/). See "Two-stage label remap".

Two-stage label remap
---------------------
Labels go through two id renames:

  1) source -> per-model scheme    (`cp_config.MANUAL_REMAP`, run by
     `cp_pseudolabel.pseudolabel_dataset` -> writes `labels_p1/`)
  2) per-model -> unified YOLOR   (`UNIFIED_REMAP_PER_DATASET`, run here by
     `translate_labels_for_unified` -> writes `labels_p1_m5/`)

Stage 1 makes each single-domain model's labels speak its own scheme
(e.g. for commercial: source 0,1 -> 80=radio, 81=mmWave radio). Stage 2 only
matters for the unified model, which needs the four schemes to share one
contiguous id space (radio=80, 5G BS=81, LampPost=82, mmWave radio=83,
streetlight=84).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cp_config as cfg

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")
LBL_EXTS = (".txt",)


# --- shared filesystem helpers ----------------------------------------------

def _find_subdir(parent: Path, *candidates: str) -> Path | None:
    """Case-insensitive lookup of a subdir name (e.g. 'images' vs 'Images').
    Returns the first match, or None if none of `candidates` exist."""
    if not parent.exists():
        return None
    lower = {p.name.lower(): p for p in parent.iterdir() if p.is_dir()}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def _stems(d: Path, exts: tuple[str, ...]) -> set[str]:
    """Set of basename-without-extension for files in `d` matching `exts`.
    Skips macOS AppleDouble shadow files (`._foo.jpg`)."""
    if not d or not d.exists():
        return set()
    return {p.stem for p in d.iterdir()
            if p.is_file() and not p.name.startswith("._")
            and p.suffix.lower() in exts}


def _dataset_root(dataset_key: str) -> Path:
    """Resolve a dataset's release-folder root (contains FullDataset/ + splits/)."""
    return cfg.DATASETS[dataset_key]


# --- stage 2: per-model -> unified YOLOR label remap -----------------------

UNIFIED_REMAP_PER_DATASET: dict[str, dict[int, int]] = {
    "cots":        {80: 80},                # radio: unchanged
    "outdoor":     {80: 81, 81: 82},        # 5G BS, LampPost shift up by one
    "commercial":  {80: 80, 81: 83},        # radio stays; mmWave radio -> 83
    "streetlight": {80: 84},                # streetlight moves to 84
}


def labels_p1_m5_dir(dataset_key: str, split_dirname: str) -> Path:
    """Where stage-2 (unified-scheme) translated labels live for one split.
    Parallel to `cp_config.labels_p1_dir()` (which is stage 1)."""
    d = cfg.WORKDIR / "labels_p1_m5" / dataset_key / split_dirname
    d.mkdir(parents=True, exist_ok=True)
    return d


def _translate_label_line(line: str, remap: dict[int, int]) -> str | None:
    """Translate one YOLO label line by remapping its class id (column 0).
    Returns None for lines too short to be a valid label."""
    parts = line.split()
    if len(parts) < 5:
        return None
    cid = int(float(parts[0]))
    new_cid = remap.get(cid, cid)            # COCO ids 0-79 pass through
    return f"{new_cid} {' '.join(parts[1:])}"


def _translate_label_file(src: Path, dst: Path, remap: dict[int, int]) -> None:
    """Translate every line in one label file and write to `dst`."""
    out = [t for t in (_translate_label_line(l, remap)
                       for l in src.read_text().splitlines())
           if t is not None]
    dst.write_text("\n".join(out) + ("\n" if out else ""))


def translate_labels_for_unified(dataset_key: str,
                                 splits=("train", "val", "test")) -> dict[str, int]:
    """Read `labels_p1/<ds>/<split>/*.txt`, remap custom ids to the unified
    YOLOR scheme, write to `labels_p1_m5/<ds>/<split>/*.txt`. COCO ids 0-79
    pass through unchanged. Idempotent (overwrites)."""
    remap = UNIFIED_REMAP_PER_DATASET[dataset_key]
    val_name = cfg.SPLIT_DIRNAMES.get(dataset_key, "val")
    counts: dict[str, int] = {}

    for split in splits:
        actual = val_name if split == "val" else split
        src = cfg.WORKDIR / "labels_p1" / dataset_key / actual
        dst = labels_p1_m5_dir(dataset_key, actual)

        if not src.exists():
            counts[split] = 0
            print(f"  [skip] {dataset_key}/{actual}: no labels_p1 source")
            continue

        n = 0
        for f in src.iterdir():
            if f.suffix != ".txt" or f.name.startswith("._"):
                continue
            _translate_label_file(f, dst / f.name, remap)
            n += 1
        counts[split] = n
        print(f"  [translate-m5] {dataset_key}/{actual}: wrote {n} labels "
              f"(remap {remap})")
    return counts


# --- release prep: split dirs -> splits/*.txt -------------------------------

# valid-name alternatives we accept when scanning for a split dir
_SPLIT_NAME_CANDIDATES = {
    "train": ("train",),
    "val":   ("val", "valid"),     # Roboflow exports often use "valid"
    "test":  ("test",),
}


def _find_split_dir(root: Path, split: str) -> Path | None:
    """Find the on-disk dir for one split, accepting `val`/`valid` variants."""
    for cand in _SPLIT_NAME_CANDIDATES[split]:
        if (root / cand).is_dir():
            return root / cand
    # also accept the cp_config preference if it's not already in the list
    pref = cfg.SPLIT_DIRNAMES.get(_dataset_key_for_root(root), "val") if split == "val" else None
    if pref and (root / pref).is_dir():
        return root / pref
    return None


def _dataset_key_for_root(root: Path) -> str | None:
    """Reverse lookup: dataset key whose cp_config.DATASETS[key] == root."""
    for k, p in cfg.DATASETS.items():
        if p == root:
            return k
    return None


def _stems_in_split(split_dir: Path) -> list[str]:
    """Stems present in BOTH the images/ and labels/ subdirs of one split
    (orphans without a matching pair are dropped)."""
    img = _find_subdir(split_dir, "images", "Images")
    lbl = _find_subdir(split_dir, "labels", "Labels")
    if img is None or lbl is None:
        return []
    return sorted(_stems(img, IMG_EXTS) & _stems(lbl, LBL_EXTS))


def build_manifest_from_splits(dataset_key: str) -> Path:
    """Write `<dataset>/splits/{train,val,test}.txt` listing the paired stems
    found in each existing split dir."""
    root = _dataset_root(dataset_key)
    splits_dir = root / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for split in ("train", "val", "test"):
        sp = _find_split_dir(root, split)
        if sp is None:
            counts[split] = 0
            (splits_dir / f"{split}.txt").write_text("")
            print(f"  [{split}] empty (no matching split dir)")
            continue
        stems = _stems_in_split(sp)
        (splits_dir / f"{split}.txt").write_text("\n".join(stems) + "\n")
        counts[split] = len(stems)
        print(f"  [{split}] {len(stems)} stems  ->  splits/{split}.txt")

    print(f"manifest: train={counts['train']} val={counts['val']} test={counts['test']}")
    return splits_dir


# --- end-user prep: splits/*.txt -> split dirs ------------------------------

def _resolve_full_dataset(root: Path) -> tuple[Path, Path]:
    """Locate `FullDataset/{Images,Labels}` under one dataset root."""
    fd = root / "FullDataset"
    img = _find_subdir(fd, "images", "Images")
    lbl = _find_subdir(fd, "labels", "Labels")
    if img is None or lbl is None:
        raise FileNotFoundError(
            f"{fd}/{{Images,Labels}} missing — extract the released dataset there first.")
    return img, lbl


def _pick_image_extension(img_src: Path) -> str:
    """Default extension for files in `img_src` (used when manifest stems are
    extensionless). Falls back to `.jpg`."""
    for p in img_src.iterdir():
        if p.suffix.lower() in IMG_EXTS and not p.name.startswith("._"):
            return p.suffix
    return ".jpg"


def _link_or_copy(src: Path, dst: Path, mode: str) -> None:
    """Symlink or copy `src -> dst`, removing any prior target first."""
    import shutil
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if mode == "symlink":
        dst.symlink_to(src.resolve())
    else:
        shutil.copy2(src, dst)


def _materialize_one_split(manifest: Path, img_src: Path, lbl_src: Path,
                           out_img: Path, out_lbl: Path,
                           ext: str, mode: str) -> tuple[int, int]:
    """Link/copy every (image, label) pair in `manifest` into the output dirs.
    Returns (kept, missing)."""
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)

    kept = miss = 0
    for st in (s for s in manifest.read_text().splitlines() if s.strip()):
        i_src, l_src = img_src / f"{st}{ext}", lbl_src / f"{st}.txt"
        if not (i_src.exists() and l_src.exists()):
            miss += 1
            continue
        _link_or_copy(i_src, out_img / f"{st}{ext}", mode)
        _link_or_copy(l_src, out_lbl / f"{st}.txt", mode)
        kept += 1
    return kept, miss


def _materialize_at_path(root: Path, val_name: str = "val",
                         mode: str = "symlink") -> dict[str, int]:
    """Materialize `<root>/{train,val,test}/{images,labels}/` from
    `<root>/FullDataset/` + `<root>/splits/*.txt`. Path-driven; doesn't need
    a cp_config dataset key. Returns per-split kept counts."""
    img_src, lbl_src = _resolve_full_dataset(root)
    splits_dir = root / "splits"
    if not splits_dir.is_dir():
        raise FileNotFoundError(f"{splits_dir} missing")

    ext = _pick_image_extension(img_src)
    plan = [("train", "train"), ("val", val_name), ("test", "test")]
    counts: dict[str, int] = {}

    for split_name, out_dirname in plan:
        manifest = splits_dir / f"{split_name}.txt"
        if not manifest.exists():
            print(f"  [{split_name}] no manifest splits/{split_name}.txt — skipped")
            counts[split_name] = 0
            continue
        kept, miss = _materialize_one_split(
            manifest,
            img_src, lbl_src,
            root / out_dirname / "images",
            root / out_dirname / "labels",
            ext, mode,
        )
        counts[split_name] = kept
        print(f"  [{split_name}] materialized {kept} pairs"
              + (f" (missing {miss})" if miss else ""))
    return counts


def build_splits_from_manifest(dataset_key: str, mode: str = "symlink") -> None:
    """cp_config-driven wrapper around `_materialize_at_path` for one dataset key."""
    root = _dataset_root(dataset_key)
    val_name = cfg.SPLIT_DIRNAMES.get(dataset_key, "val")
    _materialize_at_path(root, val_name=val_name, mode=mode)


def discover_and_materialize(datasets_root: Path | str | None = None,
                             mode: str = "symlink") -> dict[str, dict[str, int]]:
    """End-user one-shot: scan `datasets_root` for dirs that look like a
    released dataset (have BOTH `FullDataset/` and `splits/`), and run
    materialize on each. Defaults to `<YOLOR_ROOT>/FilteredTrainingDatasets/`."""
    root = Path(datasets_root) if datasets_root else cfg.DATASETS_ROOT
    if not root.is_dir():
        raise FileNotFoundError(f"{root} is not a directory")

    found = [c for c in sorted(root.iterdir())
             if c.is_dir() and (c / "FullDataset").exists() and (c / "splits").exists()]
    if not found:
        print(f"  no datasets with FullDataset/+splits/ found under {root}")
        return {}

    print(f"discovered {len(found)} dataset(s) under {root}:")
    results: dict[str, dict[str, int]] = {}
    for child in found:
        print(f"\n--- {child.name} ---")
        try:
            results[child.name] = _materialize_at_path(child, mode=mode)
        except Exception as e:                       # noqa: BLE001
            print(f"  ERROR: {e}")
            results[child.name] = {"error": str(e)}  # type: ignore
    return results


# --- CLI --------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--action", required=True,
                    choices=["build_manifest", "build_splits",
                             "translate_unified", "discover"])
    ap.add_argument("--dataset",
                    help="dataset key from cp_config.DATASETS (required for "
                         "build_manifest, build_splits, translate_unified)")
    ap.add_argument("--path",
                    help="for `discover`: filesystem path containing per-dataset "
                         "subfolders (defaults to <YOLOR_ROOT>/"
                         "FilteredTrainingDatasets/)")
    ap.add_argument("--mode", choices=["symlink", "copy"], default="symlink",
                    help="for build_splits / discover: how to materialize files")
    a = ap.parse_args()

    if a.action == "discover":
        results = discover_and_materialize(a.path, mode=a.mode)
        ok = sum(1 for r in results.values() if "error" not in r)
        print(f"\n=== discover summary: {ok}/{len(results)} datasets OK ===")
    else:
        if not a.dataset:
            ap.error(f"--dataset required for {a.action}")
        if a.action == "build_manifest":
            build_manifest_from_splits(a.dataset)
        elif a.action == "translate_unified":
            translate_labels_for_unified(a.dataset)
        elif a.action == "build_splits":
            build_splits_from_manifest(a.dataset, mode=a.mode)
