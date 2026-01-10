# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tensor Operations Module for MoralTensor.

DEME V3 helper functions for working with MoralTensors:
- Broadcasting and shape manipulation
- Stacking and concatenation
- Normalization utilities
- Distance metrics (including Wasserstein)

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from erisml.ethics.moral_tensor import MoralTensor, DEFAULT_AXIS_NAMES


def broadcast_tensors(*tensors: MoralTensor) -> Tuple[MoralTensor, ...]:
    """
    Broadcast tensors to compatible shapes.

    Uses NumPy broadcasting rules. All tensors must have the same rank
    and compatible shapes along each dimension.

    Args:
        *tensors: MoralTensors to broadcast.

    Returns:
        Tuple of MoralTensors with identical shapes.

    Raises:
        ValueError: If tensors cannot be broadcast together.

    Example:
        t1 = MoralTensor.from_dense(np.ones((9, 1)))
        t2 = MoralTensor.from_dense(np.ones((9, 3)))
        b1, b2 = broadcast_tensors(t1, t2)
        # Both now have shape (9, 3)
    """
    if len(tensors) == 0:
        return ()

    if len(tensors) == 1:
        return (tensors[0],)

    # Check all tensors have the same rank
    ranks = [t.rank for t in tensors]
    if len(set(ranks)) > 1:
        raise ValueError(f"All tensors must have the same rank, got {ranks}")

    # Get dense arrays
    arrays = [t.to_dense() for t in tensors]

    # Compute broadcast shape
    try:
        broadcast_shape = np.broadcast_shapes(*[a.shape for a in arrays])
    except ValueError as e:
        raise ValueError(f"Cannot broadcast tensors: {e}") from e

    # Broadcast each array
    broadcast_arrays = [np.broadcast_to(a, broadcast_shape).copy() for a in arrays]

    # Create new tensors
    result = []
    for i, (tensor, arr) in enumerate(zip(tensors, broadcast_arrays)):
        merged_vetoes = list(set().union(*[set(t.veto_flags) for t in tensors]))
        merged_reasons = list(set().union(*[set(t.reason_codes) for t in tensors]))

        result.append(
            MoralTensor.from_dense(
                arr,
                axis_names=tensors[0].axis_names,
                veto_flags=merged_vetoes,
                reason_codes=merged_reasons,
                metadata=tensor.metadata.copy(),
                extensions=tensor.extensions.copy(),
            )
        )

    return tuple(result)


def stack_tensors(
    tensors: List[MoralTensor],
    axis: str,
    labels: Optional[List[str]] = None,
) -> MoralTensor:
    """
    Stack tensors along a new axis.

    All tensors must have the same shape. A new axis is added
    at the appropriate position based on the axis name.

    Args:
        tensors: List of MoralTensors to stack.
        axis: Name for the new axis (e.g., "n", "tau").
        labels: Optional labels for each tensor along the new axis.

    Returns:
        Stacked MoralTensor with rank increased by 1.

    Raises:
        ValueError: If tensors have different shapes or rank exceeds 6.

    Example:
        # Stack 3 rank-1 tensors into rank-2 with 3 parties
        t1 = MoralTensor.from_dense(np.ones(9))
        t2 = MoralTensor.from_dense(np.ones(9))
        stacked = stack_tensors([t1, t2], axis="n", labels=["alice", "bob"])
    """
    if len(tensors) == 0:
        raise ValueError("Cannot stack empty list of tensors")

    # Check all shapes match
    shapes = [t.shape for t in tensors]
    if len(set(shapes)) > 1:
        raise ValueError(f"All tensors must have same shape, got {shapes}")

    # Check rank constraint
    new_rank = tensors[0].rank + 1
    if new_rank > 6:
        raise ValueError(f"Stacking would exceed max rank 6, got {new_rank}")

    # Get target axis names
    target_axis_names = DEFAULT_AXIS_NAMES.get(
        new_rank, tuple(f"dim{i}" for i in range(new_rank))
    )

    # Find where to insert the new axis
    if axis in target_axis_names:
        axis_idx = target_axis_names.index(axis)
    else:
        # Insert after 'k'
        axis_idx = 1

    # Stack arrays
    arrays = [t.to_dense() for t in tensors]
    stacked = np.stack(arrays, axis=axis_idx)

    # Build axis labels
    axis_labels = dict(tensors[0].axis_labels)
    if labels is not None:
        if len(labels) != len(tensors):
            raise ValueError(
                f"Labels length ({len(labels)}) must match tensors ({len(tensors)})"
            )
        axis_labels[axis] = labels
    else:
        axis_labels[axis] = [f"{axis}_{i}" for i in range(len(tensors))]

    # Merge vetoes and reasons
    merged_vetoes = list(set().union(*[set(t.veto_flags) for t in tensors]))
    merged_reasons = list(set().union(*[set(t.reason_codes) for t in tensors]))

    return MoralTensor.from_dense(
        stacked,
        axis_names=target_axis_names,
        axis_labels=axis_labels,
        veto_flags=merged_vetoes,
        reason_codes=merged_reasons,
    )


