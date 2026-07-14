# Response to Reviewer — *The Legal Bond Index* (JSciLaw)

We thank the reviewer for a careful and constructive report. We have accepted essentially every
point. The revision does two things: (i) it **narrows the interpretive claims** throughout — LBI is
now consistently framed as a *conditional matched-comparison diagnostic / screening signal*, not a
proof of case-level (un)fairness; and (ii) it adds a **new empirical robustness analysis**
(§Robustness, `ablation_lbi.py`) that directly tests the reviewer's central worry — that the signal
is an artefact of the feature choice — and, we believe, strengthens the paper's evidentiary basis
rather than merely qualifying it.

**New result (headline of the revision).** Recomputing LBI(race) at k=20 across four
legitimate-feature sets and three score representations:

| feature set (decile) | LBI | 95% CI | | score unit (6 features) | LBI | 95% CI |
|---|---|---|---|---|---|---|
| minimal (age, priors) | 1.041 | [1.032,1.049] | | raw decile | 1.050 | [1.040,1.058] |
| paper (6) | 1.050 | [1.040,1.059] | | 3-category (low/med/high) | 1.066 | [1.053,1.078] |
| **drop juvenile counts** | 1.038 | [1.030,1.047] | | **binary high-risk (≥5)** | 1.090 | [1.076,1.106] |
| paper + sex control | 1.060 | [1.050,1.069] | | | | |

The signal survives every available-feature specification (all CIs exclude 1), **survives dropping the
contested juvenile proxies**, and is **larger at the decision-relevant unit** (category/binary) than
at the raw decile. Point-by-point below.

---

**1. "Legitimate features" need stronger justification; distinguish available / unavailable /
contested; explain the low multicollinearity.**
Accepted. (a) We now state explicitly that the choice of legitimate features is normative and that
*data availability cannot substitute for legal justification*, and we introduce the three-way
distinction the reviewer proposes — legitimate-and-available, legitimate-but-unavailable (the COMPAS
substance-use / education / employment items absent from the public file), and available-but-contested
(§Limitations, rewritten). (b) The new §Robustness shows the result does not hinge on the particular
6-feature set. (c) On multicollinearity: we now explain that the three juvenile counts are *mutually
exclusive* charge classes and `priors_count` is adult priors, so the features **partition** rather
than duplicate prior conduct — hence the low condition number (2.65) — and Mahalanobis de-correlates
any residual dependence (§Legitimate-feature space).

**2. Some "noncontroversial" factors are in fact contested (prior arrests, juvenile history).**
Accepted, and this was the most important framing fix. We removed the word "uncontroversial." The
§Limitations paragraph now states that prior/juvenile counts are *racially patterned proxies*
reflecting policing, surveillance, and charging practices, and that controlling on them can
*understate* unfairness by normalizing the disparity. Critically, the robustness table reports the
**drop-juvenile-counts** specification (LBI 1.038, CI excludes 1): the signal is not an artefact of
those contested controls.

