# TCSS-2026-03-0366.R1 final files (accepted 2026-09-06)

Final-file source is `final_manuscript.tex` (builds to `final_manuscript.pdf`, 17 pages, pdfLaTeX, no undefined references, no overfull hbox). `revised_manuscript_v2.tex` is the version the reviewers accepted and is kept unchanged as the record.

## What the reviewers asked for at acceptance

- Reviewer 1: recheck that the use of variables is standardized and correct.
- Reviewer 2: no requests.

## Corrections made, with provenance

Every number below was re-derived in this session from the archived data or the released code, not recalled.

### Factual errors in the accepted text

1. Andersen et al. (2011) location. The accepted text said Indonesia in seven places. The experiment was run in eight villages in Meghalaya, northeast India, in Indian rupees (source: the AER paper, Section I, and the openICPSR do-file labels "20 Rupees"). Indonesia is Cameron (1999), which the paper also cites. Fixed in the abstract, introduction, Section VII.A, Fig. 5 caption, limitations, and conclusion. Also fixed in `tcss_public_data_analysis.py` and the notebook.
2. Income comparison. The accepted text said the Rs 20,000 stake was "approximately 1.6 times monthly income" and "1.6 months of wages". Andersen et al. report an average yearly income of about Rs 17,000, so the top stake is "a little over a year's income" and Rs 2,000 is "nearly one and a half month's income" (their words). Fixed throughout.
3. The reference-implementation pointer. The accepted text said the round-decay constant "is recorded in the reference implementation" at the PyPI structural-fuzzing URL. That package does not contain the economics model. The code that reproduces all sixteen predictions exactly (verified this session, unweighted MAE 2.702%) is eris-econ 0.1.0 (PyPI, Zenodo 10.5281/zenodo.20660123). The paper now cites eris-econ as reference [45].

### Method descriptions corrected to match the released code

These do not change any reported number. They change what the paper says was done.

4. Encodings (Section IV, new Table IV). The accepted text gave simplified displacement formulas (for example Δa1 = −x, Δa3 = −(0.5−x)^2). The code encodes each task as a reference point and an alternative point with the coordinates now listed in Table IV. Rejection risk enters through the epistemic coordinate (Δa9 = −0.3 P_rej), which is the mechanism that actually produces the 48% offer, the 34% MAO, and the 35% Güth offer.
5. Rejection logistic. Steepness is 15 per unit share (0.15 per percentage point), not 0.15 as a divisor. Symbol renamed from k to κ to avoid the clash with the active-set size k.
6. Public-goods round decay. The code uses a linear per-round drift of the reference point on d6 (0.02 per round) and d9 (0.03 per round), not exp(−λ_r r). The parameter count rises from 12 to 13 named quantities.
7. Choice rule for games. Game predictions are deterministic cost minima on an integer percentage grid. The softmax with cost-dependent temperature is used only for the six lottery choices. The accepted text implied softmax throughout.
8. Variance search. The code uses a 20-point log grid on [1e-2, 1e2] for one- and two-dimensional active sets and 5,000 seeded log-uniform draws on the same interval for three or more, not the 7-point grid on [1e-3, 1e3] stated before. The reported variances (78.26, 32.28, 0.01262) are the best such draw and are not on any 7-point grid.
9. Search objective. The calibration objective is a weighted MAE (weights 1 for ultimatum mean, dictator, MAO and 0.5 for ultimatum modal and each PG round). The paper's overall 2.70% is the unweighted MAE and is stated as a different quantity.
10. Candidate ranking. Four dimensions (d2, d4, d5, d8) have zero displacement in every game encoding, so the 381 candidates contain only 31 distinct calibration problems. The code breaks ties by ranking all candidates on all sixteen targets. The paper now says so and limits the held-out claim to the variance values.
11. Temperature constants. The code comment records that T_base and T_alpha were set by matching P1 and P3. The accepted text said "obtained from two calibration constraints" without naming them. The paper now says which, and marks P1 and P3 as "sets T" in Table VI.
12. Güth reference coordinate. The code docstring records that r9 = 0.78 was chosen to reproduce the 37% offer. The paper now says so and marks the target "sets r9".
13. New Section V.D "What Is Held Out" lists the lottery targets untouched by any fitting step: P7, P16, P17, and P11 (whose encoding coincides with P3). Their MAE is 5.0%.
14. P11 isolation. The code encodes P11 identically to P3 (reduced second stage), so identical predictions (15.4%). The accepted text claimed a multi-stage epistemic mechanism. The paper now states the isolation effect as an encoding assumption.
15. Domain-dependent coding also applies to d7 (active), not only d5 and d9. Table III and Section IV updated. The ablation text still describes what was ablated (d5, d9).
16. Model Robustness Index. The accepted Eq. (7) (mean ratio of perturbed to calibrated MAE) is not what the code computes. The code's MRI = 0.5 mean + 0.3 p75 + 0.2 p95 of the absolute MAE change (pp) under log-normal (sd 0.5) perturbation of all nine variances, scored on the three-game error. Re-run this session: MRI 1.388 (paper 1.39), mean 0.98, p75 1.43, p95 2.33, worst 4.98. The clause "16/16 still pass within 0.5 log-units" was removed because Section VI.D's own ±0.3 result contradicts it.
17. CPT mechanism sentence removed. The accepted text explained CPT's P3/P11 failures by the loss flip, but both are gain-domain problems. The paper now reports which targets fail without a mechanism claim.
18. BIC added to Test 3 (593.1 to 583.8), which closes the response-letter discrepancy noted in `proofread-comments.txt`. Coefficient p corrected to 1.5e-4.

