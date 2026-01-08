# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.modules.base import EthicsModuleV2

from erisml.ethics.facts import EthicalFacts
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


@dataclass
class PipelineConfig:
    """Configuration for the complete pipeline."""

    reflex_config: ReflexLayerConfig = field(default_factory=ReflexLayerConfig)
    """Configuration for reflex layer."""

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

        for facts in options:
            result = self.reflex.check(facts)
            reflex_results[facts.option_id] = result
            if result.vetoed:
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
                    "total_checked": len(options),
                },
            )
        )

        # Phase 2: Tactical layer - full moral reasoning
        tactical_start = time.perf_counter()
        tactical_results: Dict[str, TacticalResult] = {}
        tactical_vetoed: List[str] = []
        landscape = MoralLandscape()
        em_judgement_records: List[EMJudgementRecord] = []

        # Only evaluate non-reflex-vetoed options
        for facts in options:
            if facts.option_id in reflex_vetoed:
                # Skip options already vetoed by reflex
                continue

            result = self.tactical.evaluate(facts)
            tactical_results[facts.option_id] = result
            landscape.add(facts.option_id, result.aggregated_vector)

            if result.vetoed:
                tactical_vetoed.append(facts.option_id)

            # Record EM judgements for proof
            for j in result.judgements:
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
                },
            )
        )

        # Combine all vetoed options
        all_vetoed = list(set(reflex_vetoed + tactical_vetoed))

        # Rank remaining options by scalar score
        non_vetoed = landscape.filter_vetoed()
        ranked = non_vetoed.rank_by_scalar()

        # Select best option (or baseline if available and acceptable)
        selected_id: Optional[str] = None
        if ranked:
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
                vec = tactical_results[selected_id].aggregated_vector
                score = vec.to_scalar()
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

            proof = DecisionProof(
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
        )


__all__ = [
    "PipelineConfig",
    "DecisionResult",
    "DEMEPipeline",
]
