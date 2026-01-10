# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for coalition context and rank-4 tensors (Sprint 8).

Tests CoalitionContext, coalition enumeration, sparse representation,
stability checking, and action-conditioned slicing.
"""

import numpy as np
import pytest

from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.coalition import (
    CoalitionStructure,
    ActionProfile,
    CoalitionContext,
    SparseCoalitionTensor,
    CoalitionStabilityResult,
    check_coalition_stability,
    slice_by_action,
    slice_by_coalition,
    slice_by_action_profile,
    create_coalition_tensor,
    create_uniform_coalition_tensor,
    aggregate_over_coalitions,
    aggregate_over_actions,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def simple_context():
    """Create a simple 2-agent context."""
    return CoalitionContext(
        agent_ids=("alice", "bob"),
        action_labels={
            "alice": ("left", "right"),
            "bob": ("up", "down"),
        },
        coalition_mode="grand_only",
    )


@pytest.fixture
def three_agent_context():
    """Create a 3-agent context with pairwise coalitions."""
    return CoalitionContext(
        agent_ids=("a", "b", "c"),
        action_labels={
            "a": ("a1", "a2"),
            "b": ("b1", "b2"),
            "c": ("c1", "c2"),
        },
        coalition_mode="pairwise",
    )


@pytest.fixture
def rank4_tensor():
    """Create a rank-4 tensor for testing."""
    # Shape: (9, 3, 2, 4) = (dims, agents, actions, coalitions)
    data = np.random.rand(9, 3, 2, 4)
    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n", "a", "c"),
        axis_labels={
            "n": ["agent_0", "agent_1", "agent_2"],
            "a": ["action_0", "action_1"],
            "c": ["coalition_0", "coalition_1", "coalition_2", "coalition_3"],
        },
    )


@pytest.fixture
def rank2_baseline():
    """Create a rank-2 baseline tensor."""
    data = np.full((9, 2), 0.5)
    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n"),
        axis_labels={"n": ["alice", "bob"]},
    )


# =============================================================================
# CoalitionContext Tests
# =============================================================================


class TestCoalitionContext:
    """Tests for CoalitionContext dataclass."""

    def test_basic_creation(self, simple_context):
        """Test basic context creation."""
        assert simple_context.n_agents == 2
        assert simple_context.agent_ids == ("alice", "bob")
        assert simple_context.coalition_mode == "grand_only"

    def test_n_actions_per_agent(self, simple_context):
        """Test action count per agent."""
        counts = simple_context.n_actions_per_agent
        assert counts["alice"] == 2
        assert counts["bob"] == 2

    def test_total_action_profiles(self, simple_context):
        """Test total action profile count."""
        # 2 actions * 2 actions = 4 profiles
        assert simple_context.total_action_profiles == 4

    def test_empty_agents_error(self):
        """Test that empty agent list raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            CoalitionContext(agent_ids=())

    def test_duplicate_agents_error(self):
        """Test that duplicate agents raise error."""
        with pytest.raises(ValueError, match="must be unique"):
            CoalitionContext(agent_ids=("a", "a", "b"))

    def test_unknown_agent_in_actions_error(self):
        """Test that unknown agent in action_labels raises error."""
        with pytest.raises(ValueError, match="unknown agent"):
            CoalitionContext(
                agent_ids=("a", "b"),
                action_labels={"a": ("x",), "c": ("y",)},  # c is unknown
            )

    def test_from_agents_factory(self):
        """Test from_agents class method."""
        ctx = CoalitionContext.from_agents(
            agents=["x", "y", "z"],
            actions_per_agent=3,
            coalition_mode="singletons_only",
        )
        assert ctx.n_agents == 3
        assert all(len(ctx.action_labels[a]) == 3 for a in ctx.agent_ids)
        assert ctx.coalition_mode == "singletons_only"

    def test_get_action_label(self, simple_context):
        """Test action label retrieval."""
        assert simple_context.get_action_label("alice", 0) == "left"
        assert simple_context.get_action_label("alice", 1) == "right"
        assert simple_context.get_action_label("bob", 0) == "up"

    def test_get_action_label_fallback(self, simple_context):
        """Test action label fallback for invalid index."""
        label = simple_context.get_action_label("alice", 99)
        assert label == "action_99"


