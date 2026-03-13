# Chapter 2: Mahalanobis Distance and Weighted Metric Spaces

> *"Not all dimensions are created equal."*

In Chapter 1, we introduced the idea that models live in parameter spaces and that systematic exploration of those spaces -- structural fuzzing -- reveals which dimensions actually matter. But we deferred a critical question: how do we *measure* the distance between two points in a space where different dimensions have different units, different scales, and different degrees of importance? The Euclidean distance is a blunt instrument. This chapter introduces the Mahalanobis distance and the family of weighted metric spaces that arise naturally when we take the structure of data seriously.

## 2.1 From Euclidean to Mahalanobis

The Euclidean distance between two points $\mathbf{a}$ and $\mathbf{b}$ in $\mathbb{R}^n$ is the formula every student learns first:

$$d_{\text{Euclid}}(\mathbf{a}, \mathbf{b}) = \sqrt{\sum_{i=1}^{n} (a_i - b_i)^2} = \sqrt{(\mathbf{a} - \mathbf{b})^\top (\mathbf{a} - \mathbf{b})}$$

This treats every dimension identically. A difference of 1.0 in dimension 3 contributes the same as a difference of 1.0 in dimension 7, regardless of what those dimensions represent. When the dimensions are measured in commensurable units and have comparable variances, this is reasonable. In practice, it almost never is.

Consider the 9-dimensional ethical-economic space used in the `eris-econ` model (and reimplemented in this book's `geometric_economics` example). Dimension 0 ("Consequences") represents monetary payoffs and varies on a scale from 0 to roughly 50. Dimension 2 ("Fairness") is a normalized score that varies between 0 and 10. Dimension 8 ("Epistemic") is a knowledge-completeness indicator that is often constant at 8.0. Treating a 1-unit change in monetary payoff the same as a 1-unit change in fairness is not merely inaccurate -- it is *meaningless*. The units are incommensurable.

The Mahalanobis distance resolves this by introducing a positive-definite matrix $\Sigma^{-1}$ into the distance computation:

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1} (\mathbf{a} - \mathbf{b})}$$

Here $\Sigma$ is typically the covariance matrix of the data, and $\Sigma^{-1}$ is the *precision matrix*. When $\Sigma = I$ (the identity matrix), the Mahalanobis distance reduces exactly to the Euclidean distance. In all other cases, $\Sigma^{-1}$ acts as a weighting matrix that stretches, compresses, and rotates the space.

**Geometric interpretation.** The set of points equidistant from a center $\mathbf{c}$ under the Euclidean metric forms a hypersphere. Under the Mahalanobis metric, that same set forms a hyperellipsoid whose axes are aligned with the eigenvectors of $\Sigma$ and whose radii are proportional to the square roots of the eigenvalues. Dimensions with large variance (high eigenvalues in $\Sigma$) are *compressed* -- the metric effectively says "a large difference along this axis is not surprising." Dimensions with small variance are *stretched* -- small deviations along tightly constrained dimensions are penalized heavily.

This is exactly the right behavior for the structural fuzzing problem. If a parameter has historically varied over a wide range with little effect on model error, we want the distance metric to discount changes along that axis. If a parameter is finely resolved and small perturbations cause large behavioral shifts, we want the metric to amplify those changes.

The implementation in the `geometric_economics` module is direct:

```python
def mahalanobis_distance(
    a: np.ndarray,
    b: np.ndarray,
    sigma_inv: np.ndarray,
) -> float:
    """Compute Mahalanobis distance between two points.

    d = sqrt(delta^T @ sigma_inv @ delta)
    """
    delta = a - b
    return float(np.sqrt(delta @ sigma_inv @ delta))
```

Three lines of arithmetic, but the matrix `sigma_inv` encodes the entire learned structure of the space.


## 2.2 Covariance Matrices as Learned Metrics

The covariance matrix $\Sigma$ is a symmetric, positive-definite $n \times n$ matrix. Its entries encode two kinds of information:

**Diagonal entries** $\sigma_{ii} = \text{Var}(X_i)$ give the variance of each dimension. A large diagonal entry means the dimension exhibits wide natural variation -- and consequently receives *low weight* in $\Sigma^{-1}$ (since inversion flips large values to small ones). A small diagonal entry means the dimension is tightly constrained, and deviations from the mean are significant.

**Off-diagonal entries** $\sigma_{ij} = \text{Cov}(X_i, X_j)$ for $i \neq j$ encode linear coupling between dimensions. A positive off-diagonal entry means the two dimensions tend to increase together; a negative entry means they move in opposition. When the off-diagonal structure is non-trivial, the equidistant contours rotate away from the coordinate axes, and the metric captures the fact that *correlated* deviations are less surprising than *uncorrelated* ones.

In the `eris-econ` model, the covariance matrix for the 9D ethical-economic space is constructed from domain knowledge rather than estimated from data. This is a common and underappreciated approach: when you understand the generative process, you can build $\Sigma$ directly rather than waiting for enough samples to estimate it reliably. Consider the following structure:

| Entry | Value | Interpretation |
|-------|-------|----------------|
| $\sigma_{0,0}$ | 25.0 | Consequences (money) varies on a large scale |
| $\sigma_{1,1}$ | 4.0 | Rights: moderate variation |
| $\sigma_{2,2}$ | 0.25 | Fairness: finely resolved, small changes matter |
| $\sigma_{3,3}$ | 1.0 | Autonomy: moderate |
| $\sigma_{4,4}$ | 4.0 | Trust: moderate variation |
| $\sigma_{0,2}$ | 0.5 | Consequences-Fairness coupling |
| $\sigma_{1,4}$ | 0.3 | Rights-Trust coupling |

The entry $\sigma_{0,0} = 25.0$ says that monetary consequences naturally vary over a range with standard deviation $\sqrt{25} = 5.0$. In the inverse, this becomes $(\Sigma^{-1})_{0,0} \approx 1/25 = 0.04$ (before accounting for off-diagonal adjustments), so a 1-unit change in consequences contributes very little to the distance. By contrast, $\sigma_{2,2} = 0.25$ means fairness has a standard deviation of $0.5$, and $(\Sigma^{-1})_{2,2} \approx 4.0$: the metric pays close attention to fairness.

The off-diagonal entry $\sigma_{0,2} = 0.5$ captures the coupling between consequences and fairness. In a game-theoretic context, this reflects the observation that monetary outcomes and perceived fairness are not independent -- a generous offer affects both dimensions simultaneously. The precision matrix captures this coupling as a conditional relationship: once you account for the correlation, only the *residual* variation in each dimension matters for distance.

Here is how one constructs such a matrix from domain knowledge:

```python
import numpy as np

N_DIMS = 9
DIM_NAMES = [
    "Consequences", "Rights", "Fairness", "Autonomy", "Trust",
    "Social Impact", "Virtue/Identity", "Legitimacy", "Epistemic",
]

# Start with diagonal variances from domain knowledge
sigma = np.diag([
    25.0,   # Consequences: monetary payoffs, large scale
    4.0,    # Rights: moderate variation
    0.25,   # Fairness: finely resolved
    1.0,    # Autonomy: moderate
    4.0,    # Trust: moderate variation
    9.0,    # Social Impact: varies with stake size
    2.0,    # Virtue/Identity: moderate
    1.0,    # Legitimacy: moderate
    0.5,    # Epistemic: somewhat constrained
])

# Add off-diagonal couplings (symmetric)
sigma[0, 2] = sigma[2, 0] = 0.5   # Consequences-Fairness
sigma[1, 4] = sigma[4, 1] = 0.3   # Rights-Trust
sigma[0, 5] = sigma[5, 0] = 2.0   # Consequences-Social Impact
sigma[2, 6] = sigma[6, 2] = 0.2   # Fairness-Virtue

# Invert to get precision matrix
sigma_inv = np.linalg.inv(sigma)
```

