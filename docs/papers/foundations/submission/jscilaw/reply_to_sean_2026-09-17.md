Subject: Re: Legal Bond Index, formatted proof

Sean,

Thank you for the careful formatting work, and yes, well before Monday. I have read the proof against the accepted manuscript. Every table value, figure, caption, and reference came through correctly, and no text was dropped. What needs attention is a handful of typesetting issues, most of them from one cause.

Must fix

1. Hat accents were lost throughout. The manuscript uses Ŷ (predicted outcome), P̂(race | x) (estimated propensity), and f̂₀(x) (fitted base score). The proof prints a caret after the letter instead: "Y^", "P^(race|x)", "f^_0(x)". Occurrences: page 4 (the demographic parity, equalized odds, predictive parity, and counterfactual fairness formulas), page 8 (two P̂), page 12 (one P̂), page 16 (Figure 4 caption), page 18 (two f̂₀).

2. Page 4, left column, last line: the equalized-odds formula is cut off at the column edge. It should read
   Pr(Ŷ = 1 | Y = y, A = a) = Pr(Ŷ = 1 | Y = y, A = b).

3. Page 4, right column: the counterfactual-fairness formula should read Ŷ(X_{A := a′}, a′), with the subscript "A := a′" attached to X and "a′" as a primed variable. In the proof the subscript and primes float on separate lines.

4. Section numbers were removed, but the text refers to sections by number in 78 places (for example "§4.5", "§3.3", "Section 2", and the Figure 1 and Table 9 captions). Could the numbering be restored? The accepted numbering is: 1 Introduction; 2 Background (2.1 The 2016–2017 dispute; 2.2 The proliferation of fairness criteria; 2.3 What population-level metrics miss); 3 The Legal Bond Index (3.1 Definition; 3.2 Why a ratio, why k-NN, and why Mahalanobis; 3.3 Inference); 4 Empirical Analysis (4.1 Data and filter; 4.2 Legitimate-feature space; 4.3 Standard fairness metrics; 4.4 LBI across neighbourhood scales; 4.5 Are cross-race neighbours worse-matched?; 4.6 Randomization inference at full sample size; 4.7 Scores, categories, and classifications; 4.8 Robustness; 4.9 Validation under known ground truth; 4.10 Implementation details; 4.11 Summary); 5 Discussion (5.1 What LBI adds; 5.2 Relationship to individual fairness; 5.3 Relationship to counterfactual fairness; 5.4 Limitations); 6 Policy and Regulatory Implications (6.1 A research-stage screening signal; 6.2 Threshold setting; 6.3 Doctrinal context); 7 Conclusion. If the journal style does not number headings, I can instead supply a version of the text with the cross-references rewritten as section titles.

5. Table 1, page 9: the row labels should read Pr(high-risk), Pr(recid | high-risk), and Pr(recid | low-risk). The hyphens were set as spaced minus signs.

6. Page 9, end of the left column: the feature name c_charge_F is split across the column break as "( c_c harge_F )". It should be one monospace token on one line, with its parenthesis.

7. Definition 1, page 6: the subscript i on the two expectations E_i sits detached below the E, and on page 8 the i in P̂(race | x_i) drops below the baseline. Minor, but Definition 1 is the paper's central display.

Layout, at your discretion

8. Table 4 is split across pages 13 and 14, and Table 8 across pages 18 and 19, while pages 12 and 15 are each about half empty. Keeping each table on one page would remove both splits and most of the white space.

Front matter

9. For the footer: correspondence to Andrew H. Bond, andrew.bond@sjsu.edu. My ORCID is 0009-0003-2599-6158 if the style has a place for it.

I am happy to check a revised proof on the same quick turnaround.

Best regards,
Andrew
