# Chapter 8: Pareto Optimization

> *"The optimum is not a point but a surface, and the task of the engineer is to understand that surface before choosing where to stand on it."*
> --- Vilfredo Pareto, *Manual of Political Economy* (1906), adapted

The preceding chapters have developed a geometric vocabulary for multi-dimensional model analysis: state vectors (Chapter 3), subset enumeration (Chapter 4), distance metrics, and sensitivity profiling. Each of these tools produces results in multiple dimensions. Yet at some point the practitioner must *decide*---which configuration to deploy, which feature set to adopt, how much complexity to tolerate. The temptation is to collapse the multi-dimensional result into a single number and optimize that number. This chapter explains why that temptation must be resisted, what to do instead, and how the structural fuzzing framework implements the alternative.

The alternative is Pareto optimization: identifying the set of configurations that cannot be improved on one objective without sacrificing another, and then reasoning about the structure of that set directly. No weights are chosen. No objectives are combined. The geometry of the tradeoff surface speaks for itself.

---

## 8.1 Pareto Dominance: The Fundamental Definition

### 8.1.1 Dominance in Two Objectives

Consider two configurations $\mathbf{a}$ and $\mathbf{b}$, each evaluated on two objectives $f_1$ and $f_2$ that we wish to minimize. Configuration $\mathbf{a}$ *dominates* $\mathbf{b}$, written $\mathbf{a} \prec \mathbf{b}$, if and only if:

$$f_1(\mathbf{a}) \leq f_1(\mathbf{b}) \quad \text{and} \quad f_2(\mathbf{a}) \leq f_2(\mathbf{b})$$

with at least one strict inequality. Dominance is a partial order: given two arbitrary configurations, it is entirely possible that neither dominates the other. Configuration $\mathbf{a}$ may excel on $f_1$ while $\mathbf{b}$ excels on $f_2$. In this case the two are *mutually non-dominated*, and no amount of algorithmic cleverness can rank one above the other without introducing a preference between the objectives.

### 8.1.2 The General Case

For $m$ objectives $f_1, f_2, \ldots, f_m$ (all to be minimized), dominance generalizes naturally:

$$\mathbf{a} \prec \mathbf{b} \iff \forall\, i \in \{1, \ldots, m\}: f_i(\mathbf{a}) \leq f_i(\mathbf{b}) \;\;\text{and}\;\; \exists\, j: f_j(\mathbf{a}) < f_j(\mathbf{b})$$

The *Pareto frontier* (or Pareto front) is the set of all configurations that are not dominated by any other configuration in the search space:

$$\mathcal{P} = \{\mathbf{a} \in \mathcal{S} : \nexists\, \mathbf{b} \in \mathcal{S} \;\text{such that}\; \mathbf{b} \prec \mathbf{a}\}$$

Every configuration not on the Pareto frontier is strictly inferior to at least one configuration that is: it can be improved on one or more objectives without cost to any other. The frontier is the irreducible set of optimal tradeoffs---the "efficient surface" in Pareto's original terminology.

### 8.1.3 Geometric Interpretation

In the objective space $\mathbb{R}^m$, the Pareto frontier forms a $(m-1)$-dimensional surface. For two objectives, it is a curve. For three, a surface. The frontier separates the *attainable* region (objective vectors achievable by some configuration) from the *ideal* region (objective vectors better than anything achievable). The shape of this surface---its curvature, its extent, the gaps along it---encodes the fundamental tradeoff structure of the problem.

A convex Pareto frontier indicates that tradeoffs are smooth: small sacrifices in one objective yield small gains in another. A concave frontier indicates the opposite: the objectives are synergistic in some regions, and moving along the frontier can simultaneously improve both. A frontier with sharp corners indicates phase transitions---qualitative changes in the optimal strategy as the tradeoff ratio shifts.

---

## 8.2 Why Scalarization Fails

### 8.2.1 The Weighted-Sum Approach

The most common approach to multi-objective optimization is *scalarization*: combine the objectives into a single scalar using a weighted sum,

$$\Phi(\mathbf{x}) = \sum_{i=1}^{m} w_i \, f_i(\mathbf{x})$$

