# Chapter 12: Compositional Testing

> *"The whole is other than the sum of its parts."*
> --- Kurt Koffka, *Principles of Gestalt Psychology* (1935)

Chapters 4 and 9 developed two complementary views of multi-dimensional model behavior. Subset enumeration (Chapter 4) asks: which combinations of dimensions produce the best fit? Sensitivity profiling (Chapter 9) asks: how much does each dimension contribute to the baseline? Both are indispensable. Both are incomplete.

Subset enumeration tests every combination independently, but it does not reveal *how* dimensions interact---whether the combination of Complexity and Process is better than expected from their individual contributions, or merely the sum of two independent effects. Sensitivity profiling measures the marginal contribution of each dimension by ablation, but it holds all other dimensions fixed, missing the cases where removing two dimensions simultaneously is far worse (or far better) than removing each alone.

The gap between these methods is the subject of this chapter. Compositional testing fills the gap by systematically measuring the *interactions* between dimensions---the synergies and redundancies that emerge when dimensions are combined. The key insight is that interaction effects are not anomalies to be ignored but first-class geometric features of the model's behavior landscape. A dimension pair that exhibits strong synergy occupies a qualitatively different region of the evaluation space than a pair whose contributions are merely additive. Detecting, quantifying, and interpreting these interactions is essential for understanding why a model works and when it will break.

We begin with a precise definition of what single-dimension analysis misses (Section 12.1), develop the interaction matrix formalism (Section 12.2), introduce the compositional testing algorithm implemented in the structural fuzzing framework (Section 12.3), discuss interpretation of results (Section 12.4), connect compositional testing to sensitivity profiling (Section 12.5), and close with the forward connection to Chapter 13.

---

## 12.1 The Limits of Single-Dimension Analysis

### 12.1.1 Ablation Assumes Independence

Recall the sensitivity profiling function from Chapter 9. Given a baseline parameter vector and an evaluation function, it measures the effect of deactivating each dimension one at a time:

```python
def sensitivity_profile(
    params: np.ndarray,
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    inactive_value: float = 1e6,
) -> list[SensitivityResult]:
    """Compute sensitivity profile by ablating each dimension."""
    # Baseline MAE
    base_mae, _ = evaluate_fn(params)

    results: list[SensitivityResult] = []
    for i, name in enumerate(dim_names):
        ablated = params.copy()
        ablated[i] = inactive_value
        ablated_mae, _ = evaluate_fn(ablated)
        delta = ablated_mae - base_mae
        results.append(
            SensitivityResult(
                dim=i,
                dim_name=name,
                mae_with=base_mae,
                mae_without=ablated_mae,
                delta_mae=delta,
                importance_rank=0,
            )
        )

    results.sort(key=lambda r: r.delta_mae, reverse=True)
    for rank, r in enumerate(results, 1):
        r.importance_rank = rank

    return results
```

The structure is clean: iterate over dimensions, ablate one, measure the damage. The result is a ranked list of importance scores. But notice the implicit assumption: the delta for dimension $i$ is computed while *all other dimensions remain active*. This is a conditional measurement, not a marginal one. The sensitivity of dimension $i$ depends on the presence of dimensions $j, k, \ldots$, and that dependency is never measured.

### 12.1.2 The Interaction Problem

To see why this matters, consider a model with five dimensions and the following behavior:

- Dimensions A and B are individually weak: removing either one barely changes the MAE ($\Delta_A = 0.1$, $\Delta_B = 0.15$).
- Together, A and B capture a critical interaction: removing *both* increases MAE by 2.3, not 0.25.

The sensitivity profile ranks A and B at the bottom of the importance list. An analyst guided purely by sensitivity profiling might discard both dimensions to simplify the model. The result would be catastrophic---a 2.3-unit increase in error from removing dimensions that individually appeared to contribute almost nothing.

This failure mode is not exotic. It arises whenever two dimensions provide *complementary* information: each is individually uninformative, but together they triangulate a feature of the data that neither can capture alone. In software defect prediction, for example, code complexity and developer experience might individually correlate weakly with defects, but their interaction (complex code written by inexperienced developers) is a powerful predictor. In signal processing, two frequency bands might each contain only noise, but their phase relationship encodes the signal.

The general principle: single-dimension analysis decomposes a multi-dimensional space into independent axes. When the structure of the problem aligns with those axes, the decomposition is faithful. When the structure is *rotated* relative to the axes---when the important directions in the space are diagonal, not axis-aligned---single-dimension analysis misses the structure entirely.

### 12.1.3 Quantifying What Is Missed

Let $f(\mathbf{x})$ denote the MAE for parameter vector $\mathbf{x}$, and let $\mathbf{x}^{(-i)}$ denote the vector with dimension $i$ set to its inactive value. The sensitivity profile computes:

$$\Delta_i = f(\mathbf{x}^{(-i)}) - f(\mathbf{x})$$

Now define the *pairwise interaction* between dimensions $i$ and $j$ as:

$$\Phi_{ij} = \left[f(\mathbf{x}^{(-ij)}) - f(\mathbf{x})\right] - \left[\Delta_i + \Delta_j\right]$$

where $\mathbf{x}^{(-ij)}$ denotes the vector with both dimensions $i$ and $j$ deactivated. The interaction term $\Phi_{ij}$ measures the difference between the actual effect of removing both dimensions and the effect predicted by summing the individual removals.

Three regimes emerge:

| Regime | Condition | Interpretation |
|--------|-----------|----------------|
| Additive | $\Phi_{ij} \approx 0$ | Dimensions contribute independently |
| Synergistic | $\Phi_{ij} > 0$ | Removing both is worse than predicted; the dimensions complement each other |
| Redundant | $\Phi_{ij} < 0$ | Removing both is better than predicted; the dimensions overlap |

The interaction matrix $\Phi \in \mathbb{R}^{n \times n}$ collects all pairwise interactions. Its diagonal entries are zero by construction ($\Phi_{ii} = 0$), and its off-diagonal entries quantify the departure from additivity for each pair. This matrix is a first-class geometric object: it encodes the curvature of the evaluation landscape with respect to dimension activations, revealing whether the landscape is locally flat (additive), concave (synergistic), or convex (redundant) in each pairwise direction.

---

## 12.2 The Interaction Matrix

### 12.2.1 Construction

Computing the full interaction matrix for $n$ dimensions requires evaluating $\binom{n}{2}$ pairwise ablations, plus the $n$ single-dimension ablations from the sensitivity profile, plus the baseline. The total cost is:

$$1 + n + \binom{n}{2} = 1 + n + \frac{n(n-1)}{2} = \frac{n^2 + n + 2}{2}$$

For five dimensions, this is 16 evaluations. For ten dimensions, 56. The quadratic scaling is manageable for the moderate-dimensional spaces that structural fuzzing typically operates in.

Given the sensitivity profile results and the pairwise ablation results, the interaction matrix is straightforward to construct:

```python
import numpy as np

def build_interaction_matrix(
    params: np.ndarray,
    dim_names: list[str],
    evaluate_fn,
    inactive_value: float = 1e6,
) -> np.ndarray:
    """Build the pairwise interaction matrix."""
    n = len(dim_names)
    base_mae, _ = evaluate_fn(params)

    # Single-dimension ablation deltas
    deltas = np.zeros(n)
    for i in range(n):
        ablated = params.copy()
        ablated[i] = inactive_value
        mae_i, _ = evaluate_fn(ablated)
        deltas[i] = mae_i - base_mae

    # Pairwise ablation and interaction computation
    phi = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            ablated = params.copy()
            ablated[i] = inactive_value
            ablated[j] = inactive_value
            mae_ij, _ = evaluate_fn(ablated)
            joint_delta = mae_ij - base_mae
            phi[i, j] = joint_delta - (deltas[i] + deltas[j])
            phi[j, i] = phi[i, j]  # symmetric

    return phi
```

### 12.2.2 Reading the Matrix

The interaction matrix is symmetric with zero diagonal. Its entries directly answer the question: "Do these two dimensions interact?"

Consider a five-dimensional model with dimensions {Size, Complexity, Halstead, OO, Process}. A hypothetical interaction matrix might look like:

|          | Size  | Complexity | Halstead | OO    | Process |
|----------|-------|------------|----------|-------|---------|
| Size     | 0     | +0.02      | -0.31    | +0.05 | +0.41   |
| Complexity | +0.02 | 0        | -0.28    | +0.11 | +0.87   |
| Halstead | -0.31 | -0.28      | 0        | -0.04 | +0.06   |
| OO       | +0.05 | +0.11      | -0.04    | 0     | +0.15   |
| Process  | +0.41 | +0.87      | +0.06    | +0.15 | 0       |

Several patterns are immediately visible:

1. **Strong synergy: Complexity + Process** ($\Phi = +0.87$). Removing both dimensions is far worse than the sum of individual removals predicts. These dimensions provide complementary information---likely, complexity metrics identify *what* is hard to maintain while process metrics identify *who* is maintaining it, and neither alone captures defect risk as well as their combination.

2. **Strong redundancy: Size + Halstead** ($\Phi = -0.31$). Removing both is less damaging than predicted by summing individual effects. Halstead metrics are mathematically derived from the same token-level program properties that determine lines of code, so they carry overlapping information.

