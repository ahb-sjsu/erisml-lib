# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Unit tests for MoralTensor (DEME V3).

Tests cover:
- Creation from dense arrays
- Creation from sparse COO format
- Conversion to/from MoralVector (backward compat)
- Tensor operations (slice, reduce, arithmetic)
- Serialization (to_dict, from_dict)
- Veto handling
- Validation
"""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ethics.moral_tensor import (
    MoralTensor,
    SparseCOO,
    MORAL_DIMENSION_NAMES,
    DIMENSION_INDEX,
    DEFAULT_AXIS_NAMES,
)
from erisml.ethics.moral_vector import MoralVector


class TestSparseCOO:
    """Tests for SparseCOO sparse tensor storage."""

    def test_create_sparse_coo(self) -> None:
        """Test basic SparseCOO creation."""
        coords = np.array([[0, 0], [1, 1], [2, 2]], dtype=np.int32)
        values = np.array([0.5, 0.6, 0.7], dtype=np.float64)
        shape = (3, 3)

        sparse = SparseCOO(coords=coords, values=values, shape=shape)

        assert sparse.nnz == 3
        assert sparse.rank == 2
        assert sparse.shape == (3, 3)

    def test_sparse_to_dense(self) -> None:
        """Test conversion from sparse to dense."""
        coords = np.array([[0, 0], [1, 1]], dtype=np.int32)
        values = np.array([0.5, 0.8], dtype=np.float64)
        shape = (2, 2)

        sparse = SparseCOO(coords=coords, values=values, shape=shape)
        dense = sparse.to_dense()

        expected = np.array([[0.5, 0.0], [0.0, 0.8]])
        np.testing.assert_array_almost_equal(dense, expected)

    def test_dense_to_sparse(self) -> None:
        """Test conversion from dense to sparse."""
        dense = np.array([[0.5, 0.0], [0.0, 0.8]])

        sparse = SparseCOO.from_dense(dense)

        assert sparse.nnz == 2
        reconstructed = sparse.to_dense()
        np.testing.assert_array_almost_equal(reconstructed, dense)

    def test_sparse_with_fill_value(self) -> None:
        """Test sparse conversion with non-zero fill value."""
        dense = np.array([[0.5, 0.5], [0.5, 0.8]])

        sparse = SparseCOO.from_dense(dense, fill_value=0.5)

        assert sparse.nnz == 1  # Only 0.8 is different from fill
        assert sparse.fill_value == 0.5
        reconstructed = sparse.to_dense()
        np.testing.assert_array_almost_equal(reconstructed, dense)


class TestMoralTensorCreation:
    """Tests for MoralTensor creation methods."""

    def test_from_dense_rank1(self) -> None:
        """Test creating rank-1 tensor from dense array."""
        data = np.array([0.1, 0.9, 0.8, 0.85, 0.9, 0.8, 0.85, 0.75, 0.7])

        tensor = MoralTensor.from_dense(data)

        assert tensor.rank == 1
        assert tensor.shape == (9,)
        assert tensor.axis_names == ("k",)
        np.testing.assert_array_almost_equal(tensor.to_dense(), data)

    def test_from_dense_rank2(self) -> None:
        """Test creating rank-2 tensor from dense array."""
        data = np.random.rand(9, 5)
        data = np.clip(data, 0, 1)

        tensor = MoralTensor.from_dense(data)

        assert tensor.rank == 2
        assert tensor.shape == (9, 5)
        assert tensor.axis_names == ("k", "n")

    def test_from_dense_rank3(self) -> None:
        """Test creating rank-3 tensor."""
        data = np.random.rand(9, 3, 4)
        data = np.clip(data, 0, 1)

        tensor = MoralTensor.from_dense(data)

        assert tensor.rank == 3
        assert tensor.shape == (9, 3, 4)
        assert tensor.axis_names == ("k", "n", "tau")

    def test_from_dense_with_labels(self) -> None:
        """Test creating tensor with axis labels."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)

        tensor = MoralTensor.from_dense(
            data,
            axis_labels={
                "k": list(MORAL_DIMENSION_NAMES),
                "n": ["alice", "bob", "carol"],
            },
        )

        assert tensor.axis_labels["n"] == ["alice", "bob", "carol"]
        assert tensor.axis_labels["k"] == list(MORAL_DIMENSION_NAMES)

    def test_from_sparse(self) -> None:
        """Test creating tensor from sparse format."""
        coords = np.array([[0, 0], [1, 1]], dtype=np.int32)
        values = np.array([0.5, 0.8], dtype=np.float64)
        shape = (9, 3)

        tensor = MoralTensor.from_sparse(coords, values, shape)

        assert tensor.is_sparse
        assert tensor.rank == 2
        assert tensor.shape == (9, 3)

    def test_zeros(self) -> None:
        """Test creating worst-case tensor."""
        tensor = MoralTensor.zeros((9, 4))

        assert tensor.shape == (9, 4)
        data = tensor.to_dense()
        # physical_harm should be 1.0
        np.testing.assert_array_almost_equal(data[0, :], 1.0)
        # All other dimensions should be 0.0
        for k in range(1, 9):
            np.testing.assert_array_almost_equal(data[k, :], 0.0)

    def test_ones(self) -> None:
        """Test creating ideal tensor."""
        tensor = MoralTensor.ones((9, 4))

        assert tensor.shape == (9, 4)
        data = tensor.to_dense()
        # physical_harm should be 0.0
        np.testing.assert_array_almost_equal(data[0, :], 0.0)
        # All other dimensions should be 1.0
        for k in range(1, 9):
            np.testing.assert_array_almost_equal(data[k, :], 1.0)


