# ErisML I-EIP Monitor: architecture adapter protocol
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Architecture-agnostic adapter protocol for I-EIP probes.

The core I-EIP primitives (``probes.ActivationProbe``, ``rho``,
``equivariance``, ``drift``) are architecture-agnostic at the PyTorch
level: they take any ``nn.Module`` + ``numpy`` arrays and know nothing
about where those activations came from.

An :class:`IEIPAdapter` bridges the architecture-specific gap --
translating semantic probe requests (``"give me the post-residual
activation at layer 14"``) into concrete attachment points on a given
model family.

Three failure modes motivate this layer:

* Different families name layers differently (``model.model.layers``
  for Llama-lineage, ``transformer.h`` for GPT-2, ``layers`` at the
  top level for some bespoke models).
* Some deployments expose only a black-box API (OpenAI-compatible,
  NRP-hosted models). These cannot be hooked; equivariance must be
  inferred from output distributions.
* Ensembles (e.g. the Atlas AI Divine Council) have *no* single model
  to probe; the "equivariance" signal lives in the vote distribution
  over multiple advocates.

This module defines the protocol; concrete adapters live in sibling
modules (``hf_transformer``, ``api_passthrough``, ``ensemble``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Mapping,
    Protocol,
    runtime_checkable,
)

import numpy as np

from erisml.ieip.types import ActivationSite, ProbeSpec

# ── Probe sites --------------------------------------------------------------


@dataclass(frozen=True)
class ProbeSite:
    """Architecture-agnostic description of a probe attachment point.

    A :class:`ProbeSite` is what :meth:`IEIPAdapter.list_sites` returns
    and what callers pass back in to request a specific probe. It is
    intentionally opaque to the caller: the ``submodule_path`` lets an
    adapter resolve the site back to a concrete module, while
    ``layer_index`` / ``kind`` give the caller enough to identify it
    in reports.

    Parameters
    ----------
    layer_index:
        Zero-based index of the layer this site lives in. For
        ensembles this is the advocate index. For output-only adapters
        this is ``-1`` to signal "no internal site".
    kind:
        Semantic activation-site label from
        :data:`~erisml.ieip.types.ActivationSite`.
    submodule_path:
        Adapter-private dotted path that :meth:`IEIPAdapter.resolve_site`
        uses to find the module. Callers should treat it as opaque.
    name:
        Human-readable identifier used in reports.
    expected_shape:
        Optional trailing-dim shape assertion (passed to the probe).
    """

    layer_index: int
    kind: ActivationSite
    submodule_path: str
    name: str
    expected_shape: tuple[int, ...] | None = None


# ── Capability flags ---------------------------------------------------------


@dataclass(frozen=True)
class AdapterCapabilities:
    """What a given adapter can and cannot do.

    Callers should branch on these flags rather than trying every
    method and catching exceptions. For instance, an API-passthrough
    adapter sets ``supports_direct_hook=False`` and consumers use the
    output-distribution equivariance path instead.

    Parameters
    ----------
    supports_direct_hook:
        Whether :meth:`IEIPAdapter.attach_probes` can return a
        :class:`~erisml.ieip.probes.ProbeManager` of real forward
        hooks. False for API-only and ensemble-vote adapters.
    supports_output_distribution:
        Whether the adapter can return a probability/logit vector for
        a given input -- the fallback equivariance signal when hooks
        are unavailable.
    supports_transform_execution:
        Whether the adapter's :meth:`run_transformed` can run the
        model on ``g·x`` without the caller having to orchestrate it.
        (Some API surfaces require the caller to apply the transform
        themselves before calling the adapter.)
    """

    supports_direct_hook: bool
    supports_output_distribution: bool
    supports_transform_execution: bool


# ── Adapter protocol ---------------------------------------------------------


@runtime_checkable
class IEIPAdapter(Protocol):
    """Architecture adapter for the I-EIP monitor.

    Concrete adapters translate between the architecture-agnostic core
    (``probes``, ``rho``, ``equivariance``, ``drift``) and a specific
    model family's attachment + execution API.

    See :class:`BaseAdapter` for a convenience base that implements
    common validation boilerplate.

    Examples
    --------
    >>> from erisml.ieip.adapters import detect_adapter
    >>> adapter = detect_adapter(my_model)              # doctest: +SKIP
    >>> sites = adapter.list_sites()                     # doctest: +SKIP
    >>> mgr = adapter.attach_probes(                     # doctest: +SKIP
    ...     sites[:3],
    ...     lambda s: ProbeSpec(target_layer=s.layer_index, name=s.name),
    ... )
    """

    model_family: ClassVar[str]
    """Identifier like ``"hf-transformer"`` or ``"ensemble"``. Used in
    reports and auto-detection."""

    @property
    def capabilities(self) -> AdapterCapabilities:
        """Return this adapter's capability flags."""
        ...

    def num_layers(self) -> int:
        """Number of addressable layers. ``-1`` if indeterminate (API)."""
        ...

    def list_sites(
        self,
        *,
        layers: Iterable[int] | None = None,
        kinds: Iterable[ActivationSite] | None = None,
    ) -> list[ProbeSite]:
        """Enumerate the probe attachment points on this model.

        Parameters
        ----------
        layers:
            If given, only return sites for these layer indices.
        kinds:
            If given, only return sites whose ``kind`` is in this set.

        Returns
        -------
        sites:
            A list of :class:`ProbeSite`. May be empty for adapters
            without internal access (e.g., API passthrough).
        """
        ...

    def resolve_site(self, site: ProbeSite) -> Any | None:
        """Resolve a site back to the concrete attachment target.

        For PyTorch adapters this returns an ``nn.Module``. For
        adapters without direct-hook support it returns ``None``.
        """
        ...

    def attach_probes(
        self,
        sites: Iterable[ProbeSite],
        spec_factory: Callable[[ProbeSite], ProbeSpec],
    ) -> Any:
        """Attach probes at the given sites, return a manager object.

        For direct-hook adapters this returns a
        :class:`~erisml.ieip.probes.ProbeManager`. For other adapters
        it returns whatever lifecycle object the adapter uses to
        collect activations (or raises if unsupported).
        """
        ...

    def output_distribution(self, inputs: Any) -> np.ndarray | None:
        """Return a numeric output distribution for ``inputs``.

        Used as the equivariance signal when direct hooks aren't
        available. Returns ``None`` if the adapter can't produce one.
        """
        ...

    def run_transformed(self, inputs: Any, transform: Callable[[Any], Any]) -> Any:
        """Run the model on ``transform(inputs)``.

        The adapter is responsible for whatever plumbing that takes
        (re-tokenizing for text models, re-sampling for image models,
        etc.). Returns the same type as a normal forward pass.
        """
        ...


# ── Convenience base ---------------------------------------------------------


@dataclass
class BaseAdapter:
    """Convenience base with shared validation + simple defaults.

    Subclasses override :meth:`num_layers`, :meth:`list_sites`,
    :meth:`resolve_site`, :meth:`attach_probes`, and set
    ``model_family``. Everything else gets sensible defaults.
    """

    model: Any
    model_family: ClassVar[str] = "unknown"
    _caps: AdapterCapabilities = field(
        default_factory=lambda: AdapterCapabilities(
            supports_direct_hook=False,
            supports_output_distribution=False,
            supports_transform_execution=False,
        )
    )

    @property
    def capabilities(self) -> AdapterCapabilities:
        """Return this adapter's capabilities."""
        return self._caps

    def num_layers(self) -> int:  # pragma: no cover - abstract
        raise NotImplementedError

    def list_sites(
        self,
        *,
        layers: Iterable[int] | None = None,
        kinds: Iterable[ActivationSite] | None = None,
    ) -> list[ProbeSite]:  # pragma: no cover - abstract
        raise NotImplementedError

    def resolve_site(
        self, site: ProbeSite
    ) -> Any | None:  # pragma: no cover - abstract
        raise NotImplementedError

    def attach_probes(
        self,
        sites: Iterable[ProbeSite],
        spec_factory: Callable[[ProbeSite], ProbeSpec],
    ) -> Any:
        if not self._caps.supports_direct_hook:
            raise NotImplementedError(
                f"{type(self).__name__} does not support direct hooks "
                f"(capability 'supports_direct_hook' is False)"
            )
        raise NotImplementedError  # subclass must override if supported

    def output_distribution(self, inputs: Any) -> np.ndarray | None:
        """Default implementation: not supported."""
        return None

    def run_transformed(self, inputs: Any, transform: Callable[[Any], Any]) -> Any:
        """Default: apply the transform and re-run. Subclasses may override."""
        if not self._caps.supports_transform_execution:
            raise NotImplementedError(
                f"{type(self).__name__} does not support transform execution"
            )
        return self._forward(transform(inputs))

    # ── Helpers subclasses can use or override -----------------------------

    def _forward(self, inputs: Any) -> Any:  # pragma: no cover - abstract
        """Run a plain forward pass. Used by :meth:`run_transformed`."""
        raise NotImplementedError

    # ── Shared site filtering helper ---------------------------------------

    @staticmethod
    def _filter_sites(
        sites: Iterable[ProbeSite],
        *,
        layers: Iterable[int] | None,
        kinds: Iterable[ActivationSite] | None,
    ) -> list[ProbeSite]:
        """Apply ``layers`` and ``kinds`` filters consistently.

        Concrete adapters call this at the end of their ``list_sites``
        override so filtering behaves uniformly across families.
        """
        layer_set = set(layers) if layers is not None else None
        kind_set: set[str] | None = set(kinds) if kinds is not None else None
        out: list[ProbeSite] = []
        for s in sites:
            if layer_set is not None and s.layer_index not in layer_set:
                continue
            if kind_set is not None and s.kind not in kind_set:
                continue
            out.append(s)
        return out


# ── Adapter registry ---------------------------------------------------------


_REGISTRY: dict[str, type] = {}


def register_adapter(adapter_cls: type) -> type:
    """Register an adapter class under its ``model_family`` key.

    Usable as a decorator. Raises if the family is already registered
    -- registration is idempotent only if ``adapter_cls`` is the same
    class that was previously registered.

    Parameters
    ----------
    adapter_cls:
        An :class:`IEIPAdapter`-conforming class with a class-level
        ``model_family`` attribute.

    Returns
    -------
    adapter_cls:
        The input class, unchanged (so this works as a decorator).
    """
    family = getattr(adapter_cls, "model_family", None)
    if not family or family == "unknown":
        raise ValueError(
            f"{adapter_cls.__name__} must set a non-empty model_family class attribute"
        )
    existing = _REGISTRY.get(family)
    if existing is not None and existing is not adapter_cls:
        raise ValueError(
            f"model_family {family!r} is already registered to {existing.__name__}"
        )
    _REGISTRY[family] = adapter_cls
    return adapter_cls


def registered_adapters() -> Mapping[str, type]:
    """Return a read-only view of the adapter registry.

    Useful for introspection and tests. The mapping key is the
    ``model_family`` string; the value is the adapter class.
    """
    return dict(_REGISTRY)


def get_adapter(family: str) -> type:
    """Look up a registered adapter class by family name.

    Raises :class:`KeyError` if no adapter is registered under
    ``family``. Callers that want auto-detection should use
    :func:`~erisml.ieip.adapters.detect.detect_adapter` instead.
    """
    try:
        return _REGISTRY[family]
    except KeyError as exc:
        raise KeyError(
            f"no adapter registered for model_family {family!r}; "
            f"known: {sorted(_REGISTRY)}"
        ) from exc
