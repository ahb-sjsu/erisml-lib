# Chapter 18: Deploying Geometric Validation in Production

> *"What gets measured gets managed---but only if it gets measured automatically, continuously, and with enough dimensionality to detect the failures that matter."*
> --- Adapted from Peter Drucker

The geometric methods developed across Chapters 3--15 and composed into pipelines in Chapter 16 are powerful precisely because they replace scalar summaries with multi-dimensional analysis. But power in a notebook is not the same as power in production. A geometric validation that runs manually once per quarter provides a snapshot; a geometric validation that runs on every pull request, monitors every deployed model, and alerts on every frontier degradation provides a *system*. This chapter bridges the gap between the two.

We begin with the mechanics of integrating the `structural-fuzzing` package into CI/CD pipelines as a PyPI dependency. We then develop automated regression testing against MRI thresholds (Chapter 9), monitoring of Pareto frontier stability over time, and alerting when geometric baselines degrade. The middle sections address the engineering concerns that distinguish production from research: performance budgets, timeout handling, and designing `evaluate_fn` for models that live behind API endpoints. We close with LaTeX report generation for stakeholder communication and the versioning of geometric baselines---the production analog of the "save your weights" practice in model training.

---

## 18.1 The structural-fuzzing Package as a Production Dependency

### 18.1.1 Installation and Pinning

The `structural-fuzzing` package is published on PyPI and requires Python 3.10 or later. Its only hard dependency is NumPy (>= 1.24). This minimal dependency footprint is a deliberate design decision: a validation tool that drags in a hundred transitive dependencies becomes a liability in production environments where dependency conflicts are a constant source of breakage.

In a production `requirements.txt` or `pyproject.toml`, pin the version explicitly:

```toml
[project]
dependencies = [
    "structural-fuzzing==0.2.0",
    # ... other production dependencies
]
```

For organizations that mirror PyPI internally, the package installs cleanly from private indices:

```bash
pip install structural-fuzzing==0.2.0 --index-url https://pypi.internal.corp.example.com/simple
```

The optional `examples` extras (`scikit-learn`, `pandas`) are development conveniences and should not be installed in production images. If your `evaluate_fn` requires scikit-learn, that dependency belongs in your application's dependency list, not in the validation tool's.

### 18.1.2 Import Patterns for Production Code

In production systems, import the pipeline entry point and the report types directly:

```python
from structural_fuzzing.pipeline import run_campaign, StructuralFuzzReport
from structural_fuzzing.mri import compute_mri, ModelRobustnessIndex
from structural_fuzzing.pareto import pareto_frontier
from structural_fuzzing.report import format_report, format_latex_tables
```

Avoid star imports. Avoid importing the entire `structural_fuzzing` namespace. Each import should be traceable to a specific use in the calling code, which matters when dependency audits ask "why does this service depend on `structural-fuzzing`?"

---

## 18.2 Integrating Structural Fuzzing into CI/CD Pipelines

### 18.2.1 The Baseline CI Configuration

The project's own CI pipeline (`.github/workflows/ci.yaml`) provides the template. It runs tests across Python 3.10--3.13, installs in editable mode with dev extras, and runs `pytest` with coverage. A production integration extends this pattern by adding a *validation job* that runs structural fuzzing against the model under test.

The following GitHub Actions workflow illustrates the pattern. It assumes a repository that contains both a trained model and the evaluation harness:

```yaml
name: Model Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"  # Weekly Monday 6 AM UTC

jobs:
  structural-fuzz:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install structural-fuzzing==0.2.0

      - name: Run structural fuzzing campaign
        run: python scripts/run_validation.py --output results/

      - name: Check MRI threshold
        run: python scripts/check_thresholds.py results/campaign.json

      - name: Upload validation artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: structural-fuzz-results
          path: results/
          retention-days: 90
```

Three design decisions merit attention.

**The `schedule` trigger.** Structural fuzzing on every commit is often too expensive. The workflow above runs the full campaign weekly on a schedule, while PR-triggered runs execute a lighter check (Section 18.4). The scheduled run establishes the baseline; PR runs check for regressions against it.

**The `timeout-minutes` limit.** Production CI must have a hard upper bound on execution time. A campaign that runs indefinitely---because an `evaluate_fn` hangs, because a combinatorial explosion was not anticipated---blocks the pipeline and erodes trust in the validation system. Section 18.5 discusses timeout handling in detail.

**Artifact retention.** Campaign results are uploaded as CI artifacts with a 90-day retention window. This creates a versioned history of geometric baselines that can be compared over time (Section 18.8).

### 18.2.2 The Validation Script

The `run_validation.py` script is the bridge between the CI environment and the structural fuzzing API. Its structure follows the `run_campaign` function signature from `structural_fuzzing.pipeline`:

```python
#!/usr/bin/env python
"""Run structural fuzzing validation in CI."""

import json
import sys
from pathlib import Path

import numpy as np
from structural_fuzzing.pipeline import run_campaign
from structural_fuzzing.report import format_report, format_latex_tables

from my_model import load_model, make_evaluate_fn


def main() -> None:
    output_dir = Path(sys.argv[sys.argv.index("--output") + 1])
    output_dir.mkdir(parents=True, exist_ok=True)

    model = load_model("models/production_v3.pkl")

    dim_names = ["Size", "Complexity", "Halstead", "OO", "Process"]
    evaluate_fn = make_evaluate_fn(model, dataset="validation_holdout")

    report = run_campaign(
        dim_names=dim_names,
        evaluate_fn=evaluate_fn,
        max_subset_dims=3,
        n_mri_perturbations=300,
        mri_scale=0.5,
        verbose=True,
    )

    # Save structured results
    results = {
        "mri": report.mri_result.mri if report.mri_result else None,
        "mri_p95": report.mri_result.p95_omega if report.mri_result else None,
        "pareto_count": len(report.pareto_results),
        "pareto_maes": [p.mae for p in report.pareto_results],
        "pareto_dims": [p.n_dims for p in report.pareto_results],
        "sensitivity_ranking": [
            {"dim": s.dim_name, "delta_mae": s.delta_mae}
            for s in report.sensitivity_results
        ],
        "adversarial_count": len(report.adversarial_results),
    }

    with open(output_dir / "campaign.json", "w") as f:
        json.dump(results, f, indent=2)

    # Save text report
    with open(output_dir / "report.txt", "w") as f:
        f.write(format_report(report))

    # Save LaTeX tables
    with open(output_dir / "tables.tex", "w") as f:
        f.write(format_latex_tables(report))

    print(f"\nResults written to {output_dir}/")


if __name__ == "__main__":
    main()
```

The critical design element is the serialization of structured results to JSON. Text reports are for humans; JSON is for the threshold-checking step that follows.

---

## 18.3 Automated Regression Testing with MRI Thresholds

### 18.3.1 Defining Threshold Policies

The Model Robustness Index (Chapter 9) compresses the perturbation response distribution into a single score that explicitly accounts for tail risk. In production, this score becomes a *gate*: if the MRI exceeds a threshold, the pipeline fails and the change does not merge.

A threshold policy specifies acceptable bounds on the campaign results:

```python
from dataclasses import dataclass


@dataclass
class ThresholdPolicy:
    """Defines acceptable bounds for structural fuzzing results."""

    max_mri: float = 2.0
    max_mri_p95: float = 4.0
    min_pareto_count: int = 2
    max_best_mae: float = 3.0
    max_adversarial_count: int = 10
    max_sensitivity_delta: float = 5.0
```

The `max_mri` threshold deserves careful calibration. An MRI of 2.0 means the weighted combination of mean deviation, 75th percentile, and 95th percentile is at most 2.0---the model's error roughly doubles under the worst perturbations seen during validation. Whether this is acceptable depends on the domain. For a defect prediction model that informs code review priorities, an MRI of 2.0 may be fine. For a model that triggers automated security responses, an MRI above 1.0 may be unacceptable. Chapter 9 provides guidance on setting these thresholds based on domain-specific risk tolerance.

The `max_mri_p95` threshold independently bounds the tail of the perturbation distribution. A model can have a low composite MRI (because the mean is low) while still exhibiting catastrophic behavior in the worst 5% of perturbations. Bounding P95 separately catches this case.

### 18.3.2 The Threshold Checker

The `check_thresholds.py` script loads the JSON results and applies the policy:

```python
#!/usr/bin/env python
"""Check structural fuzzing results against threshold policy."""

import json
import sys


def check_thresholds(results_path: str) -> bool:
    with open(results_path) as f:
        results = json.load(f)

    failures: list[str] = []

    # MRI checks
    mri = results.get("mri")
    if mri is not None and mri > 2.0:
        failures.append(f"MRI {mri:.4f} exceeds threshold 2.0")

    mri_p95 = results.get("mri_p95")
    if mri_p95 is not None and mri_p95 > 4.0:
        failures.append(f"MRI P95 {mri_p95:.4f} exceeds threshold 4.0")

    # Pareto frontier check
    pareto_count = results.get("pareto_count", 0)
    if pareto_count < 2:
        failures.append(
            f"Pareto frontier has {pareto_count} points "
            f"(minimum 2 required)"
        )

    # Best MAE check
    pareto_maes = results.get("pareto_maes", [])
    if pareto_maes and min(pareto_maes) > 3.0:
        failures.append(
            f"Best Pareto MAE {min(pareto_maes):.4f} exceeds threshold 3.0"
        )

    # Sensitivity check: no single dimension should dominate excessively
    for entry in results.get("sensitivity_ranking", []):
        if abs(entry["delta_mae"]) > 5.0:
            failures.append(
                f"Dimension '{entry['dim']}' has excessive sensitivity "
                f"(delta_MAE={entry['delta_mae']:.4f}, threshold=5.0)"
            )

    # Report
    if failures:
        print("STRUCTURAL FUZZING THRESHOLD CHECK: FAILED")
        for f in failures:
            print(f"  - {f}")
        return False
    else:
        print("STRUCTURAL FUZZING THRESHOLD CHECK: PASSED")
        print(f"  MRI: {mri:.4f}")
        print(f"  Pareto points: {pareto_count}")
        print(f"  Best MAE: {min(pareto_maes):.4f}" if pareto_maes else "")
        return True


if __name__ == "__main__":
    success = check_thresholds(sys.argv[1])
    sys.exit(0 if success else 1)
```

