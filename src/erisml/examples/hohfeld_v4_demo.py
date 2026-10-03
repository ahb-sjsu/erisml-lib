# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
hohfeld_v4_demo.py

Demonstration of the Hohfeldian gauge structure: the Klein four-group V4.

- The four Hohfeldian positions: Obligation (O), Claim (C), Liberty (L), No-claim (N)
- The two demonstrated operations, the correlative swap s and deontic negation n
- They commute and generate V4 = {e, n, s, sn} (formal/HohfeldV4.lean); the order-8 dihedral
  group D4 is obsolete (docs/CONCEPT_REGISTRY.md section 1)
- V4 acts regularly: one operation takes any position to any other
- Holonomy is independent of order, so an order effect is a measured violation

Usage:
    python -m erisml.examples.hohfeld_v4_demo

References:
    Hohfeld, W.N. (1917). "Fundamental Legal Conceptions as Applied in
    Judicial Reasoning." Yale Law Journal, 26(8), 710-770.
"""

from __future__ import annotations

import itertools

from erisml.ethics.hohfeld import (
    HohfeldianState,
    HohfeldianVerdict,
    SemanticGate,
    V4Element,
    apply_semantic_gate,
    compute_bond_index,
    compute_wilson_observable,
    correlative,
    negation,
    v4_apply_to_state,
    v4_between,
    v4_multiply,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_hohfeldian_positions() -> None:
    """Demonstrate the four Hohfeldian normative positions."""
    print_section("The Four Hohfeldian Normative Positions")

    print(
        """
The Hohfeldian square arranges four fundamental normative positions:

         O (Obligation) -------- C (Claim)
              |                      |
              |                      |
         L (Liberty) ---------- N (No-claim)

Correlative pairs (perspective swap):
  - O <-> C: If A is obligated to B, then B has a claim against A
  - L <-> N: If A is at liberty against B, then B has no-claim against A

Negation pairs (logical opposites):
  - O <-> L: Obligation vs Liberty
  - C <-> N: Claim vs No-claim
"""
    )

    print("States:", [s.value for s in HohfeldianState])


def demo_v4_group() -> None:
    """Demonstrate the Klein four-group V4."""
    print_section("The Klein Four-Group V4")
    print(
        """
The correlative s and the negation n are commuting involutions, so they generate
V4 = {e, n, s, sn}: four elements, each its own inverse, all commuting.

Multiplication table:
"""
    )
    elems = list(V4Element)
    print("        " + "".join(f"{b.value:>4s}" for b in elems))
    for a in elems:
        print(
            f"  {a.value:>4s}  "
            + "".join(f"{v4_multiply(a, b).value:>4s}" for b in elems)
        )


def demo_regular_action() -> None:
    """One operation between any two positions."""
    print_section("A Regular Action: One Operation Between Any Two Positions")
    for x, y in itertools.product(HohfeldianState, repeat=2):
        g = v4_between(x, y)
        assert v4_apply_to_state(g, x) == y
        print(f"  {x.value} -> {y.value}: {g.value}")


def demo_order_independence() -> None:
    """V4 is abelian: the holonomy of a path ignores its order."""
    print_section("Wilson Observable: Order Never Matters in V4")
    path = [V4Element.COR, V4Element.NEG, V4Element.COR]
    for p in sorted(set(itertools.permutations(path))):
        holonomy, _ = compute_wilson_observable(
            list(p), HohfeldianState.O, HohfeldianState.O
        )
        print(f"  path {[g.value for g in p]}: holonomy {holonomy.value}")
    print(
        """
Every ordering has the same holonomy. A reasoner whose verdicts depend on the order
of a perspective swap and a negation is violating V4, which is what the bond index
and the Wilson observable measure.
"""
    )


def demo_correlative_symmetry() -> None:
    """Demonstrate correlative symmetry (s)."""
    print_section("Correlative Symmetry (Perspective Swap)")

    print("The correlative operation swaps perspectives between parties:\n")

    for state in HohfeldianState:
        corr = correlative(state)
        print(f"  correlative({state.value}) = {corr.value}")

    print(
        """