**Cultural heterogeneity.** A powerful consequence of encoding the metric in $\Sigma$ is that different populations -- different cultures, different market segments, different user cohorts -- can be modeled with different covariance structures. A culture that prioritizes fairness over economic efficiency would have a smaller $\sigma_{2,2}$ (making fairness deviations more costly) and a larger $\sigma_{0,0}$ (making monetary differences less significant). The *same* underlying model, the *same* distance function, but different $\Sigma$ matrices. This is metric learning applied to behavioral science, and it is one of the most compelling aspects of the geometric approach.


## 2.3 The Inverse Covariance as an Attention Mechanism

The precision matrix $\Sigma^{-1}$ has a natural interpretation as an *attention* mechanism. Each diagonal entry $(\Sigma^{-1})_{ii}$ determines how much the distance metric "pays attention" to dimension $i$. Large values mean high attention; small values mean the dimension is effectively ignored.

This connection to attention is more than metaphorical. In the transformer architecture that dominates modern deep learning, the attention mechanism computes a weighted combination of value vectors, where the weights are determined by query-key compatibility. The attention weight matrix plays the same structural role as $\Sigma^{-1}$: it determines which dimensions of the input receive emphasis when computing the output.

More precisely, consider a single-head attention computation with query $\mathbf{q}$ and key $\mathbf{k}$:

$$\text{attention}(\mathbf{q}, \mathbf{k}) = \frac{\exp(\mathbf{q}^\top W \mathbf{k} / \sqrt{d})}{\sum_j \exp(\mathbf{q}^\top W \mathbf{k}_j / \sqrt{d})}$$

The matrix $W = W_Q^\top W_K$ in the exponent is structurally analogous to $\Sigma^{-1}$ in the Mahalanobis distance. Both are bilinear forms that determine how two vectors interact. The key difference is that attention weights are *learned* from data via backpropagation, while $\Sigma^{-1}$ can be either estimated from data, constructed from domain knowledge, or -- as we will see -- optimized via Cholesky parameterization.

In the structural fuzzing framework, the `evaluate_fn` constructs $\Sigma^{-1}$ from parameter values, where each parameter acts as a variance (inverse attention weight):

```python
# From evaluate_fn: params[i] is the "variance" for dimension i.
# Large params[i] -> small weight -> low attention
# Small params[i] -> large weight -> high attention
weights = np.where(params < 1e5, 1.0 / np.maximum(params, 1e-6), 0.0)
sigma_inv = np.diag(weights)
```

When `params[i]` is set to $10^6$ (the `inactive_value`), the corresponding weight drops to zero, effectively removing that dimension from the metric entirely. This is how the subset enumeration in Chapter 1 works: for each subset of "active" dimensions, the inactive dimensions receive zero attention. The structural fuzzing framework then asks: which *attention pattern* -- which assignment of precision across dimensions -- best explains the empirical data?

There is a deeper connection worth noting. In Gaussian graphical models, the sparsity pattern of $\Sigma^{-1}$ encodes *conditional independence*: if $(\Sigma^{-1})_{ij} = 0$, then dimensions $i$ and $j$ are conditionally independent given all other dimensions. A sparse precision matrix is one where most dimensions interact only indirectly, through chains of conditionally dependent neighbors. When the structural fuzzing framework sets most diagonal entries to zero (by assigning `inactive_value` to those dimensions), it is effectively imposing an extreme form of sparsity on $\Sigma^{-1}$ -- asserting that only a small subset of dimensions participates in the conditional dependency structure at all.

This framing connects classical statistics (covariance estimation, graphical models), modern machine learning (attention mechanisms, sparse transformers), and the structural fuzzing framework (dimension subset search) under a single geometric umbrella.


## 2.4 Log-Space Parameterization

A persistent challenge in parameter optimization is the problem of *scale*. When a parameter might take values anywhere from 0.01 to 100, a uniform grid over that range is wasteful: 99% of the grid points fall in the interval $[1, 100]$, while the potentially important region $[0.01, 1]$ receives almost no coverage.

