# ErisML I-EIP Monitor: non-degeneracy checks
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Non-degeneracy checks for internal representations.

A model whose activations are equivariant but *trivially* so (collapsed
to a constant, or concentrated in a very low-rank subspace) cannot be
safely governed: all inputs look the same to the monitor. These checks
catch that mode.

The primary metric is **effective rank**, defined as the exponential of
the Shannon entropy of the normalized singular values:

    effective_rank = exp(H(s)),    s_i_normalized = s_i / sum(s)

This is a continuous generalization of matrix rank: for a matrix with
exactly ``k`` nonzero equal singular values it returns ``k``; for
rank-1 it returns 1; for perfectly isotropic data it returns
``min(n, d)``. It is insensitive to the scale of the activations.
"""

from __future__ import annotations

from typing import List

import numpy as np
from numpy.typing import NDArray

from erisml.ieip.rho import _as_matrix
from erisml.ieip.types import AlertLevel, NondegeneracyMetrics

FloatArray = NDArray[np.floating]

# Default threshold: if effective rank drops below 10% of the max
# possible rank, raise CRITICAL; below 25% raise ELEVATED. These are
# deliberately conservative — real transformer activations on diverse
# input typically have effective rank in the 40–80% range.
DEFAULT_CRITICAL_EFFECTIVE_RANK_FRACTION = 0.10
DEFAULT_ELEVATED_EFFECTIVE_RANK_FRACTION = 0.25


def effective_rank(X: FloatArray, eps: float = 1e-12) -> float:
    """Compute the effective rank of an activation matrix.

    Parameters
    ----------
    X:
        Activations, shape ``(n, ...)``. Trailing dims are flattened.
    eps:
        Numerical floor; singular values below this are clipped to
        avoid ``log(0)``.

    Returns
    -------
    rank:
        Effective rank in ``[1, min(n, d)]``.

    Notes
    -----
    Uses singular-value decomposition (SVD). For large ``X`` this is
    ``O(min(n, d) * n * d)``; consider sketched SVD for very large
    activation buffers.
    """
    Xm = _as_matrix(X)
    # Center — effective rank of (X - mean) is what we actually want;
    # a constant bias does not represent meaningful activation diversity.
    Xc = Xm - Xm.mean(axis=0, keepdims=True)
    if Xc.size == 0:
        return 0.0
    singular_values = np.linalg.svd(Xc, compute_uv=False)
    # If the pre-clip signal is negligible, the representation is fully
    # collapsed — report effective rank 1. Without this short-circuit,
    # clipping all-zero singular values to eps yields a uniform
    # distribution over ``d`` bins and effective rank ``d`` — the
    # opposite of the right answer.
    if singular_values.size == 0 or float(singular_values.max()) < eps:
        return 1.0
    s = np.clip(singular_values, eps, None)
    p = s / s.sum()
    entropy = -float(np.sum(p * np.log(p)))
    return float(np.exp(entropy))


def _activation_range(X: FloatArray) -> float:
    """``max|h| - min|h|`` across all samples and features.

    A simple sanity check: if everything is the same magnitude the
    activations are either dead or saturated.
    """
    Xm = _as_matrix(X)
    abs_vals = np.abs(Xm)
    if abs_vals.size == 0:
        return 0.0
    return float(abs_vals.max() - abs_vals.min())


def _max_min_singular(X: FloatArray) -> tuple[float, float]:
    """Return ``(s_max, s_min)`` of a centered activation matrix."""
    Xm = _as_matrix(X)
    Xc = Xm - Xm.mean(axis=0, keepdims=True)
    if Xc.size == 0:
        return 0.0, 0.0
    s = np.linalg.svd(Xc, compute_uv=False)
    if s.size == 0:
        return 0.0, 0.0
    return float(s.max()), float(s.min())


def _classify_nondegeneracy(
    rank: float,
    max_possible: int,
    elevated_fraction: float,
    critical_fraction: float,
) -> AlertLevel:
    """Map effective rank to an alert level.

    Parameters
    ----------
    rank:
        Measured effective rank.
    max_possible:
        ``min(n, d)`` — the theoretical maximum.
    elevated_fraction, critical_fraction:
        Fractions of ``max_possible`` below which alerts fire.
    """
    if max_possible <= 0:
        return AlertLevel.CRITICAL
    fraction = rank / max_possible
    if fraction < critical_fraction:
        return AlertLevel.CRITICAL
    if fraction < elevated_fraction:
        return AlertLevel.ELEVATED
    return AlertLevel.NORMAL


def nondegeneracy_report(
    X: FloatArray,
    layer: int,
    elevated_fraction: float = DEFAULT_ELEVATED_EFFECTIVE_RANK_FRACTION,
    critical_fraction: float = DEFAULT_CRITICAL_EFFECTIVE_RANK_FRACTION,
) -> NondegeneracyMetrics:
    """Compute a :class:`NondegeneracyMetrics` for one layer's activations.

    Parameters
    ----------
    X:
        Activation matrix, shape ``(n, ...)``.
    layer:
        Layer index for the returned report.
    elevated_fraction, critical_fraction:
        Fractions of ``min(n, d)`` below which ELEVATED / CRITICAL
        alerts fire. See the defaults at the top of this module.

    Returns
    -------
    metrics:
        A :class:`NondegeneracyMetrics` with all fields populated and
        an alert level assigned.
    """
    if critical_fraction > elevated_fraction:
        raise ValueError(
            f"critical_fraction ({critical_fraction}) must be <= "
            f"elevated_fraction ({elevated_fraction})"
        )
    Xm = _as_matrix(X)
    n, d = Xm.shape
    rank = effective_rank(Xm)
    s_max, s_min = _max_min_singular(Xm)
    act_range = _activation_range(Xm)
    alert = _classify_nondegeneracy(
        rank=rank,
        max_possible=min(n, d),
        elevated_fraction=elevated_fraction,
        critical_fraction=critical_fraction,
    )
    return NondegeneracyMetrics(
        layer=layer,
        effective_rank=rank,
        max_singular_value=s_max,
        min_singular_value=s_min,
        activation_range=act_range,
        n_samples=n,
        alert_level=alert,
    )


def nondegeneracy_reports(
    activations_by_layer: dict[int, FloatArray],
    elevated_fraction: float = DEFAULT_ELEVATED_EFFECTIVE_RANK_FRACTION,
    critical_fraction: float = DEFAULT_CRITICAL_EFFECTIVE_RANK_FRACTION,
) -> List[NondegeneracyMetrics]:
    """Convenience: run :func:`nondegeneracy_report` across several layers."""
    return [
        nondegeneracy_report(
            X=X,
            layer=layer,
            elevated_fraction=elevated_fraction,
            critical_fraction=critical_fraction,
        )
        for layer, X in sorted(activations_by_layer.items())
    ]
