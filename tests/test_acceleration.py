# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for DEME V3 Acceleration Framework (Sprint 11).

Tests the acceleration backend abstraction, CPU backend implementation,
and dispatcher functionality.
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from erisml.ethics.acceleration import (
    # Core abstractions
    DeviceInfo,
    DeviceType,
    TensorHandle,
    # CPU backend
    CPUBackend,
    get_cpu_backend,
    HAS_SCIPY,
    # CUDA backend
    CUDABackend,
    cuda_is_available,
    HAS_CUPY,
    # Jetson backend
    JetsonBackend,
    jetson_is_available,
    HAS_JETSON,
    # Dispatcher
    AccelerationDispatcher,
    BackendPreference,
    DispatcherConfig,
    get_dispatcher,
    reset_dispatcher,
    # Convenience
    get_backend,
    list_backends,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def cpu_backend():
    """Get a fresh CPU backend instance."""
    return CPUBackend()


@pytest.fixture
def dispatcher():
    """Get a fresh dispatcher instance."""
    reset_dispatcher()
    return get_dispatcher()


@pytest.fixture
def sample_array():
    """Create a sample moral tensor array (9, 5)."""
    np.random.seed(42)
    return np.random.rand(9, 5).astype(np.float64)


@pytest.fixture
def sample_rank1():
    """Create a sample rank-1 array (9,)."""
    return np.array([0.1, 0.8, 0.6, 0.7, 0.9, 0.3, 0.5, 0.4, 0.2], dtype=np.float64)


@pytest.fixture
def sample_rank3():
    """Create a sample rank-3 array (9, 4, 3)."""
    np.random.seed(123)
    return np.random.rand(9, 4, 3).astype(np.float64)


# =============================================================================
# Test DeviceType and DeviceInfo
# =============================================================================


class TestDeviceType:
    """Tests for DeviceType enum."""

    def test_device_types_exist(self):
        """All expected device types should exist."""
        assert DeviceType.CPU.value == "cpu"
        assert DeviceType.CUDA.value == "cuda"
        assert DeviceType.JETSON.value == "jetson"
        assert DeviceType.TPU.value == "tpu"
        assert DeviceType.MLX.value == "mlx"


class TestDeviceInfo:
    """Tests for DeviceInfo dataclass."""

    def test_device_info_creation(self):
        """DeviceInfo should be creatable with basic attributes."""
        info = DeviceInfo(
            device_type=DeviceType.CPU,
            device_id=0,
            name="Test CPU",
        )
        assert info.device_type == DeviceType.CPU
        assert info.device_id == 0
        assert info.name == "Test CPU"
        assert info.is_available is True

    def test_device_info_frozen(self):
        """DeviceInfo should be immutable (frozen)."""
        info = DeviceInfo(device_type=DeviceType.CPU)
        with pytest.raises(AttributeError):
            info.name = "New Name"  # type: ignore


# =============================================================================
# Test TensorHandle
# =============================================================================


class TestTensorHandle:
    """Tests for TensorHandle dataclass."""

    def test_tensor_handle_creation(self):
        """TensorHandle should store tensor metadata."""
        handle = TensorHandle(
            backend_name="cpu",
            device_type=DeviceType.CPU,
            shape=(9, 5),
            dtype="float64",
        )
        assert handle.backend_name == "cpu"
        assert handle.shape == (9, 5)
        assert handle.dtype == "float64"
        assert handle.is_sparse is False

    def test_tensor_handle_repr(self):
        """TensorHandle should have informative repr."""
        handle = TensorHandle(
            backend_name="cpu",
            device_type=DeviceType.CPU,
            shape=(9, 10),
            dtype="float64",
        )
        repr_str = repr(handle)
        assert "cpu" in repr_str
        assert "(9, 10)" in repr_str


# =============================================================================
# Test CPUBackend - Creation
# =============================================================================


class TestCPUBackendCreation:
    """Tests for CPU backend tensor creation."""

    def test_from_numpy(self, cpu_backend, sample_array):
        """from_numpy should create a TensorHandle."""
        handle = cpu_backend.from_numpy(sample_array)
        assert handle.backend_name == "cpu"
        assert handle.shape == sample_array.shape
        assert handle.dtype == "float64"

    def test_to_numpy(self, cpu_backend, sample_array):
        """to_numpy should return the same data."""
        handle = cpu_backend.from_numpy(sample_array)
        result = cpu_backend.to_numpy(handle)
        assert_allclose(result, sample_array)

    def test_zeros(self, cpu_backend):
        """zeros should create zero-filled tensor."""
        handle = cpu_backend.zeros((9, 3))
        result = cpu_backend.to_numpy(handle)
        assert result.shape == (9, 3)
        assert_allclose(result, 0.0)

    def test_ones(self, cpu_backend):
        """ones should create one-filled tensor."""
        handle = cpu_backend.ones((9, 4))
        result = cpu_backend.to_numpy(handle)
        assert result.shape == (9, 4)
        assert_allclose(result, 1.0)

    def test_full(self, cpu_backend):
        """full should create constant-filled tensor."""
        handle = cpu_backend.full((9, 2), fill_value=0.5)
        result = cpu_backend.to_numpy(handle)
        assert result.shape == (9, 2)
        assert_allclose(result, 0.5)


# =============================================================================
# Test CPUBackend - Element-wise Operations
# =============================================================================


class TestCPUBackendElementwise:
    """Tests for CPU backend element-wise operations."""

    def test_add_scalar(self, cpu_backend, sample_array):
        """add with scalar should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.add(handle, 0.1)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array + 0.1)

    def test_add_tensor(self, cpu_backend, sample_array):
        """add with tensor should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.add(handle, handle)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array * 2)

    def test_subtract(self, cpu_backend, sample_array):
        """subtract should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.subtract(handle, 0.1)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array - 0.1)

    def test_multiply_scalar(self, cpu_backend, sample_array):
        """multiply with scalar should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.multiply(handle, 2.0)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array * 2.0)

    def test_multiply_tensor(self, cpu_backend, sample_array):
        """multiply with tensor should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.multiply(handle, handle)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array * sample_array)

    def test_divide_scalar(self, cpu_backend, sample_array):
        """divide by scalar should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.divide(handle, 2.0)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array / 2.0)

    def test_divide_safe_zero(self, cpu_backend):
        """divide by zero with safe=True should return 1.0."""
        arr = np.array([0.5, 0.3, 0.7], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.divide(handle, 0.0, safe=True)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, 1.0)

    def test_clip(self, cpu_backend):
        """clip should clamp values to range."""
        arr = np.array([0.0, 0.5, 1.0, 1.5, -0.5], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.clip(handle, 0.0, 1.0)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, [0.0, 0.5, 1.0, 1.0, 0.0])

    def test_abs(self, cpu_backend):
        """abs should compute absolute values."""
        arr = np.array([-0.5, 0.0, 0.5], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.abs(handle)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, [0.5, 0.0, 0.5])

    def test_sqrt(self, cpu_backend):
        """sqrt should compute square roots."""
        arr = np.array([0.0, 0.25, 1.0, 4.0], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.sqrt(handle)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, [0.0, 0.5, 1.0, 2.0])

    def test_exp(self, cpu_backend):
        """exp should compute exponentials."""
        arr = np.array([0.0, 1.0], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.exp(handle)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, [1.0, np.e], rtol=1e-6)

    def test_log_safe(self, cpu_backend):
        """log with safe=True should handle near-zero values."""
        arr = np.array([1.0, np.e, 0.0], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.log(handle, safe=True)
        result = cpu_backend.to_numpy(result_handle)
        # First two should be correct, last should be log(EPSILON)
        assert_allclose(result[0], 0.0, atol=1e-6)
        assert_allclose(result[1], 1.0, atol=1e-6)
        assert result[2] < -20  # log(1e-10) ≈ -23


# =============================================================================
# Test CPUBackend - Reductions
# =============================================================================


class TestCPUBackendReductions:
    """Tests for CPU backend reduction operations."""

    def test_sum_all(self, cpu_backend, sample_array):
        """sum over all elements should work."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.sum(handle)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array.sum())

    def test_sum_axis(self, cpu_backend, sample_array):
        """sum over specific axis should work."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.sum(handle, axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array.sum(axis=1))

    def test_sum_keepdims(self, cpu_backend, sample_array):
        """sum with keepdims should preserve dimensions."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.sum(handle, axis=1, keepdims=True)
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 1)

    def test_mean(self, cpu_backend, sample_array):
        """mean should compute average."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.mean(handle, axis=0)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array.mean(axis=0))

    def test_min(self, cpu_backend, sample_array):
        """min should find minimum values."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.min(handle, axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array.min(axis=1))

    def test_max(self, cpu_backend, sample_array):
        """max should find maximum values."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.max(handle, axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array.max(axis=1))

    def test_argmin(self, cpu_backend, sample_array):
        """argmin should find minimum indices."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.argmin(handle, axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert_array_equal(result, sample_array.argmin(axis=1))

    def test_argmax(self, cpu_backend, sample_array):
        """argmax should find maximum indices."""
        handle = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.argmax(handle, axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert_array_equal(result, sample_array.argmax(axis=1))


# =============================================================================
# Test CPUBackend - Linear Algebra
# =============================================================================


class TestCPUBackendLinAlg:
    """Tests for CPU backend linear algebra operations."""

    def test_dot(self, cpu_backend):
        """dot product should work correctly."""
        a = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        b = np.array([4.0, 5.0, 6.0], dtype=np.float64)
        ha = cpu_backend.from_numpy(a)
        hb = cpu_backend.from_numpy(b)
        result = cpu_backend.to_numpy(cpu_backend.dot(ha, hb))
        assert_allclose(result, np.dot(a, b))

    def test_tensordot(self, cpu_backend, sample_array):
        """tensordot should contract tensors correctly."""
        weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2], dtype=np.float64)
        ht = cpu_backend.from_numpy(sample_array)
        hw = cpu_backend.from_numpy(weights)
        result_handle = cpu_backend.tensordot(ht, hw, axes=([1], [0]))
        result = cpu_backend.to_numpy(result_handle)
        expected = np.tensordot(sample_array, weights, axes=([1], [0]))
        assert_allclose(result, expected)

    def test_norm(self, cpu_backend, sample_array):
        """norm should compute Frobenius norm."""
        handle = cpu_backend.from_numpy(sample_array)
        result = cpu_backend.to_numpy(cpu_backend.norm(handle))
        expected = np.linalg.norm(sample_array)
        assert_allclose(result[0], expected)


# =============================================================================
# Test CPUBackend - Shape Operations
# =============================================================================


class TestCPUBackendShape:
    """Tests for CPU backend shape operations."""

    def test_reshape(self, cpu_backend, sample_array):
        """reshape should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)  # (9, 5)
        result_handle = cpu_backend.reshape(handle, (45,))
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (45,)
        assert_allclose(result, sample_array.flatten())

    def test_transpose(self, cpu_backend, sample_array):
        """transpose should work correctly."""
        handle = cpu_backend.from_numpy(sample_array)  # (9, 5)
        result_handle = cpu_backend.transpose(handle)
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (5, 9)
        assert_allclose(result, sample_array.T)

    def test_expand_dims(self, cpu_backend, sample_rank1):
        """expand_dims should add a dimension."""
        handle = cpu_backend.from_numpy(sample_rank1)  # (9,)
        result_handle = cpu_backend.expand_dims(handle, axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 1)

    def test_squeeze(self, cpu_backend):
        """squeeze should remove singleton dimensions."""
        arr = np.ones((9, 1, 5, 1), dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result_handle = cpu_backend.squeeze(handle)
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 5)

    def test_broadcast_to(self, cpu_backend, sample_rank1):
        """broadcast_to should expand tensor."""
        handle = cpu_backend.from_numpy(sample_rank1.reshape(9, 1))  # (9, 1)
        result_handle = cpu_backend.broadcast_to(handle, (9, 5))
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 5)


