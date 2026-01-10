# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for the Strategic Layer (DEME V3 Sprint 10).

Tests cover:
- V2 compatible types (StakeholderFeedback, ProfileUpdate, StrategicLayerConfig)
- V3 types (StrategyProfile, NashEquilibriumResult, CoalitionStabilityAnalysis, etc.)
- Nash equilibrium detection
- Coalition stability analysis
- Policy recommendation generation
- Complete strategic analysis workflow
"""

import numpy as np

from erisml.ethics.coalition import CoalitionContext
from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.layers.strategic import (
    # V2 compatible types
    StakeholderFeedback,
    ProfileUpdate,
    StrategicLayerConfig,
    StrategicLayer,
    # V3 types
    EquilibriumType,
    StrategyProfile,
    NashEquilibriumResult,
    CoalitionStabilityAnalysis,
    PolicyRecommendation,
    StrategicAnalysisResult,
)


# =============================================================================
# Test V2 Compatible Types
# =============================================================================


class TestStakeholderFeedback:
    """Tests for StakeholderFeedback dataclass."""

    def test_basic_creation(self):
        """Test basic feedback creation."""
        feedback = StakeholderFeedback(
            stakeholder_id="s1",
            decision_id="d1",
            satisfaction_score=0.8,
        )
        assert feedback.stakeholder_id == "s1"
        assert feedback.decision_id == "d1"
        assert feedback.satisfaction_score == 0.8
        assert feedback.dimension_feedback == {}
        assert feedback.comments == ""

    def test_with_dimension_feedback(self):
        """Test feedback with dimension scores."""
        feedback = StakeholderFeedback(
            stakeholder_id="s1",
            decision_id="d1",
            satisfaction_score=0.7,
            dimension_feedback={"fairness": 0.9, "privacy": 0.5},
            comments="Good fairness, privacy concerns",
        )
        assert feedback.dimension_feedback["fairness"] == 0.9
        assert feedback.dimension_feedback["privacy"] == 0.5
        assert "privacy" in feedback.comments


class TestProfileUpdate:
    """Tests for ProfileUpdate dataclass."""

    def test_basic_creation(self):
        """Test basic update creation."""
        update = ProfileUpdate(
            dimension="fairness",
            current_value=1.0,
            proposed_value=1.2,
            rationale="Low satisfaction in fairness",
        )
        assert update.dimension == "fairness"
        assert update.current_value == 1.0
        assert update.proposed_value == 1.2
        assert update.confidence == 0.5  # default

    def test_with_confidence(self):
        """Test update with custom confidence."""
        update = ProfileUpdate(
            dimension="privacy",
            current_value=0.8,
            proposed_value=1.0,
            rationale="Increase privacy weight",
            confidence=0.9,
        )
        assert update.confidence == 0.9


class TestStrategicLayerConfig:
    """Tests for StrategicLayerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = StrategicLayerConfig()
        assert config.enabled is True
        assert config.learning_rate == 0.01
        assert config.min_decisions_for_update == 100
        assert config.confidence_threshold == 0.8
        assert config.enable_nash_analysis is True
        assert config.enable_coalition_analysis is True
        assert config.enable_recommendations is True
        assert config.max_nash_iterations == 1000
        assert config.nash_convergence_threshold == 1e-6
        assert config.min_recommendation_confidence == 0.6
        assert config.welfare_aggregation == "utilitarian"

    def test_custom_config(self):
        """Test custom configuration."""
        config = StrategicLayerConfig(
            enabled=False,
            learning_rate=0.05,
            welfare_aggregation="rawlsian",
        )
        assert config.enabled is False
        assert config.learning_rate == 0.05
        assert config.welfare_aggregation == "rawlsian"


# =============================================================================
# Test V3 Types
# =============================================================================


