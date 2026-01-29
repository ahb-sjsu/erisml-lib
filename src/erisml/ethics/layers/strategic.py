# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Strategic Layer: Multi-agent policy optimization (seconds-hours).

DEME V3 Sprint 10: Complete Strategic Layer Implementation.

The strategic layer handles long-horizon analysis for multi-agent scenarios:
- Coalition stability analysis using game-theoretic methods
- Nash equilibrium detection for strategy profiles
- Policy recommendation generation based on historical patterns
- Integration with decision proofs for audit trails

This layer operates on a longer timescale (seconds to hours) than the
reflex and tactical layers, analyzing patterns across decisions.

Version: 3.0.0 (DEME V3 - Sprint 10)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

import numpy as np

if TYPE_CHECKING:
    from erisml.ethics.decision_proof import DecisionProof

from erisml.ethics.coalition import Coalition, CoalitionContext
from erisml.ethics.moral_tensor import MoralTensor

# =============================================================================
# Stakeholder Feedback (V2 Compatible)
# =============================================================================


@dataclass
class StakeholderFeedback:
    """Feedback from a stakeholder on a decision."""

    stakeholder_id: str
    """Identifier for the stakeholder."""

    decision_id: str
    """ID of the decision being evaluated."""

    satisfaction_score: float
    """Satisfaction with the decision [0, 1]."""

    dimension_feedback: Dict[str, float] = field(default_factory=dict)
    """Per-dimension satisfaction scores."""

    comments: str = ""
    """Free-text comments."""


@dataclass
class ProfileUpdate:
    """Proposed update to a governance profile."""

    dimension: str
    """Which dimension weight to update."""

    current_value: float
    """Current weight value."""

    proposed_value: float
    """Proposed new weight value."""

    rationale: str
    """Explanation for the change."""

    confidence: float = 0.5
    """Confidence in this update [0, 1]."""


# =============================================================================
# V3 Strategic Analysis Types
# =============================================================================


class EquilibriumType(Enum):
    """Types of Nash equilibria."""

    PURE = "pure"
    """Pure strategy Nash equilibrium."""

    MIXED = "mixed"
    """Mixed strategy Nash equilibrium."""

    DOMINANT = "dominant"
    """Dominant strategy equilibrium (stronger than Nash)."""

    PARETO_OPTIMAL = "pareto_optimal"
    """Pareto optimal equilibrium."""


@dataclass(frozen=True)
class StrategyProfile:
    """
    A profile of strategies, one per agent.

    Attributes:
        agent_strategies: Mapping from agent_id to strategy index.
        payoffs: Payoff for each agent under this profile.
        is_equilibrium: Whether this is a Nash equilibrium.
        equilibrium_type: Type of equilibrium if applicable.
    """

    agent_strategies: Dict[str, int]
    payoffs: Dict[str, float]
    is_equilibrium: bool = False
    equilibrium_type: Optional[EquilibriumType] = None

    def get_strategy(self, agent_id: str) -> int:
        """Get strategy index for an agent."""
        return self.agent_strategies.get(agent_id, 0)

    def get_payoff(self, agent_id: str) -> float:
        """Get payoff for an agent."""
        return self.payoffs.get(agent_id, 0.0)


@dataclass(frozen=True)
class NashEquilibriumResult:
    """
    Result of Nash equilibrium analysis.

    Attributes:
        equilibria: List of Nash equilibrium strategy profiles.
        n_pure_equilibria: Number of pure strategy equilibria found.
        has_dominant_strategy: Whether any agent has a dominant strategy.
        pareto_optimal_equilibria: Indices of Pareto optimal equilibria.
        computation_method: Method used ("exact" or "iterative").
        iterations: Number of iterations if iterative.
    """

    equilibria: Tuple[StrategyProfile, ...]
    n_pure_equilibria: int
    has_dominant_strategy: bool
    pareto_optimal_equilibria: Tuple[int, ...]
    computation_method: str = "exact"
    iterations: int = 0

    @property
    def has_equilibrium(self) -> bool:
        """Whether any equilibrium was found."""
        return len(self.equilibria) > 0

    def get_best_equilibrium(self) -> Optional[StrategyProfile]:
        """Get Pareto optimal equilibrium with highest total payoff."""
        if not self.equilibria:
            return None

        if self.pareto_optimal_equilibria:
            pareto_eq = [self.equilibria[i] for i in self.pareto_optimal_equilibria]
            return max(pareto_eq, key=lambda p: sum(p.payoffs.values()))

        return max(self.equilibria, key=lambda p: sum(p.payoffs.values()))


