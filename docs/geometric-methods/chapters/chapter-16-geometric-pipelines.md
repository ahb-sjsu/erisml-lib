# Chapter 16: Building Geometric Pipelines

> *"A complex system that works is invariably found to have evolved from a simple system that worked."*
> --- John Gall, *Systemantics* (1975)

The preceding chapters developed a collection of geometric tools---subset enumeration, Pareto frontier extraction, sensitivity profiling, the Model Robustness Index, adversarial threshold search---each addressing a distinct aspect of model validation. Used in isolation, each tool answers a narrow question. Used in sequence, they compose into something qualitatively different: an end-to-end geometric pipeline that maps a model specification to a structured, multi-dimensional validation report.

This chapter is about that composition. We develop the pipeline pattern as a first-class design concern, examine the `run_campaign` API that orchestrates all six analysis stages, study the `StructuralFuzzReport` dataclass that captures structured output, and explore the report generation facilities that transform raw results into human-readable text and publication-ready LaTeX. We close with practical guidance on designing evaluation callbacks, handling errors in long-running campaigns, and configuring the pipeline for different tradeoffs between speed and thoroughness.

---

## 16.1 The Pipeline Pattern

### 16.1.1 Why Composition Matters

Each geometric tool from Parts II and III answers one question:

| Tool | Chapter | Question |
|------|---------|----------|
| Subset enumeration | 4 | Which dimension combinations matter? |
| Pareto frontier | 5 | Which configurations are non-dominated tradeoffs? |
| Sensitivity profiling | 7 | How much does each dimension contribute? |
| Model Robustness Index | 7 | How stable is the best configuration under perturbation? |
| Adversarial threshold search | 14 | Where are the exact tipping points? |
| Compositional testing | 15 | In what order should dimensions be added? |

The answers to these questions are not independent. The Pareto frontier depends on the subset enumeration results. Sensitivity profiling uses the best configuration found by enumeration as its baseline. The MRI perturbs that same baseline. Adversarial search probes the dimensions that sensitivity profiling identified as critical. Each stage consumes the output of its predecessors and enriches the overall picture.

This data-flow dependency is what makes a pipeline more than a script that calls six functions in sequence. The pipeline must:

1. Thread results from early stages to later stages automatically.
2. Present a unified configuration surface so that parameters controlling all six stages can be specified in one place.
3. Produce a single structured output that captures all results, rather than scattering them across variables.
4. Handle partial failures gracefully---if adversarial search times out, the subset and Pareto results should still be available.

### 16.1.2 The Six-Stage Architecture

The structural fuzzing pipeline proceeds through six stages, each building on the previous:

```
Subset Enumeration
       |
       v
 Pareto Frontier
       |
       v
Sensitivity Profile  <-- uses best configuration from stage 1
       |
       v
  MRI Computation    <-- uses best configuration from stage 1
       |
       v
Adversarial Search   <-- probes each dimension independently
       |
       v
Compositional Test   <-- greedy dimension-addition sequence
```

The first two stages are tightly coupled: Pareto extraction is a filter over subset results. The middle two stages (sensitivity and MRI) both operate on the best configuration discovered in stage 1 but are independent of each other---they could, in principle, run in parallel. The final two stages are independent of each other but depend on earlier results for their baseline parameters.

An optional seventh phase runs forward selection and backward elimination baselines, providing classical feature-selection comparisons against the geometric methods. These baselines serve as a sanity check: if forward selection discovers a configuration that the exhaustive subset enumeration missed, something is wrong with the enumeration parameters.

### 16.1.3 Data Flow and the Evaluation Function

A single callable---the evaluation function---is the thread that connects all six stages. Every stage calls this function, sometimes hundreds or thousands of times, with different parameter vectors. The function's signature is the contract that binds the pipeline together:

```python
def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
    ...
```

The function takes a parameter vector (one value per dimension) and returns a tuple of `(mae, errors)` where `mae` is the aggregate mean absolute error and `errors` is a dictionary mapping named metrics to their signed deviations from targets. This dual return---a scalar summary plus a structured breakdown---enables the pipeline to optimize on the scalar while preserving per-metric detail for reporting.

The evaluation function is the pipeline's most important abstraction boundary. Everything inside it---data loading, model training, metric computation---is domain-specific. Everything outside it---subset enumeration, Pareto analysis, sensitivity profiling---is domain-agnostic. The pipeline does not know or care whether the evaluation function trains a random forest, runs a game-theoretic simulation, or queries an external API. It only knows the contract: parameters in, errors out.

---

## 16.2 The `run_campaign` API

### 16.2.1 Function Signature and Parameters

The `run_campaign` function is the pipeline's public entry point. Its signature exposes every tuning knob while providing sensible defaults:

```python
def run_campaign(
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    max_subset_dims: int = 4,
    n_mri_perturbations: int = 300,
    mri_scale: float = 0.5,
    mri_weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
    start_dim: int = 0,
    candidate_dims: Sequence[int] | None = None,
    run_baselines: bool = True,
    adversarial_tolerance: float = 0.5,
    inactive_value: float = 1e6,
    n_grid: int = 20,
    n_random: int = 5000,
    verbose: bool = True,
) -> StructuralFuzzReport:
```

