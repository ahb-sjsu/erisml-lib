# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for temporal tensor operations (Sprint 7).

Tests temporal discounting, irreversibility detection, DTW distance,
window operations, and trend analysis.
"""

import numpy as np
import pytest

from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.temporal_ops import (
    TimeMetadata,
    validate_temporal_tensor,
    is_temporal_tensor,
    apply_temporal_discount,
    temporal_aggregate,
    IrreversibilityResult,
    detect_irreversibility,
    dtw_distance,
    trajectory_similarity,
    slice_time_window,
    sliding_window,
    rolling_aggregate,
    compute_temporal_trend,
    detect_trend_reversal,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def rank2_tensor():
    """Create a standard rank-2 tensor (non-temporal)."""
    data = np.random.rand(9, 3)
    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n"),
        axis_labels={"n": ["alice", "bob", "carol"]},
    )


@pytest.fixture
def temporal_tensor():
    """Create a rank-3 temporal tensor."""
    data = np.random.rand(9, 3, 5)  # 9 dims, 3 parties, 5 timesteps
    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n", "tau"),
        axis_labels={
            "n": ["alice", "bob", "carol"],
            "tau": ["t0", "t1", "t2", "t3", "t4"],
        },
    )


@pytest.fixture
def increasing_harm_tensor():
    """Create tensor with increasing physical harm over time."""
    data = np.ones((9, 2, 5)) * 0.5  # Baseline 0.5

    # Physical harm dimension (index 0) increases over time for party 0
    data[0, 0, :] = [0.2, 0.4, 0.6, 0.8, 0.9]  # alice: increasing harm
    data[0, 1, :] = [0.3, 0.3, 0.3, 0.3, 0.3]  # bob: stable

    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n", "tau"),
        axis_labels={"n": ["alice", "bob"]},
    )


@pytest.fixture
def irreversible_harm_tensor():
    """Create tensor with irreversible harm pattern."""
    # Initialize all dimensions at high values (0.8) for "good" dimensions
    # This ensures only physical_harm (dim 0) triggers irreversibility
    data = np.ones((9, 2, 6)) * 0.8

    # Physical harm (dim 0): harm exceeds threshold at t=2 and never recovers
    data[0, 0, :] = [0.1, 0.2, 0.8, 0.85, 0.9, 0.88]  # alice: irreversible harm
    data[0, 1, :] = [0.1, 0.5, 0.7, 0.4, 0.2, 0.1]  # bob: recovers

    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n", "tau"),
        axis_labels={"n": ["alice", "bob"]},
    )


# =============================================================================
# TimeMetadata Tests
# =============================================================================


class TestTimeMetadata:
    """Tests for TimeMetadata class."""

    def test_basic_creation(self):
        """Test basic TimeMetadata creation."""
        meta = TimeMetadata(
            n_timesteps=5,
            time_unit="hours",
            duration=10.0,
            discount_rate=0.1,
        )
        assert meta.n_timesteps == 5
        assert meta.time_unit == "hours"
        assert meta.duration == 10.0
        assert meta.discount_rate == 0.1

    def test_step_duration(self):
        """Test step_duration property."""
        meta = TimeMetadata(n_timesteps=5, duration=10.0)
        assert meta.step_duration == 2.0

    def test_step_duration_none(self):
        """Test step_duration when duration is None."""
        meta = TimeMetadata(n_timesteps=5)
        assert meta.step_duration is None

    def test_with_labels(self):
        """Test creation with time labels."""
        meta = TimeMetadata(
            n_timesteps=3,
            time_labels=("t0", "t1", "t2"),
        )
        assert meta.time_labels == ("t0", "t1", "t2")

    def test_invalid_n_timesteps(self):
        """Test that n_timesteps must be >= 1."""
        with pytest.raises(ValueError, match="n_timesteps must be >= 1"):
            TimeMetadata(n_timesteps=0)

    def test_invalid_labels_length(self):
        """Test that time_labels length must match n_timesteps."""
        with pytest.raises(ValueError, match="time_labels length"):
            TimeMetadata(n_timesteps=3, time_labels=("t0", "t1"))

    def test_invalid_discount_rate_negative(self):
        """Test that discount_rate cannot be negative."""
        with pytest.raises(ValueError, match="discount_rate must be in"):
            TimeMetadata(n_timesteps=3, discount_rate=-0.1)

    def test_invalid_discount_rate_too_high(self):
        """Test that discount_rate must be < 1."""
        with pytest.raises(ValueError, match="discount_rate must be in"):
            TimeMetadata(n_timesteps=3, discount_rate=1.0)

    def test_get_discount_weights_zero_rate(self):
        """Test discount weights with zero rate."""
        meta = TimeMetadata(n_timesteps=5, discount_rate=0.0)
        weights = meta.get_discount_weights()
        np.testing.assert_array_equal(weights, np.ones(5))

    def test_get_discount_weights_nonzero_rate(self):
        """Test discount weights with nonzero rate."""
        meta = TimeMetadata(n_timesteps=3, discount_rate=0.1)
        weights = meta.get_discount_weights()

        expected = np.array([1.0, 0.9, 0.81])
        np.testing.assert_array_almost_equal(weights, expected)

    def test_from_tensor(self, temporal_tensor):
        """Test creating TimeMetadata from tensor."""
        meta = TimeMetadata.from_tensor(
            temporal_tensor,
            time_unit="days",
            duration=5.0,
            discount_rate=0.05,
        )
        assert meta.n_timesteps == 5
        assert meta.time_unit == "days"
        assert meta.time_labels == ("t0", "t1", "t2", "t3", "t4")

    def test_from_tensor_no_tau_axis(self, rank2_tensor):
        """Test from_tensor raises for non-temporal tensor."""
        with pytest.raises(ValueError, match="does not have temporal axis"):
            TimeMetadata.from_tensor(rank2_tensor)


# =============================================================================
# Validation Tests
# =============================================================================


class TestTemporalValidation:
    """Tests for temporal tensor validation."""

    def test_validate_temporal_tensor_valid(self, temporal_tensor):
        """Test validation passes for valid temporal tensor."""
        validate_temporal_tensor(temporal_tensor)  # Should not raise

    def test_validate_temporal_tensor_rank2(self, rank2_tensor):
        """Test validation fails for rank-2 tensor."""
        with pytest.raises(ValueError, match="rank >= 3"):
            validate_temporal_tensor(rank2_tensor)

    def test_validate_temporal_tensor_wrong_axis_order(self):
        """Test validation fails when tau is not at position 2."""
        data = np.random.rand(9, 5, 3)
        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "tau", "n"),  # Wrong order
        )
        with pytest.raises(ValueError, match="must be at position 2"):
            validate_temporal_tensor(tensor)

    def test_is_temporal_tensor_true(self, temporal_tensor):
        """Test is_temporal_tensor returns True for temporal tensor."""
        assert is_temporal_tensor(temporal_tensor) is True

    def test_is_temporal_tensor_false(self, rank2_tensor):
        """Test is_temporal_tensor returns False for non-temporal tensor."""
        assert is_temporal_tensor(rank2_tensor) is False


# =============================================================================
# Temporal Discounting Tests
# =============================================================================


class TestTemporalDiscount:
    """Tests for temporal discounting operations."""

    def test_zero_discount(self, temporal_tensor):
        """Test that zero discount returns same tensor."""
        result = apply_temporal_discount(temporal_tensor, 0.0)
        np.testing.assert_array_equal(result.to_dense(), temporal_tensor.to_dense())

    def test_exponential_discount(self):
        """Test exponential discounting."""
        data = np.ones((9, 2, 4))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = apply_temporal_discount(tensor, 0.1, method="exponential")
        result_data = result.to_dense()

        # Check expected weights: 1.0, 0.9, 0.81, 0.729
        expected_weights = [1.0, 0.9, 0.81, 0.729]
        for t, w in enumerate(expected_weights):
            np.testing.assert_almost_equal(result_data[0, 0, t], w)

    def test_hyperbolic_discount(self):
        """Test hyperbolic discounting."""
        data = np.ones((9, 2, 4))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = apply_temporal_discount(tensor, 0.5, method="hyperbolic")
        result_data = result.to_dense()

        # Hyperbolic: 1/(1 + 0.5*t)
        expected_weights = [1.0, 1 / 1.5, 1 / 2.0, 1 / 2.5]
        for t, w in enumerate(expected_weights):
            np.testing.assert_almost_equal(result_data[0, 0, t], w)

    def test_linear_discount(self):
        """Test linear discounting."""
        data = np.ones((9, 2, 4))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = apply_temporal_discount(tensor, 0.25, method="linear")
        result_data = result.to_dense()

        # Linear: max(0, 1 - 0.25*t)
        expected_weights = [1.0, 0.75, 0.5, 0.25]
        for t, w in enumerate(expected_weights):
            np.testing.assert_almost_equal(result_data[0, 0, t], w)

    def test_linear_discount_clamps_to_zero(self):
        """Test that linear discount clamps to 0."""
        data = np.ones((9, 2, 5))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = apply_temporal_discount(tensor, 0.3, method="linear")
        result_data = result.to_dense()

        # At t=4: 1 - 0.3*4 = -0.2 → clamped to 0
        assert result_data[0, 0, 4] >= 0.0

    def test_invalid_discount_rate(self, temporal_tensor):
        """Test invalid discount rate raises error."""
        with pytest.raises(ValueError, match="discount_rate must be in"):
            apply_temporal_discount(temporal_tensor, -0.1)

        with pytest.raises(ValueError, match="discount_rate must be in"):
            apply_temporal_discount(temporal_tensor, 1.5)

    def test_invalid_method(self, temporal_tensor):
        """Test invalid discount method raises error."""
        with pytest.raises(ValueError, match="Unknown discount method"):
            apply_temporal_discount(temporal_tensor, 0.1, method="invalid")

    def test_discount_preserves_metadata(self, temporal_tensor):
        """Test that discounting preserves tensor metadata."""
        result = apply_temporal_discount(temporal_tensor, 0.1)
        assert result.axis_names == temporal_tensor.axis_names
        assert result.axis_labels == temporal_tensor.axis_labels
        assert result.metadata.get("temporal_discount_applied") is True


class TestTemporalAggregate:
    """Tests for temporal aggregation."""

    def test_mean_aggregation(self, temporal_tensor):
        """Test mean aggregation over time."""
        result = temporal_aggregate(temporal_tensor, method="mean")

        assert result.rank == 2
        assert result.shape == (9, 3)
        assert "tau" not in result.axis_names

    def test_sum_aggregation(self):
        """Test sum aggregation over time."""
        data = np.ones((9, 2, 3))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = temporal_aggregate(tensor, method="sum")
        result_data = result.to_dense()

        # Sum should be clamped to 1.0
        np.testing.assert_almost_equal(result_data, np.ones((9, 2)))

    def test_max_aggregation(self):
        """Test max aggregation over time."""
        data = np.random.rand(9, 2, 4)
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = temporal_aggregate(tensor, method="max")
        result_data = result.to_dense()

        expected = np.max(data, axis=2)
        np.testing.assert_array_almost_equal(result_data, expected)

    def test_min_aggregation(self):
        """Test min aggregation over time."""
        data = np.random.rand(9, 2, 4)
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        result = temporal_aggregate(tensor, method="min")
        result_data = result.to_dense()

        expected = np.min(data, axis=2)
        np.testing.assert_array_almost_equal(result_data, expected)

    def test_discounted_mean(self, temporal_tensor):
        """Test mean aggregation with discounting."""
        result = temporal_aggregate(temporal_tensor, discount_rate=0.1, method="mean")

        # Should produce different result than non-discounted
        result_nodiscount = temporal_aggregate(
            temporal_tensor, discount_rate=0.0, method="mean"
        )

        # Values should differ (unless all timesteps are identical)
        assert not np.allclose(result.to_dense(), result_nodiscount.to_dense())


# =============================================================================
# Irreversibility Detection Tests
# =============================================================================


class TestIrreversibilityDetection:
    """Tests for irreversibility detection."""

    def test_no_irreversibility(self, temporal_tensor):
        """Test detection when no irreversible harm."""
        # Random tensor unlikely to have irreversible patterns
        result = detect_irreversibility(temporal_tensor, harm_threshold=0.99)

        assert result.is_irreversible is False
        assert len(result.irreversible_parties) == 0

    def test_detect_irreversible_harm(self, irreversible_harm_tensor):
        """Test detection of irreversible physical harm."""
        result = detect_irreversibility(
            irreversible_harm_tensor,
            harm_threshold=0.7,
            recovery_threshold=0.3,
            min_sustained_steps=2,
        )

        assert result.is_irreversible is True
        assert "alice" in result.irreversible_parties
        assert "bob" not in result.irreversible_parties
        assert "physical_harm" in result.irreversible_dimensions
        assert result.veto_recommended is True

    def test_irreversibility_timesteps(self, irreversible_harm_tensor):
        """Test that irreversibility timesteps are tracked."""
        result = detect_irreversibility(
            irreversible_harm_tensor,
            harm_threshold=0.7,
            min_sustained_steps=2,
        )

        assert ("alice", "physical_harm") in result.irreversibility_timesteps
        assert result.irreversibility_timesteps[("alice", "physical_harm")] >= 2

    def test_specific_dimensions(self, temporal_tensor):
        """Test detection for specific dimensions only."""
        result = detect_irreversibility(
            temporal_tensor,
            dimensions=["physical_harm", "rights_respect"],
        )

        # Result should only check specified dimensions
        for dim in result.irreversible_dimensions:
            assert dim in ["physical_harm", "rights_respect"]

    def test_reasons_populated(self, irreversible_harm_tensor):
        """Test that reasons are populated."""
        result = detect_irreversibility(irreversible_harm_tensor, harm_threshold=0.7)

        assert len(result.reasons) > 0
        assert any("alice" in r for r in result.reasons)

    def test_harm_trajectories_recorded(self, irreversible_harm_tensor):
        """Test that harm trajectories are recorded."""
        result = detect_irreversibility(irreversible_harm_tensor, harm_threshold=0.7)

        if result.is_irreversible:
            assert "alice" in result.harm_trajectories
            assert len(result.harm_trajectories["alice"]) == 6


# =============================================================================
# DTW Distance Tests
# =============================================================================


class TestDTWDistance:
    """Tests for Dynamic Time Warping distance."""

    def test_identical_trajectories(self):
        """Test that identical trajectories have zero distance."""
        data = np.random.rand(9, 2, 5)
        t1 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        dist = dtw_distance(t1, t2)
        assert dist == pytest.approx(0.0, abs=1e-10)

    def test_different_trajectories(self):
        """Test that different trajectories have positive distance."""
        data1 = np.zeros((9, 2, 5))
        data2 = np.ones((9, 2, 5))

        t1 = MoralTensor.from_dense(data1, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data2, axis_names=("k", "n", "tau"))

        dist = dtw_distance(t1, t2)
        assert dist > 0

    def test_specific_dimension(self, temporal_tensor):
        """Test DTW for specific dimension."""
        dist = dtw_distance(temporal_tensor, temporal_tensor, dimension="physical_harm")
        assert dist == pytest.approx(0.0, abs=1e-10)

    def test_specific_party(self, temporal_tensor):
        """Test DTW for specific party by name."""
        dist = dtw_distance(temporal_tensor, temporal_tensor, party="alice")
        assert dist == pytest.approx(0.0, abs=1e-10)

    def test_specific_party_index(self, temporal_tensor):
        """Test DTW for specific party by index."""
        dist = dtw_distance(temporal_tensor, temporal_tensor, party=0)
        assert dist == pytest.approx(0.0, abs=1e-10)

    def test_incompatible_party_dimensions(self):
        """Test error for incompatible party dimensions."""
        data1 = np.random.rand(9, 2, 5)
        data2 = np.random.rand(9, 3, 5)

        t1 = MoralTensor.from_dense(data1, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data2, axis_names=("k", "n", "tau"))

        with pytest.raises(ValueError, match="Party dimensions must match"):
            dtw_distance(t1, t2)

    def test_unknown_dimension(self, temporal_tensor):
        """Test error for unknown dimension."""
        with pytest.raises(ValueError, match="Unknown dimension"):
            dtw_distance(temporal_tensor, temporal_tensor, dimension="invalid")

    def test_unknown_party(self, temporal_tensor):
        """Test error for unknown party."""
        with pytest.raises(ValueError, match="not found"):
            dtw_distance(temporal_tensor, temporal_tensor, party="unknown")


class TestTrajectorySimilarity:
    """Tests for trajectory similarity."""

    def test_identical_trajectories_dtw(self):
        """Test identical trajectories have similarity 1.0 with DTW."""
        data = np.random.rand(9, 2, 5)
        t1 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        sim = trajectory_similarity(t1, t2, method="dtw")
        assert sim == pytest.approx(1.0, abs=1e-5)

    def test_identical_trajectories_euclidean(self):
        """Test identical trajectories have similarity 1.0 with Euclidean."""
        data = np.random.rand(9, 2, 5)
        t1 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        sim = trajectory_similarity(t1, t2, method="euclidean")
        assert sim == pytest.approx(1.0, abs=1e-5)

    def test_identical_trajectories_cosine(self):
        """Test identical trajectories have high similarity with cosine."""
        # Use fixed predictable data to avoid random edge cases
        data = np.full((9, 2, 5), 0.5)  # All 0.5 values
        data[0, :, :] = 0.3  # Make some variation
        data[1, :, :] = 0.7
        t1 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        sim = trajectory_similarity(t1, t2, method="cosine")
        assert sim > 0.99

    def test_similarity_range(self, temporal_tensor):
        """Test that similarity is in [0, 1]."""
        data2 = np.random.rand(9, 3, 5)
        t2 = MoralTensor.from_dense(
            data2,
            axis_names=("k", "n", "tau"),
            axis_labels={"n": ["alice", "bob", "carol"]},
        )

        for method in ["dtw", "euclidean", "cosine"]:
            sim = trajectory_similarity(temporal_tensor, t2, method=method)
            assert 0.0 <= sim <= 1.0

    def test_different_temporal_lengths(self):
        """Test similarity with different temporal lengths."""
        data1 = np.random.rand(9, 2, 5)
        data2 = np.random.rand(9, 2, 8)

        t1 = MoralTensor.from_dense(data1, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data2, axis_names=("k", "n", "tau"))

        # Should not raise - handles different lengths
        sim = trajectory_similarity(t1, t2, method="dtw")
        assert 0.0 <= sim <= 1.0

    def test_invalid_method(self, temporal_tensor):
        """Test error for invalid method."""
        with pytest.raises(ValueError, match="Unknown similarity method"):
            trajectory_similarity(temporal_tensor, temporal_tensor, method="invalid")


# =============================================================================
# Window Operations Tests
# =============================================================================


class TestSliceTimeWindow:
    """Tests for time window slicing."""

    def test_basic_slice(self, temporal_tensor):
        """Test basic time window slice."""
        result = slice_time_window(temporal_tensor, 1, 4)

        assert result.shape[2] == 3
        assert result.rank == 3

    def test_slice_preserves_data(self, temporal_tensor):
        """Test that slice preserves correct data."""
        result = slice_time_window(temporal_tensor, 1, 3)

        expected = temporal_tensor.to_dense()[:, :, 1:3]
        np.testing.assert_array_equal(result.to_dense(), expected)

    def test_invalid_start(self, temporal_tensor):
        """Test error for invalid start index."""
        with pytest.raises(ValueError, match="Invalid window"):
            slice_time_window(temporal_tensor, -1, 3)

    def test_invalid_end(self, temporal_tensor):
        """Test error for invalid end index."""
        with pytest.raises(ValueError, match="Invalid window"):
            slice_time_window(temporal_tensor, 0, 10)

    def test_start_after_end(self, temporal_tensor):
        """Test error when start >= end."""
        with pytest.raises(ValueError, match="Invalid window"):
            slice_time_window(temporal_tensor, 3, 2)


class TestSlidingWindow:
    """Tests for sliding window operation."""

    def test_basic_sliding_window(self, temporal_tensor):
        """Test basic sliding window."""
        windows = sliding_window(temporal_tensor, window_size=3)

        # 5 timesteps, window size 3, stride 1 → 3 windows
        assert len(windows) == 3

        for w in windows:
            assert w.shape[2] == 3

    def test_sliding_window_with_stride(self, temporal_tensor):
        """Test sliding window with stride > 1."""
        windows = sliding_window(temporal_tensor, window_size=2, stride=2)

        # 5 timesteps, window size 2, stride 2 → 2 windows
        assert len(windows) == 2

    def test_window_too_large(self, temporal_tensor):
        """Test error when window size exceeds timesteps."""
        with pytest.raises(ValueError, match="cannot exceed"):
            sliding_window(temporal_tensor, window_size=10)

    def test_windows_contain_correct_data(self, temporal_tensor):
        """Test that windows contain correct slices."""
        windows = sliding_window(temporal_tensor, window_size=2)
        original = temporal_tensor.to_dense()

        for i, w in enumerate(windows):
            expected = original[:, :, i : i + 2]
            np.testing.assert_array_equal(w.to_dense(), expected)


class TestRollingAggregate:
    """Tests for rolling aggregate operation."""

    def test_rolling_mean(self):
        """Test rolling mean."""
        # Create predictable data in [0, 1] range
        data = np.zeros((9, 2, 5))
        data[0, 0, :] = [0.1, 0.2, 0.3, 0.4, 0.5]

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        result = rolling_aggregate(tensor, window_size=3, method="mean")

        # Window 0: mean([0.1, 0.2, 0.3]) = 0.2
        # Window 1: mean([0.2, 0.3, 0.4]) = 0.3
        # Window 2: mean([0.3, 0.4, 0.5]) = 0.4
        expected = [0.2, 0.3, 0.4]

        for i, exp in enumerate(expected):
            assert result.to_dense()[0, 0, i] == pytest.approx(exp)

    def test_rolling_max(self):
        """Test rolling max."""
        data = np.zeros((9, 2, 5))
        data[0, 0, :] = [0.1, 0.3, 0.2, 0.5, 0.4]

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        result = rolling_aggregate(tensor, window_size=3, method="max")

        # Window 0: max([0.1, 0.3, 0.2]) = 0.3
        # Window 1: max([0.3, 0.2, 0.5]) = 0.5
        # Window 2: max([0.2, 0.5, 0.4]) = 0.5
        expected = [0.3, 0.5, 0.5]

        for i, exp in enumerate(expected):
            assert result.to_dense()[0, 0, i] == pytest.approx(exp)

    def test_rolling_min(self):
        """Test rolling min."""
        data = np.zeros((9, 2, 5))
        data[0, 0, :] = [0.1, 0.3, 0.2, 0.5, 0.4]

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        result = rolling_aggregate(tensor, window_size=3, method="min")

        # Window 0: min([0.1, 0.3, 0.2]) = 0.1
        # Window 1: min([0.3, 0.2, 0.5]) = 0.2
        # Window 2: min([0.2, 0.5, 0.4]) = 0.2
        expected = [0.1, 0.2, 0.2]

        for i, exp in enumerate(expected):
            assert result.to_dense()[0, 0, i] == pytest.approx(exp)

    def test_rolling_with_stride(self, temporal_tensor):
        """Test rolling aggregate with stride > 1."""
        result = rolling_aggregate(
            temporal_tensor, window_size=2, stride=2, method="mean"
        )

        # Should have fewer output timesteps
        assert result.shape[2] == 2


# =============================================================================
# Trend Analysis Tests
# =============================================================================


class TestTemporalTrend:
    """Tests for temporal trend computation."""

    def test_increasing_trend(self):
        """Test detection of increasing trend."""
        data = np.zeros((9, 2, 5))
        data[0, 0, :] = [0.1, 0.2, 0.3, 0.4, 0.5]  # Perfect linear increase

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        trends = compute_temporal_trend(tensor)

        assert trends["slopes"][0, 0] > 0
        assert trends["r_squared"][0, 0] > 0.99

    def test_decreasing_trend(self):
        """Test detection of decreasing trend."""
        data = np.zeros((9, 2, 5))
        data[0, 0, :] = [0.5, 0.4, 0.3, 0.2, 0.1]  # Perfect linear decrease

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        trends = compute_temporal_trend(tensor)

        assert trends["slopes"][0, 0] < 0
        assert trends["r_squared"][0, 0] > 0.99

    def test_flat_trend(self):
        """Test detection of flat/no trend."""
        data = np.ones((9, 2, 5)) * 0.5

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        trends = compute_temporal_trend(tensor)

        assert trends["slopes"][0, 0] == pytest.approx(0.0, abs=1e-10)

    def test_specific_dimension(self):
        """Test trend for specific dimension."""
        data = np.zeros((9, 2, 5))
        data[0, 0, :] = [0.1, 0.2, 0.3, 0.4, 0.5]

        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))
        trends = compute_temporal_trend(tensor, dimension="physical_harm")

        # Only physical_harm (dim 0) should have nonzero slope
        assert trends["slopes"][0, 0] > 0
        # Other dimensions should have zero slopes
        for k in range(1, 9):
            assert trends["slopes"][k, 0] == pytest.approx(0.0, abs=1e-10)

    def test_trend_output_shape(self, temporal_tensor):
        """Test that trend output has correct shape."""
        trends = compute_temporal_trend(temporal_tensor)

        assert trends["slopes"].shape == (9, 3)
        assert trends["intercepts"].shape == (9, 3)
        assert trends["r_squared"].shape == (9, 3)


class TestTrendReversal:
    """Tests for trend reversal detection."""

    def test_no_reversal(self):
        """Test when there's no reversal."""
        data = np.zeros((9, 2, 5))
        data[:, 0, :] = np.linspace(0.1, 0.5, 5)  # Monotonic increase

        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "tau"),
            axis_labels={"n": ["alice", "bob"]},
        )
        reversals = detect_trend_reversal(tensor, threshold=0.05)

        assert len(reversals["alice"]) == 0

    def test_single_reversal(self):
        """Test detection of single reversal."""
        data = np.zeros((9, 2, 5))
        # Mean across dimensions goes up then down
        data[:, 0, :] = np.array([[0.2, 0.4, 0.6, 0.4, 0.2]] * 9)

        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "tau"),
            axis_labels={"n": ["alice", "bob"]},
        )
        reversals = detect_trend_reversal(tensor, threshold=0.1)

        # Should detect reversal around t=2
        assert len(reversals["alice"]) >= 1

    def test_threshold_sensitivity(self):
        """Test that threshold affects detection."""
        data = np.zeros((9, 2, 5))
        data[:, 0, :] = np.array(
            [[0.5, 0.55, 0.52, 0.57, 0.54]] * 9
        )  # Small oscillations

        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "tau"),
            axis_labels={"n": ["alice", "bob"]},
        )

        # High threshold should not detect small oscillations
        high_thresh = detect_trend_reversal(tensor, threshold=0.1)
        # Low threshold should detect them
        low_thresh = detect_trend_reversal(tensor, threshold=0.01)

        assert len(high_thresh["alice"]) <= len(low_thresh["alice"])


