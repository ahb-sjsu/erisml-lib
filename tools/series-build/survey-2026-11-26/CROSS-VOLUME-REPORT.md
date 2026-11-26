# Geometric Series: cross-volume consistency and portal survey (2026-11-25)

This is the survey round only. No file was edited.

**What this report covers.** It checks the fourteen volumes against one another and against the portal. It covers:
1. series identity;
2. citations between volumes;
3. the status of results borrowed from another volume;
4. definitions the volumes share;
5. the portal: erisml-lib docs/index.html, books.json, sitebar.js, guides/math-primer.html, docs/site/index.html, and the encyclopedia's volume standings.

**What it leaves out.** Each volume's CORRECTIONS-2026-11-26.md was read first. Anything recorded there as fixed or as an open item is not reported again. A recorded open item that a source now settles is marked "(recorded, now settled)".

**Where the files are.** Paths are relative to each volume's checkout:
- Methods: geometric-methods
- Observation: geometric-observation
- every other volume: geometric-<name>
- Ethics: edits go into source/Geometric-Ethics-v1.29.docx through an edits script, followed by a rebuild.

**Line numbers.** Other agents were committing to the AI, Communication, Politics and Medicine clones during the survey; Medicine has 23 uncommitted files. Every finding therefore quotes its anchor text, and every old string was matched against the files as they stood at the end of the survey.

**Tags.** [AUTHOR] marks a finding where no source settles the choice, in whole or in part.

## Counts

| Volume | Findings | of which [AUTHOR] |
|---|---|---|
| 1 Methods | 3 | 0 |
| 2 Ethics | 2 | 2 |
| 3 Reasoning | 9 | 1 |
| 4 Economics | 13 | 5 |
| 5 Law | 9 | 2 |
| 6 Cognition | 3 | 2 |
| 7 Communication | 17 | 5 |
| 8 Medicine | 7 | 5 |
| 9 Education | 11 | 3 |
| 10 Politics | 7 | 4 |
| 11 AI | 41 | 9 |
| 12 Gastronomy | 8 | 5 |
| 13 Aesthetics | 8 | 4 |
| 14 Observation | 7 | 4 |
| Series-wide (all READMEs) | 1 | 1 |
| Portal (erisml-lib) | 12 | 6 |
| **Total** | **158** | **58** |

