# Chapter 4: The Moral Manifold

## Introduction: The Question of Base Space

Every tensor lives on a manifold. The stress tensor in materials science lives on the manifold of spatial points within a body. The metric tensor in general relativity lives on the manifold of spacetime events. The question for tensorial ethics is: *what is the manifold on which moral tensors are defined?*

This is not a technical detail. The choice of base space determines:
- What counts as a "point" in moral reasoning
- What transformations are admissible
- What it means for two moral situations to be "nearby" or "far apart"
- Where discontinuities and singularities can occur

This chapter develops the concept of the *moral manifold*—the space of morally relevant configurations over which ethical tensors are defined. We proceed carefully, distinguishing geometric structure from metaphysical commitment, and being explicit about what our framework can and cannot do.

---

## 4.1 What Are the Points?

The first question is fundamental: what are the "points" of moral space?

Several candidates present themselves:

### Candidate 1: Possible Actions

On this view, the moral manifold M is the space of possible actions available to an agent. Each point x ∈ M represents a complete specification of what the agent does—not just "help the neighbor" but a full description including manner, timing, motivation, and consequences.

**Strengths:** This connects directly to the practical question of ethics ("what should I do?"). The gradient of satisfaction, ∇S, points toward the best action.

**Weaknesses:** Actions are agent-relative. My action space differs from yours. This makes interpersonal comparison difficult and global structure unclear.

### Candidate 2: States of Affairs

On this view, points are possible states of the world—complete descriptions of how things are or could be. Actions are then paths or vectors, not points: an action takes the world from one state to another.

**Strengths:** This is agent-neutral. All agents evaluate the same space. It connects to consequentialist intuitions: what matters is the state of the world, not who brings it about.

**Weaknesses:** The space is enormous—potentially infinite-dimensional. And it privileges states over processes, which deontologists will resist.

### Candidate 3: Situations

A *situation* is richer than a state: it includes not just how things are, but the relationships between agents, their histories, their commitments, and the options available. A situation is something like "Alice has promised Bob X, Bob is in need of Y, Alice can provide Y but only by breaking the promise to Bob, Carol is watching."

**Strengths:** This captures the morally relevant features without requiring a full specification of the universe. It's closer to how moral reasoning actually works.

**Weaknesses:** What counts as "morally relevant" is theory-dependent. Different ethical theories may carve situation-space differently.

### Candidate 4: Agent-Situation Pairs

On this view, a point is a pair (a, s): an agent a in a situation s. This allows agent-relative evaluations while maintaining a common framework.

**Strengths:** Captures partiality and impartiality as different operations on the space (holding a fixed vs. varying a). Connects to the agent-indexed tensors of Chapter 8.

**Weaknesses:** More complex structure; requires specifying how the agent index interacts with the situation index.

### Our Choice: Structured Situations

For the purposes of this book, we take the moral manifold M to be a space of *structured situations*—specifications of:

1. The agents involved and their relationships
2. The options available to each agent
3. The morally relevant features of the context (needs, promises, histories, stakes)
4. The epistemic state (what is known, by whom)

This is deliberately ecumenical. A consequentialist can project onto states; a deontologist can focus on the structure of relationships and commitments; a virtue ethicist can attend to the character of the agents. The manifold M is the common ground; different theories correspond to different tensors, metrics, and contractions on M.

**Definition 4.1 (Moral Manifold, Informal).** *The moral manifold M is a topological space whose points represent structured moral situations—complete specifications of agents, relationships, options, and morally relevant context.*

We will make this more precise as needed, but the key point is that M is *not* identified with any single candidate above. It is a space rich enough to support all of them as substructures.

---

## 4.2 Coordinates and Transformations: A Discipline

### The Challenge

In physics, coordinate transformations have a precise meaning: a change from one coordinate chart to another covering the same region of manifold. The transformation laws for tensors tell us how components change under such redescription.

In ethics, we speak loosely of "different perspectives," "different framings," "different descriptions." But not all of these are coordinate transformations in the geometric sense. Conflating them invites the criticism that tensorial ethics is vacuous—that by choosing the right "coordinate system," we can make any answer come out.