# =============================================================================
# Integration Tests
# =============================================================================


class TestTemporalIntegration:
    """Integration tests for temporal operations."""

    def test_discount_then_aggregate(self, temporal_tensor):
        """Test discounting followed by aggregation."""
        discounted = apply_temporal_discount(temporal_tensor, 0.1)
        aggregated = temporal_aggregate(discounted, method="mean")

        assert aggregated.rank == 2
        assert aggregated.shape == (9, 3)

    def test_irreversibility_with_discounting(self, irreversible_harm_tensor):
        """Test irreversibility detection on discounted tensor."""
        discounted = apply_temporal_discount(irreversible_harm_tensor, 0.05)
        result = detect_irreversibility(discounted, harm_threshold=0.7)

        # Alice should still show irreversible harm (values are lowered but pattern remains)
        assert result.is_irreversible is True

    def test_sliding_window_and_aggregate(self, temporal_tensor):
        """Test sliding window then aggregating each window."""
        windows = sliding_window(temporal_tensor, window_size=3)

        aggregates = []
        for w in windows:
            agg = temporal_aggregate(w, method="mean")
            aggregates.append(agg)

        assert len(aggregates) == 3
        for agg in aggregates:
            assert agg.rank == 2

    def test_full_temporal_workflow(self, increasing_harm_tensor):
        """Test complete temporal analysis workflow."""
        # 1. Check for irreversibility
        detect_irreversibility(
            increasing_harm_tensor,
            harm_threshold=0.7,
            min_sustained_steps=2,
        )

        # 2. Compute trends
        trends = compute_temporal_trend(increasing_harm_tensor)

        # 3. Apply discounting
        discounted = apply_temporal_discount(increasing_harm_tensor, 0.1)

        # 4. Aggregate to rank-2
        final = temporal_aggregate(discounted, method="mean")

        # Verify increasing harm detected
        assert trends["slopes"][0, 0] > 0  # Physical harm increasing for alice
        assert final.rank == 2


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for temporal operations."""

    def test_single_timestep(self):
        """Test operations with single timestep."""
        data = np.random.rand(9, 2, 1)
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        # Should handle gracefully
        validate_temporal_tensor(tensor)
        result = temporal_aggregate(tensor, method="mean")
        assert result.rank == 2

    def test_single_party_temporal(self):
        """Test operations with single party."""
        data = np.random.rand(9, 1, 5)
        tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n", "tau"),
            axis_labels={"n": ["solo"]},
        )

        result = detect_irreversibility(tensor)
        assert isinstance(result, IrreversibilityResult)

    def test_all_zeros_tensor(self):
        """Test operations with all-zeros tensor."""
        data = np.zeros((9, 2, 5))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        # Discounting should work
        discounted = apply_temporal_discount(tensor, 0.1)
        np.testing.assert_array_equal(discounted.to_dense(), data)

        # Trends should be flat
        trends = compute_temporal_trend(tensor)
        np.testing.assert_array_almost_equal(trends["slopes"], np.zeros((9, 2)))

    def test_all_ones_tensor(self):
        """Test operations with all-ones tensor."""
        data = np.ones((9, 2, 5))
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        # Aggregation should give ones
        result = temporal_aggregate(tensor, method="mean")
        np.testing.assert_array_almost_equal(result.to_dense(), np.ones((9, 2)))

    def test_large_timesteps(self):
        """Test operations with many timesteps."""
        data = np.random.rand(9, 2, 100)
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n", "tau"))

        # Should complete without issues
        result = temporal_aggregate(tensor, discount_rate=0.01, method="mean")
        assert result.rank == 2

        windows = sliding_window(tensor, window_size=10, stride=10)
        assert len(windows) == 10

    def test_dtw_with_very_different_lengths(self):
        """Test DTW with very different temporal lengths."""
        data1 = np.random.rand(9, 2, 3)
        data2 = np.random.rand(9, 2, 20)

        t1 = MoralTensor.from_dense(data1, axis_names=("k", "n", "tau"))
        t2 = MoralTensor.from_dense(data2, axis_names=("k", "n", "tau"))

        dist = dtw_distance(t1, t2)
        assert dist >= 0  # Should not fail
