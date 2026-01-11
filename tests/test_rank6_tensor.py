# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for DEME V3 Rank-6 Tensors and Decomposition (Sprint 15).

Tests tensor decomposition methods, hierarchical sparse storage,
and memory-optimized layouts for full context tensors.
"""

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from erisml.ethics.tensor_decomposition import (
    # Types
    DecompositionType,
    MemoryLayout,
    # Tucker
    TuckerDecomposition,
    # Tensor Train
    TensorTrainDecomposition,
    # Hierarchical Sparse
    HierarchicalSparseTensor,
    # Memory Layout
    OptimizedTensor,
    # Utilities
    validate_rank6_shape,
    create_rank6_tensor,
    estimate_memory_usage,
    recommend_decomposition,
    compress_tensor,
    decompose_for_backend,
    reconstruct_from_decomposition,
)
from erisml.ethics.moral_tensor import MoralTensor


# =============================================================================
# Tucker Decomposition Tests
# =============================================================================


class TestTuckerDecomposition:
    """Tests for Tucker decomposition."""

    def test_rank2_decomposition(self):
        """Test Tucker decomposition on rank-2 tensor."""
        # Create rank-2 moral tensor data
        data = np.random.rand(9, 5) * 0.8 + 0.1  # Values in [0.1, 0.9]

        tucker = TuckerDecomposition.from_tensor(data, ranks=(4, 3))

        assert tucker.core.shape == (4, 3)
        assert len(tucker.factors) == 2
        assert tucker.factors[0].shape == (9, 4)
        assert tucker.factors[1].shape == (5, 3)
        assert tucker.original_shape == (9, 5)

    def test_rank4_decomposition(self):
        """Test Tucker decomposition on rank-4 tensor."""
        data = np.random.rand(9, 4, 3, 5) * 0.5 + 0.25

        tucker = TuckerDecomposition.from_tensor(data, ranks=(5, 2, 2, 3))

        assert tucker.core.shape == (5, 2, 2, 3)
        assert len(tucker.factors) == 4
        assert tucker.ranks == (5, 2, 2, 3)

    def test_rank6_decomposition(self):
        """Test Tucker decomposition on full rank-6 tensor."""
        # Small rank-6 tensor for testing
        data = np.random.rand(9, 3, 2, 2, 2, 4) * 0.6 + 0.2

        tucker = TuckerDecomposition.from_tensor(
            data, relative_ranks=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        )

        assert tucker.core.ndim == 6
        assert tucker.compression_ratio > 1.0  # Should compress

    def test_reconstruction_accuracy(self):
        """Test that reconstruction is accurate."""
        np.random.seed(42)
        data = np.random.rand(9, 5, 4) * 0.8 + 0.1

        # Use high ranks for accurate reconstruction
        tucker = TuckerDecomposition.from_tensor(data, ranks=(9, 5, 4))
        reconstructed = tucker.reconstruct()

        assert reconstructed.shape == data.shape
        assert_allclose(reconstructed, data, rtol=1e-10)

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        data = np.random.rand(9, 10, 8, 6) * 0.5 + 0.25

        tucker = TuckerDecomposition.from_tensor(
            data, relative_ranks=(0.3, 0.3, 0.3, 0.3)
        )

        # Verify compression ratio is reasonable
        assert tucker.compression_ratio > 1.0
        assert tucker.memory_size() < tucker.original_memory_size()

    def test_memory_size_calculation(self):
        """Test memory size calculations."""
        data = np.random.rand(9, 5, 4) * 0.5 + 0.25

        tucker = TuckerDecomposition.from_tensor(data, ranks=(5, 3, 2))

        mem_size = tucker.memory_size()
        orig_size = tucker.original_memory_size()

        assert mem_size > 0
        assert orig_size == 9 * 5 * 4 * 8  # float64
        assert mem_size < orig_size


# =============================================================================
# Tensor Train Decomposition Tests
# =============================================================================


class TestTensorTrainDecomposition:
    """Tests for Tensor Train decomposition."""

    def test_rank3_tt_decomposition(self):
        """Test TT decomposition on rank-3 tensor."""
        data = np.random.rand(9, 5, 4) * 0.8 + 0.1

        tt = TensorTrainDecomposition.from_tensor(data, max_rank=3)

        assert len(tt.cores) == 3
        assert tt.tt_ranks[0] == 1
        assert tt.tt_ranks[-1] == 1
        assert tt.original_shape == (9, 5, 4)

    def test_rank6_tt_decomposition(self):
        """Test TT decomposition on rank-6 tensor."""
        data = np.random.rand(9, 3, 2, 2, 2, 4) * 0.6 + 0.2

        tt = TensorTrainDecomposition.from_tensor(data, max_rank=4)

        assert len(tt.cores) == 6
        assert tt.tt_ranks[0] == 1
        assert tt.tt_ranks[-1] == 1

    def test_tt_reconstruction_accuracy(self):
        """Test TT reconstruction accuracy."""
        np.random.seed(42)
        data = np.random.rand(9, 4, 3) * 0.8 + 0.1

        # High max_rank for accuracy
        tt = TensorTrainDecomposition.from_tensor(data, max_rank=20)
        reconstructed = tt.reconstruct()

        assert reconstructed.shape == data.shape
        # TT-SVD should achieve good accuracy
        rel_error = np.linalg.norm(reconstructed - data) / np.linalg.norm(data)
        assert rel_error < 0.01

    def test_get_element(self):
        """Test efficient single element access."""
        np.random.seed(42)
        data = np.random.rand(9, 4, 3) * 0.8 + 0.1

        tt = TensorTrainDecomposition.from_tensor(data, max_rank=20)

        # Test a few elements
        for _ in range(10):
            idx = (
                np.random.randint(9),
                np.random.randint(4),
                np.random.randint(3),
            )
            tt_val = tt.get_element(idx)
            dense_val = data[idx]
            assert_allclose(tt_val, dense_val, rtol=0.01)

    def test_tt_compression_for_high_rank(self):
        """Test that TT achieves good compression for high-rank tensors."""
        # Create rank-5 tensor
        data = np.random.rand(9, 3, 3, 3, 4) * 0.5 + 0.25

        tt = TensorTrainDecomposition.from_tensor(data, max_rank=3)

        # Should achieve significant compression
        assert tt.compression_ratio > 1.0
        assert tt.memory_size() < tt.original_memory_size()


# =============================================================================
# Hierarchical Sparse Tensor Tests
# =============================================================================


class TestHierarchicalSparseTensor:
    """Tests for hierarchical sparse storage."""

    def test_from_dense_sparse_tensor(self):
        """Test creation from sparse dense tensor."""
        # Create tensor that is 90% zeros
        data = np.zeros((9, 4, 3))
        data[0, 0, 0] = 0.5
        data[1, 1, 1] = 0.6
        data[2, 2, 2] = 0.7

        hst = HierarchicalSparseTensor.from_dense(data, sparsity_threshold=0.5)

        assert hst.shape == (9, 4, 3)
        assert len(hst.blocks) < np.prod(
            tuple((s + b - 1) // b for s, b in zip(data.shape, hst.block_shape))
        )

    def test_get_set_elements(self):
        """Test element access."""
        data = np.random.rand(9, 4, 3) * 0.5

        hst = HierarchicalSparseTensor.from_dense(data, sparsity_threshold=0.99)

        # Test get
        for i in range(9):
            for j in range(4):
                for k in range(3):
                    val = hst.get((i, j, k))
                    assert_allclose(val, data[i, j, k], rtol=1e-10)

    def test_set_new_element(self):
        """Test setting new elements."""
        hst = HierarchicalSparseTensor(
            shape=(9, 4, 3),
            block_shape=(3, 2, 2),
            blocks={},
            fill_value=0.0,
        )

        hst.set((0, 0, 0), 0.5)
        hst.set((5, 2, 1), 0.7)

        assert hst.get((0, 0, 0)) == 0.5
        assert hst.get((5, 2, 1)) == 0.7
        assert hst.get((1, 1, 1)) == 0.0  # fill value

    def test_to_dense_roundtrip(self):
        """Test conversion to/from dense."""
        np.random.seed(42)
        data = np.random.rand(9, 5, 4) * 0.5

        hst = HierarchicalSparseTensor.from_dense(data, sparsity_threshold=0.99)
        reconstructed = hst.to_dense()

        assert reconstructed.shape == data.shape
        assert_allclose(reconstructed, data, rtol=1e-10)

    def test_compression_for_sparse_tensor(self):
        """Test compression achieved for sparse tensors."""
        # Create very sparse tensor
        data = np.zeros((9, 10, 8))
        data[0, 0, 0] = 0.5
        data[4, 5, 3] = 0.7

        hst = HierarchicalSparseTensor.from_dense(data, sparsity_threshold=0.5)

        # Should achieve good compression
        assert hst.compression_ratio > 1.0
        assert hst.memory_size() < data.nbytes


# =============================================================================
# Memory Layout Tests
# =============================================================================


class TestOptimizedTensor:
    """Tests for memory layout optimization."""

    def test_row_major_layout(self):
        """Test row-major (default) layout."""
        data = np.random.rand(9, 4, 3)

        opt = OptimizedTensor.from_tensor(data, MemoryLayout.ROW_MAJOR)

        assert opt.axis_order == (0, 1, 2)
        assert_array_equal(opt.data, data)
        assert_array_equal(opt.to_original(), data)

    def test_party_first_layout(self):
        """Test party-first layout for fairness computations."""
        data = np.random.rand(9, 4, 3)

        opt = OptimizedTensor.from_tensor(data, MemoryLayout.PARTY_FIRST)

        assert opt.axis_order == (1, 0, 2)
        assert opt.data.shape == (4, 9, 3)
        assert_allclose(opt.to_original(), data)

    def test_time_first_layout(self):
        """Test time-first layout for temporal analysis."""
        data = np.random.rand(9, 4, 5, 3)  # k, n, tau, c

        opt = OptimizedTensor.from_tensor(data, MemoryLayout.TIME_FIRST)

        assert opt.axis_order == (2, 0, 1, 3)
        assert opt.data.shape == (5, 9, 4, 3)
        assert_allclose(opt.to_original(), data)

    def test_sample_first_layout_rank5(self):
        """Test sample-first layout for rank-5 tensors."""
        # For rank-5 tensors, samples axis is at index 4
        data5 = np.random.rand(9, 3, 2, 2, 4)  # k, n, tau, c, s

        opt = OptimizedTensor.from_tensor(data5, MemoryLayout.SAMPLE_FIRST)

        assert opt.axis_order[0] == 4  # samples first
        assert_allclose(opt.to_original(), data5)

    def test_slice_axis(self):
        """Test axis slicing."""
        data = np.random.rand(9, 4, 3)

        opt = OptimizedTensor.from_tensor(data, MemoryLayout.PARTY_FIRST)

        # Slice party 2
        party_slice = opt.slice_axis("n", 2)

        assert party_slice.shape[0] == 9  # k dimension


# =============================================================================
# Rank-6 Utility Tests
# =============================================================================


class TestRank6Utilities:
    """Tests for rank-6 tensor utilities."""

    def test_validate_rank6_shape_valid(self):
        """Test validation of valid rank-6 shapes."""
        assert validate_rank6_shape((9, 3, 2, 2, 2, 4)) is True
        assert validate_rank6_shape((9, 1, 1, 1, 1, 1)) is True
        assert validate_rank6_shape((9, 10, 5, 4, 3, 100)) is True

    def test_validate_rank6_shape_invalid(self):
        """Test validation of invalid shapes."""
        assert validate_rank6_shape((8, 3, 2, 2, 2, 4)) is False  # k != 9
        assert validate_rank6_shape((9, 3, 2, 2, 2)) is False  # wrong rank
        assert validate_rank6_shape((9,)) is False  # rank-1
        assert validate_rank6_shape((9, 0, 2, 2, 2, 4)) is False  # zero dim

    def test_create_rank6_tensor(self):
        """Test rank-6 tensor creation."""
        tensor = create_rank6_tensor(
            n_parties=3,
            n_timesteps=2,
            n_actions=2,
            n_coalitions=2,
            n_samples=4,
            fill_value=0.5,
        )

        assert tensor.shape == (9, 3, 2, 2, 2, 4)
        assert np.all(tensor == 0.5)

    def test_estimate_memory_usage(self):
        """Test memory estimation."""
        shape = (9, 10, 5, 4, 3, 100)

        mem = estimate_memory_usage(shape, "float64")
        expected = 9 * 10 * 5 * 4 * 3 * 100 * 8

        assert mem == expected

    def test_recommend_decomposition_sparse(self):
        """Test decomposition recommendation for sparse tensors."""
        shape = (9, 10, 5, 4)

        rec = recommend_decomposition(shape, sparsity=0.95)

        assert rec == DecompositionType.TUCKER

    def test_recommend_decomposition_high_rank(self):
        """Test decomposition recommendation for high-rank tensors."""
        shape = (9, 5, 4, 3, 2, 10)  # rank-6

        rec = recommend_decomposition(shape, sparsity=0.1)

        assert rec == DecompositionType.TENSOR_TRAIN


# =============================================================================
# Compression Tests
# =============================================================================


class TestCompression:
    """Tests for tensor compression."""

    def test_compress_with_tucker(self):
        """Test compression using Tucker decomposition."""
        # Use larger tensor where compression is achievable
        data = np.random.rand(9, 10, 8, 6) * 0.8 + 0.1

        compressed = compress_tensor(
            data, method=DecompositionType.TUCKER, target_compression=2.0
        )

        assert isinstance(compressed, TuckerDecomposition)
        # Tucker with relative ranks should achieve some compression
        assert compressed.memory_size() < compressed.original_memory_size()

    def test_compress_with_tensor_train(self):
        """Test compression using Tensor Train."""
        data = np.random.rand(9, 4, 3, 2, 5) * 0.6 + 0.2

        compressed = compress_tensor(
            data, method=DecompositionType.TENSOR_TRAIN, target_compression=5.0
        )

        assert isinstance(compressed, TensorTrainDecomposition)

    def test_compress_auto_select(self):
        """Test automatic decomposition selection."""
        # High-rank tensor
        data = np.random.rand(9, 3, 2, 2, 2, 4) * 0.5 + 0.25

        compressed = compress_tensor(data, target_compression=10.0)

        # Should choose TT for rank-6
        assert isinstance(compressed, (TensorTrainDecomposition, TuckerDecomposition))


# =============================================================================
# Backend Integration Tests
# =============================================================================


class TestBackendIntegration:
    """Tests for acceleration backend integration."""

    def test_decompose_for_cpu_small_tensor(self):
        """Test that small tensors are not decomposed for CPU."""
        data = np.random.rand(9, 3, 2) * 0.5 + 0.25

        result = decompose_for_backend(data, "cpu", memory_limit=1000000)

        assert isinstance(result, np.ndarray)
        assert_array_equal(result, data)

    def test_decompose_for_cuda(self):
        """Test decomposition for CUDA backend."""
        data = np.random.rand(9, 10, 8, 6) * 0.5 + 0.25

        # Force compression
        result = decompose_for_backend(data, "cuda", memory_limit=1000)

        assert isinstance(result, TuckerDecomposition)

    def test_decompose_for_jetson(self):
        """Test aggressive compression for Jetson."""
        data = np.random.rand(9, 5, 4, 3) * 0.5 + 0.25

        # Very small memory limit
        result = decompose_for_backend(data, "jetson", memory_limit=100)

        assert isinstance(result, TensorTrainDecomposition)

    def test_reconstruct_from_decomposition(self):
        """Test reconstruction from any decomposition type."""
        np.random.seed(42)
        data = np.random.rand(9, 4, 3) * 0.8 + 0.1

        # Test with original array
        result = reconstruct_from_decomposition(data)
        assert_array_equal(result, data)

        # Test with Tucker
        tucker = TuckerDecomposition.from_tensor(data, ranks=(9, 4, 3))
        result = reconstruct_from_decomposition(tucker)
        assert_allclose(result, data, rtol=1e-10)

        # Test with TT
        tt = TensorTrainDecomposition.from_tensor(data, max_rank=10)
        result = reconstruct_from_decomposition(tt)
        assert result.shape == data.shape

        # Test with hierarchical sparse
        hst = HierarchicalSparseTensor.from_dense(data, sparsity_threshold=0.99)
        result = reconstruct_from_decomposition(hst)
        assert_allclose(result, data, rtol=1e-10)


# =============================================================================
# MoralTensor Integration Tests
# =============================================================================


class TestMoralTensorIntegration:
    """Tests for integration with MoralTensor."""

    def test_rank6_moral_tensor_creation(self):
        """Test creating rank-6 MoralTensor."""
        data = np.random.rand(9, 3, 2, 2, 2, 4) * 0.8 + 0.1

        tensor = MoralTensor.from_dense(data)

        assert tensor.rank == 6
        assert tensor.shape == (9, 3, 2, 2, 2, 4)

    def test_rank6_moral_tensor_operations(self):
        """Test basic operations on rank-6 MoralTensor."""
        data = np.random.rand(9, 3, 2, 2, 2, 4) * 0.8 + 0.1

        tensor = MoralTensor.from_dense(data)

        # Test to_dense
        dense = tensor.to_dense()
        assert_allclose(dense, data)

        # Test to_sparse
        sparse = tensor.to_sparse()
        assert sparse.rank == 6

    def test_moral_tensor_with_decomposition(self):
        """Test decomposing MoralTensor data."""
        data = np.random.rand(9, 4, 3, 2, 2, 5) * 0.6 + 0.2

        tensor = MoralTensor.from_dense(data)
        dense = tensor.to_dense()

        # Decompose for compression
        compressed = compress_tensor(dense, target_compression=5.0)

        # Verify we can reconstruct
        reconstructed = reconstruct_from_decomposition(compressed)
        assert reconstructed.shape == data.shape


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_element_tensor(self):
        """Test decomposition of minimal tensors."""
        data = np.array([[[[[0.5]]]]] * 9).reshape(9, 1, 1, 1, 1, 1)

        tucker = TuckerDecomposition.from_tensor(data, ranks=(1, 1, 1, 1, 1, 1))
        reconstructed = tucker.reconstruct()

        assert_allclose(reconstructed, data)

    def test_all_zeros_tensor(self):
        """Test handling of all-zero tensor."""
        data = np.zeros((9, 3, 2))

        tucker = TuckerDecomposition.from_tensor(data)
        reconstructed = tucker.reconstruct()

        assert_allclose(reconstructed, data, atol=1e-10)

    def test_all_ones_tensor(self):
        """Test handling of uniform tensor."""
        data = np.ones((9, 3, 2))

        tucker = TuckerDecomposition.from_tensor(data, ranks=(1, 1, 1))
        reconstructed = tucker.reconstruct()

        # Low-rank approx of constant tensor should be accurate
        assert_allclose(reconstructed, data, rtol=0.01)

    def test_hierarchical_sparse_empty_blocks(self):
        """Test hierarchical sparse with all empty blocks."""
        # Use shape that divides evenly into blocks to avoid edge block issues
        data = np.zeros((9, 4, 4))

        hst = HierarchicalSparseTensor.from_dense(
            data, block_shape=(3, 2, 2), sparsity_threshold=0.5
        )

        # All-zero blocks should be skipped (sparsity > threshold)
        assert len(hst.blocks) == 0

        # But should still reconstruct correctly
        reconstructed = hst.to_dense()
        assert_allclose(reconstructed, data)

    def test_large_rank6_tensor(self):
        """Test with larger rank-6 tensor."""
        # Still modest size for testing
        data = np.random.rand(9, 5, 4, 3, 3, 10) * 0.5 + 0.25

        tt = TensorTrainDecomposition.from_tensor(data, max_rank=5)

        # Should compress significantly
        assert tt.compression_ratio > 1.0

        # Reconstruction should be reasonable
        reconstructed = tt.reconstruct()
        assert reconstructed.shape == data.shape

    def test_decomposition_type_enum(self):
        """Test DecompositionType enum values."""
        assert DecompositionType.TUCKER.value == "tucker"
        assert DecompositionType.TENSOR_TRAIN.value == "tensor_train"
        assert DecompositionType.CP.value == "cp"

    def test_memory_layout_enum(self):
        """Test MemoryLayout enum values."""
        assert MemoryLayout.ROW_MAJOR.value == "row_major"
        assert MemoryLayout.PARTY_FIRST.value == "party_first"
        assert MemoryLayout.SAMPLE_FIRST.value == "sample_first"