Not counted above:
- findings in unpublished files (front_matter.md, backmatter/bibliography.md, OUTLINE.md and SERIES_OUTLINES.md, none of which are in the build's source_dirs), listed per volume;
- within-volume items noticed in passing, listed at the end.

---

# Patterns that recur across volumes

Each pattern is listed once here; the per-volume sections give its sites.

**X1. Methods title.** Many volumes write *Geometric Methods in Computational Modeling*; older lists also use *Geometric Methods for Complex Systems*. The title is *Geometric Methods: Computational Modeling* (BOOK_CONFIGS, books.json, Methods README).
- Repair: `Geometric Methods in Computational Modeling` -> `Geometric Methods: Computational Modeling`.
- In mermaid nodes: `Geometric Methods<br/>in Computational Modeling` -> `Geometric Methods<br/>Computational Modeling`.

**X2. README series tables.** The READMEs of Reasoning, Economics, Law, Communication, Medicine, Education, Politics, AI, Gastronomy and Aesthetics list 13 books.
- Volume 14 is missing, from both the table and the mermaid map.
- Ethics is marked "Published (v1.23)" (Medicine: "v1.28"). Ethics is now v1.29.
- Repair: `Published (v1.23)` -> `Published (v1.29)`, and add a row `| [Geometric Observation: The Mathematical Structure of What an Observer Can Use](https://github.com/ahb-sjsu/geometric-observation) | Draft |`.
- [AUTHOR] The status word, and where to place OBS in the maps (DOMAIN or ROOT subgraph).

**X3. Subtitles.** books.json and the READMEs carry different subtitles from BOOK_CONFIGS for Economics, Communication, Medicine, AI and Gastronomy. See Portal P1.

**X4. Scalar Irrecoverability attributed to the wrong volume, or graded "proved".** Communication, Medicine, Education, Politics, Law and AI write "proved in *Geometric Reasoning* (Ch. 13)" or "(Ch. 10)".
- *Geometric Reasoning* Theorem 13.1 (ch13:449, §13.6) is a **[Conditional Theorem]** about weighted composites of mutually Pareto-non-dominated profiles. Its Theorem A10.1 covers strictly monotone functions.
- The form "no continuous R^n -> R is injective" is *Geometric Ethics* Theorem 15.1, now tagged **[Theorem (conditional on Def. 5.2)]** (v1.29), and *Geometric Economics* Theorem 14 (Ch. 6).
- Methods' Theorem C.1 is a third, linear-functional statement under the same name. It is consistent with both and not a finding.

**X5. "Bond Index" used for a different quantity without saying so.**
- Ethics v1.26 defines the Bond Index as Bd = D_op/τ: the mean deviation of an evaluation over the declared re-descriptions, divided by a tolerance τ. 0 means perfect invariance. It is reported with the worst case and the share of tests in which the evaluation moved. Tiers: 0.01 / 0.1 / 1 / 10.
- Ethics Ch. 21 and Medicine Ch. 12 already mark the clinical Bond Index (an expected excess cost) as a different quantity that keeps the name.
- Economics, Education and Politics use the name for further quantities without that note (E8, Ed-E6, Po-P4).
- Methods and Communication give the Bond Index the MRI's percentile weights (M2, C10).

**X6. Unpublished front matter and bibliographies swap Books 2 and 3.**
- Economics, Law, Cognition, Communication, Education and Politics each have a front_matter.md (and in most cases a backmatter/bibliography.md) that numbers Reasoning as Book 2 and Ethics as Book 3.
- AI's published front matter and bibliography go further and renumber Books 2–9 (AI-1, AI-41).

---

# Volume 1, Geometric Methods (geometric-methods)

**Checked and consistent:**
- The three Volume 14 ledger rows (claims/LEDGER.md rows PAPER-III.a `[proved]`, T1 and T1-MK `[exploratory]`).
- Every Volume 14 chapter that Ch. 22 and §21.8 point to: ch05 read metric, ch07 COST, App. B cost ledger, ch10 blind probe, ch17 (the T1 note, and the example g = x1 + a sin x2 at ch17:100), ch29 estimation and control.
- The 2026-07 dated status note in §21.8:172.

## chapters/: the volume's old title in nine files

**M1.** Nine files carry the title of an earlier book, *Structural Fuzzing: Geometric Methods for Adversarial Model Validation*, as a byline under the H1; Appendix B uses it as the name of "the text". The source is BOOK_CONFIGS, books.json and README:1: *Geometric Methods: Computational Modeling*. Repairs (each keeps the line count, since the encyclopedia cites these files by line):
- appendix-a-notation.md:3, appendix-c-proofs.md:3, chapter-04-spd-manifolds.md:3, chapter-15-cholesky-parameterization.md:3 and chapter-20-case-study-bioacoustics.md:3:
  - `*Structural Fuzzing: Geometric Methods for Adversarial Model Validation* --- Andrew H. Bond` -> `*Geometric Methods: Computational Modeling* --- Andrew H. Bond`
- chapter-03-hyperbolic-geometry.md:3:
  - `*Structural Fuzzing: Geometric Methods for Adversarial Model Validation — Andrew H. Bond*` -> `*Geometric Methods: Computational Modeling — Andrew H. Bond*`
- chapter-05-topological-data-analysis.md:3:
  - `*Structural Fuzzing: Geometric Methods for Adversarial Model Validation* — Andrew H. Bond` -> `*Geometric Methods: Computational Modeling* — Andrew H. Bond`
- chapter-13-group-theoretic-augmentation.md:3:
  - `*Structural Fuzzing: Geometric Methods for Adversarial Model Validation --- Andrew H. Bond*` -> `*Geometric Methods: Computational Modeling --- Andrew H. Bond*`
- appendix-b-software.md:4-5:
  - `*Structural Fuzzing: Geometric Methods` / `for Adversarial Model Validation*` -> `*Geometric Methods:` / `Computational Modeling*`

## chapters/chapter-10-adversarial-probing.md: the Bond Index given the MRI's formula

**M2.** What the chapter says:
- Line 369: "The MRI/DRI mathematical structure is domain-agnostic. The specific transforms change, but the measurement protocol, aggregation formula, and diagnostic decomposition remain identical:".
- The table that follows has a first column "Bond Index (Ethics)" (lines 371-377).
- Line 379 reads "The common mathematical spine is:", followed by w1·mean + w2·P75 + w3·P95.

What the source says now: the Ethics Bond Index is the mean deviation over a tolerance (X5; ethics Ch. 18 §Requirement 3; CHANGES-v1.26; erisml-lib docs/BOND_INDEX.md:17-20). Its definition has no percentile weights, no adversarial threshold and no compositional chains.

Repair:
- line 369: `but the measurement protocol, aggregation formula, and diagnostic decomposition remain identical:` -> `but the measurement protocol and the diagnostic decomposition remain the same. The aggregation does not: the Bond Index of *Geometric Ethics* is the mean deviation over a tolerance, $\mathrm{Bd} = D_{op}/\tau$ (Chapter 18 there), while the DRI and the MRI weight the mean and two upper percentiles:`
- line 379: `The common mathematical spine is:` -> `The common spine of the DRI and the MRI is:`

The CORRECTIONS file's remark that 10.6.3 "asserts no result" of the Bond Index stands. This finding is about a definition, not a result.

## chapters/chapter-06-pathfinding-on-manifolds.md

**M3.** Line 667: "The Bond Geodesic formulation and its application to behavioral economics are introduced in Bond (2026)."
- Nothing in the volume resolves the key, and the volume cites several different Bond 2026 works.
- The BGE is in *Geometric Ethics* Ch. 20 and in *Geometric Economics*.
- Repair: `are introduced in Bond (2026).` -> `are introduced in *Geometric Ethics* (Chapter 20) and developed in *Geometric Economics* (Volume 4 of this series).`

---

# Volume 2, Geometric Ethics v1.29

**Checked and consistent:**
- Series identity: the index page reads "Book 2 of the Geometric Series · v1.29". No count of volumes or first/last statement appears anywhere in the built pages.
- The Ch. 21 note "Geometric Medicine (Book 8, Chapter 12)" resolves: Medicine ch12:1 and :15-17 carry the matching note.
- No withdrawn result is advertised as standing (grep of the built text for D4, quarter-turn, Conservation of Harm, SU(2), Bell, CHSH and hysteresis agrees with CHANGES-v1.29 §5).

**E1 [AUTHOR].** The Preface ("A note on version 1.25") says "the risky-choice tests of the companion economics volume favored prospect theory (§17.7b, §20.8)". §5.3 "A learned basis" likewise cites "the companion economics volume's chart".
- The published Economics volume reports neither result. Its ch01:191 and ch04:17 still "derive" prospect-theory phenomena.
- The tests are in the geometric-economics repository's experiments/ (experiments/papers/correlation/DESIGN.md:10; experiments/datasets/RESULTS_cpc18_perfold.md), not in its chapters.
- Repair (Preface): `the risky-choice tests of the companion economics volume favored prospect theory` -> `the risky-choice tests run in the companion economics volume's repository, and not yet reported in that volume, favored prospect theory`.
- The alternative is to report the tests in Economics (Economics E9 and E10). The author chooses.

**E2 [AUTHOR].** Ch. 21, Theorem 21.4 (Consent as Gauge Invariance): "Valid informed consent is equivalent to a gauge-invariance condition".
- The same theorem in *Geometric Medicine* (Theorem 8.1) was corrected on 11-26 to "requires", because "the formal statement ('consent is valid only if') and the proof give the necessary direction only" (Medicine CORRECTIONS item 11).
- Repair, if the Ethics proof gives no more than Medicine's: `is equivalent to a gauge-invariance condition` -> `requires a gauge-invariance condition`.
- The Ethics proof was not re-read for the converse.

---

# Volume 3, Geometric Reasoning

## Recorded, now settled or extended

**Unresolved 8 (MRI), ch10:70.** Methods ch09:41, :89 and :102 define the MRI: "the core scalar summary", MRI = w1·ω̄ + w2·P75 + w3·P95, with lower values meaning more robust.
- old: `is a structured protocol for quantifying how a model's performance changes under systematic perturbation. It is not a single number but a *profile*: a function that maps each perturbation type to a robustness score.`
- new: `is there a single weighted figure: the mean, 75th and 95th percentiles of the error deviation under random parameter perturbations, combined with weights 0.5, 0.3 and 0.2 (lower is more robust; Section 9.2 there). This chapter uses a profile instead: a function that maps each perturbation type to a robustness score, of which that figure is one summary.`

**Unresolved 6 (keys).** The Measuring AGI benchmarks are also cited as Bond (2026a), which is *Geometric Methods*, at ch09:30, ch09:48 and ch12:36.

**Unresolved 7 (ErisML D4 table), ch08:319.** erisml-lib commit df00fc5 (2026-10-03), "hohfeld: V4 only; the D4 machinery is removed", removed D4Element, d4_* and GATE_TO_D4. `src/erisml/ethics/hohfeld.py` now maps every gate into V4 (`GATE_TO_V4`, line 190) and keeps `compute_wilson_observable` (line 299). See R9.

## Findings

**R1 (X1).** Methods title at:
- ch00:19
- ch01:727-728, wrapped as `Geometric Methods in Computational` / `Modeling`
- ch02:424, ch04:86, ch05:366, ch06:506, ch07:403
- ch08:198 and :507
- ch09:470
- ch10:16, :70 and :560
- ch11:525, ch12:501, ch13:477
- ch14:28 and :397

**R2.** ch05:368, ch06:508, ch07:405, ch08:509, ch09:472, ch10:562, ch11:527, ch12:503, ch13:479 and ch14:399 read `*Geometric Ethics: Moral Reasoning on the Judgment Manifold.*`.
- Repair: -> `*Geometric Ethics: The Mathematical Structure of Moral Reasoning.*`

**R3.** The Nemotron pipeline is attributed to Methods. No Methods chapter mentions Nemotron; Methods Ch. 13 is group-theoretic augmentation, applied to ARC-AGI.
- ch04:217: `The Nemotron geometric training pipeline (Ch. 13 of *Geometric Methods*) exploits` -> `The Nemotron geometric training pipeline (Section 14.1; its method is the group-theoretic augmentation of *Geometric Methods*, Ch. 13, developed there for ARC-AGI) exploits`
- ch08:204: `The Nemotron Reasoning Challenge pipeline (Bond, 2026a) provides` -> `The Nemotron Reasoning Challenge pipeline (Section 14.1), built on the augmentation method of Bond (2026a, Ch. 13), provides`

**R4.** BirdCLEF and "Chapter 4.6". Methods never mentions BirdCLEF. Band-covariance extraction is Methods §4.4; §4.6 applies it to sperm-whale clicks.
- ch02:292: `In the BirdCLEF 2026 acoustic classification pipeline (Bond, 2026a, Chapter 4.6), covariance matrices` -> `In the BirdCLEF 2026 acoustic classification pipeline, which uses the frequency-band covariance extraction of Bond (2026a, Section 4.4), covariance matrices`
- ch04:247: `(Bond 2026a, Ch. 4.6)` -> `(after Bond 2026a, Section 4.4)`
- ch14:155: `implements two techniques from *Geometric Methods* (Bond, 2026a):` -> `implements two techniques of *Geometric Methods* (Bond, 2026a), which does not itself treat BirdCLEF:`
- ch14:157: `### SPD Manifold Features (Ch. 4.6)` -> `### SPD Manifold Features (Ch. 4.4)`

**R5.** ch14:276 says "from *Geometric Methods*, Theorem 20.3". Methods has no Theorem 20.3; it develops BGE in Ch. 7. Ethics Theorem 20.3 is "BGE–Nash Relationship".
- Repair: `from *Geometric Methods*, Theorem 20.3` -> `from *Geometric Ethics*, Theorem 20.3 (developed computationally in *Geometric Methods*, Chapter 7)`

**R6.** ch08:417 says the MRI "can be reinterpreted as a gauge invariance score: the fraction of gauge transformations under which the model's output remains invariant". In Methods the MRI is a deviation statistic, where lower is better; it is not a fraction.
- old: `can be reinterpreted as a gauge invariance score: the fraction of gauge transformations under which the model's output remains invariant, weighted by the importance of each transformation class.`
- new: `summarizes how far a model's error moves under random parameter perturbations (lower is more robust). Its analogue here is a gauge-violation score: how far the output moves under each class of gauge transformation, weighted by the importance of the class.`

**R7 [AUTHOR].** The same benchmark numbers disagree between Reasoning, Cognition, Communication and AI, and no repository holds the run records.

| Measurement | Reasoning | Cognition | Communication |
|---|---|---|---|
| Framing (T5) | 8.9σ (ch00:13, :89; ch02:243, :259, :372; ch05:64; ch06:376; ch08:353) | 15.3σ (ch00:21, :50; ch07:28, :109); 7B calls it an update of 8.9σ | — |
| Euphemism drift, points on the 0–70 scale | 9–16 (ch02:372) | 9 to 14 (ch07:111, :208) | 10–16 (ch14:63) |
| M1: Pro | ECE 0.230, z 2.5 | 0.186, z 2.2 (corrected 11-26) | — |
| M1: Flash 2.0 | 0.414, z 5.8 | 0.437, z 6.2 | — |
| M1: Fisher combination | 9.3σ (Table 7.1 ch07:94-100; ch09:73-79; ch07:121, :267) | 6.7σ (ch09:79-84) | — |
| M3/M4 | Pro 0.700/0.350; Claude 0.550/0.480 (ch07:141-145; ch09:116, :152) | Pro 0.500/0.000 (ch09:175, :290); ch01 and App. C give Claude 0.723/0.094, which are Reasoning's Flash 2.0 values | — |
| Model name | "Claude Sonnet 4.6" | mostly "Claude 3.5 Sonnet" | — |

- Proposed: a dated note in Reasoning §5.2 and §7.4: `A later analysis with additional scenarios and refined controls gives 15.3σ (*Geometric Cognition*, Technical Appendix 7B); the tables of this chapter are those of the earlier analysis.`
- The M1, M3/M4 and drift-range values need the run records. Record them as Unresolved in each volume.
- The AI and Communication sides are AI-9, AI-19, AI-38 and Communication C14.

**R8 (X2).** README series table :75-91 and map :37-73.

**R9 (recorded Unresolved 7, now settled).** ch08:319: "The assignment of semantic gates to $D_4$ group elements is implemented in the ErisML safety gateway ... The implementation includes the full $D_4$ multiplication table, inverse table, rotation and reflection actions, and the Wilson observable".
- Source: erisml-lib df00fc5 and hohfeld.py:18, :190 and :299.
- Repair: -> `The assignment of semantic gates to group elements is implemented in the ErisML library (\`erisml.ethics.hohfeld\`). Since 2026-10-03 every gate maps to an element of $V_4$; the earlier $D_4$ multiplication table and rotation actions were removed. The implementation keeps the Wilson observable for computing holonomy around closed paths of normative transformations.`

**Unpublished.** SERIES_OUTLINES.md:31 reads `## Book 3: Geometric Ethics`; Ethics is Book 2.

---

# Volume 4, Geometric Economics

## Recorded, now settled by Ethics v1.29

**Unresolved 12 (Thiele).** ch03:30: `with a reported replication across 6 additional languages (Thiele, 2026)` -> `and a further study in six languages reported by Thiele (2026, unpublished; *Geometric Ethics* §17.10a)`.
- Ethics v1.29 §17.10a: "reported by Thiele (2026, unpublished)". The study covers six languages, English among them.

**Unresolved 12 ("4.3% out-of-sample", ch00:57).** Ethics §20.7 now says the published calibration "reports cross-domain reuse of parameters ... not held-out prediction", and that its out-of-sample test (stake invariance) fails. The row stands against the parent text; see also E10.

## Findings

**E1 (X1).** Methods title at ch00:25, ch01:291, ch09:319, ch16:152, README:19 and README:33.

**E2.** The 3×3 derivation is misdescribed.
- What Economics says: ch03:52 has "three normative modes (consequentialist, deontological, virtue-based) ... crossed with three evaluative scopes (individual, relational, institutional) ... nine independent dimensions"; ch01:269 has "three normative modes × three scopes".
- What Ethics §5.3 says: scopes Individual / Relational / Collective × modes What Matters / Who Decides / What We Know. The nine are "a canonical engineering chart ... not a discovered empirical dimensionality".
- Repair, ch03:52: `where three normative modes (consequentialist, deontological, virtue-based) are crossed with three evaluative scopes (individual, relational, institutional), yielding a $3 \times 3$ structure that maps onto nine independent dimensions.` -> `where three ethical scopes (individual, relational, collective) are crossed with three epistemic modes (what matters, who decides, what we know), yielding a $3 \times 3$ grid whose nine cells name the dimensions. *Geometric Ethics* treats the nine as a chart chosen for coverage, not a measured dimensionality (its §5.3).`
- Repair, ch01:269: `(three normative modes × three scopes)` -> `(three ethical scopes × three epistemic modes)`

**E3.** ch03:239 says the rank ≈ 9 is posited "on the strength of the cross-lingual work reported in *Geometric Ethics*". Ethics §5.3 reports effective rank 5.19 of 8.
- `The framework further posits, on the strength of the cross-lingual work reported in *Geometric Ethics*, that the rank` -> `The framework further posits that the rank`
- `It is open: the repository's` -> `It is open: *Geometric Ethics* reports an effective rank of 5.19 of 8 for its validated moral axes, on moral text rather than economic behaviour (§5.3, §20.11); the repository's`

**E4.** ch03:410 says the nine were "validated empirically in Chapters 6-8 of that work". Ethics Chs. 6-8 are the tensor hierarchy, the worked case and stratification; the evidence is Ch. 17, and §5.3 gives 8 of 9 passing.
- `developed in Bond (2026), *Geometric Ethics*, Chapter 5, and validated empirically in Chapters 6-8 of that work.` -> `developed in Bond (2026b), *Geometric Ethics*, Chapter 5; its evidence and the limits of that evidence are in Chapter 17 and §5.3 of that work (eight of nine axes pass a frozen-null gate; rights-and-duties fails).`

**E5.** The BIP's origin is reversed. ch08:28 says "developed in *Geometric Reasoning* ... and applied to ethics in *Geometric Ethics*". Ethics states it as Axiom 5.1; Reasoning adopts it in Ch. 8.
- `developed in *Geometric Reasoning* (Bond, 2026c) and applied to ethics in *Geometric Ethics* (Bond, 2026),` -> `stated in *Geometric Ethics* (Bond, 2026b, Axiom 5.1) and generalized to all reasoning in *Geometric Reasoning* (Bond, 2026c, Ch. 8),`

**E6.** The gauge violation tensor is attributed to Reasoning Ch. 8 and Ethics Ch. 17. Neither volume defines one.
- Reasoning's nearest object is the corruption tensor (Ch. 5, Def. 5.1, read along gauge directions in §8.2).
- Ethics §17.3 tests cross-lingual invariance in LaBSE, not in people (§17.7). No gender swap appears in Ethics.
- ch08:268: `defined in *Geometric Reasoning* (Bond, 2026c, Ch. 8) and applied to ethics in *Geometric Ethics* (Bond, 2026, Ch. 17). In ethics, the gauge violation tensor measures` -> `used in *Geometric Reasoning* (Bond, 2026c, Chs. 5 and 8, the corruption tensor read along gauge directions). *Geometric Ethics* (Bond, 2026b, §17.3) tests the corresponding invariance in a multilingual embedding model, not in people (§17.7). In ethics, such a tensor would measure`
- ch08:286: `mirrors the BIP experiments from *Geometric Ethics* (Bond, 2026, Ch. 17)` -> `adapts to human subjects the BIP experiments that *Geometric Ethics* (Bond, 2026b, §17.3) ran in an embedding model`

**E7.** No Escape is graded above its source. ch16:34 says Ethics "(Chapter 18) proves the No Escape Theorem"; Ethics Theorem 18.1 is "[Theorem (conditional on Req. 1–4).]".
- `*Geometric Ethics* (Chapter 18) proves the No Escape Theorem:` -> `*Geometric Ethics* (Theorem 18.1) proves, conditional on four requirements (canonicalization, grounded evaluation, audit, external verification), the No Escape Theorem:`

**E8 [AUTHOR] (X5).** "Bond Index" is used in three senses, none of them the Ethics one.
- ch04:162 defines BI(τ) = |h(τ(x)) − h(x)|/h(x).
- ch09:133 (Corollary 9.1) uses the name for an exploitation asymmetry.
- ch16:80 (Prediction 6) has "transactions with high Bond Index".
- Repairs:
  - ch04:164, add after `measures the severity of the gauge violation.`: ` (This is the deviation under one re-description, scaled by $h(x)$. The Bond Index of *Geometric Ethics*, Chapter 18, is the mean of such deviations over the tested inputs and re-descriptions, divided by a tolerance $\tau$.)`
  - ch09:133: `the Bond Index will be non-zero` -> `the exploitation index of Proposition 9.3 will be positive`
  - ch16:80 needs the author's rewording: under the definition, a Bond Index belongs to an evaluator, not to a transaction.

**E9 [AUTHOR].** The prospect-theory claims exceed the series' current statement.
- ch04:17: "This chapter derives loss aversion -- and every other prospect-theory phenomenon -- as a geometric property ... The metric is not a parameter to be fitted."
- ch01:191: "derives prospect-theoretic phenomena as geometric properties".
- Ethics §20.8: "They are readings, not derivations, and the tests so far favor prospect theory itself"; sealed CPT tests favoured CPT (Psych-101 0.017 nats/choice). Ethics §20.7: "Each of these accounts is a reconstruction".
- Repairs:
  - ch01:191: `derives prospect-theoretic phenomena as geometric properties` -> `reads prospect-theoretic phenomena as geometric properties`
  - ch04:17: `derives` -> `reads`, and replace the last two sentences with `Sealed tests of reduced-form geometric models against cumulative prospect theory have so far favored prospect theory (*Geometric Ethics*, §20.8).`

**E10 [AUTHOR].** A sealed result on this volume's own chart goes unreported. Ethics §5.3 (prereg-learned-v1): learned coordinates beat "a nine-axis codebook that follows this grid (the companion economics volume's chart...)" by 0.047 nats, and the codebook axes overlapped the learned span less than random subspaces did (0.038 against a null mean of 0.060).
- Repair: append to ch03:54: `In a sealed test on moral-judgement data, learned coordinates outperformed a nine-axis codebook built on this chart (*Geometric Ethics*, §5.3).`

