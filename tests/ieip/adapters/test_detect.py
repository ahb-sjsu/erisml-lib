# ErisML I-EIP Monitor: tests for adapters.detect
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Auto-detection routing tests."""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ieip.adapters import (
    APIPassthroughAdapter,
    EnsembleAdapter,
    EnsembleMember,
    detect_adapter,
    describe_adapter,
)
from erisml.ieip.adapters.detect import AdapterDetectionError

# ── Fallback: API passthrough ---------------------------------------------


class _FakeClient:
    def generate(self, inputs):
        return np.array([0.6, 0.4])


def test_detect_picks_api_passthrough_for_generate_object():
    adapter = detect_adapter(_FakeClient(), name="fake")
    assert isinstance(adapter, APIPassthroughAdapter)
    assert adapter.model_family == "api-passthrough"
    assert adapter.name == "fake"


def test_detect_picks_api_passthrough_for_callable():
    def client(inputs):
        return np.array([1.0])

    adapter = detect_adapter(client)
    assert isinstance(adapter, APIPassthroughAdapter)


# ── Ensemble member sequence ----------------------------------------------


def test_detect_picks_ensemble_for_member_list():
    members = [
        EnsembleMember(adapter=detect_adapter(_FakeClient()), name="judge"),
        EnsembleMember(adapter=detect_adapter(_FakeClient()), name="advocate"),
    ]
    adapter = detect_adapter(members, name="test-ensemble")
    assert isinstance(adapter, EnsembleAdapter)
    assert adapter.name == "test-ensemble"
    assert adapter.num_layers() == 2


def test_detect_passes_through_existing_adapter():
    original = detect_adapter(_FakeClient())
    again = detect_adapter(original)
    assert again is original


# ── Rejection -------------------------------------------------------------


def test_detect_rejects_plain_object():
    class Bogus:
        pass

    with pytest.raises(AdapterDetectionError, match="no I-EIP adapter applies"):
        detect_adapter(Bogus())


def test_detect_rejects_plain_string():
    with pytest.raises(AdapterDetectionError):
        detect_adapter("just a string")


# ── describe_adapter ------------------------------------------------------


def test_describe_adapter_emits_expected_keys():
    adapter = detect_adapter(_FakeClient())
    d = describe_adapter(adapter)
    assert d["model_family"] == "api-passthrough"
    assert d["supports_direct_hook"] is False
    assert d["supports_output_distribution"] is True
    # API passthrough is layer-indeterminate
    assert d["num_layers"] == -1
    assert d["num_sites"] == 0