and then minimize $\Phi$. This reduces the problem to standard single-objective optimization, for which powerful algorithms exist.

The difficulty is that scalarization destroys precisely the information that Chapter 1 argued is irrecoverable. Recall the Scalar Irrecoverability Theorem (Section 1.1.1): the projection $\phi : \mathbb{R}^m \to \mathbb{R}^1$ has a null space of dimension $m - 1$. Any two configurations that differ only within this null space are indistinguishable under $\phi$, yet they may occupy entirely different positions on the Pareto frontier. Choosing weights *before* understanding the frontier is choosing a projection *before* understanding the space---precisely the methodological error that the geometric approach is designed to prevent.

### 8.2.2 The Convexity Limitation

Even when the practitioner is willing to choose weights, scalarization has a structural limitation: weighted-sum optimization can only find points on the *convex hull* of the Pareto frontier. If the frontier is non-convex---containing concave regions or "pockets"---no choice of positive weights can reach the configurations in those regions.

To see why, observe that minimizing $\Phi(\mathbf{x}) = \sum w_i f_i(\mathbf{x})$ is equivalent to finding the point on the Pareto frontier where the hyperplane $\sum w_i f_i = c$ (for varying $c$) first touches the attainable region. Hyperplanes are convex sets, so they can only touch the convex hull of the frontier. Points in non-convex indentations of the frontier are invisible to any weighted sum.

In the structural fuzzing context, non-convex frontiers arise naturally. Consider the two objectives "number of feature groups" (dimensionality $k$) and "prediction error" (MAE). A configuration using two carefully chosen feature groups may outperform all three-group configurations---creating a non-convex pocket at $k = 3$. No weighted combination of $k$ and MAE can discover this pocket. Only direct enumeration and dominance-based filtering can find it.

### 8.2.3 The Preference Inversion Problem

A subtler failure mode of scalarization is *preference inversion*: the optimal configuration under weights $\mathbf{w}_1$ may be ranked lower than a suboptimal configuration under slightly different weights $\mathbf{w}_2$, with no way to determine which weights are "correct" without external domain knowledge. In practice, this means that two teams analyzing the same data with slightly different weight choices can reach opposite conclusions about which configuration is best---and both are "right" within their respective scalarizations.

Pareto analysis avoids this entirely. The Pareto frontier is invariant to the choice of weights: it is a property of the configurations and objectives themselves, not of any preference structure imposed on them. The frontier presents the full tradeoff surface and lets the practitioner make an informed choice *after* seeing the options, rather than baking preferences into the optimization *before* seeing the results.

---

## 8.3 Constructing the Pareto Frontier from Subset Results

In the structural fuzzing framework, the most natural pair of objectives is:

- **Objective 1: Minimize dimensionality** $k$ (number of active feature groups). Fewer groups mean simpler models, faster training, easier interpretation.
- **Objective 2: Minimize prediction error** (MAE). Lower error means better predictive accuracy.

The `enumerate_subsets` function from Chapter 4 produces a list of `SubsetResult` objects, each recording the best MAE achievable with a particular subset of dimensions. The `pareto_frontier` function extracts the non-dominated configurations from this list.

### 8.3.1 The SubsetResult Data Structure

Each subset optimization produces a `SubsetResult` that bundles the subset identity with its performance:

```python
@dataclass
class SubsetResult:
    dims: tuple[int, ...]       # Indices of active dimensions
    dim_names: tuple[str, ...]  # Human-readable names
    n_dims: int                 # Number of active dimensions
    param_values: np.ndarray    # Full parameter vector (including inactive)
    mae: float                  # Mean absolute error at optimum
    errors: dict[str, float]    # Per-component error breakdown
    pareto_optimal: bool = False
```

The `errors` dictionary provides a per-component breakdown---not just the aggregate MAE but how each evaluation metric (accuracy, precision, recall, F1, AUC) contributes to the total error. This decomposition is essential for understanding *why* a configuration performs as it does, not just *how well*. The `pareto_optimal` flag is initially `False` and is set by the Pareto frontier extraction algorithm.

### 8.3.2 From Enumeration to Frontier

