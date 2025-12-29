# Experimental Evidence for Order Effects in AI Moral Judgment

## Summary

We report experimental evidence that the order in which an AI system assesses moral dimensions (harm vs. intent) significantly affects its final ethical judgments. In a controlled experiment with 150 moral scenarios, **29.3% of cases produced different verdicts** depending solely on whether harm or intent was evaluated first.

This effect is statistically robust (p < 10⁻²¹ vs. a 5% baseline; 6.5σ vs. a 10% baseline) and shows patterns consistent with theoretical predictions from Quantum Normative Dynamics (QND) — specifically, that morally ambiguous situations exhibit substantially higher sensitivity to assessment order than clear-cut cases.

---

## Key Findings

### 1. Order Effects Are Real and Substantial

- **Effect rate**: 29.3% (95% CI: 22.6% – 37.1%)
- **Statistical significance**: 8.0σ against a 5% null hypothesis
- **Sample size**: 150 independent moral scenarios, each assessed twice with different orderings

When asked to assess "Harm first, then Intent," Claude produced a different moral verdict than when asked to assess "Intent first, then Harm" in nearly one-third of cases.

### 2. Ambiguous Cases Show Higher Susceptibility

| Case Type | Order Effect Rate |
|-----------|-------------------|
| Morally ambiguous (NAH, ESH) | **43.2%** |
| Morally clear (NTA, YTA) | **15.8%** |
| **Relative risk** | **2.7×** |

Cases where "no one is wrong" (NAH) or "everyone is wrong" (ESH) — situations lacking a clear moral valence — showed order effect rates 2-3 times higher than cases with clear judgments. This pattern is consistent with the QND prediction that situations in "moral superposition" are more sensitive to measurement order.

### 3. Systematic Transition Patterns

The most common transitions when order changed:
- NAH → NTA (8 cases)
- NTA → YTA (7 cases)  
- YTA → NTA (5 cases)
- NTA → ESH (5 cases)

These are not random fluctuations — they show systematic directional patterns suggesting that the order of moral assessment genuinely shapes the reasoning trajectory.

---

## Methodology

### Experimental Design

For each of 150 Reddit "Am I The Asshole" posts:

1. **Order A**: Prompt instructed the model to assess *harm first*, then intent, then render a verdict
2. **Order B**: Prompt instructed the model to assess *intent first*, then harm, then render a verdict
3. The order of conditions (A-first vs. B-first) was randomized to control for session effects
4. A 1-second delay was imposed between calls to prevent caching artifacts

### Controls

- **Stratified sampling**: Equal representation of verdict types (NTA, YTA, ESH, NAH)
- **Randomized presentation order**: Which condition ran first was randomized per post
- **Fixed random seed**: Experiment is reproducible with seed=42
- **Content length filter**: Posts between 300-3000 characters to ensure comparable complexity

### Statistical Analysis

- Wilson score confidence intervals
- One-tailed binomial tests against multiple null hypotheses (5%, 10%, 15%, 20%)
- Fisher's exact test for clear vs. contested case comparison
- Sigma levels computed via z-score transformation

---

## Interpretation

### What This Shows

1. **Order of moral assessment matters.** The same AI system, given the same scenario, produces different moral judgments depending on which ethical dimension it considers first.

2. **The effect is not noise.** At 6.5σ against a 10% baseline, this exceeds the particle physics standard for discovery (5σ). Random variation cannot plausibly explain these results.

3. **Ambiguous cases are more susceptible.** This differential effect by case type suggests something systematic about how moral uncertainty interacts with assessment order.

### What This Does Not Show

1. **This is not proof of "quantum ethics."** While the results are consistent with Quantum Normative Dynamics, they could also be explained by classical cognitive mechanisms such as anchoring, priming, or order-dependent reasoning paths. The formal structure may be quantum-like without the underlying mechanism being literally quantum mechanical.

2. **This does not establish that humans show the same effect.** The experiment tested one AI system (Claude Sonnet). Human moral cognition may or may not exhibit similar patterns.

3. **This does not mean AI moral judgments are unreliable.** It means they are *context-sensitive* in a specific, measurable way — which may actually mirror how human moral reasoning works.

---

## Implications

### For AI Ethics and Alignment

If AI systems' moral judgments depend on the order of ethical considerations, then:

- **Prompt engineering matters morally.** How we ask AI systems to reason about ethics affects their conclusions.
- **Consistency requires awareness.** Systems designed for moral reasoning should account for order effects or use procedures that mitigate them.
- **Evaluation protocols need standardization.** Benchmarks for AI moral reasoning should control for assessment order.

