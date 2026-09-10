# Note to the editors: changes between the accepted manuscript and the final files

TCSS-2026-03-0366.R1, accepted 6 September 2026. Single author.

Reviewer 1 asked at acceptance that the use of variables be rechecked and
standardized. Doing that meant comparing every constant and every method
sentence against the released reference implementation (eris-econ 0.1.0,
now reference [28]) and re-running the analysis scripts archived with the
revision. That check surfaced a small number of factual errors and several
places where the method description did not match the code. Every change is
listed below with its reason. The geometric model's reported predictions,
pass counts, and headline error figures are unchanged except where an item
below says otherwise. The final manuscript is 17 pages in the two-column
format, the same length as the accepted version.

## 1. Factual corrections

1. Andersen et al. (2011) was run in eight villages in Meghalaya, northeast
   India, in rupees, not in Indonesia. The accepted text said Indonesia in
   seven places (abstract, introduction, Section VII.A, the figure caption,
   the limitations, and the conclusion). Indonesia is Cameron (1999), which
   the paper also cites. Source: Andersen et al., Section I, and the
   openICPSR data labels.
2. The Andersen top stake was described as about 1.6 months of income. The
   authors report average yearly income of about Rs 17,000, so the Rs 20,000
   stake is a little over a year's income. Corrected throughout.
3. Confidence-interval coverage on the six Ruggeri lottery items was stated
   as four of six, in the text and in my response to the reviewers. The
   evaluation file produced by the released analysis script, which was
   included in the revision package, records only P1 and P11 inside their
   Wilson intervals; P3 and P7 fall outside as well as P16 and P17. The
   per-item errors, the pooled MAE of 3.95%, and the 58% country-cell
   coverage were already stated correctly. Section V.C, the Table VI
   footnote, and Limitation 4 now say two of six.
4. The canonical CPT baseline was reported as passing 4 of 6 lottery targets.
   Its six per-target errors, which were already in the accepted text, are
   all within the 10 pp tolerance, so it passes 6 of 6 at MAE 5.7%. Table IX
   and Appendix A are corrected. A second "optimized" CPT run, whose reported
   MAE was worse than the canonical one, is withdrawn.
5. The nine-game MAE is 1.95%, not 1.96%, and the ratio of lottery to game
   MAE is 1.88, not 1.87, on re-running the reference implementation. The
   overall MAE of 2.70% is unchanged.
6. The pointer to the reference implementation named a package that does not
   contain the economics model. The paper now cites eris-econ, which
   reproduces all sixteen predictions.

## 2. Method descriptions aligned with the released code

None of these changes a reported number. Each corrects what the paper says
was done.

7. Encodings. The accepted text gave simplified displacement formulas. The
   code encodes each task as a reference point and an alternative point;
   the coordinates are now listed in full in a new Table IV so they can be
   audited.
8. Choice rule. Game predictions are deterministic cost minima on an integer
   percentage grid; the softmax with cost-dependent temperature applies only
   to the six lottery choices. The accepted text implied softmax throughout.
9. Rejection logistic steepness is 15 per unit share, and the symbol is now
   kappa to avoid a clash with the active-set size k.
10. Public-goods rounds use a linear per-round drift of the reference point,
    not an exponential decay. The named-quantity count becomes 13.
11. Variance search. A 20-point log grid on [0.01, 100] for one- and
    two-dimensional active sets, and 5,000 seeded log-uniform draws for
    larger sets, not the 7-point grid stated before.
12. Calibration objective is a weighted MAE (weights 1 and 0.5 as now stated
    in Eq. 8 and Section V.A.4); the reported 2.70% is the unweighted MAE
    and is labeled as such.
13. Candidate ranking used all sixteen targets to break ties among the 31
    distinct calibration problems. Consequently no lottery target is fully
    out of sample. The abstract, Section V, Section VI, the discussion, and
    Limitation 5 now describe the lottery results as cross-domain parameter
    reuse within a jointly selected architecture, and a new Section V.D
    lists what each target was used for. The Andersen test is identified as
    the only result independent of every fitting step.
