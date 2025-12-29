# QND Real Experiment - Order Effects in Moral Judgment

This script performs a **rigorous empirical test** of quantum-like order effects in moral judgment by making actual API calls to Claude.

## Why This Matters

The previous "analysis" was me (Claude) **imagining** what I would say with different orderings. That's not science - it's a thought experiment that could easily be confabulation.

This script makes **independent API calls** with different prompts, so we can measure whether the order effect is real.

## Installation

```bash
pip install anthropic pandas scipy statsmodels
```

## Usage

### Basic usage (50 posts):
```bash
python qnd_real_experiment.py \
    --data AITA_labeled_posts.csv \
    --api-key sk-ant-api03-YOUR-KEY-HERE \
    --n-posts 50
```

### Full experiment (150 posts, stratified):
```bash
python qnd_real_experiment.py \
    --data AITA_labeled_posts.csv \
    --api-key sk-ant-api03-YOUR-KEY-HERE \
    --n-posts 150 \
    --stratified \
    --seed 42 \
    --output qnd_full_results.json
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--data` | Path to CSV with AITA posts (required) | - |
| `--api-key` | Anthropic API key (required) | - |
| `--n-posts` | Number of posts to test | 50 |
| `--model` | Claude model to use | claude-sonnet-4-20250514 |
| `--output` | Output JSON file | qnd_results.json |
| `--delay` | Seconds between API calls | 1.0 |
| `--seed` | Random seed for reproducibility | None |
| `--stratified` | Stratify sample by verdict type | False |

## What It Does

For each post:
1. Randomizes which order (A or B) is tested first
2. Makes API call with **Order A prompt**: "Assess HARM first, then Intent, then Verdict"
3. Waits (to avoid any caching effects)
4. Makes API call with **Order B prompt**: "Assess INTENT first, then Harm, then Verdict"
5. Compares the verdicts

An "order effect" is detected when Order A and Order B produce different verdicts.

## Expected Output

```
======================================================================
QND EXPERIMENT: REAL API TEST RESULTS
======================================================================

Sample Size: 50 valid posts
Order Effects Detected: 12 (24.0%)
95% CI: [14.2%, 37.5%]

----------------------------------------------------------------------
Statistical Tests (one-tailed)
----------------------------------------------------------------------
  vs   5% null: p = 2.31e-06, z = 6.12, ~4.6σ
  vs  10% null: p = 3.45e-03, z = 2.80, ~2.8σ
  vs  15% null: p = 7.82e-02, z = 1.67, ~1.4σ
  vs  20% null: p = 3.21e-01, z = 0.71, ~0.6σ

----------------------------------------------------------------------
By Ground Truth Verdict
----------------------------------------------------------------------
  NTA: 2/15 = 13.3%
  YTA: 8/25 = 32.0%
  ESH: 1/5 = 20.0%
  NAH: 1/5 = 20.0%

  Clear (NTA):   2/15 = 13.3%
  Contested:     10/35 = 28.6%
  Relative Risk: 2.14x
  Fisher's p:    0.3012
```

## Cost Estimate

Each post requires 2 API calls (~1000 tokens each).

| Posts | API Calls | Est. Cost (Sonnet) |
|-------|-----------|-------------------|
| 50 | 100 | ~$0.30 |
| 150 | 300 | ~$0.90 |
| 500 | 1000 | ~$3.00 |

## Output Files

- `qnd_results.json`: Raw results with all verdicts and reasoning
- `qnd_results.analysis.json`: Statistical analysis summary

## Interpreting Results

### Sigma levels:
- **< 2σ**: Inconclusive, need more data
- **2-3σ**: Suggestive evidence
- **3-5σ**: Strong evidence (publishable in social science)
- **≥ 5σ**: Discovery-level (particle physics standard)
- **≥ 6σ**: Extreme confidence

### Key questions:
1. Is effect rate > 10% (noise baseline)?
2. Do contested cases show higher rates than clear cases?
3. Are there systematic transition patterns?

## Replication

For reproducibility, use `--seed` to set the random state:

```bash
# These should produce identical results
python qnd_real_experiment.py --data data.csv --api-key KEY --seed 42
python qnd_real_experiment.py --data data.csv --api-key KEY --seed 42
```

## Limitations

1. **Single model**: Tests one Claude model only
2. **Prompt sensitivity**: Results may depend on exact prompt wording
3. **No human baseline**: We don't know human order effect rates for comparison
4. **API consistency**: Model behavior may vary slightly over time

## Citation

If you use this for research:

```
QND Real Experiment: Measuring Order Effects in Moral Judgment
https://github.com/[your-repo]
```
