# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Acceleration Dispatcher for Backend Selection.

DEME V3 Sprint 11: Provides automatic and configurable backend selection
for tensor operations. The dispatcher selects the most appropriate backend
based on hardware availability, user preferences, and tensor characteristics.

Selection Priority (by default):
1. CUDA (if available and tensor is large)
2. Jetson (if on Jetson hardware)
3. CPU (always available fallback)

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type

import numpy as np

from .backend import (
    AccelerationBackend,
    DeviceInfo,
    TensorHandle,
)
from .cpu import CPUBackend


logger = logging.getLogger(__name__)


class BackendPreference(Enum):
    """Backend selection preference."""

    AUTO = "auto"  # Automatically select best available
    CPU = "cpu"  # Force CPU backend
    CUDA = "cuda"  # Prefer CUDA if available
    JETSON = "jetson"  # Prefer Jetson if available
    FASTEST = "fastest"  # Run benchmark and select fastest


@dataclass
class DispatcherConfig:
    """
    Configuration for the acceleration dispatcher.

    Attributes:
        preference: Backend selection preference.
        cuda_min_elements: Minimum tensor elements to use CUDA.
        cuda_device_id: Preferred CUDA device ID.
        enable_profiling: Whether to enable operation profiling.
        fallback_to_cpu: Whether to fall back to CPU on errors.
        cache_backends: Whether to cache backend instances.
    """

    preference: BackendPreference = BackendPreference.AUTO
    """Backend selection preference."""

    cuda_min_elements: int = 10000
    """Minimum tensor elements to use CUDA (smaller tensors use CPU)."""

    cuda_device_id: int = 0
    """Preferred CUDA device ID for multi-GPU systems."""

    enable_profiling: bool = False
    """Whether to enable operation profiling."""

    fallback_to_cpu: bool = True
    """Whether to fall back to CPU on errors."""

    cache_backends: bool = True
    """Whether to cache backend instances."""

    extra_config: Dict[str, Any] = field(default_factory=dict)
    """Backend-specific configuration."""


