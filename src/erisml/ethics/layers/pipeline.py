# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEMEPipeline: Complete three-layer decision orchestration.

Combines reflex, tactical, and strategic layers into a unified
decision pipeline with audit proof generation.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.modules.base import EthicsModuleV2

from erisml.ethics.facts import EthicalFacts
from erisml.ethics.deontic_gate import evaluate_maxim
from erisml.ethics.moral_landscape import MoralLandscape
from erisml.ethics.decision_proof import (
    DecisionProof,
    LayerOutput,
    EMJudgementRecord,
    hash_moral_vector,
    hash_ethical_facts,
)
from erisml.ethics.layers.reflex import ReflexLayer, ReflexLayerConfig, VetoResult
from erisml.ethics.layers.tactical import (
    TacticalLayer,
    TacticalLayerConfig,
    TacticalResult,
)
from erisml.ethics.layers.strategic import StrategicLayer, StrategicLayerConfig
from erisml.ethics.governance.config_v2 import GovernanceConfigV2
from erisml.ethics.governance.aggregation_v2 import select_option_v2


@dataclass
class PipelineConfig:
    """Configuration for the complete pipeline."""

    reflex_config: Optional[ReflexLayerConfig] = None
    """Configuration for reflex layer. None installs the reflex layer's default hard-constraint
    rules (rights violation, discrimination, explicit rule); an explicit config is used as given.
    Before, the default was an empty config, so a default pipeline ran no reflex rules at all."""

    tactical_config: TacticalLayerConfig = field(default_factory=TacticalLayerConfig)
    """Configuration for tactical layer."""

    strategic_config: StrategicLayerConfig = field(default_factory=StrategicLayerConfig)
    """Configuration for strategic layer."""

    generate_proofs: bool = True
    """Whether to generate decision proofs."""

    profile_name: str = "default"
    """Name of the governance profile in use."""

    profile_hash: str = ""
    """Hash of the governance profile."""

    em_catalog_version: str = "2.0.0"
    """Version of the EM catalog."""

    governance: Optional[GovernanceConfigV2] = None
    """The governance profile's configuration, executed. When set, the tactical layer runs
    the tiers it enables with its tier weights and veto rights, and aggregation, vetoes and
    selection go through ``governance.aggregation_v2.select_option_v2``: its EM, tier and
    stakeholder weights, its stakeholder aggregation strategy, its explicit veto EMs, its
    dimension weights for the scalar collapse, its score threshold, and its tie breaker (the
    baseline is preferred only under ``tie_breaker="status_quo"``). None keeps the earlier
    behaviour, the tactical layer's fixed tier weights and an always-preferred baseline."""


@dataclass
class DecisionResult:
    """Result of a complete pipeline decision."""

    selected_option_id: Optional[str]
    """ID of the selected option, or None if all vetoed."""

    ranked_options: List[str]
    """Options ranked by preference (best first, excluding vetoed)."""

    forbidden_options: List[str]
    """Options that were vetoed."""

    moral_landscape: MoralLandscape
    """MoralVectors for all options."""

    rationale: str
    """Human-readable explanation of the decision."""

    proof: Optional[DecisionProof]
    """Audit proof if generated."""

    total_latency_ms: float
    """Total pipeline execution time."""

    em_failures: Dict[str, List[str]] = field(default_factory=dict)
    """Per option, the EMs that raised instead of judging (see TacticalLayerConfig.fail_closed)."""


