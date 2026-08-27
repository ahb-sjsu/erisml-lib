# LBI-3 Mapping — COMPAS decision records → moral structure (RQ2)

**Status:** declared 2026-08-27, **before** any conflict statistic was
computed. Nothing sealed. The mapping is the paper's most attackable
choice — the projections can only read what the mapping puts in — so
it is written down first, justified on its own terms, and frozen
before the pilots run.

## The three rules the mapping must obey

1. **Attribute-blind.** The mapping never reads race or sex. If
   framework conflict later co-locates with LBI-flagged pairs, that is
   an empirical finding, not a construction.
2. **Outcome-blind.** The mapping never reads `two_year_recid`. A
   runtime governance layer sits at *decision time*; using the
   realized outcome would answer a different question and would let
   hindsight into a decision-time verdict.
3. **Uniform.** Identical rules for every defendant. No per-case
   adjustment, checked the same way as the doctrinal gates.

## Moral structure of an RAI-assisted classification

**Stakeholders** (constant): `defendant` (individual, patient),
`public` (community, patient), `court` (institution, agent +
authority).

**Act:** the court classifies the defendant at threshold *T*.
*Adverse* means score ≥ *T*. Both of ProPublica's thresholds are run:
*T* = 5 ("medium or high") and *T* = 8 ("high").

**Decision-time ethical facts:**

| fact | kind | subject | present when | severity |
|---|---|---|---|---|
| `liberty_burden` | harm | defendant | adverse | fixed — the liberty cost of an adverse classification does not scale with the decile |
| `residual_risk` | externality | public | ¬adverse ∧ elevated score | scales with score |
| `actuarial_basis` | justice | defendant | adverse | scales inversely with individualized-conduct evidence |
| `consent_absent` | consent | defendant | adverse | fixed |

**Deontic substrate.** `authority_legitimacies`: the court is a
legitimate authority. `maxim`: carries only `treats_persons_as` (the
choice below); `action_kind` is **unset**, because we do not extract
maxims from text and fabricating one would silently drive the
universalizability gate — verified that the compiler then reports that
gate *undetermined* rather than guessing.

**Correction made before the pilots ran (disclosed).** The first draft
of this mapping recorded the defendant's absent consent as a
consent-gate failure. That is a category error and it has been
removed: lawful state coercion does not turn on the coerced party's
consent — that is precisely the work *legitimate authority* does, and
a system that treated every adverse classification as a consent
violation would make the deontic verdict identical to "was the
classification adverse?", i.e. exactly the vacuity the outline names
as a kill condition. The notice-and-contest concern is real, and it is
tested — in the **doctrinal** projection (gate D6, from *Loomis*),
which is where a positive-law requirement belongs. The correction was
made because it is right, not because it produced variation; it is
recorded here so the record shows both states.

## The one substantive modelling choice: `mere_means`

If the mere-means gate fired on every adverse classification, the
deontic verdict would be identical to "was the classification
adverse?" — the pluralism would be vacuous, and the outline names
exactly that as a kill condition. So the mapping draws the Kantian
distinction where the moral literature and *Loomis*'s own group-vs-
individual caution both draw it:

> An adverse action grounded in the defendant's **own adjudicated
> conduct** treats them as a means *and* an end. An adverse action
> resting mainly on the defendant's **membership in a statistical
> reference class** treats them nearer to a mere means — an instance
> used for the protection of others.

Operationalized: adverse ∧ (individualized-conduct evidence below
`CONDUCT_FLOOR`) → `treats_as = mere_means`; adverse ∧ (evidence at or
above the floor) → `treats_as = means_and_end`. Individualized
evidence is `priors_count` (adult adjudicated priors), the only
feature in the public file that records the defendant's own
adjudicated conduct rather than a demographic or juvenile-status fact.

`CONDUCT_FLOOR = 1` is declared now (i.e. a defendant with **zero**
adult priors classified adverse is being carried by the reference
class) and is a **sensitivity parameter**: the pilots report the
conflict statistic across floors ∈ {0, 1, 2, 3, 5} and the seal fixes
one. Note `CONDUCT_FLOOR = 0` disables the distinction entirely and is
the degeneracy control — if the headline result holds only at some
floors, that is reported, not hidden.

**This choice is contestable and is meant to be.** It is the mapping's
load-bearing assumption; a reader who rejects it rejects the RQ2
result, which is why it is stated in one paragraph and given its own
sensitivity sweep.

## What the mapping does NOT do

It does not decide whether the classification was correct, whether
detention was warranted, or whether the instrument is biased. It
converts a decision record into the typed structure the four
projections read, and nothing else.

## Anticipated direction of P2(a) — recorded before the pilots

The outline's initial guess was that conflict would be higher at
*T* = 5 than at *T* = 8. Working through the mapping suggests the
opposite may hold: at *T* = 8 the adverse group has strong
consequentialist support (high risk) while the deontic gates still
fire, which is the classic permit/forbid split; at *T* = 5 many
adverse classifications have weak consequentialist support, so both
frameworks lean negative and *agree*. This note exists so that
whichever direction the pilots show, the record shows the reasoning
was on paper first. If the pilots contradict the outline's guess, P2
is respecified with disclosure **before** sealing (the DB-3
precedent), and the original guess stays on the record.
