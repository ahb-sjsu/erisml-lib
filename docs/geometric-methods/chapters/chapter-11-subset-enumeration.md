# Chapter 11: The Subset Enumeration Pattern

> *"The art of being wise is the art of knowing what to overlook."*
> --- William James, *The Principles of Psychology* (1890)

A model with $n$ parameter dimensions admits $2^n - 1$ non-empty subsets of those dimensions. Each subset defines a different structural question: *what happens when the model uses only these inputs?* For $n = 5$, there are 31 subsets---tractable. For $n = 10$, there are 1,023. For $n = 20$, over a million. The exponential growth is a combinatorial fact, and no algorithm can avoid it in general. But the equally important fact---the one that makes the subset enumeration pattern practical---is that most real problems have moderate effective dimensionality. Feature groups, not individual features, are the natural unit of structural analysis, and the number of meaningful groups rarely exceeds ten.

This chapter develops the subset enumeration pattern: the systematic exploration of all dimension combinations up to a specified cardinality. We begin with the combinatorial landscape and the conditions under which brute-force enumeration is feasible. We then examine the `optimize_subset` algorithm in detail, including its log-space parameterization and sentinel-value encoding for inactive dimensions. The `SubsetResult` data structure captures the output of each optimization in a typed, composable form. The `enumerate_subsets` function orchestrates the full sweep. We close with practical heuristics---cardinality limits, early stopping---and a worked example from software defect prediction that reveals which feature groups genuinely drive predictive performance.

The pattern connects backward to the motivating example of Chapter 1, where subset enumeration first appeared as Step 1 of the geometric validation pipeline, and forward to Chapter 8, where Pareto frontier analysis operates over the space of `SubsetResult` objects to identify non-dominated tradeoffs between model complexity and predictive quality.

---

## 11.1 The Combinatorial Explosion

### 11.1.1 Counting Subsets

Given a set of $n$ dimensions, the number of subsets of size exactly $k$ is:

$$\binom{n}{k} = \frac{n!}{k!(n-k)!}$$

The total number of subsets of size 1 through $k_{\max}$ is:

$$N(n, k_{\max}) = \sum_{k=1}^{k_{\max}} \binom{n}{k}$$

For the defect prediction example introduced in Chapter 1, $n = 5$ feature groups (Size, Complexity, Halstead, OO, Process). The subset counts are:

| $k$ | $\binom{5}{k}$ | Cumulative |
|:---:|:---:|:---:|
| 1 | 5 | 5 |
| 2 | 10 | 15 |
| 3 | 10 | 25 |
| 4 | 5 | 30 |
| 5 | 1 | 31 |

Thirty-one subsets is a small number. Even with an expensive evaluation function---say, training a random forest classifier---the full enumeration completes in seconds. This is the regime where brute-force subset testing is not merely acceptable but *optimal*: it guarantees that no combination is overlooked, eliminates the need for heuristic search strategies, and produces a complete map of the structural landscape.

### 11.1.2 The Scaling Boundary

The picture changes with $n$. The following table shows $N(n, k_{\max})$ for representative values:

| $n$ | $k_{\max} = 2$ | $k_{\max} = 3$ | $k_{\max} = 4$ | $k_{\max} = n$ |
|:---:|:---:|:---:|:---:|:---:|
| 5 | 15 | 25 | 30 | 31 |
| 8 | 36 | 92 | 162 | 255 |
| 10 | 55 | 175 | 385 | 1,023 |
| 15 | 120 | 575 | 1,940 | 32,767 |
| 20 | 210 | 1,350 | 6,195 | 1,048,575 |

Two observations. First, the full enumeration $k_{\max} = n$ is practical only for $n \leq 15$ or so, depending on evaluation cost. Second, limiting $k_{\max}$ to 3 or 4 keeps the count manageable even for $n = 20$. This is the key insight behind the `max_dims` parameter in the `enumerate_subsets` function: by bounding the maximum subset cardinality, we trade completeness for tractability, and the trade is almost always favorable because the marginal information gained from subsets of size $k > 4$ is typically small.

Why? Because the structural questions of interest are usually comparative: *does adding dimension $d$ to an existing subset improve performance?* The answer to this question is already captured by subsets of size $k$ and $k+1$ for small $k$. If Complexity alone achieves MAE 3.8 and {Complexity, Process} achieves MAE 2.1, then we know the marginal value of Process in the presence of Complexity. Extending to {Complexity, Process, Size} at MAE 1.7 tells us the marginal value of Size given the other two. By $k = 4$, the marginal contributions are usually small and the structural picture is clear.

