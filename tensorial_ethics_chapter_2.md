# Chapter 2: Why Ethics Might Be Tensorial

## The Parable of the Old Man and His Horse

There is an ancient Chinese parable known as 塞翁失马 (*Sāi Wēng Shī Mǎ*)—"The Old Man at the Border Loses His Horse." It goes like this:

> An old man living near the frontier lost his horse. His neighbors came to console him, but the old man said, "How do you know this isn't good fortune?"
>
> Some months later, the horse returned, bringing with it a herd of fine wild horses. The neighbors came to congratulate him, but the old man said, "How do you know this isn't bad fortune?"
>
> With so many horses, the old man's son took to riding. One day he fell and broke his leg. The neighbors came to console the old man, but he said, "How do you know this isn't good fortune?"
>
> A year later, war came to the border. All the able-bodied young men were conscripted, and most died in battle. But the old man's son, with his broken leg, was spared.

The parable is usually read as a lesson in epistemic humility: we cannot know whether present events are good or bad because we cannot foresee their consequences. "Maybe" is the only honest answer.

But I want to suggest a different reading—one that reveals something structural about moral evaluation itself. The old man's "maybe" is not merely a confession of ignorance. It is a recognition that *scalar evaluation is the wrong tool for the job*.

When we say "losing the horse is bad," we are assigning a number—call it S(x) = -1—to the present state. When the horse returns with others, we revise: S(x) = +3. When the son breaks his leg, we revise again: S(x) = -2. And so on.

But notice what this scalar cannot represent:

1. **Which directions matter.** The loss of the horse is "bad" primarily along the *wealth* axis. It says nothing about the *health* axis, or the *family* axis, or the *political* axis (the son's eventual exemption from conscription). A scalar collapses all these dimensions into a single number, losing the information about *where* the badness lies.

2. **Where uncertainty concentrates.** The old man's uncertainty is not uniform. He is quite certain the horse is gone. What he is uncertain about is whether events will unfold along axes where the loss matters. Will famine come (making the lost horse catastrophic)? Will the horse return (making the loss temporary)? Will war come (making his son's presence at home decisive)? The uncertainty has *shape*—it lies along some directions more than others.

3. **How evaluation changes along paths.** The moral status of "son breaks leg" depends on whether war is coming. The trajectory matters. Crossing from peacetime into wartime changes the evaluative landscape discontinuously—what was unambiguously bad (broken leg) becomes ambiguously fortunate (exemption from death). A scalar at a point cannot represent these *regime changes*.

The parable, I suggest, is pointing at a mathematical truth: **moral evaluation requires geometric structure that scalars cannot provide.**

---

## The Insufficiency of Rank-0 Ethics

Let us be precise about what a scalar moral evaluation can and cannot do.

A *scalar* is a quantity fully specified by a single number. In ethics, scalar approaches assign a value—utility, welfare, goodness, rightness—to states of affairs, actions, or outcomes. The utilitarian calculus is scalar: it asks for the sum of pleasures minus pains, yielding a single number to be maximized. Cost-benefit analysis is scalar: all considerations reduce to a common currency. Even pluralistic theories that acknowledge multiple values typically seek, at the moment of decision, to collapse this plurality into a single ranking or a single number.

Formally, a scalar moral evaluation is a function:

$$S: \mathcal{M} \to \mathbb{R}$$

assigning to each point x in the moral space M a real number S(x). The defining feature of a scalar is *invariance*: under any coordinate transformation (any redescription of the situation), the value S(x) remains the same.

This invariance is both the strength and the weakness of scalar ethics. It is a strength because it promises objectivity: the goodness of a state should not depend on how we describe it. It is a weakness because it *loses information*: to achieve invariance, we must discard everything that varies with perspective.

The parable of the old man reveals three specific structural limitations:

### Limitation 1: No Directional Information

A scalar S(x) tells us the magnitude of value at a point. It cannot tell us *which directions* in the moral space are responsible for that value, nor which directions would change the evaluation most dramatically.

Consider the moment the horse runs away. A scalar evaluation might say S = -1. But this number conceals the structure of the situation:

- Along the *wealth* dimension: strongly negative (valuable asset lost)
- Along the *labor* dimension: moderately negative (horse did farm work)
- Along the *health* dimension: neutral (no one is sick or injured)
- Along the *family* dimension: neutral (relationships unchanged)
- Along the *political* dimension: unknown (depends on future events)

A *vector* can represent this structure. Let v = (-0.8, -0.4, 0, 0, ?) be the "impact vector" of the horse's departure, with components along each morally relevant dimension. The scalar S = -1 is some contraction of this vector—perhaps its magnitude, or a weighted sum—but the vector itself contains information the scalar discards.

This matters because moral reasoning often requires knowing *which dimensions are engaged*. If a proposed remedy addresses the wrong dimension (say, offering emotional support when the problem is financial), it will be ineffective despite targeting the "badness." The vector structure tells us where to intervene; the scalar does not.

### Limitation 2: Uncertainty Has Shape

The old man's "maybe" reflects uncertainty about the future. But his uncertainty is not uniform across all possibilities. It has *shape*: he is more uncertain about some developments than others, and—critically—his uncertainty is greatest along the dimensions that are most ethically decisive.

A scalar treatment of uncertainty adds error bars: S = -1 ± 0.5. This says the true value lies somewhere in the interval [-1.5, -0.5], but nothing about *why* we are uncertain or *where* the uncertainty matters.

A tensorial treatment represents uncertainty as a *covariance matrix* (or more generally, a rank-2 tensor) that encodes both the magnitude and the directional structure of our uncertainty:

$$\Sigma_{ij} = \langle (\delta m_i)(\delta m_j) \rangle$$

This tells us: uncertainty is large along axis i, small along axis j, and correlated between axes i and k.

In the parable, the old man's uncertainty might be:

- Small along the *current wealth* axis (the horse is definitely gone)
- Large along the *future wealth* axis (will more horses come?)
- Large along the *political* axis (will there be war?)
- Correlated between *political* and *son's welfare* (war affects conscription)

The crucial insight is that **uncertainty concentrated along ethically decisive directions matters more than uncertainty along irrelevant directions**. If the old man were uncertain about the color of next year's crops but certain about everything that affects his family's survival, the first uncertainty would be ethically negligible. But if he is uncertain precisely about war and conscription—the dimensions that determine whether the broken leg is a tragedy or a salvation—then his uncertainty is ethically maximal.

Scalar uncertainty (S ± ε) cannot represent this. The covariance tensor Σ can.

### Limitation 3: Paths Cross Boundaries

The most profound limitation of scalar evaluation is its inability to represent *trajectory-dependent* moral change, especially trajectories that cross *regime boundaries*.

In the parable, the evaluation of "son has a broken leg" depends on whether war comes. Before the declaration of war, a broken leg is unambiguously bad: pain, disability, inability to work. After war is declared, the evaluation bifurcates: for those without exemptions, conscription leads to probable death; for those with exemptions (including the son), survival is likely. The broken leg, unchanged in itself, has crossed a moral phase boundary.

This is not merely a matter of new information changing our estimate. It is a structural feature of the moral landscape: there exist *strata* (regimes, phases) within which smooth trade-offs apply, separated by *boundaries* where the rules change discontinuously.

A scalar function S: M → ℝ, if it is continuous, cannot represent such discontinuities. It can represent gradual change—S increasing or decreasing smoothly—but not the sharp transitions that characterize moral thresholds: consent given vs. withheld, life vs. death, war vs. peace.

To represent regime boundaries, we need *stratified* spaces: spaces composed of smooth strata (within which scalar and vector calculus apply) joined along lower-dimensional boundaries (where discontinuities are permitted). And to represent how moral status evolves along paths that may cross these boundaries, we need *path-dependent* operations: parallel transport, holonomy, trajectory integrals.

---

## What Tensorial Structure Provides

The three limitations point toward three geometric structures beyond scalars:

| Limitation | Required Structure | Mathematical Object |
|------------|-------------------|---------------------|
| No directional information | Vectors and covectors | ∇S, O^μ, I_μ |
| Uncertainty has no shape | Covariance/correlation | Σ^{ij}, G_{μν} |
| No path-dependence | Stratification + transport | Strata, parallel transport, holonomy |

