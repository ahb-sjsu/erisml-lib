# ErisML I-EIP Monitor: ρ estimation via regularized Procrustes
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
r"""Representation-map estimation for the I-EIP criterion.

The I-EIP criterion (GUASS-SAI §16.1) is

.. math::

    h_\ell(g \cdot x) \approx \rho_\ell(g) \cdot h_\ell(x)

where :math:`h_\ell` is the model activation at layer :math:`\ell` and
:math:`\rho_\ell(g)` is the (unknown) representation map for the
transformation :math:`g`. This module estimates :math:`\rho_\ell(g)` from
pairs of activations collected on a calibration corpus.

The estimator is regularized least squares (ridge), equivalent to
the closed-form solution of

.. math::

    \hat\rho = \arg\min_\rho \| Y - \rho X \|_F^2 + \lambda \| \rho \|_F^2

which has the closed form

.. math::

    \hat\rho = Y X^T (X X^T + \lambda I)^{-1}

where columns of ``X`` are activations ``h(x)`` and columns of ``Y`` are
activations ``h(g·x)`` for the paired inputs.

This is the regularized Procrustes estimator referenced in GUASS-SAI
§16.5.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.typing import NDArray

# Default ridge regularization. Chosen small so ρ does not collapse
# toward zero on well-conditioned data, but large enough to stabilize
# solves when X is near-singular (e.g., large calibration sets on a
# thin activation dimension).
DEFAULT_LAMBDA = 1e-4

FloatArray = NDArray[np.floating]


def _as_matrix(arr: FloatArray) -> FloatArray:
    """Reshape (n, ...) tensors to (n, d) by flattening trailing dims.

    Activations from a transformer layer come in as ``(batch, seq, d)``
    or ``(batch, d)``; for ρ estimation we collapse everything but the
    activation dimension into the sample dimension.
    """
    if arr.ndim < 2:
        raise ValueError(
            f"activation array must have >= 2 dims (got shape {arr.shape})"
        )
    if arr.ndim == 2:
        return np.ascontiguousarray(arr, dtype=np.float64)
    # Flatten trailing dims: keep last dim as feature dim.
    n_feat = arr.shape[-1]
    flat = arr.reshape(-1, n_feat)
    return np.ascontiguousarray(flat, dtype=np.float64)


def estimate_rho(
    X: FloatArray,
    Y: FloatArray,
    lambda_reg: float = DEFAULT_LAMBDA,
) -> FloatArray:
    r"""Estimate the representation map ρ via regularized least squares.

    Parameters
    ----------
    X:
        Activations ``h_ℓ(x)`` for the un-transformed inputs, shape
        ``(n, d)`` or any ``(..., d)`` that flattens to ``(n, d)``.
    Y:
        Activations ``h_ℓ(g·x)`` for the paired transformed inputs,
        shape broadcast-compatible with ``X``.
    lambda_reg:
        Ridge regularization coefficient. Must be strictly positive.

    Returns
    -------
    rho:
        A ``(d, d)`` matrix satisfying ``Y ≈ X @ rho.T`` in the
        least-squares sense.

    Raises
    ------
    ValueError:
        If ``X`` and ``Y`` have mismatched shapes, too few samples,
        or ``lambda_reg`` is non-positive.

    Notes
    -----
    The returned matrix ``rho`` is shape ``(d, d)`` so that it right-
    multiplies row-vectors: ``h_transformed ≈ h @ rho.T``. This is the
    standard orientation in PyTorch and HuggingFace activation buffers.

    Complexity: ``O(n d^2)`` for the outer product and ``O(d^3)`` for
    the solve. For ``d`` above a few thousand, consider randomized
    sketching (see :func:`estimate_rho_sketched` - future work).
    """
    if lambda_reg <= 0:
        raise ValueError(f"lambda_reg must be > 0 (got {lambda_reg})")

    Xm = _as_matrix(X)
    Ym = _as_matrix(Y)

    if Xm.shape != Ym.shape:
        raise ValueError(
            f"X and Y must have matching shapes after flattening "
            f"(got {Xm.shape} vs {Ym.shape})"
        )
    n, d = Xm.shape
    if n < 2:
        raise ValueError(
            f"need at least 2 activation pairs for ρ estimation (got n={n})"
        )

    # Closed-form: ρ = Y^T X (X^T X + λI)^{-1}
    # Using the "row vector" convention: we seek ρ s.t. Y ≈ X @ ρ^T,
    # so internally we solve for ρ^T.
    gram = Xm.T @ Xm + lambda_reg * np.eye(d, dtype=np.float64)
    cross = Xm.T @ Ym  # (d, d) with rows indexed by Xm features
    rho_t = np.linalg.solve(gram, cross)  # ρ^T, shape (d, d)
    return rho_t.T  # (d, d) row-vector convention


def reconstruction_error(
    X: FloatArray,
    Y: FloatArray,
    rho: FloatArray,
    relative: bool = True,
) -> float:
    r"""Compute the reconstruction error of an estimated ρ.

    Parameters
    ----------
    X, Y:
        As in :func:`estimate_rho`.
    rho:
        The estimated representation map.
    relative:
        If True (default), return ``||Y - X ρ^T||_F / ||Y||_F``; else
        return the unnormalized Frobenius norm.

    Returns
    -------
    error:
        Scalar reconstruction error. 0 means perfect fit.
    """
    Xm = _as_matrix(X)
    Ym = _as_matrix(Y)
    if rho.shape[0] != rho.shape[1]:
        raise ValueError(f"rho must be square (got shape {rho.shape})")
    if Xm.shape[1] != rho.shape[0]:
        raise ValueError(
            f"feature dim mismatch: X has d={Xm.shape[1]} but " f"rho is {rho.shape}"
        )

    pred = Xm @ rho.T
    diff = Ym - pred
    num = float(np.linalg.norm(diff, ord="fro"))

    if not relative:
        return num
    denom = float(np.linalg.norm(Ym, ord="fro"))
    if denom < 1e-30:
        # Y is zero; report absolute error to avoid divide-by-zero.
        return num
    return num / denom


def split_pairs(
    X: FloatArray,
    Y: FloatArray,
    val_fraction: float = 0.2,
    seed: int | None = 0,
) -> Tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Split activation pairs into train / val for ρ estimation.

    Parameters
    ----------
    X, Y:
        Paired activations.
    val_fraction:
        Fraction of samples reserved for validation, in (0, 1).
    seed:
        Seed for the permutation. ``None`` uses a fresh random seed.

    Returns
    -------
    X_train, Y_train, X_val, Y_val:
        Matrix splits. Train fraction is ``1 - val_fraction``.
    """
    if not (0.0 < val_fraction < 1.0):
        raise ValueError(f"val_fraction must be in (0, 1) (got {val_fraction})")
    Xm = _as_matrix(X)
    Ym = _as_matrix(Y)
    n = Xm.shape[0]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    n_val = max(1, int(n * val_fraction))
    val_idx = perm[:n_val]
    train_idx = perm[n_val:]
    return Xm[train_idx], Ym[train_idx], Xm[val_idx], Ym[val_idx]