This section introduces discipline. We distinguish three types of transformation, only the first of which is a coordinate change in the strict sense.

### Type 1: Coordinate Redescriptions (Chart Changes)

A *coordinate redescription* is a change in how we parameterize the same underlying situation. The situation itself is unchanged; only our labels differ.

**Example:** Describing a resource allocation in terms of "amount to Alice" vs. "amount to Bob" (where total is fixed, so x_Bob = T - x_Alice). These are different coordinates on the same one-dimensional manifold.

**Example:** Describing an action as "withholding treatment" vs. "allowing natural death." If these are genuinely synonymous—if they pick out exactly the same action in all morally relevant respects—then they are coordinate redescriptions.

**The tensorial requirement:** Any moral quantity that is a genuine feature of the situation must transform appropriately under coordinate redescriptions. Scalars are invariant; vectors transform by the Jacobian; and so on.

**What this rules out:** It rules out moral evaluations that depend on *mere labeling*. If "allowing to die" sounds better than "withholding treatment" but they denote the same action, a proper moral evaluation should not distinguish them. This is the ethical analogue of general covariance in physics.

### Type 2: Perspective Shifts (Agent Transformations)

A *perspective shift* changes the evaluating agent while holding the situation fixed. This is *not* a coordinate change on M—it is a change in the index on agent-relative tensors.

**Example:** Evaluating the kidney allocation from the physician's perspective vs. a patient's family's perspective. The situation (who the patients are, what their conditions are) is the same. What changes is *who is evaluating*.

**Tensorial treatment:** Perspective shifts are transformations on the *agent index*, not on the manifold coordinates. The rank-2 tensor M_{ia} (evaluation of option i by agent a) transforms in the agent index when we change which perspectives we're considering.

**What this clarifies:** The claim "morality is objective" does not mean all perspectives must agree. It means there are perspective-invariant *structures*—perhaps certain constraints, or the shape of disagreement itself—that remain stable across perspective shifts.

### Type 3: Theory Shifts (Structural Transformations)

A *theory shift* changes the mathematical structure we impose on M: the metric, the connection, the admissible transformations themselves.

**Example:** Switching from a utilitarian metric (all dimensions commensurable) to a lexicographic metric (some dimensions have priority). This is not a coordinate change; it is a change in the *geometry* of moral space.

**Example:** Switching from a theory that treats agent identity as morally irrelevant (impartialism) to one that treats it as relevant (partiality). This changes which transformations are admissible.

**Tensorial treatment:** Theory shifts are *not* symmetries—they change the structure. Different theories correspond to different choices of metric g, connection ∇, and admissibility constraints. The tensorial framework does not adjudicate between theories; it represents each theory precisely, allowing explicit comparison.

### Summary: The Transformation Hierarchy

| Type | What Changes | Status | Example |
|------|--------------|--------|---------|
| Coordinate redescription | Labels/parameterization | True symmetry; tensors must transform appropriately | "x_Alice" vs. "T - x_Bob" |
| Perspective shift | Evaluating agent | Index transformation on agent-relative tensors | Physician vs. family evaluation |
| Theory shift | Metric, connection, structure | Not a symmetry; changes the geometry | Utilitarian vs. lexicographic metric |

**The discipline:** When we say "moral claims should be invariant under redescription," we mean Type 1 transformations. Types 2 and 3 are not symmetries in this sense—they are legitimate sources of variation that the framework makes explicit.

---

## 4.3 Local vs. Global Structure

### Local Structure: The Tangent Space

At each point x ∈ M, there is a *tangent space* T_xM representing the infinitesimal directions one can move from x. In moral terms, the tangent space contains the *possible variations* in the situation: small changes in resource allocation, slight modifications of action, marginal increases in risk.

Moral vectors—obligations, interests, gradients of value—live in tangent spaces. The obligation at x is a vector O(x) ∈ T_xM pointing in the direction one *ought* to move.

