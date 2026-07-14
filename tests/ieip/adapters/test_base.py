# ErisML I-EIP Monitor: tests for adapters.base
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Protocol conformance + registry tests for the adapter base module."""

from __future__ import annotations

from typing import Any, Callable, ClassVar, Iterable

import numpy as np
import pytest

from erisml.ieip.adapters.base import (
    AdapterCapabilities,
    BaseAdapter,
    IEIPAdapter,
    ProbeSite,
    get_adapter,
    register_adapter,
    registered_adapters,
)
from erisml.ieip.types import ActivationSite, ProbeSpec

# ── ProbeSite invariants -----------------------------------------------------


def test_probesite_is_hashable_and_frozen():
    s = ProbeSite(
        layer_index=3,
        kind="residual",
        submodule_path="model.layers.3",
        name="L03.residual",
    )
    # Frozen: can put it in a set.
    assert hash(s) == hash(s)
    assert {s, s} == {s}
    # Fields are accessible.
    assert s.layer_index == 3
    assert s.kind == "residual"


# ── BaseAdapter defaults -----------------------------------------------------


class _BareAdapter(BaseAdapter):
    model_family: ClassVar[str] = "test-bare"


def test_base_adapter_default_caps_are_all_false():
    a = _BareAdapter(model=object())
    caps = a.capabilities
    assert not caps.supports_direct_hook
    assert not caps.supports_output_distribution
    assert not caps.supports_transform_execution


def test_base_adapter_output_distribution_is_none_by_default():
    a = _BareAdapter(model=object())
    assert a.output_distribution("anything") is None


def test_base_adapter_attach_probes_raises_when_no_hooks():
    a = _BareAdapter(model=object())
    with pytest.raises(NotImplementedError, match="does not support direct hooks"):
        a.attach_probes([], lambda s: ProbeSpec(target_layer=0, name=""))


def test_base_adapter_run_transformed_raises_when_no_support():
    a = _BareAdapter(model=object())
    with pytest.raises(NotImplementedError, match="does not support transform"):
        a.run_transformed("x", lambda inp: inp)


# ── Site filtering helper ---------------------------------------------------


def test_filter_sites_by_layer_subset():
    sites = [ProbeSite(i, "residual", f"p.{i}", f"L{i}") for i in range(10)]
    out = BaseAdapter._filter_sites(sites, layers=[2, 5, 8], kinds=None)
    assert [s.layer_index for s in out] == [2, 5, 8]


def test_filter_sites_by_kind():
    sites = [
        ProbeSite(0, "residual", "p.0.res", "L0.res"),
        ProbeSite(0, "attn_out", "p.0.attn", "L0.attn"),
        ProbeSite(0, "mlp_out", "p.0.mlp", "L0.mlp"),
    ]
    out = BaseAdapter._filter_sites(sites, layers=None, kinds=["attn_out", "mlp_out"])
    assert sorted(s.kind for s in out) == ["attn_out", "mlp_out"]


def test_filter_sites_intersection():
    sites = [
        ProbeSite(0, "residual", "p.0.res", "L0.res"),
        ProbeSite(1, "residual", "p.1.res", "L1.res"),
        ProbeSite(1, "attn_out", "p.1.attn", "L1.attn"),
    ]
    out = BaseAdapter._filter_sites(sites, layers=[1], kinds=["residual"])
    assert len(out) == 1
    assert out[0].layer_index == 1
    assert out[0].kind == "residual"


def test_filter_sites_empty_filters_return_all():
    sites = [
        ProbeSite(0, "residual", "p.0", "L0"),
        ProbeSite(1, "residual", "p.1", "L1"),
    ]
    assert BaseAdapter._filter_sites(sites, layers=None, kinds=None) == sites


# ── Registry ----------------------------------------------------------------


class _AdapterAlpha(BaseAdapter):
    model_family: ClassVar[str] = "test-alpha"


class _AdapterBeta(BaseAdapter):
    model_family: ClassVar[str] = "test-beta"


def test_register_adapter_basic():
    register_adapter(_AdapterAlpha)
    assert "test-alpha" in registered_adapters()
    assert get_adapter("test-alpha") is _AdapterAlpha


def test_register_adapter_is_idempotent_for_same_class():
    # Registering the same class twice must not raise.
    register_adapter(_AdapterAlpha)
    register_adapter(_AdapterAlpha)
    assert get_adapter("test-alpha") is _AdapterAlpha


def test_register_adapter_rejects_collisions():
    register_adapter(_AdapterBeta)

    class _Impostor(BaseAdapter):
        model_family: ClassVar[str] = "test-beta"

    with pytest.raises(ValueError, match="already registered"):
        register_adapter(_Impostor)


def test_register_adapter_rejects_missing_family():
    class _NoFamily(BaseAdapter):
        # inherits model_family="unknown" from BaseAdapter
        pass

    with pytest.raises(ValueError, match="non-empty model_family"):
        register_adapter(_NoFamily)


def test_get_adapter_missing_raises_with_helpful_message():
    with pytest.raises(KeyError, match="known:"):
        get_adapter("totally-made-up")


# ── IEIPAdapter Protocol structural conformance -----------------------------


class _GoodAdapter:
    """Minimal class that structurally satisfies the Protocol."""

    model_family: ClassVar[str] = "good-shape"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_direct_hook=False,
            supports_output_distribution=False,
            supports_transform_execution=False,
        )

    def num_layers(self) -> int:
        return 0

    def list_sites(
        self,
        *,
        layers: Iterable[int] | None = None,
        kinds: Iterable[ActivationSite] | None = None,
    ) -> list[ProbeSite]:
        return []

    def resolve_site(self, site: ProbeSite) -> Any | None:
        return None

    def attach_probes(
        self,
        sites: Iterable[ProbeSite],
        spec_factory: Callable[[ProbeSite], ProbeSpec],
    ) -> Any:
        raise NotImplementedError

    def output_distribution(self, inputs: Any) -> np.ndarray | None:
        return None

    def run_transformed(self, inputs: Any, transform: Callable[[Any], Any]) -> Any:
        return inputs


def test_protocol_accepts_structural_match():
    assert isinstance(_GoodAdapter(), IEIPAdapter)


def test_protocol_rejects_incomplete_class():
    class _Missing:
        model_family = "missing"

    assert not isinstance(_Missing(), IEIPAdapter)