# =============================================================================
# Test CPUBackend - Concatenation
# =============================================================================


class TestCPUBackendConcat:
    """Tests for CPU backend concatenation operations."""

    def test_concatenate(self, cpu_backend, sample_array):
        """concatenate should join tensors along axis."""
        h1 = cpu_backend.from_numpy(sample_array)
        h2 = cpu_backend.from_numpy(sample_array)
        result_handle = cpu_backend.concatenate([h1, h2], axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 10)

    def test_stack(self, cpu_backend, sample_rank1):
        """stack should create new axis."""
        h1 = cpu_backend.from_numpy(sample_rank1)
        h2 = cpu_backend.from_numpy(sample_rank1)
        h3 = cpu_backend.from_numpy(sample_rank1)
        result_handle = cpu_backend.stack([h1, h2, h3], axis=1)
        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 3)


# =============================================================================
# Test CPUBackend - Sparse Operations
# =============================================================================


class TestCPUBackendSparse:
    """Tests for CPU backend sparse operations."""

    def test_to_sparse_coo(self, cpu_backend):
        """to_sparse_coo should extract non-zero coordinates."""
        arr = np.zeros((9, 5), dtype=np.float64)
        arr[0, 0] = 0.5
        arr[3, 2] = 0.8
        arr[8, 4] = 0.1

        handle = cpu_backend.from_numpy(arr)
        coords, values, shape = cpu_backend.to_sparse_coo(handle)

        values_np = cpu_backend.to_numpy(values)

        assert shape == (9, 5)
        assert len(values_np) == 3
        assert 0.5 in values_np
        assert 0.8 in values_np
        assert 0.1 in values_np

    def test_from_sparse_coo(self, cpu_backend):
        """from_sparse_coo should reconstruct dense tensor."""
        coords = np.array([[0, 0], [3, 2], [8, 4]], dtype=np.int32)
        values = np.array([0.5, 0.8, 0.1], dtype=np.float64)
        shape = (9, 5)

        coords_h = cpu_backend.from_numpy(coords)
        values_h = cpu_backend.from_numpy(values)
        result_handle = cpu_backend.from_sparse_coo(coords_h, values_h, shape)

        result = cpu_backend.to_numpy(result_handle)
        assert result.shape == (9, 5)
        assert result[0, 0] == 0.5
        assert result[3, 2] == 0.8
        assert result[8, 4] == 0.1
        assert result[1, 1] == 0.0  # Fill value

    def test_sparse_roundtrip(self, cpu_backend, sample_array):
        """Sparse conversion should roundtrip correctly."""
        # Make array mostly zeros for good sparsity
        sparse_arr = np.where(sample_array > 0.7, sample_array, 0.0)
        handle = cpu_backend.from_numpy(sparse_arr)

        coords, values, shape = cpu_backend.to_sparse_coo(handle)
        reconstructed = cpu_backend.from_sparse_coo(coords, values, shape)
        result = cpu_backend.to_numpy(reconstructed)

        assert_allclose(result, sparse_arr, atol=1e-10)