**E11.** ch06:414 says "the application to prospect-theoretic paradoxes, is original to Bond (2026b), *Geometric Ethics*, Chapter 15". There is no Allais or Ellsberg in Ethics Ch. 15 or 20, and Theorem 15.1 is conditional on Def. 5.2.
- `and the application to prospect-theoretic paradoxes, is original to Bond (2026b), *Geometric Ethics*, Chapter 15,` -> `is original to Bond (2026b), *Geometric Ethics*, Theorem 15.1 (conditional there on the nine-dimensional chart of Definition 5.2); the application to prospect-theoretic paradoxes is new here. Both are`

**E12 [AUTHOR].** ch08:374 cites "*Geometric Reasoning* (Bond, 2026c, Ch. 14): heuristic augmentation". Reasoning Ch. 14 is data augmentation; heuristic correction is §11.3 and §11.7.1.
- Repair: `Ch. 14` -> `Chs. 11 and 14`

**E13 [AUTHOR] (X2, X3).** The README title's subtitle ("the Bond Geodesic Equilibrium, and the Irrecoverable Geometry of Markets", which matches books.json) differs from ch00:1 and BOOK_CONFIGS ("Equilibria, and the Geometry of Markets").

**Keys, folded into the repairs above.** `(Bond, 2026)` for Ethics at ch03:30, ch03:410, ch08:28, ch08:268 and ch08:286 -> `(Bond, 2026b)`.

**Unpublished:**
- front_matter.md:26 has Reasoning "(Book 2)" and Ethics "(Book 3)" (X6), and still `$D_4 \times U(1)_H$`.
- front_matter.md:30 says "It predicts them, from geometry alone".
- backmatter/bibliography.md:8-9 swap 2026b/2026c and Books 2/3. :11 gives a Law subtitle "Courts, Constitutions, and the Architecture of Legal Reasoning", :12 a Cognition subtitle "The Manifold Structure of Mind", and the list stops at Book 8.

---

# Volume 5, Geometric Law

**L1 (X4).** ch01:42, :257 and :261 cite Scalar Irrecoverability's general form as "proved in *Geometric Reasoning* (Bond, 2026c, Ch. 10)" and call it "a corollary of the rank-nullity theorem".
- ch01:42: `developed in *Geometric Reasoning* (Bond, 2026c, Ch. 10)` -> `in the form of *Geometric Ethics* (Bond, 2026b, Theorem 15.1) and *Geometric Economics* (Bond, 2026d, Theorem 14)`
- ch01:261: `in its general form, is proved in *Geometric Reasoning* (Bond, 2026c, Ch. 10).` -> `in the form used here, is Theorem 15.1 of *Geometric Ethics* (Bond, 2026b) and Theorem 14 of *Geometric Economics* (Bond, 2026d); *Geometric Reasoning* (Bond, 2026c, Theorem 13.1 and Theorem A10.1) proves composite-score forms.`
- ch01:261: `The ethical version (Moral Irrecoverability)` -> `The ethical version (Theorem 15.1, conditional there on the nine-dimensional chart)`
- ch01:257: `is proved in Bond (2026c, *Geometric Reasoning*, Chapter 10) and is a corollary of the rank-nullity theorem applied to` -> `is Theorem 15.1 of Bond (2026b, *Geometric Ethics*), which rests on invariance of domain for`

**L2.** ch03:253 says the method "mirrors the methodology validated in the Geometric Ethics programme", and ch03:255 calls LaBSE's embeddings "language-invariant".
- Source: the Ethics ledger GE-CROSSLINGUAL is exploratory and model-mediated, and Ethics §17.10 says language identity is recoverable at 99.8%.
- ch03:253: `mirrors the methodology validated in the Geometric Ethics programme:` -> `follows the methodology of the Geometric Ethics programme (exploratory and model-mediated in that volume's claim ledger):`
- ch03:255: `that are language-invariant — the same legal concept in English, Spanish, or Mandarin maps to the same region of embedding space.` -> `that place translations close together; *Geometric Ethics* reports that language identity is still recoverable from such representations (§17.10).`

**L3.** ch03:261 says the method "directly replicates the methodology validated in the parent framework, where nine moral-dimension probes achieved $F_1 = 0.74\text{--}0.91$".
- Source: Ethics Part VI gives this range "as reported by Thiele (2026, unpublished)", and CHANGES-v1.29 open item 9 says its attribution is unclear.
- Repair: `directly replicates the methodology validated in the parent framework, where nine moral-dimension probes achieved` -> `follows the methodology of the parent framework, where linear probes for the nine moral dimensions are reported, in a study reported by Thiele (2026, unpublished), at`, then append ` The rights-and-duties axis failed its preregistered gate there (*Geometric Ethics* §5.3).`

**L4.** ch03:449: "the nine moral dimensions of Bond (2026a, *Geometric Ethics*) ... adapts the methodology of Bond (2026a), independently replicated by Thiele (2026)."
- Source: ch00:23 sets 2026a = Methods and 2026b = Ethics.
- Repair: both `2026a` -> `2026b`, and `independently replicated by Thiele (2026)` -> `and applied in six languages in a study reported by Thiele (2026, unpublished)`

**L5.** ch05:469: "extends the Bond Index of Bond (2026a, *Geometric Ethics*, Ch. 14)". Ethics Ch. 14 is collective agency; the Bond Index is Ch. 18, and the Legal Bond Index is Ch. 22.
- `(2026a, *Geometric Ethics*, Ch. 14)` -> `(2026b, *Geometric Ethics*, Ch. 18; see also its Ch. 22)`
- `reported by Bond (2026a)` -> `reported by Bond (2026b)`

**L6 [AUTHOR].** ch05:47: "The Geometric Ethics programme used $D_4$ (for the first square) and noted that the full moral gauge group is $D_4 \times D_4$".
- Source: Ethics Ch. 12 gives V4, and Ethics Conjecture 22.1 gives V4 ⋊ V4 for the octad.
- Repair: `used $D_4$ (for the first square) and noted that the full moral gauge group is $D_4 \times D_4$ when the second square is included.` -> `uses $V_4$ for the first square (its Chapter 12) and conjectures $V_4 \rtimes V_4$ for the full octad (its Conjecture 22.1).`
- The direct-product narrative at :44-48 and :95 then needs the author.

**L7.** The four failure modes are Reasoning Part II (Chs. 5-8), as Law's own ch01:182 says. Ethics has no such taxonomy.
- ch10:26: `The Geometric Ethics programme identified` -> `*Geometric Reasoning* (Bond, 2026c, Chapters 5–8) identified`
- ch10:402: `identified in the Geometric Ethics framework (Bond, 2026)` -> `identified in *Geometric Reasoning* (Bond, 2026c, Chapters 5–8)`

**L8 [AUTHOR].** ch11:494 attributes the gauge violation tensor to Ethics and to "Geometric Reasoning Chapter 8 (as referenced in the SERIES_OUTLINES)". Neither volume defines it (see E6), and SERIES_OUTLINES is not published.
- old: `The gauge violation tensor is the legal application of the gauge violation measurement methodology developed in the Geometric Ethics framework (Bond, 2026). The concept directly extends the gauge violation tensor from Geometric Reasoning Chapter 8 (as referenced in the SERIES_OUTLINES).`
- new: `The gauge violation tensor applies to law the invariance test of the Bond Invariance Principle (*Geometric Ethics*, Bond, 2026b, Axiom 5.1) and extends the corruption tensor of *Geometric Reasoning* (Bond, 2026c, Chapter 5, read along gauge directions in Chapter 8).`

**L9 (X1, X2).** README:18 and :32.

**Checked.** The Legal Bond Index's measured form (a ratio centred on 1) is stated in Law ch05 and ch08 as a different form on a different scale, so Ethics Ch. 22's identification and Law agree. The 0.155 baseline is recorded (Unresolved 5).

**Unpublished.** front_matter.md:26 (X6). backmatter/bibliography.md:8-9 swap 2026b and 2026c; :12 gives the Cognition subtitle "The Manifold Structure of Mind"; the list stops at Book 8.

