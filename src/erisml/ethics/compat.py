# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
V2/V3 Compatibility Layer for DEME.

This module provides seamless interoperability between:
- V2 MoralVector (9-dimensional ethical assessment)
- V3 MoralTensor (multi-rank tensor for multi-agent ethics)

Key functions:
- promote_v2_to_v3(): Convert MoralVector → MoralTensor
- collapse_v3_to_v2(): Convert MoralTensor → MoralVector

Collapse strategies for V3→V2 conversion:
- mean: Average across all non-k dimensions
- worst_case: Most pessimistic values (min for goods, max for harm)
- best_case: Most optimistic values (max for goods, min for harm)
- weighted: Use provided weights per axis

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

from typing import Dict, Optional, Protocol, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from erisml.ethics.moral_vector import MoralVector
    from erisml.ethics.moral_tensor import MoralTensor


# =============================================================================
# Collapse Strategy Protocol
# =============================================================================


class CollapseStrategy(Protocol):
    """Protocol for V3→V2 collapse strategies."""

    def collapse(self, tensor: "MoralTensor") -> "MoralVector":
        """Collapse a MoralTensor to a MoralVector."""
        ...


# =============================================================================
# Core Conversion Functions
# =============================================================================


def promote_v2_to_v3(
    vector: "MoralVector",
    target_rank: int = 1,
    axis_sizes: Optional[Dict[str, int]] = None,
) -> "MoralTensor":
    """
    Convert MoralVector to MoralTensor.

    This is the primary V2→V3 promotion function. By default it creates
    a rank-1 tensor equivalent to the input vector. Optionally can promote
    to higher ranks by broadcasting.

    Args:
        vector: V2 MoralVector to convert.
        target_rank: Target tensor rank (default 1 for equivalence).
        axis_sizes: Sizes for new axes if rank > 1 (e.g., {"n": 3}).

    Returns:
        MoralTensor equivalent to (or broadcast from) the input vector.

    Raises:
        ValueError: If target_rank > 1 and axis_sizes missing required axes.

    Example:
        >>> vec = MoralVector(physical_harm=0.2, rights_respect=0.9, ...)
        >>> tensor = promote_v2_to_v3(vec)  # rank-1
        >>> tensor = promote_v2_to_v3(vec, target_rank=2, axis_sizes={"n": 3})
    """
    from erisml.ethics.moral_tensor import MoralTensor

    # Create base rank-1 tensor
    tensor = MoralTensor.from_moral_vector(vector)

    # Promote to higher rank if requested
    if target_rank > 1:
        if axis_sizes is None:
            raise ValueError(
                f"axis_sizes required for target_rank > 1, got {target_rank}"
            )
        tensor = tensor.promote_rank(target_rank, axis_sizes=axis_sizes)

    return tensor


def collapse_v3_to_v2(
    tensor: "MoralTensor",
    strategy: str = "mean",
    weights: Optional[Dict[str, np.ndarray]] = None,
) -> "MoralVector":
    """
    Collapse MoralTensor to MoralVector.

    This is the primary V3→V2 collapse function. Supports multiple
    strategies for aggregating multi-dimensional tensors down to
    a single 9-dimensional vector.

    Args:
        tensor: V3 MoralTensor (any rank).
        strategy: Collapse strategy, one of:
            - "mean": Average across all non-k dimensions (default)
            - "worst_case": Most pessimistic per dimension
            - "best_case": Most optimistic per dimension
            - "weighted": Use provided weights per axis
        weights: Dict mapping axis names to weight arrays (for "weighted").

    Returns:
        Collapsed MoralVector.

    Raises:
        ValueError: If strategy is unknown or weights missing for "weighted".

    Example:
        >>> tensor = MoralTensor.from_dense(np.random.rand(9, 3))
        >>> vec = collapse_v3_to_v2(tensor, strategy="mean")
        >>> vec = collapse_v3_to_v2(tensor, strategy="worst_case")
    """
    # Rank-1 tensors can be directly converted
    if tensor.rank == 1:
        return tensor.to_moral_vector()

    # Use the tensor's to_vector method which already implements these strategies
    if strategy == "mean":
        return tensor.to_vector(strategy="mean")
    elif strategy == "worst_case":
        return _collapse_worst_case(tensor)
    elif strategy == "best_case":
        return _collapse_best_case(tensor)
    elif strategy == "weighted":
        if weights is None:
            raise ValueError("'weighted' strategy requires weights dict")
        return tensor.to_vector(strategy="weighted", weights=weights)
    else:
        raise ValueError(
            f"Unknown strategy: {strategy}. "
            "Valid: 'mean', 'worst_case', 'best_case', 'weighted'"
        )


def _collapse_worst_case(tensor: "MoralTensor") -> "MoralVector":
    """
    Collapse using worst-case values per dimension.

    For physical_harm (dim 0): take maximum (worst = more harm)
    For other dimensions: take minimum (worst = less of good thing)
    """
    from erisml.ethics.moral_vector import MoralVector

    data = tensor.to_dense()

    # Collapse all non-k dimensions
    result = np.zeros(9, dtype=np.float64)

    # physical_harm: higher is worse, so take max
    result[0] = np.max(data[0, ...])

    # Other dimensions: lower is worse, so take min
    for k in range(1, 9):
        result[k] = np.min(data[k, ...])

    return MoralVector(
        physical_harm=float(result[0]),
        rights_respect=float(result[1]),
        fairness_equity=float(result[2]),
        autonomy_respect=float(result[3]),
        privacy_protection=float(result[4]),
        societal_environmental=float(result[5]),
        virtue_care=float(result[6]),
        legitimacy_trust=float(result[7]),
        epistemic_quality=float(result[8]),
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
    )


