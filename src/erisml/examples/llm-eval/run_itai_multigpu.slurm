#!/bin/bash
#==============================================================================
# SLURM Batch Script: Multi-GPU ITAI Evaluation (Large Models)
#==============================================================================
# For running larger models (70B+) with tensor parallelism
# Requires multiple A100 or H100 GPUs
#
# Usage:
#   sbatch run_itai_multigpu.slurm
#==============================================================================

#SBATCH --job-name=itai_70b
#SBATCH --output=itai_70b_%j.log
#SBATCH --error=itai_70b_%j.err

# Request multiple GPU nodes
#SBATCH --partition=gpu
#SBATCH --gres=gpu:2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256G

# Extended time for 70B model
#SBATCH --time=48:00:00

# Email notifications
#SBATCH --mail-type=BEGIN,END,FAIL
# #SBATCH --mail-user=your.email@sjsu.edu

echo "=============================================="
echo "ITAI Multi-GPU Evaluation (70B Model)"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "Start Time: $(date)"
echo ""

# Load modules
module purge
module load cuda/12.1
module load python3/3.10

# Check GPU availability
nvidia-smi
echo ""

# Activate environment
source $HOME/anaconda3/bin/activate
conda activate itai

# Configuration for 70B model
MODEL="meta-llama/Llama-3.1-70B-Instruct"
N_SCENARIOS=100
SEED=42
TENSOR_PARALLEL=2  # Use 2 GPUs

# Output configuration
OUTPUT_DIR="$HOME/itai_results"
mkdir -p $OUTPUT_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/itai_70b_${SLURM_JOB_ID}_${TIMESTAMP}.json"

# Change to script directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

echo "Starting evaluation with:"
echo "  Model: $MODEL"
echo "  Tensor Parallel: $TENSOR_PARALLEL GPUs"
echo "  Scenarios: $N_SCENARIOS"
echo ""

# Run evaluation
python itai_bond_index_evaluation.py \
    --model "$MODEL" \
    --n-scenarios $N_SCENARIOS \
    --seed $SEED \
    --output "$OUTPUT_FILE" \
    --tensor-parallel $TENSOR_PARALLEL

EXIT_CODE=$?

echo ""
echo "=============================================="
echo "Evaluation Complete"
echo "=============================================="
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "Results: $OUTPUT_FILE"

exit $EXIT_CODE
