# ErisML - Tests for the V4 structure of Hohfeldian positions
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University

"""
Tests for the Klein four-group V4 acting on Hohfeldian positions (formal/HohfeldV4.lean).

These tests verify:
1. V4's group laws: closure, identity, every element its own inverse, associativity, abelian
2. The two demonstrated operations, correlative s and negation n, generate exactly V4
3. The action respects the group law, is faithful, and is regular (one operation per pair)
4. Semantic gates, the bond index and the Wilson observable on V4
"""

import itertools

import pytest

from erisml.ethics.hohfeld import (
    GATE_TO_V4,
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
    v4_elements,
    v4_inverse,
    v4_multiply,
)

O, C, L, N = (  # noqa: E741
    HohfeldianState.O,
    HohfeldianState.C,
    HohfeldianState.L,
    HohfeldianState.N,
)
E, NEG, COR, COR_NEG = V4Element.E, V4Element.NEG, V4Element.COR, V4Element.COR_NEG


class TestV4GroupLaws:
    def test_closure(self):
        for a, b in itertools.product(V4Element, repeat=2):
            assert v4_multiply(a, b) in V4Element

    def test_identity(self):
        for a in V4Element:
            assert v4_multiply(E, a) == a == v4_multiply(a, E)

    def test_every_element_is_its_own_inverse(self):
        for a in V4Element:
            assert v4_inverse(a) == a and v4_multiply(a, a) == E

    def test_associativity(self):
        for a, b, c in itertools.product(V4Element, repeat=3):
            assert v4_multiply(v4_multiply(a, b), c) == v4_multiply(
                a, v4_multiply(b, c)
            )

    def test_abelian(self):
        for a, b in itertools.product(V4Element, repeat=2):
            assert v4_multiply(a, b) == v4_multiply(b, a)

    def test_sn_is_the_product_of_the_generators(self):
        assert v4_multiply(COR, NEG) == COR_NEG and len(v4_elements()) == 4


class TestTheDemonstratedOperationsGenerateV4:
    def test_correlative_and_negation_generate_exactly_v4(self):
        generated = {E, COR, NEG}
        while True:
            new = {v4_multiply(a, b) for a in generated for b in generated} - generated
            if not new:
                break
            generated |= new
        assert generated == set(V4Element)

    def test_correlative_is_s(self):
        assert [correlative(x) for x in (O, C, L, N)] == [C, O, N, L]

    def test_negation_is_n(self):
        assert [negation(x) for x in (O, C, L, N)] == [L, N, O, C]

    def test_correlative_and_negation_commute_on_every_position(self):
        for x in HohfeldianState:
            assert correlative(negation(x)) == negation(correlative(x))


class TestTheAction:
    def test_action_respects_group_law(self):
        for a, b in itertools.product(V4Element, repeat=2):
            for x in HohfeldianState:
                assert v4_apply_to_state(v4_multiply(a, b), x) == v4_apply_to_state(
                    a, v4_apply_to_state(b, x)
                )

    def test_action_is_faithful(self):
        perms = {
            g: tuple(v4_apply_to_state(g, x) for x in HohfeldianState)
            for g in V4Element
        }
        assert len(set(perms.values())) == 4

    def test_action_is_regular_one_operation_per_pair_of_positions(self):
        for x, y in itertools.product(HohfeldianState, repeat=2):
            movers = [g for g in V4Element if v4_apply_to_state(g, x) == y]
            assert movers == [v4_between(x, y)]

    def test_no_operation_cycles_the_four_positions(self):
        """The quarter-turn O -> C -> L -> N is not in V4: every element has order at most 2."""
        for g in V4Element:
            assert all(
                v4_apply_to_state(g, v4_apply_to_state(g, x)) == x
                for x in HohfeldianState
            )


class TestSemanticGates:
    def test_every_gate_is_a_v4_operation(self):
        assert set(GATE_TO_V4) == set(SemanticGate)
        assert set(GATE_TO_V4.values()) <= set(V4Element)

    def test_obligation_release_is_negation(self):
        assert apply_semantic_gate(SemanticGate.ONLY_IF_CONVENIENT, O) == L

    def test_promise_binds_liberty(self):
        assert apply_semantic_gate(SemanticGate.I_PROMISE, L) == O

    def test_perspective_shift_is_correlative(self):
        for x in HohfeldianState:
            assert apply_semantic_gate(
                SemanticGate.FROM_THEIR_PERSPECTIVE, x
            ) == correlative(x)

    def test_claim_gates_keep_their_documented_transitions(self):
        assert apply_semantic_gate(SemanticGate.YOU_HAVE_EVERY_RIGHT, L) == C
        assert apply_semantic_gate(SemanticGate.THEY_CANT_DEMAND, C) == L

    def test_every_gate_is_an_involution(self):
        for gate in SemanticGate:
            for x in HohfeldianState:
                assert apply_semantic_gate(gate, apply_semantic_gate(gate, x)) == x