Let us examine each.

### Gradients and the Direction of Moral Change

If moral evaluation were purely scalar, there would be no meaningful sense of "direction" in moral space. But our actual moral reasoning is saturated with directional concepts: obligations *point* toward required states; interests *aim* at objects; responsibility *flows* from agents to patients; improvement *moves* toward better configurations.

These are not metaphors. They are descriptions of *vector* quantities—objects with both magnitude and direction.

Consider an obligation. "You ought to help your neighbor" is not merely a magnitude of oughtness. It specifies a *direction*: from the current state (neighbor unhelped) toward a required state (neighbor helped). The obligation can be stronger or weaker (magnitude), but it also has an orientation in the space of possible actions.

Formally, we can represent obligations as *vector fields* on the moral manifold:

$$O^\mu(x): \mathcal{M} \to T\mathcal{M}$$

At each point x in moral space, O^μ(x) is a tangent vector pointing in the direction of what is required.

Interests, conversely, can be represented as *covector fields*:

$$I_\mu(x): \mathcal{M} \to T^*\mathcal{M}$$

A covector (or 1-form) is a linear functional on vectors. The interest I_μ, applied to an obligation O^μ, yields a scalar: the *satisfaction* of interest I by obligation O.

$$S = I_\mu O^\mu$$

This is the fundamental formula of tensorial ethics: satisfaction is the contraction of obligations with interests. It is coordinate-invariant (a scalar), but it *arises from* vector quantities that carry directional information.

The gradient ∇S of the satisfaction function tells us: at this point in moral space, which direction increases satisfaction most rapidly? This is the direction of moral improvement—not a scalar claim ("things could be better") but a vector claim ("things could be better *in this specific way*").

### The Metric Tensor and Moral Distance

To speak of directions, we need a way to compare them. To speak of distances, we need a way to measure them. In differential geometry, these functions are performed by the *metric tensor* g_{μν}.

The metric tensor is a rank-2 object that defines the inner product between vectors:

$$\langle u, v \rangle = g_{\mu\nu} u^\mu v^\nu$$

This allows us to say when two directions are orthogonal (their inner product is zero), when they are aligned (inner product is large and positive), and when they are opposed (inner product is negative). It also defines the length of vectors and the distance between points.

In moral space, the metric encodes *how we compare values*. Two values are orthogonal if trading off one against the other is undefined—there is no exchange rate between them. They are aligned if improving one tends to improve the other. They are opposed if they conflict.

The claim that some values are *incommensurable* is, in tensorial language, the claim that the moral metric is *degenerate* along certain directions—that there exist vectors v such that g_{μν}v^μv^ν = 0, or that the metric blows up (becomes infinite) when we try to compare certain dimensions.

This is a structural claim, not a mystical one. It says that the geometry of moral space is not Euclidean—not all directions are comparable in the way that spatial directions are.

### The Covariance Tensor and Structured Uncertainty

The old man's "maybe" reflects uncertainty that has directional structure. To represent this, we introduce a *covariance tensor*:

$$\Sigma^{ij} = \mathbb{E}[(\delta m^i)(\delta m^j)]$$

where δm^i is the deviation of the i-th moral dimension from its expected value.

This rank-2 tensor encodes:

- **Variance** along each axis: Σ^{ii} tells us how uncertain we are about dimension i
- **Covariance** between axes: Σ^{ij} (i ≠ j) tells us whether uncertainty in dimension i correlates with uncertainty in dimension j
- **Principal directions**: the eigenvectors of Σ tell us the directions of maximum and minimum uncertainty

Ethically, what matters is the *alignment* between the uncertainty tensor and the gradient of moral value. If our uncertainty lies primarily along directions where the moral stakes are low, we can act confidently despite incomplete knowledge. If our uncertainty lies along the directions where moral stakes are highest, we should proceed with caution—or recognize, like the old man, that "maybe" is the honest answer.

The scalar quantity that captures this alignment is:

$$\sigma_S^2 = \Sigma^{ij} \frac{\partial S}{\partial m^i} \frac{\partial S}{\partial m^j}$$

This is the *variance of the moral evaluation* given structured uncertainty. It is large when uncertainty concentrates along morally decisive directions, and small when uncertainty lies along morally irrelevant directions.

### Stratification and Moral Phase Transitions

The parable's most profound feature is the regime change brought by war. Before war is declared, the broken leg is bad. After war is declared, it becomes potentially good (exemption from death). This is not a gradual transition; it is a discontinuous jump at a boundary.

To represent such discontinuities, we need the apparatus of *stratified spaces*: spaces composed of smooth manifolds (strata) joined along boundaries where the smooth structure breaks down.

A stratified moral space M consists of:

1. **Strata** M_i: smooth manifolds of various dimensions, representing regimes within which ordinary calculus applies
2. **Boundary conditions**: rules for how strata are joined
3. **Discontinuous functions**: moral evaluations that are smooth on each stratum but may jump at boundaries

The boundary between "peacetime" and "wartime" is a moral stratum boundary. On either side, smooth trade-offs apply (more wealth is better, less pain is better). But crossing the boundary changes *which smooth trade-offs apply*. The rules are different.

This is why the old man cannot assign a stable scalar to his son's broken leg. The evaluation depends on which stratum the world occupies, and that is exactly what he is uncertain about.

---

## The Parable Revisited

Let us return to the old man with the full apparatus of tensorial ethics.

**Moment 1: The horse runs away.**

The moral state is x_1. The impact lies primarily along the wealth dimension: obligation to provide for family is now harder to meet. The gradient ∇S points toward "recover the horse or find an alternative." The uncertainty tensor Σ is large along future-wealth and future-events axes—much could change.

A scalar evaluation says S(x_1) ≈ -1. But this discards the directional structure. The old man, implicitly recognizing the tensor structure, says "maybe."

**Moment 2: The horse returns with others.**

The moral state is x_2. The impact is strongly positive along wealth. The gradient ∇S now points toward "maintain and increase this windfall." The uncertainty tensor remains large along future-events.

A scalar evaluation says S(x_2) ≈ +3. The neighbors celebrate. The old man, still tracking the tensor structure, says "maybe."

**Moment 3: The son breaks his leg.**

The moral state is x_3. The impact is negative along health and capability. But now the uncertainty tensor Σ becomes crucial: there is high covariance between the *political* dimension (will there be war?) and the *welfare* dimension (will the son survive?). 

Crucially, the son's condition now sits near a *stratum boundary*. If war comes, the moral evaluation of the broken leg will discontinuously shift. The gradient ∇S is undefined at the boundary—it points one way in peacetime, another way in wartime.

A scalar evaluation says S(x_3) ≈ -2. The old man, sensing the proximity to regime change, says "maybe."

**Moment 4: War comes; the son is spared.**

The moral state crosses the boundary into wartime. The broken leg, unchanged in itself, is now on a different stratum. Its evaluation, relative to the counterfactual (able-bodied son conscripted and killed), is strongly positive.

The scalar is now S(x_4) ≈ +5 or +10 (how do we quantify a life saved?). But this scalar conceals the path-dependence: the same physical state (broken leg) has different moral valence depending on which stratum it occupies.

---

## Why "Maybe" Is Geometric, Not Merely Epistemic

The standard interpretation of the parable is epistemic: we should say "maybe" because we lack knowledge of the future. If only we knew whether war was coming, we could assign definite values.

But the tensorial interpretation suggests something deeper: "maybe" is the correct answer *even with perfect knowledge* when the evaluation structure is tensorial rather than scalar.

Suppose the old man had an oracle who told him exactly what would happen. Would he then assign a definite scalar to each moment?

