# ERT empirical verification — results

Empirical tests of **Endogenous Reference Theory** (`docs/papers/foundations/endogenous_reference_theory.md`).
Scripts here are reproducible from repo data + cached/downloadable sentence-transformer models.
Reporting convention: **nulls and inconclusive results are reported as such.**

---

## 1. Synthetic validation of the schism theorem — CONFIRMED

`synthetic_bifurcation.py` numerically tests Proposition 2 and the stiffness curve of §5.6–5.7,
where ground truth is known. This validates both the theory and the Fréchet/curvature code.

**Prediction (i): perpendicular "schism stiffness" at the midpoint of two clusters.**
The measured second derivative of the Fréchet function matches the closed form
$h_\kappa(\delta)=\sqrt\kappa\,\delta\cot(\sqrt\kappa\,\delta)$ (here $4\delta\cot\delta$ for the
two-point sum) **to four decimals**, and crosses zero at **δ = 1.566 ≈ π/2 = 1.571**. On the flat
plane the stiffness is constant (4.0) and never reaches zero.

**Prediction (ii): number of Fréchet minima vs cluster spread.**
On the sphere the count jumps **1 → 2** as clusters spread past threshold; on the plane it stays **1**
for all spreads. Bifurcation of the reference is a strictly positive-curvature phenomenon, as proved.

> **Verdict: the formal result holds and the code is correct.** This is a numerical confirmation of a
> theorem, not yet evidence about real morality.

---

## 2. First real-data probe (AITA, n = 2922) — INCONCLUSIVE NULL

`aita_schism_test.py` tests **Falsifier 5** on real moral judgments: where a community's verdict
*splits*, ERT predicts the moral-position distribution is **bimodal** (two references), not merely a
higher-variance unimodal blob. Per topic cluster (KMeans, K=30) we measure verdict entropy
(contestation) and bimodality of the moral-position projection (GMM 1-vs-2 BIC; Sarle's coefficient),
plus a partial correlation controlling for dispersion.

**Result (robust across two embedders):**

| Embedder | moral-axis AUC | entropy↔dBIC (ρ, p) | entropy↔BC (ρ, p) | partial (|disp) | % topics bimodal |
|---|--:|--|--|--|--:|
| bge-small-en-v1.5 (384-d) | 0.594 | −0.05 (.81) | −0.17 (.38) | −0.01 (.97) | 0% |
| bge-base-en-v1.5 (768-d)  | 0.605 | −0.03 (.89) | +0.14 (.45) | −0.04 (.82) | 0% |

No relationship between contestation and bimodality; **no topic was bimodal** (mean Sarle BC ≈ 0.17,
far below the 0.555 line) whether contested or consensus.

**This is a null, but an *underpowered* one — not a clean falsification.** Three reasons:

1. **The instrument can barely see the moral axis.** A YTA-vs-NTA linear probe reaches only
   AUC ≈ 0.60 — full-post embeddings encode mostly *topic*, so the projection tested for bimodality is
   largely noise. Improving the embedder (bge-small → bge-base) barely moved AUC, so this is a
   property of the task/encoder, not a tuning issue.
2. **The corpus is ill-suited.** AITA verdicts are **4.5:1 NTA-skewed** (NTA 2235, YTA 502) —
   self-selection: people post when they expect vindication. Genuine schism is rare here; contested
   topics (entropy ≥ 0.8) number only 4–7 of 30.
3. **The operationalization is indirect.** A 1-D logistic projection is a weak proxy for bimodality of
   the moral *manifold*, and the **curvature axis of Falsifier 5 was not tested** at all.

> **Verdict: no support found, robust to embedder — but the test cannot currently *falsify* ERT
> either, because the instrument cannot resolve the moral axis on this corpus.**

---

## 3. What a properly powered test needs

- A **polarized corpus with vote-margin data** (e.g., contested moral topics with real for/against
  splits), so contestation is measured directly rather than inferred from a skewed verdict label.
- A **stronger moral-position recovery** — the framework's own `MoralVector`/DEME scorer, or a model
  fine-tuned for moral judgment — to push the axis AUC well above 0.6.
- A **direct manifold-curvature estimate** (local PCA/sectional-curvature proxy) to test the other half
  of Falsifier 5: that schisms concentrate on high-curvature (sacred/identity) axes.
- The **early-warning test (Falsifier 6)** requires a *time series* of a community's reference; AITA is
  cross-sectional and cannot support it.

## Reproduce

```bash
python experiments/ert/synthetic_bifurcation.py            # §1, fast, no data needed
python experiments/ert/aita_schism_test.py                 # §2 (bge-small, default)
ERT_MODEL=BAAI/bge-base-en-v1.5 python experiments/ert/aita_schism_test.py   # §2 (bge-base)
```
Embedding caches (`aita_emb_*.npy`) are regenerated on first run and are git-ignored.