---

# Volume 6, Geometric Cognition

The published chapters cite other volumes only at ch00:15, ch07:71 and ch07:88.

**C1.** ch07:71: "Thiele (2026) demonstrated that the nine moral dimensions ... are linearly decodable".
- `Thiele (2026) demonstrated that the nine moral dimensions of Bond's broader geometric ethics framework are linearly decodable` -> `A study reported by Thiele (2026, unpublished; *Geometric Ethics* §17.10a) describes the nine moral dimensions of Bond's broader geometric ethics framework as linearly decodable`

**C2 [AUTHOR].** The keys have no target, since backmatter/ is not built. ch00:15 cites Ethics as "(Bond, 2026b)", but backmatter/bibliography.md:8 makes 2026b Reasoning. ch07:88 cites "The Bond Invariance Principle (Bond, 2026)".
- Repair: ch07:88 `(Bond, 2026)` -> `(*Geometric Ethics*, Axiom 5.1)`.
- ch00:15 already names the title inline: either drop `(Bond, 2026b)` or fix the bibliography.

**C3.** The benchmark numbers are counted under R7.

**C4 [AUTHOR].** README identity. Its title is "Observer-Limited Geometric Cognition", and it never states Volume 6 or the book's title. README:133 has the X1 variant, and README:31 says "twenty-nine tracks" (the campaigns README now says thirty).
- Add under "## Part of the Geometric Series": `The book in chapters/ is *Geometric Cognition: The Mathematical Structure of Human and Artificial Thought*, Volume 6 of the Geometric Series.`
- `twenty-nine tracks` -> `thirty tracks`

**Unpublished.** front_matter.md:26 (X6). backmatter/bibliography.md:8-9 are swapped, and :11 gives the Law subtitle "Courts, Constitutions, ...".

---

# Volume 7, Geometric Communication

**C1 (X4).** ch01_perplexity_trap.md:
- :166: `proved in *Geometric Reasoning* (Ch. 13) and here stated` -> `stated as a conditional theorem in *Geometric Reasoning* (Ch. 13) and here stated`
- :269: `(*Geometric Reasoning*, Ch. 13) proves that no scalar projection can preserve the Pareto structure` -> `(*Geometric Reasoning*, Ch. 13) shows, for weighted composites of mutually Pareto-non-dominated profiles, that no such projection preserves the Pareto structure`

**C2 [AUTHOR].** ch15_scalar_irrecoverability.md:16. Its level-set form is that of Ethics Theorem 15.1 (conditional; ledger GE-THM-15-1, class exploratory), not Reasoning's Pareto form.
- Repair: add `; the level-set form below is that of *Geometric Ethics*, Theorem 15.1`

**C3.** ch15:295: `Of all the domains treated in the Geometric series --- reasoning, ethics, law, method ---` -> `Of all the domains the Geometric Series treats,`

**C4.** ch04_three_geometries.md:44: `See *Geometric Methods* (Bond, 2026a), Ch. 4.3 for the derivation.` -> `... Section 3.1.2 for the derivation.` (Methods §4.3 is the Fréchet mean; hyperbolic volume growth is §3.1.2.)

**C5.** "GM Ch. 4.6" is given for hyperbolic material. Methods §4.6 is acoustic SPD; the Poincaré ball is Methods Ch. 3.
- ch05_hyperbolic_embeddings.md:22: `(Bond, 2026a, Ch. 4.6).` -> `(Bond, 2026a, Ch. 3).`
- ch05:395: `In *Geometric Methods* (Ch. 4.6), the mathematical foundations are developed in full generality.` -> `In *Geometric Methods* (Ch. 3), the mathematical foundations are developed.`
- ch07_whale_communication.md:356: `GM Ch. 4.6.` -> `GM Ch. 3.` in `Poincare ball model and distortion theorem: Ch. 5 of this volume; GM Ch. 4.6.`
- ch16_rosetta.md:301: in `Hyperbolic embeddings: Ch. 5 of this volume; GM Ch. 4.6.` -> `GM Ch. 3.` The SPD entry "GM Ch. 4.6" there is correct.
- ch18_open_questions.md:345: `Hyperbolic embeddings and distortion: GM Ch. 4.6;` -> `Hyperbolic embeddings and distortion: GM Ch. 3;`

**C6.** ch05:395: `In *Geometric Ethics* (Ch. 8), it encodes the hierarchy of normative concepts (abstract principles near the origin, specific duties near the boundary). ` -> delete. Ethics v1.29 never mentions the Poincaré ball.

**C7 [AUTHOR in part].**
- ch10_translation.md:432: `developed in *Geometric Reasoning* (Ch. 4)` -> `of parallel transport (*Geometric Ethics*, Section 4.6 and Ch. 10)`
- ch10:432, same line: `In *Geometric Ethics* (Ch. 8), the same framework describes the transport of moral concepts across cultural contexts. In *Geometric Methods* (Ch. 4.6), the mathematical foundations are developed in full generality.` -> `In *Geometric Ethics* (Ch. 10), the same framework describes the transport of moral evaluations along paths in moral space.`
- ch16:301: `Parallel transport and holonomy: Ch. 10 of this volume; GR Ch. 4.` -> `...; GE Ch. 10.`
- The "general principle" itself has no source.

**C8.** The adversarial robustness framework is attributed to Ethics Ch. 22, which is Jurisprudence; the Bond Index is Ch. 18.
- ch07:122: `(Bond, 2026b, Ch. 22)` -> `(Bond, 2026b, Ch. 18)`
- ch07:356: `Adversarial robustness framework: GE Ch. 22.` -> `Bond Index: GE Ch. 18; MRI and DRI: GM Ch. 9–10.`

**C9.** ch07:198: `There, the Bond Index measured how robust an AI system's ethical judgements are to adversarial perturbation of the input.` -> `There, the Bond Index measures how much an AI system's ethical evaluation moves under declared re-descriptions of the input that should not change it (Ch. 18, Requirement 3).`

**C10 (X5; Methods M2).** ch07:160 and appendix_b_eris_ketos.md:791 call the 0.5/0.3/0.2 weights "the Bond Index convention". Source: these are the MRI's default weights (Methods §9.2.2), carried to the DRI in Methods §10.5.1.
- ch07:160: `The weights (0.5/0.3/0.2) follow the Bond Index convention` -> `The weights (0.5/0.3/0.2) are the default weights of the Model Robustness Index of *Geometric Methods* (Section 9.2.2), which its Section 10.5.1 carries over to the DRI`
- App B:791: `The DRI is a direct adaptation of the Bond Index. The mathematical structure is identical` -> `The DRI is the Model Robustness Index of *Geometric Methods* (Sections 9.2.2 and 10.5.1) applied to input perturbations, on ErisML's fuzzing architecture. The structure it shares with that architecture is`
- App B:791: `is the Bond Index convention, emphasising tail behaviour.` -> `is the MRI's default weighting, emphasising tail behaviour.`

**C11.** These passages repeat the random-play error that Ethics v1.26 corrected (ethics ch17:119: random play scores about 0.75).
- ch11_cross_lingual.md:320: `A Bond Index of 0.5 indicates random pairing.` -> `Random answers among the four positions give the expected pairing one time in four, so random pairing scores about 0.75 (as *Geometric Ethics*, Chapter 17, corrected in its version 1.26).`
- appendix_c_bip_protocol.md:364: `0.5 indicates random classification; values above 0.5 indicate systematic anti-correlation.` -> `random classification among the four positions scores about 0.75; a value of 1 means no pairing was the expected one.`

**C12.** ch11:393: `achieves Bond Index $< \tau$` -> `achieves a Bond Index below a declared threshold`. Bd already divides by τ.

**C13.** These claims are graded above their source (Ethics §17.7 and README).
- ch13_gauge_theory.md:523: `which demonstrate gauge invariance of moral content across languages and centuries` -> `which test, in a trained encoder, whether moral content is invariant across languages and centuries (*Geometric Ethics*, §17.7, reads the cross-lingual result as a property of the model's representations)`
- ch11:403: `The experiment shows that the *grammar* of moral reasoning (who owes what to whom) is universal` -> `The experiment is consistent with a *grammar* of moral reasoning (who owes what to whom) shared by these corpora, as the encoder represents them`

**C14 [AUTHOR] (R7).** ch14_failure_modes.md:238-266 gives the distractor result as 5.0σ with a recovery ceiling near 33%. Reasoning gives 4.6σ (ch05:132, ch08:128-152) and about 39% (ch07:221). Communication's correction 1 moved Chapter 3 to the new values, so the two volumes now disagree; the run that is current is needed.

**C15 (X1).** appendices/appendix_a_math.md:3.

**C16 (X1, X2, X3) [AUTHOR].** README:18 (title). :72 `Published (v1.23)` -> `Published (v1.29)`. Add the Observation row and map node. H1 subtitle: see P1.

**C17 [AUTHOR].** Published chapters cite the held-back Chapter 17: ch16_rosetta.md:212, ch18_open_questions.md:122 and :284 (:219 is already recorded).

**Unpublished.** front_matter.md:26 (X6). backmatter/bibliography.md:5 (X1).

---

# Volume 8, Geometric Medicine

The working tree already fixes "final volume" and the Book numbers. These edits are uncommitted, by another agent.

**M1 (X4) [AUTHOR in part].**
- ch01_qaly_trap.md:130: `proved in *Geometric Reasoning* (Ch. 13) and here previewed` -> `stated as a conditional theorem in *Geometric Reasoning* (Ch. 13) and here previewed`
- ch05_qaly_irrecoverability.md:241: `Scalar Irrecoverability Theorem proved in *Geometric Reasoning* (Ch. 13) and applied in` -> `Scalar Irrecoverability Theorem, stated as a conditional theorem in *Geometric Reasoning* (Ch. 13), and applied in`
- [AUTHOR] "In each domain, the theorem has the same algebraic structure (rank-nullity)" is false for Reasoning Theorem 13.1 and Communication Theorem 1.1. Suggested: `In this volume, as in *Geometric Ethics* (Theorem 15.1), the argument is a dimension count (rank-nullity)`.

**M2.** appendices/appendix_a_math.md:110 (working tree): `Bond 2026b)` -> `Bond 2026c, Theorem 15.1, conditional on its Definition 5.2)`. In the working-tree bibliography 2026c = Ethics, and A.2 follows Ethics 15.1 nearly word for word.

**M3 [AUTHOR] (X5).** ch12_bond_index.md:376, footnote 1:
- `The Bond Index is named for its structural role in the Geometric Series: it measures the deviation between actual and optimal paths on the moral manifold` -> `The clinical Bond Index measures the deviation between actual and optimal paths on the clinical decision complex; the Bond Index of *Geometric Ethics* (Ch. 18), whose name it shares, measures invariance under re-description (Section 12.1)`
- The naming sentence is the author's.

**M4 [AUTHOR].** ch04_clinical_manifold.md:8: the epigraph is attributed to *Geometric Ethics*, but its text appears in no Ethics v1.29 page.
- `> --- Andrew H. Bond, *Geometric Ethics*` -> `> --- Andrew H. Bond`

**M5 (X1).** appendices/appendix_a_math.md:3 and README:18.

**M6 [AUTHOR] (X2, X3).** README:72 `Published (v1.28)` -> `Published (v1.29)`. Add the Observation row. H1 subtitle: see P1.

**M7 [AUTHOR].** "Chapters 13--15" includes the held-back Ch. 14, at ch01:170, :230 and :244; ch02:110; and ch07:192 and :196.

**Unpublished.** backmatter/bibliography.md:8-10 give subtitles found in no build config: Economics "Markets, Welfare, and the Topology of Value", Law "Legal Reasoning and the Structure of Justice", Cognition "The Mathematical Structure of Mind". :5 (X1).

