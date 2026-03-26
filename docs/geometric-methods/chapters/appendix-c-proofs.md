# Appendix C: Selected Proofs and Derivations

*Structural Fuzzing: Geometric Methods for Adversarial Model Validation* --- Andrew H. Bond

---

This appendix collects rigorous proofs of the main theorems and propositions stated in the body of the text. Each proof is referenced back to the chapter and section where the result first appears. The reader is assumed to be familiar with linear algebra, real analysis, and the basic definitions of metric spaces and smooth manifolds introduced in Part I.

---

## C.1 The Scalar Irrecoverability Theorem (Chapter 1)

**Theorem C.1 (Scalar Irrecoverability).** *Let $n \geq 2$ and let $\phi : \mathbb{R}^n \to \mathbb{R}$ be any linear functional $\phi(\mathbf{v}) = \mathbf{w}^\top \mathbf{v}$ with $\mathbf{w} \neq \mathbf{0}$. Then:*

*(i) The null space $\ker(\phi) = \{\mathbf{v} \in \mathbb{R}^n : \mathbf{w}^\top \mathbf{v} = 0\}$ has dimension $n - 1$.*

*(ii) For any $c \in \mathbb{R}$, the preimage $\phi^{-1}(c)$ is an affine hyperplane of dimension $n - 1$.*

*(iii) For any $c \in \mathbb{R}$ and any $M > 0$, there exist $\mathbf{v}_1, \mathbf{v}_2 \in \phi^{-1}(c)$ such that $|v_{1,i} - v_{2,i}| > M$ for every component $i \in \{1, \ldots, n\}$.*

*(iv) No nonlinear scalar-valued function $\psi : \mathbb{R}^n \to \mathbb{R}$ that is continuous and surjective can have a discrete preimage $\psi^{-1}(c)$ for all $c$ in its range.*

*Consequently, no single scalar summary of an $n$-dimensional evaluation vector preserves more than one dimension of the underlying information.*

**Proof.**

*(i)* The map $\phi : \mathbb{R}^n \to \mathbb{R}$ defined by $\phi(\mathbf{v}) = \mathbf{w}^\top \mathbf{v}$ is a linear transformation from $\mathbb{R}^n$ to $\mathbb{R}$. Since $\mathbf{w} \neq \mathbf{0}$, the map is surjective, so $\text{rank}(\phi) = 1$. By the rank-nullity theorem,

$$\dim(\ker(\phi)) = n - \text{rank}(\phi) = n - 1.$$

*(ii)* Fix any $\mathbf{v}_0$ with $\phi(\mathbf{v}_0) = c$. Then $\phi^{-1}(c) = \mathbf{v}_0 + \ker(\phi)$, which is an affine subspace of $\mathbb{R}^n$ with dimension equal to $\dim(\ker(\phi)) = n - 1$. An affine subspace of dimension $n - 1$ in $\mathbb{R}^n$ is, by definition, a hyperplane.

*(iii)* Since $\ker(\phi)$ has dimension $n - 1 \geq 1$, it contains nonzero vectors. We claim we can find a vector $\mathbf{u} \in \ker(\phi)$ with all components nonzero. To see this, choose a basis $\{\mathbf{e}_1', \ldots, \mathbf{e}_{n-1}'\}$ of $\ker(\phi)$. The set of vectors in $\ker(\phi)$ with at least one zero component is a finite union of subspaces, each of dimension at most $n - 2$. Since $\ker(\phi)$ has dimension $n - 1$, it cannot be covered by finitely many subspaces of strictly lower dimension (over $\mathbb{R}$, which is infinite). Therefore, there exists $\mathbf{u} \in \ker(\phi)$ with $u_i \neq 0$ for all $i$.

Now fix any $\mathbf{v}_0 \in \phi^{-1}(c)$. For any $M > 0$, let $\lambda = M / \min_i |u_i|$. Define $\mathbf{v}_1 = \mathbf{v}_0$ and $\mathbf{v}_2 = \mathbf{v}_0 + \lambda \mathbf{u}$. Since $\mathbf{u} \in \ker(\phi)$, we have $\phi(\mathbf{v}_2) = \phi(\mathbf{v}_0) + \lambda \phi(\mathbf{u}) = c + 0 = c$. Thus both $\mathbf{v}_1, \mathbf{v}_2 \in \phi^{-1}(c)$, and

$$|v_{1,i} - v_{2,i}| = \lambda |u_i| \geq \lambda \min_j |u_j| = M$$

for every component $i$.

*(iv)* Let $\psi : \mathbb{R}^n \to \mathbb{R}$ be continuous and surjective with $n \geq 2$. Suppose for contradiction that $\psi^{-1}(c)$ is finite for every $c$ in the range of $\psi$. Since $\psi$ is continuous and surjective, by the intermediate value theorem applied along paths in $\mathbb{R}^n$, the preimage $\psi^{-1}(c)$ is a closed subset of $\mathbb{R}^n$ for every $c$. But a continuous surjection from $\mathbb{R}^n$ (for $n \geq 2$) to $\mathbb{R}$ cannot have all fibers finite: by a dimension-counting argument (the fiber dimension must be at least $n - 1$ generically, by Sard's theorem applied to regular values), the generic fiber is an $(n-1)$-dimensional manifold, which is uncountably infinite for $n \geq 2$.

More precisely, by Sard's theorem, the set of critical values of $\psi$ has Lebesgue measure zero in $\mathbb{R}$. For any regular value $c$, the preimage theorem guarantees that $\psi^{-1}(c)$ is a smooth submanifold of $\mathbb{R}^n$ of dimension $n - 1 \geq 1$, which is infinite. This contradicts the assumption that all preimages are finite. $\square$

**Remark C.1.** Part (iii) is the precise formulation of "irrecoverability": given only $\phi(\mathbf{v}) = c$, one cannot bound any individual component $v_i$ without additional constraints. The scalar $c$ is consistent with evaluation vectors that are arbitrarily far apart in every dimension. This is not a deficiency of any particular weight vector $\mathbf{w}$; it holds for all nonzero $\mathbf{w}$ and all $c$ in the range of $\phi$.

**Remark C.2.** Part (iv) extends the result beyond linear projections: even nonlinear scalar summaries generically fail to reduce the preimage to a manageable set. The only escape is to impose domain-specific constraints on the evaluation vector (e.g., requiring all components to be non-negative and bounded), which amounts to working in a compact subset of $\mathbb{R}^n$. Even then, the preimage is typically an $(n-1)$-dimensional surface, which grows combinatorially as $n$ increases.

---

## C.2 Mahalanobis Distance Is a Valid Metric (Chapter 2)

**Theorem C.2.** *Let $\Sigma \in \text{SPD}(n)$ be a symmetric positive definite matrix. Then the Mahalanobis distance*

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1} (\mathbf{a} - \mathbf{b})}$$

