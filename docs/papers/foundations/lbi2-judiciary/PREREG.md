# Pre-registration — LBI-2: Like Cases Alike, Measured (Auditing the Human Baseline)

**Author:** Andrew H. Bond (SJSU, ORCID 0009-0003-2599-6158)
**Registered:** 2026-07-23
**Seal:** the git commit introducing this file to `ahb-sjsu/erisml-lib` `main` is the seal; any
later edit to this file must be additive, dated, and confined to the DEVIATIONS section.
**Companion:** OUTLINE.md (same directory). Estimator: LBI-1 (J. Sci. L., under revision),
reference implementation doi:10.5281/zenodo.21310251, reused unmodified.

## 0. Attestation of ignorance (what is and is not known at seal time)

At seal time: the CourtListener/RECAP bulk data and FJC IDB reside on the training host but **the
FJC judgment column has not been joined to dockets**, and no matched-pair, judge-level,
district-level, or representation-level statistic of any kind has been computed by us on this
population. Publicly known and hereby disclosed as known: approximate adjudicated-case counts
(~44k civil-rights; from the FJC codebook) and the general fact that plaintiff win rates in
federal civil-rights litigation are low. Nothing else. The xbse R6 result (case-text embedding
matching fails its gate; 2026-07-23) is known and is why matching is tabular (§4).

## 1. Estimand

The Legal Bond Index at neighbourhood scale $k$, exactly as Definition 1 of LBI-1:

LBI_k(f, g) = E_i[ mean_{j ∈ N_k(i, g_j ≠ g_i)} |f(i) − f(j)| ] / E_i[ mean_{j ∈ N_k(i, g_j = g_i)} |f(i) − f(j)| ]

with two adaptations, both registered here:

- **f is the adjudicated outcome**, binary: f(i) = 1 if FJC `judgment` = 1 (plaintiff), 0 if
  `judgment` = 2 (defendant). For binary f, mean |f(i) − f(j)| is the disagreement probability,
  so LBI_k is the ratio of cross-cell to within-cell disagreement among matched cases — the
  decision-relevant unit of LBI-1 §4.5, which is here the only unit.
- **g is a test feature that may be multi-class** (judge identity, district). The same/different
  conditions g_j ≠ g_i / g_j = g_i in N_k generalize Definition 1 without modification; this is
  the "same/different" reading of LBI-1's multi-class note (§8).

LBI-2 is a **diagnostic of case-level consistency**, not a proof of unlawful disparity; the
diagnostic register of LBI-1 carries over verbatim.

## 2. Population and exclusions (frozen)

- Source: CourtListener/RECAP federal district-court dockets joined to the FJC Integrated
  Database; local snapshot on the training host (63 GB, as inventoried in the xbse data plan).
- Include: civil dockets with nature-of-suit in **{440, 441, 443, 446, 448}** (civil-rights
  family per the banked NOS corrections), filed **2000-01-01 through 2024-12-31**, with an FJC
  `judgment` ∈ {1, 2} (adjudicated; settlement and transfer dispositions excluded from the
  primary estimand).
- Exclude: prisoner-petition NOS (550, 555, 560); cases with missing district, filing date, or
  posture; multi-district-litigation consolidated members (their assignment is not random).
- **No-valence rule:** terminations coded as jurisdictional/standing/procedural dismissal are
  excluded from the primary analysis and re-included as defendant outcomes in sensitivity S3
  only.

## 3. Feature taxonomy (frozen)

**Blocking features (exact match required; define the like-case stratum):** nature-of-suit code ·
procedural posture at termination (motion / bench / jury verdict categories) · circuit ·
filing-era band (2-year) · for the judge cell additionally: district.

**Matching features (Mahalanobis within block; Σ = empirical covariance within block-feature
space):** number of defendants (banded 1 / 2–4 / 5+) · defendant type (individual / municipal
entity / state or federal officer) · claim count (banded) · case-duration-to-termination is
**excluded** (post-treatment).

**Test features g:**
- T1 (primary, design-based): **judge identity**, within district × era blocks. Within-district
  assignment is nominally random, giving T1 a design-based interpretation.
- T2: **district**, within circuit × era blocks.
- T3 (contested feature, secondary): **representation status** (counseled vs pro se at filing).
- T4 (secondary): **district county-demographic composition** (census Black-population-share
  quartile of the district), within circuit × era.
