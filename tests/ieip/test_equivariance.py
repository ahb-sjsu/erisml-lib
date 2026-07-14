# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.equivariance."""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ieip.equivariance import (
    cross_layer_coherence,
    equivariance_error,
    equivariance_errors_batch,
)
from erisml.ieip.rho import estimate_rho
from erisml.ieip.types import EquivarianceResult


class TestEquivarianceError:
    def test_zero_error_when_rho_fits_exactly(self) -> None:
        rng = np.random.default_rng(0)
        n, d = 50, 4
        X = rng.standard_normal(size=(n, d))
        rho = np.eye(d) * 1.5
        Y = X @ rho.T
        result = equivariance_error(X, Y, rho, layer=0, transform="identity")
        assert result.error < 1e-12
        assert result.layer == 0
        assert result.transform == "identity"
        assert result.n_samples == n
        assert result.relative is True

    def test_high_error_when_rho_is_zero(self) -> None:
        rng = np.random.default_rng(1)
        n, d = 50, 4
        X = rng.standard_normal(size=(n, d))
        Y = rng.standard_normal(size=(n, d))
        rho_zero = np.zeros((d, d))
        result = equivariance_error(X, Y, rho_zero, layer=0, transform="t")
        # Zero prediction against non-zero Y → relative error ≈ 1
        assert 0.8 < result.error <= 1.0 + 1e-9

    def test_absolute_vs_relative(self) -> None:
        rng = np.random.default_rng(2)
        n, d = 20, 3
        X = rng.standard_normal(size=(n, d))
        Y = X + 0.1 * rng.standard_normal(size=(n, d))
        rho = estimate_rho(X, Y)
        rel = equivariance_error(X, Y, rho, layer=0, transform="t", relative=True)
        abs_ = equivariance_error(X, Y, rho, layer=0, transform="t", relative=False)
        assert rel.error >= 0.0
        assert abs_.error >= 0.0
        assert rel.relative is True
        assert abs_.relative is False

    def test_returns_equivariance_result(self) -> None:
        X = np.eye(3)
        Y = np.eye(3)
        result = equivariance_error(X, Y, np.eye(3), layer=5, transform="x")
        assert isinstance(result, EquivarianceResult)
        assert result.layer == 5


class TestEquivarianceErrorsBatch:
    def test_processes_all_checks(self) -> None:
        rng = np.random.default_rng(3)
        d = 4
        X = rng.standard_normal(size=(50, d))
        Y = X.copy()  # identity transform
        rho = np.eye(d)
        checks = [
            {"X": X, "Y": Y, "rho": rho, "layer": i, "transform": "id"}
            for i in range(5)
        ]
        results = equivariance_errors_batch(checks)
        assert len(results) == 5
        for r in results:
            assert r.error < 1e-12

    def test_missing_key_raises(self) -> None:
        bad = [{"X": np.eye(2), "Y": np.eye(2), "rho": np.eye(2)}]  # no layer/transform
        with pytest.raises(ValueError, match="missing required key"):
            equivariance_errors_batch(bad)


class TestCrossLayerCoherence:
    def test_empty_is_one(self) -> None:
        assert cross_layer_coherence([]) == 1.0

    def test_all_zero_error(self) -> None:
        results = [
            EquivarianceResult(layer=i, transform="t", error=0.0, n_samples=1)
            for i in range(3)
        ]
        assert cross_layer_coherence(results) == 1.0

    def test_mixed_errors(self) -> None:
        results = [
            EquivarianceResult(layer=0, transform="t", error=0.1, n_samples=1),
            EquivarianceResult(layer=1, transform="t", error=0.2, n_samples=1),
            EquivarianceResult(layer=2, transform="t", error=0.3, n_samples=1),
        ]
        c = cross_layer_coherence(results)
        assert c == pytest.approx(1.0 - 0.2)

    def test_caps_extreme_errors(self) -> None:
        """A single layer with error > 1.0 should not drive coherence negative."""
        results = [
            EquivarianceResult(layer=0, transform="t", error=2.0, n_samples=1),
            EquivarianceResult(layer=1, transform="t", error=0.0, n_samples=1),
        ]
        c = cross_layer_coherence(results)
        # error=2.0 gets capped at 1.0; mean = 0.5; coherence = 0.5
        assert c == pytest.approx(0.5)
        assert 0.0 <= c <= 1.0