The connection between subset enumeration (Chapter 4) and Pareto analysis is direct. Subset enumeration explores the space of possible feature-group combinations:

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
    n_all = len(dim_names)
    results: list[SubsetResult] = []

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

    results.sort(key=lambda r: r.mae)
    return results
```

For $n$ dimensions with maximum subset size $k$, this generates $\sum_{j=1}^{k} \binom{n}{j}$ configurations. Each is a point in the two-dimensional objective space $(k, \text{MAE})$. The Pareto frontier is the lower-left boundary of this point cloud---the configurations where no other point has both fewer dimensions and lower error.

---

## 8.4 Non-Dominated Sorting: The Algorithm

### 8.4.1 The Three-Phase Algorithm

The `pareto_frontier` function implements non-dominated sorting in three phases:

```python
def pareto_frontier(
    results: list[SubsetResult],
    tolerance: float = 0.01,
) -> list[SubsetResult]:
    if not results:
        return []

    # Reset all pareto flags
    for r in results:
        r.pareto_optimal = False

    # Find best MAE at each dimensionality
    best_at_k: dict[int, SubsetResult] = {}
    for r in results:
        k = r.n_dims
        if k not in best_at_k or r.mae < best_at_k[k].mae:
            best_at_k[k] = r

    # Extract candidates sorted by n_dims
    candidates = sorted(best_at_k.values(), key=lambda r: r.n_dims)

    # Filter to Pareto front: a candidate is dominated if another candidate
    # has fewer dims AND better-or-equal MAE
    pareto: list[SubsetResult] = []
    best_mae_so_far = float("inf")

    for candidate in candidates:
        if candidate.mae < best_mae_so_far - tolerance:
            candidate.pareto_optimal = True
            pareto.append(candidate)
            best_mae_so_far = candidate.mae
        elif not pareto:
            # Always include the first (lowest-dim) candidate
            candidate.pareto_optimal = True
            pareto.append(candidate)
            best_mae_so_far = candidate.mae

    return pareto
```

**Phase 1: Reduction to representatives.** Among all subsets of size $k$, only the one with the lowest MAE can possibly be Pareto-optimal. If two configurations have the same dimensionality, the one with worse MAE is dominated by the one with better MAE (same $k$, higher error). The `best_at_k` dictionary selects a single representative for each dimensionality level, reducing potentially hundreds of candidates to at most $n$ representatives.

**Phase 2: Sorting by dimensionality.** The representatives are sorted in ascending order of `n_dims`. This ordering is critical because the Pareto condition involves comparing each candidate against all candidates of *lower* dimensionality. By processing candidates from lowest to highest dimensionality, we can maintain a running minimum and make the dominance check in constant time per candidate.

**Phase 3: Forward sweep with tolerance.** We scan the sorted candidates, maintaining `best_mae_so_far`---the lowest MAE achieved at any dimensionality already processed. A candidate at dimensionality $k$ enters the Pareto front only if its MAE strictly improves upon the running best by at least the tolerance threshold $\epsilon$:

$$\text{MAE}(k) < \text{best\_mae\_so\_far} - \epsilon$$

The first candidate (lowest dimensionality) is always included, establishing the baseline. Each subsequent Pareto-optimal point must demonstrate that the additional complexity buys a meaningful improvement in accuracy.

### 8.4.2 Complexity Analysis

Phase 1 requires a single pass over all $m$ results: $O(m)$. Phase 2 sorts at most $n$ representatives: $O(n \log n)$, where $n$ is the number of distinct dimensionality levels. Phase 3 is a single linear scan: $O(n)$. The total complexity is $O(m + n \log n)$, which is dominated by the initial pass when $m \gg n$ (as is typical, since $m = \sum \binom{n}{j}$ grows combinatorially while $n$ is the number of dimensions).

### 8.4.3 The Role of Tolerance

The `tolerance` parameter (default $\epsilon = 0.01$) deserves careful attention. Without tolerance ($\epsilon = 0$), the frontier includes every dimensionality level where the best MAE is even infinitesimally better than at lower dimensionalities. This produces a frontier cluttered with configurations that offer negligible improvement at the cost of additional complexity.

With tolerance, the frontier enforces a *minimum marginal improvement*. A configuration at dimensionality $k$ must reduce MAE by at least $\epsilon$ relative to the best lower-dimensional configuration to be considered non-dominated. This reflects an engineering reality: improvements smaller than the tolerance are likely within measurement noise, numerical precision limits, or the variance of the optimization procedure itself.

The tolerance also has a geometric interpretation. In the $(k, \text{MAE})$ plane, standard Pareto dominance uses axis-aligned dominance cones. The tolerance parameter widens the dominance cone along the MAE axis by $\epsilon$, making it harder for marginally better configurations to survive the dominance filter. The result is a sparser, more interpretable frontier.

---

## 8.5 The Structural Fuzzing Pareto Implementation

### 8.5.1 Integration in the Campaign Pipeline

The `run_campaign` function orchestrates the full structural fuzzing analysis, with Pareto extraction as its second stage:

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

The pipeline proceeds in six stages: (1) subset enumeration, (2) Pareto frontier extraction, (3) sensitivity profiling, (4) Model Robustness Index computation, (5) adversarial threshold search, and (6) compositional testing. The Pareto frontier from stage 2 feeds into subsequent stages: the sensitivity profile and MRI are computed at the best configuration found during enumeration, and the adversarial search probes each dimension for tipping points relative to that configuration.

The relevant pipeline excerpt shows the handoff from enumeration to Pareto analysis:

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
```

