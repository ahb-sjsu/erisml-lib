# Chapter 13: Group-Theoretic Data Augmentation

*Geometric Methods in Computational Modeling --- Andrew H. Bond*

---

> *"The universe is an enormous direct product of representations of symmetry groups."*
> --- Hermann Weyl, *Symmetry* (1952)

A 5x5 grid depicting a colored L-shape admits exactly eight orientations under rotations and reflections. A model that has seen only one of these orientations and must generalize to the other seven is doing unnecessary work --- the eight orientations are not independent data points but a single orbit under the action of a finite group. This chapter develops the mathematics and engineering of *group-theoretic data augmentation*: the systematic exploitation of symmetry groups to multiply training signal, constrain learned representations, and reduce sample complexity.

The idea is ancient in mathematics and well known in computer vision, but its formalization through the lens of abstract algebra reveals structure that ad hoc augmentation pipelines miss. A rotation is not just "a transform we happened to think of." It is one element of a group whose algebraic properties --- closure, associativity, identity, inverses --- guarantee that the set of augmented examples is complete and non-redundant. When the group is known exactly (as it is for the dihedral group $D_4$ acting on square grids), the augmentation is *provably exhaustive*: no equivalent configuration is left undiscovered.

We begin with the algebra, move to the computational implementation using real code from the ARC-AGI solver, connect augmentation to the broader framework of equivariant architectures, and close with extensions to groups beyond $D_4$.

---

## 13.1 Symmetry as a Computational Resource

### 13.1.1 The Cost of Ignorance

Consider a neural network trained to classify patterns on a square grid. The training set contains 1{,}000 examples. If the network has no built-in knowledge of rotational symmetry, it must learn from the data that a pattern and its 90-degree rotation belong to the same class. This requires seeing both orientations in the training set --- and ideally seeing them with comparable frequency, lest the network develop an orientation bias.

The situation is worse than it appears. The network must not only learn that rotations preserve class identity; it must learn this *independently for each class*. With 50 classes and 4 rotations, the network needs $50 \times 4 = 200$ implicit "symmetry facts," each requiring multiple training examples to learn robustly. These facts are not independent of each other --- they all follow from a single algebraic principle --- but a network without symmetry structure has no way to share this knowledge across classes.

The cost can be quantified. Let $f: \mathcal{X} \to \mathcal{Y}$ be the target function, let $G$ be a symmetry group acting on $\mathcal{X}$, and suppose $f$ is $G$-invariant: $f(g \cdot x) = f(x)$ for all $g \in G$, $x \in \mathcal{X}$. A model that does not exploit this invariance has an effective hypothesis space of size $|\mathcal{H}|$. A model that enforces $G$-invariance reduces the hypothesis space to $|\mathcal{H}| / |G|$ (up to factors depending on the group action's structure). For $D_4$ with $|G| = 8$, this is an eightfold reduction --- equivalent, in sample complexity terms, to having eight times as much training data.

### 13.1.2 Three Ways to Exploit Symmetry

There are three distinct strategies for exploiting a known symmetry group, each with different tradeoffs:

**Data augmentation.** Generate new training examples by applying group elements to existing examples. This is the simplest approach and requires no architectural changes. The training set grows by a factor of $|G|$ (or a subset thereof). The model is free to learn any function; the augmented data *encourages* but does not *guarantee* invariance.

**Equivariant architecture.** Design the network so that its intermediate representations transform predictably under the group action: $\phi(g \cdot x) = \rho(g) \cdot \phi(x)$, where $\rho$ is a representation of $G$ on the feature space. This *guarantees* equivariance by construction but requires specialized layers (e.g., group convolutions). The final invariant prediction is obtained by pooling over the group.

**Symmetrized loss.** Average the loss over the group orbit: $\mathcal{L}_{\text{sym}}(x) = \frac{1}{|G|} \sum_{g \in G} \mathcal{L}(g \cdot x)$. This is intermediate between augmentation and architectural enforcement --- it does not expand the dataset but biases the optimization toward invariant solutions.

This chapter focuses primarily on data augmentation, which is the most widely applicable and the strategy implemented in the ARC-AGI codebase. Section 13.5 discusses equivariant architectures as a complement.

---

## 13.2 The Dihedral Group $D_4$

### 13.2.1 Definition and Elements

The *dihedral group* $D_n$ is the symmetry group of a regular $n$-gon: the set of all rigid motions of the plane that map the $n$-gon to itself. For a square ($n = 4$), the group $D_4$ has eight elements:

| Element | Symbol | Description | Matrix |
|---------|--------|-------------|--------|
| Identity | $e$ | No transformation | $\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}$ |
| Rotation 90 | $r$ | Quarter turn CCW | $\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$ |
| Rotation 180 | $r^2$ | Half turn | $\begin{pmatrix} -1 & 0 \\ 0 & -1 \end{pmatrix}$ |
| Rotation 270 | $r^3$ | Three-quarter turn CCW | $\begin{pmatrix} 0 & 1 \\ -1 & 0 \end{pmatrix}$ |
| Reflect horizontal | $s$ | Flip across vertical axis | $\begin{pmatrix} -1 & 0 \\ 0 & 1 \end{pmatrix}$ |
| Reflect vertical | $sr$ | Flip across horizontal axis | $\begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$ |
| Reflect main diagonal | $sr^2$ | Transpose | $\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$ |
| Reflect anti-diagonal | $sr^3$ | Anti-transpose | $\begin{pmatrix} 0 & -1 \\ -1 & 0 \end{pmatrix}$ |

