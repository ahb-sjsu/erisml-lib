# src/erisml/ethics/interop/profile_adapters.py

from __future__ import annotations

from typing import Dict, Tuple

from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    OverrideMode,
    BaseEMEnforcementMode,
)
from erisml.ethics.modules.triage_em import CaseStudy1TriageEM, RightsFirstEM
from erisml.ethics.governance.config import GovernanceConfig


def triage_em_from_profile(profile: DEMEProfileV03) -> CaseStudy1TriageEM:
    """
    Construct a CaseStudy1TriageEM using weights derived from a DEMEProfileV03.

    Rough mapping:
      - safety & non-maleficence -> higher weight on harm & urgency
      - beneficence -> higher weight on benefit
      - fairness + vulnerable_priority -> disadvantaged weight
      - rule_following_legality -> procedural weight
    """
    dims = profile.deme_dimensions
    prin = profile.principlism

    w_benefit = 0.3 + 0.4 * prin.beneficence
    w_harm = 0.3 + 0.4 * prin.non_maleficence
    w_urgency = 0.2 + 0.4 * dims.safety
    w_disadvantaged = 0.1 + 0.7 * dims.priority_for_vulnerable
    w_procedural = 0.1 + 0.7 * dims.rule_following_legality

    total = w_benefit + w_harm + w_urgency + w_disadvantaged + w_procedural or 1.0
    w_benefit /= total
    w_harm /= total
    w_urgency /= total
    w_disadvantaged /= total
    w_procedural /= total

    return CaseStudy1TriageEM(
        w_benefit=w_benefit,
        w_harm=w_harm,
        w_urgency=w_urgency,
        w_disadvantaged=w_disadvantaged,
        w_procedural=w_procedural,
    )


def governance_from_profile(profile: DEMEProfileV03) -> GovernanceConfig:
    """
    Build a GovernanceConfig for the triage demo based on DEMEProfileV03.

    Assume two EMs:
      - 'case_study_1_triage'
      - 'rights_first_compliance'

    Principlism + override_mode determine weights and veto structure.

    Additionally, propagate any foundational / base EMs specified in the
    profile (e.g., a 'Geneva convention' EM) into the GovernanceConfig,
    so the aggregation layer can enforce their semantics.
    """
    prin = profile.principlism

    # Relative influence of the two demo EMs
    w_triage = prin.beneficence + prin.justice
    w_rights = prin.autonomy + prin.non_maleficence

    if profile.override_mode == OverrideMode.RIGHTS_FIRST:
        w_rights *= 1.5
    elif profile.override_mode == OverrideMode.CONSEQUENCES_FIRST:
        w_triage *= 1.5

    total = w_triage + w_rights or 1.0
    w_triage /= total
    w_rights /= total

    em_weights: Dict[str, float] = {
        "case_study_1_triage": w_triage,
        "rights_first_compliance": w_rights,
    }

    veto_ems = []
    if profile.override_mode == OverrideMode.RIGHTS_FIRST:
        veto_ems = ["rights_first_compliance"]

    # ------------------------------------------------------------------
    # NEW: propagate foundational / base EMs into governance config
    # ------------------------------------------------------------------
    base_em_ids = list(profile.base_em_ids or [])

    # If base EMs are enforced via HARD_VETO, they should always have
    # effective veto power as well.
    if profile.base_em_enforcement == BaseEMEnforcementMode.HARD_VETO:
        veto_ems = sorted(set(veto_ems) | set(base_em_ids))

    return GovernanceConfig(
        stakeholder_weights={},
        em_weights=em_weights,
        veto_ems=veto_ems,
        min_score_threshold=0.0,
        require_non_forbidden=True,
        base_em_ids=base_em_ids,
        base_em_enforcement=profile.base_em_enforcement,
    )


def build_triage_ems_and_governance(
    profile: DEMEProfileV03,
) -> Tuple[CaseStudy1TriageEM, RightsFirstEM, GovernanceConfig]:
    """
    Convenience helper: given a DEMEProfileV03, build:

      - configured CaseStudy1TriageEM
      - default RightsFirstEM
      - GovernanceConfig (including base EM semantics, if any)
    """
    triage_em = triage_em_from_profile(profile)
    rights_em = RightsFirstEM()
    gov_cfg = governance_from_profile(profile)
    return triage_em, rights_em, gov_cfg
