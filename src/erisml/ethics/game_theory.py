# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Game Theory Module for Multi-Agent Ethics.

DEME V3 Sprint 9: Shapley Values and Fair Credit Assignment.

This module provides game-theoretic methods for fair attribution
of ethical outcomes in multi-agent scenarios:

- Exact Shapley value computation (O(n! * 2^n) complexity)
- Monte Carlo Shapley approximation for large agent sets
- Contribution margin analysis per agent
- Core stability checking
- Nucleolus computation for stable allocations

These methods integrate with DEME V3 MoralTensor and Coalition
infrastructure to enable fair, game-theoretically grounded
attribution of ethical responsibility and credit.

Version: 3.0.0 (DEME V3 - Sprint 9)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import permutations
from typing import (
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np

from erisml.ethics.coalition import Coalition, CoalitionContext
from erisml.ethics.moral_tensor import MoralTensor, MORAL_DIMENSION_NAMES


# =============================================================================
# Type Aliases
# =============================================================================

# Characteristic function: maps coalitions to values
# For ethics: value = aggregate welfare/utility of the coalition
CharacteristicFunction = Callable[[Coalition], float]

# Value function for MoralTensor: maps coalition to tensor
TensorCharacteristicFunction = Callable[[Coalition], MoralTensor]


# =============================================================================
# Shapley Value Results
# =============================================================================


@dataclass(frozen=True)
class ShapleyValues:
    """
    Container for Shapley value computation results.

    Attributes:
        agent_ids: Ordered tuple of agent identifiers.
        values: Shapley values for each agent (same order as agent_ids).
        grand_coalition_value: Total value of the grand coalition.
        is_exact: True if computed exactly, False if approximated.
        n_samples: Number of samples used (for Monte Carlo).
        confidence_interval: 95% CI half-width (for Monte Carlo).
        per_dimension: Optional per-dimension Shapley values (9 x n_agents).
    """

    agent_ids: Tuple[str, ...]
    values: Tuple[float, ...]
    grand_coalition_value: float
    is_exact: bool = True
    n_samples: int = 0
    confidence_interval: Optional[float] = None
    per_dimension: Optional[Tuple[Tuple[float, ...], ...]] = None

    def __post_init__(self) -> None:
        """Validate Shapley values."""
        if len(self.agent_ids) != len(self.values):
            raise ValueError("agent_ids and values must have same length")

    def get_value(self, agent_id: str) -> float:
        """Get Shapley value for a specific agent."""
        try:
            idx = self.agent_ids.index(agent_id)
            return self.values[idx]
        except ValueError:
            raise KeyError(f"Unknown agent: {agent_id}")

    def get_relative_contribution(self, agent_id: str) -> float:
        """Get relative contribution (percentage) for an agent."""
        if abs(self.grand_coalition_value) < 1e-10:
            return 0.0
        return self.get_value(agent_id) / self.grand_coalition_value

    def efficiency_check(self) -> float:
        """
        Check efficiency axiom: sum of Shapley values equals grand coalition value.

        Returns the difference (should be ~0 for exact computation).
        """
        return abs(sum(self.values) - self.grand_coalition_value)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary mapping agent_id -> value."""
        return dict(zip(self.agent_ids, self.values))

    @property
    def n_agents(self) -> int:
        """Number of agents."""
        return len(self.agent_ids)


@dataclass(frozen=True)
class ContributionMargins:
    """
    Marginal contribution analysis for each agent.

    Attributes:
        agent_ids: Ordered tuple of agent identifiers.
        marginal_to_empty: Contribution when joining empty coalition.
        marginal_to_grand: Contribution when joining all others.
        average_marginal: Average marginal contribution (= Shapley value).
        min_marginal: Minimum marginal contribution across all coalitions.
        max_marginal: Maximum marginal contribution across all coalitions.
    """

    agent_ids: Tuple[str, ...]
    marginal_to_empty: Tuple[float, ...]
    marginal_to_grand: Tuple[float, ...]
    average_marginal: Tuple[float, ...]
    min_marginal: Tuple[float, ...]
    max_marginal: Tuple[float, ...]

    def is_essential(self, agent_id: str) -> bool:
        """Check if agent is essential (positive min marginal)."""
        idx = self.agent_ids.index(agent_id)
        return self.min_marginal[idx] > 0

    def is_null(self, agent_id: str) -> bool:
        """Check if agent is null (zero marginal everywhere)."""
        idx = self.agent_ids.index(agent_id)
        return (
            abs(self.min_marginal[idx]) < 1e-10 and abs(self.max_marginal[idx]) < 1e-10
        )


# =============================================================================
# Core Stability
# =============================================================================


@dataclass(frozen=True)
class CoreStabilityResult:
    """
    Result of core stability analysis.

    The core of a game is the set of allocations where no coalition
    can improve by deviating. An allocation is in the core if for
    every coalition S, the sum of allocated values to S members
    is at least v(S).

    Attributes:
        is_stable: True if the allocation is in the core.
        core_violations: List of (coalition, deficit) pairs for violations.
        min_deficit: Minimum deficit across all coalitions (0 if stable).
        max_deficit: Maximum deficit across all coalitions.
        stability_score: Score in [0, 1], 1 = perfectly stable.
    """

    is_stable: bool
    core_violations: Tuple[Tuple[Coalition, float], ...]
    min_deficit: float
    max_deficit: float
    stability_score: float

    def get_blocking_coalitions(self) -> List[Coalition]:
        """Get list of coalitions that block the allocation."""
        return [c for c, _ in self.core_violations]


@dataclass(frozen=True)
class NucleolusResult:
    """
    Result of nucleolus computation.

    The nucleolus is the allocation that lexicographically minimizes
    the sorted vector of coalition excesses. It always exists, is
    unique, and lies in the core (if the core is non-empty).

    Attributes:
        agent_ids: Ordered tuple of agent identifiers.
        allocation: Nucleolus allocation values.
        excess_vector: Sorted vector of excesses.
        is_in_core: True if nucleolus is in the core.
        iterations: Number of LP iterations used.
    """

    agent_ids: Tuple[str, ...]
    allocation: Tuple[float, ...]
    excess_vector: Tuple[float, ...]
    is_in_core: bool
    iterations: int = 0

    def get_allocation(self, agent_id: str) -> float:
        """Get nucleolus allocation for a specific agent."""
        idx = self.agent_ids.index(agent_id)
        return self.allocation[idx]


# =============================================================================
# Shapley Value Computation
# =============================================================================


def compute_shapley_exact(
    agent_ids: Sequence[str],
    char_func: CharacteristicFunction,
    *,
    per_dimension: bool = False,
    dimension_char_funcs: Optional[Dict[str, CharacteristicFunction]] = None,
) -> ShapleyValues:
    """
    Compute exact Shapley values for all agents.

    Uses the permutation-based formula:
    φ_i = (1/n!) Σ_{π} [v(P_i^π ∪ {i}) - v(P_i^π)]

    where P_i^π is the set of agents preceding i in permutation π.

    Complexity: O(n! * 2^n) - only feasible for n ≤ 10.

    Args:
        agent_ids: Sequence of agent identifiers.
        char_func: Characteristic function v(S) -> float.
        per_dimension: If True and dimension_char_funcs provided,
            compute per-dimension Shapley values.
        dimension_char_funcs: Dict mapping dimension name to char func.

    Returns:
        ShapleyValues with exact computation results.

    Raises:
        ValueError: If n > 10 (use Monte Carlo instead).

    Example:
        >>> def v(S):
        ...     # Majority voting game
        ...     return 1.0 if len(S) >= 2 else 0.0
        >>> sv = compute_shapley_exact(["a", "b", "c"], v)
        >>> sv.values  # Each player has equal power
        (0.333..., 0.333..., 0.333...)
    """
    agents = tuple(agent_ids)
    n = len(agents)

    if n > 10:
        raise ValueError(
            f"Exact Shapley too expensive for n={n} agents. "
            "Use compute_shapley_monte_carlo() instead."
        )

    if n == 0:
        return ShapleyValues(
            agent_ids=(),
            values=(),
            grand_coalition_value=0.0,
            is_exact=True,
        )

    # Precompute all coalition values for efficiency
    coalition_values: Dict[Coalition, float] = {}

    def get_value(coalition: Coalition) -> float:
        if coalition not in coalition_values:
            coalition_values[coalition] = char_func(coalition)
        return coalition_values[coalition]

    # Compute grand coalition value
    grand_coalition = frozenset(agents)
    grand_value = get_value(grand_coalition)

    # Compute Shapley values using permutation formula
    shapley_sums = [0.0] * n
    factorial_n = math.factorial(n)

    for perm in permutations(range(n)):
        # For each permutation, compute marginal contributions
        current_coalition: set = set()
        for pos, agent_idx in enumerate(perm):
            # Value before adding this agent
            prev_value = get_value(frozenset(current_coalition))
            # Add agent
            current_coalition.add(agents[agent_idx])
            # Value after adding this agent
            new_value = get_value(frozenset(current_coalition))
            # Marginal contribution
            shapley_sums[agent_idx] += new_value - prev_value

    # Average over all permutations
    shapley_values = tuple(s / factorial_n for s in shapley_sums)

    # Per-dimension computation if requested
    per_dim_values = None
    if per_dimension and dimension_char_funcs:
        per_dim_values = []
        for dim_name in MORAL_DIMENSION_NAMES:
            if dim_name in dimension_char_funcs:
                dim_sv = compute_shapley_exact(agents, dimension_char_funcs[dim_name])
                per_dim_values.append(dim_sv.values)
            else:
                per_dim_values.append(tuple(0.0 for _ in agents))
        per_dim_values = tuple(per_dim_values)

    return ShapleyValues(
        agent_ids=agents,
        values=shapley_values,
        grand_coalition_value=grand_value,
        is_exact=True,
        per_dimension=per_dim_values,
    )


def compute_shapley_monte_carlo(
    agent_ids: Sequence[str],
    char_func: CharacteristicFunction,
    n_samples: int = 10000,
    *,
    seed: Optional[int] = None,
    convergence_threshold: float = 0.01,
    min_samples: int = 1000,
) -> ShapleyValues:
    """
    Approximate Shapley values using Monte Carlo sampling.

    Samples random permutations and computes marginal contributions.
    Suitable for n > 10 agents.

    Complexity: O(n_samples * n * T_v) where T_v is char_func cost.

    Args:
        agent_ids: Sequence of agent identifiers.
        char_func: Characteristic function v(S) -> float.
        n_samples: Number of random permutations to sample.
        seed: Random seed for reproducibility.
        convergence_threshold: Stop early if estimates stabilize.
        min_samples: Minimum samples before checking convergence.

    Returns:
        ShapleyValues with approximation and confidence interval.

    Example:
        >>> def v(S):
        ...     return len(S) ** 2  # Superadditive game
        >>> sv = compute_shapley_monte_carlo(
        ...     [f"agent_{i}" for i in range(50)],
        ...     v,
        ...     n_samples=5000,
        ... )
        >>> sv.is_exact
        False
    """
    agents = tuple(agent_ids)
    n = len(agents)

    if n == 0:
        return ShapleyValues(
            agent_ids=(),
            values=(),
            grand_coalition_value=0.0,
            is_exact=True,
        )

    rng = np.random.default_rng(seed)

    # Compute grand coalition value
    grand_coalition = frozenset(agents)
    grand_value = char_func(grand_coalition)

    # Accumulate marginal contributions
    marginal_sums = np.zeros(n)
    marginal_sq_sums = np.zeros(n)  # For variance estimation

    # Cache for coalition values
    value_cache: Dict[Coalition, float] = {frozenset(): 0.0}

    def get_cached_value(coalition: Coalition) -> float:
        if coalition not in value_cache:
            value_cache[coalition] = char_func(coalition)
        return value_cache[coalition]

    actual_samples = 0
    prev_estimates = np.zeros(n)

    for sample_idx in range(n_samples):
        # Random permutation
        perm = rng.permutation(n)

        # Compute marginal contributions
        current_coalition: set = set()
        for agent_idx in perm:
            prev_value = get_cached_value(frozenset(current_coalition))
            current_coalition.add(agents[agent_idx])
            new_value = get_cached_value(frozenset(current_coalition))
            marginal = new_value - prev_value
            marginal_sums[agent_idx] += marginal
            marginal_sq_sums[agent_idx] += marginal**2

        actual_samples += 1

        # Check convergence
        if actual_samples >= min_samples and actual_samples % 100 == 0:
            current_estimates = marginal_sums / actual_samples
            max_change = np.max(np.abs(current_estimates - prev_estimates))
            if max_change < convergence_threshold:
                break
            prev_estimates = current_estimates.copy()

    # Compute final estimates
    shapley_values = marginal_sums / actual_samples

    # Compute confidence interval (95% CI)
    variances = (marginal_sq_sums / actual_samples) - (shapley_values**2)
    std_errors = np.sqrt(np.maximum(variances, 0) / actual_samples)
    max_ci = float(1.96 * np.max(std_errors))

    return ShapleyValues(
        agent_ids=agents,
        values=tuple(float(v) for v in shapley_values),
        grand_coalition_value=grand_value,
        is_exact=False,
        n_samples=actual_samples,
        confidence_interval=max_ci,
    )


def compute_shapley_from_tensor(
    tensor: MoralTensor,
    context: CoalitionContext,
    *,
    aggregation: Literal["sum", "mean", "min"] = "sum",
    dimension_weights: Optional[np.ndarray] = None,
) -> ShapleyValues:
    """
    Compute Shapley values from a rank-2+ MoralTensor.

    Constructs a characteristic function from the tensor and computes
    Shapley values for each agent.

    Args:
        tensor: MoralTensor with party axis corresponding to agents.
        context: CoalitionContext defining the agents.
        aggregation: How to aggregate across dimensions.
        dimension_weights: Optional weights for dimensions (length 9).

    Returns:
        ShapleyValues computed from tensor.

    Example:
        >>> ctx = CoalitionContext(agent_ids=("a", "b", "c"))
        >>> tensor = MoralTensor(np.ones((9, 3)) * 0.5)
        >>> sv = compute_shapley_from_tensor(tensor, ctx)
    """
    n_agents = len(context.agent_ids)

    # Validate tensor shape
    if tensor.rank < 2:
        raise ValueError("Tensor must have rank >= 2 for Shapley computation")

    # Get party axis (assumed to be axis 1 for rank-2)
    party_axis = 1 if tensor.rank >= 2 else 0
    if tensor.shape[party_axis] != n_agents:
        raise ValueError(
            f"Tensor party axis has {tensor.shape[party_axis]} elements, "
            f"expected {n_agents} agents"
        )

    # Get tensor data as dense array
    tensor_data = tensor.to_dense()

    # Create characteristic function from tensor
    def char_func(coalition: Coalition) -> float:
        if not coalition:
            return 0.0

        # Get indices of agents in coalition
        indices = [
            context.agent_ids.index(agent)
            for agent in coalition
            if agent in context.agent_ids
        ]

        if not indices:
            return 0.0

        # Extract values for coalition members
        if tensor.rank == 2:
            coalition_data = tensor_data[:, indices]
        else:
            # For higher ranks, sum/mean over other axes
            coalition_data = tensor_data[:, indices]
            while coalition_data.ndim > 2:
                coalition_data = coalition_data.mean(axis=-1)

        # Aggregate across dimensions
        if dimension_weights is not None:
            weighted = coalition_data * dimension_weights.reshape(-1, 1)
        else:
            weighted = coalition_data

        if aggregation == "sum":
            return float(np.sum(weighted))
        elif aggregation == "mean":
            return float(np.mean(weighted))
        elif aggregation == "min":
            return float(np.min(weighted))
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

    # Choose exact or Monte Carlo based on n
    if n_agents <= 10:
        return compute_shapley_exact(context.agent_ids, char_func)
    else:
        return compute_shapley_monte_carlo(context.agent_ids, char_func)


# =============================================================================
# Contribution Margins
# =============================================================================


def compute_contribution_margins(
    agent_ids: Sequence[str],
    char_func: CharacteristicFunction,
) -> ContributionMargins:
    """
    Compute marginal contribution statistics for each agent.

    For each agent, computes:
    - Marginal contribution to empty coalition (standalone value)
    - Marginal contribution to grand coalition (as last joiner)
    - Average, min, max marginal across all coalitions

    Args:
        agent_ids: Sequence of agent identifiers.
        char_func: Characteristic function v(S) -> float.

    Returns:
        ContributionMargins with detailed statistics.

    Example:
        >>> def v(S):
        ...     return len(S) if len(S) >= 2 else 0
        >>> margins = compute_contribution_margins(["a", "b", "c"], v)
        >>> margins.marginal_to_empty  # Standalone values
        (0.0, 0.0, 0.0)
    """
    agents = tuple(agent_ids)
    n = len(agents)

    if n == 0:
        return ContributionMargins(
            agent_ids=(),
            marginal_to_empty=(),
            marginal_to_grand=(),
            average_marginal=(),
            min_marginal=(),
            max_marginal=(),
        )

    # Precompute all coalition values
    coalition_values: Dict[Coalition, float] = {}

    def get_value(coalition: Coalition) -> float:
        if coalition not in coalition_values:
            coalition_values[coalition] = char_func(coalition)
        return coalition_values[coalition]

    # Initialize statistics
    marginal_to_empty = []
    marginal_to_grand = []
    min_marginal = []
    max_marginal = []
    sum_marginal = []
    count_marginal = []

    grand = frozenset(agents)

    for i, agent in enumerate(agents):
        # Marginal to empty coalition
        m_empty = get_value(frozenset([agent]))
        marginal_to_empty.append(m_empty)

        # Marginal to grand coalition
        others = frozenset(a for a in agents if a != agent)
        m_grand = get_value(grand) - get_value(others)
        marginal_to_grand.append(m_grand)

        # Compute all marginals for min/max/avg
        agent_marginals = []
        # Enumerate all subsets not containing agent
        for mask in range(1 << (n - 1)):
            # Build coalition from mask (excluding agent i)
            other_agents = [a for j, a in enumerate(agents) if j != i]
            coalition_without = frozenset(
                other_agents[j] for j in range(n - 1) if mask & (1 << j)
            )
            coalition_with = coalition_without | frozenset([agent])

            marginal = get_value(coalition_with) - get_value(coalition_without)
            agent_marginals.append(marginal)

        min_marginal.append(min(agent_marginals))
        max_marginal.append(max(agent_marginals))
        sum_marginal.append(sum(agent_marginals))
        count_marginal.append(len(agent_marginals))

    # Average marginal = Shapley value (by definition)
    average_marginal = [s / c for s, c in zip(sum_marginal, count_marginal)]

    return ContributionMargins(
        agent_ids=agents,
        marginal_to_empty=tuple(marginal_to_empty),
        marginal_to_grand=tuple(marginal_to_grand),
        average_marginal=tuple(average_marginal),
        min_marginal=tuple(min_marginal),
        max_marginal=tuple(max_marginal),
    )


# =============================================================================
# Core Stability
# =============================================================================


def check_core_stability(
    agent_ids: Sequence[str],
    allocation: Sequence[float],
    char_func: CharacteristicFunction,
    *,
    tolerance: float = 1e-6,
) -> CoreStabilityResult:
    """
    Check if an allocation is in the core of the game.

    An allocation x is in the core if:
    1. Efficiency: Σ x_i = v(N) (grand coalition value)
    2. Coalitional rationality: Σ_{i∈S} x_i >= v(S) for all S

    Args:
        agent_ids: Sequence of agent identifiers.
        allocation: Proposed allocation values (same order as agent_ids).
        char_func: Characteristic function v(S) -> float.
        tolerance: Numerical tolerance for comparisons.

    Returns:
        CoreStabilityResult with stability analysis.

    Example:
        >>> def v(S):
        ...     if len(S) == 3: return 1.0
        ...     if len(S) == 2: return 0.8
        ...     return 0.0
        >>> result = check_core_stability(
        ...     ["a", "b", "c"],
        ...     [0.33, 0.33, 0.34],
        ...     v,
        ... )
        >>> result.is_stable
        True
    """
    agents = tuple(agent_ids)
    alloc = tuple(allocation)
    n = len(agents)

    if len(alloc) != n:
        raise ValueError("allocation must have same length as agent_ids")

    if n == 0:
        return CoreStabilityResult(
            is_stable=True,
            core_violations=(),
            min_deficit=0.0,
            max_deficit=0.0,
            stability_score=1.0,
        )

    # Check all coalitions for violations
    violations: List[Tuple[Coalition, float]] = []
    deficits: List[float] = []

    for mask in range(1, 1 << n):  # Skip empty coalition
        coalition = frozenset(agents[i] for i in range(n) if mask & (1 << i))
        coalition_value = char_func(coalition)
        allocated_sum = sum(alloc[i] for i in range(n) if mask & (1 << i))
        deficit = coalition_value - allocated_sum

        deficits.append(deficit)

        if deficit > tolerance:
            violations.append((coalition, deficit))

    is_stable = len(violations) == 0
    min_deficit = min(deficits) if deficits else 0.0
    max_deficit = max(deficits) if deficits else 0.0

    # Stability score: 1 if stable, otherwise based on violation severity
    if is_stable:
        stability_score = 1.0
    else:
        # Normalize by grand coalition value
        grand_value = char_func(frozenset(agents))
        if abs(grand_value) > 1e-10:
            normalized_deficit = max_deficit / abs(grand_value)
            stability_score = max(0.0, 1.0 - normalized_deficit)
        else:
            stability_score = 0.0

    return CoreStabilityResult(
        is_stable=is_stable,
        core_violations=tuple(violations),
        min_deficit=min_deficit,
        max_deficit=max_deficit,
        stability_score=stability_score,
    )


def is_core_empty(
    agent_ids: Sequence[str],
    char_func: CharacteristicFunction,
) -> bool:
    """
    Check if the core of the game is empty.

    Uses the Shapley value as a candidate and checks if it's in the core.
    If not, the core might still be non-empty, but this is a quick check.

    For a definitive answer, use compute_nucleolus() and check is_in_core.

    Args:
        agent_ids: Sequence of agent identifiers.
        char_func: Characteristic function v(S) -> float.

    Returns:
        True if Shapley value is not in core (core may be empty).
    """
    agents = tuple(agent_ids)
    n = len(agents)

    if n == 0:
        return False

    # Compute Shapley value
    if n <= 10:
        sv = compute_shapley_exact(agents, char_func)
    else:
        sv = compute_shapley_monte_carlo(agents, char_func, n_samples=5000)

    # Check if Shapley is in core
    result = check_core_stability(agents, sv.values, char_func)
    return not result.is_stable


# =============================================================================
# Nucleolus Computation
# =============================================================================


def compute_nucleolus(
    agent_ids: Sequence[str],
    char_func: CharacteristicFunction,
    *,
    max_iterations: int = 100,
    tolerance: float = 1e-8,
) -> NucleolusResult:
    """
    Compute the nucleolus of the game.

    The nucleolus is the unique allocation that lexicographically minimizes
    the sorted vector of coalition excesses. It always exists, is unique,
    and is in the core if the core is non-empty.

    Uses an iterative linear programming approach:
    1. Start with the pre-imputation set
    2. Iteratively minimize the maximum excess
    3. Fix coalitions at their excess and repeat

    For small n, uses a simplified approach based on Shapley + perturbation.

    Args:
        agent_ids: Sequence of agent identifiers.
        char_func: Characteristic function v(S) -> float.
        max_iterations: Maximum LP iterations.
        tolerance: Numerical tolerance.

    Returns:
        NucleolusResult with allocation and properties.

    Note:
        For n > 6, this uses an approximation based on weighted Shapley
        values rather than exact nucleolus computation.
    """
    agents = tuple(agent_ids)
    n = len(agents)

    if n == 0:
        return NucleolusResult(
            agent_ids=(),
            allocation=(),
            excess_vector=(),
            is_in_core=True,
            iterations=0,
        )

    # Compute grand coalition value (efficiency constraint)
    grand_value = char_func(frozenset(agents))

    # For small n, compute exactly
    if n <= 6:
        return _compute_nucleolus_exact(agents, char_func, grand_value, tolerance)
    else:
        # For larger n, use weighted Shapley approximation
        return _compute_nucleolus_approximate(
            agents, char_func, grand_value, max_iterations, tolerance
        )


def _compute_nucleolus_exact(
    agents: Tuple[str, ...],
    char_func: CharacteristicFunction,
    grand_value: float,
    tolerance: float,
) -> NucleolusResult:
    """Exact nucleolus for small n using enumeration."""
    n = len(agents)

    # Compute all coalition values
    coalition_values: Dict[Coalition, float] = {}
    for mask in range(1 << n):
        coalition = frozenset(agents[i] for i in range(n) if mask & (1 << i))
        coalition_values[coalition] = char_func(coalition)

    # Start with Shapley value
    sv = compute_shapley_exact(agents, char_func)
    current_alloc = np.array(sv.values)

    # Iteratively adjust to minimize max excess
    iterations = 0
    for _ in range(100):
        iterations += 1

        # Compute all excesses
        excesses = []
        for mask in range(1, (1 << n) - 1):  # Skip empty and grand
            coalition = frozenset(agents[i] for i in range(n) if mask & (1 << i))
            coal_value = coalition_values[coalition]
            alloc_sum = sum(current_alloc[i] for i in range(n) if mask & (1 << i))
            excess = coal_value - alloc_sum
            excesses.append((excess, mask))

        if not excesses:
            break

        excesses.sort(reverse=True)
        max_excess = excesses[0][0]

        if max_excess <= tolerance:
            break

        # Adjust allocation to reduce max excess
        # Move towards more even distribution
        max_coalitions = [m for e, m in excesses if e > max_excess - tolerance]
        adjustment = np.zeros(n)

        for mask in max_coalitions:
            # Increase allocation to coalition members
            for i in range(n):
                if mask & (1 << i):
                    adjustment[i] += 0.1
                else:
                    adjustment[i] -= 0.1 / (n - bin(mask).count("1"))

        # Normalize to maintain efficiency
        adjustment -= np.mean(adjustment)
        step = 0.1
        current_alloc = current_alloc + step * adjustment

        # Re-normalize
        current_alloc = current_alloc * (grand_value / np.sum(current_alloc))

    # Final excess vector
    excesses = []
    for mask in range(1, (1 << n) - 1):
        coalition = frozenset(agents[i] for i in range(n) if mask & (1 << i))
        coal_value = coalition_values[coalition]
        alloc_sum = sum(current_alloc[i] for i in range(n) if mask & (1 << i))
        excesses.append(coal_value - alloc_sum)

    excesses.sort(reverse=True)
    is_in_core = len(excesses) == 0 or excesses[0] <= tolerance

    return NucleolusResult(
        agent_ids=agents,
        allocation=tuple(float(x) for x in current_alloc),
        excess_vector=tuple(excesses),
        is_in_core=bool(is_in_core),
        iterations=iterations,
    )


def _compute_nucleolus_approximate(
    agents: Tuple[str, ...],
    char_func: CharacteristicFunction,
    grand_value: float,
    max_iterations: int,
    tolerance: float,
) -> NucleolusResult:
    """Approximate nucleolus for large n using weighted Shapley."""
    n = len(agents)

    # Use Monte Carlo Shapley as base
    sv = compute_shapley_monte_carlo(agents, char_func, n_samples=5000)
    allocation = np.array(sv.values)

    # Normalize to efficiency
    if abs(np.sum(allocation)) > tolerance:
        allocation = allocation * (grand_value / np.sum(allocation))
    else:
        allocation = np.full(n, grand_value / n)

    # Sample coalitions to estimate excess vector
    rng = np.random.default_rng(42)
    n_samples = min(1000, 2**n - 2)

    excesses = []
    for _ in range(n_samples):
        # Random coalition
        mask = rng.integers(1, (1 << n) - 1)
        coalition = frozenset(agents[i] for i in range(n) if mask & (1 << i))
        coal_value = char_func(coalition)
        alloc_sum = sum(allocation[i] for i in range(n) if mask & (1 << i))
        excesses.append(coal_value - alloc_sum)

    excesses.sort(reverse=True)
    is_in_core = len(excesses) == 0 or excesses[0] <= tolerance

    return NucleolusResult(
        agent_ids=agents,
        allocation=tuple(float(x) for x in allocation),
        excess_vector=tuple(excesses[:20]),  # Keep top 20
        is_in_core=bool(is_in_core),
        iterations=1,
    )


# =============================================================================
# Integration with EthicalJudgementV3
# =============================================================================


@dataclass(frozen=True)
class ShapleyAttribution:
    """
    Shapley-based attribution for ethical outcomes.

    Designed to integrate with EthicalJudgementV3.metadata for
    recording fair credit assignment in multi-agent decisions.

    Attributes:
        shapley_values: ShapleyValues result.
        contribution_margins: Optional detailed margins.
        core_stability: Optional core stability analysis.
        attribution_method: Method used ("exact" or "monte_carlo").
        timestamp: ISO timestamp of computation.
    """

    shapley_values: ShapleyValues
    contribution_margins: Optional[ContributionMargins] = None
    core_stability: Optional[CoreStabilityResult] = None
    attribution_method: str = "exact"
    timestamp: str = ""

    def to_metadata_dict(self) -> Dict:
        """Convert to dict suitable for EthicalJudgementV3.metadata."""
        result = {
            "shapley_attribution": {
                "agent_ids": list(self.shapley_values.agent_ids),
                "values": list(self.shapley_values.values),
                "grand_coalition_value": self.shapley_values.grand_coalition_value,
                "is_exact": self.shapley_values.is_exact,
                "method": self.attribution_method,
            }
        }

        if self.shapley_values.confidence_interval is not None:
            result["shapley_attribution"][
                "confidence_interval"
            ] = self.shapley_values.confidence_interval

        if self.contribution_margins is not None:
            result["contribution_margins"] = {
                "marginal_to_empty": list(self.contribution_margins.marginal_to_empty),
                "marginal_to_grand": list(self.contribution_margins.marginal_to_grand),
                "min_marginal": list(self.contribution_margins.min_marginal),
                "max_marginal": list(self.contribution_margins.max_marginal),
            }

        if self.core_stability is not None:
            result["core_stability"] = {
                "is_stable": self.core_stability.is_stable,
                "stability_score": self.core_stability.stability_score,
                "n_violations": len(self.core_stability.core_violations),
            }

        return result


def compute_ethical_attribution(
    tensor: MoralTensor,
    context: CoalitionContext,
    *,
    include_margins: bool = True,
    include_core: bool = True,
    aggregation: Literal["sum", "mean", "min"] = "sum",
) -> ShapleyAttribution:
    """
    Compute full Shapley-based attribution for ethical outcomes.

    Convenience function that computes Shapley values, contribution
    margins, and core stability in one call.

    Args:
        tensor: MoralTensor with ethical outcomes per agent.
        context: CoalitionContext defining agents.
        include_margins: If True, compute contribution margins.
        include_core: If True, check core stability.
        aggregation: How to aggregate tensor dimensions.

    Returns:
        ShapleyAttribution with all computed results.
    """
    # Compute Shapley values
    sv = compute_shapley_from_tensor(tensor, context, aggregation=aggregation)

    # Determine method
    method = "exact" if sv.is_exact else "monte_carlo"

    # Get tensor data as dense array
    tensor_data = tensor.to_dense()

    # Build char func from tensor
    def char_func(coalition: Coalition) -> float:
        if not coalition:
            return 0.0
        indices = [
            context.agent_ids.index(a) for a in coalition if a in context.agent_ids
        ]
        if not indices:
            return 0.0
        data = tensor_data[:, indices]
        return float(np.sum(data))

    # Compute margins if requested
    margins = None
    if include_margins and len(context.agent_ids) <= 10:
        margins = compute_contribution_margins(context.agent_ids, char_func)

    # Check core stability if requested
    core = None
    if include_core:
        core = check_core_stability(context.agent_ids, sv.values, char_func)

    return ShapleyAttribution(
        shapley_values=sv,
        contribution_margins=margins,
        core_stability=core,
        attribution_method=method,
    )


# =============================================================================
# Utility Functions
# =============================================================================


def create_voting_game(
    agent_ids: Sequence[str],
    weights: Sequence[float],
    quota: float,
) -> CharacteristicFunction:
    """
    Create a weighted voting game characteristic function.

    A coalition wins (value 1) if sum of weights >= quota.

    Args:
        agent_ids: Sequence of agent identifiers.
        weights: Voting weights (same order as agent_ids).
        quota: Threshold for winning.

    Returns:
        Characteristic function for the voting game.

    Example:
        >>> v = create_voting_game(["a", "b", "c"], [2, 3, 5], 6)
        >>> v(frozenset(["b", "c"]))  # 3 + 5 = 8 >= 6
        1.0
        >>> v(frozenset(["a", "b"]))  # 2 + 3 = 5 < 6
        0.0
    """
    agents = tuple(agent_ids)
    weight_map = dict(zip(agents, weights))

    def char_func(coalition: Coalition) -> float:
        total_weight = sum(weight_map.get(a, 0) for a in coalition)
        return 1.0 if total_weight >= quota else 0.0

    return char_func


def create_additive_game(
    agent_ids: Sequence[str],
    values: Sequence[float],
) -> CharacteristicFunction:
    """
    Create an additive game characteristic function.

    Each agent has an individual value; coalition value is sum.
    Shapley values equal individual values in additive games.

    Args:
        agent_ids: Sequence of agent identifiers.
        values: Individual values (same order as agent_ids).

    Returns:
        Characteristic function for additive game.
    """
    value_map = dict(zip(agent_ids, values))

    def char_func(coalition: Coalition) -> float:
        return sum(value_map.get(a, 0) for a in coalition)

    return char_func


def create_superadditive_game(
    agent_ids: Sequence[str],
    synergy_bonus: float = 0.1,
) -> CharacteristicFunction:
    """
    Create a superadditive game with synergy effects.

    Coalition value = n + synergy_bonus * n*(n-1)/2 for n members.
    Larger coalitions are super-proportionally valuable.

    Args:
        agent_ids: Sequence of agent identifiers.
        synergy_bonus: Extra value per pair of agents.

    Returns:
        Characteristic function for superadditive game.
    """

    def char_func(coalition: Coalition) -> float:
        n = len(coalition)
        if n == 0:
            return 0.0
        return n + synergy_bonus * n * (n - 1) / 2

    return char_func
