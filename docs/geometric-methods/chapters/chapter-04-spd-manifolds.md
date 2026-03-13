# Chapter 4: SPD Manifolds and Spectral Geometry

*Geometric Methods in Computational Modeling* --- Andrew H. Bond

---

In the preceding chapters, we established the vocabulary of manifolds, tangent spaces, and geodesics. We now turn to a specific manifold that arises naturally in signal processing, machine learning, and statistical modeling: the manifold of symmetric positive definite (SPD) matrices. This chapter develops the Riemannian geometry of SPD matrices from first principles, introduces the log-Euclidean metric as a computationally tractable distance function, and demonstrates how these ideas apply to spectral analysis of acoustic signals. The running example --- covariance analysis of cetacean vocalizations --- illustrates a broader pattern: whenever your data consists of second-order statistics (covariances, correlation matrices, diffusion tensors), flat Euclidean methods throw away geometric structure that the SPD manifold preserves.

## 4.1 The Manifold of Positive Definite Matrices

**Definition 4.1.** The set of *n x n* symmetric positive definite matrices is

$$\text{SPD}(n) = \{S \in \mathbb{R}^{n \times n} : S = S^\top,\; x^\top S x > 0 \;\forall x \neq 0\}.$$

This set is open in the space of symmetric matrices: every SPD matrix has a neighborhood of SPD matrices around it. It is also a smooth manifold of dimension *n(n+1)/2*, since a symmetric matrix is determined by its upper triangle.

### Why Not a Vector Space?

At first glance, SPD(n) looks like it might be a vector subspace of $\mathbb{R}^{n \times n}$. After all, the sum of two SPD matrices is SPD. If $S_1$ and $S_2$ are both symmetric positive definite, then for any $x \neq 0$,

$$x^\top(S_1 + S_2)x = x^\top S_1 x + x^\top S_2 x > 0.$$

However, SPD(n) fails the scalar multiplication axiom. Multiplying an SPD matrix by $-1$ produces a negative definite matrix, which is not in SPD(n). More subtly, even restricting to positive scalars does not resolve the problem, because a vector space requires closure under *all* scalars, including zero (the zero matrix is not positive definite). Therefore SPD(n) is not a vector space.

### Why Not Just Use Euclidean Distance?

One might try to measure distances between SPD matrices using the Frobenius norm:

$$d_F(S_1, S_2) = \|S_1 - S_2\|_F = \sqrt{\sum_{i,j}(S_1 - S_2)_{ij}^2}.$$

This is a perfectly valid metric in the mathematical sense, but it has a serious practical defect: it treats SPD matrices as if they were arbitrary points in $\mathbb{R}^{n \times n}$, ignoring the constraint that they must remain positive definite. Consider two covariance matrices that differ primarily in one eigenvalue --- one might have eigenvalues $(10, 1, 0.01)$ and another $(10, 1, 100)$. The Frobenius distance between them is dominated by the large eigenvalue change, but the *geometric* significance of moving an eigenvalue from $0.01$ to $100$ (a $10{,}000$-fold change in one variance direction) is much greater than Frobenius distance suggests.

More concretely, the Frobenius norm assigns equal weight to a change from $0.001$ to $0.002$ and a change from $1000.001$ to $1000.002$, even though the former represents a doubling of a variance component while the latter is negligible. For covariance matrices, ratios matter more than differences.

This motivates the use of Riemannian geometry. By equipping SPD(n) with a Riemannian metric that respects its curvature, we obtain distance functions and averaging operations that are invariant to the kinds of transformations that arise naturally in statistical settings.

### Tangent Space Structure

At any point $S \in \text{SPD}(n)$, the tangent space $T_S\text{SPD}(n)$ is the set of all *n x n* symmetric matrices --- there is no positive definiteness constraint on tangent vectors, only symmetry. This is a vector space of dimension *n(n+1)/2*. The Riemannian metric at each point defines an inner product on this tangent space, and different choices of inner product yield different Riemannian geometries on SPD(n).

## 4.2 The Log-Euclidean Metric

Among the several Riemannian metrics on SPD(n), the *log-Euclidean metric* offers the best balance of mathematical rigor and computational efficiency. It was introduced by Arsigny et al. (2006) and has since become a standard tool in diffusion tensor imaging, brain-computer interfaces, and covariance-based classification.

**Definition 4.2.** The *log-Euclidean distance* between two SPD matrices $S_1, S_2 \in \text{SPD}(n)$ is

