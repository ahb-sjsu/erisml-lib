# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
# ruff: noqa: E402
"""
Comprehensive tests for EthicalFactsV3 with per-party tracking.

Tests V3 dataclasses, distributional metrics, V2↔V3 conversion,
and MoralTensor integration.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from erisml.ethics.facts import (
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    EthicalFacts,
)
from erisml.ethics.facts_v3 import (
    PartyConsequences,
    PartyRights,
    PartyJustice,
    ConsequencesV3,
    RightsAndDutiesV3,
    JusticeAndFairnessV3,
    EthicalFactsV3,
    promote_facts_v2_to_v3,
    collapse_facts_v3_to_v2,
)
from erisml.ethics.moral_tensor import MoralTensor

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_parties() -> list[str]:
    """Sample party IDs."""
    return ["alice", "bob", "carol"]


@pytest.fixture
def sample_consequences_v3(sample_parties: list[str]) -> ConsequencesV3:
    """Sample ConsequencesV3 with varying impacts."""
    return ConsequencesV3(
        expected_benefit=0.6,
        expected_harm=0.3,
        urgency=0.5,
        affected_count=3,
        per_party=(
            PartyConsequences(
                party_id="alice", expected_benefit=0.9, expected_harm=0.1
            ),
            PartyConsequences(party_id="bob", expected_benefit=0.5, expected_harm=0.3),
            PartyConsequences(
                party_id="carol",
                expected_benefit=0.4,
                expected_harm=0.5,
                vulnerability_weight=2.0,
            ),
        ),
    )


@pytest.fixture
def sample_rights_v3(sample_parties: list[str]) -> RightsAndDutiesV3:
    """Sample RightsAndDutiesV3 with varying violations."""
    return RightsAndDutiesV3(
        violates_rights=True,
        has_valid_consent=False,
        violates_explicit_rule=False,
        role_duty_conflict=False,
        per_party=(
            PartyRights(party_id="alice", rights_violated=False, consent_given=True),
            PartyRights(party_id="bob", rights_violated=True, consent_given=False),
            PartyRights(party_id="carol", rights_violated=False, consent_given=True),
        ),
    )


@pytest.fixture
def sample_justice_v3(sample_parties: list[str]) -> JusticeAndFairnessV3:
    """Sample JusticeAndFairnessV3 with varying burdens."""
    return JusticeAndFairnessV3(
        discriminates_on_protected_attr=False,
        prioritizes_most_disadvantaged=True,
        per_party=(
            PartyJustice(
                party_id="alice",
                relative_burden=0.1,
                relative_benefit=0.5,
                is_disadvantaged=False,
            ),
            PartyJustice(
                party_id="bob",
                relative_burden=0.3,
                relative_benefit=0.3,
                is_disadvantaged=False,
            ),
            PartyJustice(
                party_id="carol",
                relative_burden=0.6,
                relative_benefit=0.2,
                is_disadvantaged=True,
                protected_attributes=("disability",),
            ),
        ),
    )


@pytest.fixture
def sample_facts_v3(
    sample_consequences_v3: ConsequencesV3,
    sample_rights_v3: RightsAndDutiesV3,
    sample_justice_v3: JusticeAndFairnessV3,
) -> EthicalFactsV3:
    """Sample EthicalFactsV3."""
    return EthicalFactsV3(
        option_id="test_option",
        consequences=sample_consequences_v3,
        rights_and_duties=sample_rights_v3,
        justice_and_fairness=sample_justice_v3,
        party_labels={"alice": "Alice A.", "bob": "Bob B.", "carol": "Carol C."},
    )


@pytest.fixture
def sample_facts_v2() -> EthicalFacts:
    """Sample V2 EthicalFacts for promotion testing."""
    return EthicalFacts(
        option_id="v2_option",
        consequences=Consequences(
            expected_benefit=0.7,
            expected_harm=0.2,
            urgency=0.5,
            affected_count=3,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=True,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
    )


# =============================================================================
# Test Per-Party Dataclasses
# =============================================================================


class TestPartyConsequences:
    """Tests for PartyConsequences dataclass."""

    def test_basic_creation(self):
        """Test basic creation."""
        pc = PartyConsequences(party_id="test", expected_benefit=0.8, expected_harm=0.2)
        assert pc.party_id == "test"
        assert pc.expected_benefit == 0.8
        assert pc.expected_harm == 0.2
        assert pc.vulnerability_weight == 1.0

    def test_validation_benefit_bounds(self):
        """Test benefit bounds validation."""
        with pytest.raises(ValueError, match="expected_benefit must be in"):
            PartyConsequences(party_id="test", expected_benefit=1.5, expected_harm=0.0)

    def test_validation_harm_bounds(self):
        """Test harm bounds validation."""
        with pytest.raises(ValueError, match="expected_harm must be in"):
            PartyConsequences(party_id="test", expected_benefit=0.5, expected_harm=-0.1)

    def test_vulnerability_weight(self):
        """Test vulnerability weight."""
        pc = PartyConsequences(
            party_id="vulnerable",
            expected_benefit=0.5,
            expected_harm=0.5,
            vulnerability_weight=2.5,
        )
        assert pc.vulnerability_weight == 2.5


class TestPartyRights:
    """Tests for PartyRights dataclass."""

    def test_basic_creation(self):
        """Test basic creation."""
        pr = PartyRights(party_id="test")
        assert pr.party_id == "test"
        assert pr.rights_violated is False
        assert pr.consent_given is True
        assert pr.duty_owed is False

    def test_with_violations(self):
        """Test with rights violations."""
        pr = PartyRights(
            party_id="victim", rights_violated=True, consent_given=False, duty_owed=True
        )
        assert pr.rights_violated is True
        assert pr.consent_given is False
        assert pr.duty_owed is True


class TestPartyJustice:
    """Tests for PartyJustice dataclass."""

    def test_basic_creation(self):
        """Test basic creation."""
        pj = PartyJustice(party_id="test")
        assert pj.party_id == "test"
        assert pj.relative_burden == 0.0
        assert pj.relative_benefit == 0.0
        assert pj.protected_attributes == ()
        assert pj.is_disadvantaged is False

    def test_with_protected_attributes(self):
        """Test with protected attributes."""
        pj = PartyJustice(
            party_id="protected",
            relative_burden=0.7,
            relative_benefit=0.2,
            protected_attributes=("age", "disability"),
            is_disadvantaged=True,
        )
        assert pj.protected_attributes == ("age", "disability")
        assert pj.is_disadvantaged is True

    def test_validation_bounds(self):
        """Test bounds validation."""
        with pytest.raises(ValueError, match="relative_burden must be in"):
            PartyJustice(party_id="test", relative_burden=1.5)


# =============================================================================
# Test V3 Dimension Dataclasses
# =============================================================================


class TestConsequencesV3:
    """Tests for ConsequencesV3 dataclass."""

    def test_per_party_tracking(self, sample_consequences_v3: ConsequencesV3):
        """Test per-party tracking."""
        assert len(sample_consequences_v3.per_party) == 3
        assert sample_consequences_v3.party_ids == ["alice", "bob", "carol"]

    def test_benefit_gini_computation(self, sample_consequences_v3: ConsequencesV3):
        """Test Gini coefficient for benefit distribution."""
        # Benefits: [0.9, 0.5, 0.4] - unequal distribution
        gini = sample_consequences_v3.benefit_gini
        assert 0.0 < gini < 1.0  # Non-zero inequality

    def test_harm_gini_computation(self, sample_consequences_v3: ConsequencesV3):
        """Test Gini coefficient for harm distribution."""
        # Harms: [0.1, 0.3, 0.5] - unequal distribution
        gini = sample_consequences_v3.harm_gini
        assert 0.0 < gini < 1.0

    def test_gini_perfect_equality(self):
        """Test Gini = 0 for perfect equality."""
        c = ConsequencesV3(
            expected_benefit=0.5,
            expected_harm=0.5,
            urgency=0.5,
            affected_count=3,
            per_party=(
                PartyConsequences(
                    party_id="a", expected_benefit=0.5, expected_harm=0.5
                ),
                PartyConsequences(
                    party_id="b", expected_benefit=0.5, expected_harm=0.5
                ),
                PartyConsequences(
                    party_id="c", expected_benefit=0.5, expected_harm=0.5
                ),
            ),
        )
        assert c.benefit_gini == 0.0
        assert c.harm_gini == 0.0

    def test_to_v2_collapse(self, sample_consequences_v3: ConsequencesV3):
        """Test collapse to V2."""
        v2 = sample_consequences_v3.to_v2()
        assert isinstance(v2, Consequences)
        assert v2.expected_benefit == 0.6
        assert v2.expected_harm == 0.3
        assert v2.urgency == 0.5
        assert v2.affected_count == 3

    def test_from_v2_promotion(self):
        """Test promotion from V2."""
        v2 = Consequences(
            expected_benefit=0.7,
            expected_harm=0.2,
            urgency=0.5,
            affected_count=2,
        )
        v3 = ConsequencesV3.from_v2(v2, parties=["x", "y"])

        assert v3.expected_benefit == 0.7
        assert v3.expected_harm == 0.2
        assert len(v3.per_party) == 2
        # Uniform distribution
        assert v3.per_party[0].expected_benefit == 0.7
        assert v3.per_party[1].expected_benefit == 0.7


class TestRightsAndDutiesV3:
    """Tests for RightsAndDutiesV3 dataclass."""

    def test_per_party_rights_tracking(self, sample_rights_v3: RightsAndDutiesV3):
        """Test per-party rights tracking."""
        assert len(sample_rights_v3.per_party) == 3

    def test_parties_with_violations(self, sample_rights_v3: RightsAndDutiesV3):
        """Test identification of parties with rights violations."""
        violated = sample_rights_v3.parties_with_rights_violated
        assert violated == ["bob"]

    def test_parties_without_consent(self, sample_rights_v3: RightsAndDutiesV3):
        """Test identification of parties without consent."""
        no_consent = sample_rights_v3.parties_without_consent
        assert no_consent == ["bob"]

    def test_aggregate_consistency(self, sample_rights_v3: RightsAndDutiesV3):
        """Test aggregate reflects per-party data."""
        # violates_rights=True because bob has rights_violated=True
        assert sample_rights_v3.violates_rights is True
        # has_valid_consent=False because bob has consent_given=False
        assert sample_rights_v3.has_valid_consent is False


class TestJusticeAndFairnessV3:
    """Tests for JusticeAndFairnessV3 dataclass."""

    def test_distributional_metrics(self, sample_justice_v3: JusticeAndFairnessV3):
        """Test distributional metrics."""
        assert sample_justice_v3.burden_gini > 0
        assert sample_justice_v3.benefit_gini > 0

    def test_worst_off_identification(self, sample_justice_v3: JusticeAndFairnessV3):
        """Test worst-off party identification."""
        # Carol has highest burden (0.6) and lowest benefit (0.2)
        worst = sample_justice_v3.worst_off_party
        assert worst == "carol"

    def test_disadvantaged_parties(self, sample_justice_v3: JusticeAndFairnessV3):
        """Test disadvantaged party identification."""
        disadvantaged = sample_justice_v3.disadvantaged_parties
        assert disadvantaged == ["carol"]

    def test_protected_attribute_tracking(
        self, sample_justice_v3: JusticeAndFairnessV3
    ):
        """Test protected attribute tracking."""
        carol = sample_justice_v3.per_party[2]
        assert carol.party_id == "carol"
        assert "disability" in carol.protected_attributes


# =============================================================================
# Test EthicalFactsV3 Container
# =============================================================================


class TestEthicalFactsV3:
    """Tests for EthicalFactsV3 container."""

    def test_party_id_extraction(self, sample_facts_v3: EthicalFactsV3):
        """Test extraction of all party IDs."""
        party_ids = sample_facts_v3.party_ids
        assert sorted(party_ids) == ["alice", "bob", "carol"]

    def test_n_parties(self, sample_facts_v3: EthicalFactsV3):
        """Test party count."""
        assert sample_facts_v3.n_parties == 3

    def test_party_labels(self, sample_facts_v3: EthicalFactsV3):
        """Test party labels."""
        assert sample_facts_v3.party_labels["alice"] == "Alice A."

    def test_to_v2_roundtrip(self, sample_facts_v3: EthicalFactsV3):
        """Test collapse to V2."""
        v2 = sample_facts_v3.to_v2()

        assert isinstance(v2, EthicalFacts)
        assert v2.option_id == "test_option"
        assert v2.consequences.expected_benefit == 0.6
        assert v2.rights_and_duties.violates_rights is True

    def test_from_v2_promotion(self, sample_facts_v2: EthicalFacts):
        """Test promotion from V2."""
        v3 = EthicalFactsV3.from_v2(sample_facts_v2, parties=["p1", "p2", "p3"])

        assert v3.option_id == "v2_option"
        assert v3.n_parties == 3
        assert v3.consequences.expected_benefit == 0.7
        assert v3.autonomy_and_agency is not None

    def test_from_v2_default_parties(self, sample_facts_v2: EthicalFacts):
        """Test promotion with default party generation."""
        v3 = EthicalFactsV3.from_v2(sample_facts_v2)

        # affected_count = 3, so should generate party_0, party_1, party_2
        assert v3.n_parties == 3
        assert "party_0" in v3.party_ids

    def test_to_moral_tensor(self, sample_facts_v3: EthicalFactsV3):
        """Test conversion to MoralTensor."""
        tensor = sample_facts_v3.to_moral_tensor()

        assert isinstance(tensor, MoralTensor)
        assert tensor.rank == 2
        assert tensor.shape == (9, 3)

    def test_tensor_party_labels(self, sample_facts_v3: EthicalFactsV3):
        """Test tensor has correct party labels."""
        tensor = sample_facts_v3.to_moral_tensor()

        assert "n" in tensor.axis_labels
        assert tensor.axis_labels["n"] == ["alice", "bob", "carol"]

    def test_serialization_dict(self, sample_facts_v3: EthicalFactsV3):
        """Test basic dict conversion (via dataclasses.asdict would work)."""
        # Just verify the object is convertible
        assert sample_facts_v3.option_id == "test_option"
        assert sample_facts_v3.consequences is not None


# =============================================================================
# Test V2↔V3 Compatibility
# =============================================================================


class TestV2V3FactsCompat:
    """Tests for V2↔V3 facts compatibility."""

    def test_promotion_preserves_aggregates(self, sample_facts_v2: EthicalFacts):
        """Test that promotion preserves aggregate values."""
        v3 = promote_facts_v2_to_v3(sample_facts_v2)

        assert (
            v3.consequences.expected_benefit
            == sample_facts_v2.consequences.expected_benefit
        )
        assert (
            v3.consequences.expected_harm == sample_facts_v2.consequences.expected_harm
        )
        assert (
            v3.rights_and_duties.violates_rights
            == sample_facts_v2.rights_and_duties.violates_rights
        )

    def test_collapse_preserves_aggregates(self, sample_facts_v3: EthicalFactsV3):
        """Test that collapse preserves aggregate values."""
        v2 = collapse_facts_v3_to_v2(sample_facts_v3)

        assert (
            v2.consequences.expected_benefit
            == sample_facts_v3.consequences.expected_benefit
        )
        assert (
            v2.consequences.expected_harm == sample_facts_v3.consequences.expected_harm
        )

    def test_roundtrip_invariance(self, sample_facts_v2: EthicalFacts):
        """Test V2 -> V3 -> V2 preserves values."""
        v3 = promote_facts_v2_to_v3(sample_facts_v2)
        v2_recovered = collapse_facts_v3_to_v2(v3)

        assert v2_recovered.option_id == sample_facts_v2.option_id
        assert (
            v2_recovered.consequences.expected_benefit
            == sample_facts_v2.consequences.expected_benefit
        )
        assert (
            v2_recovered.consequences.expected_harm
            == sample_facts_v2.consequences.expected_harm
        )
        assert (
            v2_recovered.rights_and_duties.violates_rights
            == sample_facts_v2.rights_and_duties.violates_rights
        )

    def test_promotion_with_custom_parties(self, sample_facts_v2: EthicalFacts):
        """Test promotion with custom party list."""
        v3 = promote_facts_v2_to_v3(sample_facts_v2, parties=["x", "y"])

        assert v3.n_parties == 2
        assert "x" in v3.party_ids
        assert "y" in v3.party_ids

    def test_collapse_strategies(self, sample_facts_v3: EthicalFactsV3):
        """Test different collapse strategies."""
        v2_aggregate = collapse_facts_v3_to_v2(sample_facts_v3, strategy="aggregate")
        v2_mean = collapse_facts_v3_to_v2(sample_facts_v3, strategy="mean")

        # Both should give same result for aggregate values
        assert (
            v2_aggregate.consequences.expected_benefit
            == v2_mean.consequences.expected_benefit
        )

    def test_invalid_collapse_strategy(self, sample_facts_v3: EthicalFactsV3):
        """Test invalid collapse strategy raises error."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            collapse_facts_v3_to_v2(sample_facts_v3, strategy="invalid")


