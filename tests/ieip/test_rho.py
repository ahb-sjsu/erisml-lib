# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Tests for erisml.ieip.rho — regularized Procrustes ρ estimation."""

from __future__ import annotations

import numpy as np
import pytest

from erisml.ieip.rho import (
    DEFAULT_LAMBDA,
    estimate_rho,
    reconstruction_error,
    split_pairs,
)


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


class TestEstimateRho:
    def test_recovers_known_linear_map(self, rng: np.random.Generator) -> None:
        """If Y = X @ ρ^T exactly, estimator should recover ρ closely."""
        n, d = 500, 16
        X = rng.standard_normal(size=(n, d))
        # True ρ: a random orthogonal matrix scaled
        true_rho, _ = np.linalg.qr(rng.standard_normal(size=(d, d)))
        Y = X @ true_rho.T
        rho_hat = estimate_rho(X, Y, lambda_reg=1e-8)
        # With tiny regularization, reconstruction should be very close
        err = reconstruction_error(X, Y, rho_hat)
        assert err < 1e-4

    def test_rejects_nonpositive_lambda(self) -> None:
        X = np.eye(4)
        Y = np.eye(4)
        with pytest.raises(ValueError, match="lambda_reg"):
            estimate_rho(X, Y, lambda_reg=0.0)
        with pytest.raises(ValueError, match="lambda_reg"):
            estimate_rho(X, Y, lambda_reg=-1.0)

    def test_shape_mismatch_rejected(self) -> None:
        X = np.zeros((10, 4))
        Y = np.zeros((10, 5))
        with pytest.raises(ValueError, match="matching shapes"):
            estimate_rho(X, Y)

    def test_too_few_samples_rejected(self) -> None:
        X = np.zeros((1, 4))
        Y = np.zeros((1, 4))
        with pytest.raises(ValueError, match="at least 2"):
            estimate_rho(X, Y)

    def test_accepts_3d_activation_tensors(self, rng: np.random.Generator) -> None:
        """Activations shape (batch, seq, d) should flatten to (n, d)."""
        batch, seq, d = 4, 10, 8
        X = rng.standard_normal(size=(batch, seq, d))
        Y = X + 0.01 * rng.standard_normal(size=(batch, seq, d))
        rho = estimate_rho(X, Y)
        assert rho.shape == (d, d)

    def test_returns_square_matrix(self, rng: np.random.Generator) -> None:
        X = rng.standard_normal(size=(100, 12))
        Y = rng.standard_normal(size=(100, 12))
        rho = estimate_rho(X, Y)
        assert rho.shape == (12, 12)

    def test_regularization_reduces_norm_on_noisy_data(
        self, rng: np.random.Generator
    ) -> None:
        """Larger λ should shrink ρ toward 0 on pure-noise pairs."""
        n, d = 50, 8
        X = rng.standard_normal(size=(n, d))
        Y = rng.standard_normal(size=(n, d))  # independent noise
        rho_small = estimate_rho(X, Y, lambda_reg=1e-6)
        rho_large = estimate_rho(X, Y, lambda_reg=1.0)
        assert np.linalg.norm(rho_large) < np.linalg.norm(rho_small)

    def test_deterministic(self, rng: np.random.Generator) -> None:
        X = rng.standard_normal(size=(50, 6))
        Y = X @ np.eye(6) * 2.0
        rho1 = estimate_rho(X, Y, lambda_reg=DEFAULT_LAMBDA)
        rho2 = estimate_rho(X, Y, lambda_reg=DEFAULT_LAMBDA)
        np.testing.assert_array_equal(rho1, rho2)

    def test_scale_equivariance(self, rng: np.random.Generator) -> None:
        """If Y is scaled by c, recovered ρ should scale by c too.

        Only holds in the limit λ → 0; we use tiny λ.
        """
        n, d = 200, 8
        X = rng.standard_normal(size=(n, d))
        Y = X @ np.eye(d) * 3.0 + 0.001 * rng.standard_normal(size=(n, d))
        rho_base = estimate_rho(X, Y, lambda_reg=1e-10)
        rho_scaled = estimate_rho(X, 5.0 * Y, lambda_reg=1e-10)
        np.testing.assert_allclose(rho_scaled, 5.0 * rho_base, atol=1e-4)


