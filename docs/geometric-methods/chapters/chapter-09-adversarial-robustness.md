# Chapter 9: Adversarial Robustness and the Model Robustness Index

> *"The question is not whether the bridge will hold under the load it was designed for. The question is how much more it will hold before it fails."*
> --- Henry Petroski, *Design Paradigms* (1994)

A model that performs well on the data it was fitted to has answered only the first question. The second question---how far its parameters can deviate before predictions become unacceptable---is equally important and almost universally neglected. Cross-validation tells you how the model generalizes to new data drawn from the same distribution. It tells you nothing about what happens when the parameters themselves are uncertain, quantized, transferred across domains, or simply estimated with finite precision. This chapter develops three complementary tools for answering the second question: the Model Robustness Index (MRI), sensitivity profiling via ablation, and adversarial threshold search.

The central claim is that **robustness is a geometric property of the loss landscape**, not a property of the data. Two models with identical cross-validation scores can occupy fundamentally different terrain: one sits in a broad valley where perturbations produce gentle degradation; the other perches on a narrow ridge where the slightest push sends it over the edge. The tools in this chapter distinguish between these two situations with precision.

---

## 9.1 Why Robustness Matters Beyond Accuracy

### 9.1.1 The Sharp Minimum Problem

Consider a geometric model with $d$ parameters $\boldsymbol{\theta} = (\theta_1, \ldots, \theta_d)$ fitted by minimizing a loss function $\mathcal{L}(\boldsymbol{\theta})$. The fitted parameters $\boldsymbol{\theta}^*$ sit at (or near) a minimum of $\mathcal{L}$. But not all minima are created equal. The Hessian $\mathbf{H} = \nabla^2 \mathcal{L}(\boldsymbol{\theta}^*)$ characterizes the local curvature: large eigenvalues correspond to directions where the loss increases sharply; small eigenvalues correspond to directions where the loss is nearly flat.

A *sharp minimum* has large eigenvalues in many directions---the model's predictions are highly sensitive to parameter changes. A *broad minimum* has small eigenvalues---the model tolerates perturbation gracefully. Standard training procedures, including cross-validation, are blind to this distinction. They evaluate $\mathcal{L}(\boldsymbol{\theta}^*)$ at the minimum, not the shape of $\mathcal{L}$ in its neighborhood.

The practical consequences are immediate. In deployment, parameters may be:

- **Quantized** (reducing floating-point precision for efficiency), introducing rounding errors of magnitude $\epsilon_q \sim 10^{-4}$ to $10^{-2}$.
- **Estimated from noisy data**, carrying statistical uncertainty that propagates through the optimization.
- **Transferred across domains**, where the optimal parameters differ from those learned on the source distribution.
- **Approximated for speed**, as in pruning or distillation.

In all these scenarios, a model sitting in a sharp minimum will fail unpredictably, while a model in a broad minimum will degrade gracefully. Structural fuzzing gives you the tools to distinguish the two *before* deployment, not after.

### 9.1.2 The Limitations of Standard Deviation

The obvious approach to quantifying sensitivity is to perturb the parameters, measure the resulting errors, and report the standard deviation. This is better than nothing, but it has a fundamental limitation: standard deviation treats all deviations symmetrically. A perturbation that improves the model by 2.0 and one that degrades it by 2.0 contribute equally to the standard deviation. But from a risk perspective, they are not equivalent. The improvement is pleasant; the degradation may be catastrophic.

Worse, standard deviation is dominated by the bulk of the distribution. If 95% of perturbations produce small deviations and 5% produce enormous ones, the standard deviation will look moderate---reassuringly so---while the model harbors dangerous failure modes in its tail. What we need is a summary statistic that is *explicitly sensitive to tail behavior*: one that asks not just "how much do perturbations affect the model on average?" but "how bad can it get?"

This is precisely what the Model Robustness Index provides.

---

## 9.2 The Model Robustness Index (MRI)

The MRI is the core scalar summary of a model's robustness under parameter perturbation. Its design reflects two principles: perturbations should be multiplicative (not additive), and the index should weight tail behavior explicitly.

### 9.2.1 The Perturbation Model

Given a baseline parameter vector $\boldsymbol{\theta} \in \mathbb{R}^d$, we generate perturbed versions by multiplying each parameter by an independent log-normal factor:

$$\theta_i^{(\text{pert})} = \theta_i \cdot \exp(\epsilon_i), \quad \epsilon_i \sim \mathcal{N}(0, \sigma^2)$$

where $\sigma$ (the `scale` parameter, default 0.5) controls the perturbation magnitude. The perturbed values are clamped to $[0.001, 10^6]$ to prevent numerical pathologies.

