# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tensor Decomposition for DEME V3 Rank-6 Tensors.

Sprint 15: Provides compression and memory-efficient representations for
full context tensors (rank-6). Implements:

- Tucker decomposition for multi-linear compression
- Tensor Train (TT) decomposition for exponential compression
- Hierarchical sparse storage for nested sparsity patterns
- Memory-optimized layouts for common access patterns

Rank-6 Tensor Structure:
    (k, n, τ, a, c, s) where:
    - k: moral dimensions (9)
    - n: parties/agents
    - τ: time steps
    - a: actions
    - c: coalitions
    - s: Monte Carlo samples

Version: 3.0.0 (DEME V3 Sprint 15)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Union

import numpy as np
from numpy.linalg import svd

logger = logging.getLogger(__name__)

# Numerical stability constant
EPSILON = 1e-10


class DecompositionType(Enum):
    """Types of tensor decomposition."""

    TUCKER = "tucker"
    TENSOR_TRAIN = "tensor_train"
    CP = "cp"  # Canonical Polyadic (future)
    HIERARCHICAL_TUCKER = "hierarchical_tucker"  # Future


class MemoryLayout(Enum):
    """Memory layout optimizations for access patterns."""

    ROW_MAJOR = "row_major"  # C-style, default numpy
    COLUMN_MAJOR = "column_major"  # Fortran-style
    PARTY_FIRST = "party_first"  # Optimize for party-wise access
    TIME_FIRST = "time_first"  # Optimize for temporal access
    SAMPLE_FIRST = "sample_first"  # Optimize for Monte Carlo sampling


# =============================================================================
# Tucker Decomposition
# =============================================================================


@dataclass
class TuckerDecomposition:
    """
    Tucker decomposition of a tensor.

    Represents a tensor T as: T ≈ G ×₁ U₁ ×₂ U₂ ... ×ₙ Uₙ
    where G is the core tensor and U_i are factor matrices.

    This achieves compression by using smaller factor matrices when
    rank < dimension size along each mode.

    Attributes:
        core: Core tensor G of shape (r₁, r₂, ..., rₙ).
        factors: List of factor matrices U_i of shape (dim_i, r_i).
        original_shape: Original tensor shape.
        ranks: Tucker ranks for each mode.
        compression_ratio: Memory compression achieved.
    """

    core: np.ndarray
    """Core tensor of reduced size."""

    factors: List[np.ndarray]
    """Factor matrices for each mode."""

    original_shape: Tuple[int, ...]
    """Shape of the original tensor."""

    ranks: Tuple[int, ...]
    """Tucker ranks used for each mode."""

    compression_ratio: float = 1.0
    """Memory compression ratio (original/compressed)."""

    def __post_init__(self) -> None:
        """Validate decomposition structure."""
        if len(self.factors) != len(self.original_shape):
            raise ValueError(
                f"Number of factors ({len(self.factors)}) must match "
                f"tensor rank ({len(self.original_shape)})"
            )
        if self.core.ndim != len(self.original_shape):
            raise ValueError(
                f"Core tensor rank ({self.core.ndim}) must match "
                f"original tensor rank ({len(self.original_shape)})"
            )

    def reconstruct(self) -> np.ndarray:
        """
        Reconstruct the full tensor from Tucker decomposition.

        Returns:
            Reconstructed tensor of original shape.
        """
        result = self.core.copy()
        for mode, factor in enumerate(self.factors):
            # Mode-k product: contract result's mode-th axis with factor's axis 1
            result = np.tensordot(result, factor, axes=([mode], [1]))
            # The new dimension is at the end, move it to position mode
            result = np.moveaxis(result, -1, mode)
        return result

    def memory_size(self) -> int:
        """
        Calculate memory usage of decomposed form.

        Returns:
            Memory size in bytes.
        """
        core_size = self.core.nbytes
        factor_size = sum(f.nbytes for f in self.factors)
        return core_size + factor_size

    def original_memory_size(self) -> int:
        """
        Calculate memory of original dense tensor.

        Returns:
            Memory size in bytes.
        """
        return int(np.prod(self.original_shape) * 8)  # float64

    @classmethod
    def from_tensor(
        cls,
        tensor: np.ndarray,
        ranks: Optional[Tuple[int, ...]] = None,
        relative_ranks: Optional[Tuple[float, ...]] = None,
    ) -> TuckerDecomposition:
        """
        Compute Tucker decomposition of a tensor.

        Uses Higher-Order SVD (HOSVD) for factor computation.

        Args:
            tensor: Input tensor to decompose.
            ranks: Explicit ranks for each mode (overrides relative_ranks).
            relative_ranks: Fraction of original dimension (0-1) for each mode.

        Returns:
            TuckerDecomposition instance.
        """
        original_shape = tensor.shape
        n_modes = tensor.ndim

        # Determine ranks
        if ranks is None:
            if relative_ranks is None:
                # Default: keep 50% of each dimension
                relative_ranks = tuple(0.5 for _ in range(n_modes))
            ranks = tuple(
                max(1, int(dim * rel))
                for dim, rel in zip(original_shape, relative_ranks)
            )

        # Compute factor matrices via HOSVD
        factors = []
        for mode in range(n_modes):
            # Unfold tensor along mode
            unfolded = _unfold(tensor, mode)
            # SVD of unfolded matrix
            u, _, _ = svd(unfolded, full_matrices=False)
            # Keep only top-k left singular vectors
            r = min(ranks[mode], u.shape[1])
            factors.append(u[:, :r])

        # Compute core tensor: G = T ×₁ U₁ᵀ ×₂ U₂ᵀ ... ×ₙ Uₙᵀ
        core = tensor.copy()
        for mode, factor in enumerate(factors):
            # Mode-k product: contract core's mode-th axis with factor.T's axis 1
            core = np.tensordot(core, factor.T, axes=([mode], [1]))
            # The new dimension is at the end, move it to position mode
            core = np.moveaxis(core, -1, mode)

        # Calculate compression ratio
        original_size = int(np.prod(original_shape)) * 8
        core_size = core.nbytes
        factor_size = sum(f.nbytes for f in factors)
        compression = original_size / max(core_size + factor_size, 1)

        return cls(
            core=core,
            factors=factors,
            original_shape=original_shape,
            ranks=tuple(f.shape[1] for f in factors),
            compression_ratio=compression,
        )


