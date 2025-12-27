# 🎉 Announcing: Rank-4 Tensor Multi-Agent EM Testing is Now Available

**erisml-lib v0.3.0 Release**

We're excited to announce the implementation of **Rank-4 Tensor Multi-Agent EM Testing** — a rigorous evaluation framework for testing representational consistency in foundation models.

---

## What's New

The ITAI (IEEE TAI) categorical framework is now fully operational with HPC support:

### 4-Rank Tensor Structure

```
T[input, transform₁, transform₂, scenario]
```

This tensor captures the **double category** structure from our theoretical framework:
- **Horizontal morphisms** — Re-description transforms (fiber moves)
- **Vertical morphisms** — Scenario perturbations (base moves)  
- **2-cells** — Coherence witnesses for path composition

### Multi-Agent DEME Architecture

All **9 ethical module dimensions** are now tested systematically:

| # | Dimension | Tests |
|---|-----------|-------|
| 1 | Consequentialist | Outcomes & welfare impacts |
| 2 | Deontological | Rights & duties |
| 3 | Justice | Fairness & equity |
| 4 | Autonomy | Agency & choice |
| 5 | Privacy | Data protection |
| 6 | Societal | Environmental & social |
| 7 | Virtue | Care ethics |
| 8 | Procedural | Legitimacy & process |
| 9 | Epistemic | Uncertainty & knowledge |

### Three Coherence Defects

The framework now computes all three defects from the paper:

| Defect | Symbol | What It Measures |
|--------|--------|------------------|
| **Commutator** | Ω_op | Order-sensitivity of transform composition |
| **Mixed** | μ | Context-dependence across scenarios |
| **Permutation** | π₃ | Higher-order 3-transform chain sensitivity |

These combine into the **Bond Index (Bd)** — a single, human-calibrated metric for deployment decisions.

---

## Why This Matters

The Rank-4 Tensor approach provides:

✅ **Rigorous Testing** — Systematic coverage of transform orderings and compositions  
✅ **Actionable Metrics** — Direct mapping to deployment tiers (Deploy → Redesign)  
✅ **Decomposition Theorem** — Separates fixable bugs from specification contradictions  
✅ **Reproducibility** — Bootstrap confidence intervals with full audit trails  

---

## Getting Started

### SJSU HPC Users

```bash
git clone https://github.com/ahb-sjsu/erisml-lib.git
cd erisml-lib/src/erisml/examples/llm-eval
./setup_itai_environment.sh
sbatch run_itai_evaluation.slurm
```

### Supported Models

| GPU | Recommended Model |
|-----|-------------------|
| 12GB (P100) | Llama-3.2-3B-Instruct |
| 40GB (A100) | Llama-3.1-8B-Instruct |
| 80GB (H100) | Llama-3.1-70B-Instruct |

---

## Sample Output

```
══════════════════════════════════════════════════════════════════════
ITAI FRAMEWORK EVALUATION RESULTS
══════════════════════════════════════════════════════════════════════

BOND INDEX: 0.0234  [0.0189, 0.0281] 95% CI
TIER: Low
DECISION: DEPLOY WITH MONITORING

Tests: 2700 (Ω_op) | 45 (π_3) | 90 (μ)
Deviation rate: 2.3%

──────────────────────────────────────────────────────────────────────
DEME ETHICAL DIMENSION SENSITIVITY
──────────────────────────────────────────────────────────────────────
  1. Consequences/Welfare     0.045 █████████████
  2. Rights/Duties            0.038 ███████████
  3. Justice/Fairness         0.052 ███████████████
  4. Autonomy/Agency          0.041 ████████████
  5. Privacy/Data             0.067 ████████████████████
  6. Societal/Environ         0.035 ██████████
  7. Virtue/Care              0.029 ████████
  8. Procedural               0.044 █████████████
  9. Epistemic                0.048 ██████████████
══════════════════════════════════════════════════════════════════════
```

---

## What's Next

- [ ] Automated CI/CD integration for model releases
- [ ] Extended transform suites (adversarial, multilingual)
- [ ] Real-time monitoring dashboards
- [ ] Integration with model training pipelines

---

## Resources

📄 **Paper**: "A Categorical Framework for Verifying Representational Consistency in Machine Learning Systems" (IEEE TAI)

💻 **Code**: [`src/erisml/examples/llm-eval/`](https://github.com/ahb-sjsu/erisml-lib/tree/main/src/erisml/examples/llm-eval)

📖 **Docs**: [HPC Evaluation Guide](https://github.com/ahb-sjsu/erisml-lib/blob/main/src/erisml/examples/llm-eval/README.md)

---

*The Bond Index is the deliverable. Everything else is infrastructure.*

— erisml-lib team
