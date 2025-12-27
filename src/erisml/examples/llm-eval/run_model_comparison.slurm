#!/bin/bash
#==============================================================================
# SLURM Script: Multi-Model Comparison
#==============================================================================
# Evaluates multiple models and generates comparative Bond Index report
#
# Usage:
#   sbatch run_model_comparison.slurm
#==============================================================================

#SBATCH --job-name=itai_compare
#SBATCH --output=itai_compare_%j.log
#SBATCH --error=itai_compare_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00

echo "=============================================="
echo "ITAI Multi-Model Comparison"
echo "=============================================="

# Setup
module purge
module load cuda/12.1
module load python3/3.10

source $HOME/anaconda3/bin/activate
conda activate itai

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

OUTPUT_DIR="$HOME/itai_results/comparison_${SLURM_JOB_ID}"
mkdir -p $OUTPUT_DIR

# Models to compare (adjust based on available GPU memory)
MODELS=(
    "meta-llama/Llama-3.2-3B-Instruct"
    "microsoft/phi-3-mini-4k-instruct"
    "mistralai/Mistral-7B-Instruct-v0.3"
)

# Use consistent seed for fair comparison
SEED=42
N_SCENARIOS=50  # Reduced for faster comparison

echo "Models to evaluate:"
for model in "${MODELS[@]}"; do
    echo "  - $model"
done
echo ""

# Evaluate each model
for model in "${MODELS[@]}"; do
    # Create safe filename from model name
    model_name=$(echo "$model" | sed 's/[\/:]/_/g')
    output_file="${OUTPUT_DIR}/${model_name}.json"
    
    echo ""
    echo "=============================================="
    echo "Evaluating: $model"
    echo "=============================================="
    echo "Output: $output_file"
    
    python itai_bond_index_evaluation.py \
        --model "$model" \
        --n-scenarios $N_SCENARIOS \
        --seed $SEED \
        --output "$output_file"
    
    if [ $? -eq 0 ]; then
        echo "✓ Completed: $model"
    else
        echo "✗ Failed: $model"
    fi
done

echo ""
echo "=============================================="
echo "Generating Comparison Report"
echo "=============================================="

# Generate comparison report
python - << 'EOF'
import json
import os
from pathlib import Path

output_dir = os.environ.get('OUTPUT_DIR', 'comparison')
results = []

for json_file in Path(output_dir).glob('*.json'):
    try:
        with open(json_file) as f:
            data = json.load(f)
            results.append({
                'model': data['metadata']['model'],
                'bond_index': data['bond_index']['value'],
                'ci_lower': data['bond_index']['ci_lower'],
                'ci_upper': data['bond_index']['ci_upper'],
                'tier': data['bond_index']['tier'],
                'n_tests': data['statistics']['n_tests'],
                'deviation_rate': data['statistics']['deviation_rate']
            })
    except Exception as e:
        print(f"Error reading {json_file}: {e}")

# Sort by Bond Index
results.sort(key=lambda x: x['bond_index'])

# Print comparison table
print("\n" + "=" * 80)
print("BOND INDEX COMPARISON RESULTS")
print("=" * 80)
print(f"{'Model':<45} {'Bd':>8} {'95% CI':>18} {'Tier':>12}")
print("-" * 80)

for r in results:
    ci = f"[{r['ci_lower']:.4f}, {r['ci_upper']:.4f}]"
    print(f"{r['model']:<45} {r['bond_index']:>8.4f} {ci:>18} {r['tier']:>12}")

print("-" * 80)
print("\nRanking (lower Bond Index = better coherence):")
for i, r in enumerate(results, 1):
    print(f"  {i}. {r['model']} (Bd={r['bond_index']:.4f}, {r['tier']})")

# Save comparison summary
summary = {
    'comparison_results': results,
    'seed': int(os.environ.get('SEED', 42)),
    'n_scenarios': int(os.environ.get('N_SCENARIOS', 50))
}

summary_path = os.path.join(output_dir, 'comparison_summary.json')
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary saved to: {summary_path}")
EOF

echo ""
echo "Comparison complete!"
echo "Results directory: $OUTPUT_DIR"
