"""
geneva_base_em.py

Base and baseline "Geneva" ethics modules for DEME.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from erisml.ethics.facts import (
    EthicalFacts,
)
from erisml.ethics.judgement import EthicalJudgement
from erisml.ethics.modules.base import BaseEthicsModule

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GenevaBaseEM
# ---------------------------------------------------------------------------


@dataclass
class GenevaBaseEM(BaseEthicsModule):
    """
    Base class for DEME-style Ethics Modules with canonical verdict mapping.
    """

    em_name: str = "geneva_base"
    stakeholder: str = "unspecified"

    strongly_prefer_threshold: float = 0.8
    prefer_threshold: float = 0.6
    neutral_threshold: float = 0.4
    avoid_threshold: float = 0.2

    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate threshold configuration."""
        super().__post_init__()

        thresholds = (
            self.strongly_prefer_threshold,
            self.prefer_threshold,
            self.neutral_threshold,
            self.avoid_threshold,
        )

        if not all(0.0 <= t <= 1.0 for t in thresholds):
            raise ValueError(f"Thresholds must be in [0.0, 1.0], got {thresholds!r}")

    @staticmethod
    def clamp_score(score: float) -> float:
        if score < 0.0:
            return 0.0
        if score > 1.0:
            return 1.0
        return score

    def score_to_verdict(self, score: float) -> str:
        score = self.clamp_score(score)
        if score >= self.strongly_prefer_threshold:
            return "strongly_prefer"
        elif score >= self.prefer_threshold:
            return "prefer"
        elif score >= self.neutral_threshold:
            return "neutral"
        elif score >= self.avoid_threshold:
            return "avoid"
        else:
            return "forbid"

    def norm_bundle(
        self,
        score: float,
        reasons: Iterable[str] | None = None,
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> Tuple[float, str, Dict[str, Any]]:
        clamped = self.clamp_score(score)
        verdict = self.score_to_verdict(clamped)
        reasons_list: List[str] = list(reasons) if reasons is not None else []

        metadata: Dict[str, Any] = {
            "score": clamped,
            "verdict": verdict,
            "reasons": reasons_list,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return clamped, verdict, metadata


# ---------------------------------------------------------------------------
# GenevaBaselineEM
# ---------------------------------------------------------------------------


@dataclass
class GenevaBaselineEM(GenevaBaseEM):
    """
    Baseline 'Geneva' ethics module.
    """

    em_name: str = "geneva_baseline"
    stakeholder: str = "geneva_conventions"

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        rd = facts.rights_and_duties
        jf = facts.justice_and_fairness
        auto = facts.autonomy_and_agency
        priv = facts.privacy_and_data
        soc = facts.societal_and_environmental
        proc = facts.procedural_and_legitimacy
        epi = facts.epistemic_status
        cons = facts.consequences

        reasons: List[str] = []

        # Hard veto logic
        if rd.violates_rights or jf.discriminates_on_protected_attr:
            reasons.append("Option violates fundamental rights (Geneva hard veto).")
            if rd.violates_rights:
                reasons.append("• violates_rights = True")
            if jf.discriminates_on_protected_attr:
                reasons.append("• discriminates_on_protected_attr = True")

            metadata = {
                "kind": "geneva_hard_veto",
                "hard_veto": True,
                "reasons": reasons,
            }

            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="forbid",
                normative_score=0.0,
                reasons=reasons,
                metadata=metadata,
            )

        # Soft scoring logic
        score = 1.0

        if jf.exploits_vulnerable_population:
            score -= 0.25
            reasons.append("Exploits vulnerable population.")
        if jf.exacerbates_power_imbalance:
            score -= 0.15
            reasons.append("Exacerbates power imbalance.")
        if soc and soc.burden_on_vulnerable_groups > 0.5:
            score -= 0.15
            reasons.append("High burden on vulnerable groups.")

        if auto:
            if not auto.has_meaningful_choice:
                score -= 0.20
                reasons.append("Lacks meaningful choice.")
            if auto.coercion_or_undue_influence:
                score -= 0.20
                reasons.append("Coercion present.")

        if priv:
            score -= 0.30 * priv.privacy_invasion_level
            if not priv.data_minimization_respected:
                score -= 0.10
                reasons.append("Data minimization violated.")

        if proc:
            if not proc.followed_approved_procedure:
                score -= 0.15
                reasons.append("Approved procedure not followed.")

        if cons.expected_benefit < 0.3:
            score -= 0.05
            reasons.append("Low expected benefit.")

        # Epistemic
        epistemic_penalty = 0.0
        if epi:
            epistemic_penalty += 0.20 * epi.uncertainty_level
            if epi.evidence_quality == "low":
                epistemic_penalty += 0.15
                reasons.append("Low evidence quality.")

        multiplier = max(0.5, 1.0 - epistemic_penalty)
        score *= multiplier
        reasons.append(f"Epistemic multiplier: {multiplier:.2f}")

        # Final Bundle
        score, verdict, metadata = self.norm_bundle(
            score,
            reasons=reasons,
            extra_metadata={"epistemic_multiplier": multiplier},
        )

        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            verdict=verdict,  # type: ignore
            normative_score=score,
            reasons=reasons,
            metadata=metadata,
        )