---

# Volume 9, Geometric Education

**E1 (X4).** ch01_gpa_trap.md:181: `proved in *Geometric Reasoning* (Ch. 13) and here stated` -> `stated as a conditional theorem in *Geometric Reasoning* (Ch. 13) and here stated`

**E2.** ch08_grading_moral_injury.md:12: `Moral Injury Accumulation Theorem from Geometric Medicine (Ch. 13--15)` -> `... (Ch. 13, Theorem 13.1)`. Medicine Ch. 14 is held back.

**E3.** ch08:18:
- old: `moral injury is defined as the permanent alteration of the clinician's heuristic function by forced boundary crossings on the clinical decision complex`
- new: `moral injury is defined as a forced crossing of a moral boundary on the clinical decision complex (Definition 13.1), and its accumulation is held to alter the clinician's heuristic function, irreversibly above a threshold (Theorem 13.1)`
- Source: Medicine ch13:57, :91 and :253.

**E4.** ch09_gauge_invariance.md:17: `The Bias Invariance Principle (BIP) from *Geometric Reasoning* (Ch. 11)` -> `The Bond Invariance Principle (BIP) from *Geometric Reasoning* (Ch. 8)`

**E5 [AUTHOR in part].** ch12_ai_education.md:114: `from *Geometric Ethics* (Bond, 2026b, Ch. 19), which establishes that` -> `from *Geometric Ethics* (Bond, 2026b, Ch. 18, Theorem 18.1, a conditional theorem on its four requirements), which states that`
- [AUTHOR] Theorem 12.1's mechanism is not that of Ethics 18.1; this is the same problem as Medicine's Unresolved 8.

**E6 [AUTHOR] (X5).** ch13_educational_bond_index.md:157:
- old: `follows the general Bond Index from *Geometric Ethics* (Bond, 2026b, Ch. 16), adapted for educational institutions.`
- new: `follows the clinical Bond Index of *Geometric Ethics* (Bond, 2026b, Ch. 21, Definition 21.10) and *Geometric Medicine* (Ch. 12), adapted for educational institutions. It shares a name with the Bond Index of *Geometric Ethics* (Ch. 18), which measures how much an evaluation moves under re-descriptions that should not change it, and is a different quantity.`
- The footnote has no marker. Consider putting the last sentence in §13.1 itself, as Medicine ch12:19 does.

**E7.** ch17_feedback_general_theory.md:109: `is described in *Geometric Reasoning* (Bond, 2026c, Ch. 16) and in the Series Outlines document.` -> `is described in the Series Outlines document (\`SERIES_OUTLINES.md\`, item 9, in the geometric-reasoning repository).`

**E8.** ch18_open_questions.md:107: `(Bond, 2026b, Ch. 30)` -> `(Bond, 2026b, Ch. 29)`. Ethics Ch. 29 is Open Problems.

**E9 (X1).** appendices/appendix_a_math.md:5, appendix_d_notation.md:69 and README:18.

**E10 (X2).** README:32 `Published (v1.23)` -> `Published (v1.29)`. Add the Observation row.

**E11 [AUTHOR].** ch01_gpa_trap.md:269 and ch02_testing_industrial_complex.md:90 cite the held-back Ch. 14.

**Unpublished.** front_matter.md:26: `*Geometric Reasoning* (Book 2)` -> `(Book 3)`, and `Books 3 through 8 --- *Geometric Ethics*, *Geometric Economics*,` -> `*Geometric Ethics* (Book 2) and Books 4 through 8 --- *Geometric Economics*,`. backmatter/bibliography.md:87 (X1).

---

# Volume 10, Geometric Politics

**P1 [AUTHOR] (X4).** This reverses Politics correction 12, so it needs the author's confirmation. GR ch10:313 itself says "the Scalar Irrecoverability Theorem (Chapter 13, Section 13.6)".
- ch01_left_right_trap.md:80: `proved in *Geometric Reasoning* (Ch. 10)` -> `stated as a conditional theorem in *Geometric Reasoning* (Ch. 13; restated for robustness surfaces in Section 10.7)`
- ch05_voting_contraction.md:79: `(Ch. 10)` -> `(Ch. 13)`

**P2 [AUTHOR in part].** The heuristic field is given as a vector field. Reasoning defines it as a scalar cost-to-go (ch03:9, :367).
- ch06_campaigns_heuristic.md:20: `as a vector field on the search manifold. The heuristic field $\mathbf{h}: \mathcal{M} \to T\mathcal{M}$ assigns` -> `as a scalar field on the search manifold that estimates the cost-to-go; its negative gradient $\mathbf{h} = -\nabla h: \mathcal{M} \to T\mathcal{M}$ assigns`
- ch11_media.md:22: `a heuristic field $\mathbf{h}: \mathcal{M} \to T\mathcal{M}$ guides search by estimating distances` -> `a heuristic field $h: \mathcal{M} \to \mathbb{R}$ guides search by estimating distances`
- [AUTHOR] Whether the later formulas need the vector reading.

**P3.** ch18_open_questions.md:59: `The series has produced conservation-like results in ethics` -> `The series has posited conservation-like statements in ethics`. Source: GE-HARM-CONSERVATION is withdrawn, and Economics' conservation laws are tagged Modeling Axiom.

**P4 [AUTHOR] (X5).** ch15_political_bond_index.md:18. The chapter is held back; make this edit before it is published.
- old: `The Political Bond Index is the political instantiation of the general Bond Index from *Geometric Ethics* (Ch. 18). Across the Geometric Series, the Bond Index measures the expected deviation between the manifold-optimal path and the institutionally constrained path:`
- new: `The Political Bond Index follows the clinical Bond Index of *Geometric Ethics* (Ch. 21, Definition 21.10) and *Geometric Medicine* (Ch. 12): it measures the expected deviation between the manifold-optimal path and the institutionally constrained path. It shares a name with the Bond Index of *Geometric Ethics* (Ch. 18), which measures invariance under re-description, and is a different quantity:`
- Published pages already use the index: ch05:191, ch14:146, ch16:93-103, ch18:97 and App D:55-56. ch05:191 describes it as the distance to the "gauge-invariant outcome", which is closer to the Ethics index (author).

**P5 (X1).** appendices/appendix_a_math.md:3 and README:18.

**P6 (X2).** README:32 `Published (v1.23)` -> `Published (v1.29)`. Add the Observation row.

**P7 [AUTHOR].** Published chapters cite the held-back Chs. 13 and 15: ch01:164; ch05:175 and :191; ch07:97 and :127; ch12:160; ch14:146; appendix_c:85; appendix_d:35, :36, :44, :55 and :56.

**Unpublished.** backmatter/bibliography.md has 2026b = Reasoning "[Book 2" and 2026c = Ethics "[Book 3". Swap the titles with the annotations: `(2026b). *Geometric Reasoning: From Search to Manifolds*. [Book 2:` -> `(2026b). *Geometric Ethics: The Mathematical Structure of Moral Reasoning*. [Book 2:`, and `(2026c) ... Geometric Ethics ... [Book 3:` -> `(2026c). *Geometric Reasoning: From Search to Manifolds*. [Book 3:`.

---

# Volume 11, Geometric AI

## manuscript/front_matter.md

**AI-1.** Lines 9-21, "Also in the Geometric Series", number the books 2 Reasoning, 3 Ethics, 4 Cognition, 5 Communication, 6 Medicine, 7 Education, 8 Economics and 9 Law. They use old titles ("Geometric Methods for Complex Systems", "Geometric Ethics: The Moral Manifold and the Geometry of Value"), and Gastronomy, Aesthetics and Observation are missing.
- Repair: replace lines 11-21 with titles only, in series order, each followed by " (2026)":
  1. *Geometric Methods*
  2. *Geometric Ethics*
  3. *Geometric Reasoning*
  4. *Geometric Economics*
  5. *Geometric Law*
  6. *Geometric Cognition*
  7. *Geometric Communication*
  8. *Geometric Medicine*
  9. *Geometric Education*
  10. *Geometric Politics*
  11. *Geometric AI*
  12. *Geometric Gastronomy*
  13. *Geometric Aesthetics*
  14. *Geometric Observation*
- Titles only sidestep the subtitle conflict. If the author wants subtitles, use the BOOK_CONFIGS ones.

**AI-2 (recorded Unresolved 12, now settled).** Line 91: `It has been developed across ten volumes of the Geometric Series, each applying` -> `It has been developed across the fourteen volumes of the Geometric Series, most of them applying`

**AI-3.** Line 131 (the count is recorded; "where it ends" is new):
- `grew into an eleven-volume investigation` -> `grew into a fourteen-volume investigation`
- `AI is where it ends, because AI is where it matters most.` -> `AI is the volume where it matters most.`

**AI-4 [AUTHOR].** Line 123, "This is the crown jewel. Every result from every volume converges here.", and README:18, "the volume where every result from every other domain converges". Volumes 12-14 do not feed this volume.
- Suggested: `This is where the results of the earlier volumes converge.`

**AI-5.** Line 69: `(Chapter 8) proves that structural containment on the value manifold blocks` -> `(Chapter 8) states, as a conditional theorem after *Geometric Ethics* Theorem 18.1, that structural containment on the value manifold blocks`

**AI-6.** Line 41: `(*Geometric Cognition*, Ch. 16)` -> `(*Geometric Cognition*, Chs. 7, 8 and 16)`. The framing result is in Cognition Ch. 7 and the 13.3σ sycophancy result in Ch. 8.

## part_i/

**AI-7 (X4).** ch01_scalar_alignment_trap.md:44:
- `The Scalar Irrecoverability Theorem, proved in *Geometric Reasoning* (Chapter 13) and extended` -> `The Scalar Irrecoverability Theorem, stated for continuous functions in *Geometric Ethics* (Theorem 15.1) and for weighted composites in *Geometric Reasoning* (Theorem 13.1, a conditional theorem), and extended`
- `for any scalar function defined on` -> `for any continuous scalar function defined on` (without continuity the statement is false)

**AI-8.** ch01:166, footnote 1: `was first proved in its general form in *Geometric Reasoning* (Bond, 2026c), Ch. 13.` -> `is stated in its general form in *Geometric Ethics* (Bond, 2026b), Theorem 15.1, and for weighted composite scores in *Geometric Reasoning* (Bond, 2026c), Theorem 13.1, a conditional theorem.`

**AI-9.** ch01:108 and ch10:22 (same repair): "across 25 subtasks. The composite scores ranged from 0.39 to 0.47 --- a spread of 0.08". Cognition ch16:14, :32-38 and :284 give 21 subtasks and 0.63 to 0.72, a span of 0.09.
- `25 subtasks` -> `21 subtasks`
- `ranged from 0.39 to 0.47 --- a spread of 0.08` -> `ranged from 0.63 to 0.72 --- a spread of 0.09`

**AI-10.** ch01:168, footnote 2: `reported in *Geometric Cognition* (Bond, 2026d), Ch. 16.` -> `reported in *Geometric Cognition* (Bond, 2026d), Ch. 7 (framing) and Ch. 8 (sycophancy).`

**AI-12 (recorded, now settled).** ch02_brief_history.md:161: `across nine domains` -> `across its other volumes`

**AI-13 (recorded, now settled).** ch03_case_for_geometric_alignment.md:
- :28: `The Geometric Series comprises ten volumes, each applying` -> `The Geometric Series comprises fourteen volumes, most of them applying`
- :86: `It draws on results reported in ten domains` -> `It draws on results reported in the other volumes`
- :126: `to ten domains` -> `to the domains of its volumes`

