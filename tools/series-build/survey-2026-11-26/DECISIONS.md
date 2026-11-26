# Decisions on the 58 [AUTHOR] items of the cross-volume report (2026-11-26)

The author asked: "resolve the 58 items as you recommend". These are the recommendations, now
decisions. They govern every [AUTHOR] item in `cross-volume-report.md`. The 100 source-settled
findings are applied as the report proposes. Record every application in the volume's
`CORRECTIONS-2026-11-26.md` under a section "Cross-volume repairs (2026-11-26)", saying for each
[AUTHOR] item which rule below decided it.

## General rules
- **G1. Take the suggested repair.** Where the report gives a repair for an [AUTHOR] item, apply
  it. It is the weaker, source-matching form. The exceptions are the rules below.
- **G2. Never strengthen; never invent.** Where an item asks whether to add material (e.g. GAS-5:
  add material to Cognition), do not add it. Reword the citing volume instead.
- **G3. Attribute only where the text is.**
  - An epigraph attributed to a volume that does not contain it (M4, AI-33): keep the epigraph and
    drop the attribution line.
  - A result attributed to a volume, chapter or outline that does not hold it (L8, E12, GAS-5,
    GAS-7, AES-5): cite where it is actually stated, or, if nowhere, say "this volume" and drop
    the attribution.
  - GAS-7 in particular: drop "compressibility" (Aesthetics reports its compressibility formula
    failed, and the book has no compressibility result); keep "structural-channel results".
- **G4. Same name, different quantity (X5: E8, M3, E6, P4).** Keep the name, as Ethics Ch. 21
  and Medicine Ch. 12 do. Add one sentence saying it is a different quantity from the Bond Index
  of *Geometric Ethics* (Chapter 18: mean deviation over declared re-descriptions, divided by a
  tolerance). Use the report's text where given. For E8's ch16:80 Prediction 6, write
  "transactions on which an evaluator shows a large gauge violation (Section 4.x, the deviation
  under one re-description)", using the right section.
- **G5. Benchmark numbers that disagree, with no run records (R7, C14, AI-38).** Do not choose
  values.
  - Where a volume records an update explicitly (Cognition 7B: 15.3 sigma updates 8.9 sigma),
    each volume that prints 8.9 sigma keeps it and adds at its first use "(15.3 sigma in the
    later run reported in *Geometric Cognition*, Chapter 7)".
  - Every other disagreement: add once, at the volume's first use of the benchmark, the sentence
    "The benchmark was run more than once; volumes of this series report figures from different
    runs, and the run records are not published."
  - Where a volume cites another volume as the source of a number that the cited volume does not
    print (AI-38), cite the volume that does print it (Reasoning ch10 gives T2 = 0.958).
- **G6. References to held-back chapters (C17, P7; M7 and E11 lapse because Medicine and
  Education Chapter 14 are now published).** Leave the text. The volume's contents page will say
  which chapters the online edition holds back.
- **G7. Subtitles (X3, P1, E13, AI-11, GAS-3).** The volume's own title page wins, then its
  README, then build.py.
  - Economics, Communication, Medicine: the build.py subtitle, which is the title page's. Change
    books.json, the index.html fallback and the README.
  - AI: the published front matter's subtitle ("Alignment, Safety, and the Manifold Structure of
    Machine Values", = books.json). Change build.py.
  - Gastronomy: no title page; the README's subtitle (= books.json). Change build.py.
  - Add a subtitle comparison to build.py's check_manifest.
- **G8. Series identity (X2, X6, C4, S1, AI-4, O4, O5, O6).**
  - X2: README tables list fourteen volumes. Ethics is "Published (v1.29)". The Observation row
    uses the status word Observation's README gives itself. In the mermaid maps, place the
    Observation node in the subgraph that holds Methods (or as its own node if none fits).
  - X6: everywhere, published or not: Ethics is Book 2, Reasoning Book 3.
  - C4: Cognition README states "Geometric Cognition, Volume 6 of the Geometric Series", and
    takes the track count from the campaigns README.
  - S1: apply the report's repair in all fourteen READMEs.
  - AI-4: no "every result from every volume converges here". Write "Results from the domain
    volumes before it converge here". README likewise.
  - O4: "This volume reduces its framework to a single sentence." No claim about every volume.
  - O5: "the house rule of this volume, which *Geometric Ethics* and *Geometric Cognition*, the
    other volumes that keep claim ledgers, share".
  - O6: "settled enough to build further work on".
- **G9. Withdrawn results cited (L6).** State them as history: "The *Geometric Ethics* programme
  once used D4 ... and D4 x D4; it withdrew both in version 1.25 (the group of the two
  demonstrated operations is V4)."
- **G10. Theorem forms (P1 Politics, X4, E5, Medicine Unresolved 8, Education line 465).**
  - Scalar Irrecoverability: cite *Geometric Reasoning*, Chapter 13 (Theorem 13.1, a conditional
    theorem), restated in Section 10.7, as Reasoning's own ch10:313 does. This reverses Politics
    correction 12; record it.
  - A theorem of this volume that borrows the name of the No Escape Theorem but not its
    mechanism: call it "an analogue of the No Escape Theorem of *Geometric Ethics* (Theorem
    18.1, conditional on four requirements)".
- **G11. Vector or scalar heuristic field (Politics P2).** Apply the two repairs. If a later
  formula uses h as a vector, write its gradient explicitly where it appears (h -> -grad h)
  only if the formula reads correctly that way. Otherwise list it as open.
- **G12. Prospect theory (E1, E9, E10).** Apply E9 and E10 in Economics: "reads", not "derives";
  report the sealed results as *Geometric Ethics* states them. Apply E1 in Ethics, with the
  wording "the risky-choice tests run in the companion economics volume's repository, and
  summarised in that volume's Chapter 4,". Use this only after E9 has added that summary;
  otherwise use the report's wording.
- **G13. Ethics items (E1, E2, Part VI covariance, DEME expansion, Chapter 19 "Figure 2").** These
  go into a v1.30 edit script.
  - E2: read the proof of Theorem 21.4. If it gives only the necessary direction, write
    "requires".
  - Part VI: "is not assumed; it is empirically estimated, cross-validated, and falsifiable" ->
    "is not assumed; it is to be estimated from data, cross-validated, and is falsifiable (no
    estimate yet predicts judgements better than the boundary penalties alone, Section 8.10a)".
  - DEME: one expansion, the one the book uses most.
- **G14. Portal.**
  - P7: apply the repair. The embedded game (assets/js/dear-ethicist-game.js) checks correlative
    pairs only and does not score D4, so "measures the same Hohfeldian structure" stands.
  - P8: apply the repair.
  - P9: apply the repair, and add "The book's own interference test found none (Geometric Ethics,
    Section 17.8)" to the interference card.
  - P10: replace docs/site/index.html with the redirect (option a).
  - P11: apply the repair.
