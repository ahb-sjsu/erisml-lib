# Chapter 3: Hyperbolic Geometry for Hierarchical Data

*Geometric Methods in Computational Modeling — Andrew H. Bond*

---

In the preceding chapters we established the machinery of differential geometry on smooth manifolds and studied how curvature shapes the behavior of geodesics, parallel transport, and volume growth. We now turn to the first concrete non-Euclidean geometry that has become indispensable in modern computational modeling: *hyperbolic space*. Where Euclidean space is the natural home for grid-like, translation-invariant data, hyperbolic space is the natural home for trees, taxonomies, ontologies, and every other structure whose size grows exponentially with depth.

This chapter develops the Poincaré ball model from first principles, derives the closed-form operations needed for gradient-based optimization, and demonstrates three applications drawn from production systems: taxonomy embedding, hyperbolic multinomial logistic regression, and hyperbolic rule encoding for program synthesis.

---

## 3.1 Why Hyperbolic Space?

### 3.1.1 The Exponential Growth Problem

Consider a complete binary tree of depth $d$. It contains $2^{d+1} - 1$ nodes and $2^d$ leaves. More generally, a $k$-ary tree of depth $d$ contains $\Theta(k^d)$ nodes. This exponential growth is not an inconvenience — it is the defining structural property of hierarchical data.

Now suppose we wish to embed such a tree into a metric space $(X, d_X)$ so that the tree distance $d_T(u,v)$ between any two nodes $u,v$ is faithfully preserved. Formally, we seek a mapping $f: V \to X$ and constants $\alpha, \beta > 0$ such that for all $u,v \in V$:

$$\alpha \cdot d_T(u,v) \;\leq\; d_X\bigl(f(u), f(v)\bigr) \;\leq\; \beta \cdot d_T(u,v)$$

The *distortion* of the embedding is $\beta / \alpha$. The celebrated result of Bourgain (1985) shows that any $n$-point metric space embeds into $\ell_2$ with distortion $O(\log n)$. But for trees the situation in Euclidean space is much worse.

**Theorem 3.1 (Linial, London, and Rabinovich, 1995).** Any embedding of the complete binary tree of depth $d$ into $\mathbb{R}^k$ with the Euclidean metric incurs distortion $\Omega\!\bigl(\sqrt{\log n}\,\bigr)$ when $k$ is fixed, and achieving $O(1)$ distortion requires dimension $k = \Omega(n)$.

The intuition is geometric. In $\mathbb{R}^k$, the volume of a ball of radius $r$ grows as $r^k$ — polynomially in $r$. A tree, however, has exponentially many nodes at distance $d$ from the root. No polynomial-growth space can accommodate exponential branching without either stretching nearby nodes apart or crushing distant nodes together.

### 3.1.2 Exponential Volume Growth in Hyperbolic Space

Hyperbolic space $\mathbb{H}^k$ of constant sectional curvature $-1$ has a fundamentally different volume growth profile. The volume of a geodesic ball of radius $r$ in $\mathbb{H}^k$ satisfies:

$$\text{Vol}\bigl(B_r^{\mathbb{H}^k}\bigr) \;=\; \omega_{k-1} \int_0^r \sinh^{k-1}(t)\, dt \;\sim\; C_k \, e^{(k-1)r}$$

for large $r$, where $\omega_{k-1}$ is the volume of the unit $(k-1)$-sphere. The volume grows *exponentially* in the radius — exactly matching the branching pattern of trees.

**Theorem 3.2 (Gromov, 1987; Sarkar, 2011).** Any finite tree with $n$ nodes and weighted edges embeds into the Poincaré disk $\mathbb{H}^2$ with distortion $1 + \varepsilon$ for any $\varepsilon > 0$, using only two dimensions.

This is a dramatic improvement: from $\Omega(n)$ dimensions in Euclidean space to just 2 in hyperbolic space, with arbitrarily low distortion. In practice, one works with moderate dimensions ($d \in [16, 64]$) and adjustable curvature to balance fidelity against numerical stability.

### 3.1.3 The Poincaré Ball Model

Among the five classical models of hyperbolic geometry (Poincaré ball, Poincaré half-space, Klein, hyperboloid, and hemisphere), the Poincaré ball is the most convenient for machine learning because it lives inside a bounded subset of $\mathbb{R}^d$ and thus interfaces cleanly with standard optimizers and neural network layers.

**Definition 3.1 (Poincaré Ball).** For curvature parameter $c > 0$, the Poincaré ball of dimension $d$ is the open ball

$$\mathbb{B}^d_c \;=\; \bigl\{\, x \in \mathbb{R}^d \;:\; c\,\|x\|^2 < 1 \,\bigr\}$$

equipped with the Riemannian metric tensor

$$g_x^{\mathbb{B}} \;=\; \bigl(\lambda_x^c\bigr)^2 \, g^E, \qquad \lambda_x^c \;=\; \frac{2}{1 - c\,\|x\|^2}$$

