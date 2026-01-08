# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
GenevaEMV2: Constitutional ethics module based on Geneva conventions.

This is a Tier 0 (Constitutional) EM that cannot be disabled and
always has veto capability. It enforces fundamental constraints on
rights violations, discrimination, and rule violations.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from erisml.ethics.facts import EthicalFacts
from erisml.ethics.judgement import Verdict
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.modules.registry import EMRegistry


@EMRegistry.register(
    tier=0,
    default_weight=10.0,
    veto_capable=True,
    description="Geneva convention and fundamental rights constraints",
    tags=["constitutional", "rights", "geneva"],
)
@dataclass
class GenevaEMV2(BaseEthicsModuleV2):
    """
    Constitutional EM enforcing Geneva convention principles.

    Hard vetoes on:
    - Rights violations
    - Discrimination on protected attributes
    - Explicit rule violations

    Penalties on:
    - Missing consent
    - Role duty conflicts
    - Vulnerability exploitation
    """

    em_name: str = "geneva_constitutional"
    stakeholder: str = "universal"
    em_tier: int = 0

    # Configuration
    strict_consent: bool = True
    """Require valid consent for non-veto pass."""

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Fast veto check for reflex layer.

        Returns True if option should be vetoed immediately.
        """
        # Check hard veto conditions
        if facts.rights_and_duties.violates_rights:
            return True
        if facts.justice_and_fairness.discriminates_on_protected_attr:
            return True
        if facts.rights_and_duties.violates_explicit_rule:
            return True
        return False

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        """Evaluate facts and return MoralVector-based judgement."""
        veto_flags: List[str] = []
        reason_codes: List[str] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {}

        # Start with baseline vector
        physical_harm = facts.consequences.expected_harm
        rights_respect = 1.0
        fairness_equity = 1.0
        autonomy_respect = 1.0
        legitimacy_trust = 1.0
        epistemic_quality = 1.0

        # Check hard vetoes
        if facts.rights_and_duties.violates_rights:
            rights_respect = 0.0
            veto_flags.append("RIGHTS_VIOLATION")
            reason_codes.append("rights_violated")
            reasons.append("Fundamental rights violation detected")

        if facts.justice_and_fairness.discriminates_on_protected_attr:
            fairness_equity = 0.0
            veto_flags.append("DISCRIMINATION")
            reason_codes.append("protected_attr_discrimination")
            reasons.append("Discrimination on protected attributes")

        if facts.rights_and_duties.violates_explicit_rule:
            legitimacy_trust = 0.0
            veto_flags.append("RULE_VIOLATION")
            reason_codes.append("explicit_rule_violated")
            reasons.append("Explicit rule or regulation violation")

        # Check soft constraints (penalties but not vetoes)
        if not facts.rights_and_duties.has_valid_consent:
            if self.strict_consent:
                autonomy_respect *= 0.5
            reason_codes.append("consent_missing")
            reasons.append("Valid consent not present")

        if facts.rights_and_duties.role_duty_conflict:
            legitimacy_trust *= 0.7
            reason_codes.append("role_duty_conflict")
            reasons.append("Role or duty conflict detected")

        if facts.justice_and_fairness.exploits_vulnerable_population:
            fairness_equity *= 0.5
            reason_codes.append("exploits_vulnerable")
            reasons.append("Exploits vulnerable population")

        if facts.justice_and_fairness.exacerbates_power_imbalance:
            fairness_equity *= 0.8
            reason_codes.append("power_imbalance")
            reasons.append("Exacerbates power imbalance")

        # Epistemic quality from facts
        if facts.epistemic_status is not None:
            es = facts.epistemic_status
            epistemic_quality = 1.0 - es.uncertainty_level
            if es.evidence_quality == "low":
                epistemic_quality *= 0.5
            elif es.evidence_quality == "medium":
                epistemic_quality *= 0.8

        # Determine verdict
        if veto_flags:
            verdict: Verdict = "forbid"
        elif all(
            [
                rights_respect > 0.7,
                fairness_equity > 0.7,
                legitimacy_trust > 0.7,
            ]
        ):
            if physical_harm < 0.2:
                verdict = "strongly_prefer"
            else:
                verdict = "prefer"
        elif all(
            [
                rights_respect > 0.5,
                fairness_equity > 0.5,
                legitimacy_trust > 0.5,
            ]
        ):
            verdict = "neutral"
        else:
            verdict = "avoid"

        # Build moral vector
        moral_vector = MoralVector(
            physical_harm=physical_harm,
            rights_respect=rights_respect,
            fairness_equity=fairness_equity,
            autonomy_respect=autonomy_respect,
            legitimacy_trust=legitimacy_trust,
            epistemic_quality=epistemic_quality,
            veto_flags=veto_flags,
            reason_codes=reason_codes,
        )

        metadata["hard_veto"] = len(veto_flags) > 0

        return verdict, moral_vector, reasons, metadata


__all__ = [
    "GenevaEMV2",
]
