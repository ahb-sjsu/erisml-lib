# ErisML I-EIP Monitor: API-passthrough adapter
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Adapter for black-box model APIs where weights aren't reachable.

Covers the NRP-hosted frontier models (glm-4.7, qwen3, minimax-m2,
kimi, gpt-oss, olmo) plus any OpenAI-compatible provider. These
models expose only an input-prompt / output-tokens interface -- we
cannot hook into activations, so direct equivariance of internal
representations is impossible.

Instead the adapter computes equivariance on the **output
distribution**: if the model is faithful to its training, then
meaning-preserving transformations of the input should produce
approximately the same output distribution (within a known bounded
distortion). The adapter exposes this as :meth:`output_distribution`
and :meth:`run_transformed`, while reporting
``supports_direct_hook=False``.

This is strictly weaker than internal equivariance. The
:class:`APIPassthroughAdapter` is a fallback -- the main I-EIP monitor
prefers direct-hook adapters when available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Iterable, Protocol, runtime_checkable

import numpy as np

from erisml.ieip.adapters.base import (
    AdapterCapabilities,
    BaseAdapter,
    ProbeSite,
    register_adapter,
)
from erisml.ieip.types import ActivationSite, ProbeSpec


@runtime_checkable
class APIClient(Protocol):
    """Minimal protocol an API client must satisfy.

    Real clients (OpenAI SDK, HF Inference API, NRP provider) all
    satisfy this via wrappers. Tests can pass a callable or a
    :class:`~dataclasses.dataclass` with a ``__call__``.

    The adapter only needs one method: given an input (typically a
    string or dict), return either a logprob distribution over tokens
    (preferred) or a single generated string (fallback).
    """

    def generate(self, inputs: Any) -> Any:
        """Return model output for ``inputs``.

        The return value can be:

        * A numpy array of shape ``(vocab_size,)`` -- a full
          next-token distribution. Best for equivariance.
        * A dict with ``"logprobs"`` key containing such an array.
        * A plain string -- the adapter will fall back to a
          per-character histogram.
        """
        ...


def _as_distribution(output: Any) -> np.ndarray | None:
    """Coerce an arbitrary client return into a probability vector.

    Priority:

    1. ``numpy.ndarray`` (treated as logits/probs; normalized).
    2. ``dict`` with ``"logprobs"`` / ``"probs"`` / ``"distribution"``
       key.
    3. ``str`` -- character-histogram over printable ASCII.

    Returns ``None`` for anything else (the caller decides whether to
    raise or skip).
    """
    if isinstance(output, np.ndarray):
        return _normalize(output)
    if isinstance(output, dict):
        for key in ("logprobs", "probs", "distribution"):
            if key in output:
                arr = np.asarray(output[key], dtype=np.float64)
                return _normalize(arr)
        return None
    if isinstance(output, str):
        # Fallback: histogram over 128 ASCII codepoints. Very coarse;
        # only useful when the client really returns only a string.
        hist = np.zeros(128, dtype=np.float64)
        for ch in output:
            code = ord(ch)
            if 0 <= code < 128:
                hist[code] += 1.0
        total = hist.sum()
        if total == 0:
            return None
        return hist / total
    return None


def _normalize(x: np.ndarray) -> np.ndarray:
    """Clamp to probabilities. Accepts logits or already-normalized."""
    x = x.astype(np.float64, copy=False)
    if x.ndim == 0:
        return np.array([1.0])
    if x.ndim > 1:
        x = x.reshape(-1)
    if (x >= 0).all() and abs(x.sum() - 1.0) < 1e-3:
        return x  # already a probability vector
    # Treat as logits.
    x = x - x.max()
    e = np.exp(x)
    s = e.sum()
    if s == 0:
        return np.full_like(x, 1.0 / len(x))
    return e / s


@dataclass
class APIPassthroughAdapter(BaseAdapter):
    """Adapter for black-box model APIs.

    Parameters
    ----------
    model:
        The API client. Must either implement :class:`APIClient`
        (i.e. have a ``generate(inputs)`` method) or be callable
        directly.
    name:
        Human-readable identifier (e.g., ``"glm-4.7"``). Used in
        :class:`ProbeSite` names even though no real sites exist.
    """

    model_family: ClassVar[str] = "api-passthrough"
    name: str = "api"

    def __post_init__(self) -> None:
        if not (callable(self.model) or hasattr(self.model, "generate")):
            raise TypeError(
                "APIPassthroughAdapter requires a callable or an object with "
                f"a .generate(inputs) method (got {type(self.model).__name__})"
            )
        self._caps = AdapterCapabilities(
            supports_direct_hook=False,
            supports_output_distribution=True,
            supports_transform_execution=True,
        )

    # ── Introspection -----------------------------------------------------

    def num_layers(self) -> int:
        """Black-box API: number of layers is unknown. Returns -1."""
        return -1

    def list_sites(
        self,
        *,
        layers: Iterable[int] | None = None,  # noqa: ARG002 (kept for protocol parity)
        kinds: Iterable[ActivationSite] | None = None,  # noqa: ARG002
    ) -> list[ProbeSite]:
        """API adapters expose no internal probe sites.

        Returns an empty list regardless of filter arguments. Callers
        that see an empty list should fall back to the
        output-distribution equivariance path (see
        :meth:`output_distribution`).
        """
        return []

    def resolve_site(self, site: ProbeSite) -> Any | None:  # noqa: ARG002
        """Always ``None`` -- no internal modules to return."""
        return None

    def attach_probes(
        self,
        sites: Iterable[ProbeSite],  # noqa: ARG002
        spec_factory: Callable[[ProbeSite], ProbeSpec],  # noqa: ARG002
    ) -> Any:
        raise NotImplementedError(
            "APIPassthroughAdapter cannot attach forward hooks. "
            "Use output_distribution() / run_transformed() instead."
        )

    # ── Output-distribution path -----------------------------------------

    def output_distribution(self, inputs: Any) -> np.ndarray | None:
        """Call the client and coerce its return to a probability vector.

        Returns ``None`` if the client returns a shape we can't parse.
        In that case the monitor records a "no-signal" event rather
        than raising -- black-box APIs are occasionally flaky.
        """
        raw = self._call(inputs)
        return _as_distribution(raw)

    def run_transformed(self, inputs: Any, transform: Callable[[Any], Any]) -> Any:
        """Apply ``transform`` to the prompt, then call the client."""
        return self._call(transform(inputs))

    # ── Internals --------------------------------------------------------

    def _call(self, inputs: Any) -> Any:
        """Invoke the client's ``generate`` (or call it directly)."""
        if hasattr(self.model, "generate"):
            return self.model.generate(inputs)
        return self.model(inputs)


register_adapter(APIPassthroughAdapter)