3. **Near-additive: Size + Complexity** ($\Phi = +0.02$). These dimensions contribute nearly independently. Knowing one tells you almost nothing about the other's effect.

### 12.2.3 Higher-Order Interactions

Pairwise interactions do not tell the complete story. A triple of dimensions $\{i, j, k\}$ can exhibit a three-way interaction that is invisible to any pair:

$$\Phi_{ijk} = \left[f(\mathbf{x}^{(-ijk)}) - f(\mathbf{x})\right] - \left[\Delta_i + \Delta_j + \Delta_k\right] - \left[\Phi_{ij} + \Phi_{ik} + \Phi_{jk}\right]$$

The three-way interaction is the residual after accounting for all individual and pairwise effects. Computing all $\binom{n}{3}$ three-way interactions is cubic in $n$, which remains tractable for $n \leq 10$ but becomes expensive beyond that.

In practice, higher-order interactions are rarer than pairwise ones, and when they do occur they tend to involve dimensions that already exhibit strong pairwise interactions. A practical strategy is to compute the full pairwise matrix first, identify the pairs with the largest $|\Phi_{ij}|$, and then compute three-way interactions only for triples that include at least one strongly interacting pair.

This strategy connects directly to the subset enumeration of Chapter 11. Subset enumeration tests all combinations up to a maximum size, producing a complete picture of model behavior across the combinatorial space. The interaction matrix provides a *structured decomposition* of those results: instead of a flat list of subset performances, the matrix reveals *why* certain subsets perform well (synergistic interactions among their members) and others poorly (redundancy among their members). Subset enumeration is the exhaustive search; compositional testing is the analytical lens that makes the search results interpretable.

---

## 12.3 The Compositional Testing Algorithm

### 12.3.1 Greedy Dimension Building

The structural fuzzing framework implements compositional testing through a greedy dimension-building strategy. Rather than exhaustively evaluating all possible orderings, it constructs a single optimal ordering by starting with one dimension and iteratively adding the dimension that produces the greatest improvement:

```python
def compositional_test(
    start_dim: int,
    candidate_dims: Sequence[int],
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    inactive_value: float = 1e6,
    n_grid: int = 20,
    n_random: int = 5000,
) -> CompositionResult:
    """Build a greedy dimension-addition sequence.

    Starting from start_dim, iteratively add the candidate dimension that
    produces the lowest MAE. At each step, re-optimize all active dimensions.
    """
    active = [start_dim]
    remaining = list(candidate_dims)
    if start_dim in remaining:
        remaining.remove(start_dim)

    order = [start_dim]
    order_names = [dim_names[start_dim]]
    mae_sequence: list[float] = []
    param_sequence: list[np.ndarray] = []

    # Evaluate starting configuration
    result = optimize_subset(
        active_dims=active,
        all_dim_names=dim_names,
        evaluate_fn=evaluate_fn,
        inactive_value=inactive_value,
        n_grid=n_grid,
        n_random=n_random,
    )
    mae_sequence.append(result.mae)
    param_sequence.append(result.param_values.copy())

    while remaining:
        best_mae = float("inf")
        best_dim = remaining[0]
        best_params = None

        for candidate in remaining:
            trial_dims = active + [candidate]
            trial_result = optimize_subset(
                active_dims=trial_dims,
                all_dim_names=dim_names,
                evaluate_fn=evaluate_fn,
                inactive_value=inactive_value,
                n_grid=n_grid,
                n_random=n_random,
            )
            if trial_result.mae < best_mae:
                best_mae = trial_result.mae
                best_dim = candidate
                best_params = trial_result.param_values.copy()

        active.append(best_dim)
        remaining.remove(best_dim)
        order.append(best_dim)
        order_names.append(dim_names[best_dim])
        mae_sequence.append(best_mae)
        param_sequence.append(best_params)

    return CompositionResult(
        order=order,
        order_names=order_names,
        mae_sequence=mae_sequence,
        param_sequence=param_sequence,
    )
```

The algorithm produces a `CompositionResult` containing four parallel sequences:

- `order`: the indices of dimensions in the order they were added.
- `order_names`: the corresponding human-readable names.
- `mae_sequence`: the optimized MAE at each step, after re-optimizing all active dimensions jointly.
- `param_sequence`: the full parameter vector at each step.

### 12.3.2 Re-optimization at Each Step

A critical design decision in the implementation is that `optimize_subset` is called at every step with *all* currently active dimensions. When dimension $j$ is added to the active set $\{d_1, d_2, \ldots, d_k\}$, the optimization does not merely find the best value for $j$ while holding $d_1, \ldots, d_k$ fixed. It re-optimizes the entire $(k+1)$-dimensional subset jointly.

