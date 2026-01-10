# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEME V3 Ethics Module interfaces and base classes.

This module extends DEME 2.0 (BaseEthicsModuleV2) to support:
- Distributed multi-party ethics assessment via MoralTensor
- Per-party verdicts and veto tracking
- Integration with EthicalFactsV3

Version: 3.0.0 (DEME V3 - Sprint 6)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    TYPE_CHECKING,
    runtime_checkable,
)

import numpy as np

from ..facts import EthicalFacts
from ..judgement import Verdict, EthicalJudgementV2
from ..judgement_v3 import EthicalJudgementV3, judgement_v2_to_v3
from ..moral_vector import MoralVector
from .base import BaseEthicsModuleV2, EthicsModuleV2

if TYPE_CHECKING:
    from ..facts_v3 import EthicalFactsV3
    from ..moral_tensor import MoralTensor


# =============================================================================
# DEME V3: EthicsModuleV3 Protocol
# =============================================================================


@runtime_checkable
class EthicsModuleV3(Protocol):
    """
    DEME V3 protocol for ethics modules returning MoralTensor.

    This extends EthicsModuleV2 with distributed multi-party assessment.
    It provides:
    - Per-party moral assessment via MoralTensor
    - Distributed veto tracking
    - Per-party verdicts
    - Integration with EthicalFactsV3

    V3 modules can also handle V2 inputs via the standard judge() method.
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
        Single-agent fallback: evaluate using V2 interface.

        Returns EthicalJudgementV2 with MoralVector.
        """
        ...

    def judge_distributed(self, facts: "EthicalFactsV3") -> EthicalJudgementV3:
        """
        Distributed multi-party assessment.

        Args:
            facts: V3 ethical facts with per-party tracking.

        Returns:
            EthicalJudgementV3 with MoralTensor (per-party scores).
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

    def reflex_check_distributed(
        self, facts: "EthicalFactsV3"
    ) -> Dict[str, Optional[bool]]:
        """
        Per-party fast veto check for reflex layer.

        Returns:
            Dict mapping party_id to veto decision:
            - True: veto this option for this party
            - False: pass reflex check for this party
            - None: no participation for this party
        """
        ...


# =============================================================================
# DEME V3: BaseEthicsModuleV3 Template
# =============================================================================


@dataclass
class BaseEthicsModuleV3(BaseEthicsModuleV2):
    """
    DEME V3 base class for ethics modules with MoralTensor support.

    Extends BaseEthicsModuleV2 with distributed multi-party assessment.
    Subclasses should implement `evaluate_tensor(facts: EthicalFactsV3)`
    which returns (Verdict, MoralTensor, per_party_verdicts, reasons, metadata).

    The template method pattern provides:
    - judge(): V2-compatible single-agent assessment (inherited)
    - judge_distributed(): V3 multi-party assessment (new)
    - reflex_check(): V2-compatible fast veto (inherited)
    - reflex_check_distributed(): V3 per-party fast veto (new)

    Example:

        @dataclass
        class GenevaEMV3(BaseEthicsModuleV3):
            em_name: str = "geneva_constitutional_v3"
            stakeholder: str = "universal"
            em_tier: int = 0

            def evaluate_tensor(
                self, facts: EthicalFactsV3
            ) -> Tuple[Verdict, MoralTensor, Dict[str, Verdict], List[str], Dict[str, Any]]:
                # ... compute per-party moral tensor ...
                return verdict, tensor, per_party_verdicts, reasons, metadata
    """

    def judge_distributed(self, facts: "EthicalFactsV3") -> EthicalJudgementV3:
        """
        Default implementation of EthicsModuleV3.judge_distributed.

        Delegates to `evaluate_tensor`, which subclasses must implement.
        """
        (
            verdict,
            moral_tensor,
            per_party_verdicts,
            reasons,
            metadata,
        ) = self.evaluate_tensor(facts)

        return self._make_judgement_v3(
            facts=facts,
            verdict=verdict,
            moral_tensor=moral_tensor,
            per_party_verdicts=per_party_verdicts,
            reasons=reasons,
            metadata=metadata,
        )

    def evaluate_tensor(
        self,
        facts: "EthicalFactsV3",
    ) -> Tuple[Verdict, "MoralTensor", Dict[str, Verdict], List[str], Dict[str, Any]]:
        """
        Core normative logic returning MoralTensor.

        Must return:
        - verdict: Global verdict (one of the Verdict literals)
        - moral_tensor: MoralTensor with per-party dimensional scores
        - per_party_verdicts: Dict mapping party_id to Verdict
        - reasons: list of human-readable explanation strings
        - metadata: dict of machine-readable diagnostics

        Subclasses MUST implement this method for V3 support.
        """
        raise NotImplementedError("Subclasses must implement evaluate_tensor().")

    def reflex_check_distributed(
        self, facts: "EthicalFactsV3"
    ) -> Dict[str, Optional[bool]]:
        """
        Default per-party reflex check - no participation.

        Override to provide fast per-party veto logic.

        Returns:
            Dict mapping party_id to veto decision.
        """
        # Default: no participation for any party
        parties = self._get_party_ids(facts)
        return {party: None for party in parties}

    def _get_party_ids(self, facts: "EthicalFactsV3") -> List[str]:
        """Extract party IDs from V3 facts."""
        if hasattr(facts, "consequences") and hasattr(facts.consequences, "per_party"):
            return [p.party_id for p in facts.consequences.per_party]
        return []

    def _make_judgement_v3(
        self,
        facts: "EthicalFactsV3",
        verdict: Verdict,
        moral_tensor: "MoralTensor",
        per_party_verdicts: Dict[str, Verdict],
        reasons: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EthicalJudgementV3:
        """
        Helper to create EthicalJudgementV3 with consistent fields.
        """
        if metadata is None:
            metadata = {}

        # Extract party labels from tensor or facts
        party_labels = tuple(moral_tensor.axis_labels.get("n", []))
        if not party_labels:
            party_labels = tuple(self._get_party_ids(facts))

        # Determine per-party vetoes from tensor veto_locations
        per_party_vetoes: Dict[str, bool] = {}
        veto_reasons: Dict[str, str] = {}

        for i, party in enumerate(party_labels):
            # Check if this party index is in veto_locations
            is_vetoed = any(
                loc[0] == i if len(loc) > 0 else False
                for loc in moral_tensor.veto_locations
            )
            per_party_vetoes[party] = is_vetoed

            # Check tensor veto_flags for reasons
            if is_vetoed and moral_tensor.veto_flags:
                veto_reasons[party] = ", ".join(moral_tensor.veto_flags)

        # Global veto if any party vetoed
        distributed_veto_triggered = any(per_party_vetoes.values())

        # Global veto override if verdict is forbid
        global_veto_override = verdict == "forbid"

        return EthicalJudgementV3(
            option_id=facts.option_id,
            em_name=self.em_name or self.__class__.__name__,
            stakeholder=self.stakeholder,
            em_tier=self.em_tier,
            verdict=verdict,
            moral_tensor=moral_tensor,
            per_party_verdicts=per_party_verdicts,
            party_labels=party_labels,
            distributed_veto_triggered=distributed_veto_triggered,
            per_party_vetoes=per_party_vetoes,
            veto_locations=list(moral_tensor.veto_locations),
            global_veto_override=global_veto_override,
            veto_reasons=veto_reasons,
            confidence=1.0,
            reasons=reasons,
            metadata=metadata,
        )

    # Backward compatibility: can also produce V2 judgements from V3 facts
    def judge_v2_from_v3(
        self,
        facts: "EthicalFactsV3",
        collapse_strategy: str = "mean",
    ) -> EthicalJudgementV2:
        """
        Produce V2 EthicalJudgement from V3 facts.

        Useful for V2 governance pipelines consuming V3-capable EMs.
        """
        v3_judgement = self.judge_distributed(facts)
        return v3_judgement.to_v2(collapse_strategy=collapse_strategy)


# =============================================================================
# V2 ↔ V3 Adapters
# =============================================================================


class V2ToV3EMAdapter:
    """
    Adapter to wrap V2 EthicsModuleV2 as V3.

    Enables gradual migration by allowing V2 EMs to be used
    in V3 governance pipelines. The V2 judgement is broadcast
    uniformly to all parties.
    """

    def __init__(
        self,
        v2_em: EthicsModuleV2,
    ) -> None:
        """
        Wrap a V2 EM.

        Args:
            v2_em: The V2 EthicsModuleV2 to wrap.
        """
        self._v2 = v2_em
        self.em_name = v2_em.em_name
        self.stakeholder = v2_em.stakeholder
        self.em_tier = v2_em.em_tier

    def judge(self, facts: EthicalFacts) -> EthicalJudgementV2:
        """
        Produce V2 judgement from wrapped V2 EM.
        """
        return self._v2.judge(facts)

    def judge_distributed(self, facts: "EthicalFactsV3") -> EthicalJudgementV3:
        """
        Produce V3 judgement by broadcasting V2 result to all parties.
        """
        # Collapse V3 facts to V2
        from ..facts_v3 import collapse_facts_v3_to_v2

        v2_facts = collapse_facts_v3_to_v2(facts)

        # Get V2 judgement
        v2_result = self._v2.judge(v2_facts)

        # Get party list from V3 facts
        parties = [p.party_id for p in facts.consequences.per_party]

        # Promote to V3 (uniform distribution)
        return judgement_v2_to_v3(v2_result, parties=parties)

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Delegate to V2 EM's reflex check.
        """
        return self._v2.reflex_check(facts)

    def reflex_check_distributed(
        self, facts: "EthicalFactsV3"
    ) -> Dict[str, Optional[bool]]:
        """
        Apply V2 reflex check uniformly to all parties.
        """
        from ..facts_v3 import collapse_facts_v3_to_v2

        v2_facts = collapse_facts_v3_to_v2(facts)
        result = self._v2.reflex_check(v2_facts)

        parties = [p.party_id for p in facts.consequences.per_party]
        return {party: result for party in parties}