The exit code is the contract with the CI system: zero means pass, non-zero means fail. When `check_thresholds.py` exits with code 1, the GitHub Actions step fails, the PR check turns red, and the change cannot merge without an explicit override.

### 18.3.3 Baseline Comparison Mode

Threshold checking against fixed constants is a starting point. The more powerful mode compares against a *previous baseline*:

```python
def check_regression(current_path: str, baseline_path: str) -> bool:
    """Check for regressions relative to a stored baseline."""
    with open(current_path) as f:
        current = json.load(f)
    with open(baseline_path) as f:
        baseline = json.load(f)

    failures: list[str] = []

    # MRI regression: current should not be more than 20% worse
    if current["mri"] is not None and baseline["mri"] is not None:
        ratio = current["mri"] / baseline["mri"]
        if ratio > 1.2:
            failures.append(
                f"MRI regressed by {(ratio - 1) * 100:.1f}% "
                f"({baseline['mri']:.4f} -> {current['mri']:.4f})"
            )

    # Pareto frontier should not shrink
    if current["pareto_count"] < baseline["pareto_count"]:
        failures.append(
            f"Pareto frontier shrunk from {baseline['pareto_count']} "
            f"to {current['pareto_count']} points"
        )

    # Best MAE should not increase by more than 10%
    curr_best = min(current["pareto_maes"]) if current["pareto_maes"] else float("inf")
    base_best = min(baseline["pareto_maes"]) if baseline["pareto_maes"] else float("inf")
    if curr_best > base_best * 1.1:
        failures.append(
            f"Best MAE regressed by {(curr_best / base_best - 1) * 100:.1f}% "
            f"({base_best:.4f} -> {curr_best:.4f})"
        )

    if failures:
        print("REGRESSION CHECK: FAILED")
        for f in failures:
            print(f"  - {f}")
        return False
    else:
        print("REGRESSION CHECK: PASSED")
        return True
```

The 20% MRI degradation tolerance and 10% MAE tolerance are configurable parameters, not universal constants. They should be set based on the same domain-specific risk analysis that informs the absolute thresholds.

---

## 18.4 Designing evaluate_fn for Production Models

### 18.4.1 The Contract

The `run_campaign` function (Chapter 16) requires a single callable with the signature:

```python
evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]]
```

The function takes a parameter vector (a NumPy array of length $n$, where $n$ is the number of dimensions) and returns a tuple of `(mae, errors)`. The `mae` is the primary scalar objective; `errors` is a dictionary of named error components that the framework uses for sensitivity analysis and adversarial threshold detection.

In research, `evaluate_fn` typically wraps a scikit-learn model and a local dataset. In production, the model may live behind a gRPC endpoint, the dataset may be sampled from a data warehouse, and the function must handle network failures, authentication, and rate limits.

### 18.4.2 Wrapping a Production Model

The following pattern wraps a model served via HTTP:

```python
import time
from functools import lru_cache
from typing import Any

import numpy as np
import requests


def make_evaluate_fn(
    endpoint: str,
    api_key: str,
    dataset_uri: str,
    timeout_seconds: float = 30.0,
    max_retries: int = 3,
) -> callable:
    """Create an evaluate_fn that calls a production model endpoint.

    Parameters
    ----------
    endpoint : str
        Model serving endpoint URL.
    api_key : str
        Authentication token.
    dataset_uri : str
        URI of the validation dataset.
    timeout_seconds : float
        Per-request timeout.
    max_retries : int
        Number of retries on transient failures.
    """
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })

    def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
        payload = {
            "params": params.tolist(),
            "dataset_uri": dataset_uri,
        }

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = session.post(
                    endpoint,
                    json=payload,
                    timeout=timeout_seconds,
                )
                resp.raise_for_status()
                result = resp.json()
                return result["mae"], result["errors"]
            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                wait = 2 ** attempt  # Exponential backoff
                time.sleep(wait)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    wait = float(
                        e.response.headers.get("Retry-After", 2 ** attempt)
                    )
                    time.sleep(wait)
                    last_error = e
                else:
                    raise

        raise RuntimeError(
            f"evaluate_fn failed after {max_retries} retries: {last_error}"
        )

    return evaluate_fn
```

Three aspects of this implementation matter for production reliability.

**Retries with exponential backoff.** A transient network failure should not terminate the entire campaign. The exponential backoff prevents retry storms that would overwhelm the model serving infrastructure.

**Rate limit handling.** Production model endpoints often enforce rate limits. The `429` handler respects the `Retry-After` header, adapting to the server's back-pressure signal.

**Timeout per request.** The `timeout_seconds` parameter bounds individual evaluations. This is distinct from the campaign-level timeout (Section 18.5) which bounds the entire run.

### 18.4.3 Caching Evaluations

Structural fuzzing explores many parameter configurations, and some may be evaluated more than once (e.g., the all-dimensions baseline appears in both subset enumeration and MRI computation). Caching eliminates redundant evaluations:

```python
def make_cached_evaluate_fn(
    base_fn: callable,
    cache_size: int = 4096,
) -> callable:
    """Wrap an evaluate_fn with an LRU cache.

    Note: NumPy arrays are not hashable. We convert to a tuple
    of rounded values for cache keys.
    """
    cache: dict[tuple, tuple[float, dict[str, float]]] = {}

    def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
        key = tuple(np.round(params, decimals=10))
        if key not in cache:
            if len(cache) >= cache_size:
                # Evict oldest entry (FIFO)
                oldest = next(iter(cache))
                del cache[oldest]
            cache[key] = base_fn(params)
        return cache[key]

    return evaluate_fn
```

The rounding in the cache key prevents floating-point drift from defeating cache lookups. For parameter spaces explored on a log scale, rounding to 10 decimal places is well below the precision that matters.

---

## 18.5 Performance Budgets and Timeout Handling

### 18.5.1 Estimating Campaign Cost

A structural fuzzing campaign's computational cost is determined by the number of `evaluate_fn` calls, which depends on the configuration:

| Phase | Evaluations | Formula |
|-------|-------------|---------|
| Subset enumeration | $\sum_{k=1}^{K} \binom{n}{k} \cdot C(k)$ | $C(k)$: optimization cost per subset of size $k$ |
| Sensitivity profiling | $2n$ | One with, one without per dimension |
| MRI perturbation | $N_\text{pert}$ | Typically 300 |
| Adversarial search | $n \cdot \lceil\log_2(R / \epsilon)\rceil$ | Binary search per dimension |
| Compositional test | $n \cdot C$ | One optimization per step |

For the default configuration with $n = 5$ dimensions, $K = 4$, $N_\text{pert} = 300$, and $C(k)$ using the grid/random strategy with 20 grid points and 5000 random samples:

- Subset enumeration: $\binom{5}{1} \cdot 20 + \binom{5}{2} \cdot 20^2 + \binom{5}{3} \cdot 5000 + \binom{5}{4} \cdot 5000 \approx 79,100$ evaluations
- Sensitivity: $10$ evaluations
- MRI: $300$ evaluations
- Adversarial: $\approx 100$ evaluations
- Compositional: $\approx 25,000$ evaluations

Total: roughly 104,000 evaluations. If each evaluation takes 10 milliseconds, the campaign completes in about 17 minutes. If each evaluation takes 1 second (typical for a model behind an API), the campaign would take nearly 29 hours---far too long for CI.

### 18.5.2 Budgeting Strategies

The solution is to adjust campaign parameters to fit a time budget:

```python
def budget_campaign_params(
    n_dims: int,
    eval_time_seconds: float,
    budget_minutes: float = 20.0,
) -> dict:
    """Compute campaign parameters that fit within a time budget.

    Parameters
    ----------
    n_dims : int
        Number of dimensions in the model.
    eval_time_seconds : float
        Estimated time per evaluate_fn call, in seconds.
    budget_minutes : float
        Total time budget for the campaign, in minutes.

    Returns
    -------
    dict
        Keyword arguments for run_campaign.
    """
    budget_seconds = budget_minutes * 60
    budget_evals = int(budget_seconds / eval_time_seconds)

    # Reserve 30% for MRI, 10% for sensitivity/adversarial,
    # 60% for subset enumeration
    mri_budget = int(budget_evals * 0.30)
    enum_budget = int(budget_evals * 0.60)

    # Determine max subset size that fits
    from math import comb
    max_k = 1
    total = 0
    for k in range(1, n_dims + 1):
        n_subsets = comb(n_dims, k)
        evals_per = 20 ** k if k <= 2 else 5000
        cost = n_subsets * evals_per
        if total + cost > enum_budget:
            break
        total += cost
        max_k = k

    # Scale MRI perturbations
    n_perturbations = min(mri_budget, 500)
    n_perturbations = max(n_perturbations, 50)  # Floor

    return {
        "max_subset_dims": max_k,
        "n_mri_perturbations": n_perturbations,
        "n_grid": 15,
        "n_random": min(3000, enum_budget // max(comb(n_dims, max_k), 1)),
    }
```

The 60/30/10 split prioritizes subset enumeration (the most informative phase) and MRI (the most operationally relevant). Sensitivity profiling and adversarial search are cheap and run unconditionally.

### 18.5.3 Campaign-Level Timeouts

Beyond budgeting, a hard timeout prevents runaway campaigns:

```python
import signal
from contextlib import contextmanager


class CampaignTimeoutError(Exception):
    """Raised when a campaign exceeds its time budget."""
    pass


@contextmanager
def campaign_timeout(seconds: int):
    """Context manager that raises CampaignTimeoutError after `seconds`.

    Note: This uses SIGALRM and is only available on Unix systems.
    For cross-platform support, use threading.Timer instead.
    """
    def handler(signum, frame):
        raise CampaignTimeoutError(
            f"Campaign exceeded {seconds}s timeout"
        )

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# Usage in CI:
# with campaign_timeout(1200):  # 20 minutes
#     report = run_campaign(...)
```

When the timeout fires, the `CampaignTimeoutError` propagates up, the CI step fails, and the artifact upload step (marked `if: always()`) still runs, capturing whatever partial results were produced.

---

## 18.6 Monitoring Model Robustness Over Time

### 18.6.1 The Robustness Time Series