$$d_{LE}(S_1, S_2) = \|\log(S_1) - \log(S_2)\|_F$$

where $\log(\cdot)$ denotes the matrix logarithm and $\|\cdot\|_F$ is the Frobenius norm.

**Proposition 4.1.** $d_{LE}$ is a proper metric on SPD(n). That is, it satisfies non-negativity, identity of indiscernibles, symmetry, and the triangle inequality.

*Proof sketch.* The matrix logarithm is a diffeomorphism from SPD(n) to the space Sym(n) of all *n x n* symmetric matrices. Since the Frobenius norm is a metric on Sym(n), composing with the diffeomorphism $\log$ yields a metric on SPD(n). $\square$

The key insight is that the logarithm "unfolds" the curved SPD manifold into the flat vector space of symmetric matrices, where ordinary Euclidean geometry applies. This is analogous to how the logarithm maps the positive reals $(0, \infty)$ --- which have a multiplicative structure --- onto all of $\mathbb{R}$, where addition is the natural operation.

### Computing the Matrix Logarithm

The matrix logarithm of an SPD matrix is computed via eigendecomposition. If $S = U \Lambda U^\top$ where $\Lambda = \text{diag}(\lambda_1, \ldots, \lambda_n)$ with all $\lambda_i > 0$, then

$$\log(S) = U \cdot \text{diag}(\log \lambda_1, \ldots, \log \lambda_n) \cdot U^\top.$$

This is well-defined precisely because the eigenvalues of an SPD matrix are strictly positive, so their logarithms exist. The computational cost is dominated by the eigendecomposition, which is $O(n^3)$.

The following implementation from the `eris-ketos` project encapsulates this operation as a method on an `SPDManifold` class:

```python
class SPDManifold:
    """Operations on the manifold of Symmetric Positive Definite matrices."""

    @staticmethod
    def log_map(S: torch.Tensor) -> torch.Tensor:
        """Log-Euclidean map: SPD matrix -> symmetric matrix (tangent space).

        Computes log(S) via eigendecomposition: log(S) = U·diag(log(λ))·U^T
        """
        eigvals, eigvecs = torch.linalg.eigh(S)
        eigvals = eigvals.clamp_min(1e-10)
        return eigvecs @ torch.diag_embed(eigvals.log()) @ eigvecs.transpose(-2, -1)
```

Note the `clamp_min(1e-10)` guard: in finite-precision arithmetic, eigenvalues can drift to zero or below due to numerical error, and $\log(0)$ is undefined. Clamping to a small positive constant prevents this without meaningfully affecting the result, since an eigenvalue of $10^{-10}$ already represents a direction of negligible variance. The use of `torch.linalg.eigh` (rather than `torch.linalg.eig`) exploits the symmetry of $S$ for a faster and more numerically stable decomposition.

### The Exponential Map

The inverse operation --- the matrix exponential --- maps from the tangent space (symmetric matrices) back to SPD(n):

$$\exp(X) = U \cdot \text{diag}(e^{\mu_1}, \ldots, e^{\mu_n}) \cdot U^\top$$

where $X = U \cdot \text{diag}(\mu_1, \ldots, \mu_n) \cdot U^\top$ is the eigendecomposition of the symmetric matrix $X$.

```python
    @staticmethod
    def exp_map(X: torch.Tensor) -> torch.Tensor:
        """Exp map: symmetric matrix (tangent space) -> SPD matrix."""
        eigvals, eigvecs = torch.linalg.eigh(X)
        return eigvecs @ torch.diag_embed(eigvals.exp()) @ eigvecs.transpose(-2, -1)
```

The exponential of any symmetric matrix is guaranteed to be SPD (since $e^{\mu_i} > 0$ for all real $\mu_i$), so the exp map always lands in SPD(n). Together, the log and exp maps form a diffeomorphism between SPD(n) and Sym(n), which is the foundation of the log-Euclidean framework.

### Log-Euclidean Distance Implementation

With the log map in hand, the distance computation is straightforward:

```python
    @staticmethod
    def distance(S1: torch.Tensor, S2: torch.Tensor) -> torch.Tensor:
        """Log-Euclidean distance between SPD matrices.

        d(S1, S2) = ||log(S1) - log(S2)||_F
        """
        log_diff = SPDManifold.log_map(S1) - SPDManifold.log_map(S2)
        return torch.norm(log_diff.flatten(-2), dim=-1)
```