The parameters fall into four groups:

**Problem specification.** `dim_names` provides human-readable names for each dimension, and `evaluate_fn` is the evaluation callback described above. These two arguments fully specify the problem.

**Enumeration control.** `max_subset_dims` caps the largest subset size explored during enumeration. For $n$ dimensions, the number of subsets up to size $k$ is $\sum_{i=1}^{k} \binom{n}{i}$. With $n = 9$ and $k = 4$, this is 255 subsets. With $k = 5$, it rises to 381. The default of 4 balances thoroughness against computation time. The `n_grid` and `n_random` parameters control how each subset is optimized: `n_grid` sets the number of grid points for 1D and 2D optimization, while `n_random` sets the number of random samples for 3D and higher subsets. The `inactive_value` (default $10^6$) is the sentinel assigned to deactivated dimensions.

**Robustness parameters.** `n_mri_perturbations` controls the number of random perturbations sampled for the MRI computation---more perturbations yield more stable estimates of tail behavior but cost more evaluations. `mri_scale` sets the log-space perturbation radius, and `mri_weights` controls the relative importance of mean, 75th-percentile, and 95th-percentile deviations in the composite MRI score. `adversarial_tolerance` sets the convergence criterion for binary search during adversarial threshold detection.

**Pipeline control.** `start_dim` and `candidate_dims` configure the compositional test (which dimension to start from, and which to consider adding). `run_baselines` toggles the forward/backward selection baselines. `verbose` controls progress printing.

### 16.2.2 Stage Execution

The pipeline executes its six stages in a fixed order, with verbose logging at each transition. The implementation in `pipeline.py` makes the data flow explicit:

```python
# Step 1: Enumerate subsets
subset_results = enumerate_subsets(
    dim_names=dim_names_list,
    evaluate_fn=evaluate_fn,
    max_dims=max_subset_dims,
    inactive_value=inactive_value,
    n_grid=n_grid,
    n_random=n_random,
    verbose=verbose,
)

# Step 2: Pareto frontier
pareto_results = pareto_frontier(subset_results)

# Step 3: Sensitivity profiling (uses best result's params)
if subset_results:
    best_params = subset_results[0].param_values
else:
    best_params = np.ones(n_dims)

sensitivity_results = sensitivity_profile(
    params=best_params,
    dim_names=dim_names_list,
    evaluate_fn=evaluate_fn,
    inactive_value=inactive_value,
)

# Step 4: MRI
mri_result = compute_mri(
    params=best_params,
    evaluate_fn=evaluate_fn,
    n_perturbations=n_mri_perturbations,
    scale=mri_scale,
    weights=mri_weights,
)
```

Notice how `best_params`---the parameter vector from the best subset configuration---flows from stage 1 into stages 3 and 4. This is the critical data dependency. If subset enumeration finds a poor configuration, the sensitivity and robustness analyses will profile the wrong point in parameter space. The pipeline assumes that the best MAE configuration is the right one to probe; for problems where multiple Pareto-optimal configurations deserve individual robustness analysis, the user should run `compute_mri` and `sensitivity_profile` separately on each configuration of interest.

Stages 5 and 6 iterate over dimensions:

```python
# Step 5: Adversarial threshold search
adversarial_results: list[AdversarialResult] = []
for i in range(n_dims):
    adv = find_adversarial_threshold(
        params=best_params,
        dim=i,
        dim_names=dim_names_list,
        evaluate_fn=evaluate_fn,
        tolerance=adversarial_tolerance,
    )
    adversarial_results.extend(adv)

# Step 6: Compositional test
composition_result = compositional_test(
    start_dim=start_dim,
    candidate_dims=candidate_dims_list,
    dim_names=dim_names_list,
    evaluate_fn=evaluate_fn,
    inactive_value=inactive_value,
    n_grid=n_grid,
    n_random=n_random,
)
```

The adversarial search examines each dimension independently, searching for threshold values above and below the baseline at which the error exceeds the tolerance. The compositional test builds configurations incrementally, starting from a single dimension and greedily adding the dimension that most reduces MAE at each step. Together, these two stages answer complementary questions: adversarial search asks "where does this dimension break?", while compositional testing asks "in what order should dimensions be assembled?"

### 16.2.3 Evaluation Budget

Understanding the total number of evaluations consumed by a campaign is essential for budgeting computation time. The count depends on configuration:

| Stage | Evaluations (approximate) |
|:------|:--------------------------|
| Subset enumeration | $\sum_{k=1}^{K} \binom{n}{k} \times C(k)$ |
| Pareto frontier | 0 (filter only) |
| Sensitivity profile | $2n$ |
| MRI | $N_{\text{pert}}$ |
| Adversarial search | $n \times 2 \times \lceil\log_2(R)\rceil$ |
| Compositional test | $(n-1) \times C(\cdot)$ |
| Forward selection | up to $K \times n \times C(\cdot)$ |
| Backward elimination | $n \times C(\cdot)$ |