*is a metric on $\mathbb{R}^n$. That is, for all $\mathbf{a}, \mathbf{b}, \mathbf{c} \in \mathbb{R}^n$:*

*(M1) Non-negativity: $d_M(\mathbf{a}, \mathbf{b}) \geq 0$.*

*(M2) Identity of indiscernibles: $d_M(\mathbf{a}, \mathbf{b}) = 0$ if and only if $\mathbf{a} = \mathbf{b}$.*

*(M3) Symmetry: $d_M(\mathbf{a}, \mathbf{b}) = d_M(\mathbf{b}, \mathbf{a})$.*

*(M4) Triangle inequality: $d_M(\mathbf{a}, \mathbf{c}) \leq d_M(\mathbf{a}, \mathbf{b}) + d_M(\mathbf{b}, \mathbf{c})$.*

**Proof.**

Since $\Sigma$ is symmetric positive definite, so is $\Sigma^{-1}$. By the spectral theorem, $\Sigma^{-1}$ has a unique symmetric positive definite square root $\Sigma^{-1/2}$, i.e., $\Sigma^{-1} = \Sigma^{-1/2} \Sigma^{-1/2}$. Define the linear transformation $L = \Sigma^{-1/2}$ and observe that

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1/2} \Sigma^{-1/2} (\mathbf{a} - \mathbf{b})} = \|L(\mathbf{a} - \mathbf{b})\|_2 = \|L\mathbf{a} - L\mathbf{b}\|_2.$$

Thus $d_M(\mathbf{a}, \mathbf{b})$ is the Euclidean distance between $L\mathbf{a}$ and $L\mathbf{b}$. Since $L = \Sigma^{-1/2}$ is invertible (all eigenvalues of $\Sigma^{-1/2}$ are strictly positive), the map $\mathbf{a} \mapsto L\mathbf{a}$ is a bijection on $\mathbb{R}^n$. We verify each axiom:

*(M1)* $d_M(\mathbf{a}, \mathbf{b}) = \|L\mathbf{a} - L\mathbf{b}\|_2 \geq 0$ since the Euclidean norm is non-negative.

*(M2)* $d_M(\mathbf{a}, \mathbf{b}) = 0 \iff \|L\mathbf{a} - L\mathbf{b}\|_2 = 0 \iff L\mathbf{a} = L\mathbf{b} \iff \mathbf{a} = \mathbf{b}$, where the last equivalence uses the invertibility of $L$.

*(M3)* $d_M(\mathbf{a}, \mathbf{b}) = \|L\mathbf{a} - L\mathbf{b}\|_2 = \|L\mathbf{b} - L\mathbf{a}\|_2 = d_M(\mathbf{b}, \mathbf{a})$.

*(M4)* By the Euclidean triangle inequality applied to $L\mathbf{a}$, $L\mathbf{b}$, $L\mathbf{c}$:

$$d_M(\mathbf{a}, \mathbf{c}) = \|L\mathbf{a} - L\mathbf{c}\|_2 \leq \|L\mathbf{a} - L\mathbf{b}\|_2 + \|L\mathbf{b} - L\mathbf{c}\|_2 = d_M(\mathbf{a}, \mathbf{b}) + d_M(\mathbf{b}, \mathbf{c}). \quad \square$$

**Corollary C.2.1.** *The Mahalanobis distance with $\Sigma = I$ reduces to the standard Euclidean distance. With $\Sigma = \text{diag}(\sigma_1^2, \ldots, \sigma_n^2)$, it reduces to the weighted Euclidean distance $d(\mathbf{a}, \mathbf{b}) = \sqrt{\sum_{i=1}^n (a_i - b_i)^2 / \sigma_i^2}$.*

**Proof.** Immediate from the definition: $\Sigma^{-1} = I$ gives the standard inner product, and $\Sigma^{-1} = \text{diag}(1/\sigma_1^2, \ldots, 1/\sigma_n^2)$ gives the diagonal quadratic form. $\square$

---

## C.3 The Poincare Ball Distance Is a Valid Metric (Chapter 3)

**Theorem C.3.** *For curvature parameter $c > 0$, the geodesic distance on the Poincare ball $\mathbb{B}_c^d = \{x \in \mathbb{R}^d : c\|x\|^2 < 1\}$,*

$$d_c(x, y) = \frac{2}{\sqrt{c}} \operatorname{arctanh}\!\left(\sqrt{c}\,\|(-x) \oplus_c y\|\right),$$

*satisfies the metric axioms on $\mathbb{B}_c^d$.*

**Proof.** We verify each axiom.

*(M1) Non-negativity.* Since $\operatorname{arctanh}$ is non-negative on $[0, 1)$ and $\|(-x) \oplus_c y\| \geq 0$, we have $d_c(x, y) \geq 0$.

*(M2) Identity of indiscernibles.* We have $d_c(x, y) = 0$ if and only if $\operatorname{arctanh}(\sqrt{c}\,\|(-x) \oplus_c y\|) = 0$, which holds if and only if $\|(-x) \oplus_c y\| = 0$, i.e., $(-x) \oplus_c y = \mathbf{0}$. By the properties of Mobius addition, $(-x) \oplus_c y = \mathbf{0}$ if and only if $y = x$. (The identity element of Mobius addition is $\mathbf{0}$, and $(-x) \oplus_c x = \mathbf{0}$ follows from the definition since the inverse of $x$ under $\oplus_c$ is $-x$.)

*(M3) Symmetry.* The distance can be expressed in the equivalent closed form

$$d_c(x, y) = \frac{1}{\sqrt{c}} \operatorname{arccosh}\!\left(1 + \frac{2c\,\|x - y\|^2}{(1 - c\|x\|^2)(1 - c\|y\|^2)}\right).$$

The right-hand side is manifestly symmetric in $x$ and $y$: the term $\|x - y\|^2 = \|y - x\|^2$ and the denominator is symmetric. Therefore $d_c(x, y) = d_c(y, x)$.

