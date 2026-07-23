# LBI-2: Like Cases Alike, Measured — Auditing the Human Baseline

**Follow-up to:** *The Legal Bond Index: A Geometric, Case-Level Test of Algorithmic Fairness
Applied to COMPAS* (J. Sci. L., under revision).
**Target venue:** Journal of Science and Law (Center for Science and Law).
**Tuned to:** the Center's program — quantitative, forward-looking auditing of the legal system
itself from large court-record data; decision-noise over blame intuitions; common metrics that let
algorithms and humans be compared rather than argued about.
**Status:** outline v0.1, 2026-07-23. Nothing computed; all predictions to be sealed before any
estimator touches outcome data (house rule; also the paper's own methodology).

---

## Working titles (descending preference)

1. *Like Cases Alike, Measured: A Case-Level Audit of the Human Baseline in Federal
   Civil-Rights Litigation*
2. *The Legal Bond Index of the Judiciary: Treating Like Cases Alike as a Measurable Quantity*
3. *Auditing the Auditors' Baseline: Case-Level Consistency in the System That Would Judge the
   Algorithms*

## The one-paragraph pitch

The COMPAS decade audited the algorithm and left its comparator unexamined: every fairness metric
was computed against the implicit standard of human legal judgment, which no one measured with the
same instrument. LBI-1 established a case-level, matched-pair statistic — do decision subjects who
agree on legitimate features receive similar decisions regardless of features that should not
matter? — and found LBI(COMPAS, race) = 1.050 [1.040, 1.058], rising to 1.090 at the binary
decision unit. This paper applies the *identical estimator* to the human baseline: federal
civil-rights adjudications (42 U.S.C. §1983 and related, NOS 440-series), matched on legitimate
case features, tested for outcome sensitivity to features that should not matter — and puts
LBI(judiciary) and LBI(COMPAS) **on the same axis for the first time**. Whichever is larger, the
result reframes the algorithmic-fairness debate as an empirical comparison rather than a
presumption.

## Abstract skeleton

- The impossibility results constrain population-level metrics; LBI is a case-level diagnostic
  they do not constrain (one sentence, citing LBI-1).
- Nobody has applied a like-cases-alike audit to the judicial baseline with the same estimator
  used on algorithms. We do, on N ≈ 44k adjudicated federal civil-rights cases (FJC IDB
  judgment labels joined to CourtListener/RECAP dockets).
- Headline number(s): LBI(judiciary; district | judge | representation-status | filing-era) with
  CIs and permutation p-values, stratified to respect legally sanctioned variation (circuit law).
- The comparison sentence: LBI(COMPAS, race) = 1.050 vs LBI(judiciary, ·) = [measured].
- Register: diagnostic, not proof of unfairness; matching is on selected, incomplete features
  (LBI-1's own discipline, carried over verbatim).

## 1. Introduction

- Open with the asymmetry: a decade of algorithmic audits, zero equivalent audits of the human
  baseline *with the same instrument*. The debate's implicit null — "human judgment is the
  standard" — is an unmeasured standard.
- Forward-looking frame (venue-tuned): the question that matters for policy is not "is the
  algorithm biased?" but "is the algorithm more or less consistent than the process it augments
  or replaces?" — a question that requires a common yardstick. LBI is that yardstick.
- Decision-noise literature hook: system noise in sentencing/asylum/bail is documented via
  between-judge variance; LBI sharpens noise audits by controlling legitimate case features
  geometrically (Mahalanobis matched neighborhoods) instead of coarse binning, and by returning a
  single number with a CI per illegitimate feature.
- Explicit continuity: same estimator, same three-way feature taxonomy
  (legitimate / contested / illegitimate), same robustness discipline as LBI-1.

## 2. The estimand, adapted from algorithm to institution

- LBI-1 recap in three equations (matched neighborhoods on legitimate features; cross-group vs
  same-group score gaps; ratio statistic; permutation null).
- What changes when the "algorithm" is a court:
  - **Decision variable:** adjudicated outcome (plaintiff/defendant judgment; binary), with
    disposition granularity as a secondary unit. LBI-1 showed the decision-relevant unit gives
    the sharper number (1.050 → 1.090); here the decision unit is the *only* unit — a feature,
    not a bug, and worth one paragraph.
  - **Legitimate features (matching set):** nature-of-suit code (440/441/443/446/448),
    procedural posture at termination, claim count, party configuration (individual vs entity
    defendant), filing year band, pro-se-at-filing? — NO: representation is *contested*, see §3.
  - **Illegitimate/test features:** judicial district (within circuit), individual judge (within
    district), representation status (contested — both directions argued), county demographic
    composition of the district, filing-era cohort.
  - **The circuit-split nuance (load-bearing, venue-relevant):** inter-circuit disparity is
    *legally sanctioned* — circuit law legitimately differs until the Supreme Court resolves a
    split. LBI computed naively across circuits would book lawful doctrinal variation as
    inconsistency. All headline estimands are therefore **within-circuit** (and era-banded, since
    controlling law moves: e.g., qualified-immunity doctrine shifts). Cross-circuit LBI is
    reported separately and labeled as measuring *legal geography*, not judicial inconsistency.
    This distinction — which disparities the system itself declares legitimate — is exactly the
    three-way taxonomy from LBI-1 promoted from features to strata.

## 3. The feature taxonomy for cases (the section a hostile reviewer reads first)

- Legitimate: what the law says may determine outcomes (claim type, posture, timeliness,
  prior-litigation flags).
- Illegitimate: what the law says may not (assignment lottery — the draw of judge within a
  district is *randomized by design*, making judge-level LBI the cleanest causal cell in the
  entire paper; district demographics).
- Contested: representation status (predicts outcomes; normatively double-edged — case quality
  vs access-to-justice), government-defendant status, era. Handled as in LBI-1: computed under
  every assignment, reported as a robustness table, with the drop-the-contested-feature rows
  presented first.
- **The random-assignment gift:** within a district, judge draw is (nominally) random — so
  matched-pair outcome sensitivity to judge identity has a *design-based* interpretation no
  COMPAS analysis could claim. One subsection; this is the paper's methodological high ground.

## 4. Data and labels (infrastructure already built)

- CourtListener/RECAP bulk + FJC Integrated Database join; ~63 GB local. NOS coding with the
  banked corrections (440s exclude prisoner petitions 550/555/560; 444 retired; employment
  discrimination = 442/445, distinct from wage/labor 710/720/740).
- **Tier-1 labels (scale):** FJC `judgment` field (1 = plaintiff, 2 = defendant) on adjudicated
  civil cases — ~44k civil-rights adjudications. Tier-2 (validated subsample): dual-judge reading
  of opinion text for *holdings* (was the right violated), keep concordant, human-review
  disagreements — the same hybrid labeling discipline registered in the xbse data plan.
- **Label traps, encoded not footnoted:** procedural/standing dismissals = no-valence (excluded
  from outcome, retained in a sensitivity row); the rule-direction trap (vacating a protective
  rule ≠ vacating a rollback); government role is not sign-fixed.
- **What we deliberately do NOT use:** learned case-text embeddings for matching. Pre-registered
  test (xbse R6, 2026-07-23): whether rights-violation structure in case facts is machine-readable
  by cross-corpus contrastive valence — **failed both ways** (aggregate ECHR↔US 0.509 vs untrained
  0.512; physical-integrity stratum 0.467, below baseline). Matching is therefore tabular and
  every matching feature is legible and contestable by a legal reader. One honest paragraph; it
  buys more credibility than an embedding ever would, and it is the kind of negative result this
  venue's program exists to reward.

## 5. Registered analysis plan (sealed before outcome data is touched)

- P1 (judge cell, the design-based one): within district-eras with ≥ m adjudicated matched cases,
  LBI(judge) > 1 with CI excluding 1. Direction predicted; magnitude NOT predicted (we decline to
  guess; the point is to measure).
- P2 (district within circuit): LBI(district) > 1; predicted to exceed LBI(judge) (composition +
  local practice on top of noise).
- P3 (the comparison): report LBI(judiciary, each stratum) alongside LBI(COMPAS, race) = 1.050 /
  1.090 with explicit unit-matching discussion; no prediction registered on which is larger —
  that is the finding either way, and saying so in the prereg is the paper's honesty thesis in
  one line.
- P4 (falsifier): if permutation nulls absorb the observed statistics in the judge cell (the
  randomized one), the paper reports the judiciary as *passing* its like-cases-alike audit at the
  resolution available — publishable and stated in advance.
- Estimator settings carried from LBI-1: Mahalanobis matching, k grid {5, 10, 20, 50}, permutation
  inference with subsample-size caveat handled (LBI-1 review item b), k-NN assumption disclosure
  (matching set, metric, scaling, k — the LBI-1 review's own language, landed here from day one).

## 6. Results (structure only)

- 6.1 Headline table: LBI by stratum × feature, CI, permutation p, n-pairs.
- 6.2 The common-yardstick figure: one axis, LBI(COMPAS) and LBI(judiciary) strata as points with
  CIs. (The figure Eagleman's audience will screenshot.)
- 6.3 Robustness: feature-set grid incl. drop-contested rows; era bands; no-valence sensitivity;
  tier-1 vs tier-2 label concordance.
- 6.4 Negative-space reporting: strata with insufficient matched pairs are listed, not silently
  dropped.

## 7. Discussion

- What a case-level inconsistency number can and cannot say (diagnostic register, verbatim
  discipline from LBI-1).
- Policy reading, forward-looking: a jurisdiction considering an algorithmic aid should demand
  LBI(algorithm) ≤ LBI(current process) on the same features — a concrete, computable adoption
  criterion, offered as orientation not proposal (LBI-1 review item d's phrasing discipline).
- Noise-audit positioning: LBI as the geometric refinement of between-judge variance studies.
- Limitations: adjudicated-case selection (settlement filter), FJC label coarseness, incomplete
  feature sets — each with its direction-of-bias stated.

## 8. Assets and gaps

| Asset | Status |
|---|---|
| LBI estimator + permutation code (Zenodo-archived from LBI-1) | ✅ reusable as-is |
| CourtListener 63 GB + NOS schema + corrections | ✅ on Atlas |
| FJC IDB join recipe + judgment labels | ✅ registered in data plan; join not yet run |
| Label-trap rules (no-valence, rule-direction, gov-role) | ✅ banked |
| Dual-judge tier-2 labeling harness | ✅ exists (xbse); needs a rights-holdings prompt pass |
| Judge-identity extraction (docket → judge, within-district eras) | ⚪ to build |
| District demographic covariates (census join) | ⚪ to build |
| Sealed prereg document | ⚪ next concrete step |

**Next concrete step:** draft and seal the prereg (feature taxonomy, strata, k grid, P1–P4) before
any outcome column is loaded; then run the FJC join and report matched-pair counts per stratum —
the go/no-go for the judge cell.

## Venue strategy note

Lead with the audit-symmetry thesis and the common-yardstick figure; keep the neurolaw/noise
framing to the introduction and discussion (their vocabulary, our estimator). The paper's tuned
quality is the *question* — is the human baseline more consistent than the algorithm we audited? —
not the answer, which stays wherever the data puts it. The sealed prereg travels with the
submission as supplementary material; for this journal it is not bureaucracy, it is the exhibit.
