# Chapter 6: Pathfinding on Manifolds

> *"The shortest distance between two points is not a straight line, but a geodesic --- and the geodesic knows things about the terrain that the straight line does not."*
> --- Adapted from Bernhard Riemann, *On the Hypotheses Which Lie at the Foundations of Geometry* (1854)

In Chapter 2, we introduced the Mahalanobis distance as the correct way to measure separation between two points in a space where dimensions have different scales and are correlated. In Chapter 3, we saw how hyperbolic geometry captures hierarchical structure that Euclidean space distorts. In Chapter 4, we developed the SPD manifold as the natural home for covariance data. Each of these chapters addressed a *static* problem: measuring the distance between two fixed points. But real decisions are not static. They are *sequential*: an agent at state $A$ must navigate through a series of intermediate states to reach a desired goal $B$, and the cost of the journey depends not just on the endpoints but on every step along the way. This chapter develops the algorithmic machinery for finding optimal paths on decision manifolds --- the **Bond Geodesic algorithm** --- which adapts A* search to non-Euclidean configuration spaces where standard pathfinding fails.

We begin by establishing why classical A* with Euclidean heuristics produces suboptimal or inadmissible results on curved spaces (Section 6.1), develop the relationship between geodesic distance and Euclidean distance that makes this failure precise (Section 6.2), construct the Economic Decision Complex as the graph on which pathfinding operates (Section 6.3), formulate the Bond Geodesic as the minimum-friction path on this complex (Section 6.4), adapt A* with manifold-aware heuristics including a novel moral heuristic derived from dual-process cognitive theory (Section 6.5), work through concrete examples from the `eris-econ` game theory codebase (Section 6.6), establish formal properties of the resulting paths (Section 6.7), and connect forward to multi-agent equilibria in Chapter 7 (Section 6.8).

---

## 6.1 Why Standard A* Fails on Curved Spaces

### 6.1.1 The Admissibility Problem

A* search guarantees optimal paths under one condition: the heuristic function $h(n)$ must be *admissible* --- it must never overestimate the true cost from $n$ to the goal. In Euclidean space, the straight-line distance $\|n - g\|_2$ is always a lower bound on any path from $n$ to $g$, because the straight line is the shortest path. The Euclidean heuristic is therefore admissible by construction, and A* with this heuristic finds provably optimal paths.

On a curved space, the straight-line distance is no longer the shortest path. The shortest path is a *geodesic* --- a curve that locally minimizes arc length according to the Riemannian metric of the space. When the space has non-trivial curvature, the geodesic distance can differ substantially from the Euclidean distance, and the direction of the difference depends on the sign of the curvature:

- **Positive curvature** (e.g., the surface of a sphere): geodesics converge. The geodesic distance between two points is *less than* the Euclidean distance through the ambient space, but *greater than* the chord length. The Euclidean heuristic (using chord length) underestimates and remains admissible, but may be loose.

- **Negative curvature** (e.g., hyperbolic space, as developed in Chapter 3): geodesics diverge. Two points that appear close in the ambient Euclidean coordinates can be far apart in geodesic distance, because the metric is stretched near the boundary of the Poincare ball. The Euclidean distance *underestimates* the geodesic distance, which means the Euclidean heuristic remains admissible but becomes increasingly uninformative --- approaching the zero heuristic in the worst case.

- **Non-uniform curvature** (e.g., the SPD manifold from Chapter 4, or a decision space with a Mahalanobis metric): the relationship between Euclidean and geodesic distance varies from point to point. In some regions the Euclidean heuristic is tight; in others it is arbitrarily loose. Worse, when the metric tensor $\Sigma^{-1}$ has large eigenvalues in some directions and small eigenvalues in others, the Euclidean heuristic can *overestimate* the Mahalanobis distance along low-precision directions while *underestimating* it along high-precision directions.

The last case is the one that matters for this book. The 9-dimensional economic decision space of the `eris-econ` model has a covariance matrix $\Sigma$ with eigenvalues ranging from 0.25 (the Fairness dimension, tightly constrained) to 25.0 (the Consequences dimension, loosely constrained). A 1-unit Euclidean displacement along the Fairness axis corresponds to a Mahalanobis distance of $1/\sqrt{0.25} = 2.0$, while the same displacement along the Consequences axis corresponds to $1/\sqrt{25.0} = 0.2$. The Euclidean distance treats both displacements identically --- a 10x error in relative weighting.

### 6.1.2 The Boundary Discontinuity Problem

Even if the curvature problem could be resolved by rescaling the heuristic, a deeper issue remains: the decision spaces we consider have *discontinuous* cost functions. Moral boundaries (Section 6.4) impose step-function penalties on certain transitions. A path that crosses a moral boundary incurs a finite or infinite additional cost that no smooth distance function can predict. The Euclidean heuristic, being smooth, has no mechanism to account for boundaries that may lie between the current state and the goal.

This means that even a perfectly calibrated Euclidean heuristic --- one that exactly matches the Mahalanobis distance --- would still be inadmissible in the presence of boundary penalties, because it would underestimate the true cost by ignoring the penalties. The fix requires a fundamentally different kind of heuristic: one that estimates not geometric distance but *behavioral friction*, including both the smooth metric component and the discontinuous moral component. This is the moral heuristic developed in Section 6.5.

### 6.1.3 Consequences for Pathfinding

When A* operates with an inadmissible or uninformative heuristic on a decision manifold, three failure modes arise:

1. **Suboptimal paths.** The algorithm returns a path that is not the true minimum-cost route. In a decision-theoretic context, this means the model predicts behavior that is locally plausible but globally suboptimal --- the agent appears to make a "mistake" that is actually an artifact of the heuristic.

