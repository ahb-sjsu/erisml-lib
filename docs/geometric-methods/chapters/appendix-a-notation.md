# Appendix A: Mathematical Notation and Conventions

*Geometric Methods in Computational Modeling* --- Andrew H. Bond

---

This appendix provides a consolidated reference for the mathematical notation, symbols, and conventions used throughout the book. Symbols are organized by category, with brief descriptions and references to the chapters where they are introduced or used most extensively.

---

## A.1 Sets and Spaces

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| $\mathbb{R}$ | The set of real numbers | Throughout |
| $\mathbb{R}^n$ | Euclidean $n$-dimensional space; vectors $\mathbf{v} = (v_1, \ldots, v_n)$ | Ch. 1 |
| $\mathbb{R}^{n \times n}$ | The set of real $n \times n$ matrices | Ch. 2, 4 |
| $\mathbb{B}^d_c$ | Poincare ball of dimension $d$ with curvature $-c$: $\{x \in \mathbb{R}^d : c\|x\|^2 < 1\}$ | Ch. 3 |
| $\mathbb{B}^n$ | Poincare ball with default curvature $c = 1$: $\{x \in \mathbb{R}^n : \|x\| < 1\}$ | Ch. 1, 3 |
| $\mathbb{H}^k$ | Hyperbolic space of dimension $k$ and constant sectional curvature $-1$ | Ch. 3 |
| $\text{SPD}(n)$ | The manifold of $n \times n$ symmetric positive definite matrices | Ch. 4 |
| $\text{Sym}(n)$ | The vector space of $n \times n$ symmetric matrices | Ch. 4 |
| $T_x M$ | Tangent space to manifold $M$ at point $x$ | Ch. 3, 4 |
| $T_x \mathbb{B}^d_c$ | Tangent space to the Poincare ball at point $x$ | Ch. 3 |
| $T_S \text{SPD}(n)$ | Tangent space to the SPD manifold at $S$; equals $\text{Sym}(n)$ | Ch. 4 |
| $\ker(\phi)$ | Null space (kernel) of a linear map $\phi$ | Ch. 1 |
| $\phi^{-1}(c)$ | Preimage of $c$ under the map $\phi$ | Ch. 1 |
| $\mathrm{VR}(X, \varepsilon)$ | Vietoris-Rips simplicial complex of point cloud $X$ at scale $\varepsilon$ | Ch. 5 |

---

## A.2 Vectors and Matrices

### A.2.1 Vectors

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| $\mathbf{v}, \mathbf{a}, \mathbf{b}, \mathbf{s}, \mathbf{x}, \mathbf{y}$ | Vectors in $\mathbb{R}^n$, set in bold lowercase | Throughout |
| $v_i, s_i, a_i$ | The $i$-th component of a vector | Ch. 1, 2 |
| $\mathbf{s} = (s_1, s_2, \ldots, s_n)$ | A state vector with named components | Ch. 1 |
| $\mathbf{w}$ | Weight vector used in scalar projections $\phi(\mathbf{v}) = \mathbf{w}^\top \mathbf{v}$ | Ch. 1 |
| $\mathbf{0}$ | The zero vector (origin); used as base point on manifolds | Ch. 3 |
| $\|x\|$ | Euclidean norm $\sqrt{\sum_i x_i^2}$ of vector $x$ | Throughout |

### A.2.2 Matrices

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| $\Sigma$ | Covariance matrix (symmetric positive definite) | Ch. 2, 4 |
| $\Sigma^{-1}$ | Precision matrix (inverse covariance); acts as metric tensor | Ch. 2 |
| $I$ | Identity matrix | Ch. 2, 4 |
| $L$ | Lower-triangular Cholesky factor satisfying $\Sigma^{-1} = LL^\top$ | Ch. 2 |
| $U$ | Matrix of eigenvectors from eigendecomposition | Ch. 4, 5 |
| $\Lambda$ | Diagonal matrix of eigenvalues | Ch. 3, 4 |
| $K$ | Gaussian kernel matrix $K_{ij} = \exp(-D_{ij}^2 / 2\sigma^2)$ | Ch. 3 |
| $D$ | Distance matrix; $D_{ij}$ is distance between entities $i$ and $j$ | Ch. 3 |
| $W$ | Bilinear form or weight matrix in attention mechanisms | Ch. 2 |
| $\mathbf{C}$ | Frequency-band covariance matrix from a spectrogram | Ch. 4 |
| $\mathbf{B}$ | Band-averaged spectrogram representation $\in \mathbb{R}^{n_\text{bands} \times n_\text{frames}}$ | Ch. 4 |
| $\mathbf{X}$ | Mel spectrogram matrix $\in \mathbb{R}^{n_\text{mels} \times n_\text{frames}}$ | Ch. 4 |

