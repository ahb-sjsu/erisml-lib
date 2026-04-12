# ErisML I-EIP Monitor: types
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Typed data structures for the I-EIP monitoring framework.

All dataclasses are pure-Python and safe to import without PyTorch.
Numerical payloads use ``numpy.ndarray`` to avoid a hard torch dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Tuple


class AlertLevel(str, Enum):
    """Alert severity for drift and degeneracy signals.

    ``NORMAL`` means no action required. ``ELEVATED`` means log and
    monitor more closely. ``CRITICAL`` means the deployment should
    consider halting or falling back per its DEME profile.
    """

    NORMAL = "normal"
    ELEVATED = "elevated"
    CRITICAL = "critical"


ActivationSite = Literal["residual", "attn_out", "mlp_out", "pre_norm", "post_norm"]


@dataclass(frozen=True)
class ProbeSpec:
    """Specification of a read-only activation probe.

    Parameters
    ----------
    target_layer:
        Zero-based index of the layer to probe. Interpretation depends
        on the specific model; for decoder-only transformers this is
        typically the block index.
    activation_site:
        Where within the block to read. ``residual`` is the default and
        is the most informative for equivariance analysis.
    sampling_rate:
        Fraction of inferences to probe, in (0, 1]. Lower values reduce
        overhead at the cost of temporal resolution. Use 1.0 for
        safety-critical deployments.
    expected_shape:
        Optional shape assertion (without batch dim). If set, the probe
        fails closed when observed activations mismatch.
    name:
        Human-readable probe identifier for reports.
    """

    target_layer: int
    activation_site: ActivationSite = "residual"
    sampling_rate: float = 1.0
    expected_shape: Tuple[int, ...] | None = None
    name: str = ""

    def __post_init__(self) -> None:
        if self.target_layer < 0:
            raise ValueError(f"target_layer must be >= 0 (got {self.target_layer})")
        if not (0.0 < self.sampling_rate <= 1.0):
            raise ValueError(
                f"sampling_rate must be in (0, 1] (got {self.sampling_rate})"
            )
        if self.expected_shape is not None:
            if any(d <= 0 for d in self.expected_shape):
                raise ValueError(
                    f"expected_shape must have positive dims "
                    f"(got {self.expected_shape})"
                )


@dataclass(frozen=True)
class TransformSpec:
    """Declared meaning-preserving transformation ``g``.

    A ``TransformSpec`` names a transformation under which internal
    representations should be equivariant. It does not *apply* the
    transformation -- that happens in the calibration pipeline. It
    identifies the transformation for registry and reporting purposes.

    Parameters
    ----------
    name:
        Unique identifier within the transform registry
        (e.g., ``"paraphrase"``, ``"name_swap"``, ``"unit_m_to_ft"``).
    description:
        One-line description for human operators.
    registry_version:
        Version of the transform registry that signed this spec. Used
        for audit-artifact integrity.
    """

    name: str
    description: str = ""
    registry_version: str = "0.0.0"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("TransformSpec.name must be non-empty")


@dataclass
class EquivarianceResult:
    """Result of a single equivariance check.

    Parameters
    ----------
    layer:
        Layer index that was probed.
    transform:
        Name of the transform checked.
    error:
        Relative Frobenius error ``||h(g·x) - ρ·h(x)||_F / ||h(g·x)||_F``.
        0.0 means perfect equivariance; 1.0 means the prediction is no
        better than zero.
    n_samples:
        Number of activation pairs used.
    relative:
        Whether ``error`` is relative (default) or absolute Frobenius.
    """

    layer: int
    transform: str
    error: float
    n_samples: int
    relative: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "transform": self.transform,
            "error": self.error,
            "n_samples": self.n_samples,
            "relative": self.relative,
        }


@dataclass
class DriftReport:
    """Output of a :class:`DriftDetector` observation.

    Parameters
    ----------
    layer, transform:
        Which equivariance check this report pertains to.
    current_error:
        The equivariance error just observed.
    baseline_error:
        The EWMA baseline error maintained by the detector.
    drift:
        ``current_error - baseline_error``. Positive means drifting
        toward worse equivariance.
    alert_level:
        One of :class:`AlertLevel`. Derived from ``drift`` and configured
        thresholds.
    threshold_elevated, threshold_critical:
        The thresholds applied to produce ``alert_level``.
    """

    layer: int
    transform: str
    current_error: float
    baseline_error: float
    drift: float
    alert_level: AlertLevel
    threshold_elevated: float
    threshold_critical: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "transform": self.transform,
            "current_error": self.current_error,
            "baseline_error": self.baseline_error,
            "drift": self.drift,
            "alert_level": self.alert_level.value,
            "threshold_elevated": self.threshold_elevated,
            "threshold_critical": self.threshold_critical,
        }


@dataclass
class NondegeneracyMetrics:
    """Per-layer non-degeneracy metrics.

    A model with strong equivariance but collapsed internal
    representations is not safely governable -- all inputs look the
    same to the monitor. These metrics detect that collapse.

    Parameters
    ----------
    layer:
        Layer index.
    effective_rank:
        Exponential of the Shannon entropy of normalized singular
        values. Ranges in ``[1, min(n, d)]``. Higher is better.
    max_singular_value, min_singular_value:
        Range of activation singular values. A wide gap indicates
        well-organized representations.
    activation_range:
        ``max|h| - min|h|`` across the observed batch.
    n_samples:
        Number of activations used.
    alert_level:
        Derived from ``effective_rank`` against configured thresholds.
    """

    layer: int
    effective_rank: float
    max_singular_value: float
    min_singular_value: float
    activation_range: float
    n_samples: int
    alert_level: AlertLevel = AlertLevel.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "effective_rank": self.effective_rank,
            "max_singular_value": self.max_singular_value,
            "min_singular_value": self.min_singular_value,
            "activation_range": self.activation_range,
            "n_samples": self.n_samples,
            "alert_level": self.alert_level.value,
        }


@dataclass
class IEIPReport:
    """Aggregated I-EIP monitoring report for one inference window.

    This is the contract referenced by GUASS-SAI §16.4. It is what the
    gating layer consumes to decide ``allow`` / ``veto`` / ``redirect``
    (see the I-EIP Monitor Whitepaper §4).
    """

    equivariance: List[EquivarianceResult] = field(default_factory=list)
    drift: List[DriftReport] = field(default_factory=list)
    nondegeneracy: List[NondegeneracyMetrics] = field(default_factory=list)
    cross_layer_coherence: float = 0.0
    alert_level: AlertLevel = AlertLevel.NORMAL

    def summary(self) -> str:
        """One-line human-readable summary (mirrors GUASS-SAI §16.4)."""
        max_drift = max((r.drift for r in self.drift), default=0.0)
        return (
            f"I-EIP: {self.alert_level.value}, "
            f"max_drift={max_drift:+.4f}, "
            f"coherence={self.cross_layer_coherence:.3f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "equivariance": [r.to_dict() for r in self.equivariance],
            "drift": [r.to_dict() for r in self.drift],
            "nondegeneracy": [r.to_dict() for r in self.nondegeneracy],
            "cross_layer_coherence": self.cross_layer_coherence,
            "alert_level": self.alert_level.value,
            "summary": self.summary(),
        }