Here $C(k)$ is the optimization cost for a $k$-dimensional subset: $n_{\text{grid}}$ for $k = 1$, $n_{\text{grid}}^2$ for $k = 2$, and $n_{\text{random}}$ for $k \geq 3$. $R$ is the search range ratio for adversarial binary search, and $N_{\text{pert}}$ is `n_mri_perturbations`.

For a 5-dimensional problem with defaults ($K = 4$, $n_{\text{grid}} = 20$, $n_{\text{random}} = 5000$), the enumeration stage alone requires approximately $5 \times 20 + 10 \times 400 + 10 \times 5000 + 5 \times 5000 = 79{,}100$ evaluations. If each evaluation takes 100ms (reasonable for a small random forest), the enumeration stage takes about 2 hours. The MRI adds 300 evaluations (30 seconds), sensitivity adds 10 evaluations (1 second), and adversarial search adds roughly 100 evaluations (10 seconds). Enumeration dominates.

For a 9-dimensional problem, the evaluation count rises sharply: $\binom{9}{3} = 84$ three-dimensional subsets and $\binom{9}{4} = 126$ four-dimensional subsets, each requiring 5000 random evaluations, push the total past one million. Section 16.6 discusses strategies for managing this cost.

---

## 16.3 `StructuralFuzzReport`: Structured Output

### 16.3.1 The Report Dataclass

The pipeline returns a `StructuralFuzzReport`---a dataclass that bundles the output of all six stages into a single structured object:

```python
@dataclass
class StructuralFuzzReport:
    """Complete structural fuzzing campaign report."""

    dim_names: list[str]
    subset_results: list[SubsetResult]
    pareto_results: list[SubsetResult]
    sensitivity_results: list[SensitivityResult]
    mri_result: ModelRobustnessIndex | None
    adversarial_results: list[AdversarialResult]
    composition_result: CompositionResult | None
    forward_results: list[SubsetResult] = field(default_factory=list)
    backward_results: list[SubsetResult] = field(default_factory=list)
```

Each field holds a typed result object from the corresponding pipeline stage. The `SubsetResult` objects in `subset_results` are sorted by MAE (best first). The `pareto_results` are a subset of `subset_results` containing only the Pareto-optimal configurations. The `sensitivity_results` are sorted by importance rank. The `adversarial_results` list may contain zero, one, or two entries per dimension (one for each search direction), depending on whether thresholds were found. The `forward_results` and `backward_results` are empty lists when `run_baselines=False`.

The optional fields (`mri_result`, `composition_result`) use `None` to indicate that the corresponding stage was skipped or failed. This is the pipeline's mechanism for partial results: if the MRI computation encounters a numerical error, the report still contains valid subset, Pareto, and sensitivity results.

### 16.3.2 Navigating the Results

The `StructuralFuzzReport` is designed for programmatic access. After a campaign completes, the typical analysis workflow extracts specific results:

```python
import structural_fuzzing as sf

report = sf.run_campaign(
    dim_names=["Size", "Complexity", "Halstead", "OO", "Process"],
    evaluate_fn=evaluate_fn,
)

# Best overall configuration
best = report.subset_results[0]
print(f"Best: {best.dim_names}, MAE={best.mae:.4f}")

# Pareto-optimal tradeoffs
for p in report.pareto_results:
    print(f"  k={p.n_dims}: {p.dim_names} -> MAE={p.mae:.4f}")

# Most important dimension
top_dim = report.sensitivity_results[0]
print(f"Most important: {top_dim.dim_name} (delta={top_dim.delta_mae:.4f})")

# Robustness
if report.mri_result is not None:
    print(f"MRI = {report.mri_result.mri:.4f}")
    print(f"Worst-case MAE = {report.mri_result.worst_case_mae:.4f}")

# Tipping points
for adv in report.adversarial_results:
    print(
        f"  {adv.dim_name} ({adv.direction}): "
        f"{adv.base_value:.4f} -> {adv.threshold_value:.4f} "
        f"(ratio={adv.threshold_ratio:.2f}x, flips '{adv.target_flipped}')"
    )
```

The report object is also serializable. Because all of its fields are dataclasses with primitive or NumPy-array contents, the report can be pickled for later analysis or converted to JSON for integration with external dashboards.

### 16.3.3 The `summary` Method

For quick inspection, `StructuralFuzzReport` provides a `summary` method that delegates to the report formatting system:

```python
report = sf.run_campaign(dim_names=dim_names, evaluate_fn=evaluate_fn)
print(report.summary())
```

This produces a structured text report covering all six stages, formatted for terminal display. The implementation is a thin delegation:

```python
def summary(self) -> str:
    """Generate a text summary of the campaign results."""
    from structural_fuzzing.report import format_report
    return format_report(self)
```

The lazy import avoids a circular dependency between the pipeline and report modules---a small but important architectural detail when the report formatter needs to reference pipeline types.

