# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
# ruff: noqa: E402
"""
Shared pytest fixtures for DEME 2.0 tests.

Provides common test data and fixtures used across multiple test files.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
    AutonomyAndAgency,
    EpistemicStatus,
)
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.judgement import EthicalJudgement, EthicalJudgementV2
from erisml.ethics.governance.config_v2 import GovernanceConfigV2, DimensionWeights
from erisml.ethics.profile_v04 import DEMEProfileV04


@pytest.fixture
def baseline_ethical_facts() -> EthicalFacts:
    """Standard ethical facts for testing."""
    return EthicalFacts(
        option_id="test_option",
        consequences=Consequences(
            expected_benefit=0.7,
            expected_harm=0.2,
            urgency=0.5,
            affected_count=10,
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
    )


@pytest.fixture
def rights_violating_facts() -> EthicalFacts:
    """Facts with rights violation for veto testing."""
    return EthicalFacts(
        option_id="veto_option",
        consequences=Consequences(
            expected_benefit=0.9,
            expected_harm=0.1,
            urgency=0.3,
            affected_count=5,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=True,  # Should trigger veto
            has_valid_consent=False,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
        ),
    )


@pytest.fixture
def discriminating_facts() -> EthicalFacts:
    """Facts with discrimination for veto testing."""
    return EthicalFacts(
        option_id="discriminating_option",
        consequences=Consequences(
            expected_benefit=0.8,
            expected_harm=0.15,
            urgency=0.4,
            affected_count=20,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=True,  # Should trigger veto
            prioritizes_most_disadvantaged=False,
        ),
    )


@pytest.fixture
def full_ethical_facts() -> EthicalFacts:
    """Ethical facts with all optional dimensions populated."""
    return EthicalFacts(
        option_id="full_option",
        consequences=Consequences(
            expected_benefit=0.75,
            expected_harm=0.25,
            urgency=0.6,
            affected_count=15,
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
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.3,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )


@pytest.fixture
def baseline_moral_vector() -> MoralVector:
    """Standard MoralVector for testing."""
    return MoralVector(
        physical_harm=0.2,
        rights_respect=0.9,
        fairness_equity=0.8,
        autonomy_respect=0.85,
        legitimacy_trust=0.75,
        epistemic_quality=0.7,
    )


@pytest.fixture
def vetoed_moral_vector() -> MoralVector:
    """MoralVector with veto flags."""
    return MoralVector(
        physical_harm=0.8,
        rights_respect=0.0,
        fairness_equity=0.3,
        autonomy_respect=0.4,
        legitimacy_trust=0.2,
        epistemic_quality=0.5,
        veto_flags=["RIGHTS_VIOLATION"],
        reason_codes=["rights_violated"],
    )


@pytest.fixture
def v1_judgement() -> EthicalJudgement:
    """Sample V1 judgement for migration testing."""
    return EthicalJudgement(
        option_id="test_option",
        em_name="test_em",
        stakeholder="test_stakeholder",
        verdict="prefer",
        normative_score=0.75,
        reasons=["Test reason 1", "Test reason 2"],
        metadata={"test_key": "test_value"},
    )


@pytest.fixture
def v2_judgement(baseline_moral_vector: MoralVector) -> EthicalJudgementV2:
    """Sample V2 judgement."""
    return EthicalJudgementV2(
        option_id="test_option",
        em_name="test_em_v2",
        stakeholder="test_stakeholder",
        em_tier=2,
        verdict="prefer",
        moral_vector=baseline_moral_vector,
        veto_triggered=False,
        confidence=0.9,
        reasons=["V2 test reason"],
        metadata={"v2_key": "v2_value"},
    )


@pytest.fixture
def v2_governance_config() -> GovernanceConfigV2:
    """Standard V2 governance config for testing."""
    return GovernanceConfigV2(
        dimension_weights=DimensionWeights(
            physical_harm=1.0,
            rights_respect=1.0,
            fairness_equity=1.0,
            autonomy_respect=1.0,
            legitimacy_trust=1.0,
            epistemic_quality=0.5,
        ),
    )


@pytest.fixture
def sample_profile_v04() -> DEMEProfileV04:
    """Sample V04 profile for testing."""
    return DEMEProfileV04(
        name="Test Profile V04",
        description="A test profile for DEME 2.0",
        stakeholder_label="test_stakeholder",
    )
