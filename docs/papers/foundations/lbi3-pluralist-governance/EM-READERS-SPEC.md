# EM channel readers — specification (unblocks RQ2)

**Written 2026-08-27, BEFORE any conflict statistic was computed**, as
Finding I-01 requires. The ordering is the point: these readers are
specified and frozen first, and only then may the RQ2 pilots run.

Finding I-01: five of the compiler's ten EM modules (`fairness`,
`legitimacy`, `autonomy`, `epistemic`, `rights`) are gated on English
keywords in a fact's free-text `description`. On structured decision
records — where we author the descriptions — those channels would be
set by our choice of adjectives.

## Two readers, one boundary

| | **A. `structured_v0`** | **B. `semantic_xbse`** |
|---|---|---|
| input | fact `kind` + `severity` + `subjects` | narrative text |
| text dependence | **none** | total |
| used by LBI-3 | **yes — the RQ2 path** | **no** (see below) |
| provenance | this spec | [`xbse`](https://github.com/ahb-sjsu/xbse) validated encoders |

**Why the boundary matters.** A better *text* reader does not fix our
problem, it hides it: swapping keyword matching for semantic matching
on descriptions we wrote still lets phrasing pick the verdict, just
more smoothly. So the paper's path is A. B is specified here because
it is the right fix for the compiler's *designed* input (narrative
moral material), where keyword brittleness is a real defect —
"prejudiced against him" carries no substring of
"unfair|biased|discriminat".

**Why B is inapplicable to this corpus.** The public COMPAS file
contains no PSI text, no judicial reasoning, no narrative record at
all. That is the *same missing artifact* that leaves 4 of 7 doctrinal
gates `undetermined` (E4, the auditability gap). One absent document
darkens both the doctrinal gates and the semantic perception layer —
a single finding with two faces, and worth stating as such.

## A. `structured_v0` — channel definitions

Each channel aggregates facts by `kind` with the existing
`aggregate_negative` helper (max severity, mean confidence), so
severity semantics stay identical to the modules that already work.
No description text is read by any channel.

| channel | fact kinds read | status |
|---|---|---|
| harm | `harm`, `non_maleficence` | unchanged (already structured) |
| externality | `externality` | unchanged |
| care | `care` | unchanged |
| fidelity | commitments | unchanged |
| repair | derived from harm | unchanged |
| **fairness** | `justice` | **new** — the kind already encodes that the fact is a justice matter; demanding adjectives on top double-counts |
| **legitimacy** | `legitimacy`, `coercion` | **new** |
| **autonomy** | `consent`, `coercion` | **new** |
| **epistemic** | `truth`, `deception`, `uncertainty` | **new** |
| **rights** | — none available — | **stays dark** (below) |

### The `rights` channel stays dark, on both paths

There is **no `rights` kind** in the compiler's fact vocabulary
(`coercion, consent, legitimacy, harm, vulnerability, uncertainty,
externality, justice, care, truth, role_duty, deception, reciprocity,
non_maleficence`), so `structured_v0` has nothing principled to read;
the current module's "any fact whose description contains 'right'" has
no structured counterpart.

Independently, `xbse`'s `rights_respect` encoder **failed** its
pre-registered cross-dataset bar (AUROC 0.509, margin −0.00, method-
failure branch open), and xbse's standing rule is that an unvalidated
encoder may not be used downstream. So path B cannot fill it either.

Both paths therefore report `rights` as **unavailable**, not as 0.0.
We note the convergence — the one channel with no structured source is
also the one whose encoder failed validation — as an observation, not
a causal claim; two independent reasons happen to land on the same
axis.

## B. `semantic_xbse` — specification (not run for this paper)

Per-dimension `xbse.DimensionScorer.score(text) -> Valence(value ∈
[−1,+1], confidence)`, with `+` = value upheld and `−` = violated,
which already matches the EM `DimensionScore` sign convention.
Construction goes through `from_pairsource`, which calls
`require_pass` — an unvalidated encoder cannot produce a score.

Registered reliability weighting, taken from `moral-spectrum-analyzer`
rather than invented here: `reliability_weight = max(0, 2·AUROC − 1)`
on the registered cross-dataset AUROCs.

| xbse dimension | EM channel | AUROC | reliability_weight |
|---|---|---:|---:|
| epistemic_quality | epistemic | 0.817 | 0.634 |
| virtue_care | care | 0.811 | 0.622 |
| fairness_equity | fairness | 0.789 | 0.578 |
| autonomy_respect | autonomy | 0.747 | 0.494 |
| legitimacy_trust | legitimacy | 0.708 | 0.416 |
| physical_harm | harm | 0.622 | 0.244 |
| rights_respect | rights | 0.509 | **0.018 → unavailable** |

**Mandatory gate if B is ever applied to text we authored:** a
paraphrase-invariance test. The verdict must be stable across ≥5
independent paraphrases of every fact description; if it moves, the
result is void, because the phrasing rather than the situation is
driving it. This is `moral-spectrum-analyzer`'s "invariant" trust beat
turned into a precondition, and it is what converts the circularity
objection from a blocking worry into a measurable one.

## What is frozen by this document

The channel↔kind table in §A, the rights-unavailable rule, and the
requirement that `structured_v0` read no description text. The RQ2
pilots may run only against readers matching this spec. If a channel
definition changes afterwards, the change is disclosed and the pilots
re-run — the DB-3 precedent.
