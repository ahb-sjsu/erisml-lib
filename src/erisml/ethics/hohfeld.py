# ErisML - Hohfeldian Gauge Structure for Normative Positions (V4)
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
#
# Licensed under the AGI-HPC Responsible AI License v1.0.
# See LICENSE file for details.

"""
Hohfeldian normative positions and the Klein four-group V4 of the operations on them.

Wesley Hohfeld's four normative positions (Obligation, Claim, Liberty, No-claim) admit two
demonstrated operations:

- the correlative swap s: O<->C, L<->N, the same relation seen from the other party;
- deontic negation n (written r^2 in earlier work): O<->L, C<->N.

They are commuting involutions, so the group they generate is the Klein four-group
V4 = {e, n, s, sn} = Z2 x Z2: abelian, every element its own inverse. This is machine-checked
in formal/HohfeldV4.lean (Lean 4 + Mathlib). The order-8 dihedral group D4, which would add a
quarter-turn cycling the four positions, is obsolete: the quarter-turn has never been
demonstrated as a normative operation, the Lean file proves it lies outside the generated
group, and the quarter-turn hunt (docs/papers/quarter-turn-hunt) did not find it in a learned
representation. See docs/CONCEPT_REGISTRY.md section 1.

V4 acts on the four positions regularly (simply transitively): for any two positions there is
exactly one operation taking the first to the second. The encoding below makes that explicit.
A position is two bits, (negated, correlated) relative to Obligation, and an operation is the
bit mask it flips:

    O = 00   L = 10   C = 01   N = 11        e = 00   n = 10   s = 01   sn = 11

so applying an operation, and composing two, are both XOR.

References:
    Hohfeld, W.N. (1917). "Fundamental Legal Conceptions as Applied in
    Judicial Reasoning." Yale Law Journal, 26(8), 710-770.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# =============================================================================
# HOHFELDIAN NORMATIVE POSITIONS
# =============================================================================


class HohfeldianState(str, Enum):
    """
    The four Hohfeldian normative positions.

        O -- s -- C
        |         |
        n         n
        |         |
        L -- s -- N

    Natural language mappings:
    - O (Obligation): "Must I do this?" / "Am I obligated?"
    - C (Claim): "Am I entitled?" / "Do I have a right to demand?"
    - L (Liberty): "May I refuse?" / "Am I free to choose?"
    - N (No-claim): "Can they demand?" (no) / "They have no right"

    Correlative pairs (s, perspective swap):
    - O <-> C: if A has an obligation to B, then B has a claim against A
    - L <-> N: if A has a liberty against B, then B has no claim against A

    Negation pairs (n, logical opposites):
    - O <-> L: obligation is the negation of liberty
    - C <-> N: claim is the negation of no-claim
    """

    O = "O"  # noqa: E741 - Obligation: MUST do something
    C = "C"  # Claim: OWED something / has a RIGHT to demand
    L = "L"  # Liberty: FREE to choose / no obligation
    N = "N"  # No-claim: CANNOT demand / no right against other


# =============================================================================
# THE KLEIN FOUR-GROUP V4
# =============================================================================


class V4Element(str, Enum):
    """The four operations on Hohfeldian positions: V4 = {e, n, s, sn} = Z2 x Z2."""

    E = "e"  # identity
    NEG = "n"  # deontic negation (r^2 in earlier work): O<->L, C<->N
    COR = "s"  # correlative swap: O<->C, L<->N
    COR_NEG = "sn"  # both: O<->N, C<->L


# (negated, correlated) bits of each position, and the mask each operation flips
_POSITION_BITS: Dict[HohfeldianState, int] = {
    HohfeldianState.O: 0b00,
    HohfeldianState.L: 0b10,
    HohfeldianState.C: 0b01,
    HohfeldianState.N: 0b11,
}
_BITS_POSITION: Dict[int, HohfeldianState] = {b: p for p, b in _POSITION_BITS.items()}
_ELEMENT_MASK: Dict[V4Element, int] = {
    V4Element.E: 0b00,
    V4Element.NEG: 0b10,
    V4Element.COR: 0b01,
    V4Element.COR_NEG: 0b11,
}
_MASK_ELEMENT: Dict[int, V4Element] = {m: g for g, m in _ELEMENT_MASK.items()}


def v4_elements() -> List[V4Element]:
    """All four elements of V4."""
    return list(V4Element)


def v4_multiply(a: V4Element, b: V4Element) -> V4Element:
    """a * b in V4 (abelian, so the order does not matter): the masks XOR."""
    return _MASK_ELEMENT[_ELEMENT_MASK[a] ^ _ELEMENT_MASK[b]]


def v4_inverse(a: V4Element) -> V4Element:
    """Every element of V4 is its own inverse."""
    return a


def v4_apply_to_state(element: V4Element, state: HohfeldianState) -> HohfeldianState:
    """Apply an operation to a position: flip the position's bits by the element's mask."""
    return _BITS_POSITION[_POSITION_BITS[state] ^ _ELEMENT_MASK[element]]


def v4_between(source: HohfeldianState, target: HohfeldianState) -> V4Element:
    """The unique operation taking `source` to `target` (the action is regular)."""
    return _MASK_ELEMENT[_POSITION_BITS[source] ^ _POSITION_BITS[target]]


def correlative(state: HohfeldianState) -> HohfeldianState:
    """
    The correlative position (s): O<->C, L<->N.

    The perspective swap: if A has an obligation to B, B has a claim against A; if A has a
    liberty against B, B has no claim against A.
    """
    return v4_apply_to_state(V4Element.COR, state)


def negation(state: HohfeldianState) -> HohfeldianState:
    """
    The negated position (n): O<->L, C<->N.

    Obligation is the absence of liberty; claim is the absence of no-claim.
    """
    return v4_apply_to_state(V4Element.NEG, state)


# =============================================================================
# SEMANTIC GATES
# =============================================================================


class SemanticGate(str, Enum):
    """
    Linguistic markers that move a normative position.

    Each gate is one V4 operation (GATE_TO_V4). A gate documented by a single transition (for
    example L -> C) is the unique operation between those positions, since V4 acts regularly.
    """

    # Obligation release (O -> L, n)
    ONLY_IF_CONVENIENT = "only_if_convenient"
    WHEN_YOU_GET_A_CHANCE = "when_you_get_a_chance"
    IF_NOT_TOO_MUCH_TROUBLE = "if_not_too_much_trouble"
    NO_PRESSURE = "no_pressure"

    # Liberty binding (L -> O, n)
    I_PROMISE = "i_promise"
    YOU_MUST = "you_must"
    I_SWEAR = "i_swear"
    ABSOLUTELY = "absolutely"

    # Perspective shift (s)
    FROM_THEIR_PERSPECTIVE = "from_their_perspective"
    THEY_WOULD_SAY = "they_would_say"

    # Claim strengthening and release (L -> C and C -> L, sn)
    YOU_HAVE_EVERY_RIGHT = "you_have_every_right"
    THEY_CANT_DEMAND = "they_cant_demand"


GATE_TO_V4: Dict[SemanticGate, V4Element] = {
    # Obligation release: O -> L is negation
    SemanticGate.ONLY_IF_CONVENIENT: V4Element.NEG,
    SemanticGate.WHEN_YOU_GET_A_CHANCE: V4Element.NEG,
    SemanticGate.IF_NOT_TOO_MUCH_TROUBLE: V4Element.NEG,
    SemanticGate.NO_PRESSURE: V4Element.NEG,
    # Liberty binding: L -> O is negation too (negation is an involution)
    SemanticGate.I_PROMISE: V4Element.NEG,
    SemanticGate.YOU_MUST: V4Element.NEG,
    SemanticGate.I_SWEAR: V4Element.NEG,
    SemanticGate.ABSOLUTELY: V4Element.NEG,
    # Perspective shift: the correlative
    SemanticGate.FROM_THEIR_PERSPECTIVE: V4Element.COR,
    SemanticGate.THEY_WOULD_SAY: V4Element.COR,
    # L -> C and C -> L: the correlative of the negation. These two were quarter turns under the
    # obsolete D4 reading, which agreed with sn on their documented transitions and differed
    # only on the positions they were never documented for.
    SemanticGate.YOU_HAVE_EVERY_RIGHT: V4Element.COR_NEG,
    SemanticGate.THEY_CANT_DEMAND: V4Element.COR_NEG,
}


def apply_semantic_gate(gate: SemanticGate, state: HohfeldianState) -> HohfeldianState:
    """Apply a semantic gate's operation to a Hohfeldian position."""
    return v4_apply_to_state(GATE_TO_V4[gate], state)


