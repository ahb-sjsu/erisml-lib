# Campaign Plan — The Mathematics of Distributed Decision-Making

**Refactored from:** the research campaign brief by Kim Baley
(Justice Innovations), 2026-08-22
(`source/ErisML_Eagleman_Research_Campaign_10of10.docx`).
**Mathematical framework:** ErisML-Lib — Andrew Bond.
**Prospective scientific collaborator:** David Eagleman — Stanford
University / Center for Science and Law.
**Posture:** research-development plan. Not a claim of
neuroscientific validation, clinical utility, or biological mechanism.

---

## 1. Campaign thesis

Eagleman's neuroscience describes human choice as the output of
interacting and competing processes ("team of rivals"). ErisML-Lib
independently provides mathematical machinery for order sensitivity,
context dependence, higher-order interaction, temporal evolution,
distributed contribution, and internal-state invariance. This campaign
tests whether those structures can **predict human behavior** and,
only if warranted, correspond to neural dynamics.

The scientifically interesting question is not whether the mathematics
*resembles* Eagleman's language; it is whether the mathematics
*predicts human decision trajectories better than established
alternatives*. The campaign succeeds only if ErisML moves from
describing observed effects to making reliable, preregistered,
out-of-sample predictions that survive comparison with established
cognitive models. It is explicitly designed so that ErisML **loses**
if it does not add value.

## 2. Principal research question

> Can mathematical tools implemented in ErisML-Lib characterize and
> predict measurable properties of human decision-making that arise
> when multiple cognitive or evaluative processes interact?

Operationally: do human decisions exhibit reproducible order
sensitivity, context dependence, higher-order interaction, temporal
path dependence, and distributed contribution patterns that can be
quantified with ErisML-derived measures — and do those measures
improve prediction beyond established alternatives?

- **Primary endpoint:** out-of-sample predictive performance on
  decision outcomes and/or state trajectories under sequences not used
  to estimate the participant or group model.
- **Secondary endpoints:** replicated order effects, context effects,
  higher-order interaction, temporal stability, cross-domain
  generalization, and — only in later phases — correspondence between
  mathematical interaction structure and neural measurements.

## 3. Evidence discipline

Every important statement carries one of five evidence labels
(tracked claim-by-claim in `CLAIM-LEDGER.md`):

| Tier | Meaning |
|------|---------|
| **A** | Implemented / inspectable in the current ErisML-Lib repository (code, tests, formalization, documented architecture) |
| **B** | Repository-reported empirical result — must be independently reproduced from current `main` before external use |
| **C** | Established external peer-reviewed literature, independent of ErisML |
| **D** | Cross-framework analogy — plausible conceptual mapping, not an empirical correspondence |
| **E** | New research hypothesis — unproven until preregistered data support it |

Key standing facts:

- ErisML's categorical evaluation exposes commutator defect Ω_op
  (order sensitivity), mixed defect μ (context dependence), and
  permutation defect π₃ (higher-order composition). **[A]**
- I-EIP exposes activation probes, Procrustes-based ρ estimation,
  equivariance error, drift detection, non-degeneracy checks. **[A]**
- MoralTensor operations run through rank-6 context tensors (temporal
  axes, coalition context, Shapley attribution, uncertainty). **[A]**
- QND results (28.7% Harm↔Intent reversal; 31/56 significant
  order-effect pairs) are **[B]** until reproduced (Phase 0).
- **No current ErisML-Lib result establishes correspondence with
  neural populations, biological mechanism, or human cognitive
  architecture.** That is the campaign's [E]-tier territory.

## 4. Prior-art positioning

- **Eagleman's biological premise [C]:** competing neural populations
  controlling a single behavioral output; local decisions and emergent
  coalitions; brain complexity "necessitates new kinds of mathematics"
  (*Incognito*; "The Brain on Trial", *The Atlantic* 2011).