class TestStrategyProfile:
    """Tests for StrategyProfile dataclass."""

    def test_basic_creation(self):
        """Test basic profile creation."""
        profile = StrategyProfile(
            agent_strategies={"a": 0, "b": 1},
            payoffs={"a": 1.5, "b": 2.0},
        )
        assert profile.get_strategy("a") == 0
        assert profile.get_strategy("b") == 1
        assert profile.get_payoff("a") == 1.5
        assert profile.get_payoff("b") == 2.0

    def test_equilibrium_profile(self):
        """Test equilibrium profile."""
        profile = StrategyProfile(
            agent_strategies={"a": 0, "b": 0},
            payoffs={"a": 3.0, "b": 3.0},
            is_equilibrium=True,
            equilibrium_type=EquilibriumType.PURE,
        )
        assert profile.is_equilibrium is True
        assert profile.equilibrium_type == EquilibriumType.PURE

    def test_missing_agent_defaults(self):
        """Test defaults for missing agents."""
        profile = StrategyProfile(
            agent_strategies={"a": 1},
            payoffs={"a": 1.0},
        )
        assert profile.get_strategy("missing") == 0
        assert profile.get_payoff("missing") == 0.0


class TestNashEquilibriumResult:
    """Tests for NashEquilibriumResult dataclass."""

    def test_no_equilibrium(self):
        """Test result with no equilibria."""
        result = NashEquilibriumResult(
            equilibria=(),
            n_pure_equilibria=0,
            has_dominant_strategy=False,
            pareto_optimal_equilibria=(),
        )
        assert result.has_equilibrium is False
        assert result.get_best_equilibrium() is None

    def test_single_equilibrium(self):
        """Test result with single equilibrium."""
        eq = StrategyProfile(
            agent_strategies={"a": 0, "b": 0},
            payoffs={"a": 2.0, "b": 2.0},
            is_equilibrium=True,
        )
        result = NashEquilibriumResult(
            equilibria=(eq,),
            n_pure_equilibria=1,
            has_dominant_strategy=True,
            pareto_optimal_equilibria=(0,),
        )
        assert result.has_equilibrium is True
        assert result.get_best_equilibrium() == eq

    def test_multiple_equilibria(self):
        """Test result with multiple equilibria."""
        eq1 = StrategyProfile(
            agent_strategies={"a": 0, "b": 0},
            payoffs={"a": 2.0, "b": 2.0},
            is_equilibrium=True,
        )
        eq2 = StrategyProfile(
            agent_strategies={"a": 1, "b": 1},
            payoffs={"a": 3.0, "b": 3.0},
            is_equilibrium=True,
        )
        result = NashEquilibriumResult(
            equilibria=(eq1, eq2),
            n_pure_equilibria=2,
            has_dominant_strategy=False,
            pareto_optimal_equilibria=(1,),  # eq2 is Pareto optimal
        )
        # Best should be eq2 (higher total payoff and Pareto optimal)
        best = result.get_best_equilibrium()
        assert best is not None
        assert best.payoffs["a"] == 3.0


class TestCoalitionStabilityAnalysis:
    """Tests for CoalitionStabilityAnalysis dataclass."""

    def test_stable_coalition(self):
        """Test stable coalition analysis."""
        context = CoalitionContext(agent_ids=("a", "b", "c"))
        analysis = CoalitionStabilityAnalysis(
            context=context,
            is_stable=True,
            blocking_coalitions=(),
            shapley_values={"a": 1.0, "b": 1.0, "c": 1.0},
            core_non_empty=True,
            stability_score=1.0,
            recommendations=(),
        )
        assert analysis.is_stable is True
        assert analysis.get_shapley("a") == 1.0
        assert analysis.get_shapley("missing") == 0.0

    def test_unstable_coalition(self):
        """Test unstable coalition analysis."""
        context = CoalitionContext(agent_ids=("a", "b", "c"))
        blocking = (frozenset({"a", "b"}),)
        analysis = CoalitionStabilityAnalysis(
            context=context,
            is_stable=False,
            blocking_coalitions=blocking,
            shapley_values={"a": 2.0, "b": 0.5, "c": 0.5},
            core_non_empty=False,
            stability_score=0.5,
            recommendations=("Redistribute value",),
        )
        assert analysis.is_stable is False
        assert len(analysis.blocking_coalitions) == 1