The result is a `StructuralFuzzReport` that carries both the full set of subset results and the extracted Pareto frontier, enabling downstream analysis to operate on either.

### 8.5.2 Design Decisions

Several design decisions in the implementation merit discussion.

**Dimensionality as a discrete objective.** The framework treats dimensionality $k$ as a discrete integer objective rather than a continuous variable. This is a deliberate choice. The number of active feature groups is inherently discrete---you either include a group or you do not. Treating it as continuous (e.g., via regularization strength) blurs the distinction between "feature group present" and "feature group absent," producing configurations that are difficult to interpret. The discrete treatment preserves the structural clarity of subset-based analysis.

**Mutation of the `pareto_optimal` flag.** The `pareto_frontier` function modifies the `pareto_optimal` flag on the input `SubsetResult` objects in place. This is a pragmatic choice: it allows downstream code (reporting, visualization) to query any result's Pareto status without maintaining a separate index. The tradeoff is that the function has a side effect, which violates the immutability principle discussed in Chapter 1. In practice, the Pareto computation is run exactly once per campaign, making the mutation harmless.

**The first-candidate guarantee.** The algorithm always includes the lowest-dimensionality candidate in the frontier, even if its MAE is not strictly better than any other candidate (the `elif not pareto` branch). This ensures the frontier spans the full range of dimensionalities, giving the practitioner a baseline at minimum complexity. Without this guarantee, the frontier could start at $k = 3$ if no $k = 1$ or $k = 2$ configuration met the tolerance threshold---leaving the practitioner with no information about what simpler models can achieve.

---

## 8.6 Visualizing Tradeoff Surfaces

### 8.6.1 The Dimensionality-MAE Plot

The primary visualization for Pareto analysis in the structural fuzzing framework is a scatter plot with dimensionality $k$ on the horizontal axis and MAE on the vertical axis. Every evaluated configuration appears as a point. The Pareto-optimal points are highlighted---typically with a different color or a connecting line---forming the frontier.

```
MAE
 |
 |  x
 |  x   x
 |  o       x   x
 |      o       x
 |          o
 |              o
 +--------------------> k
    1   2   3   4

 o = Pareto-optimal    x = dominated
```

The visual encodes three pieces of information simultaneously:

1. **The frontier itself** shows the best achievable MAE at each dimensionality.
2. **The gap between dominated points and the frontier** shows how much room there is for subset selection to matter. A large gap means the choice of *which* dimensions to include is as important as *how many*.
3. **The slope of the frontier** shows the marginal return to complexity. A steep section means the next dimension buys significant accuracy; a flat section means it does not.

### 8.6.2 The Error Decomposition View