This re-optimization is essential because interactions between dimensions mean that the optimal value for $d_1$ may change when $d_j$ is introduced. The evaluation function mediates all dimensions simultaneously---it takes the full parameter vector and returns a single MAE---so adding a new dimension changes the optimization landscape for every active dimension. Holding earlier dimensions fixed would miss these cross-dimensional adjustments, producing suboptimal parameter values and, more importantly, inaccurate MAE estimates for each step.

The cost of re-optimization increases with the number of active dimensions. The `optimize_subset` function from the core framework handles this gracefully by switching strategies based on dimensionality:

```python
if n_active == 1:
    # 1D grid search
    for v in grid_values:
        params = np.full(n_all, inactive_value)
        params[active_dims[0]] = v
        mae, errors = evaluate_fn(params)
        if mae < best_mae:
            best_mae = mae
            best_params = params.copy()
            best_errors = errors.copy()

elif n_active == 2:
    # 2D full grid search
    for v0, v1 in itertools.product(grid_values, grid_values):
        params = np.full(n_all, inactive_value)
        params[active_dims[0]] = v0
        params[active_dims[1]] = v1
        mae, errors = evaluate_fn(params)
        if mae < best_mae:
            best_mae = mae
            best_params = params.copy()
            best_errors = errors.copy()

else:
    # 3D+ random search in log-space
    rng = np.random.default_rng(42)
    log_low, log_high = np.log10(0.01), np.log10(100)
    for _ in range(n_random):
        params = np.full(n_all, inactive_value)
        log_vals = rng.uniform(log_low, log_high, n_active)
        for i, dim in enumerate(active_dims):
            params[dim] = 10 ** log_vals[i]
        mae, errors = evaluate_fn(params)
        if mae < best_mae:
            best_mae = mae
            best_params = params.copy()
            best_errors = errors.copy()
```

For one or two active dimensions, grid search in log-space is exhaustive and exact. For three or more, random search in log-space provides good coverage at controllable cost. The log-space parameterization ensures that the search covers both fine-grained and coarse-grained parameter values uniformly, which is critical when parameters span multiple orders of magnitude.

### 12.3.3 Computational Cost

The greedy compositional test starting from one dimension with $n - 1$ candidates requires the following number of `optimize_subset` calls:

- Step 0 (start): 1 call (1D optimization)
- Step 1: $n - 1$ candidate evaluations (each a 2D optimization)
- Step 2: $n - 2$ candidate evaluations (each a 3D optimization)
- ...
- Step $k$: $n - k$ candidate evaluations (each a $(k+1)$-dimensional optimization)

The total is $1 + \sum_{k=1}^{n-1}(n-k) = 1 + \frac{n(n-1)}{2}$, which is $O(n^2)$. Each call's internal cost varies with dimensionality, but the outer structure is quadratic in $n$. For typical structural fuzzing applications with $n \leq 10$, this is entirely tractable.

Compare this to the full subset enumeration of Chapter 11, which tests $\sum_{k=1}^{n} \binom{n}{k} = 2^n - 1$ subsets. The compositional test is exponentially cheaper but produces a single greedy ordering rather than the complete combinatorial picture. The two analyses are complementary: enumeration maps the full landscape, while compositional testing traces a single efficient path through it.

---

## 12.4 Interpreting Compositional Results

### 12.4.1 The MAE Sequence

The primary output of compositional testing is the MAE sequence: a list of error values, one for each step of the greedy construction. A typical result might look like:

```
Build order: Complexity -> Process -> Size -> OO -> Halstead
MAE sequence: [3.81, 2.09, 1.72, 1.58, 1.51]
```

This sequence encodes several types of information.

**Marginal gains.** The difference between consecutive MAE values measures the marginal gain from adding each dimension:

| Step | Added | MAE | Marginal Gain |
|------|-------|-----|---------------|
| 0 | Complexity | 3.81 | --- |
| 1 | Process | 2.09 | 1.72 |
| 2 | Size | 1.72 | 0.37 |
| 3 | OO | 1.58 | 0.14 |
| 4 | Halstead | 1.51 | 0.07 |

The gains exhibit strong diminishing returns: the first dimension added (Process) produces a gain of 1.72, while the last (Halstead) produces only 0.07. This is a common pattern. It arises because each successive dimension can only capture the variance unexplained by the already-active dimensions, and that unexplained variance shrinks with each addition.