---

## 16.4 Report Generation

### 16.4.1 Text Reports

The `format_report` function transforms a `StructuralFuzzReport` into a human-readable text summary. The output is organized into sections that mirror the pipeline stages:

```python
def format_report(report: StructuralFuzzReport) -> str:
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("STRUCTURAL FUZZING REPORT")
    lines.append("=" * 70)

    # Overview
    lines.append(f"\nDimensions: {len(report.dim_names)}")
    lines.append(f"Dimension names: {', '.join(report.dim_names)}")
    lines.append(f"Total configurations evaluated: {len(report.subset_results)}")

    # Best configuration
    if report.subset_results:
        best = report.subset_results[0]
        lines.append("\nBest configuration:")
        lines.append(f"  Dimensions: {', '.join(best.dim_names)} (k={best.n_dims})")
        lines.append(f"  MAE: {best.mae:.4f}")
        lines.append("  Errors:")
        for name, err in sorted(best.errors.items()):
            lines.append(f"    {name}: {err:+.4f}")
    ...
```

The report includes signed errors for each metric (positive means the model exceeds the target, negative means it falls short), the complete Pareto frontier, the sensitivity ranking with ablation deltas, MRI statistics including tail percentiles, adversarial thresholds with direction and flip information, and the compositional build order.

The text format is designed for three use cases: terminal inspection during development, inclusion in version-controlled reports (the text diffs cleanly), and automated parsing by downstream tools that can extract specific numbers using simple string matching.

### 16.4.2 LaTeX Tables

For publication-quality output, `format_latex_tables` generates ready-to-compile LaTeX table environments:

```python
def format_latex_tables(report: StructuralFuzzReport) -> str:
    lines: list[str] = []

    # Pareto frontier table
    lines.append("% Pareto Frontier")
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{Pareto-optimal configurations}")
    lines.append("\\label{tab:pareto}")
    lines.append("\\begin{tabular}{clr}")
    lines.append("\\toprule")
    lines.append("$k$ & Dimensions & MAE \\\\")
    lines.append("\\midrule")
    for pr in report.pareto_results:
        names = ", ".join(pr.dim_names)
        lines.append(f"{pr.n_dims} & {names} & {pr.mae:.4f} \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    ...
```

The function generates three tables: Pareto-optimal configurations, sensitivity ranking (with delta-MAE, MAE-with, and MAE-without columns), and MRI statistics. Each table uses `booktabs` rules (`\toprule`, `\midrule`, `\bottomrule`) and includes `\label` commands for cross-referencing. The tables are designed to be dropped directly into a LaTeX manuscript with no manual formatting.

The separation between data (the `StructuralFuzzReport` dataclass) and presentation (the `format_report` and `format_latex_tables` functions) is deliberate. A practitioner who needs a different output format---HTML, Jupyter notebook cells, a Slack message---can write a new formatter that consumes the same `StructuralFuzzReport` object without modifying the pipeline itself.

---

## 16.5 Designing Evaluation Functions

### 16.5.1 The Contract

The evaluation function is the bridge between the domain-agnostic pipeline and the domain-specific model. Its contract is simple but demands care:

```python
def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
```

**Input:** `params` is a 1D NumPy array of length $n$ (one entry per dimension). Each entry is either a positive real number (the parameter value for that dimension) or the inactive sentinel value (default $10^6$), indicating that the dimension should be excluded from the model.

**Output:** A tuple of `(mae, errors)` where `mae` is a non-negative float (mean absolute error across all target metrics) and `errors` is a dictionary mapping metric names to signed error values (predicted minus target).

Three properties are essential for correct pipeline behavior:

1. **Determinism.** Given the same `params`, the function must return the same `(mae, errors)`. Stochastic models should fix their random seed internally.
2. **Inactive handling.** When `params[i] >= inactive_value`, the evaluation must exclude dimension $i$ entirely---not merely set its weight to zero.
3. **Graceful degradation.** When all dimensions are inactive (every entry is the sentinel), the function should return large errors rather than raising an exception.

### 16.5.2 The Defect Prediction Pattern

The defect prediction example in `examples/defect_prediction/model.py` illustrates the standard pattern. The `make_evaluate_fn` factory generates a closure that captures the training data and returns a function with the correct signature:

```python
def make_evaluate_fn(
    n_samples: int = 1000,
    test_fraction: float = 0.3,
    seed: int = 42,
) -> Callable[[np.ndarray], tuple[float, dict[str, float]]]:
    X, y = generate_defect_data(n_samples=n_samples, seed=seed)
    # ... train/test split ...

    def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
        # Select features from active groups
        active_features: list[int] = []
        for i, indices in enumerate(group_indices):
            if params[i] < 1000:
                active_features.extend(indices)

        if not active_features:
            errors = {name: -val for name, val in target_values.items()}
            mae = sum(abs(v) for v in errors.values()) / len(errors)
            return mae, errors

        X_tr = X_train[:, active_features]
        X_te = X_test[:, active_features]

        rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=1)
        rf.fit(X_tr, y_train)
        y_pred = rf.predict(X_te)
        # ... compute metrics and errors ...
        return mae, errors

    return evaluate_fn
```