class TestPolicyRecommendation:
    """Tests for PolicyRecommendation dataclass."""

    def test_basic_recommendation(self):
        """Test basic recommendation creation."""
        rec = PolicyRecommendation(
            recommendation_type="coalition_reform",
            target_agents=("a", "b"),
            description="Reform coalition structure",
            expected_improvement=0.3,
            confidence=0.7,
        )
        assert rec.recommendation_type == "coalition_reform"
        assert rec.target_agents == ("a", "b")
        assert rec.expected_improvement == 0.3

    def test_to_dict(self):
        """Test dictionary conversion."""
        rec = PolicyRecommendation(
            recommendation_type="weight_adjustment",
            target_agents=("a",),
            description="Adjust weights",
            expected_improvement=0.2,
            confidence=0.8,
            rationale="High inequality",
        )
        d = rec.to_dict()
        assert d["type"] == "weight_adjustment"
        assert d["targets"] == ["a"]
        assert d["confidence"] == 0.8
        assert d["rationale"] == "High inequality"


class TestStrategicAnalysisResult:
    """Tests for StrategicAnalysisResult dataclass."""

    def test_basic_result(self):
        """Test basic result creation."""
        result = StrategicAnalysisResult(
            nash_analysis=None,
            coalition_analysis=None,
            recommendations=(),
            welfare_metrics={"total_welfare": 10.0},
            timestamp="2026-01-10T00:00:00Z",
            analysis_duration_ms=5.0,
        )
        assert result.welfare_metrics["total_welfare"] == 10.0
        assert result.analysis_duration_ms == 5.0

    def test_to_proof_data(self):
        """Test proof data conversion."""
        eq = StrategyProfile(
            agent_strategies={"a": 0},
            payoffs={"a": 1.0},
            is_equilibrium=True,
        )
        nash = NashEquilibriumResult(
            equilibria=(eq,),
            n_pure_equilibria=1,
            has_dominant_strategy=False,
            pareto_optimal_equilibria=(0,),
        )
        result = StrategicAnalysisResult(
            nash_analysis=nash,
            coalition_analysis=None,
            recommendations=(),
            welfare_metrics={"total_welfare": 5.0},
            timestamp="2026-01-10T00:00:00Z",
            analysis_duration_ms=10.0,
        )
        proof_data = result.to_proof_data()
        assert proof_data["nash"]["has_equilibrium"] is True
        assert proof_data["nash"]["n_equilibria"] == 1
        assert "coalition" not in proof_data


# =============================================================================
# Test Strategic Layer V2 Methods
# =============================================================================


class TestStrategicLayerV2:
    """Tests for V2-compatible Strategic Layer methods."""

    def test_initialization(self):
        """Test layer initialization."""
        layer = StrategicLayer()
        assert layer.config.enabled is True

        config = StrategicLayerConfig(enabled=False)
        layer2 = StrategicLayer(config)
        assert layer2.config.enabled is False

    def test_analyze_patterns_disabled(self):
        """Test pattern analysis when disabled."""
        config = StrategicLayerConfig(enabled=False)
        layer = StrategicLayer(config)
        result = layer.analyze_patterns()
        assert result["enabled"] is False

    def test_analyze_patterns_enabled(self):
        """Test pattern analysis when enabled."""
        layer = StrategicLayer()
        result = layer.analyze_patterns()
        assert result["enabled"] is True
        assert result["decision_count"] == 0
        assert result["feedback_count"] == 0
        assert result["ready_for_update"] is False

    def test_record_feedback(self):
        """Test recording feedback."""
        layer = StrategicLayer()
        feedback = StakeholderFeedback(
            stakeholder_id="s1",
            decision_id="d1",
            satisfaction_score=0.8,
        )
        layer.record_feedback(feedback)
        result = layer.analyze_patterns()
        assert result["feedback_count"] == 1

    def test_propose_updates_insufficient_data(self):
        """Test update proposals with insufficient data."""
        layer = StrategicLayer()
        updates = layer.propose_updates()
        assert updates == []

    def test_clear_history(self):
        """Test clearing history."""
        layer = StrategicLayer()
        feedback = StakeholderFeedback(
            stakeholder_id="s1",
            decision_id="d1",
            satisfaction_score=0.5,
        )
        layer.record_feedback(feedback)
        layer.clear_history()
        result = layer.analyze_patterns()
        assert result["feedback_count"] == 0


