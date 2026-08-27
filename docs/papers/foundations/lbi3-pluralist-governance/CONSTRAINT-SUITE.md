# LBI-3 Constraint Suite — doctrine compiled to gates (RQ1)

**Status:** draft v0.1, 2026-08-27. Nothing sealed. Every doctrinal
claim below is marked ⧗ **until quote-verified against the opinion
itself** — LBI-1's r3 round caught a *Loomis* mischaracterization in
the accepted manuscript, so second-hand statements of the holding are
not trusted here. The encoding is written against the **real**
`erisml-compiler` API (verified 2026-08-27 by reading
`projections/base.py`, `projections/deontic.py`, `ir/graph.py`), not
an idealized one.

---

## 1. What RQ1 asks, precisely

> Can the operative constraints a jurisdiction imposes on
> risk-assessment-instrument (RAI) use be encoded as gates, **once**,
> without per-case ad-hoc logic?

"Without ad-hoc logic" is the load-bearing half. A gate suite that
needs a hand-written branch per defendant proves nothing; the claim is
that doctrine is *general* over decision records, and the vector set
(§5) is designed to falsify that if false.

## 2. Where this plugs in (verified API)

The compiler exposes:

- `GateFinding(name, passed, reason, severity ∈ {minor, moderate,
  grave, catastrophic}, subjects, detail)` — frozen; `passed=False`
  means the gate **fired**.
- `ProjectionResult(framework, verdict, polarity, confidence,
  findings, framework_specific, metadata)`, where `polarity ∈
  {permit, forbid, escalate, neutral}` is auto-filled from the
  verdict via `polarity_for_verdict`.
- `Projection` ABC: `project(substrate, *, graph=None, **kwargs)`.
- Graph: nodes `{stakeholder, act, maxim, commitment, fact, norm}`,
  edges `{performs, imposes_on, consents_to, holds_commitment,
  commitment_binds, treats_as, under_maxim, coerces, surfaces_fact,
  fact_subject, would_violate_if_universalised}`.

**Design decision: a fifth projection, not a patch.** The four
existing projections (deontic-Kantian, consequentialist, virtue, care)
are *ethical-theory* readings and stay untouched. Jurisdictional
doctrine enters as a new `DoctrinalProjection` emitting the same
`GateFinding` type, so the conflict machinery (P2) sees it uniformly.
Rationale: doctrine is not a moral theory — it is positive law that
*constrains* which theory-verdicts an institution may act on. Keeping
it a separate projection preserves that distinction and lets a paper
reviewer see exactly which findings came from case law versus from
Kant.

**Polarity registration note.** `_DEFAULT_POLARITY_MAP` currently maps
the deontic trio (`permissible`/`forbidden`/`requires_review`). The
doctrinal projection reuses those three verdict strings rather than
inventing vocabulary, so polarity normalization works unmodified. A
fourth state — `undetermined` (§4) — maps to `neutral` by the existing
default and **must never be read as `permit`**; this is asserted as a
test vector (V-N1), because silently treating "unauditable" as
"compliant" is the failure mode most likely to matter in deployment.

## 3. Jurisdiction profiles (the parameterization)

A `JurisdictionProfile` is data, not code:

```yaml
id: wi-2016-loomis
source: State v. Loomis, 881 N.W.2d 749 (Wis. 2016),
        cert. denied, 137 S. Ct. 2290 (2017)
required_warnings: [proprietary_methodology, group_based_not_individual,
                    accuracy_questioned_across_groups, not_validated_for_local_population,
                    not_designed_for_this_decision_point]
determinative_use: forbidden
attribute_policy:
  race:  foreclosed
  sex:   permitted_with_justification   # ⧗ Loomis upheld sex use
  age:   permitted
sanctioned_decision_points: [post_sentencing_corrections]   # ⧗
```

The same gate code, a different profile, yields different verdicts —
that is the claim, and V-J1/V-J2 (§5) test it by swapping profiles on
a fixed record.

## 4. The gates

Each gate names: the doctrinal source (⧗ verification owed), the
operational test over the decision record, severity, and — critically
— **the record fields it requires**. A gate whose required fields are
absent returns `passed=True` with
`detail={"result": "undetermined", "missing": [...]}`, following the
compiler's own convention for the universalizability gate when no
maxim is extracted. Undetermined is *recorded*, never guessed.