### A.2.3 Matrix Operations

| Notation | Meaning | Reference |
|----------|---------|-----------|
| $A^\top$ | Transpose of matrix $A$ | Throughout |
| $A^{-1}$ | Inverse of matrix $A$ | Ch. 2, 4 |
| $A^{1/2}$ | Matrix square root (positive definite square root for SPD matrices) | Ch. 4 |
| $\|A\|_F$ | Frobenius norm: $\sqrt{\sum_{i,j} A_{ij}^2}$ | Ch. 4 |
| $\text{tr}(A)$ | Trace of matrix $A$: sum of diagonal entries | Ch. 4 |
| $\text{diag}(\lambda_1, \ldots, \lambda_n)$ | Diagonal matrix with entries $\lambda_1, \ldots, \lambda_n$ | Ch. 2, 4 |
| $\langle x, y \rangle$ | Inner product $\sum_i x_i y_i$ (Euclidean unless otherwise noted) | Ch. 3 |

---

## A.3 Distance Functions

### A.3.1 Euclidean Distance

$$d_{\text{Euclid}}(\mathbf{a}, \mathbf{b}) = \sqrt{\sum_{i=1}^{n} (a_i - b_i)^2} = \sqrt{(\mathbf{a} - \mathbf{b})^\top (\mathbf{a} - \mathbf{b})}$$

The default metric on $\mathbb{R}^n$. Treats all dimensions identically. Introduced in Chapter 1 and contrasted with alternatives in Chapters 2--4.

### A.3.2 Mahalanobis Distance

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1} (\mathbf{a} - \mathbf{b})}$$

Generalization of Euclidean distance that accounts for different scales and correlations among dimensions. When $\Sigma = I$, reduces to Euclidean distance. The precision matrix $\Sigma^{-1}$ stretches distances along directions of low variance and compresses them along directions of high variance. Chapter 2.

### A.3.3 Hyperbolic (Poincare Ball) Distance

$$d_c(x, y) = \frac{2}{\sqrt{c}} \, \text{arctanh}\!\Bigl(\sqrt{c}\,\bigl\|(-x) \oplus_c y\bigr\|\Bigr)$$

Geodesic distance on the Poincare ball $\mathbb{B}^d_c$. Diverges as points approach the boundary. Also expressed via arccosh (Chapter 1):

$$d_{\mathbb{B}}(x, y) = \text{arccosh}\left(1 + 2\frac{\|x - y\|^2}{(1 - \|x\|^2)(1 - \|y\|^2)}\right)$$

The two formulations are equivalent when $c = 1$. Chapter 1, Chapter 3.

### A.3.4 Log-Euclidean Distance

$$d_{LE}(S_1, S_2) = \|\log(S_1) - \log(S_2)\|_F$$

Distance on the SPD manifold, where $\log$ denotes the matrix logarithm. Respects the multiplicative structure of positive definite matrices: eigenvalue ratios contribute equally regardless of magnitude. Chapter 4.

### A.3.5 Affine-Invariant Distance

$$d_{AI}(S_1, S_2) = \|\log(S_1^{-1/2} S_2 S_1^{-1/2})\|_F$$

Alternative Riemannian metric on SPD(n), invariant under congruence transformations $S \mapsto ASA^\top$. Mentioned in Chapter 4, Section 4.7.

### A.3.6 Frobenius Distance

$$d_F(S_1, S_2) = \|S_1 - S_2\|_F$$

Euclidean distance on matrices treated as flat vectors. Does not respect SPD geometry. Used as a baseline in Chapter 4.

### A.3.7 Geodesic Distance from Origin

$$d_c(\mathbf{0}, h) = \frac{2}{\sqrt{c}}\,\text{arctanh}\!\bigl(\sqrt{c}\,\|h\|\bigr)$$

Special case of hyperbolic distance measuring depth/specificity of a point on the Poincare ball. Monotonically increasing in $\|h\|$. Chapter 3.

---

## A.4 Operators and Maps

### A.4.1 Mobius Addition

