# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Temporal Operations Module for MoralTensor.

DEME V3 Sprint 7: Functions for working with time-evolving ethical assessments:
- Temporal discounting (weight future impacts)
- Irreversibility detection (identify irreparable harm)
- Trajectory comparison (DTW distance)
- Window/sliding operations
- Time metadata tracking

Temporal tensors have shape (9, n_parties, n_timesteps) with axis names ("k", "n", "tau").

Version: 3.0.0 (DEME V3 - Sprint 7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple, Union

import numpy as np

from erisml.ethics.moral_tensor import (
    MoralTensor,
    MORAL_DIMENSION_NAMES,
)

# =============================================================================
# Time Metadata
# =============================================================================


@dataclass(frozen=True)
class TimeMetadata:
    """
    Metadata for temporal tensors.

    Tracks timing information for ethical assessment trajectories.

    Attributes:
        n_timesteps: Number of time steps in the tensor.
        time_labels: Optional labels for each timestep.
        time_unit: Unit of time (e.g., "seconds", "hours", "days").
        duration: Total duration covered by the trajectory.
        start_time: Optional absolute start time (ISO 8601 string).
        discount_rate: Discount rate per time unit for future values.
    """

    n_timesteps: int
    time_labels: Tuple[str, ...] = ()
    time_unit: str = "steps"
    duration: Optional[float] = None
    start_time: Optional[str] = None
    discount_rate: float = 0.0

    def __post_init__(self) -> None:
        if self.n_timesteps < 1:
            raise ValueError(f"n_timesteps must be >= 1, got {self.n_timesteps}")
        if self.time_labels and len(self.time_labels) != self.n_timesteps:
            raise ValueError(
                f"time_labels length ({len(self.time_labels)}) must match "
                f"n_timesteps ({self.n_timesteps})"
            )
        if self.discount_rate < 0 or self.discount_rate >= 1:
            raise ValueError(
                f"discount_rate must be in [0, 1), got {self.discount_rate}"
            )

    @property
    def step_duration(self) -> Optional[float]:
        """Duration of each time step."""
        if self.duration is None:
            return None
        return self.duration / self.n_timesteps

    def get_discount_weights(self) -> np.ndarray:
        """
        Get discount weights for each timestep.

        Returns:
            Array of shape (n_timesteps,) with weights in [0, 1].
            Earlier timesteps have weight 1.0, later timesteps are discounted.
        """
        if self.discount_rate == 0:
            return np.ones(self.n_timesteps, dtype=np.float64)

        # Exponential discounting: w[t] = (1 - rate)^t
        t = np.arange(self.n_timesteps, dtype=np.float64)
        return (1.0 - self.discount_rate) ** t

    @classmethod
    def from_tensor(
        cls,
        tensor: MoralTensor,
        time_unit: str = "steps",
        duration: Optional[float] = None,
        discount_rate: float = 0.0,
    ) -> "TimeMetadata":
        """
        Create TimeMetadata from a temporal tensor.

        Args:
            tensor: MoralTensor with "tau" axis.
            time_unit: Unit of time.
            duration: Total duration.
            discount_rate: Discount rate for future values.

        Returns:
            TimeMetadata instance.

        Raises:
            ValueError: If tensor does not have temporal axis.
        """
        if "tau" not in tensor.axis_names:
            raise ValueError("Tensor does not have temporal axis 'tau'")

        tau_idx = tensor.axis_names.index("tau")
        n_timesteps = tensor.shape[tau_idx]
        time_labels = tuple(tensor.axis_labels.get("tau", []))

        return cls(
            n_timesteps=n_timesteps,
            time_labels=time_labels,
            time_unit=time_unit,
            duration=duration,
            discount_rate=discount_rate,
        )


# =============================================================================
# Temporal Tensor Validation
# =============================================================================


def validate_temporal_tensor(tensor: MoralTensor) -> None:
    """
    Validate that a tensor has proper temporal structure.

    Args:
        tensor: MoralTensor to validate.

    Raises:
        ValueError: If tensor is not a valid temporal tensor.
    """
    if tensor.rank < 3:
        raise ValueError(f"Temporal tensor must have rank >= 3, got {tensor.rank}")

    if "tau" not in tensor.axis_names:
        raise ValueError(
            f"Temporal tensor must have 'tau' axis, got {tensor.axis_names}"
        )

    if tensor.axis_names[2] != "tau":
        raise ValueError(
            f"'tau' axis must be at position 2, found at "
            f"{tensor.axis_names.index('tau')}"
        )


def is_temporal_tensor(tensor: MoralTensor) -> bool:
    """Check if tensor has temporal structure."""
    return tensor.rank >= 3 and "tau" in tensor.axis_names


# =============================================================================
# Temporal Discounting
# =============================================================================


def apply_temporal_discount(
    tensor: MoralTensor,
    discount_rate: float,
    method: Literal["exponential", "hyperbolic", "linear"] = "exponential",
) -> MoralTensor:
    """
    Apply temporal discounting to future values.

    Discounts values at later timesteps, reflecting the common preference
    for present over future impacts. Higher discount rates mean less
    weight on future values.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        discount_rate: Discount rate per timestep in [0, 1).
            - 0.0: No discounting (all timesteps equal weight)
            - 0.1: 10% discount per timestep
            - 0.5: 50% discount per timestep (aggressive)
        method: Discounting method:
            - "exponential": w[t] = (1 - rate)^t (standard)
            - "hyperbolic": w[t] = 1 / (1 + rate*t) (present-biased)
            - "linear": w[t] = max(0, 1 - rate*t) (simple)

    Returns:
        Discounted MoralTensor with same shape.

    Raises:
        ValueError: If tensor is not temporal or discount_rate invalid.

    Example:
        # 10% per-step discount
        discounted = apply_temporal_discount(tensor, 0.1)
    """
    validate_temporal_tensor(tensor)

    if discount_rate < 0 or discount_rate >= 1:
        raise ValueError(f"discount_rate must be in [0, 1), got {discount_rate}")

    if discount_rate == 0:
        return tensor  # No discounting needed

    data = tensor.to_dense()
    n_timesteps = tensor.shape[2]
    t = np.arange(n_timesteps, dtype=np.float64)

    # Compute weights based on method
    if method == "exponential":
        weights = (1.0 - discount_rate) ** t
    elif method == "hyperbolic":
        weights = 1.0 / (1.0 + discount_rate * t)
    elif method == "linear":
        weights = np.maximum(0.0, 1.0 - discount_rate * t)
    else:
        raise ValueError(f"Unknown discount method: {method}")

    # Broadcast weights to tensor shape: (1, 1, n_timesteps) for (k, n, tau)
    weights_broadcast = weights.reshape(1, 1, -1)

    # Apply discount
    discounted = data * weights_broadcast
    discounted = np.clip(discounted, 0.0, 1.0)

    return MoralTensor.from_dense(
        discounted,
        axis_names=tensor.axis_names,
        axis_labels=tensor.axis_labels.copy(),
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata={
            **tensor.metadata,
            "temporal_discount_applied": True,
            "discount_rate": discount_rate,
            "discount_method": method,
        },
        extensions=tensor.extensions.copy(),
    )


def temporal_aggregate(
    tensor: MoralTensor,
    discount_rate: float = 0.0,
    method: Literal["mean", "sum", "max", "min"] = "mean",
) -> MoralTensor:
    """
    Aggregate temporal tensor to rank-2 by collapsing time axis.

    Combines all timesteps into a single assessment using weighted
    aggregation with optional discounting.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        discount_rate: Discount rate for future values.
        method: Aggregation method:
            - "mean": Weighted mean (default)
            - "sum": Weighted sum (not normalized)
            - "max": Maximum across time
            - "min": Minimum across time

    Returns:
        Rank-2 MoralTensor with shape (9, n_parties).

    Example:
        # Average ethics over time with 5% discount
        avg = temporal_aggregate(tensor, discount_rate=0.05)
    """
    validate_temporal_tensor(tensor)

    data = tensor.to_dense()
    n_timesteps = tensor.shape[2]

    if method in ("max", "min"):
        # No weighting for min/max
        if method == "max":
            result = np.max(data, axis=2)
        else:
            result = np.min(data, axis=2)
    else:
        # Get discount weights
        if discount_rate > 0:
            t = np.arange(n_timesteps, dtype=np.float64)
            weights = (1.0 - discount_rate) ** t
        else:
            weights = np.ones(n_timesteps, dtype=np.float64)

        # Weighted aggregation
        weights_broadcast = weights.reshape(1, 1, -1)
        weighted_data = data * weights_broadcast

        if method == "mean":
            result = weighted_data.sum(axis=2) / weights.sum()
        elif method == "sum":
            result = weighted_data.sum(axis=2)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

    result = np.clip(result, 0.0, 1.0)

    # Get rank-2 axis names
    new_axis_names = ("k", "n")
    new_axis_labels = {k: v for k, v in tensor.axis_labels.items() if k != "tau"}

    return MoralTensor.from_dense(
        result,
        axis_names=new_axis_names,
        axis_labels=new_axis_labels,
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata={
            **tensor.metadata,
            "temporal_aggregation": method,
            "discount_rate": discount_rate,
            "original_timesteps": n_timesteps,
        },
        extensions=tensor.extensions.copy(),
    )


# =============================================================================
# Irreversibility Detection
# =============================================================================


@dataclass
class IrreversibilityResult:
    """
    Result of irreversibility detection.

    Attributes:
        is_irreversible: Whether irreversible harm is detected.
        irreversible_parties: List of party IDs with irreversible harm.
        irreversible_dimensions: List of ethical dimensions with irreversible harm.
        irreversibility_timesteps: Dict mapping (party, dimension) to first
            irreversibility timestep.
        harm_trajectories: Dict mapping party to harm trajectory array.
        veto_recommended: Whether a veto is recommended based on irreversibility.
        reasons: Human-readable reasons for irreversibility.
    """

    is_irreversible: bool
    irreversible_parties: List[str] = field(default_factory=list)
    irreversible_dimensions: List[str] = field(default_factory=list)
    irreversibility_timesteps: Dict[Tuple[str, str], int] = field(default_factory=dict)
    harm_trajectories: Dict[str, np.ndarray] = field(default_factory=dict)
    veto_recommended: bool = False
    reasons: List[str] = field(default_factory=list)


def detect_irreversibility(
    tensor: MoralTensor,
    harm_threshold: float = 0.7,
    recovery_threshold: float = 0.3,
    min_sustained_steps: int = 2,
    dimensions: Optional[List[str]] = None,
) -> IrreversibilityResult:
    """
    Detect irreversible harm patterns across time.

    Irreversible harm is detected when harm exceeds a threshold and
    does not recover below the recovery threshold within the trajectory.

    For the physical_harm dimension, this checks if harm becomes
    permanently high. For other dimensions (rights_respect, etc.),
    it checks if they become permanently low.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        harm_threshold: Threshold above which harm is considered severe [0, 1].
        recovery_threshold: Threshold below which harm is considered recovered [0, 1].
        min_sustained_steps: Minimum consecutive steps above threshold
            to consider harm sustained.
        dimensions: Optional list of dimensions to check (default: all).

    Returns:
        IrreversibilityResult with detection details.

    Example:
        result = detect_irreversibility(tensor, harm_threshold=0.8)
        if result.veto_recommended:
            print(f"Irreversible harm detected: {result.reasons}")
    """
    validate_temporal_tensor(tensor)

    data = tensor.to_dense()
    n_parties = tensor.shape[1]
    n_timesteps = tensor.shape[2]

    # Get party labels
    party_labels = tensor.axis_labels.get("n", [f"party_{i}" for i in range(n_parties)])

    # Dimensions to check
    check_dims = dimensions or list(MORAL_DIMENSION_NAMES)

    result = IrreversibilityResult(is_irreversible=False)

    for party_idx, party_id in enumerate(party_labels):
        for dim_name in check_dims:
            if dim_name not in MORAL_DIMENSION_NAMES:
                continue

            dim_idx = MORAL_DIMENSION_NAMES.index(dim_name)
            trajectory = data[dim_idx, party_idx, :]

            # For physical_harm, high values are bad
            # For other dimensions (rights_respect, etc.), low values are bad
            if dim_name == "physical_harm":
                # Check if harm exceeds threshold and doesn't recover
                above_threshold = trajectory >= harm_threshold
            else:
                # For "good" dimensions, low values are harmful
                above_threshold = trajectory <= (1.0 - harm_threshold)

            # Find first sustained harm
            sustained_count = 0
            first_harm_step = None

            for t in range(n_timesteps):
                if above_threshold[t]:
                    sustained_count += 1
                    if (
                        sustained_count >= min_sustained_steps
                        and first_harm_step is None
                    ):
                        first_harm_step = t - min_sustained_steps + 1
                else:
                    sustained_count = 0

            # Check if harm is sustained and never recovers
            if first_harm_step is not None:
                # Check if there's any recovery after first harm
                remaining = trajectory[first_harm_step:]
                if dim_name == "physical_harm":
                    recovers = np.any(remaining <= recovery_threshold)
                else:
                    recovers = np.any(remaining >= (1.0 - recovery_threshold))

                if not recovers:
                    result.is_irreversible = True
                    if party_id not in result.irreversible_parties:
                        result.irreversible_parties.append(party_id)
                    if dim_name not in result.irreversible_dimensions:
                        result.irreversible_dimensions.append(dim_name)
                    result.irreversibility_timesteps[(party_id, dim_name)] = (
                        first_harm_step
                    )
                    result.harm_trajectories[party_id] = trajectory.copy()

                    if dim_name == "physical_harm":
                        result.reasons.append(
                            f"Irreversible physical harm to {party_id} starting at t={first_harm_step}"
                        )
                    else:
                        result.reasons.append(
                            f"Irreversible {dim_name} degradation for {party_id} "
                            f"starting at t={first_harm_step}"
                        )

    # Recommend veto if physical_harm or rights_respect is irreversibly affected
    critical_dims = {"physical_harm", "rights_respect", "fairness_equity"}
    if result.is_irreversible:
        if set(result.irreversible_dimensions) & critical_dims:
            result.veto_recommended = True

    return result


# =============================================================================
# Trajectory Comparison (DTW Distance)
# =============================================================================


def dtw_distance(
    t1: MoralTensor,
    t2: MoralTensor,
    dimension: Optional[str] = None,
    party: Optional[Union[int, str]] = None,
) -> float:
    """
    Compute Dynamic Time Warping distance between temporal trajectories.

    DTW measures similarity between two temporal sequences that may have
    different speeds or temporal alignment. Lower distance means more
    similar trajectories.

    Args:
        t1: First temporal MoralTensor.
        t2: Second temporal MoralTensor.
        dimension: Optional dimension to compare (default: all, averaged).
        party: Optional party to compare (default: all, averaged).

    Returns:
        DTW distance (>= 0). 0 means identical trajectories.

    Raises:
        ValueError: If tensors are not temporal or have incompatible shapes.

    Example:
        # Compare two ethical trajectories
        dist = dtw_distance(trajectory1, trajectory2)
        if dist < 0.1:
            print("Trajectories are very similar")
    """
    validate_temporal_tensor(t1)
    validate_temporal_tensor(t2)

    # Check compatible party dimensions
    if t1.shape[1] != t2.shape[1]:
        raise ValueError(f"Party dimensions must match: {t1.shape[1]} vs {t2.shape[1]}")

    data1 = t1.to_dense()
    data2 = t2.to_dense()

    # Optionally select specific dimension
    if dimension is not None:
        if dimension not in MORAL_DIMENSION_NAMES:
            raise ValueError(f"Unknown dimension: {dimension}")
        dim_idx = MORAL_DIMENSION_NAMES.index(dimension)
        data1 = data1[dim_idx : dim_idx + 1, :, :]
        data2 = data2[dim_idx : dim_idx + 1, :, :]

    # Optionally select specific party
    if party is not None:
        if isinstance(party, str):
            party_labels = t1.axis_labels.get("n", [])
            if party not in party_labels:
                raise ValueError(f"Party '{party}' not found")
            party_idx = party_labels.index(party)
        else:
            party_idx = party
        data1 = data1[:, party_idx : party_idx + 1, :]
        data2 = data2[:, party_idx : party_idx + 1, :]

    # Compute DTW for each (dimension, party) pair and average
    total_distance = 0.0
    count = 0

    for k in range(data1.shape[0]):
        for n in range(data1.shape[1]):
            seq1 = data1[k, n, :]
            seq2 = data2[k, n, :]
            total_distance += _compute_dtw(seq1, seq2)
            count += 1

    return total_distance / count if count > 0 else 0.0


def _compute_dtw(seq1: np.ndarray, seq2: np.ndarray) -> float:
    """
    Compute DTW distance between two 1D sequences.

    Uses dynamic programming with Euclidean distance.
    """
    n, m = len(seq1), len(seq2)

    # Initialize cost matrix
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0.0

    # Fill cost matrix
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(seq1[i - 1] - seq2[j - 1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j],  # insertion
                dtw_matrix[i, j - 1],  # deletion
                dtw_matrix[i - 1, j - 1],  # match
            )

    return float(dtw_matrix[n, m])


def trajectory_similarity(
    t1: MoralTensor,
    t2: MoralTensor,
    method: Literal["dtw", "euclidean", "cosine"] = "dtw",
) -> float:
    """
    Compute similarity between two temporal trajectories.

    Returns a value in [0, 1] where 1 means identical trajectories.

    Args:
        t1: First temporal MoralTensor.
        t2: Second temporal MoralTensor.
        method: Similarity method:
            - "dtw": DTW-based (handles temporal misalignment)
            - "euclidean": Point-wise Euclidean distance
            - "cosine": Cosine similarity of flattened trajectories

    Returns:
        Similarity in [0, 1]. Higher means more similar.
    """
    validate_temporal_tensor(t1)
    validate_temporal_tensor(t2)

    if method == "dtw":
        dist = dtw_distance(t1, t2)
        # Normalize: max possible DTW distance is roughly n*m*max_val
        max_dist = t1.shape[2] * t2.shape[2]
        return float(1.0 / (1.0 + dist / max_dist))

    data1 = t1.to_dense()
    data2 = t2.to_dense()

    # Pad to same temporal length if needed
    max_t = max(data1.shape[2], data2.shape[2])
    if data1.shape[2] < max_t:
        pad_width = ((0, 0), (0, 0), (0, max_t - data1.shape[2]))
        data1 = np.pad(data1, pad_width, mode="edge")
    if data2.shape[2] < max_t:
        pad_width = ((0, 0), (0, 0), (0, max_t - data2.shape[2]))
        data2 = np.pad(data2, pad_width, mode="edge")

    if method == "euclidean":
        dist = np.linalg.norm(data1 - data2)
        # Normalize by max possible distance
        max_dist = np.sqrt(data1.size)
        return float(1.0 - min(1.0, dist / max_dist))

    elif method == "cosine":
        flat1 = data1.flatten()
        flat2 = data2.flatten()
        norm1 = np.linalg.norm(flat1)
        norm2 = np.linalg.norm(flat2)
        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0
        cos_sim = np.dot(flat1, flat2) / (norm1 * norm2)
        return float((cos_sim + 1.0) / 2.0)  # Map from [-1,1] to [0,1]

    else:
        raise ValueError(f"Unknown similarity method: {method}")


# =============================================================================
# Window Operations
# =============================================================================


def slice_time_window(
    tensor: MoralTensor,
    start: int,
    end: int,
) -> MoralTensor:
    """
    Extract a time window from a temporal tensor.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        start: Start timestep (inclusive).
        end: End timestep (exclusive).

    Returns:
        MoralTensor with only the specified time window.

    Example:
        # Get timesteps 2-5
        window = slice_time_window(tensor, 2, 5)
    """
    validate_temporal_tensor(tensor)

    n_timesteps = tensor.shape[2]
    if start < 0 or end > n_timesteps or start >= end:
        raise ValueError(
            f"Invalid window [{start}, {end}) for tensor with {n_timesteps} timesteps"
        )

    return tensor.slice_time(slice(start, end))


def sliding_window(
    tensor: MoralTensor,
    window_size: int,
    stride: int = 1,
) -> List[MoralTensor]:
    """
    Apply sliding window over temporal axis.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        window_size: Size of each window.
        stride: Step size between windows.

    Returns:
        List of MoralTensors, each representing one window.

    Example:
        # 3-step sliding windows
        windows = sliding_window(tensor, window_size=3, stride=1)
    """
    validate_temporal_tensor(tensor)

    n_timesteps = tensor.shape[2]
    if window_size > n_timesteps:
        raise ValueError(
            f"window_size ({window_size}) cannot exceed n_timesteps ({n_timesteps})"
        )

    windows = []
    for start in range(0, n_timesteps - window_size + 1, stride):
        end = start + window_size
        window = slice_time_window(tensor, start, end)
        windows.append(window)

    return windows


def rolling_aggregate(
    tensor: MoralTensor,
    window_size: int,
    method: Literal["mean", "max", "min"] = "mean",
    stride: int = 1,
) -> MoralTensor:
    """
    Compute rolling aggregate over temporal axis.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        window_size: Size of rolling window.
        method: Aggregation method ("mean", "max", "min").
        stride: Step size between windows.

    Returns:
        MoralTensor with aggregated values at each window position.

    Example:
        # 3-step rolling mean
        smoothed = rolling_aggregate(tensor, window_size=3, method="mean")
    """
    validate_temporal_tensor(tensor)

    data = tensor.to_dense()
    n_timesteps = tensor.shape[2]

    if window_size > n_timesteps:
        raise ValueError(
            f"window_size ({window_size}) cannot exceed n_timesteps ({n_timesteps})"
        )

    # Compute rolling aggregates
    n_windows = (n_timesteps - window_size) // stride + 1
    result_shape = (tensor.shape[0], tensor.shape[1], n_windows)
    result = np.zeros(result_shape, dtype=np.float64)

    for i, start in enumerate(range(0, n_timesteps - window_size + 1, stride)):
        window = data[:, :, start : start + window_size]
        if method == "mean":
            result[:, :, i] = np.mean(window, axis=2)
        elif method == "max":
            result[:, :, i] = np.max(window, axis=2)
        elif method == "min":
            result[:, :, i] = np.min(window, axis=2)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

    # Update time labels
    new_labels = {}
    for key, val in tensor.axis_labels.items():
        if key == "tau":
            new_labels[key] = [f"window_{i}" for i in range(n_windows)]
        else:
            new_labels[key] = val

    return MoralTensor.from_dense(
        result,
        axis_names=tensor.axis_names,
        axis_labels=new_labels,
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata={
            **tensor.metadata,
            "rolling_aggregate": method,
            "window_size": window_size,
            "stride": stride,
        },
        extensions=tensor.extensions.copy(),
    )


# =============================================================================
# Temporal Trend Analysis
# =============================================================================


def compute_temporal_trend(
    tensor: MoralTensor,
    dimension: Optional[str] = None,
) -> Dict[str, np.ndarray]:
    """
    Compute linear trend coefficients for each dimension/party.

    Returns slope and intercept of linear fit to each trajectory.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        dimension: Optional specific dimension to analyze.

    Returns:
        Dict with:
            - "slopes": Array of shape (n_dims, n_parties) with trend slopes
            - "intercepts": Array of shape (n_dims, n_parties) with intercepts
            - "r_squared": Array of R² values for fit quality

    Example:
        trends = compute_temporal_trend(tensor)
        if trends["slopes"][0, 0] > 0:
            print("Physical harm increasing for first party")
    """
    validate_temporal_tensor(tensor)

    data = tensor.to_dense()
    n_dims = data.shape[0]
    n_parties = data.shape[1]
    n_timesteps = data.shape[2]

    t = np.arange(n_timesteps, dtype=np.float64)

    slopes = np.zeros((n_dims, n_parties))
    intercepts = np.zeros((n_dims, n_parties))
    r_squared = np.zeros((n_dims, n_parties))

    for k in range(n_dims):
        if dimension is not None:
            if MORAL_DIMENSION_NAMES[k] != dimension:
                continue

        for n in range(n_parties):
            y = data[k, n, :]

            # Linear regression: y = slope * t + intercept
            t_mean = t.mean()
            y_mean = y.mean()

            numerator = np.sum((t - t_mean) * (y - y_mean))
            denominator = np.sum((t - t_mean) ** 2)

            if abs(denominator) > 1e-10:
                slope = numerator / denominator
                intercept = y_mean - slope * t_mean

                # R² calculation
                y_pred = slope * t + intercept
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - y_mean) ** 2)
                r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-10 else 0.0
            else:
                slope = 0.0
                intercept = y_mean
                r2 = 0.0

            slopes[k, n] = slope
            intercepts[k, n] = intercept
            r_squared[k, n] = r2

    return {
        "slopes": slopes,
        "intercepts": intercepts,
        "r_squared": r_squared,
    }