**Diminishing-returns elbow.** The point where marginal gains transition from substantial to negligible---the "elbow" of the MAE curve---is a natural place to draw a complexity boundary. In the example above, the elbow occurs at step 2 (adding Size), after which further dimensions contribute less than 0.15 MAE each. A practitioner might reasonably conclude that three dimensions (Complexity, Process, Size) capture the essential behavior and the remaining two add complexity without proportionate benefit. This connects directly to the Pareto analysis of Chapter 5: the elbow in the compositional sequence often corresponds to a Pareto-optimal point on the (dimensionality, MAE) frontier.

**Interaction signatures.** The marginal gains also encode interaction information, though less directly than the interaction matrix. If the gain from adding dimension $j$ to the set $\{d_1, \ldots, d_k\}$ is much larger than $j$'s individual ablation delta from the sensitivity profile, then $j$ is synergistic with the current active set: it contributes more in combination than it does alone. Conversely, if the gain is much smaller than the ablation delta, the current set already captures most of $j$'s information---a signature of redundancy.

### 12.4.2 Synergy versus Redundancy

The interaction matrix $\Phi_{ij}$ provides the precise decomposition, but the compositional test's MAE sequence offers a sequential view that is often more actionable. Define the *expected marginal gain* at step $k$ as the ablation delta $\Delta_{j}$ of the dimension $j$ being added (measured from the full model). Then:

- If the actual marginal gain exceeds $\Delta_j$: dimension $j$ is synergistic with the current active set. The combination unlocks performance that $j$'s individual contribution does not predict.
- If the actual marginal gain equals $\Delta_j$: dimension $j$ is additive. It contributes independently.
- If the actual marginal gain falls below $\Delta_j$: dimension $j$ is redundant with the current active set. Some of its information is already captured by active dimensions.

This comparison is not exact---the sensitivity profile's $\Delta_j$ is measured from the full model, not from the current partial model---but it provides a useful diagnostic. Large discrepancies between expected and actual marginal gains are strong signals of interaction effects that warrant further investigation.

### 12.4.3 Order Dependence

The greedy ordering is not necessarily unique. When two candidate dimensions produce similar MAE improvements at a given step, the algorithm breaks ties arbitrarily (in practice, by iteration order). Different starting dimensions can also produce different orderings.

This order dependence is a *feature*, not a bug. It reflects genuine structure in the interaction landscape. When the ordering is stable---when the same dimension is chosen first regardless of the starting point---the interaction structure is dominated by that dimension's strong main effect. When the ordering is unstable---when small perturbations in the starting point or evaluation function produce different orderings---the interaction structure is more complex, with multiple dimensions of comparable importance that interact in non-trivial ways.

To probe order dependence, run the compositional test from multiple starting dimensions and compare the resulting orderings. If all orderings agree on the first two or three dimensions, those dimensions constitute a robust "core" of the model. If orderings diverge, the model has multiple roughly equivalent compositional structures, and the choice among them is a modeling decision rather than a empirical one.

---

## 12.5 Connection to Sensitivity Profiling

### 12.5.1 Ablation as a Special Case

Sensitivity profiling (Chapter 9) and compositional testing are two perspectives on the same underlying question: how does model behavior depend on dimension membership? The connection is precise.

Sensitivity profiling *removes* dimensions from a full model one at a time. It answers: "Given everything, what happens when we lose this?" The result is a vector of individual importance scores.

Compositional testing *adds* dimensions to an empty (or minimal) model one at a time. It answers: "Given nothing, what happens when we gain this?" The result is an ordered construction sequence.

These are dual perspectives. In a purely additive model---one where $\Phi_{ij} = 0$ for all pairs---the sensitivity ranking and the compositional ordering are exact reverses of each other: the most important dimension to remove is the most important to add. In a model with interactions, they diverge, and the divergence is precisely the interaction structure.

### 12.5.2 The Pipeline Integration

The structural fuzzing pipeline runs both analyses as part of a complete campaign. Examining the pipeline orchestration reveals the design:

```python
def run_campaign(
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    ...
) -> StructuralFuzzReport:
    ...
    # Step 3: Sensitivity profiling (uses best result's params)
    sensitivity_results = sensitivity_profile(
        params=best_params,
        dim_names=dim_names_list,
        evaluate_fn=evaluate_fn,
        inactive_value=inactive_value,
    )

    ...

    # Step 6: Compositional testing
    composition_result = compositional_test(
        start_dim=start_dim,
        candidate_dims=candidate_dims_list,
        dim_names=dim_names_list,
        evaluate_fn=evaluate_fn,
        inactive_value=inactive_value,
        n_grid=n_grid,
        n_random=n_random,
    )
    ...
```

The pipeline runs sensitivity profiling at step 3 and compositional testing at step 6. This ordering is intentional. The sensitivity profile uses the best parameter vector found during subset enumeration (step 1), while the compositional test starts from a user-specified dimension and builds up. The two analyses operate from opposite ends of the dimension space: sensitivity starts from the top and removes; composition starts from the bottom and adds.

