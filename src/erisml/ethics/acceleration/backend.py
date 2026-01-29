# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Acceleration Backend Abstract Interface.

DEME V3 Sprint 11: Provides an abstract interface for tensor acceleration
backends. This allows seamless switching between CPU (NumPy/SciPy), CUDA
(CuPy), and edge devices (Jetson/TensorRT) without changing application code.

The design follows a Strategy pattern where the AccelerationDispatcher
selects the appropriate backend based on hardware availability and user
configuration.

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class DeviceType(Enum):
    """Supported device types for acceleration."""

    CPU = "cpu"
    CUDA = "cuda"
    JETSON = "jetson"
    TPU = "tpu"  # Future support
    MLX = "mlx"  # Apple Silicon


@dataclass(frozen=True)
class DeviceInfo:
    """Information about an acceleration device."""

    device_type: DeviceType
    """Type of the device."""

    device_id: int = 0
    """Device ID (for multi-GPU systems)."""

    name: str = ""
    """Human-readable device name."""

    memory_total: int = 0
    """Total memory in bytes (0 if unknown)."""

    memory_available: int = 0
    """Available memory in bytes (0 if unknown)."""

    compute_capability: Optional[Tuple[int, int]] = None
    """CUDA compute capability (major, minor) if applicable."""

    is_available: bool = True
    """Whether the device is currently available."""

    properties: Dict[str, Any] = field(default_factory=dict)
    """Additional device-specific properties."""


@dataclass
class TensorHandle:
    """
    Opaque handle to a tensor on an acceleration device.

    This abstraction allows backends to manage device-specific tensor
    representations without exposing implementation details.
    """

    backend_name: str
    """Name of the backend that owns this tensor."""

    device_type: DeviceType
    """Device type where the tensor resides."""

    device_id: int = 0
    """Device ID for multi-device systems."""

    shape: Tuple[int, ...] = ()
    """Tensor shape."""

    dtype: str = "float64"
    """Data type string (numpy-compatible)."""

    _native_tensor: Any = None
    """Backend-specific tensor object (CuPy array, etc.)."""

    is_sparse: bool = False
    """Whether the tensor is in sparse format."""

    def __repr__(self) -> str:
        return (
            f"TensorHandle({self.backend_name}, {self.device_type.value}, "
            f"shape={self.shape}, dtype={self.dtype})"
        )


