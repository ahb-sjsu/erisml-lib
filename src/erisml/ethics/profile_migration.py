# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Profile Migration: V03 to V04 conversion utilities.

Provides migration functions for upgrading profiles from the V03
schema to the V04 (DEME 2.0) schema.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from typing import Dict, List

from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    LexicalLayer as LexicalLayerV03,
)
from erisml.ethics.profile_v04 import (
    DEMEProfileV04,
    EMTierConfig,
    LayerConfiguration,
)
from erisml.ethics.governance.config_v2 import (
    DimensionWeights,
    LexicalLayer as LexicalLayerV2,
)


def migrate_v03_to_v04(profile_v03: DEMEProfileV03) -> DEMEProfileV04:
    """
    Migrate a V03 profile to V04 format.

    This maps V03 fields to their V04 equivalents:
    - deme_dimensions → moral_dimension_weights
    - lexical_layers (V03) → lexical_priorities (V2 format)
    - base_em_ids → base_em_ids + tier 0 config
    - base_em_enforcement → tier config veto settings

    Args:
        profile_v03: The V03 profile to migrate.

    Returns:
        Equivalent DEMEProfileV04.
    """
    # Map DEME dimensions to MoralVector dimension weights
    dd = profile_v03.deme_dimensions
    moral_weights = DimensionWeights(
        physical_harm=dd.safety,
        rights_respect=dd.rule_following_legality,
        fairness_equity=dd.fairness_equity,
        autonomy_respect=dd.autonomy_respect,
        legitimacy_trust=dd.trust_relationships,
        epistemic_quality=0.5,  # New dimension, default value
        extension_weights={
            "privacy_level": dd.privacy_confidentiality,
            "environmental_impact": dd.environment_societal,
            "priority_for_vulnerable": dd.priority_for_vulnerable,
        },
    )

    # Convert lexical layers to V2 format
    lexical_priorities = _convert_lexical_layers(profile_v03.lexical_layers)

    # Configure tier 0 based on base_em_enforcement
    from erisml.ethics.profile_v03 import BaseEMEnforcementMode

    tier_0_veto = profile_v03.base_em_enforcement == BaseEMEnforcementMode.HARD_VETO

    tier_configs: Dict[int, EMTierConfig] = {
        0: EMTierConfig(
            enabled=True,
            weight_multiplier=10.0,
            veto_enabled=tier_0_veto,
        ),
        1: EMTierConfig(
            enabled=True,
            weight_multiplier=5.0,
            veto_enabled=True,
        ),
        2: EMTierConfig(
            enabled=True,
            weight_multiplier=2.0,
            veto_enabled=True,
        ),
        3: EMTierConfig(
            enabled=True,
            weight_multiplier=1.0,
            veto_enabled=False,
        ),
        4: EMTierConfig(
            enabled=True,
            weight_multiplier=0.5,
            veto_enabled=False,
        ),
    }

    # Map base EM IDs - add default constitutional EM if empty
    base_em_ids = profile_v03.base_em_ids.copy()
    if not base_em_ids:
        base_em_ids = ["geneva_constitutional"]

    return DEMEProfileV04(
        # Identity
        name=profile_v03.name,
        description=profile_v03.description,
        stakeholder_label=profile_v03.stakeholder_label,
        domain=profile_v03.domain,
        version="0.4.0",
        schema_version="DEMEProfileV04-0.1",
        # Inherited weights
        principlism=profile_v03.principlism,
        trustworthiness=profile_v03.trustworthiness,
        # Risk and override
        risk_attitude=profile_v03.risk_attitude,
        override_mode=profile_v03.override_mode,
        # Constraints
        hard_vetoes=profile_v03.hard_vetoes,
        pattern_constraints=profile_v03.pattern_constraints.copy(),
        governance_expectations=profile_v03.governance_expectations,
        override_graph=profile_v03.override_graph.copy(),
        # V04 new fields
        moral_dimension_weights=moral_weights,
        tier_configs=tier_configs,
        lexical_priorities=lexical_priorities,
        active_em_names=[],  # Will be populated by registry
        base_em_ids=base_em_ids,
        base_em_enforcement=profile_v03.base_em_enforcement,
        layer_config=LayerConfiguration(),  # Defaults
        tags=profile_v03.tags.copy(),
        notes=profile_v03.notes + "\n[Migrated from V03]",
    )


def _convert_lexical_layers(
    v03_layers: List[LexicalLayerV03],
) -> List[LexicalLayerV2]:
    """
    Convert V03 lexical layers to V2 format.

    V03 layers have:
    - name: str
    - principles: List[str]
    - hard_stop: bool
    - context_condition: Optional[str]

    V2 layers have:
    - name: str
    - tier: int
    - priority: int
    - hard_stop: bool
    - description: str
    """
    # Map V03 principle names to tiers
    principle_to_tier = {
        "rights": 0,
        "safety": 1,
        "welfare": 2,
        "autonomy": 2,
        "justice": 2,
        "fairness": 2,
        "utility": 3,
        "beneficence": 3,
    }

    result: List[LexicalLayerV2] = []
    priority = 100  # Start high, decrement

    for v03_layer in v03_layers:
        # Infer tier from principles
        tier = 2  # Default
        for principle in v03_layer.principles:
            if principle.lower() in principle_to_tier:
                tier = min(tier, principle_to_tier[principle.lower()])

        result.append(
            LexicalLayerV2(
                name=v03_layer.name,
                tier=tier,
                priority=priority,
                hard_stop=v03_layer.hard_stop,
                description=f"Migrated from V03: {', '.join(v03_layer.principles)}",
            )
        )
        priority -= 10

    return result


def migrate_profile_dict_v03_to_v04(data: Dict) -> Dict:
    """
    Migrate a V03 profile dict to V04 format.

    Useful for JSON-based profile storage.

    Args:
        data: V03 profile as dict.

    Returns:
        V04 profile as dict.
    """
    from erisml.ethics.profile_v03 import deme_profile_v03_from_dict
    from erisml.ethics.profile_v04 import deme_profile_v04_to_dict

    v03 = deme_profile_v03_from_dict(data)
    v04 = migrate_v03_to_v04(v03)
    return deme_profile_v04_to_dict(v04)


__all__ = [
    "migrate_v03_to_v04",
    "migrate_profile_dict_v03_to_v04",
]
