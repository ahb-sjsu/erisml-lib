# ErisML I-EIP Monitor: drift detection
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Drift detection for I-EIP equivariance errors.

A deployed model's equivariance error should be stable over time. A
gradual increase indicates drift: fine-tuning leakage, distributional
shift, adversarial prefix accumulation, or weight corruption. This
module tracks an exponentially weighted moving average (EWMA) of the
equivariance error per (layer, transform) key, and raises alerts when
the current error departs from the baseline by more than the
configured thresholds.

EWMA is chosen over a simple rolling mean because:

* It has constant memory (one scalar per key), independent of history.
* It naturally weights recent observations more heavily.
* It is the canonical choice for statistical process-control charts,
  with well-studied properties (ARL, false-alarm rate).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from erisml.ieip.types import AlertLevel, DriftReport

# Default EWMA smoothing coefficient. 0.05 corresponds to a ~20-step
# "effective memory" — appropriate for per-inference monitoring where
# we want the baseline to adapt but not to track every fluctuation.
DEFAULT_ALPHA = 0.05

# Default absolute thresholds over the EWMA baseline. Well-calibrated
# ρ estimators produce relative equivariance errors in the 0.01–0.10
# range; sustained increases of 0.05 are meaningful, 0.10 demand
# intervention.
DEFAULT_ELEVATED_THRESHOLD = 0.05
DEFAULT_CRITICAL_THRESHOLD = 0.10


def compute_drift_alert(
    current: float,
    baseline: float,
    threshold_elevated: float = DEFAULT_ELEVATED_THRESHOLD,
    threshold_critical: float = DEFAULT_CRITICAL_THRESHOLD,
) -> AlertLevel:
    """Categorize a (current, baseline) pair into an alert level.

    Parameters
    ----------
    current, baseline:
        The just-observed error and the running EWMA baseline.
    threshold_elevated, threshold_critical:
        Drift amounts (``current - baseline``) at which alerts fire.

    Returns
    -------
    level:
        ``CRITICAL`` > ``ELEVATED`` > ``NORMAL``.
    """
    if threshold_elevated < 0 or threshold_critical < 0:
        raise ValueError("thresholds must be non-negative")
    if threshold_critical < threshold_elevated:
        raise ValueError(
            f"threshold_critical ({threshold_critical}) must be >= "
            f"threshold_elevated ({threshold_elevated})"
        )
    drift = current - baseline
    if drift >= threshold_critical:
        return AlertLevel.CRITICAL
    if drift >= threshold_elevated:
        return AlertLevel.ELEVATED
    return AlertLevel.NORMAL


@dataclass
class _EWMAState:
    """Internal EWMA state for one (layer, transform) key."""

    baseline: float
    n_observations: int


class DriftDetector:
    """EWMA-based drift detector for equivariance errors.

    Maintains one baseline per ``(layer, transform)`` key. Update the
    detector with each new observation via :meth:`observe`; it returns
    a :class:`DriftReport` with the current alert level.

    Parameters
    ----------
    alpha:
        EWMA smoothing coefficient in (0, 1). Higher means faster
        adaptation to new levels but more sensitivity to noise.
    threshold_elevated, threshold_critical:
        Drift thresholds passed to :func:`compute_drift_alert`.
    warmup_observations:
        Number of initial observations treated as baseline-building
        only (no alerts fire). After warmup, alerts are enabled.

    Examples
    --------
    >>> det = DriftDetector()
    >>> r = det.observe(layer=0, transform="paraphrase", error=0.02)
    >>> r.alert_level
    <AlertLevel.NORMAL: 'normal'>
    """

    def __init__(
        self,
        alpha: float = DEFAULT_ALPHA,
        threshold_elevated: float = DEFAULT_ELEVATED_THRESHOLD,
        threshold_critical: float = DEFAULT_CRITICAL_THRESHOLD,
        warmup_observations: int = 10,
    ) -> None:
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"alpha must be in (0, 1] (got {alpha})")
        if warmup_observations < 0:
            raise ValueError(
                f"warmup_observations must be >= 0 " f"(got {warmup_observations})"
            )
        if threshold_critical < threshold_elevated:
            raise ValueError("threshold_critical must be >= threshold_elevated")
        self.alpha = alpha
        self.threshold_elevated = threshold_elevated
        self.threshold_critical = threshold_critical
        self.warmup_observations = warmup_observations
        self._state: Dict[Tuple[int, str], _EWMAState] = {}

    def observe(
        self,
        layer: int,
        transform: str,
        error: float,
    ) -> DriftReport:
        """Record one observation and return its drift report.

        Parameters
        ----------
        layer, transform:
            The check being observed.
        error:
            The equivariance error just computed.

        Returns
        -------
        report:
            A :class:`DriftReport` with the current baseline and alert
            level. During warmup, alert_level is always ``NORMAL``.
        """
        if error < 0:
            raise ValueError(f"error must be non-negative (got {error})")
        key = (layer, transform)
        state = self._state.get(key)
        if state is None:
            # First observation: baseline = current, alert = NORMAL
            state = _EWMAState(baseline=error, n_observations=1)
            self._state[key] = state
            return DriftReport(
                layer=layer,
                transform=transform,
                current_error=error,
                baseline_error=error,
                drift=0.0,
                alert_level=AlertLevel.NORMAL,
                threshold_elevated=self.threshold_elevated,
                threshold_critical=self.threshold_critical,
            )
        # Determine alert BEFORE updating baseline so the alert is
        # based on the state we had prior to this observation.
        in_warmup = state.n_observations < self.warmup_observations
        alert = (
            AlertLevel.NORMAL
            if in_warmup
            else compute_drift_alert(
                current=error,
                baseline=state.baseline,
                threshold_elevated=self.threshold_elevated,
                threshold_critical=self.threshold_critical,
            )
        )
        drift = error - state.baseline
        # Update baseline with EWMA
        new_baseline = self.alpha * error + (1 - self.alpha) * state.baseline
        state.baseline = new_baseline
        state.n_observations += 1
        return DriftReport(
            layer=layer,
            transform=transform,
            current_error=error,
            baseline_error=new_baseline,
            drift=drift,
            alert_level=alert,
            threshold_elevated=self.threshold_elevated,
            threshold_critical=self.threshold_critical,
        )

    def baseline_for(self, layer: int, transform: str) -> float | None:
        """Return the current baseline for a key, or None if unseen."""
        state = self._state.get((layer, transform))
        return state.baseline if state is not None else None

    def reset(self, layer: int | None = None, transform: str | None = None) -> None:
        """Reset detector state.

        Parameters
        ----------
        layer:
            If provided, only reset keys with this layer.
        transform:
            If provided, only reset keys with this transform name.

        With both ``None`` (default), clears all state.
        """
        if layer is None and transform is None:
            self._state.clear()
            return
        keys_to_drop = [
            k
            for k in self._state
            if (layer is None or k[0] == layer)
            and (transform is None or k[1] == transform)
        ]
        for k in keys_to_drop:
            del self._state[k]
