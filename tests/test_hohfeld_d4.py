# ErisML - Tests for D4 Gauge Structure
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University

"""
Comprehensive tests for the D4 dihedral group acting on Hohfeldian positions.

These tests verify:
1. D4 group axioms (closure, associativity, identity, inverses)
2. Defining relations (r⁴=e, s²=e, srs=r⁻¹)
3. Non-abelian structure (rs ≠ sr)
4. Semantic mappings (correlative=s, negation=r²)
5. Bond index computation
6. Abelian subgroup identification
"""

import pytest

from erisml.ethics.hohfeld import (
    D4Element,
    HohfeldianState,
    HohfeldianVerdict,
    SemanticGate,
    apply_semantic_gate,
    compute_bond_index,
    compute_wilson_observable,
    correlative,
    d4_apply_to_state,
    d4_inverse,
    d4_multiply,
    get_klein_four_subgroup,
    is_in_klein_four,
    negation,
    requires_nonabelian_structure,
)


class TestD4GroupAxioms:
    """Test that D4 satisfies group axioms."""

    def test_closure(self):
        """Product of any two elements is in the group."""
        elements = list(D4Element)
        for a in elements:
            for b in elements:
                result = d4_multiply(a, b)
                assert result in elements

    def test_identity(self):
        """Identity element e satisfies e*a = a*e = a."""
        for a in D4Element:
            assert d4_multiply(D4Element.E, a) == a
            assert d4_multiply(a, D4Element.E) == a

    def test_inverses(self):
        """Every element has an inverse: a * a⁻¹ = e."""
        for a in D4Element:
            a_inv = d4_inverse(a)
            assert d4_multiply(a, a_inv) == D4Element.E
            assert d4_multiply(a_inv, a) == D4Element.E

    def test_associativity(self):
        """(a*b)*c = a*(b*c) for all elements."""
        elements = list(D4Element)
        for a in elements:
            for b in elements:
                for c in elements:
                    left = d4_multiply(d4_multiply(a, b), c)
                    right = d4_multiply(a, d4_multiply(b, c))
                    assert left == right, f"({a}*{b})*{c} ≠ {a}*({b}*{c})"


class TestD4DefiningRelations:
    """Test the defining relations of D4."""

    def test_r_fourth_power_is_identity(self):
        """r⁴ = e: Four rotations return to identity."""
        r = D4Element.R
        r2 = d4_multiply(r, r)
        r3 = d4_multiply(r2, r)
        r4 = d4_multiply(r3, r)
        assert r4 == D4Element.E

    def test_s_squared_is_identity(self):
        """s² = e: Reflection is an involution."""
        s = D4Element.S
        s2 = d4_multiply(s, s)
        assert s2 == D4Element.E

    def test_srs_equals_r_inverse(self):
        """srs = r⁻¹ = r³: The key non-abelian relation."""
        s = D4Element.S
        r = D4Element.R

        # Compute srs
        sr = d4_multiply(s, r)
        srs = d4_multiply(sr, s)

        # r⁻¹ = r³
        r_inv = d4_inverse(r)
        assert r_inv == D4Element.R3
        assert srs == r_inv

    def test_all_reflections_are_involutions(self):
        """All reflection elements are self-inverse (order 2)."""
        reflections = [D4Element.S, D4Element.SR, D4Element.SR2, D4Element.SR3]
        for refl in reflections:
            assert d4_multiply(refl, refl) == D4Element.E


class TestNonAbelianStructure:
    """Test that D4 is non-abelian."""

    def test_rs_not_equal_sr(self):
        """rs ≠ sr: Rotation and reflection do not commute."""
        r = D4Element.R
        s = D4Element.S

        rs = d4_multiply(r, s)
        sr = d4_multiply(s, r)

        assert rs != sr, "D4 should be non-abelian"

    def test_rs_is_sr3(self):
        """rs = sr³ (specific relation)."""
        rs = d4_multiply(D4Element.R, D4Element.S)
        assert rs == D4Element.SR3

    def test_sr_composition(self):
        """sr is a distinct element from rs."""
        sr = d4_multiply(D4Element.S, D4Element.R)
        assert sr == D4Element.SR