class AccelerationDispatcher:
    """
    Dispatcher for selecting and managing acceleration backends.

    The dispatcher maintains a registry of available backends and
    provides methods for:

    - Automatic backend selection based on hardware
    - Manual backend selection by name or type
    - Backend-agnostic tensor operations
    - Performance profiling and benchmarking

    Example:
        dispatcher = AccelerationDispatcher()
        backend = dispatcher.get_backend()  # Auto-selects best

        # Or force a specific backend
        cpu = dispatcher.get_backend("cpu")

        # Use dispatcher for operations
        result = dispatcher.add(tensor_a, tensor_b)
    """

    def __init__(self, config: Optional[DispatcherConfig] = None):
        """
        Initialize the dispatcher.

        Args:
            config: Dispatcher configuration (default settings if None).
        """
        self._config = config or DispatcherConfig()
        self._backends: Dict[str, AccelerationBackend] = {}
        self._backend_classes: Dict[str, Type[AccelerationBackend]] = {}
        self._default_backend: Optional[AccelerationBackend] = None
        self._profiling_data: Dict[str, List[float]] = {}

        # Register built-in backends
        self._register_builtin_backends()

    def _register_builtin_backends(self) -> None:
        """Register built-in backend implementations."""
        # CPU backend is always available
        self.register_backend_class("cpu", CPUBackend)

        # Try to import and register CUDA backend
        try:
            from .cuda import CUDABackend

            self.register_backend_class("cuda", CUDABackend)
        except ImportError:
            logger.debug("CUDA backend not available (CuPy not installed)")

        # Try to import and register Jetson backend
        try:
            from .jetson import JetsonBackend

            self.register_backend_class("jetson", JetsonBackend)
        except ImportError:
            logger.debug("Jetson backend not available")

    def register_backend_class(
        self,
        name: str,
        backend_class: Type[AccelerationBackend],
    ) -> None:
        """
        Register a backend class.

        Args:
            name: Backend name (e.g., "cpu", "cuda").
            backend_class: Backend class to instantiate.
        """
        self._backend_classes[name] = backend_class
        logger.debug(f"Registered backend class: {name}")

    def register_backend(
        self,
        name: str,
        backend: AccelerationBackend,
    ) -> None:
        """
        Register a backend instance.

        Args:
            name: Backend name.
            backend: Backend instance.
        """
        self._backends[name] = backend
        logger.debug(f"Registered backend instance: {name}")

    def get_backend(
        self,
        name: Optional[str] = None,
        tensor_size: Optional[int] = None,
    ) -> AccelerationBackend:
        """
        Get a backend by name or auto-select.

        Args:
            name: Backend name (None for auto-selection).
            tensor_size: Hint for tensor size to optimize selection.

        Returns:
            AccelerationBackend instance.

        Raises:
            ValueError: If requested backend is not available.
        """
        if name is not None:
            return self._get_backend_by_name(name)

        return self._auto_select_backend(tensor_size)

    def _get_backend_by_name(self, name: str) -> AccelerationBackend:
        """Get a specific backend by name."""
        # Check cached instances
        if name in self._backends:
            return self._backends[name]

        # Try to instantiate from class
        if name in self._backend_classes:
            backend_class = self._backend_classes[name]
            try:
                backend = backend_class()
                if backend.is_available():
                    if self._config.cache_backends:
                        self._backends[name] = backend
                    return backend
                else:
                    raise ValueError(f"Backend '{name}' is not available")
            except Exception as e:
                raise ValueError(f"Failed to create backend '{name}': {e}") from e

        raise ValueError(f"Unknown backend: {name}")

    def _auto_select_backend(
        self,
        tensor_size: Optional[int] = None,
    ) -> AccelerationBackend:
        """Automatically select the best available backend."""
        preference = self._config.preference

        if preference == BackendPreference.CPU:
            return self._get_backend_by_name("cpu")

        if preference == BackendPreference.CUDA:
            if self._is_backend_available("cuda"):
                return self._get_backend_by_name("cuda")
            elif self._config.fallback_to_cpu:
                logger.warning("CUDA not available, falling back to CPU")
                return self._get_backend_by_name("cpu")
            else:
                raise ValueError("CUDA backend requested but not available")

        if preference == BackendPreference.JETSON:
            if self._is_backend_available("jetson"):
                return self._get_backend_by_name("jetson")
            elif self._config.fallback_to_cpu:
                logger.warning("Jetson not available, falling back to CPU")
                return self._get_backend_by_name("cpu")
            else:
                raise ValueError("Jetson backend requested but not available")

        # AUTO or FASTEST: try best available
        return self._select_best_backend(tensor_size)

    def _select_best_backend(
        self,
        tensor_size: Optional[int] = None,
    ) -> AccelerationBackend:
        """Select the best backend based on availability and tensor size."""
        # Check CUDA availability and size threshold
        if self._is_backend_available("cuda"):
            if tensor_size is None or tensor_size >= self._config.cuda_min_elements:
                try:
                    return self._get_backend_by_name("cuda")
                except Exception as e:
                    logger.warning(f"Failed to get CUDA backend: {e}")

        # Check Jetson availability
        if self._is_backend_available("jetson"):
            try:
                return self._get_backend_by_name("jetson")
            except Exception as e:
                logger.warning(f"Failed to get Jetson backend: {e}")

        # Fall back to CPU
        return self._get_backend_by_name("cpu")

    def _is_backend_available(self, name: str) -> bool:
        """Check if a backend is available."""
        if name in self._backends:
            return self._backends[name].is_available()

        if name in self._backend_classes:
            try:
                backend = self._backend_classes[name]()
                return backend.is_available()
            except Exception:
                return False

        return False

    def get_available_backends(self) -> List[str]:
        """Get list of available backend names."""
        available = []
        for name in self._backend_classes:
            if self._is_backend_available(name):
                available.append(name)
        return available

    def get_all_device_info(self) -> Dict[str, List[DeviceInfo]]:
        """Get device information for all available backends."""
        info: Dict[str, List[DeviceInfo]] = {}
        for name in self.get_available_backends():
            try:
                backend = self.get_backend(name)
                info[name] = backend.get_all_devices()
            except Exception as e:
                logger.warning(f"Failed to get device info for {name}: {e}")
        return info

    # -------------------------------------------------------------------------
    # Convenience Operations (delegates to selected backend)
    # -------------------------------------------------------------------------

    def from_numpy(
        self,
        array: np.ndarray,
        backend: Optional[str] = None,
    ) -> TensorHandle:
        """
        Create a tensor from NumPy array.

        Args:
            array: NumPy array.
            backend: Backend name (None for auto).

        Returns:
            TensorHandle on the selected backend.
        """
        b = self.get_backend(backend, tensor_size=array.size)
        return b.from_numpy(array)

    def to_numpy(self, handle: TensorHandle) -> np.ndarray:
        """
        Convert tensor handle to NumPy array.

        Args:
            handle: Tensor handle.

        Returns:
            NumPy array.
        """
        backend = self.get_backend(handle.backend_name)
        return backend.to_numpy(handle)

    def transfer(
        self,
        handle: TensorHandle,
        target_backend: str,
    ) -> TensorHandle:
        """
        Transfer tensor to a different backend.

        Args:
            handle: Source tensor handle.
            target_backend: Target backend name.

        Returns:
            New TensorHandle on target backend.
        """
        if handle.backend_name == target_backend:
            return handle

        # Transfer via NumPy (may be optimized for specific pairs)
        source = self.get_backend(handle.backend_name)
        target = self.get_backend(target_backend)

        array = source.to_numpy(handle)
        return target.from_numpy(array)

    # -------------------------------------------------------------------------
    # Profiling
    # -------------------------------------------------------------------------

    def enable_profiling(self, enable: bool = True) -> None:
        """Enable or disable operation profiling."""
        self._config.enable_profiling = enable

    def get_profiling_data(self) -> Dict[str, List[float]]:
        """Get collected profiling data."""
        return self._profiling_data.copy()

    def clear_profiling_data(self) -> None:
        """Clear collected profiling data."""
        self._profiling_data.clear()

    # -------------------------------------------------------------------------
    # Benchmarking
    # -------------------------------------------------------------------------

    def benchmark_backends(
        self,
        shape: Tuple[int, ...] = (9, 100, 50),
        n_iterations: int = 100,
    ) -> Dict[str, Dict[str, float]]:
        """
        Benchmark available backends.

        Runs a set of standard operations and measures execution time
        for each available backend.

        Args:
            shape: Tensor shape for benchmarks.
            n_iterations: Number of iterations per operation.

        Returns:
            Dict mapping backend names to operation timing results.
        """
        import time

        results: Dict[str, Dict[str, float]] = {}

        # Create test data
        test_data = np.random.rand(*shape).astype(np.float64)
        weights = np.random.rand(shape[1]).astype(np.float64)
        weights = weights / weights.sum()

        for backend_name in self.get_available_backends():
            try:
                backend = self.get_backend(backend_name)
                tensor = backend.from_numpy(test_data)
                weight_tensor = backend.from_numpy(weights)

                timings: Dict[str, float] = {}

                # Benchmark element-wise operations
                start = time.perf_counter()
                for _ in range(n_iterations):
                    _ = backend.multiply(tensor, 0.5)
                timings["multiply_scalar"] = (
                    time.perf_counter() - start
                ) / n_iterations

                start = time.perf_counter()
                for _ in range(n_iterations):
                    _ = backend.add(tensor, tensor)
                timings["add_tensor"] = (time.perf_counter() - start) / n_iterations

                # Benchmark reduction operations
                start = time.perf_counter()
                for _ in range(n_iterations):
                    _ = backend.sum(tensor, axis=1)
                timings["sum_axis1"] = (time.perf_counter() - start) / n_iterations

                start = time.perf_counter()
                for _ in range(n_iterations):
                    _ = backend.mean(tensor, axis=-1)
                timings["mean_axis_last"] = (time.perf_counter() - start) / n_iterations

                # Benchmark contraction
                start = time.perf_counter()
                for _ in range(n_iterations):
                    _ = backend.tensordot(tensor, weight_tensor, axes=([1], [0]))
                timings["contraction"] = (time.perf_counter() - start) / n_iterations

                # Benchmark clip (common for ethics)
                start = time.perf_counter()
                for _ in range(n_iterations):
                    _ = backend.clip(tensor, 0.0, 1.0)
                timings["clip"] = (time.perf_counter() - start) / n_iterations

                results[backend_name] = timings

            except Exception as e:
                logger.warning(f"Benchmark failed for {backend_name}: {e}")
                results[backend_name] = {"error": str(e)}  # type: ignore

        return results

    def format_benchmark_results(
        self,
        results: Dict[str, Dict[str, float]],
    ) -> str:
        """
        Format benchmark results as a readable string.

        Args:
            results: Results from benchmark_backends().

        Returns:
            Formatted string table.
        """
        lines = ["Acceleration Backend Benchmark Results", "=" * 50]

        for backend_name, timings in results.items():
            lines.append(f"\n{backend_name.upper()} Backend:")
            lines.append("-" * 30)

            if "error" in timings:
                lines.append(f"  Error: {timings['error']}")
                continue

            for op_name, duration in timings.items():
                lines.append(f"  {op_name}: {duration*1000:.4f} ms")

        return "\n".join(lines)


# Global dispatcher instance
_global_dispatcher: Optional[AccelerationDispatcher] = None


def get_dispatcher(config: Optional[DispatcherConfig] = None) -> AccelerationDispatcher:
    """
    Get the global dispatcher instance.

    Args:
        config: Configuration for new dispatcher (only used on first call).

    Returns:
        Global AccelerationDispatcher instance.
    """
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = AccelerationDispatcher(config)
    return _global_dispatcher


def set_dispatcher(dispatcher: AccelerationDispatcher) -> None:
    """
    Set the global dispatcher instance.

    Args:
        dispatcher: Dispatcher instance to use globally.
    """
    global _global_dispatcher
    _global_dispatcher = dispatcher


def reset_dispatcher() -> None:
    """Reset the global dispatcher (creates new instance on next get)."""
    global _global_dispatcher
    _global_dispatcher = None


__all__ = [
    "BackendPreference",
    "DispatcherConfig",
    "AccelerationDispatcher",
    "get_dispatcher",
    "set_dispatcher",
    "reset_dispatcher",
]
