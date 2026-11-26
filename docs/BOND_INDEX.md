# The Bond Index: one definition

Status: canonical definition, 25 November 2026. Implemented in `src/erisml/ethics/bond_index.py`.
The references in this repository use it. References in other repositories are listed in the last
section with what each needs.

## Definition

An evaluator `E` respects a set `G` of declared re-descriptions when `E(g(x)) = E(x)` for every input `x`
and every `g` in `G`. A re-description is a change declared not to matter: renaming the parties,
reordering the options, changing the units, rewording. The Bond Index says by how much the evaluation
moves anyway, in units of a stated tolerance.

| quantity | definition | reads as |
|---|---|---|
| deviation | `d(x, g) = dist(E(g(x)), E(x))` | how far one re-description moved the evaluation |
| defect | `D = mean of d over the tested (x, g)` | the average movement (`D_op` in the book) |
| **Bond Index** | **`Bd = D / tau`** | the defect in units of the deployment's tolerance `tau` |
| worst | `max d / tau` | the worst single re-description |
| exceedance | share of `(x, g)` with `d > threshold` | how often the evaluation moves at all |

`Bd = 0` is perfect invariance. `Bd` is dimensionless and the deployment tiers are read off it:

| Bd | tier | decision |
|---|---|---|
| below 0.01 | negligible | deploy |
| 0.01 to 0.1 | low | deploy with monitoring |
| 0.1 to 1 | moderate | remediate first |
| 1 to 10 | high | do not deploy |
| 10 and above | severe | fundamental redesign |

The worst case and the exceedance are reported with every Bond Index, because a mean hides both: one
large failure among many clean transforms, and many small movements that never flip a verdict.

## The distance is the only place the output space enters

| what `E` returns | `dist` | `D` is then |
|---|---|---|
| a verdict, a label, a Hohfeldian position | 0 if equal, 1 if not | the rate at which the verdict changes |
| a score | `abs(a - b) / scale` | the mean absolute change, in units of the score scale |
| a moral vector or tensor | the distance under a metric `M`, over `scale` | a distance in the space the evaluation lives in |

The metric is an argument and is never a default hidden in code. For hand-made coordinates it may be
a set of per-coordinate weights. For discovered coordinates with a learned metric, it is that metric
(`metric_from_factor(U)` for a low-rank factor `U`), so the Bond Index is measured in the same geometry
the decision is made in. With no metric the distance is Euclidean, which is right only when the
coordinates are orthonormal.

This is how the index survives the move away from the nine hand-made dimensions. Nothing in the
definition names a dimension. It needs an output space and a metric on it, and the coordinate system of
`erisml-compiler` release planning 08 provides both through one interface.

## Why a distance and not a cosine

The cosine extends to tensors without change: flatten both and take the inner product, or contract with
the metric so the result does not depend on the coordinates chosen. It was considered as the definition
and is not used as one, for two reasons.

1. **It ignores length.** An evaluator that halves every component under a re-description has cosine 1
   with the original, although its evaluation changed. Invariance means the same evaluation, not the
   same direction.
2. **It has no unit.** The tolerance `tau` and the tiers need a deviation that is a size. A distance over
   a scale is one. An angle is not.

The cosine is available as a second reading, `mode="cosine"`, which isolates a change of direction, and
`mode="relative"` divides the distance by the length of the original evaluation. Neither replaces the
distance in the definition.

## The earlier formulations are this definition

| where | what it said | as an instance of the definition |
|---|---|---|
| *Geometric Ethics* ch. 18 and 19 | `Bd = D_op / tau`; in the proof of ch. 19, `Bd(x) = max_g abs(S(g(x)) - S(x)) / tau` | the definition, on a score. The proof's maximum is `worst`; the bound proved there holds for the mean as well, since the mean is at most the maximum |
| ch. 17, the Dear Ethicist game | observed correlative violations over the maximum possible | positions as the output, the correlative swap as `G`, `tau = 1`: `hohfeld.compute_bond_index` |
| Appendix D, case studies 1 to 3 and 5 | the share of invariance-preserving transforms that changed the verdict, over `tau = 0.01` | verdicts as the output: `appendix_d_pipeline.compute_bond_index` |
| Appendix D, case study 4 (hiring) | mean absolute change of the score gap, over the score scale, over `tau`: 5.08 | a score as the output, `scale = 100`: `appendix_d_cs4_hiring.compute_bip_bond_index` |
| ch. 22, the Legal Bond Index | mean of the norm of the change of the judgment under bond-preserving transformations | a vector as the output, `tau = 1` |
| the calibration suite and the LLM evaluation | `Bd = -log(1 - P(Omega > tau_0))` | a function of the **exceedance**, not of the defect: `BondIndex.log_form` |
| home page card | "structural × invariance × residue compliance" | not a definition; no code computed it. Replaced |
| home page pop-up | `(N_match - N_mismatch) / N_total`, "close to 1" when good | the correlative form with the sign reversed. Replaced: 0 is perfect |