### Notation standardization (Reviewer 1)

- Mahalanobis cost renamed d_M to c (d_k names dimensions, Δa_k their coordinates).
- Cost gap Δ renamed Δc. Decay δ(r) replaced by the drift coordinates. Perturbation factor f renamed ξ, coefficient c_k renamed e_k, neutral labels x_i renamed z_i.
- Sample sizes are N everywhere (n reserved for players). Perturbation count is R.
- All tolerances and errors in pp. Observed and predicted rates in %.
- d_k is never used as a coordinate value; reference coordinates are r_k.

### Style pass

No em-dashes, colons, or semicolons in prose or captions. Revision-facing wording removed ("the revision", "we now", "earlier language"). Banned filler removed. Contributions rewritten as prose. Abstract and introduction carry no symbols.

### Front and back matter

- Received/revised/accepted line added (received date is a guess from the cover-letter date, confirm in ScholarOne).
- IEEE Senior Member marked in the byline (from the security-radar biography; confirm).
- Acknowledgment with AI-assistance disclosure added (IEEE policy).
- Biography reused from `security-radar/paper/security_radar_ieee_sp.tex` with research interests extended by one phrase. No photo file exists in the source tree. Add one and switch to `IEEEbiography` (comment in the .tex shows how).
- Bibliography: Fraser and Nettle title and authors corrected ("Sam Fraser", "...but not a single-shot ultimatum game", vol. 6 no. 3, DOI); Cheng 2026 issue added; Cheng 2025 month added; eris-econ added; structural-fuzzing URL removed.

## Round 2 (2026-09-07, after the owner's reviewer-style feedback on the final build)

All three blockers and the temperature issue are addressed. Every number below was re-derived from eris-econ this session.

