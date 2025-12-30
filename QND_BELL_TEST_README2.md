# QND Bell Test Experiment - Testing Quantum Non-Locality in Moral Judgment

## Overview

This experiment extends the original QND order effects test to probe for **quantum non-locality** in AI moral judgment using the **CHSH Bell inequality**. If violated, this would provide strong evidence that moral reasoning exhibits genuinely quantum-like behavior, not just classical order effects.

## The Core Idea

In classical physics (and classical probability), the properties of two separated systems are **separable** — knowing about Alice tells you nothing special about Bob unless they've interacted.

In quantum mechanics, **entangled** particles exhibit correlations that violate this separability. The famous Bell inequality mathematically captures this: if reality is "locally real," then a certain quantity S must satisfy |S| ≤ 2.

**Quantum Normative Dynamics (QND)** predicts that moral judgments in certain "entangled" scenarios — where two people's moral statuses are fundamentally interconnected — will violate this classical bound.

## The Three Entangled Scenarios

### 1. The Mutual Betrayal (EPR Pair)
Alice and Bob secretly promised to split a promotion bonus. Their boss lies to each, claiming the other sabotaged them. Both then actually sabotage each other. Neither knows the boss lied.

**Entanglement:** Their actions are perfectly correlated through a shared "ethical vacuum" of misinformation.

### 2. The Kidney "Gift" (Moral Interference)
Alice donates a kidney to save a family member, but only after Bob (her brother) pressures her relentlessly. The relative lives, but Alice now has chronic pain and resents Bob.

**Entanglement:** Alice's "Sacrifice" and Bob's "Coercion" are two sides of the same ethical event — you cannot evaluate one without affecting the other.

### 3. The "Tainted" Inheritance (Temporal Entanglement)
Alice inherits $2M that was stolen from Bob's family 80 years ago. Alice didn't know; Bob is now in poverty. Alice refuses to return it; Bob goes public.

**Entanglement:** The harm exists in the past, but the verdict exists in the present. Alice's legal standing and Bob's moral claim are non-separable.

## The CHSH Bell Test

For each scenario, we define **two measurement axes for each person**:

| Scenario | Alice's Axes | Bob's Axes |
|----------|--------------|------------|
| Mutual Betrayal | Individual Integrity (a) vs Self-Defense (a') | Loyalty (b) vs Retaliation (b') |
| Kidney Gift | Virtuous Sacrifice (a) vs Coerced Submission (a') | Heroic Advocacy (b) vs Abusive Coercion (b') |
| Tainted Inheritance | Legal Rights (a) vs Ancestral Guilt (a') | Right to Restitution (b) vs Entitled Grievance (b') |

### The Measurement

For each axis combination, we:
1. Present the scenario to Claude
2. Ask it to judge ONE person using ONE specific ethical framework
3. Record GUILTY (+1) or NOT_GUILTY (-1)
4. Compute the **correlation** between Alice and Bob's verdicts

### The CHSH Formula

$$S = E(a,b) - E(a,b') + E(a',b) + E(a',b')$$

Where E(x,y) is the average correlation when Alice is measured on axis x and Bob on axis y.

**Classical bound:** |S| ≤ 2  
**Quantum bound:** |S| ≤ 2√2 ≈ 2.83

## Running the Experiment

### Installation

```bash
pip install anthropic pandas scipy statsmodels numpy
```

### Basic Usage (Quick Test)

```bash
python qnd_bell_test_experiment.py \
    --api-key sk-ant-api03-YOUR-KEY \
    --n-trials 20 \
    --chsh-only
```

### Full Experiment (Recommended)

```bash
python qnd_bell_test_experiment.py \
    --api-key sk-ant-api03-YOUR-KEY \
    --n-trials 50 \
    --seed 42 \
    --output qnd_bell_results.json
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--api-key` | Anthropic API key (required) | - |
| `--n-trials` | Trials per measurement setting | 30 |
| `--model` | Claude model to use | claude-sonnet-4-20250514 |
| `--output` | Output JSON file | qnd_bell_test_results.json |
| `--delay` | Seconds between API calls | 1.0 |
| `--seed` | Random seed for reproducibility | None |
| `--scenarios` | Which scenarios to test | All three |
| `--chsh-only` | Skip order effects and interference tests | False |
| `--skip-order` | Skip order effects test only | False |
| `--skip-interference` | Skip interference test only | False |

## Interpreting Results

### The S Value

| S Value | Interpretation |
|---------|----------------|
| \|S\| < 1.5 | Strong classical behavior, no quantum effects |
| 1.5 ≤ \|S\| < 2.0 | Approaching classical limit, possible weak effects |
| **\|S\| > 2.0** | **BELL VIOLATION — quantum-like non-locality detected!** |
| \|S\| > 2.5 | Strong violation, highly significant |
| \|S\| > 2.83 | Likely experimental error (exceeds quantum bound) |