def _unfold(tensor: np.ndarray, mode: int) -> np.ndarray:
    """
    Unfold (matricize) a tensor along a given mode.

    Args:
        tensor: Input tensor.
        mode: Mode to unfold along.

    Returns:
        Unfolded matrix of shape (dim_mode, product of other dims).
    """
    # Move the mode to the first axis
    n_dims = tensor.ndim
    axes = [mode] + [i for i in range(n_dims) if i != mode]
    tensor_permuted = np.transpose(tensor, axes)
    # Reshape to matrix
    return tensor_permuted.reshape(tensor.shape[mode], -1)


# =============================================================================
# Tensor Train Decomposition
# =============================================================================


@dataclass
class TensorTrainDecomposition:
    """
    Tensor Train (TT) decomposition of a tensor.

    Represents a tensor T as a sequence of 3D cores:
    T(i₁, i₂, ..., iₙ) = G₁(i₁) G₂(i₂) ... Gₙ(iₙ)

    where Gₖ(iₖ) is a matrix of shape (rₖ₋₁, rₖ) and r₀ = rₙ = 1.

    This achieves exponential compression for high-rank tensors
    with bounded TT-ranks.

    Attributes:
        cores: List of 3D core tensors of shape (r_{k-1}, dim_k, r_k).
        original_shape: Original tensor shape.
        tt_ranks: TT-ranks (r₀, r₁, ..., rₙ) where r₀ = rₙ = 1.
        compression_ratio: Memory compression achieved.
    """

    cores: List[np.ndarray]
    """TT cores, each of shape (r_{k-1}, dim_k, r_k)."""

    original_shape: Tuple[int, ...]
    """Shape of the original tensor."""

    tt_ranks: Tuple[int, ...]
    """TT-ranks including boundary 1s."""

    compression_ratio: float = 1.0
    """Memory compression ratio (original/compressed)."""

    def __post_init__(self) -> None:
        """Validate TT decomposition structure."""
        if len(self.cores) != len(self.original_shape):
            raise ValueError(
                f"Number of cores ({len(self.cores)}) must match "
                f"tensor rank ({len(self.original_shape)})"
            )
        if self.tt_ranks[0] != 1 or self.tt_ranks[-1] != 1:
            raise ValueError("TT-ranks must start and end with 1")

    def reconstruct(self) -> np.ndarray:
        """
        Reconstruct the full tensor from TT decomposition.

        Returns:
            Reconstructed tensor of original shape.
        """
        n_modes = len(self.cores)
        # Start with first core reshaped
        result = self.cores[0].reshape(self.original_shape[0], self.tt_ranks[1])

        # Multiply through cores
        for k in range(1, n_modes):
            core = self.cores[k]  # (r_{k-1}, dim_k, r_k)
            # result is (prod_dims, r_{k-1})
            # core unfolded is (r_{k-1}, dim_k * r_k)
            core_mat = core.reshape(core.shape[0], -1)
            result = result @ core_mat
            # result is now (prod_dims, dim_k * r_k)
            new_shape = list(self.original_shape[: k + 1]) + [self.tt_ranks[k + 1]]
            result = result.reshape(new_shape)

        # Remove final dimension (r_n = 1)
        return result.squeeze(-1)

    def memory_size(self) -> int:
        """
        Calculate memory usage of TT decomposition.

        Returns:
            Memory size in bytes.
        """
        return sum(core.nbytes for core in self.cores)

    def original_memory_size(self) -> int:
        """
        Calculate memory of original dense tensor.

        Returns:
            Memory size in bytes.
        """
        return int(np.prod(self.original_shape) * 8)

    def get_element(self, indices: Tuple[int, ...]) -> float:
        """
        Get a single element without full reconstruction.

        Args:
            indices: Tuple of indices for each mode.

        Returns:
            Tensor value at the specified indices.
        """
        if len(indices) != len(self.cores):
            raise ValueError(f"Expected {len(self.cores)} indices, got {len(indices)}")

        # Multiply slices through cores
        result = self.cores[0][0, indices[0], :]  # (r_1,)
        for k in range(1, len(self.cores)):
            core_slice = self.cores[k][:, indices[k], :]  # (r_{k-1}, r_k)
            result = result @ core_slice  # (r_k,)

        return float(result[0])

    @classmethod
    def from_tensor(
        cls,
        tensor: np.ndarray,
        max_rank: Optional[int] = None,
        relative_accuracy: float = 1e-6,
    ) -> TensorTrainDecomposition:
        """
        Compute TT decomposition using TT-SVD algorithm.

        Args:
            tensor: Input tensor to decompose.
            max_rank: Maximum TT-rank (default: no limit).
            relative_accuracy: Target relative accuracy (Frobenius norm).

        Returns:
            TensorTrainDecomposition instance.
        """
        original_shape = tensor.shape
        n_modes = tensor.ndim

        # Frobenius norm for accuracy
        norm = np.linalg.norm(tensor)
        delta = relative_accuracy * norm / np.sqrt(n_modes - 1) if norm > EPSILON else 0

        # TT-SVD algorithm
        cores = []
        tt_ranks = [1]
        remaining = tensor.copy()

        for k in range(n_modes - 1):
            # Reshape to matrix (r_{k-1} * dim_k, remaining_dims)
            r_prev = tt_ranks[-1]
            dim_k = original_shape[k]
            remaining = remaining.reshape(r_prev * dim_k, -1)

            # Truncated SVD
            u, s, vh = svd(remaining, full_matrices=False)

            # Determine rank based on accuracy or max_rank
            cumsum = np.cumsum(s[::-1] ** 2)[::-1]
            rank_idx = np.searchsorted(-cumsum, -(delta**2)) if delta > 0 else len(s)
            rank = max(1, rank_idx)
            if max_rank is not None:
                rank = min(rank, max_rank)
            rank = min(rank, len(s))

            # Truncate
            u = u[:, :rank]
            s = s[:rank]
            vh = vh[:rank, :]

            # Store core
            core = u.reshape(r_prev, dim_k, rank)
            cores.append(core)
            tt_ranks.append(rank)

            # Prepare for next iteration
            remaining = np.diag(s) @ vh

        # Final core
        cores.append(remaining.reshape(tt_ranks[-1], original_shape[-1], 1))
        tt_ranks.append(1)

        # Calculate compression ratio
        original_size = int(np.prod(original_shape)) * 8
        compressed_size = sum(core.nbytes for core in cores)
        compression = original_size / max(compressed_size, 1)

        return cls(
            cores=cores,
            original_shape=original_shape,
            tt_ranks=tuple(tt_ranks),
            compression_ratio=compression,
        )


