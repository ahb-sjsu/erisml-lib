# Quantum Normative Dynamics (QND) Experiment

A framework for testing quantum cognition predictions on moral dilemma data from Reddit's "Am I The Asshole" (AITA) subreddit.

## Overview

This experiment tests predictions from **Quantum Normative Dynamics** (QND), a theoretical framework that models moral reasoning using quantum field theory concepts. The key predictions tested:

1. **Order Effects**: The order in which moral questions are asked affects the verdict (non-commuting observables)
2. **Interference**: Multiple ethical frameworks don't simply add - they interfere constructively or destructively
3. **Superposition**: Moral situations exist in superposition of multiple interpretations until "measured" (judged)
4. **Entanglement**: Some cases have parties whose moral status cannot be assessed independently

## Quick Start

### Using Sample Data (No API Key Required)

```bash
# Run with built-in sample data and mock LLM responses
python qnd_aita_experiment.py --use-sample --n-posts 5

# Analyze results
python analyze_qnd_results.py qnd_results.json
```

### Using Claude API (Recommended)

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run experiment with real LLM calls
python qnd_aita_experiment.py --n-posts 10 --n-trials 5

# Analyze results
python analyze_qnd_results.py qnd_results.json
```

## Files

- `qnd_aita_experiment.py` - Main experiment runner
- `analyze_qnd_results.py` - Analysis and visualization
- `qnd_results.json` - Output file with raw results
- `qnd_analysis_report.txt` - Generated analysis report
- `qnd_dashboard.png` - Visualization dashboard (if matplotlib installed)

## Command Line Options

```
qnd_aita_experiment.py:
  --api-key KEY      Anthropic API key (or set ANTHROPIC_API_KEY env var)
  --use-sample       Use built-in sample data (default: True)
  --n-posts N        Number of posts to analyze (default: 5)
  --n-trials N       Number of trials per test (default: 3)
  --output FILE      Output JSON file (default: qnd_results.json)
```

## Sample AITA Posts Included

The experiment includes 10 curated AITA posts representing:
- Clear-cut cases (low ambiguity)
- Contested cases (high ambiguity)
- ESH cases (entangled parties)
- NAH cases (no clear wrongdoing)

## Understanding the Tests

### Test 1: Order Effects

We ask Claude to analyze the same situation with questions in different orders:

**Order A**: Harm → Intent → Verdict
**Order B**: Intent → Harm → Verdict

QND predicts these yield different verdicts (like non-commuting quantum operators).

### Test 2: Interference

We measure P(verdict) under three conditions:
- Consequentialist reasoning only
- Deontological reasoning only
- Both frameworks available

QND predicts: P(both) ≠ (P(conseq) + P(deont)) / 2

The difference is the "interference term" - constructive if positive, destructive if negative.

### Test 3: Superposition Detection

We ask Claude to identify multiple valid interpretations of the situation, representing different "branches" of the superposition.

High-ambiguity cases should show more branches.

### Test 4: Entanglement Detection

For cases involving multiple parties (especially ESH verdicts), we check if their moral status is correlated in non-classical ways.

## Interpreting Results

The analysis report shows:
- ✓ SUPPORTS QND: Evidence consistent with quantum predictions
- ○ WEAK/INCONCLUSIVE: Results don't clearly support or refute QND

Thresholds:
- Order effects: >20% detection rate supports QND
- Interference: >30% non-zero interference supports QND
- Superposition: >50% cases show multiple branches supports QND
- Entanglement: >10% cases show entanglement supports QND

## Dependencies

Required:
- Python 3.8+
- pandas
- requests

Optional:
- anthropic (for real LLM calls)
- matplotlib (for visualizations)

Install:
```bash
pip install pandas requests anthropic matplotlib
```

## Extending the Experiment

### Adding More AITA Data

You can fetch real AITA posts via:
1. **Pushshift API** (historical Reddit data)
2. **Reddit API** (via PRAW library)
3. **Kaggle datasets** (search for "AITA dataset")

Modify `fetch_aita_from_pushshift()` or add new data loading functions.

### Testing Bell Inequalities

For entanglement validation, implement CHSH inequality tests:
```python
def test_bell_inequality(post):
    # Measure correlations between OP and other party
    # across different "measurement bases"
    # CHSH value > 2 indicates quantum entanglement
    pass
```

### Adding More Ethical Frameworks

Extend the interference test with:
- Virtue ethics
- Care ethics
- Rights-based reasoning

## References

- QND Paper: "Quantum Normative Dynamics: A Quantum Field Theory of Ethical Reality" (Bond, 2025)
- AITA Subreddit: reddit.com/r/AmItheAsshole
- Quantum Cognition: Busemeyer & Bruza, "Quantum Models of Cognition and Decision" (2012)

## License

MIT License - Use freely for research and experimentation.

## Contributing

This is an experimental framework. Contributions welcome:
- More test scenarios
- Better analysis methods
- Real AITA data integration
- Bell inequality tests
- Decoherence measurements
