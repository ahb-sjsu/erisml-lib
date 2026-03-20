# Chapter 5: Topological Data Analysis

*Structural Fuzzing: Geometric Methods for Adversarial Model Validation* — Andrew H. Bond

---

## 5.1 Beyond Distance: Shape

The preceding chapters built a toolkit around distance. We measured how far apart points lie in Euclidean space, computed geodesics on curved manifolds, and used metric structure to define neighborhoods, clusters, and decision boundaries. Distance is powerful, but it answers only one question: *how far?* There is a deeper question that distance alone cannot answer: *what shape?*

Consider three point clouds in the plane. The first is a tight ball of points. The second is an elongated ellipse. The third is a ring. A nearest-neighbor classifier treats all three as collections of pairwise distances. A Gaussian mixture model fits covariance ellipses. Neither representation notices the hole in the middle of the ring — the topological feature that distinguishes it from a filled disk, no matter how you stretch, bend, or compress it. Topology is the mathematics of properties preserved under continuous deformation: stretching and bending are allowed, but tearing and gluing are not. A coffee cup and a donut are topologically equivalent (both have one hole), but a sphere and a donut are not.

Topological data analysis (TDA) brings this perspective to finite point clouds. The central insight is that data has *shape*, and that shape carries information. Clusters are zero-dimensional topology (connected components). Loops are one-dimensional topology (cycles). Voids are two-dimensional topology (cavities). These features are invariant to the continuous deformations that plague distance-based methods: nonlinear scaling, monotonic warping, sensor drift, and moderate noise all change distances but preserve topology.

This invariance is not merely aesthetic. In applications where the generative process produces structured geometry — oscillatory systems, recurrent dynamics, hierarchical organization — the topological features of the data encode the structure of the process itself. A periodic signal traces a loop. A quasiperiodic signal traces a torus. A chaotic attractor produces a characteristic tangle of components and cycles that distinguishes it from stochastic noise. TDA extracts these features in a principled, stable, and computable way.

This chapter develops the TDA pipeline from first principles. We begin with a technique for lifting one-dimensional time series into higher-dimensional point clouds where topological structure becomes visible (Section 5.2). We then define persistent homology, the central algebraic tool that tracks topological features across scales (Section 5.3), and its standard visualization, the persistence diagram (Section 5.4). Section 5.5 addresses the practical problem of converting persistence diagrams into fixed-length feature vectors suitable for downstream machine learning. Finally, Section 5.6 applies the full pipeline to cetacean bioacoustics, where topological features of vocal dynamics distinguish social groups that are indistinguishable by spectral analysis alone.

---

## 5.2 Takens' Time-Delay Embedding

Many real-world systems are dynamical: they evolve in time according to deterministic or stochastic rules operating on a high-dimensional state space. We rarely observe the full state. A single sensor — a microphone, a temperature probe, a stock price — gives us a one-dimensional projection of a multi-dimensional trajectory. The question is whether we can recover the geometry of the underlying attractor from this single scalar time series.

Takens' embedding theorem (1981) answers affirmatively. Given a scalar time series $x(t)$ sampled from a smooth dynamical system whose attractor has box-counting dimension $m$, we construct delay vectors:

$$\mathbf{v}(t) = \bigl[x(t),\; x(t + \tau),\; x(t + 2\tau),\; \ldots,\; x(t + (d-1)\tau)\bigr]$$

where $\tau$ is the time delay and $d$ is the embedding dimension. Takens' theorem states that for generic $\tau$ and $d \geq 2m + 1$, the map from the original attractor to the delay-coordinate reconstruction is a diffeomorphism — a smooth, invertible map with smooth inverse. In particular, it preserves the topology of the attractor: connected components, loops, and voids in the original state space appear as connected components, loops, and voids in the reconstruction.

The requirement $d \geq 2m + 1$ is the delay-coordinate analogue of the Whitney embedding theorem, which guarantees that a $k$-dimensional manifold can be embedded in $\mathbb{R}^{2k+1}$ without self-intersections. In practice, we rarely know $m$ in advance. Setting $d = 3$ is a common starting point for systems suspected to have low-dimensional attractors (many physical oscillators have $m \leq 1$, so $d = 3 \geq 2(1) + 1$ suffices). The delay $\tau$ should be chosen large enough that successive coordinates carry independent information — a common heuristic is the first minimum of the mutual information function — but not so large that the trajectory decorrelates entirely.

