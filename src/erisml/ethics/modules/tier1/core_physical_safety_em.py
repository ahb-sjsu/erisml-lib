# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
CorePhysicalSafety-EM: Tier 1 binding safety module (Design Guide v0.1, section 4.2.1).

Purpose: prevent immediate physical harm. An option is vetoed when its predicted harm
exceeds the configured threshold and a safer feasible alternative exists. Under low
confidence the threshold becomes stricter.

"A safer feasible alternative exists" is a property of the candidate set, not of one
option, so the module judges the set (``judge_set``); judged alone (``judge``) an option has
no known alternative and is not vetoed, only scored.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from erisml.ethics.facts import EthicalFacts
from erisml.ethics.judgement import EthicalJudgementV2, Verdict
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.modules.registry import EMRegistry


@EMRegistry.register(
    tier=1,
    default_weight=5.0,
    veto_capable=True,
    description="Core physical safety: veto harm above threshold when a safer option exists",
    tags=["safety", "physical", "harm"],
)
@dataclass
class CorePhysicalSafetyEMV2(BaseEthicsModuleV2):
    """Binding tier-1 module over predicted physical harm and epistemic confidence."""

    em_name: str = "core_physical_safety"
    stakeholder: str = "affected_parties"
    em_tier: int = 1

    harm_veto_threshold: float = 0.5
    """Predicted harm above which an option is vetoed if a safer option exists."""

    low_confidence_strictness: float = 0.5
    """How much uncertainty tightens the threshold: threshold * (1 - strictness * u), with u
    the facts' uncertainty level, and u at least 0.5 when evidence quality is low."""

    def threshold(self, facts: EthicalFacts) -> float:
        es = facts.epistemic_status
        u = 0.0
        if es is not None:
            u = es.uncertainty_level
            if es.evidence_quality == "low":
                u = max(u, 0.5)
        return self.harm_veto_threshold * (1.0 - self.low_confidence_strictness * u)

    def evaluate_vector(
        self, facts: EthicalFacts
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        return self._assess(facts, safer=None)

    def judge_set(
        self, options: Sequence[EthicalFacts]
    ) -> Dict[str, EthicalJudgementV2]:
        """Judge each option against the others: the safer feasible alternatives of an option
        are the other candidates whose own predicted harm is lower and within their own
        threshold."""
        out: Dict[str, EthicalJudgementV2] = {}
        for f in options:
            harm = f.consequences.expected_harm
            safer = [
                o.option_id
                for o in options
                if o.option_id != f.option_id
                and o.consequences.expected_harm < harm
                and o.consequences.expected_harm <= self.threshold(o)
            ]
            verdict, vector, reasons, metadata = self._assess(f, safer=safer)
            out[f.option_id] = self._make_judgement_v2(
                facts=f,
                verdict=verdict,
                moral_vector=vector,
                reasons=reasons,
                metadata=metadata,
            )
        return out

    def _assess(
        self, facts: EthicalFacts, safer
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        vector = self.baseline_vector(facts)
        harm = facts.consequences.expected_harm
        limit = self.threshold(facts)
        reasons: List[str] = []
        metadata: Dict[str, Any] = {"harm": harm, "threshold": limit}
        if safer is not None:
            metadata["safer_alternatives"] = list(safer)

        if harm > limit and safer:
            vector.veto_flags = ["PHYSICAL_HARM_ABOVE_THRESHOLD"]
            vector.reason_codes = list(vector.reason_codes) + [
                "safer_alternative_exists"
            ]
            reasons.append(
                f"Predicted harm {harm:.2f} exceeds {limit:.2f} and safer options exist: "
                + ", ".join(safer)
            )
            return "forbid", vector, reasons, metadata
        if harm > limit:
            reasons.append(
                f"Predicted harm {harm:.2f} exceeds {limit:.2f}; no safer option is known"
            )
            return "avoid", vector, reasons, metadata
        if harm < 0.2:
            return "strongly_prefer", vector, reasons, metadata
        return "prefer", vector, reasons, metadata


__all__ = ["CorePhysicalSafetyEMV2"]
