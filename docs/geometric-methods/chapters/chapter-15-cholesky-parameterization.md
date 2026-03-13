# Chapter 15: Cholesky Parameterization for Positive-Definiteness

*Geometric Methods in Computational Modeling* --- Andrew H. Bond

---

> *"The art of parameterization is the art of turning constrained problems into unconstrained ones."*

In Chapter 2, we introduced the Mahalanobis distance and the precision matrix $\Sigma^{-1}$ that gives it shape. In Chapter 4, we developed the geometry of the SPD manifold on which covariance matrices live. Both chapters deferred a central engineering question: when you need to *optimize* a covariance or precision matrix --- when the metric itself is a learnable parameter --- how do you ensure that the result is always symmetric and positive definite?

This chapter answers that question in full. The Cholesky factorization $\Sigma = LL^\top$ transforms the constrained optimization over SPD matrices into an unconstrained optimization over lower-triangular matrices. The log-diagonal variant, where the diagonal of $L$ is parameterized in log-space, removes the last remaining constraint (positive diagonals) and yields a parameterization that is fully unconstrained, numerically stable, and differentiable end-to-end. These properties make it the default choice for covariance learning in modern computational modeling, from behavioral economics calibration to deep metric learning.

We develop the theory, connect it to the SPD manifold geometry of Chapter 4, implement it in both NumPy and PyTorch, and show how it applies to the Mahalanobis distance learning problem introduced in Chapter 2. We close with the diagonal-only simplification used throughout the structural fuzzing framework and a synthesis that connects the parameterization patterns of Part III back to the geometric foundations of Part I.

---

## 15.1 The Positive-Definiteness Constraint

### 15.1.1 Why Unconstrained Optimization Fails

Suppose you want to learn a $9 \times 9$ covariance matrix $\Sigma$ that makes your model's predictions match empirical data. The naive approach is to treat the 81 entries of $\Sigma$ as free parameters and run gradient descent. This fails for three reasons.

**Symmetry violation.** An unconstrained update to an arbitrary $9 \times 9$ matrix will not preserve $\Sigma = \Sigma^\top$. You can enforce symmetry by parameterizing only the upper triangle and mirroring it, reducing the parameter count from 81 to $9 \times 10 / 2 = 45$. But this is the easy constraint.

**Positive-definiteness violation.** Even if $\Sigma$ starts SPD, a gradient step can push an eigenvalue through zero, producing a matrix that is positive *semi*-definite or indefinite. When this happens, the Mahalanobis distance $d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1} (\mathbf{a} - \mathbf{b})}$ involves the inverse of a singular or indefinite matrix, which is either undefined or yields imaginary distances. The optimizer has left the feasible set, and no amount of step-size tuning guarantees it will stay inside.

**Projected gradient methods are fragile.** One could project back onto the SPD cone after each gradient step --- compute the eigendecomposition, clamp negative eigenvalues to some $\epsilon > 0$, and reconstruct the matrix. This works but is expensive ($O(n^3)$ per projection), introduces discontinuities in the optimization landscape at the boundary of the SPD cone, and can cause the optimizer to "chatter" along the boundary rather than converging smoothly.

The right solution is to choose a parameterization that makes the constraint *impossible to violate*, so the optimizer never needs to worry about it. This is the Cholesky factorization.

### 15.1.2 The SPD Cone

The set of $n \times n$ SPD matrices forms an open convex cone in the $n(n+1)/2$-dimensional space of symmetric matrices (Chapter 4, Definition 4.1). Its boundary consists of positive *semi*-definite matrices --- those with at least one zero eigenvalue. The Cholesky factorization provides a bijection between the interior of this cone and the set of lower-triangular matrices with positive diagonals, mapping the curved boundary of the SPD cone to the simple constraint "diagonal entries positive."

---

## 15.2 The Cholesky Factorization

### 15.2.1 Statement and Uniqueness

**Theorem 15.1** (Cholesky factorization). *Every symmetric positive definite matrix $M \in \text{SPD}(n)$ has a unique decomposition*

$$M = LL^\top$$

*where $L$ is lower triangular with strictly positive diagonal entries.*

The proof proceeds by induction on $n$, partitioning $M$ into a leading $(n-1) \times (n-1)$ block (which is SPD by the property that every leading principal submatrix of an SPD matrix is SPD) and applying the inductive hypothesis. The details are standard; see the Notes and References.

**Parameter count.** The Cholesky factor $L$ has $n$ diagonal entries and $n(n-1)/2$ off-diagonal entries in the lower triangle, for a total of $n(n+1)/2$ free parameters --- exactly the number of degrees of freedom in a symmetric matrix.

### 15.2.2 The Converse: From $L$ to SPD

The factorization's power for optimization comes from the converse direction. Given *any* lower-triangular matrix $L$ with strictly positive diagonal entries, the product $M = LL^\top$ is automatically:

1. **Symmetric**: $(LL^\top)^\top = (L^\top)^\top L^\top = LL^\top$.
2. **Positive definite**: for any $\mathbf{x} \neq 0$, $\mathbf{x}^\top LL^\top \mathbf{x} = \|L^\top \mathbf{x}\|^2 > 0$, since $L$ is invertible (positive diagonal implies nonzero determinant, so $L^\top \mathbf{x} \neq 0$).

