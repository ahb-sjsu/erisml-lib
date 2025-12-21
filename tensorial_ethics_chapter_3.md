# Chapter 3: Historical Precursors

## Introduction: Tensors Before Tensors

The mathematical apparatus of tensor calculus was developed in the nineteenth and early twentieth centuries, reaching its canonical form in Einstein's general relativity. Moral philosophy, obviously, predates this development by millennia. Yet the *structural insights* that tensors formalize—transformation behavior, multi-dimensional interdependence, coordinate invariance, the distinction between intrinsic and perspectival properties—have appeared throughout the history of ethics in various guises.

This chapter traces a genealogy of proto-tensorial thinking in moral philosophy. The claim is not that Aristotle or Kant secretly knew tensor calculus, but that they grappled with phenomena that resist scalar treatment and developed conceptual tools that, in retrospect, capture aspects of tensorial structure. Reading these thinkers through a tensorial lens both illuminates their insights and shows that the framework developed in this book has deep roots in the philosophical tradition.

We proceed roughly chronologically, though the ordering also reflects increasing mathematical sophistication in the proto-tensorial concepts.

---

## Aristotle: The Doctrine of the Mean as Context-Sensitive Calibration

Aristotle's *Nicomachean Ethics* presents virtue as a *mean* (μεσότης) between extremes of excess and deficiency. Courage lies between recklessness and cowardice; generosity between prodigality and miserliness; proper pride between vanity and undue humility. The virtuous person hits the mean "at the right times, with reference to the right objects, towards the right people, with the right motive, and in the right way" (1106b21).

This is emphatically not a scalar doctrine. Aristotle explicitly rejects the idea that virtue is a single quantity to be maximized:

> "It is no easy task to find the middle... anyone can get angry—that is easy—or give or spend money; but to do this to the right person, to the right extent, at the right time, with the right motive, and in the right way, that is not for everyone, nor is it easy." (1109a26)

The mean is not a fixed point on a line but a *context-dependent calibration* across multiple dimensions. What counts as courage depends on the situation (battlefield vs. sickroom), the agent's role (soldier vs. physician), the stakes involved, and the alternatives available. The mean for one person in one situation may be quite different from the mean for another person in a different situation.

### Tensorial Reading

In tensorial terms, Aristotle's mean can be understood as a *section* of a fiber bundle over the space of situations. At each point x in situation-space, there is a fiber of possible responses, and the virtuous response is determined by the local structure of the situation—not by a global, context-free rule.

More precisely, let S be the space of ethically relevant situations and let R be the space of possible responses. A *character trait* is a map σ: S → R assigning a response to each situation. The virtuous character trait σ* is the one that, at each point, selects the response appropriate to that situation's specific configuration.

The "right time, right object, right person, right motive, right way" are *coordinates* on S. Virtue requires sensitivity to all of them. A scalar theory would say: "maximize courage" or "minimize cowardice." Aristotle says: the courageous response is a *function of the local coordinates*, not a global maximum.

This is proto-tensorial because it recognizes that ethical evaluation is:
1. **Multi-dimensional** (multiple "right X" conditions)
2. **Context-dependent** (the mean varies with situation)
3. **Not reducible to optimization of a single quantity**

What Aristotle lacks is the mathematical apparatus to describe how the mean *transforms* as we change coordinates—how the courageous response in one framing relates to the courageous response in another framing of the same situation. Tensor calculus provides exactly this.

### The Doctrine of the Mean as a Metric Condition

There is another, deeper tensorial reading. The mean is defined relative to *us*—not the arithmetic mean of the extremes, but the mean "relative to us" (πρὸς ἡμᾶς). This suggests that the moral space has a *metric structure* that varies with the agent.

If we represent character traits as vectors in a space of dispositions, then "excess" and "deficiency" are directions away from the virtuous center. But what counts as excess depends on the metric: a step that is "too far" for one agent may be "not far enough" for another, because their metrics differ.

Formally, let g_{μν}(a) be the metric tensor on disposition-space, parameterized by agent a. The mean for agent a is the point equidistant (under g(a)) from the extremes. Different agents, with different metrics, will locate the mean at different points.