# =============================================================================
# Test CPUBackend - Advanced Operations
# =============================================================================


class TestCPUBackendAdvanced:
    """Tests for CPU backend advanced operations."""

    def test_sort(self, cpu_backend):
        """sort should sort tensor along axis."""
        arr = np.array([[3.0, 1.0, 2.0], [6.0, 4.0, 5.0]], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result = cpu_backend.to_numpy(cpu_backend.sort(handle, axis=1))
        expected = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        assert_allclose(result, expected)

    def test_where(self, cpu_backend):
        """where should select based on condition."""
        cond = np.array([True, False, True], dtype=bool)
        x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        y = np.array([10.0, 20.0, 30.0], dtype=np.float64)

        h_cond = cpu_backend.from_numpy(cond)
        h_x = cpu_backend.from_numpy(x)
        h_y = cpu_backend.from_numpy(y)

        result = cpu_backend.to_numpy(cpu_backend.where(h_cond, h_x, h_y))
        assert_allclose(result, [1.0, 20.0, 3.0])

    def test_einsum(self, cpu_backend, sample_array):
        """einsum should perform Einstein summation."""
        weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2], dtype=np.float64)
        ht = cpu_backend.from_numpy(sample_array)
        hw = cpu_backend.from_numpy(weights)

        # Contraction: "ij,j->i"
        result = cpu_backend.to_numpy(cpu_backend.einsum("ij,j->i", ht, hw))
        expected = np.einsum("ij,j->i", sample_array, weights)
        assert_allclose(result, expected)