class AccelerationBackend(ABC):
    """
    Abstract base class for acceleration backends.

    Each backend implements tensor operations optimized for its target
    hardware. The interface is designed to be NumPy-compatible where
    possible for ease of use.

    Subclasses must implement all abstract methods. Optional methods
    have default implementations that may be overridden for optimization.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name (e.g., 'cpu', 'cuda', 'jetson')."""
        ...

    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        """Primary device type for this backend."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on the current system."""
        ...

    @abstractmethod
    def get_device_info(self, device_id: int = 0) -> DeviceInfo:
        """
        Get information about a specific device.

        Args:
            device_id: Device ID (default 0 for single-device systems).

        Returns:
            DeviceInfo with device capabilities and status.
        """
        ...

    def get_all_devices(self) -> List[DeviceInfo]:
        """
        Get information about all available devices.

        Returns:
            List of DeviceInfo for all available devices.
        """
        return [self.get_device_info(0)]

    # -------------------------------------------------------------------------
    # Tensor Creation
    # -------------------------------------------------------------------------

    @abstractmethod
    def from_numpy(
        self,
        array: np.ndarray,
        device_id: int = 0,
    ) -> TensorHandle:
        """
        Create a tensor from a NumPy array.

        Args:
            array: NumPy array to copy to device.
            device_id: Target device ID.

        Returns:
            TensorHandle referencing the device tensor.
        """
        ...

    @abstractmethod
    def to_numpy(self, handle: TensorHandle) -> np.ndarray:
        """
        Copy a tensor back to a NumPy array.

        Args:
            handle: TensorHandle to copy from device.

        Returns:
            NumPy array with tensor data.
        """
        ...

    @abstractmethod
    def zeros(
        self,
        shape: Tuple[int, ...],
        dtype: str = "float64",
        device_id: int = 0,
    ) -> TensorHandle:
        """
        Create a tensor filled with zeros.

        Args:
            shape: Tensor shape.
            dtype: Data type string.
            device_id: Target device ID.

        Returns:
            TensorHandle for the zero tensor.
        """
        ...

    @abstractmethod
    def ones(
        self,
        shape: Tuple[int, ...],
        dtype: str = "float64",
        device_id: int = 0,
    ) -> TensorHandle:
        """
        Create a tensor filled with ones.

        Args:
            shape: Tensor shape.
            dtype: Data type string.
            device_id: Target device ID.

        Returns:
            TensorHandle for the ones tensor.
        """
        ...

    @abstractmethod
    def full(
        self,
        shape: Tuple[int, ...],
        fill_value: float,
        dtype: str = "float64",
        device_id: int = 0,
    ) -> TensorHandle:
        """
        Create a tensor filled with a constant value.

        Args:
            shape: Tensor shape.
            fill_value: Value to fill the tensor with.
            dtype: Data type string.
            device_id: Target device ID.

        Returns:
            TensorHandle for the filled tensor.
        """
        ...

    # -------------------------------------------------------------------------
    # Element-wise Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def add(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """
        Element-wise addition.

        Args:
            a: First tensor.
            b: Second tensor or scalar.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def subtract(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """
        Element-wise subtraction.

        Args:
            a: First tensor.
            b: Second tensor or scalar.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def multiply(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """
        Element-wise multiplication.

        Args:
            a: First tensor.
            b: Second tensor or scalar.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def divide(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
        safe: bool = True,
    ) -> TensorHandle:
        """
        Element-wise division.

        Args:
            a: Numerator tensor.
            b: Denominator tensor or scalar.
            safe: If True, handle division by zero gracefully.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def clip(
        self,
        a: TensorHandle,
        min_val: float,
        max_val: float,
    ) -> TensorHandle:
        """
        Clip tensor values to a range.

        Args:
            a: Input tensor.
            min_val: Minimum value.
            max_val: Maximum value.

        Returns:
            TensorHandle for the clipped tensor.
        """
        ...

    @abstractmethod
    def abs(self, a: TensorHandle) -> TensorHandle:
        """
        Element-wise absolute value.

        Args:
            a: Input tensor.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def sqrt(self, a: TensorHandle) -> TensorHandle:
        """
        Element-wise square root.

        Args:
            a: Input tensor.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def exp(self, a: TensorHandle) -> TensorHandle:
        """
        Element-wise exponential.

        Args:
            a: Input tensor.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def log(self, a: TensorHandle, safe: bool = True) -> TensorHandle:
        """
        Element-wise natural logarithm.

        Args:
            a: Input tensor.
            safe: If True, handle log(0) gracefully.

        Returns:
            TensorHandle for the result.
        """
        ...

    # -------------------------------------------------------------------------
    # Reduction Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def sum(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """
        Sum reduction along an axis.

        Args:
            a: Input tensor.
            axis: Axis to reduce (None for all).
            keepdims: Whether to keep the reduced dimension.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def mean(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """
        Mean reduction along an axis.

        Args:
            a: Input tensor.
            axis: Axis to reduce (None for all).
            keepdims: Whether to keep the reduced dimension.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def min(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """
        Minimum reduction along an axis.

        Args:
            a: Input tensor.
            axis: Axis to reduce (None for all).
            keepdims: Whether to keep the reduced dimension.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def max(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """
        Maximum reduction along an axis.

        Args:
            a: Input tensor.
            axis: Axis to reduce (None for all).
            keepdims: Whether to keep the reduced dimension.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def argmin(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """
        Index of minimum along an axis.

        Args:
            a: Input tensor.
            axis: Axis to reduce (None for flattened).

        Returns:
            TensorHandle for the indices.
        """
        ...

    @abstractmethod
    def argmax(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """
        Index of maximum along an axis.

        Args:
            a: Input tensor.
            axis: Axis to reduce (None for flattened).

        Returns:
            TensorHandle for the indices.
        """
        ...

    # -------------------------------------------------------------------------
    # Linear Algebra Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def dot(self, a: TensorHandle, b: TensorHandle) -> TensorHandle:
        """
        Dot product of two tensors.

        Args:
            a: First tensor.
            b: Second tensor.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def tensordot(
        self,
        a: TensorHandle,
        b: TensorHandle,
        axes: Union[int, Tuple[List[int], List[int]]],
    ) -> TensorHandle:
        """
        Tensor contraction.

        Args:
            a: First tensor.
            b: Second tensor.
            axes: Axes to contract.

        Returns:
            TensorHandle for the result.
        """
        ...

    @abstractmethod
    def norm(
        self,
        a: TensorHandle,
        ord: Optional[Union[int, float, str]] = None,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """
        Compute tensor norm.

        Args:
            a: Input tensor.
            ord: Norm order (None for Frobenius).
            axis: Axis along which to compute (None for all).

        Returns:
            TensorHandle for the norm value(s).
        """
        ...

    # -------------------------------------------------------------------------
    # Shape Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def reshape(
        self,
        a: TensorHandle,
        shape: Tuple[int, ...],
    ) -> TensorHandle:
        """
        Reshape tensor.

        Args:
            a: Input tensor.
            shape: New shape.

        Returns:
            TensorHandle for the reshaped tensor.
        """
        ...

    @abstractmethod
    def transpose(
        self,
        a: TensorHandle,
        axes: Optional[Tuple[int, ...]] = None,
    ) -> TensorHandle:
        """
        Transpose tensor.

        Args:
            a: Input tensor.
            axes: Permutation of axes (None for reverse).

        Returns:
            TensorHandle for the transposed tensor.
        """
        ...

    @abstractmethod
    def expand_dims(
        self,
        a: TensorHandle,
        axis: int,
    ) -> TensorHandle:
        """
        Insert a new axis.

        Args:
            a: Input tensor.
            axis: Position for the new axis.

        Returns:
            TensorHandle for the expanded tensor.
        """
        ...

    @abstractmethod
    def squeeze(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """
        Remove single-dimensional entries from shape.

        Args:
            a: Input tensor.
            axis: Axis to squeeze (None for all).

        Returns:
            TensorHandle for the squeezed tensor.
        """
        ...

    @abstractmethod
    def broadcast_to(
        self,
        a: TensorHandle,
        shape: Tuple[int, ...],
    ) -> TensorHandle:
        """
        Broadcast tensor to a new shape.

        Args:
            a: Input tensor.
            shape: Target shape.

        Returns:
            TensorHandle for the broadcast tensor.
        """
        ...

    # -------------------------------------------------------------------------
    # Concatenation and Stacking
    # -------------------------------------------------------------------------

    @abstractmethod
    def concatenate(
        self,
        tensors: List[TensorHandle],
        axis: int = 0,
    ) -> TensorHandle:
        """
        Concatenate tensors along an axis.

        Args:
            tensors: List of tensors to concatenate.
            axis: Axis along which to concatenate.

        Returns:
            TensorHandle for the concatenated tensor.
        """
        ...

    @abstractmethod
    def stack(
        self,
        tensors: List[TensorHandle],
        axis: int = 0,
    ) -> TensorHandle:
        """
        Stack tensors along a new axis.

        Args:
            tensors: List of tensors to stack.
            axis: Position for the new axis.

        Returns:
            TensorHandle for the stacked tensor.
        """
        ...

    # -------------------------------------------------------------------------
    # Sparse Operations
    # -------------------------------------------------------------------------

    def to_sparse_coo(
        self,
        a: TensorHandle,
        fill_value: float = 0.0,
    ) -> Tuple[TensorHandle, TensorHandle, Tuple[int, ...]]:
        """
        Convert dense tensor to sparse COO format.

        Args:
            a: Dense input tensor.
            fill_value: Value to treat as sparse.

        Returns:
            Tuple of (coords, values, shape).
        """
        # Default implementation falls back to NumPy
        data = self.to_numpy(a)
        mask = np.abs(data - fill_value) > 1e-10
        coords = np.argwhere(mask).astype(np.int32)
        values = data[mask]
        return (
            self.from_numpy(coords, a.device_id),
            self.from_numpy(values, a.device_id),
            data.shape,
        )

    def from_sparse_coo(
        self,
        coords: TensorHandle,
        values: TensorHandle,
        shape: Tuple[int, ...],
        fill_value: float = 0.0,
    ) -> TensorHandle:
        """
        Convert sparse COO format to dense tensor.

        Args:
            coords: Coordinate tensor (nnz, rank).
            values: Values tensor (nnz,).
            shape: Dense tensor shape.
            fill_value: Fill value for unspecified entries.

        Returns:
            TensorHandle for the dense tensor.
        """
        # Default implementation falls back to NumPy
        coords_np = self.to_numpy(coords)
        values_np = self.to_numpy(values)
        dense = np.full(shape, fill_value, dtype=np.float64)
        if len(coords_np) > 0:
            idx = tuple(coords_np[:, i] for i in range(len(shape)))
            dense[idx] = values_np
        return self.from_numpy(dense, coords.device_id)

    # -------------------------------------------------------------------------
    # Advanced Operations (Optional Overrides)
    # -------------------------------------------------------------------------

    def sort(
        self,
        a: TensorHandle,
        axis: int = -1,
    ) -> TensorHandle:
        """
        Sort tensor along an axis.

        Args:
            a: Input tensor.
            axis: Axis to sort along.

        Returns:
            TensorHandle for the sorted tensor.
        """
        data = self.to_numpy(a)
        result = np.sort(data, axis=axis)
        return self.from_numpy(result, a.device_id)

    def argsort(
        self,
        a: TensorHandle,
        axis: int = -1,
    ) -> TensorHandle:
        """
        Indices that would sort a tensor.

        Args:
            a: Input tensor.
            axis: Axis to sort along.

        Returns:
            TensorHandle for the sort indices.
        """
        data = self.to_numpy(a)
        result = np.argsort(data, axis=axis)
        return self.from_numpy(result.astype(np.int64), a.device_id)

    def where(
        self,
        condition: TensorHandle,
        x: TensorHandle,
        y: TensorHandle,
    ) -> TensorHandle:
        """
        Select elements from x or y based on condition.

        Args:
            condition: Boolean condition tensor.
            x: Values where condition is True.
            y: Values where condition is False.

        Returns:
            TensorHandle for the result.
        """
        cond_np = self.to_numpy(condition)
        x_np = self.to_numpy(x)
        y_np = self.to_numpy(y)
        result = np.where(cond_np, x_np, y_np)
        return self.from_numpy(result, x.device_id)

    # -------------------------------------------------------------------------
    # Memory Management
    # -------------------------------------------------------------------------

    def synchronize(self, device_id: int = 0) -> None:
        """
        Synchronize device operations.

        For GPU backends, this waits for all pending operations to complete.
        CPU backends typically don't need this.

        Args:
            device_id: Device to synchronize.
        """
        pass  # Default: no-op for CPU

    def get_memory_info(self, device_id: int = 0) -> Tuple[int, int]:
        """
        Get device memory information.

        Args:
            device_id: Device to query.

        Returns:
            Tuple of (used_bytes, total_bytes).
        """
        return (0, 0)  # Default: unknown

    def clear_cache(self, device_id: int = 0) -> None:
        """
        Clear any cached memory on the device.

        Args:
            device_id: Device to clear.
        """
        pass  # Default: no-op


__all__ = [
    "DeviceType",
    "DeviceInfo",
    "TensorHandle",
    "AccelerationBackend",
]