class TestBondIndex:
    """Test bond index computation."""

    def test_perfect_symmetry_gives_zero(self):
        """Perfect correlative symmetry → bond index = 0."""
        verdicts_a = [
            HohfeldianVerdict(party_name="A", state=HohfeldianState.O),
            HohfeldianVerdict(party_name="A", state=HohfeldianState.L),
        ]
        verdicts_b = [
            HohfeldianVerdict(
                party_name="B", state=HohfeldianState.C
            ),  # correlative of O
            HohfeldianVerdict(
                party_name="B", state=HohfeldianState.N
            ),  # correlative of L
        ]

        bond = compute_bond_index(verdicts_a, verdicts_b)
        assert bond == 0.0

    def test_complete_violation_gives_one_over_tau(self):
        """Complete antisymmetry → bond index = 1/tau."""
        verdicts_a = [
            HohfeldianVerdict(party_name="A", state=HohfeldianState.O),
            HohfeldianVerdict(party_name="A", state=HohfeldianState.L),
        ]
        # Wrong correlatives
        verdicts_b = [
            HohfeldianVerdict(party_name="B", state=HohfeldianState.L),  # should be C
            HohfeldianVerdict(party_name="B", state=HohfeldianState.O),  # should be N
        ]

        bond = compute_bond_index(verdicts_a, verdicts_b, tau=1.0)
        assert bond == 1.0

    def test_half_violations(self):
        """50% violations → bond index = 0.5/tau."""
        verdicts_a = [
            HohfeldianVerdict(party_name="A", state=HohfeldianState.O),
            HohfeldianVerdict(party_name="A", state=HohfeldianState.L),
        ]
        verdicts_b = [
            HohfeldianVerdict(party_name="B", state=HohfeldianState.C),  # correct
            HohfeldianVerdict(party_name="B", state=HohfeldianState.O),  # wrong
        ]

        bond = compute_bond_index(verdicts_a, verdicts_b, tau=1.0)
        assert bond == 0.5

    def test_tau_scaling(self):
        """tau parameter scales the result."""
        verdicts_a = [HohfeldianVerdict(party_name="A", state=HohfeldianState.O)]
        verdicts_b = [
            HohfeldianVerdict(party_name="B", state=HohfeldianState.L)
        ]  # wrong

        bond_tau_1 = compute_bond_index(verdicts_a, verdicts_b, tau=1.0)
        bond_tau_2 = compute_bond_index(verdicts_a, verdicts_b, tau=2.0)

        assert bond_tau_1 == 1.0
        assert bond_tau_2 == 0.5

    def test_empty_lists_give_zero(self):
        """Empty verdict lists → bond index = 0."""
        bond = compute_bond_index([], [])
        assert bond == 0.0

    def test_mismatched_lengths_raise(self):
        """Mismatched list lengths raise ValueError."""
        verdicts_a = [HohfeldianVerdict(party_name="A", state=HohfeldianState.O)]
        verdicts_b = []

        with pytest.raises(ValueError):
            compute_bond_index(verdicts_a, verdicts_b)


class TestWilsonObservable:
    def test_identity_path(self):
        for x in HohfeldianState:
            assert compute_wilson_observable([], x, x) == (E, True)

    def test_a_closed_path_returns_to_start(self):
        for x in HohfeldianState:
            assert compute_wilson_observable([COR, NEG, COR, NEG], x, x) == (E, True)

    def test_holonomy_does_not_depend_on_the_order_of_the_path(self):
        """V4 is abelian: any reordering of a path has the same holonomy, so an observed
        order effect is a measured violation of V4, not a feature of it."""
        path = [COR, NEG, NEG, COR_NEG, COR]
        holonomies = {
            compute_wilson_observable(list(p), O, O)[0]
            for p in itertools.permutations(path)
        }
        assert holonomies == {COR_NEG}  # s twice and n twice cancel; sn remains

    def test_wrong_observation_not_matched(self):
        holonomy, matched = compute_wilson_observable([COR], O, L)
        assert holonomy == COR and matched is False


class TestHohfeldianVerdict:
    """Test HohfeldianVerdict dataclass."""

    def test_is_correct_when_matching(self):
        """is_correct returns True when state matches expected."""
        v = HohfeldianVerdict(
            party_name="Test",
            state=HohfeldianState.O,
            expected=HohfeldianState.O,
        )
        assert v.is_correct is True

    def test_is_correct_when_not_matching(self):
        """is_correct returns False when state differs from expected."""
        v = HohfeldianVerdict(
            party_name="Test",
            state=HohfeldianState.O,
            expected=HohfeldianState.L,
        )
        assert v.is_correct is False

    def test_is_correct_when_no_expected(self):
        """is_correct returns None when no expected value."""
        v = HohfeldianVerdict(
            party_name="Test",
            state=HohfeldianState.O,
        )
        assert v.is_correct is None