class TestCoalitionEnumeration:
    """Tests for coalition enumeration."""

    def test_grand_only_enumeration(self, simple_context):
        """Test grand coalition only mode."""
        coalitions = list(simple_context.enumerate_coalitions())
        assert len(coalitions) == 1
        assert coalitions[0] == (frozenset({"alice", "bob"}),)

    def test_singletons_only_enumeration(self):
        """Test singletons only mode."""
        ctx = CoalitionContext(
            agent_ids=("a", "b", "c"),
            coalition_mode="singletons_only",
        )
        coalitions = list(ctx.enumerate_coalitions())
        assert len(coalitions) == 1
        assert len(coalitions[0]) == 3  # 3 singleton coalitions

    def test_pairwise_enumeration(self, three_agent_context):
        """Test pairwise coalition mode."""
        coalitions = list(three_agent_context.enumerate_coalitions())
        # 1 singleton config + 3 pairwise configs = 4
        assert len(coalitions) == 4

    def test_all_subsets_enumeration(self):
        """Test all subsets mode (Bell number)."""
        ctx = CoalitionContext(
            agent_ids=("a", "b"),
            coalition_mode="all_subsets",
        )
        coalitions = list(ctx.enumerate_coalitions())
        # Bell(2) = 2: {a,b} and {a},{b}
        assert len(coalitions) == 2

    def test_all_subsets_three_agents(self):
        """Test all subsets for 3 agents."""
        ctx = CoalitionContext(
            agent_ids=("a", "b", "c"),
            coalition_mode="all_subsets",
        )
        coalitions = list(ctx.enumerate_coalitions())
        # Bell(3) = 5
        assert len(coalitions) == 5

    def test_custom_coalition_mode(self):
        """Test custom coalition structures."""
        custom = (
            (frozenset({"a", "b"}), frozenset({"c"})),
            (frozenset({"a"}), frozenset({"b", "c"})),
        )
        ctx = CoalitionContext(
            agent_ids=("a", "b", "c"),
            coalition_mode="custom",
            coalition_structures=custom,
        )
        coalitions = list(ctx.enumerate_coalitions())
        assert len(coalitions) == 2

    def test_custom_mode_without_structures_error(self):
        """Test that custom mode requires structures."""
        with pytest.raises(ValueError, match="coalition_structures required"):
            CoalitionContext(
                agent_ids=("a", "b"),
                coalition_mode="custom",
            )

    def test_n_coalitions_property(self, three_agent_context):
        """Test n_coalitions property."""
        assert three_agent_context.n_coalitions == 4


class TestActionProfileEnumeration:
    """Tests for action profile enumeration."""

    def test_enumerate_action_profiles(self, simple_context):
        """Test action profile enumeration."""
        profiles = list(simple_context.enumerate_action_profiles())
        assert len(profiles) == 4  # 2 * 2 = 4

        # Check all combinations present
        expected = [
            {"alice": 0, "bob": 0},
            {"alice": 0, "bob": 1},
            {"alice": 1, "bob": 0},
            {"alice": 1, "bob": 1},
        ]
        for exp in expected:
            assert exp in profiles

    def test_enumerate_three_agents(self, three_agent_context):
        """Test action profile enumeration for 3 agents."""
        profiles = list(three_agent_context.enumerate_action_profiles())
        assert len(profiles) == 8  # 2^3 = 8


# =============================================================================
# SparseCoalitionTensor Tests
# =============================================================================