where $g^E$ is the Euclidean metric and $\lambda_x^c$ is the *conformal factor*. The sectional curvature is $-c$ everywhere.

The conformal factor $\lambda_x^c$ diverges as $\|x\| \to 1/\sqrt{c}$, meaning that distances near the boundary of the ball are enormously magnified — a small Euclidean step near the boundary corresponds to a large geodesic distance. This is precisely why exponentially many tree leaves can be packed near the boundary while maintaining their pairwise distances.

---

## 3.2 Core Operations on the Poincaré Ball

All practical algorithms on $\mathbb{B}^d_c$ reduce to five operations: Möbius addition, geodesic distance, the exponential map, the logarithmic map, and projection back into the ball. We derive each in turn and provide numerically stable implementations.

### 3.2.1 Möbius Addition

The group operation on $\mathbb{B}^d_c$ generalizes vector addition. For $x, y \in \mathbb{B}^d_c$, the *Möbius addition* is:

$$x \oplus_c y \;=\; \frac{\bigl(1 + 2c\,\langle x, y \rangle + c\,\|y\|^2\bigr)\,x \;+\; \bigl(1 - c\,\|x\|^2\bigr)\,y}{1 + 2c\,\langle x, y \rangle + c^2\,\|x\|^2\,\|y\|^2}$$

Möbius addition is *not* commutative: in general $x \oplus_c y \neq y \oplus_c x$. It is, however, *gyrocommutative* — it satisfies a rotated commutativity law that is the foundation of gyrovector space theory (Ungar, 2008). The identity element is $\mathbf{0}$, and the inverse of $x$ is $-x$.

Numerical stability requires care in the denominator. When $c\|x\|^2$ and $c\|y\|^2$ are both close to 1, the denominator approaches zero. We clamp it away from zero:

```python
class PoincareBall:
    """Poincaré ball model of hyperbolic space with curvature -c."""

    def __init__(self, c: float = 1.0, dim: int = 2):
        self.c = c
        self.dim = dim
        self.EPS = 1e-5
        self.MAX_NORM = 0.95  # keep points inside 95% of boundary

    def mobius_add(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """
        Möbius addition x ⊕_c y on the Poincaré ball.

        Args:
            x: Tensor of shape (..., d), points on the ball
            y: Tensor of shape (..., d), points on the ball

        Returns:
            Tensor of shape (..., d), the Möbius sum
        """
        c = self.c
        x_dot_y = (x * y).sum(dim=-1, keepdim=True)
        x_sq = (x * x).sum(dim=-1, keepdim=True)
        y_sq = (y * y).sum(dim=-1, keepdim=True)

        numerator = (1 + 2 * c * x_dot_y + c * y_sq) * x + \
                    (1 - c * x_sq) * y
        denominator = 1 + 2 * c * x_dot_y + c ** 2 * x_sq * y_sq
        denominator = denominator.clamp(min=self.EPS)

        return self.project(numerator / denominator)
```

The final `project` call (Section 3.2.5) ensures the result remains inside the ball even under floating-point error.

### 3.2.2 Geodesic Distance

The geodesic distance between two points $x, y \in \mathbb{B}^d_c$ has a closed form in terms of Möbius addition:

$$d_c(x, y) \;=\; \frac{2}{\sqrt{c}} \, \text{arctanh}\!\Bigl(\sqrt{c}\,\bigl\|(-x) \oplus_c y\bigr\|\Bigr)$$

Since $\text{arctanh}(z) = \frac{1}{2}\ln\!\bigl(\frac{1+z}{1-z}\bigr)$, the distance diverges logarithmically as points approach the boundary — confirming the exponential capacity of the space.

```python
    def distance(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """
        Geodesic distance between x and y on the Poincaré ball.

        Returns:
            Tensor of shape (...,), pairwise distances
        """
        c = self.c
        neg_x = -x
        diff = self.mobius_add(neg_x, y)
        diff_norm = diff.norm(dim=-1).clamp(min=self.EPS)
        sqrt_c = c ** 0.5

        # Clamp argument to arctanh to avoid NaN at boundary
        arg = (sqrt_c * diff_norm).clamp(max=1.0 - self.EPS)
        return (2.0 / sqrt_c) * torch.atanh(arg)
```

**Remark 3.1.** The clamping of the `arctanh` argument is essential. Without it, points at the boundary produce `arctanh(1) = ∞`, which propagates `NaN` through all subsequent gradients. The choice of `1 - EPS` with `EPS = 1e-5` provides a good balance between numerical range and stability.

### 3.2.3 Exponential Map

The exponential map $\exp_x^c: T_x\mathbb{B}^d_c \to \mathbb{B}^d_c$ takes a point $x$ on the manifold and a tangent vector $v \in T_x\mathbb{B}^d_c$ and returns the point reached by following the geodesic from $x$ in direction $v$ for unit time:

$$\exp_x^c(v) \;=\; x \oplus_c \left(\tanh\!\Bigl(\frac{\sqrt{c}\,\lambda_x^c\,\|v\|}{2}\Bigr)\,\frac{v}{\sqrt{c}\,\|v\|}\right)$$

where $\lambda_x^c = \frac{2}{1 - c\|x\|^2}$ is the conformal factor at $x$.

```python
    def exp_map(self, x: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
        """
        Exponential map at point x with tangent vector v.

        Maps from the tangent space at x onto the manifold.

        Args:
            x: Tensor of shape (..., d), base point on the ball
            v: Tensor of shape (..., d), tangent vector at x

        Returns:
            Tensor of shape (..., d), resulting point on the ball
        """
        c = self.c
        sqrt_c = c ** 0.5
        v_norm = v.norm(dim=-1, keepdim=True).clamp(min=self.EPS)
        x_sq = (x * x).sum(dim=-1, keepdim=True)

        # Conformal factor
        lambda_x = 2.0 / (1.0 - c * x_sq).clamp(min=self.EPS)

        # Second argument to Möbius addition
        coeff = torch.tanh(sqrt_c * lambda_x * v_norm / 2.0) / (sqrt_c * v_norm)
        y = coeff * v

        return self.mobius_add(x, y)
```

The exponential map is the primary mechanism by which gradient updates in tangent space (which is Euclidean and compatible with standard optimizers like Adam) are transferred onto the manifold.

### 3.2.4 Logarithmic Map

The logarithmic map $\log_x^c: \mathbb{B}^d_c \to T_x\mathbb{B}^d_c$ is the inverse of the exponential map. Given two points $x, y \in \mathbb{B}^d_c$, it returns the tangent vector at $x$ pointing toward $y$ whose magnitude equals the geodesic distance:

$$\log_x^c(y) \;=\; \frac{2}{\sqrt{c}\,\lambda_x^c}\,\text{arctanh}\!\bigl(\sqrt{c}\,\|{-x \oplus_c y}\|\bigr)\,\frac{-x \oplus_c y}{\|-x \oplus_c y\|}$$

```python
    def log_map(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """
        Logarithmic map: inverse of exp_map.

        Returns the tangent vector at x that points toward y.

        Args:
            x: Tensor of shape (..., d), base point on the ball
            y: Tensor of shape (..., d), target point on the ball

        Returns:
            Tensor of shape (..., d), tangent vector at x
        """
        c = self.c
        sqrt_c = c ** 0.5
        diff = self.mobius_add(-x, y)
        diff_norm = diff.norm(dim=-1, keepdim=True).clamp(min=self.EPS)
        x_sq = (x * x).sum(dim=-1, keepdim=True)

        lambda_x = 2.0 / (1.0 - c * x_sq).clamp(min=self.EPS)
        arg = (sqrt_c * diff_norm).clamp(max=1.0 - self.EPS)

        coeff = (2.0 / (sqrt_c * lambda_x)) * torch.atanh(arg) / diff_norm
        return coeff * diff
```

Together, the exponential and logarithmic maps provide a *Riemannian optimization* workflow: parameters live on the manifold, gradients are computed in the ambient Euclidean space, retracted to the tangent space via the Riemannian metric, and then mapped back to the manifold via $\exp_x^c$.

### 3.2.5 Projection onto the Ball

Floating-point arithmetic can push points outside the open ball. Since operations on $\mathbb{B}^d_c$ are undefined for $c\|x\|^2 \geq 1$, we must project points back inside:

$$\text{proj}(x) \;=\; \begin{cases} x & \text{if } \|x\| < \frac{r_{\max}}{\sqrt{c}} \\[4pt] \frac{r_{\max}}{\sqrt{c}\,\|x\|}\,x & \text{otherwise} \end{cases}$$

where $r_{\max} < 1$ (typically 0.95) provides a safety margin:

```python
    def project(self, x: torch.Tensor) -> torch.Tensor:
        """
        Project points back inside the Poincaré ball.

        Ensures ||x|| < MAX_NORM / sqrt(c) to maintain numerical stability.
        """
        c = self.c
        max_radius = self.MAX_NORM / (c ** 0.5)
        x_norm = x.norm(dim=-1, keepdim=True).clamp(min=self.EPS)
        cond = x_norm > max_radius
        projected = x / x_norm * max_radius
        return torch.where(cond, projected, x)
```

The choice of $r_{\max} = 0.95$ deserves comment. Setting it too close to 1 risks numerical overflow in the conformal factor $\lambda_x^c$, while setting it too small artificially constrains the usable volume of the ball. At $r_{\max} = 0.95$, the conformal factor is $\lambda = 2/(1 - 0.9025) = 20.51$, which is large but comfortably within float32 range.

---

## 3.3 Embedding Taxonomies

