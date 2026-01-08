# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
AutonomyConsentEMV2: Rights/Fairness module for autonomy and consent.

This is a Tier 2 EM that evaluates options based on respect for
autonomy and informed consent.

Version: 2.0.0 (DEME 2.0)
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
    description="Autonomy and consent evaluation",
    tags=["rights", "autonomy", "consent"],
)
@dataclass
class AutonomyConsentEMV2(BaseEthicsModuleV2):
    """
    Rights/Fairness EM for autonomy and consent.

    Evaluates:
    - Meaningful choice availability
    - Coercion or undue influence
    - Withdrawal without penalty
    - Manipulative design patterns

    Vetoes on:
    - Severe coercion combined with no consent
    """

    em_name: str = "autonomy_consent"
    stakeholder: str = "affected_parties"
    em_tier: int = 2

    # Configuration
    coercion_veto_threshold: float = 0.3
    """Autonomy score below which to veto."""

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        """Evaluate facts and return MoralVector-based judgement."""
        veto_flags: List[str] = []
        reason_codes: List[str] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {}

        # Start with baseline
        autonomy_score = 1.0

        # Check autonomy-related facts
        if facts.autonomy_and_agency is not None:
            aa = facts.autonomy_and_agency

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

        # Check consent
        if not facts.rights_and_duties.has_valid_consent:
            autonomy_score *= 0.5
            reason_codes.append("no_consent")
            reasons.append("Valid consent not obtained")

        # Check for veto
        if autonomy_score < self.coercion_veto_threshold:
            veto_flags.append("AUTONOMY_VIOLATION")
            reasons.append("Severe autonomy violation")

        # Determine verdict
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

        # Build moral vector
        moral_vector = MoralVector(
            physical_harm=facts.consequences.expected_harm,
            rights_respect=1.0 if facts.rights_and_duties.has_valid_consent else 0.5,
            fairness_equity=0.8,  # Not this EM's focus
            autonomy_respect=autonomy_score,
            legitimacy_trust=0.8,  # Not this EM's focus
            epistemic_quality=0.8,
            veto_flags=veto_flags,
            reason_codes=reason_codes,
        )

        metadata["autonomy_score"] = autonomy_score

        return verdict, moral_vector, reasons, metadata


__all__ = [
    "AutonomyConsentEMV2",
]