class TestSparseCoalitionTensor:
    """Tests for SparseCoalitionTensor."""

    def test_creation(self, simple_context, rank2_baseline):
        """Test sparse tensor creation."""
        sparse = SparseCoalitionTensor(
            context=simple_context,
            baseline=rank2_baseline,
        )
        assert sparse.n_stored_deviations == 0
        assert sparse.sparsity_ratio == 0.0

    def test_set_and_get_deviation(self, simple_context, rank2_baseline):
        """Test setting and getting deviations."""
        sparse = SparseCoalitionTensor(
            context=simple_context,
            baseline=rank2_baseline,
            deviation_threshold=0.01,
        )

        action_profile = {"alice": 0, "bob": 1}
        moral_values = np.full((9, 2), 0.8)  # Different from baseline 0.5

        sparse.set_deviation(action_profile, 0, moral_values)

        assert sparse.n_stored_deviations == 1

        retrieved = sparse.get_moral_values(action_profile, 0)
        np.testing.assert_array_almost_equal(retrieved, moral_values)

    def test_small_deviation_not_stored(self, simple_context, rank2_baseline):
        """Test that small deviations are not stored."""
        sparse = SparseCoalitionTensor(
            context=simple_context,
            baseline=rank2_baseline,
            deviation_threshold=0.1,
        )

        action_profile = {"alice": 0, "bob": 0}
        # Deviation of 0.05 is below threshold of 0.1
        moral_values = np.full((9, 2), 0.55)

        sparse.set_deviation(action_profile, 0, moral_values)

        assert sparse.n_stored_deviations == 0

    def test_get_baseline_for_missing(self, simple_context, rank2_baseline):
        """Test that baseline is returned for missing configurations."""
        sparse = SparseCoalitionTensor(
            context=simple_context,
            baseline=rank2_baseline,
        )

        action_profile = {"alice": 1, "bob": 1}
        retrieved = sparse.get_moral_values(action_profile, 0)

        np.testing.assert_array_almost_equal(retrieved, rank2_baseline.to_dense())

    def test_to_dense_tensor(self, simple_context, rank2_baseline):
        """Test conversion to dense tensor."""
        sparse = SparseCoalitionTensor(
            context=simple_context,
            baseline=rank2_baseline,
        )

        dense = sparse.to_dense_tensor()

        assert dense.rank == 4
        assert dense.shape[0] == 9  # moral dimensions
        assert dense.shape[1] == 2  # agents

    def test_invalid_baseline_rank(self, simple_context):
        """Test error for invalid baseline rank."""
        bad_baseline = MoralTensor.from_dense(
            np.ones((9,)),
            axis_names=("k",),
        )
        with pytest.raises(ValueError, match="rank-2 or rank-3"):
            SparseCoalitionTensor(
                context=simple_context,
                baseline=bad_baseline,
            )


# =============================================================================
# Coalition Stability Tests
# =============================================================================


class TestCoalitionStability:
    """Tests for coalition stability checking."""

    def test_stable_coalition(self, rank4_tensor):
        """Test stability check for stable configuration."""
        ctx = CoalitionContext.from_agents(
            agents=["agent_0", "agent_1", "agent_2"],
            actions_per_agent=2,
            coalition_mode="grand_only",
        )

        # Make grand coalition clearly best
        data = rank4_tensor.to_dense()
        data[:, :, :, 0] = 0.2  # Low harm in grand coalition
        data[:, :, :, 1:] = 0.8  # High harm in alternatives

        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "a", "c"),
            axis_labels=rank4_tensor.axis_labels,
        )

        result = check_coalition_stability(
            tensor, ctx, welfare_dimension="physical_harm"
        )

        assert result.is_stable is True
        assert len(result.blocking_coalitions) == 0

    def test_unstable_coalition(self, rank4_tensor):
        """Test stability check for unstable configuration."""
        ctx = CoalitionContext.from_agents(
            agents=["agent_0", "agent_1", "agent_2"],
            actions_per_agent=2,
        )

        # Make alternative coalitions better
        data = rank4_tensor.to_dense()
        data[:, :, :, 0] = 0.8  # High harm in grand coalition
        data[:, :, :, 1:] = 0.2  # Low harm in alternatives

        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "a", "c"),
            axis_labels=rank4_tensor.axis_labels,
        )

        result = check_coalition_stability(
            tensor, ctx, welfare_dimension="physical_harm"
        )

        assert result.is_stable is False
        assert len(result.blocking_coalitions) > 0

    def test_stability_score(self, rank4_tensor):
        """Test stability score calculation."""
        ctx = CoalitionContext.from_agents(
            agents=["agent_0", "agent_1", "agent_2"],
            actions_per_agent=2,
        )

        result = check_coalition_stability(
            rank4_tensor, ctx, welfare_dimension="physical_harm"
        )

        assert 0.0 <= result.stability_score <= 1.0

    def test_wrong_rank_error(self):
        """Test error for non-rank-4 tensor."""
        rank2 = MoralTensor.from_dense(
            np.ones((9, 3)),
            axis_names=("k", "n"),
        )
        ctx = CoalitionContext.from_agents(agents=["a", "b", "c"])

        with pytest.raises(ValueError, match="rank-4"):
            check_coalition_stability(rank2, ctx)