The solution is to search in log-space. Instead of distributing $n$ grid points uniformly over $[\alpha, \beta]$, we distribute them uniformly over $[\log_{10}(\alpha), \log_{10}(\beta)]$ and then exponentiate:

$$v_k = 10^{\log_{10}(\alpha) + k \cdot \frac{\log_{10}(\beta) - \log_{10}(\alpha)}{n-1}}, \quad k = 0, 1, \ldots, n-1$$

This produces values that are *multiplicatively* spaced. For $\alpha = 0.01$, $\beta = 100$, and $n = 20$, the first few values are approximately $0.01, 0.019, 0.036, 0.069, \ldots$ and the last few are $\ldots, 14.6, 27.8, 53.0, 100.0$. Each region of the range receives proportional coverage on a logarithmic scale.

The `optimize_subset` function in the structural fuzzing core uses exactly this approach:

```python
# From core.py: log-spaced grid for parameter search
grid_values = np.logspace(np.log10(0.01), np.log10(100), n_grid)
```

For higher-dimensional search (3D and above), random sampling in log-space replaces the grid:

```python
# Random search in log-space for 3D+ subsets
rng = np.random.default_rng(42)
log_low, log_high = np.log10(0.01), np.log10(100)
for _ in range(n_random):
    params = np.full(n_all, inactive_value)
    log_vals = rng.uniform(log_low, log_high, n_active)
    for i, dim in enumerate(active_dims):
        params[dim] = 10 ** log_vals[i]
```

**Why log-space matters for covariance parameters.** The diagonal entries of $\Sigma$ are variances, which are inherently positive and often span several orders of magnitude. In the `eris-econ` model, they range from 0.25 (fairness) to 25.0 (consequences) -- two orders of magnitude. When optimizing these values, a linear grid would over-represent the high end. Log-space parameterization ensures that the ratio $\sigma_{0,0}/\sigma_{2,2} = 100$ receives the same representational density as the ratio $\sigma_{2,2}/\sigma_{8,8} = 0.5$.

This principle extends beyond grid search. Gradient-based optimizers also benefit from log-space parameterization, because the gradient of $\log(\sigma)$ with respect to a loss function has more uniform magnitude across the parameter range than the gradient of $\sigma$ itself. To see why, consider the chain rule: if $\sigma = 10^\theta$, then $\partial \mathcal{L}/\partial \theta = (\partial \mathcal{L}/\partial \sigma) \cdot \sigma \cdot \ln(10)$. The multiplicative factor of $\sigma$ compensates for the fact that $\partial \mathcal{L}/\partial \sigma$ tends to be inversely proportional to $\sigma$ for scale-sensitive losses. The result is that gradient steps in $\theta$-space produce proportional changes in $\sigma$ regardless of the current scale. We exploit this property in the Cholesky factorization discussed next.


## 2.5 Cholesky Factorization for Positive-Definiteness

We now confront a fundamental challenge in metric learning: how do we optimize over the space of valid covariance matrices?

A covariance matrix $\Sigma$ must be symmetric and positive-definite (SPD). Symmetry is easy to enforce -- parameterize only the upper (or lower) triangle and mirror it. Positive-definiteness is harder. An unconstrained optimization over symmetric matrices will happily produce matrices with negative eigenvalues, which yield imaginary distances and meaningless metrics.

The classical solution is the **Cholesky decomposition**. Every SPD matrix $M$ can be uniquely decomposed as:

$$M = LL^\top$$

where $L$ is a lower-triangular matrix with strictly positive diagonal entries. This decomposition is the matrix analogue of the fact that every positive real number $x$ can be written as $x = y^2$ for some $y > 0$.

For metric learning, we apply this to the precision matrix rather than the covariance matrix:

$$\Sigma^{-1} = LL^\top$$

This is the parameterization used in the `eris-econ` calibration module. Instead of optimizing over $\Sigma^{-1}$ directly (which requires a positive-definiteness constraint), we optimize over the entries of $L$ (which is unconstrained except for positive diagonals). The product $LL^\top$ is automatically symmetric and positive-definite for any $L$ with positive diagonal entries.

