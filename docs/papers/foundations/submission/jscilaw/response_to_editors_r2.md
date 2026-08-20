# Response to Editorial Review (Round 2) — *The Legal Bond Index* (JSciLaw)

We thank the editors for a demanding and, as it turned out, prescient review. We implemented
every requested analysis rather than arguing around any of them, and two of the review's
methodological concerns were **confirmed by the new analyses**: cross-race neighbourhoods are
measurably worse-matched than same-race ones, and the plain permutation test does not test the
stated null (on semi-synthetic race-blind data it false-fires 56% of the time at the nominal 5%
level). The revision therefore does more than qualify claims — it rebuilds the inferential
machinery, validates it under known ground truth, and reports a corrected, two-sided result:
the race-associated signal survives the strictest calibrated test we could construct (conditional
randomization z = 5.0, global multiscale p = 0.001), while the unadjusted point estimate of 1.05
is shown to overstate the adjusted magnitude (matching-parity specifications land at 1.00–1.02).
One previously reported effect (sex) does not survive the corrected inference and has been
withdrawn. We believe the paper is substantially stronger for it.

The analysis pipeline was rebuilt end-to-end (`revision2_analysis.py`, replacing the earlier
scripts; deterministic stable-sort tie-breaking, full-sample nulls, neighbourhood-recomputing
bootstrap). All numbers in the manuscript are re-derived from this pipeline; a few point
estimates shift by at most 0.01 relative to the prior version (most visibly at k = 1, where 79% of
defendants have distance ties at the neighbourhood boundary), and the new, wider CIs reflect the
corrected bootstrap. The rebuild also surfaced an error we should disclose: the prior version's
Table 1 (standard fairness metrics) mixed values from differently filtered drafting runs and was
not reproducible from the stated subset. It has been recomputed from the same script and subset
as everything else; the derived disparities are essentially unchanged (FPR disparity +0.203 and
predictive-parity gap +0.055 exactly as before; FNR disparity −0.212 to −0.211; base-rate gap
+0.129 to +0.132), but several cells shift visibly (e.g., Black FPR 0.443 to 0.423). Complete
outputs are in `outputs/revision2_results.json` / `revision2_report.txt`.

---

## 1. Are cross-race and same-race neighbourhoods equally well matched?

They are not, and the manuscript now measures this directly in a dedicated subsection
(**§4.5 "Are cross-race neighbours worse-matched?"**), with every diagnostic the review requested:

- **Distance distributions across all k** (Table 3, Figure 2): mean Mahalanobis distance to
  cross-race neighbours exceeds same-race at every scale — ratio 1.52 at k=1 declining to 1.17 at
  k=100 (1.28 at k=20). Per-feature balance diagnostics show the same (worst on prior counts,
  0.187 vs 0.141 mean |z-diff|).
- **Common-support diagnostics**: 99.8% of defendants lie in the propensity common-support
  interval; restricting to it leaves LBI unchanged (1.048).
- **Caliper analyses**: excluding focal defendants whose nearest cross-race comparator is beyond
  the 90th (75th) percentile of nearest same-race distances attenuates LBI at k=20 from 1.049 to
  1.022 (1.012). Fixed-radius neighbourhoods give 1.022.
- **Distance-matched specification**: selecting same-race comparators at the same distances as
  the cross-race set gives 1.003 (the greedy matching overshoots — same-race comparators end up
  *farther* (0.662) than cross-race (0.458) — so we report this as an overcorrected lower bound).
- **Exact matching on the felony indicator** before continuous matching: 1.050 (unchanged; the
  indicator was already well matched). We additionally ran coarsened-exact matching on
  age/priors/juvenile/felony bins: 1.009 [1.000, 1.018] on the 3,159 defendants with sufficient
  within-stratum comparators.

The manuscript now draws the conclusion these numbers force (§4.5, §4.11): the unadjusted index
contains a mechanical component of roughly +0.01 to +0.015 attributable to poorer cross-race
match quality, and the honest adjusted range on the decile score is 1.01–1.02. This is a real
change to the paper's quantitative claims, made prominently rather than buried.

## 2. The permutation test

Every specific defect identified is fixed, and the deeper conceptual point is now a headline
methodological result:

- **Same sample size**: observed and null statistics are both computed on the full n = 5,278
  (the 500-defendant subsampling is gone; the text notes the correction explicitly, §4.6).
