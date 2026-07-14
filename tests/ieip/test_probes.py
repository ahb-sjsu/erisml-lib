# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.probes — requires PyTorch."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
# ruff: noqa: E402 - imports below depend on importorskip

import numpy as np

from erisml.ieip.probes import ActivationProbe, ProbeManager
from erisml.ieip.types import ProbeSpec


@pytest.fixture
def tiny_model() -> "torch.nn.Module":
    return torch.nn.Sequential(
        torch.nn.Linear(4, 8),
        torch.nn.ReLU(),
        torch.nn.Linear(8, 2),
    )


class TestActivationProbe:
    def test_attach_detach_lifecycle(self, tiny_model: "torch.nn.Module") -> None:
        probe = ActivationProbe(
            module=tiny_model[1],
            spec=ProbeSpec(target_layer=1, name="relu"),
        )
        assert not probe.attached
        probe.attach()
        assert probe.attached
        probe.detach()
        assert not probe.attached

    def test_attach_is_idempotent(self, tiny_model: "torch.nn.Module") -> None:
        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1))
        probe.attach()
        probe.attach()
        assert probe.attached
        probe.detach()

    def test_collects_activations(self, tiny_model: "torch.nn.Module") -> None:
        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1, name="relu"))
        probe.attach()
        x = torch.randn(3, 4)
        _ = tiny_model(x)
        probe.detach()
        acts = probe.collected()
        assert acts.shape == (3, 8)
        assert probe.call_count == 1

    def test_does_not_modify_forward_output(
        self, tiny_model: "torch.nn.Module"
    ) -> None:
        x = torch.randn(5, 4)
        # Baseline output without probes
        with torch.no_grad():
            y0 = tiny_model(x).clone()
        # Now with a probe
        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1))
        probe.attach()
        with torch.no_grad():
            y1 = tiny_model(x)
        probe.detach()
        # Outputs must be bitwise identical (probe is read-only)
        assert torch.equal(y0, y1)

    def test_detach_on_empty_probe_is_safe(self, tiny_model: "torch.nn.Module") -> None:
        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1))
        # Never attached; detach should be a no-op, not an error.
        probe.detach()
        assert not probe.attached

    def test_collected_without_runs_raises(self, tiny_model: "torch.nn.Module") -> None:
        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1))
        probe.attach()
        probe.detach()
        with pytest.raises(RuntimeError, match="no collected activations"):
            probe.collected()

    def test_clear_empties_buffer_but_keeps_counters(
        self, tiny_model: "torch.nn.Module"
    ) -> None:
        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1))
        probe.attach()
        _ = tiny_model(torch.randn(2, 4))
        assert probe.call_count == 1
        probe.clear()
        # Call count preserved; activations gone
        assert probe.call_count == 1
        probe.detach()

    def test_sampling_rate_reduces_capture(self, tiny_model: "torch.nn.Module") -> None:
        """With sampling_rate=0.0001 we expect very few captures."""
        probe = ActivationProbe(
            tiny_model[1],
            ProbeSpec(target_layer=1, sampling_rate=0.0001),
        )
        probe.attach()
        for _ in range(20):
            _ = tiny_model(torch.randn(1, 4))
        probe.detach()
        # call_count counts all forward passes; collected buffer will be sparse
        assert probe.call_count == 20
        # With such aggressive subsampling, likely 0 captures
        # (but not guaranteed; just check the counter honors calls)
        if probe._buffer.activations:  # type: ignore[attr-defined]
            assert len(probe._buffer.activations) < 5  # type: ignore[attr-defined]

    def test_expected_shape_validation(self, tiny_model: "torch.nn.Module") -> None:
        # Expected trailing dim (8,) matches the ReLU output
        probe = ActivationProbe(
            tiny_model[1],
            ProbeSpec(target_layer=1, expected_shape=(8,)),
        )
        probe.attach()
        _ = tiny_model(torch.randn(2, 4))
        probe.detach()
        acts = probe.collected()
        assert acts.shape[-1] == 8

    def test_expected_shape_mismatch_increments_failures(
        self, tiny_model: "torch.nn.Module"
    ) -> None:
        probe = ActivationProbe(
            tiny_model[1],
            ProbeSpec(target_layer=1, expected_shape=(16,)),  # wrong!
        )
        probe.attach()
        _ = tiny_model(torch.randn(2, 4))
        probe.detach()
        assert probe.failure_count >= 1
        assert "expected trailing shape" in probe.last_failure


