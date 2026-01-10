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
    """Standard MoralVector for testing (8+1 dimensions)."""
    return MoralVector(
        physical_harm=0.2,
        rights_respect=0.9,
        fairness_equity=0.8,
        autonomy_respect=0.85,
        privacy_protection=0.9,
        societal_environmental=0.8,
        virtue_care=0.85,
        legitimacy_trust=0.75,
        epistemic_quality=0.7,
    )


@pytest.fixture
def vetoed_moral_vector() -> MoralVector:
    """MoralVector with veto flags (8+1 dimensions)."""
    return MoralVector(
        physical_harm=0.8,
        rights_respect=0.0,
        fairness_equity=0.3,
        autonomy_respect=0.4,
        privacy_protection=0.5,
        societal_environmental=0.4,
        virtue_care=0.3,
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
    """Standard V2 governance config for testing (8+1 dimensions)."""
    return GovernanceConfigV2(
        dimension_weights=DimensionWeights(
            physical_harm=1.0,
            rights_respect=1.0,
            fairness_equity=1.0,
            autonomy_respect=1.0,
            privacy_protection=1.0,
            societal_environmental=0.8,
            virtue_care=0.7,
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


# =============================================================================
# DEME V3 Fixtures (MoralTensor)
# =============================================================================

from erisml.ethics.moral_tensor import MoralTensor, SparseCOO
import numpy as np


@pytest.fixture
def rank1_tensor() -> MoralTensor:
    """Basic rank-1 tensor (9,) - equivalent to MoralVector."""
    return MoralTensor.from_dense(
        np.array([0.2, 0.9, 0.8, 0.85, 0.9, 0.8, 0.85, 0.75, 0.7])
    )


@pytest.fixture
def rank2_tensor() -> MoralTensor:
    """Rank-2 tensor (9, 3) with 3 parties."""
    data = np.array(
        [
            [0.1, 0.2, 0.3],  # physical_harm
            [0.9, 0.8, 0.7],  # rights_respect
            [0.8, 0.85, 0.9],  # fairness_equity
            [0.85, 0.8, 0.75],  # autonomy_respect
            [0.9, 0.85, 0.8],  # privacy_protection
            [0.8, 0.75, 0.7],  # societal_environmental
            [0.85, 0.9, 0.8],  # virtue_care
            [0.75, 0.8, 0.85],  # legitimacy_trust
            [0.7, 0.75, 0.8],  # epistemic_quality
        ]
    )
    return MoralTensor.from_dense(
        data,
        axis_labels={"n": ["alice", "bob", "carol"]},
    )


@pytest.fixture
def rank3_tensor() -> MoralTensor:
    """Rank-3 tensor (9, 2, 4) with 2 parties over 4 time steps."""
    np.random.seed(42)
    data = np.random.rand(9, 2, 4)
    data = np.clip(data, 0.1, 0.9)
    return MoralTensor.from_dense(
        data,
        axis_labels={
            "n": ["party_a", "party_b"],
            "tau": ["t0", "t1", "t2", "t3"],
        },
    )


@pytest.fixture
def sparse_tensor() -> MoralTensor:
    """Sparse tensor for efficiency tests."""
    # Create sparse tensor with only a few non-zero values
    coords = np.array(
        [
            [0, 0],  # physical_harm for party 0
            [1, 1],  # rights_respect for party 1
            [2, 2],  # fairness_equity for party 2
        ],
        dtype=np.int32,
    )
    values = np.array([0.3, 0.8, 0.9], dtype=np.float64)

    return MoralTensor.from_sparse(
        coords=coords,
        values=values,
        shape=(9, 3),
        fill_value=0.5,  # Default ethical score
    )


@pytest.fixture
def vetoed_tensor() -> MoralTensor:
    """Tensor with veto flags and locations."""
    data = np.array(
        [
            [0.8, 0.2, 0.3],  # physical_harm (high for party 0)
            [0.1, 0.9, 0.8],  # rights_respect (low for party 0)
            [0.3, 0.8, 0.9],  # fairness_equity
            [0.4, 0.85, 0.8],  # autonomy_respect
            [0.5, 0.9, 0.85],  # privacy_protection
            [0.4, 0.8, 0.75],  # societal_environmental
            [0.3, 0.85, 0.9],  # virtue_care
            [0.2, 0.75, 0.8],  # legitimacy_trust
            [0.5, 0.7, 0.75],  # epistemic_quality
        ]
    )
    return MoralTensor.from_dense(
        data,
        axis_labels={"n": ["harmful_party", "neutral_party", "good_party"]},
        veto_flags=["RIGHTS_VIOLATION", "HIGH_HARM"],
        veto_locations=[(0,)],  # Veto applies to party 0
        reason_codes=["rights_violated", "harm_above_threshold"],
    )


@pytest.fixture
def ideal_tensor() -> MoralTensor:
    """Ideal tensor (harm=0, others=1)."""
    return MoralTensor.ones((9, 3))


@pytest.fixture
def worst_tensor() -> MoralTensor:
    """Worst-case tensor (harm=1, others=0)."""
    return MoralTensor.zeros((9, 3))