This reading explains Aristotle's insistence that virtue cannot be taught by rule. Rules are coordinate-dependent; the mean is metric-dependent. Without knowing the agent's metric—their capacities, circumstances, history—one cannot specify the mean in advance.

---

## Kant: The Categorical Imperative as an Invariance Condition

Kant's moral philosophy appears, at first glance, maximally anti-tensorial. The categorical imperative demands *universal* laws, applicable to all rational beings regardless of circumstance. "Act only according to that maxim whereby you can at the same time will that it should become a universal law" (Groundwork, 4:421). What could be more scalar than a single test applied uniformly to all actions?

But look again. The categorical imperative is not a command to maximize a quantity. It is a *constraint* on the form of permissible maxims: only those maxims that can be universalized without contradiction are morally permissible.

### Tensorial Reading

In tensorial terms, the categorical imperative is an *invariance condition*. It asks: which maxims remain valid under a specific transformation—the transformation from "I, in my particular circumstances" to "any rational being in relevantly similar circumstances"?

Let T be the transformation that generalizes a maxim from first-personal to universal form. A maxim m is permissible if and only if:

$$T(m) = m$$

That is, the maxim is a *fixed point* of the universalization transformation. Maxims that change under T—that work for me but fail when universalized—are impermissible.

This is structurally identical to how physicists identify *scalars* (quantities invariant under coordinate transformations) and *tensors* (quantities that transform in specific lawful ways). Kant is asking: which moral claims are *invariant* under the transformation from particular to universal perspective?

The parallel is not superficial. In physics, the laws of nature must be the same in all reference frames—this is the principle of general covariance. In Kantian ethics, the laws of morality must be the same for all rational agents—this is the categorical imperative. Both are invariance conditions that constrain the form of legitimate laws.

### The Kingdom of Ends as a Transformation Group

Kant's "kingdom of ends" deepens the tensorial reading. In the kingdom of ends, every rational being is both legislator (author of universal laws) and subject (bound by those laws). The moral community is defined by the *symmetry* between these roles.

In mathematical terms, the kingdom of ends is closed under the transformation that swaps legislator and subject. If a law L is valid, then the transformed law T(L)—where agent and patient are exchanged—must also be valid. This is a *symmetry condition* on the structure of moral laws.

Symmetry conditions of this form are the hallmark of tensor equations. Maxwell's equations are invariant under Lorentz transformations; Einstein's field equations are invariant under general coordinate transformations. Kant's moral laws are invariant under the permutation of rational agents.

What Kant identifies, without the mathematical language, is that *moral objectivity is transformation invariance*. A moral claim is objective not because it corresponds to some moral fact "out there," but because it remains valid under all admissible transformations of perspective.

---

## Ross: Prima Facie Duties and the Problem of Tensor Combination

W.D. Ross's *The Right and the Good* (1930) introduced the concept of *prima facie duties*: duties that are binding unless overridden by stronger duties. We have prima facie duties of fidelity (keeping promises), reparation (making amends), gratitude, justice, beneficence, self-improvement, and non-maleficence.

These duties can conflict. A promise to meet a friend may conflict with an opportunity to prevent harm to a stranger. When they conflict, we must judge which duty is stronger *in this particular situation*—a judgment Ross calls the determination of our *actual duty*.

### Tensorial Reading

Ross's prima facie duties are *components* of a moral vector. Each duty type corresponds to a dimension:

$$\mathbf{D} = (D_{fidelity}, D_{reparation}, D_{gratitude}, D_{justice}, D_{beneficence}, D_{improvement}, D_{nonmaleficence})$$

In any given situation, each component has some magnitude (possibly zero). The *actual duty* is some function of these components—but, crucially, not a simple sum.

Ross explicitly rejects the utilitarian move of reducing all duties to a single scalar (utility). He also rejects the idea that there is a fixed *priority ordering* among duty types. Instead, the determination of actual duty is a matter of *judgment* that weighs the components contextually.

In tensorial terms, Ross is grappling with the problem of *contraction*: how do we go from a multi-component vector to a single action-guiding prescription? His answer—that there is no mechanical rule, only trained judgment—reflects the fact that different situations call for different contraction operations.