- **More permutations**: 1,000 draws per null construction (was 200).
- **Conditional tests**: we added both suggested constructions — permutation within
  propensity-score deciles, and a full conditional randomization test (CRT) redrawing labels from
  the estimated P(race | x) (§3.3, §4.6). The stricter nulls are centred at 1.012–1.015, *not* 1.000,
  confirming the review's intuition that plain permutation destroys the race–feature dependence
  and thereby tests the wrong null. Validated on race-blind synthetic data (see point 3), plain
  permutation false-fires 56% of the time; the CRT is calibrated (4%). The observed LBI still
  rejects against the correctly centred conditional null: z = 5.0, global p = 0.001, with the
  stratified permutation (a nonparametric check on the CRT's propensity model) agreeing (z = 5.5).
- **Bootstrap**: confidence intervals now come from a bootstrap that **re-forms all
  neighbourhoods inside every replicate** (1,000 replicates), addressing the dependence from
  neighbour reuse (mean 40, max 198 reuses per defendant). The CIs widen accordingly (k=20:
  [1.027, 1.072] vs the naive [1.039, 1.058]); both are shown so the effect of the correction is
  visible (§4.4).

## 3. Validation under known ground truth

Added as **§4.9** with exactly the four requested conditions, built semi-synthetically on the
real feature matrix and race labels (preserving the actual race–feature dependence): (1)
race-blind score with race-correlated features; (2) explicit race coefficient (β = 0.25/0.5/1.0
deciles); (3) strong proxy (corr 0.8 with race); (4) omitted legitimate predictor (score uses
priors count, matching cannot). Each condition: 60–200 Monte Carlo replicates, tested by plain
permutation, CRT, and an OLS race-coefficient baseline; a Dwork-style nearest-neighbour
consistency score is reported as the individual-fairness comparator. Findings (Table 8, Figure 5):

- race-blind level: LBI = 1.009 ± 0.006 (near, not at, 1 — the mechanical component);
- **false-positive rates at nominal 5%: plain permutation 56%, CRT 4%, OLS 6%**;
- monotone response to direct discrimination (1.009 rising to 1.071 as β runs from 0 to 1
  decile); strong response to proxy discrimination (1.153 at γ = 1);
- matching failure (condition 4) inflates the point estimate to 1.015 but the CRT remains
  calibrated (5%), because it conditions on the recorded covariates;
- the consistency comparator barely moves across conditions (it measures smoothness, not
  protected-attribute structure); OLS is more powerful against purely linear direct effects —
  stated plainly, LBI's niche is the model-free, black-box, categorical-output setting.

## 4. Title, overclaims, and risk categories

- **Title** changed as suggested: *"The Legal Bond Index: A Matched-Neighbourhood Diagnostic of
  Algorithmic Disparity, Applied to COMPAS."*
- Every flagged formulation is rewritten: §2.3 no longer says LBI "measures case-level fairness
  directly"; the Definition's interpretation bullets no longer speak of a protected-attribute
  "flip" or of the algorithm being "responsive to the protected attribute"; the discussion no
  longer claims "case-level, not population-level" (now: "matched-neighbourhood, not marginal,"
  §5.1, with the aggregation point made explicitly). The defensible interpretation the review
  proposed — cross-group score divergence exceeding within-group divergence among neighbours
  selected on specified observed features — now appears verbatim in §2.3 and governs the
  abstract, definition, and conclusion.
- **"Inputs include protected attributes" corrected** (abstract and §6.1): the audit dataset must
  contain the protected attribute; the algorithm need not use it — with COMPAS as the example.
- **Risk categories** (§4.7): the three cutoffs are defined (1–4/5–7/8–10); the ≥5 analysis is
  renamed "medium-or-high (ProPublica's binary)"; a second binary at ≥8 is added (LBI 1.026
  [1.007, 1.045]); the text explains ProPublica's use of ≥5 and cautions that no threshold is
  universally decision-relevant; and the table reports the **raw numerator and denominator**
  (≥5: cross-race disagreement 37.3% vs same-race 34.2% — stated as a 9.2% relative, 3.1
  percentage-point excess, with the relative-vs-absolute distinction spelled out in §4.7 and
  §5.4).

## 5. Robustness across matching methods

Added (§4.8, Table 7): Euclidean on standardized features (1.048), robust Mahalanobis/MinCovDet
(1.048), log(1+x) on count features (1.048), rank transform (1.044), Gower (1.049), plus
coarsened-exact matching and fixed-distance calipers (reported with the matching-parity family in
§4.5, since they change match quality, not just the metric). The text now distinguishes
robustness to the metric family (high) from robustness to match quality (the specifications that
move the estimate) — the review's distinction, which we adopted.

## 6. Mahalanobis wording

Corrected (§3.2): Mahalanobis distance is Euclidean on the whitened representation; high-variance
leading principal directions are **downweighted** to the common scale (the previous "upweight"
sentence was wrong and is gone).

## 7a. Legal and regulatory claims

- Demographic parity is no longer equated with disparate impact; the two-step doctrinal inquiry
  is stated with citation to Barocas & Selbst (2016) (§2.2).
- The four-fifths rule is identified as an employment-selection enforcement heuristic with no
  doctrinal standing in criminal justice; its single remaining appearance (summary table) is
  marked "illustrative only" (§2.2, Table 9, §6.3).
- A new **§6.3 "Doctrinal context"** discusses *Washington v. Davis* and *McCleskey v. Kemp*
  (equal protection / discriminatory-purpose requirement), *State v. Loomis* in more depth (due
  process, proprietary methodology, required warnings, cert. denied), contestability
  (Citron 2008), and the risk-assessment race-neutrality debate (Starr 2014; Mayson 2019;
  Huq 2019). The "legally irrelevant depending on jurisdiction" sentence is replaced by the
  attribute-specific treatment (race foreclosed; sex upheld in *Loomis*).
- **The proposed LBI ranges are removed entirely.** §6.2 now states why (no empirical or legal
  basis exists), notes what the synthetic validation can and cannot ground, and frames elevated
  LBI as a trigger for disaggregated follow-up rather than a value to compare against a cutoff.

## 7b. The sex result and the choice of k

The review was right, and the corrected inference is stronger than the requested fix:

- **The sex claim is withdrawn** (§4.4). With the corrected bootstrap, LBI(sex) CIs include 1 for
  all k ≤ 20 (k=1 point estimate 0.962); the global multiscale randomization tests do not reject
  (plain p = 0.39; CRT p = 0.90). The manuscript says explicitly that the earlier version's
  "real but smaller" characterization is not supported and is withdrawn; Figure 1's caption is
  corrected. We also note (per §6.3) that LBI(sex) would not carry the same normative
  significance in any case.
- **k is defined at first use** (§3.1) with an explicit explanation of what the neighbourhood
  scale means.
- **The full k-curve is now the primary result** (§4.4: "The race curve, not any single point on
  it, is the primary finding"); k = 20 is explicitly an illustrative scale for detailed
  diagnostics. Significance is carried by a **global multiscale max-z randomization test across
  all six prespecified scales** (§3.3, §4.6), not by any single k; pointwise per-k tests are also
  reported. This implements the review's "stronger correction."

## 8. Other items

- **CIs labelled pointwise** wherever a k-range appears (§3.3, Table 2, Figure 1), with the
  multiple-comparisons burden carried by the global max-z test.
- **Ties, reused neighbours, missing values, covariance inversion, tie-breaking, few-comparator
  cases**: a dedicated implementation subsection (§4.10) reports all of these quantitatively
  (3,673/5,278 duplicated feature vectors; 79% boundary-tie rate at k=20; deterministic
  stable-sort tie-breaking; reuse mean 40/max 198 — motivating the corrected bootstrap; zero
  missing values; condition number 2.65 with 1e-6 ridge; n retained under restricted
  specifications).
- **Focal-group results** (§4.4): Black-focal 1.027 [1.015, 1.039], White-focal 1.087
  [1.071, 1.102], group-balanced 1.055 — the asymmetry is now itself a reported finding.
- **Distribution of per-defendant gaps** (§4.5, Figure 3): 53.9% positive, mean +0.108 deciles;
  excluding the top 5% lowers LBI from 1.049 to 1.009 — the tail-concentration is stated plainly.
- **Recidivism defined precisely** (§4.1): ProPublica's `two_year_recid` — a new offence
  resulting in a jail booking within two years of screening; arrest-based, not conviction-based.
- **Score specified** (§4.1): the general-recidivism decile (`decile_score`), not the violent
  scale.
- **Wilson-loop / Judicial Complex material**: removed from the body (former §4 deleted); a
  brief author note at the end records the provenance. No claims in the paper depend on it.
- **Bond (2026a)/(2026b)** labels fixed in the reference list.

---

**Reproducibility.** `revision2_analysis.py` (single script, seed 20260724) reproduces every
number, table, and figure from the public ProPublica file; outputs are bundled
(`outputs/revision2_results.json`, `outputs/revision2_report.txt`). The Zenodo record will be
versioned with the revised manuscript.
