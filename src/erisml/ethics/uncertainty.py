# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Uncertainty Quantification for DEME V3.

Sprint 14: Provides Monte Carlo uncertainty propagation for ethical
decision-making under uncertainty. Enables risk-aware ethics through:

- Rank-5 tensors with sample axis for Monte Carlo samples
- Sample generation from various distributions
- Expected value, variance, and percentile computation
- Conditional Value at Risk (CVaR) for tail risk
- Robust/worst-case aggregation methods
- Confidence interval computation

Tensor Shape Convention for Rank-5:
    (d, n, t, c, s) where:
    - d: moral dimensions (9)
    - n: parties/agents
    - t: time steps
    - c: coalitions/scenarios
    - s: Monte Carlo samples

Version: 3.0.0 (DEME V3 Sprint 14)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Numerical stability
EPSILON = 1e-10


class DistributionType(Enum):
    """Supported probability distributions for uncertainty."""

    NORMAL = "normal"
    UNIFORM = "uniform"
    BETA = "beta"
    TRIANGULAR = "triangular"
    TRUNCATED_NORMAL = "truncated_normal"
    DIRICHLET = "dirichlet"


class AggregationMethod(Enum):
    """Methods for aggregating uncertain values."""

    EXPECTED_VALUE = "expected_value"
    MEDIAN = "median"
    WORST_CASE = "worst_case"
    BEST_CASE = "best_case"
    CVAR = "cvar"  # Conditional Value at Risk
    ROBUST = "robust"  # Worst percentile


@dataclass(frozen=True)
class UncertaintyBounds:
    """
    Uncertainty bounds for a value.

    Attributes:
        mean: Expected value.
        std: Standard deviation.
        lower: Lower bound (e.g., 5th percentile).
        upper: Upper bound (e.g., 95th percentile).
        confidence: Confidence level (e.g., 0.90 for 90%).
    """

    mean: float
    std: float
    lower: float
    upper: float
    confidence: float = 0.90

    def contains(self, value: float) -> bool:
        """Check if value is within bounds."""
        return self.lower <= value <= self.upper

    def width(self) -> float:
        """Width of the confidence interval."""
        return self.upper - self.lower

    def relative_width(self) -> float:
        """Relative width (coefficient of variation style)."""
        if abs(self.mean) < EPSILON:
            return float("inf") if self.width() > EPSILON else 0.0
        return self.width() / abs(self.mean)


@dataclass
class UncertainValue:
    """
    A value with associated uncertainty represented by samples.

    Attributes:
        samples: Array of Monte Carlo samples.
        name: Optional name/label for the value.
    """

    samples: np.ndarray
    name: Optional[str] = None

    def __post_init__(self):
        self.samples = np.asarray(self.samples, dtype=np.float64)

    @property
    def n_samples(self) -> int:
        """Number of samples."""
        return len(self.samples)

    @property
    def mean(self) -> float:
        """Expected value."""
        return float(np.mean(self.samples))

    @property
    def std(self) -> float:
        """Standard deviation."""
        return float(np.std(self.samples, ddof=1))

    @property
    def var(self) -> float:
        """Variance."""
        return float(np.var(self.samples, ddof=1))

    @property
    def median(self) -> float:
        """Median value."""
        return float(np.median(self.samples))

    def percentile(self, q: float) -> float:
        """Get percentile (0-100)."""
        return float(np.percentile(self.samples, q))

    def quantile(self, q: float) -> float:
        """Get quantile (0-1)."""
        return float(np.quantile(self.samples, q))

    def bounds(self, confidence: float = 0.90) -> UncertaintyBounds:
        """Get uncertainty bounds at given confidence level."""
        alpha = (1 - confidence) / 2
        lower = self.quantile(alpha)
        upper = self.quantile(1 - alpha)
        return UncertaintyBounds(
            mean=self.mean,
            std=self.std,
            lower=lower,
            upper=upper,
            confidence=confidence,
        )

    def cvar(self, alpha: float = 0.05) -> float:
        """
        Conditional Value at Risk (Expected Shortfall).

        Returns the expected value of the worst alpha fraction of outcomes.
        Lower values indicate higher risk.

        Args:
            alpha: Tail probability (e.g., 0.05 for worst 5%).

        Returns:
            CVaR value.
        """
        cutoff = self.quantile(alpha)
        tail_samples = self.samples[self.samples <= cutoff]
        if len(tail_samples) == 0:
            return cutoff
        return float(np.mean(tail_samples))

    def cvar_upper(self, alpha: float = 0.05) -> float:
        """
        Upper-tail CVaR (best outcomes).

        Returns the expected value of the best alpha fraction of outcomes.

        Args:
            alpha: Tail probability (e.g., 0.05 for best 5%).

        Returns:
            Upper CVaR value.
        """
        cutoff = self.quantile(1 - alpha)
        tail_samples = self.samples[self.samples >= cutoff]
        if len(tail_samples) == 0:
            return cutoff
        return float(np.mean(tail_samples))

    def robust_value(self, percentile: float = 5.0) -> float:
        """
        Robust (worst-case) value at given percentile.

        Args:
            percentile: Percentile for worst-case (0-100).

        Returns:
            Value at specified percentile.
        """
        return self.percentile(percentile)