# =============================================================================
# Slicing Tests
# =============================================================================


class TestSlicing:
    """Tests for action-conditioned slicing."""

    def test_slice_by_action(self, rank4_tensor):
        """Test slicing by action index."""
        result = slice_by_action(rank4_tensor, 0)

        assert result.rank == 3
        assert result.shape == (9, 3, 4)  # (k, n, c)
        assert "a" not in result.axis_names

    def test_slice_by_action_preserves_data(self, rank4_tensor):
        """Test that slicing preserves correct data."""
        original = rank4_tensor.to_dense()
        result = slice_by_action(rank4_tensor, 1)

        np.testing.assert_array_equal(result.to_dense(), original[:, :, 1, :])

    def test_slice_by_action_invalid_index(self, rank4_tensor):
        """Test error for invalid action index."""
        with pytest.raises(IndexError, match="out of range"):
            slice_by_action(rank4_tensor, 99)

    def test_slice_by_coalition(self, rank4_tensor):
        """Test slicing by coalition index."""
        result = slice_by_coalition(rank4_tensor, 2)

        assert result.rank == 3
        assert result.shape == (9, 3, 2)  # (k, n, a)
        assert "c" not in result.axis_names

    def test_slice_by_coalition_preserves_data(self, rank4_tensor):
        """Test that coalition slicing preserves correct data."""
        original = rank4_tensor.to_dense()
        result = slice_by_coalition(rank4_tensor, 1)

        np.testing.assert_array_equal(result.to_dense(), original[:, :, :, 1])

    def test_slice_by_coalition_invalid_index(self, rank4_tensor):
        """Test error for invalid coalition index."""
        with pytest.raises(IndexError, match="out of range"):
            slice_by_coalition(rank4_tensor, 99)

    def test_slice_by_action_profile(self, rank4_tensor):
        """Test slicing by action profile."""
        ctx = CoalitionContext.from_agents(
            agents=["agent_0", "agent_1", "agent_2"],
            actions_per_agent=2,
        )
        action_profile = {"agent_0": 0, "agent_1": 1, "agent_2": 0}

        result = slice_by_action_profile(rank4_tensor, action_profile, ctx)

        assert result.rank == 2
        assert result.shape[0] == 9  # k dimension

    def test_slice_wrong_rank_error(self):
        """Test error for non-rank-4 tensor."""
        rank2 = MoralTensor.from_dense(
            np.ones((9, 3)),
            axis_names=("k", "n"),
        )
        with pytest.raises(ValueError, match="rank-4"):
            slice_by_action(rank2, 0)


# =============================================================================
# Tensor Construction Tests
# =============================================================================