The choice of multiplicative perturbation is not arbitrary. Additive perturbation treats a parameter with value 0.01 and a parameter with value 1000 identically---both receive noise of the same absolute magnitude. This makes no geometric sense. A perturbation of $\pm 1$ is catastrophic for the former and negligible for the latter. Multiplicative perturbation respects the natural scale of each parameter: the relative change $\theta_i^{(\text{pert})} / \theta_i = \exp(\epsilon_i)$ is independent of $\theta_i$. In the language of differential geometry, we are perturbing in the coordinate system of the positive reals, where the invariant metric is $ds = d\theta / \theta$---the log-space metric.

With $\sigma = 0.5$, a one-standard-deviation perturbation multiplies (or divides) each parameter by $e^{0.5} \approx 1.65$---a 65% relative change. This is large enough to explore beyond the immediate neighborhood of $\boldsymbol{\theta}^*$ but small enough that many perturbations remain in a regime where the model still functions. The default has proven effective across a range of geometric models, but practitioners should report MRI values at multiple scales for thorough characterization.

The implementation in `compute_mri` makes this concrete:

```python
def compute_mri(
    params: np.ndarray,
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    n_perturbations: int = 300,
    scale: float = 0.5,
    weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
    rng: np.random.Generator | None = None,
) -> ModelRobustnessIndex:
```

The `evaluate_fn` callback takes a parameter vector and returns a tuple of `(mae, per_target_errors)`. This abstraction decouples the robustness computation from any specific model---any system that maps parameters to predictions and predictions to errors can be tested.

For each of $N$ perturbation samples (default 300), the function generates a perturbed parameter vector, evaluates the model, and records the deviation from baseline:

```python
for _ in range(n_perturbations):
    noise = rng.normal(0.0, scale, size=params.shape)
    params_pert = params * np.exp(noise)
    params_pert = np.clip(params_pert, 0.001, 1e6)

    pert_mae, _ = evaluate_fn(params_pert)
    omega = abs(pert_mae - base_mae)
    omegas.append(omega)
```

Each $\omega_i = |\text{MAE}_{\text{perturbed}} - \text{MAE}_{\text{baseline}}|$ measures how much the $i$-th perturbation destabilized the model. The collection $\{\omega_1, \ldots, \omega_N\}$ is the empirical *perturbation sensitivity distribution*.

### 9.2.2 The MRI Formula

The MRI is a weighted combination of three statistics of the $\omega$ distribution:

$$\text{MRI} = w_0 \cdot \bar{\omega} + w_1 \cdot P_{75}(\omega) + w_2 \cdot P_{95}(\omega)$$

with default weights $(w_0, w_1, w_2) = (0.5, 0.3, 0.2)$. The implementation is direct:

```python
omegas_arr = np.array(omegas)
mean_omega = float(np.mean(omegas_arr))
p75_omega = float(np.percentile(omegas_arr, 75))
p95_omega = float(np.percentile(omegas_arr, 95))

mri_value = weights[0] * mean_omega + weights[1] * p75_omega + weights[2] * p95_omega
```

**Lower MRI indicates a more robust model.** An MRI of zero would mean that no perturbation changed the model's error at all---perfect robustness. The result is packaged in a dataclass that preserves the full decomposition:

```python
@dataclass
class ModelRobustnessIndex:
    mri: float
    mean_omega: float
    p75_omega: float
    p95_omega: float
    n_perturbations: int
    worst_case_mae: float
    perturbation_errors: list[float]
```

The `worst_case_mae` field tracks the single highest MAE observed across all perturbations---a useful diagnostic that the composite MRI intentionally softens. If `worst_case_mae` is dramatically higher than the baseline MAE, the model has at least one catastrophic failure mode, even if the composite MRI is moderate.

### 9.2.3 Why Weighted Tail Statistics Beat Standard Deviation

The three-component formula deserves careful justification. Why not simply report $\text{std}(\omega)$?

**The mean anchors the index to average behavior.** A model that is moderately fragile across the board will have a high $\bar{\omega}$. This captures the "typical" perturbation response.

**The 75th percentile captures systematic tail behavior.** If 25% of perturbations cause substantial degradation, $P_{75}$ will be elevated. This is the signature of a model where a subset of parameters (or parameter directions) is particularly sensitive---a common pattern when the loss landscape has a few steep directions and many flat ones.

**The 95th percentile captures near-worst-case behavior without being as volatile as the maximum.** The maximum of $N$ samples from a heavy-tailed distribution grows unboundedly with $N$; the 95th percentile converges. Using $P_{95}$ instead of $\max(\omega)$ makes the index stable across different values of $N$, which is essential for reproducibility.

**The weights sum to 1.0**, making the MRI interpretable on the same scale as the individual $\omega$ values. If the mean deviation is 0.8, the 75th percentile is 1.4, and the 95th percentile is 3.1, the MRI is:

$$\text{MRI} = 0.5 \times 0.8 + 0.3 \times 1.4 + 0.2 \times 3.1 = 0.40 + 0.42 + 0.62 = 1.44$$

The standard deviation of the same $\omega$ distribution might be 0.9---a number that conceals the heavy tail. The MRI reveals that while typical perturbations cause modest degradation ($\bar{\omega} = 0.8$), the worst 5% of perturbations cause error increases exceeding 3.1. This tail information is precisely what a deployment decision requires.

The formula can also be understood as an approximation to the Conditional Value at Risk (CVaR), a standard risk measure in financial mathematics. CVaR at level $\alpha$ is the expected loss in the worst $\alpha$-fraction of scenarios. The MRI's weighted combination of mean and tail percentiles roughly approximates a CVaR-weighted average, blending expected loss with conditional expectations in the upper tail. This connection to risk theory is not accidental: robustness testing *is* risk assessment, applied to computational models rather than financial portfolios.

### 9.2.4 Adjusting the Weights

The default weights $(0.5, 0.3, 0.2)$ balance average and tail behavior. They are appropriate for general-purpose assessment, but different applications may warrant different emphasis:

| Application | Suggested Weights | Rationale |
|---|---|---|
| Exploratory analysis | $(0.7, 0.2, 0.1)$ | Emphasize typical behavior |
| Production deployment | $(0.5, 0.3, 0.2)$ | Balance average and tail |
| Safety-critical systems | $(0.2, 0.3, 0.5)$ | Emphasize worst-case |
| Regulatory compliance | $(0.1, 0.2, 0.7)$ | Dominated by tail risk |

Because the `ModelRobustnessIndex` dataclass returns all three components alongside the composite score, users can always recompute the MRI with alternative weights without rerunning the perturbation experiment.

---

## 9.3 Sensitivity Profiling: Which Parameters Matter?

The MRI tells you *how robust* the model is globally. Sensitivity profiling tells you *which parameters are responsible*. The method is ablation: for each dimension, set its value to an inactive sentinel and measure the resulting degradation.

### 9.3.1 The Ablation Protocol