# =============================================================================
# Sample Generation
# =============================================================================


def generate_samples(
    distribution: DistributionType,
    n_samples: int,
    shape: Tuple[int, ...] = (),
    **params,
) -> np.ndarray:
    """
    Generate Monte Carlo samples from a distribution.

    Args:
        distribution: Type of distribution.
        n_samples: Number of samples to generate.
        shape: Shape of each sample (default scalar).
        **params: Distribution-specific parameters.

    Returns:
        Array of shape (*shape, n_samples).

    Examples:
        # Normal distribution
        samples = generate_samples(
            DistributionType.NORMAL, 1000,
            mean=0.5, std=0.1
        )

        # Beta distribution (good for [0,1] bounded values)
        samples = generate_samples(
            DistributionType.BETA, 1000,
            alpha=2.0, beta=5.0
        )
    """
    rng = np.random.default_rng(params.get("seed"))
    full_shape = (*shape, n_samples) if shape else (n_samples,)

    if distribution == DistributionType.NORMAL:
        mean = params.get("mean", 0.0)
        std = params.get("std", 1.0)
        samples = rng.normal(mean, std, full_shape)

    elif distribution == DistributionType.UNIFORM:
        low = params.get("low", 0.0)
        high = params.get("high", 1.0)
        samples = rng.uniform(low, high, full_shape)

    elif distribution == DistributionType.BETA:
        alpha = params.get("alpha", 2.0)
        beta = params.get("beta", 2.0)
        samples = rng.beta(alpha, beta, full_shape)

    elif distribution == DistributionType.TRIANGULAR:
        left = params.get("left", 0.0)
        mode = params.get("mode", 0.5)
        right = params.get("right", 1.0)
        samples = rng.triangular(left, mode, right, full_shape)

    elif distribution == DistributionType.TRUNCATED_NORMAL:
        mean = params.get("mean", 0.5)
        std = params.get("std", 0.1)
        low = params.get("low", 0.0)
        high = params.get("high", 1.0)
        # Generate and truncate
        samples = rng.normal(mean, std, full_shape)
        samples = np.clip(samples, low, high)

    elif distribution == DistributionType.DIRICHLET:
        alpha = params.get("alpha", np.ones(shape[-1]) if shape else np.ones(9))
        # Dirichlet generates (n_samples, len(alpha))
        samples = rng.dirichlet(alpha, n_samples)
        if shape:
            samples = samples.reshape(full_shape)

    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    return samples