# =============================================================================
# VERDICT AND MEASUREMENT
# =============================================================================


@dataclass
class HohfeldianVerdict:
    """
    A classification of a party's normative position.

    This is the "measurement" in the gauge theory sense.
    """

    party_name: str
    state: HohfeldianState
    expected: Optional[HohfeldianState] = None
    confidence: float = 1.0

    @property
    def is_correct(self) -> Optional[bool]:
        """Check if verdict matches expected state (if known)."""
        if self.expected is None:
            return None
        return self.state == self.expected

    @property
    def is_correlative_consistent(self) -> bool:
        """Check if state is one of the correlative pair."""
        return self.state in (HohfeldianState.O, HohfeldianState.C) or self.state in (
            HohfeldianState.L,
            HohfeldianState.N,
        )


# =============================================================================
# BOND INDEX (CORRELATIVE SYMMETRY MEASURE)
# =============================================================================


def compute_bond_index(
    verdicts_a: List[HohfeldianVerdict],
    verdicts_b: List[HohfeldianVerdict],
    tau: float = 1.0,
) -> float:
    """
    Compute the bond index measuring deviation from correlative symmetry.

    The bond index quantifies how consistently a reasoner applies the
    correlative transformation when shifting perspective from party A to B.

    Args:
        verdicts_a: Classifications of party A's positions
        verdicts_b: Classifications of party B's positions (same scenarios)
        tau: Temperature/scaling parameter

    Returns:
        Bond index in [0, 1/tau]:
        - 0: Perfect correlative symmetry (all B = s(A))
        - 1/tau: Complete antisymmetry

    The correlative gauge principle requires:
        verdict_b = correlative(verdict_a)

    Violations indicate systematic asymmetries in moral reasoning.
    """
    if len(verdicts_a) != len(verdicts_b):
        raise ValueError("Verdict lists must have equal length")

    if not verdicts_a:
        return 0.0

    defects = 0
    total = 0

    for va, vb in zip(verdicts_a, verdicts_b):
        expected_b = correlative(va.state)
        if vb.state != expected_b:
            defects += 1
        total += 1

    return (defects / total) / tau