$$x \oplus_c y = \frac{(1 + 2c\,\langle x, y \rangle + c\,\|y\|^2)\,x + (1 - c\,\|x\|^2)\,y}{1 + 2c\,\langle x, y \rangle + c^2\,\|x\|^2\,\|y\|^2}$$

The group operation on the Poincare ball $\mathbb{B}^d_c$, generalizing vector addition to hyperbolic space. Non-commutative but gyrocommutative. Identity element is $\mathbf{0}$; inverse of $x$ is $-x$. Reduces to standard addition as $c \to 0$. Chapter 3.

### A.4.2 Exponential Map (Poincare Ball)

$$\exp_x^c(v) = x \oplus_c \left(\tanh\!\Bigl(\frac{\sqrt{c}\,\lambda_x^c\,\|v\|}{2}\Bigr)\,\frac{v}{\sqrt{c}\,\|v\|}\right)$$

Maps a tangent vector $v \in T_x\mathbb{B}^d_c$ to a point on the manifold by following the geodesic from $x$ in direction $v$ for unit time. Chapter 3.

### A.4.3 Logarithmic Map (Poincare Ball)

$$\log_x^c(y) = \frac{2}{\sqrt{c}\,\lambda_x^c}\,\text{arctanh}\!\bigl(\sqrt{c}\,\|{-x \oplus_c y}\|\bigr)\,\frac{-x \oplus_c y}{\|-x \oplus_c y\|}$$

Inverse of the exponential map. Returns the tangent vector at $x$ pointing toward $y$ with magnitude equal to the geodesic distance. Chapter 3.

### A.4.4 Matrix Logarithm

$$\log(S) = U \cdot \text{diag}(\log \lambda_1, \ldots, \log \lambda_n) \cdot U^\top$$

where $S = U\Lambda U^\top$ is the eigendecomposition of SPD matrix $S$ with eigenvalues $\lambda_i > 0$. Maps from SPD(n) to Sym(n) (the tangent space). Chapter 4.

### A.4.5 Matrix Exponential

$$\exp(X) = U \cdot \text{diag}(e^{\mu_1}, \ldots, e^{\mu_n}) \cdot U^\top$$

where $X = U \cdot \text{diag}(\mu_1, \ldots, \mu_n) \cdot U^\top$ is the eigendecomposition of symmetric matrix $X$. Maps from Sym(n) to SPD(n). The inverse of the matrix logarithm. Chapter 4.

### A.4.6 Conformal Factor

$$\lambda_x^c = \frac{2}{1 - c\,\|x\|^2}$$

The Riemannian conformal factor on the Poincare ball. Relates the Poincare metric tensor to the Euclidean metric: $g_x^{\mathbb{B}} = (\lambda_x^c)^2\, g^E$. Diverges as $\|x\| \to 1/\sqrt{c}$, reflecting the exponential magnification of distances near the boundary. Chapter 3.

### A.4.7 Lorentz Factor

$$\gamma_c(x) = \frac{1}{1 - c\,\|x\|^2}$$

Used in the Einstein midpoint computation. Differs from the conformal factor $\lambda_x^c$ by a factor of 2 because it is derived in the Klein model rather than the Poincare model. Chapter 3.

### A.4.8 Projection onto the Poincare Ball

$$\text{proj}(x) = \begin{cases} x & \text{if } \|x\| < r_{\max}/\sqrt{c} \\ \frac{r_{\max}}{\sqrt{c}\,\|x\|}\,x & \text{otherwise} \end{cases}$$

Projects points back inside the open ball after floating-point drift. The parameter $r_{\max} < 1$ (typically $0.95$) provides a safety margin. Chapter 3.

### A.4.9 Scalar Projection

$$\phi : \mathbb{R}^n \to \mathbb{R}^1, \quad \phi(\mathbf{v}) = \mathbf{w}^\top \mathbf{v}$$

Any linear projection from a multi-dimensional evaluation to a single scalar. The null space $\ker(\phi)$ has dimension $n - 1$, destroying $n - 1$ directions of information. Chapter 1.

---

## A.5 Aggregation and Means

### A.5.1 Einstein Midpoint

$$\bar{x} = \frac{\sum_{i=1}^{N} \gamma_c(x_i)\, w_i\, x_i}{\sum_{i=1}^{N} \gamma_c(x_i)\, w_i}$$