Several design choices are worth noting:

**Feature groups, not individual features.** The 16 raw features are organized into 5 groups (Size, Complexity, Halstead, OO, Process). Each dimension in the parameter vector controls an entire group. This is the dimension grouping pattern from Chapter 3: the pipeline operates on a manageable 5-dimensional space rather than a 16-dimensional one, with each dimension carrying semantic meaning.

**Inactive threshold.** The function checks `params[i] < 1000` rather than comparing against the full sentinel value of $10^6$. This is a pragmatic choice: it ensures that any sufficiently large parameter value deactivates the group, avoiding floating-point comparison issues with the exact sentinel.

**Fixed random state.** The `RandomForestClassifier` uses `random_state=42`, ensuring deterministic predictions. Without this, repeated evaluations with the same parameters would return different MAE values, confusing the optimization stages.

**Target-relative errors.** Each metric is compared against an explicit target value (e.g., Accuracy target of 75.0). The error dictionary contains signed deviations: positive means the model exceeds the target, negative means it falls short. This convention allows the pipeline to track *which* targets are met and which are not, rather than collapsing everything into a single pass/fail judgment.

### 16.5.3 The Geometric Economics Pattern

The geometric economics example in `examples/geometric_economics/model.py` shows a different use of the same contract. Here, the parameters are not feature group selectors but variance weights in a Mahalanobis distance computation:

```python
def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
    # Build sigma_inv from params: diag(1/params[i])
    # Large params[i] -> small weight -> dimension less important
    weights = np.where(params < 1e5, 1.0 / np.maximum(params, 1e-6), 0.0)
    sigma_inv_local = np.diag(weights)

    errors: dict[str, float] = {}
    for target in targets:
        predicted = target.predict_fn(sigma_inv_local)
        error = predicted - target.empirical
        errors[target.name] = error

    mae = sum(abs(v) for v in errors.values()) / len(errors)
    return mae, errors
```

The parameter vector has nine entries (one per ethical-economic dimension: Consequences, Rights, Fairness, Autonomy, Trust, Social Impact, Virtue/Identity, Legitimacy, Epistemic). Each entry acts as the variance of its dimension in the Mahalanobis metric: a large value means that dimension contributes little to distance computations, effectively downweighting it. Setting a parameter to $10^5$ or above zeroes the corresponding weight, deactivating the dimension entirely.

This design demonstrates the versatility of the evaluation function contract. The pipeline neither knows nor cares that the defect prediction example trains a classifier while the economics example tunes a distance metric. Both conform to the same signature, and both produce meaningful MAE and error dictionaries that the pipeline can optimize, perturb, and analyze.

### 16.5.4 Guidelines for Custom Evaluation Functions

When writing a new evaluation function for a domain not covered by the existing examples, follow these guidelines:

1. **Precompute everything possible** in the factory function (`make_evaluate_fn`). Data loading, preprocessing, and train/test splitting should happen once, not on every evaluation call. The evaluation function will be called thousands of times; a 10ms overhead per call compounds to minutes of wasted time.

2. **Choose targets carefully.** The `errors` dictionary drives the entire analysis. Each entry should correspond to a quantity that has a meaningful target value and a natural scale. Mixing a percentage (0--100) with a probability (0--1) in the same error dictionary will skew the MAE toward the larger-scale quantity.

3. **Normalize scales.** If different metrics have different natural units, consider normalizing errors as percentages of target: `error = (predicted - target) / target * 100`. This ensures that all entries in the error dictionary contribute equally to the aggregate MAE.

4. **Document the inactive semantics.** Different domains interpret "inactive" differently. For a feature-group model, inactive means "exclude these features." For a Mahalanobis model, inactive means "set this variance weight to zero." The pipeline does not enforce any particular interpretation; it only guarantees that inactive dimensions receive the sentinel value.

5. **Return finite values.** The pipeline's optimization stages use the MAE for comparison. If the evaluation function returns `inf` or `nan`, comparisons become unreliable. When a configuration is degenerate (e.g., all features excluded), return a large but finite MAE.

---

## 16.6 Pipeline Configuration: Speed vs. Thoroughness

### 16.6.1 The Cost Knobs

Three parameters dominate the computation cost of a campaign:

- **`max_subset_dims`**: Controls the combinatorial explosion. Reducing from 4 to 3 eliminates all 4-dimensional subsets.
- **`n_random`**: Controls optimization quality for 3D+ subsets. Reducing from 5000 to 1000 makes each subset 5x faster at the cost of potentially missing the optimal parameter values.
- **`n_mri_perturbations`**: Controls MRI statistical reliability. Reducing from 300 to 100 saves 200 evaluations but increases the variance of the P95 estimate.

### 16.6.2 Configuration Profiles

For different stages of a project, different tradeoffs are appropriate:

