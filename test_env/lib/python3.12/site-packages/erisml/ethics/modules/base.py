"""
Base interfaces and helpers for ethics modules (EMs).

Ethics modules consume EthicalFacts and emit EthicalJudgement objects.
They should implement *purely normative* reasoning over EthicalFacts,
without accessing raw domain data, sensors, or models.

Version: 0.2 (EthicalDomains update)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable, List, Dict, Any, Optional

from ..facts import EthicalFacts
from ..judgement import EthicalJudgement, Verdict


@runtime_checkable
class EthicsModule(Protocol):
    """
    Protocol for all ethics modules.

    Implementations may be simple rule-based systems, scoring functions,
    logic programs, or model-based evaluators, but they MUST:

    - Accept only EthicalFacts as input.
    - Return EthicalJudgement as output.
    """

    em_name: str
    """Identifier for this module (e.g., 'case_study_1_triage')."""

    stakeholder: str
    """Stakeholder whose perspective this module encodes."""

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        """
        Evaluate a single candidate option described by EthicalFacts.

        Implementations should:
        - respect hard constraints (e.g., rights violations),
        - compute a normative_score in [0, 1],
        - choose an appropriate verdict label,
        - provide human-readable reasons and machine-readable metadata.
        """
        ...


@dataclass
class BaseEthicsModule:
    """
    Convenience base class for ethics modules.

    Subclasses should implement `evaluate(self, facts: EthicalFacts)` and
    use `_make_judgement(...)` to construct the final EthicalJudgement.

    Example:

        class CaseStudy1TriageEM(BaseEthicsModule):
            stakeholder: str = "patients_and_public"

            def evaluate(self, facts: EthicalFacts) -> Tuple[Verdict, float, List[str], Dict[str, Any]]:
                # ... compute score, verdict, reasons, metadata ...
                return verdict, score, reasons, metadata
    """

    em_name: Optional[str] = None
    """
    Name/identifier for this EM. Defaults to the class name if not provided.
    """

    stakeholder: str = "unspecified"
    """
    Stakeholder perspective this EM purports to represent.
    """

    def __post_init__(self) -> None:
        if self.em_name is None:
            self.em_name = self.__class__.__name__

    # Public API compatible with EthicsModule
    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        """
        Default implementation of the EthicsModule.judge interface.

        Delegates to `evaluate`, which subclasses must implement.
        """
        verdict, score, reasons, metadata = self.evaluate(facts)
        return self._make_judgement(
            facts=facts,
            verdict=verdict,
            normative_score=score,
            reasons=reasons,
            metadata=metadata,
        )

    # Subclasses MUST implement this
    def evaluate(
        self,
        facts: EthicalFacts,
    ) -> tuple[Verdict, float, List[str], Dict[str, Any]]:
        """
        Core normative logic for the module.

        Must return:
        - verdict: one of the Verdict literals
        - normative_score: float in [0, 1]
        - reasons: list of human-readable explanation strings
        - metadata: dict of machine-readable diagnostics

        This method should operate *only* on EthicalFacts.
        """
        raise NotImplementedError("Subclasses must implement evaluate().")

    # Helper for constructing EthicalJudgement
    def _make_judgement(
        self,
        facts: EthicalFacts,
        verdict: Verdict,
        normative_score: float,
        reasons: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EthicalJudgement:
        """
        Helper to create an EthicalJudgement with consistent fields.
        """
        if metadata is None:
            metadata = {}

        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name or self.__class__.__name__,
            stakeholder=self.stakeholder,
            verdict=verdict,
            normative_score=normative_score,
            reasons=reasons,
            metadata=metadata,
        )


__all__ = [
    "EthicsModule",
    "BaseEthicsModule",
]