class TestProbeManager:
    def test_add_and_retrieve(self, tiny_model: "torch.nn.Module") -> None:
        mgr = ProbeManager()
        mgr.add(tiny_model[0], ProbeSpec(target_layer=0, name="lin1"))
        mgr.add(tiny_model[1], ProbeSpec(target_layer=1, name="relu"))
        assert mgr.names() == ["lin1", "relu"]
        assert isinstance(mgr.get("relu"), ActivationProbe)

    def test_duplicate_name_rejected(self, tiny_model: "torch.nn.Module") -> None:
        mgr = ProbeManager()
        mgr.add(tiny_model[0], ProbeSpec(target_layer=0, name="x"))
        with pytest.raises(KeyError, match="already registered"):
            mgr.add(tiny_model[1], ProbeSpec(target_layer=1, name="x"))

    def test_active_context_attaches_and_detaches(
        self, tiny_model: "torch.nn.Module"
    ) -> None:
        mgr = ProbeManager()
        p0 = mgr.add(tiny_model[0], ProbeSpec(target_layer=0, name="p0"))
        p1 = mgr.add(tiny_model[1], ProbeSpec(target_layer=1, name="p1"))
        with mgr.active():
            assert p0.attached and p1.attached
            _ = tiny_model(torch.randn(2, 4))
        assert not p0.attached
        assert not p1.attached

    def test_collected_returns_dict_per_probe(
        self, tiny_model: "torch.nn.Module"
    ) -> None:
        mgr = ProbeManager()
        mgr.add(tiny_model[0], ProbeSpec(target_layer=0, name="lin1"))
        mgr.add(tiny_model[1], ProbeSpec(target_layer=1, name="relu"))
        with mgr.active():
            _ = tiny_model(torch.randn(4, 4))
        acts = mgr.collected()
        assert set(acts.keys()) == {"lin1", "relu"}
        assert acts["lin1"].shape == (4, 8)
        assert acts["relu"].shape == (4, 8)

    def test_any_failed_flag(self, tiny_model: "torch.nn.Module") -> None:
        mgr = ProbeManager()
        mgr.add(tiny_model[0], ProbeSpec(target_layer=0, name="ok"))
        assert not mgr.any_failed()

    def test_clear_all_resets_buffers(self, tiny_model: "torch.nn.Module") -> None:
        mgr = ProbeManager()
        mgr.add(tiny_model[1], ProbeSpec(target_layer=1, name="p"))
        with mgr.active():
            _ = tiny_model(torch.randn(2, 4))
        mgr.clear_all()
        with pytest.raises(RuntimeError, match="no collected"):
            mgr.get("p").collected()


class TestEndToEndSmall:
    """End-to-end sanity: probe → ρ estimate → equivariance check."""

    def test_identity_transform_low_error(self, tiny_model: "torch.nn.Module") -> None:
        from erisml.ieip.equivariance import equivariance_error
        from erisml.ieip.rho import estimate_rho

        probe = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1, name="relu"))
        probe.attach()
        x = torch.randn(64, 4)
        _ = tiny_model(x)
        probe.detach()
        acts_X = probe.collected()

        # "Transformed" input = the same input; Y = X.
        probe2 = ActivationProbe(tiny_model[1], ProbeSpec(target_layer=1, name="relu2"))
        probe2.attach()
        _ = tiny_model(x)
        probe2.detach()
        acts_Y = probe2.collected()

        rho = estimate_rho(acts_X, acts_Y, lambda_reg=1e-4)
        result = equivariance_error(acts_X, acts_Y, rho, layer=1, transform="identity")
        # Identity transform: error should be very small
        assert result.error < 0.05
        assert np.isfinite(result.error)