A single MRI value is a snapshot. A *time series* of MRI values, collected weekly or after every model retrain, reveals trends that no individual measurement can capture. Is the model becoming more brittle as the data distribution shifts? Is robustness improving as the training pipeline matures? These questions require longitudinal data.

The monitoring system is straightforward: store campaign results in a time-series database (or, for simpler setups, append to a JSON Lines file) and compute statistics over windows:

```python
import json
from datetime import datetime
from pathlib import Path


def append_to_history(
    results: dict,
    history_path: Path,
    model_version: str,
) -> None:
    """Append campaign results to the history file."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": model_version,
        **results,
    }
    with open(history_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_history(history_path: Path) -> list[dict]:
    """Load all history entries."""
    entries = []
    with open(history_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def compute_trend(
    history: list[dict],
    metric: str = "mri",
    window: int = 8,
) -> dict:
    """Compute trend statistics over the last `window` entries.

    Returns
    -------
    dict
        Keys: current, mean, std, slope, is_degrading.
    """
    values = [
        e[metric] for e in history[-window:]
        if e.get(metric) is not None
    ]
    if len(values) < 2:
        return {"current": values[-1] if values else None,
                "insufficient_data": True}

    import numpy as np
    arr = np.array(values)
    xs = np.arange(len(arr), dtype=float)

    # Linear regression for slope
    slope = float(np.polyfit(xs, arr, 1)[0])

    return {
        "current": float(arr[-1]),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "slope": slope,
        "is_degrading": slope > 0,  # Positive slope = increasing MRI = worse
        "window_size": len(values),
    }
```

The `slope` field is the key signal. A consistently positive MRI slope means robustness is degrading over time---even if each individual measurement is still below the absolute threshold. Catching a *trend* before it crosses a *threshold* is the difference between proactive maintenance and firefighting.

### 18.6.2 Alerting on Pareto Frontier Degradation

The Pareto frontier is a more nuanced robustness signal than MRI alone. A frontier with four non-dominated points at model version $v$ that collapses to two points at version $v+1$ indicates that the model has lost diversity in its accuracy-simplicity tradeoffs---even if the best MAE is unchanged.

Frontier degradation can be detected by comparing the *hypervolume indicator* (the area dominated by the frontier in the $(k, \text{MAE})$ plane) across versions:

```python
def pareto_hypervolume(
    pareto_dims: list[int],
    pareto_maes: list[float],
    ref_dims: int = 10,
    ref_mae: float = 10.0,
) -> float:
    """Compute the hypervolume dominated by the Pareto frontier.

    Uses a reference point (ref_dims, ref_mae) as the upper-right
    corner of the dominated region. Larger hypervolume is better.
    """
    if not pareto_dims or not pareto_maes:
        return 0.0

    # Sort by dims ascending
    points = sorted(zip(pareto_dims, pareto_maes))

    area = 0.0
    prev_dims = 0
    for dims, mae in points:
        if mae < ref_mae:
            width = dims - prev_dims
            height = ref_mae - mae
            area += width * height
            prev_dims = dims

    # Add final rectangle to reference point
    if prev_dims < ref_dims:
        last_mae = points[-1][1]
        if last_mae < ref_mae:
            area += (ref_dims - prev_dims) * (ref_mae - last_mae)

    return area


def check_frontier_degradation(
    current: dict,
    baseline: dict,
    min_hypervolume_ratio: float = 0.85,
) -> tuple[bool, str]:
    """Check if the Pareto frontier has degraded relative to baseline.

    Returns (passed, message).
    """
    curr_hv = pareto_hypervolume(
        current["pareto_dims"], current["pareto_maes"]
    )
    base_hv = pareto_hypervolume(
        baseline["pareto_dims"], baseline["pareto_maes"]
    )

    if base_hv == 0:
        return True, "No baseline hypervolume to compare against"

    ratio = curr_hv / base_hv
    if ratio < min_hypervolume_ratio:
        return False, (
            f"Pareto hypervolume degraded to {ratio:.1%} of baseline "
            f"({curr_hv:.2f} vs {base_hv:.2f})"
        )
    return True, f"Pareto hypervolume ratio: {ratio:.1%}"
```

The 85% threshold means the frontier's dominated area must remain within 15% of the baseline. This is a *relative* check, not absolute, which makes it robust to differences in scale across models.

### 18.6.3 Integration with Monitoring Infrastructure

For teams that use Prometheus, Datadog, or similar observability platforms, campaign results can be exported as custom metrics:

```python
def emit_metrics(results: dict, model_name: str) -> dict[str, float]:
    """Convert campaign results to flat metric dictionary.

    The caller is responsible for sending these to the monitoring
    backend (e.g., Prometheus push gateway, Datadog API).
    """
    metrics = {}
    prefix = f"structural_fuzz.{model_name}"

    if results.get("mri") is not None:
        metrics[f"{prefix}.mri"] = results["mri"]
    if results.get("mri_p95") is not None:
        metrics[f"{prefix}.mri_p95"] = results["mri_p95"]

    metrics[f"{prefix}.pareto_count"] = results.get("pareto_count", 0)

    if results.get("pareto_maes"):
        metrics[f"{prefix}.best_mae"] = min(results["pareto_maes"])

    metrics[f"{prefix}.adversarial_count"] = results.get(
        "adversarial_count", 0
    )

    return metrics
```

