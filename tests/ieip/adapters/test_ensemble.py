# ErisML I-EIP Monitor: tests for adapters.ensemble
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Ensemble adapter tests — no PyTorch dependency."""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ieip.adapters.api_passthrough import APIPassthroughAdapter
from erisml.ieip.adapters.ensemble import EnsembleAdapter, EnsembleMember


def _adapter_from_constant(value):
    """Build an APIPassthroughAdapter whose ``generate`` returns ``value``."""
    arr = np.asarray(value, dtype=np.float64)

    class _Client:
        def generate(self, inputs):
            return arr

    return APIPassthroughAdapter(model=_Client())


# ── EnsembleMember -------------------------------------------------------


def test_member_rejects_empty_name():
    with pytest.raises(ValueError, match="non-empty"):
        EnsembleMember(adapter=_adapter_from_constant([1.0]), name="")


def test_member_rejects_nonpositive_weight():
    with pytest.raises(ValueError, match="positive"):
        EnsembleMember(adapter=_adapter_from_constant([1.0]), name="x", weight=0.0)


# ── EnsembleAdapter ------------------------------------------------------


def test_adapter_rejects_empty_members():
    with pytest.raises(ValueError, match="at least one"):
        EnsembleAdapter(model=None, members=[])


def test_adapter_rejects_duplicate_names():
    m1 = EnsembleMember(adapter=_adapter_from_constant([1.0]), name="judge")
    m2 = EnsembleMember(adapter=_adapter_from_constant([1.0]), name="judge")
    with pytest.raises(ValueError, match="duplicate"):
        EnsembleAdapter(model=None, members=[m1, m2])


def test_adapter_capabilities():
    m = EnsembleMember(adapter=_adapter_from_constant([1.0]), name="only")
    a = EnsembleAdapter(model=None, members=[m])
    caps = a.capabilities
    assert not caps.supports_direct_hook
    assert caps.supports_output_distribution
    assert caps.supports_transform_execution


def test_adapter_num_layers_matches_members():
    members = [
        EnsembleMember(adapter=_adapter_from_constant([1.0]), name=f"adv{i}")
        for i in range(3)
    ]
    a = EnsembleAdapter(model=None, members=members)
    assert a.num_layers() == 3


def test_adapter_list_sites_one_per_advocate():
    members = [
        EnsembleMember(adapter=_adapter_from_constant([1.0]), name=n)
        for n in ("judge", "advocate", "synth")
    ]
    a = EnsembleAdapter(model=None, members=members)
    sites = a.list_sites()
    assert [s.layer_index for s in sites] == [0, 1, 2]
    assert [s.name for s in sites] == [
        "advocate:judge",
        "advocate:advocate",
        "advocate:synth",
    ]


def test_adapter_resolve_site_returns_member_adapter():
    m = EnsembleMember(adapter=_adapter_from_constant([1.0]), name="judge")
    a = EnsembleAdapter(model=None, members=[m])
    sites = a.list_sites()
    assert a.resolve_site(sites[0]) is m.adapter


def test_adapter_resolve_out_of_range_is_none():
    from erisml.ieip.adapters.base import ProbeSite

    m = EnsembleMember(adapter=_adapter_from_constant([1.0]), name="judge")
    a = EnsembleAdapter(model=None, members=[m])
    bogus = ProbeSite(99, "residual", "members.99", "missing")
    assert a.resolve_site(bogus) is None


def test_adapter_attach_probes_raises():
    m = EnsembleMember(adapter=_adapter_from_constant([1.0]), name="judge")
    a = EnsembleAdapter(model=None, members=[m])
    with pytest.raises(NotImplementedError, match="does not support direct hooks"):
        a.attach_probes([], lambda s: None)  # type: ignore[arg-type]


def test_adapter_output_distribution_is_equal_weight_average():
    members = [
        EnsembleMember(adapter=_adapter_from_constant([1.0, 0.0]), name="a"),
        EnsembleMember(adapter=_adapter_from_constant([0.0, 1.0]), name="b"),
    ]
    a = EnsembleAdapter(model=None, members=members)
    d = a.output_distribution("anything")
    np.testing.assert_allclose(d, [0.5, 0.5])


def test_adapter_output_distribution_respects_weights():
    members = [
        EnsembleMember(
            adapter=_adapter_from_constant([1.0, 0.0]), name="heavy", weight=3.0
        ),
        EnsembleMember(
            adapter=_adapter_from_constant([0.0, 1.0]), name="light", weight=1.0
        ),
    ]
    a = EnsembleAdapter(model=None, members=members)
    d = a.output_distribution("anything")
    np.testing.assert_allclose(d, [0.75, 0.25])


def test_adapter_per_member_distribution_keys_by_name():
    members = [
        EnsembleMember(adapter=_adapter_from_constant([1.0, 0.0]), name="first"),
        EnsembleMember(adapter=_adapter_from_constant([0.0, 1.0]), name="second"),
    ]
    a = EnsembleAdapter(model=None, members=members)
    d = a.per_member_distribution("x")
    assert set(d.keys()) == {"first", "second"}
    np.testing.assert_allclose(d["first"], [1.0, 0.0])
    np.testing.assert_allclose(d["second"], [0.0, 1.0])


def test_adapter_weighted_mean_pads_unequal_lengths():
    members = [
        EnsembleMember(adapter=_adapter_from_constant([1.0, 0.0, 0.0]), name="three"),
        EnsembleMember(adapter=_adapter_from_constant([0.0, 1.0]), name="two"),
    ]
    a = EnsembleAdapter(model=None, members=members)
    d = a.output_distribution("x")
    # padded-to-3 average of [1,0,0] and [0,1,0]
    np.testing.assert_allclose(d, [0.5, 0.5, 0.0])


def test_adapter_output_none_when_all_members_return_none():
    class NullClient:
        def generate(self, inputs):
            return None

    members = [
        EnsembleMember(adapter=APIPassthroughAdapter(model=NullClient()), name="nil"),
    ]
    a = EnsembleAdapter(model=None, members=members)
    assert a.output_distribution("x") is None


def test_adapter_run_transformed_returns_per_member_dict():
    members = [
        EnsembleMember(adapter=_adapter_from_constant([1.0, 0.0]), name="one"),
        EnsembleMember(adapter=_adapter_from_constant([0.5, 0.5]), name="two"),
    ]
    a = EnsembleAdapter(model=None, members=members)
    out = a.run_transformed("hi", lambda s: s)
    assert set(out.keys()) == {"one", "two"}