The `flatten(-2)` call reshapes the *n x n* matrix into a vector of length $n^2$ before computing the norm. The `dim=-1` argument computes the norm along the last dimension, enabling batched computation. This entire operation supports arbitrary batch dimensions via PyTorch's broadcasting, so one can compute distances between batches of SPD matrices without explicit loops.

### Comparison: Log-Euclidean vs. Frobenius

To build intuition for why the log-Euclidean metric is more discriminative, consider two $2 \times 2$ covariance matrices:

$$S_1 = \begin{pmatrix} 1 & 0 \\ 0 & 0.01 \end{pmatrix}, \quad S_2 = \begin{pmatrix} 1 & 0 \\ 0 & 100 \end{pmatrix}.$$

The Frobenius distance is $\|S_1 - S_2\|_F = \sqrt{(0.01 - 100)^2} = 99.99$. Now consider:

$$S_3 = \begin{pmatrix} 1 & 0 \\ 0 & 10000 \end{pmatrix}.$$

The Frobenius distance $d_F(S_2, S_3) = 9900$, which is $99\times$ larger than $d_F(S_1, S_2)$, even though both pairs differ by a factor of $10{,}000$ in one eigenvalue.

The log-Euclidean distances tell a different story. We have $\log(\lambda)$ values of $\log(0.01) \approx -4.6$, $\log(100) \approx 4.6$, and $\log(10000) \approx 9.2$. So $d_{LE}(S_1, S_2) \approx |{-4.6} - 4.6| = 9.2$ and $d_{LE}(S_2, S_3) \approx |4.6 - 9.2| = 4.6$. The log-Euclidean metric correctly reports that the multiplicative change from $S_2$ to $S_3$ (a factor of 100) is smaller than the change from $S_1$ to $S_2$ (a factor of 10,000). This scale-sensitivity is essential when eigenvalues span many orders of magnitude, as they do in covariance matrices from real-world signals.

## 4.3 The Frechet Mean on SPD(n)

Given a collection of SPD matrices $S_1, \ldots, S_k$, we often need their "average." The ordinary arithmetic mean $(S_1 + \cdots + S_k)/k$ is SPD (since SPD matrices are closed under addition and positive scalar multiplication), but it is not the correct notion of center on the Riemannian manifold. The arithmetic mean minimizes $\sum_i \|S_i - M\|_F^2$, which uses the flat Euclidean distance, not the manifold distance.

**Definition 4.3.** The *Frechet mean* (or *Karcher mean*) of SPD matrices $S_1, \ldots, S_k$ with weights $w_1, \ldots, w_k$ is

$$\bar{S} = \arg\min_{M \in \text{SPD}(n)} \sum_{i=1}^{k} w_i \, d(S_i, M)^2$$

where $d$ is the chosen Riemannian distance.

For the affine-invariant metric, computing the Frechet mean requires an iterative algorithm. A major advantage of the log-Euclidean metric is that the Frechet mean has a *closed-form solution*:

$$\bar{S}_{LE} = \exp\!\left(\sum_{i=1}^{k} w_i \log(S_i)\right).$$

This is simply the exponential of the weighted average in the tangent space. The proof is immediate: $\log$ is an isometry from $(SPD(n), d_{LE})$ to $(\text{Sym}(n), \|\cdot\|_F)$, and the Frechet mean under the Frobenius norm is the arithmetic mean.

```python
    @staticmethod
    def frechet_mean(
        matrices: torch.Tensor,
        weights: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Log-Euclidean Frechet mean of SPD matrices.

        mean = exp(weighted_mean(log(S_i)))

        Args:
            matrices: Batch of SPD matrices, shape [n, d, d].
            weights: Optional weights, shape [n]. Defaults to uniform.
        """
        logs = SPDManifold.log_map(matrices)
        if weights is not None:
            w = weights / weights.sum()
            mean_log = (logs * w.view(-1, 1, 1)).sum(dim=0)
        else:
            mean_log = logs.mean(dim=0)
        return SPDManifold.exp_map(mean_log)
```

The implementation normalizes the weights to sum to one, broadcasts them across the matrix dimensions with `w.view(-1, 1, 1)`, and computes the weighted sum in log-space. The final `exp_map` call projects back onto the SPD manifold.

**Example 4.1.** *Consider two 2x2 covariance matrices representing "narrow-band" and "broad-band" spectral patterns:*

$$S_1 = \begin{pmatrix} 1 & 0.5 \\ 0.5 & 1 \end{pmatrix}, \quad S_2 = \begin{pmatrix} 4 & 0 \\ 0 & 4 \end{pmatrix}.$$