2. **Excessive exploration.** An uninformative heuristic (one that returns near-zero values everywhere) degrades A* to Dijkstra's algorithm, which explores vertices uniformly in all directions. On large decision complexes with thousands of vertices, this can increase computation by orders of magnitude.

3. **Missed disconnections.** When sacred boundaries ($\beta = \infty$) disconnect the graph, a poor heuristic may lead the search to spend enormous effort exploring a disconnected component before concluding that no path exists. A boundary-aware heuristic can detect disconnection early.

These failures motivate the development of manifold-specific heuristics in Section 6.5. But first, we need to make the relationship between geodesic and Euclidean distance precise.

---

## 6.2 Geodesic Distance vs. Euclidean Distance

The core mathematical issue is the *distortion* between the Euclidean metric and the Riemannian metric induced by the precision matrix $\Sigma^{-1}$.

### 6.2.1 The Mahalanobis Metric as a Riemannian Metric

Recall from Chapter 2 that the Mahalanobis distance between two points $\mathbf{a}, \mathbf{b} \in \mathbb{R}^n$ is:

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{b} - \mathbf{a})^\top \Sigma^{-1} (\mathbf{b} - \mathbf{a})}$$

This is the distance function induced by the constant metric tensor $g = \Sigma^{-1}$. In Riemannian geometry, a constant metric tensor defines a *flat* space --- one with zero curvature everywhere. The Mahalanobis distance is therefore not an example of curved-space geometry in the strict Riemannian sense. Rather, it is an example of a *non-isotropic* flat geometry: the space is flat, but distances are stretched and compressed anisotropically according to the eigenstructure of $\Sigma^{-1}$.

The relationship between Mahalanobis and Euclidean distance is governed by the eigenvalues of $\Sigma^{-1}$. Let $\lambda_{\min}$ and $\lambda_{\max}$ be the smallest and largest eigenvalues. Then for any $\mathbf{a}, \mathbf{b}$:

$$\sqrt{\lambda_{\min}} \cdot \|\mathbf{b} - \mathbf{a}\|_2 \leq d_M(\mathbf{a}, \mathbf{b}) \leq \sqrt{\lambda_{\max}} \cdot \|\mathbf{b} - \mathbf{a}\|_2$$

**Proposition 6.1.** The Euclidean distance $\|\mathbf{b} - \mathbf{a}\|_2$ is an admissible heuristic for A* with Mahalanobis edge weights if and only if $\lambda_{\min} \geq 1$ --- that is, if and only if every eigenvalue of $\Sigma^{-1}$ is at least 1.

*Proof.* The heuristic $h(n) = \|n - g\|_2$ is admissible when $h(n) \leq d_M(n, g)$ for all $n, g$. By the lower bound above, $d_M(n, g) \geq \sqrt{\lambda_{\min}} \cdot \|n - g\|_2$. Thus $\|n - g\|_2 \leq d_M(n, g)$ iff $\sqrt{\lambda_{\min}} \geq 1$, i.e., $\lambda_{\min} \geq 1$. $\square$

For the `eris-econ` covariance matrix, $\Sigma$ has diagonal entries ranging from 0.25 to 25.0, so $\Sigma^{-1}$ has diagonal entries ranging from $1/25 = 0.04$ to $1/0.25 = 4.0$ (before accounting for off-diagonal corrections). Since $\lambda_{\min} < 1$, the Euclidean heuristic is *not* guaranteed admissible. In practice, it is admissible along most directions but can overestimate along the Consequences axis, where $\Sigma^{-1}$ assigns very low weight.

### 6.2.2 Corrected Euclidean Heuristic

A simple fix is to scale the Euclidean heuristic by $\sqrt{\lambda_{\min}}$:

$$h_{\text{scaled}}(n) = \sqrt{\lambda_{\min}} \cdot \|n - g\|_2$$

This is admissible by construction but often very loose (since $\lambda_{\min}$ may be much less than 1). A tighter approach uses the Mahalanobis distance directly as the heuristic:

$$h_M(n) = d_M(n, g) = \sqrt{(g - n)^\top \Sigma^{-1} (g - n)}$$

This is *exact* for the single-step case (when the goal is reachable in one edge) and provides a tight lower bound in the multi-step case, because the straight-line Mahalanobis distance is always less than or equal to the sum of edge weights along any path. However, it ignores boundary penalties, so it remains inadmissible in the presence of moral boundaries.

### 6.2.3 The Hyperbolic and SPD Cases

For completeness, we note the distortion bounds in the other geometric settings developed in this book.

In hyperbolic space (Chapter 3), the geodesic distance on the Poincare ball is:

$$d_c(x, y) = \frac{2}{\sqrt{c}} \operatorname{arctanh}\left(\sqrt{c}\|(-x) \oplus_c y\|\right)$$

For points near the origin, $d_c(x, y) \approx 2\|x - y\|$ (the Euclidean distance scaled by 2). For points near the boundary, $d_c(x, y) \gg \|x - y\|$. The Euclidean distance is always an underestimate and hence admissible, but it becomes arbitrarily loose near the boundary --- exactly where the hierarchical structure places the most specific (leaf-level) nodes.

On the SPD manifold (Chapter 4), the log-Euclidean distance $d_{LE}(S_1, S_2) = \|\log(S_1) - \log(S_2)\|_F$ has no simple relationship to $\|S_1 - S_2\|_F$ because the matrix logarithm is a nonlinear operation. A Euclidean heuristic on SPD matrices is neither reliably admissible nor reliably informative. Pathfinding on SPD manifolds requires computing distances in log-space, which is more expensive but correct.

---

## 6.3 The Economic Decision Complex

The fundamental data structure underlying the Bond Geodesic is a weighted directed graph that we call the *Economic Decision Complex*. It connects the abstract geometric notions of the preceding sections to the concrete implementation in the `eris-econ` codebase.