# =============================================================================
# Test CPUBackend - Ethics-Specific
# =============================================================================


class TestCPUBackendEthics:
    """Tests for CPU backend ethics-specific operations."""

    def test_moral_contraction(self, cpu_backend, sample_array):
        """moral_contraction should perform weighted reduction."""
        weights = np.array([0.5, 0.3, 0.1, 0.05, 0.05], dtype=np.float64)
        ht = cpu_backend.from_numpy(sample_array)
        hw = cpu_backend.from_numpy(weights)

        result_handle = cpu_backend.moral_contraction(ht, hw, axis=1, normalize=True)
        result = cpu_backend.to_numpy(result_handle)

        assert result.shape == (9,)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_batch_gini_equal(self, cpu_backend):
        """batch_gini should return 0 for equal distribution."""
        equal = np.array([[0.5, 0.5, 0.5, 0.5]], dtype=np.float64)
        handle = cpu_backend.from_numpy(equal)
        result = cpu_backend.to_numpy(cpu_backend.batch_gini(handle, axis=1))
        assert_allclose(result, 0.0, atol=1e-6)

    def test_batch_gini_unequal(self, cpu_backend):
        """batch_gini should return positive for unequal distribution."""
        unequal = np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float64)
        handle = cpu_backend.from_numpy(unequal)
        result = cpu_backend.to_numpy(cpu_backend.batch_gini(handle, axis=1))
        # Gini of [0, 0, 0, 1] should be 0.75
        assert result[0] > 0.5


