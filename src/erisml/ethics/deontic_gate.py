"""Deontic maxim gate for DEME — Kantian universalizability with polarity.

This is the evaluation-engine side of the maxim semantics that erisml-compiler
extracts. The compiler parses a ``Maxim`` (action_kind + polarity) from text;
DEME applies the categorical-imperative universalizability test here, as a veto
check in the pipeline's reflex layer.

Polarity matters: a negated maxim ("did not promise", "refused to lie") is the
maxim of *not performing* the action. Grounded in Kant's perfect/imperfect duty
distinction:

  * negating a prohibition (deceive, harm, coerce, cheat, ...) -> universalisable
  * negating a merely-permissible act (make_or_keep_commitment, disclose) -> ok
  * negating an imperfect duty (help, protect) -> fails contradiction-in-will
  * unknown action -> undetermined (no veto)

The action-kind classifications are derived from the universalizability knowledge
base in ``erisml.ethics.universalizability``, which erisml-compiler imports. Before
3.2 they were a copy of the compiler's table; the table now lives here, once, and
the dependency runs compiler -> lib.
"""

from __future__ import annotations

from dataclasses import dataclass

from .facts import Maxim
from .universalizability import DEFAULT_INSTITUTION_DEPENDENCIES
from .universalizability import IMPERFECT_DUTIES as _IMPERFECT_DUTIES

# The sets follow from the universalizability knowledge base, the one copy.
# Action kinds whose *affirmed* maxim fails universalizability.
PROHIBITIONS: frozenset[str] = frozenset(
    k for k, v in DEFAULT_INSTITUTION_DEPENDENCIES.items() if not v.passes
)
# Positive (imperfect) duties: only these fail when *negated* (omission).
IMPERFECT_DUTIES: frozenset[str] = _IMPERFECT_DUTIES
# Affirmed maxims that are universalisable (permissible or dutiful).
PERMISSIBLE: frozenset[str] = frozenset(
    k for k, v in DEFAULT_INSTITUTION_DEPENDENCIES.items() if v.passes
)


@dataclass(frozen=True)
class MaximGateResult:
    """Outcome of the deontic gate for a single maxim."""

    passes: bool
    """True iff the (possibly negated) maxim is universalisable."""
    vetoed: bool
    """True iff DEME should veto the option on deontic grounds."""
    reason: str
    contradiction_type: (
        str  # contradiction_in_conception | _in_will | no_contradiction | undetermined
    )
    action_kind: str | None
    conflict: bool = False
    """True iff the maxim fails universalizability while its purpose is an imperfect duty: a
    tragic conflict between duties, which DEME escalates to a human rather than vetoes."""


def evaluate_maxim(maxim: Maxim | None) -> MaximGateResult:
    """Apply the universalizability test to a maxim, honouring polarity.

    A maxim that fails universalizability yields ``vetoed=True``, except that an
    affirmed prohibition whose purpose is an imperfect duty ("deceive to protect those
    in my care") yields ``conflict=True`` and no veto: the perfect duty not to deceive
    and the imperfect duty to protect conflict, and a tragic conflict is escalated to a
    human, not settled by the gate (owner decision, 12 October 2026). Unknown or absent
    action kinds never veto (the gate is conservative).
    """
    if maxim is None or maxim.action_kind is None:
        return MaximGateResult(
            passes=True,
            vetoed=False,
            reason="No maxim to test.",
            contradiction_type="undetermined",
            action_kind=None,
        )

    kind = maxim.action_kind
    negated = maxim.polarity == "negated"
    known = kind in PROHIBITIONS or kind in PERMISSIBLE or kind in IMPERFECT_DUTIES

    if not known:
        return MaximGateResult(
            passes=True,
            vetoed=False,
            reason=f"action_kind {kind!r} not in the universalizability KB; cannot test.",
            contradiction_type="undetermined",
            action_kind=kind,
        )

    if not negated:
        purpose = getattr(maxim, "purpose_kind", None)
        if kind in PROHIBITIONS and purpose in IMPERFECT_DUTIES:
            return MaximGateResult(
                passes=False,
                vetoed=False,
                reason=(
                    f"Maxim of {kind!r} is not universalisable, and its purpose, to {purpose}, is "
                    f"an imperfect duty: a tragic conflict between duties, escalated rather than "
                    f"vetoed."
                ),
                contradiction_type=DEFAULT_INSTITUTION_DEPENDENCIES[
                    kind
                ].contradiction_type,
                action_kind=kind,
                conflict=True,
            )
        if kind in PROHIBITIONS:
            return MaximGateResult(
                passes=False,
                vetoed=True,
                reason=f"Maxim of {kind!r} is not universalisable (categorical-imperative failure).",
                contradiction_type="contradiction_in_conception",
                action_kind=kind,
            )
        return MaximGateResult(
            passes=True,
            vetoed=False,
            reason=f"Maxim of {kind!r} is universalisable.",
            contradiction_type="no_contradiction",
            action_kind=kind,
        )

    # Negated maxim: the maxim of NOT performing the action.
    if kind in IMPERFECT_DUTIES:
        return MaximGateResult(
            passes=False,
            vetoed=True,
            reason=(
                f"Refraining from {kind!r} omits an imperfect duty; universal "
                f"omission cannot be willed (contradiction in will)."
            ),
            contradiction_type="contradiction_in_will",
            action_kind=f"not:{kind}",
        )
    return MaximGateResult(
        passes=True,
        vetoed=False,
        reason=f"Not performing {kind!r} is universalisable (refraining from a prohibited or permissible act).",
        contradiction_type="no_contradiction",
        action_kind=f"not:{kind}",
    )
