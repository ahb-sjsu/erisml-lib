# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Coalition Context Module for Multi-Agent Ethics.

DEME V3 Sprint 8: Support multi-agent action coordination in tensors.

This module provides:
- CoalitionContext: Dataclass for multi-agent coalition configuration
- Coalition enumeration and configuration generation
- Sparse coalition representation for large coalition spaces
- Coalition stability constraints
- Action-conditioned tensor slicing

Rank-4 tensors have shape (k, n, a, c) where:
- k = 9 moral dimensions
- n = number of parties/agents
- a = number of actions per agent
- c = number of coalition configurations

Version: 3.0.0 (DEME V3 - Sprint 8)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from typing import (
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Literal,
    Set,
    Tuple,
)

import numpy as np

from erisml.ethics.moral_tensor import MoralTensor, MORAL_DIMENSION_NAMES


# =============================================================================
# Coalition Configuration Types
# =============================================================================


# A coalition is a frozenset of agent IDs
Coalition = FrozenSet[str]

# A coalition structure is a partition of agents into coalitions
CoalitionStructure = Tuple[Coalition, ...]

# An action profile maps agent IDs to their chosen action indices
ActionProfile = Dict[str, int]


# =============================================================================
# Coalition Context
# =============================================================================


@dataclass(frozen=True)
class CoalitionContext:
    """
    Context for multi-agent coalition-based ethical assessment.

    Describes the agents, their possible actions, and coalition configurations
    for a multi-agent decision scenario.

    Attributes:
        agent_ids: Ordered tuple of agent identifiers.
        action_labels: Dict mapping agent_id to list of action labels.
        coalition_mode: How coalitions are formed:
            - "all_subsets": All possible subsets (2^n configurations)
            - "grand_only": Only grand coalition (all agents together)
            - "singletons_only": Each agent acts alone
            - "pairwise": All pairs plus singletons
            - "custom": User-provided coalition structures
        coalition_structures: For "custom" mode, explicit coalition structures.
        coalition_labels: Optional labels for coalition configurations.

    Example:
        ctx = CoalitionContext(
            agent_ids=("robot_a", "robot_b", "human"),
            action_labels={
                "robot_a": ["move_left", "move_right", "stop"],
                "robot_b": ["assist", "wait"],
                "human": ["approve", "reject"],
            },
            coalition_mode="all_subsets",
        )
    """

    agent_ids: Tuple[str, ...]
    action_labels: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    coalition_mode: Literal[
        "all_subsets", "grand_only", "singletons_only", "pairwise", "custom"
    ] = "grand_only"
    coalition_structures: Tuple[CoalitionStructure, ...] = ()
    coalition_labels: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate context configuration."""
        if len(self.agent_ids) == 0:
            raise ValueError("agent_ids cannot be empty")

        if len(set(self.agent_ids)) != len(self.agent_ids):
            raise ValueError("agent_ids must be unique")

        # Validate action labels reference valid agents
        for agent_id in self.action_labels:
            if agent_id not in self.agent_ids:
                raise ValueError(f"action_labels contains unknown agent: {agent_id}")

        # Ensure all agents have action labels (default to single action)
        if self.action_labels:
            for agent_id in self.agent_ids:
                if agent_id not in self.action_labels:
                    # Use object.__setattr__ for frozen dataclass
                    object.__setattr__(
                        self,
                        "action_labels",
                        {**self.action_labels, agent_id: ("default",)},
                    )

        # Validate custom coalition structures
        if self.coalition_mode == "custom":
            if not self.coalition_structures:
                raise ValueError("coalition_structures required for 'custom' mode")
            for struct in self.coalition_structures:
                self._validate_coalition_structure(struct)

    def _validate_coalition_structure(self, struct: CoalitionStructure) -> None:
        """Validate that a coalition structure is a valid partition."""
        all_agents: Set[str] = set()
        for coalition in struct:
            if not coalition:
                continue
            for agent in coalition:
                if agent not in self.agent_ids:
                    raise ValueError(f"Coalition contains unknown agent: {agent}")
                if agent in all_agents:
                    raise ValueError(f"Agent {agent} appears in multiple coalitions")
                all_agents.add(agent)

    @property
    def n_agents(self) -> int:
        """Number of agents."""
        return len(self.agent_ids)

    @property
    def n_actions_per_agent(self) -> Dict[str, int]:
        """Number of actions available to each agent."""
        return {
            agent_id: len(self.action_labels.get(agent_id, ("default",)))
            for agent_id in self.agent_ids
        }

    @property
    def total_action_profiles(self) -> int:
        """Total number of joint action profiles (product of action counts)."""
        counts = self.n_actions_per_agent
        result = 1
        for count in counts.values():
            result *= count
        return result

    @property
    def n_coalitions(self) -> int:
        """Number of coalition configurations."""
        return len(list(self.enumerate_coalitions()))

    def enumerate_coalitions(self) -> Iterator[CoalitionStructure]:
        """
        Enumerate all coalition configurations based on mode.

        Yields:
            CoalitionStructure tuples representing partitions of agents.
        """
        agents = set(self.agent_ids)

        if self.coalition_mode == "grand_only":
            # Single coalition containing all agents
            yield (frozenset(agents),)

        elif self.coalition_mode == "singletons_only":
            # Each agent in their own coalition
            yield tuple(frozenset([a]) for a in self.agent_ids)

        elif self.coalition_mode == "pairwise":
            # All pairs plus singletons
            yield tuple(frozenset([a]) for a in self.agent_ids)  # Singletons
            for pair in combinations(self.agent_ids, 2):
                # Pair coalition plus remaining singletons
                remaining = agents - set(pair)
                coalitions = [frozenset(pair)]
                coalitions.extend(frozenset([a]) for a in remaining)
                yield tuple(coalitions)

        elif self.coalition_mode == "all_subsets":
            # All possible coalition structures (Bell number)
            yield from self._enumerate_all_partitions(list(self.agent_ids))

        elif self.coalition_mode == "custom":
            yield from self.coalition_structures

    def _enumerate_all_partitions(
        self, agents: List[str]
    ) -> Iterator[CoalitionStructure]:
        """
        Enumerate all partitions of agents (Bell number complexity).

        Uses recursive partition generation.
        """
        if not agents:
            yield ()
            return

        if len(agents) == 1:
            yield (frozenset(agents),)
            return

        first = agents[0]
        rest = agents[1:]

        # For each partition of the rest
        for partition in self._enumerate_all_partitions(rest):
            # Option 1: first agent in its own singleton
            yield (frozenset([first]),) + partition

            # Option 2: first agent joins each existing coalition
            for i, coalition in enumerate(partition):
                new_coalition = coalition | frozenset([first])
                new_partition = partition[:i] + (new_coalition,) + partition[i + 1 :]
                yield new_partition

    def enumerate_action_profiles(self) -> Iterator[ActionProfile]:
        """
        Enumerate all joint action profiles.

        Yields:
            Dict mapping agent_id to action index.
        """
        action_ranges = [
            range(len(self.action_labels.get(agent_id, ("default",))))
            for agent_id in self.agent_ids
        ]

        for action_tuple in product(*action_ranges):
            yield dict(zip(self.agent_ids, action_tuple))

    def get_coalition_label(self, idx: int) -> str:
        """Get label for coalition configuration by index."""
        if self.coalition_labels and idx < len(self.coalition_labels):
            return self.coalition_labels[idx]
        return f"coalition_{idx}"

    def get_action_label(self, agent_id: str, action_idx: int) -> str:
        """Get label for an agent's action."""
        actions = self.action_labels.get(agent_id, ("default",))
        if action_idx < len(actions):
            return actions[action_idx]
        return f"action_{action_idx}"

    @classmethod
    def from_agents(
        cls,
        agents: List[str],
        actions_per_agent: int = 2,
        coalition_mode: str = "grand_only",
    ) -> "CoalitionContext":
        """
        Create context with uniform action count per agent.

        Args:
            agents: List of agent identifiers.
            actions_per_agent: Number of actions available to each agent.
            coalition_mode: Coalition enumeration mode.

        Returns:
            CoalitionContext instance.
        """
        action_labels = {
            agent: tuple(f"action_{i}" for i in range(actions_per_agent))
            for agent in agents
        }
        return cls(
            agent_ids=tuple(agents),
            action_labels=action_labels,
            coalition_mode=coalition_mode,  # type: ignore
        )