### The Interaction Problem

Ross's framework faces a difficulty: how do prima facie duties *interact*? If I have a strong duty of fidelity and a weak duty of beneficence, does the fidelity duty simply win? Or do they combine in some more complex way?

The tensorial framework suggests an answer. Duties are not merely magnitudes to be compared; they have *directions* in moral space. Two duties may be:

- **Aligned**: both point in the same direction (keeping a promise that also helps someone)
- **Orthogonal**: independent, neither reinforcing nor conflicting (a promise to one person, a beneficence opportunity involving another)
- **Opposed**: pointing in opposite directions (a promise that requires harming someone)

The combination of duties is then a *vector sum*, with the geometry determining how they add:

$$\mathbf{D}_{actual} = \sum_i \mathbf{D}_i$$

When duties are aligned, their magnitudes add. When orthogonal, they combine by the Pythagorean theorem. When opposed, they partially cancel.

This explains why strong orthogonal duties can coexist without conflict (I can keep my promise *and* help the stranger, if I have time for both), while even weak opposed duties create tension (breaking even a minor promise to prevent trivial harm still feels like a genuine moral loss).

Ross's "judgment" can now be understood as sensitivity to the *geometry* of the duty configuration in a particular case—something that resists codification in scalar terms but has definite structure.

---

## Rawls: The Original Position as a Transformation-Invariant Framework

John Rawls's *A Theory of Justice* (1971) proposes that principles of justice are those that would be chosen by rational agents behind a "veil of ignorance"—not knowing their place in society, their natural talents, or their conception of the good. The original position is a thought experiment designed to identify principles that are fair because they are chosen without knowledge of how they will affect the chooser.

### Tensorial Reading

The original position is a *symmetry condition*. By removing knowledge of particular position, it forces the choice of principles that are *invariant* under permutation of agents. If a principle benefits position A at the expense of position B, it cannot be chosen behind the veil, because the chooser might turn out to occupy position B.

Formally, let π be a permutation of social positions. A principle P is admissible in the original position if and only if:

$$\pi(P) = P \text{ for all permutations } \pi$$

This is precisely the condition for a *symmetric tensor*—a tensor that is unchanged under index permutation.

Rawls's two principles of justice can be understood as the *unique symmetric solution* (up to specification) to the problem of social cooperation. The first principle (equal basic liberties) is symmetric by construction: everyone gets the same liberties. The second principle (difference principle) permits inequalities only if they benefit the worst-off position—which is a *symmetric* condition because the worst-off position is defined relative to the structure of positions, not to any particular occupant.

### The Metric of the Original Position

The original position also implicitly specifies a *metric* on social positions. The difference principle uses a *maximin* criterion: maximize the minimum position. This is equivalent to a metric in which distance is measured by the worst-off coordinate.

In tensorial terms, the Rawlsian metric is:

$$d(x, y) = \max_i |x_i - y_i|$$

This is the *supremum metric* (or L^∞ metric), which gives special weight to the worst-off dimension. Alternative metrics would yield different principles:

- The *utilitarian metric* (L^1): d(x,y) = Σ|x_i - y_i|, giving equal weight to all positions
- The *Euclidean metric* (L^2): d(x,y) = √(Σ(x_i - y_i)²), weighting by squared deviations

Rawls's argument against utilitarianism can be read as an argument about *which metric* is appropriate for justice. The utilitarian metric permits sacrificing some positions for aggregate gain; the Rawlsian metric does not. This is a substantive geometric claim about the structure of fair social evaluation.

---

## Sen and Nussbaum: Capabilities as a Basis for Moral Space

Amartya Sen and Martha Nussbaum developed the *capabilities approach* as an alternative to both utilitarian welfare measures and Rawlsian primary goods. The core idea is that what matters morally is not subjective well-being (utility) or objective resources (income, rights) but *capabilities*: the real freedoms people have to achieve "functionings" they have reason to value.

Sen identifies a plurality of capabilities: life, bodily health, bodily integrity, senses/imagination/thought, emotions, practical reason, affiliation, relation to other species, play, and control over one's environment (political and material). These are *irreducibly plural*—they cannot be reduced to a single scalar measure.

