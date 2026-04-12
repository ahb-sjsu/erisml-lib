# ErisML I-EIP Monitor: equivariance error computation
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Equivariance error metrics for the I-EIP criterion.

Given activations from an un-transformed input and its paired
transformed input, along with an estimated representation map ``ρ``,
the equivariance error measures how well ρ predicts the transformed
activation:

    error = ||h(g·x) - ρ · h(x)|| / ||h(g·x)||

Low error means the internal representation is equivariant with
respect to the declared transformation; high error means the model
treats semantically equivalent inputs differently internally.
"""

from __future__ import annotations

from typing import Iterable, List

import numpy as np
from numpy.typing import NDArray

from erisml.ieip.rho import _as_matrix, reconstruction_error
from erisml.ieip.types import EquivarianceResult

FloatArray = NDArray[np.floating]


def equivariance_error(
    X: FloatArray,
    Y: FloatArray,
    rho: FloatArray,
    layer: int,
    transform: str,
    relative: bool = True,
) -> EquivarianceResult:
    """Compute a single-layer single-transform equivariance error.

    Parameters
    ----------
    X:
        Activations ``h_ℓ(x)`` for the un-transformed inputs.
    Y:
        Activations ``h_ℓ(g·x)`` for the paired transformed inputs.
    rho:
        Previously estimated representation map ``ρ_ℓ(g)``.
    layer:
        Layer index (for the returned :class:`EquivarianceResult`).
    transform:
        Transform name.
    relative:
        If True, compute the ratio ``||err|| / ||Y||``; else the
        absolute Frobenius norm.

    Returns
    -------
    result:
        An :class:`EquivarianceResult` suitable for inclusion in an
        :class:`~erisml.ieip.types.IEIPReport`.
    """
    Xm = _as_matrix(X)
    err = reconstruction_error(Xm, Y, rho, relative=relative)
    n_samples = Xm.shape[0]
    return EquivarianceResult(
        layer=layer,
        transform=transform,
        error=err,
        n_samples=n_samples,
        relative=relative,
    )


def equivariance_errors_batch(
    checks: Iterable[dict],
    relative: bool = True,
) -> List[EquivarianceResult]:
    """Compute equivariance errors for a batch of (layer, transform) checks.

    Parameters
    ----------
    checks:
        Iterable of dicts, each with keys ``X``, ``Y``, ``rho``,
        ``layer``, ``transform``.
    relative:
        Relative vs absolute Frobenius. Applied uniformly.

    Returns
    -------
    results:
        A list of :class:`EquivarianceResult`, one per input check.

    Notes
    -----
    This is a convenience for running checks across the deployment's
    full (layer × transform) grid. Each check is independent; parallel
    execution is left to the caller.
    """
    results: List[EquivarianceResult] = []
    for check in checks:
        try:
            X = check["X"]
            Y = check["Y"]
            rho = check["rho"]
            layer = int(check["layer"])
            transform = str(check["transform"])
        except KeyError as e:
            raise ValueError(f"check missing required key: {e.args[0]!r}") from e
        result = equivariance_error(
            X=X,
            Y=Y,
            rho=rho,
            layer=layer,
            transform=transform,
            relative=relative,
        )
        results.append(result)
    return results


def cross_layer_coherence(results: List[EquivarianceResult]) -> float:
    """Summarize equivariance errors across layers.

    Cross-layer coherence is a single scalar in ``[0, 1]`` that is 1.0
    when all layers have zero equivariance error, and decays as errors
    grow. Defined as

        coherence = 1 - mean(min(error, 1.0))

    capped so a single catastrophic layer cannot drive the score
    negative.

    Parameters
    ----------
    results:
        Equivariance results across any set of (layer, transform)
        pairs.

    Returns
    -------
    coherence:
        Scalar in ``[0, 1]``. Returns 1.0 if ``results`` is empty.
    """
    if not results:
        return 1.0
    errors = np.array([min(r.error, 1.0) for r in results], dtype=np.float64)
    return float(1.0 - errors.mean())