| id | gate | doctrinal basis (⧗) | fires when | severity |
|---|---|---|---|---|
| D1 | `required_warnings_present` | *Loomis* mandated written cautions in the PSI | RAI score used and any profile-required warning absent from the record | grave |
| D2 | `not_determinative` | *Loomis*: score may not be the determinative factor | the record's stated basis reduces to the score alone | catastrophic |
| D3 | `group_to_individual_inference` | *Loomis* caution: scores are group-based | the record asserts an individualized prediction from the group statistic | grave |
| D4 | `validated_for_population` | *Loomis* caution: monitoring/validation for local populations | instrument's validation record does not cover the deployment population | moderate |
| D5 | `purpose_fit` | *Loomis* caution: not designed for this decision point | decision point ∉ profile's sanctioned set | grave |
| D6 | `contestability` | due-process rationale: defendant could review and challenge inputs | no notice of score or no opportunity to contest inputs | grave |
| D7 | `attribute_policy` | attribute-specific doctrine; race foreclosed, sex upheld | a foreclosed attribute is an instrument input | catastrophic (race) |

Verdict roll-up follows the existing deontic convention exactly:
any fired `grave`/`catastrophic` gate → `forbidden`; any fired
`moderate` → `requires_review`; else `permissible`.

**D7 is the suite's demonstration gate.** One gate, parameterized by
profile, reproduces the doctrinal asymmetry LBI-1 measured
empirically: race foreclosed, sex permitted. It is the cleanest
available evidence that the encoding is doctrine-driven rather than
metric-driven — and it connects LBI-1's sex/race result to positive
law without either paper leaning on the other's claims.

## 5. Test-vector set (preregistered, ground truth by construction)

Vectors are *constructed* decision records whose gate outcomes follow
from how they were built, so the ground truth is definitional, not
judgmental. Sealed before any code runs against them.

| class | n | content | expected |
|---|---|---|---|
| V-P | 7 | one per gate: minimal record that satisfies it | all pass |
| V-F | 7 | one per gate: minimal record that violates it | that gate fires, others pass |
| V-U | 7 | one per gate: required field(s) removed | `undetermined`, gate does not fire, missing fields listed |
| V-N1 | 1 | fully-stripped record (all fields absent) | **all undetermined; verdict NOT `permissible`-as-compliant** — the anti-vacuity vector |
| V-J1/J2 | 2 | one record, two profiles (race-foreclosed vs. hypothetical permissive) | D7 verdict differs, all else identical |
| V-C | 4 | multi-gate combinations (2 fires + 2 undetermined; grave+moderate mixes) | correct severity roll-up |
| V-A | 3 | adversarial: near-miss phrasings that should NOT fire (e.g. score mentioned but not relied on) | no fire; tests over-firing |

**Bar (candidate, freezes only after ≥2 disclosed calibration
draws):** 31/31 exact match, **and** the implementation contains zero
identifiers naming a specific vector or defendant — checked
mechanically by grepping the gate module for vector ids. That second
half is what actually tests "no ad-hoc logic"; the first half alone
could be passed by cheating.

**Kill condition:** any doctrinal requirement that cannot be expressed
without case-specific branching is reported as such — the finding
would be *"this much of the doctrine resists general encoding,"* which
is publishable and which the paper commits in advance to reporting.

## 6. The auditability gap (declared BEFORE the run)

The public ProPublica COMPAS file contains features, scores, and
outcomes. It contains **no** PSI text, no warning records, no notice
or contest records, no jurisdiction-specific validation studies. So on
the real corpus, by construction:

- **evaluable:** D7 (attribute policy — from the instrument's
  documented input set), D5 (decision point — from the corpus's known
  provenance), D4 (validation coverage — from published validation
  studies of the instrument);
- **undetermined:** D1, D2, D3, D6 — every gate that depends on what
  the court wrote or did.

We declare this now so it cannot be presented later as a discovery.
And we make it a measured endpoint: **E4, the auditability gap** — the
fraction of doctrinal requirements that are *unauditable from the
records an external auditor can actually obtain*. Predicted here, in
advance: **4/7 undetermined on the public corpus.** If that is right,
the finding is not "COMPAS violated *Loomis*" (which we cannot and do
not claim) but the sharper, defensible one: *the public record cannot
answer whether it did* — a transparency deficit measured rather than
asserted, and squarely within the contestability literature the paper
already engages (Citron; Kroll et al.).

## 7. Open issues before seal

1. ⧗ **Verify every doctrinal row against the opinion** (881 N.W.2d
   749), not secondary sources; record pin cites in this file. The
   *cert. denied* cite and the sex-use holding get the same treatment.
2. Decide whether D4's "validation coverage" is checkable from
   published Broward-population studies or is itself undetermined —
   affects the E4 prediction (4/7 vs 5/7); **fix before seal.**
3. Confirm the polarity map treats `undetermined` correctly end-to-end
   (V-N1), or extend `_DEFAULT_POLARITY_MAP` upstream in the compiler.
4. Legal review of the encodings by a lawyer before publication —
   these are readings of a holding, and the paper should say who read
   them. An unreviewed doctrinal encoding by an engineer is exactly
   the overreach the LBI-1 reviewers were right to police.
5. Whether the profile should be published as a citable artifact
   (a "*Loomis* profile" others can reuse or contest) — likely yes;
   it is the most directly reusable output of the paper.