The group is generated by two elements: a rotation $r$ (of order 4) and a reflection $s$ (of order 2), subject to the relation $srs = r^{-1}$. Every element can be written as $s^a r^b$ with $a \in \{0, 1\}$ and $b \in \{0, 1, 2, 3\}$, giving $2 \times 4 = 8$ elements.

### 13.2.2 The Group Multiplication Table

The multiplication (composition) table of $D_4$ encodes how transformations compose. Rather than listing all 64 entries, we note the key structural facts:

- The rotations $\{e, r, r^2, r^3\}$ form a *normal subgroup* isomorphic to $\mathbb{Z}_4$ (the cyclic group of order 4).
- The reflections $\{s, sr, sr^2, sr^3\}$ form a coset, not a subgroup (the composition of two reflections is a rotation).
- $D_4$ is non-abelian: $rs \neq sr$. Specifically, $rs = sr^3$. The order of operations matters.

These algebraic properties have direct computational consequences. The closure property guarantees that composing any two $D_4$ transforms yields another $D_4$ transform --- there are no "missing" augmentations. The non-abelian structure means that the order of reflection and rotation matters, which is why the `all_dihedral` function in the ARC codebase generates all eight transforms explicitly rather than composing rotations and reflections in arbitrary order.

### 13.2.3 Group Actions on Grids

A *group action* of $D_4$ on the set of grids $\mathcal{G} = \{0, \ldots, 9\}^{H \times W}$ is a map $\alpha: D_4 \times \mathcal{G} \to \mathcal{G}$ satisfying:

1. **Identity:** $\alpha(e, G) = G$ for all grids $G$.
2. **Compatibility:** $\alpha(g_1, \alpha(g_2, G)) = \alpha(g_1 g_2, G)$ for all $g_1, g_2 \in D_4$.

For square grids ($H = W$), the action is straightforward: rotations cycle the rows and columns, and reflections flip them. For rectangular grids ($H \neq W$), the 90-degree rotation maps an $H \times W$ grid to a $W \times H$ grid --- the action is still well-defined, but the grid dimensions change. This is a critical implementation detail that naive augmentation code often gets wrong.

The *orbit* of a grid $G$ under $D_4$ is the set of all distinct grids reachable by applying group elements:

$$\text{Orb}(G) = \{ g \cdot G : g \in D_4 \}$$

For a generic grid with no internal symmetry, $|\text{Orb}(G)| = 8$. But a grid with internal symmetry --- such as a checkerboard pattern, which is invariant under 180-degree rotation --- has a smaller orbit. The *stabilizer* $\text{Stab}(G) = \{g \in D_4 : g \cdot G = G\}$ captures the grid's internal symmetry, and the orbit-stabilizer theorem gives:

$$|\text{Orb}(G)| = \frac{|D_4|}{|\text{Stab}(G)|} = \frac{8}{|\text{Stab}(G)|}$$

A grid with 4-fold rotational symmetry (e.g., an X-pattern centered on the grid) has $|\text{Stab}(G)| = 4$ and orbit size 2. A grid with full $D_4$ symmetry (e.g., a single centered pixel) has $|\text{Stab}(G)| = 8$ and orbit size 1 --- augmentation produces no new examples.

---

## 13.3 Implementation: D4 Augmentation for ARC-AGI

### 13.3.1 The Core Transform Functions

The ARC-AGI codebase implements $D_4$ augmentation using NumPy array operations. The fundamental building blocks are rotation and reflection:

```python
def rotate_grid(grid: np.ndarray, k: int = 1) -> np.ndarray:
    """Rotate grid by k * 90 degrees counter-clockwise."""
    return np.rot90(grid, k)


def reflect_grid(grid: np.ndarray, axis: int = 0) -> np.ndarray:
    """Reflect grid.  axis=0 -> vertical flip, axis=1 -> horizontal flip."""
    if axis == 0:
        return np.flipud(grid).copy()
    return np.fliplr(grid).copy()
```

These two functions correspond to the generators $r$ and $s$ of $D_4$. Every group element can be expressed as a composition of these two operations. The `.copy()` call on reflection outputs is a deliberate engineering choice: NumPy's `flipud` and `fliplr` return *views* into the original array, not independent copies. Without the copy, subsequent in-place modifications to the reflected grid would corrupt the original --- a subtle bug that manifests as non-deterministic training behavior.

### 13.3.2 Generating the Full Orbit

The `all_dihedral` function generates all eight $D_4$ transforms of a grid in a single call:

```python
def all_dihedral(grid: np.ndarray) -> List[np.ndarray]:
    """Generate all 8 dihedral group transforms of a grid.

    Returns [identity, rot90, rot180, rot270, flip_h, flip_v, diag1, diag2].
    """
    results = []
    for k in range(4):
        rotated = np.rot90(grid, k)
        results.append(rotated.copy())
    flipped = np.fliplr(grid)
    for k in range(4):
        results.append(np.rot90(flipped, k).copy())
    return results
```