- **Human order effects are not novel by themselves.** Quantum
  cognition already models noncommutative question-order effects
  (incl. the parameter-free QQ equality — Wang et al. PNAS 2014;
  Pothos & Busemeyer, Annu. Rev. Psychol. 2022); sequential-sampling
  and competing-accumulator models are mature (Forstmann et al. 2016).
  "Humans show order effects" cannot be the novelty claim.
- **What ErisML must add:** (i) a unified interaction vocabulary
  (pairwise order + context + higher-order + temporal + attribution,
  not one order statistic); (ii) cross-level discipline separating
  output behavior, internal representation, and representational/gauge
  effects; (iii) predictive structure estimated on a subset of
  sequences and tested on unseen ones; (iv) auditability (declared
  invariances, witnesses, reproducible pipelines); (v) a common
  measurement language for human and artificial systems without
  claiming shared mechanism.

## 5. Preregistered hypothesis family

| # | Hypothesis | Candidate ErisML measure | Null |
|---|------------|--------------------------|------|
| H1 | Order dependence: judgment distribution differs by sequence for identical information | Ω_op | After reactivity/memory/presentation controls, sequence contributes no reproducible effect |
| H2 | Context dependence: factor A's effect depends on state set by other factors | μ | Factor effects stable/additive across contexts |
| H3 | Higher-order interaction: 3-factor sequences carry structure beyond pairwise | π₃ (or explicit human-data analogue) | Pairwise terms fully account for sequence differences |
| H4 | Temporal path dependence: trajectories depend on when information arrives and deliberation time | temporal tensor axis | Only the final information set matters |
| H5 | Distributed contribution: nonuniform marginal influence and coalition effects | attribution + coalition analysis | Simpler additive model predicts equally well |
| H6 | Representational vs. intrinsic: some inconsistency disappears under controlled re-representation; the remainder is candidate intrinsic structure | decomposition machinery | Decomposition adds no reliable value beyond nuisance controls |
| H7 | Predictive generalization: ErisML-derived model beats prespecified baselines on held-out sequences/participants | fitted interaction structure | No out-of-sample advantage |
| H8 | Cross-domain generalization: a subset of measures replicates in a non-moral domain | same suite | Effects specific to moral/social-judgment tasks |

## 6. Falsification and model comparison

Confirmatory analysis compares prespecified alternatives **on
held-out data**:

| Model | Role |
|-------|------|
| Baseline 1 — additive statistical | Hierarchical logistic/ordinal/multinomial, content factors, no order interactions |
| Baseline 2 — interaction regression | Conventional pairwise + higher-order terms, no ErisML structure |
| Baseline 3 — sequential sampling | DDM / competing accumulator where RT and two-choice assumptions justified |
| Baseline 4 — quantum probability | Quantum-cognition benchmark where question-order predictions apply |
| Candidate — ErisML-derived | Prespecified Ω_op / μ / π₃ / temporal-tensor features; **no post hoc feature invention in the confirmatory phase** |

Primary metrics: held-out log likelihood / proper scoring rule,
calibration, predictive accuracy where meaningful, uncertainty
intervals, preregistered complexity penalties or cross-validation.
Statistical significance alone is not sufficient.

## 7. Staged program and gates

| Phase | Work | Gate |
|-------|------|------|
| **0 — Reproducibility & construct audit** | Re-run anchoring ErisML experiments; freeze commit, environment, seeds, configs, provenance, outputs; produce the claim ledger; translate each human construct into an observable variable, marking where the mapping is only analogical | **Gate 0:** no external pitch until every numerical claim used in it has a reproducible artifact or is explicitly labeled unverified |
| **I — Behavioral discovery pilot** | Controlled stimuli, effect-size estimation, comprehension checks, validate sequence manipulations; trajectory + terminal-only arms quantify measurement reactivity; exploratory, locks the confirmatory protocol | **Gate 1:** proceed only if order/context effects are reliable enough for a powered design and not explained by attention, memory, or intermediate-question reactivity |
| **II — Preregistered confirmatory study** | Locked design; N from simulation-based power analysis with a prespecified smallest effect of interest; frozen analysis plan | **Gate 2:** ErisML must show reliable **out-of-sample** value, not merely significant in-sample fit |
| **III — Domain generalization** | Replicate strongest effects in a non-moral domain (risk/reward, delay/value, certainty/magnitude, social/economic tradeoff) | **Gate 3:** general decision-architecture claims require cross-domain replication |
| **IV — Neuroscience extension** | EEG/fMRI/MEG/pupillometry/eye-tracking/RT/autonomic measures matched to *validated* behavioral effects; no anatomical one-to-one mapping unless independently justified | **Gate 4:** seek neural correspondence only for behavioral signatures that already replicated |
| **V — Cross-level modeling** | Test whether one formal structure relates biological state, behavioral trajectory, and mathematical representation; I-EIP concepts may inspire analysis, but model-layer equivariance is **not presumed** to transfer to neural state | **Gate 5:** any shared-formalism claim requires prospective prediction in independent data |