The `StructuralFuzzReport` stores both results, enabling post-hoc comparison:

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

An analyst examining the report can compare the sensitivity ranking (which dimensions are most important to *keep*) with the compositional ordering (which dimensions are most important to *add*). Agreement between the two provides confidence in a clean, additive dimension structure. Disagreement signals interaction effects that require the interaction matrix analysis of Section 12.2 to resolve.

### 12.5.3 Reconciling the Two Views

When sensitivity and composition disagree, the reconciliation procedure is:

1. Identify the dimensions whose ranks differ by more than one position between the sensitivity ranking and the compositional ordering.
2. For each such dimension, compute the pairwise interaction terms $\Phi_{ij}$ between that dimension and all others.
3. Large positive $\Phi_{ij}$ values explain cases where the dimension ranks high in the compositional order but low in the sensitivity ranking: it is synergistic with early-added dimensions, so it appears important when building up but appears dispensable (because its partners are present) when ablating from the top.
4. Large negative $\Phi_{ij}$ values explain the reverse: the dimension appears important individually (high sensitivity rank) but redundant when combined with others (low compositional rank).

This reconciliation procedure transforms a confusing disagreement between two analyses into a structured understanding of the interaction landscape.

---

## 12.6 Practical Patterns

### 12.6.1 Choosing the Starting Dimension

The `compositional_test` function requires a `start_dim` parameter. This choice affects the resulting ordering and can bias the analysis. Three strategies are common:

**Start from the most important dimension.** Use the sensitivity profile to identify the dimension with the largest $\Delta_i$ and start the compositional test there. This produces an ordering that begins with the strongest main effect and reveals how subsequent dimensions complement it. It is the default strategy and the most interpretable for practitioners.

**Start from the least important dimension.** Starting from the weakest dimension reveals whether apparently weak dimensions become important in combination. If the greedy algorithm selects unexpected dimensions early in the sequence, the model has strong interactions that sensitivity profiling would miss.

**Start from each dimension in turn.** Run $n$ compositional tests, one from each starting dimension, and compare the orderings. This is the most thorough approach and directly reveals order dependence (Section 12.4.3). The cost is $n$ times higher, but for models with $n \leq 10$ it remains practical.

The pipeline's default behavior uses `start_dim=0`, which corresponds to the first dimension in the names list. For a thorough analysis, the pipeline supports overriding this parameter, and running multiple compositional tests with different starting points is recommended when the interaction structure is unknown.

### 12.6.2 Detecting Emergent Dimensions

An *emergent dimension* is one whose compositional marginal gain far exceeds its individual ablation delta. Formally, if the marginal gain of adding dimension $j$ at step $k$ is $G_j^{(k)}$ and the ablation delta is $\Delta_j$, then the emergence ratio is:

$$E_j = \frac{G_j^{(k)}}{\Delta_j}$$

An emergence ratio substantially greater than 1.0 indicates that dimension $j$ is synergistic with the currently active set. Ratios greater than 2.0 are noteworthy; ratios greater than 5.0 indicate strong emergent behavior that demands investigation.

Emergence often arises in models where dimensions encode different *aspects* of the same underlying phenomenon. A model predicting material failure might have one dimension for stress and another for temperature. Neither alone predicts failure well (both have low $\Delta$), but together they define the stress-temperature failure envelope: a region in the joint space where failure probability is high. The emergence ratio captures this synergy quantitatively.

### 12.6.3 Diagnosing Redundancy Clusters

When a group of dimensions are mutually redundant, the compositional test reveals this as a cluster of diminishing marginal gains. After the first dimension in the cluster is added, subsequent cluster members contribute very little because their information is already represented.

To identify redundancy clusters from the compositional result:

1. Compute the marginal gain $G_j$ for each step.
2. Compute the ratio $R_j = G_j / \Delta_j$ (gain relative to individual importance).
3. Group consecutive dimensions with $R_j < 0.3$ (or another threshold) into clusters.

Each cluster represents a set of dimensions that are largely interchangeable. The model could use any one of them as a representative, reducing dimensionality without significant loss of information. This directly connects to the dimensionality reduction motivation of Chapter 5's Pareto analysis: redundancy clusters are the mechanism by which models achieve good performance with fewer dimensions.

---

## 12.7 A Geometric Interpretation

### 12.7.1 The Composition Path in Evaluation Space

Each step of the compositional test produces a point in the evaluation space: a (dimensionality, MAE) pair. The sequence of points traces a *composition path* from the starting dimension to the full model. This path is a one-dimensional curve through the $n$-dimensional parameter space, projected onto the two-dimensional (dimensionality, MAE) plane.