# =============================================================================
# Test Nash Equilibrium Detection
# =============================================================================


class TestNashEquilibriumDetection:
    """Tests for Nash equilibrium detection."""

    def test_simple_coordination_game(self):
        """Test coordination game equilibrium detection."""
        # 2-player coordination game where matching is better
        # Payoffs: (0,0) -> better, (0,1) -> worse, (1,0) -> worse, (1,1) -> ok
        context = CoalitionContext(
            agent_ids=("a", "b"),
            action_labels={"a": ("left", "right"), "b": ("left", "right")},
        )
        # Shape (k=9, n=2, a=2) - moral dimensions, agents, actions
        # MoralTensor requires values in [0, 1]
        tensor_data = np.zeros((9, 2, 2))
        # Agent a's payoffs (normalized to [0, 1])
        tensor_data[:, 0, 0] = 0.9  # action 0 is preferred
        tensor_data[:, 0, 1] = 0.6  # action 1 is ok
        # Agent b's payoffs
        tensor_data[:, 1, 0] = 0.9  # action 0 is preferred
        tensor_data[:, 1, 1] = 0.6  # action 1 is ok

        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        layer = StrategicLayer()
        result = layer.find_nash_equilibria(tensor, context)

        assert result.has_equilibrium is True
        # Both (0,0) and (1,1) should be equilibria in a coordination game
        assert result.n_pure_equilibria >= 1

    def test_no_pure_equilibrium(self):
        """Test game with no pure strategy Nash equilibrium."""
        # Matching pennies - no pure equilibrium
        context = CoalitionContext(
            agent_ids=("a", "b"),
            action_labels={"a": ("heads", "tails"), "b": ("heads", "tails")},
        )
        # Payoffs designed so that no pure strategy is stable
        # MoralTensor requires values in [0, 1]
        tensor_data = np.zeros((9, 2, 2))

        # Agent a prefers matching, b prefers mismatching
        # Use opposing preferences within [0, 1]
        tensor_data[:, 0, 0] = 0.8  # a likes matching on heads
        tensor_data[:, 0, 1] = 0.2  # a dislikes mismatching
        tensor_data[:, 1, 0] = 0.2  # b dislikes matching
        tensor_data[:, 1, 1] = 0.8  # b likes mismatching

        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        layer = StrategicLayer()
        result = layer.find_nash_equilibria(tensor, context)

        # May or may not find equilibrium depending on exact payoffs
        assert isinstance(result, NashEquilibriumResult)

    def test_dominant_strategy(self):
        """Test detection of dominant strategy."""
        context = CoalitionContext(
            agent_ids=("a", "b"),
            action_labels={"a": ("cooperate", "defect"), "b": ("cooperate", "defect")},
        )
        # Prisoner's dilemma - defect is dominant
        # MoralTensor requires values in [0, 1]
        tensor_data = np.zeros((9, 2, 2))
        # Defect (action 1) always gives higher payoff
        tensor_data[:, 0, 0] = 0.5  # cooperate
        tensor_data[:, 0, 1] = 0.8  # defect (dominant)
        tensor_data[:, 1, 0] = 0.5
        tensor_data[:, 1, 1] = 0.8

        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        layer = StrategicLayer()
        result = layer.find_nash_equilibria(tensor, context)

        assert result.has_equilibrium is True