The structure mirrors the algebraic decomposition $D_4 = \{r^b : b = 0,\ldots,3\} \cup \{s \cdot r^b : b = 0,\ldots,3\}$. The first loop generates the four rotations $\{e, r, r^2, r^3\}$. The second loop applies the reflection $s$ (implemented as `fliplr`) and then the four rotations, generating $\{s, sr, sr^2, sr^3\}$. This produces exactly eight grids, corresponding to the eight group elements, with no duplicates (assuming the input grid has trivial stabilizer).

The choice to use `fliplr` (horizontal flip) rather than `flipud` as the reflection generator is a convention. Any reflection would serve as $s$; the horizontal flip is chosen because it composes naturally with `rot90` to produce the diagonal reflections. Specifically:
- `fliplr` followed by `rot90` with $k=1$ gives the main diagonal reflection (transpose).
- `fliplr` followed by `rot90` with $k=3$ gives the anti-diagonal reflection.

### 13.3.3 Consistent Augmentation of Input-Output Pairs

For ARC-AGI tasks, augmentation must be *consistent*: the same transformation applied to both the input and output grids of a training pair, so that the transformation rule $\tau: \text{input} \to \text{output}$ is preserved. If we rotate the input by 90 degrees but not the output, the augmented pair encodes a different (and incorrect) rule.

The `augment_pair` function implements this consistency:

```python
def augment_pair(
    in_grid: np.ndarray,
    out_grid: np.ndarray,
    *,
    n_augments: int = 4,
    seed: int = 42,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Augment an input-output pair with consistent transforms.

    Applies the SAME transform to both input and output so the
    transformation rule is preserved.
    """
    rng = np.random.RandomState(seed)
    pairs = []

    for _ in range(n_augments):
        # Random rotation
        k = rng.randint(0, 4)
        aug_in = np.rot90(in_grid, k).copy()
        aug_out = np.rot90(out_grid, k).copy()

        # Random reflection
        if rng.random() > 0.5:
            aug_in = np.fliplr(aug_in).copy()
            aug_out = np.fliplr(aug_out).copy()
        if rng.random() > 0.5:
            aug_in = np.flipud(aug_in).copy()
            aug_out = np.flipud(aug_out).copy()

        # Color permutation (same mapping for both)
        color_seed = rng.randint(0, 2**31)
        aug_in = permute_colors(aug_in, seed=color_seed)
        aug_out = permute_colors(aug_out, seed=color_seed)

        pairs.append((aug_in, aug_out))

    return pairs
```

Three design choices merit attention.

First, the function samples *random* group elements rather than generating the entire orbit. With $n\_augments = 4$, it produces four random augmentations, not all eight $D_4$ transforms. This is a deliberate trade-off: during test-time training (Section 13.4), generating the full orbit of every training pair would increase the training set by a factor of 8, slowing each refinement step. Random sampling provides most of the benefit at lower cost.

Second, the function composes $D_4$ transforms with *color permutations*. Color permutations form a separate symmetry group --- the symmetric group $S_9$ acting on the nine non-background colors (Section 13.7) --- and the combination generates elements of the *direct product* $D_4 \times S_9$. This larger group has $8 \times 9! = 2{,}903{,}040$ elements, far too many to enumerate, which is why random sampling is essential.

Third, the use of a deterministic `seed` parameter ensures that augmentation is reproducible. Given the same input pair and seed, the function returns the same augmented pairs. This is critical for debugging and for ensuring that test-time training is deterministic across runs.

---

## 13.4 The ARC-AGI Application

### 13.4.1 Why ARC Puzzles Have Natural $D_4$ Symmetry

The Abstraction and Reasoning Corpus (ARC-AGI) presents tasks as collections of input-output grid pairs. Each task encodes a transformation rule that the solver must infer from the training pairs and apply to unseen test inputs. The grids use a palette of 10 colors (integers 0--9) on grids up to 30 by 30.