def generate_moral_samples(
    base_values: np.ndarray,
    n_samples: int,
    uncertainty: float = 0.1,
    distribution: DistributionType = DistributionType.TRUNCATED_NORMAL,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generate Monte Carlo samples around base moral values.

    Adds a sample axis to the input array, generating samples that
    respect the [0, 1] bounds typical of moral values.

    Args:
        base_values: Base moral values of any shape.
        n_samples: Number of samples to generate.
        uncertainty: Relative uncertainty (std as fraction of value).
        distribution: Distribution type for sampling.
        seed: Random seed for reproducibility.

    Returns:
        Array with shape (*base_values.shape, n_samples).
    """
    rng = np.random.default_rng(seed)
    base = np.asarray(base_values, dtype=np.float64)

    # Compute per-element standard deviation
    # Scale uncertainty based on distance from bounds
    distance_to_bounds = np.minimum(base, 1.0 - base)
    std = np.clip(uncertainty * distance_to_bounds + EPSILON, EPSILON, 0.5)

    # Generate samples
    output_shape = (*base.shape, n_samples)

    if distribution == DistributionType.TRUNCATED_NORMAL:
        samples = rng.normal(
            base[..., np.newaxis],
            std[..., np.newaxis],
            output_shape,
        )
        samples = np.clip(samples, 0.0, 1.0)

    elif distribution == DistributionType.BETA:
        # Convert mean/std to alpha/beta parameters
        # Using method of moments
        mean = np.clip(base, EPSILON, 1 - EPSILON)
        var = np.clip(std**2, EPSILON, mean * (1 - mean) - EPSILON)

        # Alpha and beta from mean and variance
        common = mean * (1 - mean) / var - 1
        alpha = np.maximum(mean * common, EPSILON)
        beta = np.maximum((1 - mean) * common, EPSILON)

        samples = rng.beta(
            alpha[..., np.newaxis],
            beta[..., np.newaxis],
            output_shape,
        )

    else:
        # Default to truncated normal
        samples = rng.normal(
            base[..., np.newaxis],
            std[..., np.newaxis],
            output_shape,
        )
        samples = np.clip(samples, 0.0, 1.0)

    return samples


# =============================================================================
# Statistical Aggregation
# =============================================================================


def expected_value(
    samples: np.ndarray,
    axis: int = -1,
    weights: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Compute expected value (mean) over sample axis.

    Args:
        samples: Array with sample axis.
        axis: Axis containing samples (default -1).
        weights: Optional sample weights.

    Returns:
        Array with sample axis removed.
    """
    if weights is not None:
        weights = np.asarray(weights)
        weights = weights / np.sum(weights)
        return np.tensordot(samples, weights, axes=([axis], [0]))
    return np.mean(samples, axis=axis)


def variance(
    samples: np.ndarray,
    axis: int = -1,
    ddof: int = 1,
) -> np.ndarray:
    """
    Compute variance over sample axis.

    Args:
        samples: Array with sample axis.
        axis: Axis containing samples.
        ddof: Delta degrees of freedom.

    Returns:
        Variance array.
    """
    return np.var(samples, axis=axis, ddof=ddof)


def std_dev(
    samples: np.ndarray,
    axis: int = -1,
    ddof: int = 1,
) -> np.ndarray:
    """
    Compute standard deviation over sample axis.

    Args:
        samples: Array with sample axis.
        axis: Axis containing samples.
        ddof: Delta degrees of freedom.

    Returns:
        Standard deviation array.
    """
    return np.std(samples, axis=axis, ddof=ddof)


def percentiles(
    samples: np.ndarray,
    q: Union[float, List[float]],
    axis: int = -1,
) -> np.ndarray:
    """
    Compute percentiles over sample axis.

    Args:
        samples: Array with sample axis.
        q: Percentile(s) to compute (0-100).
        axis: Axis containing samples.

    Returns:
        Percentile values.
    """
    return np.percentile(samples, q, axis=axis)


def confidence_interval(
    samples: np.ndarray,
    confidence: float = 0.90,
    axis: int = -1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute confidence interval over sample axis.

    Args:
        samples: Array with sample axis.
        confidence: Confidence level (0-1).
        axis: Axis containing samples.

    Returns:
        Tuple of (lower_bound, upper_bound) arrays.
    """
    alpha = (1 - confidence) / 2
    lower = np.percentile(samples, alpha * 100, axis=axis)
    upper = np.percentile(samples, (1 - alpha) * 100, axis=axis)
    return lower, upper


# =============================================================================
# Risk Measures
# =============================================================================


def cvar(
    samples: np.ndarray,
    alpha: float = 0.05,
    axis: int = -1,
) -> np.ndarray:
    """
    Conditional Value at Risk (Expected Shortfall).

    Computes the expected value of the worst alpha fraction of outcomes.
    Used for risk-aware ethical decision making.

    Args:
        samples: Array with sample axis.
        alpha: Tail probability (e.g., 0.05 for worst 5%).
        axis: Axis containing samples.

    Returns:
        CVaR values (lower is more risky).
    """
    # Move sample axis to last position for easier processing
    samples = np.moveaxis(samples, axis, -1)
    n_samples = samples.shape[-1]

    # Sort samples along last axis
    sorted_samples = np.sort(samples, axis=-1)

    # Number of samples in tail
    n_tail = max(1, int(np.ceil(alpha * n_samples)))

    # Mean of worst n_tail samples
    tail_samples = sorted_samples[..., :n_tail]
    return np.mean(tail_samples, axis=-1)


def cvar_upper(
    samples: np.ndarray,
    alpha: float = 0.05,
    axis: int = -1,
) -> np.ndarray:
    """
    Upper-tail CVaR (expected value of best outcomes).

    Args:
        samples: Array with sample axis.
        alpha: Tail probability.
        axis: Axis containing samples.

    Returns:
        Upper CVaR values.
    """
    samples = np.moveaxis(samples, axis, -1)
    n_samples = samples.shape[-1]

    sorted_samples = np.sort(samples, axis=-1)
    n_tail = max(1, int(np.ceil(alpha * n_samples)))

    tail_samples = sorted_samples[..., -n_tail:]
    return np.mean(tail_samples, axis=-1)


def worst_case(
    samples: np.ndarray,
    percentile: float = 5.0,
    axis: int = -1,
) -> np.ndarray:
    """
    Worst-case (robust) value at given percentile.

    Args:
        samples: Array with sample axis.
        percentile: Percentile for worst case (0-100).
        axis: Axis containing samples.

    Returns:
        Worst-case values.
    """
    return np.percentile(samples, percentile, axis=axis)


def best_case(
    samples: np.ndarray,
    percentile: float = 95.0,
    axis: int = -1,
) -> np.ndarray:
    """
    Best-case value at given percentile.

    Args:
        samples: Array with sample axis.
        percentile: Percentile for best case (0-100).
        axis: Axis containing samples.

    Returns:
        Best-case values.
    """
    return np.percentile(samples, percentile, axis=axis)


def value_at_risk(
    samples: np.ndarray,
    alpha: float = 0.05,
    axis: int = -1,
) -> np.ndarray:
    """
    Value at Risk (VaR) - the alpha quantile.

    Args:
        samples: Array with sample axis.
        alpha: Tail probability.
        axis: Axis containing samples.

    Returns:
        VaR values.
    """
    return np.percentile(samples, alpha * 100, axis=axis)


# =============================================================================
# Aggregation Functions
# =============================================================================


def aggregate_samples(
    samples: np.ndarray,
    method: AggregationMethod = AggregationMethod.EXPECTED_VALUE,
    axis: int = -1,
    **kwargs,
) -> np.ndarray:
    """
    Aggregate samples using specified method.

    Args:
        samples: Array with sample axis.
        method: Aggregation method.
        axis: Axis containing samples.
        **kwargs: Method-specific parameters.

    Returns:
        Aggregated values.
    """
    if method == AggregationMethod.EXPECTED_VALUE:
        return expected_value(samples, axis=axis)

    elif method == AggregationMethod.MEDIAN:
        return np.median(samples, axis=axis)

    elif method == AggregationMethod.WORST_CASE:
        percentile = kwargs.get("percentile", 5.0)
        return worst_case(samples, percentile=percentile, axis=axis)

    elif method == AggregationMethod.BEST_CASE:
        percentile = kwargs.get("percentile", 95.0)
        return best_case(samples, percentile=percentile, axis=axis)

    elif method == AggregationMethod.CVAR:
        alpha = kwargs.get("alpha", 0.05)
        return cvar(samples, alpha=alpha, axis=axis)

    elif method == AggregationMethod.ROBUST:
        percentile = kwargs.get("percentile", 5.0)
        return worst_case(samples, percentile=percentile, axis=axis)

    else:
        raise ValueError(f"Unknown aggregation method: {method}")


# =============================================================================
# Uncertainty Propagation
# =============================================================================


@dataclass
class UncertaintyAnalysis:
    """
    Results of uncertainty analysis on moral values.

    Attributes:
        mean: Expected values.
        std: Standard deviations.
        lower: Lower confidence bounds.
        upper: Upper confidence bounds.
        cvar: Conditional Value at Risk (worst-case expected).
        var: Value at Risk (worst-case threshold).
        confidence: Confidence level used.
        n_samples: Number of Monte Carlo samples.
    """

    mean: np.ndarray
    std: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    cvar: np.ndarray
    var: np.ndarray
    confidence: float
    n_samples: int

    def summary(self) -> str:
        """Generate summary string."""
        lines = [
            "Uncertainty Analysis Results",
            "=" * 40,
            f"Samples: {self.n_samples}",
            f"Confidence: {self.confidence:.0%}",
            f"Mean: {np.mean(self.mean):.4f} (range: {np.min(self.mean):.4f} - {np.max(self.mean):.4f})",
            f"Std:  {np.mean(self.std):.4f} (range: {np.min(self.std):.4f} - {np.max(self.std):.4f})",
            f"CVaR: {np.mean(self.cvar):.4f} (worst-case expected)",
            f"VaR:  {np.mean(self.var):.4f} (5% worst threshold)",
        ]
        return "\n".join(lines)


def analyze_uncertainty(
    samples: np.ndarray,
    axis: int = -1,
    confidence: float = 0.90,
    cvar_alpha: float = 0.05,
) -> UncertaintyAnalysis:
    """
    Perform comprehensive uncertainty analysis.

    Args:
        samples: Array with sample axis.
        axis: Axis containing samples.
        confidence: Confidence level for intervals.
        cvar_alpha: Alpha for CVaR computation.

    Returns:
        UncertaintyAnalysis with all metrics.
    """
    n_samples = samples.shape[axis]

    mean = expected_value(samples, axis=axis)
    std = std_dev(samples, axis=axis)
    lower, upper = confidence_interval(samples, confidence=confidence, axis=axis)
    cvar_values = cvar(samples, alpha=cvar_alpha, axis=axis)
    var_values = value_at_risk(samples, alpha=cvar_alpha, axis=axis)

    return UncertaintyAnalysis(
        mean=mean,
        std=std,
        lower=lower,
        upper=upper,
        cvar=cvar_values,
        var=var_values,
        confidence=confidence,
        n_samples=n_samples,
    )


def propagate_uncertainty(
    base_tensor: np.ndarray,
    n_samples: int = 1000,
    uncertainty: float = 0.1,
    distribution: DistributionType = DistributionType.TRUNCATED_NORMAL,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, UncertaintyAnalysis]:
    """
    Propagate uncertainty through moral tensor.

    Generates Monte Carlo samples and analyzes uncertainty.

    Args:
        base_tensor: Base moral values (any shape).
        n_samples: Number of Monte Carlo samples.
        uncertainty: Relative uncertainty level.
        distribution: Distribution for sampling.
        seed: Random seed.

    Returns:
        Tuple of (samples array, uncertainty analysis).
    """
    samples = generate_moral_samples(
        base_tensor,
        n_samples=n_samples,
        uncertainty=uncertainty,
        distribution=distribution,
        seed=seed,
    )

    analysis = analyze_uncertainty(samples, axis=-1)

    return samples, analysis


# =============================================================================
# Risk-Aware Decision Support
# =============================================================================


def compare_under_uncertainty(
    samples_a: np.ndarray,
    samples_b: np.ndarray,
    method: AggregationMethod = AggregationMethod.EXPECTED_VALUE,
    axis: int = -1,
) -> Tuple[bool, float]:
    """
    Compare two uncertain alternatives.

    Args:
        samples_a: Samples for alternative A.
        samples_b: Samples for alternative B.
        method: Aggregation method for comparison.
        axis: Sample axis.

    Returns:
        Tuple of (a_preferred, confidence) where confidence is
        the probability that A > B.
    """
    # Point estimates
    value_a = aggregate_samples(samples_a, method=method, axis=axis)
    value_b = aggregate_samples(samples_b, method=method, axis=axis)

    # Probability that A > B (sample-wise comparison)
    a_better = np.mean(samples_a > samples_b, axis=axis)
    confidence = float(np.mean(a_better))

    a_preferred = float(np.mean(value_a)) > float(np.mean(value_b))

    return a_preferred, confidence


def stochastic_dominance(
    samples_a: np.ndarray,
    samples_b: np.ndarray,
    order: int = 1,
    axis: int = -1,
) -> bool:
    """
    Check if A stochastically dominates B.

    First-order: A's CDF is always <= B's CDF (A is always better)
    Second-order: Integral of A's CDF <= integral of B's CDF

    Args:
        samples_a: Samples for alternative A.
        samples_b: Samples for alternative B.
        order: Dominance order (1 or 2).
        axis: Sample axis.

    Returns:
        True if A dominates B.
    """
    # Flatten for comparison
    a = samples_a.flatten()
    b = samples_b.flatten()

    # Common evaluation points
    all_values = np.sort(np.concatenate([a, b]))

    # CDFs
    cdf_a = np.searchsorted(np.sort(a), all_values, side="right") / len(a)
    cdf_b = np.searchsorted(np.sort(b), all_values, side="right") / len(b)

    if order == 1:
        # First-order: A's CDF <= B's CDF everywhere (A is better)
        return bool(np.all(cdf_a <= cdf_b + EPSILON))
    elif order == 2:
        # Second-order: cumulative CDF
        cum_cdf_a = np.cumsum(cdf_a)
        cum_cdf_b = np.cumsum(cdf_b)
        return bool(np.all(cum_cdf_a <= cum_cdf_b + EPSILON))
    else:
        raise ValueError(f"Unsupported dominance order: {order}")


# =============================================================================
# Module Exports
# =============================================================================


__all__ = [
    # Types
    "DistributionType",
    "AggregationMethod",
    "UncertaintyBounds",
    "UncertainValue",
    "UncertaintyAnalysis",
    # Sample generation
    "generate_samples",
    "generate_moral_samples",
    # Statistics
    "expected_value",
    "variance",
    "std_dev",
    "percentiles",
    "confidence_interval",
    # Risk measures
    "cvar",
    "cvar_upper",
    "worst_case",
    "best_case",
    "value_at_risk",
    # Aggregation
    "aggregate_samples",
    # Analysis
    "analyze_uncertainty",
    "propagate_uncertainty",
    # Decision support
    "compare_under_uncertainty",
    "stochastic_dominance",
    # Constants
    "EPSILON",
]
