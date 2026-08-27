# LBI-3 Prior-Art Sweep — recon grade

**Status:** recon-grade, 2026-08-27. Anchors marked ✔ were verified
against sources today (bibliographic facts and framing); anchors
marked ⧗ are from-memory and owe quote-verification before seal
(LBI-1 standard: every load-bearing characterization quote-verified
pre-seal). No bar or claim in the outline binds until the ⧗ set is
cleared.

**The four claimed novelty axes under test** (from `OUTLINE.md`):
(i) jurisdictional legal doctrine compiled to machine-checkable
per-decision gates; (ii) ethical-theory-grounded projections rather
than metric panels; (iii) per-decision hashed normative-provenance
graphs; (iv) principled non-aggregation formally tied to the
fairness-impossibility structure, with the sealed prediction that
framework conflict concentrates where the theorem bites.

---

## S1 — Fairness toolkits and multi-metric auditing

- ✔ **Aequitas** (Saleiro et al.; audit toolkit + "fairness tree"
  guiding metric choice), **AIF360** (Bellamy et al., IBM; metric
  battery + mitigation algorithms), **Fairlearn** (Microsoft),
  **OxonFair** (2024). ⧗ on exact framings.
- **Concession:** multi-metric reporting without aggregation is
  ESTABLISHED tooling practice. The outline already concedes this;
  the sweep confirms the concession is mandatory. None of these
  encode jurisdictional doctrine, ground metrics in ethical theory,
  or emit per-decision normative provenance.

## S2 — Law as code

- ✔ **Catala** (Merigoux, Chataing, Protzenko, ICFP/PACMPL 2021):
  compiles statutory law (US IRC §121, French family benefits) to
  correct-by-construction executable specifications; found a bug in
  the official French benefits implementation. The strongest
  existence proof that legal text compiles.
- ✔ **LegalRuleML Core v1.0** (OASIS Standard, Aug 2021;
  Governatori co-chair): XML standard for legal normative rules with
  deontic modalities, defeasibility, penalty/reparation, temporal
  validity, jurisdiction metadata.
- ⧗ Rules-as-Code movement (OECD/NZ Better Rules); Lawsky's tax
  formalization; PROLEG.
- **Concession:** "law compiles to code" is taken, at standards
  level and at PL-research level, for STATUTORY/administrative law.
- **Unoccupied residue:** compiling *judicial doctrine governing RAI
  use* (the *Loomis* warning set, contestability, sex-use policy)
  into gates evaluated per scored decision of a deployed instrument,
  on a real corpus. Catala compiles the tax code; nobody has
  compiled *Loomis*.

## S3 — Ethical governors and machine-ethics architectures

- ✔ **Arkin's ethical governor** (GIT-GVU-07-11; *Governing Lethal
  Behavior in Autonomous Robots*): an architectural component that
  reviews and suppresses/permits a system's proposed action against
  LOW/ROE constraint sets before enactment. The direct ancestor of
  the "governance layer wrapped around a decision system" shape.
- ⧗ Dennis/Fisher/Slavkovik/Webster (formal verification of ethical
  choices); GenEth (Anderson & Anderson); Bringsjord's deontic
  cognitive event calculus; Winfield consequence engines.
- **Concession:** the wrap-the-system ethical-governor concept is
  20 years old; we inherit, not invent, the shape. Differentiators:
  those governors enforce a SINGLE codified constraint set; none is
  framework-pluralist, none targets RAIs, none ties conflict to
  impossibility results.

## S4 — Value pluralism and moral uncertainty (narrows axis ii)

