#!/bin/bash
#==============================================================================
# SLURM Script: Interactive ITAI Testing Session
#==============================================================================
# Request an interactive GPU session for development/testing
#
# Usage:
#   sbatch run_interactive.slurm
#==============================================================================

#SBATCH --job-name=itai_interactive
#SBATCH --output=itai_interactive_%j.log
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00

echo "=============================================="
echo "Interactive ITAI Testing Session"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo ""

# Load modules
module purge
module load cuda/12.1
module load python3/3.10

# Activate conda
source $HOME/anaconda3/bin/activate
conda activate itai

# Show GPU info
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
echo ""

# Change to script directory
cd $(dirname "$(readlink -f "$0")")

echo "Environment ready. Running quick test..."
echo ""

# Run quick evaluation (10 scenarios for testing)
python itai_bond_index_evaluation.py \
    --model meta-llama/Llama-3.2-3B-Instruct \
    --n-scenarios 10 \
    --output quick_test_results.json

echo ""
echo "Quick test complete. Results in quick_test_results.json"
