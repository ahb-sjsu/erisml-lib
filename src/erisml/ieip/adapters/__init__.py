# ErisML I-EIP Monitor: architecture adapters
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Architecture adapters for the I-EIP Monitor.

Three adapters ship with the library:

* :class:`~erisml.ieip.adapters.hf_transformer.HFTransformerAdapter` --
  Llama-lineage HF models (Llama, Qwen, Gemma, Mistral, Phi, GLM,
  DeepSeek) plus the older GPT-2 / GPT-NeoX layouts.
* :class:`~erisml.ieip.adapters.api_passthrough.APIPassthroughAdapter`
  -- black-box APIs (NRP-hosted models, OpenAI-compatible providers).
  Falls back to output-distribution equivariance since hooks are
  unavailable.
* :class:`~erisml.ieip.adapters.ensemble.EnsembleAdapter` --
  jury-of-experts ensembles (Atlas AI Divine Council, vMOE routers).
  Aggregates per-advocate distributions and exposes the vote as the
  equivariance signal.

Prefer :func:`~erisml.ieip.adapters.detect.detect_adapter` over
instantiating a specific adapter class: it picks the right one
automatically for most inputs. Pass an adapter class explicitly when
you need a non-default layout override (e.g., ``block_path=``).

Example
-------

>>> from erisml.ieip.adapters import detect_adapter      # doctest: +SKIP
>>> adapter = detect_adapter(my_model)                    # doctest: +SKIP
>>> sites = adapter.list_sites(kinds=["residual"])        # doctest: +SKIP
>>> mgr = adapter.attach_probes(                          # doctest: +SKIP
...     sites,
...     lambda s: ProbeSpec(target_layer=s.layer_index, name=s.name),
... )
"""

from __future__ import annotations

from erisml.ieip.adapters.api_passthrough import (
    APIClient,
    APIPassthroughAdapter,
)
from erisml.ieip.adapters.base import (
    AdapterCapabilities,
    BaseAdapter,
    IEIPAdapter,
    ProbeSite,
    get_adapter,
    register_adapter,
    registered_adapters,
)
from erisml.ieip.adapters.detect import (
    AdapterDetectionError,
    describe_adapter,
    detect_adapter,
)
from erisml.ieip.adapters.ensemble import EnsembleAdapter, EnsembleMember


def _import_hf_transformer() -> type:
    """Import the HF adapter lazily so torch is optional at import."""
    from erisml.ieip.adapters.hf_transformer import HFTransformerAdapter

    return HFTransformerAdapter


def __getattr__(name: str):  # pragma: no cover - import shim
    """Lazy ``HFTransformerAdapter`` import.

    Keeps the package loadable without PyTorch installed. Accessing
    ``erisml.ieip.adapters.HFTransformerAdapter`` triggers the import.
    """
    if name == "HFTransformerAdapter":
        return _import_hf_transformer()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "APIClient",
    "APIPassthroughAdapter",
    "AdapterCapabilities",
    "AdapterDetectionError",
    "BaseAdapter",
    "EnsembleAdapter",
    "EnsembleMember",
    "HFTransformerAdapter",  # re-exported lazily above
    "IEIPAdapter",
    "ProbeSite",
    "describe_adapter",
    "detect_adapter",
    "get_adapter",
    "register_adapter",
    "registered_adapters",
]