**Parameter count.** A general $n \times n$ SPD matrix has $n(n+1)/2$ free parameters (the upper triangle including the diagonal). The lower-triangular Cholesky factor $L$ has exactly the same number of free parameters: the lower triangle including the diagonal. For our 9D space, this means $9 \times 10 / 2 = 45$ parameters rather than $81$.

**Enforcing positive diagonals.** The diagonal entries of $L$ must be strictly positive. We enforce this by parameterizing them in log-space: if $\ell_{ii}$ is the $i$-th diagonal entry of $L$, we optimize over $\theta_i = \log(\ell_{ii})$ and reconstruct $\ell_{ii} = e^{\theta_i}$. This maps the unconstrained real line to the positive reals, ensuring that $L$ always has positive diagonal and therefore $LL^\top$ is always SPD.

Here is the complete parameterization:

```python
import numpy as np
from scipy.optimize import minimize

def cholesky_params_to_precision(params: np.ndarray, n: int) -> np.ndarray:
    """Convert unconstrained parameters to a positive-definite precision matrix.

    Parameters
    ----------
    params : np.ndarray
        Flat array of n*(n+1)/2 parameters. The first n entries are
        log-diagonal values; the remaining are off-diagonal entries
        of the lower-triangular Cholesky factor.
    n : int
        Dimension of the matrix.

    Returns
    -------
    np.ndarray
        n x n positive-definite precision matrix Sigma^{-1} = L @ L.T.
    """
    L = np.zeros((n, n))

    # Diagonal: exponentiate to ensure positivity
    for i in range(n):
        L[i, i] = np.exp(params[i])

    # Off-diagonal (lower triangle)
    idx = n
    for i in range(1, n):
        for j in range(i):
            L[i, j] = params[idx]
            idx += 1

    return L @ L.T


def calibrate_precision_matrix(
    evaluate_fn,
    n_dims: int,
    n_restarts: int = 10,
) -> np.ndarray:
    """Calibrate precision matrix using L-BFGS-B optimization.

    Parameters
    ----------
    evaluate_fn : callable
        Function (sigma_inv) -> scalar loss.
    n_dims : int
        Dimensionality of the space.
    n_restarts : int
        Number of random restarts for global search.

    Returns
    -------
    np.ndarray
        Optimized precision matrix.
    """
    n_params = n_dims * (n_dims + 1) // 2
    best_loss = float("inf")
    best_precision = None
    rng = np.random.default_rng(42)

    for _ in range(n_restarts):
        # Initialize: small random values, log-diagonal near 0
        x0 = rng.normal(0, 0.1, n_params)

        def objective(params):
            sigma_inv = cholesky_params_to_precision(params, n_dims)
            return evaluate_fn(sigma_inv)

        result = minimize(objective, x0, method="L-BFGS-B")

        if result.fun < best_loss:
            best_loss = result.fun
            best_precision = cholesky_params_to_precision(result.x, n_dims)

    return best_precision
```

Several details warrant discussion.

**L-BFGS-B optimization.** We use the L-BFGS-B algorithm (limited-memory Broyden-Fletcher-Goldfarb-Shanno with box constraints), a quasi-Newton method that approximates the Hessian using a limited history of gradient evaluations. It is well-suited to this problem for three reasons: (1) the objective is smooth in the Cholesky parameters, (2) the parameter space is modest in size ($n(n+1)/2 = 45$ for $n = 9$), and (3) L-BFGS-B handles the unconstrained optimization efficiently without requiring explicit gradient computation (using finite differences by default).

**Random restarts.** The objective surface over Cholesky parameters is generally non-convex. A single optimization run may find a local minimum that is far from global. Multiple random restarts -- each starting from a different initial $L$ -- increase the probability of finding a good solution. The initial parameters are drawn from $\mathcal{N}(0, 0.1)$, which corresponds to precision matrices near the identity (since $e^0 = 1$ for the diagonal and near-zero off-diagonals give weak coupling).