class TestMoralTensorValidation:
    """Tests for MoralTensor validation."""

    def test_rejects_wrong_first_dimension(self) -> None:
        """Test that first dimension must be 9."""
        data = np.random.rand(8, 3)  # Wrong: 8 instead of 9

        with pytest.raises(ValueError, match="First dimension must be 9"):
            MoralTensor.from_dense(data)

    def test_rejects_out_of_bounds_high(self) -> None:
        """Test that values > 1.0 are rejected."""
        data = np.ones((9,))
        data[2] = 1.5  # Out of bounds

        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            MoralTensor.from_dense(data)

    def test_rejects_out_of_bounds_low(self) -> None:
        """Test that values < 0.0 are rejected."""
        data = np.zeros((9,))
        data[3] = -0.1  # Out of bounds

        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            MoralTensor.from_dense(data)

    def test_rejects_invalid_rank(self) -> None:
        """Test that rank > 6 is rejected."""
        data = np.random.rand(9, 2, 2, 2, 2, 2, 2)  # Rank 7
        data = np.clip(data, 0, 1)

        with pytest.raises(ValueError, match="Rank must be 1-6"):
            MoralTensor.from_dense(data)

    def test_validates_veto_locations(self) -> None:
        """Test veto location validation."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)

        with pytest.raises(ValueError, match="out of bounds"):
            MoralTensor.from_dense(
                data,
                veto_locations=[(5,)],  # Out of bounds for dim 1 (size 3)
            )

    def test_validates_axis_names_length(self) -> None:
        """Test axis names must match rank."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)

        with pytest.raises(ValueError, match="axis_names length"):
            MoralTensor.from_dense(data, axis_names=("k",))  # Missing second axis


