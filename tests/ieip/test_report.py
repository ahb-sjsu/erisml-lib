# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.report."""

from __future__ import annotations

import json

import pytest

from erisml.ieip.report import (
    aggregate_report,
    format_json,
    format_text,
    max_alert_level,
)
from erisml.ieip.types import (
    AlertLevel,
    DriftReport,
    EquivarianceResult,
    IEIPReport,
    NondegeneracyMetrics,
)


def _make_equiv(layer: int, transform: str, error: float) -> EquivarianceResult:
    return EquivarianceResult(
        layer=layer, transform=transform, error=error, n_samples=10
    )


def _make_drift(layer: int, transform: str, alert: AlertLevel) -> DriftReport:
    return DriftReport(
        layer=layer,
        transform=transform,
        current_error=0.05,
        baseline_error=0.03,
        drift=0.02,
        alert_level=alert,
        threshold_elevated=0.05,
        threshold_critical=0.10,
    )


def _make_nondeg(layer: int, alert: AlertLevel) -> NondegeneracyMetrics:
    return NondegeneracyMetrics(
        layer=layer,
        effective_rank=10.0,
        max_singular_value=2.0,
        min_singular_value=0.01,
        activation_range=5.0,
        n_samples=100,
        alert_level=alert,
    )


class TestMaxAlertLevel:
    def test_empty_is_normal(self) -> None:
        assert max_alert_level([]) == AlertLevel.NORMAL

    def test_all_normal(self) -> None:
        assert (
            max_alert_level([AlertLevel.NORMAL, AlertLevel.NORMAL]) == AlertLevel.NORMAL
        )

    def test_elevated_beats_normal(self) -> None:
        assert (
            max_alert_level([AlertLevel.NORMAL, AlertLevel.ELEVATED])
            == AlertLevel.ELEVATED
        )

    def test_critical_beats_elevated(self) -> None:
        assert (
            max_alert_level(
                [AlertLevel.ELEVATED, AlertLevel.CRITICAL, AlertLevel.NORMAL]
            )
            == AlertLevel.CRITICAL
        )


class TestAggregateReport:
    def test_empty_inputs_produce_normal_report(self) -> None:
        report = aggregate_report([], [], [])
        assert isinstance(report, IEIPReport)
        assert report.alert_level == AlertLevel.NORMAL
        assert report.cross_layer_coherence == 1.0

    def test_drift_alert_propagates(self) -> None:
        report = aggregate_report(
            [],
            [_make_drift(0, "t", AlertLevel.CRITICAL)],
            [],
        )
        assert report.alert_level == AlertLevel.CRITICAL

    def test_nondeg_alert_propagates(self) -> None:
        report = aggregate_report(
            [],
            [],
            [_make_nondeg(0, AlertLevel.ELEVATED)],
        )
        assert report.alert_level == AlertLevel.ELEVATED

    def test_takes_max_across_sources(self) -> None:
        report = aggregate_report(
            [],
            [_make_drift(0, "t", AlertLevel.ELEVATED)],
            [_make_nondeg(0, AlertLevel.CRITICAL)],
        )
        assert report.alert_level == AlertLevel.CRITICAL

    def test_coherence_from_equivariance(self) -> None:
        report = aggregate_report(
            [_make_equiv(0, "t", 0.0), _make_equiv(1, "t", 0.0)],
            [],
            [],
        )
        assert report.cross_layer_coherence == pytest.approx(1.0)

        report_bad = aggregate_report(
            [_make_equiv(0, "t", 0.5), _make_equiv(1, "t", 0.5)],
            [],
            [],
        )
        assert report_bad.cross_layer_coherence == pytest.approx(0.5)


class TestFormatText:
    def test_empty_report_renders(self) -> None:
        r = IEIPReport()
        text = format_text(r)
        assert "I-EIP" in text
        assert "normal" in text
        assert text.endswith("\n")

    def test_all_sections_present(self) -> None:
        r = aggregate_report(
            [_make_equiv(0, "paraphrase", 0.02)],
            [_make_drift(0, "paraphrase", AlertLevel.NORMAL)],
            [_make_nondeg(0, AlertLevel.NORMAL)],
        )
        text = format_text(r)
        assert "Equivariance" in text
        assert "Drift" in text
        assert "Non-degeneracy" in text
        assert "paraphrase" in text

    def test_wide_vs_narrow(self) -> None:
        r = IEIPReport()
        n = format_text(r, wide=False)
        w = format_text(r, wide=True)
        assert "=" * 80 in n
        assert "=" * 100 in w


class TestFormatJson:
    def test_roundtrip(self) -> None:
        r = aggregate_report(
            [_make_equiv(0, "t", 0.01)],
            [_make_drift(0, "t", AlertLevel.NORMAL)],
            [_make_nondeg(0, AlertLevel.NORMAL)],
        )
        text = format_json(r, indent=2)
        parsed = json.loads(text)
        assert "equivariance" in parsed
        assert "drift" in parsed
        assert "alert_level" in parsed

    def test_compact_no_newlines_in_values(self) -> None:
        r = IEIPReport()
        text = format_json(r, indent=None)
        # indent=None produces a single JSON object
        assert text.count("\n") == 0

    def test_sort_keys_stable(self) -> None:
        r = IEIPReport()
        a = format_json(r)
        b = format_json(r)
        assert a == b