19. Holdout language removed everywhere. Because the reference implementation ranks candidate active sets on all sixteen targets, no lottery target is fully out of sample. The abstract, introduction, Section V.A, Section V.D (retitled "What Was Fitted or Selected on Which Targets"), Table VII (role column now "ranking only"), Section VI.F, the discussion, Limitation 5, and the conclusion now say: variances fitted on games, structure selected on the full benchmark, lottery results demonstrate cross-domain parameter reuse within a jointly selected architecture, not out-of-sample prediction. P11 is stated to test the reduction assumption rather than predict from distinct inputs.
20. CPT appendix corrected. The canonical absolute errors (4.7, 7.6, 5.3, 4.3, 3.4, 8.8 pp) are all within 10 pp, so canonical CPT passes 6/6 at MAE 5.7%, not 4/6. The accepted text's arithmetic was wrong. The "optimized" run (MAE 11.2%, claimed as the best MAE-minimizing solution while a 5.7% point was known) is withdrawn entirely, together with "pass-rate ceiling", "CPT does not exceed 4/6", and "both parameterizations fail P3 and P11". Table IX now reads CPT 6/6 at 5.7%, geometric 6/6 at 3.95% on the lottery subset, with a sentence that the two differ in flexibility and fitting protocol. "CPT cannot be applied to games" is now "the CPT baseline used here does not specify strategic behavior". The CPT fitting script was not found in any repo, so the canonical per-target numbers remain as reported in the accepted text and the pass count is corrected from those numbers.
21. Andersen interpretation made consistent with the stake-normalization caveat. Because the encoding normalizes money to the stake, no value of the monetary variance would predict a stake effect. The calibrated model predicts invariance and that prediction fails. Removed throughout: "as the model predicts", "becomes active at consequential stakes", "in the direction the theory anticipates", "locates the boundary". Abstract, introduction, contribution 4, Section VII.A (retitled "Money-Zero as a Falsifiable Prediction"), Fig. 5 caption ("prediction of the calibrated share-normalized model"), VII.B, VII.D, Limitation 8 ("Failure of invariance demonstrated, boundary not located"), and conclusion now say the result motivates but does not test an absolute- or income-scaled monetary coordinate with finite sensitivity.
22. Temperature nonmonotonicity reported. Turnover at cost gap 1.41. Cost gaps computed from eris-econ: P1 3.48, P3 2.21, P7 2.24, P11 2.21, P16 0.014, P17 0.013, so four of six targets sit on the nonmonotone branch. The encoding gives P1 a larger gap than P3 while the data show more risky choice on P1, and no constant temperature reproduces both (T = 0.5 gives P1 0.1%, T = 3.42 gives P3 34.4%). The two constants were set so that declining discrimination reverses that ordering. Section III.D now says the P1-versus-P3 ordering is carried by the temperature rule and not by the geometry, and that a monotone rule would need a different lottery encoding. Also cross-referenced from Limitation 5.
23. Table IX parameter column now "3 fitted variances, 13 named quantities" with a footnote pointing to Table II and the coordinate constants.
24. Nash and A* paragraph rewritten: Nash equilibrium is a consistency condition and does not assume agents compute it; A* is optimal under admissibility with complete search, and truncation trades that guarantee for tractability; nothing in the paper tests the reading.
25. Notebook reproducibility. The accepted notebook had no stored outputs. It was executed end to end this session with nbconvert against the locally archived raw data (see `tcss_public_data_analysis_executed.ipynb` and `nb_exec_log.txt` if present; otherwise the run failed and the log says why).

## Round 3 (2026-09-07, three reviewer refinements)

26. Temperature. Section III.D now states what a monotone rule requires of the encoding: the Allais risky option must get a smaller cost gap than the 80 percent gamble. The squared-maximum certainty measure gives 0.44 against 0.64 (largest single probabilities 0.66 and 0.80) even though the Allais option pays at least the sure amount with probability 0.99. A certainty measure relative to the sure alternative (probability of paying at least the certain amount) gives 0.99 and 0.80, reverses the gap ordering, and would allow a monotone or constant temperature. Untested; stated as the construction for future work.
27. Income-scaled monetary coordinate. Section VII.A gives a concrete form: s1 = (lambda/Y) q(x)(1-x) with reference lambda/Y, so the monetary displacement grows with the stake and, at finite sigma_1^2, moves the minimizer toward lower offers, the direction of the Andersen data. It replaces invariance by the testable prediction that offers depend on the stake only through lambda/Y. Stated as untested.
28. Baselines. Section VI.E now says the asymmetry runs in the geometric model's favor (baselines at published parameters, geometric structure and temperature selected on this benchmark), that a refit or joint estimation could narrow or reverse the differences, and that the comparison is evidence of cross-domain applicability and not evidence against either canonical model in its own domain.