### 11.1.3 Why Brute Force Beats Heuristics

The alternative to brute-force enumeration is heuristic search: forward selection, backward elimination, or stochastic methods like genetic algorithms. These approaches are necessary when $n$ is large, but they carry well-documented risks:

1. **Forward selection** adds dimensions greedily, choosing the single best addition at each step. It cannot recover from a poor early choice: if the best 2D subset is {Complexity, Process} but forward selection started with Size (because Size is the best 1D choice), it may converge to a suboptimal path.

2. **Backward elimination** starts with all dimensions and removes the least important one at each step. It cannot detect synergies between dimensions that are individually weak but jointly strong.

3. **Both methods produce a single path** through the lattice of subsets, not a map of the full landscape. They answer "what is a good subset?" but not "what do all subsets look like?"---and the latter question is what structural fuzzing needs.

When $n$ is small enough for brute force, there is no reason to accept these limitations. The `enumerate_subsets` function exists precisely for this regime: it tests every subset, sorts the results by performance, and returns the complete landscape for downstream analysis.

---

## 11.2 The `optimize_subset` Algorithm

The core of subset enumeration is the `optimize_subset` function, which takes a set of active dimensions and finds the best parameter values for those dimensions while holding all inactive dimensions at a sentinel value. The algorithm makes three design decisions that merit detailed examination: log-space parameterization, sentinel values for inactive dimensions, and adaptive search strategy.

### 11.2.1 Log-Space Parameterization

Parameters that represent scales, weights, or regularization strengths typically span several orders of magnitude. A parameter that might reasonably take any value from 0.01 to 100 has a range ratio of 10,000:1. A uniform grid over this range would place 99% of its points above 1.0, leaving the sub-unit region---often the most interesting---severely undersampled.

The solution is to parameterize in log-space. The `optimize_subset` function generates grid values as:

```python
grid_values = np.logspace(np.log10(0.01), np.log10(100), n_grid)
```

This produces `n_grid` points uniformly spaced on a logarithmic scale between $10^{-2}$ and $10^2$. With `n_grid = 20`, the values are approximately:

$$0.01, \; 0.017, \; 0.029, \; 0.050, \; 0.085, \; \ldots, \; 11.7, \; 20.0, \; 34.1, \; 58.5, \; 100.0$$

Each adjacent pair of grid points differs by a constant multiplicative factor of $(10^4)^{1/19} \approx 1.66$. This provides uniform resolution in the sense that matters: a change from 0.01 to 0.017 is as significant (in relative terms) as a change from 58.5 to 100.0.

For random search in higher dimensions, the same principle applies:

```python
log_low, log_high = np.log10(0.01), np.log10(100)
log_vals = rng.uniform(log_low, log_high, n_active)
for i, dim in enumerate(active_dims):
    params[dim] = 10 ** log_vals[i]
```

The random samples are drawn uniformly in $[\log_{10}(0.01), \log_{10}(100)] = [-2, 2]$ and then exponentiated, producing a distribution that is uniform in log-space. This is equivalent to drawing from a log-uniform distribution over $[0.01, 100]$, which is the maximum-entropy prior for a scale parameter whose order of magnitude is unknown.

### 11.2.2 Sentinel Values for Inactive Dimensions

When only a subset of dimensions is active, the remaining dimensions must be assigned values that effectively "turn them off." The `optimize_subset` function uses a sentinel value of $10^6$ (the `inactive_value` parameter):

```python
params = np.full(n_all, inactive_value)
params[active_dims[0]] = v
```

The parameter vector always has length $n$ (the total number of dimensions), but only the entries corresponding to active dimensions receive optimized values. All others are set to $10^6$.

This sentinel-value convention has several advantages over alternatives like maintaining variable-length parameter vectors or using a boolean mask:

1. **Fixed-size vectors.** The evaluation function always receives an array of the same length, regardless of which dimensions are active. This simplifies the function's interface and eliminates shape-mismatch bugs.

2. **Interpretability.** The sentinel value $10^6$ is orders of magnitude larger than any value in the search range $[0.01, 100]$. Any evaluation function that uses the parameter as a weight, scale factor, or regularization coefficient will naturally treat $10^6$ as "inactive" without special-case logic.