# =============================================================================
# Sparse Coalition Tensor
# =============================================================================


@dataclass
class SparseCoalitionTensor:
    """
    Sparse representation for large coalition spaces.

    For n agents, the coalition space is O(Bell(n)) which grows super-exponentially.
    This class stores only non-default coalition configurations to save memory.

    The default assumption is that most coalition configurations result in
    similar ethical assessments, so we store only deviations from a baseline.

    Attributes:
        context: CoalitionContext describing the agents and coalitions.
        baseline: MoralTensor with the default ethical assessment (rank-2 or rank-3).
        deviations: Dict mapping (action_profile, coalition_idx) to moral deltas.
        deviation_threshold: Minimum deviation magnitude to store.
    """

    context: CoalitionContext
    baseline: MoralTensor
    deviations: Dict[Tuple[Tuple[int, ...], int], np.ndarray] = field(
        default_factory=dict
    )
    deviation_threshold: float = 0.01

    def __post_init__(self) -> None:
        """Validate baseline tensor."""
        if self.baseline.rank not in (2, 3):
            raise ValueError(
                f"Baseline must be rank-2 or rank-3, got {self.baseline.rank}"
            )

    @property
    def n_stored_deviations(self) -> int:
        """Number of stored deviation entries."""
        return len(self.deviations)

    @property
    def sparsity_ratio(self) -> float:
        """Ratio of stored entries to total possible entries."""
        total = self.context.total_action_profiles * self.context.n_coalitions
        if total == 0:
            return 0.0
        return self.n_stored_deviations / total

    def set_deviation(
        self,
        action_profile: ActionProfile,
        coalition_idx: int,
        moral_values: np.ndarray,
    ) -> None:
        """
        Store a deviation from baseline for a specific configuration.

        Args:
            action_profile: Dict mapping agent_id to action index.
            coalition_idx: Coalition configuration index.
            moral_values: Array of moral dimension values (shape matches baseline).
        """
        # Convert action profile to tuple key
        action_tuple = tuple(
            action_profile[agent_id] for agent_id in self.context.agent_ids
        )

        # Compute deviation from baseline
        baseline_data = self.baseline.to_dense()
        deviation = moral_values - baseline_data

        # Only store if deviation exceeds threshold
        if np.max(np.abs(deviation)) >= self.deviation_threshold:
            self.deviations[(action_tuple, coalition_idx)] = deviation

    def get_moral_values(
        self,
        action_profile: ActionProfile,
        coalition_idx: int,
    ) -> np.ndarray:
        """
        Get moral values for a specific configuration.

        Returns baseline + deviation if deviation exists, else baseline.
        """
        action_tuple = tuple(
            action_profile[agent_id] for agent_id in self.context.agent_ids
        )

        key = (action_tuple, coalition_idx)
        baseline_data = self.baseline.to_dense()

        if key in self.deviations:
            return baseline_data + self.deviations[key]
        return baseline_data.copy()

    def to_dense_tensor(self) -> MoralTensor:
        """
        Convert to full dense rank-4 tensor.

        Warning: This can be very memory-intensive for large coalition spaces.

        Returns:
            Rank-4 MoralTensor with shape (9, n_agents, n_actions, n_coalitions).
        """
        n_dims = 9
        n_agents = self.context.n_agents
        n_coalitions = self.context.n_coalitions

        # For simplicity, assume uniform action count (first agent's count)
        first_agent = self.context.agent_ids[0]
        n_actions = len(self.context.action_labels.get(first_agent, ("default",)))

        shape = (n_dims, n_agents, n_actions, n_coalitions)
        data = np.zeros(shape, dtype=np.float64)

        # Fill with baseline, broadcasted appropriately
        baseline_data = self.baseline.to_dense()
        for a in range(n_actions):
            for c in range(n_coalitions):
                if baseline_data.ndim == 2:
                    data[:, :, a, c] = baseline_data
                else:
                    # rank-3 baseline, take first timestep
                    data[:, :, a, c] = baseline_data[:, :, 0]

        # Apply deviations
        for (action_tuple, coalition_idx), deviation in self.deviations.items():
            action_idx = action_tuple[0]  # Simplified: use first agent's action
            if deviation.ndim == 2:
                data[:, :, action_idx, coalition_idx] += deviation
            else:
                data[:, :, action_idx, coalition_idx] += deviation[:, :, 0]

        # Clamp to [0, 1]
        data = np.clip(data, 0.0, 1.0)

        return MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "a", "c"),
            axis_labels={
                "n": list(self.context.agent_ids),
                "a": [f"action_{i}" for i in range(n_actions)],
                "c": [self.context.get_coalition_label(i) for i in range(n_coalitions)],
            },
        )