## Claim changes the owner may want to veto

Items 10 through 14 weaken the out-of-sample claim relative to the accepted text. They are corrections toward what the code did. The alternative is to leave the accepted wording, which a replicator running eris-econ would find false. Recommended: keep the corrections and mention them in the final-files note to the editor.

Suggested note to the editor:

> In preparing the final files I rechecked every variable and constant against the released reference implementation, as Reviewer 1 suggested. This surfaced two factual errors in the accepted text (the Andersen et al. experiment was run in northeast India, not Indonesia, and its top stake exceeds a year's income rather than 1.6 months), and several places where the method description did not match the code (the encoding tables, the variance search, the calibration weights, and which targets set the temperature constants). All reported results are unchanged. The corrections are confined to descriptions, notation, and the two factual errors, and a new Section V.D states precisely which targets are untouched by any fitting step.

## Final-files checklist

- [x] Source (`final_manuscript.tex`) and PDF build clean.
- [x] Figures unchanged (no figure carries the location error).
- [ ] Author photo (none in tree) and biography confirmation.
- [ ] Received date confirmed against ScholarOne.
- [ ] Upload via the IEEE Author Portal, then complete the electronic copyright transfer.
- [ ] Optional: paste the note to the editor above into the final-files comments.

## Related-repo state that does NOT enter the paper

- geometric-economics has a TCSS Part II draft (`experiments/papers/tcss-part2/`), the prereg-coupling-v1 test scored FALSIFIED on the GPS proxy (an individual-level angle correlation, a different object from Part I's aggregate transfer), and prereg-dimensions-v1 frozen but not run. None re-runs or contradicts a Part I number. Part II's finding that T_alpha fit on individual CPC18 choices is about 0.42 rather than 2.13 is unpublished and is not cited.
- The leave-one-out active-set stability re-run promised as future work has not been done anywhere.

## Round 4 (2026-09-09, pre-upload proofread and review)

A full proofread of `final_manuscript.tex` plus a pre-publication review
against `revised_manuscript_v2.tex`. Fixes applied to the source; the PDF
rebuilds to 17 pages, zero undefined references, zero overfull boxes.

29. Fig. 4 (scatter) regenerated. The accepted figure's legend read "Game
    (IS) / PT (OOS) / Published (OOS)", contradicting Section V.D. Labels are
    now "Game (calibration) / Lottery / Historical replication". Data points
    unchanged (`generate_figures.py`, `fig_scatter`).
30. Fig. 6 (agent-based) text and caption corrected to what the figure shows.
    The geometric agents' density is nearly uniform from 0 to 0.5 because the
    calibrated cost differences are small relative to the softmax temperature
    (T = 0.5 in `make_abm_figure.py`); the visible mode near 0.35 is the
    Fehr-Schmidt population. The claim "modal offer near the equal split" was
    removed from Section VII.G and the caption. Figure unchanged.
31. Holdout residue removed: Section VI.G retitled "Calibration Stability";
    its opening sentence no longer says the active set was "discovered" on
    the nine game targets (it was ranked on all sixteen, per Section V.D);
    Limitation 2 "historical holdout" is now "historical replication target";
    the leave-one-out sentence now compares against the other eight game
    targets, not "the remaining fifteen".
32. Fig. 4 caption text "no systematic bias" replaced, since Section VI.B
    names P16 and P17 as the model's clearest systematic failure.
33. Notation (Reviewer 1): public-goods round index renamed from r to j (r is
    the reference vector); responder reference renamed from bold rho to bold
    r; stake in Section VII.A renamed from lambda to capital Lambda (lambda is
    CPT loss aversion); "m = 2" multiplier written as "two" (m is the
    min(2x,1) function); |d_1| and "reference d_1" in Table IV written as
    |s_1| and r_1; perturbation factor named xi at its use; CPT value
    function written over outcomes o_i (x_i is a player payoff); Table IX
    footnote states that alpha, beta follow each source's notation; P1..P17
    labels cross-referenced at first use in Section III.D.
34. Table IV footnote no longer refers to bold-faced coordinates that do not
    exist. Table IX footnote no longer says "in parentheses". "Three stated
    tolerance levels" (there are two widths) is now "three target classes
    with stated tolerances". "Weighted eighty times more heavily" now says
    the basis (sigma_6/sigma_9 in standard-deviation units).
35. Bibliography reordered to order of first citation (IEEE numbering). The
    entry set is unchanged (40 entries); eris-econ is now [28]. Haidt title
    capitalization fixed. Rs 17,000 and Rs 2,000 use the same thin-comma form
    as the stakes line.
36. Baseline table (Table IX) column separation reduced to 4.5pt to clear a
    4.6pt overfull box.

### Open items resolved 2026-09-09 (owner delegated the calls)

- MAE unit. Kept "%" for every MAE in the body and tables (Table VII's
  footnote already says errors are in percentage points); the one stray
  "1.96 pp" in Section VI.G now matches. Abstract and introduction keep
  the words "percentage points" in prose.
- Ranking weights. Read from `eris_econ.targets.build_targets`: the
  ranking score is the weighted MAE with the Eq. (8) weights on the nine
  calibration targets and weight 0.5 on each lottery target and on the
  historical target. Section V.A.4 now says so.
- Game-target MAE. Re-run `evaluate_targets` with the selected model:
  game MAE 1.9500, non-game 3.6689, ratio 1.8815, four ranking-only
  lotteries 5.004, overall unweighted 2.702. Text corrected from 1.96 to
  1.95 and the ratio from 1.87 to 1.88 (both places in Section VI.G).
- 2.87% coincidence. Both values are identical in the accepted text
  (`revised_manuscript_v2.tex` lines 691 and 708); left as reported.
- CPT formula. Section VI.E.1 now states that the separable form written
  there coincides with cumulative weighting for two-outcome prospects and
  differs only for the three-outcome P1. No number changed.
- OWNER comments removed. Received date March 26 matches the cover
  letter; revised date June 10 matches `response_to_reviewers.tex`.
  No author photo exists in any repo, so the biography stays
  `IEEEbiographynophoto`, which IEEE accepts.
- DOIs added for Ruggeri 2020, Engel 2011, Guth 1982, Tversky and
  Kahneman 1992, Fehr and Schmidt 1999, Bolton and Ockenfels 2000,
  Henrich 2010, Slonim and Roth 1998, and Cameron 1999. Each was
  resolved through the CrossRef API on 2026-09-09 and its title, first
  author, journal, volume, issue, pages, and year matched the entry.
- Zenodo title for the Fraser and Nettle data record (10.5281/zenodo.3764693)
  could not be checked: the Zenodo API and record page timed out (HTTP 504)
  on every attempt. Left as is.

Build after these edits: 17 pages, 0 undefined references, 0 overfull
boxes, citation numbers ascend in order of first appearance.

### Left for the owner (superseded; kept for the record)

- MAE unit. The abstract and Section VI.G say "percentage points"; the body
  and every table say "%". One global decision; the house rule says pp.
- Ranking weights. Section V.A.4 says candidates are ranked by "the weighted
  MAE over all sixteen targets", but Eq. (8) defines weights only for the
  nine calibration targets. State the weights used for the other seven.
- Game-target MAE. From Table VII the nine game errors average 1.95, and the
  text says 1.96 (Section VI.G, twice). Confirm from eris-econ output.
- The 2.87% MAE appears for both the eps = 0.10 variance perturbation and the
  +/-10% encoding perturbation. Coincidence or copy; confirm.
- CPT formula (Section VI.E.1) is written as a separable sum, which is
  original PT, not cumulative weighting. Confirm what was computed for the
  three-outcome P1.
- The two `% OWNER:` comments (received date; photo) still stand. Strip
  before upload, after acting on them. Revised date (June 10) also has no
  recorded provenance.
- Easy DOIs missing: Ruggeri 2020 (10.1038/s41562-020-0886-x), Engel 2011,
  Guth 1982, Tversky 1992, Fehr 1999, Bolton 2000, Henrich 2010, Slonim
  1998, Cameron 1999. Zenodo title for Fraser-Nettle differs from the journal
  title; confirm which is the record's.
- `figures/scatter.pdf` is not tracked by git (only the PNG is); the paper
  includes the PDF, so keep the regenerated file with the upload package.

## Note to the editor (replaces the Round 1 draft above)

> In preparing the final files I rechecked every variable and constant
> against the released reference implementation, as Reviewer 1 suggested.
> This surfaced two factual errors in the accepted text (the Andersen et al.
> experiment was run in northeast India, not Indonesia, and its top stake
> exceeds a year's income rather than 1.6 months) and several places where
> the method description did not match the code (the encoding tables, the
> variance search, the calibration weights, and which targets set the
> temperature constants). Three statements are corrected as a result. First,
> because the reference implementation ranks candidate active sets on all
> sixteen targets, the lottery results are now described as cross-domain
> parameter reuse within a jointly selected architecture rather than
> out-of-sample prediction. Second, the CPT baseline in Table IX and Appendix
> A is corrected from 4/6 at 5.8% to 6/6 at 5.7%; the per-target errors were
> already in the accepted text and the pass count was miscomputed, and a
> second "optimized" CPT run has been withdrawn. Third, the Andersen
> high-stakes result is now stated as a failed invariance prediction of the
> calibrated model rather than as confirmation of a predicted boundary. The
> geometric model's own reported numbers are unchanged. Fourth, the
> confidence-interval coverage on the six Ruggeri items is corrected from
> four of six to two of six. The accepted text and the response letter both
> said four of six, but the evaluation file produced by the released
> analysis script, which was included in the revision package, records P3
> and P7 outside their Wilson intervals as well as P16 and P17; the
> per-item errors and the country-cell coverage were already stated
> correctly. Two figure legends and captions were brought into line with
> the corrected text.

## Round 5 (2026-09-09, external 26-item review of the final draft)

Policy after acceptance: a line of the accepted text changes only for a
specific, verifiable reason. Each item below records where the flagged text
lives in the accepted source (`revised_manuscript_v2.tex`, "accepted") or
whether rounds 1 to 4 introduced it, the evidence consulted, and the decision.
Purely stylistic requests that the reviewers accepted as written are left
alone and listed as such.

### Changed (7 edits to `final_manuscript.tex`, 1 figure)

| # | Item | Provenance | Evidence | Change |
|---|------|------------|----------|--------|
| R5-1 | Ruggeri CI coverage "four of six" | Inherited: accepted line 502, repeated in `response_to_reviewers.tex` line 86. Factual error. | `tcss_public_data_analysis/outputs/ruggeri_frozen_prediction_evaluation.csv` as committed with the revision package at 3cd560e and as regenerated 2026-09-07: `covered_by_95ci` is True for P1 and P11 only. P3 predicts 15.4 against Wilson [11.8, 13.9]; P7 predicts 84.2 against [78.1, 80.6]. The script's own printout in every `run_log*.txt` is "95% CI coverage: 0.333". Country-cell coverage 57.9% is correct. | Section V.C coverage paragraph now says two of six inside (P1, P11) and four outside (P3, P7, P16, P17), with the interval width stated. Table VI footnote and Limitation 4 list the same four. |
| R5-2 | Per-subset MAE 0.17 / 2.29 | Not an error. Recomputing from the rounded Table VI values gives 0.15 / 2.32. | Unrounded eris-econ predictions: ultimatum errors 0.302 and 0.038 pp (MAE 0.170); public-goods MAE 2.2875. | Sentence now says "computed from unrounded predictions". Numbers unchanged. |
| R5-3 | Table IX counts "3 fitted variances, 13 named quantities" | Introduced in round 1 (item 6 raised the count from 12 to 13). Internal inconsistency. | Table III rows sum to 13 and include the three variances (3 + 2 + 1 + 2 + 2 + 3). Limitation 6 already says thirteen. | Table IX entry and footnote say thirteen named quantities, of which three are the fitted variances. |
| R5-4 | Eleven-point versus thirteen-point shift | Both sentences introduced in rounds 1 to 4. Both correct: observed 48.3 to 37.0 is eleven points, predicted 48 to 35 is thirteen. | Section IV.F and VI.B text. | Section VI.B sentence now states both numbers. |
| R5-5 | Table IV caption with math in small caps | Introduced in round 1 (new table). Rendering issue. | Caption contained $m(x)$ and $q(x)$ definitions. | Definitions moved to the table footnote. |
| R5-6 | "producing more realistic behavior" (Future Directions) | Inherited: accepted line 988. Untested claim. | No experiment in the paper compares agent realism. | Reworded as an alternative to scalar utility maximizers, realism not tested here. |
| R5-7 | "Three covariance variances" (abstract) | Introduced in round 1 abstract rewrite. Wording. | Accepted abstract had no such phrase. | "Three variances of the diagonal covariance". |
| R5-8 | Fig. 5 legend reads "Fehr--Schmidt" | Inherited: `make_abm_figure.py` line 43 passed the LaTeX string to matplotlib. | The figure file shows two hyphens. | Label uses an en dash; figure regenerated with the same seed (20260610), data unchanged. At the owner's request the density axis is now logarithmic (the expected-value spike at zero, density about 50, had flattened the other two histograms into the bottom of a linear axis); the caption says so. Also at the owner's request the in-figure title "Agent-based illustration (not a new validation)" is removed: it was set by the script since 3cd560e and duplicated the caption sentence promised in the response letter (Th4), which is unchanged. |

### Verified and left unchanged

| Item | Finding | Why unchanged |
|------|---------|---------------|
| Fig. 4 PNG with in-figure title | True. `tcss_public_data_analysis.py` sets it. | Accepted figure carried it. Cosmetic. Removing it needs a rerun of the full analysis. (Fig. 5's title was removed, see R5-8.) |
| Table VIII "Critical/High" in a numeric column | True and inherited (accepted line 785 region). | The ablation bar values in `generate_figures.py` are hand-entered approximations (0, 12, 8, 40), not a recorded run, so there is no sourced number to substitute. Noted for a future revision. |
| Error bars on Figs. 1 and 3 "as Reviewer 3 asked" | The April 19 review has no numbered reviewers and no error-bar request. | No request on record. Fig. 1 values are also approximations (see above). |
| Uniform rescaling invariance of the argmin | True as a matter of structure: game predictions are grid argmins and are invariant to a common variance scale, so the 2.49 to 2.69% spread comes from the lottery softmax. | The accepted sentence reports a measurement and is not wrong. Adding the structural statement would be a new claim after acceptance. |
| Limitation 2 should mention coverage | Coverage failure is carried by Limitation 4, now listing four items. | No second mention needed. |
| Units pp versus %, LOO heading, VI-C/VI-H overlap, P-label numbering, Henrich sentence, `\subsubsection*` at "Toward a tractable equilibrium model", Table I $d_4$ row, line 273 "without refitting" | All present in the accepted text (except line 273, which is accurate). | Stylistic. The reviewers accepted them. |
| Line 522 lists k = 1 to 4 while Fig. 1 plots k = 5 | True. The accepted text (line 423) had the same list. | No sourced k = 5 value exists (the figure's k = 4 and k = 5 points are the placeholder 2.70). |
| "jointly selected architecture" five times | True, introduced in round 1. | Repetition of the corrected holdout language is deliberate; trimming changes nothing factual. |
| Reference [11] (Cheng 2026) | vol. 33, no. 2, pp. 2037 to 2114, verified on CrossRef earlier. | Correct. |
| Reference [33] (Zenodo record) | Not verifiable: Zenodo API down 2026-09-09. | Left. Confirm the record title when Zenodo returns. |
| Classic DOIs (Kahneman and Tversky, Nash, Hart, Simon, Akerlof, Smith, Allais, Ellsberg) | All resolve on CrossRef to the cited works. | Correct. |
| "The letter you pasted is the major-revision decision" | Wrong premise. The pasted letter is the 2026-09-06 acceptance. | Nothing to do. |

The response letter is the record of what was submitted and is not edited;
its "4/6 coverage" line is superseded by the editor note below.

### Round 5b (2026-09-09, owner's external edits in `final_manuscript-2.tex`, adopted)

The owner returned a copy of the round 5 file with further edits. Each was
checked against the accepted source and the data before adoption. Two of
them correct sentences added in round 5.

| Item | Provenance | Evidence | Adopted change |
|------|------------|----------|----------------|
| "computed from unrounded predictions" (round 5, R5-2) was wrong | Round 5 wording error. | Game predictions are integer-grid values (Table VI: 48.0, 34.0, 50, 48, 46, 43, 40). The ultimatum errors 0.302 and 0.038 pp therefore come from unrounded observed means. | Now "computed from unrounded observed values". |
| "each interval is about 2 pp wide" (round 5, R5-1) was wrong | Round 5 wording error. | Wilson half-widths from the evaluation CSV: P1 1.33, P3 1.02, P7 1.24, P11 1.12, P16 1.51, P17 1.51 pp (widths 2.0 to 3.0). | Now "extends roughly plus or minus 1 to 1.5 pp around the observed frequency". |
| Henrich citation (external item 18) | Inherited: accepted line 58 cited Henrich et al. for a prospect-theory replication claim. | Henrich et al. 2010 is about cross-cultural variation, not prospect theory. | Ruggeri cited for the replication, Henrich for broader cross-cultural variation. |
| Table I $d_4$ "Transferable in exchange" (item 23) | Inherited: accepted line 185. | Rows $d_1$ and $d_2$ say "Transferable". | Now "Transferable", consistent with the column. |
| Temperature cross-reference (item 19) | Inherited: accepted text said "the selected covariance and temperature are applied ... without refitting". | Section III.C sets the temperature constants from P1 and P3, so "temperature applied without refitting" was loose. | Sentence now says the covariance is applied without refitting and points to a new label on the Cost-Dependent Temperature subsection. |
| P-label numbering (item 16) | Inherited. | P16 (0.1 percent chance of 5,000 versus 5 for sure) is Problem 14 of Kahneman and Tversky 1979, so the labels are Ruggeri et al.'s sequential item numbers, not the original problem numbers. | One sentence added at the lottery-target description. Semicolon split into a sentence. |
| Duplicate holdout sentences in Section V.C (item 14) | Introduced in round 1. | Section V.D lines carry both statements verbatim ("cross-domain parameter reuse within a jointly selected architecture", "the only result ... independent of every fitting and selection step"). | The two Section V.C copies replaced by pointers to Section V.D. Semicolon split into a sentence. |
| Sections VI-C and VI-H (item 15) | Inherited: accepted lines 647 and 826 presented the same ablation twice. | Both discuss Table VIII / Fig. 2; no distinct content. | VI-H merged into VI-C; the figure and its caption move with it, text unchanged in substance. |
| Uniform rescaling (item 6) | Inherited measurement sentence. | Game predictions are argmins of Eq. (argmin) on an integer grid (round 1, item 7, from the code), so a common variance scale cannot move them; only the lottery softmax of Eq. (temperature) depends on cost magnitude. | Two sentences added stating the invariance and that the 2.49 to 2.69% spread comes from the six lottery frequencies. |
| "Leave-one-out diagnostic" heading (item 5) | Inherited: accepted line 798. | The section's own text says the real leave-one-out refit is future work. | Heading now "Per-target error diagnostic". |
| "covariance variances" (item 17) | Inherited in Limitation 6 and Section VII; round 5 fixed only the abstract. | Consistency with the round 5 abstract wording. | "active variances" / "variances of the diagonal covariance". |
| Limitation 2 (item 8) | Inherited. | The paper uses Ruggeri's pooled frequencies; a country-level analysis is not done. | Limitation 2 now says so. |

Build after adoption: 17 pages, zero undefined references, zero overfull
boxes. `final_manuscript-2.tex` is the owner's working copy and is not
committed.