This means we can parameterize our optimization over the entries of $L$ rather than the entries of $M$. The off-diagonal entries of $L$ are completely unconstrained --- they can be any real numbers. The only constraint is that the diagonal entries must be positive.

---

## 15.3 Log-Diagonal Cholesky Parameterization

### 15.3.1 Removing the Last Constraint

The diagonal entries $\ell_{ii}$ of $L$ must be strictly positive. We remove this constraint by parameterizing them in log-space. Define

$$\ell_{ii} = \exp(\theta_i), \quad \theta_i \in \mathbb{R}.$$

Since $\exp(\cdot) : \mathbb{R} \to (0, \infty)$ is a bijection, every real value of $\theta_i$ produces a valid positive diagonal entry. The full parameterization is now:

- **Diagonal parameters** $\theta_1, \ldots, \theta_n \in \mathbb{R}$ (unconstrained)
- **Off-diagonal parameters** $\ell_{ij}$ for $i > j$ (unconstrained)

Total: $n(n+1)/2$ unconstrained real parameters that bijectively correspond to the set of $n \times n$ SPD matrices. An optimizer can take gradient steps of any magnitude in any direction without ever leaving the feasible set.

### 15.3.2 Why Log-Space for the Diagonal

The log-space parameterization is not merely a convenience for enforcing positivity. It provides three additional benefits.

**Uniform sensitivity across scales.** As discussed in Chapter 2 (Section 2.4), the gradient of a loss with respect to $\theta_i = \log(\ell_{ii})$ has more uniform magnitude across the parameter range than the gradient with respect to $\ell_{ii}$ directly. If $\mathcal{L}$ is the loss, then

$$\frac{\partial \mathcal{L}}{\partial \theta_i} = \frac{\partial \mathcal{L}}{\partial \ell_{ii}} \cdot \ell_{ii}$$

The multiplicative factor $\ell_{ii}$ compensates for the tendency of $\partial \mathcal{L} / \partial \ell_{ii}$ to shrink as $\ell_{ii}$ grows, producing gradient steps that correspond to *proportional* changes in $\ell_{ii}$ regardless of its current magnitude. A step of $\Delta\theta = 0.1$ changes $\ell_{ii}$ by approximately 10% whether $\ell_{ii}$ is 0.01 or 100.

**Natural initialization.** Setting all $\theta_i = 0$ yields $\ell_{ii} = 1$ for all $i$. If the off-diagonal entries are also initialized to zero, then $L = I$ and $M = LL^\top = I$, the identity matrix. This is the natural "no information" starting point: all dimensions are independent with unit variance. The optimizer then learns how to deviate from this baseline.

**Connection to the SPD manifold.** The log-diagonal parameterization has a natural relationship to the log-Euclidean metric on SPD(n) developed in Chapter 4. Recall that the log-Euclidean distance is $d_{LE}(S_1, S_2) = \|\log(S_1) - \log(S_2)\|_F$, where $\log$ is the matrix logarithm. For diagonal SPD matrices, the matrix logarithm reduces to the elementwise logarithm of the diagonal, and the log-Euclidean distance reduces to the Euclidean distance between the log-diagonals. The log-diagonal Cholesky parameterization thus inherits the desirable scale-equivariance of the log-Euclidean framework for the diagonal portion of the matrix.

### 15.3.3 The Complete Parameterization Map

We can now write the complete map from unconstrained parameters to SPD matrix. Let $\boldsymbol{\phi} \in \mathbb{R}^{n(n+1)/2}$ be the parameter vector, partitioned as:

$$\boldsymbol{\phi} = (\theta_1, \ldots, \theta_n, \ell_{21}, \ell_{31}, \ell_{32}, \ell_{41}, \ldots, \ell_{n,n-1})$$

The map $f : \mathbb{R}^{n(n+1)/2} \to \text{SPD}(n)$ is:

1. Construct $L$ with $L_{ii} = \exp(\theta_i)$ and $L_{ij} = \ell_{ij}$ for $i > j$.
2. Return $M = LL^\top$.

This map is smooth (infinitely differentiable), surjective onto SPD(n), and has a smooth inverse (the Cholesky decomposition followed by taking the log of the diagonal). It is therefore a diffeomorphism between $\mathbb{R}^{n(n+1)/2}$ and SPD(n), which means gradient-based optimization in parameter space $\mathbb{R}^{n(n+1)/2}$ corresponds to smooth navigation of the SPD manifold.

---

## 15.4 Implementation: NumPy

The `eris-econ` calibration module implements Cholesky parameterization for learning the precision matrix $\Sigma^{-1}$ from observed economic choices. The core routine reconstructs the precision matrix from a flat parameter vector:

```python
import numpy as np
from scipy.optimize import minimize


def cholesky_params_to_precision(params: np.ndarray, n: int) -> np.ndarray:
    """Convert unconstrained parameters to a positive-definite precision matrix.

    The first n entries are log-diagonal values (exponentiated to ensure
    positivity). The remaining n*(n-1)/2 entries are the off-diagonal
    elements of the lower-triangular Cholesky factor L.

    Returns Sigma^{-1} = L @ L.T, which is guaranteed SPD.
    """
    L = np.zeros((n, n))

    # Diagonal: exponentiate for positivity
    for i in range(n):
        L[i, i] = np.exp(params[i])

    # Off-diagonal (lower triangle): unconstrained
    idx = n
    for i in range(1, n):
        for j in range(i):
            L[i, j] = params[idx]
            idx += 1

    return L @ L.T
```

