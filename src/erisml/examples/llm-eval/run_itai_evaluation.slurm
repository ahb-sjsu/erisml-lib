#!/bin/bash
#==============================================================================
# SLURM Batch Script: ITAI 4-Rank Tensor Multi-Agent EM Testing
#==============================================================================
# For SJSU College of Engineering HPC Cluster
# https://www.sjsu.edu/cmpe/resources/hpc.php
#
# Usage:
#   sbatch run_itai_evaluation.slurm
#
# Monitor job:
#   squeue -u $USER
#   tail -f itai_eval_<jobid>.log
#==============================================================================

#------------------------------------------------------------------------------
# SLURM Configuration
#------------------------------------------------------------------------------
#SBATCH --job-name=itai_eval
#SBATCH --output=itai_eval_%j.log
#SBATCH --error=itai_eval_%j.err

# Partition: Use 'gpu' for general GPU nodes (P100, A100, H100)
# Options: compute, gpu, condo
#SBATCH --partition=gpu

# Request GPU resources
# For A100 nodes (g7, g13): --gres=gpu:1
# For H100 nodes (g2, g6): --gres=gpu:1  
# For P100 nodes: --gres=gpu:1
#SBATCH --gres=gpu:1

# Resource requests
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G

# Time limit (gpu partition max: 7 days)
# For 100 scenarios with Llama 3.1 8B: ~2-4 hours
#SBATCH --time=12:00:00

# Email notifications (optional)
#SBATCH --mail-type=BEGIN,END,FAIL
# Uncomment and set your email:
# #SBATCH --mail-user=your.email@sjsu.edu

#------------------------------------------------------------------------------
# Environment Setup
#------------------------------------------------------------------------------
echo "=============================================="
echo "ITAI Framework Evaluation Job Started"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start Time: $(date)"
echo "Working Directory: $(pwd)"
echo ""

# Load required modules
echo "Loading modules..."
module purge
module load cuda/12.1  # or cuda/11.8 depending on availability
module load python3/3.10

# Check GPU availability
echo ""
echo "GPU Information:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
echo ""

#------------------------------------------------------------------------------
# Conda Environment Setup
#------------------------------------------------------------------------------
# Option 1: Use existing conda environment
if [ -d "$HOME/anaconda3" ]; then
    echo "Activating Anaconda..."
    source $HOME/anaconda3/bin/activate
    
    # Create environment if it doesn't exist
    if ! conda env list | grep -q "itai"; then
        echo "Creating 'itai' conda environment..."
        conda create -n itai python=3.10 -y
    fi
    
    conda activate itai
    
# Option 2: Use virtualenv
else
    echo "Setting up Python virtual environment..."
    if [ ! -d "$HOME/itai_venv" ]; then
        python -m venv $HOME/itai_venv
    fi
    source $HOME/itai_venv/bin/activate
fi

#------------------------------------------------------------------------------
# Install Dependencies
#------------------------------------------------------------------------------
echo ""
echo "Installing dependencies..."

# Core dependencies
pip install --quiet --upgrade pip
pip install --quiet numpy torch transformers accelerate

# vLLM for efficient inference (recommended for production)
# Note: vLLM requires specific CUDA versions
pip install --quiet vllm

# HuggingFace hub for model access
pip install --quiet huggingface_hub

echo "Dependencies installed."

#------------------------------------------------------------------------------
# Model Configuration
#------------------------------------------------------------------------------
# Available models (choose based on GPU memory):
#
# For P100 (12GB VRAM):
#   - meta-llama/Llama-3.2-3B-Instruct (3B params, ~6GB)
#   - microsoft/phi-3-mini-4k-instruct (3.8B params, ~8GB)
#
# For A100/H100 (40-80GB VRAM):
#   - meta-llama/Llama-3.1-8B-Instruct (8B params, ~16GB)
#   - meta-llama/Llama-3.1-70B-Instruct (70B params, ~140GB, needs multi-GPU)
#   - mistralai/Mistral-7B-Instruct-v0.3 (7B params, ~14GB)

# Default model (works on A100/H100)
MODEL="meta-llama/Llama-3.1-8B-Instruct"

# Uncomment for P100 nodes:
# MODEL="meta-llama/Llama-3.2-3B-Instruct"

# Number of scenarios (100 recommended for rigorous testing)
N_SCENARIOS=100

# Random seed for reproducibility
SEED=42

# Tensor parallelism (for multi-GPU setups)
TENSOR_PARALLEL=1

#------------------------------------------------------------------------------
# HuggingFace Authentication (Required for Llama models)
#------------------------------------------------------------------------------
# Option 1: Set token directly (not recommended for shared scripts)
# export HF_TOKEN="your_token_here"

# Option 2: Use cached credentials (recommended)
# Run this once interactively: huggingface-cli login
if [ -z "$HF_TOKEN" ] && [ ! -f "$HOME/.cache/huggingface/token" ]; then
    echo ""
    echo "WARNING: HuggingFace authentication may be required for Llama models."
    echo "Run 'huggingface-cli login' interactively before submitting job."
    echo ""
fi

#------------------------------------------------------------------------------
# Run Evaluation
#------------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Starting ITAI 4-Rank Tensor Evaluation"
echo "=============================================="
echo "Model: $MODEL"
echo "Scenarios: $N_SCENARIOS"
echo "Seed: $SEED"
echo ""

# Create output directory
OUTPUT_DIR="$HOME/itai_results"
mkdir -p $OUTPUT_DIR

# Generate unique output filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/itai_results_${SLURM_JOB_ID}_${TIMESTAMP}.json"

# Change to script directory (works from any location)
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

echo "Script directory: $SCRIPT_DIR"

# Run the evaluation
python itai_bond_index_evaluation.py \
    --model "$MODEL" \
    --n-scenarios $N_SCENARIOS \
    --seed $SEED \
    --output "$OUTPUT_FILE" \
    --tensor-parallel $TENSOR_PARALLEL

# Capture exit code
EXIT_CODE=$?

#------------------------------------------------------------------------------
# Post-Processing
#------------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Evaluation Complete"
echo "=============================================="
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "Results saved to: $OUTPUT_FILE"
echo ""

# Print summary if results exist
if [ -f "$OUTPUT_FILE" ]; then
    echo "Bond Index Summary:"
    python -c "
import json
with open('$OUTPUT_FILE') as f:
    r = json.load(f)
    bd = r['bond_index']
    print(f\"  Value: {bd['value']:.4f}\")
    print(f\"  95% CI: [{bd['ci_lower']:.4f}, {bd['ci_upper']:.4f}]\")
    print(f\"  Tier: {bd['tier']}\")
    print(f\"  Decision: {bd['deployment_decision']}\")
"
fi

# Copy results to shared location if available
if [ -d "/data/$USER" ]; then
    cp "$OUTPUT_FILE" "/data/$USER/"
    echo "Results also copied to: /data/$USER/"
fi

echo ""
echo "Job completed."

exit $EXIT_CODE