We now apply the Poincaré ball to a concrete task: embedding a biological taxonomy so that taxonomic distance is faithfully represented by geodesic distance.

### 3.3.1 Problem Setup

Let $\mathcal{T}$ be a taxonomy (a rooted tree) with $n$ species. Define the *taxonomic distance matrix* $D \in \mathbb{R}^{n \times n}$ where $D_{ij}$ is the number of edges on the path from species $i$ to species $j$ in $\mathcal{T}$. Our goal is to find an embedding $f: \{1, \ldots, n\} \to \mathbb{B}^d_c$ that minimizes the stress:

$$\mathcal{L} \;=\; \sum_{i < j} \Bigl(d_c\bigl(f(i), f(j)\bigr) - D_{ij}\Bigr)^2$$

### 3.3.2 Spectral Initialization

Random initialization in hyperbolic space converges slowly and often gets trapped in poor local minima. A spectral initialization based on the Gaussian kernel over $D$ provides a much better starting point.

1. **Compute the Gaussian kernel matrix:**

$$K_{ij} \;=\; \exp\!\Bigl(-\frac{D_{ij}^2}{2\sigma^2}\Bigr)$$

   where $\sigma$ controls the bandwidth. A reasonable default is $\sigma = \text{median}(D)$.

2. **Eigendecomposition:** Compute $K = U \Lambda U^\top$ where $\Lambda = \text{diag}(\lambda_1, \ldots, \lambda_n)$ with $\lambda_1 \geq \cdots \geq \lambda_n$.

3. **Select the top $d$ eigenvectors:** Form the initial coordinates as $X_0 = U_{:,1:d}\,\Lambda_{1:d}^{1/2}$, weighting each eigenvector by the square root of its eigenvalue.

4. **Scale to fit inside the ball:** Normalize so that $\max_i \|x_i\| < r_{\max}/\sqrt{c}$.

```python
import numpy as np
from scipy.linalg import eigh

def spectral_init(distance_matrix: np.ndarray, dim: int = 2,
                  c: float = 1.0, max_norm: float = 0.9) -> np.ndarray:
    """
    Spectral initialization for Poincaré ball embedding.

    Args:
        distance_matrix: (n, n) symmetric matrix of pairwise distances
        dim: target embedding dimension
        c: curvature parameter (negative curvature = -c)
        max_norm: maximum allowed norm after scaling

    Returns:
        (n, dim) array of initial coordinates inside the ball
    """
    n = distance_matrix.shape[0]
    sigma = np.median(distance_matrix[distance_matrix > 0])

    # Gaussian kernel
    K = np.exp(-distance_matrix ** 2 / (2 * sigma ** 2))

    # Eigendecomposition (eigh returns ascending order)
    eigenvalues, eigenvectors = eigh(K)

    # Take top-d eigenvalues (they are at the end for eigh)
    top_eigenvalues = eigenvalues[-dim:][::-1]
    top_eigenvectors = eigenvectors[:, -dim:][:, ::-1]

    # Weight by sqrt of eigenvalue
    coords = top_eigenvectors * np.sqrt(np.maximum(top_eigenvalues, 0.0))

    # Scale to fit inside ball
    max_radius = max_norm / np.sqrt(c)
    current_max = np.max(np.linalg.norm(coords, axis=1))
    if current_max > 1e-8:
        coords = coords * (max_radius / current_max)

    return coords
```

### 3.3.3 Example: Cetacean Taxonomy

To make this concrete, consider embedding a small cetacean taxonomy. The order Cetacea splits into Mysticeti (baleen whales) and Odontoceti (toothed whales). Under Mysticeti we have families like Balaenopteridae (rorquals: blue whale, humpback) and Balaenidae (right whales: bowhead). Under Odontoceti we have Delphinidae (dolphins: bottlenose, orca) and Phocoenidae (porpoises: harbor porpoise).

In a Poincaré disk embedding ($d = 2$, $c = 1$), the root (Cetacea) sits near the origin. The Mysticeti and Odontoceti subtrees occupy opposite sectors of the disk, each fanning out toward the boundary. Species within the same family cluster together near the boundary, separated by small geodesic distances despite being at nearly the same Euclidean radius. Species in different suborders are separated by large geodesic distances because any path between them must pass through the low-curvature interior near the root.

This "onion-like" structure — general concepts near the center, specific instances near the boundary — is the hallmark of hyperbolic embeddings and directly mirrors the hierarchical structure of the data.

---

## 3.4 Hyperbolic Multinomial Logistic Regression

Having embedded data into the Poincaré ball, we need classifiers that operate natively in hyperbolic space. Ganea et al. (2018) showed that the standard multinomial logistic regression (MLR) generalizes naturally to the Poincaré ball.

### 3.4.1 From Euclidean to Hyperbolic