Local structure is what we can see from a single point and its immediate neighborhood. It includes:
- The dimension of the tangent space (how many independent directions of variation exist)
- The metric at that point (how we measure distances and angles between nearby situations)
- The satisfaction gradient (which direction improves moral status)

### Global Structure: Topology and Connectedness

Global structure concerns the manifold as a whole:
- **Connectedness:** Can any two situations be reached from each other by a continuous path? Or are there disconnected components (perhaps corresponding to incommensurable forms of life)?
- **Compactness:** Are there "limits" to moral space, or does it extend indefinitely?
- **Holes and handles:** Are there non-trivial loops in moral space? Can circling back to the same situation yield a different moral evaluation (holonomy)?

The global structure of M is an empirical question about ethics, not a mathematical stipulation. If there are genuine *discontinuities* in moral evaluation—situations where small changes produce large jumps in moral status—these appear as features of M's topology.

### Moral Curvature

In differential geometry, *curvature* measures how much a space deviates from flatness. A flat space is one where parallel lines stay parallel; a curved space is one where they converge or diverge.

Does moral space have curvature?

Consider: the obligation at x points in direction O(x). If we move to a nearby point y, the obligation there is O(y). In flat space, we can compare O(x) and O(y) directly—they live in "the same" vector space. In curved space, comparison requires *parallel transport*: moving O(x) along a path to y and seeing how it differs from O(y).

**Moral curvature would mean:** the way obligations vary across moral space is path-dependent. The obligation you arrive at by going x → z → y might differ from the obligation you arrive at by going x → w → y, even if both paths end at the same point y.

Is this plausible? Consider a case: you promise Alice to meet her, then encounter Bob in need. Your obligation to Bob depends on whether you're currently in the "promise to Alice" context or not. The moral landscape is shaped by prior commitments in a way that makes obligation path-dependent.

I do not claim this conclusively establishes moral curvature. But it suggests curvature is at least conceivable, and the framework is prepared to represent it if it turns out to be real.

---

## 4.4 Boundaries and Singularities

### Stratum Boundaries

The most important structural feature for ethics is not curvature but *stratification*: the division of M into regions (strata) where different rules apply.

Within a stratum, smooth trade-offs are possible. You can exchange a little more of X for a little less of Y, and the moral evaluation varies smoothly. But at stratum boundaries, something changes discontinuously:

- **Threshold effects:** Consent at 0.99 is different from consent at 1.0; the distinction between "insufficient" and "sufficient" consent is a boundary.
- **Categorical distinctions:** The difference between killing and letting die, between lying and remaining silent, between a 17-year-old and an 18-year-old—these are boundaries where legal and moral rules change.
- **Veto regions:** Certain options are simply forbidden—not just low-value, but excluded from consideration. The boundary of the forbidden region is a stratum boundary.

**Definition 4.2 (Stratum Boundary).** *A stratum boundary B ⊂ M is a lower-dimensional submanifold where the moral evaluation function S, or the structure of the moral metric g, fails to be smooth.*

Crossing a stratum boundary can produce:
- Discontinuous jumps in S (from permissible to forbidden)
- Changes in the effective dimension (some options disappear)
- Changes in the applicable rules (different duties become operative)

### Singularities and Dilemmas

A *singularity* in M is a point where the normal geometric structure breaks down. In physics, singularities are points of infinite density or undefined curvature. In ethics, they are *genuine dilemmas*: situations where the framework cannot deliver a determinate answer, not because of ignorance, but because of structural conflict.

