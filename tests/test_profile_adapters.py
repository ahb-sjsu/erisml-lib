"""
Tests for DEMEProfileV03 → EM / Governance adapters.

Covers:
- triage_em_from_profile
- governance_from_profile
- build_triage_ems_and_governance
"""

from __future__ import annotations

from typing import List

import pytest

from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    OverrideMode,
    BaseEMEnforcementMode,
    PrinciplismWeights,
    DEMEDimensionWeights,
)
from erisml.ethics.interop.profile_adapters import (
    triage_em_from_profile,
    governance_from_profile,
    build_triage_ems_and_governance,
)
from erisml.ethics.modules.triage_em import CaseStudy1TriageEM, RightsFirstEM
from erisml.ethics.governance.config import GovernanceConfig


@pytest.fixture
def sample_profile() -> DEMEProfileV03:
    """Return a basic DEMEProfileV03 for testing."""
    return DEMEProfileV03(
        name="Test Profile",
        description="Profile for testing",
        stakeholder_label="test_stakeholder",
        principlism=PrinciplismWeights(
            beneficence=0.4,
            non_maleficence=0.3,
            autonomy=0.2,
            justice=0.1,
        ),
        deme_dimensions=DEMEDimensionWeights(
            safety=0.8,
            priority_for_vulnerable=0.6,
            rule_following_legality=0.5,
        ),
        override_mode=OverrideMode.BALANCED_CASE_BY_CASE,
        base_em_ids=["geneva_em_1", "geneva_em_2"],
        base_em_enforcement=BaseEMEnforcementMode.HARD_VETO,
    )


# ---------------------------------------------------------------------------
# triage_em_from_profile
# ---------------------------------------------------------------------------


def test_triage_em_weights_sum_to_1(sample_profile: DEMEProfileV03) -> None:
    """Weights produced by triage_em_from_profile sum to 1.0."""
    em = triage_em_from_profile(sample_profile)
    total = (
        em.w_benefit + em.w_harm + em.w_urgency + em.w_disadvantaged + em.w_procedural
    )
    assert abs(total - 1.0) < 1e-6


def test_triage_em_respects_principlism(sample_profile: DEMEProfileV03) -> None:
    """Changing principlism alters weights in predictable way."""
    profile = sample_profile
    profile.principlism.beneficence = 1.0
    profile.principlism.non_maleficence = 0.0
    em = triage_em_from_profile(profile)
    # Expect benefit weight to dominate
    assert em.w_benefit > em.w_harm
    assert em.w_benefit > em.w_disadvantaged


# ---------------------------------------------------------------------------
# governance_from_profile
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "override_mode, expected_veto_em",
    [
        (OverrideMode.RIGHTS_FIRST, ["rights_first_compliance"]),
        (OverrideMode.CONSEQUENCES_FIRST, []),
        (OverrideMode.BALANCED_CASE_BY_CASE, []),
    ],
)
def test_governance_override_modes(
    sample_profile: DEMEProfileV03,
    override_mode: OverrideMode,
    expected_veto_em: List[str],
) -> None:
    """OverrideMode affects veto EMs as expected."""
    profile = sample_profile
    profile.override_mode = override_mode
    gov = governance_from_profile(profile)
    # Base EMs are added due to HARD_VETO
    expected_veto = sorted(set(expected_veto_em) | set(profile.base_em_ids))
    assert sorted(gov.veto_ems) == expected_veto
    # EM weights sum to 1.0
    total = sum(gov.em_weights.values())
    assert abs(total - 1.0) < 1e-6


def test_governance_base_em_hard_veto(sample_profile: DEMEProfileV03) -> None:
    """Base EMs with HARD_VETO are added to veto_ems."""
    profile = sample_profile
    profile.base_em_enforcement = BaseEMEnforcementMode.HARD_VETO
    gov = governance_from_profile(profile)
    for base_id in profile.base_em_ids:
        assert base_id in gov.veto_ems


def test_governance_base_em_advisory(sample_profile: DEMEProfileV03) -> None:
    """Base EMs with ADVISORY enforcement are NOT added to veto_ems."""
    profile = sample_profile
    profile.base_em_enforcement = BaseEMEnforcementMode.ADVISORY
    gov = governance_from_profile(profile)
    for base_id in profile.base_em_ids:
        assert base_id not in gov.veto_ems


# ---------------------------------------------------------------------------
# build_triage_ems_and_governance
# ---------------------------------------------------------------------------


def test_build_triage_ems_and_governance_types(sample_profile: DEMEProfileV03) -> None:
    """Check returned objects are of expected types."""
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(sample_profile)
    assert isinstance(triage_em, CaseStudy1TriageEM)
    assert isinstance(rights_em, RightsFirstEM)
    assert isinstance(gov_cfg, GovernanceConfig)


def test_build_triage_ems_and_governance_weights(
    sample_profile: DEMEProfileV03,
) -> None:
    """Check governance EM weights and vetoes are correct."""
    _, _, gov = build_triage_ems_and_governance(sample_profile)
    # EM weights sum to 1
    total = sum(gov.em_weights.values())
    assert abs(total - 1.0) < 1e-6
    # Base EMs included in veto if HARD_VETO
    for base_id in sample_profile.base_em_ids:
        assert base_id in gov.veto_ems