- Cross-circuit LBI is computed but registered as *legal geography*, not judicial inconsistency
  (circuit law legitimately differs); it is barred from the headline.

**Contested-feature policy (carried from LBI-1):** representation status is analyzed both as a
test feature (T3) and as an additional blocking feature in sensitivity S2; both are reported.

## 4. Why tabular matching (registered constraint)

Matching uses only legible docket/FJC fields above. Learned case-text embeddings are **not** used
for matching: the pre-registered xbse R6 experiment (2026-07-23) tested whether rights-violation
structure in case facts is machine-readable by cross-corpus contrastive valence and failed both
ways (aggregate 0.509 vs untrained 0.512; physical-integrity stratum 0.467 < baseline). This
constraint is registered so it cannot be quietly relaxed if tabular results disappoint.

## 5. Estimator settings (frozen)

- k grid **{5, 10, 20, 50}**; headline **k = 20** (carried from LBI-1).
- CIs: percentile bootstrap, **1,000** resamples, resampling cases within blocks.
- Permutation null: **1,000** permutations of g within its block (judge shuffled within
  district-era; district within circuit-era; etc.), statistic computed on the **full analysis
  sample** each permutation (repairing LBI-1's subsample/observed mismatch, per its review item
  b); two-tailed p.
- Minimum neighbourhood validity: a case enters the estimate only if it has ≥ k same-g and ≥ k
  different-g neighbours within its block; counts of excluded cases are reported per stratum
  (no silent drops).
- Seed: 20260723 for all resampling.

## 6. Sample-size gates (go/no-go, decided before any outcome is read)

- **Judge cell (T1) proceeds** iff ≥ 20 district-era blocks each contain ≥ 2 judges with ≥ 25
  adjudicated in-scope cases. Otherwise T1 is reported as underpowered-by-gate, not estimated.
- **T2/T3/T4 proceed** iff the analysis sample after exclusions is ≥ 5,000 cases and each
  reported stratum has ≥ 200 eligible cases.
- The join and these counts are computed and committed BEFORE the outcome column is merged into
  the analysis frame (two-stage load; the counts commit is the go/no-go record).

## 7. Label validation (tier-2)

On a stratified random subsample of **500** adjudicated cases: dual-judge LLM reading of the
terminating opinion/order for outcome direction; agreement with the FJC judgment label reported
as raw concordance + Cohen's κ; disagreements human-reviewed. **Gate:** if concordance < 0.90,
the FJC-labeled primary analysis is reported with the concordance number attached to every
headline value, and tier-2-labeled LBI on the subsample is promoted to co-headline.

## 8. Registered predictions and decision rules

- **P1 (T1, judge):** LBI_20(judge) > 1 with 95% CI excluding 1 and permutation p < 0.05.
  Direction registered; magnitude deliberately not.
- **P2 (T2, district):** LBI_20(district) > 1, and point estimate ≥ that of P1 (composition +
  local practice atop assignment noise).
- **P3 (comparison):** LBI(judiciary strata) and LBI-1's LBI(COMPAS, race) = 1.050 [1.040,
  1.058] / 1.090 (binary unit) are plotted on one axis with an explicit unit-matching caveat
  (both are binary-unit disagreement ratios; populations differ). **No prediction is registered
  on which is larger.** Whichever way it lands is the finding.
- **P4 (falsifier, publishable):** if the T1 permutation null absorbs the observed statistic
  (p ≥ 0.05), the paper reports the judiciary as passing its like-cases-alike audit at the
  resolution available, headline unchanged in register.
- Interpretation bands from LBI-1 §7.2 (1.00–1.02 / 1.02–1.10 / >1.10) are used as descriptive
  anchors, explicitly "for orientation, not proposal."

## 9. Sensitivities (all registered; anything else is labeled exploratory)

- S1: drop each matching feature in turn; drop banding (raw counts).
- S2: representation status moved from test feature to blocking feature.
- S3: no-valence terminations re-included as defendant outcomes.
- S4: era-band width 4 years; filing-date range restricted to 2010–2024.
- S5: k ∈ {5, 10, 50} full table (headline stays k = 20 regardless of which k flatters).

## 10. Deviations

*(empty at seal; any post-seal change is logged here with date, reason, and whether it was made
before or after outcome data was read)*
