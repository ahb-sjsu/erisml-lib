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
from typing import Any, Dict, List, Optional, TYPE_CHECKING

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
from erisml.ethics.governance.aggregation_v2 import (
    aggregate_moral_vectors,
    check_vetoes,
    select_option_v2,
)
from erisml.ethics.judgement import EthicalJudgementV2
from erisml.ethics.layers.composition import resolve_pattern
from erisml.ethics.moral_vector import MoralVector


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

    composition: Optional[Any] = None
    """The composition pattern (a name in composition.PATTERNS, or a CompositionPattern).
    None takes the governance profile's, else ``flat``, every EM in one stage."""

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

    composition: str = "flat"
    """The composition pattern the tactical layer ran (layers/composition.py)."""

    stages: List[Dict[str, Any]] = field(default_factory=list)
    """Per stage: its EMs, the options it evaluated, vetoed and narrowed out."""


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

    def _forbids(
        self, result: TacticalResult, gov: Optional[GovernanceConfigV2]
    ) -> bool:
        """Whether a stage's judgements forbid an option: under governance, its veto rights
        (``check_vetoes``); otherwise the tier veto rights the tactical layer applied. A
        module that failed under fail_closed forbids either way."""
        if gov is None:
            return result.vetoed
        failed_closed = bool(result.em_failures) and self.tactical.config.fail_closed
        return failed_closed or check_vetoes(result.judgements, gov)[0]

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

        # Phase 2: Tactical layer, composed by the pattern's stages (layers/composition.py).
        # Each stage runs the EMs it admits on the options still standing; it may veto,
        # narrow to its best-satisfying subset, and rank. No stage resurrects an option.
        tactical_start = time.perf_counter()
        gov = self.config.governance
        pattern = resolve_pattern(
            self.config.composition
            if self.config.composition is not None
            else (gov.composition if gov is not None else None)
        )
        weights = gov.dimension_weights.to_dict() if gov is not None else None

        def aggregate(js: List[EthicalJudgementV2]) -> MoralVector:
            if gov is not None:
                return aggregate_moral_vectors(js, gov)
            return self.tactical._aggregate_vectors(js)

        def score(vec: MoralVector) -> float:
            return vec.to_scalar(weights=weights)

        tactical_results: Dict[str, TacticalResult] = {}
        tactical_vetoed: List[str] = []
        em_failures: Dict[str, List[str]] = {}
        em_judgement_records: List[EMJudgementRecord] = []
        stage_trace: List[Dict[str, Any]] = []
        vector_of: Dict[str, MoralVector] = {}
        standing = [f for f in options if f.option_id not in reflex_vetoed]
        for (
            f
        ) in standing:  # every option the reflex layer passed is judged, if by no EM
            tactical_results[f.option_id] = TacticalResult(
                option_id=f.option_id,
                judgements=[],
                aggregated_vector=aggregate([]),
                vetoed=False,
                veto_reasons=[],
                latency_ms=0.0,
            )
            vector_of[f.option_id] = aggregate([])
        rank_source: Dict[str, List[EthicalJudgementV2]] = {}
        rank_advisory = False
        narrowed_out: List[List[str]] = []

        for stage in pattern.stages:
            ems = [em for em in self.tactical.ems if stage.admits(em)]
            trace: Dict[str, Any] = {
                "stage": stage.name,
                "ems": [getattr(em, "em_name", type(em).__name__) for em in ems],
                "evaluated": [f.option_id for f in standing],
                "vetoed": [],
                "narrowed_out": [],
            }
            stage_trace.append(trace)
            if not ems or not standing:
                continue
            results = self.tactical.evaluate_options(standing, ems)
            for oid, r in results.items():
                before = tactical_results[oid]
                tactical_results[oid] = (
                    r
                    if not before.judgements and not before.em_failures
                    else replace(
                        before,
                        judgements=before.judgements + r.judgements,
                        vetoed=before.vetoed or r.vetoed,
                        veto_reasons=before.veto_reasons + r.veto_reasons,
                        em_failures=before.em_failures + r.em_failures,
                    )
                )
                if r.em_failures:
                    em_failures.setdefault(oid, []).extend(r.em_failures)
                vector_of[oid] = aggregate(r.judgements)
                for j in r.judgements:
                    em_judgement_records.append(
                        EMJudgementRecord(
                            em_name=j.em_name,
                            em_tier=j.em_tier,
                            stakeholder=j.stakeholder,
                            verdict=j.verdict,
                            moral_vector_hash=hash_moral_vector(j.moral_vector),
                            veto_triggered=j.veto_triggered,
                            reason_summary=(
                                "; ".join(j.reasons[:2]) if j.reasons else ""
                            ),
                        )
                    )
            if stage.vetoes:
                trace["vetoed"] = [
                    f.option_id
                    for f in standing
                    if self._forbids(results[f.option_id], gov)
                ]
                tactical_vetoed += trace["vetoed"]
                standing = [f for f in standing if f.option_id not in trace["vetoed"]]
            if stage.narrows and len(standing) > 1:
                scores = {
                    f.option_id: score(aggregate(results[f.option_id].judgements))
                    for f in standing
                }
                floor = max(scores.values()) - pattern.tolerance
                trace["narrowed_out"] = sorted(
                    (oid for oid, v in scores.items() if v < floor),
                    key=lambda oid: -scores[oid],
                )
                narrowed_out.append(trace["narrowed_out"])
                standing = [f for f in standing if scores[f.option_id] >= floor]
            if stage.ranks:
                rank_source = {
                    f.option_id: results[f.option_id].judgements for f in standing
                }
                rank_advisory = not stage.vetoes

        survivors = [f.option_id for f in standing]
        if not rank_source:  # no ranking stage ran an EM: rank on everything judged
            rank_source = {
                oid: tactical_results[oid].judgements
                for oid in survivors
                if oid in tactical_results
            }
        landscape = MoralLandscape()
        for oid in tactical_results:
            js = rank_source.get(oid)
            landscape.add(oid, aggregate(js) if js is not None else vector_of[oid])

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
                    "composition": pattern.name,
                    "stages": stage_trace,
                },
            )
        )

        # Combine all vetoed options
        all_vetoed = list(dict.fromkeys(reflex_vetoed + tactical_vetoed))

        # Rank only what the stages left standing. The authoritative forbidden set is the
        # reflex vetoes and each vetoing stage's vetoes (tier veto rights, governance and
        # fail_closed applied), never the vectors' veto flags alone. Options a narrowing stage
        # filtered out are not forbidden; they follow the survivors, those filtered later first.
        selected_id: Optional[str] = None
        if gov is not None:
            judged = {oid: rank_source.get(oid, []) for oid in survivors}
            if rank_advisory:  # a stage that may not veto only re-ranks
                judged = {
                    oid: [replace(j, veto_triggered=False) for j in js]
                    for oid, js in judged.items()
                }
            governed = select_option_v2(
                judged,
                gov,
                candidate_ids=survivors,
                baseline_option_id=baseline_option_id,
            )
            for oid in governed.forbidden_options:
                if oid not in all_vetoed:
                    all_vetoed.append(oid)
            ranked = [
                (oid, score(landscape.get(oid)))
                for oid in governed.ranked_options
                if oid not in all_vetoed
            ]
            if governed.selected_option_id not in all_vetoed:
                selected_id = governed.selected_option_id
            elif ranked:
                selected_id = ranked[0][0]
        else:
            ranked = sorted(
                ((oid, score(landscape.get(oid))) for oid in survivors),
                key=lambda x: x[1],
                reverse=True,
            )
            if ranked:
                selected_id = ranked[0][0]
                # Prefer baseline if it's in the top tier
                if baseline_option_id and baseline_option_id not in all_vetoed:
                    baseline_score = next(
                        (v for oid, v in ranked if oid == baseline_option_id),
                        None,
                    )
                    if baseline_score is not None:
                        if baseline_score >= ranked[0][1] * 0.95:  # Within 5% of best
                            selected_id = baseline_option_id
        listed = {oid for oid, _ in ranked}
        threshold = gov.min_score_threshold if gov is not None else 0.0
        for out in reversed(narrowed_out):
            for oid in out:
                v = score(landscape.get(oid))
                if oid not in listed and v >= threshold:
                    ranked.append((oid, v))
                    listed.add(oid)

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
            composition=pattern.name,
            stages=stage_trace,
        )


__all__ = [
    "PipelineConfig",
    "DecisionResult",
    "DEMEPipeline",
]
