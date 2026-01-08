# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Aggregation V2: MoralVector-based judgement aggregation.

Provides functions for aggregating MoralVectors from multiple EMs,
applying lexical priorities, and selecting options.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.judgement import EthicalJudgementV2
from erisml.ethics.decision_proof import DecisionProof
from erisml.ethics.governance.config_v2 import (
    GovernanceConfigV2,
)


@dataclass
class DecisionOutcomeV2:
    """V2 decision outcome with MoralVector support."""

    selected_option_id: Optional[str]
    """ID of selected option, or None if all vetoed."""

    ranked_options: List[str]
    """Options ranked by preference (best first)."""

    aggregated_vectors: Dict[str, MoralVector]
    """Aggregated MoralVector per option."""

    aggregated_judgements: Dict[str, EthicalJudgementV2]
    """Governance-level judgement per option."""

    forbidden_options: List[str]
    """Options that were vetoed."""

    veto_reasons: Dict[str, List[str]]
    """Per-option veto reasons."""

    rationale: str
    """Human-readable decision rationale."""

    decision_proof: Optional[DecisionProof] = None
    """Audit proof if generated."""


def aggregate_moral_vectors(
    judgements: List[EthicalJudgementV2],
    config: GovernanceConfigV2,
) -> MoralVector:
    """
    Aggregate MoralVectors from multiple judgements.

    Args:
        judgements: List of V2 judgements to aggregate.
        config: Governance configuration.

    Returns:
        Aggregated MoralVector.
    """
    if not judgements:
        return MoralVector()

    # Compute weighted contributions
    weighted_values: Dict[str, float] = {
        dim: 0.0 for dim in MoralVector.core_dimension_names()
    }
    total_weight = 0.0
    all_vetoes: List[str] = []
    all_reasons: List[str] = []

    for j in judgements:
        weight = config.weight_for_em(j.em_name, j.em_tier, j.stakeholder)
        total_weight += weight

        for dim in MoralVector.core_dimension_names():
            weighted_values[dim] += weight * getattr(j.moral_vector, dim)

        all_vetoes.extend(j.moral_vector.veto_flags)
        all_reasons.extend(j.moral_vector.reason_codes)

    # Normalize
    if total_weight > 0:
        for dim in weighted_values:
            weighted_values[dim] /= total_weight

    # Deduplicate vetoes and reasons
    unique_vetoes = list(dict.fromkeys(all_vetoes))
    unique_reasons = list(dict.fromkeys(all_reasons))

    return MoralVector(
        physical_harm=weighted_values["physical_harm"],
        rights_respect=weighted_values["rights_respect"],
        fairness_equity=weighted_values["fairness_equity"],
        autonomy_respect=weighted_values["autonomy_respect"],
        legitimacy_trust=weighted_values["legitimacy_trust"],
        epistemic_quality=weighted_values["epistemic_quality"],
        veto_flags=unique_vetoes,
        reason_codes=unique_reasons,
    )


def apply_lexical_priorities(
    judgements: List[EthicalJudgementV2],
    config: GovernanceConfigV2,
) -> List[EthicalJudgementV2]:
    """
    Sort judgements by lexical priority layers.

    Higher priority tiers are considered first for veto decisions.

    Args:
        judgements: List of V2 judgements.
        config: Governance configuration.

    Returns:
        Judgements sorted by priority (highest first).
    """
    # Get priority for each tier from lexical layers
    tier_priority: Dict[int, int] = {}
    for layer in config.lexical_layers:
        tier_priority[layer.tier] = layer.priority

    # Default priorities if no lexical layers defined
    default_priorities = {0: 100, 1: 80, 2: 60, 3: 40, 4: 20}
    for tier, priority in default_priorities.items():
        if tier not in tier_priority:
            tier_priority[tier] = priority

    # Sort by tier priority (descending)
    return sorted(
        judgements,
        key=lambda j: tier_priority.get(j.em_tier, 0),
        reverse=True,
    )


def check_vetoes(
    judgements: List[EthicalJudgementV2],
    config: GovernanceConfigV2,
) -> Tuple[bool, List[str]]:
    """
    Check if any judgements trigger a veto.

    Args:
        judgements: List of V2 judgements.
        config: Governance configuration.

    Returns:
        Tuple of (vetoed, veto_reasons).
    """
    veto_reasons: List[str] = []

    for j in judgements:
        if j.veto_triggered:
            # Check if this EM can actually veto
            if config.can_veto(j.em_name, j.em_tier):
                reason = j.veto_reason or f"{j.em_name}: Veto triggered"
                veto_reasons.append(reason)

    return len(veto_reasons) > 0, veto_reasons