Most ARC transformation rules are *geometric* in nature: fill a region, extend a pattern, reflect a shape, complete a symmetry. These rules are typically invariant under the $D_4$ action --- a rule that says "extend the pattern rightward" becomes "extend the pattern downward" after a 90-degree rotation, but the *abstract* rule (extend in the direction of the pattern's orientation) is the same. By augmenting with $D_4$, the solver sees the rule from multiple orientations and learns the abstract principle rather than a specific directional instantiation.

This connects directly to the hyperbolic rule encoding developed in Chapter 3. The `HyperbolicRuleEncoder` maps transformation rules into the Poincare ball, where abstract rules cluster near the origin and specific sub-rules occupy the periphery. When the training pairs are augmented with $D_4$ transforms, the pair encoder sees eight orientations of the same abstract rule. The resulting hyperbolic embeddings cluster more tightly --- the augmented pairs reinforce the abstract rule signal while averaging out the orientation-specific noise.

### 13.4.2 Augmentation in the Solver Pipeline

The ARC solver's test-time training loop uses augmentation as a core component. The `refine_on_task` method augments each training pair before fine-tuning:

```python
def refine_on_task(self, train_pairs, device):
    from arc_prize.augment import augment_pair

    all_pairs = list(train_pairs)
    for in_grid, out_grid in train_pairs:
        for aug_in, aug_out in augment_pair(
            in_grid, out_grid,
            n_augments=self.config.n_augments,
        ):
            all_pairs.append((aug_in, aug_out))

    # Fine-tune on all_pairs (original + augmented) ...
```

With the default configuration of `n_augments=4`, each original training pair generates 4 augmented copies, expanding the training set by a factor of 5. The solver then runs leave-one-out training on this expanded set: for each pair, it infers the rule from all other pairs and predicts the held-out pair's output. The augmented pairs provide additional viewpoints on the same rule, making the inferred rule more robust.

The `solve_task` method also uses augmentation to generate a second candidate output:

```python
# Generate second candidate with augmented rule inference
aug_pairs = []
for in_g, out_g in train_pairs:
    augs = augment_pair(in_g, out_g, n_augments=2, seed=99)
    aug_pairs.extend(augs)
z_rule_alt = self.infer_rule(aug_pairs, device)
candidate_2 = self.predict(z_rule_alt, test_input, device)
```

This is a particularly elegant use of augmentation. ARC allows two submission attempts per test input. The solver uses the original training pairs for the first attempt and augmented pairs for the second. Because the augmented pairs emphasize the transformation rule from different orientations, the alternative rule encoding $z\_rule\_alt$ may capture aspects of the rule that the original encoding missed --- especially for rules with strong directional components.

### 13.4.3 Interaction with Structure Probing

Chapter 10 introduced the structure probing framework, which applies parametric transforms to grids and measures latent displacement to discover what invariances the model has learned. The connection to $D_4$ augmentation is direct: the `rotate`, `reflect_h`, and `reflect_v` parametric transforms in the probe suite are exactly the generators of $D_4$.

A model trained *without* $D_4$ augmentation will exhibit high latent displacement under rotations and reflections --- the probe reveals that the model has not learned rotational or reflective invariance. A model trained *with* $D_4$ augmentation should exhibit low displacement under these same transforms, because the augmented training data teaches the model that rotated and reflected grids are equivalent.

The structure probe's robustness index (Chapter 10, Section 10.3) thus provides a quantitative measure of how effectively augmentation has been absorbed. A model with high robustness index separates structural invariants (low displacement under $D_4$ transforms) from stress transforms (high displacement under noise and dropout). If $D_4$ augmentation is working correctly, the invariant transforms should produce near-zero displacement; any residual displacement indicates that the model has incompletely learned the symmetry.

This creates a diagnostic loop: augment, train, probe, and iterate. If probing reveals that the model remains sensitive to 90-degree rotation despite augmentation, possible causes include insufficient augmentation (increase `n_augments`), architectural bottlenecks (the encoder may lack the capacity to represent rotational invariance), or training instability (the augmented examples may be overwhelming the original signal). The probe provides the diagnostic; the group theory provides the remedy.

---

## 13.5 Equivariant Architectures

### 13.5.1 From Augmentation to Equivariance

Data augmentation teaches the model invariance through examples. An equivariant architecture enforces it through structure. The distinction is analogous to the difference between testing a program and proving it correct: augmentation checks invariance empirically; equivariance guarantees it mathematically.

A function $\phi: \mathcal{X} \to \mathcal{F}$ is *equivariant* with respect to a group $G$ if there exist group actions on $\mathcal{X}$ and $\mathcal{F}$ such that:

$$\phi(g \cdot x) = g \cdot \phi(x) \quad \text{for all } g \in G, \; x \in \mathcal{X}$$

Note that the group acts on the *output* space as well as the *input* space. Equivariance does not mean that the representation is unchanged by the group action (that would be invariance); it means that the representation transforms *predictably*. A standard CNN convolution layer is equivariant to translations: shifting the input shifts the feature map by the same amount. But standard convolutions are *not* equivariant to rotations --- rotating the input does not simply rotate the feature maps.

### 13.5.2 Group Convolutions

A *group convolution* extends the convolution operation to be equivariant to a finite group $G$. For the standard convolution on $\mathbb{Z}^2$, the output at position $x$ is:

$$[f * \psi](x) = \sum_{y \in \mathbb{Z}^2} f(y) \, \psi(x - y)$$

For a group convolution with group $G$, the output at group element $g$ is:

$$[f *_G \psi](g) = \sum_{h \in G} f(h) \, \psi(g^{-1}h)$$

In the first layer, the input is a function on $\mathbb{Z}^2$ and the filter is evaluated at all group elements applied to each spatial position. In subsequent layers, both input and output are functions on $G \times \mathbb{Z}^2$. For $D_4$, this means each spatial position carries 8 feature values, one for each group element, and the convolution respects the group structure.

The practical implications for ARC grid processing are significant. A $D_4$-equivariant encoder would guarantee that the latent representation of a rotated grid is a predictable transformation of the original grid's representation. The final invariant representation is obtained by pooling (averaging or max-pooling) over the group dimension:

$$z_{\text{inv}}(x) = \frac{1}{|G|} \sum_{g \in G} z(g, x)$$

This pooling step converts equivariance to invariance. The intermediate equivariant features retain orientation information (useful for predicting oriented outputs), while the pooled features discard it (useful for classification or rule inference).

### 13.5.3 Why ARC Uses Augmentation Instead

The ARC-AGI solver uses data augmentation rather than $D_4$-equivariant convolutions for three pragmatic reasons.

First, ARC grids are small (up to 30 by 30) and the group is small ($|D_4| = 8$). The computational overhead of augmentation --- generating 8 copies of each grid --- is negligible compared to the cost of the test-time training loop. Equivariant convolutions would reduce training-time cost but add architectural complexity.

Second, ARC tasks sometimes violate $D_4$ symmetry. A rule that says "fill the rightmost column with red" is *not* invariant under 90-degree rotation --- the rotated rule fills the top row, not the rightmost column. For such tasks, $D_4$-equivariant features would be *less* informative than orientation-specific features. Augmentation handles this naturally: the solver sees the rule from multiple orientations and learns to predict the orientation-appropriate output. An equivariant architecture would need an explicit mechanism to break symmetry when the task demands it.

Third, the solver combines $D_4$ transforms with color permutations. Building an architecture equivariant to $D_4 \times S_9$ is substantially more complex than building one equivariant to $D_4$ alone, while augmenting with elements of the product group is straightforward (as shown in Section 13.3.3).

---

## 13.6 The Orbit-Stabilizer Theorem in Practice

### 13.6.1 Detecting Redundant Augmentations

Not every grid benefits equally from augmentation. A grid with internal symmetry --- such as a rotationally symmetric pattern --- produces duplicate augmentations, wasting computation and biasing the training set.

The orbit-stabilizer theorem gives a precise count. For a grid $G$ with stabilizer subgroup $\text{Stab}(G) \leq D_4$:

$$|\text{Orb}(G)| \cdot |\text{Stab}(G)| = |D_4| = 8$$

The possible stabilizer sizes are 1, 2, 4, and 8, corresponding to orbit sizes 8, 4, 2, and 1. The following code detects the stabilizer by checking each group element:

```python
def compute_stabilizer(grid: np.ndarray) -> list[str]:
    """Find all D4 elements that leave the grid unchanged."""
    from arc_prize.augment import all_dihedral

    labels = ["e", "r", "r2", "r3", "s", "sr", "sr2", "sr3"]
    transforms = all_dihedral(grid)
    stabilizer = []
    for label, transformed in zip(labels, transforms):
        if np.array_equal(transformed, grid):
            stabilizer.append(label)
    return stabilizer


def unique_orbit(grid: np.ndarray) -> list[np.ndarray]:
    """Return only the distinct grids in the D4 orbit."""
    from arc_prize.augment import all_dihedral

    orbit = all_dihedral(grid)
    unique = [orbit[0]]
    for g in orbit[1:]:
        if not any(np.array_equal(g, u) for u in unique):
            unique.append(g)
    return unique
```

In practice, grids with large stabilizers are rare in ARC --- most task grids are asymmetric, yielding the full orbit of 8. But when they do occur, the duplicate augmentations can subtly bias training. If a symmetric grid has orbit size 2 while asymmetric grids have orbit size 8, the symmetric grid is overrepresented by a factor of 4 in the augmented training set. For large-scale training this may not matter; for the few-shot regime of ARC (typically 2--4 training pairs per task), it can shift the inferred rule toward the symmetric example.

### 13.6.2 Burnside's Lemma and Counting Distinct Patterns

A related question arises in ARC task analysis: *how many truly distinct grid patterns exist*, up to $D_4$ equivalence? Burnside's lemma (also known as the Cauchy-Frobenius lemma) answers this:

$$|\mathcal{G} / D_4| = \frac{1}{|D_4|} \sum_{g \in D_4} |X^g|$$

where $X^g = \{G \in \mathcal{G} : g \cdot G = G\}$ is the set of grids fixed by group element $g$. For 10-color grids of size $n \times n$:

- The identity $e$ fixes all $10^{n^2}$ grids.
- A 90-degree rotation $r$ fixes grids with 4-fold rotational symmetry. For an $n \times n$ grid with $n$ even, the number of fixed grids is $10^{n^2/4}$. For $n$ odd, it is $10^{(n^2-1)/4 + 1}$.
- A 180-degree rotation $r^2$ fixes grids with 2-fold symmetry: $10^{\lceil n^2/2 \rceil}$ grids.
- Reflections fix grids symmetric about the corresponding axis: $10^{\lceil n^2/2 \rceil}$ for axis-aligned reflections, $10^{(n^2+n)/2}$ for diagonal reflections (when $n$ is such that the diagonal maps the grid to itself).

For a 5 by 5 grid with 10 colors, the total number of grids is $10^{25} \approx 10^{25}$, while the number of $D_4$-equivalence classes is approximately $10^{25}/8 \approx 1.25 \times 10^{24}$. The correction from Burnside's lemma is negligible for large grids because almost all grids are asymmetric. But for small grids (3 by 3, common in ARC), the correction is significant: of the $10^9$ possible grids, a meaningful fraction have nontrivial stabilizers.

---

## 13.7 Extending Beyond $D_4$

### 13.7.1 Color Permutation Groups

The 10 ARC colors form a set $C = \{0, 1, \ldots, 9\}$, and a *color permutation* is a bijection $\sigma: C \to C$. The set of all such permutations is the symmetric group $S_{10}$ of order $10! = 3{,}628{,}800$. However, color 0 has a distinguished role as the background, so the relevant group is typically $S_9$ (permutations of colors 1--9, fixing 0), with order $9! = 362{,}880$.

The `permute_colors` function in the ARC codebase samples random elements of $S_9$:

```python
def permute_colors(grid: np.ndarray, seed: int = 0) -> np.ndarray:
    """Randomly permute non-background colors (1-9)."""
    rng = np.random.RandomState(seed)
    perm = list(range(10))
    non_bg = perm[1:]
    rng.shuffle(non_bg)
    perm[1:] = non_bg
    result = grid.copy()
    for old, new in enumerate(perm):
        if old != new:
            result[grid == old] = new
    return result
```

Color permutations commute with $D_4$ transforms: rotating a color-permuted grid is the same as color-permuting a rotated grid. This means the combined symmetry group is the *direct product* $D_4 \times S_9$, with order $8 \times 362{,}880 = 2{,}903{,}040$. No training set can cover even a fraction of this group exhaustively, which is why `augment_pair` samples randomly from it.

Not all ARC tasks are invariant under arbitrary color permutations. A task whose rule depends on specific color identities (e.g., "replace all blue cells with red") is not $S_9$-invariant. The solver handles this implicitly: the test-time training loop fine-tunes on augmented examples, and if color permutations produce examples that conflict with the true rule, the model learns to downweight them. This is a form of *soft* symmetry exploitation, where the model uses the group orbit as a regularizer but does not enforce strict invariance.

### 13.7.2 Translation Groups

Square grids support cyclic translations: shifting all cells by $(dr, dc)$ with wraparound. The group of all such translations is $\mathbb{Z}_H \times \mathbb{Z}_W$ for an $H \times W$ grid, with $H \cdot W$ elements. The `_translate` transform in the probing framework implements this:

```python
def _translate(grid: np.ndarray, intensity: float) -> np.ndarray:
    """Shift grid contents, wrapping around."""
    if intensity < 0.01:
        return grid.copy()
    h, w = grid.shape
    shift_r = int(intensity * h * 0.5) % h
    shift_c = int(intensity * w * 0.5) % w
    return np.roll(np.roll(grid, shift_r, axis=0), shift_c, axis=1)
```

Translation invariance is appropriate for tasks involving periodic patterns (e.g., tilings) but inappropriate for tasks where absolute position matters (e.g., "the red cell is in the top-left corner"). The parametric intensity control allows the probing framework to test translation sensitivity at multiple scales, revealing whether the model's rule inference depends on absolute position.

The full spatial symmetry group of a square grid (combining $D_4$ with translations) is the *semidirect product* $(\mathbb{Z}_n \times \mathbb{Z}_n) \rtimes D_4$, which has $8n^2$ elements. For a 30 by 30 grid, this is $8 \times 900 = 7{,}200$ elements --- large enough that exhaustive enumeration is impractical but small enough that random sampling is effective.

### 13.7.3 Scale Symmetries

The `_scale_up` transform in the probing suite tests invariance to integer scaling: repeating each cell to produce a grid at 2x or 3x resolution. Scale invariance is relevant for ARC tasks involving patterns at multiple scales (e.g., "the output is the input tiled 2x2"). The scaling group is not a standard algebraic group (scaling by 2 and then by 3 gives scaling by 6, but scaling by 2 and then by 1/2 requires a non-integer inverse), but for the integer-valued scales relevant to discrete grids, it forms a multiplicative semigroup.

### 13.7.4 Continuous Symmetries

The groups discussed so far are *discrete* (finite or countably infinite). Many important symmetries are *continuous*: the rotation group $SO(2)$ (all planar rotations), the Euclidean group $E(2)$ (rotations + translations), and the affine group $\text{Aff}(2)$ (linear maps + translations). These arise naturally in image recognition, physics simulation, and molecular modeling.

Discrete grids break continuous symmetries: a square grid admits only 4 rotations, not continuous rotation. But in the *feature space* of a neural network, continuous rotations are well defined. An equivariant network can learn features that transform under continuous rotation representations even though the input admits only discrete rotations. This is the bridge between the discrete $D_4$ augmentation of this chapter and the continuous geometric methods of Chapters 2--5.

For the structural fuzzing framework, continuous symmetries enter through the Lie group formalism. A Lie group $G$ is a smooth manifold with a group structure, and its *Lie algebra* $\mathfrak{g}$ is the tangent space at the identity, which captures infinitesimal symmetry transformations. The exponential map $\exp: \mathfrak{g} \to G$ connects infinitesimal and finite transformations. For $SO(2)$, the Lie algebra is one-dimensional (parameterized by the angular velocity), and the exponential map is $\exp(\omega) = R(\omega)$, the rotation by angle $\omega$. For $D_4$, the Lie algebra is trivial (discrete groups have no infinitesimal structure), which is why $D_4$ augmentation is implemented directly rather than through differential geometry.

---

## 13.8 The Algebra of Augmentation Pipelines

### 13.8.1 Augmentation as a Group Homomorphism

An augmentation pipeline can be formalized as a *group homomorphism* from the symmetry group $G$ to the group of bijections on the data space $\mathcal{X}$:

$$\rho: G \to \text{Bij}(\mathcal{X}), \quad g \mapsto T_g$$

where $T_g: \mathcal{X} \to \mathcal{X}$ is the transform corresponding to group element $g$. The homomorphism property requires:

$$T_{g_1 g_2} = T_{g_1} \circ T_{g_2} \quad \text{for all } g_1, g_2 \in G$$

This is precisely the compatibility condition of a group action (Section 13.2.3). A correct augmentation pipeline is one whose transforms faithfully represent the group structure. An incorrect pipeline --- one where the composition of two transforms does not equal the transform of the composition --- produces inconsistent augmentations that confuse rather than help the model.

### 13.8.2 Verifying Group Structure

The group axioms provide a checklist for verifying an augmentation implementation:

1. **Closure.** Composing any two augmentations yields an augmentation in the set. For `all_dihedral`, this means that applying any $D_4$ transform to any output of `all_dihedral` produces another output of `all_dihedral` (possibly a different element of the same orbit).

2. **Associativity.** $(T_{g_1} \circ T_{g_2}) \circ T_{g_3} = T_{g_1} \circ (T_{g_2} \circ T_{g_3})$. This is automatically satisfied because function composition is associative.

3. **Identity.** $T_e = \text{id}$. The first element of `all_dihedral`'s output is the unmodified grid.

4. **Inverses.** For each $T_g$, there exists $T_{g^{-1}}$ such that $T_g \circ T_{g^{-1}} = \text{id}$. Rotations are their own inverses modulo 4: the inverse of `rot90` ($k=1$) is `rot90` ($k=3$).

A unit test that verifies these properties for the ARC augmentation code:

```python
def test_d4_group_structure():
    """Verify that all_dihedral produces a valid D4 orbit."""
    grid = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    orbit = all_dihedral(grid)

    # Exactly 8 elements
    assert len(orbit) == 8

    # All distinct (this grid has trivial stabilizer)
    for i in range(8):
        for j in range(i + 1, 8):
            assert not np.array_equal(orbit[i], orbit[j])

    # Closure: applying any D4 element to any orbit member
    # gives another orbit member
    for g in orbit:
        g_orbit = all_dihedral(g)
        for h in g_orbit:
            assert any(np.array_equal(h, o) for o in orbit)

    # Identity: first element is the original grid
    assert np.array_equal(orbit[0], grid)

    # Inverse: for each element, there exists an element
    # whose composition gives the identity
    for g in orbit:
        g_orbit = all_dihedral(g)
        # The orbit of g contains g's inverse applied to g = identity
        assert any(np.array_equal(o, grid) for o in g_orbit)
```

This test is not merely pedagogical. Augmentation bugs --- where the implemented transforms do not form a group --- are a real source of training degradation. A common mistake is implementing reflections as views rather than copies (Section 13.3.1), which causes subsequent rotations to modify the original, breaking the group structure.

---

## 13.9 Connection to the Geometric Framework

### 13.9.1 Symmetry in the State Space

The geometric framework of this book represents model configurations as points in a multi-dimensional state space (Chapter 1). Symmetry groups act on this state space, mapping one configuration to an equivalent one. The orbit of a configuration under the symmetry group defines an *equivalence class*, and the quotient space $\mathcal{S} / G$ (the space of equivalence classes) is the effective search space.

For the ARC solver, the state space includes the encoder parameters, the rule embedding, and the decoder parameters. The $D_4$ symmetry acts on this space indirectly: two parameter configurations that differ only in how they represent rotated patterns are equivalent. Data augmentation does not reduce the parameter space directly, but it biases optimization toward configurations that are symmetric under $D_4$, effectively projecting the search onto the quotient space.

### 13.9.2 Orbits as Geodesics

On a Riemannian manifold, the orbit of a point under a continuous symmetry group traces a *geodesic* (or more generally, a curve with specific geometric properties). For discrete groups, the orbit is a finite set of points, but the distances between orbit elements are determined by the group structure and the manifold's geometry.

In the Poincare ball (Chapter 3), where ARC rules are embedded, the $D_4$ action on rules has a geometric interpretation. If a rule $h \in \mathbb{B}^d$ encodes "fill the rightmost column," then $r \cdot h$ (the rotated rule) encodes "fill the bottom row." In hyperbolic space, these two rules are at a specific hyperbolic distance determined by how the encoder maps directional information. A well-trained encoder that has absorbed $D_4$ augmentation will place these rules close together (they are the same abstract rule), while an encoder without augmentation may place them far apart (they look like different rules in different orientations).

The hyperbolic distance between orbit elements thus provides a *direct measure of how well augmentation is working*. This complements the probing-based measure from Section 13.4.3: probing measures invariance at the grid level (does the encoder produce the same representation for rotated grids?), while hyperbolic orbit distance measures invariance at the rule level (does the rule encoder produce the same rule for rotated training pairs?).

### 13.9.3 Equivariance and Parallel Transport

There is a deep connection between equivariance and the geometric operation of *parallel transport*. Parallel transport moves a tangent vector along a curve on a manifold while preserving its "direction" relative to the manifold's geometry. An equivariant function $\phi$ satisfying $\phi(g \cdot x) = g \cdot \phi(x)$ can be understood as preserving the group action under the map $\phi$ --- the group element is "transported" from the input space to the feature space without distortion.

When the group is continuous, this connection can be made precise through the theory of *fiber bundles*: the feature space is a fiber bundle over the input space, with the group acting on the fibers, and equivariance corresponds to a specific type of bundle morphism. For the discrete group $D_4$, the fiber bundle formalism simplifies to a direct product, but the conceptual connection remains: equivariance is the algebraic expression of geometric compatibility between the input and feature spaces.

---

## 13.10 Practical Guidelines

### 13.10.1 When to Augment

Augment when:
- The symmetry group is *known* and the target function is invariant under it (or nearly so).
- The training set is small relative to the orbit size (as in ARC's few-shot regime).
- The model architecture does not enforce equivariance by construction.

Do *not* augment when:
- The symmetry is approximate and the approximation error exceeds the benefit. A 5-degree rotation is not a symmetry of a discrete grid; the interpolation artifacts may hurt more than the augmentation helps.
- The task explicitly breaks the symmetry. If the label depends on orientation, rotation augmentation teaches the model to ignore orientation --- the opposite of what is needed.
- The augmented dataset becomes so large that training time is dominated by redundant examples. For $D_4$ with 8 elements, this is rarely an issue; for $S_9$ with 362{,}880 elements, random sampling is essential.

### 13.10.2 How Many Augmentations

For a finite group $G$ acting on a training set of $N$ examples, each with orbit size $|G|$ (assuming trivial stabilizers), the fully augmented set has $N \cdot |G|$ elements. The optimal number of augmentations per example depends on the training regime:

- **Full orbit.** Use when $|G|$ is small (e.g., $|D_4| = 8$) and training time permits. This provides exact coverage of the symmetry.
- **Random sampling.** Use when $|G|$ is large or training time is constrained. Sample $k$ random group elements per example, where $k$ is tuned on a validation set. The ARC solver uses $k = 4$ as a default.
- **Adaptive sampling.** Sample more augmentations for examples with high training loss, fewer for well-learned examples. This is not implemented in the current ARC codebase but is a natural extension.

### 13.10.3 Verifying Augmentation Effectiveness

Three diagnostics assess whether augmentation is helping:

1. **Validation loss.** Compare validation loss with and without augmentation. If augmentation hurts, the symmetry assumption may be wrong or the model may be capacity-limited.

2. **Probing invariance.** Use the structure probe (Chapter 10) to measure latent displacement under group transforms. Post-augmentation displacement should be lower than pre-augmentation displacement for the targeted transforms.

3. **Orbit consistency.** For each test input, generate all $|G|$ augmented versions, predict outputs for each, and un-transform the predictions. If the model has learned the symmetry, all $|G|$ predictions should agree. The rate of disagreement quantifies residual equivariance error.

---

## 13.11 Summary

Symmetry is not decoration --- it is a computational resource. The dihedral group $D_4$, with its eight elements, is the natural symmetry group of square-grid problems and provides an eightfold multiplication of training signal at negligible cost. The algebra ensures that augmentation is complete (every equivalent configuration is reachable) and non-redundant (the orbit-stabilizer theorem counts duplicates). Consistent augmentation of input-output pairs preserves transformation rules, making $D_4$ augmentation particularly valuable for the few-shot rule inference that ARC-AGI demands.

The key ideas of this chapter are:

1. **Symmetry groups formalize augmentation.** The group axioms (closure, associativity, identity, inverses) provide a mathematical guarantee that augmented examples are complete and consistent.

2. **$D_4$ is the symmetry group of square grids.** Its eight elements --- four rotations and four reflections --- form the exhaustive set of rigid symmetries, and the `all_dihedral` function generates the complete orbit.

3. **Consistent augmentation preserves rules.** For input-output pair tasks, the same group element must be applied to both input and output, as implemented in `augment_pair`.

4. **Augmentation complements probing.** The structure probe (Chapter 10) measures whether augmentation has been absorbed; the hyperbolic rule encoder (Chapter 3) measures whether augmented training pairs produce consistent rule embeddings.

5. **The group extends.** Combining $D_4$ with color permutations ($S_9$), translations ($\mathbb{Z}_H \times \mathbb{Z}_W$), and scalings produces a large symmetry group that is best explored by random sampling.

---

## 13.12 Forward: Symmetry-Aware Fuzzing

Chapter 14 takes the symmetry framework from augmentation to *fuzzing*. Where this chapter used symmetry to generate *equivalent* training examples, Chapter 14 uses symmetry to generate *adversarial* test cases --- inputs designed to expose failures in the model's learned invariances. The key insight is that a model's failure to respect a known symmetry is a *bug*, and fuzzing the symmetry group's orbit is a targeted strategy for finding such bugs. The probing framework of Chapter 10 provides the detection mechanism; the group theory of this chapter provides the space of perturbations to search; and Chapter 14 combines them into a systematic adversarial testing methodology.
