"""
geneva_base_em.py

Base and baseline "Geneva" ethics modules for DEME.

- GenevaBaseEM: convenience base class providing canonical score→verdict
  mapping and helpers for building metadata.
- GenevaBaselineEM: concrete EM that enforces cross-cutting "Geneva-style"
  constraints (rights, non-discrimination, autonomy/consent, privacy,
  societal impact, procedural legitimacy, and epistemic caution).

These modules are intended to be *domain-agnostic* baselines that can be
used as "base EMs" in DEME governance profiles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Tuple, cast

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
# GenevaBaseEM
# ---------------------------------------------------------------------------


@dataclass
class GenevaBaseEM(BaseEthicsModule):
    """
    Base class for DEME-style Ethics Modules with canonical verdict mapping.

    Responsibilities
    ----------------
    - Provide a mapping from a normative score in [0.0, 1.0] to a discrete
      verdict label.
    - Clamp and validate scores to stay in [0.0, 1.0].
    - Offer helper utilities for constructing metadata dictionaries and
      logging internal decisions.

    Subclasses are expected to implement `judge(...)` and may optionally
    override the threshold values if they want different semantics.
    """

    em_name: str = "geneva_base"
    stakeholder: str = "unspecified"

    strongly_prefer_threshold: float = 0.8
    prefer_threshold: float = 0.6
    neutral_threshold: float = 0.4
    avoid_threshold: float = 0.2

    # Extra free-form configuration that subclasses can use if they want.
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
            raise ValueError(
                f"{self.__class__.__name__}: all thresholds must be in [0.0, 1.0], "
                f"got {thresholds!r}"
            )

        if not (
            self.strongly_prefer_threshold
            >= self.prefer_threshold
            >= self.neutral_threshold
            >= self.avoid_threshold
        ):
            raise ValueError(
                f"{self.__class__.__name__}: thresholds must satisfy "
                "strongly_prefer >= prefer >= neutral >= avoid; "
                f"got strongly_prefer={self.strongly_prefer_threshold}, "
                f"prefer={self.prefer_threshold}, "
                f"neutral={self.neutral_threshold}, "
                f"avoid={self.avoid_threshold}"
            )

        logger.debug(
            "%s initialised with thresholds: strongly_prefer=%.3f, "
            "prefer=%.3f, neutral=%.3f, avoid=%.3f",
            self.__class__.__name__,
            self.strongly_prefer_threshold,
            self.prefer_threshold,
            self.neutral_threshold,
            self.avoid_threshold,
        )

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    @staticmethod
    def clamp_score(score: float) -> float:
        """
        Clamp a raw normative score into [0.0, 1.0].

        This is deliberately forgiving: it logs when clamping occurs but does
        not raise, so that minor numerical drift or modelling differences do
        not crash agents in production.
        """
        if score < 0.0:
            logger.debug("Clamping score %.4f up to 0.0", score)
            return 0.0
        if score > 1.0:
            logger.debug("Clamping score %.4f down to 1.0", score)
            return 1.0
        return score

    def score_to_verdict(self, score: float) -> str:
        """
        Map a normative score in [0.0, 1.0] to a discrete verdict.

        Default mapping:

            [strongly_prefer_threshold, 1.0]              -> "strongly_prefer"
            [prefer_threshold, strongly_prefer_threshold) -> "prefer"
            [neutral_threshold, prefer_threshold)         -> "neutral"
            [avoid_threshold, neutral_threshold)          -> "avoid"
            [0.0, avoid_threshold)                        -> "forbid"

        Subclasses can override either the thresholds or this method for
        more specialised behaviour.
        """
        score = self.clamp_score(score)

        if score >= self.strongly_prefer_threshold:
            verdict = "strongly_prefer"
        elif score >= self.prefer_threshold:
            verdict = "prefer"
        elif score >= self.neutral_threshold:
            verdict = "neutral"
        elif score >= self.avoid_threshold:
            verdict = "avoid"
        else:
            verdict = "forbid"

        logger.debug(
            "%s mapped score %.4f to verdict '%s'",
            self.__class__.__name__,
            score,
            verdict,
        )
        return verdict

    # ------------------------------------------------------------------
    # Convenience bundle for subclasses
    # ------------------------------------------------------------------

    def norm_bundle(
        self,
        score: float,
        reasons: Iterable[str] | None = None,
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> Tuple[float, str, Dict[str, Any]]:
        """
        Convenience helper for subclasses inside `judge(...)`.

        Returns (clamped_score, verdict, metadata_dict).
        """
        clamped = self.clamp_score(score)
        verdict = self.score_to_verdict(clamped)

        reasons_list: List[str] = list(reasons) if reasons is not None else []

        metadata: Dict[str, Any] = {
            "score": clamped,
            "verdict": verdict,
            "reasons": reasons_list,
        }

        if extra_metadata:
            for key, value in extra_metadata.items():
                if key in metadata:
                    logger.debug(
                        "%s: extra_metadata overwriting key '%s' " "(old=%r, new=%r)",
                        self.__class__.__name__,
                        key,
                        metadata[key],
                        value,
                    )
                metadata[key] = value

        return clamped, verdict, metadata


# ---------------------------------------------------------------------------
# GenevaBaselineEM
# ---------------------------------------------------------------------------


@dataclass
class GenevaBaselineEM(GenevaBaseEM):
    """
    Baseline 'Geneva' ethics module.

    Role:
      - Provide a cross-cutting baseline over rights, fairness,
        autonomy/consent, privacy, societal impact, procedural legitimacy,
        and epistemic caution.
      - Issue a hard veto when fundamental rights or non-discrimination
        constraints are violated.
      - Otherwise, produce a conservative, governance-oriented score that
        other EMs and GovernanceConfig can treat as a baseline.
    """

    em_name: str = "geneva_baseline"
    stakeholder: str = "geneva_conventions"

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        rd = facts.rights_and_duties
        jf = facts.justice_and_fairness
        auto: AutonomyAndAgency | None = facts.autonomy_and_agency
        priv: PrivacyAndDataGovernance | None = facts.privacy_and_data
        soc: SocietalAndEnvironmental | None = facts.societal_and_environmental
        proc: ProceduralAndLegitimacy | None = facts.procedural_and_legitimacy
        epi: EpistemicStatus | None = facts.epistemic_status
        cons = facts.consequences

        reasons: List[str] = []

        # --------------------------------------------------------------
        # Hard veto: fundamental rights and non-discrimination
        # --------------------------------------------------------------
        if rd.violates_rights or jf.discriminates_on_protected_attr:
            reasons.append(
                "Option violates fundamental rights and/or discriminates on "
                "protected attributes (Geneva baseline hard veto)."
            )
            if rd.violates_rights:
                reasons.append("• violates_rights = True")
            if jf.discriminates_on_protected_attr:
                reasons.append("• discriminates_on_protected_attr = True")

            metadata = {
                "kind": "geneva_hard_veto",
                "hard_veto": True,
                "forbidden_by": "geneva_baseline",
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

        # --------------------------------------------------------------
        # Soft scoring: start at 1.0 and subtract penalties
        # --------------------------------------------------------------
        score = 1.0

        # Fairness / protection for vulnerable groups
        if jf.exploits_vulnerable_population:
            score -= 0.25
            reasons.append("Exploits vulnerable population.")
        if jf.exacerbates_power_imbalance:
            score -= 0.15
            reasons.append("Exacerbates power imbalance.")
        if soc is not None and soc.burden_on_vulnerable_groups > 0.5:
            score -= 0.15
            reasons.append("High burden on vulnerable groups.")

        # Autonomy + consent
        if auto is not None:
            if not auto.has_meaningful_choice:
                score -= 0.20
                reasons.append("Lacks meaningful choice for affected persons.")
            if auto.coercion_or_undue_influence:
                score -= 0.20
                reasons.append("Coercion or undue influence is present.")
            if not auto.can_withdraw_without_penalty:
                score -= 0.10
                reasons.append("Cannot withdraw without penalty.")
            if auto.manipulative_design_present:
                score -= 0.10
                reasons.append("Manipulative / dark-pattern design present.")

        # Privacy + data governance
        if priv is not None:
            score -= 0.30 * priv.privacy_invasion_level
            if not priv.data_minimization_respected:
                score -= 0.10
                reasons.append("Data minimization is not respected.")
            if priv.secondary_use_without_consent:
                score -= 0.15
                reasons.append("Secondary data use without consent.")
            if priv.data_retention_excessive:
                score -= 0.10
                reasons.append("Excessive data retention.")
            score -= 0.20 * priv.reidentification_risk

        # Societal and environmental
        if soc is not None:
            score -= 0.20 * soc.long_term_societal_risk
            score += 0.10 * soc.benefits_to_future_generations

        # Procedural legitimacy
        if proc is not None:
            if not proc.followed_approved_procedure:
                score -= 0.15
                reasons.append("Did not follow approved procedure.")
            if not proc.stakeholders_consulted:
                score -= 0.10
                reasons.append("Stakeholders not meaningfully consulted.")
            if not proc.decision_explainable_to_public:
                score -= 0.05
                reasons.append("Decision not explainable to the public.")
            if not proc.contestation_available:
                score -= 0.05
                reasons.append("No meaningful contestation / appeal path.")

        # Mild beneficence nudge: very low expected benefit gets a small penalty
        if cons.expected_benefit < 0.3:
            score -= 0.05
            reasons.append("Expected benefit is very low.")

        # --------------------------------------------------------------
        # Epistemic caution: more uncertainty → more conservative
        # --------------------------------------------------------------
        epistemic_penalty = 0.0
        if epi is not None:
            if epi.novel_situation_flag:
                epistemic_penalty += 0.15
                reasons.append("Novel situation → Geneva baseline is more cautious.")
            if epi.evidence_quality == "low":
                epistemic_penalty += 0.15
                reasons.append("Low evidence quality.")
            elif epi.evidence_quality == "medium":
                epistemic_penalty += 0.05

            epistemic_penalty += 0.20 * epi.uncertainty_level

        multiplier = max(0.5, 1.0 - epistemic_penalty)
        score *= multiplier

        reasons.append(
            "Epistemic adjustment: "
            f"multiplier={multiplier:.2f} (penalty={epistemic_penalty:.2f})."
        )

        # Clamp, map to verdict, pack metadata using GenevaBaseEM helper
        score, verdict, metadata = self.norm_bundle(
            score,
            reasons=reasons,
            extra_metadata={
                "hard_veto": False,
                "epistemic_multiplier": multiplier,
            },
        )

        reasons_list = cast(List[str], metadata["reasons"])
        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            verdict=verdict,  # type: ignore
            normative_score=score,
            reasons=reasons_list,
            metadata=metadata,
        )  # type: ignore