The aggregate MAE hides which components of the error improve as dimensions are added. A stacked bar chart, with one bar per Pareto-optimal configuration and segments for each error component, reveals this decomposition:

| $k$ | Accuracy Error | Precision Error | Recall Error | F1 Error | AUC Error |
|:---:|:-:|:-:|:-:|:-:|:-:|
| 1 | 3.2 | 4.1 | 5.8 | 4.9 | 2.1 |
| 2 | 1.8 | 2.3 | 3.1 | 2.7 | 1.4 |
| 3 | 1.2 | 1.5 | 1.8 | 1.6 | 1.0 |
| 5 | 0.9 | 1.1 | 1.3 | 1.2 | 0.8 |

This table---derived from the `errors` dictionary on each `SubsetResult`---shows that recall error improves most dramatically between $k = 1$ and $k = 3$, while AUC error is already low at $k = 1$. The geometric interpretation: the feature groups added at $k = 2$ and $k = 3$ primarily improve the model's ability to detect positive cases (defective modules), while the model's ranking quality (AUC) is largely determined by the first feature group alone.

### 8.6.3 Three-Objective Frontiers

When three objectives are present---say dimensionality, MAE, and robustness (MRI)---the Pareto frontier becomes a surface in $\mathbb{R}^3$. Visualization requires projection. Three useful projections are:

- $(k, \text{MAE})$: the accuracy-complexity tradeoff, ignoring robustness.
- $(k, \text{MRI})$: the robustness-complexity tradeoff, ignoring accuracy.
- $(\text{MAE}, \text{MRI})$: the accuracy-robustness tradeoff, ignoring complexity.

Each projection shows a two-dimensional Pareto frontier. A configuration that appears on all three projected frontiers is a strong candidate---it is non-dominated regardless of which pair of objectives the practitioner prioritizes.

---

## 8.7 Pareto Analysis for Feature Selection

### 8.7.1 The Feature Selection Problem

Feature selection is a classic multi-objective problem: include more features to improve accuracy, or exclude features to reduce overfitting, training time, and interpretive burden. Traditional approaches---filter methods, wrapper methods, embedded methods---ultimately reduce to a single-objective problem by fixing a feature count or a regularization strength. Pareto analysis treats the problem natively as multi-objective.

In the structural fuzzing framework, features are organized into *groups* (the "dimensions" of the state space), and subset enumeration explores all combinations of groups up to a specified maximum size. This is a structured form of feature selection: rather than choosing among $2^{16}$ individual feature subsets (for 16 features), the practitioner chooses among $2^5 - 1 = 31$ group subsets (for 5 groups). The grouping reduces the combinatorial explosion while preserving the semantically meaningful structure of the feature space.

### 8.7.2 Reading the Frontier for Feature Group Importance

The Pareto frontier reveals feature group importance more precisely than univariate sensitivity analysis. Consider a 5-group defect prediction model with groups {Size, Complexity, Halstead, OO, Process}. The frontier might look like:

| $k$ | Best Subset | MAE |
|:---:|:---|:---:|
| 1 | {Complexity} | 3.8 |
| 2 | {Complexity, Process} | 2.1 |
| 3 | {Complexity, Process, Size} | 1.7 |
| 5 | All groups | 1.5 |

Several observations follow immediately:

1. **Complexity is the foundation.** It appears in every Pareto-optimal subset.
2. **Process is the strongest complement.** Adding Process to Complexity reduces MAE by 1.7---the largest single-step improvement.
3. **Size contributes modestly.** Adding Size to {Complexity, Process} reduces MAE by 0.4.
4. **OO and Halstead together contribute only 0.2.** Going from 3 groups to all 5 yields diminishing returns.
5. **No 4-group configuration appears on the frontier.** The best 4-group configuration does not improve enough over the best 3-group configuration to survive the tolerance filter.

This analysis is richer than a simple importance ranking. It tells you not just *which* groups matter but *how they combine*: Complexity and Process are jointly essential, Size is valuable but not critical, and OO and Halstead are dispensable.

### 8.7.3 The Pareto-Guided Selection Rule

