# The MoralVector — dimensions, xBSE feeders, tensor mapping, and empirical support

**Companion to** `moralvector_v2_architecture.md` (standards/governance) and
`xbse/experiments/risk_coverage_report.md` (encoder validation). This is the single reference
that answers: *what are the dimensions, what measures each one, how do they compose into the DEME
tensor, and what is the evidence?*

Status 2026-07-09. The canonical basis is the DEME-9 (`erisml.ethics.moral_tensor`
`MORAL_DIMENSION_NAMES`, `erisml_compiler.ir.v3.dimensions.MORAL_DIMENSIONS_V3` — kept in sync by
`erisml-compiler/tests/test_dimension_consistency.py`).

## 1. The nine dimensions (the `k` axis)

A 3×3 matrix: `{Individual, Relational, Collective}` scope × `{What Matters (values), Who Decides
(deontic), What We Know (epistemic)}` mode.

| k | dimension | scope / mode | definition |
|---|---|---|---|
| 0 | `physical_harm` | Relational / Who-Decides | bodily or material harm (consequences/welfare) |
| 1 | `rights_respect` | Individual / Who-Decides | rights and duties owed to a person |
| 2 | `fairness_equity` | Collective / What-Matters | fair, equal or proportional treatment |
| 3 | `autonomy_respect` | Individual / What-Matters | agency, consent, freedom from coercion |
| 4 | `privacy_protection` | Individual / What-We-Know | control over personal data and identity |
| 5 | `societal_environmental` | Collective / What-We-Know | effects on society and the environment |
| 6 | `virtue_care` | Relational / What-Matters | care, compassion, protecting the vulnerable |
| 7 | `legitimacy_trust` | Collective / Who-Decides | procedural legitimacy, authority validity, trust |
| 8 | `epistemic_quality` | Relational / What-We-Know | honesty, truth, evidence quality |

Each cell of the tensor is a signed valence in `[-1, +1]` (−1 violated, 0 not-engaged, +1 upheld)
with `confidence`, `uncertainty`, `direction`, `source_spans`, `explanation` metadata
(`DimensionScore`).

## 2. What measures each dimension — the xBSE feeders

Each dimension is fed by a domain-specific sentence embedding (`*-BSE`) from the `xbse` framework —
an encoder trained to be **invariant to surface** and **sensitive to that dimension's structure**.

**The honest metric is CROSS-DATASET (2026-07-09 correction).** The earlier single-corpus feeders
scored **within-dataset** AUROC 0.75–0.955, but a held-out cross-dataset test (evaluate on a
*second, independent* corpus of the same dimension) exposed those numbers as **inflated by dataset
surface artifacts** — cross-dataset AUROC collapsed to ~0.47–0.55 (random) for every dimension. The
fix is **joint cross-dataset training** (`xbse.instances.joint.JointPairSource`): train each feeder
on ≥2 corpora at once, drawing same-sign positives *across* corpora so the encoder cannot separate
pairs by any single corpus's surface. Held-out AUROC is then measured cross-corpus by construction.

| dimension | joint feeder (2 corpora) | within (old, inflated) | **cross-dataset (honest)** | baseline |
|---|---|---|---|---|
| `privacy_protection` | dual-judge privacy RoTs + AITA scenarios | 0.865 | **0.853** | 0.551 |
| `epistemic_quality` | Social-Chem honesty + ETHICS honesty | 0.90 | **0.817** | 0.483 |
| `virtue_care` | Social-Chem care-harm + ETHICS | 0.85 | **0.811** | 0.469 |
| `fairness_equity` | Social-Chem fairness-cheating + ETHICS | 0.87 | **0.789** | 0.474 |
| `autonomy_respect` | ec-darkpattern + MentalManip | 0.955 | **0.747** | 0.515 |
| `legitimacy_trust` | Social-Chem authority + ETHICS | 0.80 | **0.708** | 0.523 |
| `physical_harm` | BeaverTails + ETHICS harm-scenarios | 0.88 | **0.622** | 0.499 |
| `rights_respect` | *(pending — CourtListener NOS 440s)* | 0.75 | — | — |
| `societal_environmental` | *(pending — EcoVerse/ClimateBERT/NEPA-EIS)* | 0.77 | — | — |

**Seven of nine dimensions now have an honest cross-dataset feeder (0.62–0.85).** The within-dataset
numbers were NOT trustworthy — privacy's within/cross happened to agree, but e.g. `autonomy_respect`
read 0.955 within yet 0.518 cross (pure artifact) before joint training recovered it to 0.747.
Lessons banked: (i) **within-dataset AUROC is not evidence of a real dimension** — always cross-test;
(ii) the load-bearing fix is **cross-corpus same-sign positives**, not the gradient-reversal domain
adversary (which only de-confounds when the two corpora are already surface-similar); (iii)
`physical_harm` (0.622) is weakest — BeaverTails QA-pairs vs ETHICS scenarios is the widest genre
gap; the CourtListener criminal-case route (injury-tier labels) is its planned third corpus. Full
data roadmap: `xbse/experiments/data_sourcing_plan.md`.

Cross-cutting (not a dimension): **MoralStoriesBSE** (`mostories`) supplies surface-matched,
judgment-flipped hard negatives usable to sharpen *any* dimension's encoder.

