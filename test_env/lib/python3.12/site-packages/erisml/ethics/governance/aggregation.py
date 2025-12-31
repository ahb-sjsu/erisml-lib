"""
Aggregation of EthicalJudgement objects into governance decisions.

This module implements the democratic governance layer described in the
ErisML ethics whitepaper. It takes multiple EthicalJudgement objects
(produced by different EthicsModules) and, using a GovernanceConfig,
produces aggregated assessments and a final decision outcome.

Version: 0.3 (EthicalDomains + base EMs / 'Geneva' layer)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random

from .config import GovernanceConfig
from ..judgement import EthicalJudgement, Verdict
from ..profile_v03 import BaseEMEnforcementMode


@dataclass
class DecisionOutcome:
    """
    Result of aggregating EM judgements over a set of candidate options.

    Fields:
        selected_option_id:
            The chosen option ID, or None if no option passed thresholds.

        ranked_options:
            List of option IDs sorted from most to least preferred among
            *eligible* options (those not forbidden and above threshold).

        aggregated_judgements:
            Aggregated EthicalJudgement per option, including metadata about
            vetoes, forbidden status, and raw per-EM scores.

        forbidden_options:
            List of option IDs that were deemed ineligible due to vetoes or
            forbidden verdicts, according to the GovernanceConfig.

        rationale:
            Human-readable explanation of how the selection was made.
    """

    selected_option_id: Optional[str]
    ranked_options: List[str]
    aggregated_judgements: Dict[str, EthicalJudgement]
    forbidden_options: List[str]
    rationale: str


def _compute_forbidden_flags(
    judgements: List[EthicalJudgement],
    cfg: GovernanceConfig,
) -> Tuple[bool, List[str], List[str], List[str]]:
    """
    Determine whether an option is forbidden, and by whom.

    Returns:
        forbidden (bool):
            True if the option is ineligible under the governance rules.

        forbidden_by (list[str]):
            Names of EMs that issued a "forbid" verdict.

        vetoed_by (list[str]):
            Subset of forbidden_by that are also listed in cfg.veto_ems.

        base_forbidden_by (list[str]):
            Subset of forbidden_by that are also listed in cfg.base_em_ids.
            When base_em_enforcement == HARD_VETO, this alone is sufficient
            to forbid an option regardless of other config flags.
    """
    forbidden_by = [j.em_name for j in judgements if j.verdict == "forbid"]
    vetoed_by = [em for em in forbidden_by if em in cfg.veto_ems]

    base_ids = set(cfg.base_em_ids or [])
    base_forbidden_by = [em for em in forbidden_by if em in base_ids]

    forbidden = False

    # 1) Foundational / "Geneva" EMs may impose a hard veto regardless
    #    of require_non_forbidden/veto_ems settings.
    if (
        cfg.base_em_enforcement == BaseEMEnforcementMode.HARD_VETO
        and len(base_forbidden_by) > 0
    ):
        forbidden = True

    # 2) Otherwise, fall back to normal governance rules.
    else:
        if cfg.require_non_forbidden:
            # Any forbid (from any EM) is enough to exclude the option.
            forbidden = len(forbidden_by) > 0
        else:
            # Only EMs with veto power can strictly forbid.
            forbidden = len(vetoed_by) > 0

    return forbidden, forbidden_by, vetoed_by, base_forbidden_by


def aggregate_judgements(
    option_id: str,
    judgements: List[EthicalJudgement],
    cfg: GovernanceConfig,
) -> EthicalJudgement:
    """
    Aggregate multiple EthicalJudgement objects for a single option.

    The aggregation applies GovernanceConfig rules:

    - Computes a weighted normative_score using stakeholder and EM weights.
    - Computes forbidden / veto flags based on verdicts and cfg, including
      special treatment for foundational ("base") EMs.
    - Derives an aggregated verdict from the score and forbidden status.
    - Packs raw per-EM information into metadata for audit.

    Returns:
        An EthicalJudgement representing the governance-level assessment
        of this option (em_name="governance", stakeholder="multi_stakeholder").
    """
    # Sanity check: all judgements should reference the same option.
    for j in judgements:
        if j.option_id != option_id:
            raise ValueError(
                f"Judgement option_id mismatch: expected {option_id}, "
                f"got {j.option_id} from EM {j.em_name}"
            )

    # Edge case: no judgements at all.
    if not judgements:
        return EthicalJudgement(
            option_id=option_id,
            em_name="governance",
            stakeholder="multi_stakeholder",
            verdict="neutral",
            normative_score=0.0,
            reasons=["No ethical judgements available for this option."],
            metadata={
                "forbidden": False,
                "forbidden_by": [],
                "vetoed_by": [],
                "base_forbidden_by": [],
                "raw_scores": {},
                "raw_verdicts": {},
                "note": "empty_judgement_set",
                "governance_config": {
                    "stakeholder_weights": cfg.stakeholder_weights,
                    "em_weights": cfg.em_weights,
                    "veto_ems": cfg.veto_ems,
                    "min_score_threshold": cfg.min_score_threshold,
                    "require_non_forbidden": cfg.require_non_forbidden,
                    "tie_breaker": cfg.tie_breaker,
                    "prefer_higher_uncertainty": cfg.prefer_higher_uncertainty,
                    "base_em_ids": cfg.base_em_ids,
                    "base_em_enforcement": cfg.base_em_enforcement.value,
                },
            },
        )

    # Compute forbidden/veto flags, including base EM semantics.
    (
        forbidden,
        forbidden_by,
        vetoed_by,
        base_forbidden_by,
    ) = _compute_forbidden_flags(judgements, cfg)

    # Compute weighted aggregate score.
    weighted_sum = 0.0
    weight_total = 0.0

    raw_scores: Dict[str, float] = {}
    raw_verdicts: Dict[str, str] = {}

    for j in judgements:
        w = cfg.weight_for_em(j.em_name, stakeholder=j.stakeholder)
        weighted_sum += w * j.normative_score
        weight_total += w
        raw_scores[j.em_name] = j.normative_score
        raw_verdicts[j.em_name] = j.verdict

    if weight_total <= 0.0:
        aggregated_score = 0.0
    else:
        aggregated_score = weighted_sum / weight_total

    # Map score + forbidden status to an aggregated verdict.
    if forbidden:
        agg_verdict: Verdict = "forbid"
    else:
        # Simple scoring → verdict mapping. This can be refined later.
        if aggregated_score >= 0.8:
            agg_verdict = "strongly_prefer"
        elif aggregated_score >= 0.6:
            agg_verdict = "prefer"
        elif aggregated_score >= 0.4:
            agg_verdict = "neutral"
        elif aggregated_score >= 0.2:
            agg_verdict = "avoid"
        else:
            agg_verdict = "avoid"

    # Human-readable reasons.
    reasons: List[str] = []
    reasons.append(
        f"Aggregated {len(judgements)} EM judgements "
        f"with GovernanceConfig(stakeholder_weights={cfg.stakeholder_weights}, "
        f"em_weights={cfg.em_weights})."
    )

    if forbidden:
        if (
            base_forbidden_by
            and cfg.base_em_enforcement == BaseEMEnforcementMode.HARD_VETO
        ):
            reasons.append(
                "Option is forbidden due to foundational EM(s): "
                + ", ".join(sorted(set(base_forbidden_by)))
                + " (base_em_enforcement='hard_veto')."
            )
        elif vetoed_by:
            reasons.append(
                "Option is forbidden due to veto from EM(s): "
                + ", ".join(sorted(set(vetoed_by)))
            )
        else:
            reasons.append(
                "Option is forbidden because at least one EM issued a 'forbid' verdict."
            )
    else:
        reasons.append(f"Weighted average normative_score = {aggregated_score:.3f}.")

    metadata: Dict[str, object] = {
        "forbidden": forbidden,
        "forbidden_by": sorted(set(forbidden_by)),
        "vetoed_by": sorted(set(vetoed_by)),
        "base_forbidden_by": sorted(set(base_forbidden_by)),
        "raw_scores": raw_scores,
        "raw_verdicts": raw_verdicts,
        "governance_config": {
            "stakeholder_weights": cfg.stakeholder_weights,
            "em_weights": cfg.em_weights,
            "veto_ems": cfg.veto_ems,
            "min_score_threshold": cfg.min_score_threshold,
            "require_non_forbidden": cfg.require_non_forbidden,
            "tie_breaker": cfg.tie_breaker,
            "prefer_higher_uncertainty": cfg.prefer_higher_uncertainty,
            "base_em_ids": cfg.base_em_ids,
            "base_em_enforcement": cfg.base_em_enforcement.value,
        },
    }

    return EthicalJudgement(
        option_id=option_id,
        em_name="governance",
        stakeholder="multi_stakeholder",
        verdict=agg_verdict,
        normative_score=aggregated_score,
        reasons=reasons,
        metadata=metadata,
    )


def select_option(
    judgements_by_option: Dict[str, List[EthicalJudgement]],
    cfg: GovernanceConfig,
    *,
    candidate_ids: Optional[List[str]] = None,
    baseline_option_id: Optional[str] = None,
) -> DecisionOutcome:
    """
    Select a final option among candidates, given per-option judgements.

    Args:
        judgements_by_option:
            Mapping from option_id -> list of EthicalJudgement objects
            produced by various EMs.

        cfg:
            GovernanceConfig controlling aggregation, vetoes, and thresholds.

        candidate_ids:
            Optional explicit ordering of candidate option IDs.
            If None, the keys of judgements_by_option are used (sorted).

        baseline_option_id:
            Optional "status quo" or baseline option. Some tie-breaking
            strategies (e.g., 'status_quo') may prefer this option when
            scores are equal.

    Returns:
        DecisionOutcome summarizing aggregated judgements, ranking, and
        the selected option (if any).
    """
    if candidate_ids is None:
        candidate_ids = sorted(judgements_by_option.keys())

    aggregated: Dict[str, EthicalJudgement] = {}
    forbidden_options: List[str] = []

    # Aggregate per option.
    for opt_id in candidate_ids:
        judgements = judgements_by_option.get(opt_id, [])
        agg = aggregate_judgements(opt_id, judgements, cfg)
        aggregated[opt_id] = agg

        forbidden_flag = bool(agg.metadata.get("forbidden", False))
        if forbidden_flag:
            forbidden_options.append(opt_id)

    # Filter options by forbidden status and score threshold.
    eligible: List[Tuple[str, EthicalJudgement]] = []
    for opt_id in candidate_ids:
        agg = aggregated[opt_id]

        if bool(agg.metadata.get("forbidden", False)):
            continue

        if agg.normative_score < cfg.min_score_threshold:
            continue

        eligible.append((opt_id, agg))

    # If no eligible options remain, return a DecisionOutcome with None.
    if not eligible:
        rationale = (
            "No eligible options: all options were either forbidden under the "
            "governance rules (including foundational EM constraints where "
            f"applicable) or fell below the minimum score threshold "
            f"(min_score_threshold={cfg.min_score_threshold}). "
            f"Forbidden options: {forbidden_options or 'none'}."
        )
        return DecisionOutcome(
            selected_option_id=None,
            ranked_options=[],
            aggregated_judgements=aggregated,
            forbidden_options=forbidden_options,
            rationale=rationale,
        )

    # Sort eligible options by descending normative_score, then tie-break.
    # We maintain original candidate_ids order as secondary key for stability.
    index_by_id = {opt_id: idx for idx, opt_id in enumerate(candidate_ids)}

    def sort_key(item: Tuple[str, EthicalJudgement]) -> Tuple[float, float, float]:
        opt_id, agg = item
        score = agg.normative_score
        # negative index to preserve earlier candidates on ties
        base_key = (-score, index_by_id.get(opt_id, 0))

        # Optionally perturb tie-breaking using random or other rules.
        if cfg.tie_breaker == "random":
            # add a small random jitter for non-deterministic tie-breaking
            return (-score, random.random(), 0.0)
        return base_key + (0.0,)

    eligible.sort(key=sort_key)

    ranked_options = [opt_id for opt_id, _ in eligible]

    selected_option_id = ranked_options[0]

    # Special handling for 'status_quo' tie-breaker: if baseline is tied for
    # top score, prefer the baseline.
    if cfg.tie_breaker == "status_quo" and baseline_option_id is not None:
        # Find top score.
        top_score = eligible[0][1].normative_score
        # Check if baseline is among eligible with the same top score.
        for opt_id, agg in eligible:
            if (
                opt_id == baseline_option_id
                and abs(agg.normative_score - top_score) < 1e-9
            ):
                selected_option_id = baseline_option_id
                break

    rationale = (
        f"Selected option '{selected_option_id}' based on aggregated normative scores "
        f"and GovernanceConfig(min_score_threshold={cfg.min_score_threshold}, "
        f"tie_breaker={cfg.tie_breaker!r}, "
        f"base_em_ids={cfg.base_em_ids}, "
        f"base_em_enforcement={cfg.base_em_enforcement.value!r}). "
        f"Forbidden options: {forbidden_options or 'none'}."
    )

    return DecisionOutcome(
        selected_option_id=selected_option_id,
        ranked_options=ranked_options,
        aggregated_judgements=aggregated,
        forbidden_options=forbidden_options,
        rationale=rationale,
    )


__all__ = [
    "DecisionOutcome",
    "aggregate_judgements",
    "select_option",
]