The frontier suggests a concrete decision procedure:

1. Compute the Pareto frontier over all subsets.
2. For each consecutive pair of Pareto-optimal points $(k_i, \text{MAE}_i)$ and $(k_{i+1}, \text{MAE}_{i+1})$, compute the marginal cost-benefit ratio:

$$\rho_i = \frac{\text{MAE}_i - \text{MAE}_{i+1}}{k_{i+1} - k_i}$$

3. Select the configuration just before $\rho_i$ drops below a domain-specific threshold.

For the defect prediction example, the ratios are:

| Transition | $\Delta k$ | $\Delta \text{MAE}$ | $\rho$ |
|:---|:---:|:---:|:---:|
| $k=1 \to k=2$ | 1 | 1.7 | 1.70 |
| $k=2 \to k=3$ | 1 | 0.4 | 0.40 |
| $k=3 \to k=5$ | 2 | 0.2 | 0.10 |

With a threshold of $\rho \geq 0.3$, the practitioner selects $k = 3$ (three feature groups). Each additional group beyond three buys less than 0.3 MAE improvement per group added---below the threshold of practical significance. The decision is data-driven, explicit, and reproducible.

---

## 8.8 The Defect Prediction Example

### 8.8.1 Problem Setup

The `examples/defect_prediction/model.py` file implements a complete defect prediction model with known ground truth, providing a controlled testbed for Pareto analysis. The model uses five feature groups, each containing related software metrics:

```python
FEATURE_GROUPS = {
    "Size": [0, 1, 2],
    "Complexity": [3, 4, 5],
    "Halstead": [6, 7, 8, 9],
    "OO": [10, 11, 12],
    "Process": [13, 14, 15],
}
```

The synthetic data generator embeds a known causal structure: defect probability is driven primarily by Complexity and Process metrics, with a weak contribution from Size, and no contribution from OO:

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

The coefficients reveal the ground truth importance: essential complexity (0.15) and revisions (0.12) are strongest, followed by cyclomatic complexity (0.10), authors (0.10), churn (0.08), design complexity (0.05), and LOC (0.03). OO metrics (coupling, cohesion, inheritance depth) have zero coefficient---they are pure noise.

### 8.8.2 The Evaluation Function

The `make_evaluate_fn` factory creates an evaluation function compatible with the structural fuzzing framework. For each configuration, feature groups with parameter values below 1000 are included; those at or above 1000 are excluded:

```python
def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
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
    y_prob = rf.predict_proba(X_te)
    # ... compute accuracy, precision, recall, F1, AUC ...
```

The evaluation function trains a random forest on the active features, computes five performance metrics, and returns the average absolute deviation from target values as the MAE. The `errors` dictionary records each metric's deviation individually, enabling the error decomposition analysis discussed in Section 8.6.2.

### 8.8.3 Running the Pareto Analysis

A complete Pareto analysis of the defect prediction model proceeds as follows:

```python
from structural_fuzzing.core import enumerate_subsets
from structural_fuzzing.pareto import pareto_frontier
from examples.defect_prediction.model import make_evaluate_fn, GROUP_NAMES

evaluate_fn = make_evaluate_fn(n_samples=1000, seed=42)

# Enumerate all subsets up to size 4
all_results = enumerate_subsets(
    dim_names=GROUP_NAMES,
    evaluate_fn=evaluate_fn,
    max_dims=4,
    verbose=True,
)

# Extract Pareto frontier
frontier = pareto_frontier(all_results, tolerance=0.01)

print("Pareto frontier:")
for r in frontier:
    print(f"  k={r.n_dims}  {r.dim_names}  MAE={r.mae:.4f}")
```

For 5 groups with `max_dims=4`, the enumeration evaluates $\binom{5}{1} + \binom{5}{2} + \binom{5}{3} + \binom{5}{4} = 5 + 10 + 10 + 5 = 30$ subsets. Each 1D subset requires 20 evaluations (grid search), each 2D subset requires 400 (grid product), and each 3D or 4D subset requires 5000 (random search). The total evaluation budget is $5 \times 20 + 10 \times 400 + 10 \times 5000 + 5 \times 5000 = 100 + 4000 + 50{,}000 + 25{,}000 = 79{,}100$ model evaluations.