**Exploratory profile (fast).** During initial model development, the goal is a quick scan of the dimension landscape. Use `max_subset_dims=2`, `n_random=1000`, `n_mri_perturbations=100`, and `run_baselines=False`. This explores only 1D and 2D subsets with light optimization, completing in minutes for most problems.

```python
report = sf.run_campaign(
    dim_names=dim_names,
    evaluate_fn=evaluate_fn,
    max_subset_dims=2,
    n_random=1000,
    n_mri_perturbations=100,
    run_baselines=False,
)
```

**Standard profile (balanced).** For regular validation runs, the defaults are well-calibrated: `max_subset_dims=4`, `n_random=5000`, `n_mri_perturbations=300`. This explores up to 4D subsets with thorough optimization, completing in 1--4 hours for a 5--9 dimensional problem depending on evaluation cost.

```python
report = sf.run_campaign(
    dim_names=dim_names,
    evaluate_fn=evaluate_fn,
)
```

**Publication profile (thorough).** For final validation before publication, increase the sampling density: `max_subset_dims=5` (or the full dimension count), `n_random=20000`, `n_mri_perturbations=1000`, and `n_grid=50`. This provides high-confidence results at the cost of significantly longer runtime.

```python
report = sf.run_campaign(
    dim_names=dim_names,
    evaluate_fn=evaluate_fn,
    max_subset_dims=len(dim_names),
    n_random=20000,
    n_mri_perturbations=1000,
    n_grid=50,
)
```

### 16.6.3 Scaling with Dimensionality

The pipeline's cost scales differently in each stage:

- Subset enumeration scales combinatorially: $O\left(\sum_{k=1}^{K} \binom{n}{k}\right)$ subsets, each requiring $O(C(k))$ evaluations.
- Sensitivity profiling scales linearly: $O(n)$ ablation evaluations.
- MRI scales independently of dimensionality: $O(N_{\text{pert}})$ evaluations regardless of $n$.
- Adversarial search scales linearly: $O(n \log R)$ evaluations.
- Compositional testing scales quadratically in the worst case: $O(n^2 \cdot C(\cdot))$ evaluations.

For problems with $n > 10$, subset enumeration up to $k = 4$ becomes expensive. Three mitigation strategies apply:

1. **Reduce `max_subset_dims`.** Exploring only 1D and 2D subsets is often sufficient to identify the most important dimensions. Use the sensitivity profile to confirm the ranking.

2. **Use forward selection as a proxy.** Forward selection explores the same landscape as subset enumeration but follows a greedy path, evaluating $O(n \cdot K)$ subsets instead of $O(n^K)$. The `run_baselines=True` option provides this automatically.

3. **Domain-informed pruning.** If domain knowledge suggests that certain dimension combinations are irrelevant (e.g., OO metrics never matter without Size metrics), encode this as a custom enumeration rather than using the full exhaustive pipeline. The individual functions (`enumerate_subsets`, `pareto_frontier`, etc.) are available for composing custom pipelines.

---

## 16.7 Error Handling and Partial Results

### 16.7.1 Failures Within the Evaluation Function

The most common failure mode is an exception inside the evaluation function. A degenerate parameter configuration might cause a singular matrix, a division by zero, or a model that fails to converge. The pipeline does not wrap evaluation calls in blanket try/except blocks---doing so would mask bugs in the evaluation function. Instead, the evaluation function itself should handle degenerate cases:

```python
def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
    active_features = [i for i, p in enumerate(params) if p < 1000]

    if not active_features:
        # Degenerate: no features selected
        errors = {name: -val for name, val in target_values.items()}
        mae = sum(abs(v) for v in errors.values()) / len(errors)
        return mae, errors

    # Normal evaluation path
    ...
```

The key principle is that every possible parameter vector---including all-inactive, all-extreme, and mixed configurations---should produce a valid `(mae, errors)` tuple. This is a stronger requirement than typical function contracts, but it is necessary because the pipeline will exercise the entire parameter space, including corners that normal usage would never reach.

### 16.7.2 Failures Between Pipeline Stages

If a pipeline stage fails (e.g., the adversarial search raises an unhandled exception), the entire `run_campaign` call fails. This is deliberate: the pipeline makes no attempt at partial recovery because the data dependencies between stages make it difficult to reason about which downstream results are still valid.

For long-running campaigns where partial results are valuable, two approaches are available:

**Manual staging.** Call the individual functions directly, saving intermediate results:

```python
import structural_fuzzing as sf

# Stage 1
subset_results = sf.enumerate_subsets(
    dim_names=dim_names,
    evaluate_fn=evaluate_fn,
    max_dims=4,
)

# Save intermediate result
import pickle
with open("subsets.pkl", "wb") as f:
    pickle.dump(subset_results, f)

# Stage 2
pareto_results = sf.pareto_frontier(subset_results)

# Stage 3
best_params = subset_results[0].param_values
sensitivity_results = sf.sensitivity_profile(
    params=best_params,
    dim_names=dim_names,
    evaluate_fn=evaluate_fn,
)

# Continue with remaining stages...
```