class TestHohfeldianStateActions:
    """Test D4 action on Hohfeldian positions."""

    def test_rotation_cycle(self):
        """r: O → C → L → N → O (90° rotation)."""
        assert d4_apply_to_state(D4Element.R, HohfeldianState.O) == HohfeldianState.C
        assert d4_apply_to_state(D4Element.R, HohfeldianState.C) == HohfeldianState.L
        assert d4_apply_to_state(D4Element.R, HohfeldianState.L) == HohfeldianState.N
        assert d4_apply_to_state(D4Element.R, HohfeldianState.N) == HohfeldianState.O

    def test_correlative_is_s(self):
        """s (correlative): O ↔ C, L ↔ N."""
        assert correlative(HohfeldianState.O) == HohfeldianState.C
        assert correlative(HohfeldianState.C) == HohfeldianState.O
        assert correlative(HohfeldianState.L) == HohfeldianState.N
        assert correlative(HohfeldianState.N) == HohfeldianState.L

        # Also via d4_apply_to_state
        for state in HohfeldianState:
            assert correlative(state) == d4_apply_to_state(D4Element.S, state)

    def test_negation_is_r2(self):
        """r² (negation): O ↔ L, C ↔ N."""
        assert negation(HohfeldianState.O) == HohfeldianState.L
        assert negation(HohfeldianState.L) == HohfeldianState.O
        assert negation(HohfeldianState.C) == HohfeldianState.N
        assert negation(HohfeldianState.N) == HohfeldianState.C

        # Also via d4_apply_to_state
        for state in HohfeldianState:
            assert negation(state) == d4_apply_to_state(D4Element.R2, state)

    def test_identity_preserves_states(self):
        """e preserves all states."""
        for state in HohfeldianState:
            assert d4_apply_to_state(D4Element.E, state) == state

    def test_four_rotations_return_to_start(self):
        """r⁴ returns to original state."""
        for initial in HohfeldianState:
            state = initial
            for _ in range(4):
                state = d4_apply_to_state(D4Element.R, state)
            assert state == initial


class TestSemanticGates:
    """Test semantic gate mappings."""

    def test_obligation_release_is_negation(self):
        """'Only if convenient' releases obligation: O → L via r²."""
        result = apply_semantic_gate(SemanticGate.ONLY_IF_CONVENIENT, HohfeldianState.O)
        assert result == HohfeldianState.L

    def test_promise_binds_liberty(self):
        """'I promise' binds liberty: L → O via r²."""
        result = apply_semantic_gate(SemanticGate.I_PROMISE, HohfeldianState.L)
        assert result == HohfeldianState.O

    def test_perspective_shift_is_correlative(self):
        """'From their perspective' applies correlative."""
        result = apply_semantic_gate(
            SemanticGate.FROM_THEIR_PERSPECTIVE, HohfeldianState.O
        )
        assert result == HohfeldianState.C

    def test_negation_is_self_inverse(self):
        """Applying negation twice returns to original."""
        for state in HohfeldianState:
            once = apply_semantic_gate(SemanticGate.ONLY_IF_CONVENIENT, state)
            twice = apply_semantic_gate(SemanticGate.ONLY_IF_CONVENIENT, once)
            assert twice == state


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
    """Test Wilson loop/observable computation."""

    def test_identity_path(self):
        """Empty path (identity holonomy) predicts same state."""
        for state in HohfeldianState:
            holonomy, matched = compute_wilson_observable([], state, state)
            assert holonomy == D4Element.E
            assert matched is True

    def test_closed_rotation_path(self):
        """Four rotations (closed loop) should return to start."""
        path = [D4Element.R, D4Element.R, D4Element.R, D4Element.R]
        for initial in HohfeldianState:
            holonomy, matched = compute_wilson_observable(path, initial, initial)
            assert holonomy == D4Element.E
            assert matched is True

    def test_srs_path(self):
        """srs path should have holonomy r³."""
        path = [D4Element.S, D4Element.R, D4Element.S]
        holonomy, _ = compute_wilson_observable(
            path, HohfeldianState.O, HohfeldianState.L
        )
        assert holonomy == D4Element.R3

    def test_wrong_observation_not_matched(self):
        """Wrong final state is not matched."""
        path = [D4Element.R]  # O → C
        holonomy, matched = compute_wilson_observable(
            path, HohfeldianState.O, HohfeldianState.L  # Wrong!
        )
        assert holonomy == D4Element.R
        assert matched is False


