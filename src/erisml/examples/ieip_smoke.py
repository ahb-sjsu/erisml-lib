# ErisML I-EIP Monitor: end-to-end smoke demo
# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""End-to-end smoke demo for the I-EIP monitoring pipeline.

Runs on a tiny, self-contained PyTorch model (no HuggingFace / network
required) to demonstrate:

1. Attach probes to two layers
2. Run calibration pairs ``(x, g·x)`` for a declared transformation
3. Estimate ρ via regularized Procrustes
4. Compute equivariance errors
5. Feed into DriftDetector
6. Check non-degeneracy
7. Assemble and print an IEIPReport

Run: ``python -m erisml.examples.ieip_smoke``

This demo is also referenced as a reproducibility check in CI when
PyTorch is available.
"""

from __future__ import annotations

import sys
from typing import Tuple

import numpy as np

try:
    import torch
    from torch import nn
except ImportError:
    print(
        "PyTorch is not installed. Install with: " "pip install 'erisml-lib[ieip]'",
        file=sys.stderr,
    )
    sys.exit(0)  # skip demo, but do not fail the caller


from erisml.ieip import (
    ActivationProbe,
    DriftDetector,
    ProbeSpec,
    aggregate_report,
    equivariance_error,
    estimate_rho,
    nondegeneracy_report,
)
from erisml.ieip.report import format_text


def build_toy_model() -> nn.Module:
    """A small MLP that is roughly scale-equivariant.

    If ``g·x = 2·x``, an MLP with tanh activations is approximately
    equivariant at the hidden layer under a specific ρ we can estimate
    from data.
    """
    torch.manual_seed(0)
    return nn.Sequential(
        nn.Linear(16, 32),
        nn.Tanh(),
        nn.Linear(32, 32),
        nn.Tanh(),
        nn.Linear(32, 4),
    )


def calibration_pairs(
    model: nn.Module,
    probe: ActivationProbe,
    n: int,
    scale: float,
    rng: torch.Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    """Run ``n`` inputs through the model with and without ``g``.

    Here ``g`` is multiplication by ``scale``, a simple meaning-
    preserving transform under many normalization schemes.
    """
    # Baseline
    probe.attach()
    probe.clear()
    x = torch.randn((n, 16), generator=rng)
    with torch.no_grad():
        _ = model(x)
    X = probe.collected()
    probe.detach()

    # Transformed input
    probe.attach()
    probe.clear()
    with torch.no_grad():
        _ = model(scale * x)
    Y = probe.collected()
    probe.detach()

    return X, Y


def run() -> int:
    model = build_toy_model()
    # Probe the second Tanh layer (index 3 in the Sequential)
    probe = ActivationProbe(
        module=model[3],
        spec=ProbeSpec(target_layer=3, name="tanh_mid"),
    )

    rng = torch.Generator().manual_seed(7)

    # Calibration
    X_cal, Y_cal = calibration_pairs(model, probe, n=256, scale=1.05, rng=rng)
    rho = estimate_rho(X_cal, Y_cal, lambda_reg=1e-4)

    # Live monitoring
    drift_detector = DriftDetector(warmup_observations=5)
    live_equiv = []
    live_drift = []
    for _ in range(30):
        X_live, Y_live = calibration_pairs(model, probe, n=64, scale=1.05, rng=rng)
        result = equivariance_error(
            X_live, Y_live, rho, layer=3, transform="scale_1.05"
        )
        live_equiv.append(result)
        live_drift.append(
            drift_detector.observe(
                layer=result.layer,
                transform=result.transform,
                error=result.error,
            )
        )

    # Non-degeneracy snapshot on the last batch
    nondeg = nondegeneracy_report(X_live, layer=3)

    report = aggregate_report(
        equivariance=live_equiv[-3:],  # last 3 observations for brevity
        drift=live_drift[-3:],
        nondegeneracy=[nondeg],
    )

    print(format_text(report, wide=False))
    print(f"Summary: {report.summary()}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
