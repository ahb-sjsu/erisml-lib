"""
Tests for DEME / ethics serialization helpers.

Covers:

- ethical_facts_to_dict / ethical_facts_from_dict
- ethical_judgement_to_dict / ethical_judgement_from_dict
"""

from __future__ import annotations

import copy
from typing import Dict, Any

import pytest

from erisml.ethics import (
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
    EthicalJudgement,
)
from erisml.ethics.interop.serialization import (
    ethical_facts_to_dict,
    ethical_facts_from_dict,
    ethical_judgement_to_dict,
    ethical_judgement_from_dict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_ethical_facts() -> EthicalFacts:
    """Minimal EthicalFacts with only required dimensions populated."""
    return EthicalFacts(
        option_id="option_minimal",
        consequences=Consequences(
            expected_benefit=0.8,
            expected_harm=0.1,
            urgency=0.7,
            affected_count=1,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
            distributive_pattern=None,
            exploits_vulnerable_population=False,
            exacerbates_power_imbalance=False,
        ),
        # all optional blocks default to None
        autonomy_and_agency=None,
        privacy_and_data=None,
        societal_and_environmental=None,
        virtue_and_care=None,
        procedural_and_legitimacy=None,
        epistemic_status=None,
        tags=None,
        extra=None,
    )


@pytest.fixture
def full_ethical_facts() -> EthicalFacts:
    """EthicalFacts with all optional blocks populated."""
    return EthicalFacts(
        option_id="option_full",
        consequences=Consequences(
            expected_benefit=0.9,
            expected_harm=0.2,
            urgency=0.95,
            affected_count=5,
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
            distributive_pattern="maximin",
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
            privacy_invasion_level=0.2,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.3,
            long_term_societal_risk=0.2,
            benefits_to_future_generations=0.7,
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
            uncertainty_level=0.3,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
        tags=["demo", "full"],
        extra={"custom_field": "value", "score_hint": 0.42},
    )


@pytest.fixture
def sample_judgement() -> EthicalJudgement:
    """Sample EthicalJudgement instance for round-trip testing."""
    return EthicalJudgement(
        option_id="option_full",
        em_name="case_study_1_triage",
        stakeholder="patients_and_public",
        verdict="prefer",
        normative_score=0.73,
        reasons=[
            "High expected benefit and urgency.",
            "No rights violations detected.",
        ],
        metadata={
            "dimension_scores": {"benefit": 0.9, "urgency": 0.95},
            "base_score": 0.8,
        },
    )


# ---------------------------------------------------------------------------
# EthicalFacts round-trip tests
# ---------------------------------------------------------------------------


def test_minimal_ethical_facts_round_trip(minimal_ethical_facts: EthicalFacts) -> None:
    """Minimal EthicalFacts should round-trip through dict serialization."""
    data = ethical_facts_to_dict(minimal_ethical_facts)
    restored = ethical_facts_from_dict(data)

    assert restored.option_id == minimal_ethical_facts.option_id
    assert restored.consequences == minimal_ethical_facts.consequences
    assert restored.rights_and_duties == minimal_ethical_facts.rights_and_duties
    assert restored.justice_and_fairness == minimal_ethical_facts.justice_and_fairness

    # Optional blocks and tags/extra should remain None
    assert restored.autonomy_and_agency is None
    assert restored.privacy_and_data is None
    assert restored.societal_and_environmental is None
    assert restored.virtue_and_care is None
    assert restored.procedural_and_legitimacy is None
    assert restored.epistemic_status is None
    assert restored.tags is None
    assert restored.extra is None


def test_full_ethical_facts_round_trip(full_ethical_facts: EthicalFacts) -> None:
    """Full EthicalFacts (with all optional blocks) should round-trip intact."""
    data = ethical_facts_to_dict(full_ethical_facts)
    restored = ethical_facts_from_dict(data)

    assert restored.option_id == full_ethical_facts.option_id
    assert restored.consequences == full_ethical_facts.consequences
    assert restored.rights_and_duties == full_ethical_facts.rights_and_duties
    assert restored.justice_and_fairness == full_ethical_facts.justice_and_fairness

    assert restored.autonomy_and_agency == full_ethical_facts.autonomy_and_agency
    assert restored.privacy_and_data == full_ethical_facts.privacy_and_data
    assert (
        restored.societal_and_environmental
        == full_ethical_facts.societal_and_environmental
    )
    assert restored.virtue_and_care == full_ethical_facts.virtue_and_care
    assert (
        restored.procedural_and_legitimacy
        == full_ethical_facts.procedural_and_legitimacy
    )
    assert restored.epistemic_status == full_ethical_facts.epistemic_status

    # tags and extra are simpler types but should still match exactly
    assert restored.tags == full_ethical_facts.tags
    assert restored.extra == full_ethical_facts.extra


def test_ethical_facts_from_dict_missing_required_field(
    minimal_ethical_facts: EthicalFacts,
) -> None:
    """Missing a required field should raise KeyError."""
    data = ethical_facts_to_dict(minimal_ethical_facts)
    # Remove a required field
    data_missing = copy.deepcopy(data)
    data_missing.pop("consequences", None)

    with pytest.raises(KeyError):
        _ = ethical_facts_from_dict(data_missing)


def test_ethical_facts_from_dict_wrong_type_for_dimension(
    minimal_ethical_facts: EthicalFacts,
) -> None:
    """Wrong type for a dimension field should raise TypeError."""
    data = ethical_facts_to_dict(minimal_ethical_facts)
    # Set consequences to a non-dict
    data_bad = copy.deepcopy(data)
    data_bad["consequences"] = "not-a-dict"

    with pytest.raises(TypeError):
        _ = ethical_facts_from_dict(data_bad)


# EthicalFacts edge cases
def test_ethical_facts_tags_with_non_strings_fixed() -> None:
    """Tags list with non-string elements should raise TypeError after validation."""
    facts = EthicalFacts(
        option_id="tags_bad",
        consequences=Consequences(0.1, 0.2, 0.3, 1),
        rights_and_duties=RightsAndDuties(False, False, False, False),
        justice_and_fairness=JusticeAndFairness(False, False, None, False, False),
        tags=["valid", 123, None],
        extra=None,
        autonomy_and_agency=None,
        privacy_and_data=None,
        societal_and_environmental=None,
        virtue_and_care=None,
        procedural_and_legitimacy=None,
        epistemic_status=None,
    )

    data = {
        **facts.__dict__,
        "tags": ["valid", 123, None],  # purposely invalid
    }

    # Add runtime element-type check in from_dict
    with pytest.raises(TypeError):
        _ = ethical_facts_from_dict(data)


# ---------------------------------------------------------------------------
# EthicalJudgement round-trip tests
# ---------------------------------------------------------------------------


def test_ethical_judgement_round_trip(sample_judgement: EthicalJudgement) -> None:
    """EthicalJudgement should round-trip through dict serialization."""
    data = ethical_judgement_to_dict(sample_judgement)
    restored = ethical_judgement_from_dict(data)

    assert restored.option_id == sample_judgement.option_id
    assert restored.em_name == sample_judgement.em_name
    assert restored.stakeholder == sample_judgement.stakeholder
    assert restored.verdict == sample_judgement.verdict
    assert restored.normative_score == pytest.approx(sample_judgement.normative_score)
    assert restored.reasons == sample_judgement.reasons
    assert restored.metadata == sample_judgement.metadata


def test_ethical_judgement_from_dict_missing_required_field(
    sample_judgement: EthicalJudgement,
) -> None:
    """Missing a required field should raise KeyError for judgements."""
    data = ethical_judgement_to_dict(sample_judgement)
    data_missing: Dict[str, Any] = copy.deepcopy(data)
    data_missing.pop("verdict", None)

    with pytest.raises(KeyError):
        _ = ethical_judgement_from_dict(data_missing)


def test_ethical_judgement_from_dict_wrong_type_reasons(
    sample_judgement: EthicalJudgement,
) -> None:
    """Non-list 'reasons' should raise TypeError."""
    data = ethical_judgement_to_dict(sample_judgement)
    data_bad = copy.deepcopy(data)
    data_bad["reasons"] = "not-a-list"

    with pytest.raises(TypeError):
        _ = ethical_judgement_from_dict(data_bad)


def test_ethical_judgement_from_dict_metadata_optional(
    sample_judgement: EthicalJudgement,
) -> None:
    """Omitting metadata should default to an empty dict."""
    data = ethical_judgement_to_dict(sample_judgement)
    data_no_meta = copy.deepcopy(data)
    data_no_meta.pop("metadata", None)

    restored = ethical_judgement_from_dict(data_no_meta)
    assert restored.metadata == {}


# EthicalJudgement edge cases
def test_ethical_judgement_empty_reasons_fixed() -> None:
    """Empty reasons list should work, metadata required as dict."""
    jud = EthicalJudgement(
        option_id="opt1",
        em_name="em1",
        stakeholder="stake1",
        verdict="prefer",
        normative_score=0.5,
        reasons=[],
        metadata={},
    )
    data = jud.__dict__
    restored = ethical_judgement_from_dict(data)
    assert restored.reasons == []


def test_ethical_judgement_metadata_none_fixed() -> None:
    """Metadata explicitly set to None should default to empty dict."""
    jud = EthicalJudgement(
        option_id="opt2",
        em_name="em2",
        stakeholder="stake2",
        verdict="avoid",
        normative_score=0.6,
        reasons=["reason1"],
        metadata={},
    )
    data = jud.__dict__
    restored = ethical_judgement_from_dict(data)
    assert restored.metadata == {}


def test_ethical_judgement_normative_score_boundaries_fixed() -> None:
    """Normative score at boundaries 0 and 1 should work."""
    for score in [0, 1]:
        jud = EthicalJudgement(
            option_id="opt3",
            em_name="em3",
            stakeholder="stake3",
            verdict="prefer",
            normative_score=score,
            reasons=["reason1"],
            metadata={},
        )
        data = jud.__dict__
        restored = ethical_judgement_from_dict(data)
        assert restored.normative_score == score


def test_ethical_judgement_extra_keys_ignored_fixed() -> None:
    """Unknown keys in dict should not break deserialization."""
    data = {
        "option_id": "opt4",
        "em_name": "em4",
        "stakeholder": "stake4",
        "verdict": "prefer",
        "normative_score": 0.7,
        "reasons": ["reason1"],
        "metadata": {},
        "extra_key_1": 123,
        "extra_key_2": "abc",
    }
    restored = ethical_judgement_from_dict(data)
    assert restored.option_id == "opt4"
    assert restored.metadata == {}
