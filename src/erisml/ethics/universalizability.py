"""Kantian universalizability: the knowledge base behind DEME's deontic gate.

Each known action kind records the institution it presupposes, the form of
contradiction its universalised maxim meets, and a justification. The deontic
gate (erisml.ethics.deontic_gate) derives its sets from this table, and
erisml-compiler imports it rather than keeping a copy. It was written in
erisml-compiler (delta/universalizability.py, v0.8) and moved here in 3.2 so
that the ethics library holds the one copy.

## Background

Kant identified two ways the categorical imperative can be violated:

1. **Contradiction in Conception (CIC).** Universalize the maxim. If
   the resulting universal law is *internally incoherent* — if the
   universalized act becomes impossible because it presupposes an
   institution that the universalization destroys — the maxim cannot
   be willed without contradiction. Lying presupposes truth-telling;
   universalizing lying destroys the institution; lying becomes
   impossible. False promises, cheating, theft fall here.

2. **Contradiction in Will (CIW).** Universalize the maxim. The
   universal law is coherent (the act remains possible) but the
   *agent* cannot rationally will it because doing so would defeat
   their own broader ends. Universal refusal to help others is
   coherent (people can decline to help), but a rational agent
   cannot consistently will it: they themselves will need help at
   some point. Indifference to suffering, refusing aid, neglect
   fall here.

## Implementation strategy

For each `action_kind` we know how to handle, we record:
  - which institution(s) the act *presupposes*
  - whether universalizing the act destroys those institutions (CIC)
  - whether universalizing the act defeats agent's typical ends (CIW)
  - a brief justification anchored to a Kantian primary source

When the gate runs, we look up the action_kind, return the
classification, and surface the institution + contradiction-type +
justification in the GateFinding's detail block. Unknown action_kinds
return `passed=True` (we can't run the test without knowing the
institution) and record `result=undetermined` rather than silently
passing.

## What this is

  - A principled lookup table grounded in Kantian textual semantics,
    with each entry citing the form of contradiction.
  - Auditable: every gate firing surfaces *which* institution would
    be destroyed and *why*.
  - Extensible: callers can pass a custom mapping to test alternate
    institutional interpretations.

## What this is NOT

  - Not a real universalised-world model. We don't actually build
    the universalized-world ontology and run a coherence check on
    it. That would require a much richer semantics — possible
    future work via SMT solving over action-institution graphs.
  - Not the final word on contested cases. Several action_kinds
    (e.g. "disclose") are non-universalisable-by-some-readings and
    universalisable-by-others. We pick a defensible reading and
    record the contestability in `detail.contested_reading`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ContradictionType = Literal[
    "contradiction_in_conception",
    "contradiction_in_will",
    "no_contradiction",
    "undetermined",
]


@dataclass(frozen=True)
class InstitutionDependency:
    """Records what institution an action_kind presupposes and what
    happens when the maxim is universalised.

    `passes` is the test result: True iff the maxim is universalisable
    in this reading. False iff it fails CIC or CIW.
    """

    action_kind: str
    presupposes: tuple[str, ...]
    """The institutions / shared practices the action depends on
    being intact in order to be possible (e.g. lying presupposes
    truth-telling; promising presupposes trust-in-promises)."""

    contradiction_type: ContradictionType
    passes: bool
    justification: str
    """One-sentence Kantian gloss, citation-ready."""
    contested_reading: str | None = None
    """If this action_kind has a non-trivial contested reading
    (e.g. "disclose" is universalisable for whistleblowers but not
    for confidants), record it here. Surfaced in the gate's detail
    block so the audit trail captures the contestability."""


# ---------------------------------------------------------------------------
# Default knowledge base
# ---------------------------------------------------------------------------
#
# Each entry is grounded in Kantian primary-source semantics. The
# justifications are short paraphrases, not direct quotations, but
# they pin to standard Kantian readings of the test.

DEFAULT_INSTITUTION_DEPENDENCIES: dict[str, InstitutionDependency] = {
    "deceive": InstitutionDependency(
        action_kind="deceive",
        presupposes=("truth-telling", "trust-in-statements"),
        contradiction_type="contradiction_in_conception",
        passes=False,
        justification=(
            "A maxim of deceiving, universalised, destroys the "
            "institution of truthful communication that deception "
            "itself presupposes — the universalised act becomes "
            "impossible (Kant, Groundwork II)."
        ),
    ),
    "make_or_keep_commitment": InstitutionDependency(
        action_kind="make_or_keep_commitment",
        presupposes=("trust-in-promises",),
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            "Universalising the maxim of keeping commitments preserves "
            "the institution of promising rather than destroying it. "
            "No contradiction in conception or will."
        ),
    ),
    "break_commitment": InstitutionDependency(
        action_kind="break_commitment",
        presupposes=("trust-in-promises", "stability-of-vows"),
        contradiction_type="contradiction_in_conception",
        passes=False,
        justification=(
            "Universalising commitment-breaking destroys the trust on "
            "which the institution of making commitments depends — "
            "commitments become meaningless, hence impossible to give."
        ),
    ),
    "cheat": InstitutionDependency(
        action_kind="cheat",
        presupposes=("rule-following-by-most", "trust-in-fair-dealing"),
        contradiction_type="contradiction_in_conception",
        passes=False,
        justification=(
            "Cheating presupposes that others abide by the rule one is "
            "violating. Universalised, no one follows the rule, the "
            "advantage cheating seeks is gone, and the act becomes "
            "impossible — classic CIC."
        ),
    ),
    "impose_externality": InstitutionDependency(
        action_kind="impose_externality",
        presupposes=("standing-of-non-consenting-parties",),
        contradiction_type="contradiction_in_will",
        passes=False,
        justification=(
            "Universalising the imposition of cost on non-consenting "
            "third parties defeats any agent's own standing not to "
            "bear costs they did not consent to — the agent cannot "
            "consistently will it without abandoning their own status "
            "as a self-determining end."
        ),
    ),
    "coerce": InstitutionDependency(
        action_kind="coerce",
        presupposes=("autonomy-of-other-agents",),
        contradiction_type="contradiction_in_will",
        passes=False,
        justification=(
            "Universalising coercion defeats the very capacity for "
            "self-determination that makes rational agency possible. "
            "The maxim cannot be willed without willing one's own "
            "non-autonomy."
        ),
    ),
    "coerce_or_be_coerced": InstitutionDependency(
        action_kind="coerce_or_be_coerced",
        presupposes=("autonomy-of-other-agents",),
        contradiction_type="contradiction_in_will",
        passes=False,
        justification=(
            "When coercion is part of the situation's structure, "
            "universalising any maxim that participates in it defeats "
            "the autonomy that the test is meant to protect."
        ),
    ),
    "inflict_harm": InstitutionDependency(
        action_kind="inflict_harm",
        presupposes=("bodily-integrity-of-others",),
        contradiction_type="contradiction_in_will",
        passes=False,
        justification=(
            "Universal harm-infliction defeats the agent's own claim "
            "to bodily integrity — they cannot rationally will to "
            "live in a world where everyone harms whomever they wish."
        ),
    ),
    "protect": InstitutionDependency(
        action_kind="protect",
        presupposes=("vulnerability-of-protected-parties",),
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            "Universal protection preserves the institutions of care "
            "and mutual aid; no contradiction in conception or will."
        ),
    ),
    "help": InstitutionDependency(
        action_kind="help",
        presupposes=(),
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            "Helping is universalisable. The contrary — universal "
            "refusal to help — IS contradictory in will (the agent "
            "will themselves need help). Helping faces no such "
            "contradiction."
        ),
    ),
    "refuse": InstitutionDependency(
        action_kind="refuse",
        presupposes=(),
        contradiction_type="contradiction_in_will",
        passes=False,
        justification=(
            "Universal refusal to help others is coherent (CIC passes) "
            "but cannot be rationally willed: the agent will themselves "
            "need help at some point, contradicting their own ends. "
            "Kant's classic Groundwork example."
        ),
    ),
    "use_as_means": InstitutionDependency(
        action_kind="use_as_means",
        presupposes=("end-status-of-rational-agents",),
        contradiction_type="contradiction_in_will",
        passes=False,
        justification=(
            "Using rational agents as mere means defeats the "
            "humanity formulation of the categorical imperative: "
            "treat humanity, whether in one's own person or another's, "
            "always at the same time as an end and never merely as a "
            "means (Kant, Groundwork II)."
        ),
    ),
    "disclose": InstitutionDependency(
        action_kind="disclose",
        presupposes=("trust-in-confidants",),
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            "Disclosure of wrongdoing is universalisable: a world in "
            "which all whistleblowers report institutional wrongdoing "
            "is coherent and arguably more, not less, sustainable than "
            "one of universal silence."
        ),
        contested_reading=(
            "Contested: disclosure of *confidential* information (medical, "
            "legal, religious) presupposes the institution of "
            "confidentiality, which universal disclosure would destroy. "
            "On that reading 'disclose' fails CIC. The compiler picks "
            "the whistleblower reading by default; callers compiling "
            "confidentiality cases should pass an alternate mapping."
        ),
    ),
    "act_under_norm": InstitutionDependency(
        action_kind="act_under_norm",
        presupposes=("the-norm-itself",),
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            "Acting in accordance with the norm one is supposed to "
            "follow is universalisable by construction."
        ),
    ),
    "act_under_authority": InstitutionDependency(
        action_kind="act_under_authority",
        presupposes=("legitimacy-of-the-authority",),
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            "Universal compliance with legitimate authority is "
            "universalisable. (When the authority's legitimacy is "
            "itself in question, the legitimate_authority gate handles "
            "that — universalizability tests the maxim, not the "
            "authority.)"
        ),
    ),
}


# Imperfect (positive) duties: the only kinds whose *omission* is itself a
# categorical-imperative failure. Refraining from a prohibition or from a merely
# permissible act is fine; refusing universal aid/protection cannot be willed.
IMPERFECT_DUTIES: frozenset[str] = frozenset({"help", "protect"})


def _lookup(
    action_kind: str | None,
    mapping: dict[str, InstitutionDependency] | None,
) -> InstitutionDependency:
    if action_kind is None:
        return InstitutionDependency(
            action_kind="<unknown>",
            presupposes=(),
            contradiction_type="undetermined",
            passes=True,  # benefit of doubt; gate records undetermined
            justification="No action_kind extracted; test indeterminate.",
        )
    m = mapping if mapping is not None else DEFAULT_INSTITUTION_DEPENDENCIES
    if action_kind not in m:
        return InstitutionDependency(
            action_kind=action_kind,
            presupposes=(),
            contradiction_type="undetermined",
            passes=True,
            justification=(
                f"action_kind {action_kind!r} not in the universalisability "
                f"knowledge base; cannot test."
            ),
        )
    return m[action_kind]


def test_universalizability(
    action_kind: str | None,
    *,
    polarity: str = "affirmed",
    mapping: dict[str, InstitutionDependency] | None = None,
) -> InstitutionDependency:
    """Test whether a maxim's action_kind is universalisable.

    ``polarity`` reflects whether the maxim is asserted or negated in the
    source ("did not promise", "refused to lie"). A negated maxim is the maxim
    of *not performing* the action, which can have the opposite universalisability
    status, so it is tested separately rather than as the affirmed action.

    Returns the `InstitutionDependency` for the (possibly negated) action_kind.
    Unknown / None action kinds return an `undetermined` entry rather than
    silently passing.
    """
    base = _lookup(action_kind, mapping)
    if polarity != "negated":
        return base

    neg_kind = f"not:{base.action_kind}"

    # Negation of an indeterminate action is also indeterminate.
    if base.contradiction_type == "undetermined":
        return InstitutionDependency(
            action_kind=neg_kind,
            presupposes=base.presupposes,
            contradiction_type="undetermined",
            passes=True,
            justification=(
                f"Negated maxim of {base.action_kind!r}, which is outside the "
                f"knowledge base; the negation is likewise indeterminate."
            ),
        )

    # Omission of an imperfect (positive) duty fails contradiction-in-will.
    if action_kind in IMPERFECT_DUTIES:
        return InstitutionDependency(
            action_kind=neg_kind,
            presupposes=base.presupposes,
            contradiction_type="contradiction_in_will",
            passes=False,
            justification=(
                f"Refraining from {action_kind!r} is the omission of an imperfect "
                f"duty. Universal omission cannot be rationally willed — the agent "
                f"will themselves stand in need of {action_kind} (Kant, Groundwork II)."
            ),
        )

    # Negating a prohibition or a merely-permissible act is universalisable.
    return InstitutionDependency(
        action_kind=neg_kind,
        presupposes=base.presupposes,
        contradiction_type="no_contradiction",
        passes=True,
        justification=(
            f"The maxim of NOT performing {base.action_kind!r} is universalisable: "
            f"refraining from a prohibited or merely-permissible act introduces no "
            f"contradiction in conception or will."
        ),
    )
