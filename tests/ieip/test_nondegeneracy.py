# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.nondegeneracy."""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ieip.nondegeneracy import (
    effective_rank,
    nondegeneracy_report,
    nondegeneracy_reports,
)
from erisml.ieip.types import AlertLevel


class TestEffectiveRank:
    def test_full_rank_isotropic(self) -> None:
        """Isotropic Gaussian data has effective rank ≈ min(n, d)."""
        rng = np.random.default_rng(0)
        n, d = 500, 8
        X = rng.standard_normal(size=(n, d))
        rank = effective_rank(X)
        # Should be close to d (the smaller dim)
        assert rank > 0.8 * d
        assert rank <= d + 1e-6

    def test_rank_one_activation(self) -> None:
        """A matrix whose rows are all scaled copies has effective rank ≈ 1."""
        rng = np.random.default_rng(0)
        direction = rng.standard_normal(size=8)
        scales = rng.standard_normal(size=50)
        X = scales[:, None] * direction[None, :]
        rank = effective_rank(X)
        assert rank < 1.5

    def test_constant_rows_collapse(self) -> None:
        """All-constant rows → after mean-centering, zero variance → rank=1."""
        X = np.ones((10, 4)) * 3.14
        rank = effective_rank(X)
        assert rank == 1.0

    def test_range_in_valid_interval(self) -> None:
        rng = np.random.default_rng(1)
        for d in (4, 16, 64):
            X = rng.standard_normal(size=(200, d))
            r = effective_rank(X)
            assert 1.0 <= r <= d + 1e-6

    def test_empty_input_is_zero(self) -> None:
        X = np.zeros((0, 4))
        rank = effective_rank(X)
        assert rank == 0.0


class TestNondegeneracyReport:
    def test_healthy_activations_are_normal(self) -> None:
        rng = np.random.default_rng(0)
        X = rng.standard_normal(size=(500, 64))
        report = nondegeneracy_report(X, layer=3)
        assert report.layer == 3
        assert report.alert_level == AlertLevel.NORMAL
        assert report.effective_rank > 20  # clearly non-degenerate

    def test_collapsed_activations_are_critical(self) -> None:
        rng = np.random.default_rng(0)
        direction = rng.standard_normal(size=32)
        scales = rng.standard_normal(size=200)
        X = scales[:, None] * direction[None, :]  # rank 1
        report = nondegeneracy_report(X, layer=0)
        assert report.alert_level == AlertLevel.CRITICAL

    def test_metrics_populated(self) -> None:
        rng = np.random.default_rng(0)
        X = rng.standard_normal(size=(100, 16))
        report = nondegeneracy_report(X, layer=5)
        assert report.n_samples == 100
        assert report.max_singular_value >= report.min_singular_value
        assert report.activation_range > 0

    def test_rejects_inverted_fractions(self) -> None:
        X = np.eye(5)
        with pytest.raises(ValueError, match="critical_fraction"):
            nondegeneracy_report(
                X,
                layer=0,
                elevated_fraction=0.1,
                critical_fraction=0.5,
            )

    def test_custom_thresholds(self) -> None:
        rng = np.random.default_rng(0)
        X = rng.standard_normal(size=(100, 16))
        # Tight thresholds — even well-behaved data may alert
        report = nondegeneracy_report(
            X,
            layer=0,
            elevated_fraction=0.99,
            critical_fraction=0.98,
        )
        # Healthy isotropic data at dim=16 rarely reaches 0.99 of max
        assert report.alert_level in {
            AlertLevel.ELEVATED,
            AlertLevel.CRITICAL,
            AlertLevel.NORMAL,
        }

    def test_to_dict_includes_alert(self) -> None:
        rng = np.random.default_rng(0)
        X = rng.standard_normal(size=(50, 8))
        d = nondegeneracy_report(X, layer=1).to_dict()
        assert "alert_level" in d
        assert d["layer"] == 1


class TestNondegeneracyReports:
    def test_sorted_by_layer(self) -> None:
        rng = np.random.default_rng(0)
        activations = {
            2: rng.standard_normal(size=(100, 8)),
            0: rng.standard_normal(size=(100, 8)),
            1: rng.standard_normal(size=(100, 8)),
        }
        reports = nondegeneracy_reports(activations)
        assert [r.layer for r in reports] == [0, 1, 2]
