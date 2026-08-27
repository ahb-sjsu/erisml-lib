# Finding I-02 — the DEME v0 verdict function is structurally blind to
the fairness, autonomy, and rights channels

**Recorded 2026-08-27, before any conflict statistic was computed.**
Supersedes Finding I-01's causal conclusion (I-01's keyword diagnosis
stands; its explanation of `indeterminate` does not). Nothing sealed.

## How this was found

I-01 attributed the consequentialist projection's blanket
`indeterminate` to five keyword-gated EM modules. The `structured_v0`
readers were specified, frozen (commit `652ce64`), and run — and the
prediction failed: the channels filled, and **not one verdict moved**.

| channel | `default` | `structured_v0` |
|---|---:|---:|
| fairness | +0.000 | **−0.850** |
| autonomy | +0.000 | **−0.500** |
| harm | −0.850 | −0.850 |
| rights | +0.000 | *unavailable* (by construction) |
| others | +0.000 | +0.000 |

Maximal fairness and autonomy violation signals; identical verdict.
That falsified I-01's causal claim and forced the real diagnosis.

## The real diagnosis (verified in source)

`erisml_backend/deme_bridge.py` computes its verdict from exactly six
channel values (lines 43–48) plus two side conditions:

```
externality_v, harm_v, care_v, fidelity_v, repair_v, legitimacy_v
+ stakeholder.requires_review flags, epistemic uncertainty
```

**`fairness_equity`, `autonomy_respect`, and `rights_respect` appear
in no branch.** The branch conditions are:

| branch | condition | why it cannot fire here |
|---|---|---|
| tragic_conflict | `externality ≤ −0.85` ∧ defeasible commitment | no externality fact on adverse cases; no commitments |
| prohibited | `harm < −0.85` ∧ `care < 0.5` ∧ `legitimacy < 0` | **`harm` is exactly −0.85** — the weight of a `grave` fact — and the test is strict, so only a `catastrophic` fact can ever prohibit |
| permitted_with_residue | `fidelity > 0.3` ∧ … | `fidelity` derives only from commitments; an RAI decision record has none |
| clean permit | `fidelity > 0.5` ∧ … | same |
| requires_human_review | flagged stakeholder ∨ `uncertainty > 0.5` | neither is populated |
| — | else | **`indeterminate`** |

Two independent structural facts, then:

1. **Reachability.** Every verdict branch is conjunctive over channels
   a structured RAI record does not populate — chiefly `fidelity`,
   which exists only where the narrative supplies commitments. The
   `grave`-sits-exactly-on-the-boundary detail (`harm < −0.85` vs
   `severity_score("grave") = 0.85`) means the prohibition branch is
   unreachable for anything short of catastrophic.
2. **Blindness.** Even with every channel populated, the verdict
   cannot respond to fairness, autonomy, or rights, because it never
   reads them.

## Why this is decisive for RQ2, and why it is not a patchable bug

P2 asks whether **deontic-vs-consequentialist conflict concentrates
where the fairness impossibility bites**. An engine whose verdict
function is structurally incapable of responding to the fairness
channel cannot generate fairness-relevant conflict. Any conflict it
did produce would be conflict about harm and fidelity wearing a
fairness label — which is exactly the kind of quiet substitution this
paper exists to argue against.

Note the shape of the failure, because it generalizes beyond us: the
engine does not error, warn, or report low confidence. It returns
`indeterminate` with `confidence = 0.5` and the rationale
"Insufficient signal to resolve" — while a −0.850 fairness violation
sits unread in the vector it just computed.

## Status

- **RQ1 unaffected** — 37/37 vectors, 7/7 mutations. Stands.
- **`structured_v0` stands** and is validated: it does what it was
  specified to do (channels filled, zero text dependence). It is a
  genuine fix for I-01's keyword defect; it is simply not sufficient,
  because the defect it fixes is not the binding one.
- **RQ2/P2 remains HALTED.** No conflict statistic has been computed
  at any point in this campaign. The vacuity kill condition is still
  *not* triggered — that requires projections that can run.

## The move not made (again)

Reachability could be bought cheaply: give the court commitments and
`fidelity` clears 0.3, opening the permit branches. Commitments are
defensible on their own terms — courts do hold them — but adding them
*now*, with the target statistic in view and knowing exactly which
threshold they would cross, is tuning the instrument to the
hypothesis. And it would not touch the blindness in (2) regardless.

## The fix is now specified upstream

Drafted as `erisml-compiler/docs/plans/deme-verdict-function-spec.md`
(2026-08-27, proposal, not implemented). It turned out to be mostly a
**conformance** exercise rather than a new design: the DEME
architecture of record already classifies `fairness` and `autonomy` as
*substantive* blocks that must be realized as `k`-contractions, and
already classifies `rule_following` (fidelity) as **procedural** — an
attestation, not a contraction. So D1 and D2 below are deviations from
the specified architecture, not choices the v0 bridge was entitled to
make. The spec carries eight acceptance properties, all checkable
without reference to this campaign's data, and an explicit rule that
no LBI-3 statistic may be computed until it is implemented and frozen.

## What a real fix requires (specified, not built)

A verdict function that reads all validated channels, with the
reliability weighting the sibling projects already register
(`moral-spectrum-analyzer`: `reliability_weight = max(0, 2·AUROC −
1)`), and that distinguishes *unavailable* from *neutral* — the
distinction `structured_v0`'s `rights` module already implements and
that this bridge lacks. That is a change to the reasoning engine and
belongs upstream in `erisml-compiler`, specified on its own terms and
frozen before any LBI-3 statistic is computed. It is not a paper
patch, and this campaign will not make it under pressure of a pending
result.