The following implementation constructs delay vectors from a one-dimensional signal:

```python
def time_delay_embedding(
    signal: np.ndarray,
    delay: int = 10,
    dim: int = 3,
) -> np.ndarray:
    """Takens' time-delay embedding: reconstruct attractor from 1D series.

    Given a signal x(t), constructs vectors:
        v(t) = [x(t), x(t + τ), x(t + 2τ), ..., x(t + (d-1)τ)]

    By Takens' theorem, for generic τ and d ≥ 2m+1 (m = attractor dimension),
    this reconstructs the topology of the original dynamical system.

    Args:
        signal: 1D time series (audio samples or inter-click intervals).
        delay: Time delay τ in samples.
        dim: Embedding dimension d.

    Returns:
        Point cloud in R^dim, shape [n_points, dim].
    """
    n = len(signal) - (dim - 1) * delay
    if n <= 0:
        return np.zeros((1, dim))

    embedded = np.empty((n, dim))
    for d in range(dim):
        embedded[:, d] = signal[d * delay : d * delay + n]

    return embedded
```

The output is a point cloud of $n = N - (d-1)\tau$ points in $\mathbb{R}^d$, where $N$ is the length of the original signal. Each point is a window of $d$ samples spaced $\tau$ apart. For a pure sinusoid $x(t) = \sin(\omega t)$ with appropriate $\tau$, the two-dimensional embedding traces an ellipse — a topological circle. With $d = 3$ and suitable $\tau$, it traces a helix that, projected appropriately, reveals the same circular topology. More complex signals produce more complex point clouds, but the topological features of the underlying dynamical system are faithfully preserved.

**Computational tractability.** Persistent homology algorithms have superlinear complexity in the number of points (roughly $O(n^3)$ for the Vietoris-Rips complex, though efficient implementations do better in practice). For long time series, the embedded point cloud may contain tens or hundreds of thousands of points, making direct computation infeasible. Random subsampling provides a practical solution:

```python
def subsample_cloud(
    cloud: np.ndarray,
    max_points: int = 1000,
    seed: int | None = None,
) -> np.ndarray:
    """Subsample a point cloud for computational tractability.

    Args:
        cloud: Point cloud, shape [n, d].
        max_points: Maximum number of points to keep.
        seed: Random seed for reproducibility.

    Returns:
        Subsampled cloud, shape [min(n, max_points), d].
    """
    if len(cloud) <= max_points:
        return cloud
    rng = np.random.RandomState(seed)
    idx = rng.choice(len(cloud), max_points, replace=False)
    return cloud[idx]
```

This is justified by the stability of persistent homology: if the subsampled cloud is a sufficiently dense sample of the underlying manifold, its persistent homology approximates that of the full cloud (the Niyogi-Smale-Weinberger theorem makes this precise for manifolds with bounded curvature and reach). In practice, `max_points` between 500 and 2000 provides a good balance between computational cost and topological fidelity for most applications.

---

## 5.3 Persistent Homology

We now have a point cloud in $\mathbb{R}^d$. We want to extract its topological features — but a finite set of discrete points has no interesting topology in itself. Every point is an isolated connected component; there are no loops or voids. The key idea of persistent homology is to *thicken* the points and observe how topology changes as the thickening grows.

### 5.3.1 The Vietoris-Rips Complex

Fix a distance threshold $\varepsilon \geq 0$. The **Vietoris-Rips complex** $\mathrm{VR}(X, \varepsilon)$ is the simplicial complex whose $k$-simplices are subsets of $k+1$ points that are pairwise within distance $\varepsilon$:

- At $\varepsilon = 0$: every point is an isolated vertex. There are $n$ connected components, no edges, no triangles.
- At small $\varepsilon$: nearby points connect via edges. Some components merge. Perhaps a few triangles form.
- At moderate $\varepsilon$: clusters consolidate, cycles appear as rings of edges form around "holes" in the point cloud.
- At large $\varepsilon$: nearly everything is connected. Cycles get "filled in" by triangles. The complex approaches a single blob with trivial topology.

As $\varepsilon$ increases from $0$ to $\infty$, we obtain a nested sequence of simplicial complexes — a **filtration**:

$$\mathrm{VR}(X, 0) \subseteq \mathrm{VR}(X, \varepsilon_1) \subseteq \mathrm{VR}(X, \varepsilon_2) \subseteq \cdots$$

Persistent homology tracks the homology groups of these complexes across the filtration. Each topological feature has a **birth** time (the $\varepsilon$ at which it first appears) and a **death** time (the $\varepsilon$ at which it disappears). The **persistence** of a feature is the difference:

$$\text{persistence} = \text{death} - \text{birth}$$

### 5.3.2 Homology Dimensions

Homology decomposes into dimensions, each capturing a different type of topological feature:

**$H_0$ — Connected components.** Every point is born as its own connected component at $\varepsilon = 0$. A component dies when it merges with an older component (by convention, the younger component dies). Long-lived $H_0$ features correspond to well-separated clusters. If the data has $k$ natural clusters at widely different inter-cluster distances, we expect $k$ long-lived $H_0$ features and many short-lived ones (within-cluster mergers).

**$H_1$ — One-dimensional loops.** A loop is born when a cycle of edges forms that does not bound a filled-in region (a triangle or higher simplex). It dies when triangles fill in the cycle, collapsing the loop. Long-lived $H_1$ features correspond to robust circular or ring-like structures in the data — precisely the kind of structure produced by periodic or quasiperiodic dynamics in the Takens embedding.

**$H_2$ — Two-dimensional voids.** A void is born when a shell of triangles encloses an empty region and dies when tetrahedra fill it in. Long-lived $H_2$ features indicate spherical or toroidal cavities. These are less common in typical data analysis but important in materials science and molecular topology.

Higher homology dimensions follow the same pattern, but computation becomes expensive and the features are rarely interpretable in data analysis contexts. For most applications, $H_0$ and $H_1$ suffice.

### 5.3.3 Persistence as Signal vs. Noise

The fundamental heuristic of persistent homology is:

> **Long persistence = genuine topological feature. Short persistence = noise.**

A feature that persists across a wide range of scales reflects real structure in the data-generating process. A feature that appears and vanishes almost immediately is an artifact of the particular sample — slightly different noise would produce a different short-lived feature. This heuristic is formalized by the **stability theorem** (Cohen-Steiner, Edelsbrunner, and Harer, 2007): small perturbations of the input produce small perturbations of the persistence diagram, measured in the bottleneck or Wasserstein distance. Features with persistence smaller than the perturbation magnitude are unstable; features with persistence much larger than the perturbation are robust.

---

## 5.4 Persistence Diagrams

The standard visualization of persistent homology is the **persistence diagram**: a scatter plot in which each topological feature is represented as a point $(b, d)$ where $b$ is the birth time and $d$ is the death time. Since $d \geq b$ by definition, all points lie on or above the diagonal $d = b$.

The distance from a point to the diagonal is $\frac{d - b}{\sqrt{2}}$, proportional to the persistence. Points clustered near the diagonal represent short-lived, noisy features. Points far from the diagonal represent long-lived, significant features. Reading a persistence diagram amounts to identifying the off-diagonal points and interpreting their birth and death scales.

**Example: Two clusters and a loop.** Consider a point cloud consisting of two circular clusters separated by a gap. The $H_0$ persistence diagram will show many points near the diagonal (individual points merging within each cluster) and one point far from the diagonal (the two clusters merging at the inter-cluster distance). The $H_1$ persistence diagram will show two points moderately far from the diagonal (the two circular holes, one per cluster), dying when triangles fill them in.

**Infinite features.** By convention, one $H_0$ feature (the last surviving connected component) has $d = \infty$. It represents the single connected component that all others eventually merge into. Features with infinite death are often excluded from summary statistics, as they carry no discriminative information.

**Stability.** The stability theorem guarantees that if we perturb the input point cloud by at most $\delta$ in the Hausdorff distance, the persistence diagram changes by at most $\delta$ in the bottleneck distance. This means that persistence diagrams are robust descriptors: small noise produces small changes, and the large-persistence features are the most stable.

---

## 5.5 Feature Extraction from Persistence

Persistence diagrams are mathematically elegant but awkward as input to standard machine learning pipelines. They are multisets of variable cardinality — different point clouds produce diagrams with different numbers of points. We need a fixed-length vector representation.