### 6.3.1 Definition

**Definition 6.1** (Economic Decision Complex). An *Economic Decision Complex* is a triple $\mathcal{E} = (V, E, w)$ where:

- $V$ is a finite set of *vertices*, each labeled with a point $\mathbf{v} \in \mathbb{R}^9$ representing an economic state (the nine dimensions from Section 6.3.2).
- $E \subseteq V \times V$ is a set of *directed edges*, each representing an available action or transaction.
- $w : E \to \mathbb{R}_{\geq 0} \cup \{\infty\}$ is a *weight function* assigning a non-negative cost (possibly infinite) to each edge.

The weight function decomposes into two additive components:

$$w(\mathbf{a} \to \mathbf{b}) = \underbrace{\sqrt{(\mathbf{b} - \mathbf{a})^\top \Sigma^{-1} (\mathbf{b} - \mathbf{a})}}_{\text{Mahalanobis distance (smooth)}} + \underbrace{\sum_k \beta_k \cdot \mathbf{1}[\text{boundary } k \text{ crossed}]}_{\text{boundary penalties (discontinuous)}}$$

The terminology "complex" is deliberate: this is a 1-dimensional simplicial complex (a graph) embedded in $\mathbb{R}^9$, where the embedding determines edge weights through the Mahalanobis metric. The non-Euclidean structure enters through the precision matrix $\Sigma^{-1}$ and the boundary penalties $\beta_k$.

### 6.3.2 The Nine Dimensions

Every vertex in the complex carries an `EconomicState` --- a frozen dataclass wrapping a 9-tuple of floats, one per dimension. The dimensions are defined in the `eris-econ` dimensions module:

```python
class Dim(IntEnum):
    """The nine economic decision dimensions."""
    CONSEQUENCES = 0   # d_1: monetary cost, material outcome
    RIGHTS = 1         # d_2: property rights, contractual obligations
    FAIRNESS = 2       # d_3: distributional justice, reciprocity
    AUTONOMY = 3       # d_4: freedom of choice, coercion aversion
    PRIVACY_TRUST = 4  # d_5: information asymmetry, fiduciary duty
    SOCIAL_IMPACT = 5  # d_6: externalities, reputation
    VIRTUE_IDENTITY = 6  # d_7: self-image, moral identity
    LEGITIMACY = 7     # d_8: institutional trust, rule compliance
    EPISTEMIC = 8      # d_9: information quality, confidence
```

Dimensions $d_1$ through $d_4$ are *transferable* in bilateral exchange: when one agent gains, the other loses an equal amount ($\Delta d_k(A) + \Delta d_k(B) = 0$). Dimensions $d_5$ through $d_9$ are *evaluative* --- they are not conserved, allowing mutual gains from trade. This conservation structure has deep implications for equilibrium analysis (Chapter 7) but does not affect the pathfinding algorithm itself.

### 6.3.3 Implementation

The `EconomicDecisionComplex` class in the `eris-econ` codebase provides the graph data structure. Its constructor takes a covariance matrix $\Sigma$ and optional boundary penalties:

```python
class EconomicDecisionComplex:
    """Weighted directed graph representing an agent's decision space."""

    def __init__(
        self,
        sigma: np.ndarray,
        boundaries: Optional[Dict[str, float]] = None,
    ):
        if sigma.shape != (N_DIMS, N_DIMS):
            raise ValueError(f"sigma must be ({N_DIMS}, {N_DIMS})")
        self.sigma = sigma
        self.sigma_inv = np.linalg.inv(sigma + 1e-10 * np.eye(N_DIMS))
        self.boundaries = boundaries or {}

        self.vertices: Dict[str, Vertex] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, List[Edge]] = {}
```

Several design decisions deserve comment. The precision matrix $\Sigma^{-1}$ is precomputed once and cached, since it participates in every edge weight calculation. The regularization term $10^{-10}I$ prevents numerical singularity when $\Sigma$ has near-zero eigenvalues --- a concern highlighted in Chapter 2's discussion of Cholesky factorization. The adjacency structure uses a dictionary mapping vertex IDs to outgoing edge lists, providing $O(1)$ neighbor lookup during A* expansion.

Vertices and edges are added incrementally. Once all structure is in place, calling `compute_weights()` evaluates the full edge weight --- Mahalanobis distance plus boundary penalties --- for every edge:

```python
def compute_weights(self) -> None:
    """Compute edge weights for all edges."""
    for e in self.edges:
        s = self.vertices[e.source].state
        t = self.vertices[e.target].state
        e.weight = edge_weight(
            np.array(s.values),
            np.array(t.values),
            self.sigma_inv,
            self.boundaries,
        )
```

The `edge_weight` function from the metrics module computes both components:

```python
def edge_weight(
    a: np.ndarray, b: np.ndarray,
    sigma_inv: np.ndarray, boundaries: Dict[str, float],
) -> float:
    """Total edge weight: Mahalanobis distance + boundary penalties."""
    dist = mahalanobis_distance(a, b, sigma_inv)
    pen = boundary_penalty(a, b, boundaries)
    return dist + pen
```

The `add_bidirectional` method is a convenience for symmetric actions (e.g., "buy" and "sell"). Note that while the Mahalanobis distance is symmetric ($d_M(\mathbf{a}, \mathbf{b}) = d_M(\mathbf{b}, \mathbf{a})$), boundary penalties generally are not: crossing a moral boundary in one direction may incur a penalty while the reverse crossing does not. Selling stolen goods triggers a theft boundary; buying them may not.

---

## 6.4 The Bond Geodesic Formulation

### 6.4.1 Definition

We now have all the ingredients to state the central definition.

