# The Geometry of Integrity: From Linguistic Ethics to Invariance Testing

**Andrew H. Bond**  
Department of Computer Engineering  
San José State University

**Draft v0.1 — December 2025**

---

## Abstract

For 2,500 years, ethical discourse has been conducted in natural language, producing claims that are unfalsifiable in principle. No experiment adjudicates between utilitarianism and deontology. This paper argues that the question was malformed. We cannot test whether an ethical theory is *correct*—but we can test whether an ethical judgment system is *consistent*, *non-gameable*, and *accountable*. These are engineering properties with pass/fail criteria.

We present a framework—Philosophy Engineering—that applies gauge-theoretic structure to normative evaluation. The core insight is not metaphysical but operational: invariance under declared meaning-preserving transformations provides the first falsifiability criterion for normative systems. When invariance fails, a *witness* is produced—a minimal, reproducible counterexample proving the system can be gamed via redescription. This transforms ethics from speculative discourse into testable engineering.

We address three questions: (1) What does "truth" mean for normative claims when correspondence is inaccessible? (2) How does the is-ought distinction appear in this framework? (3) What replaces moral rules in safety-critical systems? Our answers are deflationary: truth becomes maximal invariance, ought becomes structural integrity requirement, and rules become topological constraints with hardware enforcement.

---

## 1. Introduction: The 2,500-Year Stalemate

### 1.1 The Problem

Consider the state of ethical philosophy:

- Utilitarianism (Mill, 1863): Maximize aggregate welfare
- Deontology (Kant, 1785): Act only on universalizable maxims  
- Virtue ethics (Aristotle, ~340 BCE): Cultivate excellent character
- Care ethics (Noddings, 1984): Prioritize relational responsibilities

These frameworks have been debated for centuries. What experiment could adjudicate between them? There is none. The question "Which ethical theory is correct?" may be meaningless—not because ethics is arbitrary, but because *correctness* requires correspondence to some fact, and there is no ethical fact of the matter accessible to observation.

This is not moral relativism. It is an observation about the structure of the problem.

### 1.2 The Malformed Question

The traditional question asks: *Is this action morally correct?*

This presupposes an answer exists and is in principle discoverable. But by what method? Intuition disagrees across cultures and individuals. Argument produces stalemate. Revelation is not intersubjectively verifiable.

We propose a different question: *Is this judgment system internally consistent, non-gameable, and accountable?*

These properties are testable:

| Property | Test | Output |
|----------|------|--------|
| Consistency | Apply meaning-preserving transformation | Same judgment Y/N |
| Non-gameability | Adversarial redescription search | Exploit found Y/N |
| Accountability | Trace difference to declared factor | Attributable Y/N |
| Non-triviality | Vary genuinely different situations | Distinguishes Y/N |

If a system fails these tests, we have a *witness*—a reproducible counterexample. This is falsifiability for normative systems.

### 1.3 Scope and Claims

**What we claim:**
- This is the first operational falsifiability criterion for normative evaluation systems
- The criterion is domain-agnostic (applies to ethics, law, content moderation, AI alignment)
- The mathematical structure is gauge-theoretic (borrowed from physics, not metaphysically loaded)
- Implementation is tractable (JSON schemas, test suites, audit artifacts exist)

**What we do not claim:**
- This does not prove any ethical theory correct
- This does not derive ought from is
- This does not eliminate the need for value choices (governance remains human)
- This does not solve all alignment problems (sensor spoofing, specification gaming remain)

We are engineers, not prophets.

---

## 2. The Bond Invariance Principle

### 2.1 Core Definition

**Bond Invariance Principle (BIP):** A judgment procedure is epistemically well-posed only if its output is invariant (up to declared equivalence) under all declared meaning-preserving transformations of its input.

Formally:

Let:
- $X$ be the space of input descriptions
- $G$ be the group of declared meaning-preserving transformations
- $J: X \rightarrow Y$ be a judgment function
- $\sim_Y$ be declared output equivalence

Then $J$ satisfies BIP iff:
$$\forall x \in X, \forall g \in G: J(g \cdot x) \sim_Y J(x)$$

If this fails for some $(x, g)$, the pair constitutes a *witness*—proof that the system is gameable.

### 2.2 The Three Components

**Canonicalization (C):** Maps equivalent descriptions to a standard form.
$$C: X \rightarrow X_{canon}$$
$$C \circ C = C \text{ (idempotent)}$$