**AI-14 [AUTHOR].** ch03:16 (epigraph): `nine radar charts, one for each domain book in the Geometric Series` -> `radar charts, one for each domain book in the Geometric Series`

**AI-15 [AUTHOR].** ch03:84 and backmatter/table_of_contents.md:37: `3.4 What the Series Has Proved` -> `3.4 What the Series Reports`. The section's own first sentence calls the framework posited.

**AI-16 (recorded Unresolved 14, now settled by Communication ch13 Def. 13.4).** ch03:38: `The $D_4$ gauge theory of communicative acts identifies the symmetry group under which meaning-preserving transformations operate.` -> `The gauge theory of communicative acts identifies the symmetry group under which meaning-preserving transformations operate (for normative communication $V_4 \times U(1)_H$; that volume has withdrawn its earlier $D_4$).`

**AI-17.** ch03:88, "From Ethics": `The moral manifold's nine-dimensional structure has been compared against clinical ethics consultations, legal reasoning, and moral psychology experiments.` -> `The moral manifold's nine dimensions are a chart, not a measured basis: eight of the nine pass a frozen-null gate (rights does not), a tenth axis carries signal the nine miss, and the validated axes have effective rank 5.19 of 8.`

**AI-18 (X4).** ch03:90: `The Scalar Irrecoverability Theorem has been proved in its general form.` -> `The Scalar Irrecoverability Theorem is stated there, as a conditional theorem, for weighted composites of measured profiles (Theorem 13.1).`

**AI-19.** ch03:92, "From Cognition" (Cognition is [posited], debt ratio 1.0):
- `The 13.3-sigma sycophancy gradient demonstrates that the truth-approval distinction lies in the reward kernel.` -> `The 13.3-sigma sycophancy gradient is read as placing the truth-approval distinction in the reward kernel.`
- `The 8.9-sigma framing displacement demonstrates that gauge variance is a real, measured, statistically significant phenomenon.` -> `The 8.9-sigma framing displacement is a measured, statistically significant gauge violation.`

**AI-20.** ch03:94, "From Communication":
- (a) `The BIP cross-lingual experiments achieved 80% F1 on deontic classification with 1.2% residual language leakage, confirming that gauge-invariant representations are learnable.` -> `The BIP experiments report a mixed-language F1 of 80% and an output-layer language dependence of 1.2%, while internal layers still separate the languages (*Geometric Ethics*, Section 17.10); cross-lingual transfer reaches 44.5% F1 on four-way classification (Chapter 11). This suggests that gauge-invariant representations are learnable.`
- (b) `The hyperbolic embedding experiments confirmed that value hierarchies embed naturally in hyperbolic space.` -> `The hyperbolic embedding experiments, on coda and cuneiform taxonomies rather than values, gave mixed results: classical MDS preserved taxonomic distances better than the Poincaré embedding, and a hyperbolic classifier gained 1.5 points over the best Euclidean baseline (Section 5.5).`
- (c) `The 8.9-sigma framing effect was independently replicated in the communication domain.` -> `The communication volume reads the same Measuring AGI framing measurement (Social Cognition T5) as a gauge violation of communication (Section 14.2.2); it is not an independent replication.`

**AI-21 (recorded, now settled by Medicine ch12:173).** ch03:96: `The clinical Bond Index was successfully applied to ethics consultation data, demonstrating that tensor-valued evaluation is practical in real-world clinical settings.` -> `The clinical Bond Index is defined there and shown on a hypothetical case; it has not yet been computed from clinical data (Section 12.4).`

**AI-22.** ch03:98: `The educational Bond Index revealed systematic disparities in learning quality that GPA averages obscure.` -> `The educational Bond Index is illustrated, in a hypothetical study, revealing disparities that GPA averages obscure; no such study has been run (Section 13.5).` (Source: Education ch13:118.)

## part_ii/

**AI-23.** ch04_value_manifold.md:182: `(*Geometric Ethics*, Ch. 14)` -> `(*Geometric Ethics*, Ch. 8)`. Stratification is Ethics §8.2.

**AI-24.** ch04:258, footnote 2: `is detailed in *Geometric Ethics* (Bond, 2026b), Ch. 14. The stratification identifies four major strata (consequentialist, deontological, virtue, care) and the boundary strata connecting them.` -> `is detailed in *Geometric Ethics* (Bond, 2026b), Ch. 8, which reads the four traditions (consequentialist, deontological, virtue, care) by how each treats stratum boundaries; the four strata of Definition 4.3 are this volume's.`

**AI-25.** ch04:256, footnote 1:
- old: `Ch. 5, and compared against clinical ethics consultations (*Geometric Medicine*, Ch. 4), legal reasoning (*Geometric Law*, Ch. 5), and moral psychology experiments. The claim that nine dimensions are sufficient is empirical and open to revision (see Chapter 20, Open Questions).`
- new: `Ch. 5. That volume now treats the nine as a chart for coverage and audit, not a measured basis: eight of the nine pass a frozen-null gate (rights does not), a tenth axis (identity attack) carries signal the nine miss, and the validated axes have effective rank 5.19 of 8 (its Section 5.3). *Geometric Medicine* (Section 4.5.2) proposes testing the structure against coded ethics consultations; that has not been run. See Chapter 20, Open Questions.`

**AI-26 [AUTHOR].** ch04:228: `Probing experiments (*Geometric Cognition*, Ch. 15) are reported to show` -> `The illustrative running example of *Geometric Cognition* (Ch. 15), in which 12 principal components capture 87% of the variance, suggests`. The "approximately 11" figure has no source.

**AI-27.** ch04:260, footnote 3: `is established through the geometric interpretation` -> `is posited in the geometric interpretation`

**AI-28 (recorded, now settled).** ch05_reward_irrecoverability.md:148: `Empirically validated by the clinical Bond Index analysis.` -> `The clinical Bond Index that would test this has not yet been computed from clinical data (*Geometric Medicine*, Section 12.4).`

**AI-29.** ch05:150: `The kernel is five-dimensional, containing creativity, collaboration, critical thinking, curiosity, and persistence.` -> `The kernel is five-dimensional; the six dimensions are domain knowledge, procedural skill, metacognitive awareness, motivation and engagement, transfer ability, and creativity (*Geometric Education*, Section 4.2).`

**AI-30 [AUTHOR].** ch05:152: `the eight-dimensional communication quality space` -> `the communication quality space (at least four independent dimensions, *Geometric Communication* Section 15.2)`. The seven-item kernel is the author's choice.

**AI-31.** ch05:154: `**GDP Irrecoverability (*Geometric Economics*, Ch. 5).**` -> `**GDP Irrecoverability (*Geometric Economics*, Ch. 6).**`

**AI-32.** ch07_alignment_gauge_group.md:62: `perfectly invariant under English-Spanish-German-French translation.` -> `invariant across the eleven languages of the corpus, as one multilingual embedding model represents them (*Geometric Ethics*, Sections 17.3 and 17.7).`

**AI-33 [AUTHOR].** Epigraphs attributed to a volume in which their text does not appear:
- ch07:7-8 ("The laws of alignment should be the same for all descriptions." — *Geometric Ethics*)
- ch18_multi_agent.md:7-8 ("The whole is not the sum of its parts..." — *Geometric Economics*)
- ch08_no_escape.md:7 ("A cage made of rules can be escaped..."). Ethics' own sentence is "The cage is not made of rules. It is made of geometry — and geometry does not have loopholes."
- Repair: `> --- Andrew H. Bond, *Geometric Ethics*` (ch07) or `*Geometric Economics*` (ch18) -> `> --- Andrew H. Bond`. In ch08, alternatively use the Ethics sentence.

## part_iii/ and part_iv/

**AI-34.** ch09_bond_index_ai.md:197, the row `| Law | Geodesic deviation on the legal manifold | GL Ch. 11 |`, is wrong. Law's LBI is an invariance measure (Law ch05:321, ch00:39), and Law Ch. 11 has no Bond Index.
- Repair: delete the row; in the next paragraph delete `the legal outcome, `; at :202, `the same insights, five domains.` -> `the same insights, four domains.`

**AI-35.** ch09:202 and :208:
- `The clinical Bond Index's finding that` -> `The clinical Bond Index's illustrative result that`
- `The educational Bond Index's finding that` -> `The educational Bond Index's illustrative result that`
- `confirming the cross-domain applicability of tensor-valued evaluation` -> `illustrating how tensor-valued evaluation would apply across domains`

**AI-36.** ch10_cognitive_signatures.md:22: as AI-9.