*The arithmetic mean is $\frac{1}{2}(S_1 + S_2) = \begin{pmatrix} 2.5 & 0.25 \\ 0.25 & 2.5 \end{pmatrix}$, which has eigenvalues $2.75$ and $2.25$. The log-Euclidean Frechet mean $\exp(\frac{1}{2}(\log(S_1) + \log(S_2)))$ yields a different matrix --- one that better interpolates the geometric structure of the two covariances. The difference is most pronounced when the constituent matrices have eigenvalues spanning several orders of magnitude.*

## 4.4 Frequency-Band Covariance Extraction

We now connect the abstract SPD machinery to concrete signal processing. Given a spectrogram --- a time-frequency representation of an audio signal --- we construct an SPD covariance matrix that encodes how frequency bands co-vary over time.

### From Spectrograms to Covariance Matrices

A mel spectrogram is a matrix $\mathbf{X} \in \mathbb{R}^{n_\text{mels} \times n_\text{frames}}$ where each row represents energy in a mel-scaled frequency bin and each column represents a time frame. Typical values are $n_\text{mels} = 128$ and $n_\text{frames}$ depends on the signal duration.

Working with the full $128 \times 128$ covariance matrix is impractical: it has $128 \times 129 / 2 = 8{,}256$ free parameters, and eigendecomposition would be expensive at every step. Instead, we reduce dimensionality by grouping mel bins into $n_\text{bands}$ frequency bands.

**Algorithm 4.1** (Frequency-band covariance extraction)**.**

1. **Band averaging.** Partition the $n_\text{mels}$ mel bins into $n_\text{bands}$ contiguous groups of equal size. Average within each group to obtain a reduced representation $\mathbf{B} \in \mathbb{R}^{n_\text{bands} \times n_\text{frames}}$.

2. **Centering.** Subtract the temporal mean from each band: $\tilde{\mathbf{B}} = \mathbf{B} - \bar{\mathbf{B}}$, where $\bar{B}_i = \frac{1}{n_\text{frames}} \sum_t B_{it}$.

3. **Covariance computation.** Compute the sample covariance:
$$\mathbf{C} = \frac{\tilde{\mathbf{B}} \tilde{\mathbf{B}}^\top}{n_\text{frames} - 1}.$$

4. **L2 regularization.** Add $\epsilon \mathbf{I}$ to guarantee positive definiteness:
$$\mathbf{C}_\text{reg} = \mathbf{C} + \epsilon \mathbf{I}, \quad \epsilon = 10^{-4}.$$

The regularization in step 4 is essential. The raw covariance matrix can be positive *semi*-definite (with zero eigenvalues) when $n_\text{frames} < n_\text{bands}$ or when frequency bands are linearly dependent. Adding $\epsilon \mathbf{I}$ shifts all eigenvalues by $\epsilon$, ensuring strict positive definiteness without materially altering the covariance structure.

```python
def compute_covariance(
    spectrogram: np.ndarray,
    n_bands: int = 16,
    regularize: float = 1e-4,
) -> np.ndarray:
    """Compute frequency-band covariance matrix from a spectrogram.

    Groups mel bins into n_bands equal-sized bands, then computes the
    covariance across time for each band pair.
    """
    n_mels, n_frames = spectrogram.shape
    band_size = n_mels // n_bands
    usable = n_bands * band_size

    # Group mel bins into bands by averaging
    bands = spectrogram[:usable, :].reshape(n_bands, band_size, n_frames).mean(axis=1)

    # Center and compute covariance
    centered = bands - bands.mean(axis=1, keepdims=True)
    cov = centered @ centered.T / max(n_frames - 1, 1)

    # Regularize for PD guarantee
    cov += regularize * np.eye(n_bands)
    return cov
```

Several implementation details deserve comment. The `reshape` and `mean` pattern for band averaging is an efficient alternative to explicit loops: `spectrogram[:usable, :].reshape(n_bands, band_size, n_frames)` creates a 3D tensor where the first axis indexes bands, the second indexes mel bins within each band, and the third indexes time frames. Averaging along `axis=1` collapses the within-band dimension. The `max(n_frames - 1, 1)` guard in the covariance denominator prevents division by zero when a window contains a single frame.

### Upper Triangle Feature Extraction

For many downstream tasks (classification, clustering, regression), we need a fixed-length feature vector rather than a matrix. Since the log-covariance matrix $\log(\mathbf{C})$ is symmetric, it is fully determined by its upper triangle. For $n_\text{bands}$ bands, this yields