3. **Composability.** The full parameter vector, including sentinel values, is stored in the `SubsetResult`. This means any downstream operation---Pareto analysis, sensitivity profiling, adversarial search---can re-evaluate the configuration by passing the stored vector directly to the evaluation function. No reconstruction logic is needed.

The defect prediction example illustrates the convention. The evaluation function checks each group's parameter against a threshold:

```python
for i, indices in enumerate(group_indices):
    if params[i] < 1000:
        active_features.extend(indices)
```

A parameter value of $10^6$ is well above the threshold of 1000, so the corresponding feature group is excluded. A parameter value in $[0.01, 100]$ is well below the threshold, so the group is included. The gap between the search range and the threshold provides a wide margin that prevents numerical edge cases.

### 11.2.3 Adaptive Search Strategy

The `optimize_subset` function uses three different search strategies depending on the number of active dimensions:

**1D subsets: grid search.** For a single active dimension, the algorithm evaluates all `n_grid` points on the log-spaced grid:

```python
if n_active == 1:
    for v in grid_values:
        params = np.full(n_all, inactive_value)
        params[active_dims[0]] = v
        mae, errors = evaluate_fn(params)
        if mae < best_mae:
            best_mae = mae
            best_params = params.copy()
            best_errors = errors.copy()
```

With `n_grid = 20`, this requires 20 evaluations. The grid is exhaustive within its resolution, guaranteeing that the optimal value (to within a factor of 1.66) is found.

**2D subsets: full grid search.** For two active dimensions, the algorithm evaluates all pairs on the grid:

```python
elif n_active == 2:
    for v0, v1 in itertools.product(grid_values, grid_values):
        params = np.full(n_all, inactive_value)
        params[active_dims[0]] = v0
        params[active_dims[1]] = v1
        mae, errors = evaluate_fn(params)
```

With `n_grid = 20`, this requires $20^2 = 400$ evaluations. The cost is quadratic in `n_grid` but still modest for typical evaluation functions. The full grid ensures that all pairwise interactions between the two dimensions are captured---an important property, since interactions are precisely what subset enumeration is designed to detect.

**3D+ subsets: random search in log-space.** For three or more active dimensions, the grid approach becomes impractical ($20^3 = 8000$, $20^4 = 160000$). The algorithm switches to random search:

```python
else:
    rng = np.random.default_rng(42)
    log_low, log_high = np.log10(0.01), np.log10(100)
    for _ in range(n_random):
        params = np.full(n_all, inactive_value)
        log_vals = rng.uniform(log_low, log_high, n_active)
        for i, dim in enumerate(active_dims):
            params[dim] = 10 ** log_vals[i]
        mae, errors = evaluate_fn(params)
```

With `n_random = 5000`, this samples 5000 random points in the log-space hypercube. Random search is surprisingly effective in low dimensions: in a $k$-dimensional space, the probability that at least one sample falls within a hypercube of side length $\epsilon$ (in log-space) is approximately $1 - (1 - \epsilon^k)^{n}$, which exceeds 0.95 for $\epsilon = 0.3$ and $n = 5000$ when $k \leq 4$.

The fixed seed (`rng = np.random.default_rng(42)`) ensures reproducibility: the same subset always produces the same search trajectory and the same result.

---

## 11.3 `SubsetResult` as a Typed Data Structure

Each call to `optimize_subset` returns a `SubsetResult` object. This is not merely a container for the output; it is a typed data structure designed for downstream composition.

```python
@dataclass
class SubsetResult:
    """Result of optimizing a single parameter subset."""

    dims: tuple[int, ...]
    dim_names: tuple[str, ...]
    n_dims: int
    param_values: np.ndarray
    mae: float
    errors: dict[str, float]
    pareto_optimal: bool = False
```

The fields serve distinct roles:

- **`dims`** and **`dim_names`**: the active dimensions, both by index and by name. The index form enables array operations; the name form enables human-readable output. The tuple type ensures immutability---a `SubsetResult` cannot be silently modified after creation.

- **`n_dims`**: the cardinality of the active subset. Storing this explicitly (rather than computing `len(dims)` each time) supports efficient sorting and filtering: "give me all results with exactly 2 active dimensions" is a constant-time field access, not a linear scan.