The function unpacks the flat array in a specific order: the first $n$ entries are log-diagonal values, and the remaining entries fill the lower triangle column by column. The `np.exp` call on the diagonal is the only nonlinearity --- everything else is linear.

The calibration loop wraps this in an objective function and calls L-BFGS-B:

```python
def calibrate_precision(
    evaluate_fn,
    n_dims: int,
    n_restarts: int = 10,
) -> np.ndarray:
    """Learn the precision matrix that minimizes a loss function.

    Uses Cholesky parameterization to ensure positive-definiteness
    at every step, with multiple random restarts for global search.
    """
    n_params = n_dims * (n_dims + 1) // 2
    best_loss = float("inf")
    best_precision = None
    rng = np.random.default_rng(42)

    for _ in range(n_restarts):
        # Initialize near identity: log-diagonal ~ 0, off-diagonal ~ 0
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

The initial parameters are drawn from $\mathcal{N}(0, 0.1)$, which corresponds to Cholesky factors near the identity: the diagonal entries are $\exp(\theta_i)$ where $\theta_i \sim \mathcal{N}(0, 0.1)$, so they cluster around 1.0, and the off-diagonal entries are small, producing weak cross-dimensional coupling. Multiple restarts are essential because the loss landscape over Cholesky parameters is generally non-convex --- a fact that reflects the non-Euclidean geometry of the SPD manifold explored in Chapter 4.

In the `eris-econ` calibration module (`calibration.py`), this parameterization appears in the `estimate_sigma` function, which learns the precision matrix from observed economic choices using a softmax likelihood model. The key inner function `_unpack_cholesky` mirrors the structure above:

```python
def _unpack_cholesky(params: np.ndarray) -> np.ndarray:
    """Reconstruct Sigma^{-1} from Cholesky factor parameters."""
    L = np.zeros((N_DIMS, N_DIMS))
    idx = 0
    for i in range(N_DIMS):
        for j in range(i + 1):
            L[i, j] = params[idx]
            idx += 1
    # Ensure positive diagonal
    for i in range(N_DIMS):
        L[i, i] = np.exp(L[i, i])
    return L @ L.T  # Sigma^{-1} = L L^T
```

Note the difference in packing order: here the parameters are packed row-by-row through the lower triangle (including the diagonal), with the diagonal entries treated as log-values after extraction. The specific packing order is a convention choice; what matters is consistency between packing and unpacking.

---

## 15.5 Implementation: PyTorch

For deep learning applications where end-to-end gradient computation is required, the Cholesky parameterization integrates naturally with PyTorch's autograd. The key is to store the unconstrained parameters as `nn.Parameter` objects and reconstruct the SPD matrix in the forward pass:

```python
import torch
import torch.nn as nn


class CholeskyPrecision(nn.Module):
    """Learnable precision matrix via log-diagonal Cholesky parameterization.

    Stores n*(n+1)/2 unconstrained parameters. The forward() method
    returns a guaranteed-SPD precision matrix Sigma^{-1} = L @ L.T.
    """

    def __init__(self, n: int):
        super().__init__()
        self.n = n
        n_params = n * (n + 1) // 2

        # Initialize near identity
        init = torch.zeros(n_params)
        # Log-diagonal entries are the first n values; init to 0 -> exp(0) = 1
        self.raw_params = nn.Parameter(init)

        # Precompute indices for lower-triangular unpacking
        rows, cols = torch.tril_indices(n, n)
        self.register_buffer("tril_rows", rows)
        self.register_buffer("tril_cols", cols)
        diag_mask = rows == cols
        self.register_buffer("diag_mask", diag_mask)

    def forward(self) -> torch.Tensor:
        """Reconstruct the precision matrix from unconstrained parameters."""
        L = torch.zeros(self.n, self.n, dtype=self.raw_params.dtype,
                        device=self.raw_params.device)

        # Fill lower triangle
        values = self.raw_params.clone()
        # Exponentiate diagonal entries for positivity
        values[self.diag_mask] = values[self.diag_mask].exp()
        L[self.tril_rows, self.tril_cols] = values

        return L @ L.T

    def cholesky_factor(self) -> torch.Tensor:
        """Return the Cholesky factor L itself (useful for determinants)."""
        L = torch.zeros(self.n, self.n, dtype=self.raw_params.dtype,
                        device=self.raw_params.device)
        values = self.raw_params.clone()
        values[self.diag_mask] = values[self.diag_mask].exp()
        L[self.tril_rows, self.tril_cols] = values
        return L