## 8. Success ladder

- **L0** — Reproducible ErisML evidence (repository claims regenerate
  from a frozen environment).
- **L1** — Replicated human sequence effects after
  measurement-reactivity controls.
- **L2** — Structured ErisML characterization: Ω_op / μ / π₃-style
  measures capture stable structure, not a relabeling of conventional
  interactions.
- **L3** — Predictive advantage over prespecified baselines on
  held-out data.
- **L4** — Cross-domain generalization outside moral/social judgment.
- **L5** — Neural correspondence in a preregistered study.
- **L6** — Cross-level formalism with successful prospective
  predictions across behavioral and neural levels (strongest, most
  distant claim).

## 9. Informative failure modes (declared in advance)

| Outcome | Meaning |
|---------|---------|
| No human order effect | Task lacks the phenomenon or effect too small; ErisML remains an AI/normative framework; neuroscience extension pauses |
| Order effect, no ErisML advantage | Conventional / quantum / sequential-sampling models suffice; the campaign narrows its claim |
| Predictive success only in moral tasks | Domain-specific judgment process, not distributed decision-making generally |
| Behavioral success, no neural correspondence | Useful behavioral formalism without biological mechanism |
| Neural association without prediction | Exploratory correlation; no mechanistic claim until prospectively predictive |

## 10. Deliverables

- **D0** Reproducibility dossier — frozen commit, environment,
  runbook, regenerated results, hashes, claim ledger.
- **D1** ErisML ↔ distributed-cognition construct map, every mapping
  A/B/C/D/E-labeled.
- **D2** Human experimental protocol (preregistration-ready; see
  `PROTOCOL-MVE.md`).
- **D3** Human-data adapter — versioned pipeline: behavioral
  trajectories → prespecified ErisML features + baseline inputs.
- **D4** Behavioral pilot package — dataset, power simulation,
  manipulation checks, reactivity estimate, locked confirmatory plan.
- **D5** Confirmatory study — preregistered dataset + held-out model
  comparison.
- **D6** Cross-domain replication.
- **D7** Neuroscience protocol (only if Gate 3 passed).
- **D8** Manuscript series — Paper 1: behavioral structure + model
  comparison; Paper 2: cross-domain generalization; Paper 3: neural
  correspondence, if supported.

## 11. Team and governance

| Role | Candidate | Responsibility |
|------|-----------|----------------|
| Mathematical / ErisML lead | Andrew Bond | Formal definitions, human-data translation, reproducibility package, limits of mathematical claims |
| Neuroscience PI | Prospective collaborator | Biological construct validity, neural-method selection, interpretation boundaries |
| Experimental psychology / cognitive modeling lead | To recruit | Task design, counterbalancing, reactivity controls, competing cognitive models |
| Statistician / quantitative methodologist | To recruit | Power simulation, preregistration, hierarchical inference, multiplicity control, validation plan |
| Research engineering lead | To recruit / assign | Human-data adapter, analysis pipeline, versioned artifacts, reproducible environment |
| Campaign / program coordination | Kim Baley / Justice Innovations, if desired | Research development, documentation, outreach, funding prep — without controlling scientific conclusions |

## 12. Ethics and responsible interpretation