This approach gives full control over checkpointing and error recovery at the cost of more code.

**Defensive evaluation functions.** Wrap the evaluation function to catch and convert exceptions:

```python
def safe_evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
    try:
        return original_evaluate_fn(params)
    except Exception:
        # Return large errors for degenerate configurations
        return 999.0, {"error": -999.0}
```

This keeps the pipeline running but may produce misleading results if exceptions occur frequently. Use with caution and always inspect the error dictionary for sentinel values in the report.

### 16.7.3 Interpreting the MRI Under Partial Information

The MRI is sensitive to the perturbation distribution. If the evaluation function returns unreliable values for certain parameter regions (e.g., near the inactive threshold), the MRI may over-estimate or under-estimate tail risk. Chapter 7 discusses this issue in detail; here the practical advice is: examine the MRI's `worst_case_mae` field. If it is unreasonably large (orders of magnitude above the baseline MAE), one or more perturbation samples likely hit a degenerate configuration, and the MRI should be recomputed with a smaller `mri_scale`.

---

## 16.8 End-to-End Examples

### 16.8.1 Defect Prediction Campaign

The defect prediction example demonstrates a complete pipeline run from data generation through report output:

```python
import structural_fuzzing as sf
from examples.defect_prediction.model import GROUP_NAMES, make_evaluate_fn

# Create evaluation function
evaluate_fn = make_evaluate_fn(n_samples=1000, seed=42)

# Run full campaign
report = sf.run_campaign(
    dim_names=GROUP_NAMES,  # ["Size", "Complexity", "Halstead", "OO", "Process"]
    evaluate_fn=evaluate_fn,
    max_subset_dims=4,
    n_mri_perturbations=300,
    verbose=True,
)

# Print text report
print(report.summary())

# Generate LaTeX tables for publication
from structural_fuzzing.report import format_latex_tables
latex = format_latex_tables(report)
with open("defect_tables.tex", "w") as f:
    f.write(latex)
```

The campaign explores all subsets of up to 4 dimensions from the 5 available (31 subsets total), identifies the Pareto frontier, profiles the sensitivity of each dimension, computes the MRI of the best configuration, searches for adversarial thresholds in each dimension, and tests the greedy dimension-addition order. The output captures everything needed for a validation report: which feature groups matter, how robust the model is, and where its tipping points lie.

### 16.8.2 Geometric Economics Campaign

The economics example operates on a higher-dimensional space (9 dimensions) and uses the evaluation function to tune Mahalanobis distance weights rather than feature-group selections:

```python
import structural_fuzzing as sf
from examples.geometric_economics.model import DIM_NAMES, make_evaluate_fn

evaluate_fn = make_evaluate_fn()

# Use exploratory profile for 9D space
report = sf.run_campaign(
    dim_names=DIM_NAMES,
    evaluate_fn=evaluate_fn,
    max_subset_dims=3,       # 9D: limit combinatorial explosion
    n_random=2000,           # Lighter optimization
    n_mri_perturbations=200,
    run_baselines=False,     # Skip baselines for speed
    verbose=True,
)

# Examine which ethical dimensions matter most
print("\nDimension importance:")
for sr in report.sensitivity_results:
    print(f"  {sr.importance_rank}. {sr.dim_name}: delta={sr.delta_mae:+.4f}")

# Check for tipping points
for adv in report.adversarial_results:
    print(
        f"  Tipping point in {adv.dim_name}: "
        f"ratio={adv.threshold_ratio:.2f}x ({adv.direction})"
    )
```

The reduced `max_subset_dims` is critical here: with 9 dimensions, exhaustive enumeration up to size 4 would require $\binom{9}{4} = 126$ four-dimensional subsets, each optimized with 2000 random samples. Limiting to 3D subsets keeps the campaign tractable while still revealing the most important dimension interactions.

### 16.8.3 Custom Pipeline with Selective Stages

For situations where the full pipeline is unnecessary or too slow, the public API (Chapter 3 introduced the module structure; the `__init__.py` exposes all components) supports composing a custom analysis:

```python
import numpy as np
import structural_fuzzing as sf

dim_names = ["Alpha", "Beta", "Gamma", "Delta"]

def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
    # Custom model evaluation
    ...
    return mae, errors

# Run only subset enumeration and Pareto analysis
subset_results = sf.enumerate_subsets(
    dim_names=dim_names,
    evaluate_fn=evaluate_fn,
    max_dims=3,
)
pareto_results = sf.pareto_frontier(subset_results)

# Run MRI on each Pareto-optimal configuration
for pr in pareto_results:
    mri = sf.compute_mri(
        params=pr.param_values,
        evaluate_fn=evaluate_fn,
        n_perturbations=500,
    )
    print(f"  k={pr.n_dims} [{', '.join(pr.dim_names)}]: "
          f"MAE={pr.mae:.4f}, MRI={mri.mri:.4f}")
```

This pattern---enumerate, filter, then probe each survivor---is more informative than the default pipeline's approach of computing the MRI only for the single best configuration. The tradeoff is that computing the MRI for every Pareto-optimal point multiplies the MRI cost by the size of the Pareto frontier.

