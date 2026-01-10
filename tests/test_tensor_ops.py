# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for DEME V3 tensor operations.

Covers:
- Convenience slicers (slice_party, slice_time, slice_dimension)
- Arithmetic operations (__sub__, __truediv__)
- contract() weighted axis reduction
- to_vector() collapse strategies
- promote_rank() dimension expansion
- tensor_ops helper functions
- Wasserstein distance metric
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from erisml.ethics.moral_tensor import (
    MoralTensor,
    DIMENSION_INDEX,
    MORAL_DIMENSION_NAMES,
)
from erisml.ethics.tensor_ops import (
    broadcast_tensors,
    stack_tensors,
    concat_tensors,
    normalize_tensor,
    clip_tensor,
    wasserstein_distance,
    cosine_similarity,
    weighted_aggregate,
)


# =============================================================================
# Test Convenience Slicers
# =============================================================================


class TestSliceParty:
    """Tests for slice_party() method."""

    def test_slice_party_by_index(self, rank2_tensor: MoralTensor) -> None:
        """Slice party by integer index."""
        result = rank2_tensor.slice_party(0)
        assert result.rank == 1
        assert result.shape == (9,)

    def test_slice_party_by_name(self, rank2_tensor: MoralTensor) -> None:
        """Slice party by string label."""
        result = rank2_tensor.slice_party("alice")
        assert result.rank == 1
        assert result.shape == (9,)

    def test_slice_party_unknown_label(self, rank2_tensor: MoralTensor) -> None:
        """Error on unknown party label."""
        with pytest.raises(ValueError, match="not found"):
            rank2_tensor.slice_party("unknown")

    def test_slice_party_no_n_axis(self, rank1_tensor: MoralTensor) -> None:
        """Error on tensor without party axis."""
        with pytest.raises(ValueError, match="does not have party axis"):
            rank1_tensor.slice_party(0)


class TestSliceTime:
    """Tests for slice_time() method."""

    def test_slice_time_by_index(self, rank3_tensor: MoralTensor) -> None:
        """Slice time by integer index."""
        result = rank3_tensor.slice_time(0)
        assert result.rank == 2
        assert result.shape[0] == 9

    def test_slice_time_by_slice(self, rank3_tensor: MoralTensor) -> None:
        """Slice time with slice object."""
        result = rank3_tensor.slice_time(slice(0, 2))
        assert result.rank == 3

    def test_slice_time_by_label(self, rank3_tensor: MoralTensor) -> None:
        """Slice time by string label."""
        result = rank3_tensor.slice_time("t0")
        assert result.rank == 2

    def test_slice_time_no_tau_axis(self, rank2_tensor: MoralTensor) -> None:
        """Error on tensor without time axis."""
        with pytest.raises(ValueError, match="does not have time axis"):
            rank2_tensor.slice_time(0)


class TestSliceDimension:
    """Tests for slice_dimension() method."""

    def test_slice_dimension_by_name(self, rank2_tensor: MoralTensor) -> None:
        """Extract ethical dimension values by name."""
        result = rank2_tensor.slice_dimension("physical_harm")
        # Returns numpy array, shape is (n,) for rank-2 tensor
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)  # 3 parties

    def test_slice_all_dimensions(self, rank2_tensor: MoralTensor) -> None:
        """Can extract each dimension by name."""
        for name in MORAL_DIMENSION_NAMES:
            result = rank2_tensor.slice_dimension(name)
            assert isinstance(result, np.ndarray)

    def test_slice_dimension_unknown(self, rank2_tensor: MoralTensor) -> None:
        """Error on unknown dimension name."""
        with pytest.raises(ValueError, match="not found"):
            rank2_tensor.slice_dimension("unknown_dim")


# =============================================================================
# Test Arithmetic Operations
# =============================================================================


