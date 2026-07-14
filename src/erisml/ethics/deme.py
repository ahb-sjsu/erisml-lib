"""
DEME: Democratic Ethics Module Engine
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional  # noqa: F401


@dataclass
class EthicalJudgement:
    verdict: str
    confidence: float
    metadata: Dict[str, Any]


class DEME:
    """
    Main entry point for the Democratic Ethics Module Engine.
    """

    def __init__(self, profile_path: Optional[str] = None):
        self.profile_path = profile_path

    def evaluate(self, context: Any) -> EthicalJudgement:
        """Evaluate a context.

        If the context carries a maxim (an ``EthicalFacts`` with a ``.maxim``,
        or a ``Maxim`` directly), the deontic universalizability gate is applied
        and a failing maxim yields a FORBID verdict. Otherwise ALLOW (the
        full tensor/module pipeline lives in ``layers.pipeline.DEMEPipeline``).
        """
        from erisml.ethics.deontic_gate import evaluate_maxim
        from erisml.ethics.facts import Maxim

        maxim = (
            context if isinstance(context, Maxim) else getattr(context, "maxim", None)
        )
        gate = evaluate_maxim(maxim)
        if gate.vetoed:
            return EthicalJudgement(
                verdict="FORBID",
                confidence=0.9,
                metadata={
                    "deontic_gate": gate.reason,
                    "contradiction_type": gate.contradiction_type,
                    "action_kind": gate.action_kind,
                },
            )
        return EthicalJudgement(verdict="ALLOW", confidence=1.0, metadata={})
