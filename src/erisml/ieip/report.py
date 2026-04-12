# ErisML I-EIP Monitor: report aggregator and formatters
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Aggregated I-EIP monitoring report.

An :class:`~erisml.ieip.types.IEIPReport` composes per-check results
(equivariance, drift, non-degeneracy) into a single artifact suitable
for storage, logging, or handoff to the gating layer. This module
provides:

* :func:`aggregate_report` - build a report from component results
* :func:`format_text` - human-readable table formatter
* :func:`format_json` - JSON serialization (compact or indented)
* :func:`max_alert_level` - reduce a list of alert levels to the
  strongest one, for top-level decision-making
"""

from __future__ import annotations

import json
from typing import Iterable, List

from erisml.ieip.equivariance import cross_layer_coherence
from erisml.ieip.types import (
    AlertLevel,
    DriftReport,
    EquivarianceResult,
    IEIPReport,
    NondegeneracyMetrics,
)

_ALERT_ORDER = {
    AlertLevel.NORMAL: 0,
    AlertLevel.ELEVATED: 1,
    AlertLevel.CRITICAL: 2,
}


def max_alert_level(levels: Iterable[AlertLevel]) -> AlertLevel:
    """Reduce a collection of alert levels to the strongest one.

    Ordering: CRITICAL > ELEVATED > NORMAL. An empty iterable returns
    NORMAL.
    """
    result = AlertLevel.NORMAL
    for lv in levels:
        if _ALERT_ORDER[lv] > _ALERT_ORDER[result]:
            result = lv
    return result


def aggregate_report(
    equivariance: List[EquivarianceResult],
    drift: List[DriftReport],
    nondegeneracy: List[NondegeneracyMetrics],
) -> IEIPReport:
    """Assemble an :class:`IEIPReport` from component lists.

    The aggregated ``alert_level`` is the maximum over all drift and
    non-degeneracy alerts. Equivariance results by themselves do not
    raise alerts (the alert comes from drift, which observes changes
    in those errors over time).

    Parameters
    ----------
    equivariance:
        Per-check equivariance errors.
    drift:
        Per-check drift reports, with alert levels already assigned by
        a :class:`~erisml.ieip.drift.DriftDetector`.
    nondegeneracy:
        Per-layer non-degeneracy metrics with alert levels.

    Returns
    -------
    report:
        An :class:`IEIPReport` with summary metrics filled in.
    """
    alerts: list[AlertLevel] = [r.alert_level for r in drift]
    alerts.extend(m.alert_level for m in nondegeneracy)
    top_alert = max_alert_level(alerts)
    coherence = cross_layer_coherence(equivariance)
    return IEIPReport(
        equivariance=list(equivariance),
        drift=list(drift),
        nondegeneracy=list(nondegeneracy),
        cross_layer_coherence=coherence,
        alert_level=top_alert,
    )


def format_text(report: IEIPReport, *, wide: bool = False) -> str:
    """Format a report as a human-readable table.

    Parameters
    ----------
    report:
        The report to format.
    wide:
        If True, use a wider column layout suitable for ≥120-char
        terminals. Default (False) fits in 80 columns.

    Returns
    -------
    text:
        Multi-line string. Always ends with a trailing newline.
    """
    lines: list[str] = []
    lines.append("=" * (100 if wide else 80))
    lines.append(f"I-EIP Monitor Report  —  {report.summary()}")
    lines.append("=" * (100 if wide else 80))

    # Equivariance
    if report.equivariance:
        lines.append("")
        lines.append("Equivariance errors:")
        header = f"{'layer':>6}  {'transform':<24}  {'error':>10}  {'n':>6}"
        lines.append(header)
        lines.append("-" * len(header))
        for r in report.equivariance:
            lines.append(
                f"{r.layer:>6}  {r.transform:<24}  "
                f"{r.error:>10.4f}  {r.n_samples:>6}"
            )

    # Drift
    if report.drift:
        lines.append("")
        lines.append("Drift:")
        header = (
            f"{'layer':>6}  {'transform':<24}  {'current':>10}  "
            f"{'baseline':>10}  {'drift':>10}  {'alert':<10}"
        )
        lines.append(header)
        lines.append("-" * len(header))
        for r in report.drift:
            lines.append(
                f"{r.layer:>6}  {r.transform:<24}  "
                f"{r.current_error:>10.4f}  "
                f"{r.baseline_error:>10.4f}  "
                f"{r.drift:>+10.4f}  "
                f"{r.alert_level.value:<10}"
            )

    # Non-degeneracy
    if report.nondegeneracy:
        lines.append("")
        lines.append("Non-degeneracy:")
        header = (
            f"{'layer':>6}  {'eff_rank':>10}  "
            f"{'s_max':>10}  {'s_min':>10}  {'alert':<10}"
        )
        lines.append(header)
        lines.append("-" * len(header))
        for m in report.nondegeneracy:
            lines.append(
                f"{m.layer:>6}  {m.effective_rank:>10.2f}  "
                f"{m.max_singular_value:>10.4f}  "
                f"{m.min_singular_value:>10.4f}  "
                f"{m.alert_level.value:<10}"
            )

    lines.append("")
    lines.append("=" * (100 if wide else 80))
    return "\n".join(lines) + "\n"


def format_json(report: IEIPReport, *, indent: int | None = 2) -> str:
    """Format a report as JSON.

    Parameters
    ----------
    report:
        The report to format.
    indent:
        JSON indentation. ``None`` produces compact one-line output
        suitable for logging.

    Returns
    -------
    text:
        JSON string.
    """
    return json.dumps(report.to_dict(), indent=indent, sort_keys=True)