14. The temperature constants were set from P1 and P3, and the Guth
    reference coordinate from the Guth offer. Both are now stated, and
    Table VI marks those targets.
15. P11 is encoded identically to P3, so their predictions coincide. The
    accepted text described a multi-stage mechanism; the paper now states
    the isolation effect as an encoding assumption.
16. The model robustness index formula is corrected to what the code
    computes (a weighted combination of the mean, 75th and 95th percentiles
    of the MAE change under log-normal perturbation). The value 1.39 is
    unchanged.
17. The Andersen high-stakes result is restated as a failed invariance
    prediction of the share-normalized model rather than as confirmation of
    a predicted boundary, because the stake normalization makes invariance
    the model's only possible prediction. Section VII.A now gives an
    income-scaled monetary coordinate as the untested construction that
    would make the stake effect predictable.
18. The temperature rule is non-monotone in the cost gap, and four of the
    six lottery targets sit on its non-monotone branch. Section III.D now
    says so, states that the P1-versus-P3 ordering is carried by the
    temperature rule and not by the geometry, and describes the certainty
    measure that would allow a monotone rule. Stated as future work.
19. Section VI.E notes that the baseline comparison favors the geometric
    model by construction (baselines at published parameters; geometric
    structure selected on this benchmark) and is evidence of cross-domain
    applicability, not evidence against either canonical model.
20. The uniform-rescaling result now states that the nine game predictions
    are exactly invariant to a common scale of the variances, so the small
    MAE spread comes from the lottery softmax alone.

## 3. Notation and units (Reviewer 1)

21. The Mahalanobis cost is c (d_k names dimensions); the cost gap is Delta c;
    the perturbation factor is xi; sample sizes are N throughout; the
    public-goods round index is j; reference coordinates are r_k; the
    Andersen stake is capital Lambda (lambda is CPT loss aversion); the CPT
    value function is written over outcomes o_i. Errors and tolerances are
    in percentage points, observed and predicted rates in percent, and the
    Table VI footnote says so.
22. BIC values are added to the Andersen logit comparison, closing a
    discrepancy noted in my own response letter, and the stake coefficient
    p-value is corrected to 1.5e-4.

## 4. Structure and presentation

23. Section VI.H (sensitivity profile) duplicated Section VI.C and is merged
    into it. The "leave-one-out diagnostic" heading is renamed "per-target
    error diagnostic", since the section itself defers the refit to future
    work.
24. Figure 3 (predicted against observed) legend read "in-sample /
    out-of-sample", contradicting item 13; labels are now "calibration /
    lottery / historical replication". Data unchanged.
25. Figure 5 (agent-based illustration): the caption said the geometric
    agents show a modal offer near the equal split, which the figure does
    not show; the caption now describes the near-uniform spread. The
    density axis is logarithmic so that the expected-value spike at zero no
    longer hides the other two populations, an in-figure title duplicating
    the caption is removed, and a legend label typo is fixed. Same seed and
    data.
26. Figure 1 (Pareto frontier) is placed at its first citation in Section V.
27. A sentence in the future-directions list claiming agent realism is
    reworded as untested. Two sentences repeating Section V.D are replaced by
    pointers. Citation scope of Henrich et al. (2010) is corrected to
    cross-cultural variation in general. Lottery labels are noted as
    Ruggeri et al.'s item numbers. Minor wording and caption edits are
    listed in the change log archived with the source.

## 5. Bibliography and front matter

28. Fraser and Nettle (2020): title and author list corrected; DOI added.
    DOIs added for nine further references after resolution through
    CrossRef. Cheng (2026) issue number added. eris-econ added as a software
    reference. Entries reordered to order of first citation.
29. An acknowledgment discloses the use of generative AI tools for drafting,
    editing, formatting, and code review, per IEEE policy.
30. Received, revised, and accepted dates and the author biography are added
    as final-files matter.

All source files, the executed analysis notebook, and a per-change log with
the evidence consulted for each item are in the public repository
accompanying the paper.