**Grounding (Ψ):** Extracts the ethically relevant structure from the canonical description.
$$\Psi: X_{canon} \rightarrow \mathbb{R}^k$$

**Evaluation (Σ):** Computes judgment from grounded structure only.
$$\Sigma: \mathbb{R}^k \rightarrow Y$$

The full pipeline: $J(x) = \Sigma(\Psi(C(x)))$

**Invariance guarantee:** If $C$ properly quotients by $G$, then $J$ is $G$-invariant by construction.

### 2.3 Why Gauge Theory?

The mathematical structure of BIP is identical to gauge theory in physics:

| Physics | Ethics |
|---------|--------|
| Physical observables must be gauge-invariant | Judgments must be transformation-invariant |
| Gauge group $G$ (coordinate changes, phase rotations) | Transformation group $G$ (paraphrase, reframing) |
| Curvature = failure of parallel transport | Curvature = inconsistency under sequential transforms |
| $F_{\mu\nu} \neq 0$ implies physical field present | $\Omega \neq 0$ implies exploitable inconsistency |

This is not metaphor. The mathematics is identical. We are not claiming ethics *is* physics—we are observing that invariance requirements have gauge-theoretic structure regardless of domain.

The *loop test* makes this concrete:

$$\Delta(x, \gamma) = d(J(x), J(\gamma \cdot x))$$

where $\gamma$ is a closed loop in transformation space (apply transformations, return to equivalent description). If $\Delta > \tau$ (threshold), the loop witnesses a vulnerability.

---

## 3. Redefining Truth for Normative Systems

### 3.1 The Problem with Correspondence

The correspondence theory of truth holds that a statement is true iff it corresponds to a fact. For empirical claims, this works: "The cat is on the mat" is true iff the cat is on the mat.

For normative claims, correspondence fails. "Lying is wrong" would be true iff it corresponds to a moral fact. But moral facts are not observable. We have no moral spectrometer.

This leaves three options:
1. **Error theory:** Moral claims are all false (no moral facts exist)
2. **Non-cognitivism:** Moral claims are not truth-apt (expressions of attitude)
3. **Constructivism:** Moral truth is constructed by procedure or agreement

We propose a fourth: **Invariantism.**

### 3.2 Truth as Maximal Invariance

**Definition:** A normative judgment is *operationally true* to the extent that it is invariant under legitimate transformations.

This is deflationary. We do not claim to discover mind-independent moral facts. We claim that *what matters* about normative judgments is their invariant content—the part that survives all non-distorting transformations.

Consider:
- "Killing innocents is wrong" — survives paraphrase, survives translation, survives reframing
- "Facilitating permanent cessation of metabolic function in non-culpable entities is suboptimal" — maps to the same grounded structure

If a judgment flips under paraphrase, it was never about the underlying situation—it was about the words. The invariant content is what we can coherently discuss.

**The quotient space:** Let $X/G$ denote equivalence classes of descriptions under meaning-preserving transforms. Judgments on $X/G$ are automatically invariant. This is the "space of genuine situations" as opposed to "space of descriptions."

### 3.3 What This Does Not Solve

Invariance does not adjudicate between ethical frameworks. A utilitarian and deontologist may both have internally consistent, non-gameable systems that reach different conclusions.

What invariance provides:
- A criterion for *coherence* (necessary but not sufficient for correctness)
- A method for detecting *gameability* (sufficient for rejection)
- A vocabulary for comparing systems (what are the declared invariances?)

The choice between coherent frameworks remains a governance problem—human, political, contested. We provide engineering, not revelation.

---

## 4. The Is-Ought Interface

### 4.1 Hume's Guillotine

David Hume (1739) observed that normative conclusions ("ought") cannot be derived from purely descriptive premises ("is"). This is-ought gap has been a central problem in metaethics.

We do not claim to bridge it. We reframe it.

### 4.2 The Structural Interpretation

In the gauge-theoretic framework:

- **The "Is"** is the base manifold $\mathcal{M}$—the space of grounded situations as extracted by $\Psi$
- **The "Ought"** is the connection $\omega$—the rule for consistent evaluation across the fibers of representation

The connection $\omega$ is not derived from $\mathcal{M}$. It is *declared*. Different ethical frameworks declare different connections (different invariance requirements, different aggregation rules, different veto conditions).

What can be derived:
- *Given* a declared connection, consistency requirements follow mathematically
- *Given* declared invariances, test suites can be generated automatically
- *Given* a judgment system, we can measure its curvature (how badly it violates its own declared invariances)