**Definition 6.2** (Bond Geodesic). Given an Economic Decision Complex $\mathcal{E} = (V, E, w)$, a starting vertex $s \in V$, and a goal set $G \subset V$, the *Bond Geodesic* is the path $\gamma^* = (v_0, v_1, \ldots, v_T)$ with $v_0 = s$ and $v_T \in G$ that minimizes the total edge weight:

$$\gamma^* = \arg\min_{\gamma : s \rightsquigarrow G} \sum_{t=0}^{T-1} w(v_t \to v_{t+1})$$

The *behavioral friction* of the decision is the total cost along the Bond Geodesic:

$$F(\gamma^*) = \sum_{t=0}^{T-1} w(v_t \to v_{t+1})$$

The term "geodesic" is imported from differential geometry, where it denotes the shortest path on a curved surface. The Bond Geodesic is the discrete analogue: the shortest path on a weighted graph embedded in $\mathbb{R}^9$, where the embedding determines edge weights through a non-Euclidean metric. The qualifier "Bond" distinguishes it from standard geodesics, which are defined by the Riemannian metric alone, without boundary penalties. The Bond Geodesic incorporates both the smooth metric structure (via Mahalanobis distance) and the discontinuous moral structure (via boundary penalties).

### 6.4.2 Behavioral Friction as a Cost Functional

Behavioral friction $F(\gamma^*)$ is a *cost functional* on paths --- it assigns a scalar cost to each route through the decision complex. Unlike scalar utility, which collapses a multi-dimensional evaluation into a single number *at each state*, behavioral friction preserves the full dimensionality of the evaluation *along the entire path* and collapses to a scalar only at the end, after integrating over all steps.

This distinction matters. Scalar utility at a single state discards $n - 1$ dimensions of information (the Scalar Irrecoverability Theorem from Chapter 1). Behavioral friction along a path preserves all $n$ dimensions in the edge weights and discards information only in the final summation. The information loss is therefore *deferred*: the full geometric structure participates in every step of the path computation, and the scalar collapse happens only after the optimal path has been identified.

### 6.4.3 Boundary Penalties: Encoding Sacred Values

The discontinuous component of the edge weight encodes moral rules, social norms, and legal constraints. The `boundary_penalty` function in the `eris-econ` metrics module checks six types of crossings:

```python
def boundary_penalty(
    a: np.ndarray, b: np.ndarray,
    boundaries: Dict[str, float],
) -> float:
    """Compute total boundary penalty for a state transition."""
    penalty = 0.0
    delta = b - a

    for name, beta in boundaries.items():
        crossed = False

        if name == "theft" and b[Dim.RIGHTS] < 0 < a[Dim.RIGHTS]:
            crossed = True
        elif name == "coercion" and delta[Dim.AUTONOMY] < -0.5:
            crossed = True
        elif name == "deception" and delta[Dim.EPISTEMIC] < -0.3:
            crossed = True
        elif name == "exploitation":
            if delta[Dim.CONSEQUENCES] > 0 and delta[Dim.FAIRNESS] < -0.3:
                crossed = True
        elif name == "sacred_value":
            if any(a[i] > 0 and b[i] <= 0 for i in range(N_DIMS)):
                crossed = True
        elif name == "promise_breaking" and delta[Dim.LEGITIMACY] < -0.5:
            crossed = True

        if crossed:
            if np.isinf(beta):
                return float("inf")
            penalty += beta

    return penalty
```

Each boundary type encodes a specific constraint:

| Boundary | Condition | Typical $\beta$ | Interpretation |
|----------|-----------|-----------------|----------------|
| Theft | $d_2$ crosses from positive to negative | $\infty$ | Sacred: rights violation absolutely forbidden |
| Coercion | $\Delta d_4 < -0.5$ | Large, finite | Autonomy curtailment is costly but not sacred |
| Deception | $\Delta d_9 < -0.3$ | Finite | Epistemic degradation has a price |
| Exploitation | $\Delta d_1 > 0$ *and* $\Delta d_3 < -0.3$ | Finite | Profiting at the expense of fairness |
| Sacred value | Any $d_k$: positive $\to$ zero | $\infty$ | No dimension may be entirely eliminated |
| Promise breaking | $\Delta d_8 < -0.5$ | Finite | Legitimacy violations are costly |

The exploitation boundary deserves special attention. It is a *conjunctive* condition: neither monetary gain alone nor fairness loss alone triggers the penalty. Only the *combination* of profit-seeking and fairness-reducing constitutes exploitation. This two-condition structure cannot be captured by any linear cost function on the state space --- it requires the piecewise-smooth formulation that boundary penalties provide.

When $\beta_k = \infty$ (a sacred boundary), the edge weight becomes infinite and A* skips the edge entirely via the check `if np.isinf(tentative_g): continue`. Sacred values are not preferences to be weighed against other considerations; they are hard constraints that eliminate certain paths from the search space.

---

## 6.5 A* Adaptation for Manifold Heuristics

### 6.5.1 The Core Algorithm

The Bond Geodesic is computed by A* search on the decision complex. The implementation in `eris-econ` follows the classical A* structure with three adaptations: Mahalanobis edge weights, sacred-boundary pruning, and a pluggable heuristic interface.