### Tensorial Reading

The capabilities are *basis vectors* for moral space. Each capability defines an independent dimension along which a person's life can go well or badly. A person's overall situation is a *vector* in capability space:

$$\mathbf{c} = (c_{life}, c_{health}, c_{integrity}, c_{senses}, c_{emotions}, c_{reason}, c_{affiliation}, c_{nature}, c_{play}, c_{control})$$

This is explicitly multi-dimensional. Sen insists that capabilities cannot be aggregated into a single index without loss of essential information—precisely the claim that moral evaluation is tensorial, not scalar.

### The Incompleteness Thesis

Sen argues that comparative judgments of capability sets are *incomplete*: we can often say that one situation is better than another along some dimensions and worse along others, without being able to say which is better overall. This incompleteness is not a failure of the theory but a feature of moral reality.

In tensorial terms, this is the claim that the moral metric is *degenerate* or *partial*. Not all vectors can be compared in length. Given two capability vectors c₁ and c₂, we may have:

- c₁ > c₂ along some dimensions
- c₁ < c₂ along other dimensions
- No basis for overall comparison

This is the tensorial signature of *incommensurability*. A scalar theory would force a comparison (by summing or by lexical priority); Sen's theory preserves the genuine incompleteness of the moral situation.

### Nussbaum's Threshold and Stratum Structure

Nussbaum modifies the capabilities approach by introducing *thresholds*: minimum levels of each capability below which a life is not fully human. This introduces *stratum structure* into capability space.

Below the threshold, we are in a different moral regime—one where the imperative is to raise capabilities to the threshold level. Above the threshold, trade-offs and choices become permissible. The threshold is a *stratum boundary* separating regions with different moral rules.

This is proto-stratified geometry. Nussbaum's capability space is not a smooth manifold but a stratified space with distinguished hypersurfaces (the thresholds) where the moral rules change discontinuously.

---

## Moral Uncertainty: Mixed States and Superposition

Recent work in moral philosophy has focused on *moral uncertainty*: what should we do when we are uncertain which moral theory is correct? If I am 60% confident in utilitarianism and 40% confident in deontology, and they recommend different actions, what should I choose?

