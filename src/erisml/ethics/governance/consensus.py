"""Consensus / schism diagnostics for DEME aggregation.

When several EthicsModule judgements are collapsed into one governance verdict, the
aggregate (scalar weighted mean today, Frechet mean on the moral manifold in general)
is only trustworthy if the judgements form a *single* consensus rather than two camps.
This module flags **bimodal ("schism") judgement distributions** so a single aggregate
is not mistaken for agreement, and exposes the dispersion that conditions whether the
aggregate is even well-posed.

Provenance: derived from Endogenous Reference Theory (the moral reference as a
load-weighted Frechet mean; a bifurcated/non-unique reference = schism). The *thesis*
that real moral schism is curvature-driven is a separate, still-being-tested empirical
claim; this diagnostic does **not** depend on it. It is sound statistics on the
judgement distribution: a useful runtime "is this aggregate representative?" signal for
DEME and the I-EIP Monitor regardless of how that science lands.
"""

from __future__ import annotations

from typing import Optional, Sequence, Union
import numpy as np

Number = Union[float, int]


def _sarle_bc(x: np.ndarray) -> float:
    """Sarle's bimodality coefficient (works for small n). >0.555 suggests bimodality."""
    n = len(x)
    if n < 4 or np.std(x) == 0:
        return float("nan")
    s = ((x - x.mean()) ** 3).mean() / x.std() ** 3
    k = ((x - x.mean()) ** 4).mean() / x.std() ** 4
    return float((s**2 + 1) / (k + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))))


def _norm_pdf(v: np.ndarray, mu: float, var: float) -> np.ndarray:
    return np.exp(-0.5 * (v - mu) ** 2 / var) / np.sqrt(2.0 * np.pi * var)


def _gmm_dbic(x: np.ndarray) -> float:
    """BIC(1-component) - BIC(2-component) for a 1-D Gaussian mixture; >0 favors
    two components (a split). Pure-numpy EM with deterministic quantile init, so the
    core package needs no scikit-learn. Returns NaN for n<12 or zero-variance input."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 12 or np.std(x) == 0:
        return float("nan")

    # 1 component: 2 free params (mean, var)
    var1 = float(np.var(x)) + 1e-12
    ll1 = float(np.sum(np.log(_norm_pdf(x, float(np.mean(x)), var1) + 1e-300)))
    bic1 = -2.0 * ll1 + 2.0 * np.log(n)

    # 2 components: EM in 1-D, deterministic init at the quartiles
    mu = np.array([np.quantile(x, 0.25), np.quantile(x, 0.75)], dtype=float)
    var = np.array([var1, var1], dtype=float)
    w = np.array([0.5, 0.5], dtype=float)
    for _ in range(200):
        r = w[None, :] * _norm_pdf(x[:, None], mu[None, :], var[None, :])
        denom = r.sum(axis=1, keepdims=True)
        denom[denom == 0.0] = 1e-300
        resp = r / denom
        nk = resp.sum(axis=0) + 1e-12
        mu = (resp * x[:, None]).sum(axis=0) / nk
        var = np.clip(
            (resp * (x[:, None] - mu[None, :]) ** 2).sum(axis=0) / nk, 1e-6, None
        )
        w = nk / n
    mix = (w[None, :] * _norm_pdf(x[:, None], mu[None, :], var[None, :])).sum(axis=1)
    ll2 = float(np.sum(np.log(mix + 1e-300)))
    bic2 = -2.0 * ll2 + 5.0 * np.log(n)  # 5 params: 2 means, 2 vars, 1 mixing weight
    return float(bic1 - bic2)


def consensus_diagnostics(
    values: Sequence[Union[Number, Sequence[Number]]],
    weights: Optional[Sequence[Number]] = None,
    *,
    bic_threshold: float = 10.0,
    coef_threshold: float = 0.555,
) -> dict:
    """Diagnose whether a set of judgements forms one consensus or a schism.

    Args:
        values: 1-D sequence of scalar normative scores, OR a 2-D array
            (rows = judgements, cols = moral-vector dimensions).
        weights: optional per-judgement weights (e.g., EM/stakeholder weights).
        bic_threshold: GMM dBIC above which a two-camp split is declared (n>=12).
        coef_threshold: Sarle coefficient above which a split is declared (small n).

    Returns dict:
        n              : number of judgements
        dispersion     : weighted RMS spread (conditions well-posedness of the mean)
        bimodality_bic : GMM dBIC, or None if n<12 / unavailable
        bimodality_coef: Sarle's coefficient, or None
        schism         : bool — True if the judgements look like two camps
        basis          : which test decided ('bic' | 'coef_lowN' | 'insufficient')
        note           : human-readable summary
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return dict(
            n=0,
            dispersion=0.0,
            bimodality_bic=None,
            bimodality_coef=None,
            schism=False,
            basis="insufficient",
            note="no judgements",
        )
    w = np.ones(len(arr)) if weights is None else np.asarray(weights, float)
    w = w / w.sum() if w.sum() > 0 else np.ones(len(arr)) / len(arr)

    if arr.ndim == 2:
        mu = np.average(arr, axis=0, weights=w)
        C = arr - mu
        # weighted principal direction -> 1-D scores along the axis of disagreement
        _, _, Vt = np.linalg.svd(C * np.sqrt(w)[:, None], full_matrices=False)
        scores = C @ Vt[0]
        dispersion = float(np.sqrt(np.average((C**2).sum(1), weights=w)))
    else:
        scores = arr
        mu = float(np.average(arr, weights=w))
        dispersion = float(np.sqrt(np.average((arr - mu) ** 2, weights=w)))

    n = len(scores)
    bc = _sarle_bc(scores)
    dbic = _gmm_dbic(scores)

    if not np.isnan(dbic):
        schism, basis = (dbic > bic_threshold), "bic"
    elif not np.isnan(bc):
        schism, basis = (bc > coef_threshold), "coef_lowN"
    else:
        schism, basis = False, "insufficient"

    note = (
        f"schism: judgements split into two camps (dispersion={dispersion:.3f})"
        if schism
        else f"consensus: single cluster of judgements (dispersion={dispersion:.3f})"
    )
    if basis == "insufficient":
        note = f"too few/identical judgements to assess schism (n={n})"
    return dict(
        n=int(n),
        dispersion=dispersion,
        bimodality_bic=(None if np.isnan(dbic) else dbic),
        bimodality_coef=(None if np.isnan(bc) else bc),
        schism=bool(schism),
        basis=basis,
        note=note,
    )