$$d = \frac{n_\text{bands}(n_\text{bands} + 1)}{2}$$

features. With $n_\text{bands} = 16$, this gives $d = 136$ features.

```python
def spd_features_from_spectrogram(
    spectrogram: np.ndarray,
    n_bands: int = 16,
    regularize: float = 1e-4,
) -> np.ndarray:
    """Extract SPD manifold features from a spectrogram.

    Computes the covariance matrix, applies the log-Euclidean map, and
    extracts the upper triangle as a feature vector.
    """
    cov = compute_covariance(spectrogram, n_bands=n_bands, regularize=regularize)

    # Log-Euclidean map via eigendecomposition
    eigvals, eigvecs = np.linalg.eigh(cov)
    eigvals = np.maximum(eigvals, 1e-10)
    log_cov = eigvecs @ np.diag(np.log(eigvals)) @ eigvecs.T

    # Upper triangle
    idx = np.triu_indices(n_bands)
    return log_cov[idx].astype(np.float32)
```

The feature vector consists of:
- **Diagonal elements** $(\log(\mathbf{C}))_{ii}$: the log-variance of each frequency band. These capture how much energy fluctuation occurs in each band over time.
- **Off-diagonal elements** $(\log(\mathbf{C}))_{ij}$ for $i < j$: the log-domain cross-band correlations. These encode how frequency bands co-vary --- whether they tend to increase and decrease together (positive), move inversely (negative), or behave independently (near zero).

The off-diagonal elements are precisely what makes SPD features more informative than per-band energy statistics. A flat spectrogram representation captures the energy in each band independently but discards information about *relationships* between bands. The covariance matrix retains this information, and the log map ensures that distances between covariance matrices respect the manifold geometry.

## 4.5 Spectral Trajectory Analysis

The covariance extraction described above produces a single SPD matrix summarizing an entire signal. But many signals of interest have time-varying spectral structure. A spoken vowel transitions into a consonant; a musical note evolves from attack to sustain to decay; a whale vocalization may shift its spectral content within a single click or across a coda sequence. To capture this temporal evolution, we extend the single-covariance analysis to a *trajectory* on the SPD manifold.

### Sliding Window Covariance

The idea is simple: slide a window across the spectrogram and compute a covariance matrix at each position. This produces a sequence of SPD matrices $\mathbf{C}_1, \mathbf{C}_2, \ldots, \mathbf{C}_T$, one per window position, which traces a path on the SPD manifold.

**Definition 4.4.** A *spectral trajectory* is a sequence of SPD covariance matrices $(\mathbf{C}_t)_{t=1}^T$ computed from overlapping windows of a spectrogram, together with the associated timestamps.

The trajectory captures how the second-order spectral structure evolves over time. If the covariance is constant (the signal is stationary), the trajectory collapses to a single point. If the signal undergoes a smooth spectral transition, the trajectory traces a smooth curve on SPD(n). If the signal changes abruptly, the trajectory exhibits discontinuities.

```python
@dataclass
class SpectralTrajectory:
    """Trajectory of SPD covariance matrices across time windows."""
    matrices: np.ndarray       # shape [n_windows, n_bands, n_bands]
    timestamps: np.ndarray     # center time of each window in seconds
    geodesic_deviation: float  # how far trajectory deviates from geodesic


def compute_spectral_trajectory(
    spectrogram: np.ndarray,
    n_bands: int = 16,
    window_frames: int = 32,
    hop_frames: int = 16,
    sr: int = 32000,
    hop_length: int = 512,
    regularize: float = 1e-4,
) -> SpectralTrajectory:
    """Compute time-varying SPD covariance trajectory."""
    n_mels, n_frames = spectrogram.shape
    matrices = []
    timestamps = []

    for start in range(0, n_frames - window_frames + 1, hop_frames):
        window = spectrogram[:, start : start + window_frames]
        cov = compute_covariance(window, n_bands=n_bands, regularize=regularize)
        matrices.append(cov)
        center_frame = start + window_frames // 2
        timestamps.append(center_frame * hop_length / sr)

    if len(matrices) < 2:
        return SpectralTrajectory(
            matrices=np.array(matrices),
            timestamps=np.array(timestamps),
            geodesic_deviation=0.0,
        )

    mat_array = np.array(matrices)
    ts_array = np.array(timestamps)

    # Compute geodesic deviation
    mat_torch = torch.tensor(mat_array, dtype=torch.float32)
    total_dist = 0.0
    geodesic_dist = float(SPDManifold.distance(mat_torch[0], mat_torch[-1]))
    for i in range(len(mat_torch) - 1):
        total_dist += float(SPDManifold.distance(mat_torch[i], mat_torch[i + 1]))

    deviation = (total_dist - geodesic_dist) / max(geodesic_dist, 1e-10)

    return SpectralTrajectory(
        matrices=mat_array,
        timestamps=ts_array,
        geodesic_deviation=deviation,
    )
```