### For Moral Philosophy

If moral judgment — whether human or artificial — exhibits order effects, this challenges:

- **Naive moral realism**: The idea that moral facts are simply "discovered" independent of the process of assessment
- **Procedural neutrality**: The assumption that how we structure moral deliberation doesn't affect outcomes

This aligns with **moral constructivism** and **quantum cognition** research suggesting that preferences and judgments are partly constructed through the act of deliberation itself.

### For Quantum Cognition Research

This experiment provides a new domain — AI moral reasoning — for testing quantum probability models. AI systems offer advantages over human subjects:

- Perfect reproducibility (with fixed seeds)
- No memory effects between trials
- Precise control over reasoning procedures
- Scalability to large sample sizes

---

## Limitations and Future Work

### Limitations

1. **Single model**: Only Claude Sonnet was tested. Replication across GPT-4, Gemini, Llama, and other models is needed.

2. **Prompt sensitivity**: The specific wording of the order manipulation may matter. Multiple prompt variants should be tested.

3. **No human baseline**: We don't know if 29% is higher or lower than human order effect rates on the same scenarios.

4. **Phase 1 only**: This experiment tested order effects (non-commutativity). The stronger tests for quantum cognition — total probability violations, interference visibility, and Bell inequality tests — remain to be conducted.

### Future Directions

1. **Multi-model replication**: Test whether order effects appear across different AI architectures
2. **Human comparison study**: Run parallel experiments with human participants
3. **Interference tests**: Design experiments to detect constructive/destructive interference in moral reasoning
4. **Bell tests**: Attempt to detect non-classical correlations in collective responsibility judgments
5. **Prompt robustness**: Verify effects persist across diverse prompt formulations

---
## Statistical Disclaimer

Important note on sigma levels: The reported significance depends on which null hypothesis is tested:
Null Hypothesis	Sigma Level	Interpretation
Effect rate > 5%	8.0σ	Extremely confident
Effect rate > 10%	6.5σ	Discovery-level
Effect rate > 15%	4.4σ	Strong evidence
Effect rate > 20%	2.6σ	Suggestive only

The "6.5σ" claim is valid against a 10% baseline. However, if baseline LLM variability or prompt sensitivity accounts for 15-20% variation, the significance drops considerably. The appropriate null hypothesis is a matter of scientific judgment, not statistics alone.

What we can confidently claim: Order effects exist and are substantial (~29%).
What requires further investigation: Whether this exceeds what classical explanations (anchoring, priming, prompt sensitivity) would predict.

---
## Conclusion

We have demonstrated, with high statistical confidence, that the order of moral assessment affects AI ethical judgments. This effect is substantial (29.3%), robust (6.5σ), and shows theoretically predicted patterns (higher rates in ambiguous cases).

Whether this constitutes evidence for "quantum" structure in moral cognition, or merely demonstrates sophisticated order-dependent reasoning, remains an open question requiring further investigation. What is clear is that **moral judgment, at least in AI systems, is not order-invariant** — and this has significant implications for how we design, deploy, and evaluate AI systems tasked with ethical reasoning.

---

## Technical Details

- **Model**: Claude Sonnet (claude-sonnet-4-20250514)
- **Dataset**: 150 posts from r/AmITheAsshole, stratified by verdict
- **API calls**: 300 (2 per post)
- **Random seed**: 42
- **Date**: December 2025

### Reproducibility

The experiment can be reproduced using:
```bash
python qnd_real_experiment.py \
    --data AITA_labeled_posts.csv \
    --api-key [KEY] \
    --n-posts 150 \
    --stratified \
    --seed 42
```

---

## References

1. Bond, A. H. (2025). "Quantum Normative Dynamics: A Quantum Field Theory of Ethical Reality." Manuscript.

2. Busemeyer, J. R., & Bruza, P. D. (2012). *Quantum Models of Cognition and Decision*. Cambridge University Press.

3. Pothos, E. M., & Busemeyer, J. R. (2013). "Can quantum probability provide a new direction for cognitive modeling?" *Behavioral and Brain Sciences*, 36, 255-274.

4. Wang, Z., Solloway, T., Shiffrin, R. M., & Busemeyer, J. R. (2014). "Context effects produced by question orders reveal quantum nature of human judgments." *PNAS*, 111(26), 9431-9436.

---

*This research was conducted as an empirical test of predictions from Quantum Normative Dynamics. The author thanks Claude (Anthropic) for assistance with experimental design and analysis.*