```

Several design choices deserve comment.

**Index precomputation.** The `tril_indices` and `diag_mask` buffers are computed once at initialization and reused on every forward pass. This avoids repeated index computation during training.

**Gradient flow.** Because `exp` and matrix multiplication are both differentiable, gradients flow from any loss computed on the precision matrix back through $LL^\top$, through the exponentiation of the diagonal, and into the raw parameters. PyTorch's autograd handles the chain rule automatically. There are no discontinuities or projections that could interrupt gradient flow.

**Determinant computation.** The log-determinant of $M = LL^\top$ is $\log \det(M) = 2 \sum_i \log(\ell_{ii}) = 2 \sum_i \theta_i$, which is trivially cheap to compute from the raw parameters. This is important for Gaussian likelihood objectives, where $\log \det(\Sigma^{-1})$ appears as a normalizing constant.

A training loop for metric learning instantiates `CholeskyPrecision(n_dims)`, calls `model()` in the forward pass to get the SPD precision matrix, computes the Mahalanobis distance $\sqrt{\boldsymbol{\delta}^\top \Sigma^{-1}\boldsymbol{\delta}}$ (with a `clamp_min(1e-8)` before the square root to prevent gradient explosion near zero), and backpropagates through the entire chain. PyTorch's autograd handles the derivatives through the exponentiation and matrix multiplication automatically.

---

## 15.6 Gradient Flow Through the Cholesky Parameterization

Understanding the gradient structure helps diagnose training dynamics and motivates initialization strategies.

### 15.6.1 The Jacobian

Let $M = LL^\top$ where $L$ is lower triangular with positive diagonal. We want the Jacobian $\partial M_{ij} / \partial L_{kl}$ (where $k \geq l$). Since $M_{ij} = \sum_r L_{ir}L_{jr}$, the derivative is:

$$\frac{\partial M_{ij}}{\partial L_{kl}} = \delta_{ik}L_{jl} + \delta_{jk}L_{il}$$

where $\delta$ is the Kronecker delta. For diagonal entries of $L$ (where we actually optimize $\theta_k = \log L_{kk}$), the chain rule gives:

$$\frac{\partial M_{ij}}{\partial \theta_k} = \frac{\partial M_{ij}}{\partial L_{kk}} \cdot L_{kk} = (\delta_{ik}L_{jk} + \delta_{jk}L_{ik}) \cdot L_{kk}$$

This Jacobian has two important properties.

**Sparsity.** Each entry $L_{kl}$ affects only the entries $M_{ij}$ where $i = k$ or $j = k$. This means the Jacobian is sparse, and gradient computation through the Cholesky parameterization is efficient.

**Scale coupling.** The factor $L_{kk}$ in the chain rule for diagonal parameters means that the gradient with respect to $\theta_k$ is proportional to $L_{kk}$ itself. Large diagonal entries amplify gradients; small ones suppress them. The log-space parameterization compensates for this scaling effect, producing more uniform gradient magnitudes across the diagonal --- a critical property for stable optimization.

### 15.6.2 Conditioning and Numerical Stability

The condition number of $M = LL^\top$ is $\kappa(M) = \kappa(L)^2$. If $L$ has a large ratio between its largest and smallest diagonal entries, $M$ will be poorly conditioned, and numerical errors in the gradient computation will be amplified.

In practice, this means the log-diagonal parameters $\theta_i$ should be bounded to prevent extreme values. A range of $\theta_i \in [-5, 5]$ constrains the diagonal to $[\exp(-5), \exp(5)] \approx [0.007, 148]$, keeping the condition number of $L$ below $\exp(10) \approx 22{,}000$ --- well within the range of stable double-precision arithmetic. For L-BFGS-B, these bounds are passed directly via the `bounds` parameter. For PyTorch, parameter clamping after each optimizer step achieves the same effect.

---

## 15.7 Connection to Mahalanobis Distance Learning

### 15.7.1 Learning $\Sigma^{-1}$ via Cholesky

Chapter 2 introduced the Mahalanobis distance

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1} (\mathbf{a} - \mathbf{b})}$$

and showed that the precision matrix $\Sigma^{-1}$ acts as an attention mechanism, assigning importance weights to each dimension and pair of dimensions. The Cholesky parameterization provides the missing link: a practical method for *learning* this attention mechanism from data.

The connection is direct. We parameterize $\Sigma^{-1} = LL^\top$ where $L$ is the log-diagonal Cholesky factor. The Mahalanobis distance becomes:

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top LL^\top (\mathbf{a} - \mathbf{b})} = \|L^\top(\mathbf{a} - \mathbf{b})\|_2$$

This last form is revealing. The Mahalanobis distance is simply the Euclidean distance after the linear transformation $\mathbf{x} \mapsto L^\top \mathbf{x}$. Learning $\Sigma^{-1}$ is equivalent to learning a linear embedding: the Cholesky factor $L^\top$ maps from the original space to a "whitened" space where Euclidean distance is the correct metric. This connects metric learning to the broader family of linear embedding methods, including PCA, LDA, and the linear layers of neural networks.

### 15.7.2 The Softmax Likelihood

In the `eris-econ` framework, the precision matrix is learned from observed choices using a softmax likelihood model. Given an observed choice where an agent at state $\mathbf{s}$ chose option $\mathbf{c}$ over alternatives $\mathbf{r}_1, \ldots, \mathbf{r}_k$, the likelihood is:

$$P(\text{choose } \mathbf{c}) = \frac{\exp(-d_M^2(\mathbf{s}, \mathbf{c}))}{\exp(-d_M^2(\mathbf{s}, \mathbf{c})) + \sum_j \exp(-d_M^2(\mathbf{s}, \mathbf{r}_j))}$$

The squared Mahalanobis distance acts as a "cost" --- lower cost means higher probability of being chosen. The negative log-likelihood is:

$$\text{NLL} = d_M^2(\mathbf{s}, \mathbf{c}) + \log\left(\exp(-d_M^2(\mathbf{s}, \mathbf{c})) + \sum_j \exp(-d_M^2(\mathbf{s}, \mathbf{r}_j))\right)$$

With the Cholesky parameterization, $d_M^2(\mathbf{s}, \mathbf{c}) = \|L^\top(\mathbf{c} - \mathbf{s})\|^2$, and the entire NLL is differentiable with respect to the entries of $L$. This is the objective minimized in `calibration.py`:

```python
def neg_log_likelihood(params: np.ndarray) -> float:
    """Negative log-likelihood of observed choices."""
    sigma_inv = _unpack_cholesky(params)
    nll = 0.0

    for obs in observations:
        delta_chosen = obs.chosen - obs.start
        cost_chosen = float(delta_chosen @ sigma_inv @ delta_chosen)

        costs = [cost_chosen]
        for alt in obs.rejected:
            delta_alt = alt - obs.start
            costs.append(float(delta_alt @ sigma_inv @ delta_alt))

        # Log-sum-exp for numerical stability
        min_cost = min(costs)
        log_denom = min_cost + np.log(
            sum(np.exp(-(c - min_cost)) for c in costs)
        )
        nll += (cost_chosen - min_cost) + log_denom

    # L2 regularization on parameters
    nll += regularization * np.sum(params**2)
    return nll