Various approaches have been proposed: "my favorite theory" (act on whichever theory you find most plausible), "maximize expected moral value" (weight each theory's recommendation by your credence in it), and more sophisticated methods that account for intertheoretic comparisons.

### Tensorial Reading

The structure of moral uncertainty is strikingly similar to *quantum superposition*. An agent under moral uncertainty is not in a definite moral state but in a *superposition* of moral states, weighted by credence.

Let |U⟩ be the state "utilitarianism is correct" and |D⟩ be the state "deontology is correct." An agent with 60% credence in utilitarianism is in the state:

$$|\psi\rangle = \sqrt{0.6}|U\rangle + \sqrt{0.4}|D\rangle$$

This is a vector in a *theory space*, not a scalar. The agent's moral situation cannot be captured by a single number (overall credence) but requires specification of the full vector.

When the agent acts, the superposition "collapses" to a definite choice—but the choice reflects the full vector structure. Expected value maximization is one way to perform this collapse (a specific *contraction* operation); other approaches perform different contractions.

### Moral Hedging as Covariance

The sophisticated treatment of moral uncertainty involves *hedging*: choosing actions that are reasonably good under multiple theories, even if not optimal under any. This is analogous to *portfolio diversification* in finance—choosing investments that reduce variance across states of the world.

In tensorial terms, hedging is sensitivity to the *covariance structure* of moral uncertainty. If my uncertainty is concentrated in ways that some actions are robust to, I can act confidently. If my uncertainty lies along the dimensions that differentiate the recommended actions, I should hedge.

Let Σ be the covariance matrix of my moral beliefs (encoding correlations between credences in different theories). Let Δa = (a_U - a_D) be the vector of differences between what each theory recommends for action a. The "risk" of action a is:

$$\sigma_a^2 = \Delta_a^T \Sigma \Delta_a$$

Actions with low σ² are robust to moral uncertainty; actions with high σ² are risky bets on particular theories being correct.

This is the moral analogue of the portfolio variance formula in finance—and it requires the full tensor structure of uncertainty, not just scalar credences.

---

## Synthesis: What the Precursors Share

Across two and a half millennia, these thinkers share a recognition that moral reality resists scalar reduction:

| Thinker | Insight | Tensorial Structure |
|---------|---------|---------------------|
| Aristotle | The mean is context-dependent | Evaluation as section of fiber bundle; agent-relative metric |
| Kant | Morality requires universalizability | Permissible maxims as transformation invariants |
| Ross | Duties are plural and interacting | Duties as vector components; combination as vector sum |
| Rawls | Justice requires position-independence | Principles as symmetric tensors; metric choice determines theory |
| Sen/Nussbaum | Capabilities are irreducibly plural | Capabilities as basis vectors; incompleteness as metric degeneracy |
| Moral uncertainty | Credences have structure | Beliefs as state vectors; hedging from covariance structure |

None of these thinkers used the language of tensors. But they all developed conceptual tools to handle phenomena that tensors formalize:

1. **Multi-dimensionality**: Moral evaluation involves multiple independent considerations that cannot be reduced to one.

2. **Transformation behavior**: What happens to moral claims when we shift perspective, permute agents, or change framing?

3. **Metric structure**: How do we compare values, measure moral distance, identify incommensurability?

4. **Context-dependence**: The same abstract principle yields different concrete prescriptions in different situations.

5. **Structured combination**: When moral considerations combine, they do so geometrically (with alignment, orthogonality, opposition), not arithmetically.

---

## What the Tensorial Framework Adds

If these insights are already present in the tradition, what does the tensorial framework add?

**Precision.** The tradition offers metaphors and intuitions; the framework offers definitions and theorems. "Duties interact" becomes "duties combine as vectors under the moral metric." "The mean is relative to us" becomes "virtue is determined by an agent-parameterized metric on disposition-space." Precision enables analysis, criticism, and extension.

**Unification.** The tradition offers disparate insights from incompatible systems. The tensorial framework reveals common structure beneath surface disagreement. Aristotle's context-sensitivity and Kant's universalizability are not opposed but complementary: both constrain the transformation behavior of moral claims, in different ways.

**New questions.** The framework suggests questions the tradition did not ask. What is the *signature* of the moral metric—is it positive-definite (Euclidean), indefinite (Lorentzian), or degenerate? What are the *symmetries* of moral space—which transformations leave the structure invariant? What *curvature* does moral space have—how does parallel transport around a loop change moral vectors?

**Computability.** Finally, and most relevant to the application of this framework to artificial systems, tensorial ethics is *computable*. Tensors can be represented in computers; tensor operations can be implemented in algorithms; tensor equations can be solved numerically. The tradition offers wisdom; the framework offers implementation.

---

## Conclusion: Tensors as the Language of Moral Structure

The history of moral philosophy is, in significant part, a struggle against the reductionism of scalar ethics. Each thinker we have examined recognized that moral reality has structure that scalars cannot capture, and developed tools to articulate that structure.

Tensorial ethics is not a break from this tradition but its continuation—and, in a sense, its completion. The conceptual tools developed by Aristotle, Kant, Ross, Rawls, Sen, Nussbaum, and theorists of moral uncertainty find their natural mathematical expression in the language of tensors, metrics, transformations, and stratified spaces.

This is not to say that the tradition was secretly doing mathematics. It is to say that mathematics, properly understood, is the science of structure—and the structures that matter for ethics are precisely those that tensor calculus was developed to describe: transformation behavior, multi-linear combination, coordinate invariance, metric geometry.

The tradition provides the insights. The framework provides the language. Together, they enable a moral philosophy that is both faithful to the complexity of ethical life and precise enough to be implemented, tested, and refined.

In the chapters that follow, we develop the framework in full. But we do so in the company of these predecessors, whose insights we are formalizing, not replacing.

---

*Aristotle sought the mean. Kant sought the universal. Ross sought the balance. Rawls sought the fair. Sen sought the capable.*

*They were all, in their different ways, seeking the tensor.*