- **`param_values`**: the full parameter vector, including sentinel values for inactive dimensions. This is the vector that, when passed to the evaluation function, reproduces the recorded MAE. Storing the complete vector rather than just the active values eliminates the need for reconstruction logic and makes re-evaluation trivial.

- **`mae`**: the mean absolute error achieved by this configuration. This is the primary sort key for comparing configurations.

- **`errors`**: a dictionary of per-metric errors. For the defect prediction example, this might contain `{"Accuracy": 3.2, "Precision": -1.5, "Recall": 5.1, "F1": 2.8, "AUC": -0.3}`. The dictionary preserves the full multi-dimensional evaluation---exactly the information that, as Chapter 1 argued, scalar summaries destroy.

- **`pareto_optimal`**: a boolean flag, initially `False`, set to `True` by the Pareto frontier analysis (Chapter 8) for configurations that are non-dominated in the (n_dims, MAE) plane. This flag allows downstream code to filter for Pareto-optimal results without re-computing the frontier.

The `__repr__` method provides a concise summary:

```python
def __repr__(self) -> str:
    names = ", ".join(self.dim_names)
    return f"SubsetResult(dims=[{names}], n_dims={self.n_dims}, mae={self.mae:.4f})"
```

A typical output might be:

```
SubsetResult(dims=[Complexity, Process], n_dims=2, mae=2.1034)
```

This design follows the principle stated in Section 1.2.2: state vectors are immutable, dimensions are named not numbered, and the full multi-dimensional evaluation is preserved.

---

## 11.4 The `enumerate_subsets` Function

With `optimize_subset` handling individual subsets and `SubsetResult` capturing the output, the `enumerate_subsets` function orchestrates the full sweep:

```python
def enumerate_subsets(
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    max_dims: int = 4,
    inactive_value: float = 1e6,
    n_grid: int = 20,
    n_random: int = 5000,
    verbose: bool = False,
) -> list[SubsetResult]:
```

The function iterates over all subset sizes from 1 to `max_dims`, generates all combinations at each size using `itertools.combinations`, and calls `optimize_subset` for each:

```python
for k in range(1, min(max_dims, n_all) + 1):
    combos = list(itertools.combinations(range(n_all), k))
    if verbose:
        print(f"  Enumerating {len(combos)} subsets of size {k}...")
    for combo in combos:
        result = optimize_subset(
            active_dims=combo,
            all_dim_names=dim_names,
            evaluate_fn=evaluate_fn,
            inactive_value=inactive_value,
            n_grid=n_grid,
            n_random=n_random,
        )
        results.append(result)
```

The results are sorted by MAE in ascending order before return:

```python
results.sort(key=lambda r: r.mae)
return results
```

This means `results[0]` is always the best configuration found, regardless of how many dimensions it uses. The caller can then apply additional filtering (e.g., "best result with at most 2 dimensions") or pass the full list to Pareto frontier analysis.

### 11.4.1 The Role of `max_dims`

The `max_dims` parameter is the primary lever for controlling computational cost. Its effect on the total number of evaluations is:

$$E(n, k_{\max}) = \sum_{k=1}^{k_{\max}} \binom{n}{k} \cdot C(k)$$

where $C(k)$ is the per-subset evaluation count: $C(1) = n_{\text{grid}}$, $C(2) = n_{\text{grid}}^2$, $C(k \geq 3) = n_{\text{random}}$. For the defect prediction example with $n = 5$, $n_{\text{grid}} = 20$, $n_{\text{random}} = 5000$:

| $k$ | Subsets | Evals per subset | Total evals |
|:---:|:---:|:---:|:---:|
| 1 | 5 | 20 | 100 |
| 2 | 10 | 400 | 4,000 |
| 3 | 10 | 5,000 | 50,000 |
| 4 | 5 | 5,000 | 25,000 |

With `max_dims = 4`, the total is 79,100 evaluations. With `max_dims = 2`, it drops to 4,100. The choice depends on the cost of a single evaluation: if `evaluate_fn` takes 1 millisecond (as in the defect prediction example with pre-trained models), the full sweep completes in under 80 seconds. If it takes 1 second, `max_dims = 2` might be the practical limit.

### 11.4.2 Integration with the Pipeline