class TestReconstructionError:
    def test_zero_error_on_exact_fit(self) -> None:
        n, d = 20, 4
        rng = np.random.default_rng(7)
        X = rng.standard_normal(size=(n, d))
        rho = np.eye(d) * 2.0
        Y = X @ rho.T
        err = reconstruction_error(X, Y, rho, relative=True)
        assert err < 1e-12

    def test_relative_vs_absolute(self) -> None:
        n, d = 20, 4
        rng = np.random.default_rng(11)
        X = rng.standard_normal(size=(n, d))
        rho = np.eye(d)
        Y = X + 0.5 * rng.standard_normal(size=(n, d))
        rel = reconstruction_error(X, Y, rho, relative=True)
        abs_ = reconstruction_error(X, Y, rho, relative=False)
        assert 0.0 < rel < 1.0
        assert abs_ > 0.0
        assert rel != abs_

    def test_zero_Y_handles_division_safely(self) -> None:
        X = np.zeros((5, 4))
        Y = np.zeros((5, 4))
        rho = np.eye(4)
        # Should not divide by zero; returns absolute value (0 here)
        err = reconstruction_error(X, Y, rho, relative=True)
        assert err == 0.0

    def test_non_square_rho_rejected(self) -> None:
        X = np.zeros((5, 4))
        Y = np.zeros((5, 4))
        rho = np.zeros((4, 3))
        with pytest.raises(ValueError, match="square"):
            reconstruction_error(X, Y, rho)

    def test_feature_dim_mismatch_rejected(self) -> None:
        X = np.zeros((5, 4))
        Y = np.zeros((5, 4))
        rho = np.eye(3)
        with pytest.raises(ValueError, match="feature dim"):
            reconstruction_error(X, Y, rho)


class TestSplitPairs:
    def test_splits_add_up(self, rng: np.random.Generator) -> None:
        X = rng.standard_normal(size=(100, 8))
        Y = rng.standard_normal(size=(100, 8))
        Xt, Yt, Xv, Yv = split_pairs(X, Y, val_fraction=0.2, seed=0)
        assert Xt.shape[0] + Xv.shape[0] == 100
        assert Yt.shape[0] + Yv.shape[0] == 100
        assert Xv.shape[0] == 20

    def test_reproducible_with_seed(self, rng: np.random.Generator) -> None:
        X = rng.standard_normal(size=(50, 4))
        Y = rng.standard_normal(size=(50, 4))
        a = split_pairs(X, Y, seed=42)
        b = split_pairs(X, Y, seed=42)
        for arr_a, arr_b in zip(a, b):
            np.testing.assert_array_equal(arr_a, arr_b)

    def test_different_seeds_differ(self, rng: np.random.Generator) -> None:
        X = rng.standard_normal(size=(50, 4))
        Y = rng.standard_normal(size=(50, 4))
        a_train = split_pairs(X, Y, seed=1)[0]
        b_train = split_pairs(X, Y, seed=2)[0]
        assert not np.array_equal(a_train, b_train)

    @pytest.mark.parametrize("frac", [0.0, 1.0, 1.5, -0.2])
    def test_bad_fraction_rejected(self, frac: float) -> None:
        X = np.zeros((10, 4))
        Y = np.zeros((10, 4))
        with pytest.raises(ValueError, match="val_fraction"):
            split_pairs(X, Y, val_fraction=frac)

    def test_at_least_one_val_sample(self, rng: np.random.Generator) -> None:
        X = rng.standard_normal(size=(10, 4))
        Y = rng.standard_normal(size=(10, 4))
        _, _, Xv, _ = split_pairs(X, Y, val_fraction=0.01, seed=0)
        assert Xv.shape[0] >= 1