The geometry of this path encodes interaction information:

- **Steep descent** from step $k$ to step $k+1$ indicates strong synergy between the newly added dimension and the current active set.
- **Shallow descent** indicates near-independence or mild redundancy.
- **Plateau** indicates complete redundancy: the new dimension adds no information.
- **Ascent** (MAE increases) is theoretically possible if re-optimization of the expanded set finds a worse optimum than the restricted set. In practice, this is rare because the search space strictly expands with each added dimension, but it can occur with random search in high dimensions where the search budget is insufficient.

### 12.7.2 Composition Paths and the Pareto Frontier

The composition path can be overlaid on the Pareto frontier from Chapter 5. Pareto-optimal points represent the best possible MAE for each dimensionality, while the composition path represents the MAE achieved by a particular greedy construction. The gap between the composition path and the Pareto frontier measures the cost of the greedy approximation: how much worse the greedy ordering is compared to the optimal subset at each dimensionality.

If the composition path lies close to the Pareto frontier at every step, the greedy algorithm is performing well---the interaction structure is sufficiently captured by the greedy choices. If the composition path deviates significantly from the Pareto frontier at some step, the greedy algorithm has made a suboptimal choice at that point, and the interaction structure contains non-greedy features (e.g., a triple of dimensions that is strong as a unit but whose pairwise components are weak).

This comparison provides a calibration of the compositional test's reliability. When the gap is small, the compositional ordering can be trusted as a faithful representation of the dimension importance hierarchy. When the gap is large, the full combinatorial analysis of Chapter 11 is needed to understand the true structure.

### 12.7.3 The Interaction Matrix as a Metric Tensor

There is a deeper geometric interpretation of the interaction matrix $\Phi$ that connects to the Riemannian framework of Chapters 6 and 9. Consider the space of *dimension activation vectors* $\mathbf{a} \in \{0, 1\}^n$, where $a_i = 1$ indicates that dimension $i$ is active. The evaluation function restricted to this discrete space defines a function $f : \{0, 1\}^n \to \mathbb{R}$.

If we approximate $f$ by a second-order expansion around the all-active point $\mathbf{a} = \mathbf{1}$:

$$f(\mathbf{a}) \approx f(\mathbf{1}) - \sum_i \Delta_i (1 - a_i) + \frac{1}{2} \sum_{i \neq j} \Phi_{ij} (1 - a_i)(1 - a_j)$$

the interaction matrix $\Phi$ plays the role of a metric tensor on the discrete activation space. It defines how "distance" in the activation space translates to distance in the evaluation space. Directions of strong synergy ($\Phi_{ij} > 0$) are directions along which the evaluation landscape curves upward (removing both dimensions is more damaging than expected); directions of redundancy ($\Phi_{ij} < 0$) are directions along which it curves downward.

This is not merely an analogy. When the discrete activation space is relaxed to a continuous space $\mathbf{a} \in [0, 1]^n$ (replacing binary on/off with continuous weighting), the interaction matrix becomes a genuine metric tensor on that space, and the compositional test traces a geodesic-like path through the space: at each step it moves in the direction of steepest descent as measured by this metric.

---

## 12.8 Limitations and Extensions

### 12.8.1 Greedy Suboptimality

The compositional test is greedy: at each step, it adds the single best dimension without lookahead. This can fail when the optimal sequence requires adding a dimension that is individually suboptimal but enables a strong subsequent addition. For example, if dimensions B and C are strongly synergistic but individually weak, the greedy algorithm will never discover their combination because it will always prefer individually stronger dimensions A and D at the first two steps.

The full subset enumeration of Chapter 11 does not suffer from this limitation---it tests all combinations---but it is exponentially more expensive. A practical middle ground is *beam search*: at each step, retain the top $b$ candidates (not just the best one) and continue from each. With beam width $b = 3$, the cost increases by a factor of 3 but the algorithm can discover dimension combinations that are invisible to the purely greedy approach.

### 12.8.2 Sensitivity to Starting Point

As discussed in Section 12.6.1, the starting dimension affects the resulting ordering. More subtly, the starting dimension determines the *evaluation baseline* for all subsequent marginal gains. Starting from a strong dimension means that subsequent gains are measured against a strong baseline, making them appear smaller. Starting from a weak dimension means that gains are measured against a weak baseline, making them appear larger.

This is not a bias in the statistical sense---both orderings are correct descriptions of the greedy construction from their respective starting points---but it means that marginal gains from different starting points are not directly comparable. When comparing orderings from different starting points, compare the MAE values at each step, not the marginal gains.

### 12.8.3 Scaling to High Dimensions