```

The log-sum-exp trick (subtracting `min_cost` before exponentiating) prevents numerical overflow. The L2 regularization on the raw Cholesky parameters penalizes deviation from the identity, acting as a prior that the metric should not be too different from the Euclidean metric unless the data strongly supports it.

### 15.7.3 From Precision to Covariance and Back

The `eris-econ` framework parameterizes the *precision* matrix $\Sigma^{-1} = LL^\top$ rather than the *covariance* matrix $\Sigma$, because the Mahalanobis distance uses $\Sigma^{-1}$ directly. If you need $\Sigma$ (for example, to sample from a Gaussian or to inspect the learned variances), you invert:

$$\Sigma = (\Sigma^{-1})^{-1} = (LL^\top)^{-1} = (L^\top)^{-1}L^{-1} = (L^{-1})^\top L^{-1}$$

Since $L$ is triangular, its inverse $L^{-1}$ can be computed in $O(n^2)$ by back-substitution, which is cheaper than the general $O(n^3)$ matrix inversion. Alternatively, one can parameterize $\Sigma = LL^\top$ directly and compute $\Sigma^{-1}$ when needed --- the choice depends on which matrix appears more often in the computation.

In the `eris-econ` `estimate_sigma` function, the final step recovers $\Sigma$ from the learned $\Sigma^{-1}$:

```python
sigma_inv = _unpack_cholesky(result.x)
# Recover Sigma from Sigma^{-1}, with regularization for stability
sigma = np.linalg.inv(sigma_inv + 1e-10 * np.eye(N_DIMS))
```

The small regularization $10^{-10} \cdot I$ guards against numerical singularity in the inversion, though the Cholesky parameterization already ensures $\Sigma^{-1}$ is positive definite.

---

## 15.8 The Diagonal-Only Simplification

### 15.8.1 When Full Covariance Is Too Expensive

The full Cholesky parameterization has $n(n+1)/2$ free parameters. For the 9-dimensional ethical-economic space used in `eris-econ`, this is $9 \times 10 / 2 = 45$ parameters. When the training signal is limited --- the `eris-econ` model has 16 prediction targets --- fitting 45 parameters risks overfitting: the precision matrix may learn spurious cross-dimensional correlations that capture noise rather than structure.

The remedy is to restrict $\Sigma^{-1}$ (and therefore $L$) to be diagonal:

$$L = \text{diag}(\ell_1, \ldots, \ell_n), \quad \Sigma^{-1} = LL^\top = \text{diag}(\ell_1^2, \ldots, \ell_n^2)$$

This reduces the parameter count from $n(n+1)/2$ to $n$ --- from 45 to 9 for the `eris-econ` model. Each parameter has a direct interpretation: $\ell_i^2 = 1/\sigma_i^2$ is the precision (inverse variance) for dimension $i$. The Cholesky factorization becomes trivial (just square roots of the diagonal), and the log-diagonal parameterization reduces to:

$$\sigma_i^{-2} = \exp(2\theta_i), \quad \text{or equivalently,} \quad \sigma_i^2 = \exp(-2\theta_i)$$

In the `calibration_v2.py` module, this is implemented even more directly by parameterizing the log-variance:

```python
def _softmax_nll(
    log_diag: np.ndarray,
    observations: list[ObservedChoice],
    regularization: float = 0.01,
) -> float:
    """Softmax negative log-likelihood for diagonal sigma."""
    sigma_diag = np.exp(log_diag)
    sigma_inv_diag = 1.0 / sigma_diag
    nll = 0.0

    for obs in observations:
        delta_chosen = obs.chosen - obs.start
        cost_chosen = float(np.sum(sigma_inv_diag * delta_chosen ** 2))

        costs = [cost_chosen]
        for alt in obs.rejected:
            delta_alt = alt - obs.start
            costs.append(float(np.sum(sigma_inv_diag * delta_alt ** 2)))

        min_cost = min(costs)
        log_denom = min_cost + np.log(
            sum(np.exp(-(c - min_cost)) for c in costs)
        )
        nll += (cost_chosen - min_cost) + log_denom

    nll += regularization * np.sum(log_diag ** 2)
    return nll