class TestSubtraction:
    """Tests for __sub__ and __rsub__."""

    def test_subtraction_tensor(self, rank2_tensor: MoralTensor) -> None:
        """Subtract two tensors element-wise."""
        result = rank2_tensor - rank2_tensor
        assert result.shape == rank2_tensor.shape
        # Self - self should be all zeros (clamped)
        assert np.allclose(result.to_dense(), 0.0)

    def test_subtraction_scalar(self, rank2_tensor: MoralTensor) -> None:
        """Subtract scalar from tensor."""
        result = rank2_tensor - 0.1
        assert result.shape == rank2_tensor.shape
        data = result.to_dense()
        assert np.all(data >= 0.0)
        assert np.all(data <= 1.0)

    def test_subtraction_clamping(self, rank1_tensor: MoralTensor) -> None:
        """Subtraction clamps to [0, 1]."""
        result = rank1_tensor - 2.0  # Large subtraction
        data = result.to_dense()
        assert np.all(data >= 0.0)

    def test_rsub(self, rank1_tensor: MoralTensor) -> None:
        """Right subtraction (scalar - tensor)."""
        result = 1.0 - rank1_tensor
        assert result.shape == rank1_tensor.shape
        data = result.to_dense()
        assert np.all(data >= 0.0)
        assert np.all(data <= 1.0)

    def test_subtraction_preserves_vetoes(self, vetoed_tensor: MoralTensor) -> None:
        """Subtraction preserves veto flags."""
        other = MoralTensor.ones(vetoed_tensor.shape)
        result = vetoed_tensor - other
        assert len(result.veto_flags) > 0


class TestDivision:
    """Tests for __truediv__ and __rtruediv__."""

    def test_division_tensor(self, rank2_tensor: MoralTensor) -> None:
        """Divide two tensors element-wise."""
        ones = MoralTensor.ones(rank2_tensor.shape)
        result = rank2_tensor / ones
        assert result.shape == rank2_tensor.shape

    def test_division_scalar(self, rank2_tensor: MoralTensor) -> None:
        """Divide tensor by scalar."""
        result = rank2_tensor / 2.0
        assert result.shape == rank2_tensor.shape
        data = result.to_dense()
        assert np.all(data >= 0.0)
        assert np.all(data <= 1.0)

    def test_division_by_zero_scalar(self, rank1_tensor: MoralTensor) -> None:
        """Division by zero yields 1.0 (maximum)."""
        result = rank1_tensor / 0.0
        data = result.to_dense()
        assert np.all(data == 1.0)

    def test_division_by_zero_tensor(self) -> None:
        """Division by tensor with zeros yields 1.0 at zero locations."""
        numerator = MoralTensor.from_dense(np.full((9, 3), 0.5))
        zeros = MoralTensor.zeros((9, 3))  # harm=1, others=0
        result = numerator / zeros
        data = result.to_dense()
        # Where zeros had 0.0, result should be 1.0
        assert data[1, 0] == 1.0  # rights_respect was 0

    def test_rtruediv(self, rank1_tensor: MoralTensor) -> None:
        """Right division (scalar / tensor)."""
        result = 1.0 / rank1_tensor
        assert result.shape == rank1_tensor.shape
        data = result.to_dense()
        assert np.all(data >= 0.0)
        assert np.all(data <= 1.0)

    def test_division_clamping(self, rank1_tensor: MoralTensor) -> None:
        """Division clamps to [0, 1]."""
        result = rank1_tensor / 0.01  # Large result
        data = result.to_dense()
        assert np.all(data <= 1.0)


# =============================================================================
# Test Contract
# =============================================================================


