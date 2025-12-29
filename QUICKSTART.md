# QND Experiment - Quick Start Guide

## Disk Space Requirements

| Dataset | Size | Records | Best For |
|---------|------|---------|----------|
| AITA Full (HuggingFace) | ~500 MB | 270K | Full experiments |
| AITA Binary | ~20 MB | 17K | Quick tests |
| Jigsaw Toxic | ~100 MB | 160K | Content moderation |
| Scruples | ~60 MB | 42K | Interference tests |
| Hendrycks ETHICS | ~20 MB | 130K | Multi-framework |
| **TOTAL** | **~700 MB** | | |

## Quick Start (No Network Required)

```bash
# Generate synthetic test data
python collect_datasets.py --synthetic --synthetic-size 100

# Run experiment with mock LLM (no API key needed)
python qnd_aita_experiment.py --data-file qnd_datasets/qnd_synthetic_data.json --n-posts 10

# Analyze results
python analyze_qnd_results.py qnd_results.json
```

## Full Experiment (Requires API Key + Network)

```bash
# 1. Download real data (run on your machine, not in sandbox)
python collect_datasets.py --aita --prepare

# 2. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Run experiment with real LLM calls
python qnd_aita_experiment.py \
    --data-file qnd_datasets/qnd_aita_prepared.json \
    --n-posts 50 \
    --n-trials 5

# 4. Analyze
python analyze_qnd_results.py qnd_results.json
```

## What the Experiment Tests

### 1. Order Effects
**QND Prediction**: Asking about harm first vs intent first should give different verdicts.

```
Order A: harm → intent → verdict
Order B: intent → harm → verdict
```

If verdicts differ, this supports non-commuting moral observables.

### 2. Interference
**QND Prediction**: Multiple ethical frameworks interfere, not just add.

```
P(verdict | both frameworks) ≠ average(P(conseq), P(deont))
```

Positive interference = constructive (frameworks reinforce)
Negative interference = destructive (frameworks cancel)

### 3. Superposition
**QND Prediction**: Ambiguous cases have multiple valid interpretations.

The transpiler identifies distinct "branches" of the superposition, each with a probability amplitude.

### 4. Entanglement
**QND Prediction**: In collective responsibility cases (ESH), parties' moral status is correlated.

Cannot assign blame to one party without affecting the other.

## Interpreting Results

| Metric | QND Support Threshold |
|--------|----------------------|
| Order Effect Rate | > 20% |
| Interference Rate | > 30% non-zero |
| Superposition Rate | > 50% |
| Entanglement Rate | > 10% |

## Files

- `qnd_aita_experiment.py` - Main experiment runner
- `collect_datasets.py` - Dataset downloader
- `analyze_qnd_results.py` - Results analysis & visualization
- `qnd_results.json` - Raw experiment output
- `qnd_dashboard.png` - Visual summary

## Next Steps for Real Validation

1. **Run with Claude API** - Mock responses don't test real moral reasoning
2. **Get 100+ posts** - Statistical significance requires larger samples
3. **Compare to human data** - Use AITA votes as ground truth
4. **Test Bell inequalities** - Rigorous entanglement validation
5. **Measure decoherence** - Track how judgments stabilize over time