*(M4) Triangle inequality.* The Poincare ball $(\mathbb{B}_c^d, g^{\mathbb{B}})$ is a Riemannian manifold of constant negative sectional curvature $-c$. On any connected Riemannian manifold, the geodesic distance is defined as the infimum of lengths of piecewise-smooth curves connecting two points:

$$d_c(x, y) = \inf_{\gamma} \int_0^1 \sqrt{g_{\gamma(t)}(\dot{\gamma}(t), \dot{\gamma}(t))}\, dt$$

where the infimum is over all piecewise-smooth curves $\gamma : [0, 1] \to \mathbb{B}_c^d$ with $\gamma(0) = x$ and $\gamma(1) = y$. The infimum of curve lengths defines a metric: the triangle inequality holds because any curve from $x$ to $z$ via $y$ has length at least $d_c(x, y) + d_c(y, z)$ (by concatenation of curves from $x$ to $y$ and from $y$ to $z$), while the direct geodesic from $x$ to $z$ has length $d_c(x, z)$, which by definition is the infimum and thus satisfies

$$d_c(x, z) \leq \text{length}(\gamma_{x \to y}) + \text{length}(\gamma_{y \to z})$$

for any curves $\gamma_{x \to y}$ and $\gamma_{y \to z}$. Taking infima on the right-hand side yields $d_c(x, z) \leq d_c(x, y) + d_c(y, z)$.

This argument applies to all Riemannian manifolds and does not depend on the specific curvature. The Poincare ball inherits the triangle inequality from the general theory of Riemannian distances. $\square$

**Proposition C.3.1 (Equivalence of distance formulas).** *The Mobius-based formula and the arccosh formula for $d_c$ agree:*

$$\frac{2}{\sqrt{c}} \operatorname{arctanh}\!\left(\sqrt{c}\,\|(-x) \oplus_c y\|\right) = \frac{1}{\sqrt{c}} \operatorname{arccosh}\!\left(1 + \frac{2c\,\|x - y\|^2}{(1 - c\|x\|^2)(1 - c\|y\|^2)}\right).$$

**Proof.** Write $\delta = (-x) \oplus_c y$. By the definition of Mobius addition,

$$\|\delta\|^2 = \frac{\|x - y\|^2 \cdot (1 + 2c\langle x, y \rangle + c^2\|x\|^2\|y\|^2) - \text{cross terms}}{(\text{denominator})^2}.$$

A direct (and somewhat lengthy) algebraic computation shows that

$$c\|\delta\|^2 = \frac{2c\|x - y\|^2}{(1 - c\|x\|^2)(1 - c\|y\|^2) + 2c\|x - y\|^2 + (1 - c\|x\|^2)(1 - c\|y\|^2)}.$$

More specifically, the identity $\operatorname{arccosh}(1 + 2t) = 2\operatorname{arctanh}(\sqrt{t/(1+t)})$ for $t \geq 0$ connects the two formulas. Setting

$$t = \frac{c\|x - y\|^2}{(1 - c\|x\|^2)(1 - c\|y\|^2)}$$

and verifying that $\sqrt{c}\,\|\delta\| = \sqrt{t/(1+t)}$ (which follows from the explicit formula for Mobius addition) establishes the equivalence. The key algebraic identity used is

$$\operatorname{arccosh}(1 + 2u) = 2\operatorname{arctanh}(\sqrt{u/(u+1)}),$$

which is proved by writing $\operatorname{arccosh}(z) = \ln(z + \sqrt{z^2 - 1})$ and $\operatorname{arctanh}(w) = \frac{1}{2}\ln\frac{1+w}{1-w}$ and verifying the identity directly. $\square$

---

## C.4 The Log-Euclidean Metric on SPD(n) Is a Complete Riemannian Metric (Chapter 4)

**Theorem C.4.** *The log-Euclidean distance*

$$d_{LE}(S_1, S_2) = \|\log(S_1) - \log(S_2)\|_F$$

*defines a complete Riemannian metric on $\text{SPD}(n)$. That is:*

*(i) $d_{LE}$ is a proper metric (non-negativity, identity of indiscernibles, symmetry, triangle inequality).*

*(ii) The Riemannian metric tensor at $S \in \text{SPD}(n)$ is*

$$\langle V, W \rangle_S^{LE} = \operatorname{tr}\!\left((D_S \log)(V)^\top (D_S \log)(W)\right)$$

*where $D_S \log : T_S\text{SPD}(n) \to \text{Sym}(n)$ is the differential of the matrix logarithm at $S$, and $V, W \in T_S\text{SPD}(n)$ are tangent vectors (symmetric matrices).*

*(iii) $(\text{SPD}(n), d_{LE})$ is a complete metric space.*

**Proof.**

*(i)* The matrix logarithm $\log : \text{SPD}(n) \to \text{Sym}(n)$ is well-defined on SPD matrices because every SPD matrix has strictly positive eigenvalues, and $\log$ is defined on the positive reals. Furthermore, $\log$ is a diffeomorphism from $\text{SPD}(n)$ onto $\text{Sym}(n)$, with inverse given by the matrix exponential $\exp : \text{Sym}(n) \to \text{SPD}(n)$.

To see that $\log$ is a bijection: if $S \in \text{SPD}(n)$ with eigendecomposition $S = U\Lambda U^\top$ where $\Lambda = \text{diag}(\lambda_1, \ldots, \lambda_n)$ with $\lambda_i > 0$, then $\log(S) = U \text{diag}(\log\lambda_1, \ldots, \log\lambda_n) U^\top \in \text{Sym}(n)$. Conversely, any $X \in \text{Sym}(n)$ has eigendecomposition $X = V\text{diag}(\mu_1, \ldots, \mu_n) V^\top$ with $\mu_i \in \mathbb{R}$, and $\exp(X) = V\text{diag}(e^{\mu_1}, \ldots, e^{\mu_n}) V^\top \in \text{SPD}(n)$. The maps $\log$ and $\exp$ are mutual inverses.

Now define $\Phi = \log : \text{SPD}(n) \to \text{Sym}(n)$. Then

$$d_{LE}(S_1, S_2) = \|\Phi(S_1) - \Phi(S_2)\|_F.$$

Since $\Phi$ is a bijection and $\|\cdot\|_F$ is a norm (hence a metric) on $\text{Sym}(n)$, the composition $d_{LE}$ inherits all metric axioms:

- **Non-negativity**: $\|\Phi(S_1) - \Phi(S_2)\|_F \geq 0$.
- **Identity of indiscernibles**: $\|\Phi(S_1) - \Phi(S_2)\|_F = 0 \iff \Phi(S_1) = \Phi(S_2) \iff S_1 = S_2$ (by injectivity of $\Phi$).
- **Symmetry**: $\|\Phi(S_1) - \Phi(S_2)\|_F = \|\Phi(S_2) - \Phi(S_1)\|_F$.
- **Triangle inequality**: $\|\Phi(S_1) - \Phi(S_3)\|_F \leq \|\Phi(S_1) - \Phi(S_2)\|_F + \|\Phi(S_2) - \Phi(S_3)\|_F$.

*(ii)* The Riemannian structure is obtained by pulling back the flat Euclidean metric on $\text{Sym}(n)$ through the diffeomorphism $\Phi = \log$. For $V \in T_S\text{SPD}(n)$, the differential $D_S\Phi(V) = (D_S \log)(V)$ is a symmetric matrix (an element of $T_{\log S}\text{Sym}(n) \cong \text{Sym}(n)$). The pulled-back inner product is

$$\langle V, W \rangle_S^{LE} = \langle D_S\Phi(V), D_S\Phi(W) \rangle_{\text{Sym}(n)} = \operatorname{tr}\!\left((D_S\log(V))^\top D_S\log(W)\right).$$

Since $\Phi$ is a diffeomorphism, $D_S\Phi$ is an isomorphism at each $S$, so the pulled-back form is a genuine inner product (positive definite on each tangent space). This defines a smooth Riemannian metric on $\text{SPD}(n)$.

*(iii)* The map $\Phi = \log : (\text{SPD}(n), d_{LE}) \to (\text{Sym}(n), \|\cdot\|_F)$ is an isometry by construction. The space $(\text{Sym}(n), \|\cdot\|_F)$ is a finite-dimensional normed vector space and hence complete (every Cauchy sequence converges). Since $\Phi$ is an isometry, it maps Cauchy sequences to Cauchy sequences and convergent sequences to convergent sequences. Given a Cauchy sequence $(S_k)$ in $(\text{SPD}(n), d_{LE})$, the sequence $(\log S_k)$ is Cauchy in $(\text{Sym}(n), \|\cdot\|_F)$ and hence converges to some $X \in \text{Sym}(n)$. Then $S_k \to \exp(X) \in \text{SPD}(n)$, so the original sequence converges in $\text{SPD}(n)$. Therefore $(\text{SPD}(n), d_{LE})$ is complete. $\square$

**Remark C.3.** The completeness of $(\text{SPD}(n), d_{LE})$ is a consequence of the global isometry to $\text{Sym}(n) \cong \mathbb{R}^{n(n+1)/2}$. This is a significant practical advantage: optimization algorithms on $\text{SPD}(n)$ can be performed in the log-domain using standard Euclidean methods, with the guarantee that limits of convergent sequences remain on the manifold.

**Remark C.4.** The log-Euclidean metric is distinct from the affine-invariant metric $d_{AI}(S_1, S_2) = \|\log(S_1^{-1/2}S_2 S_1^{-1/2})\|_F$. The affine-invariant metric is invariant under the congruence action $S \mapsto ASA^\top$ for any invertible $A$, while the log-Euclidean metric is not. However, the log-Euclidean metric is invariant under simultaneous scaling $S \mapsto \alpha S$ (since $\log(\alpha S) = \log(S) + (\log\alpha)I$, the constant shift cancels in the difference). Both metrics agree to first order near the identity matrix.

---

## C.5 Cholesky Parameterization Surjects onto SPD(n) (Chapter 15)

**Theorem C.5.** *Let $\mathcal{L}_n^+$ denote the set of $n \times n$ lower-triangular matrices with strictly positive diagonal entries. The map $\Psi : \mathcal{L}_n^+ \to \text{SPD}(n)$ defined by $\Psi(L) = LL^\top$ is a surjection. Moreover, it is a bijection: each $S \in \text{SPD}(n)$ has a unique Cholesky factor $L \in \mathcal{L}_n^+$.*

**Proof.**

**Existence (surjectivity).** Let $S \in \text{SPD}(n)$. We construct $L$ by induction on the leading principal submatrices. Write $S$ in block form

$$S = \begin{pmatrix} s_{11} & \mathbf{r}^\top \\ \mathbf{r} & S' \end{pmatrix}$$

where $s_{11} > 0$ (since $S$ is positive definite, all diagonal entries are positive), $\mathbf{r} \in \mathbb{R}^{n-1}$, and $S' \in \mathbb{R}^{(n-1) \times (n-1)}$.

Set $\ell_{11} = \sqrt{s_{11}} > 0$ and $\boldsymbol{\ell} = \mathbf{r} / \ell_{11}$. Then

$$\begin{pmatrix} \ell_{11} & 0 \\ \boldsymbol{\ell} & I \end{pmatrix} \begin{pmatrix} \ell_{11} & \boldsymbol{\ell}^\top \\ 0 & I \end{pmatrix} = \begin{pmatrix} s_{11} & \mathbf{r}^\top \\ \mathbf{r} & \boldsymbol{\ell}\boldsymbol{\ell}^\top + I \end{pmatrix}.$$

Comparing with $S$, we need $S' = \boldsymbol{\ell}\boldsymbol{\ell}^\top + S''$ where $S'' = S' - \boldsymbol{\ell}\boldsymbol{\ell}^\top$. We must verify that $S''$ is SPD. For any nonzero $\mathbf{x} \in \mathbb{R}^{n-1}$:

$$\mathbf{x}^\top S'' \mathbf{x} = \mathbf{x}^\top S' \mathbf{x} - (\boldsymbol{\ell}^\top \mathbf{x})^2 = \mathbf{x}^\top S' \mathbf{x} - \frac{(\mathbf{r}^\top \mathbf{x})^2}{s_{11}}.$$

Define $\mathbf{v} = \begin{pmatrix} -\mathbf{r}^\top\mathbf{x}/s_{11} \\ \mathbf{x} \end{pmatrix}$. Then

$$\mathbf{v}^\top S \mathbf{v} = \frac{(\mathbf{r}^\top\mathbf{x})^2}{s_{11}} - 2\frac{(\mathbf{r}^\top\mathbf{x})^2}{s_{11}} + \mathbf{x}^\top S' \mathbf{x} = \mathbf{x}^\top S' \mathbf{x} - \frac{(\mathbf{r}^\top\mathbf{x})^2}{s_{11}} = \mathbf{x}^\top S'' \mathbf{x}.$$

