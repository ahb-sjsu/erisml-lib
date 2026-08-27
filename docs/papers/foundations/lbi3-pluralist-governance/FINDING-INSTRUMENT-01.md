# Finding I-01 — the v0 EM-DAG cannot carry a structured-record
governance pipeline (RQ2 halted)

**Recorded 2026-08-27, before any conflict statistic was computed.**
Nothing sealed. This halts the RQ2 measurement and is reported as a
finding rather than worked around.

> ## ⚠ AMENDMENT, same day — this filing was PARTLY WRONG
>
> The keyword diagnosis below is **confirmed**, and the
> `structured_v0` readers built from it **work**: on the smoke case,
> `fairness` moves 0.000 → −0.850 and `autonomy` 0.000 → −0.500.
>
> But the *causal claim* — that the keyword gates are why the
> consequentialist projection returns `indeterminate` — is **wrong**.
> Filling those channels changes no verdict at all. The real causes
> are structural and are recorded in
> [`FINDING-INSTRUMENT-02.md`](FINDING-INSTRUMENT-02.md), which
> supersedes this document's §Diagnosis conclusion. The corrected
> headline: the DEME v0 verdict function reads only 6 of 10 channels
> and **never reads `fairness_equity`, `autonomy_respect`, or
> `rights_respect`** — so no amount of channel-filling can make its
> verdict respond to fairness.
>
> This amendment is left in place rather than rewritten, so the record
> shows the first diagnosis, the check that falsified it, and the
> correction.

## What happened

The RQ2 pipeline maps a COMPAS decision record into a `CompilerIR` +
`MoralSubstrate` (per `MAPPING.md`) and runs the compiler's four
ethical projections. On the smoke set, three of four projections
returned **constant** verdicts and the consequentialist projection
returned `indeterminate` for every case — meaning the
deontic-vs-consequentialist pair that P2 is *about* had no signed
verdict to disagree with.

## Diagnosis

The EM-DAG's ten modules split into two kinds:

| reads structured fields (kind + severity + commitments) | gated on English keywords in the fact's free-text `description` |
|---|---|
| harm, externality, care, fidelity, repair | **autonomy, epistemic, fairness, legitimacy, rights** |

The keyword gates are literal substring tests, e.g.
`FairnessEM` counts a `justice` fact only if its description contains
`"unfair"`, `"biased"`, or `"discriminat"`; `LegitimacyEM` wants
`"void"`, `"tyrann"`, `"coerc"`, or `"fraud"`; `AutonomyEM` wants
`"coerc"`, `"non-consensual"`, `"imposed"`, `"forced"`, or
`"without consent"`.

This is entirely reasonable for the compiler's designed input — moral
material in natural language, where those words are evidence. It is
**not** usable for our input, which is a structured decision record
with no narrative text. Our fact descriptions are written by us, so
in this pipeline those five channels would be set by *our choice of
adjectives*.

Verified consequence on the smoke set: `harm = −0.85` and
`repair = −0.85` fire correctly for adverse classifications (they are
structured readers), while `fairness`, `legitimacy`, `autonomy`,
`rights`, `epistemic`, `externality`, `care`, and `fidelity` all read
exactly 0.000 with "No relevant facts detected." With `fidelity = 0`
the DEME bridge's permit branches (which require `fidelity > 0.5` or
`> 0.3`) cannot be reached, and the harm value sits exactly at the
prohibition branch's boundary (`harm < −0.85` is strict), so every
case falls through to `indeterminate`.

## The move not made

Making the pipeline produce signed consequentialist verdicts is
trivial: write "biased" into the `actuarial_basis` description and
`FairnessEM` fires; add a commitment and `fidelity` clears 0.5. Both
were rejected. Choosing the moral verdict by choosing adjectives, in a
paper whose thesis is that governance systems must not quietly pick a
side, would be self-refuting — and the resulting P2 statistic would be
an artifact of our phrasing, not a property of the decisions. (Adding
the court's standing commitments is defensible on its own terms and
may return later, but it cannot be introduced *now*, with the target
statistic in view, without tuning the instrument to the hypothesis.)

## Status of the claims

- **RQ1 (doctrinal gates) is unaffected.** It never used the EM-DAG:
  37/37 vectors, 7/7 mutations caught. That result stands.
- **RQ2/P2 is HALTED**, not failed. The prediction has not been
  tested, and no conflict number exists. The outline's kill condition
  "projections always agree or always disagree — the pluralism is
  vacuous" is **not** triggered: we have not observed vacuous
  pluralism, we have observed that the instrument cannot see this
  input class at all. Those are different findings and must not be
  conflated.

## The finding itself is worth reporting

The 2025–26 runtime-governance line surfaced in
`PRIOR-ART-SWEEP.md` §S8 proposes machine-readable normative
constraints evaluated at runtime over AI systems. This is a concrete,
measured obstacle on that path: an off-the-shelf machine-ethics
evaluator, built for narrative moral material, degrades to half its
channels when handed structured decision records, and the degradation
is **silent** — every dark channel reports a confident 0.000 with
"No relevant facts detected", and the pipeline yields a clean-looking
`indeterminate` rather than an error. A governance layer that fails
this way in deployment would look like it was working.

## Path forward (ordering is the point)

1. Specify structured-field readers for the five keyword-gated
   channels — each channel defined by fact `kind`, `severity`, and
   `subjects`, with no text dependence — **on their own terms, written
   and frozen before any conflict statistic is computed.**
2. Offer them upstream to `erisml-compiler` as an alternative EM
   profile (`structured_v0`), since the limitation is general and the
   fix benefits any structured-input user.
3. Re-run the RQ2 pilots against that profile. If conflict is still
   degenerate, *that* is the vacuity kill condition firing, and it
   gets reported as such.
4. Only then set P2's bars from ≥2 disclosed calibration draws.

Until step 1 is done and frozen, no conflict statistic from this
pipeline may be quoted, including in drafts.