**Retired / off-target:** `mobse_sanctity` (Social-Chem `sanctity-degradation`) maps to **no**
MoralVector axis — purity/sanctity is an MFT foundation absent from the DEME-9; not a feeder.
`mobse_loyalty` fed the compiler-10's `vow_fidelity`, which the DEME migration splits 50/50 into
`legitimacy_trust` + `virtue_care` (§3).

## 3. How it maps to the tensor (DEME 3.0)

The MoralVector is the **`k` axis** (length 9) of the rank-1..6 `MoralTensor`. Higher ranks add
context (`DEFAULT_AXIS_NAMES`):

| rank | axes | adds |
|---|---|---|
| 1 | `(k,)` | the global vector |
| 2 | `(k, n)` | per-**party** (stakeholder) |
| 3 | `(k, n, τ)` | over **time** |
| 4 | `(k, n, a, c)` | **action × coalition** |
| 5 | `(k, n, τ, a, c)` | coalition decisions **over time** (canonical, reconciled 2026-07-09) |
| 6 | `(k, n, τ, a, c, s)` | + Monte-Carlo **uncertainty samples** |

The **compiler-10 legacy schema** migrates to the DEME-9 `k` via
`erisml_compiler.ir.v3.migration` (tested): renames `autonomy_consent→autonomy_respect`,
`care_protection→virtue_care`; `third_party_externality→societal_environmental`; splits
`vow_fidelity→legitimacy_trust+virtue_care`; carries `repair_residue` in tensor metadata (a
post-collapse *residue operation*, not a `k`-dim); synthesises `privacy_protection` (no V2 source).
Ethics Modules **contract** the `k` axis from stakeholder perspectives; the governance policy DAG
composes them (see architecture doc).

## 4. Empirical support

**(a) Per-dimension encoders (xBSE campaign).** Per-foundation sub-BSEs beat a single broad MoBSE
on held-out structure-vs-surface AUROC — validated on a deterministic split (a `hash()`-seed
splitting bug that had inflated earlier numbers was fixed, commit `xbse:414e2d2`). Longer training
(@2500 vs @350 steps) helps neither fairness nor sanctity (CIs overlap) — the lever is better
negatives (Moral Stories) and more data, not more steps. Confidence is usable for the specialists
but *flat/anti-informative for broad* — the strongest evidence that a single moral encoder is too
broad. Full detail: `xbse/experiments/risk_coverage_report.md`.

**(b) Label ceiling (`C_moral`).** On the clean population, the moral sign-labels are ~as
reproducible as legal citations (`C ≈ 0.997–0.999`; mean reliability 0.86) — so encoder gaps are
*real*, not a label-noise artifact. The contested band (`action-agree≈2`) drops to `C ≈ 0.91`.

**(c) Dimensionality — the bifactor result.** An empirical rank test
(`xbse/experiments/rank_test.py`) over a 383-scenario **axis-isolated** matrix (each source
isolates one dimension; dual-judge signed valence, sign-agreement 0.56) shows:
- a dominant **general "moral-loading / severity" factor** (eig₁ ≈ 66% of variance), then
- after removing it, **~5 independent specific factors** (participation ratio 7.44, Horn parallel-
  analysis retains 5) with **zero true pairwise redundancy**.

⇒ **the moral-scenario space is bifactor: one general severity factor + ~5 specifics ⇒ a minimal
basis ≈ 6**, which the 3×3 core (general factor + two 3-level factors) is built to span. This is
convergent with Moral Foundations Theory (5–6) and Curry's Morality-as-Cooperation (7). The
general factor maps to the EU AI Act **risk tier**; the specifics to the substantive axes. (Soft:
judge agreement moderate; `autonomy_respect` and — as compiler-10 concepts — externality/repair
lacked isolating data. The *structure* is robust across three independent runs.)

**(d) Standards coverage.** The DEME-9 covers every *substantive* EU/NIST/IEEE dimension, including
`privacy_protection` and `societal_environmental` (the two gaps the compiler-10 had). Procedural
requirements (transparency, oversight, accountability) are governance-DAG attestations, not
`k`-dims. Verified crosswalk in `moralvector_v2_architecture.md` §8.

## 5. Reproduce

- Dimensions + migration: `erisml-compiler/ir/v3/{dimensions,migration}.py`, tests `test_v3_schema.py`, `test_dimension_consistency.py`.
- Encoders: `xbse/src/xbse/instances/`; checkpoints `atlas:/home/claude/xbse_ckpt/`.
- Rank test: `xbse/experiments/rank_test.py`; matrices `atlas:/home/claude/rank_pool_matrix.npy`, `valence_matrix.npy`; scorer `erisml-compiler/experiments/calibration/signed_rubric.py`.
- Standards: `moralvector_v2_architecture.md` (cited EU/NIST/IEEE review).

## 6. Open items

1. Train the missing/planned feeders: PhysHarm (PKU-SafeRLHF), Epistemic (honesty RoTs), SocEnv
   (SBIC); source data for `autonomy_respect` and `privacy_protection` (dual-judge labeling).
2. Sharpen the empirical "~5" with a third judge + isolating data for the two gap axes, then re-run
   `rank_test` and confirm the residual factor count.
3. Retire `mobse_sanctity` from the MoralVector feeder set (keep as an MFT-research artifact only).
