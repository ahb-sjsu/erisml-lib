# ErisML I-EIP Monitor: tests for adapters.hf_transformer
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""HF transformer adapter tests.

Uses a tiny hand-rolled ``nn.Module`` that mimics the Llama-lineage
layout (``model.model.layers[i]`` with ``input_layernorm``, ``self_attn``,
``mlp``, ``post_attention_layernorm``). That keeps the tests fast and
independent of any real HF model download.

All tests skip automatically when PyTorch is not installed.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
nn = torch.nn  # noqa: E402

from erisml.ieip.adapters.hf_transformer import (  # noqa: E402
    HFTransformerAdapter,
    _find_blocks,
    _resolve_dotted,
)
from erisml.ieip.types import ProbeSpec  # noqa: E402

# ── Fake model ------------------------------------------------------------


class _FakeBlock(nn.Module):
    """Minimal Llama-like block."""

    def __init__(self, dim: int):
        super().__init__()
        self.input_layernorm = nn.LayerNorm(dim)
        self.self_attn = nn.Linear(dim, dim, bias=False)
        self.post_attention_layernorm = nn.LayerNorm(dim)
        self.mlp = nn.Linear(dim, dim, bias=False)

    def forward(self, x):  # noqa: D401 (matching HF style)
        h = self.input_layernorm(x)
        h = self.self_attn(h)
        x = x + h
        h2 = self.post_attention_layernorm(x)
        h2 = self.mlp(h2)
        return x + h2


class _InnerModel(nn.Module):
    def __init__(self, dim: int, n_layers: int):
        super().__init__()
        self.layers = nn.ModuleList([_FakeBlock(dim) for _ in range(n_layers)])

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x


class _CausalModel(nn.Module):
    """Mimic ``AutoModelForCausalLM``: has ``.model`` attr + logits output."""

    def __init__(self, dim: int = 8, vocab: int = 16, n_layers: int = 4):
        super().__init__()
        self.model = _InnerModel(dim, n_layers)
        self.lm_head = nn.Linear(dim, vocab, bias=False)

    def forward(self, x):
        h = self.model(x)
        logits = self.lm_head(h)
        # Mimic HF output shape by returning a simple dict.
        return {"logits": logits}


# ── _resolve_dotted / _find_blocks ----------------------------------------


def test_resolve_dotted_finds_nested_attr():
    m = _CausalModel(dim=4, n_layers=2)
    assert _resolve_dotted(m, "model.layers") is m.model.layers
    assert _resolve_dotted(m, "model.layers.0") is m.model.layers[0]


def test_resolve_dotted_missing_returns_none():
    m = _CausalModel(dim=4, n_layers=2)
    assert _resolve_dotted(m, "nope") is None
    assert _resolve_dotted(m, "model.ghosts") is None


def test_find_blocks_picks_model_layers():
    m = _CausalModel(dim=4, n_layers=3)
    found = _find_blocks(m)
    assert found is not None
    path, blocks = found
    assert path == "model.layers"
    assert len(blocks) == 3


def test_find_blocks_returns_none_when_nothing_matches():
    stub = nn.Linear(2, 2)  # no `model.layers`, no `transformer.h`, etc.
    assert _find_blocks(stub) is None


# ── HFTransformerAdapter basic shape --------------------------------------


def test_adapter_builds_and_detects_block_path():
    m = _CausalModel(dim=8, n_layers=5)
    a = HFTransformerAdapter(model=m)
    assert a.block_path == "model.layers"
    assert a.num_layers() == 5


def test_adapter_capabilities():
    m = _CausalModel(dim=4, n_layers=2)
    a = HFTransformerAdapter(model=m)
    caps = a.capabilities
    assert caps.supports_direct_hook
    assert caps.supports_output_distribution
    assert caps.supports_transform_execution


def test_adapter_rejects_non_module():
    with pytest.raises(TypeError, match="torch.nn.Module"):
        HFTransformerAdapter(model="not a module")


def test_adapter_explicit_bad_block_path_raises():
    m = _CausalModel(dim=4, n_layers=2)
    with pytest.raises(ValueError, match="did not resolve"):
        HFTransformerAdapter(model=m, block_path="nonexistent.path")


def test_adapter_on_bare_linear_module_raises():
    with pytest.raises(ValueError, match="could not locate"):
        HFTransformerAdapter(model=nn.Linear(2, 2))


# ── Site enumeration ------------------------------------------------------