**3. Describe more cautiously what LBI can and cannot prove; it is protected-attribute-focused, not
classic individual fairness.**
Accepted throughout. The intro now calls LBI a "diagnostic"; the "case-level fair by construction"
passage is rewritten to state that a matched-pair disparity is "a diagnostic signal requiring further
investigation, not by itself proof of legal unfairness"; the ratio subsection no longer claims to
"isolate the marginal contribution" (see #7); and §Robustness closes by re-framing LBI as a
conditional matched-comparison diagnostic. We also note it measures the *protected-attribute-focused*
slice of individual fairness (similar on selected predictors, differing on the protected attribute),
not the full Lipschitz notion.

**4. Clarify whether LBI detects direct discrimination, proxy discrimination, or unexplained
disparity.**
Accepted. We now state that a high LBI is a *screening signal* that does not self-interpret: it flags
that legitimately-matched defendants receive different outputs, but distinguishing direct use of race,
proxy encoding, or omitted-variable imbalance requires further, causal investigation (the
"Causal disentanglement" limitation is retained and cross-referenced from the reframed passages).

**5. Distinguish risk scores from risk classifications; correct the Northpointe characterization.**
Accepted. (a) We corrected the Northpointe characterization to **predictive parity** (equal precision
among those *classified* high-risk), *not* per-score calibration, in **all five places** it appears —
the abstract, introduction ¶1, §2.1, §2.2, and §4.3 — using consistent threshold-PPV phrasing
("among defendants it classifies high-risk"). The summary table row is relabelled from "Calibration
gap at high decile" to "Predictive-parity gap, P(recid | high)." (b) On scores vs
categories: the new §Robustness computes LBI on the 3-category (low/med/high) mapping and the binary
high-risk classification. Far from being practically insignificant, the disparity is **larger** at the
decision unit (1.066 category, 1.090 binary), which we take as evidence the finding is *more* legally
salient at the threshold, not less.

**6. Statistical descriptions.**
All accepted. (a) FPR is no longer described as the "mirror" of FNR; we now note they are distinct
rates on different denominators (FPR complements TNR, FNR complements TPR). (b) Demographic parity is
softened from "prohibits" to "generally in tension with" using correlated legitimate predictors, with
the note that the correlation can be offset by design. (c) Predictive parity and calibration are now
separated: calibration is written score-level as `Pr(Y=1 | S=s, A=a)` and predictive parity as the
threshold PPV condition, per Chouldechova (2017).

**7. The ratio's inferential significance may be overstated.**
Accepted. The ratio subsection now says it "quotients out sensitivity to the *selected* legitimate
predictors" and "does not by itself isolate the marginal causal contribution of the protected
attribute," which holds "only to the extent that the matching features are a sufficiently complete and
legally defensible account of relevant similarity." §Robustness provides the empirical counterpart.

**8. Qualify the Legal Invariance Principle.**
Accepted. The §Judicial-Complex bridge now adds two qualifications: (i) k-NN holds fixed only the
*selected* legitimate features, so the LIP as measured is conditional on the matching set (with
§Robustness testing sensitivity); (ii) "legally irrelevant" is attribute-specific — for sex and
citizenship, courts have upheld express differential treatment in risk tools, so a nonzero LBI on
those attributes is not automatically a defect, and we report LBI(sex) as a comparison, not a
violation. We also note k-NN is not assumption-free (matching set, metric, scaling, k), and interpret
k-stability cautiously.

**9. Contextualize the single-number preference.**
Accepted. The Discussion now states that scalar simplicity is a reporting convenience, not an
epistemic virtue, and that case-level fairness may vary by offence type, decision point, or assessment
window — so LBI is best read as a screening index to be disaggregated when it fires, not a substitute
for the fuller metric panel.

---

**Reproducibility.** The robustness analysis is `ablation_lbi.py` (public ProPublica file, same
Mahalanobis k-NN estimator as `lbi_compas_analysis.py`); output in
`outputs/ablation_lbi_results.txt`.

---

## Second-pass corrections (landing the letter fully in the manuscript)

A second read confirmed several fixes promised above needed to be carried into the *abstract and
introduction* specifically (the most-read paragraphs), and surfaced one technical error:

- **Northpointe / predictive parity** is now fixed in all five occurrences (abstract, intro ¶1, §2.1,
  §2.2, §4.3), including the abstract, which previously attached the right term to the score-level
  (calibration) definition.
- **Abstract narrowed:** "case-level *test*" → "case-level *diagnostic*"; "individually-similar" →
  "similar on selected legitimate predictors"; "The answer for COMPAS is *no*" → "a robust case-level
  *disparity*"; and a sentence on the robustness result (survives dropping juvenile controls;
  LBI = 1.090 at the binary threshold) now appears, with an explicit "diagnostic to be investigated,
  not a proof of legal unfairness" clause.
- **k-NN is not assumption-free (§3.2):** added that the assumptions are *shifted* to the matching
  set, metric, scaling, and k; and that persistent scale-invariance is equally consistent with a
  persistent omitted-variable imbalance as with a genuine case-level effect.
- **Corrected a limit statement (§5.3):** under perfect counterfactual fairness LBI → **1**, not 0
  (cross-group gaps approach same-group gaps); the previous "→ 0" was backwards.
- **Smaller items:** added a *State v. Loomis* (881 N.W.2d 749) citation for judicial engagement with
  the inputs (§4.2); noted the permutation null's 500-subsample dispersion makes the significance
  *conservative* (§4.5); explained the sex-control row (within-sex matching removes cross-sex dilution,
  1.050 → 1.060; §Robustness); and reframed the §7.2 threshold reference points as "descriptive
  anchors, for orientation, not proposal."
- **Open author decision:** the Wilson-loop paragraph and the two companion citations (one an
  economics monograph) may not earn their space with a legal readership; "developed in companion work
  (in preparation)" would suffice if the author prefers to trim.