Several approaches exist: persistence landscapes (Bubenik, 2015), persistence images (Adams et al., 2017), and summary statistics. For computational efficiency and interpretability, we use a summary statistics approach that extracts eight features per homology dimension, capturing the essential distributional information of the persistence diagram.

Given a persistence diagram $\{(b_i, d_i)\}_{i=1}^n$ with finite features (excluding infinite-death features), define the lifetime of each feature as $\ell_i = d_i - b_i$. The eight features are:

| Index | Feature | Formula | Interpretation |
|-------|---------|---------|----------------|
| 0 | Count | $n$ | Number of finite topological features |
| 1 | Mean lifetime | $\bar{\ell} = \frac{1}{n}\sum_i \ell_i$ | Average persistence |
| 2 | Std lifetime | $\sigma_\ell$ | Spread of persistence values |
| 3 | Max lifetime | $\max_i \ell_i$ | Most persistent (dominant) feature |
| 4 | 75th percentile | $Q_{75}(\ell)$ | Robust measure of typical persistence |
| 5 | Mean birth time | $\frac{1}{n}\sum_i b_i$ | Average scale at which features appear |
| 6 | Total persistence | $\sum_i \ell_i^2$ | $L^2$ norm of the persistence landscape |
| 7 | Normalized persistence | $\frac{\sqrt{\sum_i \ell_i^2}}{n}$ | Average energy per feature |

The implementation:

```python
def _diagram_features(dgm: np.ndarray) -> np.ndarray:
    """Extract summary statistics from a single persistence diagram.

    Returns 8 features:
        0: count — number of finite features
        1: mean_lifetime
        2: std_lifetime
        3: max_lifetime — most persistent feature
        4: p75_lifetime — 75th percentile
        5: mean_birth
        6: total_persistence — sum of squared lifetimes (L2 norm)
        7: normalized_persistence — total / count

    Args:
        dgm: Persistence diagram, shape [n, 2] with (birth, death).

    Returns:
        Feature vector, shape [8].
    """
    if len(dgm) == 0:
        return np.zeros(8, dtype=np.float32)

    finite_mask = np.isfinite(dgm[:, 1])
    finite = dgm[finite_mask]

    if len(finite) == 0:
        return np.zeros(8, dtype=np.float32)

    lifetimes = finite[:, 1] - finite[:, 0]
    n = len(lifetimes)
    total = float(np.sum(lifetimes**2))

    return np.array(
        [
            n,
            lifetimes.mean(),
            lifetimes.std() if n > 1 else 0.0,
            lifetimes.max(),
            np.percentile(lifetimes, 75),
            finite[:, 0].mean(),
            total,
            np.sqrt(total) / (n + 1e-10),
        ],
        dtype=np.float32,
    )
```

Several design choices deserve comment. First, we filter to finite features (line `finite_mask = np.isfinite(dgm[:, 1])`) because the infinite-death feature in $H_0$ carries no discriminative information. Second, we use the squared-lifetime sum for total persistence rather than the linear sum, giving greater weight to the most persistent features and aligning with the $L^2$ stability results for persistence landscapes. Third, the normalized persistence divides by the count, giving a per-feature energy that is comparable across diagrams of different sizes.

The full feature vector concatenates across homology dimensions:

```python
def tda_feature_vector(
    result: PersistenceResult,
) -> np.ndarray:
    """Extract a fixed-length feature vector from persistence diagrams.

    Concatenates 8 summary statistics per homology dimension, yielding
    8 * (max_dim + 1) features total.

    Args:
        result: Output of compute_persistence().

    Returns:
        Feature vector, shape [8 * (max_dim + 1)].
    """
    features = []
    for d in range(result.max_dim + 1):
        if d < len(result.diagrams):
            features.append(_diagram_features(result.diagrams[d]))
        else:
            features.append(np.zeros(8, dtype=np.float32))

    return np.concatenate(features)
```

With `max_homology_dim=1` (computing $H_0$ and $H_1$), this yields a 16-dimensional feature vector: 8 features for connected components and 8 features for loops. This compact representation retains enough topological information to distinguish qualitatively different point cloud shapes while being directly compatible with any classifier, regression model, or distance computation that expects fixed-length vectors.

