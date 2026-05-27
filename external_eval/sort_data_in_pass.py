"""
sort_data_in_pass.py — build the `passNN/` folders the evaluation notebooks expect.

DeepSense 6G ships each scenario as long, time-ordered capture sequences. The
evaluation notebooks iterate **pass-by-pass**, where one *pass* = one
continuous drive-by of the transmitter past the receiver (a contiguous,
time-ordered run of frames forming a single trajectory). This script reads a
`scenarioX.csv` and, for every row, copies the camera frame (`unit1_rgb`) into
`<output_root>/pass<seq_index>/`, grouping frames by the dataset's
`seq_index`.

By default the output goes to `<image_root>/unit1/camera_data_passes`, which is
exactly where the notebooks' CONFIG cell looks (`base_dir`).

Example
-------
    python sort_data_in_pass.py \\
        --csv /data/DeepSense6G/scenario9/scenario9_dev/scenario9.csv \\
        --image-root /data/DeepSense6G/scenario9/scenario9_dev

Companion code for "Look Once, Beam Twice" (Proc. IEEE SECON 2026).
Paper: https://arxiv.org/pdf/2605.05071
"""

import argparse
import os
import shutil

import pandas as pd


def build_passes(csv_path: str, image_root: str, output_root: str) -> None:
    # The DeepSense scenario CSV is the source of truth: each row is one
    # captured sample. We only need two columns:
    #   * unit1_rgb  -> the camera frame path (relative to the scenario root)
    #   * seq_index  -> which capture sequence (i.e. which "pass") the frame
    #                   belongs to. All rows sharing a seq_index form one
    #                   continuous drive-by trajectory.
    df = pd.read_csv(csv_path)
    if "unit1_rgb" not in df.columns or "seq_index" not in df.columns:
        raise KeyError("CSV must contain 'unit1_rgb' and 'seq_index' columns")

    n_copied, n_missing = 0, 0
    for _, row in df.iterrows():
        # seq_index defines the pass; every frame with the same seq_index
        # lands in the same passNN/ folder, preserving the trajectory.
        seq_index = int(row["seq_index"])

        # The CSV stores POSIX-style relative paths; normalise the separators
        # so this also works on Windows, then resolve against image_root.
        rel_image_path = str(row["unit1_rgb"]).replace("/", os.sep).replace("\\", os.sep)
        abs_image_path = os.path.join(image_root, rel_image_path)

        # Skip (but report) rows whose image is not on disk, e.g. if only a
        # subset of the scenario was downloaded.
        if not os.path.exists(abs_image_path):
            print(f"[WARN] image not found: {abs_image_path}")
            n_missing += 1
            continue

        # One folder per pass; created lazily the first time we see the index.
        pass_folder = os.path.join(output_root, f"pass{seq_index}")
        os.makedirs(pass_folder, exist_ok=True)

        # copy2 preserves timestamps/metadata; the original dataset is left
        # untouched (this only reads from it).
        shutil.copy2(abs_image_path, os.path.join(pass_folder, os.path.basename(abs_image_path)))
        n_copied += 1

    # Final tally: the notebooks then iterate every passNN/ folder here.
    print(f"[DONE] copied {n_copied} frames into passes under {output_root} "
          f"({n_missing} missing).")


def main() -> None:
    ap = argparse.ArgumentParser(description="Group DeepSense 6G frames into passNN/ folders.")
    ap.add_argument("--csv", required=True,
                    help="path to scenarioX.csv (must have unit1_rgb, seq_index columns)")
    ap.add_argument("--image-root", required=True,
                    help="scenario root that the CSV's unit1_rgb paths are relative to")
    ap.add_argument("--output-root", default=None,
                    help="where to write passNN/ folders "
                         "(default: <image_root>/unit1/camera_data_passes)")
    args = ap.parse_args()

    # Default output is exactly where each notebook's CONFIG cell expects to
    # find the passes (base_dir = <scenario_root>/unit1/camera_data_passes),
    # so no extra moving/symlinking is needed after running this script.
    output_root = args.output_root or os.path.join(
        args.image_root, "unit1", "camera_data_passes"
    )
    build_passes(args.csv, args.image_root, output_root)


if __name__ == "__main__":
    main()
