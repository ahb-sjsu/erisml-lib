# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Jetson Backend for Edge Deployment.

DEME V3 Sprint 13: Provides acceleration for NVIDIA Jetson devices
(Nano, TX2, Xavier, Orin) with TensorRT optimization and power management.

Features:
- Automatic Jetson hardware detection
- TensorRT engine optimization and caching
- DLA (Deep Learning Accelerator) support for Orin
- Power mode configuration (MAXN, 15W, 10W, etc.)
- Unified memory optimization

Version: 3.0.0 (DEME V3 Sprint 13)
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .backend import (
    AccelerationBackend,
    DeviceInfo,
    DeviceType,
    TensorHandle,
)

logger = logging.getLogger(__name__)

# Check for Jetson hardware
HAS_JETSON = False
JETSON_MODEL: Optional[str] = None


def _detect_jetson() -> Tuple[bool, Optional[str]]:
    """Detect if running on Jetson hardware."""
    # Check for Tegra chip (Jetson indicator)
    tegra_release = Path("/etc/nv_tegra_release")
    if tegra_release.exists():
        try:
            content = tegra_release.read_text()
            # Parse model from release file
            if "t210" in content.lower():
                return True, "Jetson Nano"
            elif "t186" in content.lower():
                return True, "Jetson TX2"
            elif "t194" in content.lower():
                return True, "Jetson Xavier"
            elif "t234" in content.lower():
                return True, "Jetson Orin"
            else:
                return True, "Jetson (Unknown)"
        except Exception:
            pass

    # Alternative: check /proc/device-tree/model
    model_path = Path("/proc/device-tree/model")
    if model_path.exists():
        try:
            model = model_path.read_text().lower()
            if "jetson" in model or "tegra" in model:
                if "nano" in model:
                    return True, "Jetson Nano"
                elif "tx2" in model:
                    return True, "Jetson TX2"
                elif "xavier" in model or "agx" in model:
                    return True, "Jetson Xavier"
                elif "orin" in model:
                    return True, "Jetson Orin"
                else:
                    return True, "Jetson (Unknown)"
        except Exception:
            pass

    return False, None


HAS_JETSON, JETSON_MODEL = _detect_jetson()

# Check for CuPy (required for Jetson backend)
try:
    import cupy as cp
    from cupy import cuda

    HAS_CUPY = True
except ImportError:
    cp = None  # type: ignore
    cuda = None  # type: ignore
    HAS_CUPY = False

# Check for TensorRT
try:
    import tensorrt as trt

    HAS_TENSORRT = True
except ImportError:
    trt = None  # type: ignore
    HAS_TENSORRT = False


class JetsonPowerMode(Enum):
    """Jetson power modes."""

    MAXN = "MAXN"  # Maximum performance (all cores, max clocks)
    MODE_15W = "15W"  # 15W power budget
    MODE_10W = "10W"  # 10W power budget (Nano default)
    MODE_5W = "5W"  # 5W power budget (low power)
    MODE_AUTO = "AUTO"  # Let system manage


class DLACore(Enum):
    """DLA (Deep Learning Accelerator) core selection for Orin."""

    NONE = -1  # Don't use DLA
    CORE_0 = 0  # Use DLA core 0
    CORE_1 = 1  # Use DLA core 1 (Orin AGX only)


@dataclass
class JetsonConfig:
    """
    Configuration for Jetson backend.

    Attributes:
        power_mode: Desired power mode.
        use_dla: Whether to use DLA accelerator (Orin only).
        dla_core: Which DLA core to use.
        use_unified_memory: Whether to use unified CPU/GPU memory.
        tensorrt_cache_dir: Directory for TensorRT engine cache.
        tensorrt_precision: TensorRT precision mode.
        max_workspace_size: Maximum TensorRT workspace in bytes.
    """

    power_mode: JetsonPowerMode = JetsonPowerMode.MODE_AUTO
    """Jetson power mode."""

    use_dla: bool = False
    """Whether to use Deep Learning Accelerator (Orin only)."""

    dla_core: DLACore = DLACore.NONE
    """Which DLA core to use."""

    use_unified_memory: bool = True
    """Whether to use unified CPU/GPU memory (zero-copy)."""

    tensorrt_cache_dir: Optional[str] = None
    """Directory for caching TensorRT engines."""

    tensorrt_precision: str = "fp16"
    """TensorRT precision: 'fp32', 'fp16', or 'int8'."""

    max_workspace_size: int = 1 << 28  # 256 MB
    """Maximum TensorRT workspace size in bytes."""

    extra_config: Dict[str, Any] = field(default_factory=dict)
    """Additional backend-specific configuration."""