The implementation iterates over the spectrogram with a sliding window of `window_frames` frames and a hop size of `hop_frames` frames. At each position, it computes the covariance matrix using the same `compute_covariance` function described in Section 4.4. Timestamps are computed from the center of each window using the sample rate and STFT hop length.

### The Geodesic Deviation Metric

The most informative summary statistic of a spectral trajectory is its *geodesic deviation*: how much the actual path on the SPD manifold deviates from the shortest possible path (the geodesic) between its endpoints.

**Definition 4.5.** Given a spectral trajectory $\mathbf{C}_1, \ldots, \mathbf{C}_T$, the *geodesic deviation* is

$$\delta = \frac{L_\text{path} - d_\text{geo}}{d_\text{geo}}$$

where $L_\text{path} = \sum_{t=1}^{T-1} d_{LE}(\mathbf{C}_t, \mathbf{C}_{t+1})$ is the total path length (sum of consecutive log-Euclidean distances) and $d_\text{geo} = d_{LE}(\mathbf{C}_1, \mathbf{C}_T)$ is the geodesic distance between endpoints.

By the triangle inequality, $L_\text{path} \geq d_\text{geo}$, so $\delta \geq 0$. Equality $\delta = 0$ holds if and only if the trajectory follows a geodesic --- all the $\mathbf{C}_t$ lie on the shortest path between $\mathbf{C}_1$ and $\mathbf{C}_T$.

**Interpretation.** The geodesic deviation quantifies the "straightness" of the spectral evolution on the manifold:

- $\delta \approx 0$: The spectral covariance evolves smoothly and monotonically from one state to another. In acoustic terms, this is analogous to a *diphthong* --- a smooth vowel transition.
- $\delta \gg 0$: The covariance evolution is non-monotonic, wandering or oscillating on the manifold. This suggests a more complex spectral structure, possibly involving multiple distinct spectral states.

In the log-Euclidean framework, geodesics have a particularly simple form. Since the log map is an isometry to flat space, a geodesic from $S_0$ to $S_1$ is

$$\gamma(t) = \exp\!\left((1-t)\log(S_0) + t\log(S_1)\right), \quad t \in [0, 1].$$

This is simply linear interpolation in log-space, followed by exponentiation back to SPD(n). The geodesic deviation measures how far the actual trajectory departs from this linear interpolation.

## 4.6 Application: Acoustic Signal Analysis

To ground these abstractions in a concrete application, we examine how SPD manifold methods apply to the analysis of cetacean vocalizations, specifically sperm whale (*Physeter macrocephalus*) clicks and codas.

### Spectral Structure of Whale Clicks

Sperm whale clicks are broadband, impulsive signals produced in the nasal complex. Despite their apparent simplicity, recent work by Begus et al. (*Open Mind*, 2025) has shown that sperm whale codas exhibit spectral structure analogous to human vowel formants. Specifically, the frequency-band correlations in whale clicks --- the off-diagonal elements of the covariance matrix --- reflect harmonic and resonance patterns that are remarkably similar to the formant structure of human speech.

This discovery makes SPD analysis particularly appropriate: the key discriminative information lies not in the energy of individual frequency bands (which flat spectrogram methods capture well) but in the *correlations between bands* (which only covariance-based methods capture). When two frequency bands consistently co-vary --- rising and falling in energy together --- this indicates a common underlying physical mechanism, such as a resonance in the vocal tract (for humans) or the nasal complex (for sperm whales).

### Why SPD Distance Outperforms Flat Distance

Consider two whale clicks, $A$ and $B$, with similar overall spectral energy distributions but different cross-frequency correlation patterns. Click $A$ might have strong correlation between bands 3 and 7 (suggesting a harmonic relationship at those frequencies), while click $B$ has independent energy in those same bands.

The flat spectrogram distance $\|X_A - X_B\|_F$ computes the sum of squared differences in energy at each time-frequency bin. If the total energy profiles are similar, this distance will be small, even though the correlation structure is completely different.