Since $S$ is positive definite and $\mathbf{v} \neq \mathbf{0}$ (because $\mathbf{x} \neq \mathbf{0}$), we have $\mathbf{v}^\top S \mathbf{v} > 0$, so $\mathbf{x}^\top S'' \mathbf{x} > 0$. Hence $S''$ is SPD of size $(n-1) \times (n-1)$.

By induction (with the $1 \times 1$ base case being trivial: $S = (s_{11})$, $L = (\sqrt{s_{11}})$), we obtain a lower-triangular $L$ with positive diagonal such that $S = LL^\top$.

**Uniqueness.** Suppose $L_1 L_1^\top = L_2 L_2^\top = S$. Then $L_2^{-1} L_1 (L_2^{-1} L_1)^\top = I$, so $Q = L_2^{-1} L_1$ is orthogonal. But $Q$ is also lower-triangular (product of lower-triangular matrices, since $L_2^{-1}$ is lower-triangular). A lower-triangular orthogonal matrix must be diagonal (since $QQ^\top = I$ and $Q$ is lower-triangular, the off-diagonal entries are forced to zero). Since both $L_1$ and $L_2$ have positive diagonals, $Q$ has positive diagonal, and a diagonal orthogonal matrix with positive diagonal entries is the identity. Therefore $L_1 = L_2$. $\square$

**Corollary C.5.1.** *The map $\hat{\Psi} : \mathbb{R}^{n(n+1)/2} \to \text{SPD}(n)$ defined by*

$$\hat{\Psi}(\theta_1, \ldots, \theta_n, \theta_{n+1}, \ldots, \theta_{n(n+1)/2}) = LL^\top$$

*where $L_{ii} = e^{\theta_i}$ for $i = 1, \ldots, n$ and the remaining $\theta$ values fill the strictly lower-triangular entries of $L$, is a smooth surjection from $\mathbb{R}^{n(n+1)/2}$ onto $\text{SPD}(n)$.*

**Proof.** The exponential function $\theta_i \mapsto e^{\theta_i}$ maps $\mathbb{R}$ onto $(0, \infty)$, ensuring that the diagonal entries of $L$ are strictly positive. The off-diagonal entries are unconstrained. By Theorem C.5, $\Psi(L) = LL^\top$ surjects onto $\text{SPD}(n)$, and the composition $\hat{\Psi} = \Psi \circ (\text{exp-diag construction})$ is smooth as a composition of smooth maps. $\square$

**Remark C.5.** This corollary is the mathematical justification for the Cholesky parameterization used in Chapter 15: optimizing over unconstrained $\theta \in \mathbb{R}^{n(n+1)/2}$ is equivalent to optimizing over $\text{SPD}(n)$, but without any constraints. The log-diagonal trick $L_{ii} = e^{\theta_i}$ eliminates the positivity constraint on the diagonal of $L$, making the entire optimization unconstrained.

---

## C.6 MRI Convergence Properties (Chapter 9)

The Model Robustness Index (MRI) is an empirical statistic computed from a finite sample of perturbations. This section establishes conditions under which the empirical MRI converges to its population counterpart and quantifies the sensitivity of the MRI to small changes in the baseline parameters.

**Definition C.1.** *Let $\theta^* \in \mathbb{R}^d$ be a baseline parameter vector and let $\mathcal{L} : \mathbb{R}^d \to \mathbb{R}_{\geq 0}$ be a loss function. Define the perturbation random variable*

$$\Omega = |\mathcal{L}(\theta^* \odot e^{\boldsymbol{\epsilon}}) - \mathcal{L}(\theta^*)|$$

*where $\boldsymbol{\epsilon} \sim \mathcal{N}(\mathbf{0}, \sigma^2 I_d)$ and $\odot$ denotes elementwise multiplication. The population MRI is*

$$\text{MRI}^* = w_1 \mathbb{E}[\Omega] + w_2 \, F_\Omega^{-1}(0.75) + w_3 \, F_\Omega^{-1}(0.95)$$

*where $F_\Omega^{-1}$ is the quantile function of $\Omega$ and $w_1, w_2, w_3 \geq 0$ with $w_1 + w_2 + w_3 = 1$.*

**Theorem C.6 (Convergence of the empirical MRI).** *Let $\Omega_1, \ldots, \Omega_N$ be i.i.d. copies of $\Omega$, and define the empirical MRI as*

$$\widehat{\text{MRI}}_N = w_1 \bar{\Omega}_N + w_2 \hat{Q}_{0.75} + w_3 \hat{Q}_{0.95}$$

*where $\bar{\Omega}_N = \frac{1}{N}\sum_{i=1}^N \Omega_i$ is the sample mean and $\hat{Q}_p$ is the sample $p$-th quantile. Assume $\mathbb{E}[\Omega^2] < \infty$ and that $F_\Omega$ has a positive density at $F_\Omega^{-1}(0.75)$ and $F_\Omega^{-1}(0.95)$. Then:*

*(i) $\widehat{\text{MRI}}_N \xrightarrow{a.s.} \text{MRI}^*$ as $N \to \infty$.*

*(ii) $\sqrt{N}(\widehat{\text{MRI}}_N - \text{MRI}^*) \xrightarrow{d} \mathcal{N}(0, \sigma_{\text{MRI}}^2)$ for a finite variance $\sigma_{\text{MRI}}^2$ that depends on $w_1, w_2, w_3$, the variance of $\Omega$, and the density of $F_\Omega$ at the two quantile points.*

**Proof.**

*(i)* By the strong law of large numbers, $\bar{\Omega}_N \xrightarrow{a.s.} \mathbb{E}[\Omega]$. By the Glivenko-Cantelli theorem, the empirical distribution function $\hat{F}_N$ converges uniformly to $F_\Omega$ almost surely. Since $F_\Omega$ has a positive density at the quantile points $q_{0.75}$ and $q_{0.95}$, these quantiles are uniquely defined and the sample quantiles converge: $\hat{Q}_{p} \xrightarrow{a.s.} F_\Omega^{-1}(p)$ for $p \in \{0.75, 0.95\}$ (see, e.g., Serfling, *Approximation Theorems of Mathematical Statistics*, Theorem 2.3.1). The empirical MRI is a continuous (in fact, affine) function of these three convergent quantities, so by the continuous mapping theorem, $\widehat{\text{MRI}}_N \xrightarrow{a.s.} \text{MRI}^*$.