The quadratic cost of the compositional test ($O(n^2)$ calls to `optimize_subset`) makes it tractable for $n \leq 20$ but expensive beyond that. For high-dimensional spaces, two strategies reduce the cost:

1. **Pre-screening.** Use the sensitivity profile to identify the top $k$ dimensions (by $\Delta_i$) and run the compositional test only on those $k$ dimensions, with $k \ll n$. Dimensions that have negligible individual sensitivity are unlikely to participate in strong interactions.

2. **Block composition.** Group related dimensions into blocks (e.g., all Halstead metrics into a single "Halstead block") and run the compositional test at the block level. This reduces $n$ to the number of blocks and captures inter-block interactions while ignoring intra-block structure.

Both strategies sacrifice completeness for tractability. The structural fuzzing framework supports both through the `candidate_dims` parameter of `compositional_test`, which allows the caller to restrict the search to a subset of dimensions.

---

## 12.9 Summary

Compositional testing addresses a fundamental gap in single-dimension analysis: the interaction structure between dimensions. The key contributions of this chapter are:

1. **The interaction matrix** $\Phi_{ij}$, which decomposes multi-dimensional model behavior into additive, synergistic, and redundant components. Positive entries indicate synergy (dimensions complement each other); negative entries indicate redundancy (dimensions overlap).

2. **The greedy compositional algorithm**, implemented as `compositional_test` in the structural fuzzing framework, which constructs an efficient dimension-addition ordering with quadratic cost. At each step, all active dimensions are re-optimized jointly, capturing cross-dimensional adjustments that sequential approaches miss.

3. **The MAE sequence**, which encodes marginal gains, diminishing returns, and interaction signatures in a single, interpretable output. The composition path traced by this sequence can be compared to the Pareto frontier to calibrate the greedy algorithm's quality.

4. **The duality with sensitivity profiling.** Ablation from the top and composition from the bottom are dual views of the same landscape. Their agreement signals additive structure; their disagreement reveals interactions. The pipeline runs both analyses and stores both results for systematic comparison.

5. **The geometric interpretation.** The interaction matrix functions as a metric tensor on the dimension activation space, encoding how curvature in the activation space maps to curvature in the evaluation space. Compositional testing traces an approximately geodesic path through this space.

The analysis developed in this chapter is *local*: it characterizes interactions around a specific baseline configuration (for ablation) or along a specific greedy path (for composition). It does not guarantee that the interaction structure is the same in other regions of the parameter space. For models with strongly nonlinear evaluation functions, interactions can appear and disappear as the baseline moves. Chapter 13 extends the analysis by examining how compositional structures change under perturbation, connecting the local interaction picture to the global robustness framework developed in Chapter 7.

---

## 12.10 Exercises

**12.1.** Given a model with four dimensions and the following ablation deltas: $\Delta_A = 1.0$, $\Delta_B = 0.5$, $\Delta_C = 0.3$, $\Delta_D = 0.1$, and the pairwise ablation results $f(\mathbf{x}^{(-AB)}) - f(\mathbf{x}) = 2.0$, $f(\mathbf{x}^{(-AC)}) - f(\mathbf{x}) = 1.2$, $f(\mathbf{x}^{(-AD)}) - f(\mathbf{x}) = 1.1$, compute the interaction matrix entries $\Phi_{AB}$, $\Phi_{AC}$, and $\Phi_{AD}$. Classify each pair as synergistic, additive, or redundant.

**12.2.** Run `compositional_test` on a five-dimensional evaluation function of your choice with three different starting dimensions. Compare the orderings. What do the differences (or lack thereof) tell you about the interaction structure?

**12.3.** Prove that for a purely additive model (where $f(\mathbf{x}) = \sum_i g_i(x_i)$ for independent functions $g_i$), the interaction matrix $\Phi_{ij} = 0$ for all $i \neq j$, and the compositional ordering is the reverse of the sensitivity ranking.

**12.4.** Consider a model where $\Phi_{AB} = +2.0$ (strong synergy) but both $\Delta_A < 0.1$ and $\Delta_B < 0.1$ (individually unimportant). Explain why the greedy compositional algorithm starting from dimension C will never discover this synergy. Propose a modification to the algorithm that would detect it.

**12.5.** The cost of the compositional test is $O(n^2)$ while full subset enumeration is $O(2^n)$. For what range of $n$ is the compositional test at least 10x cheaper? Derive the crossover point exactly.

---

*Chapter 13 extends the compositional framework by examining how interaction structures respond to perturbation. Where this chapter asks "which dimensions interact?", Chapter 13 asks "how stable are those interactions?"---connecting the local composition picture developed here to the global robustness analysis of the full campaign pipeline.*