### 8.8.4 Interpreting the Results

The Pareto frontier for this model recovers the known ground truth. The frontier typically contains:

- **$k = 1$: {Complexity}.** The single most informative group, as expected from the large coefficients on cyclomatic, essential, and design complexity.
- **$k = 2$: {Complexity, Process}.** The two groups with the largest aggregate coefficients.
- **$k = 3$: {Complexity, Process, Size}.** Size contributes weakly but measurably through the LOC coefficient.
- **$k = 5$: All groups.** The random forest can extract marginal signal from Halstead (which is correlated with Size and Complexity) but gains nothing from OO.

The absence of $k = 4$ from the frontier confirms that no 4-group configuration improves enough over the best 3-group configuration to meet the tolerance threshold. The best 4-group subsets are either {Complexity, Process, Size, Halstead} or {Complexity, Process, Size, OO}, both of which reduce MAE by less than 0.01 relative to {Complexity, Process, Size}.

This result validates the Pareto approach: without any knowledge of the ground-truth coefficients, the analysis correctly identifies which feature groups matter, in what order, and where the point of diminishing returns lies.

---

## 8.9 Beyond Two Objectives: Multi-Objective Extensions

### 8.9.1 Adding Robustness as a Third Objective

The campaign pipeline computes the Model Robustness Index (MRI) for the best configuration found during enumeration. But MRI can also be computed for every Pareto-optimal configuration, creating a three-objective problem: minimize dimensionality, minimize MAE, and minimize MRI (lower MRI indicates greater robustness).

This extension reveals an important phenomenon: the most accurate configuration is not always the most robust. A model using all five feature groups may achieve the lowest MAE but exhibit high MRI because perturbations in the noisy OO features propagate through the random forest. A simpler model using only {Complexity, Process} may have slightly higher MAE but much lower MRI, because all active features carry genuine signal and the model's predictions are stable under perturbation.

The three-objective Pareto frontier makes this tradeoff explicit. A configuration that is Pareto-optimal in (dimensionality, MAE) may be dominated when robustness is included, and vice versa. The three-way frontier is the correct object for decision-making when all three concerns---simplicity, accuracy, and stability---are relevant.

### 8.9.2 Fairness and Subgroup Performance

In applications where the model serves diverse populations, subgroup performance metrics become additional objectives. For defect prediction, relevant subgroups might be "large modules vs. small modules" or "legacy code vs. new code." Each subgroup's recall or precision becomes an objective to be minimized (or maximized, after negation).

The Pareto frontier in this expanded objective space identifies configurations that balance performance across subgroups without requiring the practitioner to assign relative importance to each subgroup a priori. This connects directly to Chapter 1's discussion of hidden compensation (Section 1.1.3): a scalar metric can mask disparities that the Pareto frontier reveals.

### 8.9.3 Computational Cost

The cost of Pareto frontier extraction grows with the number of objectives, but only modestly. The non-dominated sorting algorithm from Section 8.4 generalizes straightforwardly: for $m$ objectives and $n$ candidates, a naive pairwise dominance check requires $O(n^2 m)$ comparisons. For the structural fuzzing application, $n$ is the number of distinct dimensionality levels (at most equal to the number of feature groups, typically 5--10) and $m$ is the number of objectives (typically 2--4). The Pareto extraction itself is never the bottleneck; the model evaluations within `enumerate_subsets` dominate the computation.

---

## 8.10 Common Pitfalls

### 8.10.1 Confusing the Frontier with the Optimum

The Pareto frontier is not a single answer. It is a *set* of answers, each optimal under a different implicit weighting of the objectives. Practitioners accustomed to single-objective optimization sometimes extract the frontier and then immediately select the point with the lowest MAE, discarding the dimensionality information. This defeats the purpose. The frontier exists precisely so that the tradeoff can be examined and a deliberate choice made.

### 8.10.2 Over-Interpreting Small Frontiers