# =============================================================================
# Test CPUBackend - Device Info
# =============================================================================


class TestCPUBackendDeviceInfo:
    """Tests for CPU backend device information."""

    def test_is_available(self, cpu_backend):
        """CPU backend should always be available."""
        assert cpu_backend.is_available() is True

    def test_get_device_info(self, cpu_backend):
        """get_device_info should return valid info."""
        info = cpu_backend.get_device_info()
        assert info.device_type == DeviceType.CPU
        assert info.is_available is True
        assert "numpy_version" in info.properties

    def test_get_all_devices(self, cpu_backend):
        """get_all_devices should return at least one device."""
        devices = cpu_backend.get_all_devices()
        assert len(devices) >= 1
        assert devices[0].device_type == DeviceType.CPU


# =============================================================================
# Test AccelerationDispatcher
# =============================================================================


class TestDispatcher:
    """Tests for AccelerationDispatcher."""

    def test_get_backend_cpu(self, dispatcher):
        """get_backend('cpu') should return CPU backend."""
        backend = dispatcher.get_backend("cpu")
        assert backend.name == "cpu"
        assert isinstance(backend, CPUBackend)

    def test_get_backend_auto(self, dispatcher):
        """get_backend() should auto-select a backend."""
        backend = dispatcher.get_backend()
        assert backend is not None
        assert backend.is_available()

    def test_get_available_backends(self, dispatcher):
        """get_available_backends should include CPU."""
        backends = dispatcher.get_available_backends()
        assert "cpu" in backends

    def test_get_all_device_info(self, dispatcher):
        """get_all_device_info should return info for all backends."""
        info = dispatcher.get_all_device_info()
        assert "cpu" in info
        assert len(info["cpu"]) >= 1

    def test_from_numpy(self, dispatcher, sample_array):
        """from_numpy convenience method should work."""
        handle = dispatcher.from_numpy(sample_array)
        assert handle is not None
        assert handle.shape == sample_array.shape

    def test_to_numpy(self, dispatcher, sample_array):
        """to_numpy convenience method should work."""
        handle = dispatcher.from_numpy(sample_array)
        result = dispatcher.to_numpy(handle)
        assert_allclose(result, sample_array)

    def test_transfer_same_backend(self, dispatcher, sample_array):
        """transfer to same backend should return same handle."""
        handle = dispatcher.from_numpy(sample_array, backend="cpu")
        transferred = dispatcher.transfer(handle, "cpu")
        assert transferred.backend_name == "cpu"


class TestDispatcherConfig:
    """Tests for DispatcherConfig."""

    def test_config_defaults(self):
        """DispatcherConfig should have sensible defaults."""
        config = DispatcherConfig()
        assert config.preference == BackendPreference.AUTO
        assert config.cuda_min_elements == 10000
        assert config.fallback_to_cpu is True

    def test_config_custom(self):
        """DispatcherConfig should accept custom values."""
        config = DispatcherConfig(
            preference=BackendPreference.CPU,
            cuda_min_elements=1000,
        )
        assert config.preference == BackendPreference.CPU
        assert config.cuda_min_elements == 1000

    def test_dispatcher_with_config(self):
        """Dispatcher should respect configuration."""
        config = DispatcherConfig(preference=BackendPreference.CPU)
        dispatcher = AccelerationDispatcher(config)
        backend = dispatcher.get_backend()
        assert backend.name == "cpu"


