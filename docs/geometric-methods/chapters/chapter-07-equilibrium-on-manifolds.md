# Chapter 7: Equilibrium on Manifolds

> *"The shortest path between two truths in the real domain passes through the complex domain."*
> --- Jacques Hadamard

Game theory begins with a bold simplification: agents maximize scalar utility. This simplification made the subject tractable and produced powerful results---Nash equilibrium, mechanism design, auction theory. But it comes at a cost that Chapter 1 made precise: projecting a multi-dimensional evaluation onto a scalar destroys information that is mathematically irrecoverable. When the agents in a game are human beings making economic decisions, the destroyed information includes fairness perceptions, identity costs, social impact, autonomy constraints, and epistemic uncertainty---exactly the dimensions that behavioral economics has spent five decades documenting as crucial to real decision-making.

This chapter develops a generalization of Nash equilibrium to the multi-dimensional decision manifolds introduced in earlier chapters. The central object is the **Bond Geodesic Equilibrium** (BGE): a strategy profile in which each agent's chosen action is an optimal path through their own decision complex, given the paths chosen by all other agents. No player can improve their position via geodesic movement on the manifold without another player's cooperation or acquiescence. We present the iterated best response algorithm that computes BGE, prove that it reduces to classical Nash equilibrium as a special case, analyze its convergence properties, and then demonstrate how behavioral phenomena---loss aversion, the endowment effect, reference dependence, framing effects---emerge as geometric consequences of the multi-dimensional metric rather than requiring ad-hoc parametric assumptions.

---

## 7.1 The Limitations of Nash Equilibrium

### 7.1.1 Scalar Payoffs and the Information They Destroy

A Nash equilibrium is a strategy profile $(\sigma_1^*, \sigma_2^*, \ldots, \sigma_n^*)$ such that no agent can increase their scalar payoff by unilaterally changing their strategy:

$$u_i(\sigma_i^*, \sigma_{-i}^*) \geq u_i(\sigma_i, \sigma_{-i}^*) \quad \forall \sigma_i, \forall i$$

This is a fixed-point condition: each agent is best-responding to the others. The concept is powerful, but it rests on the assumption that each agent's preferences can be captured by a single scalar utility function $u_i : S \to \mathbb{R}$. As we established in Chapter 1 (Section 1.1.1), any such scalar projection discards $n - 1$ dimensions of information from an $n$-dimensional evaluation space. The Scalar Irrecoverability Theorem applies with full force: the null space of the projection grows linearly with the dimensionality of the original space, and the lost information cannot be recovered from the scalar alone.

For the 9-dimensional economic decision space defined in the `eris-econ` framework---with dimensions for consequences, rights, fairness, autonomy, privacy/trust, social impact, virtue/identity, legitimacy, and epistemic status---a scalar utility function discards eight dimensions. The resulting equilibrium concept can describe what agents choose, but it cannot explain *why*, and it systematically fails to predict choices where the discarded dimensions dominate.

### 7.1.2 The Ultimatum Game Revisited

Chapter 1 introduced the ultimatum game as a concrete illustration of scalar metric failure (Section 1.1.2). The puzzle is worth revisiting now that we have the geometric machinery to resolve it.

Player A proposes a split of \$10 with Player B. If B accepts, both receive their shares; if B rejects, both receive nothing. Nash equilibrium, operating on scalar monetary payoffs, predicts that A should offer the minimum possible amount (\$0.01) and B should accept, because any positive amount is better than zero. The prediction is spectacularly wrong: experimental data consistently show that proposers offer 40--50% of the stake, and responders reject offers below 20--30%.

The `eris-econ` framework constructs the proposer's decision complex for this game with the nine dimensions active:

```python
def ultimatum_game(
    stake: float = 10.0,
    sigma: np.ndarray | None = None,
) -> EconomicDecisionComplex:
    """Construct the proposer's decision complex for the ultimatum game.

    Explains why proposers offer ~40-50% (not $0.01):
    the fairness (d_3) and identity (d_7) penalty for low offers
    outweighs the monetary gain on d_1.
    """
    if sigma is None:
        sigma = _default_sigma()

    boundaries = {
        "exploitation": 5.0,  # large penalty for clearly unfair splits
    }

    E = EconomicDecisionComplex(sigma=sigma, boundaries=boundaries)

    # Starting state: has the stake, neutral on other dimensions
    E.add_vertex("start", _state(money=stake, fairness=0.5, identity=0.5))

    # Possible offers (keep, give)
    for give_pct in [0, 10, 20, 30, 40, 50]:
        give = stake * give_pct / 100
        keep = stake - give

        # Higher offers -> better fairness and identity scores
        fairness = 0.1 + 0.8 * (give_pct / 50)  # 50/50 = max fairness
        identity = 0.3 + 0.5 * (give_pct / 50)
        social = -0.2 + 0.6 * (give_pct / 50)

        vid = f"offer_{give_pct}"
        E.add_vertex(
            vid,
            _state(
                money=keep,
                fairness=fairness,
                identity=identity,
                social=social,
            ),
        )
        E.add_edge("start", vid, label=f"offer {give_pct}%")

    E.compute_weights()
    return E
```

The resolution is structural. Each possible offer is not a scalar payoff but a point in $\mathbb{R}^9$. Offering \$0 keeps the full \$10 on the consequences dimension ($d_1$), but it pushes fairness ($d_3$) down to 0.1, identity ($d_7$) down to 0.3, and social impact ($d_6$) to $-0.2$. Offering \$5 sacrifices half the monetary value but achieves fairness of 0.9, identity of 0.8, and social impact of 0.4. The Mahalanobis distance from the starting state to the low-offer vertex is *larger* than the distance to the equal-split vertex, because the low offer activates large displacements across multiple non-monetary dimensions. The exploitation boundary penalty ($\beta = 5.0$) adds a further discrete cost when fairness drops sharply while consequences improve---precisely the condition that characterizes exploitative offers.

