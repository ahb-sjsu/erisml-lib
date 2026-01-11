# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEME V3 Acceleration Framework.

This package provides hardware acceleration for MoralTensor operations,
enabling efficient ethical computation on various platforms:

- **CPU Backend** (Sprint 11): NumPy/SciPy optimized operations
- **CUDA Backend** (Sprint 12): GPU acceleration via CuPy
- **Jetson Backend** (Sprint 13): Edge deployment with TensorRT

Usage:
    from erisml.ethics.acceleration import get_dispatcher

    # Auto-select best backend
    dispatcher = get_dispatcher()
    backend = dispatcher.get_backend()

    # Create tensor on device
    tensor = backend.from_numpy(my_array)

    # Run operations
    result = backend.add(tensor, 0.1)
    result = backend.clip(result, 0.0, 1.0)

    # Get back to NumPy
    output = backend.to_numpy(result)

For manual backend selection:
    # Force CPU
    cpu = dispatcher.get_backend("cpu")

    # Force CUDA (if available)
    cuda = dispatcher.get_backend("cuda")

Version: 3.0.0 (DEME V3 Sprint 11)
"""

# Core abstractions
from .backend import (
    AccelerationBackend,
    DeviceInfo,
    DeviceType,
    TensorHandle,
)

# CPU backend (always available)
from .cpu import (
    CPUBackend,
    get_cpu_backend,
    HAS_SCIPY,
    EPSILON,
)

# Dispatcher
from .dispatcher import (
    AccelerationDispatcher,
    BackendPreference,
    DispatcherConfig,
    get_dispatcher,
    set_dispatcher,
    reset_dispatcher,
)


def get_backend(name: str = "cpu") -> AccelerationBackend:
    """
    Convenience function to get a backend by name.

    Args:
        name: Backend name ("cpu", "cuda", "jetson").

    Returns:
        AccelerationBackend instance.

    Example:
        backend = get_backend("cpu")
        tensor = backend.from_numpy(np.ones(9))
    """
    return get_dispatcher().get_backend(name)


def list_backends() -> list:
    """
    List available acceleration backends.

    Returns:
        List of backend names that are available on this system.

    Example:
        >>> list_backends()
        ['cpu']  # On CPU-only system
        >>> list_backends()
        ['cpu', 'cuda']  # On system with NVIDIA GPU
    """
    return get_dispatcher().get_available_backends()


__all__ = [
    # Core abstractions
    "AccelerationBackend",
    "DeviceInfo",
    "DeviceType",
    "TensorHandle",
    # CPU backend
    "CPUBackend",
    "get_cpu_backend",
    "HAS_SCIPY",
    "EPSILON",
    # Dispatcher
    "AccelerationDispatcher",
    "BackendPreference",
    "DispatcherConfig",
    "get_dispatcher",
    "set_dispatcher",
    "reset_dispatcher",
    # Convenience functions
    "get_backend",
    "list_backends",
]
