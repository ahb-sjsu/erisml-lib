# Response to Editors — Final Minor Revision

**Manuscript:** The Legal Bond Index: A Matched-Neighbourhood Diagnostic of Algorithmic Disparity, Applied to COMPAS
**Author:** Andrew H. Bond, San José State University
**Date:** July 28, 2026

Dear Editors,

Thank you for the acceptance decision and for the final round of framing guidance. I agree with both identified weaknesses and have made them explicit to the reader, in the editors' own terms, at every point where the affected claims appear. The changes are language and framing, plus a small set of corrections that surfaced during an independent reproducibility and source-verification pass, disclosed in full under Required revision 4 below. No analysis was re-run to obtain different results; every corrected number comes from the already-archived outputs or the cited primary sources, and no conclusion changes.

---

## Required revision 1 — "quantitative implementation of individual fairness" → matched-neighbourhood disparity diagnostic inspired by individual-fairness principles

Replaced in all three places the phrase appeared:

- **Abstract:** now reads "LBI is a matched-neighbourhood disparity diagnostic inspired by individual-fairness principles and by the Aristotelian 'treat-like-cases-alike' criterion."
- **§5.2 (Relationship to individual fairness):** now opens "LBI is not an implementation of individual fairness; it is a matched-neighbourhood disparity diagnostic *inspired by* individual-fairness principles…" and adds an explicit weakness sentence: because the matching metric is defined only on the measured predictors, matched neighbours are similar in the measured coordinates, not certifiably similar simpliciter, so LBI can neither verify nor refute the Dwork-style property itself.
- **§2.2:** a residual passage from the original framing ("sits inside the individual-fairness framework") has also been reworded to match ("draws on the individual-fairness tradition without implementing it"), so the manuscript is now internally consistent on this point.
- **Conclusion:** same replacement ("a matched-neighbourhood disparity diagnostic inspired by individual-fairness principles and by Aristotle's like-cases-alike criterion").

## Required revision 2 — findings conditional on measured predictors; no claim that fully similarly situated defendants were treated differently

Explicit weakness statements added in the editors' terms:

- **Abstract:** "LBI is a screening diagnostic conditional on the measured predictors, not a proof of legal unfairness: because the public dataset contains only a subset of the variables COMPAS uses, the analysis cannot confirm that the compared defendants were fully similarly situated, isolate a causal effect of race, or establish discrimination."
- **§5.4 (Limitations), first paragraph:** now states plainly that the analysis "cannot establish full individual fairness or its violation — it cannot confirm that the compared defendants were fully similarly situated, cannot isolate a causal effect of race, and cannot prove discrimination. Every finding in this paper is conditional on the measured predictors."
- **§6.1 (Policy):** after the audit procedure, a new caveat: an elevated index "does not establish that fully similarly situated individuals were treated differently, and a null result does not certify that they were not."
- **Conclusion:** a new dedicated paragraph restates both weaknesses "so no reader overlooks them."

## Required revision 3 — research-stage screening signal, not a validated regulatory audit standard

- **Abstract:** closing sentence now reads "It is a research-stage screening signal that may contribute one input to an audit, not a validated regulatory audit standard."
- **§5.1(ii):** "suitable for regulatory and audit reporting" softened to "a compact form that could slot into audit-style reporting if the metric matures beyond its current research stage."
- **§6.1:** retitled "A research-stage screening signal for legal-AI audits"; opening paragraph now states the tool "is not a validated regulatory audit standard, and nothing in this paper should be read as certifying it for that role," notes that its validation to date is one dataset and one semi-synthetic suite, and labels the audit procedure a "candidate procedure."
- **Conclusion:** "offered as a research-stage screening signal that may contribute one input to an audit, not as a validated regulatory audit standard."

## Second identified weakness — external validity of the semi-synthetic validation

