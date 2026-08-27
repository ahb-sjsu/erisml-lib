# LBI-3: Governing the Ungovernable Metric — Framework-Pluralist
Runtime Governance for Risk-Assessment Instruments

**Follow-up to:** *The Legal Bond Index: A Matched-Neighbourhood
Diagnostic of Algorithmic Disparity, Applied to COMPAS* (J. Sci. L.,
accepted; LBI-1) and the planned human-baseline audit (LBI-2,
`../lbi2-judiciary/`). LBI-1 measures like-cases-alike violations;
LBI-2 measures the human baseline; **LBI-3 asks what a decision
system should DO with the impossibility results and the diagnostics —
and answers with an architecture, not a metric.**
**Target venue:** Journal of Science and Law.
**Stack:** `erisml-compiler` (MoralGraph + framework projections,
PyPI, DOI 10.5281/zenodo.20659432), `erisml-lib` (MoralVector,
I-EIP), the LBI-1 audit pipeline (`revision2_analysis.py`, archived).
**Status:** outline v0.1, 2026-08-27. Nothing computed; all
predictions to be sealed before any estimator touches the data
(house rule, and the paper's own methodology).

---

## Working titles (descending preference)

1. *When Fairness Metrics Disagree, Don't Aggregate: Framework-Pluralist
   Governance for Risk-Assessment Instruments*
2. *Compiling the Law into the Loop: Machine-Checkable Jurisdictional
   Constraints for Algorithmic Risk Assessment*
3. *The Impossibility Theorem as a Design Requirement*

## Thesis (one paragraph)

Chouldechova–Kleinberg established that the standard fairness
criteria are mutually incompatible under unequal base rates; the
field's response has been a decade of arguing which criterion should
win. This paper takes the impossibility as a **design requirement**:
a governance system for risk-assessment instruments (RAIs) must be
*framework-pluralist* — it must evaluate every scored decision under
multiple ethical frameworks, surface their disagreements as
first-class outputs, and never collapse them into a single scalar
verdict, because the theorem guarantees any such scalar silently
takes a side. We demonstrate a working reference architecture: each
decision record (inputs, score, threshold action, context) compiles
into a typed, hash-carrying MoralGraph; jurisdictional legal
constraints (the *Loomis* warning set, sex-use policy, contestability
requirements) compile into categorical deontic gates checked per
decision (SMT-backed where universalizability is invoked); a
consequentialist projection carries the per-stakeholder harm tensor
and the LBI/metric panel; and the system's primary governance output
is the **conflict record** — which frameworks disagreed, where, and
for whom. Evaluated end-to-end on the public COMPAS corpus.

## Positioning and prior art (honesty first)

- **Multi-metric reporting is not novel** — Aequitas, AIF360, and
  Fairlearn all report metric panels without aggregation. Claimed
  novelty is NOT "many metrics"; it is (i) **compilation of
  jurisdiction-specific legal constraints into machine-checkable
  categorical gates** (doctrine as executable policy, per decision,
  with *Loomis* as the worked example); (ii) projections grounded in
  **ethical theory** (deontic gates, harm tensor, care/virtue
  readings) rather than a metric zoo, giving disagreements
  *interpretable* normative content; (iii) **per-decision hashed
  MoralGraph provenance** — every verdict traceable to a typed graph
  a court or auditor can inspect; (iv) the formal tie between
  surfaced conflict and the impossibility structure (prediction P2
  below): conflict is not noise, it concentrates exactly where the
  theorem says no scalar can be right.
- Prior art: see `PRIOR-ART-SWEEP.md` (recon-grade, 2026-08-27).
  Sweep verdict: axes (i)–(iii) each NARROWED by a named neighbor
  (Catala/LegalRuleML for law-as-code; the moral-uncertainty and
  pluralistic-alignment lines for surfaced value conflict; Kroll et
  al. for hashed accountability; the 2025–26 agentic
  runtime-governance line for generic machine-readable policy) and
  survive only in their doctrine-specific, RAI-specific forms; axis
  (iv) — conflict concentrates where the impossibility theorem
  bites, tested on a real corpus — found UNOCCUPIED and is the
  paper's center of gravity. Wachter–Mittelstadt–Russell is the
  designated contrast (choose-a-statistic vs. surface-the-conflict).
  ⧗-marked quote-verification owed pre-seal.

## Research questions and sealed endpoints

- **RQ1 (expressiveness).** Can the operative constraints a
  jurisdiction actually imposes on RAI use be encoded as gates
  without per-case ad-hoc logic? Suite drafted in
  `CONSTRAINT-SUITE.md`: 7 gates (D1 required warnings, D2
  not-determinative, D3 group-to-individual inference, D4 population
  validation, D5 purpose fit, D6 contestability, D7 attribute
  policy), carried by a new `DoctrinalProjection` alongside — not
  inside — the four ethical-theory projections, parameterized by a
  data-only `JurisdictionProfile`. Endpoint E1: 31/31 on a
  preregistered constructed-vector set **and** zero vector- or
  case-specific identifiers in the gate module (grep-checked) — the
  second half is what actually tests "no ad-hoc logic".
- **RQ1b (auditability gap).** Endpoint E4, predicted in advance:
  **4 of 7** doctrinal gates are `undetermined` on the public corpus,
  because the ProPublica file contains no PSI text, warning records,
  notice records, or contest records. The claim this licenses is not
  "COMPAS violated *Loomis*" but *"the public record cannot answer
  whether it did"* — a transparency deficit measured rather than
  asserted. Declared now so it cannot later be presented as a
  discovery.
- **RQ2 status: HALTED at the instrument** — see
  [`FINDING-INSTRUMENT-01.md`](FINDING-INSTRUMENT-01.md). Five of the
  ten EM-DAG modules are gated on English keywords in free-text fact
  descriptions, so on structured decision records those channels are
  dark and the consequentialist projection returns `indeterminate`
  throughout. P2 has **not** been tested and no conflict number
  exists. The vacuity kill condition is NOT triggered — that would
  require the projections to run and agree/disagree degenerately.
  Path forward: structured-field readers specified and frozen first,
  then pilots (ordering is the point).
- **RQ2 (conflict tracks the theorem).** On the real COMPAS corpus
  (LBI-1 filter, n = 5,278), does cross-framework verdict
  disagreement concentrate where the impossibility bites? Sealed
  prediction P2: disagreement rate between the deontic and
  consequentialist projections is higher (a) at ProPublica's
  medium-or-high threshold than at the high threshold, and (b) among
  cross-group matched pairs flagged by LBI than among unflagged
  pairs — i.e., the conflict record and the LBI diagnostic agree on
  WHERE the hard cases live, from independent machinery. Bars from
  ≥2 disclosed calibration draws before seal (across-draw rule).
- **RQ3 (audit integration).** One machine-readable governance report
  per decision and per corpus: gates, projections, LBI panel, metric
  panel, conflict record, graph hashes. Endpoint E3: bitwise
  reproducibility from the public file (seeded, hashed, CI-checked);
  report schema published.

**Kill conditions (recorded regardless):** constraints not encodable
without ad-hoc case logic (RQ1 dead — the compiler is not expressive
enough, reported as the finding); degenerate conflict behaviour
(projections always agree or always disagree — the pluralism is
vacuous, reported); P2 fails (conflict does not track the
impossibility structure — the interpretability claim falls, reported).

## Evidence-discipline labels (per the JI campaign-brief convention)

| Claim | Class |
|---|---|
| erisml-compiler: MoralGraph, 4 projections, deontic gates incl. `legitimate_authority`/`valid_consent`, Z3 universalizability, no-aggregation on conflict | **A** — implemented, 462+ tests, PyPI/Zenodo |
| LBI-1 pipeline and COMPAS results (1.041–1.069 curve; 1.092 at threshold) | **A/B** — archived, independently re-executed (Zenodo v2.1) |
| Chouldechova–Kleinberg incompatibility | **C** — established literature (Lean-verified corollary in LBI-1 archive) |
| "Legal doctrine can compile to categorical gates" | **E** — this paper's RQ1 |
| "Conflict concentrates where the theorem bites" | **E** — this paper's RQ2/P2 |
| Deployment fitness for real defendants | **out of scope — no claim** |

## Design sketch

Public COMPAS file → LBI-1 filter (n = 5,278) → per-defendant
decision record → `erisml-compiler` MoralGraph (stakeholders:
defendant, court, public; act: risk classification at declared
threshold; facts: features, group, score; norms: encoded
jurisdictional constraints) → projections + gates → per-decision
verdict vector + corpus-level conflict maps → governance report.
LBI and the standard metric panel computed by the archived LBI-1
code, imported unchanged. Calibration draws on seeded synthetic
score families (LBI-1's validation suite) before any sealed run on
the real corpus.

## Scope guards (LBI-1's restraint, inherited verbatim in spirit)

Reference architecture with measured properties on public data. NOT
a validated decision system; no claim about real deployments; no
modification of any vendor instrument; conditional throughout on the
measured predictors. The paper's product is the architecture plus
the sealed measurements of its behaviour.

## Disclosure (baked in from day zero)

The author consults for Justice Innovations (JI) and may acquire an
equity interest; JI has a working relationship with the target
journal, including board-level personnel; the erisml stack is the
author's own and plausibly commercializable in this domain. The
competing-interests statement will disclose all three, and the
relationship has been disclosed to the editors. JI funding, if any,
will be acknowledged with a no-role statement or declined.

## Artifacts and next steps

Artifacts: compiler + pipeline versions pinned; per-run JSON with
graph hashes; Zenodo deposit; Lean formalization candidate (the
gate-conflict/impossibility tie, if it crystallizes as algebra).
Next: ~~(1) prior-art sweep~~ done (`PRIOR-ART-SWEEP.md`,
recon-grade; ⧗ ledger open); ~~(2) constraint-suite draft + vector
set~~ drafted (`CONSTRAINT-SUITE.md` v0.1; ⧗ doctrine verification
and legal review open); (3) implement `DoctrinalProjection` + the
31-vector set, run it (unsealed, mechanics only); (4) two disclosed
calibration draws for the P2 bars on synthetic score families;
(5) seal `PREREG.md` in this folder; (6) sealed run on the real
corpus; (7) write. LBI-2 proceeds independently; nothing here blocks
on it.

**Pre-seal blockers (both papers' hard-won lessons):** the ⧗ doctrine
quote-verification (LBI-1's r3 caught a *Loomis* mischaracterization
in an accepted manuscript — second-hand holdings are not trusted);
legal review of the gate encodings by a lawyer; and full reads of the
two 2025–26 agentic runtime-governance papers, whose line is still
moving.