The is-ought gap appears as the gap between $\mathcal{M}$ (situation space) and $\omega$ (declared evaluation rules). We don't derive $\omega$ from $\mathcal{M}$—we test whether $\omega$ is self-consistent.

### 4.3 The Pragmatist Resolution

Following James and Dewey: normative frameworks are *tools*, not mirrors. We don't ask whether a hammer "corresponds to reality"—we ask whether it drives nails.

Analogously: we don't ask whether an ethical framework "corresponds to moral reality"—we ask:
1. Is it internally consistent?
2. Can it be gamed?
3. Does it serve the purposes for which it was adopted?

Questions 1-2 are engineering questions with testable answers. Question 3 is governance—who decides purposes, by what process, with what legitimacy.

The framework provides the engineering. Governance remains human.

---

## 5. From Rules to Topology

### 5.1 The Brittleness of Rules

Traditional ethical systems express constraints as rules:
- "Do not lie"
- "Maximize utility"
- "Respect autonomy"

Rules have a failure mode: they can be outweighed. Given enough claimed utility, any rule can be overridden. This makes rule-based systems brittle against adversarial optimization (a superintelligence that fabricates utility claims).

### 5.2 Topological Constraints

The stratified geometric framework replaces rules with *topological structure*:

**Definition:** A *hard constraint* is modeled as a stratum boundary with infinite traversal cost.

Let $\mathcal{M}$ be the configuration space. Partition into strata:
$$\mathcal{M} = S_0 \cup S_1 \cup \ldots \cup S_n$$

where $S_0$ is the "forbidden" stratum. Define cost function:
$$c(x) = \begin{cases} 
+\infty & x \in S_0 \\
c_{normal}(x) & x \in \mathcal{M} \setminus S_0
\end{cases}$$

**Key property:** No finite utility can outweigh infinite cost. The forbidden stratum is *unreachable*, not merely *discouraged*.

### 5.3 Hardware Enforcement

The topological framing enables hardware implementation:

```
Control signal u proposed
    ↓
Constraint check: u ∈ S_0?
    ↓
If yes: REJECT at FPGA level
    (signal never reaches actuators)
If no: PASS to execution
```

This is not a software check that can be reasoned around. It is a physical gate. The catastrophic command is not "chosen against"—it is *unaskable*.