class DEMEPipeline:
    """
    Complete three-layer decision pipeline.

    Orchestrates:
    1. Reflex Layer: Fast veto checks
    2. Tactical Layer: Full MoralVector reasoning
    3. Strategic Layer: Policy recording (optional)

    Produces ranked options and audit proofs.
    """

    def __init__(
        self,
        ems: Optional[List[EthicsModuleV2]] = None,
        config: Optional[PipelineConfig] = None,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            ems: List of V2 ethics modules.
            config: Pipeline configuration.
        """
        self.config = config or PipelineConfig()
        gov = self.config.governance
        if gov is not None:
            # one source for tier semantics: the tactical layer runs and weighs tiers as
            # governance says
            tiers = gov.tier_configs
            self.config.tactical_config = replace(
                self.config.tactical_config,
                tier_weights={t: c.weight_multiplier for t, c in tiers.items()},
                tier_veto_enabled={t: c.veto_enabled for t, c in tiers.items()},
                tier_enabled={t: c.enabled for t, c in tiers.items()},
            )

        self.reflex = ReflexLayer(self.config.reflex_config)
        self.tactical = TacticalLayer(ems, self.config.tactical_config)
        self.strategic = StrategicLayer(self.config.strategic_config)

    def add_em(self, em: EthicsModuleV2) -> None:
        """Add an ethics module to the tactical layer."""
        self.tactical.add_em(em)

    def decide(
        self,
        options: List[EthicalFacts],
        baseline_option_id: Optional[str] = None,
    ) -> DecisionResult:
        """
        Run complete decision pipeline.

        Args:
            options: List of candidate options as EthicalFacts.
            baseline_option_id: Optional ID of status quo option.

        Returns:
            DecisionResult with selected option and audit trail.
        """
        start_time = time.perf_counter()
        layer_outputs: List[LayerOutput] = []

        # Phase 1: Reflex layer - fast veto checks
        reflex_start = time.perf_counter()
        reflex_results: Dict[str, VetoResult] = {}
        reflex_vetoed: List[str] = []
        deontic_vetoes: Dict[str, str] = {}

        for facts in options:
            reflex_result = self.reflex.check(facts)
            reflex_results[facts.option_id] = reflex_result
            vetoed = reflex_result.vetoed
            # Deontic maxim gate: veto options whose (possibly negated) maxim
            # fails Kantian universalizability. No-op when no maxim is present.
            maxim_result = evaluate_maxim(getattr(facts, "maxim", None))
            if maxim_result.vetoed:
                vetoed = True
                deontic_vetoes[facts.option_id] = maxim_result.reason
            if vetoed:
                reflex_vetoed.append(facts.option_id)

        reflex_duration = int((time.perf_counter() - reflex_start) * 1_000_000)
        layer_outputs.append(
            LayerOutput(
                layer_name="reflex",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_us=reflex_duration,
                veto_triggered=len(reflex_vetoed) > 0,
                veto_reason=(
                    f"Vetoed {len(reflex_vetoed)} options" if reflex_vetoed else None
                ),
                output_data={
                    "vetoed_options": reflex_vetoed,
                    "deontic_vetoes": deontic_vetoes,
                    "total_checked": len(options),
                },
            )
        )

        # Phase 2: Tactical layer - full moral reasoning
        tactical_start = time.perf_counter()
        tactical_results: Dict[str, TacticalResult] = {}
        tactical_vetoed: List[str] = []
        em_failures: Dict[str, List[str]] = {}
        landscape = MoralLandscape()
        em_judgement_records: List[EMJudgementRecord] = []

        # Only evaluate non-reflex-vetoed options
        for facts in options:
            if facts.option_id in reflex_vetoed:
                # Skip options already vetoed by reflex
                continue

            tactical_result = self.tactical.evaluate(facts)
            tactical_results[facts.option_id] = tactical_result
            landscape.add(facts.option_id, tactical_result.aggregated_vector)

            if tactical_result.vetoed:
                tactical_vetoed.append(facts.option_id)
            if tactical_result.em_failures:
                em_failures[facts.option_id] = list(tactical_result.em_failures)

            # Record EM judgements for proof
            for j in tactical_result.judgements:
                em_judgement_records.append(
                    EMJudgementRecord(
                        em_name=j.em_name,
                        em_tier=j.em_tier,
                        stakeholder=j.stakeholder,
                        verdict=j.verdict,
                        moral_vector_hash=hash_moral_vector(j.moral_vector),
                        veto_triggered=j.veto_triggered,
                        reason_summary="; ".join(j.reasons[:2]) if j.reasons else "",
                    )
                )

        governed = None
        gov = self.config.governance
        if gov is not None:
            # The governance profile decides: aggregation, vetoes and ranking come from
            # select_option_v2. A module that failed under fail_closed still forbids.
            failed_closed = [
                oid
                for oid, r in tactical_results.items()
                if r.em_failures and self.tactical.config.fail_closed
            ]
            governed = select_option_v2(
                {oid: r.judgements for oid, r in tactical_results.items()},
                gov,
                candidate_ids=list(tactical_results),
                baseline_option_id=baseline_option_id,
            )
            tactical_vetoed = sorted(
                set(governed.forbidden_options) | set(failed_closed)
            )
            landscape = MoralLandscape()
            for oid, vec in governed.aggregated_vectors.items():
                landscape.add(oid, vec)

        tactical_duration = int((time.perf_counter() - tactical_start) * 1_000_000)
        layer_outputs.append(
            LayerOutput(
                layer_name="tactical",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_us=tactical_duration,
                veto_triggered=len(tactical_vetoed) > 0,
                veto_reason=(
                    f"Vetoed {len(tactical_vetoed)} options"
                    if tactical_vetoed
                    else None
                ),
                output_data={
                    "vetoed_options": tactical_vetoed,
                    "evaluated_options": len(tactical_results),
                    "em_failures": em_failures,
                },
            )
        )

        # Combine all vetoed options
        all_vetoed = list(set(reflex_vetoed + tactical_vetoed))

        # Rank against the authoritative forbidden set: the reflex vetoes and the tactical vetoes
        # of tiers allowed to veto (a failing module under fail_closed included). The vector's
        # veto flags alone are not that set: a module can forbid without setting a flag, which
        # left a forbidden option rankable and selectable, and an advisory tier's flag removed
        # an option that tier may not veto.
        forbidden = set(all_vetoed)
        selected_id: Optional[str] = None
        if governed is not None:
            weights = gov.dimension_weights.to_dict()
            ranked = [
                (oid, landscape.get(oid).to_scalar(weights=weights))
                for oid in governed.ranked_options
                if oid not in forbidden
            ]
            if governed.selected_option_id not in forbidden:
                selected_id = governed.selected_option_id
            elif ranked:
                selected_id = ranked[0][0]
        else:
            ranked = [
                (oid, s)
                for oid, s in landscape.rank_by_scalar()
                if oid not in forbidden
            ]

        # Select best option (or baseline if available and acceptable)
        if governed is None and ranked:
            selected_id = ranked[0][0]
            # Prefer baseline if it's in the top tier
            if baseline_option_id and baseline_option_id not in all_vetoed:
                baseline_score = next(
                    (score for oid, score in ranked if oid == baseline_option_id),
                    None,
                )
                if baseline_score is not None:
                    top_score = ranked[0][1]
                    if baseline_score >= top_score * 0.95:  # Within 5% of best
                        selected_id = baseline_option_id

        # Build rationale
        rationale_parts = []
        if selected_id:
            rationale_parts.append(f"Selected option: {selected_id}")
            if tactical_results.get(selected_id):
                vec = landscape.get(selected_id)
                score = vec.to_scalar(
                    weights=gov.dimension_weights.to_dict() if gov else None
                )
                rationale_parts.append(f"Aggregate score: {score:.3f}")
        else:
            rationale_parts.append("No option selected (all vetoed)")

        if all_vetoed:
            rationale_parts.append(f"Vetoed options: {', '.join(all_vetoed)}")

        rationale = ". ".join(rationale_parts)

        # Generate proof if configured
        proof: Optional[DecisionProof] = None
        if self.config.generate_proofs:
            # Hash all input facts
            facts_hashes = [hash_ethical_facts(f) for f in options]
            combined_facts_hash = hash_ethical_facts({"options": facts_hashes})

            # Build moral vector summary
            mv_summary = {oid: vec.to_dict() for oid, vec in landscape.vectors.items()}

            previous = self.strategic.latest_proof()
            proof = DecisionProof(
                previous_proof_hash=previous.proof_hash if previous else None,
                input_facts_hash=combined_facts_hash,
                profile_hash=self.config.profile_hash,
                profile_name=self.config.profile_name,
                em_catalog_version=self.config.em_catalog_version,
                active_em_names=[em.em_name for em in self.tactical.ems],
                layer_outputs=layer_outputs,
                em_judgements=em_judgement_records,
                candidate_option_ids=[f.option_id for f in options],
                selected_option_id=selected_id,
                ranked_options=[oid for oid, _ in ranked],
                forbidden_options=all_vetoed,
                governance_rationale=rationale,
                moral_vector_summary=mv_summary,
            )
            proof.finalize()

            # Record in strategic layer
            self.strategic.record_decision(proof)

        total_latency = (time.perf_counter() - start_time) * 1000

        return DecisionResult(
            selected_option_id=selected_id,
            ranked_options=[oid for oid, _ in ranked],
            forbidden_options=all_vetoed,
            moral_landscape=landscape,
            rationale=rationale,
            proof=proof,
            total_latency_ms=total_latency,
            em_failures=em_failures,
        )


__all__ = [
    "PipelineConfig",
    "DecisionResult",
    "DEMEPipeline",
]
