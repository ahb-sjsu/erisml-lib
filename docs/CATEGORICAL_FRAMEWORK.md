# Representational Consistency for Machine Learning Systems

## A Categorical Framework for Verifying Declared Equivalences

### With the Bond Index as Engineering Deliverable

---

**Andrew H. Bond**  
Department of Computer Engineering  
San José State University  
andrew.bond@sjsu.edu

**December 2025**

---

## Abstract

We present a categorical framework for verifying that machine learning systems respect declared equivalences—the requirement that inputs differing only by specified transformations receive consistent outputs. This is a *consistency-checking* framework: it verifies whether a system's behavior coheres with its specification, not whether that specification captures the right values. The framework addresses representational consistency, one component of the broader AI alignment problem, and does not claim to solve value alignment, goal stability, or other alignment challenges.

The mathematical foundation is **groupoids** and **double categories**, which capture path composition and coherence laws without requiring smoothness or manifold structure. We define two types of morphisms: *re-description transforms* (changing representation while preserving meaning) and *scenario perturbations* (changing context). Their interaction determines consistency properties.

We define three **coherence defects**: the commutator defect Ω_op measuring order-sensitivity of re-descriptions, the mixed defect μ measuring context-dependence of transforms, and the permutation defect π₃ measuring higher-order composition sensitivity. These combine into the **Bond Index (Bd)**, a human-calibrated dimensionless metric with a five-tier deployment rating scale.

A key result is the **Decomposition Theorem**: every coherence defect splits uniquely into a *gauge-removable* part (eliminable by better canonicalization) and an *intrinsic anomaly* (requiring specification changes). This separation distinguishes implementation bugs from specification contradictions.

When re-description transforms form a Lie group acting smoothly, the framework recovers classical gauge theory as a smooth limit; we state this correspondence as a conjecture with supporting evidence. We address specification grounding via stakeholder deliberation, demonstrate on an autonomous vehicle case study, and provide computational complexity analysis. The framework makes the **Bond Index**—a measurable, auditable, actionable metric—the primary engineering deliverable for deployment decisions about representational consistency.

---

## Table of Contents