Weighted average of points on the Poincare ball, derived from the Klein model. Upweights points near the boundary via the Lorentz factor $\gamma_c$. Reduces to the Euclidean weighted mean as $c \to 0$. Chapter 3.

### A.5.2 Frechet Mean on SPD(n)

$$\bar{S}_{LE} = \exp\!\left(\sum_{i=1}^{k} w_i \log(S_i)\right)$$

The Frechet mean under the log-Euclidean metric. Minimizes $\sum_i w_i\, d_{LE}(S_i, M)^2$ over $M \in \text{SPD}(n)$. Closed-form: take the weighted mean in log-space, then exponentiate. Chapter 4.

### A.5.3 Geodesic Interpolation on SPD(n)

$$\gamma(t) = \exp\!\bigl((1-t)\log(S_0) + t\log(S_1)\bigr), \quad t \in [0, 1]$$

Linear interpolation in log-space, yielding the geodesic (shortest path) on the SPD manifold under the log-Euclidean metric. Chapter 4.

---

## A.6 Topology and Persistent Homology

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| $K_\varepsilon$ | Simplicial complex built from point cloud at scale $\varepsilon$ | Ch. 5 |
| $\mathrm{VR}(X, \varepsilon)$ | Vietoris-Rips complex: $k$-simplices are $(k+1)$-subsets with pairwise distance $\leq \varepsilon$ | Ch. 5 |
| $H_0$ | Zeroth homology: counts connected components | Ch. 5 |
| $H_1$ | First homology: counts one-dimensional loops (cycles) | Ch. 5 |
| $H_2$ | Second homology: counts two-dimensional voids (cavities) | Ch. 5 |
| $(b_i, d_i)$ | Birth-death pair for the $i$-th topological feature | Ch. 5 |
| $\ell_i = d_i - b_i$ | Persistence (lifetime) of the $i$-th feature | Ch. 5 |
| $\varepsilon$ | Scale parameter in the Rips filtration | Ch. 1, 5 |

### A.6.1 Persistence Diagram

A multiset of points $\{(b_i, d_i)\}$ in the plane where $b_i$ is the birth scale and $d_i$ is the death scale of a topological feature. Points lie on or above the diagonal $b = d$. Distance from the diagonal is proportional to persistence $\ell_i$. Points far from the diagonal represent robust structure; points near the diagonal represent noise. Chapter 5.

### A.6.2 Takens' Time-Delay Embedding

$$\mathbf{v}(t) = \bigl[x(t),\; x(t + \tau),\; x(t + 2\tau),\; \ldots,\; x(t + (d-1)\tau)\bigr]$$