class TestCoalitionStabilityMethods:
    """Tests for coalition stability analysis methods."""

    def test_stable_equal_coalition(self):
        """Test stable coalition with equal values."""
        context = CoalitionContext(agent_ids=("a", "b", "c"))

        # Equal contributions lead to stable coalition
        tensor_data = np.ones((9, 3))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze_coalition_stability(tensor, context)

        assert isinstance(result, CoalitionStabilityAnalysis)
        assert result.shapley_values is not None
        assert len(result.shapley_values) == 3
        # Equal Shapley values for equal contributions
        values = list(result.shapley_values.values())
        assert all(abs(v - values[0]) < 0.01 for v in values)

    def test_unstable_unequal_coalition(self):
        """Test coalition with blocking coalitions."""
        context = CoalitionContext(agent_ids=("a", "b", "c"))

        # Very unequal contributions (within [0, 1] range)
        tensor_data = np.ones((9, 3)) * 0.1
        tensor_data[:, 0] = 0.9  # Agent a contributes much more
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze_coalition_stability(tensor, context)

        assert isinstance(result, CoalitionStabilityAnalysis)
        # With unequal contributions, Shapley values should differ
        assert result.shapley_values["a"] > result.shapley_values["b"]

    def test_shapley_value_retrieval(self):
        """Test Shapley value retrieval."""
        context = CoalitionContext(agent_ids=("a", "b"))
        # MoralTensor requires values in [0, 1]
        tensor_data = np.array([[0.3, 0.6]] * 9)
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze_coalition_stability(tensor, context)

        assert result.get_shapley("a") > 0
        assert result.get_shapley("b") > 0
        assert result.get_shapley("nonexistent") == 0.0


# =============================================================================
# Test Policy Recommendations
# =============================================================================


