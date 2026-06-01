#!/bin/bash -l
#SBATCH --job-name=cp_envtest
#SBATCH --partition=guest_gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:50:00
#SBATCH --output=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/envtest_%j.out
#SBATCH --error=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/envtest_%j.err
echo "HOST=$(hostname) PART=$SLURM_JOB_PARTITION"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
module purge 2>/dev/null || true
module load python/3.9
VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
export PIP_CACHE_DIR=/mnt/nrdstor/vuran/shared/mmWave_Shared/.pipcache
[ -d "$VENV" ] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
echo "venv python -> $(python --version 2>&1)"
pip install --no-cache-dir --upgrade pip -q
pip install --no-cache-dir -q ultralytics==8.3.158 torch torchvision opencv-python pyyaml
export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
cd "$YOLOR_ROOT/YOLOR_Training"
python - <<'PY'
import torch, ultralytics, cp_config as c
print("torch", torch.__version__, "cuda", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NOCUDA")
print("ultralytics", ultralytics.__version__)
print("cp_config epochs", c.TRAIN_HYP["epochs"], "patience", c.TRAIN_HYP["patience"],
      "imgsz/batch", c.hardware_profile()["imgsz"], c.hardware_profile()["batch"])
print("cots", c.DATASETS["cots"].exists(), "coco", c.COCO_DIR.exists())
PY
echo "ENVTEST_DONE rc=$?"
