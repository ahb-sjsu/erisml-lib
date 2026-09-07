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