The `enumerate_subsets` function is the first step of the full structural fuzzing campaign, orchestrated by the `run_campaign` function in `pipeline.py`:

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
```

The returned list of `SubsetResult` objects flows into every subsequent stage. The Pareto frontier analysis (Step 2) receives the subset results and identifies non-dominated configurations. The sensitivity profiling (Step 3) uses the best configuration's parameter vector as its baseline. The MRI computation (Step 4) perturbs that same baseline. The adversarial search (Step 5) probes its boundaries.

This architecture embodies a principle worth stating explicitly: **subset enumeration produces the raw data; all other analyses are views over that data.** The `SubsetResult` list is the foundational artifact of a structural fuzzing campaign, and its completeness determines the quality of every downstream analysis.

The `StructuralFuzzReport` dataclass makes this relationship concrete:

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

The `subset_results` field stores the complete enumeration. The `pareto_results` field stores the subset of those results that are Pareto-optimal. Both use the same `SubsetResult` type, differing only in the `pareto_optimal` flag.

---

## 11.5 Practical Heuristics

### 11.5.1 Choosing `max_dims`

The choice of `max_dims` involves a tradeoff between coverage and cost. Three guidelines:

**Rule of thumb: $k_{\max} = \min(4, n)$.** For most problems, subsets of size 4 or smaller capture the dominant structural patterns. The marginal information from 5-way interactions is rarely worth the combinatorial cost. The default `max_dims = 4` in `enumerate_subsets` reflects this heuristic.

**Cost-calibrated choice.** If the evaluation function has a known per-call cost $t$, compute the total time $T = E(n, k_{\max}) \cdot t$ for candidate values of $k_{\max}$ and choose the largest $k_{\max}$ that fits within the time budget. For the defect prediction example with $t \approx 1$ ms, even $k_{\max} = 5$ completes in under two minutes.

**Diminishing returns.** After running with a given $k_{\max}$, inspect the results. If the best configuration of size $k_{\max}$ is not substantially better than the best of size $k_{\max} - 1$, there is little reason to increase $k_{\max}$. The Pareto frontier provides a natural diagnostic: if the frontier flattens (the MAE improvement from adding one more dimension is less than some threshold $\delta$), the enumeration has reached the point of diminishing returns.

### 11.5.2 Early Stopping

The current `enumerate_subsets` implementation tests all subsets at each size before moving to the next. An alternative is early stopping: if no subset of size $k$ improves on the best result of size $k - 1$ by more than $\delta$, skip sizes $k+1, k+2, \ldots$

This heuristic is not implemented in the framework's core because it sacrifices completeness: a subset of size $k+1$ might improve dramatically over anything at size $k$ due to a synergy that only emerges when three or more dimensions interact. Such cases are rare but consequential, and the whole point of brute-force enumeration is to catch them. In practice, early stopping is best reserved for exploratory runs where speed matters more than thoroughness.

### 11.5.3 Tuning `n_grid` and `n_random`

The `n_grid` parameter controls the resolution of 1D and 2D searches. Increasing it from 20 to 50 improves resolution (the multiplicative step drops from 1.66 to 1.19) but increases the 2D cost from 400 to 2,500 evaluations per subset. For smooth evaluation functions, `n_grid = 20` is usually sufficient. For functions with narrow optima or sharp transitions, `n_grid = 50` or higher may be warranted.

The `n_random` parameter controls the coverage of 3D+ searches. The expected coverage of a random search depends on the effective dimensionality of the loss landscape. If the loss depends strongly on only one of the $k$ active dimensions, then 5,000 random samples provide excellent coverage of that dimension even in a $k$-dimensional space. If the loss depends on all $k$ dimensions with comparable sensitivity, coverage scales as $n_{\text{random}}^{1/k}$---about 17 effective grid points per dimension for $k = 3$ and $n_{\text{random}} = 5000$, or about 8 for $k = 4$. These numbers are adequate for identifying the approximate optimum but not for precise characterization. For the latter, a targeted refinement step (not part of the core framework) can be applied to the most promising configurations.

### 11.5.4 The Zero-Dimensional Baseline

The `optimize_subset` function handles the edge case of zero active dimensions:

```python
if n_active == 0:
    params = np.full(n_all, inactive_value)
    mae, errors = evaluate_fn(params)
    return SubsetResult(
        dims=(),
        dim_names=(),
        n_dims=0,
        param_values=params.copy(),
        mae=mae,
        errors=errors,
    )
