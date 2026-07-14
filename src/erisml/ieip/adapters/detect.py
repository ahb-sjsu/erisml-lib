# ErisML I-EIP Monitor: adapter auto-detection
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Auto-detect the right :class:`IEIPAdapter` for a given model object.

Detection is structural: we inspect the object's type and attributes
rather than relying on a string registry. That keeps
:func:`detect_adapter` working for models the caller didn't
pre-register (e.g., a third-party fine-tune of Llama).

Detection order (first match wins):

1. If the object is already an :class:`IEIPAdapter`, return it.
2. If it's a sequence of :class:`~.ensemble.EnsembleMember`, build an
   :class:`~.ensemble.EnsembleAdapter`.
3. If it's a ``torch.nn.Module`` and has a transformer-block list,
   build an :class:`~.hf_transformer.HFTransformerAdapter`.
4. If it's callable or exposes ``.generate``, wrap it as an
   :class:`~.api_passthrough.APIPassthroughAdapter`.
5. Otherwise, raise :class:`AdapterDetectionError`.
"""

from __future__ import annotations

from typing import Any, Sequence

from erisml.ieip.adapters.api_passthrough import APIPassthroughAdapter
from erisml.ieip.adapters.base import IEIPAdapter
from erisml.ieip.adapters.ensemble import EnsembleAdapter, EnsembleMember


class AdapterDetectionError(TypeError):
    """Raised when :func:`detect_adapter` can't pick an adapter."""


def _is_ensemble_member_seq(obj: Any) -> bool:
    """True if ``obj`` is a non-empty sequence of :class:`EnsembleMember`."""
    if isinstance(obj, (list, tuple)) and len(obj) > 0:
        return all(isinstance(m, EnsembleMember) for m in obj)
    return False


def _is_torch_module(obj: Any) -> bool:
    """Safe ``isinstance(obj, nn.Module)`` that tolerates missing torch."""
    try:
        import torch  # noqa: F401  (optional dependency)
        from torch import nn
    except ImportError:  # pragma: no cover - torch is optional
        return False
    return isinstance(obj, nn.Module)


def detect_adapter(
    model: Any,
    *,
    name: str | None = None,
) -> IEIPAdapter:
    """Return an :class:`IEIPAdapter` for ``model``.

    Parameters
    ----------
    model:
        Anything the detection rules above can handle.
    name:
        Optional friendly name. Passed to adapters that accept one
        (API passthrough, ensemble). Ignored by the HF adapter.

    Returns
    -------
    adapter:
        A concrete adapter instance. Already validated -- callers do
        not need to re-check capabilities before first use.

    Raises
    ------
    AdapterDetectionError:
        If no adapter applies. The exception message lists the
        candidates that were considered, for easier debugging.

    Examples
    --------
    >>> from erisml.ieip.adapters import detect_adapter
    >>> adapter = detect_adapter(my_model)                # doctest: +SKIP
    >>> adapter.model_family                               # doctest: +SKIP
    'hf-transformer'
    """
    # (1) Already an adapter -- pass through.
    if isinstance(model, IEIPAdapter) and not isinstance(model, type):
        return model

    # (2) Ensemble of members.
    if _is_ensemble_member_seq(model):
        return EnsembleAdapter(model=None, members=list(model), name=name or "ensemble")

    # (3) Torch module.
    if _is_torch_module(model):
        # Import here so this module still loads without torch.
        from erisml.ieip.adapters.hf_transformer import (
            HFTransformerAdapter,
            _find_blocks,
        )

        if _find_blocks(model) is not None:
            return HFTransformerAdapter(model=model)
        raise AdapterDetectionError(
            f"torch module {type(model).__name__} has no recognizable "
            "transformer-block layout; pass an HFTransformerAdapter "
            "with block_path= explicitly if you know where blocks live."
        )

    # (4) Callable / has generate() -- API passthrough.
    if callable(model) or hasattr(model, "generate"):
        return APIPassthroughAdapter(model=model, name=name or "api")

    # (5) Nothing matched.
    raise AdapterDetectionError(
        f"no I-EIP adapter applies to {type(model).__name__!r}. "
        "Candidates tried: IEIPAdapter, EnsembleMember sequence, "
        "torch.nn.Module, callable/.generate."
    )


def describe_adapter(adapter: IEIPAdapter) -> dict[str, Any]:
    """Return a short dict summary of an adapter for logs/dashboards.

    Used by the Atlas dashboard card to label each monitored subsystem
    with its family + site count + capability flags without having to
    know adapter-specific types.
    """
    caps = adapter.capabilities
    try:
        n_sites = len(adapter.list_sites())
    except Exception:  # pragma: no cover - defensive
        n_sites = -1
    return {
        "model_family": adapter.model_family,
        "num_layers": adapter.num_layers(),
        "num_sites": n_sites,
        "supports_direct_hook": caps.supports_direct_hook,
        "supports_output_distribution": caps.supports_output_distribution,
        "supports_transform_execution": caps.supports_transform_execution,
    }


def _detect_hf_lineage(model: Any) -> Sequence[str]:  # pragma: no cover - utility
    """Heuristic: guess HF lineage names from a torch module.

    Used by reports to tag probes with a user-friendly model family
    string (``"Llama"``, ``"Qwen"``, ``"Gemma"``, ...). Best-effort:
    checks class name substrings, then ``config.model_type`` if
    present.
    """
    cls = type(model).__name__.lower()
    for lineage in ("llama", "qwen", "gemma", "mistral", "phi", "glm", "deepseek"):
        if lineage in cls:
            return [lineage]
    cfg = getattr(model, "config", None)
    mt = getattr(cfg, "model_type", None)
    if isinstance(mt, str) and mt:
        return [mt]
    return []
