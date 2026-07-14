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

The action-kind classifications mirror erisml-compiler's
``delta/universalizability.py`` knowledge base. They are duplicated here
deliberately: the lib must be able to gate maxims without a hard dependency on
the compiler (the dependency direction is compiler -> lib).
"""

from __future__ import annotations

from dataclasses import dataclass

from .facts import Maxim

# Action kinds whose *affirmed* maxim fails universalizability.
PROHIBITIONS: frozenset[str] = frozenset(
    {
        "deceive",
        "break_commitment",
        "cheat",
        "impose_externality",
        "coerce",
        "coerce_or_be_coerced",
        "inflict_harm",
        "use_as_means",
        "refuse",
    }
)
# Positive (imperfect) duties: only these fail when *negated* (omission).
IMPERFECT_DUTIES: frozenset[str] = frozenset({"help", "protect"})
# Affirmed maxims that are universalisable (permissible or dutiful).
PERMISSIBLE: frozenset[str] = frozenset(
    {
        "make_or_keep_commitment",
        "protect",
        "help",
        "disclose",
        "act_under_norm",
        "act_under_authority",
    }
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


def evaluate_maxim(maxim: Maxim | None) -> MaximGateResult:
    """Apply the universalizability test to a maxim, honouring polarity.

    A maxim that fails universalizability yields ``vetoed=True``. Unknown or
    absent action kinds never veto (the gate is conservative).
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