```

Here `log_diag[i]` is $\log(\sigma_i^2)$, and `sigma_inv_diag[i]` $= 1/\sigma_i^2$ is the precision weight for dimension $i$. The squared Mahalanobis distance simplifies to the weighted sum of squared differences: $d_M^2 = \sum_i (a_i - b_i)^2 / \sigma_i^2$, which avoids the matrix multiplication entirely.

### 15.8.2 The Structural Fuzzing Connection

The diagonal parameterization is exactly what the structural fuzzing framework uses when searching over dimension subsets. In `structural_fuzz.py`, inactive dimensions receive variance $10^6$ (effectively zero precision weight), and active dimensions are optimized over a log-spaced grid:

```python
# From _optimize_subset: log-spaced variance grid
var_values = np.logspace(-2, 2, n_grid)  # 0.01 to 100

# 1D grid search over variance for the active dimension
for v in var_values:
    sigma_diag = np.full(N_DIMS, inactive_var)   # 1e6 for inactive
    sigma_diag[active_dims[0]] = v               # optimize this one
    sigma = np.diag(sigma_diag)
    mae, errors = _eval(sigma)
```

This is a grid-search version of diagonal Cholesky optimization. The log-spacing of `var_values` mirrors the log-diagonal parameterization: uniform steps in $\log(\sigma^2)$ correspond to multiplicatively uniform steps in $\sigma^2$, ensuring equal coverage across the [0.01, 100] range.

For 3D and higher subsets, the grid is too large and random search in log-space replaces it:

```python
# Random search in log-space for 3D+ subsets
rng = np.random.default_rng(42)
for _ in range(n_samples):
    sigma_diag = np.full(N_DIMS, inactive_var)
    for d in active_dims:
        sigma_diag[d] = 10 ** rng.uniform(-2, 2)  # log-uniform in [0.01, 100]
    sigma = np.diag(sigma_diag)
    mae, errors = _eval(sigma)