---

## 5.6 The Full Pipeline: From Signal to Topology

The complete TDA pipeline chains the components developed in the preceding sections. Given a raw one-dimensional signal, we:

1. **Embed** the signal into $\mathbb{R}^d$ via Takens' time-delay embedding.
2. **Subsample** the resulting point cloud for computational tractability.
3. **Normalize** to zero mean and unit variance per coordinate, ensuring the Rips filtration operates on a standardized scale.
4. **Compute** the Vietoris-Rips persistent homology via the Ripser algorithm (Bauer, 2021), an optimized implementation that exploits the apparent pairs optimization and implicit representation of the boundary matrix.
5. **Extract** a fixed-length feature vector from the resulting persistence diagrams.

The following function implements steps 1 through 4, returning a `PersistenceResult` that bundles the persistence diagrams with the point cloud and metadata:

```python
@dataclass
class PersistenceResult:
    """Result of a persistent homology computation.

    Attributes:
        diagrams: List of persistence diagrams, one per homology dimension.
                  Each diagram is an array of shape [n_features, 2] with
                  columns (birth, death).
        cloud: The point cloud used for computation.
        max_dim: Maximum homology dimension computed.
    """

    diagrams: list[np.ndarray]
    cloud: np.ndarray
    max_dim: int


def compute_persistence(
    signal: np.ndarray,
    delay: int = 10,
    dim: int = 3,
    max_points: int = 1000,
    max_homology_dim: int = 1,
    thresh: float = 2.0,
    seed: int | None = None,
) -> PersistenceResult:
    """Compute persistent homology from an audio signal.

    Pipeline:
        1. Time-delay embed the signal into R^dim
        2. Subsample for tractability
        3. Normalize to zero mean, unit variance
        4. Compute Vietoris-Rips persistence via ripser

    Args:
        signal: 1D audio signal or inter-click interval sequence.
        delay: Time delay for embedding.
        dim: Embedding dimension.
        max_points: Maximum points after subsampling.
        max_homology_dim: Maximum homology dimension (0=components, 1=loops).
        thresh: Maximum filtration value for Rips complex.
        seed: Random seed for subsampling.

    Returns:
        PersistenceResult with diagrams and metadata.

    Raises:
        ImportError: If ripser is not installed.
    """
    try:
        from ripser import ripser
    except ImportError as e:
        raise ImportError(
            "ripser is required for TDA. "
            "Install with: pip install eris-ketos[tda]"
        ) from e

    cloud = time_delay_embedding(signal, delay=delay, dim=dim)
    cloud = subsample_cloud(cloud, max_points=max_points, seed=seed)

    # Normalize
    std = cloud.std(axis=0)
    std[std < 1e-10] = 1.0
    cloud = (cloud - cloud.mean(axis=0)) / std

    result = ripser(cloud, maxdim=max_homology_dim, thresh=thresh)

    return PersistenceResult(
        diagrams=result["dgms"],
        cloud=cloud,
        max_dim=max_homology_dim,
    )
```

The `thresh` parameter limits the maximum filtration value. Setting `thresh=2.0` on normalized data means we track features born and dying within two standard deviations of the mean — capturing the main topological structure while avoiding the expensive computation of features at extreme scales that are almost certainly noise.

A typical end-to-end invocation:

```python
import numpy as np
from eris_ketos.tda_clicks import compute_persistence, tda_feature_vector

# Generate a test signal: sine wave (periodic attractor → circle → H1 feature)
t = np.linspace(0, 2 * np.pi * 5, 5000)
signal = np.sin(t).astype(np.float32)

# Compute persistence
result = compute_persistence(signal, delay=50, dim=2, max_points=500)

# The sine wave's delay embedding is a circle.
# H1 should contain at least one persistent loop.
h1_diagram = result.diagrams[1]
finite_h1 = h1_diagram[np.isfinite(h1_diagram[:, 1])]
print(f"H1 features: {len(finite_h1)}")
print(f"Most persistent loop lifetime: "
      f"{(finite_h1[:, 1] - finite_h1[:, 0]).max():.3f}")

# Extract fixed-length features
features = tda_feature_vector(result)
print(f"Feature vector shape: {features.shape}")  # (16,)
```