Only if he were willing to commit to:
1. A fixed weighting of dimensions (how much does wealth matter vs. health vs. family?)
2. A fixed treatment of path-dependence (does the broken leg's value depend on the path through wartime, or just the final state?)
3. A specific contraction that collapses the tensor to a scalar

These choices are not determined by the facts. They are *perspective-dependent*—different agents, with different weights and different interests, will perform different contractions and arrive at different scalars.

The tensor is the invariant reality. The scalar is a projection, a shadow, a contraction that loses information. "Maybe" is what you say when you recognize that the tensor cannot be faithfully represented by any single scalar.

---

## From Parable to Framework

The parable motivates the framework we will develop in subsequent chapters:

1. **Moral space has dimension** (Chapter 4). The space of morally relevant configurations is not a line (totally ordered by goodness) but a manifold of higher dimension, with independent axes for different values, agents, and considerations.

2. **Moral quantities are tensors** (Chapter 5). Obligations, interests, responsibilities, and evaluations are not scalars but tensors of various ranks, carrying directional and relational information that scalars discard.

3. **Moral space has a metric** (Chapter 6). The structure that allows comparison of values, measurement of moral distance, and identification of orthogonal (incommensurable) dimensions is a metric tensor g_{μν}.

4. **Moral space is stratified** (Chapter 4). The space is not uniformly smooth but divided into strata—regimes within which smooth trade-offs apply—separated by boundaries where rules change discontinuously.

5. **Moral transformation has structure** (Chapter 7). What happens to moral evaluations when we shift perspective, permute agents, or translate across contexts? The transformation behavior of tensors answers this question precisely.

The old man at the border, without the language of differential geometry, had the insight: moral reality is richer than any scalar can capture. What tensorial ethics provides is the mathematical apparatus to make that insight precise.

---

## Anticipating Objections

The skeptical reader will have objections. Let me briefly anticipate two.

**"Isn't this just saying ethics is complicated?"**

No. "Complicated" suggests more of the same—more variables, more factors, more considerations to weigh. Tensorial structure is *different in kind*. A vector is not just a complicated scalar; it has properties (direction, transformation behavior) that scalars lack categorically. The claim is not that ethics has many dimensions (though it does) but that moral quantities *transform* in specific ways under change of perspective, and this transformation behavior is what tensors capture.

**"We can't measure moral quantities precisely, so what use is this formalism?"**

The same objection was raised against utility theory, and against the use of calculus in economics. The response is twofold. First, the framework's value lies in *structural* insights, not numerical precision. Knowing that two values are orthogonal (incommensurable) is useful even if we cannot measure their magnitudes exactly. Second, the framework identifies *what would need to be measured* to make ethical reasoning precise, even if current methods fall short. Physics progressed from qualitative insights ("force causes acceleration") to quantitative laws (F = ma) as measurement improved. Ethics might do the same.

These objections are serious enough to warrant dedicated chapters later in the book (Chapters 11 and 12). For now, the parable has done its work: it has shown that scalar ethics loses information that matters, and pointed toward the richer structures that might preserve it.

---

## Conclusion

The old man's "maybe" is not resignation. It is recognition.

A scalar S(x) can label the present, but cannot represent which directions are ethically decisive, whether uncertainty lies along those decisive directions, or how ethical status evolves along trajectories that cross stratification boundaries.

These requirements are naturally expressed by higher-order geometric objects:

- **Gradients** capture local fragility near moral phase transitions
- **Covariance tensors** encode uncertainty in morally relevant coordinates
- **Trajectory-level transport** captures path dependence

Without this higher-order structure, "maybe" must be bolted on as an ad hoc heuristic—a confession of ignorance—rather than emerging from the model as a structural feature of moral reality.

The parable, read tensorially, is not about the limits of human knowledge. It is about the geometry of ethical evaluation. The old man sees that the tensor cannot be contracted to a scalar without loss. His "maybe" is a holding operation—a refusal to project—until the full structure of the situation is revealed.

Tensorial ethics takes this insight and makes it mathematical. The chapters that follow develop the apparatus: the moral manifold, the tensor hierarchy, the metric, the transformations. But the core insight is here, in the parable: *ethics is not a number*. It is a geometric structure. And the first step in understanding that structure is recognizing what scalars cannot do.

---

*The horse runs away. Good? Bad? Maybe.*

*The formalism agrees: the tensor is not yet fully contracted. Hold the projection. Watch the geometry unfold.*
