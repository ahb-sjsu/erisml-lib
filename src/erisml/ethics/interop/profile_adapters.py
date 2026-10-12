# src/erisml/ethics/interop/profile_adapters.py
"""
Profile adapters for building EMs and governance configs from profiles.

Supports both V03 (legacy) and V04 (DEME 2.0) profiles.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, List, Tuple

from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    OverrideMode,
    BaseEMEnforcementMode,
)

# V2 imports
from erisml.ethics.profile_v04 import DEMEProfileV04, deme_profile_v04_to_dict
from erisml.ethics.governance.config_v2 import GovernanceConfigV2
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.layers.reflex import ReflexLayer, ReflexLayerConfig
from erisml.ethics.layers.tactical import TacticalLayerConfig
from erisml.ethics.layers.strategic import StrategicLayerConfig
from erisml.ethics.modules.base import EthicsModuleV2
from erisml.ethics.modules.registry import EMRegistry

# Note: We import these assuming they exist in your project structure.
# If these imports fail, the type: ignore handles the linter, but the file paths must be correct.
from erisml.ethics.modules.triage_em import CaseStudy1TriageEM, RightsFirstEM  # type: ignore
from erisml.ethics.governance.config import GovernanceConfig  # type: ignore

log = logging.getLogger(__name__)


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
    Build a GovernanceConfigV2 from a DEMEProfileV04: its dimension weights, tier
    configuration, lexical layers, and its base EMs as explicit veto EMs
    (``DEMEProfileV04.to_governance_config``). Before, only the dimension weights were
    carried over.
    """
    return profile.to_governance_config()


def profile_hash(profile: DEMEProfileV04) -> str:
    """SHA-256 of the profile's canonical JSON, recorded in every DecisionProof."""
    canonical = json.dumps(
        deme_profile_v04_to_dict(profile), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _profile_ems(profile: DEMEProfileV04) -> List[EthicsModuleV2]:
    """The EMs a profile names: its base EMs, which cannot be disabled, then its active EMs.

    A name the registry does not hold, or an EM that fails to build, is an error: a profile
    that names a module and runs without it would decide under a different lens than the
    one its proof records. A profile that names no active EMs runs every registered EM in
    the tiers it enables, as before, skipping (and logging) those that fail to build."""
    # register the tiered EMs
    import erisml.ethics.modules.tier0  # noqa: F401
    import erisml.ethics.modules.tier2  # noqa: F401

    ems: List[EthicsModuleV2] = []
    seen = set()
    named = list(
        dict.fromkeys(list(profile.base_em_ids) + list(profile.active_em_names))
    )
    for name in named:
        entry = EMRegistry.resolve(name)
        if entry is None:
            raise ValueError(
                f"profile {profile.name!r} names EM {name!r}, not registered"
            )
        if entry.em_class in seen:
            continue
        seen.add(entry.em_class)
        ems.append(entry.em_class())
    if profile.active_em_names:
        return ems

    for em_id, em_info in EMRegistry.list_all().items():
        tier_config = profile.tier_configs.get(em_info.get("tier", 3))
        em_cls = EMRegistry.get_class(em_id)
        if em_cls is None or em_cls in seen:
            continue
        if tier_config and not tier_config.enabled:
            continue
        try:
            ems.append(em_cls())
            seen.add(em_cls)
        except Exception as e:
            log.warning("EM %s failed to build and is skipped: %s", em_id, e)
    return ems


def pipeline_from_profile(profile: DEMEProfileV04) -> DEMEPipeline:
    """
    Build a DEMEPipeline from a DEMEProfileV04, with the profile's governance executed.

    The layers follow the profile's layer configuration. The EMs are the profile's base and
    active EMs (``_profile_ems``). Aggregation, vetoes and selection follow the profile's
    governance (``PipelineConfig.governance``), and every proof records the profile's name
    and hash.
    """
    layer_cfg = profile.layer_config
    governance = governance_v2_from_profile(profile)

    # an explicit reflex config is used as given, so it carries the default hard-constraint
    # rules here (before, a profile's pipeline ran no reflex rules at all)
    reflex_config = ReflexLayerConfig(
        enabled=layer_cfg.reflex_enabled,
        timeout_us=layer_cfg.reflex_timeout_us,
        veto_rules=list(ReflexLayer().config.veto_rules),
    )
    # tier weights, veto rights and enabled tiers come from governance (DEMEPipeline)
    tactical_config = TacticalLayerConfig(enabled=layer_cfg.tactical_enabled)
    strategic_config = StrategicLayerConfig(
        enabled=layer_cfg.strategic_enabled,
    )

    pipeline_config = PipelineConfig(
        reflex_config=reflex_config,
        tactical_config=tactical_config,
        strategic_config=strategic_config,
        generate_proofs=governance.require_decision_proof,
        profile_name=profile.name,
        profile_hash=profile_hash(profile),
        governance=governance,
    )
    return DEMEPipeline(ems=_profile_ems(profile), config=pipeline_config)


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