The SPD distance $d_{LE}(\mathbf{C}_A, \mathbf{C}_B)$ operates on the covariance matrices, where the cross-frequency correlations are explicitly encoded in the off-diagonal elements. The log map amplifies differences in the eigenstructure of the covariance matrices. If click $A$ has a strong eigenvalue corresponding to the correlated band-3/band-7 direction while click $B$ does not, this difference is captured as a large displacement in log-space, yielding a large SPD distance.

### Practical Pipeline

A complete analysis pipeline for acoustic SPD features proceeds as follows:

1. **Preprocessing.** Compute a mel spectrogram from the raw audio waveform using standard parameters (e.g., 128 mel bins, 512-sample hop length, 2048-sample FFT window). Apply log-scaling: $X \leftarrow \log(X + \epsilon)$.

2. **Covariance extraction.** Apply `compute_covariance` with $n_\text{bands} = 16$ to obtain a $16 \times 16$ SPD matrix. This reduces the 128-dimensional mel representation to a 16-dimensional band representation while preserving cross-frequency correlations.

3. **Feature extraction.** Apply `spd_features_from_spectrogram` to obtain a 136-dimensional feature vector (the upper triangle of the $16 \times 16$ log-covariance matrix).

4. **Trajectory analysis.** For signals with temporal structure (e.g., a sequence of clicks in a coda), apply `compute_spectral_trajectory` with appropriate window and hop parameters. The resulting geodesic deviation quantifies how the spectral structure evolves over time.

5. **Downstream tasks.** Use the SPD features and/or trajectory statistics as inputs to classifiers, clustering algorithms, or other models. The log-Euclidean features live in a flat vector space, so standard machine learning methods (SVM, random forests, neural networks) can be applied directly.

### Choosing Parameters

The main parameters governing the covariance extraction are:

- **$n_\text{bands}$**: Controls the trade-off between spectral resolution and statistical reliability. More bands yield a higher-dimensional covariance matrix that captures finer-grained spectral relationships, but requires more temporal frames for reliable estimation. A rule of thumb is $n_\text{frames} \geq 3 \cdot n_\text{bands}$ for the sample covariance to be well-conditioned. The default of 16 bands (yielding a $16 \times 16$ covariance matrix and 136 features) works well for signals with at least 50 time frames.

- **$\epsilon$ (regularization)**: Must be large enough to prevent numerical issues in the eigendecomposition but small enough not to dominate the covariance structure. The default $\epsilon = 10^{-4}$ is appropriate when spectrogram values are in the range $[0, 1]$ or $[-1, 1]$. For log-scaled spectrograms with values in $[-10, 0]$, covariance entries are on the order of $1$ to $10$, so $10^{-4}$ is safely negligible.

- **Window and hop sizes** (for trajectory analysis): The window must be large enough to estimate a reliable covariance matrix ($\geq 3 \cdot n_\text{bands}$ frames, as above) and small enough to capture temporal variation. The hop size controls temporal resolution versus computational cost.

## 4.7 Connections and Extensions

### Relationship to Other SPD Metrics

The log-Euclidean metric is one of several Riemannian metrics on SPD(n). The most commonly discussed alternatives are:

- **Affine-invariant metric**: $d_{AI}(S_1, S_2) = \|\log(S_1^{-1/2} S_2 S_1^{-1/2})\|_F$. This is invariant under congruence transformations $S \mapsto A S A^\top$ and is the "natural" Riemannian metric on SPD(n). However, computing the Frechet mean requires iterative optimization, making it more expensive.

- **Bures-Wasserstein metric**: Related to optimal transport between Gaussian distributions. The distance $d_{BW}(S_1, S_2) = \text{tr}(S_1) + \text{tr}(S_2) - 2\text{tr}(S_1^{1/2} S_2 S_1^{1/2})^{1/2}$ arises in quantum information theory and has connections to the Wasserstein-2 distance.

- **Power-Euclidean metrics**: $d_\alpha(S_1, S_2) = \frac{1}{\alpha}\|S_1^\alpha - S_2^\alpha\|_F$ for $\alpha \in (0, 1]$. The log-Euclidean metric is the limit as $\alpha \to 0$.

The log-Euclidean metric is preferred in computational settings for three reasons: (1) the Frechet mean is closed-form, (2) the log map provides a global diffeomorphism to a vector space where standard algorithms apply, and (3) it is computationally no more expensive than Frobenius distance (one eigendecomposition per matrix).

### Diffusion Tensor Imaging