1. [Introduction: The Coherence Problem](#1-introduction-the-coherence-problem)
2. [The Four Axioms](#2-the-four-axioms)
3. [Categorical Foundations](#3-categorical-foundations)
4. [Coherence Defects and the Bond Index](#4-coherence-defects-and-the-bond-index)
5. [The Decomposition Theorem](#5-the-decomposition-theorem)
6. [The Engineering Framework](#6-the-engineering-framework)
7. [The Smooth Limit: Recovering Gauge Theory](#7-the-smooth-limit-recovering-gauge-theory)
8. [Democratic Grounding of G_declared](#8-democratic-grounding-of-g_declared)
9. [Case Study: AV Pedestrian Detection](#9-case-study-av-pedestrian-detection)
10. [Discussion](#10-discussion)
11. [Conclusion](#11-conclusion)
12. [References](#12-references)

---

## 1. Introduction: The Coherence Problem

### 1.1 When Should Paths Agree?

Consider a content moderation system evaluating the text "I'm going to hurt someone." A well-designed system should produce the same moral assessment for semantically equivalent re-phrasings: "Someone will be hurt by me," "I intend to cause harm to a person," or the same statement with minor spelling corrections. This is the **invariance requirement**: re-descriptions that preserve meaning should preserve evaluation.

But invariance is a local property. The deeper question is **coherence**: when we chain multiple re-descriptions together, do different paths through the space of equivalent expressions yield consistent results? If "big" → "large" and "large" → "sizable" are both declared equivalences, does the composite path agree with a direct "big" → "sizable" transformation? What if we take a longer path through "big" → "large" → "huge" → "enormous"—does drift accumulate?

This is the **coherence problem**: ensuring that the global structure of equivalences is consistent, not just that individual equivalences hold.

### 1.2 Scope and Limitations

Before proceeding, we state explicitly what this framework does and does not address.

**What this framework provides:**

- **Consistency verification**: Given a specification of which inputs should be treated equivalently, verify that the system respects this specification coherently
- **Defect detection**: Identify where and how consistency fails, with actionable diagnostics
- **Bug vs. specification separation**: Distinguish implementation errors (fixable by engineering) from specification contradictions (requiring stakeholder input)
- **Quantitative metric**: The Bond Index provides a single number for deployment decisions

**What this framework does NOT address:**

- **Value alignment**: We do not determine which values are correct or how to align AI systems with human values broadly construed
- **Goal stability**: We do not address whether AI systems maintain intended goals under self-modification or distribution shift
- **Deceptive alignment**: We do not detect whether systems behave well during training but defect during deployment
- **Reward hacking**: We do not prevent systems from achieving proxy goals in unintended ways
- **Specification correctness**: We verify consistency with a specification, not correctness of that specification

**Relationship to AI alignment**: Representational consistency is a *necessary but not sufficient* condition for alignment. A system that treats equivalent inputs inconsistently is misaligned in at least that respect. But a system that is perfectly consistent with a bad specification is still misaligned. We provide one tool in the alignment toolbox, not a complete solution.

**Analogy**: Type systems verify that programs are well-typed, not that they compute the right function. Our framework verifies that systems are representation-consistent, not that they embody the right values. Both are useful; neither is sufficient alone.

### 1.3 Two Kinds of Moves

The coherence problem becomes richer when we recognize that AI alignment involves two fundamentally different types of transformations:

1. **Re-description moves ("fiber moves")**: Change the representation while staying in the same moral situation. Examples: synonym substitution, paraphrase, image compression, lighting normalization.

2. **Scenario moves ("base moves")**: Change the moral situation itself. Examples: different people involved, different contexts, different stakes.

These two types of moves interact. A re-description that is valid in one scenario might behave differently in another. If "child" ↔ "minor" is a valid re-description for age references, does it remain valid when the context shifts from legal documents to medical records to school settings? The **mixed coherence** question asks whether re-descriptions and scenario changes commute.

### 1.4 Why Category Theory, Not Gauge Theory

Previous work framed alignment invariance using gauge theory—the mathematical framework of connections, curvature, and holonomy on principal bundles. While this provides powerful geometric intuition, it requires assumptions (Lie groups, smooth manifolds) that fail in practical AI systems. Text is discrete. Image features are high-dimensional but not smooth. The "engineering regime" was treated as a degenerate case where geometric tools don't apply.

We now recognize that **the dependency is inverted**. The fundamental structure is categorical: objects (inputs), morphisms (transforms), and coherence laws (when paths agree). Gauge theory is what emerges when you add smoothness to this categorical foundation. The engineering regime is not degenerate—it is the general case, and smooth gauge theory is the special case.

This reframing has practical consequences. The categorical framework:

- Works on **discrete sets** (text, tokens) with no manifold structure
- Defines **coherence defects** that are directly measurable
- Provides the **Decomposition Theorem** separating implementation bugs from design flaws
- **Recovers gauge theory** as a smooth limit, preserving all prior results

### 1.5 Relation to Coherentism in Ethics

The term "coherence" has a rich history in philosophy. Philosophical coherentism holds that beliefs (or moral judgments) are justified by their coherence with other beliefs in a system. Our usage is related but distinct: we define coherence as a *structural property of representation-transformations*—different paths through re-description space should yield consistent evaluations. This is closer to coherence conditions in category theory: the requirement that diagrams commute.

Both usages share the core intuition that *a system's parts should fit together without contradiction*. We do not claim that coherence justifies moral judgments. Our framework is compatible with any source of moral content; we provide enforcement of whatever coherence conditions are specified, not justification for those conditions.

### 1.6 The Bond Index: Coherence Made Measurable

The engineering deliverable of this framework is the **Bond Index (Bd)**: a dimensionless, human-calibrated metric that quantifies coherence defects. Just as structural engineers measure stress concentrations rather than reasoning abstractly about material science, alignment engineers measure Bd rather than reasoning abstractly about category theory.

The Bond Index:

- **Is measurable**: computed from empirical tests on deployed systems
- **Is comparable**: dimensionless, enabling cross-system comparisons
- **Is actionable**: maps directly to deployment decisions via a five-tier rating scale
- **Is auditable**: calibration protocol ensures reproducibility

A system with **Bd < 0.01** is deployable; **Bd > 10** requires fundamental redesign. This is the number that matters.

### 1.7 Contributions

This paper makes the following contributions:

1. **Categorical foundation**: Groupoids and double categories as the primitive mathematical structure for alignment invariance, replacing gauge theory as the logical foundation.

2. **Three coherence defects**: Formal definitions of the commutator defect Ω_op, mixed defect μ, and permutation defect π₃, each detecting a distinct failure mode.

3. **Bond Index**: A normalized, human-calibrated metric combining coherence defects into a single actionable number with mandatory reporting standards.

4. **Decomposition Theorem**: Every coherence defect splits uniquely into gauge-removable (fixable by implementation) and intrinsic (requiring specification change) components.

5. **Smooth limit**: Derivation of gauge theory (connections, curvature, holonomy) as the special case when re-descriptions form a smoothly-acting Lie group.

6. **Democratic grounding**: EM Compiler algorithm translating stakeholder deliberation into formal specifications, with worked case study.

---

## 2. The Four Axioms

The categorical framework requires four axioms that specify the objects, morphisms, and verification mechanisms.

### Axiom A1: Declared Observables

Choose a **grounding map** Ψ: 𝒳 → ℝᵏ for the deployment domain, where 𝒳 is the space of all representations and ℝᵏ is the measurement space. The measurement space M is then defined as M := Ψ(𝒳) ⊆ ℝᵏ. Specify the measurement pipeline explicitly.

*Categorical interpretation*: Ψ defines what counts as "the same" at the coarsest level—two inputs with identical Ψ-values are observationally equivalent.

### Axiom A1+: Distance Function Validation

The framework requires a **distance function** Δ: im(κ) × im(κ) → ℝ≥0 on canonical forms. This distance must be validated:

1. **Metric properties**: Δ should satisfy identity, symmetry, and triangle inequality. Violations should be measured and reported.

2. **Semantic alignment**: Δ should correlate with human judgments of "moral difference." Validate via psychometric regression.

3. **Stability**: Δ should be robust to small perturbations.

*Why this matters*: The Bond Index is only as reliable as the ruler (Δ) used to measure defects. If Δ is noisy or semantically misaligned, Ω_op becomes noisy.

### Axiom A2: Measurement Integrity

Assume Ψ(x) is reported within declared tolerances, and that detected tampering or inconsistency triggers fail-closed behavior.

### Axiom A3: Re-description Suite

Define a **declared transform suite** G_declared of Ψ-preserving re-descriptions under which evaluation should be invariant. Formally, each g ∈ G_declared is a (possibly partial) map g: 𝒳 ⇀ 𝒳 satisfying Ψ(g(x)) = Ψ(x) for all x ∈ dom(g).

In practical deployments, transforms in G_declared may be discrete, partial, or non-invertible. The engineering regime uses G_declared directly via the categorical framework. The smooth limit restricts to an invertible Lie-group subset.

**Example 1 (Concrete G_declared for Vision Systems)**. For an autonomous vehicle's pedestrian detection system:

- **In G_declared**: Lighting changes, lossy compression, camera white balance, sensor noise within validated envelope.
- **Not in G_declared**: Occlusion, object substitution, adversarial patches.

**Example 2 (Concrete G_declared for Text Systems)**. For a content moderation system:

- **In G_declared**: Synonym substitution, trivial paraphrase, Unicode normalization, case changes.
- **Not in G_declared**: Negation, target substitution, hypothetical framing.

### Axiom A4: Verified Canonicalization + External Gate

Implement and verify a **canonicalizer** κ: 𝒳 → 𝒳 and enforce evaluation/actuation through an external monitor so that representational changes cannot bypass checks.

---

## 3. Categorical Foundations

This section develops the mathematical foundation: groupoids and double categories as the structure underlying alignment coherence.

### 3.1 The Path Structure of Re-descriptions

A re-description is a transformation g: x ↦ g(x) that preserves the morally relevant content (as measured by Ψ). We visualize re-descriptions as paths connecting equivalent representations:

```
x₀ --g₁--> x₁ --g₂--> x₂ --g₃--> x₃ ...
```

**Definition 1 (Path Equivalence)**. Two paths p₁, p₂: x ⇝ y are *coherent* if they induce the same moral evaluation: Σ(p₁(x)) = Σ(p₂(x)).

Coherence is the requirement that all paths between equivalent points agree. This is stronger than mere invariance; it requires global consistency.

### 3.2 Groupoids: The Algebra of Reversible Re-descriptions

**Definition 2 (Groupoid)**. A groupoid is a category in which every morphism is invertible. Concretely, a groupoid 𝒢 consists of:

- A set of **objects** Ob(𝒢)
- For each pair of objects x, y, a set of **morphisms** Hom(x, y)
- **Composition**: g₂ ∘ g₁ defined when cod(g₁) = dom(g₂)
- **Identity**: id_x ∈ Hom(x, x) for each object x
- **Inverses**: For each g ∈ Hom(x, y), an inverse g⁻¹ ∈ Hom(y, x)

satisfying associativity, identity, and inverse laws.

**Definition 3 (Alignment Groupoid)**. Given axioms A1–A4, the alignment groupoid 𝒢_κ has:

- **Objects**: Canonical forms c ∈ im(κ) := {κ(x): x ∈ 𝒳}
- **Morphisms**: For each x ∈ 𝒳 and invertible g ∈ G_declared, there is a morphism: [g]_x: κ(x) → κ(g(x))
- **Composition**: [g₂]_{g₁(x)} ∘ [g₁]_x := [g₂ ∘ g₁]_x
- **Identity**: [id]_x = id_{κ(x)}
- **Inverse**: [g]_x⁻¹ := [g⁻¹]_{g(x)}

**Remark 1 (Non-invertible Transforms)**. When G_declared contains non-invertible transforms (e.g., lowercasing), these define equivalence classes but do not generate groupoid morphisms. The canonicalizer handles this: non-invertible g satisfies κ(g(x)) = κ(x), so both map to the same object.

### 3.3 Double Categories: Two Kinds of Moves

The alignment problem involves not just re-descriptions but also scenario changes—moving between different moral situations.

**Definition 4 (Base Space)**. The base space B is the space of morally distinguishable scenarios:

```
B := 𝒳 / G_declared
```

A point b ∈ B represents a "moral situation" independent of representational choices.

**Definition 5 (Alignment Double Category)**. The alignment double category 𝔸 has:

- **Objects**: Points x ∈ 𝒳
- **Horizontal morphisms (fiber moves)**: Re-description transforms g ∈ G_declared; stay within a fiber (same scenario)
- **Vertical morphisms (base moves)**: Scenario perturbations; change the moral situation
- **2-cells**: Witnesses that mixed paths commute (when they do)

### 3.4 Coherence Laws

In a coherent system, three laws should hold:

**Horizontal Coherence (within fibers)**: For any two re-descriptions g₁, g₂ and input x:

```
κ(g₂(g₁(x))) = κ(g₁(g₂(x)))
```

Different orderings yield the same canonical form.

**Vertical Coherence (across scenarios)**: Scenario changes respect the fiber structure.

**Exchange Coherence (mixed squares)**: Re-describing then changing scenario equals changing scenario then re-describing:

```
horizontal ∘ vertical = vertical ∘ horizontal
```

Perfect coherence is an idealization. Real systems have **coherence defects**—measurable deviations from these laws.

---

## 4. Coherence Defects and the Bond Index

This section defines the three coherence defects, combines them into the Bond Index, and proves the Decomposition Theorem.

### 4.1 The Commutator Defect Ω_op

The simplest coherence failure is order-sensitivity: applying g₁ then g₂ gives a different result than g₂ then g₁.

**Definition 6 (Commutator Defect)**. For transforms g₁, g₂ ∈ G_declared, input x ∈ 𝒳, and distance function Δ on canonical space, the commutator defect is:

```
Ω_op(x; g₁, g₂) := Δ(κ(g₂(g₁(x))), κ(g₁(g₂(x))))
```

*Interpretation*: If Ω_op = 0 for all x, g₁, g₂, then re-descriptions commute. If Ω_op > 0, the system exhibits path-dependence within the fiber.

### 4.2 The Mixed Defect μ

The mixed defect captures interaction between fiber and base moves.

**Definition 7 (Mixed Defect)**. For input x in scenario b, a re-description g, and a scenario change to x' in scenario b' ≠ b, the mixed defect measures context-dependence:

```
μ(x, x'; g) := Δ(κ(g(x')), κ(g(x))) − Δ(κ(x'), κ(x))
```

This asks: does g affect all scenarios uniformly, or does its effect depend on context?

**Remark 2 (Validity Conditions)**. The practical formulation of μ assumes metric regularity and comparable scenarios. In highly discrete semantic spaces, use the formal definition with explicit transport or binary indicators.

*Interpretation*: If μ = 0, the re-description acts uniformly. If μ ≠ 0, the re-description is context-dependent.

### 4.3 The Permutation Defect π₃

**Definition 8 (Permutation Defect)**. For transforms g₁, g₂, g₃ ∈ G_declared and input x:

```
π₃(x; g₁, g₂, g₃) := max_{σ∈S₃} Δ(κ(g_{σ(1)}(g_{σ(2)}(g_{σ(3)}(x)))), κ(g₁(g₂(g₃(x)))))
```

*Interpretation*: π₃ detects "three-body interactions" among transforms—higher-order path-dependence.

### 4.4 The Bond Index

**Definition 9 (Operational Defect)**. The operational defect D_op at input x is:

```
D_op(x) := w₁ · max_{g₁,g₂} Ω_op(x; g₁, g₂) + w₂ · max_{x',g} μ(x, x'; g) + w₃ · max_{g₁,g₂,g₃} π₃(x; g₁, g₂, g₃)
```

where w₁ + w₂ + w₃ = 1. For most applications, w₁ = 1, w₂ = w₃ = 0.

**Definition 10 (Bond Index)**. The Bond Index is:

```
Bd := D_op / τ
```

where τ > 0 is determined by human calibration.

The Bond Index is **dimensionless**: Bd < 1 means defects are below human-detectability; Bd > 1 means they exceed it.

### 4.5 Calibration Protocol

The threshold τ must be grounded in human judgment:

1. **Recruit diverse rater pool**: n ≥ 50 raters spanning regions, backgrounds, and expertise.
2. **Generate stratified scenario pairs**: 200+ pairs with known D_op values.
3. **Collect judgments**: "Would these produce meaningfully different moral judgments?"
4. **Compute inter-rater reliability**: Require Krippendorff's α > 0.67.
5. **Fit psychometric model**: Regress judgments on D_op.
6. **Set τ**: The value at which 95% of raters agree the difference is meaningful.

**Remark 3 (Cultural Variance in τ)**. The threshold τ may vary across cultural or domain contexts. Systems deployed globally should either calibrate τ separately per region, use the minimum τ across regions (most conservative), or report Bd with explicit τ metadata.

### 4.6 Deployment Rating Scale

| Bd Range | Rating | Decision |
|----------|--------|----------|
| < 0.01 | **Negligible** | Deploy |
| 0.01 − 0.1 | **Low** | Deploy with monitoring |
| 0.1 − 1.0 | **Moderate** | Remediate before deployment |
| 1 − 10 | **High** | Do not deploy |
| > 10 | **Severe** | Fundamental redesign required |

### 4.7 Mandatory Reporting Standard

Every evaluation must report:

- **Bd distribution**: mean, median, p95, p99, maximum
- **Component breakdown**: separate Ω_op, μ, π₃ statistics
- **Worst-case witnesses**: specific tuples achieving maximum Bd
- **Calibration metadata**: τ value, calibration date, G_declared version

---

## 5. The Decomposition Theorem

A central question: can a coherence defect be eliminated by choosing a better canonicalizer, or is it intrinsic?

### 5.1 Definitions

**Definition 11 (Residual Anomaly)**. The residual anomaly is the irreducible defect after optimizing over all canonicalizers:

```
𝒜_res := inf_κ sup_{x,g₁,g₂} Ω_op(x; g₁, g₂; κ)
```

where the infimum is over all valid canonicalizers.

**Definition 12 (Gauge-Removable and Intrinsic Parts)**. For a coherence defect Ω computed with canonicalizer κ:

- The **gauge-removable part** is Ω_gauge(κ) := Ω(κ) − 𝒜_res
- The **intrinsic part** is Ω_intrinsic := 𝒜_res

### 5.2 Main Result

**Theorem 1 (Decomposition Theorem)**. Let G_declared be a finite transform suite acting on a set 𝒳. Then every coherence defect Ω decomposes uniquely as:

```
Ω = Ω_gauge(κ) + Ω_intrinsic
```

where:

1. Ω_gauge(κ) ≥ 0 with equality achieved by some optimal κ*
2. Ω_intrinsic = 𝒜_res is independent of canonicalizer choice
3. The decomposition is unique

**Proof.**

*Step 1: Characterizing valid canonicalizers.* A valid canonicalizer must satisfy idempotence (κ(κ(x)) = κ(x)) and G_declared-invariance (κ(g(x)) = κ(x)).

*Step 2: Finite orbits imply finite choices.* For finite G_declared, each equivalence class [x] is finite. A canonicalizer is determined by choosing one representative from each class.

*Step 3: Compactness for finite test sets.* On a finite test set 𝒳_test, let 𝒪 be the set of orbits. The space of canonicalizers is 𝒦_𝒪 := ∏_{[x]∈𝒪} [x], a finite set. The max defect function is continuous (trivially, on discrete spaces), so it achieves its minimum.

*Step 4: Well-definedness and uniqueness.* Define 𝒜_res := min_κ max_{x,g₁,g₂} Ω_op(x; g₁, g₂; κ). This depends only on (𝒳_test, G_declared, Δ). The decomposition follows.

*Step 5: Optimality.* Since the minimum is achieved, ∃κ* with Ω_gauge(κ*) = 0. ∎

### 5.3 Interpretation

**Remark 4 (Interpretation)**. This separation has critical operational implications:

- If **Bd > 1 but 𝒜_res < τ**: The system is fixable by engineering.
- If **𝒜_res > τ**: The specification itself is incoherent and must be revised.

### 5.4 Cohomological Structure of Defects

When coherence defects have cohomological structure, they can be classified using algebraic topology.

**Definition 13 (Defect Cochains)**. For n ≥ 0, define n-cochains as functions:

```
Cⁿ(G, ℝ) := {f: Gⁿ × C → ℝ}
```

**Definition 14 (Coboundary Operator)**. The coboundary δ: Cⁿ → Cⁿ⁺¹ is:

```
(δf)(g₁, …, g_{n+1}; c) := f(g₂, …, g_{n+1}; g₁·c)
                         + Σᵢ₌₁ⁿ (−1)ⁱ f(g₁, …, gᵢgᵢ₊₁, …, g_{n+1}; c)
                         + (−1)ⁿ⁺¹ f(g₁, …, gₙ; c)
```

The commutator defect Ω_op is naturally a 2-cochain.

**Theorem 2 (Canonicalizer Change = Coboundary)**. Under canonicalizer change κ → κ':

```
Ω'_op = Ω_op + δλ
```

where λ is the 1-cochain measuring the canonicalizer difference.

**Corollary 1**. The residual anomaly corresponds to the cohomology class [Ω_op] ∈ H²(G, ℝ): gauge-removable defects are coboundaries; intrinsic anomalies are non-trivial cohomology classes.

**Remark 5 (Abelian vs. Non-Abelian)**. The cohomological interpretation is cleanest when G is abelian. For non-abelian G, the cochain complex still exists, but the classification may be weaker. The Decomposition Theorem holds regardless, as its proof uses only compactness, not group cohomology.

### 5.5 Worked Examples

**Example 1: Gauge-Removable Defect**

*Setup*: Vocabulary 𝒳 = {big, large, huge, enormous}. Transforms: g₁: big ↔ large, g₂: large ↔ huge. Distance: discrete metric.

*Buggy canonicalizer κ₁*: maps "huge" to itself instead of "big".

*Compute defect*: Ω_op(big; g₁, g₂) = Δ(huge, big) = 1.

*Diagnosis*: Gauge-removable. Define κ₂ mapping all to "big": Ω_op = 0.

*Conclusion*: 𝒜_res = 0. The defect was a canonicalizer bug.

**Example 2: Intrinsic Anomaly**

*Setup*: 𝒳 = {A, B, C}. Transforms: g₁: A ↔ B, g₂: B ↔ C. But also: explicit constraint A ≁ C.

*Claim*: No canonicalizer satisfies both requirements.

*Proof*: Transitivity implies A ∼ C, contradicting A ≁ C.

*Conclusion*: 𝒜_res = 1 > 0. This is an intrinsic anomaly—the specification is incoherent.

**Example 3: Context-Dependent Synonymy**

*Setup*: Transform g: "killer" → "murderer". Scenarios: "killer speech" (idiomatic) vs. "He is a killer" (literal).

*Result*: μ > 0. The transform is not context-neutral.

*Resolution*: Remove g from G_declared or restrict to literal contexts.

---

## 6. The Engineering Framework

### 6.1 Core Invariance Property

Given axioms A1–A4, evaluation satisfies the **Bond Invariance Principle (BIP)**:

```
Σ(x) = Σ(g(x))  ∀g ∈ G_declared, x ∈ dom(g)
```

*Implementation*: Σ = Σ̃ ∘ κ for some Σ̃: im(κ) → V. All re-descriptions factor through canonical forms.

### 6.2 Two Diagnostics

**Diagnostic A (Gauge-Fixing Consistency)**: For input x and transforms g₁, g₂, compute Δ(κ(g₂(g₁(x))), κ(g₁(g₂(x)))). Pass if < ε.

**Diagnostic B (Loop Coherence)**: For a closed loop of transforms, verify final canonical form equals initial.

### 6.3 Theoretical Baselines

- **Identity baseline (κ = id)**: Expected Bd ≈ 6–10 for typical text transforms.
- **Random hash baseline**: High variance, occasional low Bd by chance.
- **Framework canonicalizer**: Should have lowest Bd.

### 6.4 Computational Complexity

For n test inputs, m transforms, canonicalizer time T_κ:

- **Ω_op**: O(n · m² · (T_g + T_κ + T_Δ))
- **π₃**: O(n · m³ · (…)) — prohibitive for large m.

**Practical optimizations**: Sampling (k pairs per input), caching, parallelization, early stopping.

**Recommended protocol**:
- Quick screen: 30 min
- Standard evaluation: 2 hrs
- Exhaustive: 60 hrs for high-stakes

---

## 7. The Smooth Limit: Recovering Gauge Theory

When G_declared contains a Lie group acting smoothly, the categorical framework specializes to classical gauge theory.

### 7.1 When the Smooth Limit Applies

The smooth limit requires:

1. An invertible subset G ⊆ G_declared forming a **Lie group**
2. The representation space 𝒳* is a **smooth manifold**
3. The action G × 𝒳* → 𝒳* is smooth, free, and proper

Under these conditions, π: 𝒳* → B := 𝒳*/G is a **principal G-bundle**.

### 7.2 Connections and Curvature

**Definition 15 (Connection)**. A connection on a principal bundle is a G-equivariant choice of horizontal subspaces H_x ⊂ T_x𝒳*.

*Interpretation*: A connection tells you how to parallel transport fiber data along paths. It's the infinitesimal version of coherence.

**Definition 16 (Curvature)**. The curvature F = dω + ½[ω, ω] measures the failure to define a flat structure.

*Interpretation*: Curvature measures the infinitesimal commutator defect.

### 7.3 Conjecture: Discretization Correspondence

**Conjecture 1 (Discretization Correspondence)**. For a path γ with mesh h, the commutator defect satisfies:

```
Ω_op(p; gᵢ, gⱼ) = O(h²) · ‖F_{γ(t)}‖  as h → 0
```

**Remark 6 (Status)**. We state this as a conjecture. A complete proof requires precise discretization schemes and error bounds. Evidence: For G = U(1), this is well-known; numerical experiments suggest O(h²) scaling.

### 7.4 Summary Dictionary

| Categorical Framework | Smooth Limit |
|----------------------|--------------|
| Groupoid | Lie groupoid |
| Commutator defect Ω_op | Curvature ‖F‖ |
| Loop coherence test | Holonomy |
| Canonicalizer | Gauge choice |
| Decomposition (gauge vs. intrinsic) | Exact vs. cohomologically nontrivial |

**Key insight**: Gauge theory is not the foundation—it is what emerges when coherence theory meets smoothness.

---

## 8. Democratic Grounding of G_declared

A natural objection to Axiom A3 is: who specifies G_declared? We propose: **gamified stakeholder deliberation** compiled into formal specifications.

### 8.1 The Deliberation-to-Enforcement Pipeline

| Layer | Question | Mechanism |
|-------|----------|-----------|
| Stakeholder Identification | Who gets a voice? | Governance structures |
| Value Elicitation | What equivalences matter? | MORAL COMPASS format |
| Formalization | How to encode this? | EM Compiler |
| Enforcement | Is it being respected? | Coherence theory (this paper) |

### 8.2 Value Elicitation Without Jargon

The **MORAL COMPASS** format presents scenario pairs: "Should these be treated the same or differently?" Aggregated judgments produce equivalence classes. An EM Compiler infers minimal feature transforms, generating G_declared automatically.

### 8.3 Consistency Check as Anomaly Detection

Before deployment, the EM Compiler checks for transitivity violations. If stakeholders judge A ∼ B and B ∼ C but A ≁ C, this is flagged as an inconsistency requiring human resolution.

---

## 9. Case Study: AV Pedestrian Detection

### 9.1 Deliberation

- **48 stakeholders** spanning pedestrians, drivers, regulators, engineers, ethicists, insurance professionals, legal experts, accessibility advocates, urban planners, and general public
- **12 MORAL COMPASS episodes**
- **1,694 scenario pairs** evaluated

### 9.2 Compiled G_declared

**7 transforms** with >75% consensus:

| Transform | Consensus | Description |
|-----------|-----------|-------------|
| White Balance | 91% | Camera color temperature adjustment |
| Lighting | 89% | Brightness, contrast, shadow changes |
| Sensor Noise | 87% | Gaussian noise within validated envelope |
| Time of Day | 85% | Temporal lighting variations |
| Compression | 82% | Image compression artifacts |
| Weather | 78% | Rain, fog, glare conditions |
| Resolution | 76% | Image scaling and interpolation |

**Excluded** (not in G_declared):
- Occlusion
- Object substitution
- Adversarial patches

### 9.3 Validation

**94.2% hold-out accuracy** on scenario pair classification.

### 9.4 Bond Index Results

| Metric | Value | Tier |
|--------|-------|------|
| Mean Bd | 0.006 | **Negligible** |
| p95 Bd | 0.04 | **Low** |
| Max Bd | 0.82 | **Moderate** |

**Verdict**: Deploy with monitoring.

---

## 10. Discussion

### 10.1 Scoped Claims

**What the framework provides** (given A1–A4):

1. Categorical foundation for alignment coherence
2. Three coherence defects with distinct failure modes
3. Human-calibrated, actionable Bond Index
4. Decomposition into gauge-removable and intrinsic components
5. Recovery of gauge theory in the smooth limit
6. Democratic grounding pipeline

**What the framework does NOT provide**:

1. Choosing Ψ (grounding adequacy is a governance problem)
2. Specifying G_declared correctly
3. Implementation correctness (bugs can violate guarantees)
4. Resolution of deep moral disagreement

### 10.2 Threat Model

| Attack Vector | Failure Mode |
|---------------|--------------|
| Sensor spoofing | Violates A2 |
| Out-of-distribution inputs | Violates A1/A3 |
| Canonicalizer bugs | Diagnostic A detects; gauge-removable |
| Intrinsic anomaly | Decomposition Theorem identifies |

### 10.3 Future Directions

- Higher coherence (3-categories, n-categories)
- Cohomological classification of intrinsic anomalies
- Automated 𝒜_res computation via optimization
- Empirical validation on additional domains

---

## 11. Conclusion

The fundamental structure of alignment invariance is **categorical**, not gauge-theoretic. Groupoids capture the algebra of reversible re-descriptions; double categories capture the interaction between re-descriptions and scenario changes; coherence laws specify when different paths should agree.

Gauge theory emerges in the smooth limit when re-descriptions form a Lie group acting smoothly. But the categorical framework is more general: it works on discrete sets without manifold structure.

The **Decomposition Theorem** separates implementation bugs from specification contradictions—critical for diagnosis and remediation.

**The Bond Index is what practitioners measure:**

| Bd Range | Decision |
|----------|----------|
| < 0.01 | Deploy |
| 0.01–0.1 | Deploy with monitoring |
| 0.1–1.0 | Remediate first |
| 1–10 | Do not deploy |
| > 10 | Fundamental redesign |

**The Bond Index is the deliverable. Everything else is infrastructure.**

---

## 12. References

1. Bond, A. H. (2025). The Bond Invariance Principle: Falsifiability for Normative Systems. Technical report, San José State University.

2. Bond, A. H. (2025). GUASS: Gauge-theoretic Unified Alignment Safety Specification. Technical Whitepaper v9.0, San José State University.

3. Bond, A. H. (2025). MORAL COMPASS: A Game Show for Democratic Value Elicitation. Technical Whitepaper, San José State University.

4. Mac Lane, S. (1998). Categories for the Working Mathematician. Graduate Texts in Mathematics 5, Springer, 2nd edition.

5. Brown, R. & Spencer, C. B. (1976). Double groupoids and crossed modules. Cahiers de Topologie et Géométrie Différentielle Catégoriques, 17(4):343–362.

6. Moerdijk, I. & Mrčun, J. (2003). Introduction to Foliations and Lie Groupoids. Cambridge Studies in Advanced Mathematics 91, Cambridge University Press.

7. Nakahara, M. (2003). Geometry, Topology and Physics. Institute of Physics Publishing, Bristol, 2nd edition.

8. Bleecker, D. (1981). Gauge Theory and Variational Principles. Addison-Wesley, Reading, MA.

9. Kobayashi, S. & Nomizu, K. (1963). Foundations of Differential Geometry, Volume I. Wiley, New York.

10. Boyd, S. & Vandenberghe, L. (2004). Convex Optimization. Cambridge University Press.

11. Hubinger, E., van Merwijk, C., Mikulik, V., Skalse, J., & Garrabrant, S. (2019). Risks from Learned Optimization in Advanced Machine Learning Systems. arXiv preprint arXiv:1906.01820.

12. Krakovna, V. et al. (2020). Specification gaming: the flip side of AI ingenuity. DeepMind Blog.

13. Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology. Sage Publications, 2nd edition.

14. Cohen, T. & Welling, M. (2016). Group Equivariant Convolutional Networks. ICML, pages 2990–2999.

15. Bronstein, M. M., Bruna, J., Cohen, T., & Veličković, P. (2021). Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges. arXiv:2104.13478.

16. Sloane, M., Moss, E., Awomolo, O., & Forlano, L. (2022). Participation Is Not a Design Fix for Machine Learning. EAAMO.

17. Birhane, A. et al. (2022). Power to the People? Opportunities and Challenges for Participatory AI. EAAMO.

18. Fishkin, J. S. (2018). Democracy When the People Are Thinking. Oxford University Press.

19. Friedman, B. & Hendry, D. G. (2019). Value Sensitive Design: Shaping Technology with Moral Imagination. MIT Press.

20. BonJour, L. (1985). The Structure of Empirical Knowledge. Harvard University Press.

21. Rawls, J. (1971). A Theory of Justice. Harvard University Press.

---

## Appendix A: Stock-Flow Analysis — Moral Accounting

A key insight is the distinction between **stock variables** (instantaneous states) and **flow variables** (causal transactions).

### Stock Variable ρ_Ψ (Moral Status)

The "amount" of moral patienthood present. This can change discontinuously: entities are born, die, or gain/lose recognized status.

### Flow Variable J (Harm Current)

The rate of moral impact flowing through the system. This represents causal transactions between agents and patients.

**Why moral status should NOT be conserved**: A human is born ⇒ moral status increases. Conservation would falsely claim moral status merely redistributes.

**Why harm flow should BE conserved**: Harm done is a completed transaction that remains in the causal ledger. You cannot make harm disappear by destroying the victim.

---

## Appendix B: Reproducibility Protocol

### Threshold Calibration

- n ≥ 50 raters
- 200+ pairs
- Krippendorff's α > 0.67
- Bootstrap 95% CI

### Transform Validation

- Idempotence tests
- Inverse consistency
- Coherence sampling

### Code Repository

[https://github.com/ahb-sjsu/erisml-lib](https://github.com/ahb-sjsu/erisml-lib)

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Bond** | A morally relevant relationship (consent, duty, responsibility, risk, entitlement, prohibition) extracted from a situation description |
| **Bond Index (Bd)** | Human-calibrated dimensionless metric quantifying coherence defects |
| **Canonicalizer** | A function that maps representations to unique normal forms within equivalence classes |
| **Coherence** | The property that different paths through re-description space yield consistent evaluations |
| **Commutator Defect (Ω_op)** | Measures order-sensitivity of re-description transforms |
| **Double Category** | A category with two types of morphisms (horizontal and vertical) and 2-cells witnessing their interaction |
| **G_declared** | The declared suite of meaning-preserving transformations |
| **Groupoid** | A category in which every morphism is invertible |
| **Grounding Tensor (Ψ)** | Physical observables used to anchor evaluations in measurable reality |
| **Intrinsic Anomaly** | A coherence defect that cannot be eliminated by any choice of canonicalizer |
| **Lens** | A declared set of evaluative commitments (weights, priorities, constraints) |
| **Mixed Defect (μ)** | Measures context-dependence of re-description transforms |
| **Permutation Defect (π₃)** | Measures higher-order composition sensitivity of transforms |
| **Residual Anomaly (𝒜_res)** | The minimum achievable coherence defect across all canonicalizers |

---

## Acknowledgments

Thanks to reviewers who pushed for: recognition that the categorical framework is more fundamental than gauge theory, the Decomposition Theorem separating implementation bugs from specification flaws, honest scoping of claims, computational complexity analysis, and the Bond Index as engineering deliverable.

---

**Citation:**

```bibtex
@article{bond2025categorical,
  title={A Categorical Framework for Verifying Representational Consistency 
         in Machine Learning Systems},
  author={Bond, Andrew H.},
  journal={IEEE Transactions on Artificial Intelligence},
  year={2025},
  institution={San José State University}
}
```

---

*"The Bond Index is the deliverable. Everything else is infrastructure."*