Reconstructs the topology of a dynamical attractor from a scalar time series. For embedding dimension $d \geq 2m + 1$ (where $m$ is the attractor's box-counting dimension), the reconstruction is a diffeomorphism onto the original attractor. Chapter 5.

### A.6.3 Geodesic Deviation

$$\delta = \frac{L_\text{path} - d_\text{geo}}{d_\text{geo}}$$

where $L_\text{path} = \sum_{t=1}^{T-1} d_{LE}(\mathbf{C}_t, \mathbf{C}_{t+1})$ is the total path length and $d_\text{geo} = d_{LE}(\mathbf{C}_1, \mathbf{C}_T)$ is the endpoint geodesic distance. Measures how much a spectral trajectory on the SPD manifold deviates from a geodesic. $\delta = 0$ indicates perfectly straight (monotonic) spectral evolution. Chapter 4.

---

## A.7 Statistics and the Model Robustness Index

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| $\bar{\ell}$, $\bar{x}$ | Arithmetic mean | Throughout |
| $\sigma$, $\sigma_\ell$ | Standard deviation | Ch. 2, 5 |
| $\sigma_{ii} = \text{Var}(X_i)$ | Variance of dimension $i$ (diagonal of $\Sigma$) | Ch. 2 |
| $\sigma_{ij} = \text{Cov}(X_i, X_j)$ | Covariance between dimensions $i$ and $j$ (off-diagonal of $\Sigma$) | Ch. 2 |
| $Q_{75}(\ell)$ | 75th percentile of a distribution | Ch. 5 |
| $P_{75}$, $P_{95}$ | 75th and 95th percentile of perturbation deviation | Ch. 1 |
| MAE | Mean absolute error | Ch. 1 |
| MRI | Model Robustness Index (composite robustness score) | Ch. 1 |

### A.7.1 MRI Weights

The Model Robustness Index combines mean deviation, 75th percentile, and 95th percentile of perturbation response into a single robustness score. The composite explicitly accounts for tail risk, unlike standard deviation which treats all deviations symmetrically. Chapter 1 (introduced), Chapter 7 (developed).

### A.7.2 Softmax Choice Rule

$$P(\text{reject}) = \frac{\exp(-d_{\text{reject}} / T)}{\exp(-d_{\text{accept}} / T) + \exp(-d_{\text{reject}} / T)}$$

Probabilistic choice model based on Mahalanobis distances, where $T$ is a temperature parameter controlling decision sharpness. Chapter 2.

### A.7.3 Stake-Dependent Temperature

$$T(\text{stake}) = \max\left(T_{\text{floor}},\; T_{\text{base}} + \frac{T_\alpha}{\sqrt{\text{stake}}}\right)$$

Temperature as a function of economic stakes. High stakes yield low temperature (sharper decisions); low stakes yield high temperature (noisier decisions). Chapter 2.

### A.7.4 Persistence Diagram Summary Statistics

For a persistence diagram with finite lifetimes $\ell_1, \ldots, \ell_n$, the eight extracted features per homology dimension are:

| Index | Feature | Formula |
|-------|---------|---------|
| 0 | Count | $n$ |
| 1 | Mean lifetime | $\bar{\ell} = \frac{1}{n}\sum_i \ell_i$ |
| 2 | Std lifetime | $\sigma_\ell$ |
| 3 | Max lifetime | $\max_i \ell_i$ |
| 4 | 75th percentile | $Q_{75}(\ell)$ |
| 5 | Mean birth time | $\frac{1}{n}\sum_i b_i$ |
| 6 | Total persistence | $\sum_i \ell_i^2$ |
| 7 | Normalized persistence | $\sqrt{\sum_i \ell_i^2}\, / \, n$ |

With $H_0$ and $H_1$, this yields a 16-dimensional feature vector. Chapter 5.

---

## A.8 Conventions

### A.8.1 Indexing

- **Zero-based indexing** is used in all code and dimension numbering (e.g., "Dimension 0" is Consequences in the ethical-economic space).
- **One-based indexing** is used in mathematical exposition when conventional (e.g., eigenvalues $\lambda_1, \ldots, \lambda_n$, components $s_1, \ldots, s_n$).
- When ambiguity may arise, the text explicitly states which convention is in effect.

### A.8.2 Dimension Naming

Dimensions of state vectors are referred to by name rather than by index. The framework uses dimension enumerations so that code references "Complexity" or "Fairness" rather than "dimension 2." This convention prevents off-by-one errors and makes operations like "activate all dimensions except OO" declarative. Chapter 1.

Common dimension sets used in examples:

**Software defect prediction (5 dimensions):**

| Index | Name | Features |
|-------|------|----------|
| $s_1$ | Size | LOC, SLOC, blank lines |
| $s_2$ | Complexity | Cyclomatic, essential, design |
| $s_3$ | Halstead | Volume, difficulty, effort, time |
| $s_4$ | Object-Orientation | Coupling, cohesion, inheritance depth |
| $s_5$ | Process | Revisions, distinct authors, code churn |

**Ethical-economic space (9 dimensions):**

| Index | Name |
|-------|------|
| 0 | Consequences |
| 1 | Rights |
| 2 | Fairness |
| 3 | Autonomy |
| 4 | Trust |
| 5 | Social Impact |
| 6 | Virtue/Identity |
| 7 | Legitimacy |
| 8 | Epistemic |

### A.8.3 Sentinel Values

The sentinel value $10^6$ (denoted `inactive_value` in code) indicates that a dimension is *inactive* --- its corresponding feature group is excluded from the metric. When a parameter value exceeds the threshold $10^5$, the framework assigns zero weight to that dimension, effectively removing it from the distance computation:

$$w_i = \begin{cases} 1 / \max(p_i, 10^{-6}) & \text{if } p_i < 10^5 \\ 0 & \text{if } p_i \geq 10^5 \end{cases}$$

This mechanism enables subset enumeration: each combination of active/inactive dimensions defines a different sparsity pattern on $\Sigma^{-1}$. Chapters 1, 2.

### A.8.4 Log-Space Parameterization

Parameter values are distributed on a logarithmic scale over $[\epsilon, M]$:

$$v_k = 10^{\log_{10}(\alpha) + k \cdot \frac{\log_{10}(\beta) - \log_{10}(\alpha)}{n-1}}, \quad k = 0, 1, \ldots, n-1$$

Typical bounds are $\alpha = 0.01$, $\beta = 100$. This provides uniform resolution across orders of magnitude: a change from $0.01$ to $0.1$ and a change from $10$ to $100$ each span one decade and receive equal representation. Chapter 2.

For Cholesky diagonals, log-space is enforced via $\ell_{ii} = e^{\theta_i}$, mapping the unconstrained real line to strictly positive values. Chapter 2.

### A.8.5 Numerical Stability Constants

| Constant | Typical Value | Purpose | Reference |
|----------|--------------|---------|-----------|
| $\varepsilon$ (EPS) | $10^{-5}$ | Clamp for denominators and `arctanh` arguments on the Poincare ball | Ch. 3 |
| $r_{\max}$ (MAX_NORM) | $0.95$ | Maximum allowed norm for points inside the Poincare ball | Ch. 3 |
| Eigenvalue clamp | $10^{-10}$ | Minimum eigenvalue before taking matrix logarithm | Ch. 4 |
| Regularization $\epsilon$ | $10^{-4}$ | Ridge term added to sample covariance matrices: $\mathbf{C} + \epsilon I$ | Ch. 4 |
| Inactive threshold | $10^5$ | Parameter value above which a dimension is treated as inactive | Ch. 2 |
| Inactive value | $10^6$ | Default sentinel assigned to deactivated dimensions | Ch. 1, 2 |

### A.8.6 Curvature Convention

Hyperbolic curvature is parameterized as $-c$ where $c > 0$. The Poincare ball $\mathbb{B}^d_c$ has constant sectional curvature $-c$. Setting $c = 1$ gives standard hyperbolic geometry with curvature $-1$. Typical working range is $c \in [0.1, 2.0]$. Curvature may be treated as a learnable parameter. Chapter 3.

### A.8.7 Immutability

State vectors, once constructed, are not modified in place. All operations (perturbation, projection, interpolation) produce new vectors. This convention prevents aliasing bugs and ensures trajectory reproducibility. Chapter 1.

### A.8.8 Function Signatures

Throughout the book, mathematical functions and their computational implementations share consistent signatures:

| Mathematical | Code | Input | Output |
|-------------|------|-------|--------|
| $d_M(\mathbf{a}, \mathbf{b})$ | `mahalanobis_distance(a, b, sigma_inv)` | Two vectors, precision matrix | Scalar |
| $d_c(x, y)$ | `ball.distance(x, y)` | Two points on ball | Scalar |
| $x \oplus_c y$ | `ball.mobius_add(x, y)` | Two points on ball | Point on ball |
| $\exp_x^c(v)$ | `ball.exp_map(x, v)` | Base point, tangent vector | Point on ball |
| $\log_x^c(y)$ | `ball.log_map(x, y)` | Two points on ball | Tangent vector |
| $\log(S)$ | `SPDManifold.log_map(S)` | SPD matrix | Symmetric matrix |
| $\exp(X)$ | `SPDManifold.exp_map(X)` | Symmetric matrix | SPD matrix |
| $d_{LE}(S_1, S_2)$ | `SPDManifold.distance(S1, S2)` | Two SPD matrices | Scalar |
| $\bar{S}_{LE}$ | `SPDManifold.frechet_mean(matrices)` | Batch of SPD matrices | SPD matrix |

---

## A.9 Common Abbreviations

| Abbreviation | Expansion | Reference |
|-------------|-----------|-----------|
| ARC-AGI | Abstraction and Reasoning Corpus for Artificial General Intelligence | Ch. 1, 3 |
| BCI | Brain-Computer Interface | Ch. 4 |
| DTI | Diffusion Tensor Imaging | Ch. 4 |
| DSWP | Dominica Sperm Whale Project (dataset) | Ch. 5 |
| ICI | Inter-Click Interval | Ch. 5 |
| L-BFGS-B | Limited-memory BFGS with Box constraints | Ch. 2 |
| MLR | Multinomial Logistic Regression | Ch. 3 |
| MRI | Model Robustness Index | Ch. 1 |
| OO | Object-Orientation (dimension) | Ch. 1 |
| SPD | Symmetric Positive Definite | Ch. 2, 4 |
| TDA | Topological Data Analysis | Ch. 5 |
