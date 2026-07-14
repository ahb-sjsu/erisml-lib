# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.types."""

from __future__ import annotations

import pytest

from erisml.ieip.types import (
    AlertLevel,
    DriftReport,
    EquivarianceResult,
    IEIPReport,
    NondegeneracyMetrics,
    ProbeSpec,
    TransformSpec,
)


class TestProbeSpec:
    def test_valid_spec(self) -> None:
        spec = ProbeSpec(target_layer=3, name="mid")
        assert spec.target_layer == 3
        assert spec.sampling_rate == 1.0
        assert spec.activation_site == "residual"

    def test_negative_layer_rejected(self) -> None:
        with pytest.raises(ValueError, match="target_layer"):
            ProbeSpec(target_layer=-1)

    @pytest.mark.parametrize("rate", [0.0, -0.1, 1.5])
    def test_bad_sampling_rate_rejected(self, rate: float) -> None:
        with pytest.raises(ValueError, match="sampling_rate"):
            ProbeSpec(target_layer=0, sampling_rate=rate)

    def test_expected_shape_positive_dims(self) -> None:
        with pytest.raises(ValueError, match="expected_shape"):
            ProbeSpec(target_layer=0, expected_shape=(0, 8))

    def test_frozen(self) -> None:
        spec = ProbeSpec(target_layer=0)
        with pytest.raises(Exception):  # dataclass FrozenInstanceError
            spec.target_layer = 1  # type: ignore[misc]


class TestTransformSpec:
    def test_valid(self) -> None:
        t = TransformSpec(name="paraphrase", description="LLM paraphrase")
        assert t.name == "paraphrase"
        assert t.registry_version == "0.0.0"

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            TransformSpec(name="")


class TestAlertLevel:
    def test_ordering_semantics(self) -> None:
        # AlertLevel is a str-enum; values must be the documented strings
        assert AlertLevel.NORMAL.value == "normal"
        assert AlertLevel.ELEVATED.value == "elevated"
        assert AlertLevel.CRITICAL.value == "critical"


class TestEquivarianceResult:
    def test_to_dict_roundtrip(self) -> None:
        r = EquivarianceResult(
            layer=2,
            transform="paraphrase",
            error=0.05,
            n_samples=1000,
        )
        d = r.to_dict()
        assert d["layer"] == 2
        assert d["transform"] == "paraphrase"
        assert d["error"] == pytest.approx(0.05)
        assert d["n_samples"] == 1000
        assert d["relative"] is True


class TestDriftReport:
    def test_serialization(self) -> None:
        r = DriftReport(
            layer=1,
            transform="name_swap",
            current_error=0.08,
            baseline_error=0.05,
            drift=0.03,
            alert_level=AlertLevel.NORMAL,
            threshold_elevated=0.05,
            threshold_critical=0.10,
        )
        d = r.to_dict()
        assert d["alert_level"] == "normal"
        assert d["drift"] == pytest.approx(0.03)


class TestNondegeneracyMetrics:
    def test_default_alert_level_is_normal(self) -> None:
        m = NondegeneracyMetrics(
            layer=0,
            effective_rank=50.0,
            max_singular_value=5.0,
            min_singular_value=0.1,
            activation_range=10.0,
            n_samples=100,
        )
        assert m.alert_level == AlertLevel.NORMAL


class TestIEIPReport:
    def test_empty_summary(self) -> None:
        r = IEIPReport()
        assert "I-EIP" in r.summary()
        assert "normal" in r.summary()

    def test_summary_reflects_max_drift(self) -> None:
        r = IEIPReport(
            drift=[
                DriftReport(
                    layer=0,
                    transform="t",
                    current_error=0.1,
                    baseline_error=0.05,
                    drift=0.05,
                    alert_level=AlertLevel.ELEVATED,
                    threshold_elevated=0.05,
                    threshold_critical=0.10,
                ),
                DriftReport(
                    layer=1,
                    transform="t",
                    current_error=0.03,
                    baseline_error=0.02,
                    drift=0.01,
                    alert_level=AlertLevel.NORMAL,
                    threshold_elevated=0.05,
                    threshold_critical=0.10,
                ),
            ],
        )
        summary = r.summary()
        assert "+0.0500" in summary  # max drift

    def test_to_dict_contains_all_sections(self) -> None:
        r = IEIPReport(
            equivariance=[
                EquivarianceResult(layer=0, transform="t", error=0.01, n_samples=10)
            ],
            drift=[],
            nondegeneracy=[],
            cross_layer_coherence=0.99,
            alert_level=AlertLevel.NORMAL,
        )
        d = r.to_dict()
        assert "equivariance" in d
        assert "drift" in d
        assert "nondegeneracy" in d
        assert "summary" in d
        assert d["cross_layer_coherence"] == pytest.approx(0.99)
