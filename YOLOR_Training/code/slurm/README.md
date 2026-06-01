# SLURM templates (optional)

You do **not** need SLURM to train YOLOR. If you have a single dedicated CUDA
GPU, just follow the notebook (`../YOLOR_train_all_models.ipynb`) or the
`python cp_train.py …` commands in the top-level `README.md`. The scripts in
this folder are templates for the HPC environment this project was developed
on (the University of Nebraska–Lincoln HCC `Swan` cluster + `NRDStor`
storage), and they're useful as a starting point if you want unattended,
pre-emption-tolerant multi-day training on your own cluster.

## What's in here

| Script | What it does |
|---|---|
| `prep_model1.slurm` | One-shot data prep for **model 1** (`YOLOR-radio`): pseudo-label → materialize. |
| `prep_modelN.slurm` | Generic prep for any model id via `--export=ALL,YOLOR_MODEL=N` (models 2, 3, 4). Includes the perceptual-hash dedup branch for the commercial dataset. |
| `train_model1.slurm` | Training driver for **model 1**, with a SIGTERM-trapped self-resubmit loop and a sentinel file (`.YOLOR-radio.keepgoing`) so it survives pre-emption. |
| `train_modelN.slurm` | Generic training driver for models 2–5 via `--export=ALL,YOLOR_MODEL=N`. Same pre-emption-tolerant design as `train_model1.slurm`. |
| `gpu_test.slurm` / `env_test.slurm` | Tiny sanity checks: verify GPU visibility and that the Python env can import torch + ultralytics. |

## What's HCC-specific (and what to change for your cluster)

These scripts will not work as-is on a different cluster. Here's exactly what
to look for:

1. **Partition and GPU constraint**

   ```bash
   #SBATCH --partition=guest_gpu
   #SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
   ```

   `guest_gpu` is HCC's pre-emptible tier; change to whatever partition your
   cluster offers. The `constraint` filter asks for a ≥32 GB GPU; adjust or
   drop based on your cluster's GPU labels. If you have a single fixed GPU
   class, you can remove the constraint line entirely.

2. **Absolute paths**

   ```bash
   export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
   VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
   ```

   Repoint `YOLOR_ROOT` to wherever your copy of
   `YOLO_DatasetsandTraining` lives, and `VENV` to your Python venv.

3. **`module load` block**

   ```bash
   module purge 2>/dev/null||true; module load python/3.9
   ```

   HCC uses `lmod`. If your cluster uses `conda`/`spack`/`micromamba`/no
   module system, replace this with whatever activates Python 3.9+ in
   your environment.

4. **Pre-emption handling**

   The scripts trap `SIGTERM` and resubmit themselves (`sbatch $SELF`) so
   that on pre-emption the run continues from `last.pt` on the next slot.
   This relies on:
   - the partition actually sending SIGTERM on pre-emption (set
     `#SBATCH --signal=B:SIGTERM@120`),
   - a sentinel file (`.<MODEL>.keepgoing`) that lets you cleanly stop the
     loop (`rm` the sentinel + `scancel`),
   - `cp_train.py`'s built-in auto-resume from `runs/<model>/weights/last.pt`.

   On a non-pre-emptible partition, you can delete the trap + sentinel
   logic and just run the body inline.

5. **Output paths**

   ```bash
   #SBATCH --output=…/YOLOR_Training/logs/%x_%j.out
   ```

   Make sure the `logs/` directory exists, or change the path.

## Writing your own minimal SLURM submission

If you want to skip all the pre-emption complexity, a minimal submission for
any model `N` looks like:

```bash
#!/bin/bash -l
#SBATCH --job-name=YOLOR-N
#SBATCH --partition=<your_gpu_partition>
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=48:00:00
#SBATCH --output=logs/%x_%j.out

export YOLOR_ROOT=<path-to-YOLO_DatasetsandTraining>
source <path-to-your-venv>/bin/activate
cd $YOLOR_ROOT/YOLOR_Training/code

python cp_pseudolabel.py --dataset cots --splits train val test
python cp_coco_replay.py --step materialize --model 1
python cp_train.py --model 1 --run
python cp_eval.py  --model 1
```

That's it. Replace `cots` / `--model 1` with the dataset key and model id
you want.

## Not using a cluster at all?

Run the commands from the top-level `../README.md` or open
`../YOLOR_train_all_models.ipynb` and execute the cells. Same code path,
same results.