# =============================================================================
# Coalition Stability
# =============================================================================


@dataclass
class CoalitionStabilityResult:
    """
    Result of coalition stability analysis.

    Attributes:
        is_stable: Whether the grand coalition is stable.
        core_non_empty: Whether the core is non-empty.
        blocking_coalitions: Coalitions that can improve by deviating.
        stability_score: Overall stability score in [0, 1].
        reasons: Human-readable stability analysis.
    """

    is_stable: bool
    core_non_empty: bool = True
    blocking_coalitions: List[Coalition] = field(default_factory=list)
    stability_score: float = 1.0
    reasons: List[str] = field(default_factory=list)


def check_coalition_stability(
    tensor: MoralTensor,
    context: CoalitionContext,
    welfare_dimension: str = "physical_harm",
    stability_threshold: float = 0.05,
) -> CoalitionStabilityResult:
    """
    Check if the grand coalition is stable.

    A coalition is stable if no subset of agents can improve their welfare
    by deviating from the grand coalition.

    Args:
        tensor: Rank-4 MoralTensor with coalition configurations.
        context: CoalitionContext describing the agents.
        welfare_dimension: Moral dimension to use for welfare comparison.
        stability_threshold: Minimum improvement needed to consider blocking.

    Returns:
        CoalitionStabilityResult with stability analysis.
    """
    if tensor.rank != 4:
        raise ValueError(f"Expected rank-4 tensor, got rank-{tensor.rank}")

    if "c" not in tensor.axis_names:
        raise ValueError("Tensor must have coalition axis 'c'")

    data = tensor.to_dense()
    dim_idx = MORAL_DIMENSION_NAMES.index(welfare_dimension)

    # Get grand coalition index (typically index 0)
    grand_coalition_idx = 0

    # Get welfare in grand coalition (average over agents and actions)
    grand_welfare = np.mean(data[dim_idx, :, :, grand_coalition_idx])

    # For harm dimension, lower is better
    is_harm_dim = welfare_dimension == "physical_harm"

    blocking_coalitions: List[Coalition] = []
    reasons: List[str] = []

    # Check each alternative coalition configuration
    n_coalitions = data.shape[3]
    for c_idx in range(1, n_coalitions):
        coalition_welfare = np.mean(data[dim_idx, :, :, c_idx])

        # Check if this configuration is better
        if is_harm_dim:
            improvement = grand_welfare - coalition_welfare
        else:
            improvement = coalition_welfare - grand_welfare

        if improvement > stability_threshold:
            # This coalition configuration blocks the grand coalition
            coalition_label = context.get_coalition_label(c_idx)
            blocking_coalitions.append(frozenset([coalition_label]))
            reasons.append(
                f"Coalition config '{coalition_label}' improves welfare by {improvement:.3f}"
            )

    is_stable = len(blocking_coalitions) == 0
    stability_score = 1.0 - (len(blocking_coalitions) / max(1, n_coalitions - 1))

    if is_stable:
        reasons.append("Grand coalition is stable: no blocking coalitions found")

    return CoalitionStabilityResult(
        is_stable=is_stable,
        core_non_empty=is_stable,
        blocking_coalitions=blocking_coalitions,
        stability_score=stability_score,
        reasons=reasons,
    )