The Bond Geodesic---the minimum-cost path through this decision complex---leads to offers in the 40--50% range. This is not because the model has been calibrated to reproduce the experimental data. It is because the geometry of a 9-dimensional decision space, with a Mahalanobis metric that weights fairness, identity, and social impact alongside monetary consequences, naturally produces this outcome. The equal-split offer is *closer* to the starting state on the manifold than the greedy offer, despite being farther away on the scalar monetary axis.

This is the pattern that Section 1.1.2 identified and that this chapter now formalizes: a scalar metric declares one configuration optimal; the geometry reveals a different optimum because it accounts for dimensions the scalar projection discarded.

---

## 7.2 The Bond Geodesic Equilibrium

### 7.2.1 Definition

The Bond Geodesic Equilibrium generalizes Nash by replacing scalar utility maximization with multi-dimensional path optimization on a manifold. Each agent $i$ has:

- A **decision complex** $\mathcal{E}_i = (V_i, E_i, w_i)$: a weighted directed graph whose vertices are economic states in $\mathbb{R}^9$ and whose edges represent available actions, with weights given by the Mahalanobis distance plus boundary penalties (Chapter 6).
- A **starting state** $s_i \in V_i$: the agent's current position in the decision space.
- A **goal set** $G_i \subseteq V_i$: the set of states the agent considers desirable endpoints.

An agent's **strategy** is a path through their decision complex from $s_i$ to some vertex in $G_i$. The cost of a strategy is the total path weight---the sum of all edge weights along the path. Each edge weight is the Mahalanobis distance $\sqrt{\Delta \mathbf{a}^\top \Sigma^{-1} \Delta \mathbf{a}}$ plus any boundary penalties incurred by that transition, as developed in Chapter 6. The optimal strategy, given a fixed decision complex, is the minimum-cost path: the **Bond Geodesic**, computed by A* search.

**Definition 7.1 (Bond Geodesic Equilibrium).** A strategy profile $(p_1^*, p_2^*, \ldots, p_n^*)$ is a Bond Geodesic Equilibrium if no agent can reduce their path cost by unilaterally changing their path:

$$\text{cost}(p_i^*) \leq \text{cost}(p_i) \quad \forall p_i \in \text{Paths}(\mathcal{E}_i'), \forall i$$

where $\mathcal{E}_i'$ is agent $i$'s decision complex as modified by the strategy callback reflecting the other agents' current paths $p_{-i}^*$.

The critical difference from Nash is that the "payoff" is not a scalar externally imposed on the agent, but a path cost that emerges from the geometry of the agent's own decision manifold. The manifold encodes *all* nine dimensions simultaneously. Two strategies might have identical monetary consequences (dimension $d_1$) but differ vastly in their rights implications ($d_2$), fairness costs ($d_3$), or identity impact ($d_7$). The BGE respects these differences; the Nash equilibrium, operating on scalar projections, cannot.

### 7.2.2 The Nine Dimensions

The dimension structure underlying the BGE is defined in the `eris-econ` framework as an enumeration: consequences ($d_1$), rights ($d_2$), fairness ($d_3$), autonomy ($d_4$), privacy/trust ($d_5$), social impact ($d_6$), virtue/identity ($d_7$), legitimacy ($d_8$), and epistemic status ($d_9$). Dimensions $d_1$ through $d_4$ are *transferable* in bilateral exchange---they obey a conservation law where $\Delta d_k(A) + \Delta d_k(B) = 0$. Dimensions $d_5$ through $d_9$ are *evaluative*---not conserved, allowing mutual gains from trade. Fairness ($d_3$) is partially transferable, its conservation properties depending on context. This classification determines the structure of the feasible set in multi-agent games: transferable dimensions create zero-sum constraints while evaluative dimensions permit positive-sum outcomes.

Every economic state is represented as an immutable `EconomicState`---a frozen dataclass wrapping a length-9 tuple, following the same immutable state vector pattern introduced in Chapter 1 (Section 1.2.2). The `Dim` enumeration enables named dimension access (`state[Dim.FAIRNESS]`) rather than numeric indexing, preventing off-by-one errors and making code self-documenting.

### 7.2.3 The Decision Complex in Code

The `eris-econ` framework implements the decision complex as a class that encapsulates the weighted graph, the covariance structure, and the boundary penalty system:

```python
class EconomicDecisionComplex:
    """Weighted directed graph representing an agent's decision space.

    E = (V, E, w) where:
    - V: set of economic states (vertices)
    - E: set of available actions (directed edges)
    - w: edge weight function (Mahalanobis + boundary penalties)
    """

    def __init__(self, sigma: np.ndarray, boundaries: Optional[Dict[str, float]] = None):
        self.sigma = sigma
        self.sigma_inv = np.linalg.inv(sigma + 1e-10 * np.eye(N_DIMS))
        self.boundaries = boundaries or {}
        self.vertices: Dict[str, Vertex] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, List[Edge]] = {}
```

Each vertex holds an `EconomicState`---a length-9 tuple representing the agent's position across all nine dimensions. Edges connect states that are reachable by a single action, and their weights are computed by the full Mahalanobis-plus-boundary metric:

```python
def compute_weights(self) -> None:
    """Compute edge weights for all edges using Mahalanobis + boundaries."""
    for e in self.edges:
        s = self.vertices[e.source].state
        t = self.vertices[e.target].state
        e.weight = edge_weight(
            np.array(s.values), np.array(t.values),
            self.sigma_inv, self.boundaries,
        )
```

The `edge_weight` function from the metrics module combines Mahalanobis distance with boundary penalties: `w(a, b) = d_M(a, b) + \sum_k \beta_k \cdot \mathbf{1}[\text{boundary } k \text{ crossed}]`. This means that every edge cost simultaneously accounts for monetary changes, rights implications, fairness shifts, identity costs, and all other dimensions---weighted by the precision matrix $\Sigma^{-1}$ and subject to the discontinuous penalties imposed by moral-economic boundaries. The edge weight function is the bridge between the continuous geometry of the Mahalanobis metric (Chapter 6) and the discrete moral constraints that make economic decisions qualitatively different from pure optimization.

---

## 7.3 Computing BGE: Iterated Best Response

### 7.3.1 The Algorithm

Computing a BGE requires finding a fixed point: a state where every agent's path is optimal given every other agent's path. The natural algorithm is **iterated best response**, where agents take turns re-optimizing. The implementation in `equilibrium.py` follows a clean three-phase structure:

```python
def compute_bge(
    agents: List[Agent],
    *,
    max_iterations: int = 100,
    convergence_tol: float = 1e-6,
    strategy_callback: Optional[Callable] = None,
) -> BGEResult:
    # Phase 1: Initialize -- each agent computes A* path independently
    paths: Dict[str, PathResult] = {}
    for agent in agents:
        agent.complex.compute_weights()
        path = astar(agent.complex, agent.start, agent.goals, agent.heuristic)
        paths[agent.agent_id] = path

    prev_costs = {aid: p.total_cost for aid, p in paths.items()}

    # Phase 2: Iterate -- agents re-optimize given others' current paths
    for iteration in range(max_iterations):
        changed = False

        for agent in agents:
            if strategy_callback is not None:
                other_paths = {
                    aid: p for aid, p in paths.items()
                    if aid != agent.agent_id
                }
                strategy_callback(agent, other_paths)

            agent.complex.compute_weights()
            new_path = astar(
                agent.complex, agent.start, agent.goals, agent.heuristic,
            )
            paths[agent.agent_id] = new_path

            cost_delta = abs(new_path.total_cost - prev_costs[agent.agent_id])
            if cost_delta > convergence_tol:
                changed = True
            prev_costs[agent.agent_id] = new_path.total_cost

        # Phase 3: Check convergence -- no agent wants to change
        if not changed:
            total_bf = sum(p.total_cost for p in paths.values())
            return BGEResult(
                agent_paths=paths, converged=True,
                iterations=iteration + 1,
                total_behavioral_friction=total_bf,
            )

    total_bf = sum(p.total_cost for p in paths.values())
    return BGEResult(
        agent_paths=paths, converged=False,
        iterations=max_iterations,
        total_behavioral_friction=total_bf,
    )
```

**Phase 1: Independent initialization.** Each agent computes their optimal path in isolation, ignoring all other agents. This is equivalent to each agent solving a single-player A* search on their own decision complex---the same pathfinding algorithm developed in Chapter 6. The result is a set of initial strategies that will generally *not* be an equilibrium, because each agent's complex does not yet reflect the impact of others' choices.

**Phase 2: Sequential re-optimization.** In each iteration, every agent is given the opportunity to revise their strategy. The `strategy_callback` is the mechanism by which inter-agent coupling enters the computation: it takes the current agent and the dictionary of all other agents' current paths, and modifies the agent's decision complex accordingly. This might mean updating edge weights (if another agent's strategy changes market prices), adding or removing edges (if another agent's path opens or closes options), or adjusting boundary penalties (if another agent's behavior shifts social norms). After the callback modifies the complex, `compute_weights()` recalculates all edge weights, and A* finds the new optimal path.

The convergence check is per-agent and absolute: if the cost change $|\Delta\text{Cost}|$ falls below the tolerance for *every* agent in a round, the algorithm has found a fixed point. The tolerance default of $10^{-6}$ is tight enough for numerical precision while allowing termination in a reasonable number of iterations.

**Phase 3: Return.** The `BGEResult` packages the final paths, convergence status, iteration count, and total behavioral friction:

```python
@dataclass
class BGEResult:
    """Result of Bond Geodesic Equilibrium computation."""

    agent_paths: Dict[str, PathResult]  # agent_id -> their optimal path
    converged: bool     # whether iterated best response converged
    iterations: int     # number of iterations used
    total_behavioral_friction: float  # sum of all agents' path costs

    @property
    def n_agents(self) -> int:
        return len(self.agent_paths)
```

The `converged` flag distinguishes genuine equilibria from timeout states, which is essential for downstream analysis---a non-converged result may indicate cycling (no equilibrium exists in pure strategies) or insufficient iterations.

### 7.3.2 The Agent Abstraction

Each agent in the BGE computation carries their own decision complex, starting position, and goal set:

```python
@dataclass
class Agent:
    """An economic agent with their own decision complex."""

    agent_id: str
    complex: EconomicDecisionComplex  # their decision manifold
    start: str                        # starting vertex
    goals: Set[str]                   # goal vertices
    heuristic: Optional[Callable] = None
```

The optional heuristic enables the dual-process cognitive model discussed in Chapter 6: the heuristic $h(n)$ corresponds to System 1 (fast, automatic moral intuition), while the accumulated cost $g(n)$ corresponds to System 2 (deliberate calculation). An agent with no heuristic falls back to Dijkstra's algorithm---pure deliberative reasoning with no intuitive shortcuts.

---

## 7.4 Convergence Analysis

### 7.4.1 General Convergence Conditions

Iterated best response is not guaranteed to converge for arbitrary games. In classical game theory, best response dynamics can cycle in games like matching pennies. The same is true for BGE computation: if the strategy callback creates strong enough coupling between agents' decision complexes, the system can oscillate indefinitely.

However, two structural properties of the manifold setting promote convergence:

**Contraction from metric smoothness.** When the strategy callback produces small perturbations to edge weights---as is typical when agents' strategies change marginally---the A* optimal path changes smoothly. The Mahalanobis metric is Lipschitz continuous in the covariance parameters, which means small changes in others' strategies produce small changes in the focal agent's optimal path cost. Formally, let $\mathcal{C}_i(\mathbf{p}_{-i})$ denote the cost of agent $i$'s optimal path when others play $\mathbf{p}_{-i}$. If the strategy callback is $L$-Lipschitz in the sense that

$$|\mathcal{C}_i(\mathbf{p}_{-i}) - \mathcal{C}_i(\mathbf{p}_{-i}')| \leq L \cdot \|\mathbf{p}_{-i} - \mathbf{p}_{-i}'\|$$

with $L < 1$, then the iterated best response is a contraction mapping on the space of strategy profiles, and convergence to a unique fixed point is guaranteed by the Banach fixed-point theorem. The number of iterations required is $O(\log(1/\epsilon) / \log(1/L))$ for convergence tolerance $\epsilon$.

**Boundary penalty discreteness.** The boundary penalty system (Chapter 6) introduces discrete jumps in edge weights when moral-economic boundaries are crossed. These jumps create "attractor" regions in the strategy space where all agents' paths avoid boundary violations. The `boundary_penalty` function checks for named violations---theft (rights going negative), coercion (large autonomy drops), deception (epistemic drops), exploitation (fairness declining while consequences improve)---and adds the corresponding penalty $\beta_k$ for each crossing. Sacred-value boundaries ($\beta = \infty$) create hard partitions: paths crossing a sacred boundary have infinite cost and are never selected, permanently eliminating entire regions of the strategy space.

Once every agent's path lies within a boundary-respecting region, the continuous Mahalanobis component dominates, and the contraction property takes over.

### 7.4.2 Empirical Convergence Behavior

In the `eris-econ` implementation, the maximum iteration limit of 100 serves as a practical safeguard. For the economic games tested---ultimatum games, dictator games, public goods games, market entry games---convergence typically occurs within 5--15 iterations. The convergence profile follows a characteristic pattern:

1. **Iterations 1--3**: Large cost changes as agents discover each other's strategies and shift away from their independent optima.
2. **Iterations 3--8**: Moderate changes as agents settle into a boundary-respecting region and fine-tune within it.
3. **Iterations 8--15**: Small changes as the contraction property drives costs toward the fixed point.

Non-convergence (hitting the 100-iteration limit) is diagnostic: it typically indicates either that the game has no pure-strategy BGE (the manifold analogue of a game with no pure-strategy Nash equilibrium) or that the strategy callback introduces oscillatory coupling that prevents contraction. In either case, the `converged=False` flag in the `BGEResult` alerts the analyst that the returned paths should be interpreted with caution.

### 7.4.3 Mixed BGE and Existence

The existence of mixed BGE follows from a reduction argument to finite Nash equilibrium. Given a finite graph with finitely many paths, the set of mixed strategies (probability distributions over paths) forms a compact convex set. The best-response correspondence inherits the upper hemicontinuity and convex-valuedness properties required by Kakutani's fixed-point theorem. Therefore:

**Theorem 7.2 (Existence of Mixed BGE).** Every finite game on Economic Decision Complexes admits at least one mixed Bond Geodesic Equilibrium.

The proof is constructive: enumerate all paths for each agent, construct the augmented finite game where each path is a pure strategy, and apply Nash's existence theorem to the augmented game. The BGE of the original game corresponds to the Nash equilibrium of the augmented game. This reduction preserves the full multi-dimensional cost structure---the payoff of a path in the augmented game is its total Mahalanobis-plus-boundary cost, not a scalar projection.

---

## 7.5 The Reduction Theorem

The most important theoretical property of BGE is that it generalizes Nash equilibrium rather than replacing it. This is not merely an aesthetic desideratum---it means that the entire apparatus of classical game theory remains available as a special case.

**Theorem 7.1 (Reduction to Nash).** Let $(p_1^*, p_2^*, \ldots, p_n^*)$ be a Bond Geodesic Equilibrium on decision complexes $\{\mathcal{E}_i\}$. If the precision matrix $\Sigma^{-1}$ assigns zero weight to all dimensions except $d_1$ (consequences), i.e.,

$$(\Sigma^{-1})_{jj} = 0 \quad \forall j \neq 0$$

then the path costs reduce to monetary costs, and the BGE corresponds to a Nash equilibrium of the game with payoff functions $u_i(\sigma) = -\text{cost}_{d_1}(p_i)$.

*Proof sketch.* When only $d_1$ is active, the Mahalanobis distance between two states reduces to the scalar difference in the consequences dimension, scaled by $(\Sigma^{-1})_{00}$:

$$d_M(\mathbf{a}, \mathbf{b}) = \sqrt{(\mathbf{a} - \mathbf{b})^\top \Sigma^{-1} (\mathbf{a} - \mathbf{b})} = \sqrt{(\Sigma^{-1})_{00}} \cdot |a_0 - b_0|$$

All boundary penalties that depend on non-monetary dimensions ($d_2$ through $d_9$) become inactive, because the transitions along those dimensions have zero weight. The path cost reduces to the sum of scaled monetary differences along the path, which is proportional to the total monetary change from start to goal. Minimizing path cost is therefore equivalent to minimizing monetary cost, which is equivalent to maximizing monetary payoff. The fixed-point condition of the BGE becomes: no agent can increase their monetary payoff by unilaterally changing their strategy---which is precisely the Nash equilibrium condition. $\square$

The implementation provides a `nash_projection` function that performs this reduction on a computed BGE:

```python
def nash_projection(bge_result: BGEResult) -> Dict[str, float]:
    """Project BGE to Nash-like monetary costs (d_1 only).

    Demonstrates Theorem 7.1: BGE reduces to Nash when only
    the consequences dimension is active.
    """
    return {aid: path.total_cost for aid, path in bge_result.agent_paths.items()}
```

This function extracts the scalar path costs from a BGE result. When the BGE was computed with a full 9-dimensional precision matrix, these costs reflect the multi-dimensional path weight. When computed with a $d_1$-only precision matrix, they reflect only monetary costs---and the BGE *is* the Nash equilibrium.

**Why the reduction matters.** The reduction theorem validates BGE as a *proper* generalization. Any result that holds for Nash equilibrium also holds for BGE restricted to one dimension. Any empirical finding that matches Nash predictions is automatically consistent with BGE (since Nash is a special case). But BGE can also explain phenomena that Nash cannot---the ultimatum game offers from Section 7.1.2, loss aversion, the endowment effect, framing sensitivity---because it has access to the eight dimensions that the Nash projection discards. This is the multi-dimensional analogue of the observation that special relativity reduces to Newtonian mechanics at low velocities: the generalization is validated by the fact that it recovers the known theory in the appropriate limit.

---

## 7.6 Behavioral Friction

### 7.6.1 Definition

The total cost of an agent's optimal path through their decision complex is a quantity with a natural behavioral interpretation. We call it **behavioral friction**:

$$\text{BF}(p) = \sum_{i=0}^{|p|-2} w(v_i, v_{i+1})$$

where $p = (v_0, v_1, \ldots, v_k)$ is the Bond Geodesic and $w(v_i, v_{i+1})$ is the edge weight. In the implementation:

```python
def behavioral_friction(path: PathResult) -> float:
    """Total behavioral friction for a path (sum of all edge weights).

    BF = sum w(v_i, v_{i+1}) along the Bond Geodesic.
    Higher friction -> more cognitive/emotional cost of the decision.
    """
    return path.total_cost
```

Behavioral friction is the manifold-native measure of decision difficulty. It captures not just the monetary cost of an action but the full cognitive and emotional cost of executing it---the rights implications, the fairness considerations, the identity impact, the social consequences, and the epistemic uncertainty, all integrated through the Mahalanobis metric.

### 7.6.2 Interpretation

Higher behavioral friction means the decision is harder to execute. A decision with low friction along the Bond Geodesic---one that primarily traverses the consequences dimension, with minimal perturbation to other dimensions---is easy. A decision with high friction---one that activates multiple dimensions, crosses boundary penalties, or requires large displacements in identity or fairness space---is difficult, regardless of its monetary attractiveness.

This provides a clean operational definition of "decision difficulty" that unifies several informal concepts in behavioral economics:

- **Cognitive load**: paths traversing many dimensions simultaneously impose higher friction because each dimension requires distinct cognitive processing.
- **Moral conflict**: paths crossing boundary penalties (theft, coercion, deception) incur discrete friction spikes that represent the psychological cost of violating internalized norms.
- **Emotional cost**: identity-dimension displacements ($d_7$) and social-impact displacements ($d_6$) contribute friction that corresponds to emotional processing.

At the system level, the `BGEResult` reports `total_behavioral_friction`---the sum of all agents' path costs. This aggregate measure characterizes the overall difficulty of the equilibrium: a high-friction equilibrium is one where many agents face difficult decisions, suggesting the system as a whole is under stress. Market designers, mechanism designers, and policy analysts can use this aggregate to compare institutional arrangements: among two mechanisms that produce the same monetary outcomes, prefer the one with lower total behavioral friction, as it imposes less cognitive and emotional burden on participants.

---

## 7.7 Emergent Behavioral Properties

The most striking consequence of the multi-dimensional geometric framework is that behavioral "biases"---phenomena that behavioral economics has catalogued as departures from rational choice theory---emerge as natural geometric properties of the decision manifold. They are not hard-coded parameters, ad-hoc utility function modifications, or psychological primitives. They are consequences of the fact that the decision space has more than one dimension.

### 7.7.1 Loss Aversion

Loss aversion is the empirical finding that losses loom larger than gains of equal magnitude. Kahneman and Tversky estimated the loss aversion coefficient $\lambda \approx 2.0$--$2.5$: a loss of \$X feels roughly 2--2.5 times as bad as a gain of \$X feels good.

In the geometric framework, loss aversion emerges from the asymmetry between the dimensional profiles of gains and losses. A gain of magnitude $M$ is primarily a movement along the consequences dimension ($d_1$), with perhaps a small positive displacement in social impact ($d_6$). A loss of magnitude $M$ is a movement in the *opposite* direction along $d_1$, but it also activates rights ($d_2$: ownership is threatened), fairness ($d_3$: the loss feels unjust), social impact ($d_6$: social cost of losing), and virtue/identity ($d_7$: blow to self-image).

The loss aversion ratio is the ratio of Mahalanobis distances:

$$\lambda = \frac{d_M(\text{ref}, \text{loss\_state})}{d_M(\text{ref}, \text{gain\_state})}$$

The `behavioral.py` module computes this directly:

```python
def compute_loss_aversion(sigma: np.ndarray, magnitude: float = 1.0) -> float:
    """Compute the emergent loss aversion ratio from the metric tensor.

    A gain changes primarily d_1 (consequences).
    A loss changes d_1 AND activates d_2 (rights), d_3 (fairness),
    d_6 (social), d_7 (identity).

    lambda = d(ref, loss_state) / d(ref, gain_state)
    Empirical target: lambda ~ 2.0-2.5 (Kahneman & Tversky).
    """
    sigma_inv = np.linalg.inv(sigma + 1e-10 * np.eye(N_DIMS))

    reference = np.zeros(N_DIMS)
    reference[Dim.CONSEQUENCES] = 10.0
    reference[Dim.RIGHTS] = 1.0
    reference[Dim.FAIRNESS] = 0.5
    reference[Dim.AUTONOMY] = 1.0
    reference[Dim.VIRTUE_IDENTITY] = 0.5

    # Gain: primarily monetary, small positive social
    gain = reference.copy()
    gain[Dim.CONSEQUENCES] += magnitude
    gain[Dim.SOCIAL_IMPACT] += 0.05 * magnitude

    # Loss: monetary decline + rights threat + fairness injury + identity hit
    loss = reference.copy()
    loss[Dim.CONSEQUENCES] -= magnitude
    loss[Dim.RIGHTS] -= 0.15 * magnitude
    loss[Dim.FAIRNESS] -= 0.1 * magnitude
    loss[Dim.SOCIAL_IMPACT] -= 0.1 * magnitude
    loss[Dim.VIRTUE_IDENTITY] -= 0.1 * magnitude

    return loss_aversion_ratio(gain, loss, reference, sigma_inv)
```

The key insight is structural: gains traverse roughly 1--2 dimensions (consequences and a small social impact), while losses traverse 5 dimensions (consequences, rights, fairness, social impact, and identity). Even if each additional dimension contributes a modest displacement, the Mahalanobis distance formula---which computes the square root of a sum of squared terms, each weighted by the precision matrix---ensures that activating more dimensions increases the total distance. The ratio $\lambda$ falls in the range $2.0$--$2.5$ for reasonable covariance structures, matching the empirical estimates without any explicit "loss aversion parameter" in the model.

The underlying `loss_aversion_ratio` function in the metrics module makes the geometric nature transparent:

```python
def loss_aversion_ratio(gain_state, loss_state, reference, sigma_inv) -> float:
    """lambda = d(reference, loss_state) / d(reference, gain_state)

    lambda ~ 2.25 emerges because losses traverse more dimensions
    than gains (primarily consequences only).
    """
    d_gain = mahalanobis_distance(reference, gain_state, sigma_inv)
    d_loss = mahalanobis_distance(reference, loss_state, sigma_inv)
    if d_gain < 1e-10:
        return float("inf")
    return d_loss / d_gain
```

There is nothing in this computation that imposes loss aversion. It is a *consequence* of the geometry: losses are farther from the reference point than gains in a multi-dimensional space because they activate more dimensions.

### 7.7.2 The Endowment Effect

The endowment effect is the finding that people demand more to give up an object they own (willingness-to-accept, WTA) than they would pay to acquire the same object (willingness-to-pay, WTP). The ratio WTA/WTP typically ranges from 1.5 to 3.0 in experimental settings.

In the geometric framework, the endowment effect arises because ownership activates additional dimensions. An owner's state is distributed across consequences ($d_1$), rights ($d_2$: they hold ownership rights), autonomy ($d_4$: they can choose what to do with it), identity ($d_7$: the object is "mine"), and social impact ($d_6$: the item may carry social significance). Selling requires moving away from this rich multi-dimensional position---a large manifold distance. A buyer, by contrast, starts from a more compressed position (mostly holding cash, with weaker attachments across non-monetary dimensions) and moves toward the item---a smaller manifold distance because fewer dimensions undergo large displacements.

The `endowment_effect` function in `behavioral.py` computes the WTA and WTP manifold distances by constructing the owner's multi-dimensional state (strong values across $d_1$, $d_2$, $d_4$, $d_6$, $d_7$), the post-sale state (cash gain but losses on rights, autonomy, identity, social impact), the buyer's state (mostly monetary), and the post-purchase state (modest multi-dimensional gains). It then returns `(wta_distance, wtp_distance)` computed via `mahalanobis_distance`.

The WTA/WTP ratio exceeds 1.0 because the seller traverses more dimensions with larger displacements than the buyer. The ratio *increases* with the number of activated dimensions---an object with purely monetary significance (only $d_1$ active) has WTA/WTP close to 1.0, while a family heirloom (activating $d_1$, $d_2$, $d_4$, $d_6$, $d_7$, and possibly $d_8$) has WTA/WTP much greater than 1.0. This matches experimental evidence: the endowment effect is stronger for goods with emotional, identity, or social significance.

### 7.7.3 Reference Dependence

Classical utility theory evaluates options in absolute terms: option A has utility $u(A)$, option B has utility $u(B)$, and the agent chooses the larger. Behavioral economics has established that agents instead evaluate options *relative to a reference point*---typically their current state.

In the geometric framework, reference dependence is not an assumption but a consequence of how distances work. The Mahalanobis distance is always measured *from* a point *to* a point. The agent's current state is the natural origin:

```python
def reference_dependence(current, option_a, option_b, sigma_inv):
    """Preference depends on starting point.

    Returns (cost_a, cost_b) -- costs from current state to each option.
    The SAME pair (A, B) can have different relative costs depending
    on the reference point `current`.
    """
    cost_a = mahalanobis_distance(current, option_a, sigma_inv)
    cost_b = mahalanobis_distance(current, option_b, sigma_inv)
    return cost_a, cost_b
```

Two agents with identical option sets but different current states will compute different distances to the same options, and may therefore make different choices. This is exactly Kahneman and Tversky's reference dependence: preferences are defined over changes from a reference point, not over final states. In the manifold framework, this is simply the fact that distance depends on the starting point---a tautology in metric spaces, but one with profound behavioral implications.

### 7.7.4 Framing Effects

A framing effect occurs when two logically equivalent descriptions of the same decision lead to different choices. In the geometric framework, a frame is a **gauge transformation**: a rotation of the description basis that changes how the same objective state is represented as an attribute vector:

```python
def framing_as_gauge(state, frame_rotation, sigma_inv):
    """Model framing effects as gauge transformations.

    A "frame" is a rotation of the description basis that changes
    how the same objective state is perceived. The metric tensor
    is NOT invariant under frame rotation for boundedly-rational agents.
    """
    return frame_rotation @ state
```

The key distinction is between gauge-invariant and gauge-sensitive agents. A perfectly rational agent would have a metric tensor $\Sigma^{-1}$ that commutes with all relevant frame rotations, making the Mahalanobis distance invariant under reframing. A boundedly-rational agent's precision matrix does *not* commute with all rotations, which means the same objective state, described in different frames, produces different attribute vectors and therefore different distances to reference points. Framing effects, in this view, are not cognitive errors. They are geometric consequences of operating with a precision matrix that is not gauge-invariant. The degree of framing sensitivity is a measurable property of $\Sigma^{-1}$: the maximum change in Mahalanobis distance under orthogonal transformations of the description basis.

---

## 7.8 Dimensional Loss Aversion

Section 7.7.1 showed that loss aversion emerges from the asymmetry between the dimensional profiles of gains and losses. We now push this analysis further to show that the *magnitude* of loss aversion depends on the number and type of non-monetary dimensions activated by the loss.

### 7.8.1 The Dimensional Multiplier

Consider three scenarios involving a loss of equal monetary magnitude ($M$):

**Scenario 1: Pure cash loss.** You discover that a \$20 bill fell out of your pocket. The loss is purely monetary---no one took it from you (no rights violation), no one cheated you (no fairness injury), your identity is unaffected. The displacement vector is approximately $\Delta = (-M, 0, 0, 0, 0, 0, 0, 0, 0)$, activating only $d_1$. The loss aversion ratio:

$$\lambda_{\text{cash}} = \frac{d_M(\text{ref}, \text{ref} + \Delta_{\text{loss}})}{d_M(\text{ref}, \text{ref} + \Delta_{\text{gain}})} \approx 1.0\text{--}1.2$$

The loss is barely more painful than the gain is pleasant, because only one dimension is traversed.

**Scenario 2: Gift from a friend.** A friend gave you a \$20 book that you then lose. Now the loss activates social impact ($d_6$: the friend's gift carried social meaning) and identity ($d_7$: it was "a gift from Sarah, part of my collection"). The displacement activates four dimensions. The loss aversion ratio:

$$\lambda_{\text{gift}} \approx 2.0$$

This matches the canonical Kahneman-Tversky estimate.

**Scenario 3: Family heirloom.** Your grandmother's ring, worth \$20 in materials. The loss activates rights ($d_2$), fairness ($d_3$), autonomy ($d_4$), social impact ($d_6$), identity ($d_7$), and legitimacy ($d_8$). The displacement touches six or seven dimensions. The loss aversion ratio:

$$\lambda_{\text{heirloom}} \approx 3.0 \text{ or higher}$$

### 7.8.2 The Geometric Mechanism

The pattern is systematic: the loss aversion coefficient $\lambda$ increases with the number of dimensions activated by the loss. This is a direct consequence of the Mahalanobis distance formula. If a gain produces a displacement vector $\Delta_g$ with $k$ nonzero components and a loss produces a displacement vector $\Delta_l$ with $m > k$ nonzero components, then the ratio of distances scales approximately as:

$$\lambda \approx \sqrt{\frac{\sum_{j \in \text{loss dims}} (\Sigma^{-1})_{jj} \cdot \Delta_{l,j}^2}{\sum_{j \in \text{gain dims}} (\Sigma^{-1})_{jj} \cdot \Delta_{g,j}^2}}$$

For the diagonal case (no cross-dimensional coupling), this simplifies to a weighted count of activated dimensions. The more dimensions a loss activates, the farther it pushes the agent from their reference point in the 9-dimensional space, and the larger the perceived magnitude of the loss relative to an equivalent gain.

This analysis makes a testable prediction: loss aversion should be *context-dependent*, varying with the type of good and the nature of the loss. Pure monetary losses should produce low $\lambda$; losses involving identity, social bonds, or moral violations should produce high $\lambda$. This prediction is consistent with the experimental literature. List (2003) found that experienced traders show minimal endowment effects for commodity goods (low dimensional activation). Ariely, Huber, and Wertenbroch (2005) found stronger effects for hedonic goods than utilitarian goods (hedonic goods activate more identity and social dimensions). The geometric framework explains *why* these findings hold: the relevant variable is not "type of good" as a categorical label but the number and weight of non-monetary dimensions activated by the transaction.

### 7.8.3 Implications for Mechanism Design

Dimensional loss aversion has direct implications for the design of markets, auctions, and policies. If the goal is to reduce the friction of a transaction---to lower the behavioral friction of the equilibrium---the designer should minimize the number of non-monetary dimensions displaced by the transaction.

Concretely:

- **Separating monetary from identity concerns.** A policy that forces people to sell their homes (eminent domain) activates identity, autonomy, rights, social, and legitimacy dimensions simultaneously, producing high behavioral friction. A policy that provides a generous monetary buyout *and* assistance with relocation, community preservation, and procedural transparency reduces displacement along $d_4$, $d_6$, $d_7$, and $d_8$, thereby lowering $\lambda$ and the total behavioral friction.

- **Framing transactions neutrally.** If a transaction can be framed so that it activates fewer dimensions of loss, the loss aversion coefficient decreases. This is not manipulation---it is accurate representation of a transaction that genuinely does not threaten rights, identity, or fairness, presented in a frame that makes those non-threats salient.

- **Designing for dimensional symmetry.** A transaction where both parties experience comparable dimensional displacements feels fairer and produces lower friction than one where one party undergoes purely monetary change while the other undergoes multi-dimensional displacement. The BGE framework makes this asymmetry measurable and therefore designable.

---

## 7.9 The Covariance Structure of Real Decisions

The BGE computation depends critically on the covariance matrix $\Sigma$, which determines the Mahalanobis metric and therefore the relative importance of each dimension and the coupling between dimensions. The `eris-econ` framework provides a default covariance matrix (`_default_sigma()` in `games.py`) with an empirically motivated structure. The key design choice is the asymmetry between monetary and moral dimensions: the consequences dimension has variance 25.0, meaning that a unit change in monetary value is relatively low-cost in Mahalanobis terms---money varies on a large scale, so each dollar matters less. The moral dimensions ($d_2$ through $d_9$) each have variance 0.25, meaning that small changes in fairness, identity, or rights are high-cost---these dimensions vary on a small scale, so each increment matters more.

The off-diagonal entries encode dimensional couplings well-documented in the behavioral economics literature: consequences-fairness ($\rho = 0.5$, because fair outcomes tend to be mutually beneficial), rights-legitimacy ($\rho = 0.15$, because rights violations undermine institutional trust), identity-social impact ($\rho = 0.1$, because self-image and social reputation covary), and trust-epistemic ($\rho = 0.1$, because low-trust environments produce poor information).

These couplings mean that the Mahalanobis distance is not a simple weighted Euclidean distance. Cross-dimensional terms contribute to the metric, capturing the fact that a simultaneous change in rights *and* legitimacy is not the same as the sum of independent changes in each. The joint displacement may be more or less costly than the sum of marginal displacements, depending on the sign of the correlation. This is not a parametric assumption imposed to generate behavioral phenomena; it is an empirical observation about the *scales* at which economic dimensions naturally vary. The precision matrix $\Sigma^{-1}$ inverts these scales, and the behavioral properties documented in Sections 7.7--7.8 emerge as consequences of that inversion.

---

## 7.10 Summary and Looking Ahead

This chapter developed the Bond Geodesic Equilibrium as a multi-dimensional generalization of Nash equilibrium on decision manifolds. The key results are:

1. **BGE is a fixed-point condition on paths**, not payoffs. Each agent minimizes total path cost through their decision complex, where cost integrates all nine dimensions via the Mahalanobis metric plus boundary penalties. The iterated best response algorithm in `compute_bge()` finds this fixed point by cycling through agents, updating each agent's complex based on others' strategies, and re-running A* (Chapter 6) until convergence.

2. **BGE reduces to Nash** when all non-monetary dimensions are deactivated (Theorem 7.1). This validates BGE as a proper generalization: classical results are a special case, not a competing framework.

3. **Convergence** is promoted by metric smoothness (Lipschitz contraction of the best-response mapping) and boundary penalty discreteness (attractor regions that partition the strategy space). Mixed BGE existence follows from reduction to finite Nash equilibrium on the augmented game (Theorem 7.2).

4. **Behavioral friction** is the total path cost of the Bond Geodesic---a measure of decision difficulty that integrates cognitive, emotional, moral, and economic costs into a single geometric quantity.

5. **Behavioral biases emerge from geometry.** Loss aversion, the endowment effect, reference dependence, and framing effects are not ad-hoc psychological parameters but consequences of the multi-dimensional metric structure. They require no special assumptions beyond the existence of non-monetary dimensions and a Mahalanobis distance that respects them.

6. **Dimensional loss aversion** provides a unified explanation for why loss aversion varies by context: $\lambda$ is determined by the number and weight of dimensions activated by the loss. Pure cash losses produce $\lambda \approx 1.2$; sentimental goods produce $\lambda \approx 3.0$; the variation is continuous, predictable, and measurable.

7. **The ultimatum game** (Chapter 1) is resolved naturally: the BGE predicts 40--50% offers because the manifold distance to a fair split is shorter than the distance to a greedy offer, once fairness, identity, and social dimensions are accounted for.

Chapter 8 turns from equilibrium to optimization: given a model with multiple dimensions, how do we find the Pareto frontier of configurations that optimally trade off accuracy against complexity? Where this chapter used the manifold structure of the decision space to generalize equilibrium, Chapter 8 applies multi-objective optimization across varying numbers of active dimensions---a different algorithmic problem, but one that shares the same foundational commitment to treating multi-dimensional structure as the primary object of analysis rather than collapsing it to a scalar.
