# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Distributional Fairness Metrics for Multi-Agent Ethics.

DEME V3 metrics for assessing distributional fairness across parties:

1. Gini Coefficient - Inequality measurement [0=equal, 1=unequal]
2. Rawlsian Maximin - Worst-off party identification and welfare
3. Utilitarian Aggregation - Sum/average across parties
4. Prioritarian Weighting - Vulnerability-adjusted aggregation
5. Atkinson Inequality Index - Parametric inequality with epsilon sensitivity
6. Theil Index - Generalized entropy (GE(alpha)) for multi-dimension inequality

All functions follow established numerical stability patterns:
- Tolerance: EPSILON = 1e-10
- Clipping: np.clip() for bounds
- Safe division: np.where() for zero handling

Version: 3.0.0 (DEME V3 Sprint 5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from erisml.ethics.moral_tensor import MoralTensor
    from erisml.ethics.facts_v3 import EthicalFactsV3

# =============================================================================
# Constants
# =============================================================================

EPSILON = 1e-10

# Dimension indices where higher values indicate harm (to invert for welfare)
HARM_DIMENSIONS = {0}  # physical_harm


# =============================================================================
# Gini Coefficient
# =============================================================================


def gini_coefficient(values: Union[np.ndarray, List[float]]) -> float:
    """
    Compute the Gini coefficient for a distribution of values.

    The Gini coefficient measures inequality in a distribution:
    - 0.0 = perfect equality (all values identical)
    - 1.0 = perfect inequality (one party has everything)

    Args:
        values: 1D array or list of non-negative values representing
            welfare/benefit/burden distribution across parties.

    Returns:
        Gini coefficient in [0, 1].
        Returns 0.0 for empty, single-element, or all-zero arrays.

    Raises:
        ValueError: If any values are negative.

    Examples:
        >>> gini_coefficient([1, 1, 1, 1])  # Perfect equality
        0.0
        >>> gini_coefficient([0, 0, 0, 1])  # High inequality
        0.75
        >>> gini_coefficient([1, 2, 3, 4, 5])  # Moderate inequality
        0.2666...
    """
    arr = np.asarray(values, dtype=np.float64)

    # Validate non-negative
    if np.any(arr < 0):
        raise ValueError("Gini coefficient requires non-negative values")

    # Edge cases
    if len(arr) <= 1:
        return 0.0

    if np.all(np.abs(arr) < EPSILON):
        return 0.0

    # Sort values
    arr = np.sort(arr)
    n = len(arr)

    # Compute Gini using the relative mean absolute difference formula
    index = np.arange(1, n + 1)
    total = np.sum(arr)

    if total < EPSILON:
        return 0.0

    return float((2 * np.sum(index * arr) - (n + 1) * total) / (n * total))


# =============================================================================
# Rawlsian Maximin
# =============================================================================


def rawlsian_maximin(
    tensor: "MoralTensor",
    dimension: Optional[str] = None,
    return_party_index: bool = False,
) -> Union[float, Tuple[float, int]]:
    """
    Compute Rawlsian maximin: identify worst-off party and their welfare.

    The maximin principle focuses on maximizing the minimum welfare
    (the welfare of the worst-off party). This function identifies
    that minimum value.

    Args:
        tensor: MoralTensor of rank >= 2 with party axis 'n'.
        dimension: Specific ethical dimension to evaluate (by name).
            If None, computes aggregate welfare (mean across k dimensions,
            with physical_harm inverted).
        return_party_index: If True, returns (min_value, party_index).

    Returns:
        If return_party_index is False: The minimum welfare value [0, 1].
        If return_party_index is True: Tuple of (min_welfare, party_index).

    Raises:
        ValueError: If tensor has rank < 2 or no party axis.
    """
    from erisml.ethics.moral_tensor import DIMENSION_INDEX

    if tensor.rank < 2:
        raise ValueError(
            f"Rawlsian maximin requires rank >= 2 tensor, got rank {tensor.rank}"
        )

    if "n" not in tensor.axis_names:
        raise ValueError("Tensor must have party axis 'n'")

    data = tensor.to_dense()

    if dimension is not None:
        # Get specific dimension
        if dimension not in DIMENSION_INDEX:
            raise ValueError(f"Unknown dimension: {dimension}")
        k_idx = DIMENSION_INDEX[dimension]
        values = data[k_idx, :]

        # Invert harm dimensions (lower harm = higher welfare)
        if k_idx in HARM_DIMENSIONS:
            values = 1.0 - values
    else:
        # Compute aggregate welfare across all dimensions
        welfare = rawlsian_maximin_welfare(tensor)
        values = welfare

    min_idx = int(np.argmin(values))
    min_val = float(values[min_idx])

    if return_party_index:
        return (min_val, min_idx)
    return min_val


def rawlsian_maximin_welfare(
    tensor: "MoralTensor",
    dimension_weights: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """
    Compute per-party welfare for Rawlsian analysis.

    Welfare is computed as weighted average across ethical dimensions,
    with harm dimensions inverted (1 - harm = welfare).

    Args:
        tensor: MoralTensor of rank >= 2.
        dimension_weights: Optional weights per ethical dimension name.
            Defaults to uniform weights.

    Returns:
        1D numpy array of welfare values, one per party.
        Higher values = better welfare.
    """
    from erisml.ethics.moral_tensor import MORAL_DIMENSION_NAMES

    if tensor.rank < 2:
        raise ValueError(f"Requires rank >= 2 tensor, got rank {tensor.rank}")

    data = tensor.to_dense()
    n_parties = data.shape[1]

    # Setup weights
    if dimension_weights is None:
        weights = np.ones(9, dtype=np.float64) / 9.0
    else:
        weights = np.zeros(9, dtype=np.float64)
        for name, w in dimension_weights.items():
            idx = MORAL_DIMENSION_NAMES.index(name)
            weights[idx] = w
        # Normalize
        weights = weights / np.sum(weights)

    # Compute welfare per party
    welfare = np.zeros(n_parties, dtype=np.float64)

    for party_idx in range(n_parties):
        party_welfare = 0.0
        for k in range(9):
            val = data[k, party_idx]
            # Invert harm dimensions
            if k in HARM_DIMENSIONS:
                val = 1.0 - val
            party_welfare += weights[k] * val
        welfare[party_idx] = party_welfare

    return welfare


# =============================================================================
# Utilitarian Aggregation
# =============================================================================


def utilitarian_sum(
    tensor: "MoralTensor",
    axis: str = "n",
    dimension: Optional[str] = None,
) -> float:
    """
    Compute utilitarian sum: total welfare across parties.

    Classical utilitarianism maximizes total welfare regardless
    of distribution.

    Args:
        tensor: MoralTensor to aggregate.
        axis: Axis to sum over (default "n" for parties).
        dimension: Specific dimension to sum. If None, uses aggregate welfare.

    Returns:
        Total welfare (sum). Not bounded to [0, 1].
    """
    from erisml.ethics.moral_tensor import DIMENSION_INDEX

    if tensor.rank < 2:
        raise ValueError(f"Requires rank >= 2 tensor, got rank {tensor.rank}")

    data = tensor.to_dense()

    if dimension is not None:
        if dimension not in DIMENSION_INDEX:
            raise ValueError(f"Unknown dimension: {dimension}")
        k_idx = DIMENSION_INDEX[dimension]
        values = data[k_idx, :]
        if k_idx in HARM_DIMENSIONS:
            values = 1.0 - values
        return float(np.sum(values))
    else:
        welfare = rawlsian_maximin_welfare(tensor)
        return float(np.sum(welfare))


def utilitarian_average(
    tensor: "MoralTensor",
    axis: str = "n",
    dimension: Optional[str] = None,
) -> float:
    """
    Compute utilitarian average: mean welfare across parties.

    Average utilitarianism normalizes by party count for
    cross-scenario comparison.

    Args:
        tensor: MoralTensor to aggregate.
        axis: Axis to average over (default "n").
        dimension: Specific dimension. If None, uses aggregate welfare.

    Returns:
        Mean welfare value in [0, 1].
    """
    if tensor.rank < 2:
        raise ValueError(f"Requires rank >= 2 tensor, got rank {tensor.rank}")

    data = tensor.to_dense()
    n_parties = data.shape[1]

    if n_parties == 0:
        return 0.0

    total = utilitarian_sum(tensor, axis=axis, dimension=dimension)
    return float(total / n_parties)


# =============================================================================
# Prioritarian Weighting
# =============================================================================


def prioritarian_weighted_welfare(
    tensor: "MoralTensor",
    vulnerability_weights: Optional[np.ndarray] = None,
    priority_function: str = "linear",
    priority_param: float = 1.0,
) -> float:
    """
    Compute prioritarian weighted welfare.

    Prioritarianism gives extra weight to benefits/welfare of
    worse-off or more vulnerable parties.

    Args:
        tensor: MoralTensor of rank >= 2 with party axis 'n'.
        vulnerability_weights: Per-party vulnerability weights.
            Higher weight = more vulnerable = higher priority.
            If None, uniform weights are used.
        priority_function: Priority weighting function:
            - "linear": w_i * welfare_i (simple weighting)
            - "concave": welfare_i^(1/priority_param) (diminishing returns)
            - "threshold": extra weight below threshold
        priority_param: Parameter for the priority function:
            - For "concave": exponent (values > 1 give more weight to low welfare)
            - For "threshold": welfare threshold value

    Returns:
        Prioritarian-weighted aggregate welfare in [0, 1].
    """
    if tensor.rank < 2:
        raise ValueError(f"Requires rank >= 2 tensor, got rank {tensor.rank}")

    welfare = rawlsian_maximin_welfare(tensor)
    n_parties = len(welfare)

    if n_parties == 0:
        return 0.0

    # Setup vulnerability weights
    if vulnerability_weights is None:
        v_weights = np.ones(n_parties, dtype=np.float64)
    else:
        v_weights = np.asarray(vulnerability_weights, dtype=np.float64)
        if len(v_weights) != n_parties:
            raise ValueError(
                f"vulnerability_weights length {len(v_weights)} != n_parties {n_parties}"
            )

    # Apply priority function
    if priority_function == "linear":
        # Simple weighted average
        weighted = v_weights * welfare
    elif priority_function == "concave":
        # Diminishing returns: welfare^(1/param), then weight
        # Higher param = more weight to lower welfare values
        if priority_param <= 0:
            raise ValueError("priority_param must be > 0 for concave function")
        transformed = np.power(np.clip(welfare, EPSILON, 1.0), 1.0 / priority_param)
        weighted = v_weights * transformed
    elif priority_function == "threshold":
        # Extra weight for parties below threshold
        below_threshold = welfare < priority_param
        adjusted_weights = np.where(below_threshold, v_weights * 2.0, v_weights)
        weighted = adjusted_weights * welfare
    else:
        raise ValueError(
            f"Unknown priority_function: {priority_function}. "
            "Valid: 'linear', 'concave', 'threshold'"
        )

    # Normalize
    total_weight = np.sum(v_weights)
    if total_weight < EPSILON:
        return 0.0

    result = np.sum(weighted) / total_weight
    return float(np.clip(result, 0.0, 1.0))


def extract_vulnerability_weights(facts: "EthicalFactsV3") -> np.ndarray:
    """
    Extract vulnerability weights from EthicalFactsV3.

    Args:
        facts: EthicalFactsV3 with per-party consequences.

    Returns:
        Numpy array of vulnerability weights, one per party.
        Ordered by facts.party_ids.
    """
    party_ids = facts.party_ids
    n = len(party_ids)

    if n == 0:
        return np.array([], dtype=np.float64)

    # Build mapping from party_id to index
    party_to_idx = {pid: i for i, pid in enumerate(party_ids)}

    weights = np.ones(n, dtype=np.float64)

    # Extract from per_party consequences
    for pc in facts.consequences.per_party:
        if pc.party_id in party_to_idx:
            weights[party_to_idx[pc.party_id]] = pc.vulnerability_weight

    return weights


# =============================================================================
# Atkinson Inequality Index
# =============================================================================


def atkinson_index(
    values: Union[np.ndarray, List[float]],
    epsilon: float = 0.5,
) -> float:
    """
    Compute the Atkinson inequality index.

    The Atkinson index is a parametric measure of inequality that
    allows explicit specification of inequality aversion through
    the epsilon parameter.

    Args:
        values: 1D array of non-negative values (welfare distribution).
        epsilon: Inequality aversion parameter:
            - epsilon = 0: No inequality aversion (insensitive)
            - epsilon = 0.5: Moderate aversion (default)
            - epsilon = 1: High aversion (log-sensitivity)
            - epsilon = 2: Very high aversion (focuses on lowest values)
            - epsilon -> infinity: Rawlsian (only cares about minimum)

    Returns:
        Atkinson index in [0, 1]:
            - 0 = perfect equality
            - 1 = complete inequality

    Raises:
        ValueError: If epsilon < 0 or values contain negatives.

    Examples:
        >>> atkinson_index([1, 1, 1, 1], epsilon=0.5)
        0.0
        >>> atkinson_index([0.1, 1.0, 1.0, 1.0], epsilon=2.0)
        0.7...  # Very sensitive to the 0.1
    """
    if epsilon < 0:
        raise ValueError(f"epsilon must be >= 0, got {epsilon}")

    arr = np.asarray(values, dtype=np.float64)

    if np.any(arr < 0):
        raise ValueError("Atkinson index requires non-negative values")

    n = len(arr)

    # Edge cases
    if n <= 1:
        return 0.0

    # Clamp near-zero values for numerical stability
    arr = np.clip(arr, EPSILON, None)

    mu = np.mean(arr)
    if mu < EPSILON:
        return 0.0

    # Normalize by mean
    y_ratio = arr / mu

    # Compute based on epsilon value
    if abs(epsilon - 1.0) < EPSILON:
        # Special case: epsilon = 1 (geometric mean formula)
        log_sum = np.sum(np.log(y_ratio))
        geometric_term = np.exp(log_sum / n)
        result = 1.0 - geometric_term
    else:
        # General formula
        power = 1.0 - epsilon
        powered_sum = np.sum(np.power(y_ratio, power))
        mean_powered = powered_sum / n
        result = 1.0 - np.power(mean_powered, 1.0 / power)

    return float(np.clip(result, 0.0, 1.0))


# =============================================================================
# Theil Index (Generalized Entropy)
# =============================================================================


def theil_index(
    values: Union[np.ndarray, List[float]],
    alpha: float = 1.0,
) -> float:
    """
    Compute the Theil index (Generalized Entropy GE(alpha)).

    The Theil index is an entropy-based inequality measure from
    information theory.

    Args:
        values: 1D array of non-negative values.
        alpha: Sensitivity parameter:
            - alpha = 0: Theil's L (mean log deviation, sensitive to lower end)
            - alpha = 1: Theil's T (standard Theil, balanced sensitivity)
            - alpha = 2: Half the squared coefficient of variation

    Returns:
        Theil index >= 0:
            - 0 = perfect equality
            - Higher values = more inequality
            (Not bounded to [0,1] unlike Gini/Atkinson)

    Raises:
        ValueError: If alpha < 0 or values contain negatives.

    Examples:
        >>> theil_index([1, 1, 1, 1])
        0.0
        >>> theil_index([1, 2, 3, 4])
        0.107...
    """
    if alpha < 0:
        raise ValueError(f"alpha must be >= 0, got {alpha}")

    arr = np.asarray(values, dtype=np.float64)

    if np.any(arr < 0):
        raise ValueError("Theil index requires non-negative values")

    n = len(arr)

    # Edge cases
    if n <= 1:
        return 0.0

    # Clamp near-zero values
    arr = np.clip(arr, EPSILON, None)

    mu = np.mean(arr)
    if mu < EPSILON:
        return 0.0

    y_ratio = arr / mu

    if abs(alpha) < EPSILON:
        # Theil's L (GE(0)): mean log deviation
        result = np.mean(np.log(1.0 / y_ratio))
    elif abs(alpha - 1.0) < EPSILON:
        # Theil's T (GE(1)): standard Theil index
        result = np.mean(y_ratio * np.log(y_ratio))
    else:
        # General formula
        powered = np.power(y_ratio, alpha)
        result = (np.mean(powered) - 1.0) / (alpha * (alpha - 1.0))

    return float(max(0.0, result))


def theil_decomposition(
    tensor: "MoralTensor",
    group_axis: str = "n",
) -> Dict[str, float]:
    """
    Decompose Theil index into between-dimension and within-dimension components.

    The Theil index is decomposable: total inequality can be
    split into between-group and within-group components.

    Args:
        tensor: MoralTensor to analyze.
        group_axis: Axis defining groups (default "n" for parties).

    Returns:
        Dict with keys:
            - "total": Total Theil index
            - "between": Between-group inequality
            - "within": Within-group inequality
            - "between_share": Proportion due to between-group
    """
    if tensor.rank < 2:
        raise ValueError(f"Requires rank >= 2 tensor, got rank {tensor.rank}")

    data = tensor.to_dense()
    n_dims = data.shape[0]  # 9
    n_parties = data.shape[1]

    if n_parties <= 1:
        return {
            "total": 0.0,
            "between": 0.0,
            "within": 0.0,
            "between_share": 0.0,
        }

    # Flatten all values for total
    all_values = data.flatten()
    all_values = np.clip(all_values, EPSILON, None)
    total_theil = theil_index(all_values, alpha=1.0)

    # Compute between-group (dimensions as groups)
    dim_means = np.mean(data, axis=1)  # Mean per dimension
    dim_means = np.clip(dim_means, EPSILON, None)
    between_theil = theil_index(dim_means, alpha=1.0)

    # Within-group: weighted average of Theil within each dimension
    grand_mean = np.mean(all_values)
    within_theil = 0.0

    for k in range(n_dims):
        dim_values = data[k, :]
        dim_values = np.clip(dim_values, EPSILON, None)
        dim_mean = np.mean(dim_values)
        weight = (dim_mean * n_parties) / (grand_mean * n_dims * n_parties)
        within_theil += weight * theil_index(dim_values, alpha=1.0)

    # Between share
    if total_theil > EPSILON:
        between_share = between_theil / total_theil
    else:
        between_share = 0.0

    return {
        "total": total_theil,
        "between": between_theil,
        "within": within_theil,
        "between_share": float(np.clip(between_share, 0.0, 1.0)),
    }


# =============================================================================
# FairnessMetrics Aggregate Class
# =============================================================================


@dataclass(frozen=True)
class FairnessMetrics:
    """
    Aggregated fairness metrics for a MoralTensor or EthicalFactsV3.

    This dataclass provides a snapshot of all distributional fairness
    metrics for a given ethical assessment, suitable for:
    - Decision audit trails
    - Comparative analysis
    - Governance reporting
    - Serialization to JSON

    Attributes:
        gini: Gini coefficient for overall welfare distribution [0, 1].
        gini_per_dimension: Per-dimension Gini coefficients (9 values).
        maximin_welfare: Welfare of the worst-off party [0, 1].
        maximin_party_index: Index of the worst-off party.
        maximin_party_label: Label of worst-off party (if available).
        utilitarian_sum: Total welfare across all parties.
        utilitarian_avg: Average welfare per party [0, 1].
        prioritarian_welfare: Vulnerability-weighted welfare [0, 1].
        atkinson_05: Atkinson index with epsilon=0.5.
        atkinson_10: Atkinson index with epsilon=1.0.
        atkinson_20: Atkinson index with epsilon=2.0.
        theil_t: Theil T index (GE(1)).
        theil_l: Theil L index (GE(0)).
        n_parties: Number of parties in the distribution.
        party_labels: List of party labels (if available).
    """

    # Core distribution metrics
    gini: float
    gini_per_dimension: Tuple[float, ...]  # 9 values

    # Rawlsian maximin
    maximin_welfare: float
    maximin_party_index: int
    maximin_party_label: Optional[str]

    # Utilitarian
    utilitarian_sum: float
    utilitarian_avg: float

    # Prioritarian
    prioritarian_welfare: float

    # Atkinson indices
    atkinson_05: float
    atkinson_10: float
    atkinson_20: float

    # Theil indices
    theil_t: float
    theil_l: float

    # Metadata
    n_parties: int
    party_labels: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_tensor(
        cls,
        tensor: "MoralTensor",
        vulnerability_weights: Optional[np.ndarray] = None,
    ) -> "FairnessMetrics":
        """
        Compute all fairness metrics from a MoralTensor.

        Args:
            tensor: MoralTensor of rank >= 2 with party axis 'n'.
            vulnerability_weights: Optional per-party vulnerability weights.

        Returns:
            FairnessMetrics with all computed values.

        Raises:
            ValueError: If tensor has rank < 2 or no party axis.
        """
        if tensor.rank < 2:
            raise ValueError(
                f"FairnessMetrics requires rank >= 2 tensor, got rank {tensor.rank}"
            )

        data = tensor.to_dense()
        n_parties = data.shape[1]

        # Get party labels if available
        party_labels = tuple(
            tensor.axis_labels.get("n", [f"party_{i}" for i in range(n_parties)])
        )

        # Compute welfare for overall metrics
        welfare = rawlsian_maximin_welfare(tensor)

        # Gini for overall welfare
        overall_gini = gini_coefficient(welfare)

        # Per-dimension Gini
        gini_per_dim = []
        for k in range(9):
            dim_values = data[k, :].copy()
            if k in HARM_DIMENSIONS:
                dim_values = 1.0 - dim_values
            gini_per_dim.append(gini_coefficient(dim_values))

        # Maximin
        min_welfare, min_idx = rawlsian_maximin(tensor, return_party_index=True)
        min_label = party_labels[min_idx] if min_idx < len(party_labels) else None

        # Utilitarian
        util_sum = utilitarian_sum(tensor)
        util_avg = utilitarian_average(tensor)

        # Prioritarian
        prior_welfare = prioritarian_weighted_welfare(
            tensor, vulnerability_weights=vulnerability_weights
        )

        # Atkinson indices
        atk_05 = atkinson_index(welfare, epsilon=0.5)
        atk_10 = atkinson_index(welfare, epsilon=1.0)
        atk_20 = atkinson_index(welfare, epsilon=2.0)

        # Theil indices
        theil_t_val = theil_index(welfare, alpha=1.0)
        theil_l_val = theil_index(welfare, alpha=0.0)

        return cls(
            gini=overall_gini,
            gini_per_dimension=tuple(gini_per_dim),
            maximin_welfare=min_welfare,
            maximin_party_index=min_idx,
            maximin_party_label=min_label,
            utilitarian_sum=util_sum,
            utilitarian_avg=util_avg,
            prioritarian_welfare=prior_welfare,
            atkinson_05=atk_05,
            atkinson_10=atk_10,
            atkinson_20=atk_20,
            theil_t=theil_t_val,
            theil_l=theil_l_val,
            n_parties=n_parties,
            party_labels=party_labels,
        )

    @classmethod
    def from_facts(
        cls,
        facts: "EthicalFactsV3",
    ) -> "FairnessMetrics":
        """
        Compute fairness metrics from EthicalFactsV3.

        Convenience method that extracts vulnerability weights from
        per-party consequences and converts to MoralTensor.

        Args:
            facts: EthicalFactsV3 with per-party tracking.

        Returns:
            FairnessMetrics with all computed values.
        """
        tensor = facts.to_moral_tensor()
        vuln_weights = extract_vulnerability_weights(facts)

        # Handle empty weights
        if len(vuln_weights) == 0:
            vuln_weights = None

        return cls.from_tensor(tensor, vulnerability_weights=vuln_weights)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "gini": self.gini,
            "gini_per_dimension": list(self.gini_per_dimension),
            "maximin_welfare": self.maximin_welfare,
            "maximin_party_index": self.maximin_party_index,
            "maximin_party_label": self.maximin_party_label,
            "utilitarian_sum": self.utilitarian_sum,
            "utilitarian_avg": self.utilitarian_avg,
            "prioritarian_welfare": self.prioritarian_welfare,
            "atkinson_05": self.atkinson_05,
            "atkinson_10": self.atkinson_10,
            "atkinson_20": self.atkinson_20,
            "theil_t": self.theil_t,
            "theil_l": self.theil_l,
            "n_parties": self.n_parties,
            "party_labels": list(self.party_labels),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FairnessMetrics":
        """Deserialize from dict."""
        return cls(
            gini=float(data["gini"]),
            gini_per_dimension=tuple(data["gini_per_dimension"]),
            maximin_welfare=float(data["maximin_welfare"]),
            maximin_party_index=int(data["maximin_party_index"]),
            maximin_party_label=data.get("maximin_party_label"),
            utilitarian_sum=float(data["utilitarian_sum"]),
            utilitarian_avg=float(data["utilitarian_avg"]),
            prioritarian_welfare=float(data["prioritarian_welfare"]),
            atkinson_05=float(data["atkinson_05"]),
            atkinson_10=float(data["atkinson_10"]),
            atkinson_20=float(data["atkinson_20"]),
            theil_t=float(data["theil_t"]),
            theil_l=float(data["theil_l"]),
            n_parties=int(data["n_parties"]),
            party_labels=tuple(data.get("party_labels", [])),
        )

    def summary(self) -> str:
        """Generate human-readable summary string."""
        lines = [
            "FairnessMetrics Summary",
            "=" * 40,
            f"Parties: {self.n_parties}",
            "",
            "Inequality Measures:",
            f"  Gini coefficient:    {self.gini:.4f}",
            f"  Atkinson (e=0.5):    {self.atkinson_05:.4f}",
            f"  Atkinson (e=1.0):    {self.atkinson_10:.4f}",
            f"  Atkinson (e=2.0):    {self.atkinson_20:.4f}",
            f"  Theil T (GE(1)):     {self.theil_t:.4f}",
            f"  Theil L (GE(0)):     {self.theil_l:.4f}",
            "",
            "Aggregation:",
            f"  Utilitarian sum:     {self.utilitarian_sum:.4f}",
            f"  Utilitarian avg:     {self.utilitarian_avg:.4f}",
            f"  Prioritarian:        {self.prioritarian_welfare:.4f}",
            "",
            "Rawlsian Maximin:",
            f"  Worst-off welfare:   {self.maximin_welfare:.4f}",
            f"  Worst-off party:     {self.maximin_party_label or f'index {self.maximin_party_index}'}",
        ]
        return "\n".join(lines)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Constants
    "EPSILON",
    # Core functions
    "gini_coefficient",
    "rawlsian_maximin",
    "rawlsian_maximin_welfare",
    "utilitarian_sum",
    "utilitarian_average",
    "prioritarian_weighted_welfare",
    "extract_vulnerability_weights",
    "atkinson_index",
    "theil_index",
    "theil_decomposition",
    # Aggregate class
    "FairnessMetrics",
]
