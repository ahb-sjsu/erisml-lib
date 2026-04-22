# ErisML I-EIP Monitor: Hugging Face transformer adapter
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Adapter for Hugging Face-style decoder transformer models.

Covers the Llama-lineage layout shared by Llama, Qwen, Gemma, Mistral,
Phi, GLM, DeepSeek, and most other contemporary open-weights models::

    model.model.layers[i]       # block
      .input_layernorm
      .self_attn
      .post_attention_layernorm
      .mlp

Also supports the older GPT-2 / GPT-NeoX / BERT-ish layouts by
accepting alternative block paths. When the model's class name is
unfamiliar the adapter falls back to structural detection (first
``nn.ModuleList`` of transformer-ish blocks wins).

Imports ``torch`` lazily: the module loads without PyTorch, but
instantiating an :class:`HFTransformerAdapter` raises
:class:`ImportError` if torch is not available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Iterable, Sequence

import numpy as np

from erisml.ieip.adapters.base import (
    AdapterCapabilities,
    BaseAdapter,
    ProbeSite,
    register_adapter,
)
from erisml.ieip.types import ActivationSite, ProbeSpec

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - import-guard
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]


# Candidate dotted paths, in priority order, where transformer blocks live.
# The first path that resolves to an ``nn.ModuleList`` wins.
_BLOCK_PATHS: Sequence[str] = (
    "model.layers",  # Llama, Qwen, Gemma, Mistral, GLM, Phi, DeepSeek
    "transformer.h",  # GPT-2, GPT-J, Pythia (older HF style)
    "gpt_neox.layers",  # GPT-NeoX
    "encoder.layer",  # BERT-family (encoder-only — included for completeness)
    "layers",  # bespoke models that expose layers at the top level
)


# Per-site submodule name within a block. Adapters for models that
# diverge from the Llama naming can extend this map by subclassing.
_SITE_TO_SUBMODULE: dict[ActivationSite, str | None] = {
    "residual": None,  # the block output itself -- parent module
    "attn_out": "self_attn",
    "mlp_out": "mlp",
    "pre_norm": "input_layernorm",
    "post_norm": "post_attention_layernorm",
}


def _require_torch() -> None:
    if torch is None:
        raise ImportError(
            "erisml.ieip.adapters.hf_transformer requires PyTorch. "
            "Install with: pip install 'erisml-lib[ieip]'"
        )


def _resolve_dotted(obj: Any, path: str) -> Any | None:
    """Return ``obj.path`` for a dotted ``path``, or ``None`` if missing."""
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if not hasattr(cur, part):
            return None
        cur = getattr(cur, part)
    return cur


def _find_blocks(model: Any) -> tuple[str, Any] | None:
    """Find the transformer-block list on ``model``.

    Returns ``(path, blocks)`` or ``None`` if nothing plausibly
    transformer-shaped is found. The match requires both the dotted
    attribute to resolve and the resolved object to look list-like
    (``len()`` works) with at least one element.
    """
    for path in _BLOCK_PATHS:
        resolved = _resolve_dotted(model, path)
        if resolved is None:
            continue
        try:
            n = len(resolved)
        except TypeError:
            continue
        if n > 0:
            return path, resolved
    return None