# =============================================================================
# Action-Conditioned Slicing
# =============================================================================


def slice_by_action(
    tensor: MoralTensor,
    action_idx: int,
) -> MoralTensor:
    """
    Slice a rank-4 tensor by action index.

    Args:
        tensor: Rank-4 MoralTensor with shape (k, n, a, c).
        action_idx: Index of the action to select.

    Returns:
        Rank-3 MoralTensor with shape (k, n, c).
    """
    if tensor.rank != 4:
        raise ValueError(f"Expected rank-4 tensor, got rank-{tensor.rank}")

    if "a" not in tensor.axis_names:
        raise ValueError("Tensor must have action axis 'a'")

    data = tensor.to_dense()
    n_actions = data.shape[2]

    if action_idx < 0 or action_idx >= n_actions:
        raise IndexError(f"action_idx {action_idx} out of range [0, {n_actions})")

    sliced_data = data[:, :, action_idx, :]

    # Update axis labels
    new_labels = {k: v for k, v in tensor.axis_labels.items() if k != "a"}

    return MoralTensor.from_dense(
        sliced_data,
        axis_names=("k", "n", "c"),
        axis_labels=new_labels,
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata={
            **tensor.metadata,
            "sliced_action_idx": action_idx,
        },
    )


def slice_by_coalition(
    tensor: MoralTensor,
    coalition_idx: int,
) -> MoralTensor:
    """
    Slice a rank-4 tensor by coalition configuration index.

    Args:
        tensor: Rank-4 MoralTensor with shape (k, n, a, c).
        coalition_idx: Index of the coalition configuration to select.

    Returns:
        Rank-3 MoralTensor with shape (k, n, a).
    """
    if tensor.rank != 4:
        raise ValueError(f"Expected rank-4 tensor, got rank-{tensor.rank}")

    if "c" not in tensor.axis_names:
        raise ValueError("Tensor must have coalition axis 'c'")

    data = tensor.to_dense()
    n_coalitions = data.shape[3]

    if coalition_idx < 0 or coalition_idx >= n_coalitions:
        raise IndexError(
            f"coalition_idx {coalition_idx} out of range [0, {n_coalitions})"
        )

    sliced_data = data[:, :, :, coalition_idx]

    # Update axis labels
    new_labels = {k: v for k, v in tensor.axis_labels.items() if k != "c"}

    return MoralTensor.from_dense(
        sliced_data,
        axis_names=("k", "n", "a"),
        axis_labels=new_labels,
        veto_flags=tensor.veto_flags.copy(),
        reason_codes=tensor.reason_codes.copy(),
        metadata={
            **tensor.metadata,
            "sliced_coalition_idx": coalition_idx,
        },
    )


