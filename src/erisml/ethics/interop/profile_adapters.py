# src/erisml/ethics/interop/profile_adapters.py
"""
Profile adapters for building EMs and governance configs from profiles.

Supports both V03 (legacy) and V04 (DEME 2.0) profiles.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from typing import Dict, Tuple

from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    OverrideMode,
    BaseEMEnforcementMode,
)

# V2 imports
from erisml.ethics.profile_v04 import DEMEProfileV04
from erisml.ethics.governance.config_v2 import GovernanceConfigV2
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.layers.reflex import ReflexLayer, ReflexLayerConfig
from erisml.ethics.layers.tactical import TacticalLayer, TacticalLayerConfig
from erisml.ethics.modules.registry import EMRegistry

# Note: We import these assuming they exist in your project structure.
# If these imports fail, the type: ignore handles the linter, but the file paths must be correct.
from erisml.ethics.modules.triage_em import CaseStudy1TriageEM, RightsFirstEM  # type: ignore
from erisml.ethics.governance.config import GovernanceConfig  # type: ignore


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
    # Propagate foundational / base EMs into governance config
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
    )  # type: ignore


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


# ============================================================================
# DEME 2.0 Profile Adapters
# ============================================================================


def governance_v2_from_profile(profile: DEMEProfileV04) -> GovernanceConfigV2:
    """
    Build a GovernanceConfigV2 from a DEMEProfileV04.

    Uses the MoralVector dimension weights from the profile.
    """
    return GovernanceConfigV2(
        dimension_weights=profile.moral_dimension_weights,
    )


def pipeline_from_profile(profile: DEMEProfileV04) -> DEMEPipeline:
    """
    Build a DEMEPipeline from a DEMEProfileV04.

    Configures all three layers based on profile settings.
    """
    # Build pipeline config from profile layer settings
    pipeline_config = PipelineConfig(
        reflex_enabled=profile.layer_config.get("reflex_enabled", True),
        tactical_enabled=profile.layer_config.get("tactical_enabled", True),
        strategic_enabled=profile.layer_config.get("strategic_enabled", False),
    )

    # Build reflex layer
    reflex_config = ReflexLayerConfig(
        enabled=pipeline_config.reflex_enabled,
    )
    reflex_layer = ReflexLayer(config=reflex_config)

    # Build tactical layer with tier weights from profile
    tier_weights: Dict[int, float] = {}
    tier_veto_enabled: Dict[int, bool] = {}

    for tier_num, tier_cfg in profile.tier_configs.items():
        tier_weights[tier_num] = tier_cfg.weight
        tier_veto_enabled[tier_num] = tier_cfg.veto_enabled

    tactical_config = TacticalLayerConfig(
        enabled=pipeline_config.tactical_enabled,
        tier_weights=tier_weights,
        tier_veto_enabled=tier_veto_enabled,
    )
    tactical_layer = TacticalLayer(config=tactical_config)

    # Build EMs from registry based on tier config
    for em_id, em_info in EMRegistry.list_all().items():
        tier = em_info.get("tier", 3)
        tier_config = profile.tier_configs.get(tier)

        if tier_config and not tier_config.enabled:
            continue

        em_cls = EMRegistry.get(em_id)
        if em_cls is not None:
            try:
                em = em_cls()
                tactical_layer.add_em(em)
            except Exception:
                pass  # Skip EMs that fail to instantiate

    return DEMEPipeline(
        config=pipeline_config,
        reflex_layer=reflex_layer,
        tactical_layer=tactical_layer,
    )


def build_v2_from_profile(
    profile: DEMEProfileV04,
) -> Tuple[DEMEPipeline, GovernanceConfigV2]:
    """
    Convenience helper: given a DEMEProfileV04, build:

      - configured DEMEPipeline (three-layer architecture)
      - GovernanceConfigV2 (MoralVector aggregation settings)
    """
    pipeline = pipeline_from_profile(profile)
    gov_cfg = governance_v2_from_profile(profile)
    return pipeline, gov_cfg