For each dimension $i$, set $\theta_i$ to the sentinel value (by default, $10^6$---a value large enough to effectively remove the dimension's influence) and evaluate the model. The sensitivity delta is:

$$\Delta_i = \text{MAE}(\boldsymbol{\theta} \text{ with } \theta_i = \text{inactive}) - \text{MAE}(\boldsymbol{\theta})$$

The implementation is concise:

```python
def sensitivity_profile(
    params: np.ndarray,
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    inactive_value: float = 1e6,
) -> list[SensitivityResult]:
```

The function iterates over all dimensions, ablates each in turn, and measures the change in MAE:

```python
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
            importance_rank=0,  # assigned below
        )
    )

results.sort(key=lambda r: r.delta_mae, reverse=True)
for rank, r in enumerate(results, 1):
    r.importance_rank = rank
```

Results are sorted by $\Delta$ in descending order and assigned importance ranks. Rank 1 is the most important dimension---the one whose ablation causes the largest increase in error.

### 9.3.2 Interpreting the Sensitivity Profile

A large positive $\Delta_i$ means that dimension $i$ is carrying significant predictive load: removing it substantially degrades the model. A near-zero $\Delta_i$ means the dimension contributes almost nothing---it is a candidate for removal (simplifying the model without meaningful accuracy loss, as the Pareto analysis of Chapter 8 would confirm).

A *negative* $\Delta_i$---where removing the dimension actually *improves* the model---is the most informative signal of all. It indicates that the parameter value for dimension $i$ has drifted to a harmful configuration, either through overfitting during optimization or through an interaction effect where the dimension's presence degrades other dimensions' contributions. Negative deltas warrant immediate investigation.

### 9.3.3 Relationship to the MRI

Sensitivity profiling and the MRI answer complementary questions. The MRI says: "the model is fragile." The sensitivity profile says: "*these* dimensions are responsible." Together, they provide both the diagnosis and the prescription:

1. Compute the MRI. If it is low, the model is robust and further investigation may not be needed.
2. If the MRI is high, run the sensitivity profile. The top-ranked dimensions are where fragility concentrates.
3. For the top-ranked dimensions, run adversarial threshold search (Section 9.4) to find the exact breaking points.

This three-stage workflow is exactly how `run_campaign` in the pipeline module orchestrates the analysis, as we will see in Section 9.5.

### 9.3.4 Limitations of One-at-a-Time Ablation

One-at-a-time ablation captures *marginal* importance: how much does each dimension contribute when all others are present? It does not capture *interaction effects*: the case where dimensions $i$ and $j$ are individually unimportant but jointly critical (their information is redundant, and either one alone suffices). The subset enumeration of Chapter 4 and the compositional testing of Section 9.5 address this limitation by exploring multi-dimensional combinations. Sensitivity profiling is a fast screening step, not a complete analysis.

---

## 9.4 Adversarial Threshold Search: Finding the Tipping Points

While the MRI provides a global robustness summary and sensitivity profiling identifies the most important dimensions, adversarial threshold search finds the *exact* perturbation magnitudes where the model transitions from "working" to "broken." These are tipping points---the values where qualitative failure begins---and they are precisely the values that neither cross-validation nor global robustness summaries can reveal.

### 9.4.1 The Search Algorithm

For each dimension $i$ and each direction (increase and decrease), the algorithm performs a log-spaced search from the baseline value outward:

- **Increase direction:** search from $\theta_i$ to $\theta_i \times 1000$
- **Decrease direction:** search from $\theta_i$ to $\max(\theta_i / 1000, 10^{-6})$

At each step, the algorithm evaluates the model with the perturbed parameter and checks whether any prediction target's error has changed by more than the specified tolerance $\tau$.

```python
def find_adversarial_threshold(
    params: np.ndarray,
    dim: int,
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    tolerance: float = 0.5,
    n_steps: int = 50,
) -> list[AdversarialResult]:
```

The search uses `np.logspace` to generate test values, ensuring uniformity in log-space---consistent with the multiplicative perturbation philosophy of the MRI:

```python
for direction in ("increase", "decrease"):
    if direction == "increase":
        search_values = np.logspace(
            np.log10(base_value),
            np.log10(base_value * 1000),
            n_steps,
        )
    else:
        low = max(base_value / 1000, 1e-6)
        search_values = np.logspace(
            np.log10(base_value),
            np.log10(low),
            n_steps,
        )

    for test_value in search_values[1:]:  # skip the first (baseline)
        perturbed = params.copy()
        perturbed[dim] = test_value
        _, pert_errors = evaluate_fn(perturbed)

        for target_name in base_errors:
            if target_name in pert_errors:
                delta = abs(pert_errors[target_name] - base_errors[target_name])
                if delta > tolerance:
                    ratio = test_value / base_value
                    results.append(
                        AdversarialResult(
                            dim=dim,
                            dim_name=dim_names[dim],
                            base_value=base_value,
                            threshold_value=test_value,
                            threshold_ratio=ratio,
                            target_flipped=target_name,
                            direction=direction,
                        )
                    )
                    break
```

The `for/else/continue/break` pattern in the full implementation deserves a note: the inner `break` exits the target loop when a threshold is found, and the outer `break` (after the `else: continue`) exits the search-values loop to move to the next direction. This ensures we find the *first* threshold in each direction---the tipping point closest to the baseline.

### 9.4.2 The Threshold Ratio

Each `AdversarialResult` records the `threshold_ratio`: the multiplicative factor by which the parameter had to change before a target broke. This is the most immediately interpretable quantity:

- A ratio of **1.5** means the parameter only needed to increase by 50% before a target exceeded tolerance. The model is fragile along this dimension.
- A ratio of **200** means the parameter had to be multiplied by 200 before anything broke. The model is resilient along this dimension.
- A ratio of **0.1** (in the decrease direction) means the parameter had to be reduced to 10% of its baseline value before failure. The model tolerates substantial downward perturbation.

Parameters with low threshold ratios in either direction are the ones that demand the most careful estimation, the tightest confidence intervals, and the most conservative deployment practices. Parameters with high threshold ratios can tolerate rough approximation.

### 9.4.3 Per-Target Sensitivity

The `target_flipped` field in the result reveals *which specific prediction target* was the first to exceed tolerance. This often exposes unexpected couplings. A parameter that nominally controls one aspect of the model may turn out to critically affect a seemingly unrelated prediction. These cross-dimension dependencies are exactly the coupling effects that one-output-at-a-time analysis tends to miss, and they are among the most valuable findings adversarial threshold search can produce.

### 9.4.4 Choosing the Tolerance

The `tolerance` parameter defines the boundary between "acceptable" and "broken." This is inherently application-specific:

- For a model predicting physical measurements, tolerance might correspond to the instrument's measurement uncertainty.
- For a classification system, it might be the minimum confidence margin for a correct decision.
- For the defect prediction example from Chapter 1, it might be the maximum acceptable change in per-module error before the model's predictions are no longer actionable.

Setting tolerance too low produces false positives (thresholds that flag inconsequential changes); setting it too high misses genuine failure modes. A disciplined approach is to derive tolerance from the application's error budget or from domain-specific standards.

### 9.4.5 Computational Cost

Adversarial threshold search evaluates the model $2 \times n\_steps \times d$ times in the worst case (two directions per dimension, $n\_steps$ search values per direction, $d$ dimensions). With the default $n\_steps = 50$ and a 5-dimensional model, this is 500 evaluations. For expensive models, this can be reduced by:

1. Searching only the top-$k$ dimensions identified by sensitivity profiling (Section 9.3), rather than all $d$ dimensions.
2. Reducing $n\_steps$ at the cost of coarser threshold estimates.
3. Using a two-phase approach: a coarse scan to bracket the threshold, followed by a fine scan to refine it.

---

## 9.5 The Pipeline: Composing the Three Tools

The MRI, sensitivity profiling, and adversarial threshold search are designed to compose into a unified campaign. The `run_campaign` function in the pipeline module orchestrates this composition, executing the tools in the correct order and threading the results of earlier stages into later ones.

### 9.5.1 Campaign Architecture

The campaign proceeds in six stages. Stages 3 through 5 are the robustness tools developed in this chapter:

```python
def run_campaign(
    dim_names: Sequence[str],
    evaluate_fn: Callable[[np.ndarray], tuple[float, dict[str, float]]],
    max_subset_dims: int = 4,
    n_mri_perturbations: int = 300,
    mri_scale: float = 0.5,
    mri_weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
    ...
) -> StructuralFuzzReport:
```

The stages are:

1. **Subset enumeration** (Chapter 4): Test all dimension combinations up to a maximum size.
2. **Pareto frontier** (Chapter 8): Extract the non-dominated configurations from the enumeration results.
3. **Sensitivity profiling** (this chapter): Ablate each dimension from the best configuration to rank importance.
4. **MRI computation** (this chapter): Perturb the best configuration to quantify global robustness.
5. **Adversarial threshold search** (this chapter): Find the tipping points for every dimension.
6. **Compositional testing**: Verify that dimensions compose well when added incrementally.

The key design decision is that stages 3--5 operate on the *best configuration found by the enumeration*. This means the robustness analysis characterizes the model at its optimal operating point---the configuration a practitioner would actually deploy. The pipeline extracts the best parameters and passes them to each robustness tool:

```python
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

mri_result = compute_mri(
    params=best_params,
    evaluate_fn=evaluate_fn,
    n_perturbations=n_mri_perturbations,
    scale=mri_scale,
    weights=mri_weights,
)

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
```

### 9.5.2 The Campaign Report

All results are collected into a `StructuralFuzzReport` dataclass:

```python
@dataclass
class StructuralFuzzReport:
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

The report is a complete, machine-readable artifact that captures every aspect of the structural fuzzing campaign. Its `summary()` method generates a human-readable text report. But the real value is in the structured data: downstream analysis can query the report programmatically, computing derived quantities (e.g., the ratio of adversarial threshold to MRI, or the correlation between sensitivity rank and threshold ratio) without re-running the campaign.

### 9.5.3 Robustness Testing the Pareto Frontier

A natural extension---not yet automated in the pipeline but straightforward to implement---is to compute the MRI for every Pareto-optimal configuration, not just the best one. This answers a question that Chapter 8's Pareto analysis alone cannot: among the non-dominated tradeoffs between accuracy and complexity, *which are the most robust?*

It is entirely possible (and in practice common) that the Pareto-optimal configuration with the lowest MAE is also the most fragile. A 3-dimension configuration at MAE 1.7 might have MRI 0.3, while the 5-dimension configuration at MAE 1.5 has MRI 1.8. The 0.2 improvement in MAE comes at the cost of a 6x increase in fragility. A practitioner who saw only the Pareto frontier would choose the 5-dimension model; a practitioner who also saw the MRI values would think twice.

---

## 9.6 The Defect Prediction Example, Revisited

Chapter 1 introduced a software defect prediction model with five feature groups (Size, Complexity, Halstead, Object-Orientation, Process) and walked through the geometric analysis at a high level. We now return to this example with the full machinery of this chapter, showing what the MRI, sensitivity profile, and adversarial threshold search reveal in concrete detail.

### 9.6.1 Sensitivity Profile

The sensitivity profile, computed by ablating each of the five dimensions from the best configuration, might produce results like:

| Rank | Dimension | $\Delta$ MAE | MAE without |
|:---:|---|:---:|:---:|
| 1 | Complexity | +1.9 | 3.6 |
| 2 | Process | +1.2 | 2.9 |
| 3 | Size | +0.6 | 2.3 |
| 4 | OO | +0.15 | 1.85 |
| 5 | Halstead | +0.08 | 1.78 |

The model depends overwhelmingly on Complexity and Process. Size contributes modestly. OO and Halstead are nearly redundant---removing either barely changes the model's error. This confirms the intuition from Chapter 1's Pareto analysis, where the {Complexity, Process} two-dimensional subset achieved MAE 2.1, capturing most of the accuracy of the full five-dimensional model at MAE 1.7.

But sensitivity profiling adds something the Pareto analysis could not: it tells us that the *specific parameter values* for OO and Halstead in the best configuration contribute almost nothing. This is stronger than saying the dimensions are unnecessary in principle (which is what Pareto analysis shows). It says they are unnecessary *at their current fitted values*, which has direct implications for model simplification and maintenance.

### 9.6.2 MRI Computation

Running `compute_mri` with 300 perturbations at scale 0.5 on the best configuration produces a perturbation sensitivity distribution. Consider the following hypothetical results:

| Statistic | Value |
|:---:|:---:|
| Mean $\bar{\omega}$ | 0.8 |
| 75th percentile $P_{75}$ | 1.4 |
| 95th percentile $P_{95}$ | 3.1 |
| **MRI** | **1.44** |
| Worst-case MAE | 5.2 |

The standard deviation of the $\omega$ distribution might be 0.9. A naive report would say "the model's sensitivity has standard deviation 0.9"---a number that sounds modest. The MRI of 1.44 tells a more complete story: the typical perturbation causes moderate degradation, but the 95th percentile deviation is 3.1, meaning that 5% of perturbations nearly *double* the model's error (from baseline 1.7 to approximately 4.8).

The worst-case MAE of 5.2 indicates that at least one perturbation tripled the error. This single data point is too volatile to build an index around (it would change dramatically with different random seeds), but it is a useful flag: somewhere in the parameter neighborhood, there exists a configuration that catastrophically degrades the model.

### 9.6.3 Adversarial Threshold Search

Running adversarial threshold search with tolerance 0.5 on each of the five dimensions produces results like:

| Dimension | Direction | Threshold Ratio | Target Flipped |
|---|---|:---:|---|
| Complexity | decrease | 0.30 | high-complexity modules |
| Process | increase | 4.2 | high-churn modules |
| Process | decrease | 0.12 | legacy modules |
| Size | decrease | 0.08 | small modules |

Several findings stand out:

1. **Complexity has a tipping point at 0.30x** its baseline value in the decrease direction. Reducing the Complexity parameter below 30% of its fitted value causes the model's error on high-complexity modules to exceed tolerance. This is the most dangerous finding: a refactoring initiative that reduces code complexity across the codebase could push the model past this threshold, silently degrading predictions on precisely the modules that refactoring aims to improve.

2. **Process is sensitive in both directions.** Increasing the Process parameter by 4.2x breaks predictions for high-churn modules; decreasing it to 12% of baseline breaks predictions for legacy modules. The model's handling of Process is well-calibrated at its current value but fragile on both sides.

3. **No threshold was found for OO or Halstead** in either direction across the full three-orders-of-magnitude search range. These dimensions are not only unimportant (as sensitivity profiling showed) but also non-fragile: the model is indifferent to their values. This is consistent with their low sensitivity ranks and further supports removing them from the model.

4. **The targets that flip are dimension-specific.** Complexity perturbation affects high-complexity modules; Process perturbation affects high-churn and legacy modules. The adversarial search has revealed the *coupling structure* between parameters and prediction targets---information that global metrics like the MRI cannot provide.

### 9.6.4 Synthesis

Combining all three tools, the defect prediction model's robustness profile is:

- **Global robustness (MRI = 1.44):** Moderately fragile. The model is not catastrophically sensitive, but 5% of perturbations produce substantial degradation.
- **Fragility concentrates in Complexity and Process.** These two dimensions carry 75% of the predictive load and harbor all identified tipping points.
- **Complexity has a critical threshold at 0.30x baseline.** This is the model's most dangerous vulnerability: a specific, plausible shift in the data distribution (reduced code complexity due to refactoring) could push the model past this threshold.
- **OO and Halstead are safe to remove.** They contribute almost nothing and have no adversarial thresholds---removing them simplifies the model without sacrificing accuracy or robustness.

None of these findings are available from accuracy, precision, recall, or F1. They required treating the model's behavior as a geometric object---a point in a multi-dimensional parameter space---and systematically probing the shape of the loss landscape around that point.

---

## 9.7 The Geometry of Robustness

### 9.7.1 Robustness as a Property of the Loss Landscape

The MRI can be connected to the local geometry of the loss landscape through the Hessian. For a quadratic loss surface near the minimum:

$$\mathcal{L}(\boldsymbol{\theta}^* + \boldsymbol{\delta}) \approx \mathcal{L}(\boldsymbol{\theta}^*) + \frac{1}{2} \boldsymbol{\delta}^\top \mathbf{H} \boldsymbol{\delta}$$

the expected squared deviation under Gaussian perturbation $\boldsymbol{\delta} \sim \mathcal{N}(0, \sigma^2 \mathbf{I})$ is:

$$\mathbb{E}[\omega^2] = \frac{\sigma^2}{2} \text{tr}(\mathbf{H})$$

In this regime, the MRI is approximately proportional to $\sqrt{\text{tr}(\mathbf{H})}$---the square root of the sum of eigenvalues of the Hessian. Large eigenvalues (sharp directions in the loss landscape) contribute disproportionately to the MRI, which is exactly the behavior we want: the MRI should be elevated when the landscape has even one sharp direction, because that direction represents a vulnerability.

But the approximation breaks down when the loss surface is non-quadratic---when it has asymmetric curvature, flat plateaus that transition into cliffs, or multiple local minima in the perturbation neighborhood. In these cases, the MRI's empirical sampling approach captures behavior that the Hessian analysis misses. The Hessian is a local linear approximation; the MRI is a global (within the perturbation radius) nonlinear probe. Both are useful, but the MRI is more general.

### 9.7.2 Directional Robustness

The MRI as defined is *isotropic*: perturbations are drawn uniformly in all parameter directions. This is appropriate as a screening tool, but it can be refined. If the sensitivity profile identifies dimension $i$ as critical, one can compute a *directional MRI* by perturbing only dimension $i$ while holding all others fixed. The comparison between the global MRI and the directional MRI for dimension $i$ reveals how much of the model's total fragility is attributable to that single dimension.

More generally, one can compute MRI along any direction $\mathbf{v}$ in parameter space by restricting perturbations to the one-dimensional subspace spanned by $\mathbf{v}$:

$$\boldsymbol{\theta}^{(\text{pert})} = \boldsymbol{\theta}^* + \epsilon \cdot \mathbf{v}, \quad \epsilon \sim \mathcal{N}(0, \sigma^2)$$

The directional MRI profile---MRI as a function of direction---is a scalar field on the unit sphere $S^{d-1}$ in parameter space. Its maxima correspond to the directions of greatest fragility; its minima correspond to the directions of greatest robustness. This is the "robustness sphere" that generalizes the scalar MRI to a full directional characterization.

### 9.7.3 Robustness Under Non-Euclidean Perturbation

The log-space perturbation model (Section 9.2.1) implicitly uses a non-Euclidean metric on parameter space. In the positive orthant $\mathbb{R}_{>0}^d$, the log-space metric is:

$$d_{\log}(\boldsymbol{\theta}_1, \boldsymbol{\theta}_2) = \sqrt{\sum_{i=1}^d \left(\log \frac{\theta_{1,i}}{\theta_{2,i}}\right)^2}$$

This is the Euclidean distance in log-coordinates, but it is *not* Euclidean in the original coordinates. Perturbations that are uniformly distributed in log-space are *not* uniformly distributed in the original space---they are biased toward larger perturbations in the upward direction (multiplication) and smaller perturbations in the downward direction (division). This asymmetry reflects the natural geometry of positive parameters: doubling a parameter is as "far" as halving it, in the log-metric sense.

Chapter 10 will develop more sophisticated non-Euclidean perturbation strategies, using the manifold structure of specific parameter spaces to generate perturbations that respect the geometry of the problem. The log-space perturbation used here is a special case---but a broadly applicable one that works well for most geometric models.

---

## 9.8 Practical Considerations

### 9.8.1 Number of Perturbation Samples

The default of 300 perturbation samples provides reliable estimates of the mean and 75th percentile. The 95th percentile is estimated from approximately 15 samples in the upper tail ($300 \times 0.05 = 15$), which is adequate for detecting gross fragility but may be noisy for precise quantification. The following table provides guidance:

| Use Case | Recommended $N$ | P95 Tail Samples | Notes |
|---|---|---|---|
| Quick screening | 100 | 5 | Sufficient for gross fragility detection |
| Standard analysis | 300 | 15 | Default; adequate for most purposes |
| Publication quality | 1000 | 50 | Stable P95 estimates |
| Safety-critical | 5000+ | 250+ | Reliable extreme tail characterization |

Computational cost scales linearly with $N$, so the choice is a direct tradeoff between statistical precision and runtime.

### 9.8.2 Reproducibility

The `compute_mri` function accepts an optional `rng` parameter (a NumPy `Generator` instance) for reproducibility. When reproducibility matters---and it almost always does in scientific and engineering contexts---pass an explicit generator:

```python
rng = np.random.default_rng(42)
mri_result = compute_mri(params, evaluate_fn, rng=rng)
```

If no generator is provided, the function creates one with seed 42, ensuring that results are reproducible by default. This is a deliberate design choice: robustness analysis should produce the same results when run twice with the same inputs.

### 9.8.3 When to Run Each Tool

The three tools have different computational costs and answer different questions. The following decision tree guides their use:

1. **Always run the sensitivity profile first.** It requires only $d + 1$ model evaluations (one baseline plus one per dimension) and immediately identifies which dimensions matter. This is cheap and informative.

2. **Run the MRI if you need a global robustness score.** It requires $N + 1$ evaluations (one baseline plus $N$ perturbations). Use it to compare models, to monitor robustness over time, or to decide whether deeper investigation is warranted.

3. **Run adversarial threshold search for the top-$k$ dimensions.** It requires up to $2 \times n\_steps \times k$ evaluations. Focus on the dimensions ranked most important by sensitivity profiling---searching unimportant dimensions is unlikely to find interesting thresholds (and indeed, in the defect prediction example, the unimportant dimensions had no thresholds at all).

---

## 9.9 Connections to Related Work

### 9.9.1 Flatness and Generalization

The relationship between the sharpness of a loss minimum and generalization performance has been studied extensively in the deep learning literature. Hochreiter and Schmidhuber (1997) observed that flat minima tend to generalize better than sharp ones. Keskar et al. (2017) showed that large-batch training tends to converge to sharp minima with poor generalization. The MRI provides a practical, model-agnostic tool for measuring this property---without requiring access to the training procedure or the loss function's analytical form.

### 9.9.2 Bayesian Model Comparison

The Bayesian evidence (marginal likelihood) naturally penalizes models with sharp posterior peaks, because it integrates the likelihood over the entire parameter space. A model with a sharp peak must have its probability mass concentrated in a small region, which the prior penalizes. The MRI can be viewed as a frequentist complement to the Bayesian evidence: instead of integrating the likelihood, it samples the neighborhood of the MAP estimate and summarizes the distribution of deviations. The MRI is easier to compute (it requires no prior specification and no integration) and directly measures the quantity of practical interest (sensitivity to parameter perturbation).

### 9.9.3 Adversarial Machine Learning

The adversarial threshold search shares its philosophy with adversarial example generation in deep learning (Goodfellow et al., 2014; Carlini and Wagner, 2017), but operates in parameter space rather than input space. Input-space adversarial examples find the smallest perturbation to an *input* that changes the *output*. Parameter-space adversarial thresholds find the smallest perturbation to a *parameter* that changes the *output beyond tolerance*. The geometric intuition is the same---finding the nearest decision boundary---but the space being searched and the practical implications are different.

---

## 9.10 What Comes Next

This chapter has developed tools for characterizing the robustness of a model at a single operating point---the best configuration found by optimization. Chapter 10 extends this analysis in two directions. First, it introduces *adversarial probing*: systematic exploration of the full parameter space to find not just tipping points along individual dimensions but adversarial *regions*---connected subsets of parameter space where the model fails. This requires the topological tools (persistent homology) that Chapter 10 develops, because the shape of an adversarial region---whether it is a thin sliver or a broad basin, whether it is simply connected or has holes---determines the practical risk it poses. Second, Chapter 10 develops methods for *hardening* a model against the vulnerabilities that the MRI and adversarial threshold search reveal, closing the loop from diagnosis to treatment.

The progression from Chapter 8 to Chapter 10 mirrors the progression from a static to a dynamic understanding of the model. Chapter 8 asks: "Which configurations are optimal?" This chapter asks: "How fragile are those optima?" Chapter 10 will ask: "What does the failure landscape look like, and can we reshape it?"

---

### Exercises

**9.1.** Implement a variant of `compute_mri` that perturbs only one parameter at a time (holding all others at their baseline values) and returns a per-parameter MRI. Compare the sum of per-parameter MRIs to the global MRI for the defect prediction model. What does the discrepancy tell you about parameter interactions?

**9.2.** The adversarial threshold search uses a log-spaced linear scan with 50 steps per direction. Implement a two-phase variant that uses 10 coarse steps to bracket the threshold, then 40 fine steps within the bracket to refine it. Under what conditions does this outperform the uniform scan?

**9.3.** Derive the relationship between the MRI and the eigenvalues of the Hessian $\nabla^2 \mathcal{L}(\boldsymbol{\theta}^*)$ for a quadratic loss surface. Show that $\mathbb{E}[\text{MRI}] \propto \sqrt{\text{tr}(\mathbf{H})}$ and identify the proportionality constant as a function of $\sigma$ and the MRI weights.

**9.4.** Run the sensitivity profile on the defect prediction model with three different inactive values: $10^3$, $10^6$, and $10^9$. Does the importance ranking change? For what types of models would you expect the ranking to be sensitive to the choice of inactive value?

**9.5.** The MRI weights $(0.5, 0.3, 0.2)$ can be interpreted as an approximation to CVaR. Derive the exact CVaR at level $\alpha = 0.05$ from the empirical $\omega$ distribution and compare it to the MRI. Under what distribution shapes do the two diverge most?

**9.6.** Extend the `run_campaign` function to compute the MRI for every Pareto-optimal configuration (not just the best one). Plot the Pareto frontier in three dimensions: (dimensionality, MAE, MRI). Describe the tradeoff surface. Is there a Pareto frontier in this three-objective space, and if so, how does it differ from the two-objective frontier of Chapter 8?