def test_list_sites_covers_all_submodules():
    m = _CausalModel(dim=4, n_layers=2)
    a = HFTransformerAdapter(model=m)
    sites = a.list_sites()
    # 2 layers x {residual, attn_out, mlp_out, pre_norm, post_norm} = 10
    assert len(sites) == 2 * 5
    kinds = {s.kind for s in sites}
    assert kinds == {"residual", "attn_out", "mlp_out", "pre_norm", "post_norm"}


def test_list_sites_filter_by_layer():
    m = _CausalModel(dim=4, n_layers=3)
    a = HFTransformerAdapter(model=m)
    sites = a.list_sites(layers=[0, 2])
    assert {s.layer_index for s in sites} == {0, 2}


def test_list_sites_filter_by_kind():
    m = _CausalModel(dim=4, n_layers=3)
    a = HFTransformerAdapter(model=m)
    sites = a.list_sites(kinds=["residual"])
    assert len(sites) == 3
    assert all(s.kind == "residual" for s in sites)


def test_list_sites_skips_missing_submodule_gracefully():
    """If a block has no ``mlp``, that site should not be listed."""
    m = _CausalModel(dim=4, n_layers=2)
    # Surgery: remove the mlp from block 0.
    del m.model.layers[0].mlp
    a = HFTransformerAdapter(model=m)
    sites = a.list_sites(layers=[0], kinds=["mlp_out"])
    assert sites == []


# ── Resolve site ---------------------------------------------------------


def test_resolve_site_returns_module():
    m = _CausalModel(dim=4, n_layers=2)
    a = HFTransformerAdapter(model=m)
    site = [s for s in a.list_sites() if s.kind == "attn_out" and s.layer_index == 1][0]
    target = a.resolve_site(site)
    assert target is m.model.layers[1].self_attn


def test_resolve_site_returns_none_on_missing_path():
    from erisml.ieip.adapters.base import ProbeSite

    m = _CausalModel(dim=4, n_layers=2)
    a = HFTransformerAdapter(model=m)
    assert a.resolve_site(ProbeSite(0, "residual", "ghost.path", "x")) is None


# ── Attach + collect ----------------------------------------------------


def test_attach_probes_collects_activations():
    m = _CausalModel(dim=8, n_layers=3)
    a = HFTransformerAdapter(model=m)
    sites = [s for s in a.list_sites() if s.kind == "residual"]
    mgr = a.attach_probes(
        sites,
        lambda s: ProbeSpec(target_layer=s.layer_index, name=s.name),
    )
    with mgr.active():
        x = torch.randn(2, 5, 8)
        _ = m(x)
    collected = mgr.collected()
    assert len(collected) == 3
    # Each probe sees 2 batch × 5 seq = 10 samples, 8 feature dim.
    for arr in collected.values():
        assert arr.shape == (10, 8)


def test_attach_probes_raises_on_stale_site_path():
    m = _CausalModel(dim=4, n_layers=2)
    a = HFTransformerAdapter(model=m)
    sites = a.list_sites()
    # Corrupt the model after site enumeration.
    del m.model.layers[1]
    with pytest.raises(ValueError, match="no longer resolves"):
        a.attach_probes(
            sites,
            lambda s: ProbeSpec(target_layer=s.layer_index, name=s.name),
        )


# ── Output distribution / run_transformed ------------------------------


def test_output_distribution_shape_matches_vocab():
    m = _CausalModel(dim=8, vocab=16, n_layers=2)
    a = HFTransformerAdapter(model=m)
    x = torch.randn(1, 4, 8)
    d = a.output_distribution(x)
    assert d is not None
    # Batch squeezed away for single-batch inputs → shape (vocab,)
    assert d.shape == (16,)
    # Proper probability vector.
    assert abs(d.sum() - 1.0) < 1e-4


def test_output_distribution_handles_dict_input():
    class _WithKwargs(nn.Module):
        def __init__(self):
            super().__init__()
            self.model = _InnerModel(4, 2)
            self.lm_head = nn.Linear(4, 8, bias=False)

        def forward(self, inputs_embeds=None):
            h = self.model(inputs_embeds)
            return {"logits": self.lm_head(h)}

    m = _WithKwargs()
    a = HFTransformerAdapter(model=m)
    d = a.output_distribution({"inputs_embeds": torch.randn(1, 3, 4)})
    assert d is not None
    assert d.shape == (8,)


def test_run_transformed_applies_transform_before_forward():
    m = _CausalModel(dim=4, vocab=8, n_layers=2)
    a = HFTransformerAdapter(model=m)
    x = torch.zeros(1, 2, 4)
    # Transform replaces input entirely so we can verify call path.
    bias = torch.ones(1, 2, 4) * 1e-3
    _ = a.run_transformed(x, lambda inp: inp + bias)