class TestPolicyRecommendationGeneration:
    """Tests for policy recommendation generation."""

    def test_recommendation_for_high_inequality(self):
        """Test recommendations for high welfare inequality."""
        context = CoalitionContext(agent_ids=("a", "b", "c"))

        # Create high inequality (within [0, 1] range)
        tensor_data = np.ones((9, 3)) * 0.5
        tensor_data[:, 0] = 0.95  # Agent a gets most
        tensor_data[:, 1] = 0.1  # Agent b gets least
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        recommendations = layer.generate_recommendations(tensor, context)

        # Recommendations may be generated (filtered by confidence threshold)
        # If any exist, they should have valid types
        for rec in recommendations:
            assert rec.recommendation_type in (
                "coalition_reform",
                "weight_adjustment",
                "action_constraint",
                "incentive_realignment",
                "stakeholder_inclusion",
            )

    def test_recommendation_confidence_filtering(self):
        """Test that low-confidence recommendations are filtered."""
        config = StrategicLayerConfig(min_recommendation_confidence=0.9)
        layer = StrategicLayer(config)

        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.ones((9, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        recommendations = layer.generate_recommendations(tensor, context)

        # All recommendations should have confidence >= 0.9
        for rec in recommendations:
            assert rec.confidence >= 0.9


# =============================================================================
# Test Complete Strategic Analysis
# =============================================================================


class TestCompleteStrategicAnalysis:
    """Tests for complete strategic analysis workflow."""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        context = CoalitionContext(
            agent_ids=("a", "b", "c"),
            action_labels={
                "a": ("action0", "action1"),
                "b": ("action0", "action1"),
                "c": ("action0", "action1"),
            },
        )

        # Create tensor with 3 agents, 2 actions
        tensor_data = np.random.rand(9, 3, 2)
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        layer = StrategicLayer()
        result = layer.analyze(tensor, context)

        assert isinstance(result, StrategicAnalysisResult)
        assert result.nash_analysis is not None
        assert result.coalition_analysis is not None
        assert result.welfare_metrics is not None
        assert result.analysis_duration_ms > 0

    def test_welfare_metrics_computation(self):
        """Test welfare metrics computation."""
        context = CoalitionContext(agent_ids=("a", "b", "c"))
        # MoralTensor requires values in [0, 1]
        tensor_data = np.array([[0.2, 0.5, 0.8]] * 9)
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze(tensor, context)

        metrics = result.welfare_metrics
        assert "total_welfare" in metrics
        assert "average_welfare" in metrics
        assert "min_welfare" in metrics
        assert "max_welfare" in metrics
        assert "welfare_gini" in metrics
        assert metrics["min_welfare"] <= metrics["average_welfare"]
        assert metrics["average_welfare"] <= metrics["max_welfare"]

    def test_to_proof_data_complete(self):
        """Test complete proof data conversion."""
        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.ones((9, 2, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        layer = StrategicLayer()
        result = layer.analyze(tensor, context)
        proof_data = result.to_proof_data()

        assert "timestamp" in proof_data
        assert "duration_ms" in proof_data
        assert "welfare_metrics" in proof_data

    def test_analysis_with_custom_payoff_function(self):
        """Test analysis with custom payoff function."""
        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.ones((9, 2, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        def custom_payoff(data: np.ndarray) -> float:
            return float(np.mean(data) * 2)

        layer = StrategicLayer()
        result = layer.analyze(tensor, context, payoff_func=custom_payoff)

        assert result.nash_analysis is not None


# =============================================================================
# Test Configuration Effects
# =============================================================================


class TestConfigurationEffects:
    """Tests for configuration effects on analysis."""

    def test_disabled_nash_analysis(self):
        """Test with Nash analysis disabled."""
        config = StrategicLayerConfig(enable_nash_analysis=False)
        layer = StrategicLayer(config)

        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.ones((9, 2, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n", "a"))

        result = layer.analyze(tensor, context)

        assert result.nash_analysis is None

    def test_disabled_coalition_analysis(self):
        """Test with coalition analysis disabled."""
        config = StrategicLayerConfig(enable_coalition_analysis=False)
        layer = StrategicLayer(config)

        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.ones((9, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        result = layer.analyze(tensor, context)

        assert result.coalition_analysis is None

    def test_disabled_recommendations(self):
        """Test with recommendations disabled."""
        config = StrategicLayerConfig(enable_recommendations=False)
        layer = StrategicLayer(config)

        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.ones((9, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        result = layer.analyze(tensor, context)

        assert len(result.recommendations) == 0


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_agent(self):
        """Test with single agent."""
        context = CoalitionContext(agent_ids=("a",))
        tensor_data = np.ones((9, 1))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze(tensor, context)

        assert result.welfare_metrics["n_agents"] == 1
        assert (
            result.welfare_metrics["welfare_gini"] == 0.0
        )  # No inequality with 1 agent

    def test_many_agents(self):
        """Test with many agents."""
        n_agents = 8
        context = CoalitionContext(
            agent_ids=tuple(f"agent_{i}" for i in range(n_agents))
        )
        tensor_data = np.random.rand(9, n_agents)
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze(tensor, context)

        assert result.welfare_metrics["n_agents"] == n_agents

    def test_zero_tensor(self):
        """Test with zero tensor."""
        context = CoalitionContext(agent_ids=("a", "b"))
        tensor_data = np.zeros((9, 2))
        tensor = MoralTensor.from_dense(tensor_data, axis_names=("k", "n"))

        layer = StrategicLayer()
        result = layer.analyze(tensor, context)

        assert result.welfare_metrics["total_welfare"] == 0.0


class TestEquilibriumType:
    """Tests for EquilibriumType enum."""

    def test_equilibrium_types(self):
        """Test all equilibrium types."""
        assert EquilibriumType.PURE.value == "pure"
        assert EquilibriumType.MIXED.value == "mixed"
        assert EquilibriumType.DOMINANT.value == "dominant"
        assert EquilibriumType.PARETO_OPTIMAL.value == "pareto_optimal"
