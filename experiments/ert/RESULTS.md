# ERT empirical verification — results

Tests of **Endogenous Reference Theory** (`docs/papers/foundations/endogenous_reference_theory.md`).
Reproducible from repo data + cached/downloadable models. **Convention: nulls and inconclusive
results are reported as such.** Shared primitives: `ert_analysis.py` (Fréchet means, Fisher-Rao
sphere, bimodality battery), validated on a synthetic uni/bimodal control.

## Scoreboard

| # | Test | Source | Result |
|---|------|--------|--------|
| 1 | Synthetic schism theorem (Prop 2) | — | ✅ **Confirmed** |
| 2 | 5a (bimodality) | AITA (2.9k) | ❌ Null — underpowered |
| 3 | 5b (multimodality of country refs) | GlobalOpinionQA (906 q) | ⚠️ **Core supported**, sacred-axis not |
| 4 | 5a (labeled axis) | MFRC (17.8k) | ❌ Null / uninformative |
| 5 | 5a (real-vote axis, PRIMARY) | Scruples (25.3k) | ❌ Null on the clean measure |
| 6 | 5b (population, decisive) | Moral Machine (177 agents) | ⚠️ **Basins yes; sacred-axis FALSIFIED** |

## 1. Synthetic — CONFIRMED
Stiffness matches `4·δ·cot(δ)` to 4 dp, crosses zero at **δ=1.566 ≈ π/2**; Fréchet reference
bifurcates **only** under positive curvature (1→2 minima on the sphere, always 1 on the plane).
The theorem and the code are correct. *(This confirms the math, not that morality obeys it.)*

## 2. AITA — null (underpowered)
Moral-axis recoverability AUC≈0.60 (text encodes topic, not verdict); 4.5:1 NTA skew. No
contestation↔bimodality relation; robust across bge-small/bge-base. Instrument too weak to test.

## 3. GlobalOpinionQA — mixed; the one positive signal
906 questions; each country a load configuration on a Fisher-Rao sphere.
**dispersion ↔ multimodality: ρ=+0.144, p=1.4e-5 — significant** (the link AITA could not detect).
7% of questions show a genuinely bifurcated reference. **But the sacred-axis prediction failed**
(sacred vs material dBIC, p=0.32; dispersion-controlled p=0.44; sacred n=26, crude keyword tags).
Reading: weak support for "references bifurcate as contestation rises"; no support for the
sacred-axis refinement.

## 4. MFRC — null / uninformative
Labeled moral-foundation axis (fixes the AUC ceiling), annotator-level disagreement. But the
discrete MF vectors **saturate** the bimodality measure (40/40 clusters flagged), disagreement is
collinear with dispersion (ρ=0.90), and the honest summary — **partial correlation controlling for
dispersion — is null (ρ=−0.009, p=0.96)**. Discrete labels don't support the continuous test.

## 5. Scruples — null on the clean measure (PRIMARY test)
25,284 anecdotes, mean 19.8 community votes each, 32% genuinely divisive — moral position from
**real votes** (`p_wrong`), so immune to the AUC problem.
- clean measure (judgment dispersion ↔ two-camp bimodality): **ρ=−0.12, p=0.45 (null)**
- the significant negative (contestation↔bimodality, partial ρ=−0.36, p=0.022) is **a tautology**:
  divisive anecdotes sit at p≈0.5, the *valley* between the two camps, so they mechanically reduce
  0/1 bimodality. Not evidence either way.
- 40/40 "bimodal" saturation ⇒ absolute flag uninformative.
**Does not support** the schism prediction; the negative is an operationalization artifact.

## 6. Moral Machine — decisive test run; sacred-axis FALSIFIED
`mm_5b_test.py`. The decisive instrument was pre-registered as the human 130-country × 9-AMCE matrix.
The data that became available is an **LLM Moral Machine benchmark** —
`summary_overall_preferences.csv`, a labeled **9-dimension × 177-agent** AMCE matrix (176 LLMs + one
aggregate "Human"; no per-country human matrix). So this is the well-powered 5b test on an **AI-model
population**, not human cultures — it informs the *mechanism* but does not strictly satisfy the
country-level pre-registration. The 9 labeled dims removed every instrument excuse (no embedding, no
AUC ceiling).

**Pre-registered kill criterion (adapted to this population):**
- **Confirm:** references cluster into ≥2 stable basins **and** multimodality concentrates on
  sacred/identity dimensions (age/gender/status/species/fitness) over impartial ones
  (number/intervention/law/relation), dispersion-controlled, p<0.01.
- **Kill:** clean null/contradiction on this well-powered instrument.

**Result:**
- **(A) Basins — PASS.** GMM BIC improves monotonically k=1→4 (3492→3366→3247→3235), BIC-optimal = 4
  components; silhouette 0.36–0.40; principal-axis dBIC +56. Agent references do split into camps.
- **(B) Sacred-axis — FAIL, opposite direction.** The most bimodal dimensions are **impartial**
  (No. Characters dBIC +103, Relation-to-AV, Law) plus Species; the identity axes (Age, Gender,
  Social Status, Fitness) are the *least* bimodal — agents largely **agree** there. Mann-Whitney
  sacred > impartial: **p=0.90** (Sarle) / 0.90 (dBIC); the impartial axes carry the schism.
- **Verdict: NOT CONFIRMED.** The distinctive ERT mechanism (schism on sacred/high-curvature axes)
  is contradicted. The actual disagreement is on the **consequentialist aggregation axis** (how much
  "more lives" / species matter) — i.e. framework-level, not sacred-value-level.

## Honest overall conclusion
The schism **theorem holds** (math). Its distinctive **empirical** prediction — that real moral
schism concentrates on **sacred/high-curvature value axes** — has now **failed twice with zero
confirmations**: null on GlobalOpinionQA (n=26) and **contradicted on Moral Machine** (n=177,
well-powered, labeled, p=0.90 wrong direction). What survives is only the weaker claim that **moral
references bifurcate into camps** (GOQA ρ=0.14; MM 3–4 basins) — which is ordinary opinion-dynamics
clustering, not unique to ERT. **The distinctive empirical thesis is falsified.** ERT stands as a
coherent philosophical reframe + correct theorems + a shipped engineering tool (below); its signature
empirical claim did not survive its decisive test. *(Caveat: the exact human per-country matrix was
not available — only an aggregate Human column — so the human-cultural version is technically
untested; but the mechanism failed on a strong, well-powered proxy population on top of the GOQA null.)*

## Salvageable engineering (falsification-independent)
The aggregation machinery is useful to DEME/the compiler regardless of the science:
`src/erisml/ethics/governance/consensus.py` adds a **schism / consensus diagnostic** (bimodality of
EM judgements → flag when a single aggregate verdict masks two camps), wired non-breaking into
`aggregate_judgements` (`metadata["consensus"]` + a rationale warning). 11 governance+consensus
tests pass. This ships independent of how the Moral Machine test resolves.

## Reproduce
```bash
python experiments/ert/synthetic_bifurcation.py
python experiments/ert/goqa_5b_test.py
python experiments/ert/mfrc_5a_test.py
python experiments/ert/scruples_5a_test.py        # downloads Scruples (25 MB) on first run
python experiments/ert/mm_5b_test.py              # needs mm_data/mm_unzip/summary_overall_preferences.csv
```
Embedding/data caches (`*.npy`, `scruples_data/`, `mm_data/`) are git-ignored.
