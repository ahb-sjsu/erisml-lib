# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tactical Layer: Full MoralVector reasoning (10-100ms target).

The tactical layer runs all active EMs and aggregates their MoralVector
outputs according to governance configuration.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.facts import EthicalFacts
    from erisml.ethics.modules.base import EthicsModuleV2

from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.moral_landscape import MoralLandscape
from erisml.ethics.judgement import EthicalJudgementV2


@dataclass
class TacticalLayerConfig:
    """Configuration for the tactical layer."""

    enabled: bool = True
    """Whether tactical layer is active."""

    timeout_ms: int = 100
    """Target timeout in milliseconds."""

    parallel_ems: bool = False
    """Whether to run EMs in parallel (requires threading)."""

    # Tier configuration
    tier_weights: Dict[int, float] = field(
        default_factory=lambda: {
            0: 10.0,  # Constitutional
            1: 5.0,  # Core Safety
            2: 2.0,  # Rights/Fairness
            3: 1.0,  # Soft Values
            4: 0.5,  # Meta-Governance
        }
    )
    """Weight multipliers per tier."""

    tier_veto_enabled: Dict[int, bool] = field(
        default_factory=lambda: {
            0: True,  # Constitutional always can veto
            1: True,  # Core Safety can veto
            2: True,  # Rights/Fairness can veto
            3: False,  # Soft Values advisory only
            4: False,  # Meta-Governance advisory only
        }
    )
    """Whether each tier can trigger vetoes."""


@dataclass
class TacticalResult:
    """Result from tactical layer evaluation."""

    option_id: str
    """Option that was evaluated."""

    judgements: List[EthicalJudgementV2]
    """Individual EM judgements."""

    aggregated_vector: MoralVector
    """Aggregated moral vector across all EMs."""

    vetoed: bool
    """Whether option was vetoed by any EM."""

    veto_reasons: List[str]
    """List of veto reasons if vetoed."""

    latency_ms: float
    """Execution latency in milliseconds."""


class TacticalLayer:
    """
    Full MoralVector reasoning layer.

    Runs all active EMs, collects their judgements, and aggregates
    the results according to governance configuration.
    """

    def __init__(
        self,
        ems: Optional[List[EthicsModuleV2]] = None,
        config: Optional[TacticalLayerConfig] = None,
    ) -> None:
        """
        Initialize the tactical layer.

        Args:
            ems: List of V2 ethics modules to run.
            config: Layer configuration.
        """
        self.ems: List[EthicsModuleV2] = ems or []
        self.config = config or TacticalLayerConfig()

    def add_em(self, em: EthicsModuleV2) -> None:
        """Add an ethics module."""
        self.ems.append(em)

    def remove_em(self, em_name: str) -> bool:
        """
        Remove an EM by name.

        Returns:
            True if EM was found and removed.
        """
        original_len = len(self.ems)
        self.ems = [em for em in self.ems if em.em_name != em_name]
        return len(self.ems) < original_len

    def evaluate(self, facts: EthicalFacts) -> TacticalResult:
        """
        Evaluate a single option through all EMs.

        Args:
            facts: The EthicalFacts to evaluate.

        Returns:
            TacticalResult with aggregated assessment.
        """
        if not self.config.enabled:
            return TacticalResult(
                option_id=facts.option_id,
                judgements=[],
                aggregated_vector=MoralVector.from_ethical_facts(facts),
                vetoed=False,
                veto_reasons=[],
                latency_ms=0.0,
            )

        start_time = time.perf_counter()

        # Collect judgements from all EMs
        judgements: List[EthicalJudgementV2] = []
        veto_reasons: List[str] = []
        vetoed = False

        for em in self.ems:
            try:
                judgement = em.judge(facts)
                judgements.append(judgement)

                # Check for veto
                tier = em.em_tier
                if judgement.veto_triggered:
                    if self.config.tier_veto_enabled.get(tier, True):
                        vetoed = True
                        if judgement.veto_reason:
                            veto_reasons.append(
                                f"{em.em_name}: {judgement.veto_reason}"
                            )
            except Exception:
                # EM failure - log but continue with other EMs
                # In production, this would be monitored
                pass

        # Aggregate moral vectors
        aggregated_vector = self._aggregate_vectors(judgements)

        latency_ms = (time.perf_counter() - start_time) * 1000

        return TacticalResult(
            option_id=facts.option_id,
            judgements=judgements,
            aggregated_vector=aggregated_vector,
            vetoed=vetoed,
            veto_reasons=veto_reasons,
            latency_ms=latency_ms,
        )

    def evaluate_batch(
        self,
        facts_list: List[EthicalFacts],
    ) -> Tuple[List[TacticalResult], MoralLandscape]:
        """
        Evaluate multiple options and build a moral landscape.

        Args:
            facts_list: List of EthicalFacts to evaluate.

        Returns:
            Tuple of (results list, moral landscape).
        """
        results: List[TacticalResult] = []
        landscape = MoralLandscape()

        for facts in facts_list:
            result = self.evaluate(facts)
            results.append(result)
            landscape.add(facts.option_id, result.aggregated_vector)

        return results, landscape

    def _aggregate_vectors(
        self,
        judgements: List[EthicalJudgementV2],
    ) -> MoralVector:
        """Aggregate MoralVectors from multiple judgements."""
        if not judgements:
            return MoralVector()

        # Compute weighted aggregation based on tier weights
        weighted_vectors: List[Tuple[MoralVector, float]] = []
        total_weight = 0.0

        for j in judgements:
            tier_weight = self.config.tier_weights.get(j.em_tier, 1.0)
            weighted_vectors.append((j.moral_vector, tier_weight))
            total_weight += tier_weight

        if total_weight == 0:
            return MoralVector()

        # Weighted average of each dimension
        dims = MoralVector.core_dimension_names()
        result_dims: Dict[str, float] = {dim: 0.0 for dim in dims}
        all_vetoes: List[str] = []
        all_reasons: List[str] = []

        for vec, weight in weighted_vectors:
            normalized_weight = weight / total_weight
            for dim in dims:
                result_dims[dim] += normalized_weight * getattr(vec, dim)

            all_vetoes.extend(vec.veto_flags)
            all_reasons.extend(vec.reason_codes)

        # Deduplicate vetoes and reasons
        unique_vetoes = list(dict.fromkeys(all_vetoes))
        unique_reasons = list(dict.fromkeys(all_reasons))

        return MoralVector(
            physical_harm=result_dims["physical_harm"],
            rights_respect=result_dims["rights_respect"],
            fairness_equity=result_dims["fairness_equity"],
            autonomy_respect=result_dims["autonomy_respect"],
            legitimacy_trust=result_dims["legitimacy_trust"],
            epistemic_quality=result_dims["epistemic_quality"],
            veto_flags=unique_vetoes,
            reason_codes=unique_reasons,
        )


__all__ = [
    "TacticalLayerConfig",
    "TacticalResult",
    "TacticalLayer",
]