**AI-37.** ch10:33: `Divided attention: $A_3 = 0.000$` -> `Divided attention: $A_4 = 0.000$` (Cognition ch16; this chapter's own line 47).

**AI-38 [AUTHOR] (R7).** ch10:32: `$T_2 = 0.958$`. Cognition ch16, the cited source, gives Claude T2 = 0.867; Reasoning ch10:51 gives 0.958.

**AI-39.** ch12_sycophancy_manifold.md:110: `(Ch. 13--15)` -> `(Ch. 13 and 15)`. Medicine Ch. 14 is held back.

**AI-40.** ch13_gauge_invariant_rewards.md:36: `The BIP experiments reported 80% F1 on cross-lingual deontic classification with 1.2% residual language leakage.` -> `The BIP experiments reported a mixed-language F1 of 80% and an output-layer language dependence of 1.2%; internal layers still separate the languages (*Geometric Ethics*, Section 17.10).`

## backmatter/, appendices/, README

**AI-41.** backmatter/bibliography.md:63-81 gives the wrong book numbers and old titles. Keep keys a-j and replace the text:

| Key | Replace with |
|---|---|
| 2026a | *Geometric Methods: Computational Modeling*. [Series Book 1.] |
| 2026b | *Geometric Ethics: The Mathematical Structure of Moral Reasoning*. [Series Book 2.] |
| 2026c | *Geometric Reasoning: From Search to Manifolds*. [Series Book 3.] |
| 2026d | *Geometric Cognition: The Mathematical Structure of Human and Artificial Thought*. [Series Book 6.] |
| 2026e | *Geometric Communication*. [Series Book 7.] |
| 2026f | *Geometric Medicine*. [Series Book 8.] |
| 2026g | *Geometric Education: Learning, Assessment, and the Topology of Understanding*. [Series Book 9.] |
| 2026h | *Geometric Economics*. [Series Book 4.] |
| 2026i | *Geometric Law: Symmetry, Invariance, and the Structure of Legal Reasoning*. [Series Book 5.] |
| 2026j | *Geometric Politics: Representation, Polarization, and the Topology of Democratic Choice*. [Series Book 10.] |

- Communication, Medicine and Economics get titles only, because their subtitles are in dispute (P1).
- appendices/appendix_a_math_prerequisites.md:5 and :116: `*Geometric Methods for Complex Systems*` -> `*Geometric Methods: Computational Modeling*`

**AI-42 (X1, X2) [AUTHOR for the status cell].** README:26 (Methods title). :39 `Published (v1.23)` -> `Published (v1.29)`. Add the Observation row after :50.

**AI-11 [AUTHOR] (P1).** README:1 and front_matter.md:1 and :21 give "Alignment, Safety, and the Manifold Structure of Machine Values", which matches books.json. BOOK_CONFIGS gives "...the Structure-Preserving Path to Superintelligence". One side must change.

**Unpublished.** OUTLINE.md still has D4 as the Hohfeldian group at :37, :68, :90, :109 and :217 (only :218 is recorded), "nine domains" at :155, and "Geometric Ethics Ch. 14" for stratification at :177.

---

# Volume 12, Geometric Gastronomy

**GAS-1 (X1).** README:19, and the mermaid node at :37.

**GAS-2 [AUTHOR] (X2).** README:77 `Published (v1.23)` -> `Published (v1.29)`. Add the Observation row after :88; the map (:41-55) has no Observation node.

**GAS-3 [AUTHOR] (P1).** README:1 has "...Flavor, Pairing, Cooking, and Culinary Navigation" (= books.json). BOOK_CONFIGS has "...Flavor, Pairing, and Culinary Harmony" (= OUTLINE.md:4, "Working subtitle").

**GAS-4.** Volume 6 comes before Volume 12, so these references do not point "forward":
- ch11:80 and ch13:100 "Connecting forward to Volume 6": drop "forward".
- ch14:54 "This connects forward to Volume 6".
- ch05:128 "Volume 6 ... will recognize".

**GAS-5 [AUTHOR].** Material is attributed to *Geometric Cognition* that is not in it. A search of Cognition ch00-17 found no hedonics, predictive coding, autoassociative recall, habituation, heat kernel or cross-modal treatment. The author decides whether to add the material to Cognition or to reword. Default rewordings:

| Location | Old | New |
|---|---|---|
| ch03:100 | `and the multi-modal hedonics of Volume 6: Geometric Cognition, where the same gradient-on-a-manifold structure governs preference far beyond the table.` | `and to Volume 6: *Geometric Cognition*, whose cognitive manifold could carry the same gradient-on-a-manifold structure for preference far beyond the table.` |
| ch05:128 | `and Volume 6: *Geometric Cognition* will recognize the anchor-and-moat structure of §5.3 as the same predictive-coding geometry that governs perception in every modality, flavor merely being the most delicious instance.` | `and whether the anchor-and-moat structure of §5.3 is a predictive-coding geometry shared by every modality is a question for Volume 6: *Geometric Cognition*, which does not yet treat it.` |
| ch12:103 | `The geometric model is the one developed for Volume 6, *Geometric Cognition*, which represents memory as` | `The geometric model is that of associative memory, which represents memory as` |
| ch12:107 | `exactly the autoassociative recall of Volume 6, with` | `exactly autoassociative recall, with` |
| ch12:113 | `connecting this volume to the associative memory of Volume 6: *Geometric Cognition*.` | `connecting this volume to associative memory, which Volume 6: *Geometric Cognition* does not yet treat.` |
| ch13:100 | `Connecting forward to Volume 6: Geometric Cognition, those same dynamics` | `Those same dynamics` |
| ch14:54 | `This connects forward to Volume 6, *Geometric Cognition*, where the same heat-kernel machinery describes the decay of attention and the spread of activation in semantic memory.` | (delete) |
| ch14:78 | `the flavor-space analogue of how Volume 6 models the consolidation of a learned skill.` | `the flavor-space analogue of the consolidation of a learned skill.` |
| ch14:92 | `are the heat-kernel and consolidation dynamics of *Geometric Cognition* (Volume 6);` | `are heat-kernel and consolidation dynamics of a kind *Geometric Cognition* (Volume 6) does not yet treat;` |
| ch17:77 | `is developed in Chapter 12 and, at the level of cross-modal cognition, in Volume 6: *Geometric Cognition*.` | `is developed in Chapter 12.` |

**GAS-6.** ch08:116: `resonating with the cultural attractors of *Geometric Economics* (Volume 4) and the learned manifolds` -> `resonating with the learned manifolds`. "Attractor" occurs nowhere in the Economics chapters.

**GAS-7 [AUTHOR].** ch14:92: "are the compressibility and structural-channel results of *Geometric Aesthetics* (Volume 13)".
- Source: the Aesthetics README says "the original compressibility formula failed and is reported as failed", and Aesthetics has no tempo or alignment result.
- Repair: `are the compressibility and structural-channel results of` -> `echo the structural-channel result of`

**GAS-8 [AUTHOR].** ch14:32: `exactly the separation that Volume 13, *Geometric Aesthetics*, found between structural form and its unfolding in music and narrative.` -> `a separation that Volume 13, *Geometric Aesthetics*, could test with its trajectory channel in music and narrative.`

---

# Volume 13, Geometric Aesthetics

**AES-1 [AUTHOR for map placement] (X1, X2).** README:96 `Published (v1.23)` -> `Published (v1.29)`. Add the Observation row after :107. Mermaid :56: `Geometric Methods<br/>in Computational Modeling` -> `Geometric Methods<br/>Computational Modeling`. "Volume 13" is correct.

**AES-2.** chapter-15, lines 129-131: `be any function mapping a $d$-dimensional aesthetic tensor to a scalar verdict` -> `be any continuous function mapping a $d$-dimensional aesthetic tensor to a scalar verdict`. The text says Ethics' Chapter 15 theorem "transfers ... unchanged", and that theorem has "any continuous function".

**AES-3 (recorded Unresolved 7, now settled by Ethics v1.29 §6).** chapter-17, line 205:
- `The moral manifold carries a nine-dimensional structure that *Geometric Ethics* reports as cross-culturally invariant at the level of dimensions (its Chapter 17 §17.3)` -> `The moral manifold carries a nine-dimensional chart whose obligation/permission axis *Geometric Ethics* reports as transferring across eleven languages in one multilingual embedding model (its Chapter 17 §17.3)`
- `(its Chapter 17 §17.2 and Chapter 20 §20.10)` -> `(its Chapter 17 §17.2)`. Ethics §20.10 holds the retrospective economic cases.

**AES-4 (recorded, now settled).** chapter-08, line 162: `and the 100% cross-linguistic transfer of the deontic axis in the BIP experiments` -> `and the 100% cross-linguistic transfer of the deontic axis in one multilingual embedding model (a preliminary result; *Geometric Ethics* §17.3, §17.7)`

**AES-5 [AUTHOR].** chapter-17, line 235: `The claim in *Geometric Ethics* (Chapter 4 §4.9) that meaning has geometric structure in a unified sense` -> `A claim that meaning has geometric structure in a unified sense, which *Geometric Ethics* does not make,`. Ethics §4.9 is "Gauge Theory: A Brief Introduction".

**AES-6.** appendices/appendix-a, line 81: `Where Ethics used synthetic scenario data and algebraic verification` -> `Where Ethics used an advice-column corpus, a multilingual corpus read through one embedding model, scenario tests of one language model, and algebraic verification`

**AES-7 [AUTHOR].** chapter-12, line 207: `## 12.8 Harm, Beauty, and the Conserved Quantity` -> `## 12.8 Harm, Beauty, and the Invariant Quantity`, keeping the `{#conserved-quantity}` anchor. Ethics v1.29 renamed its own §12.7 and §12.9 headings.

**AES-8 [AUTHOR wording].** erisml-lib tools/series-build/build.py, AESTHETICS_ABSTRACT (printed on the volume's contents page).
- Every number matches chapter 17: R=0.241 at 17σ, 28.3σ, ρ≈0.70, ρ=+0.126 at 8.4σ, ρ=−0.076 with p=5×10⁻³³.
- But the README lists "cross-modal sign flips" among the reasons the instrument is inadmissible and calls the surrounding theory posited, and chapter 12 §12.5 has not ruled out an encoder-level origin.
- Repair, lines 109-110: `The aesthetic geometry has directionality` / `that is modality-specific, and that directionality is measurable.` -> `The aesthetic geometry may have directionality that is modality-specific; whether the flip belongs to the works or to the encoders has not been ruled out (Chapter 12), and the book-length theory around these results is posited.`

**Checked and fine.** About 40 citations of Ethics Chs. 2, 4, 5-11, 13, 15-19, 26 and 30 match v1.29.

---

# Volume 14, Geometric Observation (geometric-observation)

**Checked and consistent:**
- Series identity: ch00_front_matter.md:4 "Volume 14 of the Geometric Series"; README:4 and :34 "the fourteenth work".
- The only other cross-volume citation is Appendix A:95 (O2).

**O1.** README.md:18-20: "The public index name is **DRI** (the "Bond Index" of early drafts, renamed — provenance footnoted in the sweep)."
- Source: the Bond Index was not renamed. It is still Ethics' invariance index (Ch. 18, v1.26). The DRI is a different index: Methods Ch. 10, the Decoder Robustness Index, 0.5·mean + 0.3·P75 + 0.2·P95. Observation's own Appendix A:95 and DOMAIN-GENERALITY-SWEEP.md:107-108 call the DRI the Bond Index's "descendant".
- Repair: `(the "Bond Index" of early drafts, renamed — provenance footnoted in the sweep)` -> `(the Decoder Robustness Index of *Geometric Methods*, Chapter 10; early drafts called it the "Bond Index", which is the different, earlier invariance index of *Geometric Ethics*; provenance footnoted in the sweep)`

**O2.** chapters/appendix_a_related_work.md:95-97: "The Bond Index (Geometric Ethics) and its bioacoustic descendant the Decoder Robustness Index (DRI): scoring a system by its distortion under read-relevant versus invariant transforms."
- Source: the Bond Index scores declared invariant re-descriptions only. The split into invariant and stress transforms belongs to the DRI (Methods 10.5 and 20.5.1: "The DRI scores these categories separately").
- Repair: `scoring a system by its distortion under read-relevant versus invariant transforms.` -> `the first scores a system by how far its evaluation moves under declared invariant re-descriptions, the second scores a decoder separately under invariant and stress (read-relevant) transforms (*Geometric Methods*, Chapter 10).`

**O3.** ch00_front_matter.md:18-19: "This is the meta-volume of the series: where the earlier books each posit one domain's geometry". Volume 1 is not a domain volume (Methods README: "the series' metrology discipline").
- Repair: `where the earlier books each posit one domain's geometry` -> `where the domain volumes each posit one domain's geometry`

**O4 [AUTHOR].** ch18_the_principle.md:3-4: "Every volume of this series ends by reducing its framework to a single sentence, and this one is no exception." Line 9: "The rest of this closing chapter".
- Methods ends with Ch. 22 (the read metric) and no one-sentence reduction.
- Ch. 18 is no longer this volume's closing chapter: Parts F and G (Chs. 19-29) follow it on the contents page.
- Repair: `Every volume of this series ends by reducing its framework to a single sentence, and` / `this one is no exception. Seventeen chapters,` -> `This chapter reduces the framework of the first seventeen chapters to a single sentence.` / `Seventeen chapters,`
- Repair: `The rest of this closing chapter says` -> `The rest of this chapter says`

**O5 [AUTHOR].** The house rule is said to be inherited from every volume. ch01_why_observation_needs_a_theory.md:150-152: "whose house rule — inherited from every volume of this series — is that *the book may not assert what the ledger cannot show*". ch15_registration_first.md:13: "inherited from every volume of the series".
- Only Ethics (ledger/), Cognition (claims/LEDGER.md) and this volume keep a claim ledger; Economics has a historical ledger under experiments/. The other ten volumes have none.
- The series-wide rule is stated in Methods Ch. 21 (line 118).
- Repair: ch01 `— inherited from every volume of this series —` -> `— the series' rule, stated in *Geometric Methods*, Chapter 21 —`
- Repair: ch15 `inherited from every volume of the series and` -> `the series' rule (*Geometric Methods*, Chapter 21),`
- The preface's "inherited from the series" (preface.md:170) can stand.

**O6 [AUTHOR].** ch17_open_problems_and_the_keystone_theorem.md:193-194: "settled enough to build the next volume on". Volume 14 is the last volume.
- Repair: `settled enough to build the` / `next volume on, in the precise sense` -> `settled enough to build` / `on, in the precise sense`
- Leave it if a further volume is planned.

**O7 [AUTHOR in part].** README.md:95: "The book (ch00–ch18 + appendices A–G)". The site publishes ch00-ch29.
- Repair: `ch00–ch18` -> `ch00–ch29`
- README:12-13 ("then Part A of the book — the instruments") and :95 ("**Part A = the canonical instrument docs**") disagree with the published contents page, where Part A is "The Problem" (ch01-03) and the instruments are Part D (ch10-13). Repair: `Part A` -> `Part D` in both.
- The front matter's own table of contents (ch00:160-200) uses a third scheme, Parts I-IX. Which scheme is canonical is the author's choice.

---

# Series-wide: the license paragraph in all fourteen READMEs

**S1 [AUTHOR].** Every README's license section has: "Every claim in this series carries a status label, such as `[proved]`, `[posited]` or `[open]`, graded against a claim ledger" (e.g. Methods README:73-76; 14 occurrences).
- Ten volumes keep no claim ledger (O5).
- Most chapters tag with `[Empirical.]`, `[Modeling Axiom.]` and `[Conditional Theorem.]`.
- Repair (each README): `Every claim in this series carries a status label, such as` -> `Claims in this series carry status labels, such as`, and `` `[proved]`, `[posited]` or `[open]`, graded against a claim ledger, `` -> `` `[proved]`, `[posited]` or `[open]` or a volume's own tags, graded against a claim ledger where the volume keeps one, ``

---

# The portal (erisml-lib)

## docs/books.json and docs/index.html (series cards): five subtitles disagree with BOOK_CONFIGS

**P1 [AUTHOR for AI; X3].** At run time, assets/js/series.js:96 renders the books.json subtitles into the card grid, and sitebar.js:193 uses them as tooltips. index.html carries static fallback copies. build.py prints the BOOK_CONFIGS subtitle on every page of the volume.

| Volume | books.json and index.html fallback | build.py BOOK_CONFIGS | The volume itself |
|---|---|---|---|
| 4 Economics | "Decision Manifolds, the Bond Geodesic Equilibrium, and the Irrecoverable Geometry of Markets" (index.html:1503) | "Decision Manifolds, Equilibria, and the Geometry of Markets" | published ch00:1 = build.py; README:1 = books.json |
| 7 Communication | "Signal, Symmetry, and the Geometry of Meaning" (:1521) | "Language, Signal, and the Topology of Meaning" | front_matter.md:7 (unpublished) = build.py; README:1 = books.json |
| 8 Medicine | "Clinical Reasoning, Allocation, and the Mathematics of Moral Injury" (:1527) | "Clinical Reasoning, Triage, and the Ethics of Allocation" | front_matter.md:7 (unpublished) = build.py; README:1 = books.json |
| 11 AI | "Alignment, Safety, and the Manifold Structure of Machine Values" (:1545) | "Alignment, Safety, and the Structure-Preserving Path to Superintelligence" | **published** front_matter.md:1 and :21 = books.json; README:1 = books.json |
| 12 Gastronomy | "The Mathematical Structure of Flavor, Pairing, Cooking, and Culinary Navigation" (:1551) | "The Mathematical Structure of Flavor, Pairing, and Culinary Harmony" | no subtitle in chapters; OUTLINE.md:4 "Working subtitle" = build.py; README:1 = books.json |

The manifest check compares number and title only (build.py:301-304), so the drift passes the build.

Repair, taking build.py as authoritative: set the five `subtitle` values in books.json, and the five fallback lines of index.html, to the build.py strings. The READMEs' H1s and series tables follow.

For AI the published front matter sides with books.json against build.py. Either build.py or the front matter and README must change; that is the author's choice.

Optional guard: also compare `subtitle` in check_manifest (build.py:293).

## docs/index.html: the Geometric Ethics sections

**P2.** Line 811 (Key Results, Thm 9.2 Structured Pluralism): `Assumes: BIP, Def 4.5`.
- Source: Ethics Theorem 9.2 is "[Conditional on Def. A.1 and Def. 9.1]"; its Appendix F row gives "Thm 9.1". Def 4.5 is the Riemann curvature tensor.
- Repair: `Assumes: BIP, Def 4.5` -> `Assumes: Def A.1, Def 9.1`

**P3.** Lines 815-816: badge "Thm 12.1", title "Invariance of Harm Accounting".
- Source: Ethics Theorem 12.1 is "Moral Noether's Theorem" [Theorem (conditional on BIP)].
- Repair: `<h3>Invariance of Harm Accounting</h3>` -> `<h3>Moral Noether's Theorem: the Invariance of Harm Accounting</h3>`

**P4.** Line 631: `<h4>Noether's Theorem for Ethics</h4>`.
- Source: Ch. 12 is "Noether-Style Reasoning for Ethics — Symmetry, Invariance, and Harm Accounting".
- Repair: -> `<h4>Noether-Style Reasoning for Ethics</h4>`

**P5.** Line 120 (hero stat "7 Theorems") and line 803 ("Seven central theorems, each conditional on stated assumptions").
- The seven cards include Posit 12.3, which the card itself says is posited, and Prop 15.3, which Appendix F lists as Proved, pure math.
- Repair, line 120: `Theorems` -> `Key Results`
- Repair, line 803: -> `Seven central results, each with its stated assumptions`

**P6.** Line 866: "Nine established domains, each with worked examples and falsifiable predictions".
- Source: v1.29 says the 149 statements of the domain chapters are untagged (all but one), the ledger classes them exploratory, and the Ch. 20 and 25 readings are retrospective. "Established" reads as a grade.
- Repair: -> `Nine domains with their own formal traditions, each with worked examples and stated predictions`

**P7 [AUTHOR in part].** Line 1626: "Submit your Dear Ethicist session data. Every game contributes to the Bell test and moral structure research."
- Source: the Bell prediction was tested and not found (:1425, :1450; Ethics §17.8 table, N=9,600, all |S| ≤ 2). The same page says the game "does not send your answers anywhere" (:1456).
- Repair: -> `Submit your Dear Ethicist session data. The game sends nothing by itself; a session you submit adds to the study of Hohfeldian structure in human judgments.`
- [AUTHOR] erisml-lib docs/BOND_INDEX.md:133 records that `sqnd-probe`, the Dear Ethicist game, "still implements D4". If the embedded game (assets/js/dear-ethicist-game.js) scores D4, then section XII's subtitle and line 1456 ("measures the same Hohfeldian structure") advertise the withdrawn group. I did not check the game code.

**P8 [AUTHOR].** Line 1649: "The methodology is inductive, not axiomatic. The structures were found in data and then formalized."
- Source: Ethics README: everything beyond the gated measurements and machine-checked results "is *posited* theory". v1.28: the metric is untested.
- Repair: `The structures were found in data and then formalized.` -> `Some structures were suggested by data and then formalized; the rest are posited.`

**P9 [AUTHOR in part].** assets/js/visualizations.js:883, the "CHSH Inequality" concept card on the landing page: "...Violation indicates that moral cognition has genuinely quantum-like structure. The Dear Ethicist game is designed to test this empirically." The card omits the result.
- Repair: `The Dear Ethicist game is designed to test this empirically.` -> `The book's test found no violation: |S| ≤ 2 in all 9,600 trials (Geometric Ethics, Section 17.8).`
- Line 879 (interference "matches observed phenomena in moral psychology") is about the human literature. [AUTHOR] whether to add that the book's own interference test found none (index.html:1445).

## docs/site/index.html: an old copy of the Ethics landing page, still served at erisml.org/site/

**P10 [AUTHOR].** The file is the pre-v1.26 landing page; it was last touched in ed2ada4 ("old Ethics landing page links fixed"). It still says:
- lines 275-276: the Bond Index is a "Quantitative alignment score for AI systems" and a "Scalar measure of structural × invariance × residue compliance" (wording v1.26 removed);
- line 1030: harm is "conserved";
- line 1287: "the full D4 machinery is included so the posited extension stays testable" (the machinery was removed in df00fc5);
- line 1305: the Bond Index LLM evaluation will "Measure structural compliance, invariance, and residue";
- line 1439: "Your moral judgments help test whether ethics has quantum structure";
- line 1483: "contributes to the Bell test";
- P2, P5, P6 and P8 again, at lines 807, 116/799, 862 and 1506.

Repair, author's choice:
- (a) replace the file with a redirect: `<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../index.html"><link rel="canonical" href="../index.html"><title>Geometric Ethics</title>`;
- (b) port the main page's current text into each line above.

(a) is the smaller change and removes every stale statement at once.

## docs/guides/math-primer.html

**P11 [AUTHOR wording].** Line 105 (blockquote): "Beauty is compressibility. Meaning has holonomy." Line 107: "Those two slogans are the two lenses pointed at art and at language."
- Source: the Aesthetics README (:8-10) says "the original compressibility formula failed and is reported as failed"; Communication is a posited framework.
- Repair, line 105: -> `Is beauty compressibility? Does meaning have holonomy?`
- Repair, line 107: `Those two slogans are the two lenses pointed at art and at language.` -> `Those two questions point the two lenses at art and at language (the aesthetics volume reports that its first compressibility formula failed).`

## tools/series-build/README.md

**P12.** Line 3: "Canonical tooling for the thirteen Geometric Series volumes served at https://erisml.org/".
- Fourteen volumes are served; thirteen of them are built by this kit.
- Repair: `the thirteen Geometric Series volumes served at` -> `the thirteen kit-built volumes of the fourteen Geometric Series volumes served at`

## Portal: checked and consistent

- index.html:1473 "Fourteen volumes", Books 1-14 numbers and titles, and sitebar.js:4 "the fourteen volumes".
- books.json numbers, titles, slugs and hrefs, against BOOK_CONFIGS plus Ethics.
- The landing page's Ethics sections otherwise match v1.29: nine dimensions as a chart (:292), Bond Index definition (:280), V4 with D4 withdrawn (:824, :1288), Bell, order-effect and interference status (:1425-1450), DEME (:1138), and the list of withdrawn results (:1649, second sentence).
- math-primer Trail three against Observation ch05, ch07, ch24-29 and Methods Ch. 22.
- The encyclopedia has 13 volume files. Observation's entries are built from its ledger (encyclopedia/README.md:305-312; build_site.py:419).
- Every `standing` matches its volume's README status block as it stands. I checked all 13, plus the spots they cite: Medicine §18.9, Education §18.1 and §16.3, Politics' District 7, AI's ARIA, Reasoning's five-model benchmark, and Methods §21.8.
- "Encyclopedia · 595 entries" = 310 + 285, correct.

---

# Within-volume items noticed in passing (not counted; outside the cross-volume brief)

- **Ethics, Part VI, "Calibration of the Covariance Matrix".** "The covariance matrix is not assumed; it is empirically estimated, cross-validated, and falsifiable". This contradicts v1.28 §8.10a: no measurement shows a metric predicting judgements, and the one registered test was void.
- **Ethics.** DEME is expanded two ways: "Distributed Ethical Monitoring Engine" (Ch. 1) and "Democratically Governed Ethics Module Engine" (bibliography 2026d and elsewhere).
- **Medicine ch12 summary.** It still says the case study "demonstrates ... revealing a 2.31x disparity", although §12.4 is marked illustrative.
- **Communication ch18:339.** The tools "have confirmed that the structure exists ... gauge-invariant", against its README's "posited".
- **Cognition.** Claude's divided attention is 0.571 at ch01:77 and 0.000 in the ch16 table.
- **Observation.** The front matter's table of contents uses Parts I-IX, the published contents page (BOOK_CONFIGS) uses Parts A-G, ch12:123 says "Part V puts the whole apparatus on trial", and the README uses Part A for the instruments.
- **Reasoning.** ch10:407 and ch11:315 refer to "the gauge violation tensor of Chapter 8", which Chapter 8 does not define. This underlies Economics E6 and Law L8.
