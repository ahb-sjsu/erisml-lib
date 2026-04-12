# ErisML I-EIP Monitor: PyTorch activation probes
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Read-only activation probes for PyTorch models.

An :class:`ActivationProbe` wraps ``torch.nn.Module.register_forward_hook``
with the read-only, fail-closed, shape-validated semantics required by
the I-EIP Monitor (see I-EIP Monitor Whitepaper §2.3).

Key invariants:

* Probes never mutate activations. Hooks return ``None`` so the
  forward pass continues with the original tensor.
* On any probe-internal failure (shape mismatch, allocation error,
  etc.), the probe marks itself failed and the downstream gating
  layer is expected to fail-closed.
* Probes are batched observers; they accumulate tensors in a buffer
  for later aggregation rather than computing metrics inside the
  forward pass (which would dominate latency and risk interfering
  with autograd).

This module imports ``torch`` lazily. ``import erisml.ieip.probes``
will raise :exc:`ImportError` if PyTorch is not installed, but
``import erisml.ieip`` does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List

try:
    import torch
    from torch import nn
except ImportError as e:  # pragma: no cover - import-guard
    raise ImportError(
        "erisml.ieip.probes requires PyTorch. "
        "Install with: pip install 'erisml-lib[ieip]'"
    ) from e

import numpy as np

from erisml.ieip.types import ActivationSite, ProbeSpec

if TYPE_CHECKING:
    # For type hints only; avoids runtime import cost.
    from torch import Tensor


@dataclass
class _ProbeBuffer:
    """Internal storage for activations captured by one probe.

    Activations are kept as detached CPU float32 numpy arrays to
    decouple them from autograd and GPU state. For very large models
    this is deliberate: we accept the H2D copy cost to keep probe
    state inspectable from out-of-model code.
    """

    activations: List[np.ndarray] = field(default_factory=list)
    calls: int = 0
    failures: int = 0
    last_failure: str = ""


