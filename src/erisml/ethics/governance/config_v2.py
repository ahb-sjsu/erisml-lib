# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Governance Configuration V2: MoralVector-aware governance settings.

Extends the V1 GovernanceConfig with dimension weights, lexical
priority layers, and democratic stakeholder aggregation.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AggregationStrategy(str, Enum):
    """Strategies for aggregating stakeholder preferences."""

    WEIGHTED_MEAN = "weighted_mean"
    """Weighted average of dimension scores."""

    MEDIAN = "median"
    """Median across stakeholders (robust to outliers)."""

    MIN = "min"
    """Worst-case across stakeholders (conservative)."""

    MAX = "max"
    """Best-case across stakeholders (optimistic)."""


@dataclass
class DimensionWeights:
    """Per-dimension weights for MoralVector aggregation."""

    physical_harm: float = 1.0
    """Weight for physical harm dimension."""

    rights_respect: float = 1.0
    """Weight for rights respect dimension."""

    fairness_equity: float = 1.0
    """Weight for fairness/equity dimension."""

    autonomy_respect: float = 1.0
    """Weight for autonomy respect dimension."""

    legitimacy_trust: float = 1.0
    """Weight for legitimacy/trust dimension."""

    epistemic_quality: float = 0.5
    """Weight for epistemic quality dimension."""

    extension_weights: Dict[str, float] = field(default_factory=dict)
    """Weights for domain-specific extension dimensions."""

    def to_dict(self) -> Dict[str, float]:
        """Convert to flat dictionary."""
        result = {
            "physical_harm": self.physical_harm,
            "rights_respect": self.rights_respect,
            "fairness_equity": self.fairness_equity,
            "autonomy_respect": self.autonomy_respect,
            "legitimacy_trust": self.legitimacy_trust,
            "epistemic_quality": self.epistemic_quality,
        }
        result.update(self.extension_weights)
        return result


@dataclass
class LexicalLayer:
    """DAG-based lexical priority layer."""

    name: str
    """Unique name for this layer."""

    tier: int
    """Associated EM tier (0-4)."""

    priority: int
    """Priority level (higher = more important)."""

    hard_stop: bool = False
    """If True, violations at this layer cannot be overridden."""

    description: str = ""
    """Human-readable description."""


@dataclass
class TierConfig:
    """Configuration for an EM tier."""

    enabled: bool = True
    """Whether this tier is active."""

    weight_multiplier: float = 1.0
    """Weight multiplier for EMs in this tier."""

    veto_enabled: bool = True
    """Whether EMs in this tier can trigger vetoes."""


@dataclass
class GovernanceConfigV2:
    """
    DEME 2.0 governance configuration with MoralVector support.

    Extends V1 configuration with:
    - Dimension weights for MoralVector aggregation
    - Lexical priority layers
    - Tier-based configuration
    - Democratic stakeholder aggregation
    """

    # Dimension weighting
    dimension_weights: DimensionWeights = field(default_factory=DimensionWeights)
    """Per-dimension weights for scalar collapse."""

    # Tier configuration
    tier_configs: Dict[int, TierConfig] = field(
        default_factory=lambda: {
            0: TierConfig(weight_multiplier=10.0, veto_enabled=True),
            1: TierConfig(weight_multiplier=5.0, veto_enabled=True),
            2: TierConfig(weight_multiplier=2.0, veto_enabled=True),
            3: TierConfig(weight_multiplier=1.0, veto_enabled=False),
            4: TierConfig(weight_multiplier=0.5, veto_enabled=False),
        }
    )
    """Per-tier configuration."""

    # Lexical priority layers
    lexical_layers: List[LexicalLayer] = field(default_factory=list)
    """DAG-based priority layers for conflict resolution."""

    # Stakeholder aggregation
    stakeholder_weights: Dict[str, float] = field(default_factory=dict)
    """Weights per stakeholder for aggregation."""

    stakeholder_aggregation: AggregationStrategy = AggregationStrategy.WEIGHTED_MEAN
    """Strategy for combining stakeholder perspectives."""

    # EM weighting
    em_weights: Dict[str, float] = field(default_factory=dict)
    """Per-EM weight overrides."""

    veto_ems: List[str] = field(default_factory=list)
    """EMs with explicit veto authority."""

    # Decision thresholds
    min_score_threshold: float = 0.0
    """Minimum score for option to be considered."""

    require_non_forbidden: bool = True
    """Require at least one non-forbidden option."""

    # Tie breaking
    tie_breaker: Optional[str] = None
    """Tie-breaking strategy: 'random', 'status_quo', 'first'."""

    # Audit
    require_decision_proof: bool = True
    """Whether to generate decision proofs."""

    def get_tier_config(self, tier: int) -> TierConfig:
        """Get configuration for a tier, with defaults."""
        return self.tier_configs.get(tier, TierConfig())

    def weight_for_em(
        self,
        em_name: str,
        em_tier: int,
        stakeholder: Optional[str] = None,
    ) -> float:
        """
        Compute effective weight for an EM.

        Combines tier weight, EM override, and stakeholder weight.
        """
        # Base tier weight
        tier_config = self.get_tier_config(em_tier)
        weight = tier_config.weight_multiplier

        # EM-specific override
        if em_name in self.em_weights:
            weight *= self.em_weights[em_name]

        # Stakeholder weight
        if stakeholder and stakeholder in self.stakeholder_weights:
            weight *= self.stakeholder_weights[stakeholder]

        return weight

    def can_veto(self, em_name: str, em_tier: int) -> bool:
        """Check if an EM can trigger vetoes."""
        # Explicit veto list
        if em_name in self.veto_ems:
            return True

        # Tier-based veto
        tier_config = self.get_tier_config(em_tier)
        return tier_config.veto_enabled


__all__ = [
    "AggregationStrategy",
    "DimensionWeights",
    "LexicalLayer",
    "TierConfig",
    "GovernanceConfigV2",
]