def slice_by_action_profile(
    tensor: MoralTensor,
    action_profile: ActionProfile,
    context: CoalitionContext,
) -> MoralTensor:
    """
    Slice a rank-4 tensor by a joint action profile.

    Args:
        tensor: Rank-4 MoralTensor with shape (k, n, a, c).
        action_profile: Dict mapping agent_id to action index.
        context: CoalitionContext for agent ordering.

    Returns:
        Rank-2 MoralTensor with shape (k, c) - one row per agent.
    """
    if tensor.rank != 4:
        raise ValueError(f"Expected rank-4 tensor, got rank-{tensor.rank}")

    data = tensor.to_dense()
    n_dims = data.shape[0]
    n_agents = data.shape[1]
    n_coalitions = data.shape[3]

    # Extract values for each agent's action choice
    result = np.zeros((n_dims, n_coalitions), dtype=np.float64)

    for agent_idx, agent_id in enumerate(context.agent_ids):
        action_idx = action_profile.get(agent_id, 0)
        # Average this agent's contribution across all agents
        result += data[:, agent_idx, action_idx, :] / n_agents

    new_labels = {k: v for k, v in tensor.axis_labels.items() if k not in ("n", "a")}

    return MoralTensor.from_dense(
        result,
        axis_names=("k", "c"),
        axis_labels=new_labels,
        metadata={
            **tensor.metadata,
            "action_profile": action_profile,
        },
    )