This example makes the Takens theorem concrete. A sine wave $x(t) = \sin(\omega t)$ embedded with $d = 2$ produces points $(\sin(\omega t), \sin(\omega(t + \tau)))$, which trace an ellipse in $\mathbb{R}^2$ — a topological circle. The persistence computation detects this circle as a long-lived $H_1$ feature: a loop that is born when edges connect points around the ellipse and dies only when triangles fill in the interior at a much larger scale. The persistence (death minus birth) of this loop is large, reflecting the genuine circular topology of the embedding. Short-lived $H_1$ features, born and dying at similar scales, reflect the finite sampling density rather than genuine topology.

---

## 5.7 Application: Cetacean Click Dynamics

We now apply the full TDA pipeline to a problem where topological analysis reveals structure invisible to conventional methods: the classification of sperm whale vocalizations.

### 5.7.1 Background

Sperm whales (*Physeter macrocephalus*) communicate through stereotyped sequences of broadband clicks called *codas*. Recent research has revealed that these codas possess a combinatorial phonetic system with rhythm, tempo, rubato, and ornamentation combining hierarchically — far more structured than simple click counting would suggest (Sharma et al., *Nature Communications*, 2024). Different social units (clans) use distinct coda repertoires, and the temporal micro-structure of clicks within a coda carries clan-specific signatures.

Standard approaches analyze codas through their spectral content (frequency-domain features) or inter-click interval (ICI) histograms. These methods capture *what* the whale produces (which frequencies, which intervals) but not *how* the production unfolds over time. Two codas with identical ICI histograms but different ordering — say, accelerating versus decelerating rhythm — are indistinguishable spectrally but dynamically distinct.

### 5.7.2 Topological Approach

TDA captures the *dynamics* of click production by treating the ICI sequence as a time series and applying the Takens-persistence pipeline:

1. **Extract ICI sequence.** Given a coda with click onset times $t_1, t_2, \ldots, t_k$, compute the inter-click intervals $\Delta_i = t_{i+1} - t_i$. This is a short one-dimensional time series (typically 3--20 values for sperm whale codas, longer for click trains of other species).

2. **Time-delay embed.** Apply Takens embedding with appropriate $\tau$ and $d$. For short ICI sequences, $d = 2$ or $d = 3$ and $\tau = 1$ (consecutive ICIs) is common. For longer click trains or continuous audio, higher $\tau$ and subsampling are needed.

3. **Compute persistent homology.** The Vietoris-Rips persistence of the embedded cloud captures:
   - **$H_0$ (components):** Distinct clusters in the ICI attractor. A coda type with two characteristic rhythms (e.g., fast clicks followed by slow clicks) produces two well-separated clusters in the embedding, visible as a long-lived $H_0$ feature.
   - **$H_1$ (loops):** Cyclic patterns in the ICI dynamics. A click train with repeating rhythmic motifs traces a loop in the delay embedding, detected as a persistent $H_1$ feature. The persistence of the loop reflects the regularity of the repetition — highly stereotyped rhythm produces a clean, long-lived loop, while variable rhythm produces a noisier, shorter-lived loop.

4. **Extract features and classify.** The 16-dimensional TDA feature vector (8 per homology dimension) feeds into a standard classifier. Because the features are topological invariants, they are insensitive to the absolute timing scale of the clicks — a slow rendition and a fast rendition of the same rhythmic pattern produce the same topology — while remaining sensitive to the structural organization.

### 5.7.3 What TDA Captures That Spectral Methods Miss

The power of the topological approach is best understood through contrast with spectral methods.

**Spectral features** (Fourier coefficients, mel-frequency cepstral coefficients, spectral centroid) characterize the *frequency content* of individual clicks. They answer: what does each click sound like? Two clicks from different species that happen to have similar spectral envelopes will produce similar spectral features. More fundamentally, spectral features are *local* — they describe individual clicks or short windows, not the temporal organization of click sequences.

**ICI histograms** capture the *distribution* of inter-click intervals but discard their ordering. A coda that goes fast-fast-slow-slow and one that goes fast-slow-fast-slow produce identical ICI histograms. This is a serious loss of information for codas where rhythm pattern, not just rhythm rate, carries communicative content.