**Numerical stability.** The exponential mapping $\ell_{ii} = e^{\theta_i}$ can produce very large or very small diagonal entries if $\theta_i$ drifts far from zero. In practice, it is wise to add bounds: $\theta_i \in [-5, 5]$ constrains the diagonal to $[e^{-5}, e^5] \approx [0.007, 148]$, which is more than adequate for most applications. This is easily incorporated into L-BFGS-B via its `bounds` parameter.


## 2.6 Diagonal-Only Simplification

The full Cholesky parameterization has $n(n+1)/2$ free parameters. For $n = 9$, this is 45 -- manageable but potentially overparameterized when the training signal is weak. The `eris-econ` model has 16 prediction targets. Fitting 45 parameters to 16 targets risks overfitting: the precision matrix may learn spurious correlations that capture noise rather than structure.

The remedy is to restrict $\Sigma$ (and therefore $\Sigma^{-1}$) to be diagonal:

$$\Sigma = \text{diag}(\sigma_1^2, \sigma_2^2, \ldots, \sigma_n^2), \quad \Sigma^{-1} = \text{diag}(1/\sigma_1^2, 1/\sigma_2^2, \ldots, 1/\sigma_n^2)$$

This is the parameterization used in the structural fuzzing framework's `evaluate_fn`:

```python
weights = np.where(params < 1e5, 1.0 / np.maximum(params, 1e-6), 0.0)
sigma_inv = np.diag(weights)
```

Here `params[i]` plays the role of $\sigma_i^2$, and `weights[i]` $= 1/\sigma_i^2$ is the precision (attention) for dimension $i$. The threshold at $10^5$ provides a clean mechanism for "turning off" dimensions entirely.

**Advantages of the diagonal restriction:**

1. **Fewer parameters.** Only $n$ free values instead of $n(n+1)/2$. For $n = 9$, this is 9 vs. 45 -- a 5x reduction.

2. **Interpretability.** Each parameter has a direct meaning: the variance (inverse importance) of a single dimension. There are no interaction terms to interpret.

3. **Efficient search.** The structural fuzzing framework searches over subsets of dimensions with grid search (1D, 2D) or random search (3D+). The diagonal restriction makes this enumeration tractable.

4. **Per-dimension bounds.** Different dimensions can have different feasible ranges. Monetary parameters might range over $[0.01, 100]$ while normalized scores might range over $[0.1, 10]$. Diagonal parameterization makes these per-dimension bounds natural.

**When to use full vs. diagonal covariance.** The choice depends on the ratio of training signal to parameter count and on domain knowledge about inter-dimensional coupling:

- **Diagonal** when the number of targets is small relative to $n(n+1)/2$, or when dimensions are believed to be approximately independent.
- **Block-diagonal** when groups of dimensions are coupled (e.g., the economic dimensions 0, 1, 2 form one block; the social dimensions 4, 5, 6 form another) but between-group coupling is weak.
- **Full** when the training signal is rich and inter-dimensional coupling is critical to the model's predictions.

**Cross-validation for regularization.** Even with the diagonal simplification, overfitting is possible. $k$-fold cross-validation provides a principled approach: partition the targets into $k$ folds, fit $\Sigma^{-1}$ on $k-1$ folds, and evaluate on the held-out fold. The regularization strength (e.g., a ridge penalty $\lambda \| \Sigma^{-1} \|_F^2$ added to the loss) is chosen to minimize the cross-validated error.

**Bootstrap confidence intervals.** To assess the reliability of the learned metric, draw $B$ bootstrap samples from the targets (sampling with replacement), fit $\Sigma^{-1}$ to each bootstrap sample, and examine the distribution of the resulting parameters. Dimensions whose precision estimates have tight bootstrap intervals are reliably important. Dimensions with wide intervals are uncertain -- the data does not strongly constrain their contribution to the metric.

