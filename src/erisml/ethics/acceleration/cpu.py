# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
CPU Acceleration Backend using NumPy and SciPy.

DEME V3 Sprint 11: Optimized CPU backend for tensor operations.
Uses NumPy for dense operations and SciPy for sparse tensor operations.

Features:
- SIMD-accelerated operations via NumPy's optimized BLAS/LAPACK
- Sparse tensor support via SciPy's sparse module
- Memory-efficient operations with in-place modifications where safe
- Thread-safe for parallel execution

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

import platform
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import scipy.sparse as sp
    from scipy.linalg import norm as scipy_norm

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from .backend import (
    AccelerationBackend,
    DeviceInfo,
    DeviceType,
    TensorHandle,
)


# Numerical stability constant
EPSILON = 1e-10


class CPUBackend(AccelerationBackend):
    """
    CPU-based acceleration backend using NumPy and SciPy.

    This is the default backend that is always available. It provides
    optimized tensor operations using:

    - NumPy for dense tensor operations (leverages BLAS/LAPACK)
    - SciPy for sparse tensor operations (optional)
    - SIMD acceleration through NumPy's vectorized operations

    The backend is thread-safe and can be used in parallel execution
    contexts.
    """

    def __init__(self, use_scipy_sparse: bool = True):
        """
        Initialize the CPU backend.

        Args:
            use_scipy_sparse: Whether to use SciPy for sparse operations
                            (falls back to dense if SciPy not available).
        """
        self._use_scipy_sparse = use_scipy_sparse and HAS_SCIPY
        self._device_info: Optional[DeviceInfo] = None

    @property
    def name(self) -> str:
        return "cpu"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.CPU

    def is_available(self) -> bool:
        """CPU backend is always available."""
        return True

    def get_device_info(self, device_id: int = 0) -> DeviceInfo:
        """
        Get CPU information.

        Note: Memory info is approximate and may not reflect actual
        available system memory.
        """
        if self._device_info is None:
            try:
                import psutil

                mem = psutil.virtual_memory()
                memory_total = mem.total
                memory_available = mem.available
            except ImportError:
                memory_total = 0
                memory_available = 0

            # Get CPU info
            try:
                cpu_name = platform.processor() or "Unknown CPU"
            except Exception:
                cpu_name = "Unknown CPU"

            properties: Dict[str, Any] = {
                "numpy_version": np.__version__,
                "scipy_available": HAS_SCIPY,
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            }

            if HAS_SCIPY:
                import scipy

                properties["scipy_version"] = scipy.__version__

            # Check for BLAS info
            try:
                blas_info = np.show_config(mode="dicts")
                if isinstance(blas_info, dict) and "Build Dependencies" in blas_info:
                    properties["blas"] = blas_info.get("Build Dependencies", {}).get(
                        "blas", {}
                    )
            except Exception:
                pass

            self._device_info = DeviceInfo(
                device_type=DeviceType.CPU,
                device_id=0,
                name=cpu_name,
                memory_total=memory_total,
                memory_available=memory_available,
                compute_capability=None,
                is_available=True,
                properties=properties,
            )

        return self._device_info

    def get_all_devices(self) -> List[DeviceInfo]:
        """Return single CPU device."""
        return [self.get_device_info(0)]

    # -------------------------------------------------------------------------
    # Tensor Creation
    # -------------------------------------------------------------------------

    def from_numpy(
        self,
        array: np.ndarray,
        device_id: int = 0,
    ) -> TensorHandle:
        """Create a tensor handle from a NumPy array (zero-copy on CPU)."""
        # Ensure float64 array, preserving shape (including 0-d scalars)
        arr = np.asarray(array, dtype=np.float64)
        if arr.ndim > 0:
            arr = np.ascontiguousarray(arr)
        return TensorHandle(
            backend_name=self.name,
            device_type=self.device_type,
            device_id=device_id,
            shape=arr.shape,
            dtype="float64",
            _native_tensor=arr,
            is_sparse=False,
        )

    def to_numpy(self, handle: TensorHandle) -> np.ndarray:
        """Return the underlying NumPy array."""
        if handle._native_tensor is None:
            raise ValueError("TensorHandle has no underlying tensor")
        return np.asarray(handle._native_tensor)

    def zeros(
        self,
        shape: Tuple[int, ...],
        dtype: str = "float64",
        device_id: int = 0,
    ) -> TensorHandle:
        """Create a zero-filled tensor."""
        arr = np.zeros(shape, dtype=np.dtype(dtype))
        return TensorHandle(
            backend_name=self.name,
            device_type=self.device_type,
            device_id=device_id,
            shape=shape,
            dtype=dtype,
            _native_tensor=arr,
            is_sparse=False,
        )

    def ones(
        self,
        shape: Tuple[int, ...],
        dtype: str = "float64",
        device_id: int = 0,
    ) -> TensorHandle:
        """Create a one-filled tensor."""
        arr = np.ones(shape, dtype=np.dtype(dtype))
        return TensorHandle(
            backend_name=self.name,
            device_type=self.device_type,
            device_id=device_id,
            shape=shape,
            dtype=dtype,
            _native_tensor=arr,
            is_sparse=False,
        )

    def full(
        self,
        shape: Tuple[int, ...],
        fill_value: float,
        dtype: str = "float64",
        device_id: int = 0,
    ) -> TensorHandle:
        """Create a tensor filled with a constant value."""
        arr = np.full(shape, fill_value, dtype=np.dtype(dtype))
        return TensorHandle(
            backend_name=self.name,
            device_type=self.device_type,
            device_id=device_id,
            shape=shape,
            dtype=dtype,
            _native_tensor=arr,
            is_sparse=False,
        )

    # -------------------------------------------------------------------------
    # Element-wise Operations
    # -------------------------------------------------------------------------

    def _get_tensor(self, handle: TensorHandle) -> np.ndarray:
        """Extract numpy array from handle."""
        return self.to_numpy(handle)

    def _wrap_result(
        self,
        result: np.ndarray,
        device_id: int = 0,
    ) -> TensorHandle:
        """Wrap numpy array result in a TensorHandle."""
        return TensorHandle(
            backend_name=self.name,
            device_type=self.device_type,
            device_id=device_id,
            shape=result.shape,
            dtype=str(result.dtype),
            _native_tensor=result,
            is_sparse=False,
        )

    def add(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """Element-wise addition."""
        a_arr = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            b_arr = self._get_tensor(b)
            result = np.add(a_arr, b_arr)
        else:
            result = np.add(a_arr, b)
        return self._wrap_result(result, a.device_id)

    def subtract(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """Element-wise subtraction."""
        a_arr = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            b_arr = self._get_tensor(b)
            result = np.subtract(a_arr, b_arr)
        else:
            result = np.subtract(a_arr, b)
        return self._wrap_result(result, a.device_id)

    def multiply(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """Element-wise multiplication."""
        a_arr = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            b_arr = self._get_tensor(b)
            result = np.multiply(a_arr, b_arr)
        else:
            result = np.multiply(a_arr, b)
        return self._wrap_result(result, a.device_id)

    def divide(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
        safe: bool = True,
    ) -> TensorHandle:
        """Element-wise division with optional safe handling."""
        a_arr = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            b_arr = self._get_tensor(b)
            if safe:
                with np.errstate(divide="ignore", invalid="ignore"):
                    result = np.where(
                        np.abs(b_arr) < EPSILON,
                        1.0,  # Division by zero yields 1.0 for ethics
                        a_arr / b_arr,
                    )
            else:
                result = np.divide(a_arr, b_arr)
        else:
            if safe and abs(b) < EPSILON:
                result = np.ones_like(a_arr)
            else:
                result = np.divide(a_arr, b)
        return self._wrap_result(result, a.device_id)

    def clip(
        self,
        a: TensorHandle,
        min_val: float,
        max_val: float,
    ) -> TensorHandle:
        """Clip tensor values to a range."""
        a_arr = self._get_tensor(a)
        result = np.clip(a_arr, min_val, max_val)
        return self._wrap_result(result, a.device_id)

    def abs(self, a: TensorHandle) -> TensorHandle:
        """Element-wise absolute value."""
        result = np.abs(self._get_tensor(a))
        return self._wrap_result(result, a.device_id)

    def sqrt(self, a: TensorHandle) -> TensorHandle:
        """Element-wise square root."""
        result = np.sqrt(self._get_tensor(a))
        return self._wrap_result(result, a.device_id)

    def exp(self, a: TensorHandle) -> TensorHandle:
        """Element-wise exponential."""
        result = np.exp(self._get_tensor(a))
        return self._wrap_result(result, a.device_id)

    def log(self, a: TensorHandle, safe: bool = True) -> TensorHandle:
        """Element-wise natural logarithm."""
        a_arr = self._get_tensor(a)
        if safe:
            # Clamp to avoid log(0)
            a_arr = np.clip(a_arr, EPSILON, None)
        result = np.log(a_arr)
        return self._wrap_result(result, a.device_id)

    # -------------------------------------------------------------------------
    # Reduction Operations
    # -------------------------------------------------------------------------

    def sum(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Sum reduction along an axis."""
        result = np.sum(self._get_tensor(a), axis=axis, keepdims=keepdims)
        if isinstance(result, np.ndarray):
            return self._wrap_result(result, a.device_id)
        else:
            # Scalar result
            return self._wrap_result(np.array(result), a.device_id)

    def mean(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Mean reduction along an axis."""
        result = np.mean(self._get_tensor(a), axis=axis, keepdims=keepdims)
        if isinstance(result, np.ndarray):
            return self._wrap_result(result, a.device_id)
        else:
            return self._wrap_result(np.array(result), a.device_id)

    def min(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Minimum reduction along an axis."""
        result = np.min(self._get_tensor(a), axis=axis, keepdims=keepdims)
        if isinstance(result, np.ndarray):
            return self._wrap_result(result, a.device_id)
        else:
            return self._wrap_result(np.array(result), a.device_id)

    def max(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Maximum reduction along an axis."""
        result = np.max(self._get_tensor(a), axis=axis, keepdims=keepdims)
        if isinstance(result, np.ndarray):
            return self._wrap_result(result, a.device_id)
        else:
            return self._wrap_result(np.array(result), a.device_id)

    def argmin(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Index of minimum along an axis."""
        result = np.argmin(self._get_tensor(a), axis=axis)
        if isinstance(result, np.ndarray):
            return self._wrap_result(result.astype(np.int64), a.device_id)
        else:
            return self._wrap_result(np.array(result, dtype=np.int64), a.device_id)

    def argmax(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Index of maximum along an axis."""
        result = np.argmax(self._get_tensor(a), axis=axis)
        if isinstance(result, np.ndarray):
            return self._wrap_result(result.astype(np.int64), a.device_id)
        else:
            return self._wrap_result(np.array(result, dtype=np.int64), a.device_id)

    # -------------------------------------------------------------------------
    # Linear Algebra Operations
    # -------------------------------------------------------------------------

    def dot(self, a: TensorHandle, b: TensorHandle) -> TensorHandle:
        """Dot product of two tensors."""
        result = np.dot(self._get_tensor(a), self._get_tensor(b))
        return self._wrap_result(np.atleast_1d(result), a.device_id)

    def tensordot(
        self,
        a: TensorHandle,
        b: TensorHandle,
        axes: Union[int, Tuple[List[int], List[int]]],
    ) -> TensorHandle:
        """Tensor contraction."""
        result = np.tensordot(self._get_tensor(a), self._get_tensor(b), axes=axes)
        return self._wrap_result(result, a.device_id)

    def norm(
        self,
        a: TensorHandle,
        ord: Optional[Union[int, float, str]] = None,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Compute tensor norm."""
        a_arr = self._get_tensor(a)

        if HAS_SCIPY and axis is None:
            # Use scipy for full tensor norm (more accurate)
            result = scipy_norm(a_arr.ravel(), ord=ord)
            return self._wrap_result(np.array([result]), a.device_id)
        else:
            result = np.linalg.norm(a_arr, ord=ord, axis=axis)
            if isinstance(result, np.ndarray):
                return self._wrap_result(result, a.device_id)
            else:
                return self._wrap_result(np.array([result]), a.device_id)

    # -------------------------------------------------------------------------
    # Shape Operations
    # -------------------------------------------------------------------------

    def reshape(
        self,
        a: TensorHandle,
        shape: Tuple[int, ...],
    ) -> TensorHandle:
        """Reshape tensor."""
        result = np.reshape(self._get_tensor(a), shape)
        return self._wrap_result(result, a.device_id)

    def transpose(
        self,
        a: TensorHandle,
        axes: Optional[Tuple[int, ...]] = None,
    ) -> TensorHandle:
        """Transpose tensor."""
        result = np.transpose(self._get_tensor(a), axes=axes)
        return self._wrap_result(result, a.device_id)

    def expand_dims(
        self,
        a: TensorHandle,
        axis: int,
    ) -> TensorHandle:
        """Insert a new axis."""
        result = np.expand_dims(self._get_tensor(a), axis=axis)
        return self._wrap_result(result, a.device_id)

    def squeeze(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Remove single-dimensional entries from shape."""
        result = np.squeeze(self._get_tensor(a), axis=axis)
        return self._wrap_result(result, a.device_id)

    def broadcast_to(
        self,
        a: TensorHandle,
        shape: Tuple[int, ...],
    ) -> TensorHandle:
        """Broadcast tensor to a new shape."""
        result = np.broadcast_to(self._get_tensor(a), shape).copy()
        return self._wrap_result(result, a.device_id)

    # -------------------------------------------------------------------------
    # Concatenation and Stacking
    # -------------------------------------------------------------------------

    def concatenate(
        self,
        tensors: List[TensorHandle],
        axis: int = 0,
    ) -> TensorHandle:
        """Concatenate tensors along an axis."""
        arrays = [self._get_tensor(t) for t in tensors]
        result = np.concatenate(arrays, axis=axis)
        device_id = tensors[0].device_id if tensors else 0
        return self._wrap_result(result, device_id)

    def stack(
        self,
        tensors: List[TensorHandle],
        axis: int = 0,
    ) -> TensorHandle:
        """Stack tensors along a new axis."""
        arrays = [self._get_tensor(t) for t in tensors]
        result = np.stack(arrays, axis=axis)
        device_id = tensors[0].device_id if tensors else 0
        return self._wrap_result(result, device_id)

    # -------------------------------------------------------------------------
    # Sparse Operations (SciPy optimized)
    # -------------------------------------------------------------------------

    def to_sparse_coo(
        self,
        a: TensorHandle,
        fill_value: float = 0.0,
    ) -> Tuple[TensorHandle, TensorHandle, Tuple[int, ...]]:
        """Convert dense tensor to sparse COO format."""
        data = self._get_tensor(a)
        shape = data.shape

        if self._use_scipy_sparse and len(shape) == 2:
            # Use SciPy for 2D sparse (optimized)
            if fill_value == 0.0:
                sparse_mat = sp.coo_matrix(data)
            else:
                sparse_mat = sp.coo_matrix(data - fill_value)
                sparse_mat.data += fill_value

            coords = np.column_stack([sparse_mat.row, sparse_mat.col]).astype(np.int32)
            values = sparse_mat.data.astype(np.float64)
        else:
            # General N-D sparse conversion
            if fill_value == 0.0:
                mask = np.abs(data) > EPSILON
            else:
                mask = np.abs(data - fill_value) > EPSILON

            coords = np.argwhere(mask).astype(np.int32)
            values = data[mask].astype(np.float64)

        return (
            self.from_numpy(coords, a.device_id),
            self.from_numpy(values, a.device_id),
            shape,
        )

    def from_sparse_coo(
        self,
        coords: TensorHandle,
        values: TensorHandle,
        shape: Tuple[int, ...],
        fill_value: float = 0.0,
    ) -> TensorHandle:
        """Convert sparse COO format to dense tensor."""
        coords_np = self._get_tensor(coords)
        values_np = self._get_tensor(values)

        # Ensure coordinates are integers for indexing
        coords_int = coords_np.astype(np.int64)

        if self._use_scipy_sparse and len(shape) == 2 and len(coords_int) > 0:
            # Use SciPy for 2D sparse (optimized)
            sparse_mat = sp.coo_matrix(
                (values_np, (coords_int[:, 0], coords_int[:, 1])),
                shape=shape,
            )
            dense = sparse_mat.toarray().astype(np.float64)
            if fill_value != 0.0:
                # Add fill value to zero entries
                dense = np.where(dense == 0.0, fill_value, dense)
        else:
            # General N-D sparse conversion
            dense = np.full(shape, fill_value, dtype=np.float64)
            if len(coords_int) > 0:
                idx = tuple(coords_int[:, i] for i in range(len(shape)))
                dense[idx] = values_np

        return self.from_numpy(dense, coords.device_id)

    def sparse_matmul(
        self,
        coords_a: TensorHandle,
        values_a: TensorHandle,
        shape_a: Tuple[int, int],
        b: TensorHandle,
    ) -> TensorHandle:
        """
        Sparse matrix-dense matrix multiplication.

        Optimized for cases where one operand is sparse. Uses SciPy's
        sparse BLAS routines when available.

        Args:
            coords_a: Sparse COO coordinates for matrix A.
            values_a: Sparse COO values for matrix A.
            shape_a: Shape of sparse matrix A.
            b: Dense matrix B.

        Returns:
            TensorHandle for the dense result.
        """
        coords_np = self._get_tensor(coords_a)
        values_np = self._get_tensor(values_a)
        b_np = self._get_tensor(b)

        # Ensure coordinates are integers for indexing
        coords_int = coords_np.astype(np.int64)

        if self._use_scipy_sparse and len(coords_int) > 0:
            # Create SciPy sparse matrix
            sparse_a = sp.csr_matrix(
                (values_np, (coords_int[:, 0], coords_int[:, 1])),
                shape=shape_a,
            )
            # Sparse-dense multiplication (SciPy optimized)
            result = sparse_a.dot(b_np)
        else:
            # Fall back to dense multiplication
            dense_a = np.zeros(shape_a, dtype=np.float64)
            if len(coords_int) > 0:
                idx = (coords_int[:, 0], coords_int[:, 1])
                dense_a[idx] = values_np
            result = np.dot(dense_a, b_np)

        return self.from_numpy(result, b.device_id)

    # -------------------------------------------------------------------------
    # Advanced Operations (Optimized)
    # -------------------------------------------------------------------------

    def sort(
        self,
        a: TensorHandle,
        axis: int = -1,
    ) -> TensorHandle:
        """Sort tensor along an axis (uses NumPy's optimized sort)."""
        result = np.sort(self._get_tensor(a), axis=axis)
        return self._wrap_result(result, a.device_id)

    def argsort(
        self,
        a: TensorHandle,
        axis: int = -1,
    ) -> TensorHandle:
        """Indices that would sort a tensor."""
        result = np.argsort(self._get_tensor(a), axis=axis)
        return self._wrap_result(result.astype(np.int64), a.device_id)

    def where(
        self,
        condition: TensorHandle,
        x: TensorHandle,
        y: TensorHandle,
    ) -> TensorHandle:
        """Select elements from x or y based on condition."""
        cond_np = self._get_tensor(condition)
        x_np = self._get_tensor(x)
        y_np = self._get_tensor(y)
        result = np.where(cond_np, x_np, y_np)
        return self._wrap_result(result, x.device_id)

    def einsum(
        self,
        subscripts: str,
        *operands: TensorHandle,
    ) -> TensorHandle:
        """
        Einstein summation convention.

        Optimized for common ethics tensor operations like contraction
        and weighted aggregation.

        Args:
            subscripts: Einstein notation string.
            operands: Input tensor handles.

        Returns:
            TensorHandle for the result.
        """
        arrays = [self._get_tensor(op) for op in operands]
        result = np.einsum(subscripts, *arrays, optimize=True)
        device_id = operands[0].device_id if operands else 0
        return self._wrap_result(result, device_id)

    # -------------------------------------------------------------------------
    # Ethics-Specific Optimizations
    # -------------------------------------------------------------------------

    def moral_contraction(
        self,
        tensor: TensorHandle,
        weights: TensorHandle,
        axis: int,
        normalize: bool = True,
    ) -> TensorHandle:
        """
        Optimized moral tensor contraction.

        This is a weighted reduction commonly used in DEME governance
        to aggregate ethical assessments.

        Args:
            tensor: Input moral tensor.
            weights: Weight vector for the contraction axis.
            axis: Axis to contract.
            normalize: Whether to normalize weights.

        Returns:
            TensorHandle for the contracted tensor.
        """
        t_arr = self._get_tensor(tensor)
        w_arr = self._get_tensor(weights)

        if normalize:
            w_sum = w_arr.sum()
            if w_sum > EPSILON:
                w_arr = w_arr / w_sum
            else:
                w_arr = np.ones_like(w_arr) / len(w_arr)

        # Use tensordot for efficient contraction
        result = np.tensordot(t_arr, w_arr, axes=([axis], [0]))

        # Clamp to [0, 1] for ethics validity
        result = np.clip(result, 0.0, 1.0)

        return self._wrap_result(result, tensor.device_id)

    def batch_gini(self, values: TensorHandle, axis: int = -1) -> TensorHandle:
        """
        Batched Gini coefficient computation.

        Computes Gini coefficient along the specified axis for each
        slice, optimized for fairness metrics on moral tensors.

        Args:
            values: Input tensor with values to compute Gini for.
            axis: Axis along which to compute Gini.

        Returns:
            TensorHandle with Gini coefficients (reduced along axis).
        """
        v = self._get_tensor(values)

        # Move target axis to last position
        v = np.moveaxis(v, axis, -1)
        original_shape = v.shape[:-1]
        n = v.shape[-1]

        if n <= 1:
            # Gini is 0 for 0 or 1 element
            return self._wrap_result(
                np.zeros(original_shape, dtype=np.float64), values.device_id
            )

        # Flatten batch dimensions
        batch_size = int(np.prod(original_shape)) if original_shape else 1
        v_flat = v.reshape(batch_size, n)

        # Sort each row
        v_sorted = np.sort(v_flat, axis=1)

        # Compute Gini for each row
        indices = np.arange(1, n + 1)
        gini = (
            2 * np.sum(indices * v_sorted, axis=1) - (n + 1) * np.sum(v_sorted, axis=1)
        ) / (n * np.sum(v_sorted, axis=1) + EPSILON)

        # Handle edge cases (all zeros)
        gini = np.where(np.sum(v_sorted, axis=1) < EPSILON, 0.0, gini)

        # Reshape back
        if original_shape:
            gini = gini.reshape(original_shape)

        return self._wrap_result(gini, values.device_id)


# Create a default CPU backend instance
_default_cpu_backend: Optional[CPUBackend] = None


def get_cpu_backend() -> CPUBackend:
    """Get the default CPU backend instance."""
    global _default_cpu_backend
    if _default_cpu_backend is None:
        _default_cpu_backend = CPUBackend()
    return _default_cpu_backend


__all__ = [
    "CPUBackend",
    "get_cpu_backend",
    "HAS_SCIPY",
    "EPSILON",
]