def concat_tensors(
    tensors: List[MoralTensor],
    axis: str,
) -> MoralTensor:
    """
    Concatenate tensors along an existing axis.

    All tensors must have the same shape except along the concatenation axis.

    Args:
        tensors: List of MoralTensors to concatenate.
        axis: Name of axis to concatenate along.

    Returns:
        Concatenated MoralTensor.

    Raises:
        ValueError: If axis not found or shapes incompatible.

    Example:
        t1 = MoralTensor.from_dense(np.ones((9, 2)))  # 2 parties
        t2 = MoralTensor.from_dense(np.ones((9, 3)))  # 3 parties
        combined = concat_tensors([t1, t2], axis="n")  # 5 parties
    """
    if len(tensors) == 0:
        raise ValueError("Cannot concatenate empty list of tensors")

    if len(tensors) == 1:
        return tensors[0]

    # Check axis exists in all tensors
    for i, t in enumerate(tensors):
        if axis not in t.axis_names:
            raise ValueError(f"Tensor {i} does not have axis '{axis}'")

    # Get axis index (should be same for all)
    axis_idx = tensors[0].axis_names.index(axis)

    # Check shapes are compatible (same except along concat axis)
    base_shape = list(tensors[0].shape)
    base_shape[axis_idx] = None  # type: ignore

    for i, t in enumerate(tensors[1:], 1):
        check_shape = list(t.shape)
        check_shape[axis_idx] = None  # type: ignore
        if check_shape != base_shape:
            raise ValueError(
                f"Tensor {i} has incompatible shape {t.shape} vs {tensors[0].shape}"
            )

    # Concatenate arrays
    arrays = [t.to_dense() for t in tensors]
    concatenated = np.concatenate(arrays, axis=axis_idx)

    # Concatenate axis labels
    axis_labels = dict(tensors[0].axis_labels)
    if axis in axis_labels:
        new_labels = []
        for t in tensors:
            new_labels.extend(t.axis_labels.get(axis, []))
        axis_labels[axis] = new_labels

    # Merge vetoes and reasons
    merged_vetoes = list(set().union(*[set(t.veto_flags) for t in tensors]))
    merged_reasons = list(set().union(*[set(t.reason_codes) for t in tensors]))

    return MoralTensor.from_dense(
        concatenated,
        axis_names=tensors[0].axis_names,
        axis_labels=axis_labels,
        veto_flags=merged_vetoes,
        reason_codes=merged_reasons,
    )


def normalize_tensor(
    tensor: MoralTensor,
    axis: str,
    method: str = "sum",
) -> MoralTensor:
    """
    Normalize values along an axis.

    Args:
        tensor: MoralTensor to normalize.
        axis: Axis to normalize along.
        method: Normalization method:
            - "sum": Normalize so values sum to 1 along axis.
            - "max": Normalize by maximum value along axis.
            - "minmax": Normalize to [0, 1] range along axis.

    Returns:
        Normalized MoralTensor with values in [0, 1].

    Example:
        # Normalize party weights to sum to 1
        normalized = normalize_tensor(tensor, axis="n", method="sum")
    """
    if axis not in tensor.axis_names:
        raise ValueError(f"Axis '{axis}' not found in {tensor.axis_names}")

    axis_idx = tensor.axis_names.index(axis)
    data = tensor.to_dense()

    if method == "sum":
        sums = np.sum(data, axis=axis_idx, keepdims=True)
        # Avoid division by zero
        sums = np.where(sums < 1e-10, 1.0, sums)
        result = data / sums

    elif method == "max":
        maxes = np.max(data, axis=axis_idx, keepdims=True)
        maxes = np.where(maxes < 1e-10, 1.0, maxes)
        result = data / maxes

    elif method == "minmax":
        mins = np.min(data, axis=axis_idx, keepdims=True)
        maxes = np.max(data, axis=axis_idx, keepdims=True)
        ranges = maxes - mins
        ranges = np.where(ranges < 1e-10, 1.0, ranges)
        result = (data - mins) / ranges

    else:
        raise ValueError(f"Unknown normalization method: {method}")

    # Clamp to [0, 1]
    result = np.clip(result, 0.0, 1.0)

    return MoralTensor.from_dense(
        result,
        axis_names=tensor.axis_names,
        axis_labels=tensor.axis_labels.copy(),
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata=tensor.metadata.copy(),
        extensions=tensor.extensions.copy(),
    )