class TestDispatcherBenchmark:
    """Tests for dispatcher benchmarking."""

    def test_benchmark_backends(self, dispatcher):
        """benchmark_backends should run without error."""
        results = dispatcher.benchmark_backends(
            shape=(9, 10, 5),
            n_iterations=10,
        )
        assert "cpu" in results
        assert "error" not in results["cpu"]

    def test_format_benchmark_results(self, dispatcher):
        """format_benchmark_results should produce readable output."""
        results = {"cpu": {"add_tensor": 0.001, "multiply_scalar": 0.0005}}
        formatted = dispatcher.format_benchmark_results(results)
        assert "CPU Backend" in formatted
        assert "add_tensor" in formatted


# =============================================================================
# Test Module-Level Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_backend(self):
        """get_backend should return a backend."""
        reset_dispatcher()
        backend = get_backend("cpu")
        assert backend.name == "cpu"

    def test_list_backends(self):
        """list_backends should include CPU."""
        reset_dispatcher()
        backends = list_backends()
        assert "cpu" in backends

    def test_get_cpu_backend(self):
        """get_cpu_backend should return singleton."""
        backend1 = get_cpu_backend()
        backend2 = get_cpu_backend()
        assert backend1 is backend2


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_tensor(self, cpu_backend):
        """Empty tensors should be handled gracefully."""
        arr = np.array([], dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result = cpu_backend.to_numpy(handle)
        assert len(result) == 0

    def test_scalar_tensor(self, cpu_backend):
        """Scalar (0-d) tensors should work."""
        arr = np.array(0.5, dtype=np.float64)
        handle = cpu_backend.from_numpy(arr)
        result = cpu_backend.to_numpy(handle)
        assert result.shape == ()
        assert result == 0.5

    def test_large_tensor(self, cpu_backend):
        """Large tensors should work (memory permitting)."""
        arr = np.random.rand(9, 100, 50).astype(np.float64)
        handle = cpu_backend.from_numpy(arr)
        result = cpu_backend.to_numpy(handle)
        assert result.shape == (9, 100, 50)
        assert_allclose(result, arr)

    def test_unknown_backend(self, dispatcher):
        """Unknown backend should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            dispatcher.get_backend("nonexistent")

    def test_tensor_handle_no_data(self, cpu_backend):
        """TensorHandle with no data should raise on to_numpy."""
        handle = TensorHandle(
            backend_name="cpu",
            device_type=DeviceType.CPU,
            shape=(9,),
            _native_tensor=None,
        )
        with pytest.raises(ValueError, match="no underlying tensor"):
            cpu_backend.to_numpy(handle)


# =============================================================================
# Test SciPy Availability
# =============================================================================


class TestScipyIntegration:
    """Tests for SciPy integration."""

    def test_has_scipy_flag(self):
        """HAS_SCIPY should reflect actual availability."""
        try:
            import scipy  # noqa: F401

            assert HAS_SCIPY is True
        except ImportError:
            assert HAS_SCIPY is False

    @pytest.mark.skipif(not HAS_SCIPY, reason="SciPy not available")
    def test_scipy_sparse_matmul(self, cpu_backend):
        """sparse_matmul should use SciPy when available."""
        # Create sparse matrix A (3x4)
        coords = np.array([[0, 0], [1, 2], [2, 3]], dtype=np.int32)
        values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        shape_a = (3, 4)

        # Dense matrix B (4x2)
        b = np.array([[1, 2], [3, 4], [5, 6], [7, 8]], dtype=np.float64)

        coords_h = cpu_backend.from_numpy(coords)
        values_h = cpu_backend.from_numpy(values)
        b_h = cpu_backend.from_numpy(b)

        result_h = cpu_backend.sparse_matmul(coords_h, values_h, shape_a, b_h)
        result = cpu_backend.to_numpy(result_h)

        # Verify result shape
        assert result.shape == (3, 2)

        # Verify result values (manually computed)
        expected = np.array([[1, 2], [10, 12], [21, 24]], dtype=np.float64)
        assert_allclose(result, expected)


# =============================================================================
# Test CUDA Backend (Sprint 12)
# =============================================================================


# Skip all CUDA tests if CuPy not installed or CUDA not available
SKIP_CUDA = not HAS_CUPY or not cuda_is_available()
CUDA_SKIP_REASON = "CUDA not available (CuPy not installed or no NVIDIA GPU)"


@pytest.fixture
def cuda_backend():
    """Get a fresh CUDA backend instance."""
    if SKIP_CUDA:
        pytest.skip(CUDA_SKIP_REASON)
    return CUDABackend()


class TestCUDABackendAvailability:
    """Tests for CUDA backend availability checking."""

    def test_has_cupy_flag(self):
        """HAS_CUPY should reflect actual availability."""
        try:
            import cupy  # noqa: F401

            assert HAS_CUPY is True
        except ImportError:
            assert HAS_CUPY is False

    def test_cuda_is_available_function(self):
        """cuda_is_available() should return correct status."""
        result = cuda_is_available()
        assert isinstance(result, bool)
        if HAS_CUPY:
            pass  # Result depends on GPU availability
        else:
            assert result is False

    def test_cuda_backend_class_exists(self):
        """CUDABackend class should be importable (may be None)."""
        if HAS_CUPY:
            assert CUDABackend is not None


@pytest.mark.skipif(SKIP_CUDA, reason=CUDA_SKIP_REASON)
class TestCUDABackendCreation:
    """Tests for CUDA backend tensor creation."""

    def test_from_numpy(self, cuda_backend, sample_array):
        """from_numpy should create a TensorHandle on GPU."""
        handle = cuda_backend.from_numpy(sample_array)
        assert handle.backend_name == "cuda"
        assert handle.shape == sample_array.shape

    def test_to_numpy(self, cuda_backend, sample_array):
        """to_numpy should return the same data."""
        handle = cuda_backend.from_numpy(sample_array)
        result = cuda_backend.to_numpy(handle)
        assert_allclose(result, sample_array)

    def test_zeros(self, cuda_backend):
        """zeros should create zero-filled tensor on GPU."""
        handle = cuda_backend.zeros((9, 3))
        result = cuda_backend.to_numpy(handle)
        assert_allclose(result, 0.0)


@pytest.mark.skipif(SKIP_CUDA, reason=CUDA_SKIP_REASON)
class TestCUDABackendOperations:
    """Tests for CUDA backend operations."""

    def test_add_scalar(self, cuda_backend, sample_array):
        """add with scalar should work on GPU."""
        handle = cuda_backend.from_numpy(sample_array)
        result_handle = cuda_backend.add(handle, 0.1)
        result = cuda_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array + 0.1)

    def test_multiply_scalar(self, cuda_backend, sample_array):
        """multiply with scalar should work on GPU."""
        handle = cuda_backend.from_numpy(sample_array)
        result_handle = cuda_backend.multiply(handle, 2.0)
        result = cuda_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array * 2.0)

    def test_sum_axis(self, cuda_backend, sample_array):
        """sum over axis should work on GPU."""
        handle = cuda_backend.from_numpy(sample_array)
        result_handle = cuda_backend.sum(handle, axis=1)
        result = cuda_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array.sum(axis=1))

    def test_clip(self, cuda_backend):
        """clip should clamp values on GPU."""
        arr = np.array([0.0, 0.5, 1.0, 1.5, -0.5], dtype=np.float64)
        handle = cuda_backend.from_numpy(arr)
        result_handle = cuda_backend.clip(handle, 0.0, 1.0)
        result = cuda_backend.to_numpy(result_handle)
        assert_allclose(result, [0.0, 0.5, 1.0, 1.0, 0.0])


@pytest.mark.skipif(SKIP_CUDA, reason=CUDA_SKIP_REASON)
class TestCUDABackendDeviceInfo:
    """Tests for CUDA backend device information."""

    def test_is_available(self, cuda_backend):
        """CUDA backend should be available when fixture succeeds."""
        assert cuda_backend.is_available() is True

    def test_get_device_info(self, cuda_backend):
        """get_device_info should return valid GPU info."""
        info = cuda_backend.get_device_info()
        assert info.device_type == DeviceType.CUDA
        assert info.is_available is True


@pytest.mark.skipif(SKIP_CUDA, reason=CUDA_SKIP_REASON)
class TestDispatcherWithCUDA:
    """Tests for dispatcher with CUDA backend."""

    def test_cuda_in_available_backends(self, dispatcher):
        """CUDA should appear in available backends."""
        backends = dispatcher.get_available_backends()
        assert "cuda" in backends

    def test_get_cuda_backend(self, dispatcher):
        """get_backend('cuda') should return CUDA backend."""
        backend = dispatcher.get_backend("cuda")
        assert backend.name == "cuda"


# =============================================================================
# Test Jetson Backend (Sprint 13)
# =============================================================================


# Skip all Jetson tests if not on Jetson hardware
SKIP_JETSON = not HAS_JETSON or not jetson_is_available()
JETSON_SKIP_REASON = "Jetson not available (not on Jetson hardware)"


@pytest.fixture
def jetson_backend():
    """Get a fresh Jetson backend instance."""
    if SKIP_JETSON:
        pytest.skip(JETSON_SKIP_REASON)
    return JetsonBackend()


class TestJetsonBackendAvailability:
    """Tests for Jetson backend availability checking."""

    def test_has_jetson_flag(self):
        """HAS_JETSON should reflect hardware detection."""
        # Just verify it's a boolean
        assert isinstance(HAS_JETSON, bool)

    def test_jetson_is_available_function(self):
        """jetson_is_available() should return correct status."""
        result = jetson_is_available()
        assert isinstance(result, bool)
        # Should be False on non-Jetson hardware
        if not HAS_JETSON:
            assert result is False

    def test_jetson_backend_class_exists(self):
        """JetsonBackend class should be importable (may be None)."""
        # JetsonBackend should exist even if not on Jetson
        assert JetsonBackend is not None


@pytest.mark.skipif(SKIP_JETSON, reason=JETSON_SKIP_REASON)
class TestJetsonBackendCreation:
    """Tests for Jetson backend tensor creation."""

    def test_from_numpy(self, jetson_backend, sample_array):
        """from_numpy should create a TensorHandle on Jetson."""
        handle = jetson_backend.from_numpy(sample_array)
        assert handle.backend_name == "jetson"
        assert handle.shape == sample_array.shape

    def test_to_numpy(self, jetson_backend, sample_array):
        """to_numpy should return the same data."""
        handle = jetson_backend.from_numpy(sample_array)
        result = jetson_backend.to_numpy(handle)
        assert_allclose(result, sample_array)

    def test_zeros(self, jetson_backend):
        """zeros should create zero-filled tensor."""
        handle = jetson_backend.zeros((9, 3))
        result = jetson_backend.to_numpy(handle)
        assert_allclose(result, 0.0)


@pytest.mark.skipif(SKIP_JETSON, reason=JETSON_SKIP_REASON)
class TestJetsonBackendOperations:
    """Tests for Jetson backend operations."""

    def test_add_scalar(self, jetson_backend, sample_array):
        """add with scalar should work on Jetson."""
        handle = jetson_backend.from_numpy(sample_array)
        result_handle = jetson_backend.add(handle, 0.1)
        result = jetson_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array + 0.1)

    def test_multiply_scalar(self, jetson_backend, sample_array):
        """multiply with scalar should work on Jetson."""
        handle = jetson_backend.from_numpy(sample_array)
        result_handle = jetson_backend.multiply(handle, 2.0)
        result = jetson_backend.to_numpy(result_handle)
        assert_allclose(result, sample_array * 2.0)

    def test_clip(self, jetson_backend):
        """clip should clamp values on Jetson."""
        arr = np.array([0.0, 0.5, 1.0, 1.5, -0.5], dtype=np.float64)
        handle = jetson_backend.from_numpy(arr)
        result_handle = jetson_backend.clip(handle, 0.0, 1.0)
        result = jetson_backend.to_numpy(result_handle)
        assert_allclose(result, [0.0, 0.5, 1.0, 1.0, 0.0])


@pytest.mark.skipif(SKIP_JETSON, reason=JETSON_SKIP_REASON)
class TestJetsonBackendDeviceInfo:
    """Tests for Jetson backend device information."""

    def test_is_available(self, jetson_backend):
        """Jetson backend should be available when fixture succeeds."""
        assert jetson_backend.is_available() is True

    def test_get_device_info(self, jetson_backend):
        """get_device_info should return valid Jetson info."""
        info = jetson_backend.get_device_info()
        assert info.device_type == DeviceType.JETSON
        assert info.is_available is True


@pytest.mark.skipif(SKIP_JETSON, reason=JETSON_SKIP_REASON)
class TestDispatcherWithJetson:
    """Tests for dispatcher with Jetson backend."""

    def test_jetson_in_available_backends(self, dispatcher):
        """Jetson should appear in available backends."""
        backends = dispatcher.get_available_backends()
        assert "jetson" in backends

    def test_get_jetson_backend(self, dispatcher):
        """get_backend('jetson') should return Jetson backend."""
        backend = dispatcher.get_backend("jetson")
        assert backend.name == "jetson"