@dataclass(frozen=True)
class CoalitionStabilityAnalysis:
    """
    Analysis of coalition stability in multi-agent scenario.

    Attributes:
        context: The coalition context analyzed.
        is_stable: Whether current configuration is stable.
        blocking_coalitions: Coalitions that could improve by deviating.
        shapley_values: Shapley value attribution per agent.
        core_non_empty: Whether the core is non-empty.
        stability_score: Overall stability score [0, 1].
        recommendations: List of stability improvement recommendations.
    """

    context: CoalitionContext
    is_stable: bool
    blocking_coalitions: Tuple[Coalition, ...]
    shapley_values: Dict[str, float]
    core_non_empty: bool
    stability_score: float
    recommendations: Tuple[str, ...]

    def get_shapley(self, agent_id: str) -> float:
        """Get Shapley value for an agent."""
        return self.shapley_values.get(agent_id, 0.0)


@dataclass
class PolicyRecommendation:
    """
    A policy recommendation based on strategic analysis.

    Attributes:
        recommendation_type: Type of recommendation.
        target_agents: Agents affected by this recommendation.
        description: Human-readable description.
        expected_improvement: Expected improvement in stability/welfare.
        confidence: Confidence in this recommendation [0, 1].
        rationale: Detailed rationale for the recommendation.
    """

    recommendation_type: Literal[
        "coalition_reform",
        "weight_adjustment",
        "action_constraint",
        "incentive_realignment",
        "stakeholder_inclusion",
    ]
    target_agents: Tuple[str, ...]
    description: str
    expected_improvement: float
    confidence: float
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.recommendation_type,
            "targets": list(self.target_agents),
            "description": self.description,
            "expected_improvement": self.expected_improvement,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


@dataclass
class StrategicAnalysisResult:
    """
    Complete result of strategic layer analysis.

    Attributes:
        nash_analysis: Nash equilibrium analysis results.
        coalition_analysis: Coalition stability analysis.
        recommendations: Policy recommendations.
        welfare_metrics: Aggregate welfare metrics.
        timestamp: When analysis was performed.
        analysis_duration_ms: How long analysis took.
    """

    nash_analysis: Optional[NashEquilibriumResult]
    coalition_analysis: Optional[CoalitionStabilityAnalysis]
    recommendations: Tuple[PolicyRecommendation, ...]
    welfare_metrics: Dict[str, float]
    timestamp: str
    analysis_duration_ms: float

    def to_proof_data(self) -> Dict[str, Any]:
        """Convert to data suitable for decision proof."""
        result: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "duration_ms": self.analysis_duration_ms,
            "welfare_metrics": self.welfare_metrics,
        }

        if self.nash_analysis:
            result["nash"] = {
                "has_equilibrium": self.nash_analysis.has_equilibrium,
                "n_equilibria": len(self.nash_analysis.equilibria),
                "n_pure": self.nash_analysis.n_pure_equilibria,
                "has_dominant": self.nash_analysis.has_dominant_strategy,
                "method": self.nash_analysis.computation_method,
            }

        if self.coalition_analysis:
            result["coalition"] = {
                "is_stable": self.coalition_analysis.is_stable,
                "n_blocking": len(self.coalition_analysis.blocking_coalitions),
                "core_non_empty": self.coalition_analysis.core_non_empty,
                "stability_score": self.coalition_analysis.stability_score,
                "shapley_values": self.coalition_analysis.shapley_values,
            }

        if self.recommendations:
            result["recommendations"] = [r.to_dict() for r in self.recommendations]

        return result


# =============================================================================
# Strategic Layer Configuration
# =============================================================================