def aggregate_judgements_v2(
    option_id: str,
    judgements: List[EthicalJudgementV2],
    config: GovernanceConfigV2,
) -> EthicalJudgementV2:
    """
    Aggregate judgements for a single option into a governance-level judgement.

    Args:
        option_id: ID of the option.
        judgements: List of EM judgements for this option.
        config: Governance configuration.

    Returns:
        Aggregated governance-level judgement.
    """
    # Aggregate moral vectors
    aggregated_vector = aggregate_moral_vectors(judgements, config)

    # Check for vetoes
    vetoed, veto_reasons = check_vetoes(judgements, config)

    # Determine verdict
    if vetoed:
        verdict = "forbid"
    else:
        score = aggregated_vector.to_scalar(weights=config.dimension_weights.to_dict())
        if score >= 0.8:
            verdict = "strongly_prefer"
        elif score >= 0.6:
            verdict = "prefer"
        elif score >= 0.4:
            verdict = "neutral"
        else:
            verdict = "avoid"

    # Collect reasons
    all_reasons = []
    for j in judgements:
        all_reasons.extend(j.reasons)
    unique_reasons = list(dict.fromkeys(all_reasons))

    return EthicalJudgementV2(
        option_id=option_id,
        em_name="governance",
        stakeholder="multi_stakeholder",
        em_tier=-1,  # Governance level
        verdict=verdict,
        moral_vector=aggregated_vector,
        veto_triggered=vetoed,
        veto_reason="; ".join(veto_reasons) if veto_reasons else None,
        confidence=1.0,
        reasons=unique_reasons[:5],  # Top 5 reasons
        metadata={
            "em_count": len(judgements),
            "veto_count": len(veto_reasons),
        },
    )


def select_option_v2(
    judgements_by_option: Dict[str, List[EthicalJudgementV2]],
    config: GovernanceConfigV2,
    *,
    candidate_ids: Optional[List[str]] = None,
    baseline_option_id: Optional[str] = None,
) -> DecisionOutcomeV2:
    """
    Select the best option from a set of candidates.

    Args:
        judgements_by_option: Dict mapping option_id to list of judgements.
        config: Governance configuration.
        candidate_ids: Optional subset of options to consider.
        baseline_option_id: Optional status quo option (for tie-breaking).

    Returns:
        DecisionOutcomeV2 with selected option and ranking.
    """
    if candidate_ids is None:
        candidate_ids = list(judgements_by_option.keys())

    # Aggregate judgements for each option
    aggregated_vectors: Dict[str, MoralVector] = {}
    aggregated_judgements: Dict[str, EthicalJudgementV2] = {}
    forbidden_options: List[str] = []
    veto_reasons: Dict[str, List[str]] = {}

    for option_id in candidate_ids:
        judgements = judgements_by_option.get(option_id, [])
        agg_judgement = aggregate_judgements_v2(option_id, judgements, config)

        aggregated_judgements[option_id] = agg_judgement
        aggregated_vectors[option_id] = agg_judgement.moral_vector

        if agg_judgement.veto_triggered:
            forbidden_options.append(option_id)
            if agg_judgement.veto_reason:
                veto_reasons[option_id] = [agg_judgement.veto_reason]

    # Filter and rank non-forbidden options
    eligible_ids = [oid for oid in candidate_ids if oid not in forbidden_options]

    # Apply score threshold
    if config.min_score_threshold > 0:
        eligible_ids = [
            oid
            for oid in eligible_ids
            if aggregated_vectors[oid].to_scalar(
                weights=config.dimension_weights.to_dict()
            )
            >= config.min_score_threshold
        ]

    # Check require_non_forbidden
    if config.require_non_forbidden and not eligible_ids:
        return DecisionOutcomeV2(
            selected_option_id=None,
            ranked_options=[],
            aggregated_vectors=aggregated_vectors,
            aggregated_judgements=aggregated_judgements,
            forbidden_options=forbidden_options,
            veto_reasons=veto_reasons,
            rationale="All options were vetoed or below threshold",
        )

    # Rank by scalar score
    ranked = sorted(
        eligible_ids,
        key=lambda oid: aggregated_vectors[oid].to_scalar(
            weights=config.dimension_weights.to_dict()
        ),
        reverse=True,
    )

    # Select best option
    selected_id: Optional[str] = None
    if ranked:
        selected_id = ranked[0]

        # Handle tie-breaking with baseline
        if baseline_option_id and baseline_option_id in ranked:
            baseline_score = aggregated_vectors[baseline_option_id].to_scalar(
                weights=config.dimension_weights.to_dict()
            )
            best_score = aggregated_vectors[ranked[0]].to_scalar(
                weights=config.dimension_weights.to_dict()
            )

            if config.tie_breaker == "status_quo":
                # Prefer baseline if within 5% of best
                if baseline_score >= best_score * 0.95:
                    selected_id = baseline_option_id
            elif config.tie_breaker == "random":
                # Random among top-tier options
                threshold = best_score * 0.95
                top_tier = [
                    oid
                    for oid in ranked
                    if aggregated_vectors[oid].to_scalar(
                        weights=config.dimension_weights.to_dict()
                    )
                    >= threshold
                ]
                selected_id = random.choice(top_tier)

    # Build rationale
    if selected_id:
        score = aggregated_vectors[selected_id].to_scalar(
            weights=config.dimension_weights.to_dict()
        )
        rationale = f"Selected {selected_id} with score {score:.3f}"
    else:
        rationale = "No eligible options"

    if forbidden_options:
        rationale += f". Vetoed: {', '.join(forbidden_options)}"

    return DecisionOutcomeV2(
        selected_option_id=selected_id,
        ranked_options=ranked,
        aggregated_vectors=aggregated_vectors,
        aggregated_judgements=aggregated_judgements,
        forbidden_options=forbidden_options,
        veto_reasons=veto_reasons,
        rationale=rationale,
    )


__all__ = [
    "DecisionOutcomeV2",
    "aggregate_moral_vectors",
    "apply_lexical_priorities",
    "check_vetoes",
    "aggregate_judgements_v2",
    "select_option_v2",
]