- **IRB before recruitment**; informed consent for any behavioral or
  neural data collection.
- **No moral profiling:** individual-level "decision geometry" is a
  research parameterization — never a diagnostic, character score,
  risk score, or legal inference about a person.
- **Data minimization:** collect only what the hypotheses need;
  separate identity from research records; predefine retention and
  sharing.
- **No legal overreach:** even a neural correspondence would not by
  itself establish diminished responsibility, culpability, or
  capacity.
- **Registered reporting** where feasible (Registered Report or
  equivalent).
- **Reproducible artifacts:** archive code, environment, transforms,
  stimuli versions, model specs, exclusions, and all claim-generating
  outputs.

## 13. Scientific risk register

| Risk | Why it matters | Mitigation |
|------|----------------|------------|
| Novelty overclaim | Order effects and noncommutative cognitive models already exist | Position novelty on the integrated measurement suite, falsifiable invariance framework, prediction, cross-system comparison |
| Measurement-induced order effects | Intermediate questions may alter cognitive state | Terminal-only arm; preregister the reactivity contrast |
| Post hoc mathematics | Flexible feature definitions fit anything | Freeze human-data analogues before confirmatory analysis; hold out sequences and participants |
| Biological reification | Mathematical axes mistaken for neural modules | Biological mapping stays a hypothesis; never infer anatomy from algebra |
| Model-selection bias | Only favorable baselines chosen | Preregister mature competing families; invite an independent cognitive modeler |
| Moral-domain confound | Effects peculiar to moral language | Require non-moral replication before general claims |
| Repository drift | Codebase changes mid-project | Freeze tagged commits per study; preserve containers/lockfiles |
| Founder effect / confirmation pressure | Stakeholders incentivized to see correspondence | Independent analysis review, preregistration, transparent nulls, Registered Report review |

## 14. Outreach posture

**The first ask is small:** a technical conversation with Eagleman to
pressure-test the construct mapping and the behavioral experiment —
not endorsement, not validation, not attaching his name to a
conclusion. Questions worth putting to him: which "team of rivals"
phenomena are experimentally mature enough to operationalize; whether
order/context manipulations are the most diagnostic competition
paradigm; which neural modality fits *after* a behavioral signature
exists; what result would convince a neuroscientist the formalism
captures structure rather than fitting behavior; which alternative
models/collaborators to include from the outset.

**The defensible external thesis.** Do **not** say: "Andrew Bond
mathematically proved David Eagleman's theory." Say: "Eagleman's
neuroscience describes human choice as emerging from interacting and
competing processes. ErisML-Lib independently implements a
mathematical framework for measuring several properties expected in
interacting decision systems. We propose to test, prospectively and
against established alternative models, whether those structures
predict human decision dynamics and ultimately correspond to neural
measurements." If the predictive and cross-domain gates pass, the
long-range claim is a **candidate mathematical language for
distributed decision-making testable across human and artificial
systems** — not "proof of Eagleman."

## 15. Source basis

Access verified 2026-08-22 (fuller systematic review required before
IRB/preregistration):

1. ErisML-Lib repository — https://github.com/ahb-sjsu/erisml-lib
2. Eagleman, "The Brain on Trial," *The Atlantic* (2011).
3. Eagleman, *Incognito* (excerpt) — distributed local decision
   processes; complexity necessitating new mathematics.
4. Eagleman, *Inner Cosmos* podcast, Ep. 5 ("team of rivals").
5. Stanford profile: David Eagleman (affiliation; Center for Science
   and Law).
6. Wang, Solloway, Shiffrin & Busemeyer (2014), PNAS 111(26):9431–9436
   — quantum question-order effects.
7. Pothos & Busemeyer (2022), *Annu. Rev. Psychol.* 73:749–778 —
   quantum cognition.
8. Forstmann, Ratcliff & Wagenmakers (2016), *Annu. Rev. Psychol.*
   67:641–666 — sequential-sampling models.
9. Khona & Fiete (2022), *Nat. Rev. Neurosci.* 23:744–766 — attractor
   and integrator networks.