# =============================================================================
# Hierarchical Sparse Tensor
# =============================================================================


@dataclass
class SparseBlock:
    """A sparse block within a hierarchical tensor."""

    offset: Tuple[int, ...]
    """Starting indices for this block."""

    shape: Tuple[int, ...]
    """Shape of this block."""

    data: np.ndarray
    """Dense data for this block."""

    is_leaf: bool = True
    """Whether this is a leaf block (contains data)."""

    children: List["SparseBlock"] = field(default_factory=list)
    """Child blocks for non-leaf nodes."""


@dataclass
class HierarchicalSparseTensor:
    """
    Hierarchical sparse tensor storage.

    Uses a block-sparse structure where the tensor is divided into
    blocks, and only non-zero blocks are stored. Blocks can be
    further subdivided for nested sparsity patterns.

    This is particularly efficient for rank-6 ethical tensors where:
    - Most coalition configurations have zero impact
    - Sparsity has hierarchical structure (e.g., if party i absent,
      all i-dependent entries are zero)

    Attributes:
        shape: Full tensor shape.
        block_shape: Shape of each block.
        blocks: Dictionary mapping block indices to data.
        fill_value: Value for unspecified blocks.
        n_levels: Number of hierarchical levels.
    """

    shape: Tuple[int, ...]
    """Full tensor shape."""

    block_shape: Tuple[int, ...]
    """Shape of each block."""

    blocks: dict
    """Mapping from block indices to block data."""

    fill_value: float = 0.0
    """Default value for empty blocks."""

    n_levels: int = 1
    """Number of hierarchical subdivision levels."""

    compression_ratio: float = 1.0
    """Memory compression achieved."""

    def __post_init__(self) -> None:
        """Validate hierarchical structure."""
        if len(self.shape) != len(self.block_shape):
            raise ValueError(
                f"Shape rank ({len(self.shape)}) must match "
                f"block_shape rank ({len(self.block_shape)})"
            )

    def get(self, indices: Tuple[int, ...]) -> float:
        """
        Get a single element.

        Args:
            indices: Full tensor indices.

        Returns:
            Value at the specified indices.
        """
        # Compute block index and offset within block
        block_idx = tuple(i // b for i, b in zip(indices, self.block_shape))
        within_block = tuple(i % b for i, b in zip(indices, self.block_shape))

        if block_idx in self.blocks:
            return float(self.blocks[block_idx][within_block])
        return self.fill_value

    def set(self, indices: Tuple[int, ...], value: float) -> None:
        """
        Set a single element.

        Args:
            indices: Full tensor indices.
            value: Value to set.
        """
        block_idx = tuple(i // b for i, b in zip(indices, self.block_shape))
        within_block = tuple(i % b for i, b in zip(indices, self.block_shape))

        if block_idx not in self.blocks:
            # Create new block
            self.blocks[block_idx] = np.full(
                self.block_shape, self.fill_value, dtype=np.float64
            )

        self.blocks[block_idx][within_block] = value

    def to_dense(self) -> np.ndarray:
        """
        Convert to dense numpy array.

        Returns:
            Dense tensor.
        """
        result = np.full(self.shape, self.fill_value, dtype=np.float64)

        for block_idx, block_data in self.blocks.items():
            # Calculate slice for this block
            slices = tuple(
                slice(i * b, min((i + 1) * b, s))
                for i, b, s in zip(block_idx, self.block_shape, self.shape)
            )
            # Handle edge blocks that may be smaller
            block_slices = tuple(slice(0, sl.stop - sl.start) for sl in slices)
            result[slices] = block_data[block_slices]

        return result

    def memory_size(self) -> int:
        """
        Calculate memory usage.

        Returns:
            Memory size in bytes.
        """
        overhead = 64 * len(self.blocks)  # Approximate dict overhead
        data_size = sum(b.nbytes for b in self.blocks.values())
        return overhead + data_size

    @classmethod
    def from_dense(
        cls,
        tensor: np.ndarray,
        block_shape: Optional[Tuple[int, ...]] = None,
        fill_value: float = 0.0,
        sparsity_threshold: float = 0.9,
    ) -> HierarchicalSparseTensor:
        """
        Create hierarchical sparse tensor from dense array.

        Args:
            tensor: Dense input tensor.
            block_shape: Shape of each block (default: auto-compute).
            fill_value: Value to treat as sparse.
            sparsity_threshold: Fraction of fill values to skip block.

        Returns:
            HierarchicalSparseTensor instance.
        """
        shape = tensor.shape
        rank = tensor.ndim

        # Auto-compute block shape
        if block_shape is None:
            # Use smaller blocks for higher ranks
            block_size = max(2, 8 // rank)
            block_shape = tuple(min(block_size, s) for s in shape)

        # Compute number of blocks per dimension
        n_blocks = tuple((s + b - 1) // b for s, b in zip(shape, block_shape))

        # Iterate over all possible blocks
        blocks = {}
        threshold = sparsity_threshold * np.prod(block_shape)

        for block_idx in np.ndindex(*n_blocks):
            # Extract block
            slices = tuple(
                slice(i * b, min((i + 1) * b, s))
                for i, b, s in zip(block_idx, block_shape, shape)
            )
            block_data = tensor[slices].copy()

            # Check sparsity
            if fill_value == 0.0:
                n_zeros = np.sum(np.abs(block_data) < EPSILON)
            else:
                n_zeros = np.sum(np.abs(block_data - fill_value) < EPSILON)

            # Store only non-sparse blocks
            if n_zeros < threshold:
                # Pad to full block shape if edge block
                if block_data.shape != block_shape:
                    padded = np.full(block_shape, fill_value, dtype=np.float64)
                    padded_slices = tuple(slice(0, s) for s in block_data.shape)
                    padded[padded_slices] = block_data
                    block_data = padded
                blocks[block_idx] = block_data

        # Calculate compression
        original_size = tensor.nbytes
        compressed_size = sum(b.nbytes for b in blocks.values()) + 64 * len(blocks)
        compression = original_size / max(compressed_size, 1)

        return cls(
            shape=shape,
            block_shape=block_shape,
            blocks=blocks,
            fill_value=fill_value,
            compression_ratio=compression,
        )


# =============================================================================
# Memory Layout Optimization
# =============================================================================


@dataclass
class OptimizedTensor:
    """
    Tensor with optimized memory layout for specific access patterns.

    Provides efficient access for common DEME operations like:
    - Party-wise iteration (for fairness metrics)
    - Time-wise slicing (for temporal analysis)
    - Sample aggregation (for Monte Carlo)
    """

    data: np.ndarray
    """Tensor data in optimized layout."""

    original_shape: Tuple[int, ...]
    """Original tensor shape."""

    layout: MemoryLayout
    """Memory layout used."""

    axis_order: Tuple[int, ...]
    """Order of axes in optimized layout."""

    def __post_init__(self) -> None:
        """Validate layout."""
        if len(self.axis_order) != len(self.original_shape):
            raise ValueError("axis_order must match tensor rank")

    def to_original(self) -> np.ndarray:
        """
        Convert back to original layout.

        Returns:
            Tensor in original axis order.
        """
        # Inverse permutation
        inv_order = [0] * len(self.axis_order)
        for i, j in enumerate(self.axis_order):
            inv_order[j] = i
        return np.transpose(self.data, inv_order)

    def slice_axis(self, axis_name: str, index: int) -> np.ndarray:
        """
        Efficiently slice along an axis.

        Args:
            axis_name: Name of axis to slice ('n', 'tau', 's', etc.).
            index: Index to select.

        Returns:
            Sliced tensor.
        """
        # Map axis name to position in optimized layout
        axis_map = {"k": 0, "n": 1, "tau": 2, "a": 3, "c": 4, "s": 5}
        original_axis = axis_map.get(axis_name, -1)
        if original_axis < 0 or original_axis >= len(self.original_shape):
            raise ValueError(f"Unknown axis: {axis_name}")

        # Find position in optimized layout
        opt_axis = self.axis_order.index(original_axis)

        # Slice
        slices = [slice(None)] * self.data.ndim
        slices[opt_axis] = index
        return self.data[tuple(slices)]

    @classmethod
    def from_tensor(cls, tensor: np.ndarray, layout: MemoryLayout) -> OptimizedTensor:
        """
        Create optimized tensor with specified layout.

        Args:
            tensor: Input tensor.
            layout: Desired memory layout.

        Returns:
            OptimizedTensor with optimized access patterns.
        """
        original_shape = tensor.shape
        rank = tensor.ndim

        # Determine axis order based on layout
        if layout == MemoryLayout.ROW_MAJOR:
            axis_order = tuple(range(rank))
        elif layout == MemoryLayout.COLUMN_MAJOR:
            axis_order = tuple(reversed(range(rank)))
        elif layout == MemoryLayout.PARTY_FIRST:
            # Put party axis (n) first for party-wise iteration
            # (n, k, tau, a, c, s) for rank-6
            if rank >= 2:
                axis_order = (1, 0) + tuple(range(2, rank))
            else:
                axis_order = tuple(range(rank))
        elif layout == MemoryLayout.TIME_FIRST:
            # Put time axis (tau) first for temporal analysis
            # (tau, k, n, a, c, s) for rank-6
            if rank >= 3:
                axis_order = (2, 0, 1) + tuple(range(3, rank))
            else:
                axis_order = tuple(range(rank))
        elif layout == MemoryLayout.SAMPLE_FIRST:
            # Put sample axis last (or first) for Monte Carlo
            # For rank-5/6, samples are last axis
            if rank >= 5:
                axis_order = (rank - 1,) + tuple(range(rank - 1))
            else:
                axis_order = tuple(range(rank))
        else:
            axis_order = tuple(range(rank))

        # Transpose to optimized layout
        data = np.transpose(tensor, axis_order)

        # Make contiguous for cache efficiency
        data = np.ascontiguousarray(data)

        return cls(
            data=data,
            original_shape=original_shape,
            layout=layout,
            axis_order=axis_order,
        )


# =============================================================================
# Rank-6 Tensor Utilities
# =============================================================================


def validate_rank6_shape(shape: Tuple[int, ...]) -> bool:
    """
    Validate that a shape is valid for rank-6 ethical tensor.

    Rank-6 shape: (k, n, τ, a, c, s) where k=9.

    Args:
        shape: Shape tuple to validate.

    Returns:
        True if valid rank-6 shape.
    """
    if len(shape) != 6:
        return False
    if shape[0] != 9:
        return False
    return all(dim > 0 for dim in shape)


def create_rank6_tensor(
    n_parties: int,
    n_timesteps: int,
    n_actions: int,
    n_coalitions: int,
    n_samples: int,
    fill_value: float = 0.5,
) -> np.ndarray:
    """
    Create an empty rank-6 ethical tensor.

    Args:
        n_parties: Number of parties/agents.
        n_timesteps: Number of time steps.
        n_actions: Number of actions per party.
        n_coalitions: Number of coalition configurations.
        n_samples: Number of Monte Carlo samples.
        fill_value: Initial fill value.

    Returns:
        Rank-6 tensor of shape (9, n, τ, a, c, s).
    """
    shape = (9, n_parties, n_timesteps, n_actions, n_coalitions, n_samples)
    return np.full(shape, fill_value, dtype=np.float64)


def estimate_memory_usage(shape: Tuple[int, ...], dtype: str = "float64") -> int:
    """
    Estimate memory usage for a tensor.

    Args:
        shape: Tensor shape.
        dtype: Data type.

    Returns:
        Estimated memory in bytes.
    """
    n_elements = int(np.prod(shape))
    bytes_per_element = {"float32": 4, "float64": 8, "float16": 2}.get(dtype, 8)
    return n_elements * bytes_per_element


def recommend_decomposition(
    shape: Tuple[int, ...],
    target_compression: float = 10.0,
    sparsity: float = 0.0,
) -> DecompositionType:
    """
    Recommend best decomposition for a tensor.

    Args:
        shape: Tensor shape.
        target_compression: Desired compression ratio.
        sparsity: Estimated fraction of zero/fill values.

    Returns:
        Recommended decomposition type.
    """
    rank = len(shape)

    # High sparsity: use hierarchical sparse
    if sparsity > 0.9:
        return DecompositionType.TUCKER  # or HIERARCHICAL_TUCKER when available

    # High rank (5-6): Tensor Train is efficient
    if rank >= 5:
        return DecompositionType.TENSOR_TRAIN

    # Medium rank: Tucker works well
    if rank >= 3:
        return DecompositionType.TUCKER

    # Low rank: minimal compression needed
    return DecompositionType.TUCKER


def compress_tensor(
    tensor: np.ndarray,
    method: Optional[DecompositionType] = None,
    target_compression: float = 10.0,
    **kwargs,
) -> Union[TuckerDecomposition, TensorTrainDecomposition, HierarchicalSparseTensor]:
    """
    Compress a tensor using the best available method.

    Args:
        tensor: Input tensor.
        method: Specific decomposition to use (auto-select if None).
        target_compression: Desired compression ratio.
        **kwargs: Additional arguments for decomposition.

    Returns:
        Compressed tensor representation.
    """
    if method is None:
        # Estimate sparsity
        sparsity = np.sum(np.abs(tensor) < EPSILON) / tensor.size
        method = recommend_decomposition(tensor.shape, target_compression, sparsity)

    if method == DecompositionType.TUCKER:
        # Compute relative ranks for target compression
        rank = tensor.ndim
        # Rough estimate: relative_rank^rank ≈ 1/compression
        # Use smaller relative ranks to ensure actual compression
        rel = (1.0 / target_compression) ** (1.0 / rank)
        # Cap at 0.7 to ensure meaningful compression
        rel = min(rel, 0.7)
        relative_ranks = tuple(rel for _ in range(rank))
        return TuckerDecomposition.from_tensor(
            tensor, relative_ranks=relative_ranks, **kwargs
        )

    elif method == DecompositionType.TENSOR_TRAIN:
        # Estimate max rank for target compression
        rank = tensor.ndim
        max_rank = kwargs.get("max_rank")
        if max_rank is None:
            # Rough estimate
            max_dim = max(tensor.shape)
            max_rank = max(1, int(max_dim / (target_compression ** (1.0 / rank))))
        return TensorTrainDecomposition.from_tensor(tensor, max_rank=max_rank, **kwargs)

    else:
        # Default to hierarchical sparse
        return HierarchicalSparseTensor.from_dense(tensor, **kwargs)


# =============================================================================
# Backend Integration
# =============================================================================


def decompose_for_backend(
    tensor: np.ndarray,
    backend_name: str,
    memory_limit: Optional[int] = None,
) -> Union[np.ndarray, TuckerDecomposition, TensorTrainDecomposition]:
    """
    Decompose tensor for efficient use with acceleration backend.

    Args:
        tensor: Input tensor.
        backend_name: Name of acceleration backend ('cpu', 'cuda', 'jetson').
        memory_limit: Maximum memory in bytes (None = no limit).

    Returns:
        Original tensor or decomposed representation.
    """
    tensor_memory = tensor.nbytes

    # Check if compression needed
    if memory_limit is None or tensor_memory <= memory_limit:
        return tensor

    # Compute required compression
    target_compression = tensor_memory / memory_limit

    # Backend-specific recommendations
    if backend_name == "cuda":
        # CUDA prefers Tucker for GPU-friendly matrix operations
        return compress_tensor(
            tensor,
            method=DecompositionType.TUCKER,
            target_compression=target_compression,
        )
    elif backend_name == "jetson":
        # Jetson has limited memory, use aggressive compression
        return compress_tensor(
            tensor,
            method=DecompositionType.TENSOR_TRAIN,
            target_compression=max(target_compression, 20.0),
        )
    else:
        # CPU: use whatever achieves target
        return compress_tensor(tensor, target_compression=target_compression)


def reconstruct_from_decomposition(
    decomposed: Union[
        np.ndarray,
        TuckerDecomposition,
        TensorTrainDecomposition,
        HierarchicalSparseTensor,
    ]
) -> np.ndarray:
    """
    Reconstruct dense tensor from any decomposed representation.

    Args:
        decomposed: Decomposed tensor or original array.

    Returns:
        Dense numpy array.
    """
    if isinstance(decomposed, np.ndarray):
        return decomposed
    elif isinstance(decomposed, TuckerDecomposition):
        return decomposed.reconstruct()
    elif isinstance(decomposed, TensorTrainDecomposition):
        return decomposed.reconstruct()
    elif isinstance(decomposed, HierarchicalSparseTensor):
        return decomposed.to_dense()
    else:
        raise TypeError(f"Unknown decomposition type: {type(decomposed)}")