*(ii)* The central limit theorem gives $\sqrt{N}(\bar{\Omega}_N - \mathbb{E}[\Omega]) \xrightarrow{d} \mathcal{N}(0, \text{Var}(\Omega))$. For sample quantiles, the Bahadur representation yields

$$\sqrt{N}(\hat{Q}_p - q_p) \xrightarrow{d} \mathcal{N}\!\left(0, \frac{p(1-p)}{f_\Omega(q_p)^2}\right)$$

where $q_p = F_\Omega^{-1}(p)$ and $f_\Omega(q_p)$ is the density at the quantile. The joint distribution of $(\bar{\Omega}_N, \hat{Q}_{0.75}, \hat{Q}_{0.95})$, properly centered and scaled by $\sqrt{N}$, converges to a trivariate normal (this follows from the joint Bahadur representation of sample quantiles and the sample mean). Since $\widehat{\text{MRI}}_N$ is a linear combination of these three, its asymptotic distribution is univariate normal with variance

$$\sigma_{\text{MRI}}^2 = w_1^2 \text{Var}(\Omega) + w_2^2 \frac{0.75 \cdot 0.25}{f_\Omega(q_{0.75})^2} + w_3^2 \frac{0.95 \cdot 0.05}{f_\Omega(q_{0.95})^2} + \text{cross terms}.$$

The cross terms arise from the covariance between the sample mean and the sample quantiles, which is also finite under our assumptions. $\square$

**Proposition C.6.1 (Perturbation stability of MRI).** *Suppose $\mathcal{L}$ is $K$-Lipschitz in the multiplicative perturbation sense: for all $\theta$ and all perturbation vectors $\boldsymbol{\epsilon}$,*

$$|\mathcal{L}(\theta \odot e^{\boldsymbol{\epsilon}}) - \mathcal{L}(\theta)| \leq K \|\boldsymbol{\epsilon}\|_2.$$

*Then for two baseline parameters $\theta_1^*$ and $\theta_2^*$ with $\|\log(\theta_1^*/\theta_2^*)\|_2 \leq \delta$ (componentwise log-ratio), the population MRIs satisfy*

$$|\text{MRI}^*(\theta_1^*) - \text{MRI}^*(\theta_2^*)| \leq 2K\delta.$$

**Proof.** Let $\Omega_1$ and $\Omega_2$ denote the perturbation random variables for baselines $\theta_1^*$ and $\theta_2^*$ respectively, with the same noise $\boldsymbol{\epsilon}$. The perturbed parameters are $\theta_j^* \odot e^{\boldsymbol{\epsilon}}$ for $j = 1, 2$. Taking logarithms componentwise, $\log(\theta_1^* \odot e^{\boldsymbol{\epsilon}}) - \log(\theta_2^* \odot e^{\boldsymbol{\epsilon}}) = \log(\theta_1^*/\theta_2^*)$, which has norm at most $\delta$. By the Lipschitz assumption applied twice,

$$|\Omega_1 - \Omega_2| \leq |\mathcal{L}(\theta_1^* \odot e^{\boldsymbol{\epsilon}}) - \mathcal{L}(\theta_2^* \odot e^{\boldsymbol{\epsilon}})| + |\mathcal{L}(\theta_1^*) - \mathcal{L}(\theta_2^*)| \leq 2K\delta.$$

Since $|\Omega_1 - \Omega_2| \leq 2K\delta$ holds pointwise, it holds for the mean and for all quantiles:

$$|\mathbb{E}[\Omega_1] - \mathbb{E}[\Omega_2]| \leq 2K\delta, \quad |F_{\Omega_1}^{-1}(p) - F_{\Omega_2}^{-1}(p)| \leq 2K\delta$$

for all $p \in (0,1)$. Therefore

$$|\text{MRI}^*(\theta_1^*) - \text{MRI}^*(\theta_2^*)| \leq (w_1 + w_2 + w_3) \cdot 2K\delta = 2K\delta. \quad \square$$

---

## C.7 Pareto Frontier Non-Dominance Transitivity (Chapter 8)

**Definition C.2.** *Given a multi-objective minimization problem with objective vector $\mathbf{f}(\mathbf{x}) = (f_1(\mathbf{x}), \ldots, f_m(\mathbf{x}))$, we say configuration $\mathbf{x}$ dominates configuration $\mathbf{y}$, written $\mathbf{x} \preceq \mathbf{y}$, if $f_i(\mathbf{x}) \leq f_i(\mathbf{y})$ for all $i \in \{1, \ldots, m\}$ with strict inequality for at least one $i$.*

**Theorem C.7 (Dominance is a strict partial order).** *The dominance relation $\preceq$ is:*

*(i) Irreflexive: $\mathbf{x} \not\preceq \mathbf{x}$ for all $\mathbf{x}$.*

*(ii) Asymmetric: if $\mathbf{x} \preceq \mathbf{y}$ then $\mathbf{y} \not\preceq \mathbf{x}$.*

*(iii) Transitive: if $\mathbf{x} \preceq \mathbf{y}$ and $\mathbf{y} \preceq \mathbf{z}$, then $\mathbf{x} \preceq \mathbf{z}$.*

**Proof.**

*(i) Irreflexivity.* For $\mathbf{x} \preceq \mathbf{x}$ to hold, we would need $f_i(\mathbf{x}) \leq f_i(\mathbf{x})$ for all $i$ (which holds trivially) and $f_j(\mathbf{x}) < f_j(\mathbf{x})$ for some $j$ (which is impossible). Therefore $\mathbf{x} \not\preceq \mathbf{x}$.

*(ii) Asymmetry.* Suppose $\mathbf{x} \preceq \mathbf{y}$. Then there exists $j$ such that $f_j(\mathbf{x}) < f_j(\mathbf{y})$. For $\mathbf{y} \preceq \mathbf{x}$ to hold, we would need $f_j(\mathbf{y}) \leq f_j(\mathbf{x})$, contradicting $f_j(\mathbf{x}) < f_j(\mathbf{y})$.

*(iii) Transitivity.* Suppose $\mathbf{x} \preceq \mathbf{y}$ and $\mathbf{y} \preceq \mathbf{z}$. Then:

- For all $i$: $f_i(\mathbf{x}) \leq f_i(\mathbf{y}) \leq f_i(\mathbf{z})$, so $f_i(\mathbf{x}) \leq f_i(\mathbf{z})$.
- Since $\mathbf{x} \preceq \mathbf{y}$, there exists $j$ with $f_j(\mathbf{x}) < f_j(\mathbf{y})$. Combined with $f_j(\mathbf{y}) \leq f_j(\mathbf{z})$, we get $f_j(\mathbf{x}) < f_j(\mathbf{z})$.