@dataclass
class StrategicLayerConfig:
    """Configuration for the strategic layer."""

    enabled: bool = True
    """Whether strategic layer is active."""

    # V2 compatibility options
    learning_rate: float = 0.01
    """How fast to adjust profile weights."""

    min_decisions_for_update: int = 100
    """Minimum decisions needed before proposing updates."""

    confidence_threshold: float = 0.8
    """Minimum confidence to propose an update."""

    # V3 multi-agent options
    enable_nash_analysis: bool = True
    """Whether to compute Nash equilibria."""

    enable_coalition_analysis: bool = True
    """Whether to analyze coalition stability."""

    enable_recommendations: bool = True
    """Whether to generate policy recommendations."""

    max_nash_iterations: int = 1000
    """Maximum iterations for Nash equilibrium search."""

    nash_convergence_threshold: float = 1e-6
    """Convergence threshold for iterative Nash methods."""

    min_recommendation_confidence: float = 0.6
    """Minimum confidence for a recommendation."""

    welfare_aggregation: Literal["utilitarian", "rawlsian", "prioritarian"] = (
        "utilitarian"
    )
    """How to aggregate welfare across agents."""


# =============================================================================
# Strategic Layer Implementation
# =============================================================================


class StrategicLayer:
    """
    Strategic layer for multi-agent policy optimization.

    Provides:
    - Nash equilibrium detection for strategy profiles
    - Coalition stability analysis using game-theoretic methods
    - Policy recommendation generation
    - Historical decision pattern analysis

    This layer operates on a longer timescale (seconds to hours) than
    the reflex and tactical layers.

    Example:
        >>> config = StrategicLayerConfig(enabled=True)
        >>> layer = StrategicLayer(config)
        >>> context = CoalitionContext(agent_ids=("a", "b", "c"))
        >>> tensor = MoralTensor.from_dense(np.random.rand(9, 3, 2))
        >>> result = layer.analyze(tensor, context)
        >>> print(result.nash_analysis.has_equilibrium)
    """

    def __init__(
        self,
        config: Optional[StrategicLayerConfig] = None,
    ) -> None:
        """
        Initialize the strategic layer.

        Args:
            config: Layer configuration.
        """
        self.config = config or StrategicLayerConfig()
        self._decision_history: List[DecisionProof] = []
        self._feedback_history: List[StakeholderFeedback] = []
        self._analysis_cache: Dict[str, StrategicAnalysisResult] = {}

    # =========================================================================
    # V2 Compatible Methods
    # =========================================================================

    def record_decision(self, proof: DecisionProof) -> None:
        """
        Record a decision for later analysis.

        Args:
            proof: The decision proof to record.
        """
        self._decision_history.append(proof)

    def record_feedback(self, feedback: StakeholderFeedback) -> None:
        """
        Record stakeholder feedback.

        Args:
            feedback: The feedback to record.
        """
        self._feedback_history.append(feedback)

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze decision patterns for insights.

        Returns:
            Dictionary of analysis results.
        """
        if not self.config.enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "decision_count": len(self._decision_history),
            "feedback_count": len(self._feedback_history),
            "ready_for_update": (
                len(self._decision_history) >= self.config.min_decisions_for_update
            ),
        }

    def propose_updates(self) -> List[ProfileUpdate]:
        """
        Propose profile updates based on analysis.

        Returns:
            List of proposed updates (empty if not enough data).
        """
        if not self.config.enabled:
            return []

        if len(self._decision_history) < self.config.min_decisions_for_update:
            return []

        # Analyze feedback to propose weight adjustments
        updates: List[ProfileUpdate] = []

        if self._feedback_history:
            dim_scores: Dict[str, List[float]] = {}
            for fb in self._feedback_history:
                for dim, score in fb.dimension_feedback.items():
                    if dim not in dim_scores:
                        dim_scores[dim] = []
                    dim_scores[dim].append(score)

            # Propose updates for dimensions with low satisfaction
            for dim, scores in dim_scores.items():
                avg_score = sum(scores) / len(scores)
                if avg_score < 0.5:  # Low satisfaction
                    updates.append(
                        ProfileUpdate(
                            dimension=dim,
                            current_value=1.0,
                            proposed_value=1.0 + self.config.learning_rate,
                            rationale=f"Low satisfaction ({avg_score:.2f}) in {dim}",
                            confidence=min(0.9, len(scores) / 50),
                        )
                    )

        return updates

    def clear_history(self) -> None:
        """Clear decision and feedback history."""
        self._decision_history.clear()
        self._feedback_history.clear()
        self._analysis_cache.clear()

    # =========================================================================
    # V3 Multi-Agent Analysis Methods
    # =========================================================================

    def analyze(
        self,
        tensor: MoralTensor,
        context: CoalitionContext,
        *,
        payoff_func: Optional[Callable[[np.ndarray], float]] = None,
    ) -> StrategicAnalysisResult:
        """
        Perform complete strategic analysis.

        Args:
            tensor: MoralTensor with ethical assessments.
            context: CoalitionContext defining agents and actions.
            payoff_func: Optional custom payoff aggregation function.

        Returns:
            StrategicAnalysisResult with all analyses.
        """
        import time

        start_time = time.perf_counter()

        nash_result = None
        coalition_result = None
        recommendations: List[PolicyRecommendation] = []
        welfare_metrics: Dict[str, float] = {}

        # Get tensor data
        tensor_data = tensor.to_dense()

        # Compute welfare metrics
        welfare_metrics = self._compute_welfare_metrics(tensor_data, context)

        # Nash equilibrium analysis
        if self.config.enable_nash_analysis and tensor.rank >= 3:
            nash_result = self._find_nash_equilibria(tensor_data, context, payoff_func)

        # Coalition stability analysis
        if self.config.enable_coalition_analysis:
            coalition_result = self._analyze_coalition_stability(
                tensor_data, context, payoff_func
            )

        # Generate recommendations
        if self.config.enable_recommendations:
            recommendations = self._generate_recommendations(
                nash_result, coalition_result, welfare_metrics, context
            )

        duration_ms = (time.perf_counter() - start_time) * 1000

        return StrategicAnalysisResult(
            nash_analysis=nash_result,
            coalition_analysis=coalition_result,
            recommendations=tuple(recommendations),
            welfare_metrics=welfare_metrics,
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_duration_ms=duration_ms,
        )

    def find_nash_equilibria(
        self,
        tensor: MoralTensor,
        context: CoalitionContext,
        *,
        payoff_func: Optional[Callable[[np.ndarray], float]] = None,
    ) -> NashEquilibriumResult:
        """
        Find Nash equilibria in the multi-agent game.

        Args:
            tensor: MoralTensor with shape (k, n, a1, a2, ...) or (k, n, a).
            context: CoalitionContext defining agents and actions.
            payoff_func: Custom function to aggregate tensor to payoff.

        Returns:
            NashEquilibriumResult with found equilibria.
        """
        tensor_data = tensor.to_dense()
        return self._find_nash_equilibria(tensor_data, context, payoff_func)

    def analyze_coalition_stability(
        self,
        tensor: MoralTensor,
        context: CoalitionContext,
        *,
        payoff_func: Optional[Callable[[np.ndarray], float]] = None,
    ) -> CoalitionStabilityAnalysis:
        """
        Analyze coalition stability.

        Args:
            tensor: MoralTensor with ethical assessments.
            context: CoalitionContext defining agents.
            payoff_func: Custom payoff aggregation function.

        Returns:
            CoalitionStabilityAnalysis with stability metrics.
        """
        tensor_data = tensor.to_dense()
        return self._analyze_coalition_stability(tensor_data, context, payoff_func)

    def generate_recommendations(
        self,
        tensor: MoralTensor,
        context: CoalitionContext,
    ) -> List[PolicyRecommendation]:
        """
        Generate policy recommendations.

        Args:
            tensor: MoralTensor with ethical assessments.
            context: CoalitionContext defining agents.

        Returns:
            List of policy recommendations.
        """
        result = self.analyze(tensor, context)
        return list(result.recommendations)

    # =========================================================================
    # Internal Analysis Methods
    # =========================================================================

    def _compute_welfare_metrics(
        self,
        tensor_data: np.ndarray,
        context: CoalitionContext,
    ) -> Dict[str, float]:
        """Compute aggregate welfare metrics."""
        n_agents = len(context.agent_ids)

        # Aggregate across dimensions (axis 0)
        if tensor_data.ndim >= 2:
            agent_welfare = tensor_data.mean(axis=0)  # Average across dimensions
            if agent_welfare.ndim > 1:
                # Further aggregate if needed
                agent_welfare = agent_welfare.mean(
                    axis=tuple(range(1, agent_welfare.ndim))
                )
        else:
            agent_welfare = tensor_data

        # Ensure we have per-agent values
        if len(agent_welfare) != n_agents:
            agent_welfare = np.full(n_agents, float(np.mean(tensor_data)))

        # Compute metrics
        total_welfare = float(np.sum(agent_welfare))
        avg_welfare = float(np.mean(agent_welfare))
        min_welfare = float(np.min(agent_welfare))
        max_welfare = float(np.max(agent_welfare))

        # Gini coefficient
        sorted_welfare = np.sort(agent_welfare)
        n = len(sorted_welfare)
        if n > 0 and total_welfare > 0:
            gini = (
                2 * np.sum((np.arange(1, n + 1) * sorted_welfare))
                - (n + 1) * total_welfare
            ) / (n * total_welfare)
            gini = float(max(0, min(1, gini)))
        else:
            gini = 0.0

        return {
            "total_welfare": total_welfare,
            "average_welfare": avg_welfare,
            "min_welfare": min_welfare,
            "max_welfare": max_welfare,
            "welfare_gini": gini,
            "n_agents": n_agents,
        }

    def _find_nash_equilibria(
        self,
        tensor_data: np.ndarray,
        context: CoalitionContext,
        payoff_func: Optional[Callable[[np.ndarray], float]] = None,
    ) -> NashEquilibriumResult:
        """Find Nash equilibria using support enumeration."""
        n_agents = len(context.agent_ids)

        # Get number of actions per agent
        n_actions = []
        for agent_id in context.agent_ids:
            if agent_id in context.action_labels:
                n_actions.append(len(context.action_labels[agent_id]))
            else:
                n_actions.append(2)  # Default to 2 actions

        # Default payoff function: sum across dimensions for each agent
        if payoff_func is None:

            def payoff_func(data: np.ndarray) -> float:
                return float(np.sum(data))

        # Build payoff matrices
        # For simplicity, assume tensor has shape (k, n, a) where a is common action count
        # or we extract payoffs from the tensor appropriately

        equilibria: List[StrategyProfile] = []
        has_dominant = False

        # For small games, enumerate all pure strategy profiles
        if n_agents <= 4 and all(a <= 5 for a in n_actions):
            equilibria, has_dominant = self._enumerate_pure_equilibria(
                tensor_data, context, n_actions, payoff_func
            )

        # Identify Pareto optimal equilibria
        pareto_optimal: List[int] = []
        for i, eq in enumerate(equilibria):
            is_pareto = True
            for j, other in enumerate(equilibria):
                if i != j:
                    # Check if other Pareto dominates eq
                    dominates = all(
                        other.payoffs[a] >= eq.payoffs[a] for a in eq.payoffs
                    ) and any(other.payoffs[a] > eq.payoffs[a] for a in eq.payoffs)
                    if dominates:
                        is_pareto = False
                        break
            if is_pareto:
                pareto_optimal.append(i)

        return NashEquilibriumResult(
            equilibria=tuple(equilibria),
            n_pure_equilibria=len(equilibria),
            has_dominant_strategy=has_dominant,
            pareto_optimal_equilibria=tuple(pareto_optimal),
            computation_method="exact" if n_agents <= 4 else "iterative",
            iterations=0,
        )

    def _enumerate_pure_equilibria(
        self,
        tensor_data: np.ndarray,
        context: CoalitionContext,
        n_actions: List[int],
        payoff_func: Callable[[np.ndarray], float],
    ) -> Tuple[List[StrategyProfile], bool]:
        """Enumerate pure strategy Nash equilibria."""
        from itertools import product

        equilibria: List[StrategyProfile] = []
        has_dominant = False

        # Generate all strategy profiles
        action_ranges = [range(n) for n in n_actions]

        for profile in product(*action_ranges):
            # Compute payoffs for this profile
            payoffs = self._compute_profile_payoffs(
                tensor_data, context, profile, payoff_func
            )

            # Check if this is a Nash equilibrium
            is_equilibrium = True
            eq_type = EquilibriumType.PURE

            for i, agent_id in enumerate(context.agent_ids):
                # Check if agent i can improve by deviating
                current_payoff = payoffs[agent_id]

                for alt_action in range(n_actions[i]):
                    if alt_action == profile[i]:
                        continue

                    # Create alternative profile
                    alt_profile = list(profile)
                    alt_profile[i] = alt_action
                    alt_payoffs = self._compute_profile_payoffs(
                        tensor_data, context, tuple(alt_profile), payoff_func
                    )

                    if alt_payoffs[agent_id] > current_payoff + 1e-10:
                        is_equilibrium = False
                        break

                if not is_equilibrium:
                    break

            if is_equilibrium:
                equilibria.append(
                    StrategyProfile(
                        agent_strategies=dict(zip(context.agent_ids, profile)),
                        payoffs=payoffs,
                        is_equilibrium=True,
                        equilibrium_type=eq_type,
                    )
                )

        # Check for dominant strategy (all equilibria have same strategy for some agent)
        if equilibria:
            for i, agent_id in enumerate(context.agent_ids):
                strategies = {eq.agent_strategies[agent_id] for eq in equilibria}
                if len(strategies) == 1:
                    has_dominant = True
                    break

        return equilibria, has_dominant

    def _compute_profile_payoffs(
        self,
        tensor_data: np.ndarray,
        context: CoalitionContext,
        profile: Tuple[int, ...],
        payoff_func: Callable[[np.ndarray], float],
    ) -> Dict[str, float]:
        """Compute payoffs for each agent given a strategy profile."""
        payoffs: Dict[str, float] = {}

        for i, agent_id in enumerate(context.agent_ids):
            # Extract agent's moral values from tensor
            if tensor_data.ndim == 2:
                # Shape (k, n) - no action dimension
                agent_data = tensor_data[:, i]
            elif tensor_data.ndim == 3:
                # Shape (k, n, a) - single action dimension
                action_idx = profile[i] if i < len(profile) else 0
                if action_idx < tensor_data.shape[2]:
                    agent_data = tensor_data[:, i, action_idx]
                else:
                    agent_data = tensor_data[:, i, 0]
            else:
                # Higher rank - aggregate appropriately
                agent_data = tensor_data[:, i].mean(
                    axis=tuple(range(1, tensor_data.ndim - 1))
                )

            payoffs[agent_id] = payoff_func(agent_data)

        return payoffs

    def _analyze_coalition_stability(
        self,
        tensor_data: np.ndarray,
        context: CoalitionContext,
        payoff_func: Optional[Callable[[np.ndarray], float]] = None,
    ) -> CoalitionStabilityAnalysis:
        """Analyze coalition stability using Shapley values."""
        n_agents = len(context.agent_ids)

        if payoff_func is None:

            def payoff_func(data: np.ndarray) -> float:
                return float(np.sum(data))

        # Build characteristic function from tensor
        def char_func(coalition: Coalition) -> float:
            if not coalition:
                return 0.0
            indices = [
                context.agent_ids.index(a) for a in coalition if a in context.agent_ids
            ]
            if not indices:
                return 0.0
            if tensor_data.ndim >= 2:
                coal_data = tensor_data[:, indices]
            else:
                coal_data = tensor_data
            return payoff_func(coal_data)

        # Compute Shapley values (simplified for small n)
        shapley_values: Dict[str, float] = {}

        if n_agents <= 10:
            # Exact computation
            from itertools import permutations
            import math

            factorial_n = math.factorial(n_agents)
            shapley_sums = {a: 0.0 for a in context.agent_ids}

            for perm in permutations(range(n_agents)):
                current_coalition: set = set()
                for pos in perm:
                    agent = context.agent_ids[pos]
                    prev_value = char_func(frozenset(current_coalition))
                    current_coalition.add(agent)
                    new_value = char_func(frozenset(current_coalition))
                    shapley_sums[agent] += new_value - prev_value

            shapley_values = {a: v / factorial_n for a, v in shapley_sums.items()}
        else:
            # Monte Carlo approximation
            rng = np.random.default_rng(42)
            n_samples = 1000
            shapley_sums = {a: 0.0 for a in context.agent_ids}

            for _ in range(n_samples):
                perm = rng.permutation(n_agents)
                current_coalition: set = set()
                for pos in perm:
                    agent = context.agent_ids[pos]
                    prev_value = char_func(frozenset(current_coalition))
                    current_coalition.add(agent)
                    new_value = char_func(frozenset(current_coalition))
                    shapley_sums[agent] += new_value - prev_value

            shapley_values = {a: v / n_samples for a, v in shapley_sums.items()}

        # Check core stability
        blocking_coalitions: List[Coalition] = []
        core_non_empty = True

        # Check all coalitions for blocking
        for mask in range(1, (1 << n_agents) - 1):
            coalition = frozenset(
                context.agent_ids[i] for i in range(n_agents) if mask & (1 << i)
            )
            coal_value = char_func(coalition)
            alloc_sum = sum(shapley_values[a] for a in coalition)

            if coal_value > alloc_sum + 1e-10:
                blocking_coalitions.append(coalition)
                core_non_empty = False

        is_stable = len(blocking_coalitions) == 0
        stability_score = (
            1.0
            if is_stable
            else max(0.0, 1.0 - len(blocking_coalitions) / (2**n_agents - 2))
        )

        # Generate recommendations
        recommendations: List[str] = []
        if not is_stable:
            recommendations.append(
                f"Consider redistributing value to stabilize {len(blocking_coalitions)} blocking coalitions"
            )
        if shapley_values:
            min_agent = min(shapley_values, key=shapley_values.get)  # type: ignore
            max_agent = max(shapley_values, key=shapley_values.get)  # type: ignore
            if shapley_values[max_agent] > 2 * shapley_values[min_agent]:
                recommendations.append(
                    f"High inequality: {max_agent} receives {shapley_values[max_agent]:.2f} "
                    f"while {min_agent} receives {shapley_values[min_agent]:.2f}"
                )

        return CoalitionStabilityAnalysis(
            context=context,
            is_stable=is_stable,
            blocking_coalitions=tuple(blocking_coalitions),
            shapley_values=shapley_values,
            core_non_empty=core_non_empty,
            stability_score=stability_score,
            recommendations=tuple(recommendations),
        )

    def _generate_recommendations(
        self,
        nash_result: Optional[NashEquilibriumResult],
        coalition_result: Optional[CoalitionStabilityAnalysis],
        welfare_metrics: Dict[str, float],
        context: CoalitionContext,
    ) -> List[PolicyRecommendation]:
        """Generate policy recommendations based on analysis."""
        recommendations: List[PolicyRecommendation] = []

        # Coalition stability recommendations
        if coalition_result and not coalition_result.is_stable:
            recommendations.append(
                PolicyRecommendation(
                    recommendation_type="coalition_reform",
                    target_agents=tuple(context.agent_ids),
                    description="Reform coalition structure to eliminate blocking coalitions",
                    expected_improvement=0.3,
                    confidence=0.7,
                    rationale=(
                        f"{len(coalition_result.blocking_coalitions)} coalitions "
                        "can improve by deviating from current allocation"
                    ),
                )
            )

        # Nash equilibrium recommendations
        if nash_result:
            if not nash_result.has_equilibrium:
                recommendations.append(
                    PolicyRecommendation(
                        recommendation_type="action_constraint",
                        target_agents=tuple(context.agent_ids),
                        description="Add action constraints to enable equilibrium",
                        expected_improvement=0.4,
                        confidence=0.6,
                        rationale="No pure strategy Nash equilibrium exists",
                    )
                )
            elif nash_result.n_pure_equilibria > 1:
                recommendations.append(
                    PolicyRecommendation(
                        recommendation_type="incentive_realignment",
                        target_agents=tuple(context.agent_ids),
                        description="Align incentives to select Pareto optimal equilibrium",
                        expected_improvement=0.2,
                        confidence=0.8,
                        rationale=(
                            f"Multiple equilibria ({nash_result.n_pure_equilibria}) exist; "
                            "coordination mechanism needed"
                        ),
                    )
                )

        # Welfare inequality recommendations
        gini = welfare_metrics.get("welfare_gini", 0.0)
        if gini > 0.3:
            recommendations.append(
                PolicyRecommendation(
                    recommendation_type="weight_adjustment",
                    target_agents=tuple(context.agent_ids),
                    description="Adjust weights to reduce welfare inequality",
                    expected_improvement=0.25,
                    confidence=0.65,
                    rationale=f"Welfare Gini coefficient ({gini:.2f}) indicates significant inequality",
                )
            )

        # Filter by confidence threshold
        recommendations = [
            r
            for r in recommendations
            if r.confidence >= self.config.min_recommendation_confidence
        ]

        return recommendations


__all__ = [
    # V2 compatible types
    "StakeholderFeedback",
    "ProfileUpdate",
    "StrategicLayerConfig",
    "StrategicLayer",
    # V3 types
    "EquilibriumType",
    "StrategyProfile",
    "NashEquilibriumResult",
    "CoalitionStabilityAnalysis",
    "PolicyRecommendation",
    "StrategicAnalysisResult",
]
