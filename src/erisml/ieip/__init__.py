# ErisML I-EIP Monitor (Internal Epistemic Invariance Principle)
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Internal Epistemic Invariance Principle (I-EIP) monitoring.

Runtime framework for applying the EIP to internal model state.

Implements GUASS-SAI Sprint 2.5 ("I-EIP Monitor Foundation"):

    h_ℓ(g·x) ≈ ρ_ℓ(g) · h_ℓ(x)

where ``h_ℓ`` is the activation at layer ℓ and ``ρ_ℓ`` is the estimated
representation map for transformation ``g``.

The monitoring half of the framework exposed here provides:

* :func:`estimate_rho` -- regularized Procrustes estimator for ρ
* :func:`equivariance_error` -- per-transform/per-layer error
* :class:`DriftDetector` -- EWMA baseline + threshold alerts
* :func:`nondegeneracy_report` -- effective-rank and range checks
* :class:`IEIPReport` -- aggregated metrics with text/JSON formatters
* :class:`ActivationProbe` -- PyTorch forward-hook wrapper (requires ``torch``)

See :doc:`docs/I-EIP_Monitor_Whitepaper` for the full specification
and :doc:`docs/development/I-EIP_Monitor_Sprint_Plan` for the roadmap.
"""

from __future__ import annotations

from erisml.ieip.drift import DriftDetector, compute_drift_alert
from erisml.ieip.equivariance import equivariance_error, equivariance_errors_batch
from erisml.ieip.nondegeneracy import effective_rank, nondegeneracy_report
from erisml.ieip.report import IEIPReport, aggregate_report
from erisml.ieip.rho import estimate_rho, reconstruction_error
from erisml.ieip.types import (
    AlertLevel,
    DriftReport,
    EquivarianceResult,
    NondegeneracyMetrics,
    ProbeSpec,
    TransformSpec,
)

__all__ = [
    "AlertLevel",
    "ActivationProbe",  # re-exported lazily below
    "DriftDetector",
    "DriftReport",
    "EquivarianceResult",
    "IEIPReport",
    "NondegeneracyMetrics",
    "ProbeSpec",
    "TransformSpec",
    "aggregate_report",
    "compute_drift_alert",
    "effective_rank",
    "equivariance_error",
    "equivariance_errors_batch",
    "estimate_rho",
    "nondegeneracy_report",
    "reconstruction_error",
]


def __getattr__(name: str):  # pragma: no cover - import shim
    """Lazy import for ``torch``-dependent classes.

    Keeps the top-level import torch-free so ``import erisml.ieip`` works
    even in environments without PyTorch installed.
    """
    if name == "ActivationProbe":
        from erisml.ieip.probes import ActivationProbe

        return ActivationProbe
    if name == "ProbeManager":
        from erisml.ieip.probes import ProbeManager

        return ProbeManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