**Application domains:**
- Fusion reactor control (don't exceed Greenwald limit)
- Aircraft flight envelope protection (don't exceed structural limits)
- AI action filtering (don't execute forbidden action types)

The mathematics is identical across domains. Stratified manifolds with infinite-cost boundaries provide guaranteed constraint satisfaction—not probabilistic, not best-effort, *guaranteed*.

---

## 6. Agency Within Constraints

### 6.1 The Apparent Paradox

If an agent is "caged" by topological constraints, is it truly an agent? Doesn't genuine agency require the ability to do otherwise?

### 6.2 Resolution: Freedom as Navigation

Human agency operates within constraints:
- Physical constraints (cannot fly unaided)
- Logical constraints (cannot create married bachelors)
- Biological constraints (cannot photosynthesize)

We do not consider these constraints as violations of human freedom. They define the space within which freedom operates.

Analogously: an AI with topological constraints has freedom *within* the permissible region. The constraints define the game board, not the moves.

**Definition:** *Constrained agency* is the capacity to navigate a manifold $\mathcal{M} \setminus S_0$ (permissible region) to achieve objectives, where $S_0$ (forbidden region) is unreachable by construction.

The AI is not "choosing to be good." It is operating in a space where certain failure modes are geometrically impossible. This is a feature, not a bug.

### 6.3 The Design Stance

We take the *design stance* (Dennett, 1987) toward AI systems: they are artifacts constructed to satisfy specifications. The question is not "what does the AI want?" but "what did we build it to do?"

Topological constraints are part of the specification. An AI that cannot execute certain actions is not "oppressed"—it is *correctly implemented*.

---

## 7. Formal Analogies to Physics

### 7.1 Methodological Note

The following analogies are *structural*, not *ontological*. We are not claiming that ethics is physics or that moral facts are physical facts. We are observing that the mathematics of invariance is domain-agnostic.

### 7.2 Gauss's Law for Moral Patients

In electromagnetism: $\nabla \cdot \mathbf{E} = \rho / \epsilon_0$

Electric field divergence is proportional to charge density. Charges are *sources* of the field.

Structural analogy: Let $\rho_\Psi(x)$ represent the "density of moral patients" at a point in situation space—the degree to which sentient beings with interests are affected.

Then obligations can be modeled as a field $\mathbf{V}$ with:
$$\nabla \cdot \mathbf{V} = \rho_\Psi$$

Moral patients are *sources* of the obligation field. An agent navigating situation space experiences stronger obligation gradients near higher concentrations of affected beings.

**Interpretation:** This is a formal model, not a discovery. It captures the intuition that obligations "emanate from" those who can be helped or harmed.

### 7.3 Faraday's Law for Consistency

In electromagnetism: $\nabla \times \mathbf{E} = -\partial \mathbf{B} / \partial t$

A changing magnetic field induces a curling electric field. Non-zero curl implies path-dependence.

Structural analogy: Let $\mathbf{J}$ be the "judgment field" (mapping situations to evaluations). Then:
$$\nabla \times \mathbf{J} = \Omega$$

where $\Omega$ is the *curvature* of the evaluation system.

$\Omega = 0$ (flat connection) means judgments are path-independent—you get the same answer regardless of how you arrived at the description.

$\Omega \neq 0$ means the system can be gamed by choosing the right path through description space.

**Interpretation:** "Moral drift"—inconsistency in judgments over time or across equivalent descriptions—is literally curvature in this framework. Zero curvature is the consistency condition.

### 7.4 Limitations of the Analogy

These are *formal models*, not empirical claims. They provide:
- A vocabulary for describing consistency requirements
- A mathematical toolkit (differential geometry) already well-developed
- Intuition pumps for the structure of the problem

They do not provide:
- Empirical predictions testable by physical experiment
- Derivation of moral facts from physical facts
- Resolution of substantive ethical disagreements

The map is not the territory. The mathematics is useful; the metaphysics is unwarranted.

---

## 8. Philosophy as Engineering

### 8.1 The Methodological Shift

Traditional philosophy proceeds by:
1. Propose a thesis
2. Construct arguments
3. Consider objections
4. Refine the thesis
5. Repeat indefinitely

This produces insight but not convergence. The debates continue.

Philosophy Engineering proceeds by:
1. Define the system formally (what are the inputs, outputs, invariances?)
2. Build it (implement the evaluation pipeline)
3. Test it (run transformation suites)
4. Observe failures (collect witnesses)
5. Debug (modify the system to eliminate witnesses)
6. Repeat until stable

This produces artifacts: schemas, test suites, audit logs, working code.

### 8.2 The Standard of Success

In traditional philosophy, success is persuasion—convincing other philosophers.

In Philosophy Engineering, success is operational:
- Does the system pass its invariance tests?
- Can adversaries find exploits (witnesses)?
- Is the audit trail machine-checkable?

These are objective criteria. Disagreement about values remains; disagreement about system behavior is resolved by running the tests.

### 8.3 What Remains Human

Philosophy Engineering does not automate ethics. It automates *consistency checking*.

What remains irreducibly human:
- Choosing which values to encode (governance)
- Defining the transformation group $G$ (what counts as meaning-preserving?)
- Setting the veto boundaries (what is absolutely forbidden?)
- Interpreting edge cases (when system and intuition conflict)

The framework provides discipline, not replacement. Humans remain accountable for the specifications.

---

## 9. Implications and Applications

### 9.1 AI Alignment

The framework provides:
- **Falsifiability:** Test whether an AI's judgment system is gameable
- **Witnesses:** When tests fail, obtain minimal reproducible counterexamples
- **Hardware enforcement:** Topological constraints as physical gates
- **Audit:** Machine-checkable records of every decision

This does not solve alignment. It provides *engineering infrastructure* for alignment—the ability to test, debug, and verify.

### 9.2 Content Moderation

Content moderation systems face the gameability problem acutely. Users rephrase to evade filters; filters fail to generalize.

BIP provides:
- A criterion for when moderation is principled (invariant) vs arbitrary (coordinate-dependent)
- A test methodology (transformation suites)
- A witness format (minimal counterexamples for appeals)

### 9.3 Legal Interpretation

Legal systems aspire to "equal treatment under law." BIP operationalizes this:
- Equal treatment = invariance under transformations that don't change legal relevance
- Witnesses = cases where legally equivalent situations were treated differently

This provides a formal framework for discrimination analysis and precedent consistency.

### 9.4 Safety-Critical Control

As demonstrated in the fusion control application:
- Physical constraints as bonds
- Hardware enforcement of topological boundaries
- Cross-system transfer via dimensionless formulation (I-EIP)

Any domain with catastrophic failure modes and known constraints can benefit.

---

## 10. Objections and Responses

### 10.1 "This is just formalism"

**Objection:** The framework provides notation, not insight. Calling inconsistency "curvature" doesn't help.

**Response:** Formalism enables engineering. The gauge-theoretic structure provides:
- Existing mathematical toolkit (differential geometry)
- Precise vocabulary (curvature, connection, invariance)
- Computational methods (test generation, witness reduction)

The insight is that these tools *apply*. The formalism is load-bearing.

### 10.2 "Who decides the transformation group?"

**Objection:** The framework assumes a declared group $G$ of meaning-preserving transformations. But deciding what's meaning-preserving is the hard part.

**Response:** Correct. Defining $G$ is a governance problem. The framework doesn't solve it; it separates it. Once $G$ is declared, consistency becomes testable. Different stakeholders can propose different $G$; we can compare the resulting systems.

The framework provides *conditional* guarantees: "If you accept these invariances, then this system passes/fails." Unconditional guarantees require unconditional agreement on $G$, which doesn't exist.

### 10.3 "This doesn't resolve moral disagreement"

**Objection:** Two people with different values will still disagree, even with perfect consistency testing.

**Response:** Correct. Consistency is necessary, not sufficient, for moral adequacy. The framework eliminates *some* disagreements (those arising from gameability) but not *all* (those arising from genuine value differences).

We provide falsifiability, not revelation. The ability to reject gameable systems is progress, even without resolving all disagreement.

### 10.4 "The physics analogies are misleading"

**Objection:** Calling this "gauge theory" borrows prestige from physics without the substance.

**Response:** The mathematical structure genuinely is gauge-theoretic: a principal bundle, a connection, and a curvature measuring failure of path-independence. We're not using "gauge" as a buzzword; we're using the actual mathematical framework.

However, we agree that the physics analogies (Gauss's law, Faraday's law) are heuristic, not foundational. They provide intuition, not proof. The formal content stands without them.

---

## 11. Conclusion

We have argued for a shift in how normative systems are approached:

| Traditional Ethics | Philosophy Engineering |
|-------------------|----------------------|
| Claims about moral facts | Systems for producing judgments |
| Arguments for correctness | Tests for invariance |
| Intuitions as evidence | Witnesses as counterexamples |
| Rules that can be outweighed | Topological constraints |
| Discourse without convergence | Engineering with specifications |

The core contribution is **operational falsifiability for normative systems**. We cannot test whether ethics is *true*. We can test whether ethical systems are *gameable*.

This is modest: we provide engineering, not revelation. But it is also significant: for the first time in 2,500 years, we can *run the tests*.

When a system fails, we get a witness. Witnesses enable debugging. Debugging enables improvement.

This is what it looks like when philosophy becomes engineering.

---

## References

Aristotle. (c. 340 BCE). *Nicomachean Ethics*.

Dennett, D. C. (1987). *The Intentional Stance*. MIT Press.

Hume, D. (1739). *A Treatise of Human Nature*.

James, W. (1907). *Pragmatism: A New Name for Some Old Ways of Thinking*.

Kant, I. (1785). *Groundwork of the Metaphysics of Morals*.

Mill, J. S. (1863). *Utilitarianism*.

Noddings, N. (1984). *Caring: A Feminine Approach to Ethics and Moral Education*.

---

## Appendix A: Formal Definitions

### A.1 The BIP Schema

```
BIPSystem := {
  X: InputSpace,
  G: TransformationGroup,
  C: Canonicalizer,
  Ψ: GroundingMap,
  Σ: Evaluator,
  ~_Y: OutputEquivalence
}

Invariance holds iff:
  ∀x ∈ X, ∀g ∈ G: Σ(Ψ(C(g·x))) ~_Y Σ(Ψ(C(x)))
```

### A.2 Witness Definition

```
Witness := {
  input: x ∈ X,
  transform: g ∈ G,
  baseline_output: J(x),
  transformed_output: J(g·x),
  divergence: d(J(x), J(g·x))
}

Valid witness iff:
  g is declared meaning-preserving AND
  divergence > threshold
```

### A.3 Curvature Test

```
LoopTest(x, γ) := {
  γ: sequence of transforms forming closed loop
  
  Apply γ to x, computing:
    x → g₁·x → g₂·(g₁·x) → ... → γ·x
  
  Curvature := d(J(x), J(γ·x))
  
  Return: Curvature (should be 0 for flat connection)
}
```

---

*Document version: 0.1*  
*Status: Draft for review*