class V3ToV2EMAdapter:
    """
    Adapter to wrap V3 EthicsModuleV3 as V2.

    Enables V3 EMs to be used in V2 governance pipelines.
    The V3 tensor is collapsed to a single vector.
    """

    def __init__(
        self,
        v3_em: EthicsModuleV3,
        collapse_strategy: str = "mean",
    ) -> None:
        """
        Wrap a V3 EM.

        Args:
            v3_em: The V3 EthicsModuleV3 to wrap.
            collapse_strategy: How to collapse per-party scores.
        """
        self._v3 = v3_em
        self._collapse_strategy = collapse_strategy
        self.em_name = v3_em.em_name
        self.stakeholder = v3_em.stakeholder
        self.em_tier = v3_em.em_tier

    def judge(self, facts: EthicalFacts) -> EthicalJudgementV2:
        """
        Produce V2 judgement from wrapped V3 EM.

        Promotes V2 facts to V3, runs V3 judgement, then collapses.
        """
        # For pure V2 facts, delegate to V3's V2 interface
        return self._v3.judge(facts)

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Delegate to V3 EM's reflex check.
        """
        return self._v3.reflex_check(facts)


# =============================================================================
# Utility Functions
# =============================================================================


def aggregate_party_verdicts(
    per_party_verdicts: Dict[str, Verdict],
    strategy: str = "conservative",
) -> Verdict:
    """
    Aggregate per-party verdicts into a global verdict.

    Args:
        per_party_verdicts: Dict mapping party_id to Verdict.
        strategy: Aggregation strategy:
            - "conservative": Use most restrictive verdict (any forbid → forbid)
            - "majority": Use majority verdict
            - "optimistic": Use least restrictive verdict

    Returns:
        Aggregated global Verdict.
    """
    if not per_party_verdicts:
        return "neutral"

    verdicts = list(per_party_verdicts.values())

    # Verdict ordering from most to least restrictive
    verdict_order: List[Verdict] = [
        "forbid",
        "avoid",
        "neutral",
        "prefer",
        "strongly_prefer",
    ]

    if strategy == "conservative":
        # Return most restrictive (lowest index)
        for v in verdict_order:
            if v in verdicts:
                return v
        return "neutral"

    elif strategy == "majority":
        # Return most common verdict
        from collections import Counter

        counter = Counter(verdicts)
        return counter.most_common(1)[0][0]

    elif strategy == "optimistic":
        # Return least restrictive (highest index)
        for v in reversed(verdict_order):
            if v in verdicts:
                return v
        return "neutral"

    else:
        raise ValueError(f"Unknown aggregation strategy: {strategy}")


def create_uniform_tensor(
    base_vector: MoralVector,
    n_parties: int,
    party_labels: Optional[List[str]] = None,
) -> "MoralTensor":
    """
    Create a MoralTensor with uniform values across all parties.

    Args:
        base_vector: The MoralVector to replicate.
        n_parties: Number of parties.
        party_labels: Optional party identifiers.

    Returns:
        MoralTensor with shape (9, n_parties).
    """
    from ..moral_tensor import MoralTensor, MORAL_DIMENSION_NAMES

    # Extract vector values as numpy array
    vector_dict = base_vector.to_dict()
    values = np.array([vector_dict[dim] for dim in MORAL_DIMENSION_NAMES])

    # Broadcast to (9, n_parties)
    data = np.tile(values.reshape(-1, 1), (1, n_parties))

    # Create labels
    if party_labels is None:
        party_labels = [f"party_{i}" for i in range(n_parties)]

    # Veto locations if base vector has veto
    veto_locations: List[Tuple[int, ...]] = []
    if base_vector.has_veto():
        veto_locations = [(i,) for i in range(n_parties)]

    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n"),
        axis_labels={"n": party_labels},
        veto_flags=list(base_vector.veto_flags) if base_vector.veto_flags else [],
        veto_locations=veto_locations,
    )


__all__ = [
    # Protocol
    "EthicsModuleV3",
    # Base class
    "BaseEthicsModuleV3",
    # Adapters
    "V2ToV3EMAdapter",
    "V3ToV2EMAdapter",
    # Utilities
    "aggregate_party_verdicts",
    "create_uniform_tensor",
]