def clip_tensor(
    tensor: MoralTensor,
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> MoralTensor:
    """
    Clip tensor values to a range.

    Args:
        tensor: MoralTensor to clip.
        min_val: Minimum value (default 0.0).
        max_val: Maximum value (default 1.0).

    Returns:
        Clipped MoralTensor.
    """
    data = tensor.to_dense()
    result = np.clip(data, min_val, max_val)

    return MoralTensor.from_dense(
        result,
        axis_names=tensor.axis_names,
        axis_labels=tensor.axis_labels.copy(),
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata=tensor.metadata.copy(),
        extensions=tensor.extensions.copy(),
    )


def wasserstein_distance(
    t1: MoralTensor,
    t2: MoralTensor,
    p: int = 1,
) -> float:
    """
    Compute Wasserstein (Earth Mover's) distance between tensors.

    Treats each ethical dimension as a distribution over parties
    and computes the transport cost. For rank-1 tensors, computes
    a simple L-p distance.

    Note: For accurate Wasserstein computation on higher-rank tensors,
    scipy is used if available. Otherwise falls back to approximate
    computation.

    Args:
        t1: First MoralTensor.
        t2: Second MoralTensor (must have same shape).
        p: Order (1 for W1, 2 for W2).

    Returns:
        Wasserstein distance (>= 0).

    Raises:
        ValueError: If tensors have different shapes.
    """
    if t1.shape != t2.shape:
        raise ValueError(f"Shape mismatch: {t1.shape} vs {t2.shape}")

    data1 = t1.to_dense()
    data2 = t2.to_dense()

    # For rank-1, just compute L-p distance
    if t1.rank == 1:
        diff = np.abs(data1 - data2)
        return float(np.sum(diff**p) ** (1 / p))

    # Try to use scipy for accurate computation
    try:
        from scipy.stats import wasserstein_distance as scipy_wasserstein

        # Compute Wasserstein distance per dimension, then aggregate
        total = 0.0
        for k in range(9):
            d1 = data1[k, ...].flatten()
            d2 = data2[k, ...].flatten()

            # Normalize to probability distributions
            d1_sum = d1.sum()
            d2_sum = d2.sum()

            if d1_sum > 1e-10 and d2_sum > 1e-10:
                d1_norm = d1 / d1_sum
                d2_norm = d2 / d2_sum
                total += scipy_wasserstein(d1_norm, d2_norm) ** p
            else:
                # Fall back to L-p for zero distributions
                total += (np.abs(d1 - d2).sum()) ** p

        return float(total ** (1 / p))

    except ImportError:
        # Fall back to approximate: use mean absolute difference
        # weighted by position
        total = 0.0
        for k in range(9):
            d1 = data1[k, ...].flatten()
            d2 = data2[k, ...].flatten()

            # Sort and compute cumulative difference (approximation)
            d1_sorted = np.sort(d1)
            d2_sorted = np.sort(d2)
            total += np.sum(np.abs(d1_sorted - d2_sorted) ** p)

        return float(total ** (1 / p))


def cosine_similarity(t1: MoralTensor, t2: MoralTensor) -> float:
    """
    Compute cosine similarity between tensors.

    Args:
        t1: First MoralTensor.
        t2: Second MoralTensor (must have same shape).

    Returns:
        Cosine similarity in [-1, 1]. Higher means more similar.

    Raises:
        ValueError: If tensors have different shapes.
    """
    if t1.shape != t2.shape:
        raise ValueError(f"Shape mismatch: {t1.shape} vs {t2.shape}")

    data1 = t1.to_dense().flatten()
    data2 = t2.to_dense().flatten()

    norm1 = np.linalg.norm(data1)
    norm2 = np.linalg.norm(data2)

    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0

    return float(np.dot(data1, data2) / (norm1 * norm2))


def weighted_aggregate(
    tensors: List[MoralTensor],
    weights: Optional[np.ndarray] = None,
) -> MoralTensor:
    """
    Compute weighted aggregate of multiple tensors.

    Args:
        tensors: List of MoralTensors (must have same shape).
        weights: Optional weight for each tensor (default: uniform).

    Returns:
        Weighted average MoralTensor.

    Raises:
        ValueError: If tensors have different shapes.
    """
    if len(tensors) == 0:
        raise ValueError("Cannot aggregate empty list of tensors")

    if len(tensors) == 1:
        return tensors[0]

    # Check shapes
    shapes = [t.shape for t in tensors]
    if len(set(shapes)) > 1:
        raise ValueError(f"All tensors must have same shape, got {shapes}")

    # Default to uniform weights
    if weights is None:
        w = np.ones(len(tensors), dtype=np.float64) / len(tensors)
    else:
        w = np.asarray(weights, dtype=np.float64)
        if len(w) != len(tensors):
            raise ValueError(
                f"Weights length ({len(w)}) must match tensors ({len(tensors)})"
            )
        w = w / w.sum()  # Normalize

    # Compute weighted sum
    arrays = [t.to_dense() for t in tensors]
    result = np.zeros_like(arrays[0])
    for arr, weight in zip(arrays, w):
        result += arr * weight

    # Clamp to [0, 1]
    result = np.clip(result, 0.0, 1.0)

    # Merge vetoes and reasons
    merged_vetoes = list(set().union(*[set(t.veto_flags) for t in tensors]))
    merged_reasons = list(set().union(*[set(t.reason_codes) for t in tensors]))

    return MoralTensor.from_dense(
        result,
        axis_names=tensors[0].axis_names,
        axis_labels=tensors[0].axis_labels.copy(),
        veto_flags=merged_vetoes,
        reason_codes=merged_reasons,
    )


__all__ = [
    "broadcast_tensors",
    "stack_tensors",
    "concat_tensors",
    "normalize_tensor",
    "clip_tensor",
    "wasserstein_distance",
    "cosine_similarity",
    "weighted_aggregate",
]