class TestContract:
    """Tests for contract() method."""

    def test_contract_uniform_weights(self, rank2_tensor: MoralTensor) -> None:
        """Contract with uniform weights (default)."""
        result = rank2_tensor.contract("n")
        assert result.rank == 1
        assert result.shape == (9,)

    def test_contract_custom_weights(self, rank2_tensor: MoralTensor) -> None:
        """Contract with custom weights."""
        weights = np.array([0.5, 0.3, 0.2])
        result = rank2_tensor.contract("n", weights=weights)
        assert result.rank == 1
        assert result.shape == (9,)

    def test_contract_preserves_vetoes(self, vetoed_tensor: MoralTensor) -> None:
        """Contract preserves veto flags."""
        result = vetoed_tensor.contract("n")
        assert len(result.veto_flags) > 0

    def test_contract_normalizes_weights(self, rank2_tensor: MoralTensor) -> None:
        """Weights are normalized by default."""
        weights = np.array([1.0, 1.0, 1.0])  # Sum to 3
        result = rank2_tensor.contract("n", weights=weights)
        assert result.rank == 1

    def test_contract_no_normalize(self, rank2_tensor: MoralTensor) -> None:
        """Can disable weight normalization."""
        weights = np.array([1.0, 0.0, 0.0])
        result = rank2_tensor.contract("n", weights=weights, normalize=False)
        assert result.rank == 1

    def test_contract_wrong_weights_length(self, rank2_tensor: MoralTensor) -> None:
        """Error on weights with wrong length."""
        weights = np.array([0.5, 0.5])  # Wrong length
        with pytest.raises(ValueError, match="must match axis size"):
            rank2_tensor.contract("n", weights=weights)

    def test_contract_unknown_axis(self, rank2_tensor: MoralTensor) -> None:
        """Error on unknown axis name."""
        with pytest.raises(ValueError, match="not found"):
            rank2_tensor.contract("unknown")

    def test_contract_rank3(self, rank3_tensor: MoralTensor) -> None:
        """Contract rank-3 tensor along time axis."""
        result = rank3_tensor.contract("tau")
        assert result.rank == 2


# =============================================================================
# Test to_vector
# =============================================================================