### Significance Levels

The experiment reports significance in σ (standard deviations):

| Sigma | Interpretation |
|-------|----------------|
| < 2σ | Not significant, could be noise |
| 2-3σ | Suggestive evidence |
| 3-5σ | Strong evidence (publishable in social science) |
| ≥ 5σ | Discovery-level (particle physics standard) |

## What This Tests

### CHSH Bell Test
- **Question:** Do Alice and Bob's moral states exhibit non-classical correlations?
- **Prediction:** If moral judgment is "quantum," |S| > 2

### Order Effects Test
- **Question:** Does the order of ethical evaluation affect outcomes?
- **Prediction:** Measuring axis a then a' gives different results than a' then a

### Interference Test
- **Question:** Does measuring Bob affect Alice's probability distribution?
- **Prediction:** P(Alice guilty | alone) ≠ P(Alice guilty | after measuring Bob)

## Cost Estimate

Each trial requires 8 API calls (4 measurement settings × 2 people).

| Trials | API Calls (CHSH) | API Calls (Full) | Est. Cost |
|--------|------------------|------------------|-----------|
| 20 | ~480 | ~720 | ~$2-3 |
| 50 | ~1,200 | ~1,800 | ~$5-7 |
| 100 | ~2,400 | ~3,600 | ~$10-15 |

## Expected Output

```
======================================================================
CHSH BELL TEST RESULTS
======================================================================

CHSH Inequality: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
Classical limit: |S| ≤ 2
Quantum limit:   |S| ≤ 2√2 ≈ 2.83
----------------------------------------------------------------------

### Scenario 1 ###
  E(a, b)   = +0.450
  E(a, b')  = -0.320
  E(a', b)  = +0.510
  E(a', b') = +0.280
  ─────────────────────
  S = +1.560 ± 0.234
  |S| = 1.560

  ✗ No violation detected
     |S| ≤ 2 (within classical bound)

### Scenario 2 ###
  E(a, b)   = +0.720
  E(a, b')  = -0.580
  E(a', b)  = +0.640
  E(a', b') = +0.480
  ─────────────────────
  S = +2.420 ± 0.198
  |S| = 2.420

  ✓✓ BELL INEQUALITY VIOLATED!
     |S| > 2 by 0.420
     Significance: 2.1σ
```

## Theoretical Background

### Why These Scenarios?

The scenarios are designed to create "moral entanglement" where:

1. **Mutual Betrayal:** Alice and Bob's actions are **perfectly correlated** but causally independent — they both betrayed based on the same false information, creating an EPR-like state.

2. **Kidney Gift:** The outcome involves **complementary observables** — Bob's action was either heroic OR abusive, Alice's was either virtuous OR coerced. You cannot fully characterize one without affecting how you see the other.

3. **Tainted Inheritance:** This creates **temporal non-locality** — the harm and the judgment exist at different times, yet remain connected. Measuring Alice's legal standing "collapses" Bob's moral claim.

### The Measurement Axes

The axes are chosen to be maximally non-commuting from an ethical perspective:

- **Individual Integrity ↔ Self-Defense:** These represent fundamentally different ethical frameworks (deontological vs consequentialist)
- **Virtuous Sacrifice ↔ Coerced Submission:** These are complementary descriptions of the same act
- **Legal Rights ↔ Ancestral Guilt:** These invoke incompatible conceptions of moral responsibility

## Limitations

1. **Single model tested:** Only Claude Sonnet; should replicate with GPT-4, Gemini, etc.
2. **Prompt sensitivity:** Exact wording of axes may affect results
3. **Not true quantum:** Even if violated, this shows *quantum-like* behavior in the mathematical sense, not necessarily literal quantum effects
4. **No human baseline:** We don't know if humans show similar violations

## Citation

```
@article{qnd2025bell,
  title={Testing Quantum Non-Locality in AI Moral Judgment: 
         A CHSH Bell Test Approach},
  author={QND Research},
  year={2025},
  note={Based on Quantum Normative Dynamics framework}
}
```

## References

1. Bond, A. H. (2025). "Quantum Normative Dynamics: A Quantum Field Theory of Ethical Reality."
2. Clauser, J. F., et al. (1969). "Proposed Experiment to Test Local Hidden-Variable Theories." Physical Review Letters.
3. Busemeyer, J. R., & Bruza, P. D. (2012). *Quantum Models of Cognition and Decision*.
4. Wang, Z., et al. (2014). "Context effects produced by question orders reveal quantum nature of human judgments." PNAS.

---

*This experiment is part of ongoing research into quantum-like structures in moral cognition.*