For the `eris-econ` model, bootstrap analysis reveals that dimensions 0 (Consequences), 2 (Fairness), and 4 (Trust) consistently receive high precision across bootstrap samples, while dimensions 3 (Autonomy) and 7 (Legitimacy) are unstable. This aligns with the structural fuzzing results from Chapter 1: the Pareto frontier is dominated by subsets containing Consequences and Fairness.


## 2.7 Putting It Together: From Distance to Decision

To see how the Mahalanobis metric drives actual predictions, consider how the `eris-econ` model predicts ultimatum game rejection rates.

The model represents each decision scenario as a point in the 9D ethical-economic space. An ultimatum offer of 20% of a \$10 stake maps to a specific 9D vector via `ultimatum_state(stake=10.0, offer_pct=20.0)`. A "fair" reference offer of 50% maps to another vector. The model computes the Mahalanobis distance from each option (accept, reject) to the fair reference point, then applies a softmax choice rule:

$$P(\text{reject}) = \frac{\exp(-d_{\text{reject}} / T)}{\exp(-d_{\text{accept}} / T) + \exp(-d_{\text{reject}} / T)}$$

where $T$ is a temperature parameter that may itself depend on the stakes. The precision matrix $\Sigma^{-1}$ determines *which dimensions* of the difference between the offer and the fair reference point matter for this distance computation. If fairness receives high precision, then unfair offers create large distances from the reference, driving up rejection rates. If monetary consequences receive high precision, then the cost of rejection (losing the offered money) dominates, driving down rejection rates.

The interplay between the metric and the temperature is worth emphasizing. The temperature $T$ in the `eris-econ` model is itself stake-dependent, computed via a cost-dependent formula:

$$T(\text{stake}) = \max\left(T_{\text{floor}},\; T_{\text{base}} + \frac{T_\alpha}{\sqrt{\text{stake}}}\right)$$

At low stakes, the temperature is high -- choices are noisy and the model predicts behavior closer to random. At high stakes, the temperature drops, and the precision matrix exerts stronger influence on the prediction. This captures the empirical observation that people are more "rational" (more sensitive to the structure of the decision) when the stakes are high. The metric $\Sigma^{-1}$ determines *what* the agent pays attention to; the temperature determines *how sharply* that attention translates into behavioral differences.

The entire behavioral prediction reduces to a geometric computation in a weighted metric space, and the problem of *calibrating* the model reduces to the problem of *learning the metric* -- finding the $\Sigma^{-1}$ that makes the model's predictions match empirical data. This is not a metaphor. The 16 prediction targets in the `eris-econ` model -- ultimatum rejection rates, dictator giving levels, public goods contributions, Kahneman-Tversky prospect choices -- are all functions of Mahalanobis distances. The structural fuzzing campaign over dimension subsets is literally a search over the sparsity pattern and scale of the precision matrix.


## 2.8 Summary and Looking Ahead

This chapter developed the Mahalanobis distance as the natural generalization of Euclidean distance for spaces with non-uniform, correlated dimensions. The key ideas are:

1. **The covariance matrix $\Sigma$** encodes the scale and coupling structure of the dimensions. It can be estimated from data or constructed from domain knowledge.

2. **The precision matrix $\Sigma^{-1}$** acts as an attention mechanism, assigning importance weights to each dimension and each pair of dimensions.

3. **Log-space parameterization** provides uniform coverage over parameters that span multiple orders of magnitude.

4. **Cholesky factorization** $\Sigma^{-1} = LL^\top$ enables unconstrained optimization over the space of valid (positive-definite) precision matrices, with $n(n+1)/2$ free parameters and log-space diagonals.

5. **Diagonal simplification** reduces the parameter count to $n$ when the full covariance is overparameterized, with cross-validation and bootstrap analysis for regularization and uncertainty quantification.

In Chapter 3, we turn to the *search* problem: given a space equipped with a Mahalanobis metric, how do we systematically explore the subsets of dimensions that contribute to it? This is the core algorithmic problem of structural fuzzing, and it connects the geometric foundations of this chapter to the combinatorial enumeration machinery that makes the framework practical.