Therefore $f_i(\mathbf{x}) \leq f_i(\mathbf{z})$ for all $i$ with strict inequality for at least one $i$, which is $\mathbf{x} \preceq \mathbf{z}$. $\square$

**Corollary C.7.1 (Non-dominance is not transitive).** *Define $\mathbf{x} \sim \mathbf{y}$ (mutual non-dominance) if $\mathbf{x} \not\preceq \mathbf{y}$ and $\mathbf{y} \not\preceq \mathbf{x}$. The relation $\sim$ is not transitive. That is, there exist $\mathbf{x}, \mathbf{y}, \mathbf{z}$ with $\mathbf{x} \sim \mathbf{y}$ and $\mathbf{y} \sim \mathbf{z}$ but $\mathbf{x} \preceq \mathbf{z}$ (so $\mathbf{x} \not\sim \mathbf{z}$).*

**Proof.** We give an explicit counterexample in two objectives ($m = 2$). Let

$$\mathbf{f}(\mathbf{x}) = (1, 3), \quad \mathbf{f}(\mathbf{y}) = (2, 2), \quad \mathbf{f}(\mathbf{z}) = (3, 4).$$

Then:

- $\mathbf{x} \sim \mathbf{y}$: $f_1(\mathbf{x}) = 1 < 2 = f_1(\mathbf{y})$ but $f_2(\mathbf{x}) = 3 > 2 = f_2(\mathbf{y})$. Neither dominates the other.
- $\mathbf{y} \sim \mathbf{z}$: $f_1(\mathbf{y}) = 2 < 3 = f_1(\mathbf{z})$ and $f_2(\mathbf{y}) = 2 < 4 = f_2(\mathbf{z})$... wait, this means $\mathbf{y} \preceq \mathbf{z}$, not $\mathbf{y} \sim \mathbf{z}$.

We adjust the example. Let

$$\mathbf{f}(\mathbf{x}) = (1, 3), \quad \mathbf{f}(\mathbf{y}) = (2, 2), \quad \mathbf{f}(\mathbf{z}) = (3, 1).$$

Then:

- $\mathbf{x} \sim \mathbf{y}$: $f_1(\mathbf{x}) < f_1(\mathbf{y})$ but $f_2(\mathbf{x}) > f_2(\mathbf{y})$. Neither dominates.
- $\mathbf{y} \sim \mathbf{z}$: $f_1(\mathbf{y}) < f_1(\mathbf{z})$ but $f_2(\mathbf{y}) > f_2(\mathbf{z})$. Neither dominates.
- $\mathbf{x} \sim \mathbf{z}$: $f_1(\mathbf{x}) < f_1(\mathbf{z})$ but $f_2(\mathbf{x}) > f_2(\mathbf{z})$. Neither dominates.

This shows that non-dominance *can* be transitive in specific cases. To show it is not *always* transitive, consider three objectives ($m = 3$):

$$\mathbf{f}(\mathbf{x}) = (1, 3, 1), \quad \mathbf{f}(\mathbf{y}) = (2, 1, 3), \quad \mathbf{f}(\mathbf{z}) = (2, 4, 2).$$

- $\mathbf{x} \sim \mathbf{y}$: $f_1(\mathbf{x}) < f_1(\mathbf{y})$ and $f_3(\mathbf{x}) < f_3(\mathbf{y})$, but $f_2(\mathbf{x}) > f_2(\mathbf{y})$. Neither dominates.
- $\mathbf{y} \sim \mathbf{z}$: $f_2(\mathbf{y}) < f_2(\mathbf{z})$, but $f_3(\mathbf{y}) > f_3(\mathbf{z})$. Neither dominates.
- $\mathbf{x} \preceq \mathbf{z}$: $f_1(\mathbf{x}) = 1 \leq 2 = f_1(\mathbf{z})$, $f_2(\mathbf{x}) = 3 \leq 4 = f_2(\mathbf{z})$ (actually $3 < 4$), $f_3(\mathbf{x}) = 1 \leq 2 = f_3(\mathbf{z})$, with strict inequality in objectives 1, 2, and 3. So $\mathbf{x} \preceq \mathbf{z}$.

Thus $\mathbf{x} \sim \mathbf{y}$ and $\mathbf{y} \sim \mathbf{z}$ but $\mathbf{x} \not\sim \mathbf{z}$ (in fact $\mathbf{x}$ dominates $\mathbf{z}$). This proves that $\sim$ is not transitive. $\square$