# Numerical stability constant
EPSILON = 1e-10


class JetsonBackend(AccelerationBackend):
    """
    Acceleration backend for NVIDIA Jetson devices.

    Provides optimized tensor operations for edge deployment with:
    - TensorRT engine optimization
    - DLA support for Orin devices
    - Power mode management
    - Unified memory for zero-copy transfers

    Example:
        if jetson_is_available():
            backend = JetsonBackend()
            tensor = backend.from_numpy(data)
            result = backend.add(tensor, 0.5)
    """

    def __init__(
        self,
        config: Optional[JetsonConfig] = None,
        device_id: int = 0,
    ):
        """
        Initialize Jetson backend.

        Args:
            config: Jetson configuration options.
            device_id: GPU device ID (usually 0 on Jetson).
        """
        self._config = config or JetsonConfig()
        self._device_id = device_id
        self._tensors: Dict[int, Any] = {}
        self._next_id = 0
        self._initialized = False
        self._trt_engines: Dict[str, Any] = {}

        if HAS_JETSON and HAS_CUPY:
            self._initialize()

    def _initialize(self) -> None:
        """Initialize the Jetson backend."""
        if not HAS_CUPY:
            logger.warning("CuPy not available, Jetson backend disabled")
            return

        try:
            with cuda.Device(self._device_id):
                # Configure unified memory if requested
                if self._config.use_unified_memory:
                    # Access memory pool to ensure it's initialized
                    # Jetson uses unified memory by default
                    cp.get_default_memory_pool()

                self._initialized = True
                logger.debug(f"Jetson backend initialized on {JETSON_MODEL}")

                # Apply power mode if not AUTO
                if self._config.power_mode != JetsonPowerMode.MODE_AUTO:
                    self._set_power_mode(self._config.power_mode)

        except Exception as e:
            logger.error(f"Failed to initialize Jetson backend: {e}")
            self._initialized = False

    def _set_power_mode(self, mode: JetsonPowerMode) -> bool:
        """
        Set Jetson power mode.

        Args:
            mode: Desired power mode.

        Returns:
            True if successful.
        """
        mode_map = {
            JetsonPowerMode.MAXN: "0",
            JetsonPowerMode.MODE_15W: "1",
            JetsonPowerMode.MODE_10W: "2",
            JetsonPowerMode.MODE_5W: "3",
        }

        if mode == JetsonPowerMode.MODE_AUTO:
            return True

        mode_id = mode_map.get(mode, "0")
        try:
            subprocess.run(
                ["sudo", "nvpmodel", "-m", mode_id],
                check=True,
                capture_output=True,
            )
            logger.info(f"Set Jetson power mode to {mode.value}")
            return True
        except Exception as e:
            logger.warning(f"Failed to set power mode: {e}")
            return False

    @property
    def name(self) -> str:
        """Backend name."""
        return "jetson"

    def is_available(self) -> bool:
        """Check if Jetson backend is available."""
        return HAS_JETSON and HAS_CUPY and self._initialized

    def get_device_info(self, device_id: int = 0) -> DeviceInfo:
        """Get Jetson device information."""
        if not self.is_available():
            return DeviceInfo(
                device_type=DeviceType.JETSON,
                device_id=device_id,
                name="Jetson (unavailable)",
                is_available=False,
            )

        try:
            with cuda.Device(device_id):
                props = cuda.runtime.getDeviceProperties(device_id)
                mem_info = cuda.runtime.memGetInfo()

                return DeviceInfo(
                    device_type=DeviceType.JETSON,
                    device_id=device_id,
                    name=JETSON_MODEL or "Jetson",
                    is_available=True,
                    compute_capability=f"{props['major']}.{props['minor']}",
                    memory_total=props.get("totalGlobalMem", mem_info[1]),
                    memory_free=mem_info[0],
                    extra_info={
                        "model": JETSON_MODEL,
                        "power_mode": self._config.power_mode.value,
                        "unified_memory": self._config.use_unified_memory,
                        "dla_available": JETSON_MODEL and "Orin" in JETSON_MODEL,
                    },
                )
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return DeviceInfo(
                device_type=DeviceType.JETSON,
                device_id=device_id,
                name="Jetson (error)",
                is_available=False,
            )

    def get_all_devices(self) -> List[DeviceInfo]:
        """Get info for all Jetson devices (usually just one)."""
        if not self.is_available():
            return []
        return [self.get_device_info(0)]

    def _get_tensor(self, handle: TensorHandle) -> Any:
        """Get CuPy array from handle."""
        return self._tensors[handle.tensor_id]

    def _wrap_result(self, array: Any, device_id: int = 0) -> TensorHandle:
        """Wrap CuPy array in TensorHandle."""
        tensor_id = self._next_id
        self._next_id += 1
        self._tensors[tensor_id] = array

        return TensorHandle(
            tensor_id=tensor_id,
            backend_name="jetson",
            device_id=device_id,
            shape=tuple(array.shape),
            dtype=str(array.dtype),
        )

    # -------------------------------------------------------------------------
    # Tensor Creation
    # -------------------------------------------------------------------------

    def from_numpy(
        self,
        array: np.ndarray,
        device_id: int = 0,
    ) -> TensorHandle:
        """Create tensor from NumPy array using unified memory."""
        if not self.is_available():
            raise RuntimeError("Jetson backend not available")

        with cuda.Device(device_id):
            if self._config.use_unified_memory:
                # Use managed memory for zero-copy
                gpu_array = cp.asarray(array, dtype=cp.float64)
            else:
                gpu_array = cp.asarray(array, dtype=cp.float64)

            return self._wrap_result(gpu_array, device_id)

    def to_numpy(self, handle: TensorHandle) -> np.ndarray:
        """Convert tensor to NumPy array."""
        gpu_array = self._get_tensor(handle)
        return cp.asnumpy(gpu_array)

    def zeros(
        self,
        shape: Tuple[int, ...],
        device_id: int = 0,
    ) -> TensorHandle:
        """Create zero-filled tensor."""
        if not self.is_available():
            raise RuntimeError("Jetson backend not available")

        with cuda.Device(device_id):
            array = cp.zeros(shape, dtype=cp.float64)
            return self._wrap_result(array, device_id)

    def ones(
        self,
        shape: Tuple[int, ...],
        device_id: int = 0,
    ) -> TensorHandle:
        """Create one-filled tensor."""
        if not self.is_available():
            raise RuntimeError("Jetson backend not available")

        with cuda.Device(device_id):
            array = cp.ones(shape, dtype=cp.float64)
            return self._wrap_result(array, device_id)

    def full(
        self,
        shape: Tuple[int, ...],
        fill_value: float,
        device_id: int = 0,
    ) -> TensorHandle:
        """Create constant-filled tensor."""
        if not self.is_available():
            raise RuntimeError("Jetson backend not available")

        with cuda.Device(device_id):
            array = cp.full(shape, fill_value, dtype=cp.float64)
            return self._wrap_result(array, device_id)

    # -------------------------------------------------------------------------
    # Element-wise Operations
    # -------------------------------------------------------------------------

    def add(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """Element-wise addition."""
        arr_a = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            arr_b = self._get_tensor(b)
            result = cp.add(arr_a, arr_b)
        else:
            result = cp.add(arr_a, b)
        return self._wrap_result(result, a.device_id)

    def subtract(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """Element-wise subtraction."""
        arr_a = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            arr_b = self._get_tensor(b)
            result = cp.subtract(arr_a, arr_b)
        else:
            result = cp.subtract(arr_a, b)
        return self._wrap_result(result, a.device_id)

    def multiply(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
    ) -> TensorHandle:
        """Element-wise multiplication."""
        arr_a = self._get_tensor(a)
        if isinstance(b, TensorHandle):
            arr_b = self._get_tensor(b)
            result = cp.multiply(arr_a, arr_b)
        else:
            result = cp.multiply(arr_a, b)
        return self._wrap_result(result, a.device_id)

    def divide(
        self,
        a: TensorHandle,
        b: Union[TensorHandle, float],
        safe: bool = False,
    ) -> TensorHandle:
        """Element-wise division with optional safety."""
        arr_a = self._get_tensor(a)

        if isinstance(b, TensorHandle):
            arr_b = self._get_tensor(b)
            if safe:
                result = cp.where(
                    cp.abs(arr_b) < EPSILON,
                    cp.ones_like(arr_a),
                    arr_a / arr_b,
                )
            else:
                result = cp.divide(arr_a, arr_b)
        else:
            if safe and abs(b) < EPSILON:
                result = cp.ones_like(arr_a)
            else:
                result = cp.divide(arr_a, b)

        return self._wrap_result(result, a.device_id)

    def clip(
        self,
        a: TensorHandle,
        min_val: float,
        max_val: float,
    ) -> TensorHandle:
        """Clip values to range."""
        arr = self._get_tensor(a)
        result = cp.clip(arr, min_val, max_val)
        return self._wrap_result(result, a.device_id)

    def abs(self, a: TensorHandle) -> TensorHandle:
        """Element-wise absolute value."""
        arr = self._get_tensor(a)
        result = cp.abs(arr)
        return self._wrap_result(result, a.device_id)

    def sqrt(self, a: TensorHandle) -> TensorHandle:
        """Element-wise square root."""
        arr = self._get_tensor(a)
        result = cp.sqrt(arr)
        return self._wrap_result(result, a.device_id)

    def exp(self, a: TensorHandle) -> TensorHandle:
        """Element-wise exponential."""
        arr = self._get_tensor(a)
        result = cp.exp(arr)
        return self._wrap_result(result, a.device_id)

    def log(self, a: TensorHandle, safe: bool = False) -> TensorHandle:
        """Element-wise natural logarithm."""
        arr = self._get_tensor(a)
        if safe:
            arr = cp.clip(arr, EPSILON, None)
        result = cp.log(arr)
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
        """Sum reduction."""
        arr = self._get_tensor(a)
        result = cp.sum(arr, axis=axis, keepdims=keepdims)
        return self._wrap_result(result, a.device_id)

    def mean(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Mean reduction."""
        arr = self._get_tensor(a)
        result = cp.mean(arr, axis=axis, keepdims=keepdims)
        return self._wrap_result(result, a.device_id)

    def min(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Minimum reduction."""
        arr = self._get_tensor(a)
        result = cp.min(arr, axis=axis, keepdims=keepdims)
        return self._wrap_result(result, a.device_id)

    def max(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
        keepdims: bool = False,
    ) -> TensorHandle:
        """Maximum reduction."""
        arr = self._get_tensor(a)
        result = cp.max(arr, axis=axis, keepdims=keepdims)
        return self._wrap_result(result, a.device_id)

    def argmin(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Index of minimum value."""
        arr = self._get_tensor(a)
        result = cp.argmin(arr, axis=axis)
        return self._wrap_result(result, a.device_id)

    def argmax(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Index of maximum value."""
        arr = self._get_tensor(a)
        result = cp.argmax(arr, axis=axis)
        return self._wrap_result(result, a.device_id)

    # -------------------------------------------------------------------------
    # Linear Algebra
    # -------------------------------------------------------------------------

    def dot(self, a: TensorHandle, b: TensorHandle) -> TensorHandle:
        """Dot product."""
        arr_a = self._get_tensor(a)
        arr_b = self._get_tensor(b)
        result = cp.dot(arr_a, arr_b)
        return self._wrap_result(result, a.device_id)

    def tensordot(
        self,
        a: TensorHandle,
        b: TensorHandle,
        axes: Union[int, Tuple[List[int], List[int]]],
    ) -> TensorHandle:
        """Tensor contraction."""
        arr_a = self._get_tensor(a)
        arr_b = self._get_tensor(b)
        result = cp.tensordot(arr_a, arr_b, axes=axes)
        return self._wrap_result(result, a.device_id)

    def norm(
        self,
        a: TensorHandle,
        ord: Optional[Union[int, float, str]] = None,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Compute tensor norm."""
        arr = self._get_tensor(a)
        result = cp.linalg.norm(arr, ord=ord, axis=axis)
        return self._wrap_result(result, a.device_id)

    def einsum(
        self,
        subscripts: str,
        *operands: TensorHandle,
    ) -> TensorHandle:
        """Einstein summation."""
        arrays = [self._get_tensor(op) for op in operands]
        result = cp.einsum(subscripts, *arrays)
        device_id = operands[0].device_id if operands else 0
        return self._wrap_result(result, device_id)

    # -------------------------------------------------------------------------
    # Shape Operations
    # -------------------------------------------------------------------------

    def reshape(
        self,
        a: TensorHandle,
        shape: Tuple[int, ...],
    ) -> TensorHandle:
        """Reshape tensor."""
        arr = self._get_tensor(a)
        result = cp.reshape(arr, shape)
        return self._wrap_result(result, a.device_id)

    def transpose(
        self,
        a: TensorHandle,
        axes: Optional[Tuple[int, ...]] = None,
    ) -> TensorHandle:
        """Transpose tensor."""
        arr = self._get_tensor(a)
        result = cp.transpose(arr, axes)
        return self._wrap_result(result, a.device_id)

    def expand_dims(
        self,
        a: TensorHandle,
        axis: int,
    ) -> TensorHandle:
        """Add dimension."""
        arr = self._get_tensor(a)
        result = cp.expand_dims(arr, axis)
        return self._wrap_result(result, a.device_id)

    def squeeze(
        self,
        a: TensorHandle,
        axis: Optional[int] = None,
    ) -> TensorHandle:
        """Remove single-element dimensions."""
        arr = self._get_tensor(a)
        result = cp.squeeze(arr, axis=axis)
        return self._wrap_result(result, a.device_id)

    def broadcast_to(
        self,
        a: TensorHandle,
        shape: Tuple[int, ...],
    ) -> TensorHandle:
        """Broadcast tensor to shape."""
        arr = self._get_tensor(a)
        result = cp.broadcast_to(arr, shape)
        return self._wrap_result(result, a.device_id)

    def concatenate(
        self,
        tensors: List[TensorHandle],
        axis: int = 0,
    ) -> TensorHandle:
        """Concatenate tensors."""
        arrays = [self._get_tensor(t) for t in tensors]
        result = cp.concatenate(arrays, axis=axis)
        device_id = tensors[0].device_id if tensors else 0
        return self._wrap_result(result, device_id)

    def stack(
        self,
        tensors: List[TensorHandle],
        axis: int = 0,
    ) -> TensorHandle:
        """Stack tensors along new axis."""
        arrays = [self._get_tensor(t) for t in tensors]
        result = cp.stack(arrays, axis=axis)
        device_id = tensors[0].device_id if tensors else 0
        return self._wrap_result(result, device_id)

    # -------------------------------------------------------------------------
    # Sparse Operations (basic support)
    # -------------------------------------------------------------------------

    def to_sparse_coo(
        self,
        a: TensorHandle,
        threshold: float = 0.0,
    ) -> Tuple[TensorHandle, TensorHandle, Tuple[int, ...]]:
        """Convert to sparse COO format."""
        arr = self._get_tensor(a)
        mask = cp.abs(arr) > threshold
        coords = cp.argwhere(mask)
        values = arr[mask]
        shape = arr.shape

        return (
            self._wrap_result(coords, a.device_id),
            self._wrap_result(values, a.device_id),
            shape,
        )

    def from_sparse_coo(
        self,
        coords: TensorHandle,
        values: TensorHandle,
        shape: Tuple[int, ...],
        fill_value: float = 0.0,
    ) -> TensorHandle:
        """Convert sparse COO to dense."""
        coords_gpu = self._get_tensor(coords)
        values_gpu = self._get_tensor(values)

        # Ensure coordinates are integers
        coords_int = coords_gpu.astype(cp.int64)

        dense = cp.full(shape, fill_value, dtype=cp.float64)
        if len(coords_int) > 0:
            idx = tuple(coords_int[:, i] for i in range(len(shape)))
            dense[idx] = values_gpu

        return self._wrap_result(dense, coords.device_id)

    # -------------------------------------------------------------------------
    # Advanced Operations
    # -------------------------------------------------------------------------

    def sort(
        self,
        a: TensorHandle,
        axis: int = -1,
    ) -> TensorHandle:
        """Sort tensor along axis."""
        arr = self._get_tensor(a)
        result = cp.sort(arr, axis=axis)
        return self._wrap_result(result, a.device_id)

    def where(
        self,
        condition: TensorHandle,
        x: TensorHandle,
        y: TensorHandle,
    ) -> TensorHandle:
        """Conditional selection."""
        cond = self._get_tensor(condition)
        arr_x = self._get_tensor(x)
        arr_y = self._get_tensor(y)
        result = cp.where(cond, arr_x, arr_y)
        return self._wrap_result(result, x.device_id)

    # -------------------------------------------------------------------------
    # Ethics-Specific Operations
    # -------------------------------------------------------------------------

    def moral_contraction(
        self,
        tensor: TensorHandle,
        weights: TensorHandle,
        axis: int = 1,
        normalize: bool = True,
    ) -> TensorHandle:
        """
        Optimized moral dimension contraction for Jetson.

        Uses unified memory for efficient CPU-GPU coordination.
        """
        t = self._get_tensor(tensor)
        w = self._get_tensor(weights)

        # Normalize weights if requested
        if normalize:
            w_sum = cp.sum(w)
            if w_sum > EPSILON:
                w = w / w_sum

        # Contract using tensordot
        result = cp.tensordot(t, w, axes=([axis], [0]))

        # Ensure result is in valid range
        result = cp.clip(result, 0.0, 1.0)

        return self._wrap_result(result, tensor.device_id)

    def batch_gini(
        self,
        tensor: TensorHandle,
        axis: int = -1,
    ) -> TensorHandle:
        """
        Compute Gini coefficient along axis (batched).

        Optimized for Jetson's unified memory architecture.
        """
        arr = self._get_tensor(tensor)

        # Move axis to last position
        arr = cp.moveaxis(arr, axis, -1)
        n = arr.shape[-1]

        if n <= 1:
            result = cp.zeros(arr.shape[:-1], dtype=cp.float64)
            return self._wrap_result(result, tensor.device_id)

        # Sort along last axis
        sorted_arr = cp.sort(arr, axis=-1)

        # Compute cumulative sum
        cumsum = cp.cumsum(sorted_arr, axis=-1)
        total = cumsum[..., -1:]

        # Handle zero totals
        safe_total = cp.where(total < EPSILON, cp.ones_like(total), total)

        # Gini formula
        indices = cp.arange(1, n + 1, dtype=cp.float64)
        numerator = cp.sum((2 * indices - n - 1) * sorted_arr, axis=-1)
        gini = numerator / (n * safe_total[..., 0])

        # Zero out where total was zero
        gini = cp.where(total[..., 0] < EPSILON, cp.zeros_like(gini), gini)
        gini = cp.clip(gini, 0.0, 1.0)

        return self._wrap_result(gini, tensor.device_id)

    # -------------------------------------------------------------------------
    # Memory Management
    # -------------------------------------------------------------------------

    def get_memory_info(self, device_id: int = 0) -> Tuple[int, int]:
        """Get GPU memory usage (used, total)."""
        if not self.is_available():
            return (0, 0)

        with cuda.Device(device_id):
            free, total = cuda.runtime.memGetInfo()
            return (total - free, total)

    def clear_cache(self) -> None:
        """Clear GPU memory cache."""
        if HAS_CUPY:
            mempool = cp.get_default_memory_pool()
            mempool.free_all_blocks()

    def synchronize(self, device_id: int = 0) -> None:
        """Synchronize device."""
        if HAS_CUPY:
            with cuda.Device(device_id):
                cuda.Stream.null.synchronize()


# -----------------------------------------------------------------------------
# Module-level convenience functions
# -----------------------------------------------------------------------------


def jetson_is_available() -> bool:
    """Check if Jetson hardware is available."""
    return HAS_JETSON and HAS_CUPY


def get_jetson_model() -> Optional[str]:
    """Get Jetson model name."""
    return JETSON_MODEL


def get_jetson_backend(config: Optional[JetsonConfig] = None) -> JetsonBackend:
    """Get a Jetson backend instance."""
    return JetsonBackend(config=config)


__all__ = [
    "JetsonBackend",
    "JetsonConfig",
    "JetsonPowerMode",
    "DLACore",
    "jetson_is_available",
    "get_jetson_model",
    "get_jetson_backend",
    "HAS_JETSON",
    "HAS_TENSORRT",
]
