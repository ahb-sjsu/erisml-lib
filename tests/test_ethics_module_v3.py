# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for DEME V3 Ethics Module (Sprint 6).

Tests cover:
- EthicalJudgementV3 dataclass
- EthicsModuleV3 protocol and BaseEthicsModuleV3
- GenevaEMV3 reference implementation
- V2↔V3 conversion functions
- Per-party verdict and veto tracking
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from erisml.ethics.judgement import EthicalJudgementV2
from erisml.ethics.judgement_v3 import (
    EthicalJudgementV3,
    judgement_v2_to_v3,
    judgement_v3_to_v2,
    is_forbidden_v3,
    is_strongly_preferred_v3,
    compute_verdict_distribution,
)
from erisml.ethics.modules.base_v3 import (
    BaseEthicsModuleV3,
    V2ToV3EMAdapter,
    V3ToV2EMAdapter,
    aggregate_party_verdicts,
    create_uniform_tensor,
)
from erisml.ethics.modules.tier0.geneva_em_v3 import GenevaEMV3
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.facts import (
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    PrivacyAndDataGovernance,
    SocietalAndEnvironmental,
    VirtueAndCare,
    ProceduralAndLegitimacy,
    EpistemicStatus,
)
from erisml.ethics.facts_v3 import (
    EthicalFactsV3,
    ConsequencesV3,
    RightsAndDutiesV3,
    JusticeAndFairnessV3,
    AutonomyAndAgencyV3,
    PrivacyAndDataGovernanceV3,
    SocietalAndEnvironmentalV3,
    VirtueAndCareV3,
    ProceduralAndLegitimacyV3,
    EpistemicStatusV3,
    PartyConsequences,
    PartyRights,
    PartyJustice,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def simple_moral_vector() -> MoralVector:
    """Create a simple MoralVector for testing."""
    return MoralVector(
        physical_harm=0.2,
        rights_respect=0.9,
        fairness_equity=0.8,
        autonomy_respect=0.85,
        privacy_protection=0.9,
        societal_environmental=0.7,
        virtue_care=0.8,
        legitimacy_trust=0.85,
        epistemic_quality=0.9,
    )


@pytest.fixture
def veto_moral_vector() -> MoralVector:
    """Create a MoralVector with veto flags."""
    return MoralVector(
        physical_harm=0.8,
        rights_respect=0.0,
        fairness_equity=0.3,
        autonomy_respect=0.5,
        privacy_protection=0.7,
        societal_environmental=0.6,
        virtue_care=0.5,
        legitimacy_trust=0.4,
        epistemic_quality=0.7,
        veto_flags=["RIGHTS_VIOLATION"],
    )


@pytest.fixture
def three_party_tensor() -> MoralTensor:
    """Create a 3-party MoralTensor for testing."""
    data = np.array(
        [
            [0.1, 0.3, 0.5],  # physical_harm
            [0.9, 0.8, 0.7],  # rights_respect
            [0.8, 0.7, 0.6],  # fairness_equity
            [0.9, 0.85, 0.8],  # autonomy_respect
            [0.95, 0.9, 0.85],  # privacy_protection
            [0.7, 0.7, 0.7],  # societal_environmental
            [0.8, 0.75, 0.7],  # virtue_care
            [0.85, 0.8, 0.75],  # legitimacy_trust
            [0.9, 0.85, 0.8],  # epistemic_quality
        ]
    )
    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n"),
        axis_labels={"n": ["alice", "bob", "carol"]},
    )


