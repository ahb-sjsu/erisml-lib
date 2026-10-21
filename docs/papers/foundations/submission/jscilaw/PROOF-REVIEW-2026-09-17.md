# Proof review: "Legal Bond Index Formatted.pdf" (JSciLaw typeset proof, 29 pp)

Reviewed 2026-09-17 against the accepted source `lbi_manuscript.tex`
(2026-08-27 build). Every table value in the proof (Tables 1 to 9) matches the
source. All five figures are present, legible, and carry the right captions.
The reference list has 16 entries and the source cites exactly 16 keys. A
prose-only sentence comparison (154 sentences without math or citations)
found no dropped or altered sentence. The problems are all typesetting.

## Must fix before publication

1. **Every "hat" accent was lost.** The source has $\hat Y$, $\hat P$ and
   $\hat f_0$; the proof prints a caret after the letter: "Y^", "P^(race|x)",
   "f^_0(x)". Occurrences: p. 4 (demographic parity, equalized odds,
   predictive parity, counterfactual fairness, five formulas), p. 8 (two
   "P^(race|x)"), p. 12 ("P^(race|x)"), p. 16 (Fig. 4 caption), p. 18 (two
   "f^_0(x)"). Should read Ŷ, P̂, f̂₀ with the accent over the letter.
2. **Equalized odds formula is cut off at the column edge** (p. 4, left
   column, last line). It ends "Pr(Ŷ = 1 | Y = y, A" and the right-hand side
   "= b)" is missing. Full formula:
   Pr(Ŷ = 1 | Y = y, A = a) = Pr(Ŷ = 1 | Y = y, A = b).
3. **Counterfactual fairness formula is mangled** (p. 4, right column): the
   subscript "A := a′" and the primes float on separate lines. Should read
   Ŷ(X_{A := a′}, a′), with "a′" as a primed variable, not a superscript.
4. **Table 1 row labels** (p. 9): the hyphens in "high-risk" and "low-risk"
   became spaced minus signs: "Pr(high − risk)", "Pr(recid | high − risk)",
   "Pr(recid | low − risk)". Should be "Pr(high-risk)", "Pr(recid | high-risk)",
   "Pr(recid | low-risk)".
5. **Feature name split** (p. 9, end of left column into right column): the
   felony indicator "c_charge_F" appears as "( c_c harge_F )" with the
   opening parenthesis orphaned at the column break. Should be
   "(c_charge_F)" in monospace, on one line.
6. **Section numbers were removed but the text cross-references them.**
   The source has 78 references of the form "§4.5", "§3.3", "Section 2",
   and the proof keeps all of them (for example p. 3 "§4.5", "§4.6",
   "§4.9"; p. 7 "§3.3"; Fig. 1 caption "§4.6"; Table 9 "§4.5", "§6.3").
   With unnumbered headings none of them resolves. Simplest fix: restore
   the numbering. The accepted numbering is
   1 Introduction; 2 Background (2.1 The 2016–2017 dispute, 2.2 The
   proliferation of fairness criteria, 2.3 What population-level metrics
   miss); 3 The Legal Bond Index (3.1 Definition, 3.2 Why a ratio, why
   k-NN, and why Mahalanobis, 3.3 Inference); 4 Empirical Analysis
   (4.1 Data and filter, 4.2 Legitimate-feature space, 4.3 Standard fairness
   metrics, 4.4 LBI across neighbourhood scales, 4.5 Are cross-race
   neighbours worse-matched?, 4.6 Randomization inference, 4.7 Scores,
   categories, and classifications, 4.8 Robustness, 4.9 Validation under
   known ground truth, 4.10 Implementation details, 4.11 Summary);
   5 Discussion (5.1 What LBI adds, 5.2 Individual fairness,
   5.3 Counterfactual fairness, 5.4 Limitations); 6 Policy and Regulatory
   Implications (6.1 A research-stage screening signal, 6.2 Threshold
   setting, 6.3 Doctrinal context); 7 Conclusion.
7. **Subscript placement in Definition 1** (p. 6): the "i" on the two
   expectations E_i sits detached below the E, and the subscript "i" in
   "P̂(race | x_i)" (p. 8) drops below the baseline. Minor, but the
   definition is the paper's central display.

## Layout suggestions (the journal's call)

8. Table 4 is split across pp. 13–14 and Table 8 across pp. 18–19, while
   p. 12 and p. 15 are each half blank. Keeping each table on one page
   would remove both splits and most of the white space.
9. Page 12 ends with roughly half a page empty above Figure 2; page 15
   is half empty after Table 5; page 19 is two-thirds empty after the
   five conclusions.

## Front matter for the journal to fill

10. Header "doi: [DOI]" and the footer placeholders on every page
    ([name], [email], Received/Accepted/Published dates, citation info,
    issue info, doi number). Correspondence: Andrew H. Bond,
    andrew.bond@sjsu.edu.
11. The author block in the source carries ORCID 0009-0003-2599-6158;
    the proof omits it. Add it if the journal style has a place for it.

## Verified correct

- Title, author, affiliation, abstract (all numbers match), keywords.
- Tables 1–9, every cell, including the † footnote of Table 7.
- Figures 1–5 and their captions.
- Numbered lists (three null constructions, five conclusions, four-step
  procedure) preserved.
- References: 16 of 16, in order, with volumes and pages intact.
- Zenodo DOI, ProPublica GitHub link, and repository path in the
  Conclusion.