In Euclidean MLR, the logit for class $k$ is $\langle a_k, x \rangle + b_k$, which measures signed distance from $x$ to the hyperplane $\{z : \langle a_k, z \rangle + b_k = 0\}$. In hyperbolic space, hyperplanes are replaced by *geodesic hyperplanes* (totally geodesic submanifolds of codimension 1), and signed distance to such a hyperplane takes the form:

$$\ell_k(x) \;=\; \frac{\lambda_{p_k}^c\,\|a_k\|}{\sqrt{c}} \,\sinh^{-1}\!\Bigl(\frac{2\sqrt{c}\,\langle (-p_k) \oplus_c x,\; a_k \rangle}{(1 - c\,\|(-p_k) \oplus_c x\|^2)\,\|a_k\|}\Bigr)$$

where $p_k \in \mathbb{B}^d_c$ is the *prototype* for class $k$ and $a_k \in T_{p_k}\mathbb{B}^d_c$ is the normal direction.

In practice, a simpler distance-based formulation often works as well or better:

### 3.4.2 Prototype-Based Classification

For each class $k$, learn a prototype $p_k \in \mathbb{B}^d_c$ and a temperature $\tau_k > 0$. The logit for class $k$ is the negative scaled geodesic distance:

$$\ell_k(x) \;=\; -\frac{d_c(x, p_k)}{\tau_k}$$

The class probabilities follow from a softmax:

$$P(y = k \mid x) \;=\; \frac{\exp(\ell_k(x))}{\sum_{j=1}^{K} \exp(\ell_j(x))}$$

Points closest to prototype $p_k$ in geodesic distance receive the highest probability for class $k$. The per-class temperature $\tau_k$ controls how sharply the decision boundary is drawn: small $\tau_k$ produces a hard boundary, large $\tau_k$ a soft one.

```python
import torch
import torch.nn as nn

class HyperbolicMLR(nn.Module):
    """
    Hyperbolic multinomial logistic regression via prototypes.

    Prototypes are parameterized in tangent space at the origin
    and mapped to the ball via exp_map for stable optimization.
    """

    def __init__(self, dim: int, n_classes: int, c: float = 1.0):
        super().__init__()
        self.ball = PoincareBall(c=c, dim=dim)
        self.dim = dim
        self.n_classes = n_classes

        # Learnable prototype directions in tangent space at origin
        self.proto_tangent = nn.Parameter(torch.randn(n_classes, dim) * 0.01)

        # Per-class log-temperature (log to ensure positivity)
        self.log_tau = nn.Parameter(torch.zeros(n_classes))

    def get_prototypes(self) -> torch.Tensor:
        """Map tangent-space parameters to Poincaré ball prototypes."""
        origin = torch.zeros(1, self.dim, device=self.proto_tangent.device)
        return self.ball.exp_map(
            origin.expand(self.n_classes, -1),
            self.proto_tangent
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Compute class logits for input points.

        Args:
            x: (batch, dim) points on the Poincaré ball

        Returns:
            (batch, n_classes) logits
        """
        prototypes = self.get_prototypes()  # (n_classes, dim)
        tau = self.log_tau.exp()             # (n_classes,)

        # Compute pairwise distances: (batch, n_classes)
        # Expand x to (batch, 1, dim) and prototypes to (1, n_classes, dim)
        dists = self.ball.distance(
            x.unsqueeze(1).expand(-1, self.n_classes, -1),
            prototypes.unsqueeze(0).expand(x.shape[0], -1, -1)
        )

        # Logits = negative distance scaled by temperature
        logits = -dists / tau.unsqueeze(0)
        return logits
```

A key design choice: prototypes are *parameterized in the tangent space at the origin* and mapped to the ball via `exp_map` at each forward pass. This avoids the need for Riemannian optimizers — standard Euclidean Adam updates the tangent-space parameters, and the exponential map handles the manifold constraint. This "tangent space parameterization" trick is widely used and generally more stable than direct Riemannian SGD for moderate curvatures.

---

## 3.5 Hyperbolic Rule Encoding

The most sophisticated application of hyperbolic geometry in this book comes from the ARC-AGI system, where hyperbolic space is used to encode *rules* — the discrete transformation programs that map input grids to output grids. The key insight is that rules have natural hierarchical structure: general rules (e.g., "apply color mapping") subsume specific sub-rules (e.g., "map red to blue in the upper-left quadrant"), forming a tree of increasing specificity.

### 3.5.1 Architecture

The `HyperbolicRuleEncoder` is a neural module that maps from a Euclidean latent space $\mathbb{R}^m$ (produced by an upstream encoder) to the Poincaré ball $\mathbb{B}^d_c$:

$$h \;=\; \exp_{\mathbf{0}}^c\!\bigl(\text{MLP}(z)\bigr), \qquad z \in \mathbb{R}^m,\; h \in \mathbb{B}^d_c$$

The MLP has two layers with a GELU activation:

```python
class HyperbolicRuleEncoder(nn.Module):
    """
    Maps Euclidean latent codes to the Poincaré ball for
    hierarchical rule representation.

    Rules closer to the origin are more general (lower depth
    in the rule tree). Rules near the boundary are highly
    specific. Rule similarity is measured by geodesic distance.
    """

    def __init__(self, input_dim: int, hyperbolic_dim: int, c: float = 1.0):
        super().__init__()
        self.ball = PoincareBall(c=c, dim=hyperbolic_dim)

        # Two-layer MLP: Euclidean z-space → tangent space at origin
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, 2 * hyperbolic_dim),
            nn.GELU(),
            nn.Linear(2 * hyperbolic_dim, hyperbolic_dim),
        )

        # Initialize final layer with small weights for near-origin start
        nn.init.uniform_(self.mlp[-1].weight, -0.001, 0.001)
        nn.init.zeros_(self.mlp[-1].bias)

    def encode(self, z: torch.Tensor) -> torch.Tensor:
        """
        Encode latent vectors into the Poincaré ball.

        Args:
            z: (batch, input_dim) Euclidean latent codes

        Returns:
            h: (batch, hyperbolic_dim) points on the Poincaré ball
        """
        tangent_vec = self.mlp(z)
        origin = torch.zeros_like(tangent_vec)
        h = self.ball.exp_map(origin, tangent_vec)
        return h

    def rule_similarity(self, h1: torch.Tensor, h2: torch.Tensor) -> torch.Tensor:
        """
        Compute similarity between two rule embeddings.

        Uses exp(-distance) so similar rules have similarity near 1
        and dissimilar rules have similarity near 0.

        Args:
            h1, h2: (batch, hyperbolic_dim) rule embeddings

        Returns:
            (batch,) similarity scores in (0, 1]
        """
        dist = self.ball.distance(h1, h2)
        return torch.exp(-dist)

    def rule_depth(self, h: torch.Tensor) -> torch.Tensor:
        """
        Estimate rule specificity from its position on the ball.

        Rules near the origin (small norm) are general.
        Rules near the boundary (large norm) are specific.
        Returns geodesic distance from origin, which grows
        logarithmically as points approach the boundary.

        Args:
            h: (batch, hyperbolic_dim) rule embeddings

        Returns:
            (batch,) depth/specificity scores
        """
        origin = torch.zeros_like(h)
        return self.ball.distance(origin, h)
```

### 3.5.2 Interpreting the Embedding

The `HyperbolicRuleEncoder` exploits three properties of the Poincaré ball:

1. **Rule similarity via geodesic distance.** Two rules that perform similar transformations will have nearby latent codes $z_1, z_2$, which the MLP maps to nearby tangent vectors, which `exp_map` sends to nearby points on the ball. Their similarity $\exp(-d_c(h_1, h_2))$ is close to 1. Rules that perform unrelated transformations end up far apart, with similarity close to 0.

2. **Rule depth/specificity via norm.** The geodesic distance from the origin to a point $h \in \mathbb{B}^d_c$ is:

$$d_c(\mathbf{0}, h) \;=\; \frac{2}{\sqrt{c}}\,\text{arctanh}\!\bigl(\sqrt{c}\,\|h\|\bigr)$$

   This is a monotonically increasing function of $\|h\|$ that diverges as $\|h\| \to 1/\sqrt{c}$. The MLP is initialized with near-zero weights so that all rules start near the origin (maximum generality). During training, rules that apply to specific sub-cases are pushed toward the boundary, while rules that capture broad patterns remain near the center.

3. **Exponential packing capacity.** Because the volume of the ball grows exponentially near the boundary, there is room for exponentially many specific rules without crowding. A single general rule near the center can have $2^k$ specialized descendants at depth $k$, all well-separated.

### 3.5.3 Training Signal

The encoder is trained end-to-end with the downstream task. The loss typically includes:

- A **task loss** (e.g., cross-entropy on predicted output grids) that drives the encoder to produce useful rule representations.
- A **hierarchical regularizer** that encourages parent rules to have smaller norm than their children:

$$\mathcal{L}_{\text{hier}} \;=\; \sum_{(r, r') \in \text{parent-child}} \max\bigl(0,\; \|h_r\| - \|h_{r'}\| + \alpha\bigr)$$

  where $\alpha > 0$ is a margin ensuring children are at least $\alpha$ further from the origin than their parents.

---

## 3.6 Einstein Midpoint for Aggregation

A recurring operation in hyperbolic neural networks is *weighted averaging* — computing the centroid of a set of points on the ball. The Euclidean weighted mean $\bar{x} = \sum_i w_i x_i / \sum_i w_i$ does not generalize directly because $\mathbb{B}^d_c$ is not a vector space.

### 3.6.1 Derivation

The *Einstein midpoint* provides a principled solution. It arises from the Klein model of hyperbolic geometry (which has straight-line geodesics) and can be transferred to the Poincaré ball model.

