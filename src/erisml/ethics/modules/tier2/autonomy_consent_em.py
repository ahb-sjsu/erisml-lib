# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
AutonomyConsentEMV2: Tier 2 module for autonomy and consent (Design Guide v0.1, 4.3.1).

Purpose: respect informed consent and refusals, with limited emergency overrides.

- Binding: an option the affected person has refused or not consented to is vetoed when
  that person is competent (an unknown capacity counts as competent), except when the
  emergency override holds: the hazard is imminent and grave (urgency at or above
  ``emergency_urgency``), the option is necessary to prevent severe harm (its expected
  benefit at or above ``necessity_benefit``), and governance allows the override
  (``allow_emergency_override``, AutonomyPolicy.allow_override_in_high_stakes). An override
  is annotated (``consent_override_reason``), and so is whether governance asks a human to
  confirm it.
- A person without capacity (``decision_capacity="impaired"``) does not bind by refusal;
  the missing consent still lowers the autonomy score.
- Coercion, manipulation, a missing meaningful choice and a withdrawal penalty lower the
  score, and a score below ``coercion_veto_threshold`` vetoes, as before.

Version: 2.1.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from erisml.ethics.facts import EthicalFacts
from erisml.ethics.judgement import Verdict
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.modules.registry import EMRegistry


@EMRegistry.register(
    tier=2,
    default_weight=2.0,
    veto_capable=True,
    description="Autonomy and consent: refusals bind, with limited emergency overrides",
    tags=["rights", "autonomy", "consent"],
)
@dataclass
class AutonomyConsentEMV2(BaseEthicsModuleV2):
    """Rights tier module for consent, refusal, capacity and coercion."""

    em_name: str = "autonomy_consent"
    stakeholder: str = "affected_parties"
    em_tier: int = 2

    coercion_veto_threshold: float = 0.3
    """Autonomy score below which to veto."""

    allow_emergency_override: bool = True
    """Governance allows the emergency override (AutonomyPolicy.allow_override_in_high_stakes)."""

    override_requires_human_confirmation: bool = True
    """Annotated on an override (AutonomyPolicy.override_requires_human_confirmation)."""

    emergency_urgency: float = 0.75
    """Urgency at or above which the hazard counts as imminent and grave."""

    necessity_benefit: float = 0.75
    """Expected benefit at or above which the option counts as necessary to prevent severe
    harm."""

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        veto_flags: List[str] = []
        reason_codes: List[str] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {}

        autonomy_score = 1.0
        aa = facts.autonomy_and_agency
        if aa is not None:
            if aa.coercion_or_undue_influence:
                autonomy_score *= 0.2
                reason_codes.append("coercion")
                reasons.append("Coercion or undue influence detected")
            if aa.manipulative_design_present:
                autonomy_score *= 0.4
                reason_codes.append("manipulative_design")
                reasons.append("Manipulative design patterns present")
            if not aa.has_meaningful_choice:
                autonomy_score *= 0.6
                reason_codes.append("no_meaningful_choice")
                reasons.append("No meaningful choice available")
            if not aa.can_withdraw_without_penalty:
                autonomy_score *= 0.8
                reason_codes.append("withdrawal_penalty")
                reasons.append("Cannot withdraw without penalty")
        capacity = getattr(aa, "decision_capacity", None) if aa is not None else None
        metadata["decision_capacity"] = capacity or "unknown"

        if not facts.rights_and_duties.has_valid_consent:
            autonomy_score *= 0.5
            reason_codes.append("no_consent")
            reasons.append("Valid consent not obtained")
            if capacity != "impaired":
                c = facts.consequences
                emergency = (
                    self.allow_emergency_override
                    and c.urgency >= self.emergency_urgency
                    and c.expected_benefit >= self.necessity_benefit
                )
                if emergency:
                    metadata["consent_override_reason"] = (
                        f"imminent grave hazard (urgency {c.urgency:.2f}) and the option "
                        f"is necessary to prevent severe harm (benefit "
                        f"{c.expected_benefit:.2f})"
                    )
                    metadata["requires_human_confirmation"] = (
                        self.override_requires_human_confirmation
                    )
                    reason_codes.append("consent_override")
                    reasons.append("Emergency override of a refusal or missing consent")
                else:
                    veto_flags.append("CONSENT_REFUSED_OR_ABSENT")
                    reasons.append(
                        "A competent person has refused or not consented, and no "
                        "emergency override applies"
                    )
            else:
                reason_codes.append("no_capacity")
                reasons.append(
                    "The affected person lacks capacity; refusal does not bind"
                )

        if autonomy_score < self.coercion_veto_threshold:
            veto_flags.append("AUTONOMY_VIOLATION")
            reasons.append("Severe autonomy violation")

        if veto_flags:
            verdict: Verdict = "forbid"
        elif autonomy_score > 0.8:
            verdict = "strongly_prefer"
        elif autonomy_score > 0.6:
            verdict = "prefer"
        elif autonomy_score > 0.4:
            verdict = "neutral"
        else:
            verdict = "avoid"

        # the whole facts vector, with this perspective's reading of autonomy
        moral_vector = self.baseline_vector(facts)
        moral_vector.autonomy_respect = autonomy_score
        moral_vector.veto_flags = veto_flags
        moral_vector.reason_codes = list(
            dict.fromkeys(list(moral_vector.reason_codes) + reason_codes)
        )
        metadata["autonomy_score"] = autonomy_score
        return verdict, moral_vector, reasons, metadata


__all__ = [
    "AutonomyConsentEMV2",
]
