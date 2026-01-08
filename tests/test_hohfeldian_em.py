# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""Tests for HohfeldianEM gauge verification module."""


from erisml.ethics import (
    EthicalFacts,
    RightsAndDuties,
    Consequences,
    JusticeAndFairness,
)
from erisml.ethics.hohfeld import (
    HohfeldianState,
    D4Element,
)
from erisml.ethics.modules.hohfeldian_em import (
    HohfeldianEM,
    quick_gauge_check,
)


def make_minimal_facts(option_id: str = "test", **kwargs) -> EthicalFacts:
    """Create minimal EthicalFacts for testing."""
    # Allow overriding the defaults
    defaults = {
        "consequences": Consequences(
            expected_benefit=0.5,
            expected_harm=0.2,
            urgency=0.3,
            affected_count=1,
        ),
        "rights_and_duties": RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        "justice_and_fairness": JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
        ),
    }
    # Override defaults with provided kwargs
    for key in defaults:
        if key not in kwargs:
            kwargs[key] = defaults[key]

    return EthicalFacts(option_id=option_id, **kwargs)


class TestHohfeldianEM:
    """Tests for HohfeldianEM ethics module."""

    def test_initialization_defaults(self):
        """EM initializes with correct defaults."""
        em = HohfeldianEM()
        assert em.gauge_violation_threshold == 0.1
        assert em.strict_enforcement is False
        assert em.tau == 1.0
        assert em.em_name == "hohfeldian_gauge"
        assert em.stakeholder == "all_parties"

    def test_initialization_custom(self):
        """EM accepts custom parameters."""
        em = HohfeldianEM(
            gauge_violation_threshold=0.2,
            strict_enforcement=True,
            tau=2.0,
        )
        assert em.gauge_violation_threshold == 0.2
        assert em.strict_enforcement is True
        assert em.tau == 2.0

    def test_evaluate_insufficient_parties(self):
        """Returns neutral when fewer than 2 parties."""
        em = HohfeldianEM()
        facts = make_minimal_facts()

        judgement = em.evaluate("test", facts)

        assert judgement.verdict == "neutral"
        assert judgement.metadata["gauge_check"] == "SKIPPED"

    def test_evaluate_with_tag_positions(self):
        """Extracts positions from tags."""
        em = HohfeldianEM()

        # Create facts with Hohfeldian positions encoded in tags
        facts = make_minimal_facts(
            tags=[
                "hohfeld:patient:C",  # Claim
                "hohfeld:hospital:O",  # Obligation - correlative of C
            ]
        )

        judgement = em.evaluate("test", facts)

        assert judgement.metadata["gauge_check"] == "PASSED"
        assert judgement.metadata["bond_index"] == 0.0

    def test_evaluate_gauge_violation(self):
        """Detects gauge violations."""
        em = HohfeldianEM()

        # Create facts with inconsistent positions
        facts = make_minimal_facts(
            tags=[
                "hohfeld:patient:C",  # Claim
                "hohfeld:hospital:L",  # Liberty - NOT correlative of C (should be O)
            ]
        )

        judgement = em.evaluate("test", facts)

        assert judgement.metadata["gauge_check"] == "FAILED"
        assert judgement.metadata["bond_index"] > 0
        assert len(judgement.metadata["violations"]) > 0

    def test_evaluate_strict_enforcement(self):
        """Strict enforcement produces avoid verdict on violation."""
        em = HohfeldianEM(strict_enforcement=True)

        facts = make_minimal_facts(
            tags=[
                "hohfeld:patient:C",
                "hohfeld:hospital:L",  # Violation
            ]
        )

        judgement = em.evaluate("test", facts)

        assert judgement.verdict == "avoid"
        assert judgement.normative_score < 0.3


class TestGaugeVerification:
    """Tests for gauge verification logic."""

    def test_perfect_correlative_symmetry(self):
        """Perfect correlative pairs give zero bond index."""
        em = HohfeldianEM()

        # O <-> C is a correlative pair
        positions = {
            "party_a": HohfeldianState.O,
            "party_b": HohfeldianState.C,
        }

        result = em._verify_gauge_consistency(positions)

        assert result.bond_index == 0.0
        assert result.passed is True
        assert len(result.violations) == 0

    def test_liberty_noclaim_pair(self):
        """L <-> N is also a correlative pair."""
        em = HohfeldianEM()

        positions = {
            "actor": HohfeldianState.L,
            "affected": HohfeldianState.N,
        }

        result = em._verify_gauge_consistency(positions)

        assert result.bond_index == 0.0
        assert result.passed is True

    def test_violation_detected(self):
        """Non-correlative pairs are detected."""
        em = HohfeldianEM()

        # O <-> L is NOT a correlative pair
        positions = {
            "party_a": HohfeldianState.O,
            "party_b": HohfeldianState.L,  # Should be C
        }

        result = em._verify_gauge_consistency(positions)

        assert result.bond_index > 0
        assert result.passed is False
        assert len(result.violations) == 1
        assert "expected party_b to have C" in result.violations[0]

    def test_multiple_parties(self):
        """Handles multiple party pairs."""
        em = HohfeldianEM()

        # 3 parties, checking all pairs
        positions = {
            "a": HohfeldianState.O,
            "b": HohfeldianState.C,  # Correlative of O - OK
            "c": HohfeldianState.L,  # Not correlative of O or C
        }

        result = em._verify_gauge_consistency(positions)

        # a-b: OK, a-c: violation, b-c: violation
        # 2/3 violations
        assert result.bond_index > 0
        assert result.passed is False