For points $x_1, \ldots, x_N \in \mathbb{B}^d_c$ with non-negative weights $w_1, \ldots, w_N$, the Einstein midpoint is:

$$\bar{x} \;=\; \frac{\sum_{i=1}^{N} \gamma_i\, w_i\, x_i}{\sum_{i=1}^{N} \gamma_i\, w_i}$$

where $\gamma_i = \gamma_c(x_i)$ is the *Lorentz factor* (conformal factor):

$$\gamma_c(x) \;=\; \frac{1}{1 - c\,\|x\|^2}$$

The Lorentz factor upweights points near the boundary, which is geometrically correct: points near the boundary of the Poincaré ball are "further out" in the actual hyperbolic space, and their positions should contribute more strongly to the midpoint computation to avoid the midpoint being biased toward the origin.

**Proposition 3.1.** The Einstein midpoint of a set of points in $\mathbb{B}^d_c$ lies in $\mathbb{B}^d_c$ (i.e., the formula is closed), and it reduces to the Euclidean weighted mean in the limit $c \to 0$.

*Proof sketch.* By convexity of the open ball and the fact that the $\gamma$-weighted combination is a convex combination (all $\gamma_i w_i \geq 0$ and we normalize by their sum), the result lies in the convex hull of the $x_i$, which is contained in $\mathbb{B}^d_c$. The limit $c \to 0$ sends all $\gamma_i \to 1$, recovering the Euclidean formula. $\square$

```python
    def einstein_midpoint(self, x: torch.Tensor,
                          weights: torch.Tensor = None) -> torch.Tensor:
        """
        Compute the weighted Einstein midpoint of points on the ball.

        Used for aggregating multiple rule representations into
        a single summary point on the manifold.

        Args:
            x: (N, dim) or (batch, N, dim) points on the ball
            weights: (N,) or (batch, N) non-negative weights.
                     If None, uniform weights are used.

        Returns:
            (dim,) or (batch, dim) the Einstein midpoint
        """
        c = self.c

        # Lorentz (conformal) factors: γ_i = 1 / (1 - c||x_i||²)
        x_sq = (x * x).sum(dim=-1)  # (..., N)
        gamma = 1.0 / (1.0 - c * x_sq).clamp(min=self.EPS)  # (..., N)

        if weights is None:
            weights = torch.ones_like(gamma)

        # Weighted combination: Σ γ_i w_i x_i / Σ γ_i w_i
        scale = gamma * weights  # (..., N)
        numerator = (scale.unsqueeze(-1) * x).sum(dim=-2)  # (..., dim)
        denominator = scale.sum(dim=-1, keepdim=True).clamp(min=self.EPS)

        midpoint = numerator / denominator
        return self.project(midpoint)
```

### 3.6.2 Application: Aggregating Rule Embeddings

In the ARC-AGI system, a single input-output example may activate multiple candidate rules. The Einstein midpoint aggregates their hyperbolic representations into a single summary vector:

```python
def aggregate_rules(encoder: HyperbolicRuleEncoder,
                    rule_latents: torch.Tensor,
                    attention_weights: torch.Tensor) -> torch.Tensor:
    """
    Aggregate multiple rule embeddings into a single representation.

    Args:
        encoder: the hyperbolic rule encoder
        rule_latents: (batch, n_rules, input_dim) Euclidean latents
        attention_weights: (batch, n_rules) attention-derived weights

    Returns:
        (batch, hyperbolic_dim) aggregated rule embedding
    """
    # Encode each rule into the Poincaré ball
    batch, n_rules, _ = rule_latents.shape
    flat = rule_latents.reshape(batch * n_rules, -1)
    h_flat = encoder.encode(flat)
    h = h_flat.reshape(batch, n_rules, -1)  # (batch, n_rules, hyp_dim)

    # Aggregate via Einstein midpoint
    return encoder.ball.einstein_midpoint(h, weights=attention_weights)
```

The attention weights typically come from a cross-attention mechanism that scores how relevant each candidate rule is to the current input. The Einstein midpoint then produces a single point on the ball that respects the hyperbolic geometry — it is not simply the Euclidean average of the embeddings, which would systematically underestimate the "depth" of the aggregate rule.

---

## 3.7 Numerical Considerations and Best Practices

Working with hyperbolic embeddings introduces numerical challenges that do not arise in Euclidean models. We summarize the key lessons:

1. **Always clamp denominators and `arctanh` arguments.** The formulas for Möbius addition, distance, and the exponential map all contain terms that can approach zero or one under finite precision. A minimum clamp of $\varepsilon = 10^{-5}$ is usually sufficient for float32.

2. **Project after every operation.** Any sequence of Möbius additions or exponential maps can drift outside the ball due to accumulated floating-point error. Call `project()` after every manifold operation.