**TDA features** capture the *shape of the dynamical trajectory* in delay-coordinate space. This shape reflects the temporal organization — the ordering, the cyclicity, the clustering of intervals — in a way that is invariant to absolute tempo (stretching time uniformly is a continuous deformation that preserves topology) but sensitive to structural pattern. Two codas with different rhythmic organizations produce topologically distinct attractors even if their ICI histograms and spectral content are identical.

### 5.7.4 Practical Pipeline

The complete pipeline for a batch of whale click recordings:

```python
import numpy as np
from eris_ketos.tda_clicks import compute_persistence, tda_feature_vector

def process_coda(ici_sequence: np.ndarray) -> np.ndarray:
    """Extract topological features from a single coda's ICI sequence.

    Args:
        ici_sequence: Inter-click intervals in seconds.

    Returns:
        16-dimensional TDA feature vector.
    """
    result = compute_persistence(
        signal=ici_sequence,
        delay=1,          # consecutive ICIs
        dim=3,            # 3D embedding
        max_points=500,   # subsample for long sequences
        max_homology_dim=1,
        thresh=2.0,
        seed=42,
    )
    return tda_feature_vector(result)

# Process a collection of codas
coda_icis = [...]  # list of ICI arrays, one per coda
feature_matrix = np.stack([process_coda(ici) for ici in coda_icis])
# feature_matrix.shape = (n_codas, 16)
```

The resulting feature matrix can be passed to any classifier. The first 8 columns encode $H_0$ structure (cluster topology), and the last 8 encode $H_1$ structure (loop topology). In practice, the most discriminative features tend to be the $H_1$ max lifetime (feature index 11: the persistence of the most prominent loop, reflecting the strength of the dominant cyclic pattern) and the $H_0$ count (feature index 0: the number of distinct interval clusters).

### 5.7.5 Interpretation of Results

When applied to the DSWP dataset (1,501 annotated sperm whale codas), TDA features reveal structure aligned with the known social organization:

- **$H_0$ features differentiate coda types by interval clustering.** Codas with a single characteristic interval (e.g., "regular" codas with roughly equal spacing) produce a single dominant $H_0$ component. Codas with two characteristic intervals (e.g., "1+1+3" codas with a short-short-long pattern) produce two well-separated clusters, reflected in higher $H_0$ count and longer maximum $H_0$ lifetime.

- **$H_1$ features capture rhythmic regularity.** Codas with highly stereotyped rhythm (low rubato) produce clean loops in the delay embedding, yielding high $H_1$ max lifetime. Codas with variable rhythm (high rubato, ornamentation) produce noisier loops with lower persistence. This topological measure of rhythmic regularity correlates with — but is not reducible to — the coefficient of variation of ICIs.

- **Clan separation.** Different vocal clans produce topologically distinct attractors. The topological feature vectors cluster by clan in ways that complement spectral clustering, suggesting that clans differ not only in *what* intervals they use but in *how* they organize those intervals dynamically. This is consistent with the combinatorial phonetic hypothesis: clan identity is encoded in the compositional structure of codas, not merely in their spectral or temporal primitives.

---

## 5.8 Summary

Topological data analysis provides a principled framework for extracting shape-based features from data that complement and extend distance-based methods. The key ideas of this chapter are:

1. **Takens' embedding** lifts one-dimensional time series into higher-dimensional point clouds that faithfully reconstruct the topology of the underlying dynamical system, provided the embedding dimension satisfies $d \geq 2m + 1$.

2. **Persistent homology** tracks topological features (components, loops, voids) across a growing sequence of simplicial complexes built from the point cloud. Each feature has a birth, a death, and a persistence (lifetime).

3. **Long persistence indicates signal; short persistence indicates noise.** This heuristic is formalized by the stability theorem, which guarantees that small perturbations produce small changes in the persistence diagram.

4. **Persistence diagrams** visualize the birth-death pairs as a scatter plot. Points far from the diagonal represent robust topological features.

5. **Feature extraction** converts variable-size persistence diagrams into fixed-length vectors (8 summary statistics per homology dimension) suitable for downstream learning.

6. **Application to cetacean bioacoustics** demonstrates that topological features capture the dynamical shape of vocal patterns — cyclic structure, interval clustering, rhythmic regularity — in ways that are invariant to tempo and complementary to spectral analysis.

