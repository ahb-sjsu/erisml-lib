# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEMEProfileV04: DEME 2.0 profile schema with MoralVector and EM tiers.

Extends V03 with:
- MoralVector dimension weights
- EM tier configuration
- Lexical priority layers (V2 format)
- Active EM specification
- Layer configuration (reflex/tactical/strategic)

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from erisml.ethics.profile_v03 import (
    BaseEMEnforcementMode,
    DimensionRiskTolerance,
    GovernanceExpectations,
    HardVetoes,
    OverrideEdge,
    OverrideMode,
    PatternConstraint,
    PatternConstraintKind,
    PrinciplismWeights,
    RiskAppetite,
    RiskAttitudeProfile,
    TrustworthinessWeights,
)
from erisml.ethics.governance.config_v2 import (
    DimensionWeights,
    LexicalLayer as LexicalLayerV2,
)


@dataclass
class EMTierConfig:
    """Per-tier configuration for EM behavior."""

    enabled: bool = True
    """Whether EMs in this tier are active."""

    weight_multiplier: float = 1.0
    """Weight multiplier for EMs in this tier."""

    veto_enabled: bool = True
    """Whether EMs in this tier can trigger vetoes."""


@dataclass
class LayerConfiguration:
    """Configuration for the three-layer architecture."""

    reflex_enabled: bool = True
    """Whether reflex layer is active."""

    reflex_timeout_us: int = 100
    """Target timeout for reflex layer in microseconds."""

    tactical_enabled: bool = True
    """Whether tactical layer is active."""

    tactical_timeout_ms: int = 100
    """Target timeout for tactical layer in milliseconds."""

    strategic_enabled: bool = False
    """Whether strategic layer is active (default off for MVP)."""


@dataclass
class DEMEProfileV04:
    """
    DEME Profile Schema 0.4 (V04) - DEME 2.0 format.

    Extends V03 with MoralVector dimension weights, EM tiers,
    and three-layer architecture configuration.
    """

    # Identity & context
    name: str
    description: str
    stakeholder_label: str
    domain: Optional[str] = None

    version: str = "0.4.0"
    schema_version: str = "DEMEProfileV04-0.1"

    # === V03 inherited fields ===

    # Ethically significant weightings
    principlism: PrinciplismWeights = field(default_factory=PrinciplismWeights)
    trustworthiness: TrustworthinessWeights = field(
        default_factory=TrustworthinessWeights
    )

    # Risk posture & summary override mode
    risk_attitude: RiskAttitudeProfile = field(default_factory=RiskAttitudeProfile)
    override_mode: OverrideMode = OverrideMode.BALANCED_CASE_BY_CASE

    # Constraints & governance expectations
    hard_vetoes: HardVetoes = field(default_factory=HardVetoes)
    pattern_constraints: List[PatternConstraint] = field(default_factory=list)
    governance_expectations: GovernanceExpectations = field(
        default_factory=GovernanceExpectations
    )

    # Override DAG (V03 format, still supported)
    override_graph: List[OverrideEdge] = field(default_factory=list)

    # === V04 NEW FIELDS ===

    # MoralVector dimension weights (replaces deme_dimensions)
    moral_dimension_weights: DimensionWeights = field(default_factory=DimensionWeights)
    """Weights for MoralVector scalar collapse."""

    # EM tier configuration
    tier_configs: Dict[int, EMTierConfig] = field(
        default_factory=lambda: {
            0: EMTierConfig(weight_multiplier=10.0, veto_enabled=True),
            1: EMTierConfig(weight_multiplier=5.0, veto_enabled=True),
            2: EMTierConfig(weight_multiplier=2.0, veto_enabled=True),
            3: EMTierConfig(weight_multiplier=1.0, veto_enabled=False),
            4: EMTierConfig(weight_multiplier=0.5, veto_enabled=False),
        }
    )
    """Per-tier configuration."""

    # Lexical priority layers (V2 format)
    lexical_priorities: List[LexicalLayerV2] = field(default_factory=list)
    """DAG-based priority layers for conflict resolution."""

    # Active EM specification
    active_em_names: List[str] = field(default_factory=list)
    """List of EM names to activate for this profile."""

    # Base EMs (constitutional tier)
    base_em_ids: List[str] = field(default_factory=lambda: ["geneva_constitutional"])
    """Constitutional EMs that cannot be disabled."""

    base_em_enforcement: BaseEMEnforcementMode = BaseEMEnforcementMode.HARD_VETO
    """How base EMs are enforced."""

    # Layer configuration
    layer_config: LayerConfiguration = field(default_factory=LayerConfiguration)
    """Three-layer architecture configuration."""

    # Misc
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def get_tier_config(self, tier: int) -> EMTierConfig:
        """Get configuration for a tier, with defaults."""
        return self.tier_configs.get(tier, EMTierConfig())

    def to_governance_config(self):
        """Convert to GovernanceConfigV2."""
        from erisml.ethics.governance.config_v2 import (
            GovernanceConfigV2,
            TierConfig as GovTierConfig,
        )

        # Convert tier configs
        gov_tiers = {
            tier: GovTierConfig(
                enabled=tc.enabled,
                weight_multiplier=tc.weight_multiplier,
                veto_enabled=tc.veto_enabled,
            )
            for tier, tc in self.tier_configs.items()
        }

        return GovernanceConfigV2(
            dimension_weights=self.moral_dimension_weights,
            tier_configs=gov_tiers,
            lexical_layers=self.lexical_priorities,
            veto_ems=self.base_em_ids,
            require_decision_proof=True,
        )


