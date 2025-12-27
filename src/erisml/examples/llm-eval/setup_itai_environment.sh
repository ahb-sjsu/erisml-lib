#!/bin/bash
#==============================================================================
# ITAI Framework Setup Script for SJSU HPC
#==============================================================================
# Run this script once before submitting SLURM jobs
#
# Usage:
#   chmod +x setup_itai_environment.sh
#   ./setup_itai_environment.sh
#==============================================================================

set -e  # Exit on error

echo "=============================================="
echo "ITAI Framework Environment Setup"
echo "SJSU College of Engineering HPC"
echo "=============================================="
echo ""

#------------------------------------------------------------------------------
# Check if running on HPC
#------------------------------------------------------------------------------
if [[ ! $(hostname) =~ ^coe-hpc ]]; then
    echo "WARNING: This script should be run on the SJSU HPC login node."
    echo "Current hostname: $(hostname)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

#------------------------------------------------------------------------------
# Setup Conda Environment
#------------------------------------------------------------------------------
echo "Step 1: Setting up Conda environment..."

# Check for existing Anaconda installation
if [ ! -d "$HOME/anaconda3" ]; then
    echo "Anaconda not found. Installing Miniconda..."
    
    # Download Miniconda
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    
    # Install
    bash /tmp/miniconda.sh -b -p $HOME/anaconda3
    rm /tmp/miniconda.sh
    
    # Initialize
    $HOME/anaconda3/bin/conda init bash
    source $HOME/.bashrc
fi

# Activate conda
source $HOME/anaconda3/bin/activate

# Create ITAI environment
echo "Creating 'itai' conda environment with Python 3.10..."
conda create -n itai python=3.10 -y

# Activate environment
conda activate itai

echo "Conda environment 'itai' created and activated."
echo ""

#------------------------------------------------------------------------------
# Install Dependencies
#------------------------------------------------------------------------------
echo "Step 2: Installing Python dependencies..."

# Upgrade pip
pip install --upgrade pip

# Core dependencies
echo "Installing core packages..."
pip install numpy scipy

# PyTorch with CUDA support
echo "Installing PyTorch with CUDA 12.1..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Transformers and related
echo "Installing transformers ecosystem..."
pip install transformers accelerate huggingface_hub

# vLLM for efficient inference
echo "Installing vLLM..."
pip install vllm

# Additional utilities
pip install tqdm rich

echo "Dependencies installed."
echo ""

#------------------------------------------------------------------------------
# HuggingFace Authentication
#------------------------------------------------------------------------------
echo "Step 3: HuggingFace Authentication..."
echo ""
echo "Many foundation models (e.g., Llama 3.1) require HuggingFace authentication."
echo "You need to:"
echo "  1. Create an account at https://huggingface.co"
echo "  2. Accept the model license (e.g., for Llama at https://huggingface.co/meta-llama)"
echo "  3. Create an access token at https://huggingface.co/settings/tokens"
echo ""

read -p "Do you want to login to HuggingFace now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    huggingface-cli login
fi

echo ""

#------------------------------------------------------------------------------
# Create Directory Structure
#------------------------------------------------------------------------------
echo "Step 4: Creating directory structure..."

mkdir -p $HOME/itai_results
mkdir -p $HOME/itai_logs
mkdir -p $HOME/itai_models

echo "Directories created:"
echo "  $HOME/itai_results  - Evaluation results"
echo "  $HOME/itai_logs     - Job logs"
echo "  $HOME/itai_models   - Cached models"
echo ""

#------------------------------------------------------------------------------
# Verify GPU Access
#------------------------------------------------------------------------------
echo "Step 5: Verifying GPU access..."
echo "Requesting interactive GPU session for verification..."

# Submit a quick GPU test
srun -p gpu --gres=gpu:1 -n 1 -N 1 -c 2 --time=00:05:00 bash -c '
echo "GPU Node: $(hostname)"
nvidia-smi --query-gpu=name,memory.total --format=csv
python -c "import torch; print(f\"PyTorch CUDA: {torch.cuda.is_available()}\"); print(f\"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}\")"
' 2>/dev/null || echo "Note: GPU verification skipped (no available slots). GPUs will be verified at job runtime."

echo ""

#------------------------------------------------------------------------------
# Print Summary
#------------------------------------------------------------------------------
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "To run an evaluation:"
echo ""
echo "  1. Activate the environment:"
echo "     conda activate itai"
echo ""
echo "  2. Submit a SLURM job:"
echo "     cd $(dirname "$(readlink -f "$0")")"
echo "     sbatch run_itai_evaluation.slurm"
echo ""
echo "  3. Monitor your job:"
echo "     squeue -u \$USER"
echo "     tail -f itai_eval_<jobid>.log"
echo ""
echo "  4. View results:"
echo "     ls -la \$HOME/itai_results/"
echo ""
echo "For interactive testing:"
echo "     srun -p gpu --gres=gpu:1 -n 1 -N 1 -c 4 --pty /bin/bash"
echo ""
echo "Available models (based on GPU memory):"
echo "  P100 (12GB):  meta-llama/Llama-3.2-3B-Instruct"
echo "  A100 (40GB):  meta-llama/Llama-3.1-8B-Instruct"
echo "  H100 (80GB):  meta-llama/Llama-3.1-70B-Instruct (multi-GPU)"
echo ""