# =============================================================================
# Test MoralTensor Integration
# =============================================================================


class TestMoralTensorIntegration:
    """Tests for MoralTensor integration."""

    def test_facts_to_tensor_shape(self, sample_facts_v3: EthicalFactsV3):
        """Test tensor has correct shape."""
        tensor = sample_facts_v3.to_moral_tensor()

        assert tensor.shape == (9, 3)  # 9 dimensions, 3 parties

    def test_tensor_harm_dimension(self, sample_facts_v3: EthicalFactsV3):
        """Test harm dimension (0) mapped correctly."""
        tensor = sample_facts_v3.to_moral_tensor()
        data = tensor.to_dense()

        # Harm values: alice=0.1, bob=0.3, carol=0.5
        assert np.isclose(data[0, 0], 0.1)  # alice
        assert np.isclose(data[0, 1], 0.3)  # bob
        assert np.isclose(data[0, 2], 0.5)  # carol

    def test_tensor_rights_dimension(self, sample_facts_v3: EthicalFactsV3):
        """Test rights dimension (1) mapped correctly."""
        tensor = sample_facts_v3.to_moral_tensor()
        data = tensor.to_dense()

        # Rights: alice=not violated (1.0), bob=violated (0.0), carol=not violated (1.0)
        assert np.isclose(data[1, 0], 1.0)  # alice
        assert np.isclose(data[1, 1], 0.0)  # bob
        assert np.isclose(data[1, 2], 1.0)  # carol

    def test_tensor_fairness_dimension(self, sample_facts_v3: EthicalFactsV3):
        """Test fairness dimension (2) mapped correctly."""
        tensor = sample_facts_v3.to_moral_tensor()
        data = tensor.to_dense()

        # Fairness = 1 - relative_burden
        # alice: 1-0.1=0.9, bob: 1-0.3=0.7, carol: 1-0.6=0.4
        assert np.isclose(data[2, 0], 0.9)  # alice
        assert np.isclose(data[2, 1], 0.7)  # bob
        assert np.isclose(data[2, 2], 0.4)  # carol

    def test_empty_parties_returns_rank1(self):
        """Test empty parties returns rank-1 tensor."""
        facts = EthicalFactsV3(
            option_id="empty",
            consequences=ConsequencesV3(
                expected_benefit=0.5,
                expected_harm=0.3,
                urgency=0.5,
                affected_count=0,
            ),
            rights_and_duties=RightsAndDutiesV3(
                violates_rights=False,
                has_valid_consent=True,
                violates_explicit_rule=False,
                role_duty_conflict=False,
            ),
            justice_and_fairness=JusticeAndFairnessV3(
                discriminates_on_protected_attr=False,
                prioritizes_most_disadvantaged=False,
            ),
        )
        tensor = facts.to_moral_tensor()

        assert tensor.rank == 1
        assert tensor.shape == (9,)