class TestKleinFourSubgroup:
    """Test abelian subgroup identification."""

    def test_klein_four_elements(self):
        """V₄ = {e, r², s, sr²}."""
        v4 = get_klein_four_subgroup()
        assert set(v4) == {D4Element.E, D4Element.R2, D4Element.S, D4Element.SR2}

    def test_klein_four_is_abelian(self):
        """All pairs in V₄ commute."""
        v4 = get_klein_four_subgroup()
        for a in v4:
            for b in v4:
                ab = d4_multiply(a, b)
                ba = d4_multiply(b, a)
                assert ab == ba, f"{a} and {b} should commute in V₄"

    def test_klein_four_is_closed(self):
        """V₄ is closed under multiplication."""
        v4 = set(get_klein_four_subgroup())
        for a in v4:
            for b in v4:
                assert d4_multiply(a, b) in v4

    def test_is_in_klein_four(self):
        """is_in_klein_four correctly identifies subgroup elements."""
        assert is_in_klein_four(D4Element.E)
        assert is_in_klein_four(D4Element.R2)
        assert is_in_klein_four(D4Element.S)
        assert is_in_klein_four(D4Element.SR2)
        assert not is_in_klein_four(D4Element.R)
        assert not is_in_klein_four(D4Element.R3)
        assert not is_in_klein_four(D4Element.SR)
        assert not is_in_klein_four(D4Element.SR3)

    def test_requires_nonabelian_structure(self):
        """Correctly identify when non-abelian elements are present."""
        # Only abelian elements
        assert not requires_nonabelian_structure(
            [D4Element.E, D4Element.R2, D4Element.S]
        )

        # Include r (quarter turn)
        assert requires_nonabelian_structure([D4Element.E, D4Element.R])

        # Include sr³
        assert requires_nonabelian_structure([D4Element.S, D4Element.SR3])


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


class TestGroupLawVerification:
    """Tests for empirical group law verification protocol."""

    def test_srs_matches_r_inverse_on_all_states(self):
        """srs and r³ produce identical results on all states."""
        for initial in HohfeldianState:
            # Path 1: srs
            state1 = d4_apply_to_state(D4Element.S, initial)
            state1 = d4_apply_to_state(D4Element.R, state1)
            state1 = d4_apply_to_state(D4Element.S, state1)

            # Path 2: r³
            state2 = d4_apply_to_state(D4Element.R3, initial)

            assert state1 == state2

    def test_path_dependence_signature(self):
        """rs and sr paths produce different results."""
        differences_found = 0
        for initial in HohfeldianState:
            # Path 1: rs
            state_rs = d4_apply_to_state(D4Element.R, initial)
            state_rs = d4_apply_to_state(D4Element.S, state_rs)

            # Path 2: sr
            state_sr = d4_apply_to_state(D4Element.S, initial)
            state_sr = d4_apply_to_state(D4Element.R, state_sr)

            if state_rs != state_sr:
                differences_found += 1

        # Should differ on all states
        assert differences_found == 4