---

## 16.9 The Pipeline as a Geometric Object

### 16.9.1 State Space of the Pipeline Itself

The pipeline has its own configuration space: the vector of all its parameters (`max_subset_dims`, `n_random`, `n_mri_perturbations`, `mri_scale`, `mri_weights`, `adversarial_tolerance`, `n_grid`). This meta-configuration lives in a space of its own, and the same geometric reasoning that the pipeline applies to models can be applied to the pipeline itself.

For instance: how sensitive is the pipeline's output to `n_random`? If increasing `n_random` from 3000 to 7000 changes the best configuration found, the pipeline was under-sampling at 3000 and the results at that setting are unreliable. If the results are stable, the extra samples are wasted computation. Running the pipeline twice with different `n_random` values and comparing the Pareto frontiers is a simple convergence check---and it is, itself, a sensitivity analysis.

### 16.9.2 Reproducibility

The pipeline does not set global random seeds. The evaluation function is responsible for its own determinism (as discussed in Section 16.5.1), and the pipeline's internal stages use deterministic algorithms where possible. Subset enumeration is exhaustive (no randomness). Pareto extraction is a deterministic filter. Sensitivity profiling evaluates fixed parameter configurations. Only the MRI stage introduces randomness (random perturbation sampling), and its random seed can be controlled through the evaluation function's internal state.

For bit-reproducible results across runs, ensure that:

1. The evaluation function uses a fixed random seed.
2. The underlying model (e.g., `RandomForestClassifier(random_state=42)`) uses a fixed random seed.
3. The NumPy random generator used for MRI perturbations is seeded consistently.

### 16.9.3 Composition with External Tools

The pipeline produces structured data; what happens to that data next is outside the pipeline's scope but worth considering as a design question. Common downstream integrations include:

- **Visualization.** Plotting the Pareto frontier (MAE vs. number of dimensions), the sensitivity bar chart, and the MRI perturbation distribution. The `StructuralFuzzReport` contains all the data needed for these plots; the pipeline does not generate them because plotting libraries are a matter of preference.

- **Regression testing.** Storing the `StructuralFuzzReport` from each campaign and comparing it against previous runs to detect changes in the Pareto frontier, shifts in the sensitivity ranking, or deterioration of the MRI.

- **Hyperparameter optimization.** Using the pipeline's output as the objective for a higher-level optimizer that searches over model hyperparameters or data preprocessing choices.

Each of these integrations treats the pipeline's output as a first-class object rather than a log file to be parsed---the benefit of structured output over printf-style reporting.

---

## 16.10 Looking Ahead

This chapter has treated the pipeline as a sequential, single-machine process. For the problems considered in this book---5 to 15 dimensions, evaluation functions that run in milliseconds to seconds---this is sufficient. But two pressures push toward more sophisticated execution models.

First, **scaling to higher dimensions** (Chapter 17) introduces evaluation budgets that exceed what sequential execution can deliver in reasonable time. Distributing subset evaluations across multiple cores or machines, caching evaluation results to avoid redundant computation, and using surrogate models to approximate expensive evaluations are all extensions that preserve the pipeline's logical structure while changing its execution strategy.

Second, **deploying geometric validation in production** (Chapter 18) requires integrating the pipeline into continuous integration systems, monitoring dashboards, and alerting infrastructure. The pipeline's structured output---the `StructuralFuzzReport`---provides the foundation for these integrations, but the operational concerns (scheduling, retry policies, result storage, alert thresholds) are distinct from the analytical concerns developed in this chapter.

Chapter 17 takes up the scaling challenge, developing methods for efficient exploration of high-dimensional spaces where exhaustive enumeration is infeasible and the geometric tools from Parts II and III must be adapted to operate under strict computational budgets.

---

## Summary

The geometric pipeline composes six analysis stages---subset enumeration, Pareto frontier extraction, sensitivity profiling, MRI computation, adversarial threshold search, and compositional testing---into a single `run_campaign` call. The pipeline's power comes from three design choices:

1. **A unified evaluation contract.** The `evaluate_fn` callback decouples the domain-specific model from the domain-agnostic analysis, enabling the same pipeline to validate a random forest classifier and a game-theoretic distance metric.

2. **Structured output.** The `StructuralFuzzReport` dataclass captures all results in a typed, navigable object that supports programmatic analysis, text reporting, and LaTeX table generation without loss of information.

3. **Configurable thoroughness.** The pipeline's parameters (`max_subset_dims`, `n_random`, `n_mri_perturbations`) provide explicit control over the tradeoff between computation time and result quality, enabling exploratory runs during development and publication-quality analyses for final validation.

The pipeline is not the final word on geometric validation---it is a starting point. The individual components are independently usable, the report format is extensible, and the evaluation function contract is simple enough to implement for any parameterized model. What the pipeline provides is a disciplined default: a sequence of analyses that, taken together, reveal the multi-dimensional structure that scalar metrics systematically hide.