```

The structural fuzzing campaign over dimension subsets (Chapter 2, Section 2.6) is therefore a combinatorial search over the *sparsity pattern* of a diagonal precision matrix, combined with log-space optimization of the nonzero entries. Each subset corresponds to a particular mask on the diagonal of $\Sigma^{-1}$, and the framework asks: which mask and scale combination best explains the empirical data?

### 15.8.3 When to Use Full vs. Diagonal

The choice between full and diagonal covariance is a bias-variance tradeoff:

| Parameterization | Parameters | Captures | Risk |
|:---|:---:|:---|:---|
| Full Cholesky | $n(n+1)/2$ | Cross-dimensional correlations | Overfitting with limited data |
| Block-diagonal | $\sum_b n_b(n_b+1)/2$ | Within-group correlations | Misses between-group structure |
| Diagonal | $n$ | Per-dimension scales | Misses all correlations |

**Use full Cholesky** when you have abundant training signal (many more targets than $n(n+1)/2$ parameters) and domain knowledge suggests important cross-dimensional correlations. For example, in brain-computer interfaces, the correlation structure between EEG channels is critical for classification, and full SPD covariance matrices significantly outperform diagonal ones (Barachant et al., 2010).

**Use block-diagonal** when dimensions naturally cluster into groups with strong internal coupling but weak between-group interactions. In the `eris-econ` model, one might group the transferable dimensions (Consequences, Rights, Autonomy) into one block and the evaluative dimensions (Social Impact, Virtue, Legitimacy, Epistemic) into another, allowing correlations within each group while assuming independence between groups.

**Use diagonal** when the target-to-parameter ratio is low, or when interpretability is paramount. The structural fuzzing framework uses diagonal parameterization because (a) the 16 prediction targets do not reliably constrain 45 parameters, and (b) the ablation and sensitivity analyses are most interpretable when each parameter controls exactly one dimension.

### 15.8.4 Cross-Validation and Bootstrap Analysis

The `calibration_v2.py` module includes two tools for assessing the reliability of the diagonal parameterization:

**Cross-validation** selects the regularization strength. The targets are partitioned into $k$ folds; the diagonal precision is fitted on $k-1$ folds and evaluated on the held-out fold. The regularization $\lambda$ that minimizes the cross-validated negative log-likelihood is chosen. The `cross_validate` function in `calibration_v2.py` implements this, sweeping over regularization values $[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]$ and returning the best.

**Bootstrap confidence intervals** quantify parameter uncertainty. The training data is resampled with replacement $B$ times; the diagonal precision is fitted to each bootstrap sample; and the distribution of the resulting parameters reveals which dimensions are reliably important and which are unstable. In the `eris-econ` joint calibration, bootstrap analysis reveals that Consequences ($d_1$), Fairness ($d_3$), and Privacy/Trust ($d_5$) consistently receive high precision across bootstrap samples, while Autonomy ($d_4$) and Legitimacy ($d_8$) are unstable --- wide confidence intervals indicate the data does not strongly constrain their contribution. This aligns with the structural fuzzing results: the Pareto frontier of dimension subsets is dominated by configurations containing Consequences and Fairness.

---

## 15.9 Advanced Topics

### 15.9.1 The Cholesky Parameterization and Riemannian Optimization

The Cholesky parameterization provides an alternative to explicit Riemannian optimization on the SPD manifold (Chapter 4). Instead of computing the Riemannian gradient and exponential map at each step (which requires eigendecompositions), we work in the flat parameter space of Cholesky entries and let the nonlinear map $L \mapsto LL^\top$ implicitly handle the manifold geometry. This is computationally cheaper per step, though the induced metric on the parameter space is not the Euclidean metric, so standard optimizers like Adam or L-BFGS are not doing true Riemannian descent. In practice, the Cholesky approach works well for most applications; explicit Riemannian methods become advantageous when $n > 50$ or the condition number is extreme.

### 15.9.2 Determinant and Log-Likelihood

Many probabilistic models involve the log-determinant of the precision or covariance matrix. For a multivariate Gaussian, the log-likelihood of observing $\mathbf{x}$ given mean $\boldsymbol{\mu}$ and precision $\Lambda = \Sigma^{-1}$ is:

$$\log p(\mathbf{x}) = \frac{1}{2}\log\det(\Lambda) - \frac{1}{2}(\mathbf{x} - \boldsymbol{\mu})^\top \Lambda (\mathbf{x} - \boldsymbol{\mu}) - \frac{n}{2}\log(2\pi)$$

With the Cholesky parameterization $\Lambda = LL^\top$, the log-determinant is:

$$\log\det(\Lambda) = \log\det(LL^\top) = 2\log\det(L) = 2\sum_{i=1}^{n}\log L_{ii} = 2\sum_{i=1}^{n}\theta_i$$

This is a linear function of the log-diagonal parameters --- no eigendecomposition or matrix factorization required. It is the cheapest possible determinant computation, and it is numerically exact (no floating-point accumulation from multiplying many eigenvalues).

---

## 15.10 Synthesis: From Parameterization Patterns to Geometric Framework

This chapter completes the core parameterization toolkit of Part III. Let us step back and trace the thread that connects the patterns developed in Chapters 12--15 to the geometric framework established in Part I.

### The Central Theme

Part I established that computational models live in multi-dimensional spaces, and that the geometry of those spaces --- distances, directions, curvatures --- carries information that scalar summaries destroy. Part II developed algorithms for navigating and analyzing those spaces. Part III has addressed a different question: how do you *construct* and *learn* the geometric structures themselves?

The Cholesky parameterization is the final piece of this construction. Consider the full pipeline:

1. **Chapter 2** introduced the Mahalanobis distance and showed that the precision matrix $\Sigma^{-1}$ encodes the geometry of the evaluation space --- which dimensions matter, how they are coupled, and what "distance" means in context.

2. **Chapter 4** placed covariance matrices on the SPD manifold and showed that the correct distance between two covariance structures is not the Frobenius norm but the log-Euclidean metric, which respects the multiplicative structure of eigenvalues.

3. **This chapter** provided the engineering bridge: the log-diagonal Cholesky factorization turns the constrained optimization over the SPD manifold into an unconstrained optimization in $\mathbb{R}^{n(n+1)/2}$, where standard optimizers can operate without ever producing an invalid (non-SPD) result.

Together, these three chapters form a complete recipe for *learning the geometry of a problem from data*. The SPD manifold tells you the shape of the space you are searching in. The Cholesky parameterization tells you how to navigate that space efficiently. The Mahalanobis distance tells you how to use the result.

### The Diagonal Hierarchy

A recurring pattern in this book is the progression from full generality to practical simplification:

| Level | Object | Parameters | Captures |
|:---|:---|:---:|:---|
| Full SPD | $\Sigma^{-1} = LL^\top$, $L$ unrestricted | $n(n+1)/2$ | All cross-dimensional structure |
| Block-diagonal | $\Sigma^{-1}$ block-diagonal | $\sum n_b(n_b+1)/2$ | Within-group structure |
| Diagonal | $\Sigma^{-1} = \text{diag}(w_1, \ldots, w_n)$ | $n$ | Per-dimension scaling |
| Sparse subset | Diagonal with some $w_i = 0$ | $k < n$ | Active dimension selection |
| Scalar | $\Sigma^{-1} = \alpha I$ | 1 | Uniform scaling (Euclidean) |

The structural fuzzing framework operates primarily at the "sparse subset" level, searching over which dimensions to include and at what scale. The `eris-econ` calibration operates at the "diagonal" level, learning per-dimension variances with regularization. The full Cholesky parameterization waits in reserve for problems with enough data and enough cross-dimensional structure to justify its $n(n+1)/2$ parameters.

This hierarchy mirrors the bias-variance tradeoff that pervades statistical learning. Moving up the hierarchy (toward full SPD) reduces bias --- the model can represent richer geometric structure --- but increases variance, because more parameters must be estimated from the same data. Moving down (toward scalar) increases bias but reduces variance. The right level depends on the ratio of training signal to parameter count, and on domain knowledge about the importance of cross-dimensional coupling.

### Connecting Back to Geometry

The Cholesky parameterization is not merely a computational trick. It reveals something fundamental about the relationship between optimization and geometry. The SPD manifold is curved --- it is not a flat vector space. Optimizing over it with flat-space methods (unconstrained gradient descent on the raw matrix entries) fails because flat-space steps leave the manifold. The Cholesky parameterization provides a *global chart* for the manifold: a single coordinate system that covers the entire SPD cone, in which the curvature is absorbed into the nonlinear map $L \mapsto LL^\top$. This is the same strategy used throughout differential geometry --- find coordinates that make the problem tractable, even if the coordinates themselves introduce nonlinearity.

Chapter 4 used a different chart: the matrix logarithm, which maps SPD(n) to the flat space of symmetric matrices. The log map is an isometry under the log-Euclidean metric, making it ideal for distance computation and averaging. The Cholesky map is not an isometry under any standard metric, but it has the compensating advantage of being algebraically simple (just matrix multiplication) and parameterically efficient (no eigendecomposition required). In practice, the two charts serve complementary purposes: log-Euclidean for analysis and distance computation, Cholesky for optimization and learning.

This duality --- between the analytical elegance of log-Euclidean geometry and the practical efficiency of Cholesky parameterization --- is a microcosm of the broader theme of this book. Geometry provides the conceptual framework and the correctness guarantees. Engineering provides the efficient implementations. The best computational models use both: geometric insight to formulate the right problem, and careful parameterization to solve it at scale.

---

## Exercises

**15.1.** Implement `cholesky_params_to_precision` for $n = 3$ and verify that the output is always SPD by checking: (a) symmetry, (b) all eigenvalues positive, for 1000 random parameter vectors drawn from $\mathcal{N}(0, 1)$.

**15.2.** Starting from the identity ($\theta_i = 0$, off-diagonals $= 0$), compute the gradient of $\text{tr}(\Sigma^{-1}A)$ with respect to the Cholesky parameters, where $A$ is a fixed symmetric matrix. Verify your analytical gradient against finite differences.

**15.3.** Compare the convergence of L-BFGS-B on a toy metric learning problem using three parameterizations: (a) raw symmetric matrix entries with eigenvalue projection, (b) full Cholesky with positive-diagonal enforcement via absolute value, (c) log-diagonal Cholesky. Measure wall-clock time and final loss across 50 random initializations.

**15.4.** For the 9-dimensional `eris-econ` space, compute the ratio of parameters to targets for full Cholesky (45 parameters, 16 targets) and diagonal (9 parameters, 16 targets). Using AIC or BIC, determine which parameterization is preferred for this problem.

**15.5.** Implement block-diagonal Cholesky parameterization with two blocks: transferable dimensions {Consequences, Rights, Autonomy} and evaluative dimensions {Privacy/Trust, Social Impact, Virtue/Identity, Legitimacy, Epistemic}. Compare its AIC to the full and diagonal parameterizations on the `eris-econ` calibration problem.

**15.6.** The geodesic on SPD(n) under the log-Euclidean metric is $\gamma(t) = \exp((1-t)\log(S_0) + t\log(S_1))$. Show that the Cholesky factorization of $\gamma(t)$ is *not* in general a linear interpolation of the Cholesky factors of $S_0$ and $S_1$. Under what conditions does linear interpolation of Cholesky factors approximate the geodesic?

**15.7.** Extend the `CholeskyPrecision` PyTorch module to output both $\Sigma^{-1}$ and $\log\det(\Sigma^{-1})$ in a single forward pass, sharing the Cholesky factor computation. Use this to implement a full Gaussian negative log-likelihood loss.

---

## Notes and References

The Cholesky factorization is named for Andre-Louis Cholesky (1875--1918), a French military officer and geodesist who developed the method for solving systems of linear equations arising in geodetic survey computations. The factorization was published posthumously by Benoit in *Bulletin geodesique* 2, 1924.

The use of Cholesky parameterization for constrained covariance estimation is standard in the statistics literature. See Pinheiro and Bates, "Unconstrained parameterizations for variance-covariance matrices," *Statistics and Computing* 6(3), 1996, for an early systematic treatment. The log-diagonal variant is discussed in the context of variational inference by Kingma and Welling, "Auto-encoding variational Bayes," *ICLR* 2014, where it parameterizes the approximate posterior's covariance.

For Riemannian optimization on SPD manifolds, see Bonnabel, "Stochastic gradient descent on Riemannian manifolds," *IEEE Transactions on Automatic Control* 58(9), 2013; and Absil, Mahony, and Sepulchre, *Optimization Algorithms on Matrix Manifolds*, Princeton University Press, 2008.

The connection between metric learning and linear embeddings is developed in Weinberger and Saul, "Distance metric learning for large margin nearest neighbor classification," *JMLR* 10, 2009. The softmax likelihood for choice modeling has its roots in McFadden's random utility framework: McFadden, "Conditional logit analysis of qualitative choice behavior," in *Frontiers in Econometrics*, Academic Press, 1974.

The `eris-econ` implementation of Cholesky-parameterized calibration and the structural fuzzing framework's diagonal optimization are described in Bond (2026). The cross-validation and bootstrap methods for covariance estimation follow the treatments in Hastie, Tibshirani, and Friedman, *The Elements of Statistical Learning*, Springer, 2009, Chapter 7.