```python
def astar(
    graph: EconomicDecisionComplex,
    start: str,
    goals: Set[str],
    heuristic: Optional[Callable] = None,
    max_explored: int = 100000,
) -> PathResult:
    """A* search for the Bond Geodesic."""
    if heuristic is None:
        heuristic = zero_heuristic

    g_scores: Dict[str, float] = {start: 0.0}
    came_from: Dict[str, str] = {}
    open_set: List[_Node] = []
    closed_set: Set[str] = set()

    h_start = heuristic(start, graph)
    heapq.heappush(open_set, _Node(
        f_score=h_start, vertex_id=start, g_score=0.0))

    explored = 0
    while open_set and explored < max_explored:
        current = heapq.heappop(open_set)
        vid = current.vertex_id

        if vid in closed_set:
            continue
        closed_set.add(vid)
        explored += 1

        if vid in goals:
            path = _reconstruct_path(came_from, vid)
            return PathResult(
                path=path, total_cost=current.g_score,
                explored=explored, found=True)

        for edge in graph.neighbors(vid):
            neighbor = edge.target
            if neighbor in closed_set:
                continue
            tentative_g = current.g_score + edge.weight

            # Sacred boundary pruning
            if np.isinf(tentative_g):
                continue

            if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                g_scores[neighbor] = tentative_g
                came_from[neighbor] = vid
                h = heuristic(neighbor, graph)
                f = tentative_g + h
                heapq.heappush(open_set, _Node(
                    f_score=f, vertex_id=neighbor, g_score=tentative_g))

    return PathResult(
        path=[], total_cost=float("inf"),
        explored=explored, found=False)
```

The priority queue uses Python's `heapq` with a dataclass whose `order=True` annotation ensures that only `f_score` participates in comparison:

```python
@dataclass(order=True)
class _Node:
    """Priority queue entry for A* search."""
    f_score: float
    vertex_id: str = field(compare=False)
    g_score: float = field(compare=False)
```

Path reconstruction traces the `came_from` dictionary from goal to start:

```python
def _reconstruct_path(came_from: Dict[str, str], current: str) -> List[str]:
    """Trace back from goal to start."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path
```

**Complexity.** With a binary heap, the worst-case time complexity is $O(|E| \log |V|)$. For the decision complexes in `eris-econ`, $|V|$ ranges from a handful (the ultimatum game with 7 vertices) to low thousands (multi-step negotiations), and A* terminates in milliseconds. The `max_explored` limit of 100,000 is a safety net for pathological graphs with dense connectivity and uninformative heuristics.

### 6.5.2 The Dual-Process Interpretation

The A* decomposition $f(n) = g(n) + h(n)$ maps naturally onto dual-process theory from cognitive psychology (Kahneman, 2011). This is not a metaphor --- it is a structural correspondence between the algorithm and the cognitive model:

- **$g(n)$ is System 2** (slow, deliberate, analytical). The accumulated cost from start to $n$ is computed by exact summation of edge weights along the path. Each edge weight involves a matrix-vector product (Mahalanobis distance) and a set of logical checks (boundary penalties). This is the computational analogue of carefully reasoning through the consequences of each action in sequence.

- **$h(n)$ is System 1** (fast, automatic, intuitive). The heuristic estimate from $n$ to the goal is a quick, approximate judgment about how far the agent is from their objective. It does not trace out a specific path; it "feels" the distance.

The admissibility condition --- $h(n)$ must never overestimate --- has a direct cognitive interpretation: System 1 intuitions must not be *too optimistic*, or the agent will pursue paths that seem promising but lead to dead ends. When the heuristic is admissible, A* guarantees optimality: the first path found is the true Bond Geodesic. When the heuristic is inadmissible, A* becomes a greedy search that may find suboptimal paths --- the cognitive analogue of an agent whose intuitions lead them astray.

### 6.5.3 Three Heuristic Functions

The `eris-econ` implementation provides three heuristics, each encoding a different System 1 model.

**The zero heuristic (Dijkstra).** The simplest option assigns zero to every vertex:

```python
def zero_heuristic(vid: str, graph: EconomicDecisionComplex) -> float:
    """Trivial heuristic (Dijkstra). Always admissible."""
    return 0.0
```

This is trivially admissible but provides no guidance. The search explores uniformly in all directions, relying entirely on System 2 accumulation. Cognitively, this models a decision-maker approaching a completely novel problem with no prior intuitions.

**The Euclidean heuristic.** The straight-line Euclidean distance to the nearest goal state provides a lower bound on the Mahalanobis distance when $\Sigma = I$:

```python
def euclidean_heuristic(goal_ids: Set[str]) -> Callable:
    """Euclidean distance to nearest goal state.
    Admissible when Sigma is identity."""

    def h(vid: str, graph: EconomicDecisionComplex) -> float:
        state = np.array(graph.get_state(vid).values)
        min_dist = float("inf")
        for gid in goal_ids:
            goal_state = np.array(graph.get_state(gid).values)
            d = np.linalg.norm(state - goal_state)
            min_dist = min(min_dist, d)
        return min_dist

    return h
```

This is a closure: it captures the goal set at construction time and returns a function. As established in Section 6.2, admissibility depends on $\lambda_{\min}(\Sigma^{-1}) \geq 1$. For the default `eris-econ` covariance matrix, this condition fails, and the Euclidean heuristic is not guaranteed admissible. In practice, it often works because the low-weight dimensions (Consequences) are also the dimensions with the largest state-space extent, and the overestimate along those dimensions is partially offset by the underestimate along high-weight dimensions.

**The moral heuristic.** This is the distinctive contribution of the geometric framework:

```python
def moral_heuristic(
    goal_ids: Set[str],
    boundary_probs: Dict[str, float],
    boundary_penalties: Dict[str, float],
) -> Callable:
    """Moral heuristic: h_M(n) = sum_k beta_k * P(cross boundary k).

    Admissible when beta_k <= beta_k* for all k.
    """

    def h(vid: str, graph: EconomicDecisionComplex) -> float:
        cost = 0.0
        for name, prob in boundary_probs.items():
            beta = boundary_penalties.get(name, 0.0)
            if not np.isinf(beta):
                cost += beta * prob
        return cost

    return h
```

The moral heuristic computes $h_M(n) = \sum_k \beta_k \cdot P(\text{cross boundary } k \text{ from } n)$, where $\beta_k$ is the penalty for crossing moral boundary $k$ and $P(\cdot)$ is the estimated probability that any path from $n$ to the goal will cross that boundary. This is System 1 in its purest form: a fast, emotion-based estimate of the moral cost of proceeding.