class TestToVector:
    """Tests for to_vector() method."""

    def test_to_vector_mean(self, rank2_tensor: MoralTensor) -> None:
        """to_vector with mean strategy."""
        result = rank2_tensor.to_vector(strategy="mean")
        assert hasattr(result, "physical_harm")
        assert hasattr(result, "rights_respect")

    def test_to_vector_max(self, rank2_tensor: MoralTensor) -> None:
        """to_vector with max strategy."""
        result = rank2_tensor.to_vector(strategy="max")
        assert result is not None

    def test_to_vector_min(self, rank2_tensor: MoralTensor) -> None:
        """to_vector with min strategy."""
        result = rank2_tensor.to_vector(strategy="min")
        assert result is not None

    def test_to_vector_weighted(self, rank2_tensor: MoralTensor) -> None:
        """to_vector with weighted strategy."""
        weights = {"n": np.array([0.5, 0.3, 0.2])}
        result = rank2_tensor.to_vector(strategy="weighted", weights=weights)
        assert result is not None

    def test_to_vector_party(self, rank2_tensor: MoralTensor) -> None:
        """to_vector with party strategy."""
        result = rank2_tensor.to_vector(strategy="party", party_idx=0)
        assert result is not None

    def test_to_vector_preserves_vetoes(self, vetoed_tensor: MoralTensor) -> None:
        """to_vector preserves veto flags."""
        result = vetoed_tensor.to_vector(strategy="mean")
        assert len(result.veto_flags) > 0

    def test_to_vector_rank1(self, rank1_tensor: MoralTensor) -> None:
        """to_vector on rank-1 returns MoralVector directly."""
        result = rank1_tensor.to_vector()
        assert hasattr(result, "physical_harm")

    def test_to_vector_weighted_requires_weights(
        self, rank2_tensor: MoralTensor
    ) -> None:
        """Error if weighted strategy without weights."""
        with pytest.raises(ValueError, match="requires weights"):
            rank2_tensor.to_vector(strategy="weighted")

    def test_to_vector_party_requires_idx(self, rank2_tensor: MoralTensor) -> None:
        """Error if party strategy without party_idx."""
        with pytest.raises(ValueError, match="requires party_idx"):
            rank2_tensor.to_vector(strategy="party")

    def test_to_vector_unknown_strategy(self, rank2_tensor: MoralTensor) -> None:
        """Error on unknown strategy."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            rank2_tensor.to_vector(strategy="unknown")


# =============================================================================
# Test promote_rank
# =============================================================================


class TestPromoteRank:
    """Tests for promote_rank() method."""

    def test_promote_rank1_to_rank2(self, rank1_tensor: MoralTensor) -> None:
        """Promote rank-1 to rank-2."""
        result = rank1_tensor.promote_rank(2, axis_sizes={"n": 3})
        assert result.rank == 2
        assert result.shape == (9, 3)

    def test_promote_rank2_to_rank3(self, rank2_tensor: MoralTensor) -> None:
        """Promote rank-2 to rank-3."""
        result = rank2_tensor.promote_rank(3, axis_sizes={"tau": 4})
        assert result.rank == 3
        assert result.shape[2] == 4

    def test_promote_with_broadcast(self, rank1_tensor: MoralTensor) -> None:
        """Values are broadcast to new dimensions."""
        result = rank1_tensor.promote_rank(2, axis_sizes={"n": 3})
        data = result.to_dense()
        # All parties should have same values
        assert np.allclose(data[:, 0], data[:, 1])
        assert np.allclose(data[:, 1], data[:, 2])

    def test_promote_preserves_vetoes(self, rank1_tensor: MoralTensor) -> None:
        """promote_rank preserves veto flags."""
        # Add a veto
        tensor_with_veto = MoralTensor.from_dense(
            rank1_tensor.to_dense(),
            veto_flags=["TEST_VETO"],
        )
        result = tensor_with_veto.promote_rank(2, axis_sizes={"n": 3})
        assert "TEST_VETO" in result.veto_flags

    def test_promote_rank_too_low(self, rank2_tensor: MoralTensor) -> None:
        """Error if target rank <= current rank."""
        with pytest.raises(ValueError, match="must be > current rank"):
            rank2_tensor.promote_rank(2)

    def test_promote_rank_too_high(self, rank1_tensor: MoralTensor) -> None:
        """Error if target rank > 6."""
        with pytest.raises(ValueError, match="cannot exceed 6"):
            rank1_tensor.promote_rank(7)

    def test_promote_missing_axis_size(self, rank1_tensor: MoralTensor) -> None:
        """Error if missing size for new axis."""
        with pytest.raises(ValueError, match="Missing size"):
            rank1_tensor.promote_rank(2)


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestBroadcastTensors:
    """Tests for broadcast_tensors()."""

    def test_broadcast_same_shape(self, rank2_tensor: MoralTensor) -> None:
        """Broadcasting same-shape tensors returns unchanged."""
        t1, t2 = broadcast_tensors(rank2_tensor, rank2_tensor)
        assert t1.shape == t2.shape

    def test_broadcast_different_shapes(self) -> None:
        """Broadcasting expands dimensions."""
        t1 = MoralTensor.from_dense(np.ones((9, 1)))
        t2 = MoralTensor.from_dense(np.ones((9, 3)))
        b1, b2 = broadcast_tensors(t1, t2)
        assert b1.shape == (9, 3)
        assert b2.shape == (9, 3)

    def test_broadcast_single_tensor(self, rank1_tensor: MoralTensor) -> None:
        """Broadcasting single tensor returns it unchanged."""
        (result,) = broadcast_tensors(rank1_tensor)
        assert result.shape == rank1_tensor.shape

    def test_broadcast_empty(self) -> None:
        """Broadcasting empty list returns empty tuple."""
        result = broadcast_tensors()
        assert result == ()

    def test_broadcast_incompatible(self) -> None:
        """Error on incompatible shapes."""
        t1 = MoralTensor.from_dense(np.ones((9, 2)))
        t2 = MoralTensor.from_dense(np.ones((9, 3)))
        with pytest.raises(ValueError, match="Cannot broadcast"):
            broadcast_tensors(t1, t2)


class TestStackTensors:
    """Tests for stack_tensors()."""

    def test_stack_tensors(self, rank1_tensor: MoralTensor) -> None:
        """Stack multiple rank-1 tensors."""
        t1 = rank1_tensor
        t2 = MoralTensor.from_dense(np.ones(9) * 0.5)
        result = stack_tensors([t1, t2], axis="n", labels=["alice", "bob"])
        assert result.rank == 2
        assert result.shape == (9, 2)
        assert result.axis_labels.get("n") == ["alice", "bob"]

    def test_stack_empty(self) -> None:
        """Error on empty list."""
        with pytest.raises(ValueError, match="empty list"):
            stack_tensors([], axis="n")

    def test_stack_different_shapes(self) -> None:
        """Error on different shapes."""
        t1 = MoralTensor.from_dense(np.ones(9))
        t2 = MoralTensor.from_dense(np.ones((9, 2)))
        with pytest.raises(ValueError, match="same shape"):
            stack_tensors([t1, t2], axis="n")


class TestConcatTensors:
    """Tests for concat_tensors()."""

    def test_concat_tensors(self) -> None:
        """Concatenate tensors along existing axis."""
        t1 = MoralTensor.from_dense(np.ones((9, 2)))
        t2 = MoralTensor.from_dense(np.ones((9, 3)))
        result = concat_tensors([t1, t2], axis="n")
        assert result.shape == (9, 5)

    def test_concat_single(self, rank2_tensor: MoralTensor) -> None:
        """Concatenating single tensor returns it."""
        result = concat_tensors([rank2_tensor], axis="n")
        assert result.shape == rank2_tensor.shape

    def test_concat_empty(self) -> None:
        """Error on empty list."""
        with pytest.raises(ValueError, match="empty list"):
            concat_tensors([], axis="n")


class TestNormalizeTensor:
    """Tests for normalize_tensor()."""

    def test_normalize_sum(self, rank2_tensor: MoralTensor) -> None:
        """Normalize so values sum to 1."""
        result = normalize_tensor(rank2_tensor, axis="n", method="sum")
        data = result.to_dense()
        # Each row should sum to 1 (approximately)
        sums = np.sum(data, axis=1)
        assert np.allclose(sums, 1.0)

    def test_normalize_max(self, rank2_tensor: MoralTensor) -> None:
        """Normalize by max value."""
        result = normalize_tensor(rank2_tensor, axis="n", method="max")
        data = result.to_dense()
        # Max along axis should be 1.0
        maxes = np.max(data, axis=1)
        assert np.all(maxes <= 1.0)

    def test_normalize_minmax(self, rank2_tensor: MoralTensor) -> None:
        """Normalize to [0, 1] range."""
        result = normalize_tensor(rank2_tensor, axis="n", method="minmax")
        data = result.to_dense()
        assert np.all(data >= 0.0)
        assert np.all(data <= 1.0)


class TestClipTensor:
    """Tests for clip_tensor()."""

    def test_clip_default(self, rank2_tensor: MoralTensor) -> None:
        """Clip to default [0, 1]."""
        result = clip_tensor(rank2_tensor)
        data = result.to_dense()
        assert np.all(data >= 0.0)
        assert np.all(data <= 1.0)

    def test_clip_custom_range(self, rank2_tensor: MoralTensor) -> None:
        """Clip to custom range."""
        result = clip_tensor(rank2_tensor, min_val=0.2, max_val=0.8)
        data = result.to_dense()
        assert np.all(data >= 0.2)
        assert np.all(data <= 0.8)


# =============================================================================
# Test Wasserstein Distance
# =============================================================================


class TestWassersteinDistance:
    """Tests for wasserstein_distance()."""

    def test_wasserstein_identical(self, rank1_tensor: MoralTensor) -> None:
        """Wasserstein distance to self is 0."""
        dist = wasserstein_distance(rank1_tensor, rank1_tensor)
        assert dist == pytest.approx(0.0)

    def test_wasserstein_different(self) -> None:
        """Wasserstein distance between different tensors."""
        t1 = MoralTensor.from_dense(np.full(9, 0.2))
        t2 = MoralTensor.from_dense(np.full(9, 0.8))
        dist = wasserstein_distance(t1, t2)
        assert dist > 0

    def test_wasserstein_p1_vs_p2(self) -> None:
        """W1 and W2 can give different values."""
        t1 = MoralTensor.from_dense(
            np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        )
        t2 = MoralTensor.from_dense(
            np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        )
        w1 = wasserstein_distance(t1, t2, p=1)
        w2 = wasserstein_distance(t1, t2, p=2)
        # Both should be positive
        assert w1 > 0
        assert w2 > 0

    def test_wasserstein_shape_mismatch(self) -> None:
        """Error on shape mismatch."""
        t1 = MoralTensor.from_dense(np.ones(9))
        t2 = MoralTensor.from_dense(np.ones((9, 2)))
        with pytest.raises(ValueError, match="Shape mismatch"):
            wasserstein_distance(t1, t2)

    def test_wasserstein_via_distance_method(self, rank1_tensor: MoralTensor) -> None:
        """Can call wasserstein via MoralTensor.distance()."""
        other = MoralTensor.from_dense(np.ones(9) * 0.5)
        dist = rank1_tensor.distance(other, metric="wasserstein")
        assert dist >= 0

    def test_euclidean_alias(self, rank1_tensor: MoralTensor) -> None:
        """euclidean metric is alias for frobenius."""
        other = MoralTensor.from_dense(np.ones(9) * 0.5)
        d1 = rank1_tensor.distance(other, metric="frobenius")
        d2 = rank1_tensor.distance(other, metric="euclidean")
        assert d1 == pytest.approx(d2)


class TestCosineSimilarity:
    """Tests for cosine_similarity()."""

    def test_cosine_identical(self, rank1_tensor: MoralTensor) -> None:
        """Cosine similarity to self is 1."""
        sim = cosine_similarity(rank1_tensor, rank1_tensor)
        assert sim == pytest.approx(1.0)

    def test_cosine_different(self) -> None:
        """Cosine similarity between different tensors."""
        t1 = MoralTensor.from_dense(np.full(9, 0.5))
        t2 = MoralTensor.from_dense(np.full(9, 0.5))
        sim = cosine_similarity(t1, t2)
        assert sim == pytest.approx(1.0)  # Same direction


class TestWeightedAggregate:
    """Tests for weighted_aggregate()."""

    def test_weighted_aggregate_uniform(self, rank2_tensor: MoralTensor) -> None:
        """Aggregate with uniform weights."""
        t1 = MoralTensor.from_dense(np.full((9, 3), 0.2))
        t2 = MoralTensor.from_dense(np.full((9, 3), 0.8))
        result = weighted_aggregate([t1, t2])
        data = result.to_dense()
        assert np.allclose(data, 0.5)  # Average

    def test_weighted_aggregate_custom(self) -> None:
        """Aggregate with custom weights."""
        t1 = MoralTensor.from_dense(np.full((9, 3), 0.0))
        t2 = MoralTensor.from_dense(np.full((9, 3), 1.0))
        weights = np.array([0.25, 0.75])
        result = weighted_aggregate([t1, t2], weights=weights)
        data = result.to_dense()
        assert np.allclose(data, 0.75)

    def test_weighted_aggregate_single(self, rank2_tensor: MoralTensor) -> None:
        """Aggregating single tensor returns it."""
        result = weighted_aggregate([rank2_tensor])
        assert result.shape == rank2_tensor.shape

    def test_weighted_aggregate_empty(self) -> None:
        """Error on empty list."""
        with pytest.raises(ValueError, match="empty list"):
            weighted_aggregate([])