When the number of dimensionality levels is small (say, 3--5), the frontier contains very few points and its shape is difficult to interpret. A frontier with two points---one at $k = 1$ and one at $k = 5$---tells you only that intermediate configurations do not improve enough over $k = 1$ to meet the tolerance. It does not tell you that $k = 2, 3, 4$ are useless; it tells you that the *best* configurations at those sizes were not sufficiently better than at $k = 1$. The distinction matters when the number of candidate subsets at each size is small.

### 8.10.3 Tolerance Sensitivity

The tolerance parameter $\epsilon$ has outsized influence on small frontiers. Setting $\epsilon = 0$ produces the maximum number of Pareto-optimal points; setting $\epsilon$ too large collapses the frontier to a single point. There is no universally correct value. A principled approach is to set $\epsilon$ equal to the standard deviation of the optimization noise---the variation in MAE that arises from the stochastic elements of the search (random initialization, random search in 3D+ subsets). Improvements smaller than this noise floor are not reliably meaningful.

---

## 8.11 Connection to What Follows

The Pareto frontier identifies *which* configurations represent optimal tradeoffs. It does not, by itself, reveal *how fragile* those tradeoffs are. A configuration sitting on the frontier may occupy a broad, stable region of the parameter space, or it may perch on a narrow ridge where small perturbations send it tumbling off the frontier entirely.

Chapter 9 addresses this question directly through adversarial robustness testing. Where this chapter asks "what are the best tradeoffs?", Chapter 9 asks "how far can we push each tradeoff before it breaks?" The two analyses compose naturally: first identify the Pareto-optimal configurations (this chapter), then stress-test each one to find its breaking points (Chapter 9). Together, they provide a complete picture of the tradeoff landscape---not just its surface, but its depth and stability.

The progression from enumeration (Chapter 4) through Pareto analysis (this chapter) to adversarial probing (Chapter 9) reflects a general principle of the geometric approach: understanding a space requires examining it at multiple scales. Enumeration maps the space coarsely. Pareto analysis identifies the interesting regions. Adversarial testing probes the fine structure of those regions. Each step narrows the focus while increasing the resolution, building toward the complete geometric characterization that is the goal of the structural fuzzing framework.

---

## Exercises

1. **Dominance relation properties.** Prove that Pareto dominance is a strict partial order: it is irreflexive ($\mathbf{a} \nprec \mathbf{a}$), asymmetric ($\mathbf{a} \prec \mathbf{b} \implies \mathbf{b} \nprec \mathbf{a}$), and transitive ($\mathbf{a} \prec \mathbf{b}$ and $\mathbf{b} \prec \mathbf{c}$ imply $\mathbf{a} \prec \mathbf{c}$). Why is totality ($\mathbf{a} \prec \mathbf{b}$ or $\mathbf{b} \prec \mathbf{a}$ for all $\mathbf{a} \neq \mathbf{b}$) generally absent?

2. **Convexity and scalarization.** Construct a set of four points in $(k, \text{MAE})$ space such that the Pareto frontier is non-convex. Show that no positive weight vector $\mathbf{w} = (w_1, w_2)$ with $w_1, w_2 > 0$ recovers the complete frontier when used for scalarized optimization.

3. **Tolerance calibration.** Run `pareto_frontier` on the defect prediction example with tolerance values $\epsilon \in \{0, 0.001, 0.01, 0.1, 1.0\}$. Plot the number of Pareto-optimal configurations as a function of $\epsilon$. At what value of $\epsilon$ does the frontier collapse to a single point? Relate this value to the range of MAE values in the subset results.

4. **Three-objective frontier.** Extend the defect prediction analysis to compute MRI for each Pareto-optimal configuration (in the two-objective sense). Identify configurations that are Pareto-optimal in the two-objective $(k, \text{MAE})$ sense but dominated in the three-objective $(k, \text{MAE}, \text{MRI})$ sense. What does this tell you about the relationship between accuracy and robustness?

5. **Greedy vs. exhaustive.** Compare the Pareto frontier obtained from `enumerate_subsets` with the compositional sequence from `compositional_test` for the defect prediction model. At which dimensionality levels do the two methods select different subsets? Explain the disagreement in terms of feature group interactions.