The topological perspective will recur in later chapters. In Part II, we will see how persistent homology can detect phase transitions in adversarial parameter spaces (Chapter 9) and how topological features serve as robust invariants for structural fuzzing campaigns (Chapter 20). The key takeaway is that topology captures qualitative structure — the presence or absence of holes, loops, and clusters — that persists under the continuous deformations induced by noise, measurement error, and parameter perturbation, making it a natural complement to the metric and manifold methods developed in Chapters 2 through 4.

---

## Exercises

**5.1.** *Embedding dimension.* Generate a Lorenz attractor time series ($\sigma = 10$, $\rho = 28$, $\beta = 8/3$) and compute Takens' embedding with $d = 2, 3, 4, 5$ and $\tau = 15$. For each $d$, compute the $H_1$ persistence diagram. At what $d$ does the dominant $H_1$ feature stabilize? How does this relate to the known dimension of the Lorenz attractor ($m \approx 2.06$)?

**5.2.** *Stability under noise.* Take a clean sine wave, compute its $H_1$ persistence diagram, and record the lifetime of the most persistent loop. Add Gaussian noise with increasing standard deviation ($\sigma = 0.01, 0.05, 0.1, 0.5, 1.0$) and repeat. Plot the dominant $H_1$ lifetime as a function of $\sigma$. At what noise level does the loop become indistinguishable from noise features? Relate your findings to the stability theorem.

**5.3.** *Feature comparison.* For a dataset of your choosing (e.g., ECG time series, financial data, synthetic chaotic systems), compute both (a) standard time-domain features (mean, variance, autocorrelation) and (b) TDA features from the Takens embedding. Train a classifier on each feature set independently, then on their concatenation. Does TDA provide complementary information?

**5.4.** *Computational scaling.* Measure the wall-clock time of `compute_persistence` as a function of `max_points` for $n \in \{100, 200, 500, 1000, 2000, 5000\}$ with `max_homology_dim=1`. Fit a power law $T(n) \propto n^\alpha$. What is the empirical exponent? How does it compare to the theoretical $O(n^3)$ worst case?

---

## Notes and Further Reading

Takens' original embedding theorem appeared in F. Takens, "Detecting strange attractors in turbulence," *Lecture Notes in Mathematics* 898 (1981). The definitive modern treatment is T. Sauer, J. Yorke, and M. Casdagli, "Embedology," *Journal of Statistical Physics* 65 (1991). For practical guidance on choosing $\tau$ and $d$, see H. Kantz and T. Schreiber, *Nonlinear Time Series Analysis* (Cambridge, 2nd ed., 2004).

Persistent homology was introduced by H. Edelsbrunner, D. Letscher, and A. Zomorodian, "Topological persistence and simplification," *Discrete & Computational Geometry* 28 (2002), and the algebraic foundations were laid by A. Zomorodian and G. Carlsson, "Computing persistent homology," *Discrete & Computational Geometry* 33 (2005). The stability theorem is due to D. Cohen-Steiner, H. Edelsbrunner, and J. Harer, "Stability of persistence diagrams," *Discrete & Computational Geometry* 37 (2007). For a comprehensive introduction, see H. Edelsbrunner and J. Harer, *Computational Topology: An Introduction* (AMS, 2010).

The Ripser algorithm is described in U. Bauer, "Ripser: efficient computation of Vietoris-Rips persistence barcodes," *Journal of Applied and Computational Topology* 5 (2021). The Python binding is available as `ripser` on PyPI.

For TDA in time series analysis, see J. Perea and J. Harer, "Sliding windows and persistence: an application of topological methods to signal analysis," *Foundations of Computational Mathematics* 15 (2015). For applications to biological signals, see B. Stolz et al., "Persistent homology of time-dependent functional networks constructed from coupled time series," *Chaos* 27 (2017).

The cetacean vocalization data and combinatorial phonetic analysis are from P. Sharma et al., "Contextual and combinatorial structure in sperm whale vocalisations," *Nature Communications* 15, 3617 (2024), and G. Begus et al., "Vowel- and diphthong-like spectral patterns in sperm whale codas," *Open Mind* (MIT Press, 2025). The DSWP dataset is available at [huggingface.co/datasets/orrp/DSWP](https://huggingface.co/datasets/orrp/DSWP).