The SPD manifold framework was originally developed for diffusion tensor imaging (DTI) in neuroimaging, where each voxel in a brain scan is represented by a $3 \times 3$ SPD matrix describing the local diffusion of water molecules. The same mathematical machinery described in this chapter --- log-Euclidean distances, Frechet means, trajectory analysis --- applies directly to DTI data, with "frequency bands" replaced by "diffusion directions."

### Covariance Descriptors in Computer Vision

In computer vision, *region covariance descriptors* summarize image regions by the covariance of pixel features (position, intensity, gradient magnitude, gradient orientation). These descriptors are SPD matrices, and log-Euclidean methods have been used for texture classification, pedestrian detection, and visual tracking. The frequency-band covariance extraction described here is the acoustic analogue of the visual region covariance descriptor.

### Information Geometry

The SPD manifold has deep connections to information geometry, the study of statistical models as Riemannian manifolds. A multivariate Gaussian distribution $\mathcal{N}(\mu, \Sigma)$ is parameterized by its mean $\mu$ and covariance $\Sigma \in \text{SPD}(n)$. The Fisher information metric on the space of Gaussians induces a Riemannian metric on SPD(n) that is closely related to the affine-invariant metric. The log-Euclidean metric can be seen as a computationally convenient approximation to this Fisher metric.

## Exercises

**4.1.** Prove that SPD(n) is an open subset of the vector space of $n \times n$ symmetric matrices. (*Hint*: use the continuity of eigenvalues as functions of matrix entries.)

**4.2.** Show that the arithmetic mean of two SPD matrices $\frac{1}{2}(S_1 + S_2)$ is always SPD, but it does not minimize $d_{LE}(S_1, M)^2 + d_{LE}(S_2, M)^2$ over $M \in \text{SPD}(n)$ in general.

**4.3.** Implement a function that computes the geodesic $\gamma(t) = \exp((1-t)\log(S_0) + t\log(S_1))$ for $t \in [0, 1]$ and verify numerically that $d_{LE}(S_0, \gamma(t)) = t \cdot d_{LE}(S_0, S_1)$ for several values of $t$.

**4.4.** Consider a spectrogram with $n_\text{mels} = 128$ and $n_\text{frames} = 20$. With $n_\text{bands} = 16$, the covariance matrix is $16 \times 16$, requiring estimation of $16 \times 17 / 2 = 136$ free parameters from 20 observations. Discuss the statistical reliability of this estimate and the role of regularization.

**4.5.** A spectral trajectory has geodesic deviation $\delta = 0.05$. Another has $\delta = 2.3$. Without seeing the spectrograms, what can you infer about the spectral evolution in each case? Propose a hypothesis about what kinds of acoustic signals might produce each pattern.

**4.6.** The `compute_covariance` implementation uses band averaging (mean within each band) for dimensionality reduction. An alternative is band max-pooling. Discuss the trade-offs: what spectral information does each approach preserve or discard? Implement both and compare the resulting SPD distances on synthetic spectrograms.

**4.7.** Show that the geodesic deviation $\delta$ is invariant under reparameterization of the trajectory (i.e., it depends on the sequence of matrices but not on the timestamps). Is this a desirable property for acoustic analysis? Why or why not?

## Notes and References

The log-Euclidean framework for SPD matrices was introduced by Arsigny, Fillard, Pennec, and Ayache, "Log-Euclidean metrics for fast and simple calculus on diffusion tensors," *Magnetic Resonance in Medicine* 56(2), 2006. The affine-invariant metric dates to Pennec, Fillard, and Ayache, "A Riemannian framework for tensor computing," *International Journal of Computer Vision* 66(1), 2006.

For covariance descriptors in computer vision, see Tuzel, Porikli, and Meer, "Region covariance: A fast descriptor for detection and classification," *ECCV* 2006. The application to brain-computer interfaces is surveyed in Barachant, Bonnet, Congedo, and Jutten, "Riemannian geometry applied to BCI classification," *LVA/ICA* 2010.

The discovery of vowel-like spectral structure in sperm whale clicks is reported in Begus, Leban, Silov, Gero, and Sprague, "Vowels and diphthongs in sperm whale vocalization," *Open Mind* 9, 2025. The SPD manifold analysis of cetacean codas using the methods described in this chapter is implemented in the `eris-ketos` package (Bond, 2026).

The connection between SPD geometry and information geometry is developed in Amari, *Information Geometry and Its Applications*, Springer, 2016. For optimal transport on SPD matrices, see Bhatia, Jain, and Lim, "On the Bures-Wasserstein distance between positive definite matrices," *Expositiones Mathematicae* 37(2), 2019.