@dataclass
class HFTransformerAdapter(BaseAdapter):
    """I-EIP adapter for HF-style decoder transformers.

    Parameters
    ----------
    model:
        A ``torch.nn.Module``. Typically the output of
        ``AutoModelForCausalLM.from_pretrained(...)`` or equivalent.
    block_path:
        Optional override for the dotted path to the block list. Use
        this when the adapter's auto-detection picks the wrong path
        (e.g., a model wraps its transformer in a non-standard
        attribute). Defaults to auto-detection.
    site_map:
        Optional override for the per-site submodule map. Subclasses
        can pass a custom map for architectures that deviate from the
        Llama sub-block naming.
    """

    model_family: ClassVar[str] = "hf-transformer"
    block_path: str | None = None
    site_map: dict[ActivationSite, str | None] | None = None

    def __post_init__(self) -> None:
        _require_torch()
        if not isinstance(self.model, nn.Module):
            raise TypeError(
                f"HFTransformerAdapter requires a torch.nn.Module "
                f"(got {type(self.model).__name__})"
            )

        if self.block_path is None:
            found = _find_blocks(self.model)
            if found is None:
                raise ValueError(
                    "could not locate a transformer-block ModuleList on the model "
                    f"(tried: {list(_BLOCK_PATHS)}). "
                    "Pass block_path= explicitly if the model uses a custom layout."
                )
            self.block_path = found[0]

        blocks = _resolve_dotted(self.model, self.block_path)
        if blocks is None or len(blocks) == 0:
            raise ValueError(
                f"block_path {self.block_path!r} did not resolve to a non-empty list"
            )
        self._blocks: Any = blocks

        if self.site_map is None:
            self.site_map = dict(_SITE_TO_SUBMODULE)

        self._caps = AdapterCapabilities(
            supports_direct_hook=True,
            supports_output_distribution=True,
            supports_transform_execution=True,
        )

    # ── Introspection -----------------------------------------------------

    def num_layers(self) -> int:
        return len(self._blocks)

    def list_sites(
        self,
        *,
        layers: Iterable[int] | None = None,
        kinds: Iterable[ActivationSite] | None = None,
    ) -> list[ProbeSite]:
        """Enumerate all plausible probe sites on this model.

        A site is included only if the corresponding submodule
        actually exists on the block. Silently skips missing sites
        (rather than raising) so the adapter degrades gracefully on
        models that expose only a subset of sub-blocks.
        """
        assert self.site_map is not None  # invariant after __post_init__
        assert self.block_path is not None
        out: list[ProbeSite] = []
        for li in range(len(self._blocks)):
            block = self._blocks[li]
            for kind, sub in self.site_map.items():
                if sub is None:
                    path = f"{self.block_path}.{li}"
                    target = block
                else:
                    if not hasattr(block, sub):
                        continue
                    path = f"{self.block_path}.{li}.{sub}"
                    target = getattr(block, sub)
                # Sanity: only keep sites whose target is an nn.Module.
                if not isinstance(target, nn.Module):
                    continue
                out.append(
                    ProbeSite(
                        layer_index=li,
                        kind=kind,
                        submodule_path=path,
                        name=f"L{li:02d}.{kind}",
                    )
                )
        return self._filter_sites(out, layers=layers, kinds=kinds)

    def resolve_site(self, site: ProbeSite) -> Any | None:
        """Return the ``nn.Module`` for a given probe site.

        Returns ``None`` if the site's path no longer resolves -- e.g.,
        after the caller swapped out a submodule between ``list_sites``
        and ``resolve_site``.
        """
        return _resolve_dotted(self.model, site.submodule_path)

    # ── Attachment --------------------------------------------------------

    def attach_probes(
        self,
        sites: Iterable[ProbeSite],
        spec_factory: Callable[[ProbeSite], ProbeSpec],
    ) -> Any:
        """Attach probes at ``sites`` and return a :class:`ProbeManager`.

        Each site's :class:`ProbeSpec` is produced by ``spec_factory``.
        That two-step is on purpose: callers that want per-site
        sampling / shape assertions can compute them from the site
        metadata without the adapter having to know them in advance.
        """
        # Import here so the module loads without torch.
        from erisml.ieip.probes import ProbeManager

        mgr = ProbeManager()
        for site in sites:
            target = self.resolve_site(site)
            if target is None:
                raise ValueError(
                    f"site {site.name!r} path {site.submodule_path!r} no longer resolves"
                )
            mgr.add(target, spec_factory(site))
        return mgr

    # ── Output distribution (fallback equivariance signal) ---------------

    def output_distribution(self, inputs: Any) -> np.ndarray | None:
        """Run the model and return softmax of the last-token logits.

        Returns a ``(vocab_size,)`` array for the last position in the
        sequence -- the classic next-token distribution. For non-causal
        models this is undefined; they should override.
        """
        out = self._forward(inputs)
        logits = _extract_logits(out)
        if logits is None:
            return None
        last = logits[..., -1, :]  # (batch, vocab) after indexing last seq position
        probs = _softmax(last).detach().to("cpu").float().numpy()
        if probs.ndim == 2 and probs.shape[0] == 1:
            return probs[0]
        return probs

    # ── Forward helpers --------------------------------------------------

    def _forward(self, inputs: Any) -> Any:
        """Call ``self.model`` as ``model(**inputs)`` or ``model(inputs)``.

        HF models accept either a plain tensor or a ``dict``-style
        batch. We support both so callers can pass whichever shape
        they have on hand.
        """
        self.model.eval()
        with torch.no_grad():
            if isinstance(inputs, dict):
                return self.model(**inputs)
            return self.model(inputs)


def _extract_logits(out: Any) -> Any:
    """Pull a ``logits`` tensor out of an HF model output."""
    if hasattr(out, "logits"):
        return out.logits
    if isinstance(out, dict) and "logits" in out:
        return out["logits"]
    if isinstance(out, torch.Tensor):
        return out
    return None


def _softmax(x: Any) -> Any:
    """Numerically stable softmax on the last dim."""
    x = x - x.amax(dim=-1, keepdim=True)
    e = x.exp()
    return e / e.sum(dim=-1, keepdim=True)


# Register with the adapter registry so detect_adapter() can find it.
register_adapter(HFTransformerAdapter)