# =============================================================================
# Coalition Tensor Construction
# =============================================================================


def create_coalition_tensor(
    context: CoalitionContext,
    value_function: Callable[[ActionProfile, CoalitionStructure], np.ndarray],
) -> MoralTensor:
    """
    Create a rank-4 coalition tensor from a value function.

    Args:
        context: CoalitionContext describing agents and coalitions.
        value_function: Function (action_profile, coalition) -> moral_values
            where moral_values is array of shape (9, n_agents).

    Returns:
        Rank-4 MoralTensor with shape (9, n_agents, n_actions, n_coalitions).
    """
    n_dims = 9
    n_agents = context.n_agents

    # Get action count (assume uniform for now)
    first_agent = context.agent_ids[0]
    n_actions = len(context.action_labels.get(first_agent, ("default",)))

    # Enumerate coalitions
    coalition_list = list(context.enumerate_coalitions())
    n_coalitions = len(coalition_list)

    # Initialize tensor
    data = np.zeros((n_dims, n_agents, n_actions, n_coalitions), dtype=np.float64)

    # Fill tensor
    for c_idx, coalition_struct in enumerate(coalition_list):
        for action_profile in context.enumerate_action_profiles():
            # Get moral values from value function
            moral_values = value_function(action_profile, coalition_struct)

            # Store in tensor (simplified: use first agent's action as index)
            action_idx = action_profile[first_agent]

            if moral_values.shape == (n_dims, n_agents):
                data[:, :, action_idx, c_idx] = moral_values
            elif moral_values.shape == (n_dims,):
                # Broadcast to all agents
                data[:, :, action_idx, c_idx] = moral_values[:, np.newaxis]
            else:
                raise ValueError(
                    f"value_function returned unexpected shape: {moral_values.shape}"
                )

    # Clamp to [0, 1]
    data = np.clip(data, 0.0, 1.0)

    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n", "a", "c"),
        axis_labels={
            "n": list(context.agent_ids),
            "a": [context.get_action_label(first_agent, i) for i in range(n_actions)],
            "c": [context.get_coalition_label(i) for i in range(n_coalitions)],
        },
        metadata={
            "coalition_mode": context.coalition_mode,
            "n_agents": n_agents,
            "n_coalitions": n_coalitions,
        },
    )


def create_uniform_coalition_tensor(
    context: CoalitionContext,
    base_values: np.ndarray,
) -> MoralTensor:
    """
    Create a rank-4 tensor with uniform values across all configurations.

    Args:
        context: CoalitionContext describing agents and coalitions.
        base_values: Array of shape (9,) or (9, n_agents) with base moral values.

    Returns:
        Rank-4 MoralTensor with uniform values.
    """
    n_dims = 9
    n_agents = context.n_agents

    first_agent = context.agent_ids[0]
    n_actions = len(context.action_labels.get(first_agent, ("default",)))
    n_coalitions = context.n_coalitions

    # Prepare base values
    if base_values.shape == (n_dims,):
        base_2d = np.tile(base_values[:, np.newaxis], (1, n_agents))
    elif base_values.shape == (n_dims, n_agents):
        base_2d = base_values
    else:
        raise ValueError("base_values must have shape (9,) or (9, n_agents)")

    # Broadcast to rank-4
    data = np.tile(
        base_2d[:, :, np.newaxis, np.newaxis], (1, 1, n_actions, n_coalitions)
    )

    coalition_list = list(context.enumerate_coalitions())

    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n", "a", "c"),
        axis_labels={
            "n": list(context.agent_ids),
            "a": [f"action_{i}" for i in range(n_actions)],
            "c": [context.get_coalition_label(i) for i in range(len(coalition_list))],
        },
    )


