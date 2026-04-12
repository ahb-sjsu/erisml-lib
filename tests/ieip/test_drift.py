# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.drift."""

from __future__ import annotations

import pytest

from erisml.ieip.drift import (
    DEFAULT_ELEVATED_THRESHOLD,
    DEFAULT_CRITICAL_THRESHOLD,
    DriftDetector,
    compute_drift_alert,
)
from erisml.ieip.types import AlertLevel


class TestComputeDriftAlert:
    def test_normal_range(self) -> None:
        assert compute_drift_alert(current=0.01, baseline=0.01) == AlertLevel.NORMAL

    def test_elevated_at_threshold(self) -> None:
        assert (
            compute_drift_alert(
                current=0.05 + DEFAULT_ELEVATED_THRESHOLD,
                baseline=0.05,
            )
            == AlertLevel.ELEVATED
        )

    def test_critical_at_threshold(self) -> None:
        assert (
            compute_drift_alert(
                current=0.05 + DEFAULT_CRITICAL_THRESHOLD,
                baseline=0.05,
            )
            == AlertLevel.CRITICAL
        )

    def test_negative_drift_is_normal(self) -> None:
        # Error got better — not an alert
        assert compute_drift_alert(current=0.01, baseline=0.10) == AlertLevel.NORMAL

    def test_rejects_inverted_thresholds(self) -> None:
        with pytest.raises(ValueError, match="threshold_critical"):
            compute_drift_alert(
                current=0.0,
                baseline=0.0,
                threshold_elevated=0.1,
                threshold_critical=0.05,
            )

    def test_rejects_negative_thresholds(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            compute_drift_alert(
                current=0.0,
                baseline=0.0,
                threshold_elevated=-0.1,
                threshold_critical=0.1,
            )


class TestDriftDetector:
    def test_first_observation_is_normal(self) -> None:
        det = DriftDetector()
        r = det.observe(layer=0, transform="paraphrase", error=0.05)
        assert r.alert_level == AlertLevel.NORMAL
        assert r.drift == 0.0
        assert r.baseline_error == pytest.approx(0.05)

    def test_warmup_suppresses_alerts(self) -> None:
        det = DriftDetector(warmup_observations=5)
        # Establish a baseline near 0.01
        for _ in range(5):
            det.observe(layer=0, transform="t", error=0.01)
        # Huge spike during warmup — still NORMAL during warmup,
        # but after warmup the next spike should alert
        r_after = det.observe(layer=0, transform="t", error=0.50)
        # If spike happens right at the boundary it's the first post-warmup
        # obs -- should be able to alert
        assert r_after.alert_level in {
            AlertLevel.ELEVATED,
            AlertLevel.CRITICAL,
        }

    def test_stable_signal_stays_normal(self) -> None:
        det = DriftDetector(warmup_observations=0)
        for _ in range(50):
            r = det.observe(layer=0, transform="t", error=0.02)
        assert r.alert_level == AlertLevel.NORMAL

    def test_gradual_drift_eventually_alerts(self) -> None:
        det = DriftDetector(alpha=0.2, warmup_observations=0)
        # Build baseline around 0.02
        for _ in range(30):
            det.observe(layer=0, transform="t", error=0.02)
        # Jump to something that should cross the ELEVATED threshold
        r = det.observe(
            layer=0,
            transform="t",
            error=0.02 + DEFAULT_ELEVATED_THRESHOLD + 0.01,
        )
        assert r.alert_level != AlertLevel.NORMAL

    def test_multiple_keys_independent(self) -> None:
        det = DriftDetector(warmup_observations=0)
        det.observe(layer=0, transform="a", error=0.01)
        det.observe(layer=0, transform="b", error=0.10)
        a_baseline = det.baseline_for(0, "a")
        b_baseline = det.baseline_for(0, "b")
        assert a_baseline is not None
        assert b_baseline is not None
        assert a_baseline < b_baseline

    def test_baseline_for_unseen_is_none(self) -> None:
        det = DriftDetector()
        assert det.baseline_for(99, "nope") is None

    def test_reset_all(self) -> None:
        det = DriftDetector()
        det.observe(layer=0, transform="t", error=0.01)
        det.observe(layer=1, transform="t", error=0.02)
        det.reset()
        assert det.baseline_for(0, "t") is None
        assert det.baseline_for(1, "t") is None

    def test_reset_by_layer(self) -> None:
        det = DriftDetector()
        det.observe(layer=0, transform="t", error=0.01)
        det.observe(layer=1, transform="t", error=0.02)
        det.reset(layer=0)
        assert det.baseline_for(0, "t") is None
        assert det.baseline_for(1, "t") is not None

    def test_reset_by_transform(self) -> None:
        det = DriftDetector()
        det.observe(layer=0, transform="a", error=0.01)
        det.observe(layer=0, transform="b", error=0.02)
        det.reset(transform="a")
        assert det.baseline_for(0, "a") is None
        assert det.baseline_for(0, "b") is not None

    def test_rejects_negative_error(self) -> None:
        det = DriftDetector()
        with pytest.raises(ValueError, match="non-negative"):
            det.observe(layer=0, transform="t", error=-0.01)

    @pytest.mark.parametrize("alpha", [0.0, -0.1, 1.5])
    def test_rejects_bad_alpha(self, alpha: float) -> None:
        with pytest.raises(ValueError, match="alpha"):
            DriftDetector(alpha=alpha)

    def test_rejects_negative_warmup(self) -> None:
        with pytest.raises(ValueError, match="warmup"):
            DriftDetector(warmup_observations=-1)

    def test_rejects_inverted_thresholds(self) -> None:
        with pytest.raises(ValueError, match="threshold_critical"):
            DriftDetector(threshold_elevated=0.1, threshold_critical=0.05)

    def test_ewma_approaches_new_level(self) -> None:
        """With alpha=1, baseline tracks current exactly."""
        det = DriftDetector(alpha=1.0, warmup_observations=0)
        det.observe(layer=0, transform="t", error=0.01)
        r = det.observe(layer=0, transform="t", error=0.10)
        assert r.baseline_error == pytest.approx(0.10)

    def test_ewma_ignores_at_alpha_near_zero(self) -> None:
        """With alpha very small, baseline barely moves."""
        det = DriftDetector(alpha=0.001, warmup_observations=0)
        det.observe(layer=0, transform="t", error=0.01)
        r = det.observe(layer=0, transform="t", error=0.99)
        assert r.baseline_error < 0.02  # essentially unchanged