**Example (Sophie's Choice):** A mother must choose which of her two children will be killed. There is no "right" answer. Any choice involves irreducible moral loss. The situation is *singular*: the satisfaction function S has no maximum, or has multiple maxima with incomparable moral residue.

**Tensorial representation:** A singular point is one where the metric g becomes degenerate (det(g) = 0), or where the satisfaction gradient ∇S is undefined, or where multiple constraint surfaces intersect in pathological ways.

Singularities are not bugs in the framework—they are features. The framework *represents* genuine dilemmas as singular points, rather than forcing a false determinacy. This is an advance over scalar approaches, which must either deliver an answer (by arbitrary tie-breaking) or fall silent (by declaring the situation beyond their scope).

### The Forbidden Region

A special kind of boundary is the *constraint boundary*: the edge of the region where options are permissible.

**Definition 4.3 (Constraint Set).** *The constraint set C ⊂ M is the set of points (situations, actions) that are absolutely forbidden—moral non-starters regardless of other considerations.*

Within C, the satisfaction function S = -∞ by convention. The boundary ∂C is where S transitions from finite values to negative infinity. This is a hard discontinuity.

Examples of constraint boundaries:
- Actions involving non-consensual harm to innocents
- Violations of absolute rights
- Discrimination on protected characteristics

The tensorial framework does not determine *what* goes in C—that is the task of normative ethics, democratic deliberation, and institutional governance. But it represents the *structure* of constraints precisely: as a region with hard boundaries, distinguished from regions of trade-offs.

---

## 4.5 An Example: The Manifold of a Medical Decision

Let us construct M explicitly for a simplified medical decision.

**Situation:** A physician must allocate a scarce treatment among three patients (A, B, C). Each patient has:
- A medical benefit score β_i ∈ [0, 1]
- A waiting time w_i ∈ [0, ∞)
- An age a_i ∈ [0, 120]
- A number of dependents d_i ∈ {0, 1, 2, ...}

**The Manifold:** The space of possible allocations is the 2-simplex:
$$\Delta^2 = \{(p_A, p_B, p_C) : p_i \geq 0, \sum_i p_i = 1\}$$

where p_i is the probability (or fraction) of treatment allocated to patient i.

**Strata:**
- *Interior* (dim = 2): Allocations where all patients have positive probability. Smooth trade-offs possible.
- *Edges* (dim = 1): Allocations between two patients, one excluded.
- *Vertices* (dim = 0): Deterministic allocations. These are the *actual decisions*; the interior represents deliberation space.

**Constraint region:** Suppose Patient C's allocation would involve discrimination (the decision is based on a protected characteristic). Then the region p_C > 0 is forbidden:
$$C = \{(p_A, p_B, p_C) : p_C > 0\}$$

The feasible region is the edge from vertex A to vertex B.

**Metric:** Different metrics on Δ² correspond to different ethical theories:
- *Euclidean metric:* All movements equally costly. Trading probability from A to B costs the same as from B to A.
- *Weighted metric:* Movement toward sicker patients is "easier" (lower moral cost) than movement away.
- *Lexicographic metric:* The allocation must first maximize benefit to the worst-off; only then consider secondary criteria.

**Satisfaction function:** S: Δ² → ℝ assigns a moral score to each allocation. On the interior, S is smooth (we can improve by tilting probability toward more deserving patients). On the constraint boundary, S = -∞.

This simple example illustrates all the features of a moral manifold: points, strata, boundaries, metrics, and the interplay between local trade-offs and global constraints.

---

## 4.6 What Tensorial Structure Does and Does Not Provide

### What It Provides

1. **Precision about structure.** The framework makes explicit what is often implicit: the dimensionality of moral space, the presence of constraints, the metric that governs trade-offs. Disagreements can be localized: do we disagree about the metric, the constraint set, or the contraction?

2. **Representation of hard cases.** Singularities and stratum boundaries are *represented*, not wished away. The framework can say "this is a genuine dilemma" in a precise way.

3. **Theory comparison.** Different ethical theories become different geometric structures on the same underlying manifold. We can ask precisely how they differ and where they agree.

4. **Computability.** Manifolds, tensors, and constraint regions can be implemented. This enables machine ethics that is explicit about its assumptions.

### What It Does Not Provide

1. **Metaethical grounding.** The framework does not answer: "Why be moral?" or "What makes moral claims true?" It represents moral structure; it does not ground normativity.

2. **Content determination.** The framework does not tell you what the constraint set C should be, or what metric g is correct. That remains the work of normative ethics, empirical moral psychology, and democratic deliberation.

3. **Motivation.** Knowing the structure of moral space does not, by itself, motivate moral action. The question of moral psychology—why we care about morality—is orthogonal to the question of moral structure.

4. **Resolution of all disagreement.** If two theories correspond to genuinely different metrics, the framework represents both precisely but does not choose between them. Pluralism at the level of metric choice remains.

### The Modest Claim

Our claim is structural, not metaphysical:

> *Tensorial representation is a better structural model of moral phenomena than scalarization.*

"Better" means: it captures more of what we want to say, loses less information, makes implicit assumptions explicit, and enables analysis that scalar frameworks cannot support.

This is a modeling claim, not a claim about what morality *really is* at the deepest metaphysical level. Whether moral tensors are "out there" in some robust realist sense, or are useful constructs for organizing moral thought, is a question the framework does not settle. It is compatible with realism, constructivism, and expressivism alike—each can use the framework while giving different accounts of what the tensors represent.

---

## 4.7 Conclusion: The Manifold as Common Ground

The moral manifold M is the base space over which all ethical tensors are defined. Its points are structured situations; its structure includes local tangent spaces, global topology, stratum boundaries, and singular points.

Different ethical theories correspond to different structures *on* M:
- Different metrics (utilitarian vs. egalitarian vs. lexicographic)
- Different constraint sets (what is absolutely forbidden)
- Different contractions (how multi-dimensional evaluation reduces to action)

But all theories share M as common ground. This makes disagreement tractable: we can ask whether two theories differ in their metrics, their constraints, or their contractions. We can identify where they agree (perhaps on the constraint set) and where they diverge (perhaps on the metric).

The manifold is not the whole of ethics. It is the *stage* on which ethics plays out—the space of possibilities that moral reasoning navigates. The next chapters develop the actors: the tensors of various ranks that live on M, the metric that measures distances between points, and the transformations that reveal what is invariant and what is perspective-dependent.

But without the manifold, there is nowhere for tensors to live. The moral manifold is the foundation.

---

## Technical Appendix: Formal Definitions

**Definition A.1 (Moral Manifold, Formal).** *A moral manifold is a paracompact Hausdorff topological space M equipped with:*
1. *A stratification {M_i}_{i ∈ I} into smooth manifolds of varying dimensions;*
2. *A partial order ⪯ on I satisfying the frontier condition: M_i ∩ cl(M_j) ≠ ∅ implies i ⪯ j;*
3. *Whitney's condition (B) at all stratum boundaries.*

**Definition A.2 (Coordinate Chart).** *A coordinate chart on a stratum M_i is a homeomorphism φ: U → ℝ^{dim(M_i)} from an open set U ⊂ M_i to Euclidean space. A coordinate transformation is a composition φ' ∘ φ^{-1}: ℝ^n → ℝ^n.*

**Definition A.3 (Admissible Transformation).** *An admissible transformation of the moral manifold is a homeomorphism ψ: M → M that preserves the stratification: ψ(M_i) = M_{σ(i)} for some permutation σ of strata. Type 1 transformations (coordinate redescriptions) are admissible; Type 3 transformations (theory shifts) are not.*

**Definition A.4 (Constraint Set).** *A constraint set C ⊂ M is a closed subset such that any satisfaction function S: M → ℝ ∪ {-∞} satisfies S|_C = -∞. The boundary ∂C is a stratum boundary where S has a discontinuity.*

**Definition A.5 (Moral Singularity).** *A point x ∈ M is a moral singularity if:*
1. *The metric tensor g_x is degenerate (det(g_x) = 0); or*
2. *The satisfaction function S is not differentiable at x; or*
3. *Multiple constraint surfaces intersect at x creating a cone of forbidden directions.*

*Singularities represent genuine dilemmas: points where the moral structure does not determine a unique best response.*

---

*The manifold is the ground. The tensors are the figures.*

*Before we can say what obligation points toward, we must know the space in which it points.*

*This is that space: M, the moral manifold, where ethics takes its shape.*