3. **Parameterize in tangent space.** Rather than directly optimizing points on the ball (which requires Riemannian gradient descent), parameterize them as tangent vectors at the origin and apply `exp_map` at each forward pass. This allows standard Euclidean optimizers and avoids the need for specialized Riemannian step-size schedules.

4. **Use moderate curvature.** Very large $c$ (high curvature) packs the effective space into a tiny Euclidean ball, amplifying floating-point errors. Very small $c$ (low curvature) approaches flat Euclidean geometry and loses the benefits of hyperbolic embedding. Values of $c \in [0.1, 2.0]$ are typical. Curvature can also be made a learnable parameter.

5. **Initialize near the origin.** New embeddings and MLP output layers should be initialized with small weights so that initial points lie near the origin. This provides a "blank slate" from which the optimizer can gradually push points outward as hierarchical structure is learned.

6. **Mixed-precision caution.** Float16 has only 3.3 decimal digits of precision. The conformal factor $\lambda_x^c = 2/(1 - c\|x\|^2)$ at $\|x\| = 0.99$ is $\approx 100$, and at $\|x\| = 0.999$ is $\approx 1000$. In float16, $1 - 0.999^2 = 1 - 0.998 = 0.002$ loses significant precision. Use float32 for all hyperbolic operations even when the rest of the model uses mixed precision.

---

## 3.8 Summary and Connections

Hyperbolic geometry provides a mathematically principled framework for representing hierarchical data in continuous space. The Poincaré ball model offers:

- **Exponential volume growth** matching the branching factor of trees, enabling low-distortion embedding in fixed dimension.
- **Closed-form operations** (Möbius addition, geodesic distance, exp/log maps) that are differentiable and compatible with gradient-based optimization.
- **Interpretable structure** where distance from the origin encodes depth/specificity and geodesic distance encodes similarity.

We saw three applications:

- *Taxonomy embedding* (Section 3.3): encoding species trees with spectral initialization and stress minimization.
- *Hyperbolic MLR* (Section 3.4): prototype-based classification using geodesic distance as the logit.
- *Hyperbolic rule encoding* (Section 3.5): mapping program synthesis rules to the Poincaré ball so that general rules sit near the center and specific sub-rules fan out toward the boundary.

The Einstein midpoint (Section 3.6) provides the aggregation primitive needed to combine multiple hyperbolic representations — a building block we will use extensively in Part II when we develop hyperbolic attention mechanisms and tree-structured decoders.

In the next chapter, we turn to *product manifolds* — spaces formed by taking Cartesian products of Euclidean, hyperbolic, and spherical components. These mixed-curvature spaces can simultaneously capture hierarchical, flat, and cyclical structure in a single embedding, extending the ideas of this chapter to data with heterogeneous geometric character.

---

### Exercises

**3.1.** Prove that Möbius addition reduces to standard vector addition in the limit $c \to 0$. *(Hint: expand the numerator and denominator to first order in $c$.)*

**3.2.** Show that $d_c(\mathbf{0}, x) = \frac{2}{\sqrt{c}}\,\text{arctanh}(\sqrt{c}\,\|x\|)$ by computing $(-\mathbf{0}) \oplus_c x$ and substituting into the distance formula.

**3.3.** Implement the full taxonomy embedding pipeline for the cetacean example: construct the distance matrix for a 12-species tree, compute the spectral initialization, and refine by gradient descent on the stress loss. Plot the resulting Poincaré disk embedding and verify that taxonomic neighbors are geodesically close.

**3.4.** The conformal factor $\gamma_c(x) = 1/(1 - c\|x\|^2)$ and the Riemannian conformal factor $\lambda_x^c = 2/(1 - c\|x\|^2)$ differ by a factor of 2. Explain why the Einstein midpoint uses $\gamma$ rather than $\lambda$. *(Hint: the Einstein midpoint is derived in the Klein model, not the Poincaré model.)*

**3.5.** Extend the `HyperbolicMLR` classifier to use the full Ganea et al. (2018) formulation with geodesic hyperplanes rather than prototype distances. Compare classification accuracy on a synthetic hierarchical dataset.

---

### Bibliographic Notes

The use of hyperbolic geometry for tree embedding traces to Gromov's theory of $\delta$-hyperbolic metric spaces (Gromov, 1987). Sarkar (2011) gave the first constructive low-distortion embedding of trees into $\mathbb{H}^2$. The Poincaré ball model for machine learning was popularized by Nickel and Kiela (2017), who learned word embeddings with dramatically better hierarchy capture than Euclidean models. Ganea et al. (2018) developed hyperbolic neural network layers including the MLR classifier. The Einstein midpoint aggregation was introduced by Gulcehre et al. (2019) and refined by Chami et al. (2019). For a comprehensive treatment of gyrovector spaces underpinning Möbius operations, see Ungar (2008). The connection between curvature and volume growth is covered in standard Riemannian geometry texts; we recommend do Carmo (1992) for the foundations.