Added a dedicated Limitations paragraph (§5.4, "External validity of the semi-synthetic validation"): the suite is built on the COMPAS feature matrix and one linear score family; it establishes calibration and power in this setting but "does not establish that the metric or its inference machinery will perform consistently across other algorithms, jurisdictions, or decision settings. This is a weakness of the present evidence." The same caveat is stated in §6.1 and restated in the Conclusion's weakness paragraph.

## Required revision 4 — reproducibility of the archived code, data filters, tables, and figures

I verified the accepted manuscript against the archived pipeline (`revision2_analysis.py`, fixed seed 20260724, single script) two ways: by cross-checking every reported number against the committed outputs (`outputs/revision2_results.json`), and by an independent re-execution of the script in a fresh environment (current library versions, public ProPublica data snapshot). The re-execution reproduced the archived outputs bit-for-bit on every quantity except one robustness row — the robust-Mahalanobis (MinCovDet) estimate, which moves from 1.048 to 1.047 across scikit-learn versions, a known implementation sensitivity of that estimator and immaterial to any claim. The data filter (n = 5,278), Table 1, the LBI curve (1.041–1.069; 1.049 at k = 20, CI [1.027, 1.072]), the null-distribution table, the matching-parity range (1.00–1.02), the focal-group asymmetry (1.087/1.027), the threshold analysis (1.092; 37.3% vs. 34.2%), and the semi-synthetic LBI and rejection-rate values all trace to the archived outputs at the printed precision.

The check surfaced discrepancies, each now corrected in the manuscript and disclosed here:

1. **CRT z-statistic (rounding, conservative direction):** the archived value at k = 20 is 4.91 and had been reported as "5.0"; the manuscript now reports **z = 4.9** in all eight occurrences (the neighbouring rows, 9.7 plain and 5.5 stratified, were already rounded correctly). The global p = 0.001 is unaffected.
2. **Dwork-consistency column of the semi-synthetic validation table:** the previously printed values (0.66–0.69) were stale — they are not producible from the archived outputs. The column now reports the archived values (0.37–0.38 for conditions 1–3, 0.31 for the omitted-predictor condition), and the accompanying sentence has been corrected: the comparator is flat as injected race structure grows (its intended point, now stated accurately) and responds only when a legitimate predictor is withheld from the matching space — i.e., it measures smoothness in the matched coordinates, not protected-attribute structure. The comparator's role in the argument is unchanged; the corrected values state it more accurately.
3. **Two rejection rates now at exact precision:** the CRT false-positive rate is reported as 4.5% (archived 0.045; previously "4%") and the plain-permutation false-fire rate as 56.5% (archived 0.565; previously "56%"), in the abstract and the validation table (which now carries one-decimal rejection rates throughout).
4. **Source-verification corrections (citation precision, no claims affected):** ProPublica's false-positive disparity is now quoted as "nearly twice (44.9% vs. 23.5%)" rather than "1.7–2.0×", and the approximate-accuracy figure as "about 62%" per ProPublica's own methodology article; the description of Northpointe's response now notes it disputed ProPublica's statistical choices while resting its central defense on predictive parity; the Dwork et al. quotation now uses their verbatim phrase ("similar individuals are treated similarly"); and the *Loomis* parenthetical now says the court upheld sentencing use of COMPAS, whose inputs include criminal-history and age factors, rather than implying a holding on those factors specifically.

No conclusion, confidence interval, test result, or figure changes under any of these corrections.

The Zenodo record (concept DOI 10.5281/zenodo.21310251) contains the script, the public-data snapshot, the outputs, and the figures; version 2 of the record, matching this final manuscript, will be published so the concept DOI resolves to the version of record. Version 2 additionally includes two supplementary verification artifacts produced during this check: a machine-checked Lean 4/Mathlib file (`LbiImpossibility.lean`, kernel-checked with no errors or warnings) verifying the confusion-matrix identity underlying the §2 impossibility discussion and its corollary that equal predictive parity and equal false-negative rates force unequal false-positive rates whenever prevalence differs; and the log of the independent re-execution described above. Neither is cited in the manuscript; both strengthen the archive.

Thank you again — I look forward to the final stage.

Sincerely,
Andrew H. Bond