class TestWilsonObservable:
    """Tests for path verification using Wilson observable."""

    def test_identity_path(self):
        """Identity path should match any final state equal to initial."""
        em = HohfeldianEM()

        holonomy, matched, explanation = em.verify_decision_path(
            path=[D4Element.E],
            initial_state=HohfeldianState.O,
            observed_final=HohfeldianState.O,
        )

        assert holonomy == D4Element.E
        assert matched is True
        assert "PASSED" in explanation

    def test_rotation_path(self):
        """Four rotations should return to start."""
        em = HohfeldianEM()

        # r^4 = e
        path = [D4Element.R, D4Element.R, D4Element.R, D4Element.R]

        holonomy, matched, explanation = em.verify_decision_path(
            path=path,
            initial_state=HohfeldianState.O,
            observed_final=HohfeldianState.O,  # Should return to O
        )

        assert holonomy == D4Element.E
        assert matched is True

    def test_srs_path(self):
        """srs = r^-1 verification."""
        em = HohfeldianEM()

        # srs path from O should give same result as r^3
        path = [D4Element.S, D4Element.R, D4Element.S]

        # r^3(O) = N (O -> C -> L -> N backwards is O -> N)
        holonomy, matched, explanation = em.verify_decision_path(
            path=path,
            initial_state=HohfeldianState.O,
            observed_final=HohfeldianState.N,
        )

        assert holonomy == D4Element.R3
        assert matched is True

    def test_mismatched_path(self):
        """Detects when observation doesn't match prediction."""
        em = HohfeldianEM()

        holonomy, matched, explanation = em.verify_decision_path(
            path=[D4Element.R],  # O -> C
            initial_state=HohfeldianState.O,
            observed_final=HohfeldianState.L,  # Wrong! Should be C
        )

        assert matched is False
        assert "FAILED" in explanation
        assert "Expected C" in explanation


class TestNonAbelianSignature:
    """Tests for non-abelian structure detection."""

    def test_abelian_operations_only(self):
        """Klein-4 operations don't prove non-abelian structure."""
        em = HohfeldianEM()

        # {e, r², s, sr²} are all abelian (Klein-4)
        operations = [D4Element.E, D4Element.R2, D4Element.S, D4Element.SR2]

        is_nonabelian, explanation = em.check_nonabelian_signature(operations)

        assert is_nonabelian is False
        assert "Klein-4" in explanation

    def test_quarter_turn_proves_nonabelian(self):
        """Quarter-turn operations prove non-abelian structure."""
        em = HohfeldianEM()

        # Including r (quarter-turn) proves non-abelian
        operations = [D4Element.R, D4Element.S]

        is_nonabelian, explanation = em.check_nonabelian_signature(operations)

        assert is_nonabelian is True
        assert "Non-abelian" in explanation

    def test_sr_also_nonabelian(self):
        """sr is also a non-abelian element."""
        em = HohfeldianEM()

        operations = [D4Element.SR]

        is_nonabelian, explanation = em.check_nonabelian_signature(operations)

        assert is_nonabelian is True


class TestQuickGaugeCheck:
    """Tests for quick_gauge_check utility function."""

    def test_correlative_pair_passes(self):
        """Correlative pairs pass quick check."""
        result = quick_gauge_check({"a": "O", "b": "C"})
        assert result.passed is True
        assert result.bond_index == 0.0

    def test_violation_detected(self):
        """Violations detected in quick check."""
        result = quick_gauge_check({"a": "O", "b": "N"})  # Should be C
        assert result.passed is False
        assert result.bond_index > 0

    def test_custom_threshold(self):
        """Custom threshold affects passing."""
        # With high threshold, some violations might pass
        result = quick_gauge_check(
            {"a": "O", "b": "N"},  # Violation
            threshold=2.0,  # Very permissive
        )
        # Bond index is 1.0 for complete violation, still under 2.0
        assert result.bond_index > 0


class TestIntegrationWithEthicalFacts:
    """Integration tests with full EthicalFacts."""

    def test_with_rights_and_duties_and_tags(self):
        """Extracts positions from tags with rights_and_duties context."""
        em = HohfeldianEM()

        facts = make_minimal_facts(
            rights_and_duties=RightsAndDuties(
                violates_rights=True,  # Implies affected party had Claim
                has_valid_consent=False,
                violates_explicit_rule=False,
                role_duty_conflict=False,
            ),
            tags=[
                "hohfeld:actor:O",
                "hohfeld:affected:C",
            ],
        )

        judgement = em.evaluate("test", facts)

        # Should pass - O and C are correlative
        assert judgement.metadata["gauge_check"] == "PASSED"

    def test_score_reflects_bond_index(self):
        """Score is higher when bond index is lower."""
        em = HohfeldianEM()

        # Perfect symmetry
        facts_good = make_minimal_facts(
            tags=["hohfeld:a:O", "hohfeld:b:C"],
        )

        # Violation
        facts_bad = make_minimal_facts(
            tags=["hohfeld:a:O", "hohfeld:b:L"],
        )

        judgement_good = em.evaluate("test", facts_good)
        judgement_bad = em.evaluate("test", facts_bad)

        assert judgement_good.normative_score > judgement_bad.normative_score
