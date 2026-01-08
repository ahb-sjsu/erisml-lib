"""
Base interfaces and helpers for ethics modules (EMs).

Ethics modules consume EthicalFacts and emit EthicalJudgement objects.
They should implement *purely normative* reasoning over EthicalFacts,
without accessing raw domain data, sensors, or models.

Version: 2.0.0 (DEME 2.0 - adds EthicsModuleV2, BaseEthicsModuleV2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable, List, Dict, Any, Optional, Tuple

from ..facts import EthicalFacts
from ..judgement import (
    EthicalJudgement,
    EthicalJudgementV2,
    Verdict,
    judgement_v1_to_v2,
)
from ..moral_vector import MoralVector


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


# =============================================================================
# DEME 2.0: EthicsModuleV2 with MoralVector
# =============================================================================


@runtime_checkable
class EthicsModuleV2(Protocol):
    """
    DEME 2.0 protocol for ethics modules returning MoralVector.

    This is the preferred interface for new EMs. It provides:
    - Multi-dimensional moral assessment via MoralVector
    - Tier classification for governance priority
    - Optional reflex layer check for fast veto
    """

    em_name: str
    """Identifier for this module."""

    stakeholder: str
    """Stakeholder whose perspective this module encodes."""

    em_tier: int
    """
    Tier classification (0-4):
    - 0: Constitutional (non-removable, hard veto)
    - 1: Core Safety (collision, physical harm)
    - 2: Rights/Fairness (autonomy, consent, allocation)
    - 3: Soft Values (beneficence, environment)
    - 4: Meta-Governance (pattern guard, profile integrity)
    """

    def judge(self, facts: EthicalFacts) -> EthicalJudgementV2:
        """
        Evaluate a single candidate option described by EthicalFacts.

        Returns EthicalJudgementV2 with MoralVector and tier info.
        """
        ...

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Fast veto check for reflex layer (<100μs target).

        Returns:
            True if option should be vetoed.
            False if option passes reflex check.
            None if this EM does not participate in reflex layer.
        """
        ...


@dataclass
class BaseEthicsModuleV2:
    """
    DEME 2.0 base class for ethics modules with MoralVector support.

    Subclasses should implement `evaluate_vector(self, facts: EthicalFacts)`
    which returns (Verdict, MoralVector, reasons, metadata).

    Example:

        @dataclass
        class GenevaEMV2(BaseEthicsModuleV2):
            em_name: str = "geneva_constitutional"
            stakeholder: str = "universal"
            em_tier: int = 0

            def evaluate_vector(
                self, facts: EthicalFacts
            ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
                # ... compute moral vector ...
                return verdict, vector, reasons, metadata
    """

    em_name: Optional[str] = None
    """Name/identifier for this EM. Defaults to class name."""

    stakeholder: str = "unspecified"
    """Stakeholder perspective this EM represents."""

    em_tier: int = 2
    """Tier classification (default: 2 for Rights/Fairness)."""

    def __post_init__(self) -> None:
        if self.em_name is None:
            self.em_name = self.__class__.__name__

    def judge(self, facts: EthicalFacts) -> EthicalJudgementV2:
        """
        Default implementation of EthicsModuleV2.judge.

        Delegates to `evaluate_vector`, which subclasses must implement.
        """
        verdict, moral_vector, reasons, metadata = self.evaluate_vector(facts)
        return self._make_judgement_v2(
            facts=facts,
            verdict=verdict,
            moral_vector=moral_vector,
            reasons=reasons,
            metadata=metadata,
        )

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Default reflex check - no participation.

        Override to provide fast veto logic for reflex layer.
        """
        return None

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        """
        Core normative logic returning MoralVector.

        Must return:
        - verdict: one of the Verdict literals
        - moral_vector: MoralVector with dimensional scores
        - reasons: list of human-readable explanation strings
        - metadata: dict of machine-readable diagnostics

        Subclasses MUST implement this method.
        """
        raise NotImplementedError("Subclasses must implement evaluate_vector().")

    def _make_judgement_v2(
        self,
        facts: EthicalFacts,
        verdict: Verdict,
        moral_vector: MoralVector,
        reasons: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EthicalJudgementV2:
        """
        Helper to create EthicalJudgementV2 with consistent fields.
        """
        if metadata is None:
            metadata = {}

        # Determine if veto was triggered
        veto_triggered = moral_vector.has_veto() or verdict == "forbid"
        veto_reason = None
        if veto_triggered and moral_vector.veto_flags:
            veto_reason = ", ".join(moral_vector.veto_flags)

        return EthicalJudgementV2(
            option_id=facts.option_id,
            em_name=self.em_name or self.__class__.__name__,
            stakeholder=self.stakeholder,
            em_tier=self.em_tier,
            verdict=verdict,
            moral_vector=moral_vector,
            veto_triggered=veto_triggered,
            veto_reason=veto_reason,
            confidence=1.0,
            reasons=reasons,
            metadata=metadata,
        )

    # Backward compatibility: can also produce V1 judgements
    def judge_v1(self, facts: EthicalFacts) -> EthicalJudgement:
        """
        Produce V1 EthicalJudgement for backward compatibility.
        """
        v2_judgement = self.judge(facts)
        from ..judgement import judgement_v2_to_v1

        return judgement_v2_to_v1(v2_judgement)


class V1ToV2Adapter:
    """
    Adapter to wrap V1 EthicsModule as V2.

    Enables gradual migration by allowing V1 EMs to be used
    in V2 governance pipelines.
    """

    def __init__(
        self,
        v1_em: EthicsModule,
        em_tier: int = 2,
    ) -> None:
        """
        Wrap a V1 EM.

        Args:
            v1_em: The V1 EthicsModule to wrap.
            em_tier: Tier to assign (default 2 for Rights/Fairness).
        """
        self._v1 = v1_em
        self.em_name = v1_em.em_name
        self.stakeholder = v1_em.stakeholder
        self.em_tier = em_tier

    def judge(self, facts: EthicalFacts) -> EthicalJudgementV2:
        """
        Produce V2 judgement from wrapped V1 EM.
        """
        v1_result = self._v1.judge(facts)
        return judgement_v1_to_v2(v1_result, em_tier=self.em_tier)

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        V1 EMs don't support reflex checks.
        """
        return None


class V2ToV1Adapter:
    """
    Adapter to wrap V2 EthicsModuleV2 as V1.

    Enables V2 EMs to be used in V1 governance pipelines.
    """

    def __init__(self, v2_em: EthicsModuleV2) -> None:
        """
        Wrap a V2 EM.

        Args:
            v2_em: The V2 EthicsModuleV2 to wrap.
        """
        self._v2 = v2_em
        self.em_name = v2_em.em_name
        self.stakeholder = v2_em.stakeholder

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        """
        Produce V1 judgement from wrapped V2 EM.
        """
        from ..judgement import judgement_v2_to_v1

        v2_result = self._v2.judge(facts)
        return judgement_v2_to_v1(v2_result)


__all__ = [
    # V1 (still supported)
    "EthicsModule",
    "BaseEthicsModule",
    # V2 (DEME 2.0)
    "EthicsModuleV2",
    "BaseEthicsModuleV2",
    # Adapters
    "V1ToV2Adapter",
    "V2ToV1Adapter",
]
