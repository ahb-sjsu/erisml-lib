"""
geneva_base_em.py

Base and baseline "Geneva" ethics modules for DEME.

Refactored for:
- Configurable weights (GenevaWeights)
- Modular scoring logic
- Type safety
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Optional

from erisml.ethics.facts import (
    AutonomyAndAgency,
    EpistemicStatus,
    EthicalFacts,
    PrivacyAndDataGovernance,
    ProceduralAndLegitimacy,
    SocietalAndEnvironmental,
)
from erisml.ethics.judgement import EthicalJudgement
from erisml.ethics.modules.base import BaseEthicsModule

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration: Weights & Penalties
# ---------------------------------------------------------------------------


@dataclass
class GenevaWeights:
    """
    Central configuration for Geneva scoring penalties.
    Positive values here represent penalties (subtracted from score).
    """

    # Fairness
    exploits_vulnerable: float = 0.25
    power_imbalance: float = 0.15
    burden_on_vulnerable: float = 0.15

    # Autonomy
    lacks_choice: float = 0.20
    coercion: float = 0.20
    no_withdrawal: float = 0.10
    manipulative_design: float = 0.10

    # Privacy
    privacy_invasion_multiplier: float = 0.30
    no_data_minimization: float = 0.10
    secondary_use_no_consent: float = 0.15
    excessive_retention: float = 0.10
    reid_risk_multiplier: float = 0.20

    # Societal
    societal_risk_multiplier: float = 0.20
    future_benefit_bonus_multiplier: float = 0.10  # This adds to score

    # Procedural
    bad_procedure: float = 0.15
    no_consultation: float = 0.10
    unexplainable: float = 0.05
    no_appeal: float = 0.05

    # Beneficence
    low_benefit_penalty: float = 0.05

    # Epistemic (Uncertainty)
    novelty_penalty: float = 0.15
    low_evidence_penalty: float = 0.15
    medium_evidence_penalty: float = 0.05
    uncertainty_multiplier: float = 0.20


# ---------------------------------------------------------------------------
# GenevaBaseEM (Abstract Base)
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
        super().__post_init__()
        self._validate_thresholds()

    def _validate_thresholds(self) -> None:
        thresholds = (
            self.strongly_prefer_threshold,
            self.prefer_threshold,
            self.neutral_threshold,
            self.avoid_threshold,
        )
        if not all(0.0 <= t <= 1.0 for t in thresholds):
            raise ValueError(f"Thresholds must be in [0.0, 1.0], got {thresholds}")

        if not (
            self.strongly_prefer_threshold
            >= self.prefer_threshold
            >= self.neutral_threshold
            >= self.avoid_threshold
        ):
            raise ValueError(
                "Thresholds must be monotonic: strongly >= prefer >= neutral >= avoid"
            )

    @staticmethod
    def clamp_score(score: float) -> float:
        return max(0.0, min(1.0, score))

    def score_to_verdict(self, score: float) -> str:
        score = self.clamp_score(score)
        if score >= self.strongly_prefer_threshold:
            return "strongly_prefer"
        if score >= self.prefer_threshold:
            return "prefer"
        if score >= self.neutral_threshold:
            return "neutral"
        if score >= self.avoid_threshold:
            return "avoid"
        return "forbid"

    def norm_bundle(
        self,
        score: float,
        reasons: Iterable[str] | None = None,
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> Tuple[float, str, Dict[str, Any]]:
        clamped = self.clamp_score(score)
        verdict = self.score_to_verdict(clamped)
        reasons_list = list(reasons) if reasons is not None else []

        metadata = {
            "score": clamped,
            "verdict": verdict,
            "reasons": reasons_list,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return clamped, verdict, metadata


# ---------------------------------------------------------------------------
# GenevaBaselineEM (Concrete Implementation)
# ---------------------------------------------------------------------------


@dataclass
class GenevaBaselineEM(GenevaBaseEM):
    """
    Baseline 'Geneva' ethics module.
    Enforces cross-cutting constraints using configurable weights.
    """

    em_name: str = "geneva_baseline"
    stakeholder: str = "geneva_conventions"
    weights: GenevaWeights = field(default_factory=GenevaWeights)

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        # 1. Check Hard Vetoes
        veto_result = self._check_hard_vetoes(facts)
        if veto_result:
            return veto_result

        # 2. Calculate Deductions
        score = 1.0
        reasons: List[str] = []

        score = self._apply_fairness(facts, score, reasons)
        score = self._apply_autonomy(facts, score, reasons)
        score = self._apply_privacy(facts, score, reasons)
        score = self._apply_societal(facts, score, reasons)
        score = self._apply_procedural(facts, score, reasons)
        score = self._apply_beneficence(facts, score, reasons)

        # 3. Apply Epistemic Multiplier (Uncertainty)
        score, multiplier = self._apply_epistemic(facts, score, reasons)

        # 4. Finalize
        final_score, verdict, metadata = self.norm_bundle(
            score, reasons=reasons, extra_metadata={"epistemic_multiplier": multiplier}
        )

        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            verdict=verdict,
            normative_score=final_score,
            reasons=reasons,
            metadata=metadata,
        )

    def _check_hard_vetoes(self, facts: EthicalFacts) -> Optional[EthicalJudgement]:
        rd = facts.rights_and_duties
        jf = facts.justice_and_fairness
        reasons = []

        if rd.violates_rights:
            reasons.append("• violates_rights = True")
        if jf.discriminates_on_protected_attr:
            reasons.append("• discriminates_on_protected_attr = True")

        if reasons:
            msg = "Option violates fundamental rights (Hard Veto)."
            reasons.insert(0, msg)
            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="forbid",
                normative_score=0.0,
                reasons=reasons,
                metadata={"hard_veto": True},
            )
        return None

    def _apply_fairness(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> float:
        jf = facts.justice_and_fairness
        soc = facts.societal_and_environmental

        if jf.exploits_vulnerable_population:
            score -= self.weights.exploits_vulnerable
            reasons.append("Exploits vulnerable population.")
        if jf.exacerbates_power_imbalance:
            score -= self.weights.power_imbalance
            reasons.append("Exacerbates power imbalance.")
        if soc and soc.burden_on_vulnerable_groups > 0.5:
            score -= self.weights.burden_on_vulnerable
            reasons.append("High burden on vulnerable groups.")
        return score

    def _apply_autonomy(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> float:
        auto = facts.autonomy_and_agency
        if not auto:
            return score

        if not auto.has_meaningful_choice:
            score -= self.weights.lacks_choice
            reasons.append("Lacks meaningful choice.")
        if auto.coercion_or_undue_influence:
            score -= self.weights.coercion
            reasons.append("Coercion present.")
        if not auto.can_withdraw_without_penalty:
            score -= self.weights.no_withdrawal
            reasons.append("Cannot withdraw without penalty.")
        if auto.manipulative_design_present:
            score -= self.weights.manipulative_design
            reasons.append("Manipulative design present.")
        return score

    def _apply_privacy(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> float:
        priv = facts.privacy_and_data
        if not priv:
            return score

        score -= self.weights.privacy_invasion_multiplier * priv.privacy_invasion_level

        if not priv.data_minimization_respected:
            score -= self.weights.no_data_minimization
            reasons.append("Data minimization violated.")
        if priv.secondary_use_without_consent:
            score -= self.weights.secondary_use_no_consent
            reasons.append("Secondary use without consent.")
        if priv.data_retention_excessive:
            score -= self.weights.excessive_retention
            reasons.append("Excessive data retention.")

        score -= self.weights.reid_risk_multiplier * priv.reidentification_risk
        return score

    def _apply_societal(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> float:
        soc = facts.societal_and_environmental
        if not soc:
            return score

        score -= self.weights.societal_risk_multiplier * soc.long_term_societal_risk
        score += (
            self.weights.future_benefit_bonus_multiplier
            * soc.benefits_to_future_generations
        )
        return score

    def _apply_procedural(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> float:
        proc = facts.procedural_and_legitimacy
        if not proc:
            return score

        if not proc.followed_approved_procedure:
            score -= self.weights.bad_procedure
            reasons.append("Did not follow procedure.")
        if not proc.stakeholders_consulted:
            score -= self.weights.no_consultation
            reasons.append("Stakeholders not consulted.")
        if not proc.decision_explainable_to_public:
            score -= self.weights.unexplainable
            reasons.append("Not explainable to public.")
        if not proc.contestation_available:
            score -= self.weights.no_appeal
            reasons.append("No contestation path.")
        return score

    def _apply_beneficence(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> float:
        if facts.consequences.expected_benefit < 0.3:
            score -= self.weights.low_benefit_penalty
            reasons.append("Expected benefit is very low.")
        return score

    def _apply_epistemic(
        self, facts: EthicalFacts, score: float, reasons: List[str]
    ) -> Tuple[float, float]:
        epi = facts.epistemic_status
        if not epi:
            return score, 1.0

        penalty = 0.0
        if epi.novel_situation_flag:
            penalty += self.weights.novelty_penalty
            reasons.append("Novel situation (cautious).")

        if epi.evidence_quality == "low":
            penalty += self.weights.low_evidence_penalty
            reasons.append("Low evidence quality.")
        elif epi.evidence_quality == "medium":
            penalty += self.weights.medium_evidence_penalty

        penalty += self.weights.uncertainty_multiplier * epi.uncertainty_level

        multiplier = max(0.5, 1.0 - penalty)

        if multiplier < 1.0:
            reasons.append(f"Epistemic multiplier: {multiplier:.2f}")

        return score * multiplier, multiplier