class ActivationProbe:
    """Read-only activation probe for one module in a PyTorch model.

    Parameters
    ----------
    module:
        The ``torch.nn.Module`` to probe. Typically a transformer
        block or an output-norm layer.
    spec:
        The :class:`~erisml.ieip.types.ProbeSpec` describing what and
        how to probe.

    Examples
    --------
    >>> import torch.nn as nn
    >>> from erisml.ieip import ActivationProbe, ProbeSpec
    >>> model = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 2))
    >>> spec = ProbeSpec(target_layer=1, name="relu")
    >>> probe = ActivationProbe(model[1], spec)
    >>> probe.attach()
    >>> _ = model(torch.randn(3, 4))
    >>> acts = probe.collected()
    >>> acts.shape
    (3, 8)
    >>> probe.detach()
    """

    def __init__(self, module: "nn.Module", spec: ProbeSpec) -> None:
        self.module = module
        self.spec = spec
        self._handle: Any | None = None
        self._buffer = _ProbeBuffer()
        self._rng = np.random.default_rng(seed=None)
        self._failed = False

    def attach(self) -> None:
        """Register the forward hook on the target module.

        Idempotent: calling ``attach`` twice does not double-register.
        """
        if self._handle is not None:
            return
        self._handle = self.module.register_forward_hook(self._hook)

    def detach(self) -> None:
        """Remove the forward hook.

        Always safe to call, even if never attached.
        """
        if self._handle is not None:
            self._handle.remove()
            self._handle = None

    @property
    def attached(self) -> bool:
        """Whether the probe is currently attached to its module."""
        return self._handle is not None

    @property
    def failed(self) -> bool:
        """Whether the probe has entered a permanent failed state.

        Once failed, the probe stops recording and downstream code
        should treat this inference as un-gated (fail-closed).
        """
        return self._failed

    @property
    def call_count(self) -> int:
        """Number of forward passes observed (including skipped ones)."""
        return self._buffer.calls

    @property
    def failure_count(self) -> int:
        """Number of per-call failures."""
        return self._buffer.failures

    @property
    def last_failure(self) -> str:
        """Message from the most recent failure, or empty string."""
        return self._buffer.last_failure

    def collected(self) -> np.ndarray:
        """Return all collected activations stacked along the sample axis.

        Returns
        -------
        array:
            Shape ``(sum_of_batches * seq_if_any, d)``. Trailing dims
            are flattened into the sample dim so downstream code (ρ
            estimation, equivariance) can operate on ``(n, d)``.

        Raises
        ------
        RuntimeError:
            If no activations have been collected.
        """
        if not self._buffer.activations:
            raise RuntimeError(f"probe {self.spec.name!r} has no collected activations")
        # Each entry is already shape (batch*..., d); concatenate.
        return np.concatenate(self._buffer.activations, axis=0)

    def clear(self) -> None:
        """Drop collected activations but keep counters.

        Useful between inference batches.
        """
        self._buffer.activations.clear()

    # ---- internals ----------------------------------------------------

    def _hook(
        self,
        _module: "nn.Module",
        _inputs: tuple[Any, ...],
        output: Any,
    ) -> None:
        """Forward hook callback. Returns None (read-only)."""
        self._buffer.calls += 1
        if self._failed:
            return None
        # Subsampling
        if self.spec.sampling_rate < 1.0:
            if self._rng.random() > self.spec.sampling_rate:
                return None
        try:
            tensor = self._extract_tensor(output)
            self._validate_shape(tensor)
            arr = self._to_numpy(tensor)
            self._buffer.activations.append(arr)
        except Exception as exc:  # pragma: no cover - defensive
            self._buffer.failures += 1
            self._buffer.last_failure = f"{type(exc).__name__}: {exc}"
            # Too many failures → mark probe failed (fail-closed).
            if self._buffer.failures > max(3, self._buffer.calls // 10):
                self._failed = True
        return None

    def _extract_tensor(self, output: Any) -> "Tensor":
        """Pull the activation tensor out of the module's output.

        Transformer blocks often return tuples or dict-like structures.
        We pick the first tensor we find. For cases where the desired
        tensor is not the first, users should probe a more specific
        submodule.
        """
        if isinstance(output, torch.Tensor):
            return output
        if isinstance(output, tuple) and output:
            for item in output:
                if isinstance(item, torch.Tensor):
                    return item
        if isinstance(output, dict):
            for v in output.values():
                if isinstance(v, torch.Tensor):
                    return v
        raise TypeError(
            f"module output is not a tensor or a structure containing one "
            f"(got {type(output).__name__})"
        )

    def _validate_shape(self, tensor: "Tensor") -> None:
        """Assert the activation shape matches ``expected_shape`` if set."""
        if self.spec.expected_shape is None:
            return
        # Compare trailing dims only (batch/seq are free).
        exp = tuple(self.spec.expected_shape)
        actual = tuple(tensor.shape)
        if len(actual) < len(exp) or actual[-len(exp) :] != exp:
            raise ValueError(
                f"activation shape {actual} does not match expected "
                f"trailing shape {exp}"
            )

    def _to_numpy(self, tensor: "Tensor") -> np.ndarray:
        """Detach, move to CPU, convert to numpy float32.

        We flatten everything but the last dim into the sample dim so
        downstream ρ estimation can work on ``(n, d)`` matrices.
        """
        with torch.no_grad():
            cpu = tensor.detach().to("cpu").float()
        arr = cpu.numpy()
        if arr.ndim < 2:
            arr = arr.reshape(1, -1)
        else:
            n_feat = arr.shape[-1]
            arr = arr.reshape(-1, n_feat)
        return arr


class ProbeManager:
    """Coordinated lifecycle for a set of :class:`ActivationProbe`.

    Typical usage::

        mgr = ProbeManager()
        mgr.add(model.blocks[0], ProbeSpec(target_layer=0, name="b0"))
        mgr.add(model.blocks[5], ProbeSpec(target_layer=5, name="b5"))
        with mgr.active():
            _ = model(input_ids)
            acts = mgr.collected()

    The context manager handles ``attach`` and ``detach`` automatically.
    """

    def __init__(self) -> None:
        self._probes: Dict[str, ActivationProbe] = {}

    def add(self, module: "nn.Module", spec: ProbeSpec) -> ActivationProbe:
        """Register a new probe. Returns the probe for convenience."""
        key = spec.name or f"layer_{spec.target_layer}_{spec.activation_site}"
        if key in self._probes:
            raise KeyError(f"probe with name {key!r} already registered")
        probe = ActivationProbe(module=module, spec=spec)
        self._probes[key] = probe
        return probe

    def get(self, name: str) -> ActivationProbe:
        """Retrieve a registered probe by name."""
        return self._probes[name]

    def names(self) -> List[str]:
        """Return all registered probe names in insertion order."""
        return list(self._probes.keys())

    def attach_all(self) -> None:
        """Attach every registered probe."""
        for p in self._probes.values():
            p.attach()

    def detach_all(self) -> None:
        """Detach every registered probe."""
        for p in self._probes.values():
            p.detach()

    def clear_all(self) -> None:
        """Clear buffered activations on every probe."""
        for p in self._probes.values():
            p.clear()

    def collected(self) -> Dict[str, np.ndarray]:
        """Return all collected activations keyed by probe name."""
        return {name: p.collected() for name, p in self._probes.items()}

    def any_failed(self) -> bool:
        """Whether any probe has entered the failed state."""
        return any(p.failed for p in self._probes.values())

    def active(self) -> "_ProbeManagerContext":
        """Context manager that attaches on enter, detaches on exit."""
        return _ProbeManagerContext(self)


class _ProbeManagerContext:
    """Support context object for :meth:`ProbeManager.active`."""

    def __init__(self, manager: ProbeManager) -> None:
        self._manager = manager

    def __enter__(self) -> ProbeManager:
        self._manager.attach_all()
        return self._manager

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: Any,
    ) -> None:
        self._manager.detach_all()


# Optional helper for framework-specific activation sites.
_SITE_DISPATCH: Dict[ActivationSite, Callable[["nn.Module"], "nn.Module"]] = {}
"""Registry that maps :class:`ActivationSite` values to the submodule
within a block that should be probed for that site.

This is a tiny extension point: framework-specific adapter packages can
register a dispatch function so users can specify an activation site
(``"residual"``, ``"attn_out"``, ...) and have it resolved to the right
submodule automatically. Left empty by default so the core package has
no framework-specific knowledge baked in.
"""