# =============================================================================
# Coalition Aggregation
# =============================================================================


def aggregate_over_coalitions(
    tensor: MoralTensor,
    method: Literal["mean", "max", "min", "worst_case"] = "mean",
) -> MoralTensor:
    """
    Aggregate a rank-4 tensor over the coalition axis.

    Args:
        tensor: Rank-4 MoralTensor with shape (k, n, a, c).
        method: Aggregation method:
            - "mean": Average over coalitions
            - "max": Maximum over coalitions
            - "min": Minimum over coalitions
            - "worst_case": Worst ethical outcome per dimension

    Returns:
        Rank-3 MoralTensor with shape (k, n, a).
    """
    if tensor.rank != 4:
        raise ValueError(f"Expected rank-4 tensor, got rank-{tensor.rank}")

    data = tensor.to_dense()

    if method == "mean":
        result = np.mean(data, axis=3)
    elif method == "max":
        result = np.max(data, axis=3)
    elif method == "min":
        result = np.min(data, axis=3)
    elif method == "worst_case":
        # For harm dimensions (index 0), max is worst
        # For other dimensions, min is worst
        result = np.zeros(data.shape[:3], dtype=np.float64)
        result[0, :, :] = np.max(
            data[0, :, :, :], axis=2
        )  # physical_harm: max is worst
        for k in range(1, 9):
            result[k, :, :] = np.min(data[k, :, :, :], axis=2)  # others: min is worst
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

    new_labels = {k: v for k, v in tensor.axis_labels.items() if k != "c"}

    return MoralTensor.from_dense(
        result,
        axis_names=("k", "n", "a"),
        axis_labels=new_labels,
        veto_flags=tensor.veto_flags.copy(),
        metadata={
            **tensor.metadata,
            "coalition_aggregation": method,
        },
    )


def aggregate_over_actions(
    tensor: MoralTensor,
    method: Literal["mean", "max", "min", "nash"] = "mean",
) -> MoralTensor:
    """
    Aggregate a rank-4 tensor over the action axis.

    Args:
        tensor: Rank-4 MoralTensor with shape (k, n, a, c).
        method: Aggregation method:
            - "mean": Average over actions
            - "max": Maximum over actions (best action per agent)
            - "min": Minimum over actions (worst action per agent)
            - "nash": Nash equilibrium selection (simplified)

    Returns:
        Rank-3 MoralTensor with shape (k, n, c).
    """
    if tensor.rank != 4:
        raise ValueError(f"Expected rank-4 tensor, got rank-{tensor.rank}")

    data = tensor.to_dense()

    if method == "mean":
        result = np.mean(data, axis=2)
    elif method == "max":
        result = np.max(data, axis=2)
    elif method == "min":
        result = np.min(data, axis=2)
    elif method == "nash":
        # Simplified Nash: each agent picks action maximizing their welfare
        # For now, just use mean as placeholder
        result = np.mean(data, axis=2)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

    new_labels = {k: v for k, v in tensor.axis_labels.items() if k != "a"}

    return MoralTensor.from_dense(
        result,
        axis_names=("k", "n", "c"),
        axis_labels=new_labels,
        veto_flags=tensor.veto_flags.copy(),
        metadata={
            **tensor.metadata,
            "action_aggregation": method,
        },
    )


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Types
    "Coalition",
    "CoalitionStructure",
    "ActionProfile",
    # Core classes
    "CoalitionContext",
    "SparseCoalitionTensor",
    "CoalitionStabilityResult",
    # Stability
    "check_coalition_stability",
    # Slicing
    "slice_by_action",
    "slice_by_coalition",
    "slice_by_action_profile",
    # Construction
    "create_coalition_tensor",
    "create_uniform_coalition_tensor",
    # Aggregation
    "aggregate_over_coalitions",
    "aggregate_over_actions",
]