- ✔ **MacAskill, Bykvist & Ord, *Moral Uncertainty*** (OUP 2020):
  the decision-under-moral-uncertainty program (MEC, ordinal/cardinal
  regimes, social-choice analogy). ✔ **Newberry & Ord**, the
  parliamentary approach (Bostrom's moral parliament).
- ✔ **Value Kaleidoscope / ValuePrism** (Sorensen et al., AAAI 2024
  oral): a model that generates and assesses *pluralistic* values,
  rights, and duties per situation, explicitly refusing to wash out
  value conflicts; ⧗ **A Roadmap to Pluralistic Alignment**
  (Sorensen et al., ICML 2024).
- **Narrowing:** "AI systems should surface plural values in
  tension rather than average them" is now an active, named research
  line. Axis (ii) must be positioned as: theory-grounded projections
  *of a typed decision graph* (deontic gates with SMT
  universalizability, harm tensor, care/virtue) applied to
  *legally-situated RAI decisions*, with the impossibility theorem —
  not general value pluralism — as the reason aggregation is
  forbidden. The moral-uncertainty literature mostly seeks a
  RESOLUTION rule (MEC, parliament); our posture (surface, never
  resolve; the resolution is institutionally the court's) is closer
  to Value Kaleidoscope's but grounded in doctrine, not crowdsourced
  values.

## S5 — Formal methods for fairness (bounds the SMT claim)

- ✔ **FairSquare** (Albarghouthi, D'Antoni, Drews, Nori, OOPSLA
  2017): first automated verifier certifying probabilistic fairness
  properties of decision programs (SMT/quantifier elimination).
  ⧗ Justicia; runtime fairness monitoring (2023–25 arXiv line).
- **Concession:** SMT applied to fairness properties is taken. Our
  SMT use is different in kind (Z3 discharge of universalizability
  gates over maxims, not verification of probabilistic fairness),
  and the paper must say so explicitly to avoid an overclaim.

## S6 — Accountability and provenance (narrows axis iii)

- ✔ **Kroll, Huey, Barocas, Felten, Reidenberg, Robinson & Yu,
  "Accountable Algorithms"** (165 U. Pa. L. Rev. 633 (2017)):
  cryptographic commitments + verifiable computation to establish
  *procedural regularity* of automated decisions — the canonical
  "hashes meet due process" work.
- ✔ **SMACTR** (Raji et al., FAT* 2020): end-to-end internal audit
  framework with defined, documented audit artifacts. ⧗ Model
  cards (Mitchell et al.), datasheets (Gebru et al.), FactSheets.
- **Narrowing:** hashed/committed artifacts for algorithmic
  accountability are established. Axis (iii) must be framed as the
  *object* being new, not the hashing: Kroll et al. commit to the
  COMPUTATION (same rules applied to everyone); we commit to the
  NORMATIVE EVALUATION (a typed MoralGraph per decision recording
  stakeholders, acts, imposed harms, gate outcomes, and framework
  verdicts — the thing a court would actually want to inspect).
  Position as the normative-provenance complement to Kroll.

## S7 — The law-and-fairness bridge (the foil)

- ✔ **Wachter, Mittelstadt & Russell, "Why Fairness Cannot Be
  Automated"** (CLSR 2021): EU non-discrimination law is contextual
  by design and incompatible with static metric testing; proposes
  Conditional Demographic Disparity as the single summary statistic
  courts could use. **The instructive OPPOSITE:** they respond to
  legal contextuality by choosing one legally-grounded statistic;
  we respond to impossibility by refusing the choice and surfacing
  the conflict for the institution that owns it. This contrast is a
  section of the paper, not a footnote.
- ⧗ Huq (racial equity), Mayson (*Bias In, Bias Out*), Starr,
  Citron (technological due process), *Loomis* notes (131 Harv. L.
  Rev. 1530); ✔ "Code is law: how COMPAS affects the way the
  judiciary handles the risk of recidivism" (AI & Law, 2024) —
  socio-legal background on judicial COMPAS handling.

## S8 — Runtime governance of agentic AI (NEW; narrows axis i)

- ✔ (existence) **"Deontic Policies for Runtime Governance of
  Agentic AI Systems"** (arXiv 2606.19464; AgenticRei — Rei-based
  deontic policy language, OWL, runtime logic engine) and **"Policy
  Cards: Machine-Readable Runtime Governance for Autonomous AI
  Agents"** (arXiv 2510.24383; allow/deny/require_escalation rules
  tied to evidence fields). ⧗ full reads owed — these are recent
  and must be engaged carefully.
- **Narrowing:** "machine-readable normative constraints enforced at
  runtime over an AI system" is now an active 2025–26 line for
  *agentic AI generally*. Axis (i)'s claim survives only in its
  specific form: constraints sourced from *adjudicated doctrine*
  (not operator policy), targeting *risk-assessment instruments*
  (not LLM agents), evaluated on a *real decision corpus* with
  sealed predictions. The generic form is conceded.

---

## Verdict table (axes → status after sweep)

| Axis | Status | Surviving claim |
|---|---|---|
| (i) doctrine → gates | **narrowed** (S2 statutory law-as-code; S8 generic runtime policy) | *judicial RAI doctrine* (Loomis set) compiled to per-decision gates, evaluated on a real corpus — unoccupied |
| (ii) theory-grounded projections | **narrowed** (S4 pluralistic-values line) | pluralist projections *of typed legal-decision graphs*, aggregation forbidden *because of the impossibility theorem*, resolution assigned to the court — unoccupied |
| (iii) hashed normative provenance | **narrowed** (S6 Kroll; SMACTR) | provenance of the *normative evaluation* (MoralGraph), complement to Kroll's procedural regularity — unoccupied |
| (iv) conflict tracks the theorem (P2) | **unoccupied** | no found work predicts *where* framework conflict concentrates from the impossibility structure and tests it on a real RAI corpus — this is the load-bearing novel claim; protect it |
| "multi-metric, no aggregation" | **conceded** (S1) | none — never claim it |
| "SMT for fairness" | **conceded** (S5) | none — SMT is for universalizability gates only, say so |
| "ethical governor shape" | **conceded** (S3) | none — inherit and cite Arkin |

## Implications for OUTLINE.md

1. Positioning section holds, with two required additions: the
   moral-uncertainty/pluralistic-alignment line (S4) and the 2025–26
   agentic runtime-governance line (S8). Neither occupies the
   conjunction; both narrow individual axes and MUST be cited.
2. P2 (conflict concentrates where the theorem bites) is confirmed
   as the paper's center of gravity — the one claim with no
   neighbor. Design effort and statistical power go there.
3. Wachter et al. get a dedicated contrast section (choose-a-
   statistic vs. surface-the-conflict) — it is the clearest way to
   explain what pluralist governance IS.
4. Pre-seal obligations: clear the ⧗ ledger (full reads of
   2606.19464 and 2510.24383 first — most recent, highest collision
   risk); re-run this sweep's searches at seal time (the S8 line is
   moving).