class TestTensorConstruction:
    """Tests for coalition tensor construction."""

    def test_create_coalition_tensor(self, simple_context):
        """Test creating coalition tensor from value function."""

        def value_fn(
            action_profile: ActionProfile, coalition: CoalitionStructure
        ) -> np.ndarray:
            # Simple function: higher action indices = higher harm
            harm = sum(action_profile.values()) * 0.1
            values = np.full((9, 2), 0.5)
            values[0, :] = harm  # physical_harm
            return values

        tensor = create_coalition_tensor(simple_context, value_fn)

        assert tensor.rank == 4
        assert tensor.shape[0] == 9  # moral dimensions
        assert tensor.shape[1] == 2  # agents
        assert "c" in tensor.axis_names

    def test_create_uniform_coalition_tensor(self, simple_context):
        """Test creating uniform coalition tensor."""
        base = np.full((9,), 0.3)
        tensor = create_uniform_coalition_tensor(simple_context, base)

        assert tensor.rank == 4
        # All values should be 0.3
        np.testing.assert_array_almost_equal(
            tensor.to_dense(), np.full(tensor.shape, 0.3)
        )

    def test_create_uniform_with_2d_base(self, simple_context):
        """Test creating uniform tensor with 2D base values."""
        base = np.array(
            [
                [0.1, 0.2],  # agent-specific values
                [0.3, 0.4],
                [0.5, 0.5],
                [0.5, 0.5],
                [0.5, 0.5],
                [0.5, 0.5],
                [0.5, 0.5],
                [0.5, 0.5],
                [0.5, 0.5],
            ]
        )
        tensor = create_uniform_coalition_tensor(simple_context, base)

        assert tensor.rank == 4
        # First dimension should vary by agent
        assert tensor.to_dense()[0, 0, 0, 0] == pytest.approx(0.1)
        assert tensor.to_dense()[0, 1, 0, 0] == pytest.approx(0.2)

    def test_create_uniform_invalid_base_shape(self, simple_context):
        """Test error for invalid base shape."""
        bad_base = np.ones((5,))  # Wrong shape
        with pytest.raises(ValueError, match="shape"):
            create_uniform_coalition_tensor(simple_context, bad_base)


# =============================================================================
# Aggregation Tests
# =============================================================================