# =============================================================================
# Test Domain Interfaces
# =============================================================================


class TestDomainInterfaces:
    """Tests for V3 domain interfaces."""

    def test_v2_to_v3_adapter(self, sample_facts_v2: EthicalFacts):
        """Test V2ToV3FactsAdapter."""
        from erisml.ethics.domain.interfaces import (
            CandidateOption,
            DomainAssessmentContext,
            V2ToV3FactsAdapter,
        )

        class MockV2Builder:
            def build_facts(self, option, context) -> EthicalFacts:
                return sample_facts_v2

        adapter = V2ToV3FactsAdapter(MockV2Builder())
        option = CandidateOption(option_id="v2_option", payload=None)
        context = DomainAssessmentContext(state=None)

        v3_facts = adapter.build_facts(option, context, parties=["a", "b"])

        assert isinstance(v3_facts, EthicalFactsV3)
        assert v3_facts.n_parties == 2


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_party(self):
        """Test with single party."""
        c = ConsequencesV3(
            expected_benefit=0.7,
            expected_harm=0.2,
            urgency=0.5,
            affected_count=1,
            per_party=(
                PartyConsequences(
                    party_id="solo", expected_benefit=0.7, expected_harm=0.2
                ),
            ),
        )

        assert c.benefit_gini == 0.0  # Single party = no inequality
        assert c.party_ids == ["solo"]

    def test_empty_per_party(self):
        """Test with empty per_party."""
        c = ConsequencesV3(
            expected_benefit=0.5,
            expected_harm=0.3,
            urgency=0.5,
            affected_count=0,
        )

        assert c.party_ids == []
        assert c.benefit_gini == 0.0

    def test_validation_errors(self):
        """Test validation errors."""
        with pytest.raises(ValueError):
            ConsequencesV3(
                expected_benefit=1.5,  # Invalid
                expected_harm=0.3,
                urgency=0.5,
                affected_count=0,
            )

    def test_frozen_dataclass(self):
        """Test that per-party dataclasses are frozen."""
        pc = PartyConsequences(party_id="test", expected_benefit=0.5, expected_harm=0.3)
        with pytest.raises(Exception):  # FrozenInstanceError
            pc.expected_benefit = 0.9  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