The flat metric dictionary integrates with any monitoring backend. A Grafana dashboard plotting `structural_fuzz.defect_model.mri` over time provides at-a-glance robustness monitoring without requiring stakeholders to understand the geometric details.

---

## 18.7 Interpreting Results in Automated Contexts

### 18.7.1 The Interpretation Problem

In a notebook, a practitioner reads the campaign report, examines the Pareto frontier, and makes a judgment. In CI, there is no practitioner---only a pass/fail gate. The gap between rich geometric output and binary CI decisions is bridged by *interpretation rules*: codified heuristics that translate multi-dimensional results into actionable signals.

The following interpretation framework maps campaign results to severity levels:

```python
from enum import Enum


class Severity(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


def interpret_campaign(results: dict) -> list[dict]:
    """Interpret campaign results into actionable findings."""
    findings: list[dict] = []

    # MRI interpretation
    mri = results.get("mri")
    if mri is not None:
        if mri > 3.0:
            findings.append({
                "metric": "MRI",
                "severity": Severity.CRITICAL,
                "value": mri,
                "message": (
                    f"MRI of {mri:.2f} indicates severe fragility. "
                    f"The model's error triples under worst-case "
                    f"perturbations."
                ),
            })
        elif mri > 2.0:
            findings.append({
                "metric": "MRI",
                "severity": Severity.WARNING,
                "value": mri,
                "message": (
                    f"MRI of {mri:.2f} indicates moderate fragility. "
                    f"Consider investigating high-sensitivity dimensions."
                ),
            })
        else:
            findings.append({
                "metric": "MRI",
                "severity": Severity.OK,
                "value": mri,
                "message": f"MRI of {mri:.2f} is within acceptable bounds.",
            })

    # Sensitivity concentration
    rankings = results.get("sensitivity_ranking", [])
    if len(rankings) >= 2:
        top_delta = abs(rankings[0]["delta_mae"])
        second_delta = abs(rankings[1]["delta_mae"])
        if second_delta > 0 and top_delta / second_delta > 3.0:
            findings.append({
                "metric": "sensitivity_concentration",
                "severity": Severity.WARNING,
                "value": top_delta / second_delta,
                "message": (
                    f"Dimension '{rankings[0]['dim']}' dominates sensitivity "
                    f"({top_delta:.2f} vs {second_delta:.2f}). "
                    f"The model is over-dependent on a single feature group."
                ),
            })

    # Adversarial threshold count
    adv_count = results.get("adversarial_count", 0)
    if adv_count > len(rankings) * 2:
        findings.append({
            "metric": "adversarial_thresholds",
            "severity": Severity.WARNING,
            "value": adv_count,
            "message": (
                f"Found {adv_count} adversarial thresholds. "
                f"Multiple dimensions have tipping points."
            ),
        })

    return findings
```

Each finding includes a severity level, the metric that triggered it, the raw value, and a human-readable message. The message is written for automated Slack notifications or PR comments, not for geometric experts---it explains the *implication* of the value, not the mathematical definition.

### 18.7.2 PR Comments from CI

GitHub Actions can post findings directly as PR comments, making geometric validation visible in the developer workflow:

```yaml
      - name: Post validation comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(
              fs.readFileSync('results/campaign.json', 'utf8')
            );
            const mri = results.mri ? results.mri.toFixed(4) : 'N/A';
            const pareto = results.pareto_count || 0;
            const bestMae = results.pareto_maes && results.pareto_maes.length
              ? Math.min(...results.pareto_maes).toFixed(4)
              : 'N/A';

            const body = [
              '## Structural Fuzzing Validation',
              '',
              '| Metric | Value |',
              '|--------|-------|',
              `| MRI | ${mri} |`,
              `| Pareto points | ${pareto} |`,
              `| Best MAE | ${bestMae} |`,
              `| Adversarial thresholds | ${results.adversarial_count || 0} |`,
              '',
              `Full report available in [CI artifacts](${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}).`,
            ].join('\n');

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: body,
            });
```

This closes the feedback loop: the developer who changed the model sees the geometric impact of their change directly in the pull request, without navigating to a separate dashboard.

---

## 18.8 LaTeX Report Generation for Stakeholders

### 18.8.1 The Reporting Pipeline

Not every consumer of geometric validation results is a developer reading PR comments. Model governance boards, regulatory reviewers, and academic collaborators expect formatted reports with tables, captions, and proper typesetting. The `format_latex_tables` function in `structural_fuzzing.report` generates publication-ready LaTeX directly from campaign results.

The function produces three tables: the Pareto frontier (with `\label{tab:pareto}`), the sensitivity ranking (with `\label{tab:sensitivity}`), and the MRI summary (with `\label{tab:mri}`). Each table uses the `booktabs` package for professional formatting:

```python
from structural_fuzzing.report import format_latex_tables

latex_code = format_latex_tables(report)
with open("validation_report/tables.tex", "w") as f:
    f.write(latex_code)
```

The generated LaTeX integrates into a larger document via `\input{tables.tex}`. A minimal wrapper document:

```latex
\documentclass{article}
\usepackage{booktabs}

\title{Model Validation Report: Defect Predictor v3.2}
\author{Automated Validation Pipeline}
\date{\today}

\begin{document}
\maketitle

\section{Geometric Validation Results}

The following results were produced by the structural fuzzing
framework (v0.2.0) running against the production validation
holdout set.

\input{tables.tex}

\section{Interpretation}

The Model Robustness Index of 1.43 indicates that under
worst-case perturbations within the explored parameter space,
the model's mean absolute error increases by a factor of
approximately 1.4. The 95th percentile perturbation produces
a deviation of 3.1, indicating non-trivial tail risk.

The Pareto frontier identifies four non-dominated configurations,
suggesting meaningful tradeoffs between model complexity and
prediction accuracy. See Chapter~5 of \cite{bond2026geometric}
for the theoretical basis of Pareto analysis in this context.

\end{document}
```

### 18.8.2 Automating Report Generation in CI

The CI pipeline can produce compiled PDFs by adding a LaTeX compilation step:

```yaml
      - name: Generate LaTeX report
        run: |
          python scripts/generate_report.py results/ report/

      - name: Compile PDF
        uses: xu-cheng/latex-action@v3
        with:
          root_file: report/validation_report.tex
          working_directory: report/

      - name: Upload PDF report
        uses: actions/upload-artifact@v4
        with:
          name: validation-report-pdf
          path: report/validation_report.pdf
```

The compiled PDF is available as a downloadable artifact. For organizations that require audit trails, these PDFs provide timestamped, version-controlled evidence of model validation at every release.

---

## 18.9 Versioning Geometric Baselines

### 18.9.1 The Baseline Problem

A regression check requires a baseline to regress against. Where does the baseline come from? Who updates it? What happens when the model architecture changes and the old baseline is no longer comparable?

The simplest approach stores the baseline JSON alongside the model in version control:

```
models/
    production_v3/
        model.pkl
        geometric_baseline.json
        threshold_policy.json
```

When a new model version is promoted to production, its campaign results become the new baseline:

```python
import shutil


def promote_baseline(
    campaign_results_path: str,
    baseline_path: str,
    archive_dir: str,
) -> None:
    """Promote current results to baseline, archiving the old one."""
    baseline = Path(baseline_path)
    archive = Path(archive_dir)
    archive.mkdir(parents=True, exist_ok=True)

    # Archive old baseline with timestamp
    if baseline.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        archive_name = f"baseline_{timestamp}.json"
        shutil.copy2(baseline, archive / archive_name)

    # Promote new results
    shutil.copy2(campaign_results_path, baseline)
    print(f"Promoted {campaign_results_path} to {baseline_path}")
```

### 18.9.2 Schema Versioning

As the structural fuzzing framework evolves, the JSON schema of campaign results may change. A `schema_version` field in every results file prevents silent incompatibilities:

```python
def save_results(results: dict, path: str) -> None:
    """Save campaign results with schema version."""
    versioned = {
        "schema_version": "1.0",
        "framework_version": "0.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        **results,
    }
    with open(path, "w") as f:
        json.dump(versioned, f, indent=2)


def load_results(path: str) -> dict:
    """Load campaign results, validating schema version."""
    with open(path) as f:
        data = json.load(f)

    version = data.get("schema_version", "unknown")
    if version != "1.0":
        raise ValueError(
            f"Unsupported schema version: {version}. "
            f"Expected 1.0. Re-run the campaign to generate "
            f"a compatible baseline."
        )
    return data
```

When the schema changes, the loader raises an explicit error rather than silently misinterpreting fields. This is the geometric analog of the "your saved model is incompatible with this version of the framework" error that every ML practitioner has encountered.

### 18.9.3 Baseline Branching for A/B Tests

When multiple model variants are under evaluation simultaneously (A/B tests, champion/challenger deployments), each variant needs its own baseline:

```
baselines/
    champion/
        geometric_baseline.json
        threshold_policy.json
    challenger_v1/
        geometric_baseline.json
        threshold_policy.json
    challenger_v2/
        geometric_baseline.json
        threshold_policy.json
```

The CI pipeline selects the appropriate baseline based on the branch or an environment variable:

```yaml
      - name: Check thresholds
        run: |
          VARIANT="${{ github.head_ref || 'champion' }}"
          BASELINE="baselines/${VARIANT}/geometric_baseline.json"
          if [ ! -f "$BASELINE" ]; then
            BASELINE="baselines/champion/geometric_baseline.json"
          fi
          python scripts/check_thresholds.py \
            results/campaign.json \
            --baseline "$BASELINE"
```

The fallback to the champion baseline ensures that new variants are compared against the production standard when no variant-specific baseline exists.

---

## 18.10 A Complete Production Integration Example

Bringing the pieces together, the following is a complete GitHub Actions workflow for a team that deploys a defect prediction model weekly, runs structural fuzzing on every PR and nightly, and generates PDF reports for the model governance board:

```yaml
name: Model Validation Pipeline

on:
  pull_request:
    branches: [main]
    paths:
      - "models/**"
      - "src/**"
      - "scripts/run_validation.py"
  schedule:
    - cron: "0 3 * * *"  # Nightly at 3 AM UTC

jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e ".[dev]"
          pip install structural-fuzzing==0.2.0

      - name: Estimate evaluation cost
        id: budget
        run: |
          python -c "
          from scripts.budget import estimate_budget
          params = estimate_budget(
              n_dims=5,
              eval_time_seconds=0.05,
              budget_minutes=30,
          )
          print(f'max_subset_dims={params[\"max_subset_dims\"]}')
          print(f'n_mri_perturbations={params[\"n_mri_perturbations\"]}')
          " >> "$GITHUB_OUTPUT"

      - name: Run structural fuzzing
        run: |
          python scripts/run_validation.py \
            --output results/ \
            --model models/production_latest.pkl \
            --dataset data/validation_holdout.parquet

      - name: Check absolute thresholds
        run: python scripts/check_thresholds.py results/campaign.json

      - name: Check regression against baseline
        run: |
          python scripts/check_thresholds.py \
            results/campaign.json \
            --baseline baselines/champion/geometric_baseline.json \
            --max-mri-regression 0.20 \
            --max-mae-regression 0.10

      - name: Update history
        if: github.event_name == 'schedule'
        run: |
          python scripts/update_history.py \
            results/campaign.json \
            monitoring/mri_history.jsonl

      - name: Generate PDF report
        if: github.event_name == 'schedule'
        run: python scripts/generate_report.py results/ report/

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-${{ github.sha }}
          path: |
            results/
            report/
          retention-days: 90
```

This workflow embodies the production deployment principles developed throughout this chapter: budget-aware campaign configuration, absolute and relative threshold checks, longitudinal monitoring, stakeholder reporting, and versioned artifacts.

---

## 18.11 Operational Considerations

### 18.11.1 Flaky Evaluations

Production `evaluate_fn` implementations are subject to non-determinism: stochastic models produce different outputs on each call, data sampling introduces variance, and network latency adds noise. A campaign that fails on Monday and passes on Tuesday---with no code changes---erodes trust in the validation system.

The mitigation is to run the MRI computation with enough perturbations to produce stable statistics (at least 200; 300 is the default) and to set thresholds with headroom. If the MRI consistently measures 1.4 and the threshold is 1.5, a noisy evaluation will occasionally cross the boundary. Setting the threshold at 2.0 provides operational margin while still catching genuine regressions.

### 18.11.2 Secrets Management

The `evaluate_fn` for a production model endpoint requires API keys, database credentials, or service account tokens. These must never appear in CI logs, workflow files, or campaign results.

Store secrets in the CI platform's secret store (GitHub Actions secrets, GitLab CI variables) and pass them via environment variables:

```yaml
      - name: Run structural fuzzing
        env:
          MODEL_API_KEY: ${{ secrets.MODEL_API_KEY }}
          DATA_WAREHOUSE_URI: ${{ secrets.DATA_WAREHOUSE_URI }}
        run: python scripts/run_validation.py --output results/
```

The validation script reads from `os.environ`, never from configuration files that might be committed.

### 18.11.3 Resource Isolation

A structural fuzzing campaign that evaluates 100,000+ parameter configurations exerts sustained load on the model serving infrastructure. In production, this load should be directed at a *staging* or *shadow* replica, not at the production endpoint serving live traffic. The CI workflow should configure `evaluate_fn` to point at the staging environment, which is the same model version but isolated from production traffic.

---

## 18.12 Summary

Deploying geometric validation in production transforms it from an analytical technique into an engineering system. The key components are:

1. **Package dependency management.** The `structural-fuzzing` package's minimal dependency footprint (NumPy only) makes it safe to include in production environments.

2. **CI/CD integration.** Campaign results gate merges via threshold checks; PR comments surface geometric metrics in the developer workflow.

3. **MRI thresholds.** Absolute bounds catch catastrophic fragility; relative bounds (regression checks against baselines) catch gradual degradation.

4. **Pareto frontier monitoring.** Hypervolume comparison detects loss of tradeoff diversity that scalar metrics would miss.

5. **Performance budgets.** Campaign parameters are automatically tuned to fit CI time constraints.

6. **evaluate_fn engineering.** Production models behind API endpoints require retry logic, caching, and timeout handling.

7. **LaTeX reporting.** Automated PDF generation provides audit-ready documentation for governance and regulatory review.

8. **Baseline versioning.** Schema-versioned JSON baselines, archived on promotion, enable longitudinal comparison and A/B test support.

The system described in this chapter does not require any changes to the model itself. It operates entirely on the `evaluate_fn` interface established in Chapter 16: give the framework a callable that maps parameter vectors to errors, and it will quantify robustness, identify fragilities, and enforce quality gates---automatically, repeatedly, and with full geometric fidelity.

---

## 18.13 Connection to Chapter 19

This chapter treated the `evaluate_fn` as a black box: given a parameter vector, it returns a scalar error and a dictionary of named components. Chapter 19 opens the black box. It examines how geometric validation interacts with specific model architectures---deep neural networks, gradient-boosted trees, Gaussian processes---and how architectural properties (differentiability, ensemble structure, posterior uncertainty) can be exploited to make structural fuzzing more efficient and more informative. Where this chapter asked "how do we deploy geometric validation?", Chapter 19 asks "how do we make the models themselves geometric-validation-aware?"