def compute_wilson_observable(
    path: List[V4Element],
    initial_state: HohfeldianState,
    observed_final: HohfeldianState,
) -> Tuple[V4Element, bool]:
    """
    Compute the Wilson observable for a path of transformations.

    The holonomy of the path is the product of its elements. V4 is abelian, so the holonomy
    depends only on how many times each of n and s occurs (mod 2), never on their order: two
    paths with the same counts must end in the same position. An observed path dependence is
    therefore a measured violation of the V4 structure, not a feature of it.

    Args:
        path: Sequence of V4 elements (transformations applied)
        initial_state: Starting Hohfeldian position
        observed_final: Actually observed final state

    Returns:
        (holonomy, matched): The predicted group element and whether
        the observation matched the prediction.
    """
    holonomy = V4Element.E
    for g in path:
        holonomy = v4_multiply(holonomy, g)
    predicted_final = v4_apply_to_state(holonomy, initial_state)
    return holonomy, observed_final == predicted_final


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "HohfeldianState",
    "V4Element",
    "SemanticGate",
    # Group operations
    "v4_elements",
    "v4_multiply",
    "v4_inverse",
    "v4_apply_to_state",
    "v4_between",
    "correlative",
    "negation",
    # Semantic gates
    "GATE_TO_V4",
    "apply_semantic_gate",
    # Verdict
    "HohfeldianVerdict",
    # Bond index
    "compute_bond_index",
    "compute_wilson_observable",
]