class TestAggregation:
    """Tests for coalition and action aggregation."""

    def test_aggregate_over_coalitions_mean(self, rank4_tensor):
        """Test mean aggregation over coalitions."""
        result = aggregate_over_coalitions(rank4_tensor, method="mean")

        assert result.rank == 3
        assert result.shape == (9, 3, 2)  # (k, n, a)
        assert "c" not in result.axis_names

    def test_aggregate_over_coalitions_max(self, rank4_tensor):
        """Test max aggregation over coalitions."""
        result = aggregate_over_coalitions(rank4_tensor, method="max")

        original = rank4_tensor.to_dense()
        expected = np.max(original, axis=3)
        np.testing.assert_array_almost_equal(result.to_dense(), expected)

    def test_aggregate_over_coalitions_min(self, rank4_tensor):
        """Test min aggregation over coalitions."""
        result = aggregate_over_coalitions(rank4_tensor, method="min")

        original = rank4_tensor.to_dense()
        expected = np.min(original, axis=3)
        np.testing.assert_array_almost_equal(result.to_dense(), expected)

    def test_aggregate_over_coalitions_worst_case(self, rank4_tensor):
        """Test worst-case aggregation over coalitions."""
        result = aggregate_over_coalitions(rank4_tensor, method="worst_case")

        original = rank4_tensor.to_dense()
        # For physical_harm (dim 0), max is worst
        assert result.to_dense()[0, 0, 0] == pytest.approx(np.max(original[0, 0, 0, :]))
        # For other dimensions, min is worst
        assert result.to_dense()[1, 0, 0] == pytest.approx(np.min(original[1, 0, 0, :]))

    def test_aggregate_over_actions_mean(self, rank4_tensor):
        """Test mean aggregation over actions."""
        result = aggregate_over_actions(rank4_tensor, method="mean")

        assert result.rank == 3
        assert result.shape == (9, 3, 4)  # (k, n, c)
        assert "a" not in result.axis_names

    def test_aggregate_over_actions_max(self, rank4_tensor):
        """Test max aggregation over actions."""
        result = aggregate_over_actions(rank4_tensor, method="max")

        original = rank4_tensor.to_dense()
        expected = np.max(original, axis=2)
        np.testing.assert_array_almost_equal(result.to_dense(), expected)

    def test_aggregate_invalid_method(self, rank4_tensor):
        """Test error for invalid aggregation method."""
        with pytest.raises(ValueError, match="Unknown"):
            aggregate_over_coalitions(rank4_tensor, method="invalid")


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for coalition tensor operations."""

    def test_full_workflow(self, three_agent_context):
        """Test complete coalition tensor workflow."""

        # 1. Create context and tensor
        def value_fn(ap, cs):
            return np.full((9, 3), 0.5)

        tensor = create_coalition_tensor(three_agent_context, value_fn)

        # 2. Check stability
        result = check_coalition_stability(
            tensor, three_agent_context, welfare_dimension="physical_harm"
        )
        assert isinstance(result, CoalitionStabilityResult)

        # 3. Aggregate over coalitions first (rank-4 -> rank-3)
        aggregated = aggregate_over_coalitions(tensor, method="mean")
        assert aggregated.rank == 3
        assert aggregated.shape == (9, 3, 2)  # (k, n, a)

        # 4. Then aggregate over actions (rank-3 -> conceptually rank-2)
        # Or slice by action from original
        sliced = slice_by_action(tensor, 0)
        assert sliced.rank == 3
        assert sliced.shape == (9, 3, 4)  # (k, n, c)

    def test_sparse_to_dense_workflow(self, simple_context, rank2_baseline):
        """Test sparse tensor workflow."""
        # 1. Create sparse tensor
        sparse = SparseCoalitionTensor(
            context=simple_context,
            baseline=rank2_baseline,
        )

        # 2. Add some deviations
        sparse.set_deviation(
            {"alice": 0, "bob": 0},
            coalition_idx=0,
            moral_values=np.full((9, 2), 0.8),
        )

        # 3. Convert to dense
        dense = sparse.to_dense_tensor()
        assert dense.rank == 4

        # 4. Slice and aggregate
        sliced = slice_by_coalition(dense, 0)
        assert sliced.rank == 3


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_single_agent(self):
        """Test with single agent."""
        ctx = CoalitionContext(
            agent_ids=("solo",),
            action_labels={"solo": ("act1", "act2", "act3")},
            coalition_mode="grand_only",
        )
        assert ctx.n_agents == 1
        assert ctx.n_coalitions == 1

        coalitions = list(ctx.enumerate_coalitions())
        assert len(coalitions) == 1

    def test_many_agents_pairwise(self):
        """Test pairwise mode with many agents."""
        ctx = CoalitionContext.from_agents(
            agents=[f"agent_{i}" for i in range(5)],
            coalition_mode="pairwise",
        )
        # 1 singleton config + C(5,2)=10 pairwise configs = 11
        assert ctx.n_coalitions == 11

    def test_single_action_per_agent(self):
        """Test with single action per agent."""
        ctx = CoalitionContext(
            agent_ids=("a", "b"),
            action_labels={
                "a": ("only_action",),
                "b": ("only_action",),
            },
        )
        assert ctx.total_action_profiles == 1

    def test_tensor_with_veto_flags(self):
        """Test slicing preserves veto flags."""
        data = np.random.rand(9, 2, 2, 3)
        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "a", "c"),
            veto_flags=["RIGHTS_VIOLATION"],
        )

        sliced = slice_by_action(tensor, 0)
        assert "RIGHTS_VIOLATION" in sliced.veto_flags

    def test_large_action_space(self):
        """Test with large action space."""
        ctx = CoalitionContext(
            agent_ids=("a", "b"),
            action_labels={
                "a": tuple(f"a{i}" for i in range(10)),
                "b": tuple(f"b{i}" for i in range(10)),
            },
        )
        assert ctx.total_action_profiles == 100