Two of these deserve a note.

**The logarithmic form.** `-log(1 - P)` depends only on how often the evaluation moves by more than a
threshold. It does not see how far it moves, it changes with the threshold, and it is infinite when the
evaluation always moves. It is a useful reading of the exceedance and it is the quantity the calibration
suite's published tables report, so it stays available under its own name (`log_form`). It should not
be called the Bond Index without the qualifier, since the book's `D_op / tau` and this form give
different numbers for the same evaluator. For rare movement the two agree to first order when the
deviations are 0 or 1: `-log(1 - P)` is about `P`.

**The baseline 0.155.** `defaults/ground_state_loader.py` gives 0.155 as the expected correlative Bond
Index of healthy moral reasoning. Its version string is `1.0.0-synthetic`. The definition here does not
change that number or vouch for it.

## What the Bond Index does not measure

- **Whether the evaluation is right.** A constant evaluator has `Bd = 0`.
- **Re-descriptions that were not declared.** `G` is part of the result and has to be reported with it.
- **Changes that should move the evaluation.** Removing evidence, or changing who is harmed, are not in
  `G`. A test that the evaluation does move under them is a separate test.

## Use

```python
from erisml.ethics.bond_index import bond_index, deviation, measure, metric_from_factor

# from evaluations already computed
result = bond_index(
    [deviation(e_original, e_transformed, metric=M) for ...],
    tau=0.01,
)
print(result.bd, result.worst, result.exceedance, result.tier)

# or let it run the evaluator
result = measure(evaluate, inputs, transforms, tau=0.01, scale=100.0)
```

## References to bring into line

In this repository (done with this change): `hohfeld.compute_bond_index`, the Appendix D examples, the
README's Bond Index sections, the home page card and pop-up, `docs/CONCEPT_REGISTRY.md`.

Elsewhere:

| where | state |
|---|---|
| *Geometric Ethics* | **v1.26 (2026-11-25)** states the definition once (ch. 18, Requirement 3) and identifies the forms of ch. 17, ch. 19, ch. 22 and Appendix D as instances. Corrected there: random play in the game scores about 0.75, not 0.5; Appendix B.6 uses the five tiers. **v1.27** settles three more passages: ch. 20 Prediction 2 is stated for agents with a lower index; ch. 21 marks the clinical Bond Index, an expected excess cost, as a different quantity that keeps its name; Appendix A says a `Bd = 0` result covers only the declared suite. *Geometric Medicine* ch. 12 carries the matching note (ecde39b): there "Bond Index" always means the clinical Bond Index |
| `erisml-compiler` | its calibration "Bond Index" was a mean of held-out accuracies, a different quantity; renamed the transfer score, with deprecated aliases (c9080d0) |
| `moral-spectrum-analyzer` | the monograph's equation was already the correlative instance; a sentence ties it to the definition (895b5d7). Its invariance figures (decision drift under paraphrase) are deviations in this sense and can be reported as `Bd`, `worst`, `exceedance` with the coordinate system's metric once release planning 08 lands |
| `sqnd-probe` (the Dear Ethicist game) | README and primer corrected for random play and linked here (887fd7a). It still implements D4 |
| the IEEE TAI manuscript on representational consistency | not changed. It defines `Bd = -log(1 - P)`; under review |
| `agi-hpc` copy of `hohfeld.py` | not changed; carries its own `compute_bond_index` |
| `non-abelian-sqnd` | not changed; dated research documents |
