# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEME V3 Judgements with MoralTensor for distributed multi-party ethics.

This module extends DEME 2.0 (EthicalJudgementV2) to support:
- Per-party ethical assessment via MoralTensor
- Distributed veto tracking with location information
- Per-party verdict mapping
- Fairness metrics integration

Version: 3.0.0 (DEME V3 - Sprint 6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple, TYPE_CHECKING

from .judgement import Verdict, EthicalJudgementV2, DEFAULT_V2_WEIGHTS

if TYPE_CHECKING:
    from .moral_tensor import MoralTensor
    from .moral_vector import MoralVector


# Collapse strategies for tensor-to-vector conversion
CollapseStrategy = Literal["mean", "worst_case", "best_case", "weighted", "maximin"]


@dataclass
class EthicalJudgementV3:
    """
    DEME V3 judgement with MoralTensor for distributed multi-party ethics.

    This is the preferred format for multi-agent ethics assessment. It provides:
    - Per-party moral assessment via MoralTensor (shape: [9, n_parties])
    - Per-party verdict tracking
    - Distributed veto locations
    - Integration with fairness metrics

    The moral_tensor has shape (9, n) where:
    - 9 = moral dimensions (physical_harm, rights_respect, etc.)
    - n = number of affected parties

    Example:
        tensor_data = np.array([
            [0.1, 0.8, 0.3],  # physical_harm per party
            [0.9, 0.2, 0.7],  # rights_respect per party
            ...
        ])
        tensor = MoralTensor.from_dense(tensor_data, axis_labels={"n": ["alice", "bob", "carol"]})

        judgement = EthicalJudgementV3(
            option_id="opt1",
            moral_tensor=tensor,
            per_party_verdicts={"alice": "prefer", "bob": "avoid", "carol": "neutral"},
            ...
        )
    """

    option_id: str
    """Identifier for the candidate option being judged."""

    em_name: str
    """Name of the ethics module that produced this judgement."""

    stakeholder: str
    """Stakeholder perspective this EM represents."""

    em_tier: int
    """
    Tier classification (0-4):
    - 0: Constitutional (Geneva, BasicHumanRights, NonDiscrimination)
    - 1: Core Safety (PhysicalSafety, Proxemics)
    - 2: Rights/Fairness (AutonomyConsent, AllocationFairness)
    - 3: Soft Values (Beneficence, Environmental)
    - 4: Meta-Governance (PatternGuard, ProfileIntegrity)
    """

    verdict: Verdict
    """Global verdict aggregating all per-party verdicts."""

    moral_tensor: MoralTensor
    """
    Multi-dimensional moral assessment per party.
    Shape: (9, n) where n = number of parties.
    Axis names: ("k", "n") where k = dimension, n = party.
    """

    # Per-party tracking
    per_party_verdicts: Dict[str, Verdict] = field(default_factory=dict)
    """Verdict for each party: {"party_id": Verdict}."""

    party_labels: Tuple[str, ...] = field(default_factory=tuple)
    """Ordered party identifiers matching tensor axis 'n'."""

    # Distributed veto tracking
    distributed_veto_triggered: bool = False
    """Whether any party triggered a veto."""

    per_party_vetoes: Dict[str, bool] = field(default_factory=dict)
    """Veto status for each party: {"party_id": bool}."""

    veto_locations: List[Tuple[int, ...]] = field(default_factory=list)
    """
    Tensor coordinates where vetoes apply.
    Format: [(party_idx,), ...] for rank-2 tensors.
    """

    global_veto_override: bool = False
    """If True, veto applies to entire option regardless of per-party status."""

    veto_reasons: Dict[str, str] = field(default_factory=dict)
    """Veto reasons per party: {"party_id": "reason"}."""

    # Metadata
    confidence: float = 1.0
    """Confidence level [0, 1] in this judgement."""

    reasons: List[str] = field(default_factory=list)
    """Human-readable explanations for the verdict."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Machine-readable metadata for analysis."""

    def __post_init__(self) -> None:
        """Validate and set derived fields."""
        # Extract party labels from tensor if not provided
        if not self.party_labels and self.moral_tensor is not None:
            labels = self.moral_tensor.axis_labels.get("n", [])
            if labels:
                self.party_labels = tuple(labels)
            else:
                # Generate default labels
                n_parties = self.moral_tensor.shape[1] if len(self.moral_tensor.shape) > 1 else 1
                self.party_labels = tuple(f"party_{i}" for i in range(n_parties))

        # Update distributed_veto_triggered from tensor veto_locations
        if self.moral_tensor is not None and self.moral_tensor.veto_locations:
            self.distributed_veto_triggered = True

    @property
    def n_parties(self) -> int:
        """Number of parties in the assessment."""
        if self.moral_tensor is not None and len(self.moral_tensor.shape) > 1:
            return self.moral_tensor.shape[1]
        return 1

    @property
    def has_any_veto(self) -> bool:
        """Return True if any veto is active."""
        return (
            self.distributed_veto_triggered
            or self.global_veto_override
            or any(self.per_party_vetoes.values())
        )

    def get_party_vector(self, party: str | int) -> "MoralVector":
        """
        Extract MoralVector for a specific party.

        Args:
            party: Party identifier (string) or index (int).

        Returns:
            MoralVector for the specified party.

        Raises:
            KeyError: If party not found.
            IndexError: If index out of range.
        """
        from .compat import collapse_v3_to_v2

        if isinstance(party, str):
            if party not in self.party_labels:
                raise KeyError(f"Party '{party}' not found. Available: {self.party_labels}")
            idx = self.party_labels.index(party)
        else:
            idx = party

        # Slice the tensor at party index
        party_tensor = self.moral_tensor.slice_party(idx)

        # Collapse to vector (rank-1 tensor → MoralVector)
        return collapse_v3_to_v2(party_tensor)

    def get_party_verdict(self, party: str) -> Verdict:
        """Get verdict for a specific party."""
        return self.per_party_verdicts.get(party, self.verdict)

    def is_party_vetoed(self, party: str) -> bool:
        """Check if a specific party triggered a veto."""
        return self.per_party_vetoes.get(party, False)

    @property
    def normative_score(self) -> float:
        """
        Collapse to scalar for V1/V2 compatibility.

        Uses mean collapse strategy across parties.
        """
        from .compat import collapse_v3_to_v2

        vector = collapse_v3_to_v2(self.moral_tensor, strategy="mean")
        return vector.to_scalar(weights=DEFAULT_V2_WEIGHTS)

    def to_v2(
        self,
        collapse_strategy: CollapseStrategy = "mean",
        weights: Optional[Dict[str, float]] = None,
    ) -> EthicalJudgementV2:
        """
        Convert to V2 judgement for backward compatibility.

        Args:
            collapse_strategy: How to collapse per-party scores:
                - "mean": Average across parties
                - "worst_case": Most pessimistic per dimension
                - "best_case": Most optimistic per dimension
                - "weighted": Use provided weights
                - "maximin": Focus on worst-off party (Rawlsian)
            weights: Party weights for "weighted" strategy.

        Returns:
            EthicalJudgementV2 with collapsed MoralVector.
        """
        from .compat import collapse_v3_to_v2

        # Collapse tensor to vector
        if collapse_strategy == "maximin":
            # Find worst-off party and use their vector
            from .fairness_metrics import rawlsian_maximin

            _, worst_idx = rawlsian_maximin(
                self.moral_tensor, dimension="physical_harm", return_party_index=True
            )
            moral_vector = self.get_party_vector(worst_idx)
        else:
            moral_vector = collapse_v3_to_v2(
                self.moral_tensor,
                strategy=collapse_strategy if collapse_strategy != "weighted" else "weighted",
                weights=weights,
            )

        # Determine single veto status
        veto_triggered = self.has_any_veto
        veto_reason = None
        if veto_triggered:
            reasons = list(self.veto_reasons.values())
            veto_reason = "; ".join(reasons) if reasons else "Distributed veto"

        return EthicalJudgementV2(
            option_id=self.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            em_tier=self.em_tier,
            verdict=self.verdict,
            moral_vector=moral_vector,
            veto_triggered=veto_triggered,
            veto_reason=veto_reason,
            confidence=self.confidence,
            reasons=self.reasons.copy(),
            metadata={
                **self.metadata,
                "_collapsed_from_v3": True,
                "_n_parties": self.n_parties,
                "_collapse_strategy": collapse_strategy,
            },
        )


# =============================================================================
# V2 ↔ V3 Conversion Functions
# =============================================================================


def judgement_v2_to_v3(
    j: EthicalJudgementV2,
    parties: List[str],
    distribution_strategy: str = "uniform",
) -> EthicalJudgementV3:
    """
    Promote V2 judgement to V3 with per-party tracking.

    Args:
        j: The V2 EthicalJudgementV2.
        parties: List of party identifiers to distribute to.
        distribution_strategy: How to distribute the single vector:
            - "uniform": Same assessment for all parties
            - "replicate": Copy vector to each party column

    Returns:
        EthicalJudgementV3 with per-party assessment.
    """
    from .moral_tensor import MoralTensor, MORAL_DIMENSION_NAMES
    import numpy as np

    # Promote MoralVector to MoralTensor by broadcasting
    n_parties = len(parties)

    # Convert MoralVector to numpy array (9 dimensions)
    vector_dict = j.moral_vector.to_dict()
    vector_values = np.array([vector_dict[dim] for dim in MORAL_DIMENSION_NAMES])

    # Broadcast to (9, n_parties)
    data = np.tile(vector_values.reshape(-1, 1), (1, n_parties))

    # Create tensor with party labels
    moral_tensor = MoralTensor.from_dense(
        data,
        axis_names=("k", "n"),
        axis_labels={"n": parties},
        veto_flags=list(j.moral_vector.veto_flags) if j.moral_vector.veto_flags else [],
    )

    # Create uniform per-party verdicts
    per_party_verdicts = {party: j.verdict for party in parties}

    # Uniform veto status
    per_party_vetoes = {party: j.veto_triggered for party in parties}

    # Veto reasons
    veto_reasons = {}
    if j.veto_triggered and j.veto_reason:
        for party in parties:
            veto_reasons[party] = j.veto_reason

    # Veto locations (all parties if veto)
    veto_locations: List[Tuple[int, ...]] = []
    if j.veto_triggered:
        veto_locations = [(i,) for i in range(n_parties)]

    return EthicalJudgementV3(
        option_id=j.option_id,
        em_name=j.em_name,
        stakeholder=j.stakeholder,
        em_tier=j.em_tier,
        verdict=j.verdict,
        moral_tensor=moral_tensor,
        per_party_verdicts=per_party_verdicts,
        party_labels=tuple(parties),
        distributed_veto_triggered=j.veto_triggered,
        per_party_vetoes=per_party_vetoes,
        veto_locations=veto_locations,
        global_veto_override=j.veto_triggered,
        veto_reasons=veto_reasons,
        confidence=j.confidence,
        reasons=j.reasons.copy(),
        metadata={
            **j.metadata,
            "_promoted_from_v2": True,
            "_distribution_strategy": distribution_strategy,
        },
    )


def judgement_v3_to_v2(
    j: EthicalJudgementV3,
    collapse_strategy: CollapseStrategy = "mean",
    weights: Optional[Dict[str, float]] = None,
) -> EthicalJudgementV2:
    """
    Collapse V3 judgement to V2 for backward compatibility.

    Args:
        j: The V3 EthicalJudgementV3.
        collapse_strategy: How to collapse per-party scores.
        weights: Party weights for "weighted" strategy.

    Returns:
        EthicalJudgementV2 with collapsed MoralVector.
    """
    return j.to_v2(collapse_strategy=collapse_strategy, weights=weights)


# =============================================================================
# Helper Functions
# =============================================================================


def is_forbidden_v3(j: EthicalJudgementV3) -> bool:
    """Return True if this V3 judgement marks the option as forbidden."""
    return j.verdict == "forbid" or j.has_any_veto


def is_strongly_preferred_v3(j: EthicalJudgementV3) -> bool:
    """Return True if this V3 judgement strongly prefers the option."""
    return j.verdict == "strongly_prefer" and not j.has_any_veto


def get_worst_off_party(j: EthicalJudgementV3) -> Tuple[str, float]:
    """
    Identify the worst-off party in the judgement.

    Returns:
        Tuple of (party_id, welfare_score) for the worst-off party.
    """
    from .fairness_metrics import rawlsian_maximin_welfare

    welfare_scores = rawlsian_maximin_welfare(j.moral_tensor)

    min_idx = int(welfare_scores.argmin())
    min_welfare = float(welfare_scores[min_idx])

    party_id = j.party_labels[min_idx] if min_idx < len(j.party_labels) else f"party_{min_idx}"

    return party_id, min_welfare


def compute_verdict_distribution(j: EthicalJudgementV3) -> Dict[Verdict, int]:
    """
    Count how many parties have each verdict.

    Returns:
        Dict mapping Verdict to count.
    """
    distribution: Dict[Verdict, int] = {
        "strongly_prefer": 0,
        "prefer": 0,
        "neutral": 0,
        "avoid": 0,
        "forbid": 0,
    }

    for verdict in j.per_party_verdicts.values():
        distribution[verdict] += 1

    return distribution


__all__ = [
    # Core V3 judgement
    "EthicalJudgementV3",
    "CollapseStrategy",
    # Conversion functions
    "judgement_v2_to_v3",
    "judgement_v3_to_v2",
    # Helper functions
    "is_forbidden_v3",
    "is_strongly_preferred_v3",
    "get_worst_off_party",
    "compute_verdict_distribution",
]
