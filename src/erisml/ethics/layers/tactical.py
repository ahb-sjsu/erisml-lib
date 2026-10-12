# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tactical Layer: Full MoralVector reasoning (10-100ms target).

The tactical layer runs all active EMs and aggregates their MoralVector
outputs according to governance configuration.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.facts import EthicalFacts
    from erisml.ethics.modules.base import EthicsModuleV2

from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.moral_landscape import MoralLandscape
from erisml.ethics.judgement import EthicalJudgementV2

log = logging.getLogger(__name__)


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

    tier_enabled: Dict[int, bool] = field(default_factory=dict)
    """Tiers switched off by governance; a tier not listed runs. Tier 0 (constitutional)
    always runs, whatever this says."""

    fail_closed: bool = False
    """What an EM that raises means for the option it was judging.

    An EM that fails has not approved the option; it has said nothing. Every failure is
    recorded in ``TacticalResult.em_failures`` and logged either way. With ``fail_closed``
    True the failure also vetoes the option, as an objection would. The default (False)
    keeps the earlier behaviour, judging the option by the EMs that did answer; safety-
    critical deployments should set it to True."""


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

    em_failures: List[str] = field(default_factory=list)
    """EMs that raised instead of judging, as ``"em_name: ExceptionType: message"``."""


def _v2(judgement: EthicalJudgementV2) -> EthicalJudgementV2:
    """A V2 judgement, or an AttributeError (a V1 EM added without its adapter), raised where
    the caller records it as that EM's failure."""
    judgement.veto_triggered, judgement.em_tier  # noqa: B018
    return judgement


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
        return self.evaluate_options([facts])[facts.option_id]

    def evaluate_options(
        self,
        options: Sequence[EthicalFacts],
        ems: Optional[Sequence[EthicsModuleV2]] = None,
    ) -> Dict[str, TacticalResult]:
        """Evaluate a set of options through the given EMs (default: all).

        An EM that defines ``judge_set(options)`` judges the set at once, for judgements
        that depend on the alternatives (CorePhysicalSafety's "a safer option exists");
        any other EM judges each option alone. Disabled tiers are skipped (tier 0 always
        runs), and a failing EM is recorded per option, vetoing under ``fail_closed``.
        """
        if not self.config.enabled:
            return {
                f.option_id: TacticalResult(
                    option_id=f.option_id,
                    judgements=[],
                    aggregated_vector=MoralVector.from_ethical_facts(f),
                    vetoed=False,
                    veto_reasons=[],
                    latency_ms=0.0,
                )
                for f in options
            }

        start_time = time.perf_counter()
        ids = [f.option_id for f in options]
        judgements: Dict[str, List[EthicalJudgementV2]] = {i: [] for i in ids}
        veto_reasons: Dict[str, List[str]] = {i: [] for i in ids}
        em_failures: Dict[str, List[str]] = {i: [] for i in ids}
        vetoed: Dict[str, bool] = {i: False for i in ids}

        def failed(name: str, oid: str, e: Exception) -> None:
            failure = f"{name}: {type(e).__name__}: {e}"
            em_failures[oid].append(failure)
            log.warning("ethics module failed on option %s: %s", oid, failure)
            if self.config.fail_closed:
                vetoed[oid] = True
                veto_reasons[oid].append(
                    f"{name}: failed ({type(e).__name__}); fail_closed"
                )

        for em in self.ems if ems is None else ems:
            name = getattr(em, "em_name", type(em).__name__)
            em_tier = getattr(em, "em_tier", None)
            if em_tier != 0 and not self.config.tier_enabled.get(em_tier, True):
                continue
            judged: Dict[str, EthicalJudgementV2] = {}
            judge_set = getattr(em, "judge_set", None)
            if callable(judge_set):
                try:
                    judged = {
                        k: _v2(j) for k, j in dict(judge_set(list(options))).items()
                    }
                except Exception as e:  # an EM that fails has not approved any option
                    for oid in ids:
                        failed(name, oid, e)
                    continue
            else:
                for f in options:
                    try:
                        judged[f.option_id] = _v2(em.judge(f))
                    except Exception as e:
                        failed(name, f.option_id, e)
            for oid, judgement in judged.items():
                if oid not in judgements:
                    continue
                judgements[oid].append(judgement)
                if judgement.veto_triggered and self.config.tier_veto_enabled.get(
                    judgement.em_tier, True
                ):
                    vetoed[oid] = True
                    if judgement.veto_reason:
                        veto_reasons[oid].append(f"{name}: {judgement.veto_reason}")

        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            oid: TacticalResult(
                option_id=oid,
                judgements=judgements[oid],
                aggregated_vector=self._aggregate_vectors(judgements[oid]),
                vetoed=vetoed[oid],
                veto_reasons=veto_reasons[oid],
                latency_ms=latency_ms,
                em_failures=em_failures[oid],
            )
            for oid in ids
        }

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
            privacy_protection=result_dims["privacy_protection"],
            societal_environmental=result_dims["societal_environmental"],
            virtue_care=result_dims["virtue_care"],
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