```

This baseline measures the evaluation function's output when *all* dimensions are inactive---the "null model." While `enumerate_subsets` does not include this case in its loop (it starts at $k = 1$), calling `optimize_subset` with an empty `active_dims` tuple produces a valid `SubsetResult` that can be used as a reference point. The improvement of any subset over the null model quantifies the absolute contribution of those dimensions, as opposed to the marginal contribution measured by comparing subsets of different sizes.

---

## 11.6 Worked Example: Defect Prediction

The defect prediction example, introduced in Chapter 1 and implemented in `examples/defect_prediction/model.py`, provides a concrete demonstration of the subset enumeration pattern. The model predicts whether a software module contains defects based on 16 software metrics organized into five feature groups.

### 11.6.1 Feature Groups as Dimensions

The `FEATURE_GROUPS` dictionary defines the mapping from feature group names to feature indices:

```python
FEATURE_GROUPS = {
    "Size": [0, 1, 2],
    "Complexity": [3, 4, 5],
    "Halstead": [6, 7, 8, 9],
    "OO": [10, 11, 12],
    "Process": [13, 14, 15],
}
GROUP_NAMES = list(FEATURE_GROUPS.keys())
```

Each group aggregates related software metrics:

- **Size**: lines of code (LOC), source lines (SLOC), blank lines---raw measures of module size.
- **Complexity**: cyclomatic complexity, essential complexity, design complexity---structural measures of control flow.
- **Halstead**: volume, difficulty, effort, time estimate---vocabulary-based measures derived from operator and operand counts.
- **OO**: coupling between objects, cohesion, inheritance depth---object-oriented design metrics.
- **Process**: revisions, distinct authors, code churn---measures of development activity.

The choice of five groups rather than sixteen individual features is itself a modeling decision. It reduces the number of subsets from $2^{16} - 1 = 65{,}535$ to $2^5 - 1 = 31$, making brute-force enumeration trivially feasible. More importantly, it aligns the structural analysis with the conceptual structure of the domain: practitioners think in terms of "size metrics" and "complexity metrics," not individual features. The subset enumeration pattern operates at the level of these semantic groups.

### 11.6.2 The Evaluation Function

The `make_evaluate_fn` function constructs an evaluation function compatible with the structural fuzzing framework:

```python
def make_evaluate_fn(
    n_samples: int = 1000,
    test_fraction: float = 0.3,
    seed: int = 42,
) -> Callable[[np.ndarray], tuple[float, dict[str, float]]]:
```

The returned callable takes a parameter vector of length 5 (one entry per feature group). If `params[i] < 1000`, the features in group $i$ are included in the model; otherwise, the group is excluded. This binary inclusion semantics means that the *value* of `params[i]` (when below 1000) does not affect the model---only its presence above or below the threshold matters. The actual feature scaling is handled internally by the random forest's invariance to monotone feature transformations.

The function trains a `RandomForestClassifier` on the active features and computes five metrics against target values:

```python
target_values = {
    "Accuracy": 75.0,
    "Precision": 70.0,
    "Recall": 65.0,
    "F1": 67.0,
    "AUC": 80.0,
}
```

The errors are signed differences (predicted minus target), and the MAE is the mean of their absolute values. A configuration with MAE 0 would match all targets exactly. The multi-dimensional error vector preserves the direction of deviation---overperformance versus underperformance on each metric---while the MAE provides a scalar summary for sorting.

### 11.6.3 What the Enumeration Reveals

Running `enumerate_subsets` with `max_dims = 4` on the defect prediction example produces 30 `SubsetResult` objects (all subsets of sizes 1 through 4 from the five groups). The results, sorted by MAE, typically exhibit the following pattern:

**Single-dimension results ($k = 1$).** The five single-group models reveal the standalone predictive power of each group:

| Group | MAE | Interpretation |
|-------|:---:|----------------|
| Complexity | ~3.8 | Strongest single predictor |
| Process | ~4.2 | Second strongest |
| Size | ~5.1 | Moderate |
| Halstead | ~5.4 | Weak (correlated with Size) |
| OO | ~8.9 | Near-noise |

Complexity alone is the best single predictor, confirming the domain knowledge that cyclomatic complexity is the primary driver of defect-proneness. OO metrics contribute almost nothing in isolation---a finding consistent with the data generation process, where OO features are pure noise.

**Two-dimension results ($k = 2$).** The ten pairwise combinations reveal interaction effects:

| Pair | MAE | Delta from best singleton |
|------|:---:|:---:|
| {Complexity, Process} | ~2.1 | -1.7 |
| {Complexity, Size} | ~2.9 | -0.9 |
| {Complexity, Halstead} | ~3.1 | -0.7 |
| {Process, Size} | ~3.4 | N/A |
| ... | ... | ... |

The {Complexity, Process} pair is substantially better than any singleton, demonstrating a *synergy*: the structural (complexity) and temporal (process) views of the code are complementary. The framework reveals this synergy because it tests all pairs exhaustively; forward selection, starting from Complexity, would find {Complexity, Process} only if Process happened to be the best addition---which it is, but that outcome is not guaranteed in general.

**Three- and four-dimension results ($k = 3, 4$).** Adding Size to {Complexity, Process} reduces MAE to approximately 1.7. Adding Halstead or OO provides marginal further improvement. The pattern is one of diminishing returns: two dimensions capture most of the predictive structure, a third adds a meaningful increment, and the fourth and fifth add little.

### 11.6.4 Connecting to the Pareto Frontier

The 30 `SubsetResult` objects, when plotted in the $(k, \text{MAE})$ plane, define a point cloud from which the Pareto frontier is extracted (Chapter 8). The frontier typically contains four points:

$$\{(\text{Complexity})\}, \; \{(\text{Complexity, Process})\}, \; \{(\text{Complexity, Process, Size})\}, \; \{(\text{all})\}$$

Each Pareto-optimal point represents the best achievable MAE at its cardinality. The frontier makes the complexity-performance tradeoff explicit: the practitioner can see that going from 2 to 3 dimensions buys a 0.4-point MAE improvement, while going from 3 to 5 dimensions buys only 0.2 points. Whether the additional features are worth the added model complexity is a domain decision, but the subset enumeration pattern provides the quantitative basis for making it.

### 11.6.5 The Ground Truth Test

The synthetic data in `model.py` has a known ground truth. The defect probability is generated as:

```python
logit = (
    -3
    + 0.1 * np.log1p(cyclomatic)
    + 0.15 * np.log1p(essential)
    + 0.05 * np.log1p(design)
    + 0.12 * np.log1p(revisions)
    + 0.1 * np.log1p(authors)
    + 0.08 * np.log1p(churn / 100)
    + 0.03 * np.log1p(loc / 1000)
    + rng.normal(0, 0.5, n_samples)
)
```

The true predictors are Complexity (coefficients 0.1, 0.15, 0.05), Process (0.12, 0.1, 0.08), and Size (0.03). Halstead is correlated with Size but has no direct effect. OO is pure noise.

The subset enumeration correctly recovers this structure: Complexity and Process are the dominant groups, Size contributes marginally, Halstead's apparent contribution comes from its correlation with Size, and OO adds nothing. This ground-truth validation confirms that the brute-force enumeration pattern, despite its simplicity, reliably identifies the true structural dependencies in the data.

---

## 11.7 Computational Considerations

### 11.7.1 Parallelism

The `enumerate_subsets` loop is embarrassingly parallel: each subset can be optimized independently. The current implementation is sequential for simplicity, but parallelization is straightforward---each call to `optimize_subset` is a pure function with no shared state (beyond the evaluation function, which must be thread-safe).

For the defect prediction example, parallelizing over subsets would reduce wall-clock time roughly linearly with the number of available cores, since the per-subset computation (training a random forest on ~700 samples) is dominated by CPU time rather than I/O.

### 11.7.2 Memory

Each `SubsetResult` stores a parameter vector of length $n$ (a NumPy array), an error dictionary, and metadata. For $n = 5$, this is negligible. For $n = 100$ with $N(100, 3) = 166{,}750$ subsets, the memory footprint is approximately $166{,}750 \times (100 \times 8 + \text{overhead}) \approx 200$ MB---large but manageable.

The more significant memory concern is the evaluation function itself. If `evaluate_fn` loads a large model or dataset into memory, the cost is paid once (at construction time, via `make_evaluate_fn`) and amortized over all evaluations.

### 11.7.3 Reproducibility

The `optimize_subset` function uses a fixed random seed (`rng = np.random.default_rng(42)`) for the 3D+ random search. This ensures that the same subset always produces the same result, which is essential for reproducibility. However, it also means that the random samples are the same for every subset of the same size. This is a deliberate design choice: it eliminates one source of variability (different random seeds for different subsets) and makes it possible to attribute performance differences between subsets entirely to the choice of active dimensions.

---

## 11.8 Relationship to Other Patterns

### 11.8.1 Subset Enumeration vs. Forward/Backward Selection

The `run_campaign` function in `pipeline.py` runs both brute-force enumeration and the greedy baselines (forward selection and backward elimination), storing the results in the `forward_results` and `backward_results` fields of `StructuralFuzzReport`. This design enables direct comparison:

- **Subset enumeration** provides the complete landscape: every subset tested, every MAE recorded.
- **Forward selection** provides a single path from one dimension to `max_dims` dimensions, greedy at each step.
- **Backward elimination** provides a single path from all dimensions down, removing the least valuable at each step.

When the three methods agree---they select the same dimensions and rank them similarly---the result is robust. When they disagree---as they will when dimensions interact non-additively---the brute-force enumeration is the ground truth, and the discrepancy reveals the limitations of the greedy methods.

### 11.8.2 Subset Enumeration and Sensitivity Analysis

Sensitivity analysis (asking "how much does the objective change when I perturb one dimension?") is a local probe: it examines the neighborhood of a single configuration. Subset enumeration is a global survey: it examines the entire lattice of dimension combinations. The two are complementary. Sensitivity analysis reveals *which dimensions are important near the current optimum*; subset enumeration reveals *which dimension combinations define the best optima*.

In the pipeline, sensitivity analysis is applied to the best configuration found by subset enumeration. The combination provides both global structure (which subsets are best overall) and local structure (which dimensions are most influential at the optimum).

### 11.8.3 Subset Enumeration and Pareto Analysis

As discussed in Section 11.6.4, the output of `enumerate_subsets`---a list of `SubsetResult` objects---is the natural input to Pareto frontier analysis. The Pareto frontier operates over the $(k, \text{MAE})$ plane, identifying configurations that are non-dominated: no other configuration has both fewer dimensions *and* lower MAE.

The Pareto analysis (Chapter 8) does not depend on the enumeration being exhaustive. It produces a valid frontier from any set of results. But the frontier is most informative when the input is complete: if a subset was not tested, its potential position on the frontier is unknown, and the frontier may be suboptimal. This is another argument for brute-force enumeration when it is feasible: it guarantees that the Pareto frontier is exact.

---

## 11.9 Summary

The subset enumeration pattern is the simplest and most powerful tool in the structural fuzzing framework. It works by exhaustion: test every combination, record the result, sort by performance. Its effectiveness rests on three conditions that hold in practice for a wide range of problems:

1. **Moderate effective dimensionality.** Real models have few meaningful dimension groups (typically 3--10), even when the raw feature count is high.

2. **Cheap evaluation.** The evaluation function is fast enough to call thousands or tens of thousands of times. This includes models with pre-computed datasets, cached computations, or inherently fast inference.

3. **Structural interest.** The practitioner cares not just about the best configuration but about the *structure* of the configuration space: which dimensions matter, which are redundant, which interact.

When these conditions hold, `enumerate_subsets` with a moderate `max_dims` produces a complete structural map in acceptable time. The `SubsetResult` objects that emerge---typed, immutable, carrying both scalar and multi-dimensional performance data---feed directly into Pareto analysis, sensitivity profiling, adversarial testing, and every other downstream stage of the structural fuzzing pipeline.

The pattern's limitation is equally clear: it does not scale to hundreds of dimensions. For those problems, the heuristic methods---forward selection, backward elimination, and the stochastic approaches discussed in Chapter 12---are necessary. But the heuristics are most effective when calibrated against the brute-force ground truth on a reduced problem, and the transition from exact enumeration to approximate search is the subject of the next chapter.

---

## 11.10 Looking Ahead

Chapter 12 introduces the *compositional testing pattern*, which addresses the question that subset enumeration leaves open: **in what order should dimensions be added?** Subset enumeration tells us that {Complexity, Process, Size} is a strong 3-dimensional configuration, but it does not tell us whether to start with Complexity and add Process, or start with Process and add Complexity. The compositional test builds dimensions incrementally, measuring the marginal contribution of each addition in context, and produces an ordering that reveals the causal structure of dimension interactions. Where subset enumeration maps the landscape, compositional testing traces a path through it.