**Remark C.6.** The non-transitivity of mutual non-dominance has practical consequences for multi-objective optimization. One cannot simply sort configurations by pairwise comparison as one would with a total order. Instead, the Pareto frontier must be computed by checking each candidate against all others --- there is no shortcut based on transitivity of incomparability. This is why Pareto frontier computation has time complexity $O(N^2 m)$ for $N$ configurations in $m$ objectives (or $O(N \log^{m-1} N)$ using Kung et al.'s algorithm for $m \geq 3$), rather than the $O(N \log N)$ that a total order would permit.

**Proposition C.7.1 (Pareto frontier stability under perturbation).** *Let $\mathcal{F} = \{(\mathbf{f}(\mathbf{x}_1), \ldots, \mathbf{f}(\mathbf{x}_N))\}$ be a set of $N$ evaluated configurations and let $\mathcal{P} \subseteq \mathcal{F}$ be its Pareto frontier. If each objective value is perturbed by at most $\epsilon$ --- that is, $|\tilde{f}_i(\mathbf{x}_j) - f_i(\mathbf{x}_j)| \leq \epsilon$ for all $i, j$ --- then every point on the perturbed Pareto frontier $\tilde{\mathcal{P}}$ is within $2\epsilon$ (in each objective) of some point in $\mathcal{P} \cup \mathcal{N}_\epsilon(\mathcal{P})$, where $\mathcal{N}_\epsilon(\mathcal{P})$ is the set of points that are within $2\epsilon$ of being non-dominated in the original problem.*

**Proof sketch.** If $\mathbf{x}$ is dominated in the original problem, with $\mathbf{y} \preceq \mathbf{x}$ and $f_i(\mathbf{y}) \leq f_i(\mathbf{x}) - \delta_i$ for gap $\delta_i \geq 0$ (with some $\delta_j > 0$), then after perturbation $\tilde{f}_i(\mathbf{y}) \leq f_i(\mathbf{y}) + \epsilon \leq f_i(\mathbf{x}) - \delta_i + \epsilon \leq \tilde{f}_i(\mathbf{x}) + 2\epsilon - \delta_i$. So $\mathbf{y}$ still dominates $\mathbf{x}$ in the perturbed problem if $\delta_j > 2\epsilon$ for some $j$. Points that are dominated by a margin exceeding $2\epsilon$ in every objective cannot appear on the perturbed frontier. Only points that are either non-dominated or within $2\epsilon$ of non-dominance can join $\tilde{\mathcal{P}}$. $\square$

---

## C.8 Auxiliary Results

### C.8.1 Positive Definiteness of the Inverse

**Lemma C.1.** *If $\Sigma \in \text{SPD}(n)$, then $\Sigma^{-1} \in \text{SPD}(n)$.*

**Proof.** Since $\Sigma$ is symmetric and invertible, $\Sigma^{-1}$ is symmetric: $(\Sigma^{-1})^\top = (\Sigma^\top)^{-1} = \Sigma^{-1}$. For positive definiteness, let $\mathbf{x} \neq \mathbf{0}$ and set $\mathbf{y} = \Sigma^{-1}\mathbf{x} \neq \mathbf{0}$ (since $\Sigma^{-1}$ is invertible). Then $\mathbf{x}^\top \Sigma^{-1} \mathbf{x} = (\Sigma \mathbf{y})^\top \Sigma^{-1} (\Sigma \mathbf{y}) = \mathbf{y}^\top \Sigma^\top \Sigma^{-1} \Sigma \mathbf{y} = \mathbf{y}^\top \Sigma \mathbf{y} > 0$, where the last inequality uses the positive definiteness of $\Sigma$. $\square$

### C.8.2 The Matrix Logarithm on SPD(n) Is Well-Defined

**Lemma C.2.** *For any $S \in \text{SPD}(n)$, the matrix logarithm $\log(S)$ exists, is unique among symmetric matrices, and satisfies $\exp(\log(S)) = S$.*

**Proof.** Write $S = U\text{diag}(\lambda_1, \ldots, \lambda_n)U^\top$ with $\lambda_i > 0$ (eigenvalues of an SPD matrix are strictly positive). Define $\log(S) = U\text{diag}(\ln\lambda_1, \ldots, \ln\lambda_n)U^\top$. This is symmetric since $(\log S)^\top = U\text{diag}(\ln\lambda_1, \ldots, \ln\lambda_n)U^\top = \log(S)$.

By construction, $\exp(\log(S)) = U\text{diag}(e^{\ln\lambda_1}, \ldots, e^{\ln\lambda_n})U^\top = U\text{diag}(\lambda_1, \ldots, \lambda_n)U^\top = S$.

For uniqueness among symmetric matrices: suppose $X$ is symmetric with $\exp(X) = S$. Write $X = V\text{diag}(\mu_1, \ldots, \mu_n)V^\top$. Then $\exp(X) = V\text{diag}(e^{\mu_1}, \ldots, e^{\mu_n})V^\top = S$. Since eigenvalues are unique (up to ordering), we must have $\{e^{\mu_i}\} = \{\lambda_i\}$ (as multisets) and $V$ must be a corresponding eigenbasis. Since $\ln$ is injective on $(0,\infty)$, the values $\mu_i = \ln\lambda_i$ are uniquely determined, and $X = V\text{diag}(\ln\lambda_1, \ldots, \ln\lambda_n)V^\top = \log(S)$ (up to reordering of equal eigenvalues, which does not affect the matrix). $\square$

### C.8.3 The Log-Euclidean Geodesic

**Proposition C.8.** *The log-Euclidean geodesic from $S_0$ to $S_1$ in $\text{SPD}(n)$ is*

$$\gamma(t) = \exp\!\bigl((1-t)\log(S_0) + t\log(S_1)\bigr), \quad t \in [0, 1].$$

*This curve satisfies $\gamma(0) = S_0$, $\gamma(1) = S_1$, and $d_{LE}(S_0, \gamma(t)) = t \cdot d_{LE}(S_0, S_1)$ for all $t \in [0, 1]$.*

**Proof.** The first two properties are immediate: $\gamma(0) = \exp(\log(S_0)) = S_0$ and $\gamma(1) = \exp(\log(S_1)) = S_1$.

For the distance property, let $A = \log(S_0)$ and $B = \log(S_1)$. Then $\log(\gamma(t)) = (1-t)A + tB$ (since $\log \circ \exp = \text{id}$ on $\text{Sym}(n)$). Therefore

$$d_{LE}(S_0, \gamma(t)) = \|\log(S_0) - \log(\gamma(t))\|_F = \|A - ((1-t)A + tB)\|_F = t\|A - B\|_F = t \cdot d_{LE}(S_0, S_1).$$

This shows that $\gamma$ is a constant-speed geodesic: the distance from the starting point increases linearly with the parameter $t$. Since $d_{LE}$ is the distance function of the log-Euclidean Riemannian metric and $\gamma$ achieves equality in the triangle inequality (i.e., $d_{LE}(S_0, \gamma(t)) + d_{LE}(\gamma(t), S_1) = d_{LE}(S_0, S_1)$ for all $t$), $\gamma$ is a length-minimizing curve. $\square$

---

## Notes on Notation

Throughout this appendix, we use the following conventions:

| Symbol | Meaning |
|--------|---------|
| $\text{SPD}(n)$ | The manifold of $n \times n$ symmetric positive definite matrices |
| $\text{Sym}(n)$ | The vector space of $n \times n$ symmetric matrices |
| $\|\cdot\|_F$ | The Frobenius norm: $\|A\|_F = \sqrt{\operatorname{tr}(A^\top A)}$ |
| $\|\cdot\|_2$ | The Euclidean vector norm |
| $\log(\cdot)$ | Matrix logarithm (for matrices) or natural logarithm (for scalars) |
| $\exp(\cdot)$ | Matrix exponential (for matrices) or natural exponential (for scalars) |
| $\oplus_c$ | Mobius addition on $\mathbb{B}_c^d$ |
| $\odot$ | Elementwise (Hadamard) product |
| $\operatorname{arctanh}$ | Inverse hyperbolic tangent |
| $\operatorname{arccosh}$ | Inverse hyperbolic cosine |
| $T_S M$ | Tangent space of manifold $M$ at point $S$ |
| $\preceq$ | Pareto dominance relation |