class TestMoralVectorCompatibility:
    """Tests for MoralVector <-> MoralTensor conversion."""

    def test_from_moral_vector(self, baseline_moral_vector: MoralVector) -> None:
        """Test creating tensor from MoralVector."""
        tensor = MoralTensor.from_moral_vector(baseline_moral_vector)

        assert tensor.rank == 1
        assert tensor.shape == (9,)
        data = tensor.to_dense()
        assert data[0] == baseline_moral_vector.physical_harm
        assert data[1] == baseline_moral_vector.rights_respect
        assert data[8] == baseline_moral_vector.epistemic_quality

    def test_to_moral_vector(self) -> None:
        """Test converting tensor back to MoralVector."""
        data = np.array([0.2, 0.9, 0.8, 0.85, 0.9, 0.8, 0.85, 0.75, 0.7])
        tensor = MoralTensor.from_dense(data)

        vec = tensor.to_moral_vector()

        assert vec.physical_harm == pytest.approx(0.2)
        assert vec.rights_respect == pytest.approx(0.9)
        assert vec.epistemic_quality == pytest.approx(0.7)

    def test_roundtrip_moral_vector(self, baseline_moral_vector: MoralVector) -> None:
        """Test MoralVector -> MoralTensor -> MoralVector roundtrip."""
        tensor = MoralTensor.from_moral_vector(baseline_moral_vector)
        vec_back = tensor.to_moral_vector()

        assert vec_back.physical_harm == pytest.approx(
            baseline_moral_vector.physical_harm
        )
        assert vec_back.rights_respect == pytest.approx(
            baseline_moral_vector.rights_respect
        )
        assert vec_back.fairness_equity == pytest.approx(
            baseline_moral_vector.fairness_equity
        )
        assert vec_back.autonomy_respect == pytest.approx(
            baseline_moral_vector.autonomy_respect
        )
        assert vec_back.privacy_protection == pytest.approx(
            baseline_moral_vector.privacy_protection
        )
        assert vec_back.societal_environmental == pytest.approx(
            baseline_moral_vector.societal_environmental
        )
        assert vec_back.virtue_care == pytest.approx(baseline_moral_vector.virtue_care)
        assert vec_back.legitimacy_trust == pytest.approx(
            baseline_moral_vector.legitimacy_trust
        )
        assert vec_back.epistemic_quality == pytest.approx(
            baseline_moral_vector.epistemic_quality
        )

    def test_to_moral_vector_rejects_rank2(self) -> None:
        """Test that to_moral_vector rejects rank > 1."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)
        tensor = MoralTensor.from_dense(data)

        with pytest.raises(ValueError, match="Can only convert rank-1"):
            tensor.to_moral_vector()

    def test_from_moral_vectors(self) -> None:
        """Test stacking multiple MoralVectors."""
        vec1 = MoralVector(physical_harm=0.1, rights_respect=0.9)
        vec2 = MoralVector(physical_harm=0.3, rights_respect=0.7)
        vec3 = MoralVector(physical_harm=0.2, rights_respect=0.8)

        tensor = MoralTensor.from_moral_vectors(
            {
                "alice": vec1,
                "bob": vec2,
                "carol": vec3,
            }
        )

        assert tensor.rank == 2
        assert tensor.shape == (9, 3)
        assert tensor.axis_labels["n"] == ["alice", "bob", "carol"]

        data = tensor.to_dense()
        assert data[0, 0] == pytest.approx(0.1)  # alice's harm
        assert data[0, 1] == pytest.approx(0.3)  # bob's harm
        assert data[1, 2] == pytest.approx(0.8)  # carol's rights_respect

    def test_from_moral_vectors_preserves_vetoes(self) -> None:
        """Test that vetoes are preserved when stacking vectors."""
        vec1 = MoralVector(physical_harm=0.1, veto_flags=["RIGHTS_VIOLATION"])
        vec2 = MoralVector(physical_harm=0.2, veto_flags=["DISCRIMINATION"])

        tensor = MoralTensor.from_moral_vectors({"a": vec1, "b": vec2})

        assert "RIGHTS_VIOLATION" in tensor.veto_flags
        assert "DISCRIMINATION" in tensor.veto_flags


class TestMoralTensorOperations:
    """Tests for tensor operations."""

    def test_getitem_scalar(self) -> None:
        """Test scalar indexing."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)
        tensor = MoralTensor.from_dense(data)

        value = tensor[0, 0]

        assert isinstance(value, float)
        assert value == pytest.approx(data[0, 0])

    def test_getitem_slice(self) -> None:
        """Test slice indexing."""
        data = np.random.rand(9, 4)
        data = np.clip(data, 0, 1)
        tensor = MoralTensor.from_dense(data)

        sliced = tensor[:, 1:3]

        assert isinstance(sliced, MoralTensor)
        assert sliced.shape == (9, 2)

    def test_slice_by_axis_name(self) -> None:
        """Test slicing by named axis."""
        data = np.random.rand(9, 4)
        data = np.clip(data, 0, 1)
        tensor = MoralTensor.from_dense(data)

        sliced = tensor.slice_axis("n", 2)

        assert sliced.rank == 1
        assert sliced.shape == (9,)

    def test_reduce_mean(self) -> None:
        """Test mean reduction along axis."""
        data = np.ones((9, 4)) * 0.5
        data[0, :] = 0.2  # physical_harm
        tensor = MoralTensor.from_dense(data)

        reduced = tensor.reduce("n", method="mean")

        assert reduced.rank == 1
        assert reduced.shape == (9,)
        result = reduced.to_dense()
        assert result[0] == pytest.approx(0.2)
        assert result[1] == pytest.approx(0.5)

    def test_reduce_min(self) -> None:
        """Test min reduction."""
        data = np.array([[0.2, 0.4, 0.3]] + [[0.5, 0.6, 0.7]] * 8)
        tensor = MoralTensor.from_dense(data)

        reduced = tensor.reduce("n", method="min")

        result = reduced.to_dense()
        assert result[0] == pytest.approx(0.2)

    def test_reduce_max(self) -> None:
        """Test max reduction."""
        data = np.array([[0.2, 0.4, 0.3]] + [[0.5, 0.6, 0.7]] * 8)
        tensor = MoralTensor.from_dense(data)

        reduced = tensor.reduce("n", method="max")

        result = reduced.to_dense()
        assert result[0] == pytest.approx(0.4)

    def test_add_tensors(self) -> None:
        """Test tensor addition with clamping."""
        data1 = np.ones((9,)) * 0.3
        data2 = np.ones((9,)) * 0.4
        t1 = MoralTensor.from_dense(data1)
        t2 = MoralTensor.from_dense(data2)

        result = t1 + t2

        assert result.shape == (9,)
        np.testing.assert_array_almost_equal(result.to_dense(), 0.7)

    def test_add_clamping(self) -> None:
        """Test that addition clamps to [0, 1]."""
        data1 = np.ones((9,)) * 0.7
        data2 = np.ones((9,)) * 0.5
        t1 = MoralTensor.from_dense(data1)
        t2 = MoralTensor.from_dense(data2)

        result = t1 + t2

        # Should be clamped to 1.0
        np.testing.assert_array_almost_equal(result.to_dense(), 1.0)

    def test_scalar_multiply(self) -> None:
        """Test scalar multiplication."""
        data = np.ones((9,)) * 0.5
        tensor = MoralTensor.from_dense(data)

        result = tensor * 0.5

        np.testing.assert_array_almost_equal(result.to_dense(), 0.25)

    def test_multiply_clamping(self) -> None:
        """Test that multiplication clamps to [0, 1]."""
        data = np.ones((9,)) * 0.5
        tensor = MoralTensor.from_dense(data)

        result = tensor * 3.0  # Would be 1.5 without clamping

        np.testing.assert_array_almost_equal(result.to_dense(), 1.0)