def deme_profile_v04_to_dict(profile: DEMEProfileV04) -> Dict[str, Any]:
    """Convert a DEMEProfileV04 to a JSON-safe dict."""
    data = asdict(profile)

    # Enums → string values
    data["risk_attitude"]["appetite"] = profile.risk_attitude.appetite.value
    data["override_mode"] = profile.override_mode.value
    data["base_em_enforcement"] = profile.base_em_enforcement.value

    # Pattern constraints
    for pc, orig_pc in zip(
        data.get("pattern_constraints", []), profile.pattern_constraints
    ):
        pc["kind"] = orig_pc.kind.value

    return data


def deme_profile_v04_from_dict(data: Dict[str, Any]) -> DEMEProfileV04:
    """Reconstruct a DEMEProfileV04 from a dict."""
    # Parse risk attitude
    ra = data.get("risk_attitude", {})
    tolerances = ra.get("tolerances", {})
    risk_attitude = RiskAttitudeProfile(
        appetite=RiskAppetite(ra.get("appetite", "balanced")),
        max_overall_risk=ra.get("max_overall_risk", 0.3),
        tolerances=DimensionRiskTolerance(**tolerances),
        escalate_near_threshold=ra.get("escalate_near_threshold", True),
        escalation_margin=ra.get("escalation_margin", 0.05),
    )

    # Parse pattern constraints
    pattern_constraints = [
        PatternConstraint(
            name=pc["name"],
            kind=PatternConstraintKind(pc["kind"]),
            expression=pc["expression"],
            rationale=pc["rationale"],
        )
        for pc in data.get("pattern_constraints", [])
    ]

    # Parse override graph
    override_graph = [OverrideEdge(**og) for og in data.get("override_graph", [])]

    # Parse moral dimension weights
    mdw_data = data.get("moral_dimension_weights", {})
    moral_dimension_weights = DimensionWeights(
        physical_harm=mdw_data.get("physical_harm", 1.0),
        rights_respect=mdw_data.get("rights_respect", 1.0),
        fairness_equity=mdw_data.get("fairness_equity", 1.0),
        autonomy_respect=mdw_data.get("autonomy_respect", 1.0),
        legitimacy_trust=mdw_data.get("legitimacy_trust", 1.0),
        epistemic_quality=mdw_data.get("epistemic_quality", 0.5),
        extension_weights=mdw_data.get("extension_weights", {}),
    )

    # Parse tier configs
    tier_configs = {
        int(k): EMTierConfig(**v) for k, v in data.get("tier_configs", {}).items()
    }

    # Parse lexical priorities
    lexical_priorities = [
        LexicalLayerV2(**lp) for lp in data.get("lexical_priorities", [])
    ]

    # Parse layer config
    lc_data = data.get("layer_config", {})
    layer_config = LayerConfiguration(**lc_data) if lc_data else LayerConfiguration()

    return DEMEProfileV04(
        name=data["name"],
        description=data.get("description", ""),
        stakeholder_label=data.get("stakeholder_label", "unspecified"),
        domain=data.get("domain"),
        version=data.get("version", "0.4.0"),
        schema_version=data.get("schema_version", "DEMEProfileV04-0.1"),
        principlism=PrinciplismWeights(**data.get("principlism", {})),
        trustworthiness=TrustworthinessWeights(**data.get("trustworthiness", {})),
        risk_attitude=risk_attitude,
        override_mode=OverrideMode(data.get("override_mode", "balanced_case_by_case")),
        hard_vetoes=HardVetoes(**data.get("hard_vetoes", {})),
        pattern_constraints=pattern_constraints,
        governance_expectations=GovernanceExpectations(
            **data.get("governance_expectations", {})
        ),
        override_graph=override_graph,
        moral_dimension_weights=moral_dimension_weights,
        tier_configs=tier_configs,
        lexical_priorities=lexical_priorities,
        active_em_names=data.get("active_em_names", []),
        base_em_ids=data.get("base_em_ids", ["geneva_constitutional"]),
        base_em_enforcement=BaseEMEnforcementMode(
            data.get("base_em_enforcement", "hard_veto")
        ),
        layer_config=layer_config,
        tags=data.get("tags", []),
        notes=data.get("notes", ""),
    )


__all__ = [
    "EMTierConfig",
    "LayerConfiguration",
    "DEMEProfileV04",
    "deme_profile_v04_to_dict",
    "deme_profile_v04_from_dict",
]