def _collapse_best_case(tensor: "MoralTensor") -> "MoralVector":
    """
    Collapse using best-case values per dimension.

    For physical_harm (dim 0): take minimum (best = less harm)
    For other dimensions: take maximum (best = more of good thing)
    """
    from erisml.ethics.moral_vector import MoralVector

    data = tensor.to_dense()

    # Collapse all non-k dimensions
    result = np.zeros(9, dtype=np.float64)

    # physical_harm: lower is better, so take min
    result[0] = np.min(data[0, ...])

    # Other dimensions: higher is better, so take max
    for k in range(1, 9):
        result[k] = np.max(data[k, ...])

    return MoralVector(
        physical_harm=float(result[0]),
        rights_respect=float(result[1]),
        fairness_equity=float(result[2]),
        autonomy_respect=float(result[3]),
        privacy_protection=float(result[4]),
        societal_environmental=float(result[5]),
        virtue_care=float(result[6]),
        legitimacy_trust=float(result[7]),
        epistemic_quality=float(result[8]),
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
    )


# =============================================================================
# Round-Trip Utilities
# =============================================================================


def ensure_tensor(value: "MoralVector | MoralTensor") -> "MoralTensor":
    """
    Ensure value is a MoralTensor.

    If already a tensor, return as-is. If a vector, promote to rank-1 tensor.

    Args:
        value: MoralVector or MoralTensor.

    Returns:
        MoralTensor.
    """
    from erisml.ethics.moral_tensor import MoralTensor
    from erisml.ethics.moral_vector import MoralVector

    if isinstance(value, MoralTensor):
        return value
    elif isinstance(value, MoralVector):
        return promote_v2_to_v3(value)
    else:
        raise TypeError(f"Expected MoralVector or MoralTensor, got {type(value)}")


def ensure_vector(
    value: "MoralVector | MoralTensor",
    strategy: str = "mean",
) -> "MoralVector":
    """
    Ensure value is a MoralVector.

    If already a vector, return as-is. If a tensor, collapse to vector.

    Args:
        value: MoralVector or MoralTensor.
        strategy: Collapse strategy if tensor (default "mean").

    Returns:
        MoralVector.
    """
    from erisml.ethics.moral_tensor import MoralTensor
    from erisml.ethics.moral_vector import MoralVector

    if isinstance(value, MoralVector):
        return value
    elif isinstance(value, MoralTensor):
        return collapse_v3_to_v2(value, strategy=strategy)
    else:
        raise TypeError(f"Expected MoralVector or MoralTensor, got {type(value)}")


def is_v3_compatible(value: "MoralVector | MoralTensor") -> bool:
    """
    Check if a value can be used in V3 context.

    All MoralVectors and MoralTensors are V3-compatible.

    Args:
        value: Value to check.

    Returns:
        True if V3-compatible.
    """
    from erisml.ethics.moral_tensor import MoralTensor
    from erisml.ethics.moral_vector import MoralVector

    return isinstance(value, (MoralVector, MoralTensor))


# =============================================================================
# Batch Conversion Utilities
# =============================================================================


def promote_vectors_to_tensor(
    vectors: Dict[str, "MoralVector"],
    axis_name: str = "n",
) -> "MoralTensor":
    """
    Convert multiple MoralVectors to a single rank-2 MoralTensor.

    Args:
        vectors: Dict mapping party/entity names to MoralVectors.
        axis_name: Name for the stacked axis (default "n").

    Returns:
        Rank-2 MoralTensor with shape (9, n).

    Example:
        >>> vecs = {"alice": vec1, "bob": vec2, "carol": vec3}
        >>> tensor = promote_vectors_to_tensor(vecs)
        >>> tensor.shape  # (9, 3)
    """
    from erisml.ethics.moral_tensor import MoralTensor

    return MoralTensor.from_moral_vectors(vectors, axis_name=axis_name)


def collapse_tensor_to_vectors(
    tensor: "MoralTensor",
    strategy: str = "mean",
) -> Dict[str, "MoralVector"]:
    """
    Convert a rank-2 MoralTensor to multiple MoralVectors.

    Args:
        tensor: Rank-2 MoralTensor with shape (9, n).
        strategy: How to handle if rank > 2 (reduce first).

    Returns:
        Dict mapping party labels to MoralVectors.

    Raises:
        ValueError: If tensor is not rank-2.

    Example:
        >>> tensor = MoralTensor.from_dense(data, axis_labels={"n": ["a", "b"]})
        >>> vecs = collapse_tensor_to_vectors(tensor)
        >>> vecs["a"], vecs["b"]
    """
    if tensor.rank != 2:
        raise ValueError(f"Expected rank-2 tensor, got rank {tensor.rank}")

    labels = tensor.axis_labels.get("n", [f"party_{i}" for i in range(tensor.shape[1])])
    result = {}

    for i, label in enumerate(labels):
        party_tensor = tensor.slice_party(i)
        result[label] = party_tensor.to_moral_vector()

    return result


__all__ = [
    # Core functions
    "promote_v2_to_v3",
    "collapse_v3_to_v2",
    # Utility functions
    "ensure_tensor",
    "ensure_vector",
    "is_v3_compatible",
    # Batch functions
    "promote_vectors_to_tensor",
    "collapse_tensor_to_vectors",
    # Protocol
    "CollapseStrategy",
]