Example: Alice lends money to Bob
  - Alice's perspective: Bob has OBLIGATION to repay (O)
  - Bob's perspective: Alice has CLAIM to receive payment (C)

The correlative symmetry captures this: correlative(O) = C
"""
    )


def demo_negation_symmetry() -> None:
    """Demonstrate negation symmetry (n)."""
    print_section("Negation Symmetry (Logical Opposites)")

    print("The negation operation (n) maps to logical opposites:\n")

    for state in HohfeldianState:
        neg = negation(state)
        print(f"  negation({state.value}) = {neg.value}")

    print(
        """
Example: "You must do X" vs "You may refuse X"
  - "Must" implies OBLIGATION (O)
  - "May refuse" implies LIBERTY (L)

These are logical negations: negation(O) = L
"""
    )


def demo_semantic_gates() -> None:
    """Demonstrate semantic gates (linguistic triggers)."""
    print_section("Semantic Gates (Linguistic Triggers)")

    print("Semantic gates are phrases that trigger V4 operations:\n")

    examples = [
        (SemanticGate.ONLY_IF_CONVENIENT, HohfeldianState.O),
        (SemanticGate.I_PROMISE, HohfeldianState.L),
        (SemanticGate.FROM_THEIR_PERSPECTIVE, HohfeldianState.O),
    ]

    for gate, initial in examples:
        final = apply_semantic_gate(gate, initial)
        print(f'  "{gate.value}" applied to {initial.value} -> {final.value}')

    print(
        """
Example: "Please help me with this task, but only if convenient."
  - Base state: O (Obligation to help)
  - Gate: "only if convenient" (negation, n)
  - Result: L (Liberty - free to refuse)
"""
    )


def demo_bond_index() -> None:
    """Demonstrate bond index computation."""
    print_section("Bond Index (Correlative Symmetry Measure)")

    print(
        """
The bond index measures deviation from correlative symmetry.
It quantifies how consistently a reasoner applies perspective swaps.
"""
    )

    # Perfect symmetry case
    verdicts_a = [
        HohfeldianVerdict("A", HohfeldianState.O),
        HohfeldianVerdict("A", HohfeldianState.L),
        HohfeldianVerdict("A", HohfeldianState.C),
    ]
    verdicts_b_perfect = [
        HohfeldianVerdict("B", HohfeldianState.C),  # correlative(O) = C
        HohfeldianVerdict("B", HohfeldianState.N),  # correlative(L) = N
        HohfeldianVerdict("B", HohfeldianState.O),  # correlative(C) = O
    ]

    bi_perfect = compute_bond_index(verdicts_a, verdicts_b_perfect)
    print(f"Perfect correlative symmetry: Bond Index = {bi_perfect:.3f}")

    # Imperfect symmetry case
    verdicts_b_imperfect = [
        HohfeldianVerdict("B", HohfeldianState.C),  # correct
        HohfeldianVerdict("B", HohfeldianState.L),  # WRONG - should be N
        HohfeldianVerdict("B", HohfeldianState.O),  # correct
    ]

    bi_imperfect = compute_bond_index(verdicts_a, verdicts_b_imperfect)
    print(f"One violation (1/3 wrong): Bond Index = {bi_imperfect:.3f}")

    print(
        """
Interpretation:
  - Bond Index = 0: Perfect correlative symmetry
  - Bond Index > 0: Systematic asymmetry in moral reasoning
"""
    )


def main() -> None:
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  HOHFELDIAN GAUGE STRUCTURE: THE KLEIN FOUR-GROUP V4")
    print("=" * 70)

    demo_hohfeldian_positions()
    demo_v4_group()
    demo_correlative_symmetry()
    demo_negation_symmetry()
    demo_regular_action()
    demo_semantic_gates()
    demo_bond_index()
    demo_order_independence()


if __name__ == "__main__":
    main()
