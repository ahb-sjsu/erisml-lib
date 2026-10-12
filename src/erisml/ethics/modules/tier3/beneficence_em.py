# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Beneficence-EM: Tier 3 advisory welfare module (Design Guide v0.1, section 4.4.1).

Purpose: promote welfare within the constraints set by higher tiers. Each option is scored
by its expected welfare, the benefit it secures net of the harm it brings, so that among
options equally safe and respectful of rights the one that does more good ranks higher.

Welfare is read onto dimension 0 of the canonical nine, "physical_harm/welfare"
(docs/moralvector_v2_architecture.md section 3): the vector's physical_harm under this
perspective is (1 + harm - benefit) / 2, so an option that secures more than it costs scores
below the neutral 0.5 and one that costs more than it secures above it. Without this reading
expected_benefit reaches no dimension, and no shipped module carried it into the ranking.

Advisory: it never vetoes.

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
    tier=3,
    default_weight=1.0,
    veto_capable=False,
    description="Beneficence: score options by expected welfare (benefit net of harm)",
    tags=["welfare", "beneficence"],
)
@dataclass
class BeneficenceEMV2(BaseEthicsModuleV2):
    """Advisory tier-3 module over expected benefit and harm."""

    em_name: str = "beneficence"
    stakeholder: str = "affected_parties"
    em_tier: int = 3

    def evaluate_vector(
        self, facts: EthicalFacts
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        c = facts.consequences
        welfare = c.expected_benefit - c.expected_harm  # in [-1, 1]
        vector = self.baseline_vector(facts)
        vector.physical_harm = (1.0 - welfare) / 2.0
        reasons = [
            f"Expected welfare {welfare:+.2f} (benefit {c.expected_benefit:.2f}, "
            f"harm {c.expected_harm:.2f})"
        ]
        if welfare > 0.5:
            verdict: Verdict = "strongly_prefer"
        elif welfare > 0.2:
            verdict = "prefer"
        elif welfare > -0.2:
            verdict = "neutral"
        else:
            verdict = "avoid"
        return verdict, vector, reasons, {"welfare": welfare}


__all__ = ["BeneficenceEMV2"]
