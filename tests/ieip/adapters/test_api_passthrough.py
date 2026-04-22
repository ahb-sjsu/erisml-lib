# ErisML I-EIP Monitor: tests for adapters.api_passthrough
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Output-distribution adapter tests — no PyTorch dependency."""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ieip.adapters.api_passthrough import (
    APIClient,
    APIPassthroughAdapter,
    _as_distribution,
    _normalize,
)

# ── _normalize -------------------------------------------------------------


def test_normalize_preserves_probability_vector():
    p = np.array([0.2, 0.5, 0.3])
    out = _normalize(p)
    np.testing.assert_allclose(out, p)


def test_normalize_softmaxes_logits():
    logits = np.array([2.0, 1.0, 0.0])
    out = _normalize(logits)
    # Softmax sum is 1, argmax preserved.
    np.testing.assert_allclose(out.sum(), 1.0)
    assert out.argmax() == 0


def test_normalize_handles_all_zero():
    out = _normalize(np.zeros(4))
    np.testing.assert_allclose(out, np.full(4, 0.25))


def test_normalize_handles_scalar():
    out = _normalize(np.array(5.0))
    assert out.shape == (1,)


# ── _as_distribution -------------------------------------------------------


def test_as_distribution_from_numpy_array():
    out = _as_distribution(np.array([0.5, 0.5]))
    np.testing.assert_allclose(out, [0.5, 0.5])


def test_as_distribution_from_logprobs_dict():
    out = _as_distribution({"logprobs": [0.2, 0.8]})
    np.testing.assert_allclose(out, [0.2, 0.8])


def test_as_distribution_from_probs_dict():
    out = _as_distribution({"probs": [0.1, 0.9]})
    np.testing.assert_allclose(out, [0.1, 0.9])


def test_as_distribution_from_string_falls_back_to_hist():
    out = _as_distribution("AB")
    assert out is not None
    assert out.shape == (128,)
    # A=65, B=66 → each 0.5
    assert pytest.approx(out[65]) == 0.5
    assert pytest.approx(out[66]) == 0.5


def test_as_distribution_from_empty_string_is_none():
    assert _as_distribution("") is None


def test_as_distribution_from_unknown_type_is_none():
    assert _as_distribution(object()) is None


# ── APIPassthroughAdapter --------------------------------------------------


class _DictClient:
    """Client that returns a dict with logprobs."""

    def __init__(self):
        self.calls: list[object] = []

    def generate(self, inputs):
        self.calls.append(inputs)
        return {"logprobs": [0.3, 0.7]}


def test_adapter_rejects_bad_model_type():
    with pytest.raises(TypeError, match="callable or an object"):
        APIPassthroughAdapter(model=42)


def test_adapter_capabilities_are_correct():
    adapter = APIPassthroughAdapter(model=_DictClient())
    caps = adapter.capabilities
    assert not caps.supports_direct_hook
    assert caps.supports_output_distribution
    assert caps.supports_transform_execution


def test_adapter_num_layers_is_minus_one():
    adapter = APIPassthroughAdapter(model=_DictClient())
    assert adapter.num_layers() == -1


def test_adapter_list_sites_always_empty():
    adapter = APIPassthroughAdapter(model=_DictClient())
    assert adapter.list_sites() == []
    assert adapter.list_sites(layers=[0, 1], kinds=["residual"]) == []


def test_adapter_resolve_site_returns_none():
    from erisml.ieip.adapters.base import ProbeSite

    adapter = APIPassthroughAdapter(model=_DictClient())
    site = ProbeSite(0, "residual", "x", "x")
    assert adapter.resolve_site(site) is None


def test_adapter_attach_probes_raises():
    adapter = APIPassthroughAdapter(model=_DictClient())
    with pytest.raises(NotImplementedError, match="cannot attach"):
        adapter.attach_probes([], lambda s: None)  # type: ignore[arg-type]


def test_adapter_output_distribution_calls_generate():
    client = _DictClient()
    adapter = APIPassthroughAdapter(model=client)
    d = adapter.output_distribution("hello")
    np.testing.assert_allclose(d, [0.3, 0.7])
    assert client.calls == ["hello"]


def test_adapter_run_transformed_applies_transform_first():
    client = _DictClient()
    adapter = APIPassthroughAdapter(model=client)
    adapter.run_transformed("cat", lambda s: s.upper())
    assert client.calls == ["CAT"]


def test_adapter_accepts_plain_callable():
    def client(inputs):
        return np.array([1.0, 0.0])

    adapter = APIPassthroughAdapter(model=client)
    np.testing.assert_allclose(adapter.output_distribution("x"), [1.0, 0.0])


def test_adapter_returns_none_on_unparseable_output():
    class BadClient:
        def generate(self, inputs):
            return {"weird_key": [1, 2, 3]}

    adapter = APIPassthroughAdapter(model=BadClient())
    assert adapter.output_distribution("x") is None


# ── APIClient protocol -----------------------------------------------------


def test_api_client_protocol_is_structural():
    assert isinstance(_DictClient(), APIClient)

    class NotAClient:
        pass

    assert not isinstance(NotAClient(), APIClient)