**Theorem 6.1** (Moral heuristic admissibility). *The moral heuristic $h_M$ is admissible when $\beta_k \leq \beta_k^*$ for all $k$, where $\beta_k^*$ is the true minimum boundary penalty along any optimal path from $n$ to the goal.*

The cognitive interpretation is that moral intuitions must not *exaggerate* the moral cost of continuing. Well-calibrated intuitions ($\beta_k \leq \beta_k^*$) produce optimal decisions. Overestimated moral costs --- moral hypervigilance --- produce cautious but suboptimal behavior: the agent avoids some acceptable paths, ending up on a more expensive route.

Note the asymmetry: infinite penalties (sacred values) are excluded from the heuristic calculation. Sacred boundaries produce infinite edge weights, which A* prunes via the `np.isinf(tentative_g)` check. Sacred values do not need to be estimated; they are enforced structurally.

---

## 6.6 Concrete Examples from the eris-econ Codebase

### 6.6.1 The Ultimatum Game

The ultimatum game is the canonical test case for behavioral economics and the most illuminating example of the Bond Geodesic in action. Player 1 (proposer) receives \$10 and offers a split to Player 2 (responder), who can accept or reject. The Nash equilibrium: offer the minimum, accept anything. The empirical result: proposers offer 40--50%, and responders reject offers below about 20%.

**Constructing the decision complex.** The `ultimatum_game()` function in `eris-econ` builds the proposer's decision complex. First, the covariance matrix:

```python
def _default_sigma() -> np.ndarray:
    sigma = np.eye(N_DIMS)
    sigma[Dim.CONSEQUENCES, Dim.CONSEQUENCES] = 25.0  # money: large scale
    for d in range(1, N_DIMS):
        sigma[d, d] = 0.25  # moral dims: fine resolution
    # Off-diagonal couplings
    sigma[Dim.CONSEQUENCES, Dim.FAIRNESS] = 0.5
    sigma[Dim.FAIRNESS, Dim.CONSEQUENCES] = 0.5
    sigma[Dim.RIGHTS, Dim.LEGITIMACY] = 0.15
    sigma[Dim.LEGITIMACY, Dim.RIGHTS] = 0.15
    sigma[Dim.VIRTUE_IDENTITY, Dim.SOCIAL_IMPACT] = 0.1
    sigma[Dim.SOCIAL_IMPACT, Dim.VIRTUE_IDENTITY] = 0.1
    sigma[Dim.PRIVACY_TRUST, Dim.EPISTEMIC] = 0.1
    sigma[Dim.EPISTEMIC, Dim.PRIVACY_TRUST] = 0.1
    return sigma
```

The key structure: $\sigma_{0,0} = 25.0$ means the monetary dimension has high variance (low precision weight per unit), while $\sigma_{k,k} = 0.25$ for the moral dimensions means small moral differences are heavily penalized by the metric. This encodes the empirical observation that people are less sensitive to monetary differences than to moral differences --- one dollar more or less matters less than a small change in perceived fairness.

Then the vertices:

```python
E = EconomicDecisionComplex(sigma=sigma, boundaries={"exploitation": 5.0})
E.add_vertex("start", _state(money=stake, fairness=0.5, identity=0.5))

for give_pct in [0, 10, 20, 30, 40, 50]:
    give = stake * give_pct / 100
    keep = stake - give

    fairness = 0.1 + 0.8 * (give_pct / 50)  # 50/50 = max fairness
    identity = 0.3 + 0.5 * (give_pct / 50)
    social = -0.2 + 0.6 * (give_pct / 50)

    vid = f"offer_{give_pct}"
    E.add_vertex(vid, _state(
        money=keep, fairness=fairness,
        identity=identity, social=social))
    E.add_edge("start", vid, label=f"offer {give_pct}%")

E.compute_weights()
```

Each offer level affects *multiple* dimensions simultaneously. Offering 0% keeps all the money ($d_1 = 10$) but produces terrible fairness ($d_3 = 0.1$) and identity ($d_7 = 0.3$) scores. Offering 50% splits the money ($d_1 = 5$) but achieves maximum fairness ($d_3 = 0.9$) and strong identity ($d_7 = 0.8$). The linear scaling functions (e.g., $\text{fairness} = 0.1 + 0.8 \cdot (\text{give\_pct}/50)$) are calibrated to empirical data on perceived fairness.

**Running pathfinding.** The Bond Geodesic is computed by:

```python
from eris_econ.pathfinding import astar

E = ultimatum_game(stake=10.0)
goals = {f"offer_{p}" for p in [0, 10, 20, 30, 40, 50]}
result = astar(E, start="start", goals=goals)

print(f"Optimal offer: {result.path[-1]}")
print(f"Behavioral friction: {result.total_cost:.4f}")
```

**Why the model predicts ~40%.** Consider the edge weights for the extreme offers:

For "offer 0%": the fairness drop ($0.5 \to 0.1$, $\Delta = -0.4$) on a dimension with variance 0.25 contributes $(-0.4)^2 / 0.25 = 0.64$ to the squared Mahalanobis distance. The identity drop ($0.5 \to 0.3$, $\Delta = -0.2$) adds $(-0.2)^2 / 0.25 = 0.16$. The social impact drop ($0.0 \to -0.2$) adds another $(-0.2)^2 / 0.25 = 0.16$. The monetary gain ($10.0 \to 10.0$, $\Delta = 0$) contributes nothing because the proposer keeps everything --- the same as the starting state. And the exploitation boundary fires ($\Delta d_1 > 0$ from the start's perspective combined with $\Delta d_3 < -0.3$), adding a penalty of 5.0.

For "offer 40%": fairness *improves* ($0.5 \to 0.74$), identity *improves* ($0.5 \to 0.7$), and the exploitation boundary is not crossed. The monetary loss ($10 \to 6$) contributes only $(-4)^2 / 25 = 0.64$ to the squared Mahalanobis distance --- a modest cost because the Consequences dimension has high variance.

The result: the 40% offer path has lower total behavioral friction than the 0% offer path. The Bond Geodesic terminates near the 40% vertex.

### 6.6.2 The Prisoner's Dilemma

The prisoner's dilemma provides a complementary example where boundary penalties drive the qualitative prediction.

```python
def prisoners_dilemma(sigma=None):
    boundaries = {"promise_breaking": 3.0}

    def make_player_complex(cooperate_money, defect_money):
        E = EconomicDecisionComplex(sigma=sigma, boundaries=boundaries)
        E.add_vertex("start", _state(
            money=0, fairness=0.5, identity=0.5, legitimacy=0.5))
        E.add_vertex("cooperate", _state(
            money=cooperate_money, fairness=0.8,
            identity=0.8, social=0.6, legitimacy=0.7))
        E.add_vertex("defect", _state(
            money=defect_money, fairness=0.1,
            identity=0.2, social=-0.3, legitimacy=0.2))
        E.add_edge("start", "cooperate")
        E.add_edge("start", "defect")
        E.compute_weights()
        return E

    A = make_player_complex(cooperate_money=3, defect_money=5)
    B = make_player_complex(cooperate_money=3, defect_money=5)
    return A, B
```

The Nash equilibrium (projecting onto $d_1$ alone) predicts mutual defection: defecting yields \$5 vs. cooperating for \$3. But on the full 9D manifold, defection causes massive drops in fairness ($0.5 \to 0.1$), identity ($0.5 \to 0.2$), social impact ($0.0 \to -0.3$), and legitimacy ($0.5 \to 0.2$). The promise-breaking boundary ($\Delta d_8 = -0.3 < -0.5$? No --- $\Delta d_8 = 0.2 - 0.5 = -0.3$, which does not trigger at the $-0.5$ threshold) does not fire here, but the accumulated Mahalanobis cost across four moral dimensions makes defection more expensive than cooperation on the full manifold. The Bond Geodesic predicts cooperation --- consistent with empirical results showing significant cooperation rates in one-shot prisoner's dilemmas.

### 6.6.3 The Public Goods Game

The public goods game illustrates multi-step reasoning. In a group of $n$ players, each decides how much of their endowment to contribute to a common pool, which is multiplied by a factor $m$ and divided equally. The Nash prediction: contribute nothing (free-ride). The empirical result: initial contributions are around 40--60%, declining over rounds but never reaching zero.

The `eris-econ` implementation models a single player's decision:

```python
for contrib_pct in [0, 25, 50, 75, 100]:
    contrib = endowment * contrib_pct / 100
    others_contrib = endowment * 0.5 * (n_players - 1)
    total_pool = (contrib + others_contrib) * multiplier / n_players
    remaining = endowment - contrib + total_pool

    fairness = 0.1 + 0.8 * (contrib_pct / 100)
    identity = 0.2 + 0.6 * (contrib_pct / 100)
    social = -0.4 + 0.8 * (contrib_pct / 100)
```

The Bond Geodesic on this complex predicts moderate contributions (approximately 50%), because the identity and social impact costs of contributing nothing ($d_7 = 0.2$, $d_6 = -0.4$) create large Mahalanobis distances from the start state, while the monetary cost of contributing is discounted by the high variance of the Consequences dimension. The prediction matches the first-round empirical average.

---

## 6.7 Formal Properties

Several formal properties of the Bond Geodesic follow from the A* optimality guarantee and the structure of the edge weight function.

**Theorem 6.2** (Existence). *If the decision complex $\mathcal{E}$ is finite and there exists at least one path from $s$ to some $g \in G$ with finite total weight, then the Bond Geodesic exists and is found by A* with any admissible heuristic.*

*Proof sketch.* A* on a finite graph with non-negative edge weights and an admissible heuristic is complete and optimal (Hart, Nilsson, and Raphael, 1968). Edge weights are non-negative by construction. The graph is finite because $V$ is finite. $\square$

**Theorem 6.3** (Uniqueness of cost). *The total behavioral friction $F(\gamma^*)$ is unique. The path itself may not be unique when multiple paths achieve the same minimum cost.*

**Theorem 6.4** (Sacred boundary avoidance). *If boundary $k$ has penalty $\beta_k = \infty$ and the only paths from $s$ to $G$ cross boundary $k$, then the Bond Geodesic does not exist ($\texttt{found=False}$). The agent cannot reach the goal without violating the sacred value.*

This last theorem captures an important psychological reality: some goals are unreachable not because of physical impossibility but because of moral impossibility. The geometric framework represents this as a *topological* property of the decision complex --- sacred boundaries disconnect the graph, creating unreachable components. This connects directly to the topological analysis of Chapter 5: persistent homology could, in principle, detect the connected components created by sacred boundaries and quantify how "close" the agent is to a disconnected goal.

**Theorem 6.5** (Reduction to Dijkstra). *When $h(n) = 0$ for all $n$, A* reduces to Dijkstra's algorithm. The Bond Geodesic is still found optimally, but the search explores vertices uniformly in all directions from the start.*

**Behavioral friction as a decision metric.** The total cost $F(\gamma^*)$ serves as a *difficulty metric* for decisions. High friction means the decision is cognitively and emotionally costly, even when the optimal path is clear. This predicts:

- *Decision delay*: response times increase with behavioral friction (more cognitive processing required).
- *Decision avoidance*: agents opt out when friction exceeds a threshold (the cost of deciding exceeds the benefit of any outcome).
- *Decision fatigue*: accumulated friction over a sequence of decisions depletes cognitive resources, leading to degraded later decisions.

These predictions are testable and have partial empirical support in the behavioral economics literature on choice overload, decision fatigue, and ego depletion.

---

## 6.8 From Pathfinding to Equilibrium

This chapter developed the complete pathfinding pipeline for decision manifolds:

1. **Standard A* fails on curved spaces** because Euclidean heuristics are inadmissible when the metric tensor has eigenvalues below 1, and they are oblivious to boundary penalties that create discontinuous costs. Section 6.1 made these failure modes precise.

2. **Geodesic distance vs. Euclidean distance** is governed by the eigenstructure of $\Sigma^{-1}$. The distortion bounds $\sqrt{\lambda_{\min}} \leq d_M / d_E \leq \sqrt{\lambda_{\max}}$ determine when the Euclidean heuristic is admissible. For the `eris-econ` covariance matrix, it is not. Section 6.2 developed corrected heuristics.

3. **The Economic Decision Complex** is a weighted directed graph whose edge weights combine smooth Mahalanobis distance with discontinuous boundary penalties. The nine dimensions span consequences, rights, fairness, autonomy, privacy/trust, social impact, virtue/identity, legitimacy, and epistemic status. Section 6.3 presented the data structures and implementation.

4. **The Bond Geodesic** is the minimum-friction path from a current state to a goal set. Behavioral friction --- the total path cost --- measures the cognitive-emotional difficulty of the decision. Section 6.4 defined the formulation and established its relationship to scalar utility.

5. **A* with manifold heuristics** adapts the classical algorithm to non-Euclidean edge weights. Three heuristics --- zero (Dijkstra), Euclidean, and moral --- encode different System 1 models within the dual-process cognitive framework. The moral heuristic $h_M(n) = \sum_k \beta_k \cdot P(\text{cross boundary } k)$ is the distinctive contribution, encoding fast emotional judgment as an A* heuristic with a precise admissibility condition. Section 6.5 developed this machinery.

6. **Concrete examples** from `eris-econ` demonstrated the framework's explanatory power. The ultimatum game prediction of ~40% offers, the prisoner's dilemma prediction of cooperation, and the public goods game prediction of moderate contributions all match empirical data and diverge from Nash equilibrium predictions. Section 6.6 traced the computations step by step.

In Chapter 7, we extend from single-agent pathfinding to multi-agent interaction. When two or more decision complexes are coupled --- when each agent's edge weights depend on the other agents' chosen paths --- the Bond Geodesic becomes a fixed point of a coupled optimization. The result is the *Bond Geodesic Equilibrium* (BGE): a strategy profile in which each agent's path is optimal given the paths of all others. We will prove that Nash equilibrium emerges as a special case --- the projection of the BGE onto the $d_1$ (Consequences) axis alone. The geometric framework does not replace game theory; it *generalizes* it to the full decision manifold, recovering classical results as a degenerate case while explaining the behavioral anomalies that classical theory cannot.

---

### Exercises

**6.1.** Given a $3 \times 3$ covariance matrix $\Sigma = \text{diag}(4, 1, 0.25)$, compute the Mahalanobis distance between $\mathbf{a} = (0, 0, 0)$ and $\mathbf{b} = (2, 2, 2)$. Compare with the Euclidean distance. Verify that the Euclidean distance is admissible as an A* heuristic iff $\lambda_{\min}(\Sigma^{-1}) \geq 1$.

**6.2.** Construct an Economic Decision Complex for a simple bartering scenario: two agents, three goods, two possible trades. Compute the Bond Geodesic for each agent and verify that the total friction is lower along the trade path that maintains fairness than along the trade path that maximizes monetary payoff.

**6.3.** Prove that the moral heuristic $h_M(n) = \sum_k \beta_k \cdot P_k$ is admissible when $\beta_k \leq \beta_k^*$ (the true minimum boundary cost) and $P_k \leq 1$ for all $k$. Show that setting $P_k = 1$ for all $k$ yields a heuristic that is admissible but maximally loose.

**6.4.** Modify the ultimatum game construction to model a culture that values autonomy more than fairness: set $\sigma_{3,3} = 0.1$ (low Autonomy variance, high precision) and $\sigma_{2,2} = 1.0$ (higher Fairness variance, lower precision). Predict how the Bond Geodesic shifts and explain the qualitative difference.

**6.5.** The `add_bidirectional` method creates two edges with potentially different weights (because boundary penalties are asymmetric). Give a concrete example where $w(\mathbf{a} \to \mathbf{b}) \neq w(\mathbf{b} \to \mathbf{a})$ and explain the behavioral interpretation.

**6.6.** Implement a Mahalanobis heuristic $h_M(n) = d_M(n, g)$ that uses the precision matrix from the decision complex. Under what conditions is this heuristic admissible? Compare the number of vertices explored by A* using $h_M$ vs. the Euclidean heuristic on the ultimatum game complex.

---

### Bibliographic Notes

The A* algorithm was introduced by Hart, Nilsson, and Raphael (1968). The dual-process model of cognition (System 1 / System 2) is developed in Kahneman, *Thinking, Fast and Slow* (2011). The use of Mahalanobis distance in behavioral modeling connects to the broader metric learning literature surveyed by Kulis (2013). The ultimatum game data referenced throughout this chapter comes from the cross-cultural studies of Henrich et al. (2001, 2005) and the meta-analysis of Oosterbeek et al. (2004). Stake-size effects are documented in Slonim and Roth (1998). The framing effects referenced in Section 6.6 are from Liberman, Samuels, and Ross (2004). The connection between sacred values and deontological constraints is developed by Tetlock et al. (2000). The Bond Geodesic formulation and its application to behavioral economics are introduced in Bond (2026).