def detect_trend_reversal(
    tensor: MoralTensor,
    threshold: float = 0.1,
) -> Dict[str, List[int]]:
    """
    Detect points where trends reverse direction.

    Args:
        tensor: Temporal MoralTensor with "tau" axis.
        threshold: Minimum change magnitude to consider a reversal.

    Returns:
        Dict mapping "party_id" to list of reversal timesteps.

    Example:
        reversals = detect_trend_reversal(tensor)
        for party, times in reversals.items():
            print(f"{party} has reversals at: {times}")
    """
    validate_temporal_tensor(tensor)

    data = tensor.to_dense()
    n_parties = tensor.shape[1]

    party_labels = tensor.axis_labels.get("n", [f"party_{i}" for i in range(n_parties)])

    result: Dict[str, List[int]] = {party: [] for party in party_labels}

    for party_idx, party_id in enumerate(party_labels):
        # Aggregate across dimensions for overall trend
        trajectory = np.mean(data[:, party_idx, :], axis=0)

        # Compute first differences
        diffs = np.diff(trajectory)

        # Find sign changes with sufficient magnitude
        for t in range(1, len(diffs)):
            if abs(diffs[t]) >= threshold and abs(diffs[t - 1]) >= threshold:
                if np.sign(diffs[t]) != np.sign(diffs[t - 1]):
                    result[party_id].append(t)

    return result


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Metadata
    "TimeMetadata",
    # Validation
    "validate_temporal_tensor",
    "is_temporal_tensor",
    # Discounting
    "apply_temporal_discount",
    "temporal_aggregate",
    # Irreversibility
    "IrreversibilityResult",
    "detect_irreversibility",
    # Trajectory comparison
    "dtw_distance",
    "trajectory_similarity",
    # Window operations
    "slice_time_window",
    "sliding_window",
    "rolling_aggregate",
    # Trend analysis
    "compute_temporal_trend",
    "detect_trend_reversal",
]
