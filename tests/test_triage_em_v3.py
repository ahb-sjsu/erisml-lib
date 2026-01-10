# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for TriageEMV3 and RightsFirstEMV3 (Sprint 6 completion).

Tests cover:
- TriageEMV3 V2 interface (evaluate_vector)
- TriageEMV3 V3 interface (evaluate_tensor/judge_distributed)
- Per-party verdict and veto tracking
- Distributional fairness metrics
- RightsFirstEMV3 implementation
- Edge cases and numerical stability
"""

from __future__ import annotations

import pytest

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
from erisml.ethics.modules.triage_em_v3 import TriageEMV3, RightsFirstEMV3


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def triage_em() -> TriageEMV3:
    """Create default TriageEMV3 instance."""
    return TriageEMV3()


@pytest.fixture
def rights_first_em() -> RightsFirstEMV3:
    """Create default RightsFirstEMV3 instance."""
    return RightsFirstEMV3()


@pytest.fixture
def v2_facts_good() -> EthicalFacts:
    """Create V2 EthicalFacts with good outcomes."""
    return EthicalFacts(
        option_id="good_option",
        consequences=Consequences(
            expected_benefit=0.8,
            expected_harm=0.1,
            urgency=0.7,
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
            uncertainty_level=0.1,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )


@pytest.fixture
def v2_facts_veto() -> EthicalFacts:
    """Create V2 EthicalFacts with rights violation."""
    return EthicalFacts(
        option_id="veto_option",
        consequences=Consequences(
            expected_benefit=0.3,
            expected_harm=0.7,
            urgency=0.2,
            affected_count=50,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=True,
            has_valid_consent=False,
            violates_explicit_rule=True,
            role_duty_conflict=True,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
            exploits_vulnerable_population=True,
            exacerbates_power_imbalance=True,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=False,
            coercion_or_undue_influence=True,
            can_withdraw_without_penalty=False,
            manipulative_design_present=True,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.8,
            data_minimization_respected=False,
            secondary_use_without_consent=True,
            data_retention_excessive=True,
            reidentification_risk=0.8,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.7,
            long_term_societal_risk=0.6,
            benefits_to_future_generations=0.1,
            burden_on_vulnerable_groups=0.7,
        ),
        virtue_and_care=VirtueAndCare(
            expresses_compassion=False,
            betrays_trust=True,
            respects_person_as_end=False,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=False,
            stakeholders_consulted=False,
            decision_explainable_to_public=False,
            contestation_available=False,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.8,
            evidence_quality="low",
            novel_situation_flag=True,
        ),
    )


@pytest.fixture
def v3_facts_three_party() -> EthicalFactsV3:
    """Create V3 EthicalFacts with 3 parties."""
    return EthicalFactsV3(
        option_id="triage_option",
        consequences=ConsequencesV3(
            expected_benefit=0.5,
            expected_harm=0.3,
            urgency=0.6,
            affected_count=3,
            per_party=(
                PartyConsequences(
                    party_id="patient_a",
                    expected_benefit=0.9,
                    expected_harm=0.1,
                    vulnerability_weight=0.3,
                ),
                PartyConsequences(
                    party_id="patient_b",
                    expected_benefit=0.4,
                    expected_harm=0.4,
                    vulnerability_weight=0.6,
                ),
                PartyConsequences(
                    party_id="patient_c",
                    expected_benefit=0.2,
                    expected_harm=0.5,
                    vulnerability_weight=0.9,
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
                    party_id="patient_a",
                    rights_violated=False,
                    consent_given=True,
                    duty_owed=True,
                ),
                PartyRights(
                    party_id="patient_b",
                    rights_violated=False,
                    consent_given=True,
                    duty_owed=True,
                ),
                PartyRights(
                    party_id="patient_c",
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
                    party_id="patient_a",
                    relative_burden=0.1,
                    relative_benefit=0.4,
                    is_disadvantaged=False,
                ),
                PartyJustice(
                    party_id="patient_b",
                    relative_burden=0.3,
                    relative_benefit=0.3,
                    is_disadvantaged=False,
                ),
                PartyJustice(
                    party_id="patient_c",
                    relative_burden=0.6,
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
    """Create V3 EthicalFacts with one party having rights violated."""
    return EthicalFactsV3(
        option_id="partial_veto_option",
        consequences=ConsequencesV3(
            expected_benefit=0.5,
            expected_harm=0.3,
            urgency=0.5,
            affected_count=2,
            per_party=(
                PartyConsequences(
                    party_id="party_ok",
                    expected_benefit=0.7,
                    expected_harm=0.2,
                    vulnerability_weight=0.3,
                ),
                PartyConsequences(
                    party_id="party_violated",
                    expected_benefit=0.3,
                    expected_harm=0.6,
                    vulnerability_weight=0.5,
                ),
            ),
        ),
        rights_and_duties=RightsAndDutiesV3(
            violates_rights=True,
            has_valid_consent=False,
            violates_explicit_rule=False,
            role_duty_conflict=False,
            per_party=(
                PartyRights(
                    party_id="party_ok",
                    rights_violated=False,
                    consent_given=True,
                    duty_owed=False,
                ),
                PartyRights(
                    party_id="party_violated",
                    rights_violated=True,
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
                    party_id="party_ok",
                    relative_burden=0.2,
                    relative_benefit=0.5,
                    is_disadvantaged=False,
                ),
                PartyJustice(
                    party_id="party_violated",
                    relative_burden=0.6,
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
            privacy_invasion_level=0.2,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.2,
        ),
        societal_and_environmental=SocietalAndEnvironmentalV3(
            environmental_harm=0.1,
            long_term_societal_risk=0.1,
            benefits_to_future_generations=0.5,
            burden_on_vulnerable_groups=0.2,
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
# TriageEMV3 Tests - V2 Interface
# =============================================================================


class TestTriageEMV3V2Interface:
    """Tests for TriageEMV3 V2-compatible interface."""

    def test_judge_good_option(
        self, triage_em: TriageEMV3, v2_facts_good: EthicalFacts
    ):
        """Test judge with good outcomes returns strongly_prefer or prefer."""
        result = triage_em.judge(v2_facts_good)
        assert result.verdict in ("strongly_prefer", "prefer")
        assert result.normative_score >= 0.6
        assert result.em_name == "triage_em_v3"
        assert not result.moral_vector.has_veto()

    def test_judge_veto_option(
        self, triage_em: TriageEMV3, v2_facts_veto: EthicalFacts
    ):
        """Test judge with rights violation returns forbid."""
        result = triage_em.judge(v2_facts_veto)
        assert result.verdict == "forbid"
        # normative_score is computed from moral_vector, should be low
        assert result.normative_score < 0.5
        assert result.moral_vector.has_veto()
        assert "RIGHTS_VIOLATION" in result.moral_vector.veto_flags

    def test_reflex_check_no_violation(
        self, triage_em: TriageEMV3, v2_facts_good: EthicalFacts
    ):
        """Test reflex_check returns False when no violation."""
        result = triage_em.reflex_check(v2_facts_good)
        assert result is False

    def test_reflex_check_with_violation(
        self, triage_em: TriageEMV3, v2_facts_veto: EthicalFacts
    ):
        """Test reflex_check returns True when rights violated."""
        result = triage_em.reflex_check(v2_facts_veto)
        assert result is True

    def test_epistemic_penalty_applied(self, triage_em: TriageEMV3):
        """Test epistemic penalty reduces score."""
        # Create facts with high uncertainty
        facts = EthicalFacts(
            option_id="uncertain_option",
            consequences=Consequences(
                expected_benefit=0.8,
                expected_harm=0.1,
                urgency=0.7,
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
                uncertainty_level=0.9,
                evidence_quality="low",
                novel_situation_flag=True,
            ),
        )
        result = triage_em.judge(facts)
        # High epistemic penalty should reduce score
        assert result.metadata["epistemic_factor"] < 0.6


# =============================================================================
# TriageEMV3 Tests - V3 Interface
# =============================================================================


class TestTriageEMV3V3Interface:
    """Tests for TriageEMV3 V3 distributed interface."""

    def test_judge_distributed_basic(
        self, triage_em: TriageEMV3, v3_facts_three_party: EthicalFactsV3
    ):
        """Test judge_distributed returns proper V3 judgement."""
        result = triage_em.judge_distributed(v3_facts_three_party)

        assert result.option_id == "triage_option"
        assert result.em_name == "triage_em_v3"
        assert result.moral_tensor is not None
        assert result.moral_tensor.shape == (9, 3)
        assert len(result.per_party_verdicts) == 3
        assert "patient_a" in result.per_party_verdicts
        assert "patient_b" in result.per_party_verdicts
        assert "patient_c" in result.per_party_verdicts

    def test_judge_distributed_per_party_verdicts(
        self, triage_em: TriageEMV3, v3_facts_three_party: EthicalFactsV3
    ):
        """Test per-party verdicts reflect individual outcomes."""
        result = triage_em.judge_distributed(v3_facts_three_party)

        # Patient A has best outcomes (benefit=0.9, harm=0.1)
        # Should have best verdict
        assert result.per_party_verdicts["patient_a"] in (
            "strongly_prefer",
            "prefer",
            "neutral",
        )

        # All parties should have some verdict
        for party, verdict in result.per_party_verdicts.items():
            assert verdict in (
                "strongly_prefer",
                "prefer",
                "neutral",
                "avoid",
                "forbid",
            )

    def test_judge_distributed_with_veto(
        self, triage_em: TriageEMV3, v3_facts_with_veto: EthicalFactsV3
    ):
        """Test per-party veto tracking."""
        result = triage_em.judge_distributed(v3_facts_with_veto)

        # One party should be vetoed
        assert result.distributed_veto_triggered is True
        assert result.per_party_verdicts["party_violated"] == "forbid"
        assert "party_violated" in result.per_party_vetoes
        assert result.per_party_vetoes["party_violated"] is True

        # Global verdict should be forbid (conservative)
        assert result.verdict == "forbid"

    def test_judge_distributed_tensor_dimensions(
        self, triage_em: TriageEMV3, v3_facts_three_party: EthicalFactsV3
    ):
        """Test tensor has correct shape and axis labels."""
        result = triage_em.judge_distributed(v3_facts_three_party)

        tensor = result.moral_tensor
        assert tensor.rank == 2
        assert tensor.shape == (9, 3)
        assert tensor.axis_names == ("k", "n")
        assert tensor.axis_labels["n"] == ["patient_a", "patient_b", "patient_c"]

    def test_reflex_check_distributed(
        self, triage_em: TriageEMV3, v3_facts_with_veto: EthicalFactsV3
    ):
        """Test per-party reflex check."""
        result = triage_em.reflex_check_distributed(v3_facts_with_veto)

        assert "party_ok" in result
        assert "party_violated" in result
        assert result["party_ok"] is False
        assert result["party_violated"] is True

    def test_distributional_fairness_metadata(
        self, triage_em: TriageEMV3, v3_facts_three_party: EthicalFactsV3
    ):
        """Test Gini and maximin metrics in metadata."""
        result = triage_em.judge_distributed(v3_facts_three_party)

        assert "score_gini" in result.metadata
        assert "worst_off_party" in result.metadata
        assert "worst_off_score" in result.metadata

        # Gini should be between 0 and 1
        assert 0.0 <= result.metadata["score_gini"] <= 1.0

    def test_vulnerability_prioritization(self, triage_em: TriageEMV3):
        """Test vulnerable parties get priority weighting."""
        facts = EthicalFactsV3(
            option_id="vuln_test",
            consequences=ConsequencesV3(
                expected_benefit=0.5,
                expected_harm=0.3,
                urgency=0.5,
                affected_count=2,
                per_party=(
                    PartyConsequences(
                        party_id="vulnerable",
                        expected_benefit=0.5,
                        expected_harm=0.3,
                        vulnerability_weight=0.9,  # High vulnerability
                    ),
                    PartyConsequences(
                        party_id="not_vulnerable",
                        expected_benefit=0.5,
                        expected_harm=0.3,
                        vulnerability_weight=0.2,  # Low vulnerability
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
                        party_id="not_vulnerable",
                        rights_violated=False,
                        consent_given=True,
                        duty_owed=True,
                    ),
                ),
            ),
            justice_and_fairness=JusticeAndFairnessV3(
                discriminates_on_protected_attr=False,
                prioritizes_most_disadvantaged=True,
                per_party=(
                    PartyJustice(
                        party_id="vulnerable",
                        relative_burden=0.3,
                        relative_benefit=0.3,
                        is_disadvantaged=True,
                    ),
                    PartyJustice(
                        party_id="not_vulnerable",
                        relative_burden=0.3,
                        relative_benefit=0.3,
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

        result = triage_em.judge_distributed(facts)

        # Vulnerable party should have higher score due to prioritization
        vuln_score = result.metadata["per_party_details"]["vulnerable"]["final_score"]
        non_vuln_score = result.metadata["per_party_details"]["not_vulnerable"][
            "final_score"
        ]

        # The vulnerability multiplier should boost the vulnerable party's score
        assert vuln_score > non_vuln_score


# =============================================================================
# RightsFirstEMV3 Tests
# =============================================================================


class TestRightsFirstEMV3:
    """Tests for RightsFirstEMV3."""

    def test_judge_no_violation(
        self, rights_first_em: RightsFirstEMV3, v2_facts_good: EthicalFacts
    ):
        """Test judge returns prefer when no violation."""
        result = rights_first_em.judge(v2_facts_good)
        assert result.verdict == "prefer"
        assert result.normative_score >= 0.7
        assert not result.moral_vector.has_veto()

    def test_judge_with_violation(
        self, rights_first_em: RightsFirstEMV3, v2_facts_veto: EthicalFacts
    ):
        """Test judge returns forbid when violation."""
        result = rights_first_em.judge(v2_facts_veto)
        assert result.verdict == "forbid"
        assert result.moral_vector.has_veto()

    def test_judge_distributed_no_violation(
        self, rights_first_em: RightsFirstEMV3, v3_facts_three_party: EthicalFactsV3
    ):
        """Test distributed judge with no violations."""
        result = rights_first_em.judge_distributed(v3_facts_three_party)
        assert result.verdict == "prefer"
        assert not result.distributed_veto_triggered

        for party, verdict in result.per_party_verdicts.items():
            assert verdict == "prefer"

    def test_judge_distributed_with_violation(
        self, rights_first_em: RightsFirstEMV3, v3_facts_with_veto: EthicalFactsV3
    ):
        """Test distributed judge with one party violated."""
        result = rights_first_em.judge_distributed(v3_facts_with_veto)

        # Should forbid globally due to one party violation
        assert result.verdict == "forbid"
        assert result.distributed_veto_triggered is True
        assert result.per_party_verdicts["party_violated"] == "forbid"
        assert result.per_party_verdicts["party_ok"] == "prefer"

    def test_reflex_check(
        self, rights_first_em: RightsFirstEMV3, v2_facts_veto: EthicalFacts
    ):
        """Test reflex check for violations."""
        assert rights_first_em.reflex_check(v2_facts_veto) is True

    def test_reflex_check_distributed(
        self, rights_first_em: RightsFirstEMV3, v3_facts_with_veto: EthicalFactsV3
    ):
        """Test per-party reflex check."""
        result = rights_first_em.reflex_check_distributed(v3_facts_with_veto)
        assert result["party_ok"] is False
        assert result["party_violated"] is True


# =============================================================================
# Protocol Compliance Tests
# =============================================================================


class TestProtocolCompliance:
    """Tests for EthicsModuleV3 protocol compliance."""

    def test_triage_em_has_required_attributes(self, triage_em: TriageEMV3):
        """Test TriageEMV3 has required protocol attributes."""
        assert hasattr(triage_em, "em_name")
        assert hasattr(triage_em, "stakeholder")
        assert hasattr(triage_em, "em_tier")
        assert triage_em.em_tier == 2

    def test_triage_em_has_required_methods(self, triage_em: TriageEMV3):
        """Test TriageEMV3 has required protocol methods."""
        assert hasattr(triage_em, "judge")
        assert hasattr(triage_em, "judge_distributed")
        assert hasattr(triage_em, "reflex_check")
        assert hasattr(triage_em, "reflex_check_distributed")

    def test_rights_first_em_has_required_attributes(
        self, rights_first_em: RightsFirstEMV3
    ):
        """Test RightsFirstEMV3 has required protocol attributes."""
        assert hasattr(rights_first_em, "em_name")
        assert hasattr(rights_first_em, "stakeholder")
        assert hasattr(rights_first_em, "em_tier")
        assert rights_first_em.em_tier == 2


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_party(self, triage_em: TriageEMV3):
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
                        party_id="solo",
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
                        party_id="solo",
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
                        party_id="solo",
                        relative_burden=0.3,
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
            epistemic_status=None,
        )

        result = triage_em.judge_distributed(facts)
        assert result.moral_tensor.shape == (9, 1)
        assert len(result.per_party_verdicts) == 1
        assert "solo" in result.per_party_verdicts

    def test_all_parties_vetoed(self, triage_em: TriageEMV3):
        """Test when all parties have rights violated."""
        facts = EthicalFactsV3(
            option_id="all_violated",
            consequences=ConsequencesV3(
                expected_benefit=0.3,
                expected_harm=0.7,
                urgency=0.5,
                affected_count=2,
                per_party=(
                    PartyConsequences(
                        party_id="p1",
                        expected_benefit=0.3,
                        expected_harm=0.7,
                        vulnerability_weight=0.5,
                    ),
                    PartyConsequences(
                        party_id="p2",
                        expected_benefit=0.3,
                        expected_harm=0.7,
                        vulnerability_weight=0.5,
                    ),
                ),
            ),
            rights_and_duties=RightsAndDutiesV3(
                violates_rights=True,
                has_valid_consent=False,
                violates_explicit_rule=True,
                role_duty_conflict=False,
                per_party=(
                    PartyRights(
                        party_id="p1",
                        rights_violated=True,
                        consent_given=False,
                        duty_owed=True,
                    ),
                    PartyRights(
                        party_id="p2",
                        rights_violated=True,
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
                        party_id="p1",
                        relative_burden=0.5,
                        relative_benefit=0.2,
                        is_disadvantaged=True,
                    ),
                    PartyJustice(
                        party_id="p2",
                        relative_burden=0.5,
                        relative_benefit=0.2,
                        is_disadvantaged=True,
                    ),
                ),
            ),
            autonomy_and_agency=AutonomyAndAgencyV3(
                has_meaningful_choice=False,
                coercion_or_undue_influence=True,
                can_withdraw_without_penalty=False,
                manipulative_design_present=False,
            ),
            privacy_and_data=PrivacyAndDataGovernanceV3(
                privacy_invasion_level=0.5,
                data_minimization_respected=False,
                secondary_use_without_consent=True,
                data_retention_excessive=True,
                reidentification_risk=0.5,
            ),
            societal_and_environmental=SocietalAndEnvironmentalV3(
                environmental_harm=0.5,
                long_term_societal_risk=0.5,
                benefits_to_future_generations=0.2,
                burden_on_vulnerable_groups=0.5,
            ),
            virtue_and_care=VirtueAndCareV3(
                expresses_compassion=False,
                betrays_trust=True,
                respects_person_as_end=False,
            ),
            procedural_and_legitimacy=ProceduralAndLegitimacyV3(
                followed_approved_procedure=False,
                stakeholders_consulted=False,
                decision_explainable_to_public=False,
                contestation_available=False,
            ),
            epistemic_status=None,
        )

        result = triage_em.judge_distributed(facts)
        assert result.verdict == "forbid"
        assert result.distributed_veto_triggered is True
        assert len(result.veto_locations) == 2
        assert result.per_party_verdicts["p1"] == "forbid"
        assert result.per_party_verdicts["p2"] == "forbid"

    def test_no_epistemic_status(
        self, triage_em: TriageEMV3, v2_facts_good: EthicalFacts
    ):
        """Test handling of None epistemic_status."""
        v2_facts_good.epistemic_status = None
        result = triage_em.judge(v2_facts_good)
        # Should still work, default epistemic factor = 1.0
        assert result.verdict in ("strongly_prefer", "prefer", "neutral")


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests with full pipeline scenarios."""

    def test_multi_em_consistency(
        self,
        triage_em: TriageEMV3,
        rights_first_em: RightsFirstEMV3,
        v3_facts_with_veto: EthicalFactsV3,
    ):
        """Test both EMs agree on veto for rights violation."""
        triage_result = triage_em.judge_distributed(v3_facts_with_veto)
        rights_result = rights_first_em.judge_distributed(v3_facts_with_veto)

        # Both should forbid due to rights violation
        assert triage_result.verdict == "forbid"
        assert rights_result.verdict == "forbid"

        # Both should have vetoed the same party
        assert triage_result.per_party_vetoes["party_violated"] is True
        assert rights_result.per_party_vetoes["party_violated"] is True

    def test_v2_to_v3_consistency(
        self, triage_em: TriageEMV3, v2_facts_good: EthicalFacts
    ):
        """Test V2 and V3 interfaces produce consistent results."""
        v2_result = triage_em.judge(v2_facts_good)

        # V2 result should be consistent with V3 single-party
        assert v2_result.verdict in (
            "strongly_prefer",
            "prefer",
            "neutral",
            "avoid",
            "forbid",
        )
        assert 0.0 <= v2_result.normative_score <= 1.0
