#!/bin/bash -l
#SBATCH --job-name=YOLOR-trainN
#SBATCH --partition=guest_gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=120G
#SBATCH --time=168:00:00
#SBATCH --signal=B:SIGTERM@120
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/%x_%j.out
#SBATCH --error=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/%x_%j.err
: "${YOLOR_MODEL:?set YOLOR_MODEL via --export}"
R=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training
SELF=$R/slurm/train_modelN.slurm
export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
export YOLOR_BATCH=4
export CP_ES_MIN_EPOCH=181
export CP_ES_PATIENCE=8
VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
module purge 2>/dev/null||true; module load python/3.9
[ -d "$VENV" ]||python3 -m venv "$VENV"; source "$VENV/bin/activate"
pip install --no-cache-dir -q ultralytics==8.3.158 torch torchvision opencv-python pyyaml pillow
cd "$R"
MNAME=${YOLOR_RUN_NAME:-$(python -c "import cp_config as c;print(c.model_name($YOLOR_MODEL))")}
KEEP=$R/.${MNAME}.keepgoing
on_pre(){ echo "[preempt] $(date)"; if [ -f "$KEEP" ]; then echo "resubmit (resume last.pt)"; sbatch --export=ALL,YOLOR_MODEL=$YOLOR_MODEL --job-name="$SLURM_JOB_NAME" "$SELF"; else echo "sentinel absent - clean stop"; fi; exit 0; }
trap on_pre SIGTERM
touch "$KEEP"
python cp_train.py --model "$YOLOR_MODEL" --run &
TP=$!; wait $TP; RC=$?
rm -f "$KEEP"
echo "[exit] model $YOLOR_MODEL rc=$RC $(date)"