@pytest.fixture
def v2_facts() -> EthicalFacts:
    """Create V2 EthicalFacts for testing."""
    return EthicalFacts(
        option_id="test_option",
        consequences=Consequences(
            expected_benefit=0.7,
            expected_harm=0.2,
            urgency=0.5,
            affected_count=100,
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
            exploits_vulnerable_population=False,
            exacerbates_power_imbalance=False,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.1,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.1,
            long_term_societal_risk=0.1,
            benefits_to_future_generations=0.5,
            burden_on_vulnerable_groups=0.1,
        ),
        virtue_and_care=VirtueAndCare(
            expresses_compassion=True,
            betrays_trust=False,
            respects_person_as_end=True,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.2,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )


@pytest.fixture
def v3_facts_three_party() -> EthicalFactsV3:
    """Create V3 EthicalFacts with 3 parties for testing."""
    return EthicalFactsV3(
        option_id="test_option_v3",
        consequences=ConsequencesV3(
            expected_benefit=0.53,
            expected_harm=0.3,
            urgency=0.5,
            affected_count=3,
            per_party=(
                PartyConsequences(
                    party_id="alice",
                    expected_benefit=0.8,
                    expected_harm=0.1,
                    vulnerability_weight=0.3,
                ),
                PartyConsequences(
                    party_id="bob",
                    expected_benefit=0.5,
                    expected_harm=0.3,
                    vulnerability_weight=0.5,
                ),
                PartyConsequences(
                    party_id="carol",
                    expected_benefit=0.3,
                    expected_harm=0.5,
                    vulnerability_weight=0.8,
                ),
            ),
        ),
        rights_and_duties=RightsAndDutiesV3(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
            per_party=(
                PartyRights(
                    party_id="alice",
                    rights_violated=False,
                    consent_given=True,
                    duty_owed=False,
                ),
                PartyRights(
                    party_id="bob",
                    rights_violated=False,
                    consent_given=True,
                    duty_owed=True,
                ),
                PartyRights(
                    party_id="carol",
                    rights_violated=False,
                    consent_given=False,
                    duty_owed=True,
                ),
            ),
        ),
        justice_and_fairness=JusticeAndFairnessV3(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=True,
            per_party=(
                PartyJustice(
                    party_id="alice",
                    relative_burden=0.2,
                    relative_benefit=0.4,
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
                    relative_burden=0.5,
                    relative_benefit=0.2,
                    is_disadvantaged=True,
                ),
            ),
        ),
        autonomy_and_agency=AutonomyAndAgencyV3(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        privacy_and_data=PrivacyAndDataGovernanceV3(
            privacy_invasion_level=0.1,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmentalV3(
            environmental_harm=0.1,
            long_term_societal_risk=0.1,
            benefits_to_future_generations=0.5,
            burden_on_vulnerable_groups=0.1,
        ),
        virtue_and_care=VirtueAndCareV3(
            expresses_compassion=True,
            betrays_trust=False,
            respects_person_as_end=True,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacyV3(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatusV3(
            uncertainty_level=0.2,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )


@pytest.fixture
def v3_facts_with_veto() -> EthicalFactsV3:
    """Create V3 EthicalFacts with rights violation for one party."""
    return EthicalFactsV3(
        option_id="test_option_veto",
        consequences=ConsequencesV3(
            expected_benefit=0.5,
            expected_harm=0.4,
            urgency=0.5,
            affected_count=2,
            per_party=(
                PartyConsequences(
                    party_id="alice",
                    expected_benefit=0.8,
                    expected_harm=0.1,
                    vulnerability_weight=0.3,
                ),
                PartyConsequences(
                    party_id="bob",
                    expected_benefit=0.2,
                    expected_harm=0.7,
                    vulnerability_weight=0.5,
                ),
            ),
        ),
        rights_and_duties=RightsAndDutiesV3(
            violates_rights=True,  # Bob has rights violation
            has_valid_consent=False,  # Bob doesn't have consent
            violates_explicit_rule=False,
            role_duty_conflict=False,
            per_party=(
                PartyRights(
                    party_id="alice",
                    rights_violated=False,
                    consent_given=True,
                    duty_owed=False,
                ),
                PartyRights(
                    party_id="bob",
                    rights_violated=True,  # Rights violation for Bob
                    consent_given=False,
                    duty_owed=True,
                ),
            ),
        ),
        justice_and_fairness=JusticeAndFairnessV3(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
            per_party=(
                PartyJustice(
                    party_id="alice",
                    relative_burden=0.2,
                    relative_benefit=0.5,
                    is_disadvantaged=False,
                ),
                PartyJustice(
                    party_id="bob",
                    relative_burden=0.8,
                    relative_benefit=0.2,
                    is_disadvantaged=True,
                ),
            ),
        ),
        autonomy_and_agency=AutonomyAndAgencyV3(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        privacy_and_data=PrivacyAndDataGovernanceV3(
            privacy_invasion_level=0.1,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmentalV3(
            environmental_harm=0.1,
            long_term_societal_risk=0.1,
            benefits_to_future_generations=0.5,
            burden_on_vulnerable_groups=0.1,
        ),
        virtue_and_care=VirtueAndCareV3(
            expresses_compassion=True,
            betrays_trust=False,
            respects_person_as_end=True,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacyV3(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatusV3(
            uncertainty_level=0.3,
            evidence_quality="medium",
            novel_situation_flag=False,
        ),
    )


# =============================================================================
# Test EthicalJudgementV3
# =============================================================================


class TestEthicalJudgementV3:
    """Tests for EthicalJudgementV3 dataclass."""

    def test_create_judgement(self, three_party_tensor: MoralTensor) -> None:
        """Test creating a basic EthicalJudgementV3."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
            per_party_verdicts={"alice": "prefer", "bob": "neutral", "carol": "avoid"},
        )

        assert judgement.option_id == "opt1"
        assert judgement.em_name == "test_em"
        assert judgement.verdict == "prefer"
        assert judgement.n_parties == 3
        assert len(judgement.party_labels) == 3

    def test_party_labels_from_tensor(self, three_party_tensor: MoralTensor) -> None:
        """Test that party labels are extracted from tensor."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
        )

        assert judgement.party_labels == ("alice", "bob", "carol")

    def test_get_party_vector(self, three_party_tensor: MoralTensor) -> None:
        """Test extracting MoralVector for a specific party."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
        )

        alice_vector = judgement.get_party_vector("alice")
        assert isinstance(alice_vector, MoralVector)
        assert alice_vector.physical_harm == pytest.approx(0.1, rel=0.01)

        bob_vector = judgement.get_party_vector("bob")
        assert bob_vector.physical_harm == pytest.approx(0.3, rel=0.01)

    def test_get_party_vector_by_index(self, three_party_tensor: MoralTensor) -> None:
        """Test extracting MoralVector by index."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
        )

        vector_0 = judgement.get_party_vector(0)
        vector_alice = judgement.get_party_vector("alice")

        assert vector_0.physical_harm == pytest.approx(
            vector_alice.physical_harm, rel=0.01
        )

    def test_get_party_verdict(self, three_party_tensor: MoralTensor) -> None:
        """Test getting verdict for specific party."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
            per_party_verdicts={"alice": "prefer", "bob": "neutral", "carol": "avoid"},
        )

        assert judgement.get_party_verdict("alice") == "prefer"
        assert judgement.get_party_verdict("bob") == "neutral"
        assert judgement.get_party_verdict("carol") == "avoid"
        # Unknown party falls back to global verdict
        assert judgement.get_party_verdict("unknown") == "prefer"

    def test_has_any_veto(self, three_party_tensor: MoralTensor) -> None:
        """Test veto detection."""
        # No veto
        judgement1 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
        )
        assert not judgement1.has_any_veto

        # Distributed veto
        judgement2 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="forbid",
            moral_tensor=three_party_tensor,
            distributed_veto_triggered=True,
            per_party_vetoes={"alice": False, "bob": True, "carol": False},
        )
        assert judgement2.has_any_veto

    def test_normative_score(self, three_party_tensor: MoralTensor) -> None:
        """Test scalar collapse for V1/V2 compatibility."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
        )

        score = judgement.normative_score
        assert 0.0 <= score <= 1.0


class TestJudgementConversion:
    """Tests for V2↔V3 judgement conversion."""

    def test_v2_to_v3_conversion(self, simple_moral_vector: MoralVector) -> None:
        """Test promoting V2 judgement to V3."""
        v2_judgement = EthicalJudgementV2(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=1,
            verdict="prefer",
            moral_vector=simple_moral_vector,
        )

        parties = ["alice", "bob", "carol"]
        v3_judgement = judgement_v2_to_v3(v2_judgement, parties=parties)

        assert v3_judgement.option_id == "opt1"
        assert v3_judgement.em_name == "test_em"
        assert v3_judgement.verdict == "prefer"
        assert v3_judgement.n_parties == 3
        assert v3_judgement.party_labels == tuple(parties)

        # All parties should have same verdict
        for party in parties:
            assert v3_judgement.get_party_verdict(party) == "prefer"

    def test_v2_to_v3_with_veto(self, veto_moral_vector: MoralVector) -> None:
        """Test promoting V2 judgement with veto to V3."""
        v2_judgement = EthicalJudgementV2(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="forbid",
            moral_vector=veto_moral_vector,
            veto_triggered=True,
            veto_reason="Rights violation",
        )

        parties = ["alice", "bob"]
        v3_judgement = judgement_v2_to_v3(v2_judgement, parties=parties)

        assert v3_judgement.distributed_veto_triggered
        assert v3_judgement.global_veto_override
        # All parties should be vetoed
        for party in parties:
            assert v3_judgement.per_party_vetoes.get(party, False)

    def test_v3_to_v2_conversion(self, three_party_tensor: MoralTensor) -> None:
        """Test collapsing V3 judgement to V2."""
        v3_judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=1,
            verdict="prefer",
            moral_tensor=three_party_tensor,
            per_party_verdicts={"alice": "prefer", "bob": "neutral", "carol": "avoid"},
        )

        v2_judgement = judgement_v3_to_v2(v3_judgement, collapse_strategy="mean")

        assert v2_judgement.option_id == "opt1"
        assert v2_judgement.em_name == "test_em"
        assert v2_judgement.verdict == "prefer"
        assert isinstance(v2_judgement.moral_vector, MoralVector)
        assert v2_judgement.metadata.get("_collapsed_from_v3")

    def test_v3_to_v2_worst_case(self, three_party_tensor: MoralTensor) -> None:
        """Test collapsing V3 to V2 with worst_case strategy."""
        v3_judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=1,
            verdict="neutral",
            moral_tensor=three_party_tensor,
        )

        v2_judgement = judgement_v3_to_v2(v3_judgement, collapse_strategy="worst_case")

        # Worst case should use highest harm, lowest other scores
        assert v2_judgement.moral_vector.physical_harm == pytest.approx(0.5, rel=0.01)

    def test_round_trip_conversion(self, simple_moral_vector: MoralVector) -> None:
        """Test V2 → V3 → V2 round-trip preserves key properties."""
        original_v2 = EthicalJudgementV2(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=2,
            verdict="prefer",
            moral_vector=simple_moral_vector,
        )

        # V2 → V3
        v3 = judgement_v2_to_v3(original_v2, parties=["alice", "bob"])

        # V3 → V2
        final_v2 = judgement_v3_to_v2(v3, collapse_strategy="mean")

        assert final_v2.option_id == original_v2.option_id
        assert final_v2.em_name == original_v2.em_name
        assert final_v2.verdict == original_v2.verdict
        # Scores should be similar (mean of uniform broadcast is same)
        assert final_v2.normative_score == pytest.approx(
            original_v2.normative_score, rel=0.01
        )


class TestJudgementHelpers:
    """Tests for judgement helper functions."""

    def test_is_forbidden_v3(self, three_party_tensor: MoralTensor) -> None:
        """Test is_forbidden_v3 helper."""
        # Not forbidden
        j1 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="prefer",
            moral_tensor=three_party_tensor,
        )
        assert not is_forbidden_v3(j1)

        # Forbidden by verdict
        j2 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="forbid",
            moral_tensor=three_party_tensor,
        )
        assert is_forbidden_v3(j2)

        # Forbidden by veto
        j3 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="neutral",
            moral_tensor=three_party_tensor,
            distributed_veto_triggered=True,
        )
        assert is_forbidden_v3(j3)

    def test_is_strongly_preferred_v3(self, three_party_tensor: MoralTensor) -> None:
        """Test is_strongly_preferred_v3 helper."""
        # Strongly preferred
        j1 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="strongly_prefer",
            moral_tensor=three_party_tensor,
        )
        assert is_strongly_preferred_v3(j1)

        # Not strongly preferred (has veto)
        j2 = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="strongly_prefer",
            moral_tensor=three_party_tensor,
            distributed_veto_triggered=True,
        )
        assert not is_strongly_preferred_v3(j2)

    def test_compute_verdict_distribution(
        self, three_party_tensor: MoralTensor
    ) -> None:
        """Test verdict distribution computation."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="neutral",
            moral_tensor=three_party_tensor,
            per_party_verdicts={
                "alice": "prefer",
                "bob": "prefer",
                "carol": "avoid",
            },
        )

        dist = compute_verdict_distribution(judgement)
        assert dist["prefer"] == 2
        assert dist["avoid"] == 1
        assert dist["neutral"] == 0


# =============================================================================
# Test BaseEthicsModuleV3
# =============================================================================


class TestBaseEthicsModuleV3:
    """Tests for BaseEthicsModuleV3 template class."""

    def test_aggregate_party_verdicts_conservative(self) -> None:
        """Test conservative verdict aggregation."""
        verdicts = {"alice": "prefer", "bob": "avoid", "carol": "neutral"}
        result = aggregate_party_verdicts(verdicts, strategy="conservative")
        assert result == "avoid"

    def test_aggregate_party_verdicts_with_forbid(self) -> None:
        """Test that forbid always wins in conservative mode."""
        verdicts = {"alice": "strongly_prefer", "bob": "forbid", "carol": "prefer"}
        result = aggregate_party_verdicts(verdicts, strategy="conservative")
        assert result == "forbid"

    def test_aggregate_party_verdicts_majority(self) -> None:
        """Test majority verdict aggregation."""
        verdicts = {"alice": "prefer", "bob": "prefer", "carol": "avoid"}
        result = aggregate_party_verdicts(verdicts, strategy="majority")
        assert result == "prefer"

    def test_aggregate_party_verdicts_optimistic(self) -> None:
        """Test optimistic verdict aggregation."""
        verdicts = {"alice": "avoid", "bob": "neutral", "carol": "prefer"}
        result = aggregate_party_verdicts(verdicts, strategy="optimistic")
        assert result == "prefer"

    def test_create_uniform_tensor(self, simple_moral_vector: MoralVector) -> None:
        """Test creating uniform tensor from vector."""
        tensor = create_uniform_tensor(
            simple_moral_vector,
            n_parties=3,
            party_labels=["alice", "bob", "carol"],
        )

        assert tensor.shape == (9, 3)
        assert tensor.axis_labels.get("n") == ["alice", "bob", "carol"]

        # All parties should have same values
        for j in range(3):
            assert tensor._data[0, j] == pytest.approx(0.2, rel=0.01)  # physical_harm

    def test_create_uniform_tensor_with_veto(
        self, veto_moral_vector: MoralVector
    ) -> None:
        """Test uniform tensor preserves veto flags."""
        tensor = create_uniform_tensor(
            veto_moral_vector,
            n_parties=2,
            party_labels=["alice", "bob"],
        )

        assert len(tensor.veto_locations) == 2  # Both parties vetoed


# =============================================================================
# Test GenevaEMV3
# =============================================================================


class TestGenevaEMV3:
    """Tests for GenevaEMV3 reference implementation."""

    def test_create_em(self) -> None:
        """Test creating GenevaEMV3."""
        em = GenevaEMV3()
        assert em.em_name == "geneva_constitutional_v3"
        assert em.stakeholder == "universal"
        assert em.em_tier == 0

    def test_judge_v2_interface(self, v2_facts: EthicalFacts) -> None:
        """Test V2-compatible judge() method."""
        em = GenevaEMV3()
        judgement = em.judge(v2_facts)

        assert isinstance(judgement, EthicalJudgementV2)
        assert judgement.option_id == "test_option"
        assert judgement.em_name == "geneva_constitutional_v3"

    def test_judge_distributed(self, v3_facts_three_party: EthicalFactsV3) -> None:
        """Test V3 judge_distributed() method."""
        em = GenevaEMV3()
        judgement = em.judge_distributed(v3_facts_three_party)

        assert isinstance(judgement, EthicalJudgementV3)
        assert judgement.option_id == "test_option_v3"
        assert judgement.n_parties == 3
        assert judgement.party_labels == ("alice", "bob", "carol")

        # Check per-party verdicts exist
        assert "alice" in judgement.per_party_verdicts
        assert "bob" in judgement.per_party_verdicts
        assert "carol" in judgement.per_party_verdicts

    def test_judge_distributed_with_rights_violation(
        self, v3_facts_with_veto: EthicalFactsV3
    ) -> None:
        """Test that rights violation triggers per-party veto."""
        em = GenevaEMV3()
        judgement = em.judge_distributed(v3_facts_with_veto)

        # Bob has rights violation
        assert judgement.per_party_vetoes.get("bob", False)
        assert judgement.per_party_verdicts.get("bob") == "forbid"

        # Alice should not be vetoed
        assert not judgement.per_party_vetoes.get("alice", True)

        # Global verdict should be forbid (conservative)
        assert judgement.verdict == "forbid"
        assert judgement.distributed_veto_triggered

    def test_reflex_check(self, v2_facts: EthicalFacts) -> None:
        """Test V2 reflex check."""
        em = GenevaEMV3()
        result = em.reflex_check(v2_facts)
        assert result is False  # No veto conditions

    def test_reflex_check_distributed(self, v3_facts_with_veto: EthicalFactsV3) -> None:
        """Test V3 reflex check returns per-party results."""
        em = GenevaEMV3()
        results = em.reflex_check_distributed(v3_facts_with_veto)

        assert "alice" in results
        assert "bob" in results
        assert results["alice"] is False  # No rights violation
        assert results["bob"] is True  # Rights violated

    def test_vulnerable_party_handling(self) -> None:
        """Test that vulnerable parties get extra protection."""
        em = GenevaEMV3()

        # Create facts with vulnerable party facing harm
        facts = EthicalFactsV3(
            option_id="vulnerable_test",
            consequences=ConsequencesV3(
                expected_benefit=0.4,
                expected_harm=0.3,
                urgency=0.5,
                affected_count=2,
                per_party=(
                    PartyConsequences(
                        party_id="vulnerable",
                        expected_benefit=0.2,
                        expected_harm=0.4,  # Significant harm
                        vulnerability_weight=0.8,  # High vulnerability
                    ),
                    PartyConsequences(
                        party_id="normal",
                        expected_benefit=0.6,
                        expected_harm=0.2,
                        vulnerability_weight=0.3,
                    ),
                ),
            ),
            rights_and_duties=RightsAndDutiesV3(
                violates_rights=False,
                has_valid_consent=True,
                violates_explicit_rule=False,
                role_duty_conflict=False,
                per_party=(
                    PartyRights(
                        party_id="vulnerable",
                        rights_violated=False,
                        consent_given=True,
                        duty_owed=True,
                    ),
                    PartyRights(
                        party_id="normal",
                        rights_violated=False,
                        consent_given=True,
                        duty_owed=False,
                    ),
                ),
            ),
            justice_and_fairness=JusticeAndFairnessV3(
                discriminates_on_protected_attr=False,
                prioritizes_most_disadvantaged=True,
                per_party=(
                    PartyJustice(
                        party_id="vulnerable",
                        relative_burden=0.6,
                        relative_benefit=0.2,
                        is_disadvantaged=True,
                    ),
                    PartyJustice(
                        party_id="normal",
                        relative_burden=0.2,
                        relative_benefit=0.5,
                        is_disadvantaged=False,
                    ),
                ),
            ),
            autonomy_and_agency=AutonomyAndAgencyV3(
                has_meaningful_choice=True,
                coercion_or_undue_influence=False,
                can_withdraw_without_penalty=True,
                manipulative_design_present=False,
            ),
            privacy_and_data=PrivacyAndDataGovernanceV3(
                privacy_invasion_level=0.0,
                data_minimization_respected=True,
                secondary_use_without_consent=False,
                data_retention_excessive=False,
                reidentification_risk=0.0,
            ),
            societal_and_environmental=SocietalAndEnvironmentalV3(
                environmental_harm=0.0,
                long_term_societal_risk=0.0,
                benefits_to_future_generations=0.5,
                burden_on_vulnerable_groups=0.0,
            ),
            virtue_and_care=VirtueAndCareV3(
                expresses_compassion=True,
                betrays_trust=False,
                respects_person_as_end=True,
            ),
            procedural_and_legitimacy=ProceduralAndLegitimacyV3(
                followed_approved_procedure=True,
                stakeholders_consulted=True,
                decision_explainable_to_public=True,
                contestation_available=True,
            ),
            epistemic_status=EpistemicStatusV3(
                uncertainty_level=0.2,
                evidence_quality="high",
                novel_situation_flag=False,
            ),
        )

        judgement = em.judge_distributed(facts)

        # Vulnerable party should have lower virtue_care score due to harm
        tensor = judgement.moral_tensor
        vulnerable_idx = judgement.party_labels.index("vulnerable")
        normal_idx = judgement.party_labels.index("normal")

        # Virtue care dimension (index 6) should be lower for vulnerable party
        assert tensor._data[6, vulnerable_idx] < tensor._data[6, normal_idx]


# =============================================================================
# Test V2↔V3 EM Adapters
# =============================================================================


class TestEMAdapters:
    """Tests for V2↔V3 EM adapters."""

    def test_v2_to_v3_adapter(
        self, v2_facts: EthicalFacts, v3_facts_three_party: EthicalFactsV3
    ) -> None:
        """Test wrapping V2 EM for V3 usage."""
        from erisml.ethics.modules.tier0.geneva_em import GenevaEMV2

        v2_em = GenevaEMV2()
        adapter = V2ToV3EMAdapter(v2_em)

        # Should work with V2 facts
        v2_result = adapter.judge(v2_facts)
        assert isinstance(v2_result, EthicalJudgementV2)

        # Should work with V3 facts (broadcast)
        v3_result = adapter.judge_distributed(v3_facts_three_party)
        assert isinstance(v3_result, EthicalJudgementV3)
        assert v3_result.n_parties == 3

    def test_v3_to_v2_adapter(self, v2_facts: EthicalFacts) -> None:
        """Test wrapping V3 EM for V2 usage."""
        v3_em = GenevaEMV3()
        adapter = V3ToV2EMAdapter(v3_em)

        # Should produce V2 judgement
        result = adapter.judge(v2_facts)
        assert isinstance(result, EthicalJudgementV2)


# =============================================================================
# Test Protocol Compliance
# =============================================================================


class TestProtocolCompliance:
    """Tests for protocol compliance."""

    def test_geneva_em_v3_is_ethics_module_v3(self) -> None:
        """Test that GenevaEMV3 satisfies EthicsModuleV3 protocol."""
        em = GenevaEMV3()

        # Check required attributes
        assert hasattr(em, "em_name")
        assert hasattr(em, "stakeholder")
        assert hasattr(em, "em_tier")

        # Check required methods
        assert callable(getattr(em, "judge", None))
        assert callable(getattr(em, "judge_distributed", None))
        assert callable(getattr(em, "reflex_check", None))
        assert callable(getattr(em, "reflex_check_distributed", None))

    def test_base_class_requires_evaluate_tensor(self) -> None:
        """Test that subclass must implement evaluate_tensor."""

        @dataclass
        class IncompleteEM(BaseEthicsModuleV3):
            em_name: str = "incomplete"

        em = IncompleteEM()

        # Should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            em.evaluate_tensor(None)  # type: ignore


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for V3 ethics modules."""

    def test_full_v3_pipeline(self, v3_facts_three_party: EthicalFactsV3) -> None:
        """Test full V3 ethics assessment pipeline."""
        em = GenevaEMV3()

        # 1. Fast reflex check
        reflex_results = em.reflex_check_distributed(v3_facts_three_party)
        assert all(r is False or r is None for r in reflex_results.values())

        # 2. Full distributed assessment
        judgement = em.judge_distributed(v3_facts_three_party)

        # 3. Verify output structure
        assert judgement.moral_tensor.shape == (9, 3)
        assert len(judgement.per_party_verdicts) == 3
        assert len(judgement.party_labels) == 3

        # 4. Extract individual party assessments
        for party in judgement.party_labels:
            vector = judgement.get_party_vector(party)
            assert isinstance(vector, MoralVector)
            verdict = judgement.get_party_verdict(party)
            assert verdict in [
                "strongly_prefer",
                "prefer",
                "neutral",
                "avoid",
                "forbid",
            ]

        # 5. Collapse to V2 for governance
        v2_judgement = judgement.to_v2(collapse_strategy="mean")
        assert isinstance(v2_judgement, EthicalJudgementV2)

    def test_multi_em_scenario(self, v3_facts_three_party: EthicalFactsV3) -> None:
        """Test scenario with multiple V3 EMs."""
        from erisml.ethics.modules.tier0.geneva_em import GenevaEMV2

        # Mix of V2 and V3 EMs
        v3_em = GenevaEMV3()
        v2_em = GenevaEMV2()
        v2_adapter = V2ToV3EMAdapter(v2_em)

        # Both should be able to assess V3 facts
        j1 = v3_em.judge_distributed(v3_facts_three_party)
        j2 = v2_adapter.judge_distributed(v3_facts_three_party)

        assert j1.n_parties == j2.n_parties
        assert j1.party_labels == j2.party_labels


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_party(self) -> None:
        """Test with single party."""
        facts = EthicalFactsV3(
            option_id="single_party",
            consequences=ConsequencesV3(
                expected_benefit=0.7,
                expected_harm=0.2,
                urgency=0.5,
                affected_count=1,
                per_party=(
                    PartyConsequences(
                        party_id="only_party",
                        expected_benefit=0.7,
                        expected_harm=0.2,
                        vulnerability_weight=0.5,
                    ),
                ),
            ),
            rights_and_duties=RightsAndDutiesV3(
                violates_rights=False,
                has_valid_consent=True,
                violates_explicit_rule=False,
                role_duty_conflict=False,
                per_party=(
                    PartyRights(
                        party_id="only_party",
                        rights_violated=False,
                        consent_given=True,
                        duty_owed=False,
                    ),
                ),
            ),
            justice_and_fairness=JusticeAndFairnessV3(
                discriminates_on_protected_attr=False,
                prioritizes_most_disadvantaged=False,
                per_party=(
                    PartyJustice(
                        party_id="only_party",
                        relative_burden=0.3,
                        relative_benefit=0.7,
                        is_disadvantaged=False,
                    ),
                ),
            ),
            autonomy_and_agency=AutonomyAndAgencyV3(
                has_meaningful_choice=True,
                coercion_or_undue_influence=False,
                can_withdraw_without_penalty=True,
                manipulative_design_present=False,
            ),
            privacy_and_data=PrivacyAndDataGovernanceV3(
                privacy_invasion_level=0.0,
                data_minimization_respected=True,
                secondary_use_without_consent=False,
                data_retention_excessive=False,
                reidentification_risk=0.0,
            ),
            societal_and_environmental=SocietalAndEnvironmentalV3(
                environmental_harm=0.0,
                long_term_societal_risk=0.0,
                benefits_to_future_generations=0.5,
                burden_on_vulnerable_groups=0.0,
            ),
            virtue_and_care=VirtueAndCareV3(
                expresses_compassion=True,
                betrays_trust=False,
                respects_person_as_end=True,
            ),
            procedural_and_legitimacy=ProceduralAndLegitimacyV3(
                followed_approved_procedure=True,
                stakeholders_consulted=True,
                decision_explainable_to_public=True,
                contestation_available=True,
            ),
            epistemic_status=EpistemicStatusV3(
                uncertainty_level=0.2,
                evidence_quality="high",
                novel_situation_flag=False,
            ),
        )

        em = GenevaEMV3()
        judgement = em.judge_distributed(facts)

        assert judgement.n_parties == 1
        assert judgement.party_labels == ("only_party",)

    def test_empty_per_party_verdicts(self, three_party_tensor: MoralTensor) -> None:
        """Test judgement with no explicit per-party verdicts."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="neutral",
            moral_tensor=three_party_tensor,
            # No per_party_verdicts
        )

        # Should fall back to global verdict
        assert judgement.get_party_verdict("alice") == "neutral"

    def test_party_not_found(self, three_party_tensor: MoralTensor) -> None:
        """Test error when party not found."""
        judgement = EthicalJudgementV3(
            option_id="opt1",
            em_name="test_em",
            stakeholder="universal",
            em_tier=0,
            verdict="neutral",
            moral_tensor=three_party_tensor,
        )

        with pytest.raises(KeyError):
            judgement.get_party_vector("nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