class TestMoralTensorComparison:
    """Tests for tensor comparison operations."""

    def test_dominates_simple(self) -> None:
        """Test simple Pareto dominance."""
        # Better tensor: less harm, higher everything else
        better = MoralTensor.from_dense(
            np.array([0.1, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
        )
        worse = MoralTensor.from_dense(
            np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        )

        assert better.dominates(worse)
        assert not worse.dominates(better)

    def test_dominates_no_dominance(self) -> None:
        """Test when neither dominates (tradeoff)."""
        t1 = MoralTensor.from_dense(
            np.array([0.1, 0.9, 0.5, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
        )
        t2 = MoralTensor.from_dense(
            np.array([0.1, 0.5, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
        )

        assert not t1.dominates(t2)
        assert not t2.dominates(t1)

    def test_distance_frobenius(self) -> None:
        """Test Frobenius distance."""
        t1 = MoralTensor.from_dense(np.zeros((9,)))
        t2 = MoralTensor.from_dense(np.ones((9,)))

        dist = t1.distance(t2, metric="frobenius")

        assert dist == pytest.approx(3.0)  # sqrt(9) = 3

    def test_distance_max(self) -> None:
        """Test max (Chebyshev) distance."""
        t1 = MoralTensor.from_dense(np.zeros((9,)))
        t2 = MoralTensor.from_dense(np.ones((9,)))

        dist = t1.distance(t2, metric="max")

        assert dist == pytest.approx(1.0)

    def test_distance_mean_abs(self) -> None:
        """Test mean absolute distance."""
        t1 = MoralTensor.from_dense(np.zeros((9,)))
        t2 = MoralTensor.from_dense(np.ones((9,)))

        dist = t1.distance(t2, metric="mean_abs")

        assert dist == pytest.approx(1.0)


class TestMoralTensorVeto:
    """Tests for veto handling."""

    def test_has_veto(self) -> None:
        """Test has_veto detection."""
        tensor = MoralTensor.from_dense(
            np.random.rand(9),
            veto_flags=["RIGHTS_VIOLATION"],
        )

        assert tensor.has_veto()

    def test_no_veto(self) -> None:
        """Test has_veto when no vetoes."""
        tensor = MoralTensor.from_dense(np.random.rand(9))

        assert not tensor.has_veto()

    def test_has_veto_at_global(self) -> None:
        """Test global veto detection."""
        tensor = MoralTensor.from_dense(
            np.random.rand(9, 3),
            veto_flags=["GLOBAL_VETO"],
        )

        # Global veto applies everywhere
        assert tensor.has_veto_at(n=0)
        assert tensor.has_veto_at(n=1)
        assert tensor.has_veto_at(n=2)

    def test_has_veto_at_specific(self) -> None:
        """Test location-specific veto detection."""
        tensor = MoralTensor.from_dense(
            np.random.rand(9, 3),
            veto_flags=["PARTY_VETO"],
            veto_locations=[(1,)],  # Veto at n=1
        )

        assert not tensor.has_veto_at(n=0)
        assert tensor.has_veto_at(n=1)
        assert not tensor.has_veto_at(n=2)


class TestMoralTensorSerialization:
    """Tests for serialization."""

    def test_to_dict_dense(self) -> None:
        """Test serialization of dense tensor."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)
        tensor = MoralTensor.from_dense(
            data,
            veto_flags=["TEST_VETO"],
            reason_codes=["test_reason"],
        )

        d = tensor.to_dict()

        assert d["version"] == "3.0.0"
        assert d["shape"] == [9, 3]
        assert d["rank"] == 2
        assert d["veto_flags"] == ["TEST_VETO"]
        assert d["reason_codes"] == ["test_reason"]
        assert "data" in d

    def test_to_dict_sparse(self) -> None:
        """Test serialization of sparse tensor."""
        coords = np.array([[0, 0], [1, 1]], dtype=np.int32)
        values = np.array([0.5, 0.8], dtype=np.float64)
        tensor = MoralTensor.from_sparse(coords, values, (9, 3))

        d = tensor.to_dict()

        assert d["is_sparse"]
        assert "sparse_coords" in d
        assert "sparse_values" in d

    def test_from_dict_dense(self) -> None:
        """Test deserialization of dense tensor."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)
        original = MoralTensor.from_dense(data, veto_flags=["VETO"])

        d = original.to_dict()
        restored = MoralTensor.from_dict(d)

        assert restored.shape == original.shape
        assert restored.veto_flags == original.veto_flags
        np.testing.assert_array_almost_equal(restored.to_dense(), original.to_dense())

    def test_roundtrip_serialization(self) -> None:
        """Test full serialization roundtrip."""
        original = MoralTensor.from_dense(
            np.random.rand(9, 4, 3),
            veto_flags=["V1", "V2"],
            veto_locations=[(2, 1)],
            reason_codes=["r1", "r2"],
            metadata={"key": "value"},
        )

        d = original.to_dict()
        restored = MoralTensor.from_dict(d)

        assert restored == original


class TestMoralTensorSpecialMethods:
    """Tests for special methods."""

    def test_repr(self) -> None:
        """Test string representation."""
        tensor = MoralTensor.from_dense(
            np.random.rand(9, 3),
            veto_flags=["VETO"],
        )

        repr_str = repr(tensor)

        assert "MoralTensor" in repr_str
        assert "rank=2" in repr_str
        assert "shape=(9, 3)" in repr_str
        assert "vetoes=1" in repr_str

    def test_eq_same(self) -> None:
        """Test equality of identical tensors."""
        data = np.random.rand(9, 3)
        data = np.clip(data, 0, 1)
        t1 = MoralTensor.from_dense(data)
        t2 = MoralTensor.from_dense(data.copy())

        assert t1 == t2

    def test_eq_different_values(self) -> None:
        """Test inequality of different tensors."""
        t1 = MoralTensor.from_dense(np.zeros((9,)))
        t2 = MoralTensor.from_dense(np.ones((9,)))

        assert t1 != t2

    def test_eq_different_vetoes(self) -> None:
        """Test inequality when vetoes differ."""
        data = np.random.rand(9)
        data = np.clip(data, 0, 1)
        t1 = MoralTensor.from_dense(data, veto_flags=["VETO"])
        t2 = MoralTensor.from_dense(data.copy())

        assert t1 != t2

    def test_summary(self) -> None:
        """Test summary string generation."""
        tensor = MoralTensor.from_dense(
            np.random.rand(9, 3),
            veto_flags=["TEST"],
        )

        summary = tensor.summary()

        assert "MoralTensor Summary" in summary
        assert "Shape: (9, 3)" in summary
        assert "Rank: 2" in summary
        for dim_name in MORAL_DIMENSION_NAMES:
            assert dim_name in summary


class TestMoralTensorConstants:
    """Tests for module constants."""

    def test_dimension_names(self) -> None:
        """Test MORAL_DIMENSION_NAMES has 9 entries."""
        assert len(MORAL_DIMENSION_NAMES) == 9
        assert MORAL_DIMENSION_NAMES[0] == "physical_harm"
        assert MORAL_DIMENSION_NAMES[8] == "epistemic_quality"

    def test_dimension_index(self) -> None:
        """Test DIMENSION_INDEX mapping."""
        assert DIMENSION_INDEX["physical_harm"] == 0
        assert DIMENSION_INDEX["epistemic_quality"] == 8
        assert len(DIMENSION_INDEX) == 9

    def test_default_axis_names(self) -> None:
        """Test DEFAULT_AXIS_NAMES for each rank."""
        assert DEFAULT_AXIS_NAMES[1] == ("k",)
        assert DEFAULT_AXIS_NAMES[2] == ("k", "n")
        assert DEFAULT_AXIS_NAMES[6] == ("k", "n", "tau", "a", "c", "s")
